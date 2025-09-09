"""Tests for figure extraction and caption binding functionality."""

from __future__ import annotations

import pytest

from pdf2md.config import ToolConfig
from pdf2md.figures import (
    CaptionCandidate,
    bind_captions_to_figures,
    build_figure_projections,
    detect_caption_candidates,
    generate_figure_filename,
    generate_figure_id,
    score_caption_candidate,
)
from pdf2md.models import Figure, Span


@pytest.fixture
def config() -> ToolConfig:
    """Create test configuration with known weights."""
    return ToolConfig(
        caption_weight_distance=0.4,
        caption_weight_position=0.3,
        caption_weight_pattern=0.3,
        figure_caption_distance=150,
        image_format="png",
    )


@pytest.fixture
def sample_figure() -> Figure:
    """Create a sample figure for testing."""
    return Figure(
        image_path="sample.png",
        caption=None,
        alt=None,
        page=1,
        bbox=(100, 100, 200, 200),  # x1, y1, x2, y2
    )


def test_generate_figure_id_zero_padding() -> None:
    """Test that figure IDs are generated with proper zero padding."""
    assert generate_figure_id(0) == "fig_000"
    assert generate_figure_id(1) == "fig_001"
    assert generate_figure_id(2) == "fig_002"
    assert generate_figure_id(99) == "fig_099"
    assert generate_figure_id(999) == "fig_999"


def test_generate_figure_id_custom_width() -> None:
    """Test figure ID generation with custom width."""
    assert generate_figure_id(0, width=2) == "fig_00"
    assert generate_figure_id(5, width=4) == "fig_0005"


def test_generate_figure_filename_with_caption(config: ToolConfig) -> None:
    """Test figure filename generation with caption."""
    used_filenames: set[str] = set()
    filename = generate_figure_filename("fig_001", "Sample Chart Data", config, used_filenames)
    assert filename == "fig_001_sample-chart-data.png"
    assert filename in used_filenames


def test_generate_figure_filename_without_caption(config: ToolConfig) -> None:
    """Test figure filename generation without caption."""
    used_filenames: set[str] = set()
    filename = generate_figure_filename("fig_001", None, config, used_filenames)
    assert filename == "fig_001.png"


def test_generate_figure_filename_collision_handling(config: ToolConfig) -> None:
    """Test that filename collisions are handled with numeric suffixes."""
    used_filenames: set[str] = set()

    # Add the first file
    filename1 = generate_figure_filename("fig_001", "Test Chart", config, used_filenames)
    assert filename1 == "fig_001_test-chart.png"

    # Simulate collision by pre-adding the same filename pattern
    used_filenames.add("fig_002_test-chart.png")

    # Now generate for a different figure with same caption - should get collision suffix
    filename2 = generate_figure_filename("fig_002", "Test Chart", config, used_filenames)
    assert filename2 == "fig_002_test-chart-2.png"


def test_generate_figure_filename_empty_caption(config: ToolConfig) -> None:
    """Test figure filename generation with empty caption."""
    used_filenames: set[str] = set()
    filename = generate_figure_filename("fig_001", "", config, used_filenames)
    assert filename == "fig_001.png"

    # Use different figure ID to avoid collision
    filename2 = generate_figure_filename("fig_002", "   ", config, used_filenames)
    assert filename2 == "fig_002.png"


def test_detect_caption_candidates_same_page(config: ToolConfig, sample_figure: Figure) -> None:
    """Test caption candidate detection on same page."""
    spans = [
        Span(
            text="Figure 1: Sample chart showing data trends",
            bbox=(90, 220, 210, 240),  # Below the figure
            font_name="Arial",
            font_size=10,
            style_flags={},
            page=1,
            order_index=1,
        ),
        Span(
            text="This is unrelated text far away",
            bbox=(500, 500, 600, 520),  # Far from figure
            font_name="Arial",
            font_size=10,
            style_flags={},
            page=1,
            order_index=2,
        ),
    ]

    candidates = detect_caption_candidates(spans, sample_figure, config)
    assert len(candidates) == 1
    assert candidates[0].text == "Figure 1: Sample chart showing data trends"


