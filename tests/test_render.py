"""Tests for minimal Markdown rendering functionality."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from pdf2md.config import ToolConfig
from pdf2md.models import SectionNode
from pdf2md.render import generate_filename, render_section_stub, render_sections


@pytest.fixture
def config() -> ToolConfig:
    """Create test configuration with default slug_prefix_width=2."""
    return ToolConfig()


@pytest.fixture
def sample_sections() -> list[SectionNode]:
    """Create sample sections for testing filename and content generation."""
    # Create sections based on the issue scenario
    section1 = SectionNode(
        title="Intro",
        level=1,
        slug="intro",
        pages=(1, 3),
    )

    section2 = SectionNode(
        title="Data Analysis",
        level=1,
        slug="data-analysis",
        pages=(4, 8),
    )

    section3 = SectionNode(
        title="Overview",
        level=2,
        slug="overview",
        pages=(5, 6),
    )

    # Create hierarchy: section2 has section3 as child
    section2.add_child(section3)

    return [section1, section2]


class TestGenerateFilename:
    """Tests for filename generation following slug policy."""

    def test_filename_format_with_prefix_01(self, config: ToolConfig) -> None:
        """Test scenario from issue: section with prefix 01 and title 'Intro'."""
        section = SectionNode(title="Intro", level=1, slug="intro")
        filename = generate_filename(section, 1, config)
        assert filename == "01_intro.md"

    def test_filename_format_with_different_prefixes(self, config: ToolConfig) -> None:
        """Test filename generation with different prefix indices."""
        section = SectionNode(title="Data Analysis", level=1, slug="data-analysis")

        # Test prefix 02
        filename = generate_filename(section, 2, config)
        assert filename == "02_data-analysis.md"

        # Test prefix 10
        filename = generate_filename(section, 10, config)
        assert filename == "10_data-analysis.md"

    def test_filename_respects_slug_prefix_width(self) -> None:
        """Test that filename respects slug_prefix_width configuration."""
        # Test with width=3
        config = ToolConfig(slug_prefix_width=3)
        section = SectionNode(title="Test", level=1, slug="test")
        filename = generate_filename(section, 5, config)
        assert filename == "005_test.md"

        # Test with width=1
        config = ToolConfig(slug_prefix_width=1)
        filename = generate_filename(section, 7, config)
        assert filename == "7_test.md"

    def test_filename_handles_missing_slug(self, config: ToolConfig) -> None:
        """Test filename generation when section has no slug."""
        section = SectionNode(title="No Slug", level=1, slug=None)
        filename = generate_filename(section, 1, config)
        assert filename == "01_untitled.md"

    def test_filename_with_complex_slug(self, config: ToolConfig) -> None:
        """Test filename with complex slug containing dashes."""
        section = SectionNode(
            title="Chapter 1: Introduction to Data", level=1, slug="chapter-1-introduction-to-data"
        )
        filename = generate_filename(section, 3, config)
        assert filename == "03_chapter-1-introduction-to-data.md"


class TestRenderSectionStub:
    """Tests for section content rendering."""

    def test_renders_h1_heading_only(self) -> None:
        """Test that section is rendered as H1 heading only."""
        section = SectionNode(title="Intro", level=1)
        content = render_section_stub(section)
        assert content == "# Intro\n"

    def test_renders_different_titles(self) -> None:
        """Test rendering sections with different titles."""
        # Simple title
        section1 = SectionNode(title="Overview", level=2)
        content1 = render_section_stub(section1)
        assert content1 == "# Overview\n"

        # Complex title with numbers and punctuation
        section2 = SectionNode(title="Chapter 1: Data Analysis", level=1)
        content2 = render_section_stub(section2)
        assert content2 == "# Chapter 1: Data Analysis\n"

    def test_renders_title_with_special_characters(self) -> None:
        """Test rendering titles with special characters."""
        section = SectionNode(title="Analysis & Results", level=1)
        content = render_section_stub(section)
        assert content == "# Analysis & Results\n"


class TestRenderSections:
    """Tests for rendering multiple sections to files."""

    def test_creates_book_directory(
        self, config: ToolConfig, sample_sections: list[SectionNode]
    ) -> None:
        """Test that render_sections creates book subdirectory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            written_files = render_sections(sample_sections, output_dir, config)

            book_dir = output_dir / "book"
            assert book_dir.exists()
            assert book_dir.is_dir()
            assert len(written_files) > 0

    def test_custom_book_subdir_name(
        self, config: ToolConfig, sample_sections: list[SectionNode]
    ) -> None:
        """Test rendering with custom book subdirectory name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            written_files = render_sections(
                sample_sections, output_dir, config, book_subdir="chapters"
            )

            chapters_dir = output_dir / "chapters"
            assert chapters_dir.exists()
            assert len(written_files) > 0
            # Verify files are in the custom directory
            for file_path in written_files:
                assert file_path.parent.name == "chapters"

    def test_filename_and_content_generation(
        self, config: ToolConfig, sample_sections: list[SectionNode]
    ) -> None:
        """Test that files are created with correct names and contents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            written_files = render_sections(sample_sections, output_dir, config)

            assert len(written_files) == 3  # 2 root + 1 child section

            # Check filenames follow expected pattern (pre-order traversal)
            expected_filenames = [
                "01_intro.md",  # First root section
                "02_data-analysis.md",  # Second root section
                "03_overview.md",  # Child of second section
            ]

            actual_filenames = [f.name for f in written_files]
            assert actual_filenames == expected_filenames

            # Check file contents
            for file_path in written_files:
                content = file_path.read_text(encoding="utf-8")

                if file_path.name == "01_intro.md":
                    assert content == "# Intro\n"
                elif file_path.name == "02_data-analysis.md":
                    assert content == "# Data Analysis\n"
                elif file_path.name == "03_overview.md":
                    assert content == "# Overview\n"

    def test_preorder_traversal_ordering(self, config: ToolConfig) -> None:
        """Test that sections are processed in pre-order (parent before children)."""
        # Create deeper hierarchy to test traversal order
        root = SectionNode(title="Root", level=1, slug="root")
        child1 = SectionNode(title="Child 1", level=2, slug="child-1")
        child2 = SectionNode(title="Child 2", level=2, slug="child-2")
        grandchild = SectionNode(title="Grandchild", level=3, slug="grandchild")

        # Build hierarchy: root -> child1 -> grandchild, root -> child2
        root.add_child(child1)
        root.add_child(child2)
        child1.add_child(grandchild)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            written_files = render_sections([root], output_dir, config)

            # Should be: root, child1, grandchild, child2 (pre-order)
            expected_filenames = [
                "01_root.md",
                "02_child-1.md",
                "03_grandchild.md",
                "04_child-2.md",
            ]

            actual_filenames = [f.name for f in written_files]
            assert actual_filenames == expected_filenames

    def test_relative_paths_are_correct(
        self, config: ToolConfig, sample_sections: list[SectionNode]
    ) -> None:
        """Test that returned file paths are relative to output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            written_files = render_sections(sample_sections, output_dir, config)

            # All files should be under book/ subdirectory
            for file_path in written_files:
                rel_path = file_path.relative_to(output_dir)
                assert rel_path.parts[0] == "book"
                assert len(rel_path.parts) == 2  # book/{filename}.md
                assert rel_path.suffix == ".md"

    def test_empty_sections_list(self, config: ToolConfig) -> None:
        """Test rendering with empty sections list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            written_files = render_sections([], output_dir, config)

            # Should create book directory but no files
            book_dir = output_dir / "book"
            assert book_dir.exists()
            assert len(written_files) == 0

    def test_file_writing_utf8_encoding(self, config: ToolConfig) -> None:
        """Test that files are written with UTF-8 encoding."""
        section = SectionNode(title="Résumé & Café", level=1, slug="resume-cafe")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            written_files = render_sections([section], output_dir, config)

            assert len(written_files) == 1
            content = written_files[0].read_text(encoding="utf-8")
            assert content == "# Résumé & Café\n"


