"""Line merging and text structure analysis for PDF spans.

This module provides functionality to merge spans into logical text lines,
repair hyphenation breaks across line boundaries, and assemble spans into
structured blocks (paragraphs, lists, code blocks, etc.).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, cast

from .utils import repair_hyphenation

if TYPE_CHECKING:
    from .config import ToolConfig
    from .models import Block, Span


# Pattern to match punctuation-only spans that should not have spaces before them
PUNCTUATION_ONLY_RE = re.compile(r'^[^\w\s]+$')

# Patterns for list item detection
BULLET_LIST_RE = re.compile(r"^\s*[•·▪▫‣-]\s+")
ORDERED_LIST_RE = re.compile(r'^\s*(\d+|[a-zA-Z]+)\.\s+')

# Pattern for potential table-like content (multiple columns separated by whitespace)
TABLE_PATTERN = re.compile(r'^\s*\S+(?:\s{2,}\S+)+\s*$')

# Constants for layout calculations
SPACE_WIDTH_ESTIMATE = 5  # Estimated width of a space character in points
POINTS_PER_NESTING_LEVEL = 25.0  # Points per indentation level for list nesting


def assemble_blocks(spans: list[Span], config: ToolConfig) -> list[Block]:
    """Assemble spans into logical blocks (paragraphs, lists, code blocks, etc.).

    Groups consecutive spans into structured blocks based on their content and layout.
    This includes detecting paragraphs, list items (bullet and numbered), code blocks
    based on indentation, and empty lines.

    Args:
        spans: List of Span objects to process, assumed to be sorted by order_index.
        config: ToolConfig instance containing block assembly parameters.

    Returns:
        List of Block objects representing the structured content.

    Examples:
        >>> from pdf2md.config import ToolConfig
        >>> config = ToolConfig()
        >>> spans = [
        ...     Span("Hello world", (0, 100, 100, 110), "Arial", 12, {}, 1, 0),
        ...     Span("This is a test", (0, 80, 120, 90), "Arial", 12, {}, 1, 1),
        ... ]
        >>> blocks = assemble_blocks(spans, config)
        >>> len(blocks)
        1
        >>> blocks[0].block_type
        'Paragraph'
    """
    if not spans:
        return []

    # Import here to avoid circular imports
    from .models import BlockType

    # Group spans into logical lines while preserving the original spans for each line
    line_groups = _group_spans_into_lines_with_spans(spans, config)
    if not line_groups:
        return []

    # Group line groups into blocks
    blocks = []
    current_block_line_groups: list[list[Span]] = []
    current_block_type: str | None = None
    i = 0

    while i < len(line_groups):
        line_group = line_groups[i]
        line_text = _join_spans_with_smart_spacing(line_group).strip()

        # Handle empty lines
        if not line_text:
            # Finish current block if any
            if current_block_line_groups and current_block_type is not None:
                block = _create_block_from_line_groups(
                    current_block_type, current_block_line_groups
                )
                if block:
                    blocks.append(block)
                current_block_line_groups = []
                current_block_type = None

            # Create empty line block
            empty_block = _create_empty_line_block()
            if empty_block:
                blocks.append(empty_block)
            i += 1
            continue

        # Determine line type using the original text with indentation preserved
        original_line_text = _join_spans_preserving_leading_whitespace(line_group)
        line_type = _classify_line_with_indentation(original_line_text, config)

        # Handle code blocks - check for monospace spans first, then indented lines
        if line_type == BlockType.CODE_BLOCK or _is_monospace_line(line_group):
            # Look ahead for consecutive code lines (either indented or monospace)
            code_line_groups, consumed = _extract_code_block_from_line_groups(
                line_groups, i, config
            )
            if len(code_line_groups) >= config.code_min_lines:
                # Finish current block if any
                if current_block_line_groups and current_block_type is not None:
                    block = _create_block_from_line_groups(
                        current_block_type, current_block_line_groups
                    )
                    if block:
                        blocks.append(block)
                    current_block_line_groups = []
                    current_block_type = None

                # Create code block
                code_block = _create_code_block_from_line_groups(code_line_groups)
                if code_block:
                    blocks.append(code_block)
                i += consumed
                continue
            # Not enough lines for code block, treat as regular text
            line_type = BlockType.PARAGRAPH

        # Check for potential table blocks - look ahead for table-like patterns
        if _could_be_table_line(line_group) and line_type == BlockType.PARAGRAPH:
            table_line_groups, consumed = _extract_potential_table_from_line_groups(
                line_groups, i, config
            )
            if len(table_line_groups) >= 2:  # Need at least 2 lines for a table
                table_block = _create_table_or_fallback_block(table_line_groups, config)
                if table_block:
                    # Finish current block if any
                    if current_block_line_groups and current_block_type is not None:
                        if (
                            current_block_type == BlockType.LIST
                            or current_block_type == BlockType.LIST_ITEM
                        ):
                            block = _create_nested_list_block(current_block_line_groups, config)
                        else:
                            block = _create_block_from_line_groups(
                                current_block_type, current_block_line_groups
                            )
                        if block:
                            blocks.append(block)
                        current_block_line_groups = []
                        current_block_type = None

                    blocks.append(table_block)
                    i += consumed
                    continue
            # Not enough lines for table, treat as regular text
            line_type = BlockType.PARAGRAPH

        # Handle block transitions
        if current_block_type is None:
            # Start new block
            current_block_type = line_type
            current_block_line_groups = [line_group]
        elif current_block_type == line_type or _can_continue_block(current_block_type, line_type):
            # Continue current block
            current_block_line_groups.append(line_group)
        else:
            # Block type changed, finish current block and start new one
            if current_block_type == BlockType.LIST or current_block_type == BlockType.LIST_ITEM:
                # Special handling for lists - process nesting
                block = _create_nested_list_block(current_block_line_groups, config)
            else:
                block = _create_block_from_line_groups(
                    current_block_type, current_block_line_groups
                )
            if block:
                blocks.append(block)

            current_block_type = line_type
            current_block_line_groups = [line_group]

        i += 1

    # Don't forget the last block
    if current_block_line_groups and current_block_type is not None:
        if current_block_type == BlockType.LIST or current_block_type == BlockType.LIST_ITEM:
            # Special handling for lists - process nesting
            block = _create_nested_list_block(current_block_line_groups, config)
        else:
            block = _create_block_from_line_groups(current_block_type, current_block_line_groups)
        if block:
            blocks.append(block)

    return blocks


def _group_spans_into_lines_with_spans(spans: list[Span], config: ToolConfig) -> list[list[Span]]:
    """Group spans into logical lines while preserving the span information.

    This is similar to merge_lines but returns groups of spans rather than merged text.

    Args:
        spans: List of spans to group.
        config: ToolConfig instance with line merging parameters.

    Returns:
        List of span groups, each representing a logical line.
    """
    return _group_spans_into_lines_ordered(spans, config.line_merge_y_tolerance)


def _classify_line_with_indentation(line: str, config: ToolConfig) -> str:
    """Classify a line into its block type based on content and formatting, preserving indentation.

    Args:
        line: The text line to classify (with original indentation preserved).
        config: ToolConfig instance containing classification parameters.

    Returns:
        Block type string (from BlockType constants).
    """
    from .models import BlockType

    stripped = line.strip()

    # Check for list items - be more conservative about ordered lists to avoid headings
    if BULLET_LIST_RE.match(stripped):
        return BlockType.LIST_ITEM

    # For ordered lists, add some heuristics to avoid false positives with headings
    if ORDERED_LIST_RE.match(stripped):
        # Get the leading indentation
        leading_spaces = len(line) - len(line.lstrip())

        # Extract the number and the rest of the text
        number_match = ORDERED_LIST_RE.match(stripped)
        if number_match:
            number_text = number_match.group()
            remaining_text = stripped[len(number_text) :].strip()

            # Very conservative check: only reject if it looks like a heading
            # - No indentation (starts at margin)
            # - Very short text (1-3 words)
            # - Starts with a capital letter
            # - Contains typical heading words like "Introduction", "Overview", "Summary"
            if (
                leading_spaces == 0
                and len(remaining_text.split()) <= 3
                and remaining_text
                and remaining_text[0].isupper()
                and any(
                    heading_word in remaining_text.lower()
                    for heading_word in [
                        'introduction',
                        'overview',
                        'summary',
                        'conclusion',
                        'abstract',
                        'background',
                        'methodology',
                        'results',
                    ]
                )
            ):
                return BlockType.PARAGRAPH
            return BlockType.LIST_ITEM

    # Check for code by indentation (using original line with whitespace)
    leading_spaces = len(line) - len(line.lstrip())
    if leading_spaces >= config.code_indent_threshold and stripped:  # Don't count empty lines
        return BlockType.CODE_BLOCK

    # Default to paragraph
    return BlockType.PARAGRAPH


def _is_monospace_line(line_spans: list[Span]) -> bool:
    """Check if a line consists primarily of monospace spans.

    Args:
        line_spans: List of spans in the line.

    Returns:
        True if the line should be considered monospace for code detection.
    """
    if not line_spans:
        return False

    # Consider a line monospace if most spans (by character count) are monospace
    total_chars = 0
    mono_chars = 0

    for span in line_spans:
        text = span.text.strip()
        if text:  # Only count non-empty spans
            total_chars += len(text)
            if span.style_flags.get("mono", False):
                mono_chars += len(text)

    # Line is monospace if at least 60% of characters are in monospace spans
    return total_chars > 0 and (mono_chars / total_chars) >= 0.6


def _extract_code_block_from_line_groups(
    line_groups: list[list[Span]], start_idx: int, config: ToolConfig
) -> tuple[list[list[Span]], int]:
    """Extract consecutive code line groups (indented or monospace) that form a code block.

    Args:
        line_groups: List of all line groups.
        start_idx: Index to start looking for code block.
        config: ToolConfig instance with code detection parameters.

    Returns:
        Tuple of (code_line_groups, number_of_line_groups_consumed).
    """
    code_line_groups = []
    i = start_idx

    while i < len(line_groups):
        line_group = line_groups[i]
        line_text = _join_spans_preserving_leading_whitespace(line_group)
        stripped = line_text.strip()

        # Empty lines are allowed in code blocks
        if not stripped:
            code_line_groups.append(line_group)
            i += 1
            continue

        # Check if line qualifies as code (either indented or monospace)
        leading_spaces = len(line_text) - len(line_text.lstrip())
        is_indented_code = leading_spaces >= config.code_indent_threshold
        is_monospace_code = _is_monospace_line(line_group)

        if is_indented_code or is_monospace_code:
            code_line_groups.append(line_group)
            i += 1
        else:
            # Non-code line ends the code block
            break

    return code_line_groups, i - start_idx


def _create_block_from_line_groups(block_type: str, line_groups: list[list[Span]]) -> Block | None:
    """Create a Block object from classified line groups.

    Args:
        block_type: Type of block to create.
        line_groups: List of span groups (lines) for the block.

    Returns:
        Block object or None if creation fails.
    """
    if not line_groups or not block_type:
        return None

    from .models import Block, BlockType

    # Flatten all spans from all line groups
    all_spans = []
    for line_group in line_groups:
        all_spans.extend(line_group)

    # Calculate bounding box and page span from spans
    if all_spans:
        bbox = _calculate_combined_bbox(all_spans)
        page_span = (min(s.page for s in all_spans), max(s.page for s in all_spans))
    else:
        # Fallback if no spans available
        bbox = (0.0, 0.0, 0.0, 0.0)
        page_span = (1, 1)

    # Create metadata based on block type
    meta: dict[str, object] = {}

    if block_type == BlockType.LIST_ITEM:
        # This should now be handled by _create_nested_list_block
        # But keep this as fallback for single items
        meta["list_level"] = 0
        block_type = BlockType.LIST
    elif block_type == BlockType.CODE_BLOCK:
        # Collect lines and remove leading indentation for code blocks
        code_lines = []
        for line_group in line_groups:
            line_text = _join_spans_preserving_leading_whitespace(line_group)
            code_lines.append(line_text)

        dedented_lines = _dedent_code_lines(code_lines)
        meta["code_language"] = None  # TODO: Implement language detection
        meta["dedented_lines"] = dedented_lines

    return Block(block_type=block_type, spans=all_spans, bbox=bbox, page_span=page_span, meta=meta)


def _create_code_block_from_line_groups(line_groups: list[list[Span]]) -> Block | None:
    """Create a CodeBlock from indented line groups.

    Args:
        line_groups: List of indented code line groups.

    Returns:
        CodeBlock Block object.
    """
    from .models import Block, BlockType

    if not line_groups:
        return None

    # Flatten all spans
    all_spans = []
    code_lines = []

    for line_group in line_groups:
        all_spans.extend(line_group)
        line_text = _join_spans_preserving_leading_whitespace(line_group)
        code_lines.append(line_text)

    # Remove common leading indentation
    dedented_lines = _dedent_code_lines(code_lines)

    # Calculate bbox and page span
    if all_spans:
        bbox = _calculate_combined_bbox(all_spans)
        page_span = (min(s.page for s in all_spans), max(s.page for s in all_spans))
    else:
        bbox = (0.0, 0.0, 0.0, 0.0)
        page_span = (1, 1)

    return Block(
        block_type=BlockType.CODE_BLOCK,
        spans=all_spans,
        bbox=bbox,
        page_span=page_span,
        meta={
            "code_language": None,  # TODO: Implement language detection
            "dedented_lines": dedented_lines,
        },
    )


def _can_continue_block(current_type: str, new_type: str) -> bool:
    """Check if a line of new_type can continue a block of current_type.

    Args:
        current_type: Current block type.
        new_type: Type of the new line.

    Returns:
        True if the line can be added to the current block.
    """
    from .models import BlockType

    # List items can continue list blocks
    if current_type == BlockType.LIST and new_type == BlockType.LIST_ITEM:
        return True

    # Same types can always continue
    return current_type == new_type


def _create_empty_line_block() -> Block | None:
    """Create an EmptyLine block.

    Returns:
        EmptyLine Block object.
    """
    from .models import Block, BlockType

    return Block(
        block_type=BlockType.EMPTY_LINE,
        spans=[],
        bbox=(0.0, 0.0, 0.0, 0.0),
        page_span=(1, 1),
        meta={},
    )


def _dedent_code_lines(lines: list[str]) -> list[str]:
    """Remove common leading indentation from code lines.

    Args:
        lines: List of code lines with indentation.

    Returns:
        List of lines with common indentation removed.
    """
    if not lines:
        return []

    # Find minimum indentation of non-empty lines
    min_indent = None
    for line in lines:
        stripped = line.strip()
        if stripped:  # Only consider non-empty lines
            leading_spaces = len(line) - len(line.lstrip())
            min_indent = leading_spaces if min_indent is None else min(min_indent, leading_spaces)

    if min_indent is None:
        min_indent = 0

    # Remove the common indentation
    dedented = []
    for line in lines:
        if line.strip():  # Non-empty line
            dedented.append(line[min_indent:])
        else:
            dedented.append("")  # Preserve empty lines

    return dedented


def _create_nested_list_block(line_groups: list[list[Span]], config: ToolConfig) -> Block | None:
    """Create a List block with proper nesting based on x-offset deltas.

    Args:
        line_groups: List of span groups, each representing a list item line.
        config: ToolConfig instance with list_indent_tolerance.

    Returns:
        Block object with nested list structure or None if creation fails.
    """
    if not line_groups:
        return None

    from .models import Block, BlockType

    # Flatten all spans
    all_spans = []
    for line_group in line_groups:
        all_spans.extend(line_group)

    # Calculate x-positions for each list item
    list_items = []
    for line_group in line_groups:
        x_pos = _get_list_item_x_position(line_group)
        list_items.append(
            {
                "spans": line_group,
                "x_position": x_pos,
                "level": 0,  # Will be calculated below
            }
        )

    # Calculate nesting levels based on x-position clusters
    _assign_nesting_levels(list_items, config.list_indent_tolerance)

    # Calculate bounding box and page span
    if all_spans:
        bbox = _calculate_combined_bbox(all_spans)
        page_span = (min(s.page for s in all_spans), max(s.page for s in all_spans))
    else:
        bbox = (0.0, 0.0, 0.0, 0.0)
        page_span = (1, 1)

    # Store the nested structure in metadata
    meta = {
        "list_items": list_items,
        "max_nesting_level": max((cast(int, item["level"]) for item in list_items), default=0),
    }

    return Block(
        block_type=BlockType.LIST, spans=all_spans, bbox=bbox, page_span=page_span, meta=meta
    )


def _get_list_item_x_position(line_spans: list[Span]) -> float:
    """Get the x-position of a list item's marker.

    Args:
        line_spans: Spans for the list item line.

    Returns:
        X-coordinate of the list marker.
    """
    if not line_spans:
        return 0.0

    # Find the span containing the list marker
    for span in line_spans:
        text = span.text.strip()
        if BULLET_LIST_RE.match(text) or ORDERED_LIST_RE.match(text):
            return span.bbox[0]  # x0 coordinate

    # Fallback: use the leftmost span
    return min(span.bbox[0] for span in line_spans)


def _assign_nesting_levels(list_items: list[dict[str, object]], tolerance: int) -> None:
    """Assign nesting levels to list items based on x-position clusters.

    Args:
        list_items: List of dicts with 'x_position' and 'level' keys.
        tolerance: Tolerance for x-position clustering.
    """
    if not list_items:
        return

    # Sort by x-position to find clusters
    sorted_items = sorted(list_items, key=lambda item: cast(float, item["x_position"]))

    # Find unique x-position clusters within tolerance
    clusters: list[dict[str, object]] = []
    for item in sorted_items:
        x_pos = cast(float, item["x_position"])

        # Find existing cluster within tolerance
        found_cluster = None
        for cluster in clusters:
            cluster_x_pos = cast(float, cluster["x_pos"])
            if abs(x_pos - cluster_x_pos) <= tolerance:
                found_cluster = cluster
                break

        if found_cluster:
            cluster_items = found_cluster["items"]
            if isinstance(cluster_items, list):
                cluster_items.append(item)
        else:
            clusters.append(
                {
                    "x_pos": x_pos,
                    "items": [item],
                    "level": len(clusters),  # Level based on order of discovery
                }
            )

    # Assign levels to items
    for cluster in clusters:
        cluster_items = cluster["items"]
        cluster_level = cast(int, cluster["level"])
        if isinstance(cluster_items, list):
            for item in cluster_items:
                item["level"] = cluster_level


def _could_be_table_line(line_spans: list[Span]) -> bool:
    """Check if a line could be part of a table based on layout heuristics.

    Args:
        line_spans: List of spans in the line.

    Returns:
        True if the line could be part of a table.
    """
    if not line_spans:
        return False

    # Join the line text and check against table pattern
    line_text = _join_spans_with_smart_spacing(line_spans)

    # Check if it matches table-like pattern (multiple columns)
    if TABLE_PATTERN.match(line_text):
        return True

    # Additional heuristic: check if spans are well-separated horizontally
    if len(line_spans) >= 2:
        # Sort spans by x-position
        sorted_spans = sorted(line_spans, key=lambda s: s.bbox[0])

        # Check for significant gaps between spans (potential column separators)
        gaps = []
        for i in range(len(sorted_spans) - 1):
            gap = sorted_spans[i + 1].bbox[0] - sorted_spans[i].bbox[2]  # Next x0 - current x1
            gaps.append(gap)

        # If there are significant gaps (> 10 points), it might be a table
        if gaps and max(gaps) > 10:
            return True

    return False


def _extract_potential_table_from_line_groups(
    line_groups: list[list[Span]], start_idx: int, config: ToolConfig
) -> tuple[list[list[Span]], int]:
    """Extract consecutive line groups that could form a table.

    Args:
        line_groups: List of all line groups.
        start_idx: Index to start looking for table.
        config: ToolConfig instance.

    Returns:
        Tuple of (table_line_groups, number_of_line_groups_consumed).
    """
    table_line_groups = []
    i = start_idx

    while i < len(line_groups):
        line_group = line_groups[i]
        line_text = _join_spans_with_smart_spacing(line_group).strip()

        # Empty lines break tables
        if not line_text:
            break

        # Check if line could be part of table
        if _could_be_table_line(line_group):
            table_line_groups.append(line_group)
            i += 1
        else:
            # Non-table line ends the table
            break

    return table_line_groups, i - start_idx


def _create_table_or_fallback_block(
    line_groups: list[list[Span]], config: ToolConfig
) -> Block | None:
    """Create a table block or fallback to fenced code block based on confidence.

    Args:
        line_groups: List of span groups that could form a table.
        config: ToolConfig instance with table_confidence_min.

    Returns:
        Block object (either Table or CodeBlock) or None if creation fails.
    """
    if not line_groups:
        return None

    from .models import Block, BlockType

    # Calculate table confidence
    confidence = _calculate_table_confidence(line_groups)

    # Flatten all spans
    all_spans = []
    for line_group in line_groups:
        all_spans.extend(line_group)

    # Calculate bounding box and page span
    if all_spans:
        bbox = _calculate_combined_bbox(all_spans)
        page_span = (min(s.page for s in all_spans), max(s.page for s in all_spans))
    else:
        bbox = (0.0, 0.0, 0.0, 0.0)
        page_span = (1, 1)

    if confidence >= config.table_confidence_min:
        # High confidence - create a proper table block
        table_rows = _extract_table_rows(line_groups)
        meta = {"table_rows": table_rows, "confidence": confidence, "format": "table"}
        return Block(
            block_type=BlockType.TABLE, spans=all_spans, bbox=bbox, page_span=page_span, meta=meta
        )
    # Low confidence - fallback to fenced code block
    code_lines = []
    for line_group in line_groups:
        line_text = _join_spans_preserving_leading_whitespace(line_group)
        code_lines.append(line_text)

    meta = {
        "code_language": None,
        "dedented_lines": code_lines,  # Don't dedent for table fallback
        "format": "fenced_fallback",
        "original_confidence": confidence,
    }
    return Block(
        block_type=BlockType.CODE_BLOCK,
        spans=all_spans,
        bbox=bbox,
        page_span=page_span,
        meta=meta,
    )


def _calculate_table_confidence(line_groups: list[list[Span]]) -> float:
    """Calculate confidence score for table detection.

    Args:
        line_groups: List of span groups to analyze.

    Returns:
        Confidence score between 0.0 and 1.0.
    """
    if not line_groups:
        return 0.0

    confidence_factors = []

    # Factor 1: Consistent number of columns
    column_counts = []
    for line_group in line_groups:
        line_text = _join_spans_with_original_spacing(line_group)
        # Count potential columns by splitting on multiple spaces
        columns = re.split(r'\s{2,}', line_text.strip())
        column_counts.append(len(columns))

    if column_counts:
        # Higher confidence if column counts are consistent
        most_common_count = max(set(column_counts), key=column_counts.count)
        consistency = column_counts.count(most_common_count) / len(column_counts)
        confidence_factors.append(consistency)

    # Factor 2: Multiple columns detected
    if column_counts and max(column_counts) >= 2:
        # More columns = higher confidence (up to a point)
        max_columns = max(column_counts)
        column_factor = min(1.0, max_columns / 4.0)  # Normalize to 1.0 at 4+ columns
        confidence_factors.append(column_factor)
    else:
        confidence_factors.append(0.0)

    # Factor 3: Number of rows (more rows = higher confidence)
    row_factor = min(1.0, len(line_groups) / 5.0)  # Normalize to 1.0 at 5+ rows
    confidence_factors.append(row_factor)

    # Factor 4: Alignment consistency (check if spans align vertically)
    alignment_factor = _calculate_alignment_factor(line_groups)
    confidence_factors.append(alignment_factor)

    # Average all factors
    if confidence_factors:
        return sum(confidence_factors) / len(confidence_factors)
    return 0.0


def _calculate_alignment_factor(line_groups: list[list[Span]]) -> float:
    """Calculate alignment consistency factor for table confidence.

    Args:
        line_groups: List of span groups to analyze.

    Returns:
        Alignment factor between 0.0 and 1.0.
    """
    if len(line_groups) < 2:
        return 0.0

    # Collect x-positions of spans across all lines
    x_positions = []
    for line_group in line_groups:
        line_x_positions = [span.bbox[0] for span in line_group]
        x_positions.append(line_x_positions)

    # Check for consistent alignment (x-positions that appear in multiple lines)
    alignment_tolerance = 5.0  # pixels
    alignment_scores = []

    for i, positions_i in enumerate(x_positions):
        for _j, positions_j in enumerate(x_positions[i + 1 :], i + 1):
            # Count aligned positions between lines i and j
            aligned_count = 0
            for pos_i in positions_i:
                for pos_j in positions_j:
                    if abs(pos_i - pos_j) <= alignment_tolerance:
                        aligned_count += 1
                        break

            # Score based on proportion of aligned positions
            max_positions = max(len(positions_i), len(positions_j))
            if max_positions > 0:
                alignment_scores.append(aligned_count / max_positions)

    return sum(alignment_scores) / len(alignment_scores) if alignment_scores else 0.0


def _join_spans_with_original_spacing(spans: list[Span]) -> str:
    """Join spans preserving original spacing between them based on bbox positions.

    This is useful for table detection where we need to preserve column separations.

    Args:
        spans: List of spans to join, assumed to be sorted by x-coordinate.

    Returns:
        Joined text with original spacing preserved.
    """
    if not spans:
        return ""

    # Sort spans by x-coordinate to ensure left-to-right order
    sorted_spans = sorted(spans, key=lambda s: s.bbox[0])

    result = ""
    for i, span in enumerate(sorted_spans):
        text = span.text.strip()
        if not text:
            continue

        if i == 0:
            # First span
            result = text
        else:
            # Calculate gap between previous span and current span
            prev_span = sorted_spans[i - 1]
            gap = span.bbox[0] - prev_span.bbox[2]  # Current x0 - previous x1

            # Convert gap to approximate number of spaces
            # Assume each space is about 4-6 points wide in typical fonts
            space_count = max(1, int(gap / SPACE_WIDTH_ESTIMATE))

            result += " " * space_count + text

    return result


def _extract_table_rows(line_groups: list[list[Span]]) -> list[list[str]]:
    """Extract table rows from line groups.

    Args:
        line_groups: List of span groups representing table lines.

    Returns:
        List of table rows, each row is a list of cell strings.
    """
    rows = []
    for line_group in line_groups:
        line_text = _join_spans_with_original_spacing(line_group)
        # Split on multiple spaces to get columns
        columns = re.split(r'\s{2,}', line_text.strip())
        # Clean up columns
        clean_columns = [col.strip() for col in columns if col.strip()]
        if clean_columns:
            rows.append(clean_columns)
    return rows


def _calculate_list_nesting_level(line_spans: list[Span], all_spans: list[Span]) -> int:
    """Calculate the nesting level of a list item based on x-offset.

    Args:
        line_spans: Spans for the list item line.
        all_spans: All spans in the document for baseline calculation.

    Returns:
        Nesting level (0 for top level, 1 for first nested, etc.).
    """
    if not line_spans:
        return 0

    # Find the leftmost x-position of the list marker
    # Look for the first span that contains list markers
    marker_x = None
    for span in line_spans:
        text = span.text.strip()
        if BULLET_LIST_RE.match(text) or ORDERED_LIST_RE.match(text):
            marker_x = span.bbox[0]  # x0 coordinate
            break

    if marker_x is None:
        # Fallback: use the leftmost span
        marker_x = min(span.bbox[0] for span in line_spans)

    # Find the baseline x-position (leftmost margin) from all spans
    baseline_x = min(span.bbox[0] for span in all_spans) if all_spans else 0.0

    # Calculate offset from baseline
    x_offset = marker_x - baseline_x

    # Convert offset to nesting level
    # Each level is approximately 20-30 points in typical PDFs
    # We'll use the configured default as a reasonable baseline
    return max(0, round(x_offset / POINTS_PER_NESTING_LEVEL))


def _calculate_combined_bbox(spans: list[Span]) -> tuple[float, float, float, float]:
    """Calculate the bounding box that encompasses all given spans.

    Args:
        spans: List of spans to combine.

    Returns:
        Combined bounding box as (x0, y0, x1, y1).
    """
    if not spans:
        return (0.0, 0.0, 0.0, 0.0)

    x0 = min(span.bbox[0] for span in spans)
    y0 = min(span.bbox[1] for span in spans)
    x1 = max(span.bbox[2] for span in spans)
    y1 = max(span.bbox[3] for span in spans)

    return (x0, y0, x1, y1)


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


def _join_spans_preserving_leading_whitespace(spans: list[Span]) -> str:
    """Join spans preserving leading whitespace from the first span.

    This function is used for block classification where leading indentation
    matters (e.g., code block detection).

    Args:
        spans: List of spans to join, assumed to be sorted by x-coordinate.

    Returns:
        Joined text with leading whitespace preserved.
    """
    if not spans:
        return ""

    result_parts = []
    for i, span in enumerate(spans):
        if i == 0:
            # First span preserves its original whitespace (including leading)
            text = span.text
            if not text.strip():  # Skip empty spans
                continue
            result_parts.append(text)
        else:
            # Subsequent spans get stripped and space-prefixed
            text = span.text.strip()
            if not text:
                continue

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
