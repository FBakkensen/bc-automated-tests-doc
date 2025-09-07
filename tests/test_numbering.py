"""Tests for numbering and appendix detection functionality."""

from __future__ import annotations

import logging

import pytest

from pdf2md.config import ToolConfig
from pdf2md.models import Block, BlockType, Span
from pdf2md.numbering import NumberingProcessor


@pytest.fixture
def config():
    """Provide a default ToolConfig for tests."""
    return ToolConfig()


@pytest.fixture
def config_no_gaps():
    """Provide a ToolConfig with gap validation disabled."""
    return ToolConfig(numbering_validate_gaps=False)


@pytest.fixture
def config_allow_resets():
    """Provide a ToolConfig that allows chapter resets."""
    return ToolConfig(numbering_allow_chapter_resets=True)


@pytest.fixture
def config_no_page_break():
    """Provide a ToolConfig that doesn't require page breaks for appendices."""
    return ToolConfig(appendix_requires_page_break=False)


def create_block(text: str, page: int = 1, y_position: float = 50.0) -> Block:
    """Helper to create a test block with specified text and position."""
    span = Span(text, (0, y_position, 200, y_position + 10), "Arial", 12, {"bold": True}, page, 0)
    return Block(
        BlockType.HEADING_CANDIDATE, [span], (0, y_position, 200, y_position + 10), (page, page), {}
    )


def create_top_block(text: str, page: int = 1) -> Block:
    """Helper to create a block at the top of the page."""
    return create_block(text, page, y_position=10.0)  # Near top


class TestTask61GlobalChapterNumbering:
    """Tests for Task 6.1: Global chapter numbering."""

    def test_chapter_global_numbering_without_resets(self, config, caplog):
        """Test that chapters get global numbering without resets across parts."""
        with caplog.at_level(logging.WARNING):
            processor = NumberingProcessor(config)

            # Part I, Chapter 1
            part1_block = create_block("Part I Overview")
            processor.process_heading_block(part1_block, "Part I Overview")

            chapter1_block = create_block("Chapter 1 Introduction")
            chapter1_meta = processor.process_heading_block(
                chapter1_block, "Chapter 1 Introduction"
            )

            # Part II, Chapter 1 (should be assigned internal number 2)
            part2_block = create_block("Part II Analysis")
            processor.process_heading_block(part2_block, "Part II Analysis")

            chapter1_again_block = create_block("Chapter 1 Methodology")
            chapter1_again_meta = processor.process_heading_block(
                chapter1_again_block, "Chapter 1 Methodology"
            )

            # Check that global numbering increments
            assert chapter1_meta["chapter_number"] == 1
            assert chapter1_again_meta["chapter_number"] == 2

            # Check that reset warning was logged
            assert any(
                "chapter_number_reset_detected" in record.getMessage() for record in caplog.records
            )

    def test_duplicate_chapter_number_warning(self, config, caplog):
        """Test that duplicate chapter numbers are logged and handled."""
        with caplog.at_level(logging.WARNING):
            processor = NumberingProcessor(config)

            # Two headings with same chapter number
            chapter1_block = create_block("Chapter 5 First")
            meta1 = processor.process_heading_block(chapter1_block, "Chapter 5 First")

            chapter1_dup_block = create_block("Chapter 5 Second")
            meta2 = processor.process_heading_block(chapter1_dup_block, "Chapter 5 Second")

            # First gets the number, second is treated as implicit
            assert meta1["chapter_number"] == 1
            assert meta2["chapter_number"] == 2

            # Check duplicate warning was logged
            assert any(
                "duplicate_chapter_number" in record.getMessage() for record in caplog.records
            )

    def test_chapter_numbering_with_resets_allowed(self, config_allow_resets, caplog):
        """Test chapter numbering when resets are allowed."""
        with caplog.at_level(logging.WARNING):
            processor = NumberingProcessor(config_allow_resets)

            chapter1_block = create_block("Chapter 1 Introduction")
            meta1 = processor.process_heading_block(chapter1_block, "Chapter 1 Introduction")

            chapter1_again_block = create_block("Chapter 1 Methodology")
            meta2 = processor.process_heading_block(chapter1_again_block, "Chapter 1 Methodology")

            # Both should get sequential global numbers
            assert meta1["chapter_number"] == 1
            assert meta2["chapter_number"] == 2

            # No reset warning when resets are allowed
            assert not any(
                "chapter_number_reset_detected" in record.getMessage() for record in caplog.records
            )


