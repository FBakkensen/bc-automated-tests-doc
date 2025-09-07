"""Tests for manifest generation and structural hash computation."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from pdf2md.config import ToolConfig
from pdf2md.exporter import build_manifest, compute_structural_hash, export_manifest
from pdf2md.models import SectionNode


@pytest.fixture
def config() -> ToolConfig:
    """Create test configuration."""
    return ToolConfig()


@pytest.fixture
def sample_sections() -> list[SectionNode]:
    """Create sample section tree for testing."""
    # Create root section (Chapter 1)
    root_section = SectionNode(
        title="Chapter 1 Introduction",
        level=1,
        slug="00-chapter-1-introduction",
        pages=(1, 5),
    )

    # Create child section (Section 1.1)
    child_section = SectionNode(
        title="1.1 Overview",
        level=2,
        slug="01-1-1-overview",
        pages=(2, 3),
    )

    # Create another child section (Section 1.2)
    child_section2 = SectionNode(
        title="1.2 Methodology",
        level=2,
        slug="02-1-2-methodology",
        pages=(4, 5),
    )

    # Build hierarchy
    root_section.add_child(child_section)
    root_section.add_child(child_section2)

    # Create second root section (Chapter 2)
    root_section2 = SectionNode(
        title="Chapter 2 Analysis",
        level=1,
        slug="03-chapter-2-analysis",
        pages=(6, 10),
    )

    return [root_section, root_section2]


def test_manifest_structure_and_field_order(
    config: ToolConfig, sample_sections: list[SectionNode]
) -> None:
    """Test that manifest has correct structure and field ordering."""
    manifest = build_manifest(sample_sections, config, tool_version="0.1.0")

    # Check top-level structure and field presence
    expected_fields = [
        "schema_version",
        "sections",
        "figures",
        "footnotes",
        "assets",
        "cross_references",
        "structural_hash",
        "generated_with",
    ]

    assert list(manifest.keys()) == expected_fields

    # Check basic field values
    assert manifest["schema_version"] == "1.0.0"
    assert isinstance(manifest["sections"], list)
    assert manifest["figures"] == []
    assert manifest["footnotes"] == []
    assert manifest["assets"] == []
    assert manifest["cross_references"] == []
    assert manifest["structural_hash"].startswith("sha256:")
    assert manifest["generated_with"]["tool"] == "pdf2md"
    assert manifest["generated_with"]["version"] == "0.1.0"


def test_sections_preorder_traversal_and_ordering(
    config: ToolConfig, sample_sections: list[SectionNode]
) -> None:
    """Test that sections are serialized in pre-order with correct order_index."""
    manifest = build_manifest(sample_sections, config)

    sections = manifest["sections"]
    assert len(sections) == 4  # 2 root + 2 children

    # Verify pre-order traversal: parent before children
    # Expected order: Chapter 1, 1.1 Overview, 1.2 Methodology, Chapter 2
    expected_titles = [
        "Chapter 1 Introduction",
        "1.1 Overview",
        "1.2 Methodology",
        "Chapter 2 Analysis",
    ]

    actual_titles = [section["title"] for section in sections]
    assert actual_titles == expected_titles

    # Verify order_index is 1-based and sequential
    for i, section in enumerate(sections):
        assert section["order_index"] == i + 1

    # Verify first section has order_index = 1 as required by test scenario
    assert sections[0]["order_index"] == 1


def test_section_projection_fields_match_prd(
    config: ToolConfig, sample_sections: list[SectionNode]
) -> None:
    """Test that section projections have correct fields matching PRD specification."""
    manifest = build_manifest(sample_sections, config)

    for section in manifest["sections"]:
        # Check required fields from PRD
        required_fields = ["id", "slug", "parent_id", "level", "order_index", "title", "page_span"]
        assert list(section.keys()) == required_fields

        # Check field types and formats
        assert section["id"].startswith("sec_")
        assert len(section["id"]) == 8  # "sec_" + 4 digits
        assert isinstance(section["slug"], str)
        assert section["parent_id"] is None or section["parent_id"].startswith("sec_")
        assert isinstance(section["level"], int)
        assert isinstance(section["order_index"], int)
        assert isinstance(section["title"], str)
        assert isinstance(section["page_span"], list)
        assert len(section["page_span"]) == 2
        assert section["page_span"][0] <= section["page_span"][1]


def test_parent_child_relationships(config: ToolConfig, sample_sections: list[SectionNode]) -> None:
    """Test that parent-child relationships are correctly represented."""
    manifest = build_manifest(sample_sections, config)

    sections = manifest["sections"]

    # First section (Chapter 1) should have no parent
    assert sections[0]["parent_id"] is None
    assert sections[0]["level"] == 1

    # Second section (1.1 Overview) should have Chapter 1 as parent
    assert sections[1]["parent_id"] == sections[0]["id"]
    assert sections[1]["level"] == 2

    # Third section (1.2 Methodology) should have Chapter 1 as parent
    assert sections[2]["parent_id"] == sections[0]["id"]
    assert sections[2]["level"] == 2

    # Fourth section (Chapter 2) should have no parent
    assert sections[3]["parent_id"] is None
    assert sections[3]["level"] == 1


def test_structural_hash_changes_on_title_change(
    config: ToolConfig, sample_sections: list[SectionNode]
) -> None:
    """Test that structural hash changes when section title changes."""
    # Build manifest with original titles
    manifest1 = build_manifest(sample_sections, config, tool_version="0.1.0")
    hash1 = manifest1["structural_hash"]

    # Clone sections and change a title
    sections_copy = []
    for section in sample_sections:
        new_section = SectionNode(
            title=section.title,
            level=section.level,
            slug=section.slug,
            pages=section.pages,
        )
        for child in section.children:
            new_child = SectionNode(
                title=child.title,
                level=child.level,
                slug=child.slug,
                pages=child.pages,
            )
            new_section.add_child(new_child)
        sections_copy.append(new_section)

    # Change title of first section
    sections_copy[0].title = "Chapter 1 Different Title"

    # Build manifest with changed title
    manifest2 = build_manifest(sections_copy, config, tool_version="0.1.0")
    hash2 = manifest2["structural_hash"]

    # Hashes should be different
    assert hash1 != hash2


def test_structural_hash_stable_on_tool_version_change(
    config: ToolConfig, sample_sections: list[SectionNode]
) -> None:
    """Test that structural hash does NOT change when only tool version changes."""
    # Build manifest with version 0.1.0
    manifest1 = build_manifest(sample_sections, config, tool_version="0.1.0")
    hash1 = manifest1["structural_hash"]

    # Build manifest with different version
    manifest2 = build_manifest(sample_sections, config, tool_version="0.2.0")
    hash2 = manifest2["structural_hash"]

    # Hashes should be identical (version excluded from hash computation)
    assert hash1 == hash2

    # But generated_with should be different
    assert manifest1["generated_with"]["version"] != manifest2["generated_with"]["version"]


def test_structural_hash_canonical_serialization(config: ToolConfig) -> None:
    """Test that structural hash uses canonical JSON serialization."""
    # Create minimal test data
    test_manifest = {
        "sections": [
            {
                "id": "sec_0001",
                "slug": "00-test",
                "parent_id": None,
                "level": 1,
                "order_index": 1,
                "title": "Test",
                "page_span": [1, 2],
            }
        ],
        "figures": [],
        "generated_with": {"tool": "pdf2md", "version": "0.1.0"},
    }

    hash_result = compute_structural_hash(test_manifest)

    # Should be prefixed with sha256:
    assert hash_result.startswith("sha256:")

    # Should be deterministic (same input = same hash)
    hash_result2 = compute_structural_hash(test_manifest)
    assert hash_result == hash_result2

    # Verify hash excludes generated_with (should be same even if version changes)
    test_manifest2 = test_manifest.copy()
    test_manifest2["generated_with"] = {"tool": "pdf2md", "version": "0.2.0"}
    hash_result3 = compute_structural_hash(test_manifest2)
    assert hash_result == hash_result3


def test_export_manifest_writes_file(
    config: ToolConfig, sample_sections: list[SectionNode]
) -> None:
    """Test that export_manifest writes file correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        manifest_path = export_manifest(sample_sections, output_dir, config)

        # Check file was created
        assert manifest_path.exists()
        assert manifest_path.name == "manifest.json"

        # Check content is valid JSON
        with manifest_path.open("r", encoding="utf-8") as f:
            loaded_manifest = json.load(f)

        # Basic validation
        assert loaded_manifest["schema_version"] == "1.0.0"
        assert len(loaded_manifest["sections"]) == 4
        assert loaded_manifest["structural_hash"].startswith("sha256:")


def test_empty_sections_list(config: ToolConfig) -> None:
    """Test manifest generation with empty sections list."""
    manifest = build_manifest([], config)

    assert manifest["sections"] == []
    assert manifest["structural_hash"].startswith("sha256:")

    # Hash should be computed correctly even for empty sections
    empty_hash = compute_structural_hash(manifest)
    assert empty_hash.startswith("sha256:")


def test_section_id_format_and_zero_padding(
    config: ToolConfig, sample_sections: list[SectionNode]
) -> None:
    """Test that section IDs follow proper format with zero padding."""
    manifest = build_manifest(sample_sections, config)

    # Check ID format: sec_ + 4-digit zero-padded number
    expected_ids = ["sec_0000", "sec_0001", "sec_0002", "sec_0003"]
    actual_ids = [section["id"] for section in manifest["sections"]]

    assert actual_ids == expected_ids
