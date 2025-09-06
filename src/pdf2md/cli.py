from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from .config import ToolConfig

app = typer.Typer(add_completion=False, help="PDF to structured Markdown converter (scaffold)")


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
) -> None:
    """Convert a PDF into structured markdown (stub)."""
    if not pdf_path.exists():
        err_pdf_not_found = "PDF file not found"
        raise typer.BadParameter(err_pdf_not_found)
    if not out.exists():
        out.mkdir(parents=True)
    cfg = ToolConfig()
    if config:
        cfg = ToolConfig.from_file(str(config))
    # Echo config
    typer.echo(f"Config loaded: {cfg.model_dump_json(indent=2)}")
    # Write partial manifest.json
    manifest_data = {
        "version": "0.1.0",
        "source_pdf": str(pdf_path),
        "output_dir": str(out),
        "config": cfg.model_dump(),
        "status": "stubbed",
        "structural_hash": "TBD",
    }
    manifest_path = out / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    typer.echo("Stubbed conversion complete: partial manifest written.")


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
