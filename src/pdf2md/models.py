from __future__ import annotations

from dataclasses import dataclass, field

BBox = tuple[float, float, float, float]


@dataclass
class Span:
    text: str
    bbox: BBox
    font_name: str
    font_size: float
    style_flags: dict[str, bool]
    page: int
    order_index: int


@dataclass
class Node:
    type: str
    children: list[Node] = field(default_factory=list)
    meta: dict[str, object] = field(default_factory=dict)


@dataclass
class Figure:
    image_path: str
    caption: str | None
    alt: str | None
    page: int
    bbox: BBox


@dataclass
class CodeBlock:
    language: str | None
    lines: list[str]
    page_span: tuple[int, int]


@dataclass
class Table:
    rows: list[list[str]]
    page_span: tuple[int, int]
    confidence: float


@dataclass
class ManifestEntry:
    slug: str
    title: str
    level: int
    file: str
    parent: str | None
    pages: tuple[int, int]
