"""Numbering and appendix detection logic for headings.

This module implements the PRD rules for global chapter numbering,
section gap detection, and appendix detection with page break rules.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import ToolConfig
    from .models import Block

# Patterns for heading extraction
CHAPTER_PATTERN = re.compile(r"^chapter\s+(\d+)", re.IGNORECASE)
PART_PATTERN = re.compile(r"^part\s+(\w+)", re.IGNORECASE)
APPENDIX_PATTERN = re.compile(r"^appendix\s+([a-zA-Z])", re.IGNORECASE)
DOTTED_PATTERN = re.compile(r"^(\d+(?:\.\d+)*)\b")

logger = logging.getLogger(__name__)


class NumberingProcessor:
    """Handles numbering normalization and validation for headings."""

    def __init__(self, config: ToolConfig) -> None:
        self.config = config
        self.global_chapter_counter = 0
        self.seen_chapter_numbers: set[int] = set()
        self.seen_appendix_letters: set[str] = set()
        self.first_chapter_detected = False
        # Track seen section paths for gap detection
        self.seen_section_paths: dict[tuple[int, ...], int] = {}

    def process_heading_block(self, block: Block, text: str) -> dict[str, object]:
        """Process a heading block and extract numbering information.

        Args:
            block: The heading block to process
            text: The heading text

        Returns:
            Meta dictionary with numbering information
        """
        meta: dict[str, object] = {}

        # Process chapter numbering
        chapter_match = CHAPTER_PATTERN.match(text.strip())
        if chapter_match:
            self.first_chapter_detected = True
            explicit_number = int(chapter_match.group(1))
            self._process_chapter_numbering(explicit_number, meta)

        # Process appendix detection
        appendix_match = APPENDIX_PATTERN.match(text.strip())
        if appendix_match:
            letter = appendix_match.group(1).upper()
            self._process_appendix_detection(block, letter, text, meta)

        # Process dotted section paths
        dotted_match = DOTTED_PATTERN.match(text.strip())
        if dotted_match:
            dotted_text = dotted_match.group(1)
            self._process_dotted_path(dotted_text, meta)

        return meta

    def _process_chapter_numbering(self, explicit_number: int, meta: dict[str, object]) -> None:
        """Process chapter numbering with global counter and reset detection."""
        # Check for duplicates only when resets are not allowed
        if (
            not self.config.numbering_allow_chapter_resets
            and explicit_number in self.seen_chapter_numbers
        ):
            logger.warning("duplicate_chapter_number", extra={"explicit_number": explicit_number})
            # Treat as implicit sequence (no explicit number in meta)
        else:
            self.seen_chapter_numbers.add(explicit_number)

        # Check for resets
        if (
            not self.config.numbering_allow_chapter_resets
            and explicit_number <= self.global_chapter_counter
        ):
            logger.warning(
                "chapter_number_reset_detected",
                extra={
                    "explicit_number": explicit_number,
                    "global_counter": self.global_chapter_counter,
                },
            )

        # Increment global counter and assign
        self.global_chapter_counter += 1
        meta["chapter_number"] = self.global_chapter_counter

    def _process_appendix_detection(
        self, block: Block, letter: str, text: str, meta: dict[str, object]
    ) -> None:
        """Process appendix detection with page break rule and ordering."""
        # Check if appendix appears before first chapter
        if not self.first_chapter_detected:
            logger.warning("appendix_early_ignored", extra={"letter": letter, "text": text})
            return

        # Check page break requirement
        if self.config.appendix_requires_page_break and not self._is_at_page_top(block):
            logger.warning("appendix_missing_page_break", extra={"letter": letter, "text": text})
            return

        # Check for duplicate letters
        if letter in self.seen_appendix_letters:
            logger.warning("appendix_duplicate_letter", extra={"letter": letter, "text": text})
            # Demote to regular section (don't add appendix_letter to meta)
            return

        # Check for out-of-order letters
        if self.seen_appendix_letters:
            last_letter = max(self.seen_appendix_letters, key=lambda letter_char: ord(letter_char))
            expected_letter = chr(ord(last_letter) + 1)
            if letter != expected_letter:
                logger.warning(
                    "appendix_out_of_order",
                    extra={"letter": letter, "expected": expected_letter},
                )

        self.seen_appendix_letters.add(letter)
        meta["appendix_letter"] = letter
        logger.info("appendix_detected", extra={"letter": letter})

    def _process_dotted_path(self, dotted_text: str, meta: dict[str, object]) -> None:
        """Process dotted section paths with gap detection and depth limits."""
        segments = [int(s) for s in dotted_text.split('.')]

        # Truncate depth if needed
        if len(segments) > self.config.numbering_max_depth:
            segments = segments[: self.config.numbering_max_depth]

        # Store section path
        meta["section_path"] = segments

        # Validate gaps if enabled
        if self.config.numbering_validate_gaps and len(segments) >= 2:
            self._check_section_gaps(segments)

    def _check_section_gaps(self, segments: list[int]) -> None:
        """Check for gaps in section numbering and log if found."""
        if len(segments) < 2:
            return

        # Track section paths to detect gaps
        section_tuple = tuple(segments)
        prefix = section_tuple[:-1]  # All but the last segment
        current_number = segments[-1]

        # Check if we've seen this prefix before
        if prefix in self.seen_section_paths:
            last_seen = self.seen_section_paths[prefix]
            # Check for gap: if current number is more than 1 greater than last seen
            if current_number > last_seen + 1:
                logger.warning(
                    "section_gap_detected",
                    extra={
                        "section_path": ".".join(map(str, segments)),
                        "current_section": current_number,
                        "previous_section": last_seen,
                        "gap_size": current_number - last_seen - 1,
                    },
                )

        # Update the highest seen number for this prefix
        self.seen_section_paths[prefix] = max(
            self.seen_section_paths.get(prefix, 0), current_number
        )

    def _is_at_page_top(self, block: Block) -> bool:
        """Check if a block is at the top of its page."""
        # Simple heuristic: check if the block's y-coordinate is near the top
        if block.spans:
            # Get the topmost y-coordinate of the block
            top_y = min(span.bbox[1] for span in block.spans)
            # Consider "top of page" as being within the top 20 pixels (arbitrary threshold)
            return top_y <= 20.0
        return False
