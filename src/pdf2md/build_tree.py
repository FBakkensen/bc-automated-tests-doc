"""Tree building functionality for constructing hierarchical SectionNode trees.

This module provides functionality to build document trees from detected headings
and blocks, maintaining proper hierarchy and implementing freezing for immutability.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .headings import assign_heading_levels
from .utils import deterministic_slug

if TYPE_CHECKING:
    from .config import ToolConfig
    from .models import Block, SectionNode


def build_tree(blocks: list[Block], config: ToolConfig) -> list[SectionNode]:
    """Build a hierarchical tree of SectionNodes from blocks.

    Processes blocks to identify headings and build a properly nested
    tree structure with appropriate parent-child relationships.
    Children are guaranteed to follow parents in pre-order traversal.

    Args:
        blocks: List of Block objects to process
        config: ToolConfig instance with tree building settings

    Returns:
        List of root-level SectionNode objects representing the document tree

    Examples:
        >>> from pdf2md.config import ToolConfig
        >>> from pdf2md.models import Block, BlockType, Span
        >>> config = ToolConfig()
        >>> spans1 = [Span("Chapter 1", (0, 100, 100, 110), "Arial", 14, {"bold": True}, 1, 0)]
        >>> spans2 = [Span("1.1 Section", (0, 80, 100, 90), "Arial", 12, {"bold": True}, 1, 1)]
        >>> blocks = [
        ...     Block(BlockType.HEADING_CANDIDATE, spans1, (0, 100, 100, 110), (1, 1), {}),
        ...     Block(BlockType.HEADING_CANDIDATE, spans2, (0, 80, 100, 90), (1, 1), {})
        ... ]
        >>> tree = build_tree(blocks, config)
        >>> len(tree)
        1
        >>> len(tree[0].children)
        1
        >>> tree[0].level
        1
        >>> tree[0].children[0].level
        2
    """
    # Import here to avoid circular imports
    from .models import SectionNode

    # First, identify all headings with their levels
    headings = assign_heading_levels(blocks, config)

    if not headings:
        return []

    # Create SectionNode objects for each heading
    section_nodes = []
    block_indices = {}  # Map block indices to their corresponding sections

    for i, (block, level) in enumerate(headings):
        text = " ".join(span.text for span in block.spans).strip()

        # Create slug using deterministic_slug with prefix for ordering
        slug = deterministic_slug(text, prefix_index=i, width=config.slug_prefix_width)

        # Calculate page span from block
        if block.spans:
            first_page = min(span.page for span in block.spans)
            last_page = max(span.page for span in block.spans)
            pages = (first_page, last_page)
        else:
            pages = block.page_span

        section = SectionNode(
            title=text,
            level=level,
            slug=slug,
            blocks=[],  # Will be populated later
            children=[],
            pages=pages,
            meta={},
        )

        section_nodes.append(section)
        # Find the index of this block in the original blocks list
        block_index = blocks.index(block)
        block_indices[block_index] = section

    # Build the hierarchy by establishing parent-child relationships
    # We'll maintain a stack of ancestors to determine the correct parent
    root_sections = []
    ancestor_stack: list[SectionNode] = []

    for section in section_nodes:
        current_level = section.level

        # Pop ancestors until we find the correct parent level
        while ancestor_stack and ancestor_stack[-1].level >= current_level:
            ancestor_stack.pop()

        # Add to appropriate parent or root
        if ancestor_stack:
            parent = ancestor_stack[-1]
            parent.add_child(section)
        else:
            root_sections.append(section)

        # Add current section to ancestor stack
        ancestor_stack.append(section)

    # Now assign blocks to their appropriate sections
    # Blocks belong to the most recent heading before them
    current_section = None

    for i, block in enumerate(blocks):
        if i in block_indices:
            # This block is a heading, update current section
            current_section = block_indices[i]
        elif current_section is not None:
            # Regular block, add to current section
            current_section.add_block(block)

    # Freeze all sections to make them immutable
    for section in root_sections:
        section.freeze()

    return root_sections


def _traverse_preorder(sections: list[SectionNode]) -> list[SectionNode]:
    """Traverse sections in pre-order (parent before children).

    Helper function to verify pre-order traversal of the tree.

    Args:
        sections: List of root SectionNode objects

    Returns:
        List of all SectionNode objects in pre-order traversal
    """
    result = []

    def _visit(section: SectionNode) -> None:
        result.append(section)
        for child in section.children:
            _visit(child)

    for section in sections:
        _visit(section)

    return result
