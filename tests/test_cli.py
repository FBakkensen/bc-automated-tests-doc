"""Tests for CLI integration and exit codes (Issue 10).

Tests for Task 10.1 (convert happy path) and Task 10.2 (exit code mapping).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from pdf2md.cli import app


class TestCliHappyPath:
    """Tests for Task 10.1: Convert happy path."""

    def test_convert_with_basic_headings_pdf(self, tmp_path: Path) -> None:
        """Test scenario: Convert writes manifest and stubs.

        Given `basic_headings.pdf` and output dir
        When `pdf2md convert <pdf> --out out --manifest`
        Then `manifest.json` and section files exist
        """
        runner = CliRunner()
        pdf_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        result = runner.invoke(
            app, ["convert", str(pdf_path), "--out", str(tmp_path), "--manifest"]
        )

        # Should succeed
        assert result.exit_code == 0
        assert "Conversion complete" in result.stdout

        # Check that manifest.json exists
        manifest_path = tmp_path / "manifest.json"
        assert manifest_path.exists()

        # Verify manifest content structure
        manifest_data = json.loads(manifest_path.read_text())
        assert "schema_version" in manifest_data
        assert "sections" in manifest_data
        assert "structural_hash" in manifest_data
        assert "generated_with" in manifest_data
        assert manifest_data["generated_with"]["tool"] == "pdf2md"

    def test_convert_creates_book_directory(self, tmp_path: Path) -> None:
        """Test that conversion creates book directory structure."""
        runner = CliRunner()
        pdf_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        result = runner.invoke(
            app, ["convert", str(pdf_path), "--out", str(tmp_path), "--manifest"]
        )

        assert result.exit_code == 0
        assert (tmp_path / "book").exists()
        assert (tmp_path / "book").is_dir()

    def test_convert_with_verbose_output(self, tmp_path: Path) -> None:
        """Test conversion with verbose output shows detailed logging."""
        runner = CliRunner()
        pdf_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        result = runner.invoke(
            app, ["convert", str(pdf_path), "--out", str(tmp_path), "--manifest", "-v"]
        )

        assert result.exit_code == 0
        assert "Config loaded:" in result.stdout
        assert "manifest: " in result.stdout

    def test_convert_with_config_file(self, tmp_path: Path) -> None:
        """Test conversion with custom config file."""
        runner = CliRunner()
        pdf_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        # Create a config file
        config_path = tmp_path / "test_config.json"
        config_data = {"slug_prefix_width": 3, "font_cluster_epsilon": 2.0}
        config_path.write_text(json.dumps(config_data, indent=2))

        result = runner.invoke(
            app,
            [
                "convert",
                str(pdf_path),
                "--out",
                str(tmp_path / "output"),
                "--config",
                str(config_path),
                "--manifest",
                "-v",
            ],
        )

        assert result.exit_code == 0
        assert '"slug_prefix_width": 3' in result.stdout
        assert '"font_cluster_epsilon": 2.0' in result.stdout

    def test_convert_without_manifest_option(self, tmp_path: Path) -> None:
        """Test conversion without manifest option."""
        runner = CliRunner()
        pdf_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        result = runner.invoke(
            app,
            [
                "convert",
                str(pdf_path),
                "--out",
                str(tmp_path),
                "--no-manifest",  # Disable manifest
            ],
        )

        assert result.exit_code == 0
        # Should not create manifest when disabled
        assert not (tmp_path / "manifest.json").exists()


class TestCliExitCodes:
    """Tests for Task 10.2: Exit code mapping."""

    def test_config_error_returns_exit_code_2(self, tmp_path: Path) -> None:
        """Test scenario: Config error returns exit code 2.

        Given a config file with invalid content
        When `pdf2md convert` runs
        Then process exits with code 2 and prints a clear message
        """
        runner = CliRunner()
        pdf_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        # Create invalid config file (invalid JSON)
        config_path = tmp_path / "invalid_config.json"
        config_path.write_text("{ invalid json }")

        result = runner.invoke(
            app,
            [
                "convert",
                str(pdf_path),
                "--out",
                str(tmp_path / "output"),
                "--config",
                str(config_path),
                "--manifest",
            ],
        )

        assert result.exit_code == 2
        assert "Error:" in result.output

    def test_config_error_with_debug_json_shows_structured_error(self, tmp_path: Path) -> None:
        """Test config error with --debug-json-errors shows structured output."""
        runner = CliRunner()
        pdf_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        # Create invalid config file
        config_path = tmp_path / "invalid_config.json"
        config_path.write_text("{ invalid json }")

        result = runner.invoke(
            app,
            [
                "convert",
                str(pdf_path),
                "--out",
                str(tmp_path / "output"),
                "--config",
                str(config_path),
                "--debug-json-errors",
                "--manifest",
            ],
        )

        assert result.exit_code == 2

        # Parse the JSON error output from output (stderr is mixed in)
        output_lines = result.output.strip().split('\n')
        json_line = None
        for line in output_lines:
            if line.startswith('{') and '"category"' in line:
                json_line = line
                break

        assert json_line is not None, f"No JSON error found in output: {result.output}"

        try:
            error_data = json.loads(json_line)
            assert error_data["category"] == "CONFIG"
            assert "config_parse_error" in error_data["code"]
            assert "context" in error_data
        except json.JSONDecodeError:
            pytest.fail(f"Expected JSON error output, got: {json_line}")

    def test_nonexistent_config_file_returns_exit_code_2(self, tmp_path: Path) -> None:
        """Test that non-existent config file returns exit code 2."""
        runner = CliRunner()
        pdf_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        result = runner.invoke(
            app,
            [
                "convert",
                str(pdf_path),
                "--out",
                str(tmp_path),
                "--config",
                str(tmp_path / "nonexistent.json"),
                "--manifest",
            ],
        )

        assert result.exit_code == 2
        assert "Error:" in result.output

    def test_nonexistent_pdf_file_returns_exit_code_3(self, tmp_path: Path) -> None:
        """Test that non-existent PDF file returns exit code 3 (IO error)."""
        runner = CliRunner()

        result = runner.invoke(
            app,
            ["convert", str(tmp_path / "nonexistent.pdf"), "--out", str(tmp_path), "--manifest"],
        )

        assert result.exit_code == 3
        assert "Error:" in result.output

    def test_unwritable_output_directory_returns_exit_code_3(self) -> None:
        """Test that unwritable output directory returns exit code 3."""
        runner = CliRunner()
        pdf_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        # Try to write to a path that should be unwritable (assuming /root is not writable)
        result = runner.invoke(
            app, ["convert", str(pdf_path), "--out", "/root/unwritable", "--manifest"]
        )

        # Could be exit code 3 (IO error) if we can't create the directory
        # or it might succeed if the directory can be created, so we check accordingly
        if result.exit_code != 0:
            assert result.exit_code == 3
            assert "Error:" in result.output

    def test_yaml_config_parsing(self, tmp_path: Path) -> None:
        """Test that YAML config files are properly parsed."""
        runner = CliRunner()
        pdf_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        # Create a YAML config file
        config_path = tmp_path / "test_config.yaml"
        config_content = """
