from __future__ import annotations
import typer
import sys
from pathlib import Path
from .config import ToolConfig
import json

app = typer.Typer(add_completion=False, help="PDF to structured Markdown converter (scaffold)")

@app.command()
def convert(pdf_path: Path, out: Path = typer.Option(..., dir_okay=True, file_okay=False), config: Path | None = None, toc: bool = True, manifest: bool = True, force: bool = False, resume: bool = False, max_pages: int | None = None, verbose: int = typer.Option(0, "-v", count=True)):
    """Convert a PDF into structured markdown (stub)."""
    if not pdf_path.exists():
        raise typer.BadParameter("PDF file not found")
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
        "structural_hash": "TBD"
    }
    manifest_path = out / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    typer.echo("Stubbed conversion complete: partial manifest written.")

@app.command("dry-run")
def dry_run(pdf_path: Path, max_pages: int | None = None, config: Path | None = None):
    """Preview detected structure without writing output (stub)."""
    typer.echo("Dry run not implemented yet.")

if __name__ == "__main__":  # pragma: no cover
    app()
