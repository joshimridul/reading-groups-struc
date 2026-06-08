#!/usr/bin/env python3

"""Embed fonts in active `main2.tex` figure PDFs using Ghostscript.

Several plotting backends write PDF figures that reference Helvetica without
embedding it. That is usually readable locally but brittle for journal portals
and circulation. This script post-processes only the figure PDFs actively
included by `main2.tex`; it does not regenerate data, estimates, or TeX.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from audit_overleaf_artifacts import DEFAULT_OVERLEAF
from verify_freeze_manifest import DEFAULT_REPO_OUTPUT


DEFAULT_ENTRYPOINT = "main2.tex"
GHOSTSCRIPT_DEFAULT = shutil.which("gs")


@dataclass
class EmbedResult:
    path: Path
    changed: bool
    ok: bool
    detail: str


def strip_latex_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        kept = []
        for idx, char in enumerate(line):
            if char == "%" and (idx == 0 or line[idx - 1] != "\\"):
                break
            kept.append(char)
        lines.append("".join(kept))
    return "\n".join(lines)


def active_figure_names(overleaf_dir: Path, entrypoint: str) -> list[str]:
    text = strip_latex_comments((overleaf_dir / entrypoint).read_text(errors="ignore"))
    names = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{stata_output/([^}]+)\}", text)
    seen: set[str] = set()
    ordered = []
    for name in names:
        filename = name if Path(name).suffix else f"{name}.pdf"
        if filename not in seen:
            seen.add(filename)
            ordered.append(filename)
    return ordered


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False)


def nonembedded_font_lines(pdf_path: Path) -> list[str]:
    result = run_command(["pdffonts", str(pdf_path)])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"pdffonts failed for {pdf_path}")

    lines = []
    for line in result.stdout.splitlines()[2:]:
        parts = [part for part in re.split(r"\s+", line.strip()) if part]
        if not parts:
            continue
        yes_no_positions = [idx for idx, part in enumerate(parts) if part in {"yes", "no"}]
        if not yes_no_positions:
            continue
        embedded = parts[yes_no_positions[0]]
        if embedded == "no":
            lines.append(line)
    return lines


def embed_fonts(pdf_path: Path, gs_bin: str, dry_run: bool) -> EmbedResult:
    before = nonembedded_font_lines(pdf_path)
    if not before:
        return EmbedResult(pdf_path, False, True, "all fonts already embedded")
    if dry_run:
        return EmbedResult(pdf_path, False, False, f"{len(before)} non-embedded font rows")

    tmp_path = pdf_path.with_name(f"{pdf_path.stem}.fontembed.tmp.pdf")
    result = run_command(
        [
            gs_bin,
            "-q",
            "-dNOPAUSE",
            "-dBATCH",
            "-dSAFER",
            "-sDEVICE=pdfwrite",
            "-dPDFSETTINGS=/prepress",
            "-dCompatibilityLevel=1.5",
            "-dEmbedAllFonts=true",
            "-dSubsetFonts=true",
            "-dCompressFonts=true",
            f"-sOutputFile={tmp_path}",
            str(pdf_path),
        ]
    )
    if result.returncode != 0:
        if tmp_path.exists():
            tmp_path.unlink()
        return EmbedResult(pdf_path, False, False, result.stderr.strip() or "Ghostscript failed")

    after = nonembedded_font_lines(tmp_path)
    if after:
        tmp_path.unlink()
        return EmbedResult(pdf_path, False, False, f"{len(after)} non-embedded font rows remain")

    tmp_path.replace(pdf_path)
    return EmbedResult(pdf_path, True, True, f"embedded {len(before)} previously non-embedded font rows")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overleaf-dir", type=Path, default=DEFAULT_OVERLEAF)
    parser.add_argument("--entrypoint", default=DEFAULT_ENTRYPOINT)
    parser.add_argument("--repo-output-dir", type=Path, default=DEFAULT_REPO_OUTPUT)
    parser.add_argument("--gs-bin", default=GHOSTSCRIPT_DEFAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.gs_bin:
        raise FileNotFoundError("Ghostscript `gs` not found on PATH")

    figures = active_figure_names(args.overleaf_dir, args.entrypoint)
    results = []
    for filename in figures:
        path = args.repo_output_dir / filename
        if not path.exists():
            results.append(EmbedResult(path, False, False, "missing active figure"))
            continue
        results.append(embed_fonts(path, args.gs_bin, args.dry_run))

    changed = 0
    for result in results:
        status = "PASS" if result.ok else "BLOCK"
        changed += int(result.changed)
        print(f"[{status}] {result.path.name}: {result.detail}")

    if all(result.ok for result in results):
        action = "would change" if args.dry_run else "changed"
        print(f"\nFigure font embedding passed; {action} {changed} of {len(results)} active figures")
        return 0

    print("\nFigure font embedding failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
