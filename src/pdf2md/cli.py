from __future__ import annotations
import typer
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
    # placeholder logic
    typer.echo(f"[dry] Parsed config: {cfg.model_dump()}")
    typer.echo("Conversion logic not yet implemented.")
    if manifest:
        (out / "manifest.json").write_text(json.dumps({"status": "stub"}, indent=2), encoding="utf-8")

@app.command("dry-run")
def dry_run(pdf_path: Path, max_pages: int | None = None, config: Path | None = None):
    """Preview detected structure without writing output (stub)."""
    typer.echo("Dry run not implemented yet.")

if __name__ == "__main__":  # pragma: no cover
    app()
