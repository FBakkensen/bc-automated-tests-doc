from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

from .config import ToolConfig
from .errors import Pdf2MdError
from .pipeline import run_conversion

app = typer.Typer(add_completion=False, help="PDF to structured Markdown converter")


@app.command()
def convert(
    pdf_path: Annotated[Path, typer.Argument()],
    out: Annotated[Path, typer.Option(dir_okay=True, file_okay=False)],
    config: Annotated[Path | None, typer.Option()] = None,
    toc: Annotated[bool, typer.Option()] = True,
    manifest: Annotated[bool, typer.Option()] = True,
    force: Annotated[bool, typer.Option()] = False,
    resume: Annotated[bool, typer.Option()] = False,
    max_pages: Annotated[int | None, typer.Option()] = None,
    verbose: Annotated[int, typer.Option("-v", count=True)] = 0,
    debug_json_errors: Annotated[bool, typer.Option("--debug-json-errors")] = False,
) -> None:
    """Convert a PDF into structured markdown."""
    # Set up logging based on verbosity
    if verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose == 1:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    try:
        # Load configuration
        cfg = ToolConfig()
        if config:
            cfg = ToolConfig.from_file(str(config))

        if verbose > 0:
            typer.echo(f"Config loaded: {cfg.model_dump_json(indent=2)}")

        # Run the conversion pipeline
        output_files = run_conversion(
            pdf_path=pdf_path,
            output_dir=out,
            config=cfg,
            max_pages=max_pages,
            manifest=manifest,
            toc=toc,
        )

        # Report results
        typer.echo(f"Conversion complete: {len(output_files)} files written to {out}")
        if verbose > 0:
            for file_path, file_type in output_files.items():
                typer.echo(f"  {file_type}: {file_path}")

    except Pdf2MdError as e:
        if debug_json_errors:
            import json

            error_data = {
                "category": e.category,
                "code": e.error_code,
                "message": e.message,
                "context": e.context,
            }
            typer.echo(json.dumps(error_data), err=True)
        else:
            typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(e.exit_code) from e
    except Exception as e:
        # Fallback for any unhandled exceptions
        error = Pdf2MdError(f"Unexpected error: {e}")
        if debug_json_errors:
            import json

            error_data = {
                "category": error.category,
                "code": error.error_code,
                "message": error.message,
                "context": error.context,
            }
            typer.echo(json.dumps(error_data), err=True)
        else:
            typer.echo(f"Error: {error.message}", err=True)
        raise typer.Exit(error.exit_code) from e


@app.command("dry-run")
def dry_run(
    pdf_path: Annotated[Path, typer.Argument()],
    max_pages: Annotated[int | None, typer.Option()] = None,
    config: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Preview detected structure without writing output (stub)."""
    typer.echo("Dry run not implemented yet.")


if __name__ == "__main__":  # pragma: no cover
    app()
