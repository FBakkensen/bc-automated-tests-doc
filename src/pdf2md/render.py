"""Minimal Markdown rendering for section files.

This module provides functionality to render SectionNode trees into
minimal Markdown stub files with proper filename generation following
the slug policy from the PRD.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import ToolConfig
    from .models import SectionNode


def generate_filename(section: SectionNode, prefix_index: int, config: ToolConfig) -> str:
    """Generate filename for a section following the slug policy.

    Args:
        section: SectionNode to generate filename for
        prefix_index: Index for filename prefix (zero-padded)
        config: Tool configuration containing slug_prefix_width

    Returns:
        Filename in format {prefix:0{width}d}_{slug}.md

    Examples:
        >>> section = SectionNode(title="Introduction", level=1, slug="introduction")
        >>> config = ToolConfig(slug_prefix_width=2)
        >>> generate_filename(section, 1, config)
        '01_introduction.md'
    """
    width = config.slug_prefix_width
    slug = section.slug or "untitled"
    return f"{prefix_index:0{width}d}_{slug}.md"


def render_section_stub(section: SectionNode) -> str:
    """Render a section as minimal Markdown stub with H1 heading only.

    Args:
        section: SectionNode to render

    Returns:
        Markdown content string with H1 heading

    Examples:
        >>> section = SectionNode(title="Introduction", level=1)
        >>> render_section_stub(section)
        '# Introduction\\n'
    """
    return f"# {section.title}\n"


def render_sections(
    sections: list[SectionNode],
    output_dir: Path,
    config: ToolConfig,
    *,
    book_subdir: str = "book",
) -> list[Path]:
    """Render sections to minimal Markdown stub files.

    Args:
        sections: List of SectionNode objects to render
        output_dir: Base output directory
        config: Tool configuration
        book_subdir: Subdirectory name for markdown files (default: "book")

    Returns:
        List of paths to written markdown files

    Raises:
        OSError: If directory creation or file writing fails
    """
    book_dir = output_dir / book_subdir
    book_dir.mkdir(parents=True, exist_ok=True)

    written_files = []

    # Flatten all sections in pre-order (parent before children)
    all_sections = _flatten_sections_preorder(sections)

    for i, section in enumerate(all_sections):
        prefix_index = i + 1  # 1-based indexing for filename prefixes
        filename = generate_filename(section, prefix_index, config)
        file_path = book_dir / filename

        content = render_section_stub(section)

        file_path.write_text(content, encoding="utf-8")
        written_files.append(file_path)

    return written_files


def _flatten_sections_preorder(sections: list[SectionNode]) -> list[SectionNode]:
    """Flatten section tree in pre-order traversal (parent before children).

    Args:
        sections: List of root SectionNode objects

    Returns:
        Flattened list of all SectionNode objects in pre-order
    """
    result = []

    def _visit(section: SectionNode) -> None:
        result.append(section)
        for child in section.children:
            _visit(child)

    for section in sections:
        _visit(section)

    return result
