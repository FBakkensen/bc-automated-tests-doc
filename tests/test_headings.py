"""Tests for heading detection and tree building functionality."""

from __future__ import annotations

import pytest

from pdf2md.build_tree import build_tree
from pdf2md.config import ToolConfig
from pdf2md.headings import assign_heading_levels, detect_heading_level
from pdf2md.models import Block, BlockType, SectionNode, Span


@pytest.fixture
def config():
    """Provide a default ToolConfig for tests."""
    return ToolConfig()


@pytest.fixture
def sample_spans():
    """Provide sample spans for testing."""
    return {
        "chapter1": [
            Span("Chapter 1 Introduction", (0, 100, 200, 110), "Arial", 14, {"bold": True}, 1, 0)
        ],
        "section1_1": [Span("1.1 Background", (0, 80, 150, 90), "Arial", 12, {"bold": True}, 1, 1)],
        "section1_2": [
            Span("1.2 Methodology", (0, 60, 180, 70), "Arial", 12, {"bold": True}, 1, 2)
        ],
        "subsection1_2_1": [
            Span("1.2.1 Data Collection", (0, 40, 200, 50), "Arial", 10, {"bold": True}, 1, 3)
        ],
        "chapter2": [
            Span("Chapter 2 Results", (0, 20, 160, 30), "Arial", 14, {"bold": True}, 1, 4)
        ],
        "all_caps": [Span("METHODOLOGY", (0, 200, 120, 210), "Arial", 12, {"bold": True}, 1, 5)],
        "paragraph": [
            Span(
                "This is a regular paragraph of text that should not be detected as a heading.",
                (0, 180, 400, 190),
                "Arial",
                11,
                {},
                1,
                6,
            )
        ],
    }


# Tests for Task 5.1: Regex and uppercase heuristics


def test_detect_heading_level_chapter(config):
    """Test that Chapter headings are detected as level 1."""
    assert detect_heading_level("Chapter 1 Introduction", config) == 1
    assert detect_heading_level("Chapter 10 Conclusion", config) == 1
    assert detect_heading_level("CHAPTER 5 ANALYSIS", config) == 1


def test_detect_heading_level_dotted_numbering(config):
    """Test that dotted numbering is detected with correct levels."""
    assert detect_heading_level("1. Introduction", config) == 1
    assert detect_heading_level("1.1 Background", config) == 2
    assert detect_heading_level("1.2 Methodology", config) == 2
    assert detect_heading_level("1.2.1 Data Collection", config) == 3
    assert detect_heading_level("1.2.3.4 Detailed Analysis", config) == 4
    assert detect_heading_level("2.1.3.4.5.6.7", config) == 6  # Capped at 6 levels


def test_detect_heading_level_all_caps(config):
    """Test that ALL-CAPS headings are detected as level 1."""
    assert detect_heading_level("METHODOLOGY", config) == 1
    assert detect_heading_level("INTRODUCTION AND BACKGROUND", config) == 1
    assert detect_heading_level("RESULTS", config) == 1


def test_detect_heading_level_part_and_appendix(config):
    """Test that Part and Appendix headings are detected as level 1."""
    assert detect_heading_level("Part I Overview", config) == 1
    assert detect_heading_level("Part II Analysis", config) == 1
    assert detect_heading_level("Appendix A Data Tables", config) == 1
    assert detect_heading_level("Appendix B Code Listings", config) == 1


def test_detect_heading_level_non_headings(config):
    """Test that regular text is not detected as headings."""
    assert detect_heading_level("This is a regular paragraph.", config) is None
    assert (
        detect_heading_level(
            "A very long paragraph that exceeds the length threshold for heading "
            "detection and should not be considered a heading candidate.",
            config,
        )
        is None
    )
    assert detect_heading_level("", config) is None
    assert detect_heading_level("   ", config) is None


def test_detect_heading_level_edge_cases(config):
    """Test edge cases for heading detection."""
    # Short all-caps words (should still pass due to is_heading_candidate)
    assert detect_heading_level("ABC DEF", config) == 1

    # Mixed case that doesn't match patterns and doesn't pass is_heading_candidate
    assert detect_heading_level("Introduction", config) is None  # Doesn't pass is_heading_candidate