class TestTask62DottedPathsAndGaps:
    """Tests for Task 6.2: Dotted paths and gaps."""

    def test_section_gap_detection(self, config, caplog):
        """Test that gaps in section numbering are detected and logged."""
        with caplog.at_level(logging.WARNING):
            processor = NumberingProcessor(config)

            # Create sections with a gap: 3.2 followed by 3.5
            section1_block = create_block("3.2 Background")
            meta1 = processor.process_heading_block(section1_block, "3.2 Background")

            section2_block = create_block("3.5 Results")
            meta2 = processor.process_heading_block(section2_block, "3.5 Results")

            # Check section paths are stored
            assert meta1["section_path"] == [3, 2]
            assert meta2["section_path"] == [3, 5]

            # Check gap warning was logged
            assert any("section_gap_detected" in record.getMessage() for record in caplog.records)

    def test_section_gap_validation_disabled(self, config_no_gaps, caplog):
        """Test that gap validation can be disabled."""
        with caplog.at_level(logging.WARNING):
            processor = NumberingProcessor(config_no_gaps)

            section1_block = create_block("3.2 Background")
            processor.process_heading_block(section1_block, "3.2 Background")

            section2_block = create_block("3.5 Results")
            processor.process_heading_block(section2_block, "3.5 Results")

            # No gap warning when validation is disabled
            assert not any(
                "section_gap_detected" in record.getMessage() for record in caplog.records
            )

    def test_dotted_path_depth_truncation(self, config):
        """Test that deeply nested paths are truncated per config."""
        # Set max depth to 3
        config.numbering_max_depth = 3
        processor = NumberingProcessor(config)

        deep_section_block = create_block("1.2.3.4.5.6.7 Deep Section")
        meta = processor.process_heading_block(deep_section_block, "1.2.3.4.5.6.7 Deep Section")

        # Should be truncated to max depth
        assert meta["section_path"] == [1, 2, 3]

    def test_valid_dotted_paths(self, config):
        """Test that valid dotted paths are processed correctly."""
        processor = NumberingProcessor(config)

        test_cases = [
            ("1. Introduction", [1]),
            ("1.1 Background", [1, 1]),
            ("1.2.3 Methodology", [1, 2, 3]),
            ("2.1.3.4.5.6 Deep", [2, 1, 3, 4, 5, 6]),
        ]

        for text, expected_path in test_cases:
            block = create_block(text)
            meta = processor.process_heading_block(block, text)
            assert meta["section_path"] == expected_path


