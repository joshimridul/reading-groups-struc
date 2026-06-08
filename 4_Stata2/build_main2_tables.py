#!/usr/bin/env python3

"""
Legacy builder for generated exhibits once consumed by `main2.tex`.

This script does not edit `main2.tex`. Instead it:
1. runs the Stata pipeline in `_master.do`
2. materializes legacy alias tables still referenced by `main2.tex`
3. copies the required table and figure inputs into repo-local `stata_output/`

Environment overrides:
  MAIN2_PATH     full path to main2.tex
  STATA_BIN      full path to the Stata executable
  RSCRIPT_BIN    command/path for Rscript
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STATA_DIR = REPO_ROOT / "4_Stata2"
OUTPUT_DIR = STATA_DIR / "output"
DEFAULT_MAIN2 = Path(
    os.environ.get(
        "MAIN2_PATH",
        str(REPO_ROOT / "archive" / "legacy_root_entrypoints_2026-06-07_ability_migration" / "main2.tex"),
    )
)
DEFAULT_STATA_OUTPUT = REPO_ROOT / "stata_output"

DEFAULT_STATA_CANDIDATES = [
    Path(os.environ["STATA_BIN"]) if "STATA_BIN" in os.environ else None,
    Path("/Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp"),
    Path("/Applications/Stata/StataMP.app/Contents/MacOS/stata-mp"),
]

ALIASES = {
    "tab_balance_1do": {
        "source": OUTPUT_DIR / "legacy_1do" / "Kenya_new" / "baseline_balance_K.tex",
        "label": "tab:balance_1do",
        "caption": r"\caption{\small Baseline Balance}",
    },
    "tab_attrition_1do": {
        "source": OUTPUT_DIR / "legacy_1do" / "attrition.tex",
        "label": "tab:attrition",
        "caption": r"\caption{\small Test Score Follow-up}",
    },
}


def run(cmd: list[str], cwd: Path) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def resolve_stata_bin() -> Path:
    for candidate in DEFAULT_STATA_CANDIDATES:
        if candidate is not None and candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Could not find a Stata executable. Set STATA_BIN or install Stata at a standard path."
    )


def unique_ordered(values: list[str]) -> list[str]:
    seen = set()
    ordered = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def read_active_tex(main2_path: Path) -> str:
    text = main2_path.read_text()
    # Remove LaTeX comments before parsing so commented-out exhibits do not
    # become part of the sync manifest. Escaped percent signs are preserved.
    return "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in text.splitlines())


def parse_main2_table_inputs(main2_path: Path) -> list[str]:
    text = read_active_tex(main2_path)
    stems = re.findall(r"\\input\{stata_output/([^}]+)\}", text)
    if not stems:
        raise RuntimeError(f"No stata_output inputs found in {main2_path}")
    return unique_ordered(stems)


def parse_main2_figure_inputs(main2_path: Path) -> list[str]:
    text = read_active_tex(main2_path)
    figures = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{stata_output/([^}]+)\}", text)
    return unique_ordered(figures)


def normalize_table_text(text: str) -> str:
    text = text.replace(r"\begin{table}[!h]", r"\begin{table}[H]")
    text = text.replace(r"\begin{table}[h]", r"\begin{table}[H]")
    text = text.replace(r"\begin{table}[ht]", r"\begin{table}[H]")
    text = text.replace(r"\begin{table}[tbp]", r"\begin{table}[H]")
    return text


def clean_legacy_balance_text(text: str) -> str:
    """Remove stale joint-test rows from the legacy Kenya/Liberia balance table."""
    lines = []
    for line in text.splitlines():
        if "F-stat of joint test" in line or "P-value" in line:
            continue
        line = line.replace(
            " The joint test specification includes only class size and baseline test score.",
            "",
        )
        lines.append(line)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def materialize_alias(stem: str) -> Path:
    spec = ALIASES[stem]
    src = spec["source"]
    dst = OUTPUT_DIR / f"{stem}.tex"

    if not src.exists():
        raise FileNotFoundError(f"Missing alias source: {src}")

    text = src.read_text()
    if stem == "tab_balance_1do":
        text = clean_legacy_balance_text(text)
    text = text.replace(r"\begin{center}", r"\begin{table}[H]" + "\n" + r"\centering")
    text = text.replace(r"\end{center}", r"\end{table}")
    text = text.replace(r"\clearpage", "")
    text = re.sub(
        r"\\label\{[^}]+\}",
        lambda _: rf"\label{{{spec['label']}}}",
        text,
        count=1,
    )
    text = re.sub(
        r"\\caption\{[^}]+\}",
        lambda _: spec["caption"],
        text,
        count=1,
    )
    text = normalize_table_text(text).strip() + "\n"
    dst.write_text(text)
    return dst


def resolve_output_file(stem: str) -> Path:
    if stem in ALIASES:
        return materialize_alias(stem)

    path = OUTPUT_DIR / f"{stem}.tex"
    if not path.exists():
        raise FileNotFoundError(f"Missing generated table for `{stem}` at {path}")
    return path


def resolve_figure_file(filename: str) -> Path:
    path = OUTPUT_DIR / filename
    if path.exists():
        return path

    if Path(filename).suffix:
        raise FileNotFoundError(f"Missing generated figure for `{filename}` at {path}")

    pdf_path = OUTPUT_DIR / f"{filename}.pdf"
    if pdf_path.exists():
        return pdf_path
    raise FileNotFoundError(f"Missing generated figure for `{filename}` at {path} or {pdf_path}")


def nonembedded_font_lines(pdf_path: Path) -> list[str]:
    result = subprocess.run(
        ["pdffonts", str(pdf_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"pdffonts failed for {pdf_path}")

    lines = []
    for line in result.stdout.splitlines()[2:]:
        parts = [part for part in re.split(r"\s+", line.strip()) if part]
        yes_no_positions = [idx for idx, part in enumerate(parts) if part in {"yes", "no"}]
        if yes_no_positions and parts[yes_no_positions[0]] == "no":
            lines.append(line)
    return lines


def embed_pdf_fonts(pdf_path: Path) -> None:
    before = nonembedded_font_lines(pdf_path)
    if not before:
        return

    gs_bin = shutil.which("gs")
    if gs_bin is None:
        raise FileNotFoundError("Ghostscript `gs` not found; cannot embed figure fonts")

    tmp_path = pdf_path.with_name(f"{pdf_path.stem}.fontembed.tmp.pdf")
    result = subprocess.run(
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
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        if tmp_path.exists():
            tmp_path.unlink()
        raise RuntimeError(result.stderr.strip() or f"Ghostscript failed for {pdf_path}")
    if nonembedded_font_lines(tmp_path):
        tmp_path.unlink()
        raise RuntimeError(f"Non-embedded fonts remain after Ghostscript pass: {pdf_path}")
    tmp_path.replace(pdf_path)


def sync_required_tables(main2_path: Path, target_dir: Path) -> list[Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for stem in parse_main2_table_inputs(main2_path):
        src = resolve_output_file(stem)
        dst = target_dir / src.name
        text = normalize_table_text(src.read_text())
        dst.write_text(text)
        copied.append(dst)
    return copied


def sync_required_figures(main2_path: Path, target_dir: Path) -> list[Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for filename in parse_main2_figure_inputs(main2_path):
        src = resolve_figure_file(filename)
        embed_pdf_fonts(src)
        dst = target_dir / src.name
        shutil.copy2(src, dst)
        copied.append(dst)
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main2", type=Path, default=DEFAULT_MAIN2, help="Path to main2.tex")
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=DEFAULT_STATA_OUTPUT,
        help="Destination for copied table inputs",
    )
    parser.add_argument("--skip-stata", action="store_true", help="Skip `_master.do`")
    parser.add_argument("--no-sync", action="store_true", help="Do not copy exhibits to target dir")
    args = parser.parse_args()

    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not args.skip_stata:
        stata_bin = resolve_stata_bin()
        run([str(stata_bin), "-b", "do", str(STATA_DIR / "_master.do")], cwd=STATA_DIR)
        run([str(stata_bin), "-b", "do", str(STATA_DIR / "07_lesson_completion.do")], cwd=STATA_DIR)

    required_tables = parse_main2_table_inputs(args.main2)
    print("Required tables from main2.tex:")
    for stem in required_tables:
        print("  -", stem)

    required_figures = parse_main2_figure_inputs(args.main2)
    print("Required figures from main2.tex:")
    for filename in required_figures:
        print("  -", filename)

    # Validate or materialize all required files before syncing.
    for stem in required_tables:
        resolve_output_file(stem)
    for filename in required_figures:
        resolve_figure_file(filename)

    if not args.no_sync:
        copied_tables = sync_required_tables(args.main2, args.target_dir)
        copied_figures = sync_required_figures(args.main2, args.target_dir)
        print(
            f"Copied {len(copied_tables)} table files and "
            f"{len(copied_figures)} figure files to {args.target_dir}"
        )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"Command failed with exit code {exc.returncode}", file=sys.stderr)
        raise
    except Exception as exc:  # pragma: no cover
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
