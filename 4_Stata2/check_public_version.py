#!/usr/bin/env python3

"""Build and verify a public-version dry run of the canonical manuscript.

The current three-country manuscript has no draft/public switch. For older
manuscripts that still use one, this script flips the switch only in a temp
copy. It then builds the temp copy and runs the same manuscript checks used by
the release-readiness wrapper plus a PDF text scan for draft markers and
unresolved references.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from check_release_readiness import (
    EXPECTED_PDF_AUTHOR,
    EXPECTED_PDF_KEYWORD_PARTS,
    EXPECTED_PAGES,
    EXPECTED_PDF_TITLE,
    WARNING_RE,
    CheckResult,
    check_artifacts,
    check_labels,
    check_pdf_fonts,
    check_log,
    check_pdf_metadata,
    render_results,
)
from check_pdf_render import check_rendered_pdf
from verify_freeze_manifest import DEFAULT_OVERLEAF, DEFAULT_REPO_OUTPUT


PUBLIC_SWITCH_FALSE = r"\publicversionfalse"
PUBLIC_SWITCH_TRUE = r"\publicversiontrue"
DEFAULT_ENTRYPOINT = "main_3country_new.structural_edit.tex"


@dataclass
class DryRunPaths:
    temp_dir: Path
    entrypoint: Path
    pdf: Path
    log: Path


def run_command(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


def today_latex_date() -> str:
    now = datetime.now()
    return f"{now.strftime('%B')} {now.day}, {now.year}"


def make_temp_copy(overleaf_dir: Path, temp_parent: Path, prefix: str, entrypoint: str) -> DryRunPaths:
    overleaf_dir = overleaf_dir.resolve()
    if not overleaf_dir.exists():
        raise FileNotFoundError(f"Missing Overleaf directory: {overleaf_dir}")

    temp_dir = Path(tempfile.mkdtemp(prefix=prefix, dir=temp_parent))
    target = temp_dir / overleaf_dir.name
    shutil.copytree(overleaf_dir, target)

    entrypoint_path = target / entrypoint
    if not entrypoint_path.exists():
        raise FileNotFoundError(f"Missing entrypoint in temp copy: {entrypoint_path}")

    return DryRunPaths(
        temp_dir=target,
        entrypoint=entrypoint_path,
        pdf=target / Path(entrypoint).with_suffix(".pdf"),
        log=target / Path(entrypoint).with_suffix(".log"),
    )


def flip_public_switch(entrypoint: Path) -> CheckResult:
    text = entrypoint.read_text()
    false_count = text.count(PUBLIC_SWITCH_FALSE)
    true_count = text.count(PUBLIC_SWITCH_TRUE)

    if false_count == 1:
        entrypoint.write_text(text.replace(PUBLIC_SWITCH_FALSE, PUBLIC_SWITCH_TRUE, 1))
        return CheckResult("temp public-version switch", True, "flipped draft switch in temp copy only")
    if false_count > 1:
        return CheckResult(
            "temp public-version switch",
            False,
            f"found {false_count} draft switches; refusing ambiguous temp edit",
        )
    if true_count >= 1:
        return CheckResult(
            "temp public-version switch",
            True,
            "temp copy already has public-version switch set",
        )
    if "PRELIMINARY" in text or "PLEASE DO NOT CIRCULATE" in text:
        return CheckResult("temp public-version switch", False, "no switch found, but draft markers remain")
    return CheckResult("temp public-version switch", True, "no switch found; temp copy has no draft markers")


def build_latex(paths: DryRunPaths, entrypoint: str) -> CheckResult:
    result = run_command(
        ["latexmk", "-g", "-pdf", "-interaction=nonstopmode", "-halt-on-error", entrypoint],
        cwd=paths.temp_dir,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        stdout_tail = "\n".join(result.stdout.splitlines()[-20:])
        detail = stderr or stdout_tail or "latexmk failed"
        return CheckResult("public temp build", False, detail)
    if not paths.pdf.exists():
        return CheckResult("public temp build", False, f"missing PDF after build: {paths.pdf}")
    return CheckResult(
        "public temp build",
        True,
        f"{paths.pdf.name} built in temp copy ({paths.pdf.stat().st_size:,} bytes)",
    )


def pdfinfo_dict(pdf_path: Path) -> tuple[dict[str, str], str]:
    result = run_command(["pdfinfo", str(pdf_path)])
    if result.returncode != 0:
        return {}, result.stderr.strip() or "pdfinfo failed"

    info: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        info[key.strip()] = value.strip()
    return info, ""


def extract_pdf_text(pdf_path: Path) -> tuple[str, str]:
    result = run_command(["pdftotext", str(pdf_path), "-"])
    if result.returncode != 0:
        return "", result.stderr.strip() or "pdftotext failed"
    return result.stdout, ""


def normalize_pdf_text(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def check_pdf_text(pdf_path: Path, expected_date: str) -> CheckResult:
    text, error = extract_pdf_text(pdf_path)
    if error:
        return CheckResult("PDF text scan", False, error)
    normalized = normalize_pdf_text(text)

    forbidden_literals = [
        "PRELIMINARY",
        "PLEASE DO NOT CIRCULATE",
        "finsamp",
        "TODO",
        "FIXME",
        "TBD",
    ]
    missing_literals = [
        "Why Sorting Students Is Not Enough",
        "Evidence from Three Ability-Grouping Experiments",
        "Guthrie Gray-Lobe",
        "Mridul Joshi",
        "Michael Kremer",
        expected_date,
        "Abstract",
        "Keywords:",
        "JEL Codes:",
    ]
    unresolved_patterns = [
        (r"\?\?", "visible unresolved reference marker"),
        (r"\bTable\s+\?", "visible unresolved table reference"),
        (r"\bFigure\s+\?", "visible unresolved figure reference"),
        (r"\bSection\s+\?", "visible unresolved section reference"),
    ]

    errors: list[str] = []
    for literal in forbidden_literals:
        if literal in normalized:
            errors.append(f"forbidden text found: {literal}")
    for literal in missing_literals:
        if literal not in normalized:
            errors.append(f"required text missing: {literal}")
    for pattern, label in unresolved_patterns:
        if re.search(pattern, normalized):
            errors.append(label)

    if errors:
        return CheckResult("PDF text scan", False, "; ".join(errors[:8]))
    return CheckResult(
        "PDF text scan",
        True,
        "front matter present; no draft markers, TODOs, code labels, or unresolved refs",
    )


def check_pdf_summary(pdf_path: Path) -> CheckResult:
    info, error = pdfinfo_dict(pdf_path)
    if error:
        return CheckResult("public PDF summary", False, error)
    pages = info.get("Pages", "unknown")
    size = info.get("File size", f"{pdf_path.stat().st_size:,} bytes")
    version = info.get("PDF version", "unknown PDF version")
    title = info.get("Title", "")
    author = info.get("Author", "")
    if title != EXPECTED_PDF_TITLE or author != EXPECTED_PDF_AUTHOR:
        return CheckResult("public PDF summary", False, "title or author metadata mismatch")
    return CheckResult("public PDF summary", True, f"{pages} pages; {size}; PDF version {version}")


def check_public_pdf_render(pdf_path: Path) -> CheckResult:
    ok, detail = check_rendered_pdf(pdf_path, expected_pages=int(EXPECTED_PAGES))
    return CheckResult("public PDF render smoke test", ok, detail)


def cleanup_auxiliary_logs(paths: DryRunPaths) -> None:
    """Leave the temp PDF inspectable without hiding build evidence."""
    # Intentionally no cleanup: the whole temp Overleaf copy is the audit trail.
    _ = paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overleaf-dir", type=Path, default=DEFAULT_OVERLEAF)
    parser.add_argument("--repo-output-dir", type=Path, default=DEFAULT_REPO_OUTPUT)
    parser.add_argument("--entrypoint", default=DEFAULT_ENTRYPOINT)
    parser.add_argument("--temp-parent", type=Path, default=Path("/private/tmp"))
    parser.add_argument("--temp-prefix", default="rg_threecountry_public.")
    parser.add_argument("--expected-date", default=today_latex_date())
    args = parser.parse_args()

    paths = make_temp_copy(args.overleaf_dir, args.temp_parent, args.temp_prefix, args.entrypoint)

    results: list[CheckResult] = []
    switch_result = flip_public_switch(paths.entrypoint)
    results.append(switch_result)
    if switch_result.ok:
        build_result = build_latex(paths, args.entrypoint)
        results.append(build_result)
    else:
        build_result = CheckResult("public temp build", False, "skipped because public switch failed")
        results.append(build_result)

    if build_result.ok:
        results.extend(
            [
                check_log(paths.temp_dir, args.entrypoint),
                check_artifacts(paths.temp_dir, args.repo_output_dir, args.entrypoint),
                check_labels(paths.temp_dir, args.entrypoint),
                check_pdf_metadata(paths.temp_dir, args.entrypoint),
                check_pdf_fonts(paths.temp_dir, args.entrypoint),
                check_public_pdf_render(paths.pdf),
                check_pdf_text(paths.pdf, args.expected_date),
                check_pdf_summary(paths.pdf),
            ]
        )

    cleanup_auxiliary_logs(paths)

    print("Public-version dry run")
    print(f"Live Overleaf source: {args.overleaf_dir}")
    print(f"Temp Overleaf copy: {paths.temp_dir}")
    print(f"Temp PDF: {paths.pdf}")
    print()
    render_results(results)

    if all(result.ok for result in results):
        print("\nPublic-version dry run passed")
        print("No live Overleaf files were modified.")
        return 0

    print("\nPublic-version dry run failed")
    print("No live Overleaf files were modified.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