def test_assign_heading_levels_mixed_content(config, sample_spans):
    """Test assigning levels to a mix of heading candidates and regular blocks."""
    blocks = [
        Block(
            BlockType.HEADING_CANDIDATE, sample_spans["chapter1"], (0, 100, 200, 110), (1, 1), {}
        ),
        Block(BlockType.PARAGRAPH, sample_spans["paragraph"], (0, 180, 400, 190), (1, 1), {}),
        Block(
            BlockType.HEADING_CANDIDATE, sample_spans["section1_1"], (0, 80, 150, 90), (1, 1), {}
        ),
        Block(
            BlockType.HEADING_CANDIDATE, sample_spans["all_caps"], (0, 200, 120, 210), (1, 1), {}
        ),
    ]

    headings = assign_heading_levels(blocks, config)

    # Should find 3 headings (not the paragraph)
    assert len(headings) == 3

    # Check levels
    assert headings[0][1] == 1  # Chapter 1
    assert headings[1][1] == 2  # 1.1 Background
    assert headings[2][1] == 1  # METHODOLOGY


def test_assign_heading_levels_empty_input(config):
    """Test assign_heading_levels with empty input."""
    assert assign_heading_levels([], config) == []


def test_assign_heading_levels_no_heading_candidates(config, sample_spans):
    """Test assign_heading_levels with no heading candidate blocks."""
    blocks = [
        Block(BlockType.PARAGRAPH, sample_spans["paragraph"], (0, 180, 400, 190), (1, 1), {}),
    ]

    headings = assign_heading_levels(blocks, config)
    assert len(headings) == 0


# Tests for Task 5.2: Tree build and freeze points


def test_build_tree_simple_hierarchy(config, sample_spans):
    """Test building a simple two-level hierarchy."""
    blocks = [
        Block(
            BlockType.HEADING_CANDIDATE, sample_spans["chapter1"], (0, 100, 200, 110), (1, 1), {}
        ),
        Block(
            BlockType.HEADING_CANDIDATE, sample_spans["section1_1"], (0, 80, 150, 90), (1, 1), {}
        ),
        Block(
            BlockType.HEADING_CANDIDATE, sample_spans["section1_2"], (0, 60, 180, 70), (1, 1), {}
        ),
    ]

    tree = build_tree(blocks, config)

    assert len(tree) == 1  # One root (Chapter 1)

    root = tree[0]
    assert root.title == "Chapter 1 Introduction"
    assert root.level == 1
    assert len(root.children) == 2  # Two subsections

    # Check children
    assert root.children[0].title == "1.1 Background"
    assert root.children[0].level == 2
    assert root.children[1].title == "1.2 Methodology"
    assert root.children[1].level == 2


def test_build_tree_multi_level_hierarchy(config, sample_spans):
    """Test building a three-level hierarchy."""
    blocks = [
        Block(
            BlockType.HEADING_CANDIDATE, sample_spans["chapter1"], (0, 100, 200, 110), (1, 1), {}
        ),
        Block(
            BlockType.HEADING_CANDIDATE, sample_spans["section1_2"], (0, 60, 180, 70), (1, 1), {}
        ),
        Block(
            BlockType.HEADING_CANDIDATE,
            sample_spans["subsection1_2_1"],
            (0, 40, 200, 50),
            (1, 1),
            {},
        ),
        Block(BlockType.HEADING_CANDIDATE, sample_spans["chapter2"], (0, 20, 160, 30), (1, 1), {}),
    ]

    tree = build_tree(blocks, config)

    assert len(tree) == 2  # Two root chapters

    # Check first chapter
    chapter1 = tree[0]
    assert chapter1.title == "Chapter 1 Introduction"
    assert chapter1.level == 1
    assert len(chapter1.children) == 1

    section1_2 = chapter1.children[0]
    assert section1_2.title == "1.2 Methodology"
    assert section1_2.level == 2
    assert len(section1_2.children) == 1

    subsection = section1_2.children[0]
    assert subsection.title == "1.2.1 Data Collection"
    assert subsection.level == 3
    assert len(subsection.children) == 0

    # Check second chapter
    chapter2 = tree[1]
    assert chapter2.title == "Chapter 2 Results"
    assert chapter2.level == 1
    assert len(chapter2.children) == 0


def test_build_tree_preorder_traversal(config, sample_spans):
    """Test that children follow parents in pre-order traversal."""
    blocks = [
        Block(
            BlockType.HEADING_CANDIDATE, sample_spans["chapter1"], (0, 100, 200, 110), (1, 1), {}
        ),
        Block(
            BlockType.HEADING_CANDIDATE, sample_spans["section1_1"], (0, 80, 150, 90), (1, 1), {}
        ),
        Block(
            BlockType.HEADING_CANDIDATE, sample_spans["section1_2"], (0, 60, 180, 70), (1, 1), {}
        ),
        Block(
            BlockType.HEADING_CANDIDATE,
            sample_spans["subsection1_2_1"],
            (0, 40, 200, 50),
            (1, 1),
            {},
        ),
        Block(BlockType.HEADING_CANDIDATE, sample_spans["chapter2"], (0, 20, 160, 30), (1, 1), {}),
    ]

    tree = build_tree(blocks, config)

    # Manual pre-order traversal
    def traverse_preorder(sections):
        result = []
        for section in sections:
            result.append(section)
            result.extend(traverse_preorder(section.children))
        return result

    preorder = traverse_preorder(tree)

    # Verify order: Chapter 1, 1.1, 1.2, 1.2.1, Chapter 2
    assert len(preorder) == 5
    assert preorder[0].title == "Chapter 1 Introduction"
    assert preorder[1].title == "1.1 Background"
    assert preorder[2].title == "1.2 Methodology"
    assert preorder[3].title == "1.2.1 Data Collection"
    assert preorder[4].title == "Chapter 2 Results"


