"""Tests for line merging and hyphenation repair functionality."""

from __future__ import annotations

import pytest

from pdf2md.config import ToolConfig
from pdf2md.models import BlockType, Span
from pdf2md.structure import assemble_blocks, merge_lines


@pytest.fixture
def config():
    """Provide a default ToolConfig for tests."""
    return ToolConfig()


def test_merge_lines_empty_input(config):
    """Test merge_lines with empty input."""
    result = merge_lines([], config)
    assert result == []


def test_merge_lines_single_span(config):
    """Test merge_lines with a single span."""
    spans = [Span("Hello world", (0, 100, 100, 110), "Arial", 12, {}, 1, 0)]
    result = merge_lines(spans, config)
    assert result == ["Hello world"]


def test_merge_lines_same_line_multiple_spans(config):
    """Test merging multiple spans on the same line."""
    spans = [
        Span("Hello", (0, 100, 50, 110), "Arial", 12, {}, 1, 0),
        Span("world", (60, 100, 100, 110), "Arial", 12, {}, 1, 1),
        Span("test", (110, 100, 140, 110), "Arial", 12, {}, 1, 2),
    ]
    result = merge_lines(spans, config)
    assert result == ["Hello world test"]


def test_merge_lines_multiple_lines(config):
    """Test merging spans across multiple lines."""
    spans = [
        # First line at y=100
        Span("Hello", (0, 100, 50, 110), "Arial", 12, {}, 1, 0),
        Span("world", (60, 100, 100, 110), "Arial", 12, {}, 1, 1),
        # Second line at y=80 (different from first)
        Span("This is", (0, 80, 60, 90), "Arial", 12, {}, 1, 2),
        Span("a test", (70, 80, 120, 90), "Arial", 12, {}, 1, 3),
    ]
    result = merge_lines(spans, config)
    assert result == ["Hello world", "This is a test"]


def test_merge_lines_with_whitespace_normalization(config):
    """Test that spaces are normalized properly."""
    spans = [
        Span("  Hello  ", (0, 100, 50, 110), "Arial", 12, {}, 1, 0),
        Span("  world  ", (60, 100, 100, 110), "Arial", 12, {}, 1, 1),
    ]
    result = merge_lines(spans, config)
    assert result == ["Hello world"]


def test_merge_lines_skip_empty_spans(config):
    """Test that empty or whitespace-only spans are skipped."""
    spans = [
        Span("Hello", (0, 100, 50, 110), "Arial", 12, {}, 1, 0),
        Span("   ", (55, 100, 60, 110), "Arial", 12, {}, 1, 1),  # Empty
        Span("world", (60, 100, 100, 110), "Arial", 12, {}, 1, 2),
    ]
    result = merge_lines(spans, config)
    assert result == ["Hello world"]


def test_merge_lines_with_hyphenation_repair_basic(config):
    """Test basic hyphenation repair with lowercase continuation."""
    spans = [
        # Line ending with hyphen
        Span("transfor-", (0, 100, 80, 110), "Arial", 12, {}, 1, 0),
        # Next line starting with lowercase
        Span("mation", (0, 80, 60, 90), "Arial", 12, {}, 1, 1),
    ]
    result = merge_lines(spans, config)
    assert result == ["transformation"]


def test_merge_lines_with_hyphenation_no_repair_uppercase(config):
    """Test that hyphenation is not repaired when next line starts with uppercase."""
    spans = [
        # Line ending with hyphen
        Span("some-", (0, 100, 50, 110), "Arial", 12, {}, 1, 0),
        # Next line starting with uppercase
        Span("Thing", (0, 80, 60, 90), "Arial", 12, {}, 1, 1),
    ]
    result = merge_lines(spans, config)
    assert result == ["some-Thing"]


