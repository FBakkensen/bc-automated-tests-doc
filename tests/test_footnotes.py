"""Tests for footnote detection and association functionality."""

from __future__ import annotations

import pytest

from pdf2md.config import ToolConfig
from pdf2md.models import BlockType, Span


@pytest.fixture
def config():
    """Provide a default ToolConfig for tests."""
    return ToolConfig()


def test_detect_superscript_marker():
    """Test detection of superscript markers in text."""
    # Test with a simple superscript footnote marker
    spans = [
        Span("This is text", (0, 100, 100, 110), "Arial", 12, {}, 1, 0),
        Span("1", (105, 95, 115, 105), "Arial", 8, {"superscript": True}, 1, 1),
        Span("more text", (120, 100, 200, 110), "Arial", 12, {}, 1, 2),
    ]

    # This should be implemented in footnotes module
    from pdf2md.footnotes import detect_footnote_markers

    markers = detect_footnote_markers(spans)
    assert len(markers) == 1
    assert markers[0]["number"] == "1"
    assert markers[0]["span"] == spans[1]


def test_detect_footnote_text_in_bottom_band(config):
    """Test detection of footnote text at the bottom of a page."""
    # Mock page height = 800, so bottom band starts around y=700
    spans = [
        # Regular text in middle of page
        Span("Regular text", (0, 400, 200, 410), "Arial", 12, {}, 1, 0),
        # Footnote text at bottom of page
        Span("1", (50, 750, 60, 760), "Arial", 10, {}, 1, 1),
        Span("This is footnote text", (65, 750, 300, 760), "Arial", 10, {}, 1, 2),
    ]

    from pdf2md.footnotes import detect_footnote_text

    footnote_text = detect_footnote_text(spans, page_height=800, config=config)
    assert len(footnote_text) == 1
    assert footnote_text[0]["number"] == "1"
    assert "This is footnote text" in footnote_text[0]["text"]


def test_associate_footnotes():
    """Test association between footnote markers and footnote text."""
    # Create marker span
    marker_spans = [
        Span("Text with footnote", (0, 100, 150, 110), "Arial", 12, {}, 1, 0),
        Span("1", (155, 95, 165, 105), "Arial", 8, {"superscript": True}, 1, 1),
    ]

    # Create footnote text spans at bottom of page
    footnote_spans = [
        Span("1", (50, 750, 60, 760), "Arial", 10, {}, 1, 2),
        Span("This is the footnote explanation", (65, 750, 350, 760), "Arial", 10, {}, 1, 3),
    ]

    from pdf2md.footnotes import associate_footnotes

    associations = associate_footnotes(marker_spans, footnote_spans, page_height=800)
    assert len(associations) == 1
    assert associations[0]["marker_number"] == "1"
    assert associations[0]["footnote_number"] == "1"
    assert "footnote explanation" in associations[0]["footnote_text"]


def test_multiline_footnote_merge(config):
    """Test merging multi-line footnotes when config enables it."""
    # Multi-line footnote text
    footnote_spans = [
        Span("1", (50, 750, 60, 760), "Arial", 10, {}, 1, 0),
        Span("This is the first line", (65, 750, 250, 760), "Arial", 10, {}, 1, 1),
        Span("of the footnote", (65, 760, 200, 770), "Arial", 10, {}, 1, 2),
    ]

    from pdf2md.footnotes import detect_footnote_text

    # With merge enabled (default)
    footnote_text = detect_footnote_text(footnote_spans, page_height=800, config=config)
    assert len(footnote_text) == 1
    assert "This is the first line of the footnote" in footnote_text[0]["text"]


def test_multiline_footnote_no_merge():
    """Test keeping multi-line footnotes separate when config disables merging."""
    config_no_merge = ToolConfig(footnote_merge=False)

    footnote_spans = [
        Span("1", (50, 750, 60, 760), "Arial", 10, {}, 1, 0),
        Span("This is the first line", (65, 750, 250, 760), "Arial", 10, {}, 1, 1),
        Span("of the footnote", (65, 740, 200, 750), "Arial", 10, {}, 1, 2),
    ]

    from pdf2md.footnotes import detect_footnote_text

    # With merge disabled
    footnote_text = detect_footnote_text(footnote_spans, page_height=800, config=config_no_merge)
    # Should treat as separate footnote lines - implementation dependent
    # But marker should still be detected
    assert any("This is the first line" in ft["text"] for ft in footnote_text)


def test_footnote_integration_with_blocks(config):
    """Test that footnotes are properly integrated into block assembly."""
    spans = [
        # Regular paragraph
        Span("This is regular text", (0, 100, 200, 110), "Arial", 12, {}, 1, 0),
        Span("1", (205, 95, 215, 105), "Arial", 8, {"superscript": True}, 1, 1),
        # Footnote at bottom
        Span("1", (50, 750, 60, 760), "Arial", 10, {}, 1, 2),
        Span("Footnote explanation", (65, 750, 250, 760), "Arial", 10, {}, 1, 3),
    ]

    from pdf2md.structure import assemble_blocks

    blocks = assemble_blocks(spans, config)

    # Should have a paragraph block and a footnote placeholder block
    block_types = [block.block_type for block in blocks]
    assert BlockType.PARAGRAPH in block_types
    assert BlockType.FOOTNOTE_PLACEHOLDER in block_types