def test_build_tree_freeze_functionality(config, sample_spans):
    """Test that nodes are frozen after tree building."""
    blocks = [
        Block(
            BlockType.HEADING_CANDIDATE, sample_spans["chapter1"], (0, 100, 200, 110), (1, 1), {}
        ),
        Block(
            BlockType.HEADING_CANDIDATE, sample_spans["section1_1"], (0, 80, 150, 90), (1, 1), {}
        ),
    ]

    tree = build_tree(blocks, config)

    root = tree[0]
    child = root.children[0]

    # Verify nodes are frozen
    assert root.is_frozen()
    assert child.is_frozen()

    # Verify that modification attempts raise errors
    with pytest.raises(ValueError, match="Cannot modify frozen SectionNode"):
        root.add_child(child)

    with pytest.raises(ValueError, match="Cannot modify frozen SectionNode"):
        child.add_block(Block(BlockType.PARAGRAPH, [], (0, 0, 0, 0), (1, 1), {}))


def test_build_tree_empty_input(config):
    """Test build_tree with empty input."""
    tree = build_tree([], config)
    assert tree == []


def test_build_tree_no_headings(config, sample_spans):
    """Test build_tree with no heading candidates."""
    blocks = [
        Block(BlockType.PARAGRAPH, sample_spans["paragraph"], (0, 180, 400, 190), (1, 1), {}),
    ]

    tree = build_tree(blocks, config)
    assert tree == []


def test_section_node_slug_generation(config, sample_spans):
    """Test that slugs are generated deterministically with proper prefixes."""
    blocks = [
        Block(
            BlockType.HEADING_CANDIDATE, sample_spans["chapter1"], (0, 100, 200, 110), (1, 1), {}
        ),
        Block(
            BlockType.HEADING_CANDIDATE, sample_spans["section1_1"], (0, 80, 150, 90), (1, 1), {}
        ),
    ]

    tree = build_tree(blocks, config)

    # Check that slugs are generated with prefix ordering
    root = tree[0]
    child = root.children[0]

    assert root.slug == "00-chapter-1-introduction"
    assert child.slug == "01-1-1-background"


def test_section_node_pages_assignment(config, sample_spans):
    """Test that page ranges are correctly assigned to SectionNodes."""
    # Create spans on different pages
    chapter_spans = [Span("Chapter 1", (0, 100, 100, 110), "Arial", 14, {"bold": True}, 2, 0)]
    section_spans = [Span("1.1 Background", (0, 80, 150, 90), "Arial", 12, {"bold": True}, 3, 1)]

    blocks = [
        Block(BlockType.HEADING_CANDIDATE, chapter_spans, (0, 100, 100, 110), (2, 2), {}),
        Block(BlockType.HEADING_CANDIDATE, section_spans, (0, 80, 150, 90), (3, 3), {}),
    ]

    tree = build_tree(blocks, config)

    root = tree[0]
    child = root.children[0]

    assert root.pages == (2, 2)
    assert child.pages == (3, 3)


# Tests for Task 6: Numbering and Appendices Integration


def test_chapter_numbering_metadata_attached(config):
    """Test that chapter numbering metadata is attached to blocks."""
    chapter_spans = [
        Span("Chapter 1 Introduction", (0, 10, 200, 20), "Arial", 14, {"bold": True}, 1, 0)
    ]
    chapter_block = Block(BlockType.HEADING_CANDIDATE, chapter_spans, (0, 10, 200, 20), (1, 1), {})

    headings = assign_heading_levels([chapter_block], config)

    assert len(headings) == 1
    block, level = headings[0]

    # Check that numbering metadata was attached
    assert "chapter_number" in block.meta
    assert block.meta["chapter_number"] == 1


