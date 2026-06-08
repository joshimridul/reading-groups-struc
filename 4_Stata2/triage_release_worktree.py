#!/usr/bin/env python3

"""Classify current worktree changes for final paper-release cleanup.

This is a read-only helper. It does not decide what to keep, commit, restore, or
remove; it turns the large `git status --short` list into release-review buckets
so the final cleanup can be deliberate.
"""

from __future__ import annotations

import argparse
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from audit_overleaf_artifacts import DEFAULT_OVERLEAF, scan_tex_references


DEFAULT_REPO = Path("/Users/mriduljoshi/Github/AbilityGrouping")
DEFAULT_REPO_OUTPUT = DEFAULT_REPO / "4_Stata2" / "output"
DEFAULT_ENTRYPOINT = "main2.tex"
LOCAL_ARTIFACT_NAMES = {".DS_Store", "Rplots.pdf"}


@dataclass(frozen=True)
class StatusEntry:
    status: str
    path: str


CATEGORY_ORDER = [
    "release_guardrails_and_docs",
    "canonical_pipeline_code",
    "active_canonical_outputs",
    "inactive_generated_outputs",
    "supplemental_diagnostics_not_active",
    "nigeria_or_three_country_extension",
    "structural_python_extension",
    "legacy_or_old_pipeline",
    "local_artifacts_or_metadata",
    "deleted_or_removed",
    "other",
]


def run_git_status(repo_root: Path) -> list[StatusEntry]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git status failed")

    entries: list[StatusEntry] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        status = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        entries.append(StatusEntry(status=status, path=path))
    return entries


