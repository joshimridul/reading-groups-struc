#!/usr/bin/env python3

"""Verify the paper reproducibility freeze manifest against current files.

This is a read-only companion to `audit_overleaf_artifacts.py`. It checks that
the hashes recorded in `PAPER_REPRODUCIBILITY_FREEZE.md` still match the live
Overleaf manuscript, the main generation/sync code, and every active exhibit
referenced by `main2.tex`.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

from audit_overleaf_artifacts import DEFAULT_OVERLEAF, scan_tex_references


DEFAULT_REPO = Path("/Users/mriduljoshi/Github/reading-groups-struc")
DEFAULT_MANIFEST = DEFAULT_REPO / "PAPER_REPRODUCIBILITY_FREEZE.md"
DEFAULT_REPO_OUTPUT = DEFAULT_REPO / "4_Stata2" / "output"


LIVE_LABELS = {
    "live `main2.tex`": "main2.tex",
    "live `main2.pdf`": "main2.pdf",
    "live `main2.log`": "main2.log",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_hash_rows(manifest: Path) -> dict[str, str]:
    text = manifest.read_text()
    rows: dict[str, str] = {}
    for label, digest in re.findall(r"^\| ([^|]+?) \| `([0-9a-f]{64})` \|$", text, re.M):
        rows[label.strip()] = digest
    return rows


def expected_file_for_label(label: str, repo_root: Path, overleaf_dir: Path, repo_output: Path) -> Path | None:
    if label in LIVE_LABELS:
        return overleaf_dir / LIVE_LABELS[label]

    if label.startswith("`") and label.endswith("`"):
        inner = label.strip("`")
        repo_path = repo_root / inner
        if repo_path.exists():
            return repo_path
        exhibit_path = repo_output / inner
        if exhibit_path.exists():
            return exhibit_path

    return None


def verify_hash_rows(
    rows: dict[str, str], repo_root: Path, overleaf_dir: Path, repo_output: Path
) -> list[str]:
    errors: list[str] = []
    for label, expected in sorted(rows.items()):
        path = expected_file_for_label(label, repo_root, overleaf_dir, repo_output)
        if path is None:
            errors.append(f"no current file found for manifest row: {label}")
            continue
        if not path.exists():
            errors.append(f"missing file for manifest row {label}: {path}")
            continue
        actual = sha256(path)
        if actual != expected:
            errors.append(f"hash mismatch for {label}: expected {expected}, got {actual}")
    return errors


def verify_active_exhibits(
    rows: dict[str, str], overleaf_dir: Path, repo_output: Path, entrypoint: str
) -> list[str]:
    errors: list[str] = []
    refs_by_tex = scan_tex_references(overleaf_dir)
    entry_refs = sorted(refs_by_tex.get(entrypoint, set()))

    for name in entry_refs:
        label = f"`{name}`"
        if label not in rows:
            errors.append(f"active exhibit missing from manifest: {name}")
            continue
        overleaf_path = overleaf_dir / "stata_output" / name
        repo_path = repo_output / name
        if not overleaf_path.exists():
            errors.append(f"active exhibit missing in Overleaf: {name}")
            continue
        if not repo_path.exists():
            errors.append(f"active exhibit missing in repo output: {name}")
            continue
        overleaf_hash = sha256(overleaf_path)
        repo_hash = sha256(repo_path)
        expected = rows[label]
        if overleaf_hash != repo_hash:
            errors.append(f"Overleaf/repo active exhibit hash differs: {name}")
        if overleaf_hash != expected:
            errors.append(f"active exhibit hash differs from manifest: {name}")

    manifest_exhibits = {
        label.strip("`")
        for label in rows
        if label.startswith("`")
        and label.endswith("`")
        and (repo_output / label.strip("`")).exists()
    }
    extras = sorted(manifest_exhibits - set(entry_refs))
    for name in extras:
        errors.append(f"manifest exhibit is not active in {entrypoint}: {name}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--overleaf-dir", type=Path, default=DEFAULT_OVERLEAF)
    parser.add_argument("--repo-output-dir", type=Path, default=DEFAULT_REPO_OUTPUT)
    parser.add_argument("--entrypoint", default="main2.tex")
    args = parser.parse_args()

    rows = parse_hash_rows(args.manifest)
    errors = []
    errors.extend(verify_hash_rows(rows, args.repo_root, args.overleaf_dir, args.repo_output_dir))
    errors.extend(verify_active_exhibits(rows, args.overleaf_dir, args.repo_output_dir, args.entrypoint))

    print(f"Manifest: {args.manifest}")
    print(f"Hash rows checked: {len(rows)}")
    print(f"Active {args.entrypoint} exhibits: {len(scan_tex_references(args.overleaf_dir).get(args.entrypoint, set()))}")

    if errors:
        print("Freeze manifest verification FAILED")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Freeze manifest verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
