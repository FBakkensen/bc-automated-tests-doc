from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple

BBox = Tuple[float, float, float, float]

@dataclass
class Span:
    text: str
    bbox: BBox
    font_name: str
    font_size: float
    style_flags: Dict[str, bool]
    page: int

@dataclass
class Node:
    type: str
    children: List["Node"] = field(default_factory=list)
    meta: Dict[str, object] = field(default_factory=dict)

@dataclass
class Figure:
    image_path: str
    caption: Optional[str]
    alt: Optional[str]
    page: int
    bbox: BBox

@dataclass
class CodeBlock:
    language: Optional[str]
    lines: List[str]
    page_span: Tuple[int, int]

@dataclass
class Table:
    rows: List[List[str]]
    page_span: Tuple[int, int]
    confidence: float

@dataclass
class ManifestEntry:
    slug: str
    title: str
    level: int
    file: str
    parent: Optional[str]
    pages: Tuple[int, int]
