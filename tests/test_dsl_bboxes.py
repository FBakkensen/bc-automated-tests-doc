from __future__ import annotations

import importlib
from pathlib import Path

import pdfplumber


def test_heading_positions_are_exact(tmp_path: Path) -> None:
    gen = importlib.import_module("scripts.gen_fixtures")
    out = tmp_path / "basic_headings.pdf"
    gen.make_basic_headings(out)

    with pdfplumber.open(out) as pdf:
        page = pdf.pages[0]
        chars = page.chars
        # Focus on the first heading: "Chapter 1 Introduction"
        # Expect it at x=72, y=700 baseline with exact positions
        # Filter first 7 characters "Chapter"
        first_chars = chars[:7]
        x0s = [float(c["x0"]) for c in first_chars]
        y0s = [float(c["y0"]) for c in first_chars]
        assert min(x0s) == 72.0
        # All characters on the same baseline
        assert len({round(y, 3) for y in y0s}) == 1
        # Check the text object's translation matrix encodes the baseline y=700
        assert float(first_chars[0]["matrix"][4]) == 72.0
        assert float(first_chars[0]["matrix"][5]) == 700.0
