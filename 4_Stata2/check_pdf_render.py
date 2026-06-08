#!/usr/bin/env python3

"""Render the canonical manuscript PDF and check for page-level failures.

This catches a portability class that LaTeX logs, `pdfinfo`, and text extraction
do not: PDFs that exist and have metadata but contain a blank or malformed page
when rendered. The check is intentionally coarse and stable. It renders each
page at low resolution, verifies the expected page count and uniform page size,
and requires a small amount of non-white ink on every page.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from audit_overleaf_artifacts import DEFAULT_OVERLEAF


DEFAULT_ENTRYPOINT = "main2.tex"
DEFAULT_EXPECTED_PAGES = 66
DEFAULT_DPI = 45
DEFAULT_MIN_INK_COVERAGE = 0.003
INK_THRESHOLD = 245
BLACK_THRESHOLD = 180


@dataclass
class RenderPage:
    page: int
    width: int
    height: int
    ink_coverage: float
    black_coverage: float
    bbox: tuple[int, int, int, int] | None


def run_command(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


def pdfinfo_pages(pdf_path: Path) -> tuple[int | None, str]:
    result = run_command(["pdfinfo", str(pdf_path)])
    if result.returncode != 0:
        return None, result.stderr.strip() or "pdfinfo failed"

    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            _, value = line.split(":", 1)
            try:
                return int(value.strip()), ""
            except ValueError:
                return None, f"could not parse page count from pdfinfo line: {line}"
    return None, "pdfinfo output did not include a page count"


def rendered_page_number(path: Path) -> int:
    match = re.search(r"-(\d+)$", path.stem)
    if not match:
        raise ValueError(f"could not parse rendered page number from {path.name}")
    return int(match.group(1))


def render_pdf(pdf_path: Path, dpi: int, temp_parent: Path) -> tuple[list[Path], str]:
    if shutil.which("pdftoppm") is None:
        return [], "pdftoppm is not available"

    temp_dir = Path(tempfile.mkdtemp(prefix="rg_pdf_render.", dir=temp_parent))
    prefix = temp_dir / "page"
    result = run_command(["pdftoppm", "-r", str(dpi), "-gray", "-png", str(pdf_path), str(prefix)])
    if result.returncode != 0:
        return [], result.stderr.strip() or "pdftoppm failed"

    pages = sorted(temp_dir.glob("page-*.png"), key=rendered_page_number)
    if not pages:
        return [], f"pdftoppm rendered no pages in {temp_dir}"
    return pages, ""


def inspect_rendered_page(path: Path) -> RenderPage:
    from PIL import Image

    page = rendered_page_number(path)
    image = Image.open(path).convert("L")
    width, height = image.size
    histogram = image.histogram()
    total = width * height
    ink_pixels = sum(histogram[:INK_THRESHOLD])
    black_pixels = sum(histogram[:BLACK_THRESHOLD])
    mask = image.point(lambda value: 0 if value >= INK_THRESHOLD else 255)

    return RenderPage(
        page=page,
        width=width,
        height=height,
        ink_coverage=ink_pixels / total,
        black_coverage=black_pixels / total,
        bbox=mask.getbbox(),
    )


def check_rendered_pdf(
    pdf_path: Path,
    expected_pages: int = DEFAULT_EXPECTED_PAGES,
    dpi: int = DEFAULT_DPI,
    min_ink_coverage: float = DEFAULT_MIN_INK_COVERAGE,
    temp_parent: Path = Path("/private/tmp"),
) -> tuple[bool, str]:
    if not pdf_path.exists():
        return False, f"missing PDF: {pdf_path}"

    page_count, page_count_error = pdfinfo_pages(pdf_path)
    if page_count_error:
        return False, page_count_error
    if expected_pages and page_count != expected_pages:
        return False, f"unexpected page count: {page_count}, expected {expected_pages}"

    rendered_paths, render_error = render_pdf(pdf_path, dpi, temp_parent)
    if render_error:
        return False, render_error
    if page_count is not None and len(rendered_paths) != page_count:
        return False, f"rendered {len(rendered_paths)} pages, but pdfinfo reports {page_count}"

    pages = [inspect_rendered_page(path) for path in rendered_paths]
    dimensions = {(page.width, page.height) for page in pages}
    if len(dimensions) != 1:
        formatted = ", ".join(f"{width}x{height}" for width, height in sorted(dimensions))
        return False, f"inconsistent rendered page dimensions: {formatted}"

    blankish = [page for page in pages if page.bbox is None or page.ink_coverage < min_ink_coverage]
    if blankish:
        first = blankish[0]
        return (
            False,
            f"{len(blankish)} page(s) below ink threshold; "
            f"first page {first.page} has {first.ink_coverage:.3%} ink coverage",
        )

    min_page = min(pages, key=lambda page: page.ink_coverage)
    max_page = max(pages, key=lambda page: page.ink_coverage)
    width, height = next(iter(dimensions))
    return (
        True,
        f"{len(pages)} pages render at {dpi} DPI; dimensions {width}x{height}; "
        f"ink coverage range {min_page.ink_coverage:.3%} (p. {min_page.page}) "
        f"to {max_page.ink_coverage:.3%} (p. {max_page.page})",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overleaf-dir", type=Path, default=DEFAULT_OVERLEAF)
    parser.add_argument("--entrypoint", default=DEFAULT_ENTRYPOINT)
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--expected-pages", type=int, default=DEFAULT_EXPECTED_PAGES)
    parser.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    parser.add_argument("--min-ink-coverage", type=float, default=DEFAULT_MIN_INK_COVERAGE)
    parser.add_argument("--temp-parent", type=Path, default=Path("/private/tmp"))
    args = parser.parse_args()

    pdf_path = args.pdf or args.overleaf_dir / Path(args.entrypoint).with_suffix(".pdf")
    ok, detail = check_rendered_pdf(
        pdf_path,
        expected_pages=args.expected_pages,
        dpi=args.dpi,
        min_ink_coverage=args.min_ink_coverage,
        temp_parent=args.temp_parent,
    )

    status = "PASS" if ok else "BLOCK"
    print(f"[{status}] PDF render smoke test: {detail}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
