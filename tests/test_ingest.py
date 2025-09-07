"""Tests for PDF ingestion module."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from pdf2md.config import ToolConfig
from pdf2md.ingest import PdfIngestor
from pdf2md.models import Span


class TestPdfIngestor:
    """Test cases for PdfIngestor class."""

    def test_pdf_ingestor_initialization(self) -> None:
        """Test PdfIngestor can be initialized with config."""
        config = ToolConfig()
        ingestor = PdfIngestor(config)
        assert ingestor.config is config

    def test_extract_spans_with_basic_headings_fixture(self) -> None:
        """Test spans extraction from basic_headings.pdf fixture."""
        config = ToolConfig()
        ingestor = PdfIngestor(config)

        fixture_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        # Skip test if fixture doesn't exist
        if not fixture_path.exists():
            pytest.skip(f"Test fixture not found: {fixture_path}")

        spans = ingestor.extract_spans(fixture_path)

        # Basic validation
        assert isinstance(spans, list)
        assert len(spans) > 0, "Should extract at least one span"

        # All spans should be Span objects
        for span in spans:
            assert isinstance(span, Span)
            assert isinstance(span.text, str)
            assert len(span.text.strip()) > 0, f"Span text should not be empty: {span.text!r}"
            assert isinstance(span.bbox, tuple)
            assert len(span.bbox) == 4
            assert isinstance(span.font_name, str)
            assert isinstance(span.font_size, float)
            assert span.font_size > 0
            assert isinstance(span.style_flags, dict)
            assert isinstance(span.page, int)
            assert span.page > 0
            assert isinstance(span.order_index, int)

    def test_order_index_strictly_increasing(self) -> None:
        """Test that order_index values are strictly increasing across all pages."""
        config = ToolConfig()
        ingestor = PdfIngestor(config)

        fixture_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        if not fixture_path.exists():
            pytest.skip(f"Test fixture not found: {fixture_path}")

        spans = ingestor.extract_spans(fixture_path)

        # Extract order indices
        order_indices = [span.order_index for span in spans]

        # Check strictly increasing
        for i in range(1, len(order_indices)):
            assert order_indices[i] > order_indices[i - 1], (
                f"Order index not strictly increasing: {order_indices[i - 1]} >= "
                f"{order_indices[i]} at position {i}"
            )

    def test_non_empty_spans_only(self) -> None:
        """Test that only non-empty spans are produced."""
        config = ToolConfig()
        ingestor = PdfIngestor(config)

        fixture_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        if not fixture_path.exists():
            pytest.skip(f"Test fixture not found: {fixture_path}")

        spans = ingestor.extract_spans(fixture_path)

        # All spans should have non-empty text
        for span in spans:
            assert span.text.strip(), f"Found span with empty text: {span.text!r}"

    def test_style_flags_structure(self) -> None:
        """Test that style_flags includes bold and italic keys."""
        config = ToolConfig()
        ingestor = PdfIngestor(config)

        fixture_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        if not fixture_path.exists():
            pytest.skip(f"Test fixture not found: {fixture_path}")

        spans = ingestor.extract_spans(fixture_path)

        # All spans should have style_flags with bold and italic
        for span in spans:
            assert "bold" in span.style_flags
            assert "italic" in span.style_flags
            assert isinstance(span.style_flags["bold"], bool)
            assert isinstance(span.style_flags["italic"], bool)

    def test_exclude_pages_multipage_functionality(self) -> None:
        """Test exclude_pages with multi-page PDF."""
        fixture_path = Path(__file__).parent / "fixtures" / "pdfs" / "multipage.pdf"

        if not fixture_path.exists():
            pytest.skip(f"Multi-page test fixture not found: {fixture_path}")

        # Test normal behavior (all pages)
        config = ToolConfig(exclude_pages=[])
        ingestor = PdfIngestor(config)
        all_spans = ingestor.extract_spans(fixture_path)

        # Should have spans from all 3 pages
        pages_found = {span.page for span in all_spans}
        assert 1 in pages_found, "Should have spans from page 1"
        assert 2 in pages_found, "Should have spans from page 2"
        assert 3 in pages_found, "Should have spans from page 3"

        # Test excluding page 2
        config = ToolConfig(exclude_pages=[2])
        ingestor = PdfIngestor(config)
        filtered_spans = ingestor.extract_spans(fixture_path)

        # Should have spans from pages 1 and 3, but not 2
        pages_found = {span.page for span in filtered_spans}
        assert 1 in pages_found, "Should have spans from page 1"
        assert 2 not in pages_found, "Should not have spans from page 2"
        assert 3 in pages_found, "Should have spans from page 3"

        # Should have fewer spans than all pages
        assert len(filtered_spans) < len(all_spans), "Should have fewer spans when excluding a page"

    def test_exclude_pages_functionality(self) -> None:
        """Test that pages in exclude_pages are skipped."""
        # Test with page 1 excluded (basic_headings.pdf has 1 page)
        config = ToolConfig(exclude_pages=[1])
        ingestor = PdfIngestor(config)

        fixture_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        if not fixture_path.exists():
            pytest.skip(f"Test fixture not found: {fixture_path}")

        spans = ingestor.extract_spans(fixture_path)

        # Should be empty since page 1 is excluded
        assert len(spans) == 0, "Should have no spans when page 1 is excluded"

    def test_exclude_pages_no_effect_on_nonexistent_pages(self) -> None:
        """Test that excluding non-existent pages has no effect."""
        # Exclude page 99 (doesn't exist in basic_headings.pdf)
        config = ToolConfig(exclude_pages=[99])
        ingestor = PdfIngestor(config)

        fixture_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        if not fixture_path.exists():
            pytest.skip(f"Test fixture not found: {fixture_path}")

        spans = ingestor.extract_spans(fixture_path)

        # Should still have spans since we only excluded a non-existent page
        assert len(spans) > 0, "Should have spans when excluding non-existent page"

    def test_file_not_found_error(self) -> None:
        """Test FileNotFoundError for non-existent PDF."""
        config = ToolConfig()
        ingestor = PdfIngestor(config)

        # Use tempfile for safer temporary path handling
        with tempfile.TemporaryDirectory() as tmp_dir:
            non_existent_path = Path(tmp_dir) / "non_existent_file.pdf"

            with pytest.raises(FileNotFoundError, match="PDF file not found"):
                ingestor.extract_spans(non_existent_path)

    def test_invalid_pdf_error(self) -> None:
        """Test ValueError for invalid PDF content."""
        config = ToolConfig()
        ingestor = PdfIngestor(config)

        # Create a temporary file with invalid PDF content
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(b"This is not a valid PDF file")
            tmp_path = Path(tmp_file.name)

        try:
            with pytest.raises(ValueError, match="Failed to read PDF"):
                ingestor.extract_spans(tmp_path)
        finally:
            tmp_path.unlink()  # Clean up

    def test_detect_style_flags_bold_font_names(self) -> None:
        """Test style flags detection for bold font names."""
        config = ToolConfig()
        ingestor = PdfIngestor(config)

        # Test various bold font name patterns
        bold_fonts = ["Arial-Bold", "Times-Black", "DejaVu-Heavy", "SomeFont-Thick"]

        for font_name in bold_fonts:
            style_flags = ingestor._detect_style_flags(font_name, [])
            assert style_flags["bold"], f"Should detect bold for font: {font_name}"
            assert not style_flags["italic"], f"Should not detect italic for font: {font_name}"

    def test_detect_style_flags_italic_font_names(self) -> None:
        """Test style flags detection for italic font names."""
        config = ToolConfig()
        ingestor = PdfIngestor(config)

        # Test various italic font name patterns
        italic_fonts = ["Arial-Italic", "Times-Oblique", "DejaVu-Slant"]

        for font_name in italic_fonts:
            style_flags = ingestor._detect_style_flags(font_name, [])
            assert style_flags["italic"], f"Should detect italic for font: {font_name}"
            assert not style_flags["bold"], f"Should not detect bold for font: {font_name}"

    def test_detect_style_flags_regular_font_names(self) -> None:
        """Test style flags detection for regular font names."""
        config = ToolConfig()
        ingestor = PdfIngestor(config)

        # Test regular font names
        regular_fonts = ["Arial", "Times-Roman", "DejaVuSans", "Helvetica"]

        for font_name in regular_fonts:
            style_flags = ingestor._detect_style_flags(font_name, [])
            assert not style_flags["bold"], f"Should not detect bold for font: {font_name}"
            assert not style_flags["italic"], f"Should not detect italic for font: {font_name}"

    def test_detect_style_flags_empty_font_name(self) -> None:
        """Test style flags detection with empty font name."""
        config = ToolConfig()
        ingestor = PdfIngestor(config)

        style_flags = ingestor._detect_style_flags("", [])
        assert not style_flags["bold"]
        assert not style_flags["italic"]