def test_merge_lines_with_hyphenation_mixed_case(config):
    """Test hyphenation repair with mixed cases in the same document."""
    spans = [
        # First word: repair hyphenation (lowercase continuation)
        Span("transfor-", (0, 100, 80, 110), "Arial", 12, {}, 1, 0),
        Span("mation", (0, 80, 60, 90), "Arial", 12, {}, 1, 1),
        # Second word: don't repair (uppercase continuation)
        Span("some-", (0, 60, 50, 70), "Arial", 12, {}, 1, 2),
        Span("Thing", (0, 40, 60, 50), "Arial", 12, {}, 1, 3),
    ]
    result = merge_lines(spans, config)
    assert result == ["transformation", "some-Thing"]


def test_merge_lines_complex_hyphenation(config):
    """Test complex hyphenation scenarios."""
    spans = [
        # Multiple words on first line, ending with hyphen
        Span("This is transfor-", (0, 100, 150, 110), "Arial", 12, {}, 1, 0),
        # Continuation with more words
        Span("mation of text", (0, 80, 120, 90), "Arial", 12, {}, 1, 1),
        # Another line
        Span("Another line", (0, 60, 100, 70), "Arial", 12, {}, 1, 2),
    ]
    result = merge_lines(spans, config)
    assert result == ["This is transformation of text", "Another line"]


def test_merge_lines_ordering_preserved(config):
    """Test that the order of lines is preserved."""
    spans = [
        # Third line (lowest y-coordinate)
        Span("Third", (0, 60, 50, 70), "Arial", 12, {}, 1, 4),
        # First line (highest y-coordinate)
        Span("First", (0, 100, 50, 110), "Arial", 12, {}, 1, 0),
        # Second line
        Span("Second", (0, 80, 60, 90), "Arial", 12, {}, 1, 2),
    ]
    result = merge_lines(spans, config)
    # Should maintain order based on order_index, not y-coordinate
    assert result == ["First", "Second", "Third"]


def test_merge_lines_y_tolerance(config):
    """Test that spans with slightly different y-coordinates are merged."""
    spans = [
        # Spans with slightly different y-coordinates (within tolerance)
        Span("Hello", (0, 100, 50, 110), "Arial", 12, {}, 1, 0),
        Span("world", (60, 102, 100, 112), "Arial", 12, {}, 1, 1),  # y slightly different
    ]
    result = merge_lines(spans, config)
    assert result == ["Hello world"]


def test_merge_lines_y_tolerance_exceeded(config):
    """Test that spans with very different y-coordinates are not merged."""
    spans = [
        # Spans with y-coordinates that exceed tolerance
        Span("Hello", (0, 100, 50, 110), "Arial", 12, {}, 1, 0),
        Span("world", (60, 90, 100, 100), "Arial", 12, {}, 1, 1),  # y difference > tolerance
    ]
    result = merge_lines(spans, config)
    assert result == ["Hello", "world"]


def test_merge_lines_left_to_right_ordering(config):
    """Test that spans are ordered left to right within a line."""
    spans = [
        # Spans on same line but in wrong x-order
        Span("world", (60, 100, 100, 110), "Arial", 12, {}, 1, 1),  # Right span first
        Span("Hello", (0, 100, 50, 110), "Arial", 12, {}, 1, 0),  # Left span second
    ]
    result = merge_lines(spans, config)
    assert result == ["Hello world"]  # Should be reordered by x-coordinate


def test_merge_lines_hyphenation_short_words_ignored(config):
    """Test that hyphenation repair ignores short words (< 3 characters)."""
    spans = [
        # Short word ending with hyphen should not be repaired (due to regex requirement)
        Span("a-", (0, 100, 20, 110), "Arial", 12, {}, 1, 0),
        Span("test", (0, 80, 40, 90), "Arial", 12, {}, 1, 1),
    ]
    result = merge_lines(spans, config)
    # The hyphenation regex requires 3+ characters, so "a-" won't match
    assert result == ["a-", "test"]