class TestTask63AppendixDetectionWithPageBreak:
    """Tests for Task 6.3: Appendix detection with page break rule."""

    def test_appendix_page_break_requirement(self, config, caplog):
        """Test that appendix not at top of page is ignored."""
        with caplog.at_level(logging.WARNING):
            processor = NumberingProcessor(config)

            # Need a chapter first
            chapter_block = create_block("Chapter 1 Introduction")
            processor.process_heading_block(chapter_block, "Chapter 1 Introduction")

            # Appendix not at page top (y=50 is mid-page)
            appendix_block = create_block("Appendix A Data Tables", y_position=50.0)
            meta = processor.process_heading_block(appendix_block, "Appendix A Data Tables")

            # Should be ignored - no appendix_letter in meta
            assert "appendix_letter" not in meta

            # Should log missing page break warning
            assert any(
                "appendix_missing_page_break" in record.getMessage() for record in caplog.records
            )

    def test_appendix_at_page_top_accepted(self, config, caplog):
        """Test that appendix at top of page is accepted."""
        with caplog.at_level(logging.INFO):
            processor = NumberingProcessor(config)

            # Need a chapter first
            chapter_block = create_block("Chapter 1 Introduction")
            processor.process_heading_block(chapter_block, "Chapter 1 Introduction")

            # Appendix at page top
            appendix_block = create_top_block("Appendix A Data Tables")
            meta = processor.process_heading_block(appendix_block, "Appendix A Data Tables")

            # Should be accepted
            assert meta["appendix_letter"] == "A"

            # Should log detection
            assert any("appendix_detected" in record.getMessage() for record in caplog.records)

    def test_appendix_page_break_disabled(self, config_no_page_break, caplog):
        """Test appendix detection when page break requirement is disabled."""
        processor = NumberingProcessor(config_no_page_break)

        # Need a chapter first
        chapter_block = create_block("Chapter 1 Introduction")
        processor.process_heading_block(chapter_block, "Chapter 1 Introduction")

        # Appendix not at page top, but page break requirement disabled
        appendix_block = create_block("Appendix A Data Tables", y_position=50.0)
        meta = processor.process_heading_block(appendix_block, "Appendix A Data Tables")

        # Should be accepted even though not at page top
        assert meta["appendix_letter"] == "A"

    def test_early_appendix_ignored(self, config, caplog):
        """Test that appendix before first chapter is ignored."""
        with caplog.at_level(logging.WARNING):
            processor = NumberingProcessor(config)

            # Appendix before any chapter
            appendix_block = create_top_block("Appendix A Data Tables")
            meta = processor.process_heading_block(appendix_block, "Appendix A Data Tables")

            # Should be ignored
            assert "appendix_letter" not in meta

            # Should log early appendix warning
            assert any("appendix_early_ignored" in record.getMessage() for record in caplog.records)

    def test_appendix_letter_ordering(self, config, caplog):
        """Test proper appendix letter ordering detection."""
        processor = NumberingProcessor(config)

        # Need a chapter first
        chapter_block = create_block("Chapter 1 Introduction")
        processor.process_heading_block(chapter_block, "Chapter 1 Introduction")

        # Appendices in order: A, B, C
        appendix_a = create_top_block("Appendix A Data")
        meta_a = processor.process_heading_block(appendix_a, "Appendix A Data")

        appendix_b = create_top_block("Appendix B Code")
        meta_b = processor.process_heading_block(appendix_b, "Appendix B Code")

        appendix_c = create_top_block("Appendix C References")
        meta_c = processor.process_heading_block(appendix_c, "Appendix C References")

        # All should be accepted
        assert meta_a["appendix_letter"] == "A"
        assert meta_b["appendix_letter"] == "B"
        assert meta_c["appendix_letter"] == "C"

    def test_appendix_out_of_order(self, config, caplog):
        """Test detection of out-of-order appendix letters."""
        with caplog.at_level(logging.WARNING):
            processor = NumberingProcessor(config)

            # Need a chapter first
            chapter_block = create_block("Chapter 1 Introduction")
            processor.process_heading_block(chapter_block, "Chapter 1 Introduction")

            # Out of order: A, C, B
            appendix_a = create_top_block("Appendix A Data")
            processor.process_heading_block(appendix_a, "Appendix A Data")

            appendix_c = create_top_block("Appendix C References")
            processor.process_heading_block(appendix_c, "Appendix C References")

            appendix_b = create_top_block("Appendix B Code")
            meta_b = processor.process_heading_block(appendix_b, "Appendix B Code")

            # B should still be accepted but warning logged
            assert meta_b["appendix_letter"] == "B"
            assert any("appendix_out_of_order" in record.getMessage() for record in caplog.records)

    def test_duplicate_appendix_letter(self, config, caplog):
        """Test handling of duplicate appendix letters."""
        with caplog.at_level(logging.WARNING):
            processor = NumberingProcessor(config)

            # Need a chapter first
            chapter_block = create_block("Chapter 1 Introduction")
            processor.process_heading_block(chapter_block, "Chapter 1 Introduction")

            # Two appendices with same letter
            appendix_a1 = create_top_block("Appendix A First")
            meta_a1 = processor.process_heading_block(appendix_a1, "Appendix A First")

            appendix_a2 = create_top_block("Appendix A Second")
            meta_a2 = processor.process_heading_block(appendix_a2, "Appendix A Second")

            # First should be accepted, second demoted
            assert meta_a1["appendix_letter"] == "A"
            assert "appendix_letter" not in meta_a2

            # Should log duplicate warning
            assert any(
                "appendix_duplicate_letter" in record.getMessage() for record in caplog.records
            )
