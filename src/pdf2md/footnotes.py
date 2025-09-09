"""Footnote detection and association functionality."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import ToolConfig
    from .models import Span


def detect_footnote_markers(spans: list[Span]) -> list[dict[str, object]]:
    """Detect superscript footnote markers in spans.

    Args:
        spans: List of spans to search for footnote markers.

    Returns:
        List of footnote marker dictionaries with 'number' and 'span' keys.
    """
    markers = []

    for span in spans:
        # Check for superscript style or small font size relative to context
        is_superscript = span.style_flags.get("superscript", False) or _is_likely_superscript(
            span, spans
        )

        if is_superscript and _is_numeric_footnote_marker(span.text):
            markers.append(
                {"number": span.text.strip(), "span": span, "page": span.page, "bbox": span.bbox}
            )

    return markers


def detect_footnote_text(
    spans: list[Span], page_height: float, config: ToolConfig | None = None
) -> list[dict[str, object]]:
    """Detect footnote text in the bottom band of a page.

    Args:
        spans: List of spans to search for footnote text.
        page_height: Height of the page for determining bottom band.
        config: Optional configuration object.

    Returns:
        List of footnote text dictionaries with 'number' and 'text' keys.
    """
    if config is None:
        from .config import ToolConfig

        config = ToolConfig()

    # Determine bottom band (footer area)
    footer_threshold = page_height * 0.85  # Bottom 15% of page

    # Find spans in bottom band
    bottom_spans = [span for span in spans if span.bbox[1] >= footer_threshold]

    if not bottom_spans:
        return []

    # Group footnote text by line/proximity
    footnote_groups = _group_footnote_text(bottom_spans, config)

    footnotes = []
    for group in footnote_groups:
        footnote_number = _extract_footnote_number(group[0])
        if footnote_number:
            footnote_text = _merge_footnote_text(group, config)
            footnotes.append(
                {
                    "number": footnote_number,
                    "text": footnote_text,
                    "spans": group,
                    "page": group[0].page,
                }
            )

    return footnotes


def associate_footnotes(
    marker_spans: list[Span], footnote_spans: list[Span], page_height: float
) -> list[dict[str, object]]:
    """Associate footnote markers with their corresponding footnote text.

    Args:
        marker_spans: Spans containing footnote markers.
        footnote_spans: Spans containing footnote text.
        page_height: Height of the page.

    Returns:
        List of association dictionaries linking markers to footnote text.
    """
    from .config import ToolConfig

    config = ToolConfig()

    # Detect markers and footnote text
    markers = detect_footnote_markers(marker_spans)
    footnote_text = detect_footnote_text(footnote_spans, page_height, config)

    # Create mapping from footnote number to text
    footnote_map = {ft["number"]: ft for ft in footnote_text}

    associations = []
    for marker in markers:
        marker_number = marker["number"]
        if marker_number in footnote_map:
            associations.append(
                {
                    "marker_number": marker_number,
                    "footnote_number": marker_number,
                    "footnote_text": footnote_map[marker_number]["text"],
                    "marker_span": marker["span"],
                    "footnote_spans": footnote_map[marker_number]["spans"],
                }
            )

    return associations


def _is_likely_superscript(span: Span, context_spans: list[Span]) -> bool:
    """Check if a span is likely a superscript based on position and size."""
    # Find nearby spans to compare font size
    nearby_spans = [
        s for s in context_spans if s.page == span.page and abs(s.bbox[0] - span.bbox[0]) < 50
    ]

    if not nearby_spans:
        return False

    # Check if font is significantly smaller than nearby text
    avg_font_size = sum(s.font_size for s in nearby_spans) / len(nearby_spans)
    is_smaller = span.font_size < avg_font_size * 0.8

    # Check if positioned higher (lower y coordinate in PDF)
    avg_y = sum(s.bbox[1] for s in nearby_spans) / len(nearby_spans)
    is_raised = span.bbox[1] < avg_y - 2

    return is_smaller and is_raised


def _is_numeric_footnote_marker(text: str) -> bool:
    """Check if text looks like a numeric footnote marker."""
    stripped = text.strip()
    return bool(re.match(r'^\d+$', stripped)) and len(stripped) <= 3


def _group_footnote_text(spans: list[Span], config: ToolConfig) -> list[list[Span]]:
    """Group footnote text spans by proximity and line."""
    if not spans:
        return []

    # Sort spans by y-coordinate (top to bottom) then x-coordinate
    sorted_spans = sorted(
        spans, key=lambda s: (-s.bbox[1], s.bbox[0])
    )  # Negative y for bottom-to-top

    groups = []
    current_group = [sorted_spans[0]]

    for span in sorted_spans[1:]:
        # Check if this span belongs to the current footnote group
        prev_span = current_group[-1]

        # Same line if y-coordinates are close
        y_diff = abs(span.bbox[1] - prev_span.bbox[1])
        is_same_line = y_diff <= config.line_merge_y_tolerance

        # Check if this starts a new footnote (has a leading number)
        starts_new_footnote = _extract_footnote_number(span) is not None

        if starts_new_footnote and current_group and not is_same_line:
            # Start new group
            groups.append(current_group)
            current_group = [span]
        elif is_same_line or (y_diff <= 15 and not starts_new_footnote):
            # Continue current group (multi-line footnote)
            current_group.append(span)
        else:
            # End current group and start new one
            if current_group:
                groups.append(current_group)
            current_group = [span]

    # Add the last group
    if current_group:
        groups.append(current_group)

    return groups


def _extract_footnote_number(span: Span) -> str | None:
    """Extract footnote number from the beginning of span text."""
    text = span.text.strip()
    match = re.match(r'^(\d+)', text)
    return match.group(1) if match else None


def _merge_footnote_text(spans: list[Span], config: ToolConfig) -> str:
    """Merge spans into footnote text, respecting merge configuration."""
    if not spans:
        return ""

    # Sort spans by reading order (y descending for footnotes, then x ascending)
    sorted_spans = sorted(spans, key=lambda s: (-s.bbox[1], s.bbox[0]))

    # Extract text from each span
    texts = []
    first_span_processed = False

    for span in sorted_spans:
        text = span.text.strip()
        # Remove leading footnote number from first span if present
        if not first_span_processed:
            text = re.sub(r'^\d+\s*', '', text)
            first_span_processed = True
        if text:  # Only add non-empty text
            texts.append(text)

    # Merge based on configuration
    if config.footnote_merge:
        # Merge all text into a single footnote
        return ' '.join(texts).strip()
    # Keep separate lines (for now, still merge but preserve line breaks)
    return ' '.join(texts).strip()