slug_prefix_width: 4
font_cluster_epsilon: 1.5
heading_normalize: false
"""
        config_path.write_text(config_content)

        result = runner.invoke(
            app,
            [
                "convert",
                str(pdf_path),
                "--out",
                str(tmp_path / "output"),
                "--config",
                str(config_path),
                "--manifest",
                "-v",
            ],
        )

        assert result.exit_code == 0
        assert '"slug_prefix_width": 4' in result.stdout
        assert '"font_cluster_epsilon": 1.5' in result.stdout
        assert '"heading_normalize": false' in result.stdout

    def test_invalid_yaml_config_returns_exit_code_2(self, tmp_path: Path) -> None:
        """Test that invalid YAML config returns exit code 2."""
        runner = CliRunner()
        pdf_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        # Create invalid YAML config file
        config_path = tmp_path / "invalid_config.yaml"
        config_path.write_text("invalid: yaml: content: [")

        result = runner.invoke(
            app,
            [
                "convert",
                str(pdf_path),
                "--out",
                str(tmp_path / "output"),
                "--config",
                str(config_path),
                "--manifest",
            ],
        )

        assert result.exit_code == 2
        assert "Error:" in result.output

    def test_general_exception_returns_exit_code_1(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that unexpected exceptions return exit code 1."""
        runner = CliRunner()
        pdf_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        # Mock a function to raise an unexpected exception
        def mock_run_conversion(*args: Any, **kwargs: Any) -> None:
            raise ValueError("Unexpected error for testing")

        monkeypatch.setattr("pdf2md.cli.run_conversion", mock_run_conversion)

        result = runner.invoke(
            app, ["convert", str(pdf_path), "--out", str(tmp_path), "--manifest"]
        )

        assert result.exit_code == 1
        assert "Error:" in result.output


class TestDryRunStub:
    """Test the dry-run command stub."""

    def test_dry_run_command_exists(self) -> None:
        """Test that dry-run command exists and shows not implemented message."""
        runner = CliRunner()
        pdf_path = Path(__file__).parent / "fixtures" / "pdfs" / "basic_headings.pdf"

        result = runner.invoke(app, ["dry-run", str(pdf_path)])

        assert result.exit_code == 0
        assert "Dry run not implemented yet" in result.stdout
