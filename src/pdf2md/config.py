from __future__ import annotations

import json
import pathlib

import yaml
from pydantic import BaseModel, Field


class ToolConfig(BaseModel):
    font_cluster_epsilon: float = 1.0
    min_heading_font_size: float | None = None
    list_indent_tolerance: int = 6
    code_min_lines: int = 2
    code_indent_threshold: int = 4
    figure_caption_distance: int = 150
    exclude_pages: list[int] = Field(default_factory=list)
    heading_normalize: bool = True
    slug_prefix_width: int = 2
    linkify_cross_references: bool = True
    table_confidence_min: float = 0.5
    image_format: str = "png"
    image_dpi: int = 200
    footnote_merge: bool = True
    language_detection: bool = False
    char_gap_threshold: float = 2.0
    bold_width_ratio_threshold: float = 0.8
    line_merge_y_tolerance: float = 3.0

    @classmethod
    def from_file(cls, path: str) -> ToolConfig:
        p = pathlib.Path(path)
        if not p.exists():
            raise FileNotFoundError(path)
        text = p.read_text(encoding="utf-8")
        if p.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(text) or {}
        else:
            data = json.loads(text)
        return cls(**data)
