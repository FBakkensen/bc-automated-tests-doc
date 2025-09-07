"""Heading detection and level assignment logic.

This module provides functionality to detect headings from text blocks
and assign appropriate levels based on patterns, font sizes, and other heuristics.
It integrates with the numbering module for chapter numbering and appendix detection.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .numbering import NumberingProcessor
from .utils import is_heading_candidate

if TYPE_CHECKING:
    from .config import ToolConfig
    from .models import Block


# Patterns for different heading types
CHAPTER_PATTERN = re.compile(r"^chapter\s+\d+", re.IGNORECASE)
PART_PATTERN = re.compile(r"^part\s+\w+", re.IGNORECASE)
APPENDIX_PATTERN = re.compile(r"^appendix\s+[a-zA-Z]", re.IGNORECASE)
DOTTED_PATTERN = re.compile(r"^\d+(?:\.\d+)*\b")


def detect_heading_level(text: str, config: ToolConfig) -> int | None:
    """Detect the heading level for a given text.

    Uses patterns and heuristics to determine if text is a heading
    and what level it should be assigned.

    Args:
        text: The text to analyze
        config: ToolConfig instance with heading detection settings

    Returns:
        Heading level (1-based) if text is a heading, None otherwise

    Examples:
        >>> from pdf2md.config import ToolConfig
        >>> config = ToolConfig()
        >>> detect_heading_level("Chapter 1 Introduction", config)
        1
        >>> detect_heading_level("1.2 Background", config)
        2
        >>> detect_heading_level("METHODOLOGY", config)
        1
        >>> detect_heading_level("Regular paragraph text", config)

    """
    # First check if it's a heading candidate at all
    if not is_heading_candidate(text):
        return None

    text_stripped = text.strip()

    # Pattern-based level detection
    if CHAPTER_PATTERN.match(text_stripped):
        return 1

    if PART_PATTERN.match(text_stripped):
        return 1

    if APPENDIX_PATTERN.match(text_stripped):
        return 1

    # Handle dotted numbering (1.2.3 format)
    dotted_match = DOTTED_PATTERN.match(text_stripped)
    if dotted_match:
        # Count the number of dots to determine depth
        dotted_text = dotted_match.group(0)
        level = dotted_text.count('.') + 1
        # Cap at reasonable level (6 levels max)
        return min(level, 6)

    # All-caps heuristic - treat as level 1 by default
    words = text_stripped.split()
    if words and all(word.isupper() and len(word) > 2 for word in words):
        return 1

    # If it passed is_heading_candidate but no specific pattern,
    # we should still return a level since it was deemed a candidate
    return 1


def assign_heading_levels(blocks: list[Block], config: ToolConfig) -> list[tuple[Block, int]]:
    """Assign heading levels to heading candidate blocks.

    Processes a list of blocks and identifies which ones are headings,
    assigning appropriate levels based on patterns and heuristics.
    Also applies numbering normalization and appendix detection.

    Args:
        blocks: List of Block objects to process
        config: ToolConfig instance with heading detection settings

    Returns:
        List of tuples (block, level) for blocks identified as headings

    Examples:
        >>> from pdf2md.config import ToolConfig
        >>> from pdf2md.models import Block, BlockType, Span
        >>> config = ToolConfig()
        >>> spans = [
        ...     Span(
        ...         "Chapter 1 Introduction", (0, 100, 200, 110), "Arial", 14, {"bold": True}, 1, 0
        ...     )
        ... ]
        >>> block = Block(BlockType.HEADING_CANDIDATE, spans, (0, 100, 200, 110), (1, 1), {})
        >>> headings = assign_heading_levels([block], config)
        >>> len(headings)
        1
        >>> headings[0][1]  # Level
        1
    """
    headings = []
    # Create numbering processor for this document
    numbering_processor = NumberingProcessor(config)

    for block in blocks:
        # Only process heading candidates
        if block.block_type != "HeadingCandidate":
            continue

        # Extract text from spans
        if not block.spans:
            continue

        text = " ".join(span.text for span in block.spans).strip()
        level = detect_heading_level(text, config)

        if level is not None:
            # Process numbering and attach metadata
            numbering_meta = numbering_processor.process_heading_block(block, text)

            # Merge numbering metadata into block's metadata
            block.meta.update(numbering_meta)

            headings.append((block, level))

    return headings
