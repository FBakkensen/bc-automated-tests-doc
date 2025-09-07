from __future__ import annotations

from dataclasses import dataclass, field

BBox = tuple[float, float, float, float]


# Block type constants
class BlockType:
    PARAGRAPH = "Paragraph"
    LIST = "List"
    LIST_ITEM = "ListItem"
    CODE_BLOCK = "CodeBlock"
    TABLE = "Table"
    FIGURE_PLACEHOLDER = "FigurePlaceholder"
    FOOTNOTE_PLACEHOLDER = "FootnotePlaceholder"
    HEADING_CANDIDATE = "HeadingCandidate"
    EMPTY_LINE = "EmptyLine"
    RAW_NOISE = "RawNoise"
    CALLOUT = "Callout"


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
class Block:
    block_type: str
    spans: list[Span]
    bbox: BBox
    page_span: tuple[int, int]
    meta: dict[str, object] = field(default_factory=dict)


@dataclass
class SectionNode:
    """Hierarchical logical section (chapter/section) with support for freezing."""

    title: str
    level: int
    slug: str | None = None
    blocks: list[Block] = field(default_factory=list)
    children: list[SectionNode] = field(default_factory=list)
    pages: tuple[int, int] = (0, 0)
    meta: dict[str, object] = field(default_factory=dict)
    _frozen: bool = field(default=False, init=False)

    def freeze(self) -> None:
        """Freeze this node, making children and blocks lists immutable."""
        if not self._frozen:
            self._frozen = True
            # Freeze all children recursively
            for child in self.children:
                child.freeze()

    def is_frozen(self) -> bool:
        """Check if this node is frozen."""
        return self._frozen

    def add_child(self, child: SectionNode) -> None:
        """Add a child node. Raises ValueError if frozen."""
        if self._frozen:
            raise ValueError("Cannot modify frozen SectionNode")
        self.children.append(child)

    def add_block(self, block: Block) -> None:
        """Add a block. Raises ValueError if frozen."""
        if self._frozen:
            raise ValueError("Cannot modify frozen SectionNode")
        self.blocks.append(block)


@dataclass
class ManifestEntry:
    slug: str
    title: str
    level: int
    file: str
    parent: str | None
    pages: tuple[int, int]