class TestIntegrationScenario:
    """Integration tests matching the issue requirements."""

    def test_issue_scenario_exact_match(self, config: ToolConfig) -> None:
        """Test exact scenario from issue: section with prefix 01 and title 'Intro'."""
        # Given a section with prefix 01 and title "Intro"
        section = SectionNode(title="Intro", level=1, slug="intro")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # When rendering Markdown
            written_files = render_sections([section], output_dir, config)

            # Then file `book/01_intro.md` exists with heading line
            expected_file = output_dir / "book" / "01_intro.md"
            assert expected_file.exists()
            assert expected_file in written_files

            content = expected_file.read_text(encoding="utf-8")
            assert content == "# Intro\n"

    def test_multiple_sections_for_comprehensive_validation(self, config: ToolConfig) -> None:
        """Test with 2-3 sections as required by definition of done."""
        # Create 3 sections to test comprehensive behavior
        sections = [
            SectionNode(title="Introduction", level=1, slug="introduction"),
            SectionNode(title="Methodology", level=1, slug="methodology"),
            SectionNode(title="Results", level=1, slug="results"),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            written_files = render_sections(sections, output_dir, config)

            # Verify all files exist with correct names
            expected_files = [
                output_dir / "book" / "01_introduction.md",
                output_dir / "book" / "02_methodology.md",
                output_dir / "book" / "03_results.md",
            ]

            for expected_file in expected_files:
                assert expected_file.exists()
                assert expected_file in written_files

            # Verify contents
            assert expected_files[0].read_text() == "# Introduction\n"
            assert expected_files[1].read_text() == "# Methodology\n"
            assert expected_files[2].read_text() == "# Results\n"