def test_footnote_numbering_sequence():
    """Test handling of sequential footnote numbering."""
    spans = [
        # Text with multiple footnotes
        Span("First", (0, 100, 50, 110), "Arial", 12, {}, 1, 0),
        Span("1", (55, 95, 65, 105), "Arial", 8, {"superscript": True}, 1, 1),
        Span("and second", (70, 100, 150, 110), "Arial", 12, {}, 1, 2),
        Span("2", (155, 95, 165, 105), "Arial", 8, {"superscript": True}, 1, 3),
        # Multiple footnotes at bottom
        Span("1", (50, 750, 60, 760), "Arial", 10, {}, 1, 4),
        Span("First footnote", (65, 750, 200, 760), "Arial", 10, {}, 1, 5),
        Span("2", (50, 740, 60, 750), "Arial", 10, {}, 1, 6),
        Span("Second footnote", (65, 740, 200, 750), "Arial", 10, {}, 1, 7),
    ]

    from pdf2md.footnotes import associate_footnotes

    associations = associate_footnotes(spans, spans, page_height=800)
    assert len(associations) == 2

    # Check proper numbering sequence
    numbers = [assoc["marker_number"] for assoc in associations]
    assert "1" in numbers
    assert "2" in numbers


def test_unmatched_footnote_marker():
    """Test handling of footnote markers without corresponding text."""
    marker_spans = [
        Span("Text with footnote", (0, 100, 150, 110), "Arial", 12, {}, 1, 0),
        Span("99", (155, 95, 175, 105), "Arial", 8, {"superscript": True}, 1, 1),
    ]

    # No footnote text at bottom
    footnote_spans = []

    from pdf2md.footnotes import associate_footnotes

    associations = associate_footnotes(marker_spans, footnote_spans, page_height=800)
    # Should handle gracefully, perhaps return empty or log warning
    assert len(associations) == 0


def test_unmatched_footnote_text():
    """Test handling of footnote text without corresponding markers."""
    # No markers in text
    marker_spans = [
        Span("Regular text without footnotes", (0, 100, 300, 110), "Arial", 12, {}, 1, 0),
    ]

    # Footnote text at bottom
    footnote_spans = [
        Span("1", (50, 750, 60, 760), "Arial", 10, {}, 1, 1),
        Span("Orphaned footnote", (65, 750, 250, 760), "Arial", 10, {}, 1, 2),
    ]

    from pdf2md.footnotes import associate_footnotes

    associations = associate_footnotes(marker_spans, footnote_spans, page_height=800)
    # Should handle gracefully
    assert len(associations) == 0


def test_footnote_grouping_respects_page_boundaries(config):
    """Test that footnotes on different pages are grouped separately."""
    spans = [
        # Page 1 footnotes
        Span("1", (50, 750, 60, 760), "Arial", 10, {}, 1, 0),
        Span("Footnote on page 1", (65, 750, 250, 760), "Arial", 10, {}, 1, 1),
        # Page 2 footnotes with similar y-coordinates
        Span("1", (50, 750, 60, 760), "Arial", 10, {}, 2, 2),
        Span("Footnote on page 2", (65, 750, 250, 760), "Arial", 10, {}, 2, 3),
    ]

    from pdf2md.footnotes import detect_footnote_text

    footnote_text = detect_footnote_text(spans, page_height=800, config=config)

    # Should detect 2 separate footnotes, one per page
    assert len(footnote_text) == 2

    # Both should be footnote number "1" but on different pages
    assert footnote_text[0]["number"] == "1"
    assert footnote_text[1]["number"] == "1"
    assert footnote_text[0]["page"] != footnote_text[1]["page"]

    # Check content to ensure they're separate
    assert "page 1" in footnote_text[0]["text"]
    assert "page 2" in footnote_text[1]["text"]


def test_footnote_merge_configuration(config):
    """Test that footnote merging behavior respects configuration."""
    # Multi-line footnote spans with smaller y difference
    spans = [
        Span("1", (50, 750, 60, 760), "Arial", 10, {}, 1, 0),
        Span("First line of footnote", (65, 750, 250, 760), "Arial", 10, {}, 1, 1),
        Span("Second line of footnote", (65, 752, 250, 762), "Arial", 10, {}, 1, 2),
    ]

    from pdf2md.footnotes import detect_footnote_text

    # Test with footnote_merge=True (should join with spaces)
    config.footnote_merge = True
    footnote_text = detect_footnote_text(spans, page_height=800, config=config)
    assert len(footnote_text) == 1
    assert footnote_text[0]["text"] == "First line of footnote Second line of footnote"

    # Test with footnote_merge=False (should preserve line breaks)
    config.footnote_merge = False
    footnote_text = detect_footnote_text(spans, page_height=800, config=config)
    assert len(footnote_text) == 1
    assert footnote_text[0]["text"] == "First line of footnote\nSecond line of footnote"
