"""PDF ingestion module for extracting Span objects with style flags and page info."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pdfplumber

from pdf2md.config import ToolConfig
from pdf2md.models import BBox, Span


class PdfIngestor:
    """Extracts ordered Span objects from PDF with style flags and page info."""

    def __init__(self, config: ToolConfig) -> None:
        """Initialize the PdfIngestor with configuration.

        Args:
            config: ToolConfig instance containing ingestion settings.
        """
        self.config = config

    def extract_spans(self, pdf_path: Path) -> list[Span]:
        """Extract spans from PDF with strictly increasing order_index.

        Args:
            pdf_path: Path to the PDF file to process.

        Returns:
            List of Span objects with order_index strictly increasing across all pages.

        Raises:
            FileNotFoundError: If PDF file doesn't exist.
            ValueError: If PDF cannot be read.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        spans: list[Span] = []
        order_index = 0

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    # Skip excluded pages
                    if page_num in self.config.exclude_pages:
                        continue

                    # Extract characters from page
                    chars = page.chars

                    # Group characters into text spans
                    page_spans = self._group_chars_into_spans(chars, page_num, order_index)
                    spans.extend(page_spans)
                    order_index += len(page_spans)

        except Exception as e:
            raise ValueError(f"Failed to read PDF {pdf_path}: {e}") from e

        return spans

    def _group_chars_into_spans(
        self, chars: list[dict[str, Any]], page_num: int, start_order_index: int
    ) -> list[Span]:
        """Group individual characters into text spans based on proximity and styling.

        Args:
            chars: List of character dictionaries from pdfplumber.
            page_num: Current page number (1-based).
            start_order_index: Starting order index for this page.

        Returns:
            List of Span objects for this page.
        """
        if not chars:
            return []

        spans: list[Span] = []
        current_span_chars: list[dict[str, Any]] = []
        current_font_name = ""
        current_font_size = 0.0
        order_index = start_order_index

        for char in chars:
            font_name = char.get("fontname", "")
            font_size = char.get("size", 0.0)

            # Start new span if font characteristics change or significant gap
            if (current_span_chars and
                (font_name != current_font_name or
                 abs(font_size - current_font_size) > 0.1 or
                 self._has_significant_gap(current_span_chars[-1], char))):

                # Finalize current span
                span = self._create_span_from_chars(current_span_chars, page_num, order_index)
                if span:
                    spans.append(span)
                    order_index += 1

                # Start new span
                current_span_chars = [char]
                current_font_name = font_name
                current_font_size = font_size
            else:
                # Add to current span
                current_span_chars.append(char)
                if not current_font_name:  # First character
                    current_font_name = font_name
                    current_font_size = font_size

        # Handle final span
        if current_span_chars:
            span = self._create_span_from_chars(current_span_chars, page_num, order_index)
            if span:
                spans.append(span)

        return spans

    def _has_significant_gap(self, char1: dict[str, Any], char2: dict[str, Any]) -> bool:
        """Check if there's a significant gap between two characters.

        Args:
            char1: First character dictionary.
            char2: Second character dictionary.

        Returns:
            True if there's a significant gap, False otherwise.
        """
        # Calculate horizontal gap
        x1_end = char1.get("x1", 0.0)
        x2_start = char2.get("x0", 0.0)
        gap = x2_start - x1_end

        # Consider gap significant if it's more than 2 character widths
        char_width = char1.get("width", 0.0)
        return bool(gap > char_width * 2)

    def _create_span_from_chars(
        self, chars: list[dict[str, Any]], page_num: int, order_index: int
    ) -> Span | None:
        """Create a Span object from a list of characters.

        Args:
            chars: List of character dictionaries.
            page_num: Page number (1-based).
            order_index: Order index for this span.

        Returns:
            Span object or None if no valid text.
        """
        if not chars:
            return None

        # Extract text
        text = "".join(char.get("text", "") for char in chars).strip()
        if not text:
            return None

        # Calculate bounding box
        x0 = min(char.get("x0", 0.0) for char in chars)
        y0 = min(char.get("y0", 0.0) for char in chars)
        x1 = max(char.get("x1", 0.0) for char in chars)
        y1 = max(char.get("y1", 0.0) for char in chars)
        bbox: BBox = (x0, y0, x1, y1)

        # Use first character's font info (should be consistent within span)
        first_char = chars[0]
        font_name = first_char.get("fontname", "")
        font_size = first_char.get("size", 0.0)

        # Detect style flags
        style_flags = self._detect_style_flags(font_name, chars)

        return Span(
            text=text,
            bbox=bbox,
            font_name=font_name,
            font_size=font_size,
            style_flags=style_flags,
            page=page_num,
            order_index=order_index,
        )

    def _detect_style_flags(self, font_name: str, chars: list[dict[str, Any]]) -> dict[str, bool]:
        """Detect style flags (bold, italic) from font characteristics.

        Args:
            font_name: Font name from character data.
            chars: List of character dictionaries for additional analysis.

        Returns:
            Dictionary with style flags (bold, italic).
        """
        style_flags = {"bold": False, "italic": False}

        if not font_name:
            return style_flags

        font_name_lower = font_name.lower()

        # Detect bold from font name
        bold_indicators = ["bold", "black", "heavy", "thick"]
        style_flags["bold"] = any(indicator in font_name_lower for indicator in bold_indicators)

        # Detect italic from font name
        italic_indicators = ["italic", "oblique", "slant"]
        style_flags["italic"] = any(indicator in font_name_lower for indicator in italic_indicators)

        # Additional heuristics based on character properties
        if chars:
            # Check for character-level style information if available
            first_char = chars[0]

            # Some PDFs store style in character attributes
            if "bold" in first_char:
                style_flags["bold"] = bool(first_char["bold"])
            if "italic" in first_char:
                style_flags["italic"] = bool(first_char["italic"])

            # Fallback: detect bold by font weight or width
            if "width" in first_char and first_char["width"] > 0:
                char_width = first_char["width"]
                font_size = first_char.get("size", 12)
                # Heuristic: bold text typically has wider characters relative to font size
                width_ratio = char_width / font_size if font_size > 0 else 0
                if width_ratio > 0.8:  # Threshold for detecting bold text
                    style_flags["bold"] = True

        return style_flags