def test_detect_caption_candidates_different_page(
    config: ToolConfig, sample_figure: Figure
) -> None:
    """Test that candidates on different pages are excluded."""
    spans = [
        Span(
            text="Figure 1: This is on a different page",
            bbox=(90, 220, 210, 240),
            font_name="Arial",
            font_size=10,
            style_flags={},
            page=2,  # Different page
            order_index=1,
        ),
    ]

    candidates = detect_caption_candidates(spans, sample_figure, config)
    assert len(candidates) == 0


def test_detect_caption_candidates_distance_filtering(
    config: ToolConfig, sample_figure: Figure
) -> None:
    """Test that candidates too far away are filtered out."""
    spans = [
        Span(
            text="Figure 1: Close caption",
            bbox=(90, 220, 210, 240),  # Close to figure
            font_name="Arial",
            font_size=10,
            style_flags={},
            page=1,
            order_index=1,
        ),
        Span(
            text="Figure 2: Far caption",
            bbox=(500, 500, 600, 520),  # Far from figure
            font_name="Arial",
            font_size=10,
            style_flags={},
            page=1,
            order_index=2,
        ),
    ]

    candidates = detect_caption_candidates(spans, sample_figure, config)
    assert len(candidates) == 1
    assert candidates[0].text == "Figure 1: Close caption"


def test_score_caption_candidate_distance_component(
    config: ToolConfig, sample_figure: Figure
) -> None:
    """Test distance component of caption scoring."""
    # Close candidate
    close_candidate = CaptionCandidate(
        text="Figure 1: Close caption",
        bbox=(90, 220, 210, 240),  # Very close
        page=1,
        spans=[],
    )

    # Far candidate (but still within distance threshold)
    far_candidate = CaptionCandidate(
        text="Figure 2: Far caption",
        bbox=(90, 280, 210, 300),  # Further away
        page=1,
        spans=[],
    )

    close_score = score_caption_candidate(close_candidate, sample_figure, config)
    far_score = score_caption_candidate(far_candidate, sample_figure, config)

    # Close candidate should score higher due to distance component
    assert close_score > far_score


def test_score_caption_candidate_position_component(
    config: ToolConfig, sample_figure: Figure
) -> None:
    """Test position component of caption scoring (below-figure preference)."""
    # Below figure candidate (higher Y in PDF coordinates)
    below_candidate = CaptionCandidate(
        text="Caption below figure",
        bbox=(90, 220, 210, 240),  # Below figure (y > 200)
        page=1,
        spans=[],
    )

    # Above figure candidate (lower Y in PDF coordinates)
    above_candidate = CaptionCandidate(
        text="Caption above figure",
        bbox=(90, 80, 210, 100),  # Above figure (y < 100)
        page=1,
        spans=[],
    )

    below_score = score_caption_candidate(below_candidate, sample_figure, config)
    above_score = score_caption_candidate(above_candidate, sample_figure, config)

    # Below candidate should score higher due to position preference
    assert below_score > above_score


def test_score_caption_candidate_pattern_component(
    config: ToolConfig, sample_figure: Figure
) -> None:
    """Test pattern component of caption scoring."""
    # Pattern matching candidate
    pattern_candidate = CaptionCandidate(
        text="Figure 1: This matches the pattern",
        bbox=(90, 220, 210, 240),
        page=1,
        spans=[],
    )

    # Non-pattern candidate
    no_pattern_candidate = CaptionCandidate(
        text="This does not match any pattern",
        bbox=(90, 220, 210, 240),  # Same position for fair comparison
        page=1,
        spans=[],
    )

    pattern_score = score_caption_candidate(pattern_candidate, sample_figure, config)
    no_pattern_score = score_caption_candidate(no_pattern_candidate, sample_figure, config)

    # Pattern candidate should score higher
    assert pattern_score > no_pattern_score


