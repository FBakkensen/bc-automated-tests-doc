"""Minimal Markdown rendering for section files.

This module provides functionality to render SectionNode trees into
minimal Markdown stub files with proper filename generation following
the slug policy from the PRD.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import ToolConfig
    from .models import SectionNode

# Pattern to detect if a slug already has a numeric prefix (e.g., "01-intro")
PREFIXED_SLUG_PATTERN = re.compile(r"^\d+-")


def generate_filename(section: SectionNode, prefix_index: int, config: ToolConfig) -> str:
    """Generate filename for a section following the slug policy.

    If the section already has a prefixed slug (e.g., "01-intro"), use it directly.
    Otherwise, create a new slug with the provided prefix_index.

    Args:
        section: SectionNode to generate filename for
        prefix_index: Index for filename prefix (zero-padded, only used if slug lacks prefix)
        config: Tool configuration containing slug_prefix_width and default_slug_fallback

    Returns:
        Filename with .md extension

    Examples:
        >>> # Section with pre-existing prefixed slug
        >>> section = SectionNode(title="Introduction", level=1, slug="01-introduction")
        >>> config = ToolConfig()
        >>> generate_filename(section, 1, config)
        '01-introduction.md'

        >>> # Section with simple slug - add prefix
        >>> section = SectionNode(title="Overview", level=1, slug="overview")
        >>> generate_filename(section, 2, config)
        '02-overview.md'
    """
    slug = section.slug or config.default_slug_fallback

    # If slug already has a numeric prefix (e.g., "01-intro"), use it directly
    if PREFIXED_SLUG_PATTERN.match(slug):
        return f"{slug}.md"

    # Otherwise, add the prefix using the configured width
    width = config.slug_prefix_width
    return f"{prefix_index:0{width}d}-{slug}.md"


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
