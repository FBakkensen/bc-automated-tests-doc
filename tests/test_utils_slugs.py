"""Tests for deterministic slug generation and collision handling."""

from __future__ import annotations

import pytest

from pdf2md.utils import clear_slug_cache, deterministic_slug, generate_unique_slug


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the slug cache before each test to ensure test isolation."""
    clear_slug_cache()
    yield
    clear_slug_cache()


class TestDeterministicSlugFormat:
    """Tests for Task 7.1: Deterministic slug format."""

    def test_scenario_introduction_to_data(self):
        """Test the scenario from the issue: 'Introduction to Data' with prefix 2, width 2."""
        result = deterministic_slug("Introduction to Data", prefix_index=2, width=2)
        assert result == "02-introduction-to-data"

    def test_punctuation_stripping_quotes(self):
        """Test that single and double quotes are stripped."""
        result = deterministic_slug("Chapter's 'Introduction' \"Example\"", prefix_index=1, width=2)
        assert result == "01-chapters-introduction-example"

    def test_punctuation_stripping_complex(self):
        """Test various punctuation marks are handled correctly."""
        result = deterministic_slug("Analysis & Results: (A Study)", prefix_index=0, width=3)
        assert result == "000-analysis-results-a-study"

    def test_width_handling_single_digit(self):
        """Test width=1 produces single digit prefix."""
        result = deterministic_slug("Test Title", prefix_index=5, width=1)
        assert result == "5-test-title"

    def test_width_handling_three_digits(self):
        """Test width=3 produces three digit prefix with zero padding."""
        result = deterministic_slug("Test Title", prefix_index=7, width=3)
        assert result == "007-test-title"

    def test_width_handling_large_index(self):
        """Test that large index values work correctly with padding."""
        result = deterministic_slug("Test Title", prefix_index=123, width=2)
        assert result == "123-test-title"  # Width doesn't truncate, just sets minimum

    def test_no_prefix_index(self):
        """Test slug generation without prefix index."""
        result = deterministic_slug("Introduction to Data")
        assert result == "introduction-to-data"

    def test_empty_string(self):
        """Test handling of empty string."""
        result = deterministic_slug("", prefix_index=1, width=2)
        assert result == "01-"

    def test_whitespace_normalization(self):
        """Test that leading/trailing whitespace is handled."""
        result = deterministic_slug("  Spaced Out Title  ", prefix_index=1, width=2)
        assert result == "01-spaced-out-title"

    def test_case_normalization(self):
        """Test that case is normalized to lowercase."""
        result = deterministic_slug("UPPERCASE Title", prefix_index=1, width=2)
        assert result == "01-uppercase-title"

    def test_special_characters_unicode(self):
        """Test handling of unicode and special characters."""
        result = deterministic_slug("Résumé & Café", prefix_index=1, width=2)
        assert result == "01-resume-cafe"  # Should be slugified properly

    def test_numbers_in_title(self):
        """Test that numbers are preserved in slugs."""
        result = deterministic_slug("Section 1.2.3 Analysis", prefix_index=5, width=2)
        assert result == "05-section-1-2-3-analysis"


class TestCollisionSuffixing:
    """Tests for Task 7.2: Collision suffixing."""

    def test_no_collision_simple(self):
        """Test that unique slugs are used as-is."""
        used_slugs: set[str] = set()
        result = generate_unique_slug(
            "Introduction", prefix_index=0, width=2, used_slugs=used_slugs
        )
        assert result == "00-introduction"
        assert "00-introduction" in used_slugs

    def test_single_collision_duplicate_title(self):
        """Test scenario: duplicate titles get -2 suffix."""
        used_slugs: set[str] = set()

        # First occurrence
        result1 = generate_unique_slug(
            "Data Analysis", prefix_index=0, width=2, used_slugs=used_slugs
        )
        assert result1 == "00-data-analysis"

        # Second occurrence (collision)
        result2 = generate_unique_slug(
            "Data Analysis", prefix_index=1, width=2, used_slugs=used_slugs
        )
        assert result2 == "01-data-analysis-2"

    def test_multiple_collisions(self):
        """Test multiple collisions with same base slug."""
        used_slugs: set[str] = set()

        # First occurrence
        result1 = generate_unique_slug(
            "Introduction", prefix_index=0, width=2, used_slugs=used_slugs
        )
        assert result1 == "00-introduction"

        # Second occurrence
        result2 = generate_unique_slug(
            "Introduction", prefix_index=1, width=2, used_slugs=used_slugs
        )
        assert result2 == "01-introduction-2"

        # Third occurrence
        result3 = generate_unique_slug(
            "Introduction", prefix_index=2, width=2, used_slugs=used_slugs
        )
        assert result3 == "02-introduction-3"

    def test_collision_with_different_prefixes(self):
        """Test that prefixes make slugs unique, but same base text collides."""
        used_slugs: set[str] = set()

        # Different base texts should not collide
        result1 = generate_unique_slug(
            "Introduction", prefix_index=0, width=2, used_slugs=used_slugs
        )
        result2 = generate_unique_slug("Conclusion", prefix_index=1, width=2, used_slugs=used_slugs)
        assert result1 == "00-introduction"
        assert result2 == "01-conclusion"

        # Same base text with different prefix should collide
        result3 = generate_unique_slug(
            "Introduction", prefix_index=2, width=2, used_slugs=used_slugs
        )
        assert result3 == "02-introduction-2"

    def test_collision_stable_ordering(self):
        """Test that collision numbering is stable and predictable."""
        used_slugs: set[str] = set()

        # Add some collisions in order
        results = []
        for i in range(5):
            result = generate_unique_slug("Test", prefix_index=i, width=2, used_slugs=used_slugs)
            results.append(result)

        # Should get predictable suffixes
        assert results[0] == "00-test"
        assert results[1] == "01-test-2"
        assert results[2] == "02-test-3"
        assert results[3] == "03-test-4"
        assert results[4] == "04-test-5"

    def test_collision_without_prefix(self):
        """Test collision handling when no prefix is used."""
        used_slugs: set[str] = set()

        result1 = generate_unique_slug(
            "introduction", prefix_index=None, width=2, used_slugs=used_slugs
        )
        assert result1 == "introduction"

        result2 = generate_unique_slug(
            "introduction", prefix_index=None, width=2, used_slugs=used_slugs
        )
        assert result2 == "introduction-2"

    def test_collision_with_complex_punctuation(self):
        """Test collision handling with complex text that gets normalized."""
        used_slugs: set[str] = set()

        # These should normalize to the same base slug
        result1 = generate_unique_slug(
            "Chapter's \"Introduction\"", prefix_index=0, width=2, used_slugs=used_slugs
        )
        result2 = generate_unique_slug(
            "Chapters Introduction", prefix_index=1, width=2, used_slugs=used_slugs
        )

        assert result1 == "00-chapters-introduction"
        assert result2 == "01-chapters-introduction-2"

    def test_numbered_titles_no_false_collision(self):
        """Test that numbered titles like 'Section 1', 'Section 2' don't falsely collide."""
        used_slugs: set[str] = set()

        # "Section 1" should get "00-section-1"
        result1 = generate_unique_slug("Section 1", prefix_index=0, width=2, used_slugs=used_slugs)
        assert result1 == "00-section-1"

        # "Section 2" should get "01-section-2" (not a collision with Section 1)
        result2 = generate_unique_slug("Section 2", prefix_index=1, width=2, used_slugs=used_slugs)
        assert result2 == "01-section-2"

        # Plain "Section" should get "02-section" (not section-3)
        result3 = generate_unique_slug("Section", prefix_index=2, width=2, used_slugs=used_slugs)
        assert result3 == "02-section"

        # Second occurrence of "Section" should get collision suffix
        result4 = generate_unique_slug("Section", prefix_index=3, width=2, used_slugs=used_slugs)
        assert result4 == "03-section-2"

    def test_used_slugs_set_mutation(self):
        """Test that the used_slugs set is properly updated."""
        used_slugs: set[str] = set()

        generate_unique_slug("Test", prefix_index=0, width=2, used_slugs=used_slugs)
        assert len(used_slugs) == 1
        assert "00-test" in used_slugs

        generate_unique_slug("Test", prefix_index=1, width=2, used_slugs=used_slugs)
        assert len(used_slugs) == 2
        assert "01-test-2" in used_slugs
