"""Line merging and text structure analysis for PDF spans.

This module provides functionality to merge spans into logical text lines
and repair hyphenation breaks across line boundaries.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .utils import repair_hyphenation

if TYPE_CHECKING:
    from .config import ToolConfig
    from .models import Span


# Pattern to match punctuation-only spans that should not have spaces before them
PUNCTUATION_ONLY_RE = re.compile(r'^[^\w\s]+$')


def merge_lines(spans: list[Span], config: ToolConfig) -> list[str]:
    """Merge spans into logical text lines with space normalization.

    Groups spans by their vertical position and merges them into logical
    text lines. Consecutive spans on the same line are joined with normalized
    spaces, and line breaks between logical paragraphs are preserved.
    The order of lines follows the original span order (order_index).

    Args:
        spans: List of Span objects to merge. Will be sorted by order_index.
        config: ToolConfig instance containing line merging parameters.

    Returns:
        List of merged text lines with hyphenation repaired.

    Examples:
        >>> # Mock spans for testing
        >>> from pdf2md.config import ToolConfig
        >>> config = ToolConfig()
        >>> spans = [
        ...     Span("Hello", (0, 100, 50, 110), "Arial", 12, {}, 1, 0),
        ...     Span("world", (60, 100, 100, 110), "Arial", 12, {}, 1, 1),
        ...     Span("This is", (0, 80, 60, 90), "Arial", 12, {}, 1, 2),
        ...     Span("a test", (70, 80, 120, 90), "Arial", 12, {}, 1, 3),
        ... ]
        >>> merge_lines(spans, config)
        ['Hello world', 'This is a test']
    """
    if not spans:
        return []

    # Sort spans by order_index to ensure proper ordering
    sorted_spans = sorted(spans, key=lambda s: s.order_index)

    # Group spans into logical lines, preserving order
    lines = _group_spans_into_lines_ordered(sorted_spans, config.line_merge_y_tolerance)

    # Convert each line group to text
    text_lines = []
    for line_spans in lines:
        # Sort spans within the line by x-coordinate (left to right)
        line_spans.sort(key=lambda s: s.bbox[0])  # Sort by x0 (left edge)

        # Join text from spans in the line with appropriate spacing
        line_text = _join_spans_with_smart_spacing(line_spans)

        if line_text:
            text_lines.append(line_text)

    # Apply hyphenation repair to the merged lines
    return repair_hyphenation(text_lines)


def _group_spans_into_lines_ordered(spans: list[Span], y_tolerance: float) -> list[list[Span]]:
    """Group spans that belong to the same logical line, preserving order.

    Uses y-coordinate proximity and order_index to determine which spans
    belong together on the same line. The groups maintain the original
    ordering of spans by order_index.

    Args:
        spans: List of spans to group, assumed to be sorted by order_index.
        y_tolerance: Tolerance for considering spans on the same line (in PDF units).

    Returns:
        List of span groups, each representing a logical line, in order.
    """
    if not spans:
        return []

    lines: list[list[Span]] = []
    current_line: list[Span] = [spans[0]]

    for span in spans[1:]:
        # Get y-coordinate (middle of bounding box) for comparison
        current_y = _get_span_y_center(span)
        prev_y = _get_span_y_center(current_line[-1])

        # If y-coordinates are close enough, add to current line
        if abs(current_y - prev_y) <= y_tolerance:
            current_line.append(span)
        else:
            # Start a new line
            if current_line:
                lines.append(current_line)
            current_line = [span]

    # Don't forget the last line
    if current_line:
        lines.append(current_line)

    return lines


def _join_spans_with_smart_spacing(spans: list[Span]) -> str:
    """Join spans with smart spacing that handles punctuation correctly.

    Punctuation-only spans (like standalone hyphens) are joined without
    preceding spaces to ensure hyphenation repair can work correctly.

    Args:
        spans: List of spans to join, assumed to be sorted by x-coordinate.

    Returns:
        Joined text with appropriate spacing.
    """
    if not spans:
        return ""

    result_parts = []
    for i, span in enumerate(spans):
        text = span.text.strip()
        if not text:
            continue

        if i == 0:
            # First span always added without prefix
            result_parts.append(text)
        else:
            # Check if this span is punctuation-only
            is_punctuation = PUNCTUATION_ONLY_RE.match(text)
            if is_punctuation:
                # Join punctuation directly without space
                result_parts.append(text)
            else:
                # Normal span gets a space prefix
                result_parts.append(" " + text)

    return "".join(result_parts)


def _get_span_y_center(span: Span) -> float:
    """Get the vertical center coordinate of a span's bounding box.

    Args:
        span: The span to get the y-center for.

    Returns:
        The y-coordinate of the span's center.
    """
    return (span.bbox[1] + span.bbox[3]) / 2
