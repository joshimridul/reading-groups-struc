#!/usr/bin/env python3

"""Audit paper `stata_output` artifacts against TeX entrypoint references.

The script is read-only. It strips LaTeX comments, scans root-level `.tex`
files for `stata_output/` table and figure references, and reports missing or
extra files. It is meant to keep the repository paper folder organization
reproducible.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path


DEFAULT_OVERLEAF = Path(__file__).resolve().parents[1]


def strip_latex_comments(text: str) -> str:
    """Remove unescaped percent comments from LaTeX source."""
    lines = []
    for line in text.splitlines():
        kept = []
        for i, char in enumerate(line):
            if char == "%" and (i == 0 or line[i - 1] != "\\"):
                break
            kept.append(char)
        lines.append("".join(kept))
    return "\n".join(lines)


def normalize_reference(ref: str) -> str:
    path = Path(ref)
    return path.name if path.suffix else f"{path.name}.tex"


def line_number(text: str, position: int) -> int:
    return text[:position].count("\n") + 1


def scan_tex_references(overleaf_dir: Path) -> dict[str, set[str]]:
    refs_by_tex: dict[str, set[str]] = {}
    for tex_path in sorted(overleaf_dir.glob("*.tex")):
        text = strip_latex_comments(tex_path.read_text(errors="ignore"))
        refs = set(re.findall(r"\\input\{stata_output/([^}]+)\}", text))
        refs.update(
            re.findall(
                r"\\includegraphics(?:\[[^\]]*\])?\{stata_output/([^}]+)\}",
                text,
            )
        )
        normalized = {normalize_reference(ref) for ref in refs}
        if normalized:
            refs_by_tex[tex_path.name] = normalized
    return refs_by_tex


def scan_entrypoint_labels(
    overleaf_dir: Path, entrypoint: str
) -> tuple[dict[str, list[tuple[str, int]]], list[tuple[str, str, int]]]:
    """Scan labels and refs in an entrypoint plus its active table inputs."""
    entrypoint_path = overleaf_dir / entrypoint
    text = strip_latex_comments(entrypoint_path.read_text(errors="ignore"))

    labels: dict[str, list[tuple[str, int]]] = {}
    refs: list[tuple[str, str, int]] = []

    def add_label(label: str, source: str, line: int) -> None:
        labels.setdefault(label, []).append((source, line))

    for match in re.finditer(r"\\label\{([^}]+)\}", text):
        add_label(match.group(1), entrypoint, line_number(text, match.start()))
    for match in re.finditer(r"\\(?:ref|eqref|autoref|pageref)\{([^}]+)\}", text):
        refs.append((match.group(1), entrypoint, line_number(text, match.start())))

    input_matches = re.finditer(r"\\input\{((?:stata_output|structural_output)/[^}]+)\}", text)
    for match in input_matches:
        input_ref = match.group(1)
        input_path = overleaf_dir / (input_ref if Path(input_ref).suffix else f"{input_ref}.tex")
        if not input_path.exists():
            continue
        input_text = strip_latex_comments(input_path.read_text(errors="ignore"))
        source = str(input_path.relative_to(overleaf_dir))
        for label_match in re.finditer(r"\\label\{([^}]+)\}", input_text):
            add_label(label_match.group(1), source, line_number(input_text, label_match.start()))
        for ref_match in re.finditer(
            r"\\(?:ref|eqref|autoref|pageref)\{([^}]+)\}", input_text
        ):
            refs.append((ref_match.group(1), source, line_number(input_text, ref_match.start())))

    return labels, refs


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overleaf-dir", type=Path, default=DEFAULT_OVERLEAF)
    parser.add_argument("--entrypoint", default="main_3country_new.tex")
    parser.add_argument(
        "--show-extra",
        action="store_true",
        help="Print files in stata_output not referenced by any scanned root TeX file.",
    )
    parser.add_argument(
        "--repo-output-dir",
        type=Path,
        help="Optional repo output directory to compare against the entrypoint's active references.",
    )
    parser.add_argument(
        "--check-labels",
        action="store_true",
        help="Check label/ref integrity in the entrypoint plus active table inputs.",
    )
    args = parser.parse_args()

    overleaf_dir = args.overleaf_dir
    stata_output = overleaf_dir / "stata_output"
    if not overleaf_dir.exists():
        raise FileNotFoundError(f"Missing paper directory: {overleaf_dir}")
    if not stata_output.exists():
        raise FileNotFoundError(f"Missing stata_output directory: {stata_output}")

    refs_by_tex = scan_tex_references(overleaf_dir)
    all_refs = set().union(*refs_by_tex.values()) if refs_by_tex else set()
    files = {path.name for path in stata_output.iterdir() if path.is_file()}
    entry_refs = refs_by_tex.get(args.entrypoint, set())

    missing_all = sorted(all_refs - files)
    missing_entry = sorted(entry_refs - files)
    extra_all = sorted(files - all_refs)
    extra_entry = sorted(files - entry_refs)

    print(f"Paper directory: {overleaf_dir}")
    print(f"Root TeX files with stata_output refs: {len(refs_by_tex)}")
    for name in sorted(refs_by_tex):
        print(f"  - {name}: {len(refs_by_tex[name])} files")
    print(f"stata_output files: {len(files)}")
    print(f"Referenced by any scanned TeX: {len(all_refs)}")
    print(f"Referenced by {args.entrypoint}: {len(entry_refs)}")
    print(f"Missing referenced files, any scanned TeX: {len(missing_all)}")
    for name in missing_all:
        print(f"  missing-any: {name}")
    print(f"Missing referenced files, {args.entrypoint}: {len(missing_entry)}")
    for name in missing_entry:
        print(f"  missing-entry: {name}")
    print(f"Extra files versus any scanned TeX: {len(extra_all)}")
    if args.show_extra:
        for name in extra_all:
            print(f"  extra-any: {name}")
    print(f"Extra files versus {args.entrypoint}: {len(extra_entry)}")

    sync_failed = False
    if args.repo_output_dir is not None:
        repo_output = args.repo_output_dir
        if not repo_output.exists():
            raise FileNotFoundError(f"Missing repo output directory: {repo_output}")

        same = []
        different = []
        missing_repo = []
        missing_overleaf = []
        for name in sorted(entry_refs):
            repo_path = repo_output / name
            overleaf_path = stata_output / name
            if not repo_path.exists():
                missing_repo.append(name)
                continue
            if not overleaf_path.exists():
                missing_overleaf.append(name)
                continue
            if sha256(repo_path) == sha256(overleaf_path):
                same.append(name)
            else:
                different.append(name)

        print(f"Repo output directory: {repo_output}")
        print(f"Synced active {args.entrypoint} files: {len(same)}")
        print(f"Different active {args.entrypoint} files: {len(different)}")
        for name in different:
            print(f"  different-entry: {name}")
        print(f"Missing active {args.entrypoint} files in repo output: {len(missing_repo)}")
        for name in missing_repo:
            print(f"  missing-repo-entry: {name}")
        print(f"Missing active {args.entrypoint} files in Overleaf: {len(missing_overleaf)}")
        for name in missing_overleaf:
            print(f"  missing-overleaf-entry: {name}")
        sync_failed = bool(different or missing_repo or missing_overleaf)

    label_failed = False
    if args.check_labels:
        labels, refs = scan_entrypoint_labels(overleaf_dir, args.entrypoint)
        label_names = set(labels)
        ref_names = {label for label, _, _ in refs}
        missing_labels = sorted(ref_names - label_names)
        unreferenced_labels = sorted(label_names - ref_names)
        unreferenced_exhibit_labels = [
            label
            for label in unreferenced_labels
            if label.startswith(("tab:", "fig:"))
        ]

        print(f"Labels in {args.entrypoint} plus active table inputs: {len(label_names)}")
        print(f"Distinct refs in {args.entrypoint} plus active table inputs: {len(ref_names)}")
        print(f"Refs with missing labels: {len(missing_labels)}")
        for label in missing_labels:
            locations = [f"{source}:{line}" for ref, source, line in refs if ref == label]
            print(f"  missing-label: {label} referenced at {', '.join(locations)}")
        print(f"Unreferenced exhibit labels: {len(unreferenced_exhibit_labels)}")
        for label in unreferenced_exhibit_labels:
            locations = [f"{source}:{line}" for source, line in labels[label]]
            print(f"  unreferenced-exhibit-label: {label} at {', '.join(locations)}")
        label_failed = bool(missing_labels)

    return 1 if missing_all or missing_entry or extra_all or extra_entry or sync_failed or label_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
