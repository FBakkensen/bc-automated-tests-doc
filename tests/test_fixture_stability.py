from __future__ import annotations

import hashlib
import importlib
from pathlib import Path


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_basic_pdf_is_byte_stable(tmp_path: Path) -> None:
    gen = importlib.import_module("scripts.gen_fixtures")
    out1 = tmp_path / "basic_headings_1.pdf"
    out2 = tmp_path / "basic_headings_2.pdf"

    # API: make_basic_headings(output_path: Path) -> Path
    gen.make_basic_headings(out1)
    gen.make_basic_headings(out2)

    h1, h2 = sha256(out1), sha256(out2)
    assert h1 == h2

    # Check constant metadata tokens and embedded font name markers
    data = out1.read_bytes()
    assert b"pdf2md-fixtures" in data  # Producer tag
    assert b"D:20240101000000Z" in data  # CreationDate
    assert b"DejaVuSans" in data  # Embedded font name appears in PDF