def run_git_ls_files(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git ls-files failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def tracked_clean_local_artifact_entries(repo_root: Path, entries: list[StatusEntry]) -> list[StatusEntry]:
    status_paths = {entry.path for entry in entries}
    tracked_paths = [
        path
        for path in run_git_ls_files(repo_root)
        if Path(path).name in LOCAL_ARTIFACT_NAMES and path not in status_paths
    ]
    return [StatusEntry(status="tracked", path=path) for path in tracked_paths]


def active_exhibit_paths(overleaf_dir: Path, repo_output: Path, entrypoint: str) -> set[str]:
    refs = scan_tex_references(overleaf_dir).get(entrypoint, set())
    return {str(repo_output / name) for name in refs} | {f"4_Stata2/output/{name}" for name in refs}


def is_generated_output(path: str) -> bool:
    return path.startswith("4_Stata2/output/")


def is_active_canonical_output(path: str, active_paths: set[str]) -> bool:
    if not path.startswith("4_Stata2/output/"):
        return False
    return path in active_paths or str(DEFAULT_REPO / path) in active_paths


def classify(entry: StatusEntry, active_paths: set[str]) -> str:
    path = entry.path
    name = Path(path).name

    if entry.status.strip().startswith("D"):
        return "deleted_or_removed"
    if "nigeria" in path.lower() or "/tab_ng_" in path or "/tab_pooled_" in path or "pooled_" in name:
        return "nigeria_or_three_country_extension"
    if path == "STRUCTURAL_RESULTS_NOTE.md" or (
        path.startswith("3_Python/") and "structural" in path.lower()
    ):
        return "structural_python_extension"
    if name in {"04b_peer_diagnostics.do", "04c_assignment_channel_tests.do"}:
        return "supplemental_diagnostics_not_active"
    if name in LOCAL_ARTIFACT_NAMES or path.endswith("/.DS_Store"):
        return "local_artifacts_or_metadata"
    if path in {
        ".gitignore",
        "README.md",
        "PAPER_COMPLETION_AUDIT.md",
        "PAPER_FINAL_READINESS.md",
        "PAPER_RELEASE_CANDIDATE_PATHS.txt",
        "PAPER_RELEASE_CLEANUP_PATHS.txt",
        "PAPER_RELEASE_WORKTREE_TRIAGE.md",
        "PAPER_REPRODUCIBILITY_FREEZE.md",
        "OVERLEAF_ARCHIVE_PLAN.md",
        "OVERLEAF_FOLDER_MAP.md",
    }:
        return "release_guardrails_and_docs"
    if path.startswith("4_Stata2/") and name in {
        "README.md",
        "build_main2_tables.py",
        "audit_overleaf_artifacts.py",
        "verify_freeze_manifest.py",
        "check_release_readiness.py",
        "check_public_version.py",
        "check_numeric_claims.py",
        "check_pdf_render.py",
        "embed_active_figure_fonts.py",
        "triage_release_worktree.py",
    }:
        return "release_guardrails_and_docs"
    if is_active_canonical_output(path, active_paths):
        return "active_canonical_outputs"
    if is_generated_output(path):
        return "inactive_generated_outputs"
    if path.startswith("3_Python/") and name not in {"00_clean_kenya.py"}:
        return "structural_python_extension"
    if path.startswith("1_Do/") or "/legacy_1do/" in path:
        return "legacy_or_old_pipeline"
    if path.startswith("4_Stata2/") and name.endswith((".do", ".R")):
        return "canonical_pipeline_code"
    if path == "3_Python/00_clean_kenya.py":
        return "canonical_pipeline_code"
    return "other"


def group_entries(entries: list[StatusEntry], active_paths: set[str]) -> dict[str, list[StatusEntry]]:
    buckets: dict[str, list[StatusEntry]] = defaultdict(list)
    for entry in entries:
        buckets[classify(entry, active_paths)].append(entry)
    return buckets


def render(entries: list[StatusEntry], active_paths: set[str], max_paths: int) -> None:
    buckets = group_entries(entries, active_paths)

    print("Release worktree triage")
    print(f"Changed/untracked paths: {len(entries)}")
    print()

    for category in CATEGORY_ORDER:
        items = buckets.get(category, [])
        if not items:
            continue
        print(f"{category}: {len(items)}")
        for item in items[:max_paths]:
            print(f"  {item.status} {item.path}")
        if len(items) > max_paths:
            print(f"  ... {len(items) - max_paths} more")
        print()

    unknown_categories = sorted(set(buckets) - set(CATEGORY_ORDER))
    for category in unknown_categories:
        items = buckets[category]
        print(f"{category}: {len(items)}")
        for item in items[:max_paths]:
            print(f"  {item.status} {item.path}")
        if len(items) > max_paths:
            print(f"  ... {len(items) - max_paths} more")
        print()

    print("Suggested release-review order:")
    print("  1. Decide public/draft mode and coauthor approval.")
    print("  2. Stage release guardrails/docs and canonical pipeline/output changes that support main2.tex.")
    print("  3. Keep Nigeria/three-country, structural-extension, supplemental-diagnostic, inactive-output, and legacy work separate from the Kenya/Liberia release unless scope changes.")
    print("  4. Decide whether tracked local artifacts such as .DS_Store and Rplots.pdf should be removed or restored before tagging.")


def format_status_entries(items: list[StatusEntry]) -> list[str]:
    return [f"- `{item.status} {item.path}`" for item in items]


def release_candidate_entries(buckets: dict[str, list[StatusEntry]]) -> list[StatusEntry]:
    return (
        buckets.get("release_guardrails_and_docs", [])
        + buckets.get("canonical_pipeline_code", [])
        + buckets.get("active_canonical_outputs", [])
    )


def separate_work_entries(buckets: dict[str, list[StatusEntry]]) -> list[StatusEntry]:
    return (
        buckets.get("nigeria_or_three_country_extension", [])
        + buckets.get("structural_python_extension", [])
        + buckets.get("supplemental_diagnostics_not_active", [])
        + buckets.get("inactive_generated_outputs", [])
        + buckets.get("legacy_or_old_pipeline", [])
    )


def cleanup_decision_entries(buckets: dict[str, list[StatusEntry]]) -> list[StatusEntry]:
    return (
        buckets.get("local_artifacts_or_metadata", [])
        + buckets.get("deleted_or_removed", [])
        + buckets.get("other", [])
    )


def cleanup_review_entries(
    repo_root: Path, entries: list[StatusEntry], buckets: dict[str, list[StatusEntry]]
) -> list[StatusEntry]:
    return cleanup_decision_entries(buckets) + tracked_clean_local_artifact_entries(repo_root, entries)


def write_markdown_plan(path: Path, repo_root: Path, entries: list[StatusEntry], active_paths: set[str]) -> None:
    buckets = group_entries(entries, active_paths)
    release_candidate = release_candidate_entries(buckets)
    separate_work = separate_work_entries(buckets)
    needs_decision = cleanup_review_entries(repo_root, entries, buckets)

    lines = [
        "# Paper release worktree triage",
        "",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "This read-only triage separates the dirty worktree into release-review buckets for the canonical Kenya/Liberia paper. It does not stage, restore, remove, or commit files.",
        "",
        "If `PAPER_RELEASE_CANDIDATE_PATHS.txt` or `PAPER_RELEASE_CLEANUP_PATHS.txt` exists, treat it as review input for a future staging/cleanup pass, not as an instruction to stage or remove blindly.",
        "",
        "## Summary",
        "",
        f"- Changed/untracked paths: {len(entries)}",
        f"- Release-candidate review set: {len(release_candidate)} paths",
        f"- Separate extension/legacy/generated review set: {len(separate_work)} paths",
        f"- Explicit cleanup decisions: {len(needs_decision)} paths",
        "",
        "## Recommended Release Order",
        "",
        "1. Decide whether the live manuscript should remain draft or be switched to public mode.",
        "2. Review the release-candidate set below: guardrails/docs, canonical Kenya/Liberia pipeline code, and active `main2.tex` outputs.",
        "3. Keep Nigeria, three-country, structural-extension, supplemental-diagnostic, inactive-output, and legacy work out of the Kenya/Liberia release unless the paper scope changes.",
        "4. Resolve local metadata and deleted-file decisions before tagging or committing a final release.",
        "",
        "## Release-Candidate Review Set",
        "",
        "These paths are the plausible Kenya/Liberia paper release set. They still require human review before staging because the worktree contains many related changes.",
        "",
    ]
    lines.extend(format_status_entries(release_candidate) or ["- None"])
    lines.extend(
        [
            "",
            "## Keep Separate Unless Scope Changes",
            "",
            "These paths belong to Nigeria, three-country, structural, supplemental-diagnostic, inactive generated-output, or legacy work. They should not be mixed into a clean Kenya/Liberia release without an explicit scope decision.",
            "",
        ]
    )
    lines.extend(format_status_entries(separate_work) or ["- None"])
    lines.extend(
        [
            "",
            "## Explicit Cleanup Decisions",
            "",
            "These paths need an explicit remove, restore, keep, or ignore decision before a clean release. The list includes tracked local artifacts even when they are not currently modified.",
            "",
        ]
    )
    lines.extend(format_status_entries(needs_decision) or ["- None"])
    lines.extend([""])
    path.write_text("\n".join(lines))


def write_pathspec(path: Path, entries: list[StatusEntry], active_paths: set[str]) -> None:
    buckets = group_entries(entries, active_paths)
    release_candidate = release_candidate_entries(buckets)
    lines = [
        "# Review-only pathspec for the plausible Kenya/Liberia release set.",
        "# Generated by 4_Stata2/triage_release_worktree.py.",
        "# Do not stage this list blindly; review PAPER_RELEASE_WORKTREE_TRIAGE.md first.",
        "#",
    ]
    lines.extend(item.path for item in release_candidate)
    lines.append("")
    path.write_text("\n".join(lines))


def write_cleanup_pathspec(path: Path, repo_root: Path, entries: list[StatusEntry], active_paths: set[str]) -> None:
    buckets = group_entries(entries, active_paths)
    needs_decision = cleanup_review_entries(repo_root, entries, buckets)
    lines = [
        "# Review-only pathspec for release cleanup decisions.",
        "# Generated by 4_Stata2/triage_release_worktree.py.",
        "# Do not remove, restore, or stage this list blindly; review PAPER_RELEASE_WORKTREE_TRIAGE.md first.",
        "#",
    ]
    lines.extend(item.path for item in needs_decision)
    lines.append("")
    path.write_text("\n".join(lines))


def expected_pathspec_entries(entries: list[StatusEntry], active_paths: set[str]) -> list[str]:
    buckets = group_entries(entries, active_paths)
    return [item.path for item in release_candidate_entries(buckets)]


def expected_cleanup_pathspec_entries(
    repo_root: Path, entries: list[StatusEntry], active_paths: set[str]
) -> list[str]:
    buckets = group_entries(entries, active_paths)
    return [item.path for item in cleanup_review_entries(repo_root, entries, buckets)]


def read_pathspec(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(path)
    return [
        line.strip()
        for line in path.read_text(errors="ignore").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def check_pathspec(path: Path, entries: list[StatusEntry], active_paths: set[str]) -> bool:
    return check_expected_pathspec(
        path=path,
        expected=expected_pathspec_entries(entries, active_paths),
        label="release-candidate",
    )


def check_cleanup_pathspec(
    path: Path, repo_root: Path, entries: list[StatusEntry], active_paths: set[str]
) -> bool:
    return check_expected_pathspec(
        path=path,
        expected=expected_cleanup_pathspec_entries(repo_root, entries, active_paths),
        label="cleanup-decision",
    )


def check_expected_pathspec(path: Path, expected: list[str], label: str) -> bool:
    try:
        actual = read_pathspec(path)
    except FileNotFoundError:
        print(f"BLOCK pathspec drift check: {path} does not exist")
        return False

    actual_set = set(actual)
    expected_set = set(expected)
    missing = [item for item in expected if item not in actual_set]
    extra = [item for item in actual if item not in expected_set]
    duplicate_count = len(actual) - len(actual_set)

    if missing or extra or duplicate_count:
        print(f"BLOCK pathspec drift check: {path}")
        print(f"  expected {label} paths: {len(expected)}")
        print(f"  pathspec paths: {len(actual)}")
        if missing:
            print(f"  missing from pathspec: {len(missing)}")
            for item in missing[:10]:
                print(f"    {item}")
        if extra:
            print(f"  extra in pathspec: {len(extra)}")
            for item in extra[:10]:
                print(f"    {item}")
        if duplicate_count:
            print(f"  duplicate pathspec rows: {duplicate_count}")
        return False

    print(f"PASS pathspec drift check: {path} ({len(expected)} {label} paths)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--overleaf-dir", type=Path, default=DEFAULT_OVERLEAF)
    parser.add_argument("--repo-output-dir", type=Path, default=DEFAULT_REPO_OUTPUT)
    parser.add_argument("--entrypoint", default=DEFAULT_ENTRYPOINT)
    parser.add_argument("--max-paths", type=int, default=12)
    parser.add_argument(
        "--write-markdown",
        type=Path,
        help="Optional path for a durable markdown triage plan. The file is overwritten.",
    )
    parser.add_argument(
        "--write-pathspec",
        type=Path,
        help="Optional path for a review-only newline-delimited release-candidate path list.",
    )
    parser.add_argument(
        "--write-cleanup-pathspec",
        type=Path,
        help="Optional path for a review-only newline-delimited cleanup-decision path list.",
    )
    parser.add_argument(
        "--check-pathspec",
        type=Path,
        help="Optional existing pathspec to compare against the current release-candidate set.",
    )
    parser.add_argument(
        "--check-cleanup-pathspec",
        type=Path,
        help="Optional existing pathspec to compare against the current cleanup-decision set.",
    )
    args = parser.parse_args()

    entries = run_git_status(args.repo_root)
    active_paths = active_exhibit_paths(args.overleaf_dir, args.repo_output_dir, args.entrypoint)
    render(entries, active_paths=active_paths, max_paths=args.max_paths)
    if args.write_markdown:
        write_markdown_plan(
            args.write_markdown,
            repo_root=args.repo_root,
            entries=entries,
            active_paths=active_paths,
        )
        print()
        print(f"Wrote markdown triage plan: {args.write_markdown}")
    if args.write_pathspec:
        write_pathspec(args.write_pathspec, entries=entries, active_paths=active_paths)
        print(f"Wrote review-only release pathspec: {args.write_pathspec}")
    if args.write_cleanup_pathspec:
        write_cleanup_pathspec(
            args.write_cleanup_pathspec,
            repo_root=args.repo_root,
            entries=entries,
            active_paths=active_paths,
        )
        print(f"Wrote review-only cleanup pathspec: {args.write_cleanup_pathspec}")
    if args.check_pathspec:
        entries = run_git_status(args.repo_root)
        active_paths = active_exhibit_paths(args.overleaf_dir, args.repo_output_dir, args.entrypoint)
        if not check_pathspec(args.check_pathspec, entries=entries, active_paths=active_paths):
            return 1
    if args.check_cleanup_pathspec:
        entries = run_git_status(args.repo_root)
        active_paths = active_exhibit_paths(args.overleaf_dir, args.repo_output_dir, args.entrypoint)
        if not check_cleanup_pathspec(
            args.check_cleanup_pathspec,
            repo_root=args.repo_root,
            entries=entries,
            active_paths=active_paths,
        ):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
