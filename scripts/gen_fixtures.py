#!/usr/bin/env python3
"""
Deterministic PDF fixtures generator.

Purpose:
  - Generate tiny, fully deterministic PDFs for unit/integration tests.
  - Embed repo-bundled DejaVu fonts and set constant metadata.

Usage:
  python scripts/gen-fixtures.py --out tests/fixtures/pdfs --case basic_headings
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent.parent
FONTS_DIR = HERE / "fonts"


def _register_fonts() -> None:
    fonts = [
        ("DejaVuSans", FONTS_DIR / "DejaVuSans.ttf"),
        ("DejaVuSansMono", FONTS_DIR / "DejaVuSansMono.ttf"),
    ]
    registered = set(pdfmetrics.getRegisteredFontNames())
    for name, path in fonts:
        if name not in registered:
            pdfmetrics.registerFont(TTFont(name, str(path)))


def draw_heading(c: canvas.Canvas, *, level: int, text: str, xy: tuple[float, float]) -> None:
    size = {1: 18, 2: 14, 3: 12}.get(level, 12)
    c.setFont("DejaVuSans", size)
    x, y = xy
    c.drawString(x, y, text)


def draw_paragraph(
    c: canvas.Canvas,
    *,
    text: str,
    xy: tuple[float, float],
    leading: float = 14.0,
) -> None:
    c.setFont("DejaVuSans", 11)
    x, y = xy
    for i, line in enumerate(_wrap_simple(text, width=80)):
        c.drawString(x, y - i * leading, line)


def _wrap_simple(s: str, width: int) -> Iterable[str]:
    words = s.split()
    line: list[str] = []
    count = 0
    for w in words:
        if count and count + 1 + len(w) > width:
            yield " ".join(line)
            line = [w]
            count = len(w)
        else:
            if count:
                line.append(w)
                count += 1 + len(w)
            else:
                line = [w]
                count = len(w)
    if line:
        yield " ".join(line)


def _set_constant_metadata(c: canvas.Canvas) -> None:
    # Constant, test-friendly metadata
    c.setCreator("pdf2md-fixtures")
    c.setProducer("pdf2md-fixtures")
    # ReportLab uses current time; force a fixed date by overriding the formatter
    info = c._doc.info
    from contextlib import suppress

    # _dateFormatter is consulted when writing CreationDate/ModDate
    # ReportLab may forbid setting this private attribute; ignore failures
    with suppress(AttributeError):  # pragma: no cover -- defensive
        info._dateFormatter = lambda yyyy, mm, dd, hh, m, s: "D:20240101000000Z"


def make_basic_headings(output_path: Path) -> Path:
    _register_fonts()
    c = canvas.Canvas(str(output_path), pagesize=letter, invariant=True)
    _set_constant_metadata(c)
    # Page geometry
    # Letter: 612 x 792 pts; margin 72 pts (1 inch)
    x_margin = 72.0
    # Heading 1
    draw_heading(c, level=1, text="Chapter 1 Introduction", xy=(x_margin, 700.0))
    # Paragraph
    para = (
        "This is a deterministic PDF used for testing. It embeds DejaVu fonts and uses "
        "constant metadata to ensure byte-for-byte stability across runs."
    )
    draw_paragraph(c, text=para, xy=(x_margin, 660.0))
    c.showPage()
    c.save()
    return output_path


def make_multipage(output_path: Path) -> Path:
    """Create a multi-page PDF for testing exclude_pages functionality."""
    _register_fonts()
    c = canvas.Canvas(str(output_path), pagesize=letter, invariant=True)
    _set_constant_metadata(c)

    x_margin = 72.0

    # Page 1
    draw_heading(c, level=1, text="Page 1 Title", xy=(x_margin, 700.0))
    draw_paragraph(c, text="This is content on page 1.", xy=(x_margin, 660.0))
    c.showPage()

    # Page 2
    draw_heading(c, level=1, text="Page 2 Title", xy=(x_margin, 700.0))
    draw_paragraph(c, text="This is content on page 2.", xy=(x_margin, 660.0))
    c.showPage()

    # Page 3
    draw_heading(c, level=1, text="Page 3 Title", xy=(x_margin, 700.0))
    draw_paragraph(c, text="This is content on page 3.", xy=(x_margin, 660.0))
    c.showPage()

    c.save()
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("tests/fixtures/pdfs"))
    parser.add_argument("--case", type=str, default="basic_headings")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.case == "basic_headings":
        out = make_basic_headings(args.out / "basic_headings.pdf")
    elif args.case == "multipage":
        out = make_multipage(args.out / "multipage.pdf")
    else:
        raise SystemExit(f"unknown case: {args.case}")
    print(f"Wrote fixture: {out}")


if __name__ == "__main__":
    main()
