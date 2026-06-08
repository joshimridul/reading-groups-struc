#!/usr/bin/env python3

"""Check whether the canonical paper is ready for final circulation.

This read-only check separates two states that are easy to conflate:

1. Manuscript gates: build log, active exhibit sync, label integrity, freeze
   hashes, PDF metadata, and rendered-page checks are clean.
2. Release gates: the manuscript has been switched out of draft mode and the
   repository is clean enough to commit/tag.

The script exits nonzero when either manuscript gates fail or release blockers
remain. Known intentional blockers, such as `\\publicversionfalse`, are reported
as blockers rather than hidden behind the clean manuscript checks.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from audit_overleaf_artifacts import scan_entrypoint_labels, scan_tex_references, sha256
from verify_freeze_manifest import (
    DEFAULT_MANIFEST,
    DEFAULT_OVERLEAF,
    DEFAULT_REPO,
    DEFAULT_REPO_OUTPUT,
    parse_hash_rows,
    verify_active_exhibits,
    verify_hash_rows,
)
from triage_release_worktree import (
    active_exhibit_paths,
    expected_cleanup_pathspec_entries,
    expected_pathspec_entries,
    read_pathspec,
    run_git_status,
)


WARNING_RE = re.compile(
    r"(Warning|Undefined|Citation.*undefined|Reference.*undefined|"
    r"There were undefined|Label.*multiply|Fatal|Emergency|Overfull|Underfull)"
)

EXPECTED_PDF_TITLE = (
    "When Does Ability Grouping Improve Learning? "
    "Evidence from Two Experiments in Kenya and Liberia"
)
EXPECTED_PDF_AUTHOR = "Guthrie Gray-Lobe, Mridul Joshi, and Michael Kremer"
DEFAULT_RELEASE_PATHSPEC = DEFAULT_REPO / "PAPER_RELEASE_CANDIDATE_PATHS.txt"
DEFAULT_CLEANUP_PATHSPEC = DEFAULT_REPO / "PAPER_RELEASE_CLEANUP_PATHS.txt"
EXPECTED_PDF_KEYWORD_PARTS = [
    "ability grouping",
    "tracking",
    "diagnostic assessment",
    "peer effects",
    "class size",
    "education in developing countries",
]
EXPECTED_DRAFT_MARKERS = [
    "PRELIMINARY",
    "PLEASE DO NOT CIRCULATE",
]
FORBIDDEN_PDF_TEXT = [
    "TODO",
    "FIXME",
    "TBD",
    "finsamp",
    "sampleconstruction",
    "withingrade",
    "gradelevel",
    "treatmentcontrol",
    "baselinescored",
    "treatmentinteracted",
    "treatmentinduced",
    "schoolclustered",
    "gradedispersion",
    "differentlyinformative",
    "baselineability",
    "classroomlevel",
    "Metaanalyses",
    "gradebased",
]
UNRESOLVED_PDF_PATTERNS = [
    (r"\?\?", "visible unresolved reference marker"),
    (r"\bTable\s+\?", "visible unresolved table reference"),
    (r"\bFigure\s+\?", "visible unresolved figure reference"),
    (r"\bSection\s+\?", "visible unresolved section reference"),
]


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def run_command(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


def normalize_pdf_text(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def check_public_version(overleaf_dir: Path, entrypoint: str) -> CheckResult:
    text = (overleaf_dir / entrypoint).read_text(errors="ignore")
    if r"\publicversiontrue" in text:
        return CheckResult("public version switch", True, r"\publicversiontrue is set")
    if r"\publicversionfalse" in text:
        return CheckResult("public version switch", False, r"\publicversionfalse is still set")
    return CheckResult("public version switch", False, "no public-version switch found")


def check_log(overleaf_dir: Path, entrypoint: str) -> CheckResult:
    log_path = overleaf_dir / Path(entrypoint).with_suffix(".log")
    hits = [
        f"{idx}: {line.strip()}"
        for idx, line in enumerate(log_path.read_text(errors="ignore").splitlines(), start=1)
        if WARNING_RE.search(line)
    ]
    if hits:
        preview = "; ".join(hits[:5])
        return CheckResult("LaTeX warning scan", False, preview)
    return CheckResult("LaTeX warning scan", True, "no warning/error/rerun hits")


def check_artifacts(overleaf_dir: Path, repo_output: Path, entrypoint: str) -> CheckResult:
    refs_by_tex = scan_tex_references(overleaf_dir)
    all_refs = set().union(*refs_by_tex.values()) if refs_by_tex else set()
    entry_refs = refs_by_tex.get(entrypoint, set())
    files = {path.name for path in (overleaf_dir / "stata_output").iterdir() if path.is_file()}

    errors: list[str] = []
    missing_all = sorted(all_refs - files)
    missing_entry = sorted(entry_refs - files)
    if missing_all:
        errors.append(f"missing referenced files: {len(missing_all)}")
    if missing_entry:
        errors.append(f"missing {entrypoint} files: {len(missing_entry)}")

    different = []
    missing_repo = []
    missing_overleaf = []
    for name in sorted(entry_refs):
        repo_path = repo_output / name
        overleaf_path = overleaf_dir / "stata_output" / name
        if not repo_path.exists():
            missing_repo.append(name)
            continue
        if not overleaf_path.exists():
            missing_overleaf.append(name)
            continue
        if sha256(repo_path) != sha256(overleaf_path):
            different.append(name)

    if different:
        errors.append(f"different active files: {len(different)}")
    if missing_repo:
        errors.append(f"missing active files in repo output: {len(missing_repo)}")
    if missing_overleaf:
        errors.append(f"missing active files in Overleaf: {len(missing_overleaf)}")

    if errors:
        return CheckResult("active exhibit sync", False, "; ".join(errors))
    return CheckResult(
        "active exhibit sync",
        True,
        f"{len(entry_refs)} active {entrypoint} exhibits synced; {len(all_refs)} files referenced by retained roots",
    )


def check_labels(overleaf_dir: Path, entrypoint: str) -> CheckResult:
    labels, refs = scan_entrypoint_labels(overleaf_dir, entrypoint)
    label_names = set(labels)
    ref_names = {label for label, _, _ in refs}
    missing_labels = sorted(ref_names - label_names)
    unreferenced_exhibit_labels = sorted(
        label
        for label in (label_names - ref_names)
        if label.startswith(("tab:", "fig:"))
    )
    if missing_labels or unreferenced_exhibit_labels:
        return CheckResult(
            "label/reference integrity",
            False,
            f"missing refs={len(missing_labels)}, unreferenced exhibits={len(unreferenced_exhibit_labels)}",
        )
    return CheckResult(
        "label/reference integrity",
        True,
        f"{len(label_names)} labels, {len(ref_names)} refs, no missing or unreferenced exhibit labels",
    )


def check_freeze_manifest(
    manifest: Path, repo_root: Path, overleaf_dir: Path, repo_output: Path, entrypoint: str
) -> CheckResult:
    rows = parse_hash_rows(manifest)
    errors = []
    errors.extend(verify_hash_rows(rows, repo_root, overleaf_dir, repo_output))
    errors.extend(verify_active_exhibits(rows, overleaf_dir, repo_output, entrypoint))
    if errors:
        return CheckResult("freeze manifest", False, "; ".join(errors[:5]))
    return CheckResult("freeze manifest", True, f"{len(rows)} hash rows match current files")


def check_pdf_metadata(overleaf_dir: Path, entrypoint: str) -> CheckResult:
    pdf_path = overleaf_dir / Path(entrypoint).with_suffix(".pdf")
    result = run_command(["pdfinfo", str(pdf_path)])
    if result.returncode != 0:
        return CheckResult("PDF metadata", False, result.stderr.strip() or "pdfinfo failed")

    info: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        info[key.strip()] = value.strip()

    errors = []
    if info.get("Title") != EXPECTED_PDF_TITLE:
        errors.append("title missing or stale")
    if info.get("Author") != EXPECTED_PDF_AUTHOR:
        errors.append("author missing or stale")
    keywords = info.get("Keywords", "")
    missing_keywords = [part for part in EXPECTED_PDF_KEYWORD_PARTS if part not in keywords]
    if missing_keywords:
        errors.append(f"keywords missing: {', '.join(missing_keywords)}")
    if info.get("Pages") != "66":
        errors.append(f"unexpected page count: {info.get('Pages')}")

    if errors:
        return CheckResult("PDF metadata", False, "; ".join(errors))
    return CheckResult(
        "PDF metadata",
        True,
        f"66 pages; {info.get('File size', 'unknown size')}; title/author/keywords populated",
    )


def nonembedded_pdf_font_lines(pdf_path: Path) -> tuple[list[str], str]:
    result = run_command(["pdffonts", str(pdf_path)])
    if result.returncode != 0:
        return [], result.stderr.strip() or "pdffonts failed"

    lines = []
    for line in result.stdout.splitlines()[2:]:
        parts = [part for part in re.split(r"\s+", line.strip()) if part]
        yes_no_positions = [idx for idx, part in enumerate(parts) if part in {"yes", "no"}]
        if yes_no_positions and parts[yes_no_positions[0]] == "no":
            lines.append(line)
    return lines, ""


def check_pdf_fonts(overleaf_dir: Path, entrypoint: str) -> CheckResult:
    pdf_path = overleaf_dir / Path(entrypoint).with_suffix(".pdf")
    nonembedded, error = nonembedded_pdf_font_lines(pdf_path)
    if error:
        return CheckResult("PDF font embedding", False, error)
    if nonembedded:
        return CheckResult(
            "PDF font embedding",
            False,
            f"{len(nonembedded)} non-embedded font rows; first: {nonembedded[0].strip()}",
        )
    return CheckResult("PDF font embedding", True, "all fonts embedded")


def check_pdf_render(overleaf_dir: Path, entrypoint: str) -> CheckResult:
    script = Path(__file__).with_name("check_pdf_render.py")
    result = run_command(
        [
            sys.executable,
            str(script),
            "--overleaf-dir",
            str(overleaf_dir),
            "--entrypoint",
            entrypoint,
        ]
    )
    if result.returncode == 0:
        detail = result.stdout.strip().removeprefix("[PASS] PDF render smoke test: ")
        return CheckResult("PDF render smoke test", True, detail)

    failed_lines = [
        line
        for line in result.stdout.splitlines()
        if line.startswith("[BLOCK]") or line.startswith("[FAIL]")
    ]
    detail = "; ".join(failed_lines[:3]) or result.stderr.strip() or "PDF render check failed"
    return CheckResult("PDF render smoke test", False, detail)


def check_pdf_text_hygiene(overleaf_dir: Path, entrypoint: str) -> CheckResult:
    tex_text = (overleaf_dir / entrypoint).read_text(errors="ignore")
    draft_mode = r"\publicversionfalse" in tex_text and r"\publicversiontrue" not in tex_text
    public_mode = r"\publicversiontrue" in tex_text

    pdf_path = overleaf_dir / Path(entrypoint).with_suffix(".pdf")
    result = run_command(["pdftotext", str(pdf_path), "-"])
    if result.returncode != 0:
        return CheckResult("PDF text hygiene", False, result.stderr.strip() or "pdftotext failed")

    text = normalize_pdf_text(result.stdout)
    errors: list[str] = []

    for literal in FORBIDDEN_PDF_TEXT:
        if literal in text:
            errors.append(f"forbidden text found: {literal}")
    for pattern, label in UNRESOLVED_PDF_PATTERNS:
        if re.search(pattern, text):
            errors.append(label)

    required_text = [
        "When Does Ability Grouping Improve Learning?",
        "Evidence from Two Experiments in Kenya and Liberia",
        "Guthrie Gray-Lobe",
        "Mridul Joshi",
        "Michael Kremer",
        "Abstract",
        "Keywords:",
        "JEL codes:",
    ]
    required_text.extend(EXPECTED_PDF_KEYWORD_PARTS)
    for literal in required_text:
        if literal not in text:
            errors.append(f"required text missing: {literal}")

    draft_hits = [marker for marker in EXPECTED_DRAFT_MARKERS if marker in text]
    if draft_mode:
        missing_draft_markers = sorted(set(EXPECTED_DRAFT_MARKERS) - set(draft_hits))
        if missing_draft_markers:
            errors.append(f"draft marker missing: {', '.join(missing_draft_markers)}")
    elif public_mode:
        if draft_hits:
            errors.append(f"draft marker present in public mode: {', '.join(draft_hits)}")
    else:
        errors.append("no public-version switch found in source")

    if errors:
        return CheckResult("PDF text hygiene", False, "; ".join(errors[:8]))

    marker_detail = "draft marker present" if draft_mode else "draft marker absent"
    return CheckResult(
        "PDF text hygiene",
        True,
        f"front matter present; no unresolved refs/TODO/code-label artifacts; {marker_detail}",
    )


def check_numeric_claims(overleaf_dir: Path, repo_output: Path, entrypoint: str) -> CheckResult:
    script = Path(__file__).with_name("check_numeric_claims.py")
    result = run_command(
        [
            sys.executable,
            str(script),
            "--overleaf-dir",
            str(overleaf_dir),
            "--repo-output-dir",
            str(repo_output),
            "--entrypoint",
            entrypoint,
        ]
    )
    if result.returncode == 0:
        return CheckResult(
            "numeric prose claims",
            True,
            "central and robustness prose claims align with active generated tables",
        )

    failed_lines = [
        line
        for line in result.stdout.splitlines()
        if line.startswith("[BLOCK]") or line.startswith("[FAIL]")
    ]
    detail = "; ".join(failed_lines[:3]) or result.stderr.strip() or "numeric claim check failed"
    return CheckResult("numeric prose claims", False, detail)


def check_git_clean(repo_root: Path) -> CheckResult:
    result = run_command(["git", "status", "--porcelain"], cwd=repo_root)
    if result.returncode != 0:
        return CheckResult("git worktree", False, result.stderr.strip() or "git status failed")
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if lines:
        return CheckResult("git worktree", False, f"{len(lines)} changed/untracked paths")
    return CheckResult("git worktree", True, "clean")


def check_release_pathspec(
    pathspec: Path,
    repo_root: Path,
    overleaf_dir: Path,
    repo_output: Path,
    entrypoint: str,
) -> CheckResult:
    try:
        actual = read_pathspec(pathspec)
    except FileNotFoundError:
        return CheckResult("release pathspec drift", False, f"{pathspec} does not exist")

    try:
        entries = run_git_status(repo_root)
        active_paths = active_exhibit_paths(overleaf_dir, repo_output, entrypoint)
    except Exception as exc:
        return CheckResult("release pathspec drift", False, str(exc))

    expected = expected_pathspec_entries(entries, active_paths)
    actual_set = set(actual)
    expected_set = set(expected)
    missing = [item for item in expected if item not in actual_set]
    extra = [item for item in actual if item not in expected_set]
    duplicate_count = len(actual) - len(actual_set)

    if missing or extra or duplicate_count:
        pieces = [
            f"expected {len(expected)} paths, found {len(actual)}",
        ]
        if missing:
            pieces.append(f"missing {len(missing)}")
        if extra:
            pieces.append(f"extra {len(extra)}")
        if duplicate_count:
            pieces.append(f"duplicates {duplicate_count}")
        preview = (missing + extra)[:3]
        if preview:
            pieces.append("first drift: " + ", ".join(preview))
        return CheckResult("release pathspec drift", False, "; ".join(pieces))

    return CheckResult("release pathspec drift", True, f"{len(expected)} release-candidate paths match triage")


def check_cleanup_pathspec(
    pathspec: Path,
    repo_root: Path,
    overleaf_dir: Path,
    repo_output: Path,
    entrypoint: str,
) -> CheckResult:
    try:
        actual = read_pathspec(pathspec)
    except FileNotFoundError:
        return CheckResult("cleanup pathspec drift", False, f"{pathspec} does not exist")

    try:
        entries = run_git_status(repo_root)
        active_paths = active_exhibit_paths(overleaf_dir, repo_output, entrypoint)
        expected = expected_cleanup_pathspec_entries(repo_root, entries, active_paths)
    except Exception as exc:
        return CheckResult("cleanup pathspec drift", False, str(exc))

    actual_set = set(actual)
    expected_set = set(expected)
    missing = [item for item in expected if item not in actual_set]
    extra = [item for item in actual if item not in expected_set]
    duplicate_count = len(actual) - len(actual_set)

    if missing or extra or duplicate_count:
        pieces = [
            f"expected {len(expected)} paths, found {len(actual)}",
        ]
        if missing:
            pieces.append(f"missing {len(missing)}")
        if extra:
            pieces.append(f"extra {len(extra)}")
        if duplicate_count:
            pieces.append(f"duplicates {duplicate_count}")
        preview = (missing + extra)[:3]
        if preview:
            pieces.append("first drift: " + ", ".join(preview))
        return CheckResult("cleanup pathspec drift", False, "; ".join(pieces))

    return CheckResult("cleanup pathspec drift", True, f"{len(expected)} cleanup-decision paths match triage")


def tracked_local_artifact_paths(repo_root: Path) -> tuple[list[str], str]:
    tracked = run_command(["git", "ls-files"], cwd=repo_root)
    if tracked.returncode != 0:
        return [], tracked.stderr.strip()

    paths = [
        line.strip()
        for line in tracked.stdout.splitlines()
        if line.strip() and Path(line.strip()).name in {".DS_Store", "Rplots.pdf"}
    ]
    return paths, ""


def porcelain_path(line: str) -> str:
    path = line[3:].strip()
    if " -> " in path:
        path = path.rsplit(" -> ", 1)[-1]
    return path


def check_tracked_local_artifacts(repo_root: Path) -> CheckResult:
    tracked_files, error = tracked_local_artifact_paths(repo_root)
    if error:
        return CheckResult("tracked local artifacts", False, error)
    if not tracked_files:
        return CheckResult("tracked local artifacts", True, "no tracked .DS_Store or Rplots.pdf")

    status = run_command(["git", "status", "--porcelain", "--", *tracked_files], cwd=repo_root)
    if status.returncode != 0:
        return CheckResult("tracked local artifacts", False, status.stderr.strip() or "git status failed")
    modified = [line for line in status.stdout.splitlines() if line.strip()]
    if modified:
        modified_paths = [porcelain_path(line) for line in modified]
        return CheckResult(
            "tracked local artifacts",
            False,
            "tracked local artifacts need release decision: "
            + ", ".join(tracked_files)
            + "; modified now: "
            + ", ".join(modified_paths),
        )
    return CheckResult(
        "tracked local artifacts",
        False,
        "tracked local artifacts should be removed before a clean release: " + ", ".join(tracked_files),
    )


def render_results(results: list[CheckResult]) -> None:
    for result in results:
        status = "PASS" if result.ok else "BLOCK"
        print(f"[{status}] {result.name}: {result.detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--overleaf-dir", type=Path, default=DEFAULT_OVERLEAF)
    parser.add_argument("--repo-output-dir", type=Path, default=DEFAULT_REPO_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--entrypoint", default="main2.tex")
    parser.add_argument("--release-pathspec", type=Path, default=DEFAULT_RELEASE_PATHSPEC)
    parser.add_argument("--cleanup-pathspec", type=Path, default=DEFAULT_CLEANUP_PATHSPEC)
    args = parser.parse_args()

    manuscript_checks = [
        check_log(args.overleaf_dir, args.entrypoint),
        check_artifacts(args.overleaf_dir, args.repo_output_dir, args.entrypoint),
        check_labels(args.overleaf_dir, args.entrypoint),
        check_freeze_manifest(
            args.manifest,
            args.repo_root,
            args.overleaf_dir,
            args.repo_output_dir,
            args.entrypoint,
        ),
        check_pdf_metadata(args.overleaf_dir, args.entrypoint),
        check_pdf_fonts(args.overleaf_dir, args.entrypoint),
        check_pdf_render(args.overleaf_dir, args.entrypoint),
        check_pdf_text_hygiene(args.overleaf_dir, args.entrypoint),
        check_numeric_claims(args.overleaf_dir, args.repo_output_dir, args.entrypoint),
    ]
    release_checks = [
        check_public_version(args.overleaf_dir, args.entrypoint),
        check_git_clean(args.repo_root),
        check_release_pathspec(
            args.release_pathspec,
            args.repo_root,
            args.overleaf_dir,
            args.repo_output_dir,
            args.entrypoint,
        ),
        check_cleanup_pathspec(
            args.cleanup_pathspec,
            args.repo_root,
            args.overleaf_dir,
            args.repo_output_dir,
            args.entrypoint,
        ),
        check_tracked_local_artifacts(args.repo_root),
    ]

    print("Manuscript gates")
    render_results(manuscript_checks)
    print()
    print("Release gates")
    render_results(release_checks)

    all_results = manuscript_checks + release_checks
    if all(result.ok for result in all_results):
        print("\nRelease readiness check passed")
        return 0

    print("\nRelease readiness check blocked")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
