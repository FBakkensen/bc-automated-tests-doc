# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Build/Lint/Test Commands (Non-Standard)
- Run: pdf2md convert <pdf_path> [options] (CLI entry; stubbed, echoes config).
- Test all: pytest -q (quiet mode suppresses details).
- Single test: pytest tests/test_utils.py::test_specific_func (requires conftest.py sys.path addition for src/ imports without install).
- Lint: ruff check . (line length 100).
- Type check: mypy . (strict=false, gradual typing).

## Code Style (Project-Specific)
- Use src/ layout; add src/ to sys.path in conftest.py for dev imports (no editable install needed).
- Mypy: python_version=3.11, no strict mode (allows partial annotations).

## Critical Patterns/Gotchas
- Determinism: Use utils.deterministic_slug(title, prefix_index=...) with slug_prefix_width for zero-padded ordering; avoid set/dict iteration order.
- Hyphenation: Apply repair_hyphenation only after line merging, before paragraph assembly.
- Heading detection: Start with is_heading_candidate (regex/uppercase heuristics), then font clustering in headings.py.
- I/O: Keep functions pure; restrict writes/image extraction to exporter.py.
- Config: Pass ToolConfig explicitly (no globals); load from YAML/JSON via ToolConfig.from_file.
- Models: Dataclasses for internal; Pydantic for validation (e.g., manifest schema).
- No network calls during conversion (PRD requirement).
- Implementation phasing: ingest.py → headings.py → structure.py → codeblocks.py/tables.py → figures.py → build_tree.py → render.py → exporter.py → postprocess.py.
- Testing: Use synthetic samples in tests/fixtures and tests/golden/ (no large PDFs in repo); check determinism via structural tree hash.
- TDD: Add unit tests for every new heuristic/transformation; ensure no syntax/import errors pre-PR.
- Performance: Stream pages with generators; defer image rasterization post-text extraction.
- Errors: Raise targeted exceptions (e.g., for PDF readability); CLI exits map to codes (1:general, 2:config, 3:I/O, 4:parse).
- CLI stub: Writes partial manifest.json without full processing; --resume planned but unused.
- Lazy imports: __init__.py uses __getattr__ to defer ToolConfig (avoids cycles in tests).
- Global chapter numbering (no per-part reset, log warnings).

## Mandatory Documentation Validation Rule

All agents must perform a clean validation of the doc/ directory files (e.g., doc/design.md and others) whenever they are touched, modified, or referenced in any task. This is a mandatory pre-action step in agent workflows, similar to pre-commit/CI hooks, to enforce documentation integrity. The rule applies to all modes (code, architect, etc.).

### When to Run
Run validation for any task that involves touching, modifying, or referencing files in the doc/ directory.

### How to Run
Execute `bash scripts/validate-md.sh` from the project root.

### Tool Checks and Failures
The script ensures that required tools are installed and functional:
- markdownlint-cli
- @mermaid-js/mermaid-cli (mmdc)
- pandoc

If any tool is missing, the script fails with a non-zero exit code and provides clear installation instructions, such as:
- For Windows: `choco install pandoc; npm install -g @mermaid-js/mermaid-cli markdownlint-cli`
- For Linux: Use appropriate package managers (e.g., `apt install pandoc; npm install -g @mermaid-js/mermaid-cli markdownlint-cli`)

### Expected Output
The validation checks for:
- Markdown linting errors
- Mermaid diagram rendering to SVG/PDF
- Pandoc conversion success

On pass, it reports "Total errors: 0". Otherwise, it provides detailed errors with suggested fixes.

### Cross-Platform Compatibility
The Python script ensures compatibility across Linux and Windows. Use Python for execution on both platforms.

### References
For implementation details, see [doc/validation-design.md](doc/validation-design.md) and [doc/dev-workflow.md](doc/dev-workflow.md). This rule builds on the completed tasks for validation system architecture and workflow integration.