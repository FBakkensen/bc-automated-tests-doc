from __future__ import annotations

import json
import pathlib

import yaml
from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator


class ToolConfig(BaseModel):
    font_cluster_epsilon: float = 1.0
    min_heading_font_size: float | None = None
    list_indent_tolerance: int = 6
    code_min_lines: int = 2
    code_indent_threshold: int = 4
    figure_caption_distance: int = 150
    # Caption scoring weights - must sum to 1.0
    caption_weight_distance: float = 0.4
    caption_weight_position: float = 0.3  # below-figure preference
    caption_weight_pattern: float = 0.3  # pattern matching (Fig., Figure, etc.)
    exclude_pages: list[int] = Field(default_factory=list)
    heading_normalize: bool = True
    slug_prefix_width: int = 2
    default_slug_fallback: str = "untitled"
    linkify_cross_references: bool = True
    table_confidence_min: float = 0.5
    image_format: str = "png"
    image_dpi: int = 200
    footnote_merge: bool = True
    language_detection: bool = False
    char_gap_threshold: float = 2.0
    bold_width_ratio_threshold: float = 0.8
    line_merge_y_tolerance: float = 3.0
    # Numbering configuration
    numbering_validate_gaps: bool = True
    numbering_allow_chapter_resets: bool = False
    numbering_max_depth: int = 6
    # Appendix configuration
    appendix_requires_page_break: bool = True

    @field_validator("caption_weight_distance", "caption_weight_position", "caption_weight_pattern")
    @classmethod
    def validate_caption_weights(cls, v: float, info: ValidationInfo) -> float:
        """Validate individual caption weights are between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Caption weight must be between 0.0 and 1.0, got {v}")
        return v

    @model_validator(mode="after")
    def validate_weights_sum(self) -> ToolConfig:
        """Validate that caption weights sum to 1.0."""
        total_weight = (
            self.caption_weight_distance
            + self.caption_weight_position
            + self.caption_weight_pattern
        )
        if abs(total_weight - 1.0) > 1e-6:  # Allow small floating point errors
            raise ValueError(
                f"Caption weights must sum to 1.0, got {total_weight:.6f} "
                f"(distance={self.caption_weight_distance}, "
                f"position={self.caption_weight_position}, "
                f"pattern={self.caption_weight_pattern})"
            )
        return self

    @classmethod
    def from_file(cls, path: str) -> ToolConfig:
        from .errors import ConfigParseError

        p = pathlib.Path(path)
        if not p.exists():
            raise ConfigParseError(f"Config file not found: {path}", {"path": path})

        try:
            text = p.read_text(encoding="utf-8")
            if p.suffix.lower() in {".yaml", ".yml"}:
                data = yaml.safe_load(text) or {}
            else:
                data = json.loads(text)
            return cls(**data)
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ConfigParseError(
                f"Failed to parse config file: {e}", {"path": path, "error": str(e)}
            ) from e
        except Exception as e:
            raise ConfigParseError(
                f"Unexpected error loading config: {e}", {"path": path, "error": str(e)}
            ) from e
