# pdf2md (Scaffold)

Early scaffold for the Technical PDF to Structured Markdown Conversion Tool described in `doc/prd.md`.

## Features (planned)
See PRD for comprehensive requirements. Current scaffold provides:
- Config model (`ToolConfig`)
- Core data structures (`Span`, `Node`, etc.)
- Utility helpers (slug generation, hyphenation repair, heading heuristic)
- Typer CLI skeleton with `convert` and `dry-run` commands (stubs)
- Initial pytest tests for utilities

## Local Development

### 1. Create & activate virtual environment (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

(Unix / WSL)
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies
```powershell
pip install -e .[dev]
```

### 3. Run tests
```powershell
pytest
```

### 4. Run CLI (stub)
```powershell
pdf2md convert .\pdf\AUTOMATED_TESTING_IN_MICROSOFT_DYNAMICS_365_BUSI.pdf --out output --manifest
```

## Next Implementation Steps
1. Implement PDF ingestion producing `Span` objects (pdfplumber).
2. Font size clustering & heading tree builder.
3. Paragraph/list assembly & code block detection.
4. Image extraction (pypdf + pdf2image fallback) with captions.
5. Table detection pipeline.
6. Markdown file rendering + manifest & optional TOC export.
7. Cross-reference linking & footnotes.
8. Performance tuning & deterministic hashing.

## Config
Create a YAML file and pass with `--config`:
```yaml
font_cluster_epsilon: 1.0
slug_prefix_width: 2
```

## License
MIT (adjust as needed).
