from __future__ import annotations

from pathlib import Path


def test_vendored_fonts_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    fonts = root / "fonts"
    assert (fonts / "DejaVuSans.ttf").exists()
    assert (fonts / "DejaVuSansMono.ttf").exists()
    lic = fonts / "LICENSE.txt"
    assert lic.exists()
    text = lic.read_text(encoding="utf-8", errors="ignore")
    assert "DejaVu" in text
