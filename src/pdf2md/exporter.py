"""Manifest generation and structural hash computation functionality.

This module provides functionality to export document trees to manifest.json
with deterministic field ordering and structural hash computation according
to the canonical manifest schema specification.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .config import ToolConfig
    from .models import SectionNode


def _traverse_preorder(sections: list[SectionNode]) -> list[SectionNode]:
    """Traverse sections in pre-order (parent before children).

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


def _generate_section_id(index: int) -> str:
    """Generate section ID with zero-padded format.

    Args:
        index: 0-based index position

    Returns:
        Section ID in format "sec_NNNN" with 4-digit zero padding
    """
    return f"sec_{index:04d}"


def _build_section_projection(
    section: SectionNode, order_index: int, parent_id: str | None = None
) -> dict[str, Any]:
    """Build section projection for manifest.

    Args:
        section: SectionNode to project
        order_index: 1-based order index in pre-order traversal
        parent_id: Parent section ID or None for root

    Returns:
        Section projection dict with required fields
    """
    section_id = _generate_section_id(order_index - 1)  # Convert to 0-based for ID

    return {
        "id": section_id,
        "slug": section.slug or "",
        "parent_id": parent_id,
        "level": section.level,
        "order_index": order_index,
        "title": section.title,
        "page_span": list(section.pages),  # Convert tuple to list for JSON
    }


def build_manifest(
    sections: list[SectionNode],
    config: ToolConfig,
    *,
    tool_version: str = "0.1.0",
) -> dict[str, Any]:
    """Build complete manifest data structure from section tree.

    Args:
        sections: List of root SectionNode objects
        config: Tool configuration
        tool_version: Tool version string for generated_with field

    Returns:
        Complete manifest dict with all required fields in proper order
    """
    # Get all sections in pre-order traversal
    all_sections = _traverse_preorder(sections)

    # Build section projections with proper parent-child relationships
    section_projections = []

    for i, section in enumerate(all_sections):
        order_index = i + 1  # 1-based indexing

        # Find parent ID by looking up parent in the all_sections list using identity
        parent_id = None
        for j, potential_parent in enumerate(all_sections):
            # Use identity comparison to avoid mislinking duplicates
            if any(child is section for child in potential_parent.children):
                parent_id = _generate_section_id(j)
                break

        projection = _build_section_projection(section, order_index, parent_id)
        section_projections.append(projection)

    # Build manifest with exact field order from schema
    manifest = {
        "schema_version": "1.0.0",
        "sections": section_projections,
        "figures": [],  # Empty for now, will be populated when figure extraction is implemented
        "footnotes": [],  # Empty for now, will be populated when footnote extraction is implemented
        "assets": [],
        "cross_references": [],
        "structural_hash": "",  # Will be computed separately
        "generated_with": {"tool": "pdf2md", "version": tool_version},
    }

    # Compute and set structural hash
    structural_hash = compute_structural_hash(manifest)
    manifest["structural_hash"] = structural_hash

    return manifest


def compute_structural_hash(manifest: dict[str, Any]) -> str:
    """Compute structural hash from manifest using canonical serialization.

    Args:
        manifest: Complete manifest dict

    Returns:
        Structural hash prefixed with "sha256:"
    """
    # Build projection dict with only structural fields
    # Exclude generated_with, assets, cross_references per spec
    projection = {
        "sections": manifest["sections"],
        "figures": manifest.get("figures", []),
    }

    # Only include footnotes if not empty (per schema spec)
    footnotes = manifest.get("footnotes", [])
    if footnotes:
        projection["footnotes"] = footnotes

    # Sort arrays by order_index (sections) or id numeric suffix (figures/footnotes)
    if "sections" in projection:
        projection["sections"] = sorted(projection["sections"], key=lambda x: x["order_index"])

    if "figures" in projection:
        projection["figures"] = sorted(
            projection["figures"], key=lambda x: int(x["id"].split("_")[-1])
        )

    if "footnotes" in projection:
        projection["footnotes"] = sorted(
            projection["footnotes"], key=lambda x: int(x["id"].split("_")[-1])
        )

    # Serialize with canonical format: UTF-8, separators without whitespace, sorted keys
    json_bytes = json.dumps(
        projection, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")

    # Compute SHA-256 hash
    hash_obj = hashlib.sha256(json_bytes)
    return f"sha256:{hash_obj.hexdigest()}"


def write_manifest(manifest: dict[str, Any], output_path: Path, *, indent: int | None = 2) -> None:
    """Write manifest to JSON file with proper formatting.

    Args:
        manifest: Complete manifest dict
        output_path: Path to write manifest.json
        indent: JSON indentation (2 for readable, None for compact)
    """
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=indent)


def export_manifest(
    sections: list[SectionNode],
    output_dir: Path,
    config: ToolConfig,
    *,
    tool_version: str = "0.1.0",
) -> Path:
    """Export complete manifest to output directory.

    Args:
        sections: List of root SectionNode objects
        output_dir: Directory to write manifest.json
        config: Tool configuration
        tool_version: Tool version string

    Returns:
        Path to written manifest.json file
    """
    manifest = build_manifest(sections, config, tool_version=tool_version)
    manifest_path = output_dir / "manifest.json"
    write_manifest(manifest, manifest_path)
    return manifest_path
