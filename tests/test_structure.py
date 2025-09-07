"""Tests for line merging and hyphenation repair functionality."""

from __future__ import annotations

import pytest

from pdf2md.config import ToolConfig
from pdf2md.models import Span
from pdf2md.structure import merge_lines


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
    spans = [
        Span("Hello world", (0, 100, 100, 110), "Arial", 12, {}, 1, 0)
    ]
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
        Span("Hello", (0, 100, 50, 110), "Arial", 12, {}, 1, 0),    # Left span second
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
        Span("   ", (55, 100, 70, 110), "Arial", 12, {}, 1, 1),   # Multiple spaces
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
    # Should produce "transfor-" on first line, then "mation" which gets repaired to "transformation"
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


if __name__ == "__main__":
    pytest.main([__file__])