def test_section_path_metadata_attached(config):
    """Test that section path metadata is attached to blocks."""
    section_spans = [Span("1.2.3 Methodology", (0, 10, 200, 20), "Arial", 12, {"bold": True}, 1, 0)]
    section_block = Block(BlockType.HEADING_CANDIDATE, section_spans, (0, 10, 200, 20), (1, 1), {})

    headings = assign_heading_levels([section_block], config)

    assert len(headings) == 1
    block, level = headings[0]

    # Check that section path metadata was attached
    assert "section_path" in block.meta
    assert block.meta["section_path"] == [1, 2, 3]


def test_appendix_metadata_attached(config):
    """Test that appendix metadata is attached to blocks."""
    # First need a chapter to enable appendix detection
    chapter_spans = [
        Span("Chapter 1 Introduction", (0, 10, 200, 20), "Arial", 14, {"bold": True}, 1, 0)
    ]
    chapter_block = Block(BlockType.HEADING_CANDIDATE, chapter_spans, (0, 10, 200, 20), (1, 1), {})

    # Appendix at top of page (y=10 is near top)
    appendix_spans = [Span("Appendix A Data", (0, 10, 200, 20), "Arial", 14, {"bold": True}, 2, 0)]
    appendix_block = Block(
        BlockType.HEADING_CANDIDATE, appendix_spans, (0, 10, 200, 20), (2, 2), {}
    )

    blocks = [chapter_block, appendix_block]
    headings = assign_heading_levels(blocks, config)

    assert len(headings) == 2

    # Check chapter
    chapter_block, chapter_level = headings[0]
    assert "chapter_number" in chapter_block.meta

    # Check appendix
    appendix_block, appendix_level = headings[1]
    assert "appendix_letter" in appendix_block.meta
    assert appendix_block.meta["appendix_letter"] == "A"


def test_global_chapter_numbering_across_parts_integration(config):
    """Test integration of global chapter numbering across parts."""
    blocks = [
        # Part I
        Block(
            BlockType.HEADING_CANDIDATE,
            [Span("Part I Overview", (0, 10, 200, 20), "Arial", 16, {"bold": True}, 1, 0)],
            (0, 10, 200, 20),
            (1, 1),
            {},
        ),
        # Chapter 1
        Block(
            BlockType.HEADING_CANDIDATE,
            [Span("Chapter 1 Introduction", (0, 10, 200, 20), "Arial", 14, {"bold": True}, 2, 0)],
            (0, 10, 200, 20),
            (2, 2),
            {},
        ),
        # Part II
        Block(
            BlockType.HEADING_CANDIDATE,
            [Span("Part II Analysis", (0, 10, 200, 20), "Arial", 16, {"bold": True}, 3, 0)],
            (0, 10, 200, 20),
            (3, 3),
            {},
        ),
        # Chapter 1 again (should get global number 2)
        Block(
            BlockType.HEADING_CANDIDATE,
            [Span("Chapter 1 Methodology", (0, 10, 200, 20), "Arial", 14, {"bold": True}, 4, 0)],
            (0, 10, 200, 20),
            (4, 4),
            {},
        ),
    ]

    headings = assign_heading_levels(blocks, config)

    # Find the chapter blocks
    chapter_blocks = [h for h in headings if "chapter_number" in h[0].meta]

    assert len(chapter_blocks) == 2
    assert chapter_blocks[0][0].meta["chapter_number"] == 1
    assert chapter_blocks[1][0].meta["chapter_number"] == 2  # Global numbering


def test_section_node_basic_functionality():
    """Test basic SectionNode functionality without config dependency."""
    # Test creation and basic operations
    section = SectionNode(title="Test Section", level=1)

    assert section.title == "Test Section"
    assert section.level == 1
    assert section.slug is None
    assert len(section.blocks) == 0
    assert len(section.children) == 0
    assert not section.is_frozen()

    # Test adding children and blocks
    child = SectionNode(title="Child Section", level=2)
    section.add_child(child)
    assert len(section.children) == 1
    assert section.children[0] is child

    block = Block(BlockType.PARAGRAPH, [], (0, 0, 100, 10), (1, 1), {})
    section.add_block(block)
    assert len(section.blocks) == 1
    assert section.blocks[0] is block

    # Test freezing
    section.freeze()
    assert section.is_frozen()
    assert child.is_frozen()  # Children should be frozen recursively

    # Test that frozen nodes cannot be modified
    with pytest.raises(ValueError, match="Cannot modify frozen SectionNode"):
        section.add_child(SectionNode(title="Another Child", level=2))

    with pytest.raises(ValueError, match="Cannot modify frozen SectionNode"):
        section.add_block(Block(BlockType.PARAGRAPH, [], (0, 0, 100, 10), (1, 1), {}))


if __name__ == "__main__":
    pytest.main([__file__])