def test_merge_lines_hyphenation_no_following_line(config):
    """Test hyphenation when there's no following line."""
    spans = [
        # Line ending with hyphen but no continuation
        Span("transfor-", (0, 100, 80, 110), "Arial", 12, {}, 1, 0),
    ]
    result = merge_lines(spans, config)
    # When there's no following line, the hyphen is removed
    # (as per utils.repair_hyphenation line 41)
    assert result == ["transfor"]


def test_merge_lines_multiple_spaces_normalized(config):
    """Test that multiple spaces between words are normalized to single space."""
    spans = [
        Span("Hello", (0, 100, 50, 110), "Arial", 12, {}, 1, 0),
        Span("   ", (55, 100, 70, 110), "Arial", 12, {}, 1, 1),  # Multiple spaces
        Span("world", (75, 100, 110, 110), "Arial", 12, {}, 1, 2),
    ]
    result = merge_lines(spans, config)
    assert result == ["Hello world"]


def test_merge_lines_punctuation_no_space_before_hyphen(config):
    """Test that hyphen spans are joined without preceding space for hyphenation repair."""
    spans = [
        # Word span followed by separate hyphen span
        Span("transfor", (0, 100, 70, 110), "Arial", 12, {}, 1, 0),
        Span("-", (71, 100, 75, 110), "Arial", 12, {}, 1, 1),
        # Next line starts with lowercase for hyphenation repair
        Span("mation", (0, 80, 60, 90), "Arial", 12, {}, 1, 2),
    ]
    result = merge_lines(spans, config)
    # Should produce "transfor-" on first line, then "mation"
    # which gets repaired to "transformation"
    assert result == ["transformation"]


def test_merge_lines_punctuation_no_space_before_period(config):
    """Test that period spans are joined without preceding space."""
    spans = [
        Span("Hello world", (0, 100, 80, 110), "Arial", 12, {}, 1, 0),
        Span(".", (81, 100, 85, 110), "Arial", 12, {}, 1, 1),
        Span("This is next", (0, 80, 100, 90), "Arial", 12, {}, 1, 2),
    ]
    result = merge_lines(spans, config)
    assert result == ["Hello world.", "This is next"]


def test_merge_lines_punctuation_mixed_with_normal_spacing(config):
    """Test mixing of punctuation and normal spans with appropriate spacing."""
    spans = [
        Span("Hello", (0, 100, 50, 110), "Arial", 12, {}, 1, 0),
        Span(",", (51, 100, 55, 110), "Arial", 12, {}, 1, 1),  # Punctuation
        Span("world", (60, 100, 100, 110), "Arial", 12, {}, 1, 2),  # Normal word
        Span("!", (101, 100, 105, 110), "Arial", 12, {}, 1, 3),  # Punctuation
    ]
    result = merge_lines(spans, config)
    assert result == ["Hello, world!"]


def test_merge_lines_custom_y_tolerance(config):
    """Test that custom y_tolerance from config is respected."""
    # Set a smaller tolerance
    config.line_merge_y_tolerance = 1.0

    spans = [
        # Spans with y-coordinates that would merge with default tolerance but not with smaller
        Span("Hello", (0, 100, 50, 110), "Arial", 12, {}, 1, 0),
        Span("world", (60, 102, 100, 112), "Arial", 12, {}, 1, 1),  # y difference = 2.0
    ]
    result = merge_lines(spans, config)
    # With tolerance = 1.0, these should NOT merge (difference > 1.0)
    assert result == ["Hello", "world"]


# Tests for assemble_blocks function


def test_assemble_blocks_empty_input(config):
    """Test assemble_blocks with empty input."""
    result = assemble_blocks([], config)
    assert result == []


