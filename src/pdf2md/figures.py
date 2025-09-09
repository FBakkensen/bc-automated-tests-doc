"""Figure extraction and caption binding functionality.

This module provides functionality to:
1. Extract figures from PDF pages
2. Detect caption candidates near figures
3. Score and bind captions to figures using weighted scoring
4. Generate deterministic figure IDs and file names with collision handling
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .models import BBox, Figure, Span
from .utils import deterministic_slug

if TYPE_CHECKING:
    from .config import ToolConfig

# Pattern for detecting figure captions (case insensitive)
CAPTION_PATTERN = re.compile(
    r"^\s*(?:fig(?:ure)?\.?\s*\d*|table\s*\d*|diagram\s*\d*)(?:\s*[:.]|\s|$)",
    re.IGNORECASE,
)


@dataclass
class CaptionCandidate:
    """A potential caption for a figure."""

    text: str
    bbox: BBox
    page: int
    spans: list[Span]
    score: float = 0.0


@dataclass
class FigureWithCandidates:
    """A figure with its potential caption candidates."""

    figure: Figure
    candidates: list[CaptionCandidate]
    final_caption: CaptionCandidate | None = None


def generate_figure_id(index: int, width: int = 3) -> str:
    """Generate figure ID with zero-padded format.

    Args:
        index: 0-based index position
        width: Width for zero-padding (default 3 for fig_001, fig_002, etc.)

    Returns:
        Figure ID in format "fig_NNN" with specified zero padding
    """
    return f"fig_{index:0{width}d}"


def generate_figure_filename(
    figure_id: str, caption: str | None, config: ToolConfig, used_filenames: set[str]
) -> str:
    """Generate deterministic figure filename with collision handling.

    Args:
        figure_id: Figure ID (e.g., "fig_001")
        caption: Figure caption text (optional)
        config: Tool configuration
        used_filenames: Set of already used filenames to check for collisions

    Returns:
        Unique filename with format "fig_001_caption-slug.png" or "fig_001.png"

    Examples:
        >>> config = ToolConfig()
        >>> used = set()
        >>> generate_figure_filename("fig_001", "Sample Chart", config, used)
        'fig_001_sample-chart.png'
        >>> used.add('fig_001_sample-chart.png')
        >>> generate_figure_filename("fig_002", "Sample Chart", config, used)
        'fig_002_sample-chart.png'
    """
    # Start with figure ID
    base_name = figure_id

    # Add caption slug if available
    if caption and caption.strip():
        caption_slug = deterministic_slug(caption.strip())
        if caption_slug:  # Only add if slug is not empty
            base_name = f"{base_name}_{caption_slug}"

    # Add image format extension
    filename = f"{base_name}.{config.image_format}"

    # Handle collisions by adding suffix
    if filename in used_filenames:
        base_without_ext = filename.rsplit(".", 1)[0]
        extension = filename.rsplit(".", 1)[1]
        counter = 2
        while True:
            new_filename = f"{base_without_ext}-{counter}.{extension}"
            if new_filename not in used_filenames:
                filename = new_filename
                break
            counter += 1

    used_filenames.add(filename)
    return filename


def detect_caption_candidates(
    spans: list[Span], figure: Figure, config: ToolConfig
) -> list[CaptionCandidate]:
    """Detect potential caption candidates near a figure.

    Args:
        spans: List of text spans from the document
        figure: Figure to find captions for
        config: Tool configuration

    Returns:
        List of caption candidates within the configured distance
    """
    candidates = []
    fig_x1, fig_y1, fig_x2, fig_y2 = figure.bbox

    for span in spans:
        # Skip spans not on the same page
        if span.page != figure.page:
            continue

        # Calculate distance from span to figure
        span_x1, span_y1, span_x2, span_y2 = span.bbox

        # Calculate minimum distance between span and figure bboxes
        horizontal_distance = max(0, max(span_x1 - fig_x2, fig_x1 - span_x2))
        vertical_distance = max(0, max(span_y1 - fig_y2, fig_y1 - span_y2))
        distance = (horizontal_distance**2 + vertical_distance**2) ** 0.5

        # Skip if too far away
        if distance > config.figure_caption_distance:
            continue

        # Create candidate
        candidate = CaptionCandidate(
            text=span.text,
            bbox=span.bbox,
            page=span.page,
            spans=[span],
        )
        candidates.append(candidate)

    return candidates


def score_caption_candidate(
    candidate: CaptionCandidate, figure: Figure, config: ToolConfig
) -> float:
    """Score a caption candidate using weighted scoring.

    Args:
        candidate: Caption candidate to score
        figure: Figure being captioned
        config: Tool configuration with scoring weights

    Returns:
        Score between 0.0 and 1.0 (higher is better)
    """
    # Distance component (closer is better)
    fig_x1, fig_y1, fig_x2, fig_y2 = figure.bbox
    cap_x1, cap_y1, cap_x2, cap_y2 = candidate.bbox

    horizontal_distance = max(0, max(cap_x1 - fig_x2, fig_x1 - cap_x2))
    vertical_distance = max(0, max(cap_y1 - fig_y2, fig_y1 - cap_y2))
    distance = (horizontal_distance**2 + vertical_distance**2) ** 0.5

    # Normalize distance score (1.0 at distance 0, 0.0 at max distance)
    distance_score = max(0.0, 1.0 - (distance / config.figure_caption_distance))

    # Position component (below figure is preferred)
    cap_center_y = (cap_y1 + cap_y2) / 2
    fig_center_y = (fig_y1 + fig_y2) / 2

    # Check if caption is below figure (higher Y values are lower on page in PDF coordinates)
    is_below = cap_center_y > fig_center_y
    position_score = 1.0 if is_below else 0.5  # Prefer below, but don't completely exclude above

    # Pattern component (matches "Fig.", "Figure", etc.)
    pattern_score = 1.0 if CAPTION_PATTERN.match(candidate.text.strip()) else 0.3

    # Weighted sum
    total_score = (
        config.caption_weight_distance * distance_score
        + config.caption_weight_position * position_score
        + config.caption_weight_pattern * pattern_score
    )

    return float(min(1.0, max(0.0, total_score)))  # Ensure score is in [0, 1]


def bind_captions_to_figures(
    figures: list[Figure], spans: list[Span], config: ToolConfig
) -> list[FigureWithCandidates]:
    """Bind captions to figures using weighted scoring and tie-breaking.

    Args:
        figures: List of figures to caption
        spans: List of text spans from the document
        config: Tool configuration

    Returns:
        List of figures with their best caption candidates
    """
    figures_with_candidates = []

    for figure in figures:
        # Find caption candidates
        candidates = detect_caption_candidates(spans, figure, config)

        # Score each candidate
        for candidate in candidates:
            candidate.score = score_caption_candidate(candidate, figure, config)

        # Sort candidates by score (highest first), then apply tie-breaking
        candidates.sort(
            key=lambda c: (
                c.score,  # Primary: highest score
                _is_below_figure(c, figure),  # Secondary: below-figure preference
                _has_pattern_match(c),  # Tertiary: pattern match preference
                -_distance_to_figure(c, figure),  # Quaternary: closer distance (negative for desc)
            ),
            reverse=True,
        )

        # Select best candidate
        final_caption = candidates[0] if candidates else None

        figure_with_candidates = FigureWithCandidates(
            figure=figure,
            candidates=candidates,
            final_caption=final_caption,
        )
        figures_with_candidates.append(figure_with_candidates)

    return figures_with_candidates


def _is_below_figure(candidate: CaptionCandidate, figure: Figure) -> bool:
    """Check if candidate is below the figure."""
    cap_center_y = (candidate.bbox[1] + candidate.bbox[3]) / 2
    fig_center_y = (figure.bbox[1] + figure.bbox[3]) / 2
    return cap_center_y > fig_center_y


def _has_pattern_match(candidate: CaptionCandidate) -> bool:
    """Check if candidate matches caption pattern."""
    return bool(CAPTION_PATTERN.match(candidate.text.strip()))


def _distance_to_figure(candidate: CaptionCandidate, figure: Figure) -> float:
    """Calculate distance from candidate to figure."""
    fig_x1, fig_y1, fig_x2, fig_y2 = figure.bbox
    cap_x1, cap_y1, cap_x2, cap_y2 = candidate.bbox

    horizontal_distance = max(0, max(cap_x1 - fig_x2, fig_x1 - cap_x2))
    vertical_distance = max(0, max(cap_y1 - fig_y2, fig_y1 - cap_y2))
    return float((horizontal_distance**2 + vertical_distance**2) ** 0.5)


def build_figure_projections(figures: list[Figure], filenames: list[str]) -> list[dict[str, Any]]:
    """Build figure projections for manifest from figures and pre-generated filenames.

    This function creates manifest entries by combining Figure objects with their
    corresponding pre-generated filenames. Figure IDs are generated based on the
    position in the list (fig_000, fig_001, etc.) and should match the IDs used
    in the filename generation process.

    Args:
        figures: List of Figure objects in display order
        filenames: List of corresponding filenames (generated elsewhere using
                  generate_figure_filename with matching indices)

    Returns:
        List of figure projection dicts for manifest, each containing:
        - id: Generated figure ID (fig_000, fig_001, etc.)
        - filename: The pre-generated filename
        - caption: Figure caption or empty string
        - alt: Alt text or empty string
        - page: Page number
        - bbox: Bounding box as list
    """
    projections = []

    for i, (figure, filename) in enumerate(zip(figures, filenames, strict=True)):
        figure_id = generate_figure_id(i)

        projection = {
            "id": figure_id,
            "filename": filename,
            "caption": figure.caption or "",
            "alt": figure.alt or "",
            "page": figure.page,
            "bbox": list(figure.bbox),  # Convert tuple to list for JSON
        }
        projections.append(projection)

    return projections


def process_figures_with_captions(
    figures: list[Figure], spans: list[Span], config: ToolConfig
) -> tuple[list[Figure], list[str]]:
    """Process figures with caption binding and generate filenames.

    Args:
        figures: List of figures to process
        spans: List of text spans for caption detection
        config: Tool configuration

    Returns:
        Tuple of (updated_figures_list, filenames_list)
    """
    # Bind captions to figures
    figures_with_candidates = bind_captions_to_figures(figures, spans, config)

    # Generate figure IDs and filenames
    updated_figures = []
    filenames = []
    used_filenames: set[str] = set()

    for i, figure_with_candidate in enumerate(figures_with_candidates):
        figure = figure_with_candidate.figure
        final_caption = figure_with_candidate.final_caption

        # Generate figure ID
        figure_id = generate_figure_id(i)

        # Update figure with caption
        caption_text = final_caption.text if final_caption else None
        updated_figure = Figure(
            image_path=figure.image_path,
            caption=caption_text,
            alt=figure.alt,
            page=figure.page,
            bbox=figure.bbox,
        )

        # Generate filename
        filename = generate_figure_filename(figure_id, caption_text, config, used_filenames)

        updated_figures.append(updated_figure)
        filenames.append(filename)

    return updated_figures, filenames
