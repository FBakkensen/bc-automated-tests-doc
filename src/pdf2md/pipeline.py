"""Pipeline orchestration for pdf2md conversion.

This module provides the main run_conversion function that orchestrates the entire
PDF to Markdown conversion pipeline, integrating all components.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .build_tree import build_tree
from .errors import ParseError, PdfUnreadableError
from .exporter import export_manifest
from .ingest import PdfIngestor
from .render import render_sections
from .structure import assemble_blocks

if TYPE_CHECKING:
    from .config import ToolConfig

logger = logging.getLogger(__name__)


def run_conversion(
    pdf_path: Path,
    output_dir: Path,
    config: ToolConfig,
    *,
    max_pages: int | None = None,
    manifest: bool = True,
    toc: bool = True,
) -> dict[str, str]:
    """Run the complete PDF to Markdown conversion pipeline.

    Args:
        pdf_path: Path to input PDF file
        output_dir: Directory to write output files
        config: Configuration object
        max_pages: Optional limit on number of pages to process
        manifest: Whether to write manifest.json
        toc: Whether to write table of contents (not implemented yet)

    Returns:
        Dictionary mapping output file paths to their content types

    Raises:
        PdfUnreadableError: If PDF cannot be read
        IOError: If output directory cannot be created or written to
        ParseError: If PDF structure cannot be parsed
    """
    # Validate inputs
    if not pdf_path.exists():
        raise PdfUnreadableError(f"PDF file not found: {pdf_path}", {"path": str(pdf_path)})

    if not pdf_path.is_file():
        raise PdfUnreadableError(f"Path is not a file: {pdf_path}", {"path": str(pdf_path)})

    # Ensure output directory exists
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        from .errors import OutputPathUnwritableError

        raise OutputPathUnwritableError(
            f"Cannot create output directory: {e}", {"path": str(output_dir), "error": str(e)}
        ) from e

    if not output_dir.is_dir():
        from .errors import OutputPathUnwritableError

        raise OutputPathUnwritableError(
            f"Output path is not a directory: {output_dir}", {"path": str(output_dir)}
        )

    logger.info(f"Starting conversion of {pdf_path} to {output_dir}")

    # Step 1: Ingestion - extract spans from PDF
    logger.info("Step 1: Ingesting PDF...")
    try:
        ingestor = PdfIngestor(config)
        spans = ingestor.extract_spans(pdf_path)
        logger.info(f"Extracted {len(spans)} spans")
    except Exception as e:
        raise PdfUnreadableError(
            f"Failed to extract content from PDF: {e}", {"path": str(pdf_path), "error": str(e)}
        ) from e

    if not spans:
        logger.warning("No text spans extracted from PDF")

    # Step 2: Block Assembly - group spans into logical blocks
    logger.info("Step 2: Assembling blocks...")
    try:
        blocks = assemble_blocks(spans, config)
        logger.info(f"Assembled {len(blocks)} blocks")
    except Exception as e:
        raise ParseError(
            f"Failed to assemble text blocks: {e}", {"spans_count": len(spans), "error": str(e)}
        ) from e

    # Step 3: Tree Building - create hierarchical structure
    logger.info("Step 3: Building document tree...")
    try:
        sections = build_tree(blocks, config)
        logger.info(f"Built tree with {len(sections)} root sections")
    except Exception as e:
        raise ParseError(
            f"Failed to build document tree: {e}", {"blocks_count": len(blocks), "error": str(e)}
        ) from e

    # Step 4: Rendering - generate markdown files
    logger.info("Step 4: Rendering sections...")
    try:
        output_file_paths = render_sections(sections, output_dir, config)
        logger.info(f"Rendered {len(output_file_paths)} section files")
    except Exception as e:
        from .errors import OutputPathUnwritableError

        raise OutputPathUnwritableError(
            f"Failed to write section files: {e}", {"output_dir": str(output_dir), "error": str(e)}
        ) from e

    # Step 5: Export manifest if requested
    results: dict[str, str] = {}
    # Add section files to results
    for file_path in output_file_paths:
        results[str(file_path)] = "section"

    if manifest:
        logger.info("Step 5: Exporting manifest...")
        try:
            manifest_path = export_manifest(
                sections=sections,
                output_dir=output_dir,
                config=config,
            )
            results[str(manifest_path)] = "manifest"
            logger.info(f"Exported manifest to {manifest_path}")
        except Exception as e:
            from .errors import OutputPathUnwritableError

            raise OutputPathUnwritableError(
                f"Failed to write manifest: {e}", {"output_dir": str(output_dir), "error": str(e)}
            ) from e

    # TODO: Step 6: TOC generation (when toc=True)
    if toc:
        logger.info("TOC generation not yet implemented")

    logger.info(f"Conversion complete: {len(results)} files written")
    return results