def test_score_caption_candidate_pattern_variations(
    config: ToolConfig, sample_figure: Figure
) -> None:
    """Test that various caption patterns are recognized."""
    test_cases = [
        ("Figure 1:", True),
        ("Fig. 2:", True),
        ("fig 3:", True),
        ("FIGURE 4:", True),
        ("Table 1:", True),
        ("Diagram 5:", True),
        ("Figure:", True),  # Unnumbered caption
        ("Fig.", True),  # Unnumbered caption
        ("Table:", True),  # Unnumbered caption
        ("Diagram:", True),  # Unnumbered caption
        ("Random text", False),
        ("Figures are important", False),  # Should not match mid-word
    ]

    for text, should_match in test_cases:
        candidate = CaptionCandidate(
            text=text,
            bbox=(90, 220, 210, 240),
            page=1,
            spans=[],
        )

        score = score_caption_candidate(candidate, sample_figure, config)

        # Calculate actual distance between candidate and figure
        fig_x1, fig_y1, fig_x2, fig_y2 = sample_figure.bbox
        cap_x1, cap_y1, cap_x2, cap_y2 = candidate.bbox
        horizontal_distance = max(0, max(cap_x1 - fig_x2, fig_x1 - cap_x2))
        vertical_distance = max(0, max(cap_y1 - fig_y2, fig_y1 - cap_y2))
        actual_distance = (horizontal_distance**2 + vertical_distance**2) ** 0.5

        # Extract pattern component from total score
        # Pattern component = (score - distance_component - position_component) / pattern_weight
        distance_score = 1.0 - (actual_distance / config.figure_caption_distance)
        position_score = 1.0  # Below figure
        expected_score_without_pattern = (
            config.caption_weight_distance * distance_score
            + config.caption_weight_position * position_score
        )

        if should_match:
            # Should include full pattern weight
            expected_total = expected_score_without_pattern + config.caption_weight_pattern * 1.0
            assert abs(score - expected_total) < 0.01, f"Pattern '{text}' should match"
        else:
            # Should include reduced pattern weight
            expected_total = expected_score_without_pattern + config.caption_weight_pattern * 0.3
            assert abs(score - expected_total) < 0.01, f"Pattern '{text}' should not match"


def test_bind_captions_to_figures_simple_case(config: ToolConfig) -> None:
    """Test basic caption binding with single figure and caption."""
    figures = [
        Figure(
            image_path="test.png",
            caption=None,
            alt=None,
            page=1,
            bbox=(100, 100, 200, 200),
        )
    ]

    spans = [
        Span(
            text="Figure 1: Test caption",
            bbox=(90, 220, 210, 240),
            font_name="Arial",
            font_size=10,
            style_flags={},
            page=1,
            order_index=1,
        )
    ]

    result = bind_captions_to_figures(figures, spans, config)
    assert len(result) == 1
    assert result[0].final_caption is not None
    assert result[0].final_caption.text == "Figure 1: Test caption"


def test_bind_captions_to_figures_tie_break_below_wins(config: ToolConfig) -> None:
    """Test tie-breaking where below-figure candidate with pattern wins."""
    figure = Figure(
        image_path="test.png",
        caption=None,
        alt=None,
        page=1,
        bbox=(100, 100, 200, 200),
    )

    spans = [
        # Above figure, with pattern - same distance
        Span(
            text="Figure 1: Above caption",
            bbox=(90, 80, 210, 100),  # Above
            font_name="Arial",
            font_size=10,
            style_flags={},
            page=1,
            order_index=1,
        ),
        # Below figure, with pattern - same distance
        Span(
            text="Figure 2: Below caption",
            bbox=(90, 220, 210, 240),  # Below
            font_name="Arial",
            font_size=10,
            style_flags={},
            page=1,
            order_index=2,
        ),
    ]

    result = bind_captions_to_figures([figure], spans, config)

    # Below candidate should win due to position preference
    assert result[0].final_caption is not None
    assert result[0].final_caption.text == "Figure 2: Below caption"