def test_assemble_blocks_single_paragraph(config):
    """Test assembling a single paragraph from consecutive text lines."""
    spans = [
        Span("Hello world", (0, 100, 100, 110), "Arial", 12, {}, 1, 0),
        Span("This is a test", (0, 80, 120, 90), "Arial", 12, {}, 1, 1),
        Span("of paragraph assembly", (0, 60, 150, 70), "Arial", 12, {}, 1, 2),
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 1
    assert result[0].block_type == BlockType.PARAGRAPH
    # The block should have a valid bbox and page span
    assert result[0].bbox != (0.0, 0.0, 0.0, 0.0)
    assert result[0].page_span == (1, 1)


def test_assemble_blocks_paragraph_with_empty_line(config):
    """Test that empty lines create separate blocks and break paragraphs."""
    spans = [
        Span("First paragraph", (0, 100, 100, 110), "Arial", 12, {}, 1, 0),
        Span("", (0, 80, 0, 90), "Arial", 12, {}, 1, 1),  # Empty line
        Span("Second paragraph", (0, 60, 120, 70), "Arial", 12, {}, 1, 2),
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 3
    assert result[0].block_type == BlockType.PARAGRAPH
    assert result[1].block_type == BlockType.EMPTY_LINE
    assert result[2].block_type == BlockType.PARAGRAPH


def test_assemble_blocks_bullet_list_detection(config):
    """Test that bullet list items are detected correctly."""
    spans = [
        Span("• First item", (0, 100, 80, 110), "Arial", 12, {}, 1, 0),
        Span("• Second item", (0, 80, 90, 90), "Arial", 12, {}, 1, 1),
        Span("• Third item", (0, 60, 85, 70), "Arial", 12, {}, 1, 2),
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 1
    assert result[0].block_type == BlockType.LIST


def test_assemble_blocks_ordered_list_detection(config):
    """Test that ordered list items are detected correctly."""
    spans = [
        Span("1. First item", (0, 100, 80, 110), "Arial", 12, {}, 1, 0),
        Span("2. Second item", (0, 80, 90, 90), "Arial", 12, {}, 1, 1),
        Span("3. Third item", (0, 60, 85, 70), "Arial", 12, {}, 1, 2),
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 1
    assert result[0].block_type == BlockType.LIST


def test_assemble_blocks_code_block_detection_by_indent(config):
    """Test that indented code blocks are detected when meeting minimum line threshold."""
    # Use default config values: code_min_lines=2, code_indent_threshold=4
    spans = [
        Span("    def hello():", (40, 100, 120, 110), "Courier", 10, {"mono": True}, 1, 0),
        Span("        print('hello')", (80, 80, 160, 90), "Courier", 10, {"mono": True}, 1, 1),
        Span("        return True", (80, 60, 150, 70), "Courier", 10, {"mono": True}, 1, 2),
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 1
    assert result[0].block_type == BlockType.CODE_BLOCK
    assert "dedented_lines" in result[0].meta
    # Check that indentation was removed properly
    dedented = result[0].meta["dedented_lines"]
    assert dedented[0] == "def hello():"
    assert dedented[1] == "    print('hello')"
    assert dedented[2] == "    return True"


def test_assemble_blocks_insufficient_code_lines(config):
    """Test that insufficient indented lines don't create a code block."""
    # Only one indented line, but code_min_lines=2
    spans = [
        Span("    single_line = True", (40, 100, 120, 110), "Courier", 10, {"mono": True}, 1, 0),
        Span("Regular paragraph text", (0, 80, 120, 90), "Arial", 12, {}, 1, 1),
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 1
    assert result[0].block_type == BlockType.PARAGRAPH  # Not enough lines for code block


def test_assemble_blocks_respect_code_min_lines_config(config):
    """Test that code_min_lines config parameter is respected."""
    config.code_min_lines = 3  # Require 3 lines minimum

    spans = [
        Span("    line1 = 1", (40, 100, 80, 110), "Courier", 10, {"mono": True}, 1, 0),
        Span(
            "    line2 = 2", (40, 80, 80, 90), "Courier", 10, {"mono": True}, 1, 1
        ),  # Only 2 lines
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 1
    assert (
        result[0].block_type == BlockType.PARAGRAPH
    )  # Not enough for code block with higher threshold


def test_assemble_blocks_respect_code_indent_threshold(config):
    """Test that code_indent_threshold config parameter is respected."""
    config.code_indent_threshold = 8  # Require more indentation

    spans = [
        Span("    not_enough_indent", (40, 100, 120, 110), "Courier", 10, {"mono": True}, 1, 0),
        Span("    still_not_enough", (40, 80, 120, 90), "Courier", 10, {"mono": True}, 1, 1),
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 1
    assert result[0].block_type == BlockType.PARAGRAPH  # Not indented enough for code block


def test_assemble_blocks_mixed_content(config):
    """Test assembling mixed content: paragraph, list, and code block."""
    spans = [
        # Paragraph
        Span("Introduction text", (0, 120, 100, 130), "Arial", 12, {}, 1, 0),
        Span("", (0, 110, 0, 115), "Arial", 12, {}, 1, 1),  # Empty line
        # List
        Span("• First item", (0, 100, 80, 110), "Arial", 12, {}, 1, 2),
        Span("• Second item", (0, 90, 85, 100), "Arial", 12, {}, 1, 3),
        Span("", (0, 80, 0, 85), "Arial", 12, {}, 1, 4),  # Empty line
        # Code block
        Span("    def function():", (40, 70, 120, 80), "Courier", 10, {"mono": True}, 1, 5),
        Span("        return True", (80, 60, 150, 70), "Courier", 10, {"mono": True}, 1, 6),
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 5  # paragraph, empty, list, empty, code
    assert result[0].block_type == BlockType.PARAGRAPH
    assert result[1].block_type == BlockType.EMPTY_LINE
    assert result[2].block_type == BlockType.LIST
    assert result[3].block_type == BlockType.EMPTY_LINE
    assert result[4].block_type == BlockType.CODE_BLOCK


def test_assemble_blocks_code_with_empty_lines(config):
    """Test that empty lines within code blocks are preserved."""
    spans = [
        Span("    def function():", (40, 100, 120, 110), "Courier", 10, {"mono": True}, 1, 0),
        Span("", (40, 90, 40, 95), "Courier", 10, {"mono": True}, 1, 1),  # Empty line in code
        Span("        return True", (80, 80, 150, 90), "Courier", 10, {"mono": True}, 1, 2),
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 1
    assert result[0].block_type == BlockType.CODE_BLOCK
    dedented = result[0].meta["dedented_lines"]
    assert len(dedented) == 3
    assert dedented[0] == "def function():"
    assert dedented[1] == ""  # Empty line preserved
    assert dedented[2] == "    return True"


def test_assemble_blocks_avoid_heading_false_positives(config):
    """Test that numbered headings are not incorrectly classified as list items."""
    # Test cases that should be treated as paragraphs, not list items
    heading_spans = [
        # Typical chapter headings that should not be lists
        Span("1. Introduction", (0, 100, 80, 110), "Arial", 14, {"bold": True}, 1, 0),
        Span("2. Background", (0, 80, 90, 90), "Arial", 14, {"bold": True}, 1, 1),
        Span("3. Methodology", (0, 60, 85, 70), "Arial", 14, {"bold": True}, 1, 2),
    ]

    result = assemble_blocks(heading_spans, config)
    # Should create one paragraph block (consecutive paragraphs get grouped)
    assert len(result) == 1
    assert result[0].block_type == BlockType.PARAGRAPH

    # Test mixed case - actual list items should still be detected
    mixed_spans = [
        # This looks like a heading
        Span("1. Introduction", (0, 100, 80, 110), "Arial", 14, {"bold": True}, 1, 0),
        Span("", (0, 80, 0, 80), "Arial", 12, {}, 1, 1),  # Empty line
        # These look like actual list items
        Span("1. First task to complete", (0, 60, 120, 70), "Arial", 12, {}, 1, 2),
        Span("2. Second task in sequence", (0, 40, 130, 50), "Arial", 12, {}, 1, 3),
    ]

    result = assemble_blocks(mixed_spans, config)
    assert len(result) == 3  # Paragraph, empty line, list
    assert result[0].block_type == BlockType.PARAGRAPH  # The heading
    assert result[1].block_type == BlockType.EMPTY_LINE
    assert result[2].block_type == BlockType.LIST  # The actual list items


def test_assemble_blocks_monospace_code_detection(config):
    """Test that monospace spans are detected as code blocks."""
    spans = [
        Span("def hello():", (0, 100, 80, 110), "Courier", 10, {"mono": True}, 1, 0),
        Span("    print('hello')", (0, 80, 120, 90), "Courier", 10, {"mono": True}, 1, 1),
        Span("    return True", (0, 60, 110, 70), "Courier", 10, {"mono": True}, 1, 2),
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 1
    assert result[0].block_type == BlockType.CODE_BLOCK
    # Check that code language detection is present
    assert "code_language" in result[0].meta
    assert result[0].meta["code_language"] is None  # Should be None for now


def test_assemble_blocks_mixed_monospace_regular_text(config):
    """Test mixed monospace and regular text - should detect code when mostly monospace."""
    spans = [
        # Line with mostly monospace text should be detected as code
        Span("def", (0, 100, 20, 110), "Courier", 10, {"mono": True}, 1, 0),
        Span(" ", (20, 100, 25, 110), "Arial", 12, {}, 1, 1),  # Regular space
        Span("function():", (25, 100, 80, 110), "Courier", 10, {"mono": True}, 1, 2),
        # Second line also mostly monospace
        Span("    return", (0, 80, 50, 90), "Courier", 10, {"mono": True}, 1, 3),
        Span(" True", (50, 80, 80, 90), "Courier", 10, {"mono": True}, 1, 4),
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 1
    assert result[0].block_type == BlockType.CODE_BLOCK


def test_assemble_blocks_insufficient_monospace_lines(config):
    """Test that insufficient monospace lines don't create a code block."""
    # Only one monospace line, but code_min_lines=2
    spans = [
        Span("single_line()", (0, 100, 80, 110), "Courier", 10, {"mono": True}, 1, 0),
        Span("Regular paragraph text", (0, 80, 120, 90), "Arial", 12, {}, 1, 1),
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 1
    assert result[0].block_type == BlockType.PARAGRAPH  # Not enough lines for code block


def test_assemble_blocks_monospace_and_indent_mixed(config):
    """Test that both monospace and indented code detection work together."""
    spans = [
        # Monospace code without much indentation
        Span("function test() {", (0, 120, 100, 130), "Courier", 10, {"mono": True}, 1, 0),
        # Indented code with regular font
        Span("    var x = 1;", (40, 100, 100, 110), "Arial", 10, {}, 1, 1),
        Span("    return x;", (40, 80, 90, 90), "Arial", 10, {}, 1, 2),
        # Monospace closing
        Span("}", (0, 60, 10, 70), "Courier", 10, {"mono": True}, 1, 3),
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 1
    assert result[0].block_type == BlockType.CODE_BLOCK


def test_assemble_blocks_nested_bullet_lists(config):
    """Test nested bullet list detection by x-offset."""
    spans = [
        # Top level items at x=10
        Span("• First item", (10, 120, 80, 130), "Arial", 12, {}, 1, 0),
        # Nested item at x=30 (20 point offset)
        Span("  • Nested item", (30, 100, 100, 110), "Arial", 12, {}, 1, 1),
        Span("  • Another nested", (30, 80, 110, 90), "Arial", 12, {}, 1, 2),
        # Back to top level
        Span("• Second item", (10, 60, 90, 70), "Arial", 12, {}, 1, 3),
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 1
    assert result[0].block_type == BlockType.LIST
    
    # Check nesting structure
    meta = result[0].meta
    assert "list_items" in meta
    list_items = meta["list_items"]
    assert len(list_items) == 4
    
    # Check nesting levels
    assert list_items[0]["level"] == 0  # First item
    assert list_items[1]["level"] == 1  # Nested item
    assert list_items[2]["level"] == 1  # Another nested
    assert list_items[3]["level"] == 0  # Second item
    
    # Check max nesting level
    assert meta["max_nesting_level"] == 1


def test_assemble_blocks_nested_ordered_lists(config):
    """Test nested ordered list detection by x-offset."""
    spans = [
        # Top level items at x=10
        Span("1. First item", (10, 120, 80, 130), "Arial", 12, {}, 1, 0),
        # Nested items at x=30
        Span("  a. Nested item", (30, 100, 100, 110), "Arial", 12, {}, 1, 1),
        Span("  b. Another nested", (30, 80, 110, 90), "Arial", 12, {}, 1, 2),
        # Back to top level
        Span("2. Second item", (10, 60, 90, 70), "Arial", 12, {}, 1, 3),
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 1
    assert result[0].block_type == BlockType.LIST
    
    # Check nesting structure
    meta = result[0].meta
    list_items = meta["list_items"]
    assert len(list_items) == 4
    
    # Check nesting levels
    assert list_items[0]["level"] == 0  # 1. First item
    assert list_items[1]["level"] == 1  # a. Nested item
    assert list_items[2]["level"] == 1  # b. Another nested
    assert list_items[3]["level"] == 0  # 2. Second item


def test_assemble_blocks_mixed_list_types_nesting(config):
    """Test mixed bullet and ordered list nesting."""
    spans = [
        # Top level bullet at x=10
        Span("• Main topic", (10, 120, 80, 130), "Arial", 12, {}, 1, 0),
        # Nested ordered list at x=30
        Span("  1. First subtopic", (30, 100, 120, 110), "Arial", 12, {}, 1, 1),
        Span("  2. Second subtopic", (30, 80, 130, 90), "Arial", 12, {}, 1, 2),
        # Deeply nested bullet at x=50
        Span("    • Detail point", (50, 60, 110, 70), "Arial", 12, {}, 1, 3),
        # Back to top level
        Span("• Another main topic", (10, 40, 120, 50), "Arial", 12, {}, 1, 4),
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 1
    assert result[0].block_type == BlockType.LIST
    
    # Check nesting structure
    meta = result[0].meta
    list_items = meta["list_items"]
    assert len(list_items) == 5
    
    # Check nesting levels (should be based on x-position clusters)
    assert list_items[0]["level"] == 0  # • Main topic (x=10)
    assert list_items[1]["level"] == 1  # 1. First subtopic (x=30)
    assert list_items[2]["level"] == 1  # 2. Second subtopic (x=30)
    assert list_items[3]["level"] == 2  # • Detail point (x=50)
    assert list_items[4]["level"] == 0  # • Another main topic (x=10)
    
    # Check max nesting level
    assert meta["max_nesting_level"] == 2


def test_assemble_blocks_list_indent_tolerance_respected(config):
    """Test that list_indent_tolerance is respected in nesting detection."""
    # Set a smaller tolerance for this test
    config.list_indent_tolerance = 5
    
    spans = [
        # Items at x=10 and x=13 should be same level (within tolerance)
        Span("• First item", (10, 120, 80, 130), "Arial", 12, {}, 1, 0),
        Span("• Similar position", (13, 100, 100, 110), "Arial", 12, {}, 1, 1),
        # Item at x=20 should be nested (outside tolerance)
        Span("  • Nested item", (20, 80, 100, 90), "Arial", 12, {}, 1, 2),
    ]

    result = assemble_blocks(spans, config)
    assert len(result) == 1
    assert result[0].block_type == BlockType.LIST
    
    # Check nesting structure
    meta = result[0].meta
    list_items = meta["list_items"]
    assert len(list_items) == 3
    
    # Items at x=10 and x=13 should have same level (within tolerance of 5)
    assert list_items[0]["level"] == list_items[1]["level"]
    # Item at x=20 should have different level (outside tolerance)
    assert list_items[2]["level"] != list_items[0]["level"]


if __name__ == "__main__":
    pytest.main([__file__])