def test_bind_captions_to_figures_multiple_figures(config: ToolConfig) -> None:
    """Test caption binding with multiple figures."""
    figures = [
        Figure(
            image_path="test1.png",
            caption=None,
            alt=None,
            page=1,
            bbox=(100, 100, 200, 200),
        ),
        Figure(
            image_path="test2.png",
            caption=None,
            alt=None,
            page=1,
            bbox=(300, 100, 400, 200),
        ),
    ]

    spans = [
        Span(
            text="Figure 1: First caption",
            bbox=(90, 220, 210, 240),  # Near first figure
            font_name="Arial",
            font_size=10,
            style_flags={},
            page=1,
            order_index=1,
        ),
        Span(
            text="Figure 2: Second caption",
            bbox=(290, 220, 410, 240),  # Near second figure
            font_name="Arial",
            font_size=10,
            style_flags={},
            page=1,
            order_index=2,
        ),
    ]

    result = bind_captions_to_figures(figures, spans, config)
    assert len(result) == 2

    # First figure should get first caption
    assert result[0].final_caption is not None
    assert result[0].final_caption.text == "Figure 1: First caption"

    # Second figure should get second caption
    assert result[1].final_caption is not None
    assert result[1].final_caption.text == "Figure 2: Second caption"


def test_bind_captions_to_figures_no_candidates(config: ToolConfig) -> None:
    """Test figure with no caption candidates."""
    figures = [
        Figure(
            image_path="test.png",
            caption=None,
            alt=None,
            page=1,
            bbox=(100, 100, 200, 200),
        )
    ]

    spans: list[Span] = []  # No spans

    result = bind_captions_to_figures(figures, spans, config)
    assert len(result) == 1
    assert result[0].final_caption is None


def test_config_validation_weights_sum_to_one() -> None:
    """Test that caption weights must sum to 1.0."""
    # Valid weights
    config = ToolConfig(
        caption_weight_distance=0.4,
        caption_weight_position=0.3,
        caption_weight_pattern=0.3,
    )
    assert config.caption_weight_distance == 0.4

    # Invalid weights - don't sum to 1.0
    with pytest.raises(ValueError, match="Caption weights must sum to 1.0"):
        ToolConfig(
            caption_weight_distance=0.5,
            caption_weight_position=0.3,
            caption_weight_pattern=0.3,  # Total = 1.1
        )


def test_config_validation_individual_weights_range() -> None:
    """Test that individual caption weights must be between 0 and 1."""
    # Invalid weight - negative
    with pytest.raises(ValueError, match="Caption weight must be between 0.0 and 1.0"):
        ToolConfig(
            caption_weight_distance=-0.1,
            caption_weight_position=0.6,
            caption_weight_pattern=0.5,
        )

    # Invalid weight - greater than 1
    with pytest.raises(ValueError, match="Caption weight must be between 0.0 and 1.0"):
        ToolConfig(
            caption_weight_distance=1.2,
            caption_weight_position=0.0,
            caption_weight_pattern=-0.2,
        )


def test_config_validation_floating_point_tolerance() -> None:
    """Test that small floating point errors in weight sum are tolerated."""
    # Should work with small floating point error
    config = ToolConfig(
        caption_weight_distance=0.333333,
        caption_weight_position=0.333333,
        caption_weight_pattern=0.333334,  # Sum = 1.000000 (within tolerance)
    )
    assert config.caption_weight_distance == 0.333333


def test_build_figure_projections() -> None:
    """Test building figure projections for manifest."""
    figures = [
        Figure(
            image_path="test1.png",
            caption="Figure 1: First test image",
            alt="Alt text for first image",
            page=1,
            bbox=(100, 100, 200, 200),
        ),
        Figure(
            image_path="test2.png",
            caption=None,  # No caption
            alt=None,  # No alt text
            page=2,
            bbox=(150, 150, 250, 250),
        ),
    ]

    filenames = ["fig_000_first-test-image.png", "fig_001.png"]

    projections = build_figure_projections(figures, filenames)

    assert len(projections) == 2

    # First figure projection
    assert projections[0]["id"] == "fig_000"
    assert projections[0]["filename"] == "fig_000_first-test-image.png"
    assert projections[0]["caption"] == "Figure 1: First test image"
    assert projections[0]["alt"] == "Alt text for first image"
    assert projections[0]["page"] == 1
    assert projections[0]["bbox"] == [100, 100, 200, 200]

    # Second figure projection
    assert projections[1]["id"] == "fig_001"
    assert projections[1]["filename"] == "fig_001.png"
    assert projections[1]["caption"] == ""  # Empty string for None caption
    assert projections[1]["alt"] == ""  # Empty string for None alt
    assert projections[1]["page"] == 2
    assert projections[1]["bbox"] == [150, 150, 250, 250]
