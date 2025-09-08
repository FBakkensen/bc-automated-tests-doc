# Copilot Project Instructions: pdf2md

**ALWAYS FOLLOW THESE INSTRUCTIONS FIRST.** Only fall back to additional search and context gathering if the information in these instructions is incomplete or found to be in error.

These instructions guide AI coding agents contributing to this repository. Focus on delivering the PDF→Structured Markdown pipeline incrementally while preserving determinism and testability.

## Project Purpose
Convert technical, text-based PDFs into a multi-file, semantically structured Markdown corpus (chapters, sections, code blocks, tables, figures, footnotes, manifest, optional TOC) with high fidelity and deterministic output.

## Working Effectively

**CRITICAL**: Follow these exact commands for a fresh clone. All timing estimates include 50% buffer. NEVER CANCEL any long-running command.

### 1. Initial Setup (Required)
Create and activate virtual environment:
```bash
cd /path/to/bc-automated-tests-doc
python -m venv .venv
source .venv/bin/activate  # Unix/WSL
# OR on Windows PowerShell:
# .\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies (~45 seconds - NEVER CANCEL)
```bash
pip install -e .[dev]
```
**Expected timing**: 30-45 seconds. Installs Python dependencies including pdfplumber, pytest, ruff, mypy, and all development tools.

**TROUBLESHOOTING**: If pip install fails:
- Retry the command if timeout errors occur
- Consider using `pip install -e .[dev] --timeout 300` for extended timeout
- Network access has been configured and should work reliably

### 3. Code Quality Checks (~15 seconds - NEVER CANCEL)
Run the complete local validation suite:
```bash
bash scripts/local-check.sh
```
**Expected timing**: 1-2 seconds. This runs all checks that CI will run:
- Ruff format check (~0.02 seconds)
- Ruff linting (~0.05 seconds) 
- Mypy type checking (~11 seconds)
- pytest unit tests (~1.2 seconds)

### 4. Individual Development Commands
```bash
# Run tests only (~2 seconds)
pytest -q

# Check code formatting 
ruff format --check .

# Auto-fix formatting issues
ruff format .

# Run linting
ruff check .

# Type checking (~15 seconds - NEVER CANCEL)
mypy .

# Test CLI functionality
pdf2md --help
pdf2md convert pdf/AUTOMATED_TESTING_IN_MICROSOFT_DYNAMICS_365_BUSI.pdf --out /tmp/output --manifest
```

### 5. Documentation Validation (~45 seconds)
Run documentation validation with all tools:
```bash
# Install tools (network access configured)
npm install -g @mermaid-js/mermaid-cli markdownlint-cli
sudo apt-get update && sudo apt-get install -y pandoc

# Run validation
bash scripts/validate-md.sh doc/*.md
```
**Expected timing**: ~45 seconds total for npm install, ~10 seconds for apt install, ~5 seconds for validation.

## Manual Validation Scenarios

**ALWAYS** test these scenarios after making changes to ensure functionality:

### Core PDF Processing Validation
1. **CLI Help Test**: Run `pdf2md --help` - should display command usage without errors
2. **Basic Conversion Test**: Run `pdf2md convert pdf/AUTOMATED_TESTING_IN_MICROSOFT_DYNAMICS_365_BUSI.pdf --out /tmp/test-output --manifest`
   - Should complete without errors
   - Should display configuration object
   - Should report "Stubbed conversion complete"
3. **Config Loading Test**: Conversion should load and display configuration with all expected fields
4. **Output Directory Test**: Ensure the tool can write to specified output directories

### Code Quality Validation  
1. **Formatting Test**: Run `ruff format .` followed by `ruff format --check .` - should report "files already formatted"
2. **Linting Test**: Run `ruff check .` - should report "All checks passed!"
3. **Type Safety Test**: Run `mypy .` - should report "Success: no issues found" (notes about untyped functions are acceptable)
4. **Test Suite Test**: Run `pytest -q` - all tests should pass, no failures

### Pre-Commit Validation
1. **Local Check Script**: Run `bash scripts/local-check.sh` - should pass all 4 stages
2. **Individual Tool Tests**: Verify each tool (ruff, mypy, pytest) works independently
3. **CI Compatibility**: Local checks should match what CI will run

## High-Level Architecture (Planned)
1. Ingestion: Stream PDF pages → raw layout objects (pdfplumber + pdfminer.six under the hood).
2. Normalization: Convert to `Span` objects (text, bbox, font meta, page).
3. Semantic Detection: Build a tree of `Node` types (Part / Chapter / Section / Paragraph / List / CodeBlock / Table / Figure / Footnote).
4. Post-Processing: Slug assignment, cross-reference linking, footnote resolution, dedup noise removal.
5. Rendering: Emit Markdown fragments per logical chapter/file (respect slug + numbering policy).
6. Export: Write files, images, `manifest.json`, optional `toc.yml`.

Keep layers loosely coupled. Avoid embedding rendering concerns in ingestion or detection.

## Key Data Structures (in `src/pdf2md/models.py`)
- `Span`: smallest textual layout unit with bounding box + font info.
- `Node`: generic tree node; subtype via `type` + `meta` (avoid premature inheritance).
- `Figure`, `CodeBlock`, `Table`, `ManifestEntry`: logical artifacts produced mid/late pipeline.

## Configuration (`ToolConfig` in `config.py`)
- Central source for heuristic thresholds (e.g., `font_cluster_epsilon`, `list_indent_tolerance`).
- Always pass a `ToolConfig` instance explicitly into new pipeline functions (no hidden globals).
- Support loading from YAML or JSON via `ToolConfig.from_file`.

## Conventions & Patterns
- Determinism: sorting, slug prefixes, and file naming must not depend on set/dict iteration order. Use explicit ordered lists.
- Slugs: use `utils.deterministic_slug(title, prefix_index=...)` with `slug_prefix_width` for zero-padded ordering.
- Hyphenation: run `repair_hyphenation` only after line merging, before paragraph assembly.
- Heading detection: start with size/regex heuristics (see `is_heading_candidate`), then refine with font clustering (to be implemented in a dedicated module, e.g. `headings.py`).
- Keep pure functions side-effect free; isolate I/O (filesystem writes, image extraction) to late pipeline steps (e.g., `exporter.py`).
- CLI (`cli.py`) should remain thin: parse args, load config, delegate to orchestration function (proposed: `run_conversion(config: ToolConfig, pdf_path: Path, out_dir: Path, ...)`).
- Use `dataclasses` for internal modeling except where validation/serialization is needed (then Pydantic models are appropriate, e.g., outward-facing manifest schema in future).
- No network calls during conversion (security requirement in PRD).

## Implementation Order (Recommended Incremental PRs)
1. Ingestion module (`ingest.py`): yield `Span` objects page by page.
2. Font stats + heading tier clustering (`headings.py`).
3. Line → paragraph assembler + hyphenation + list detection (`structure.py`).
4. Code block detector (`codeblocks.py`) and table extraction wrapper (`tables.py`).
5. Figure extractor (`figures.py`) using `pypdf` (embedded) then `pdf2image` fallback.
6. Tree builder & slug assignment (`build_tree.py`).
7. Renderer (`render.py`) producing Markdown text chunks + asset links.
8. Manifest + TOC exporter (`exporter.py`).
9. Cross-reference & footnote resolver (`postprocess.py`).

## Testing Strategy
- Unit tests: Each heuristic (slug, hyphenation, heading candidate, list nesting soon) is a pure function and should remain easily testable.
- Future golden tests: small synthetic PDFs producing snapshot markdown (store under `tests/fixtures` + `tests/golden/`). Do NOT add large binary PDFs to repo; prefer minimal crafted samples.
- Determinism check: hash of serialized structural tree should be stable across runs (add later).

## TDD Requirement
- Strict TDD: This project follows a strict test-driven development (TDD) flow. Every code change must include or update unit tests that cover the new behavior. Before returning work (or creating a PR), ensure all tests at minimum parse and collect successfully (no syntax/import/collection errors) when run locally. Aim for tests to pass; CI may enforce passing tests for merges.

## Using Context7 for External Docs
- When documentation or code examples for an external library are needed, use the Context7 tools in this order: first call the resolver to obtain a Context7-compatible library ID, then fetch the library docs with that ID. This ensures accurate, up-to-date examples and reduces ambiguity. Example workflow:
    1. Call `mcp_context7_resolve-library-id` with the library name to get the library ID.
    2. Call `mcp_context7_get-library-docs` with the returned ID and topic to retrieve focused documentation.
 3. Use the fetched docs as the authoritative source when generating code or writing examples. Do not skip the resolver step unless the exact Context7 ID is provided.

## Performance & Memory
- Stream pages (generator) rather than accumulating all page objects in memory.
- Defer expensive operations (image rasterization) until after structural text extraction is complete.
- Consider optional parallelism only for image extraction step (I/O bound) after correctness established.

## Error Handling
- Raise clear exceptions for: unreadable PDF, config parse failure, output path unwritable.
- Non-zero exit codes to match PRD (1 general, 2 config, 3 I/O, 4 parse fatal) when wiring CLI exit logic.

## Style & Quality
- Keep functions small and composable; avoid mega-procedures blending multiple heuristic concerns.
- Prefer dependency injection (pass config + logger) over importing singletons.
- Add type hints everywhere; use `from __future__ import annotations` (already present) for forward references.
- Avoid premature micro-optimizations until functional completeness and correctness are validated.

## Code Quality & Local Checks

**CRITICAL TIMING**: Set timeouts of 60+ seconds for any command that includes mypy or full test suites.

- **ALWAYS run local checks before committing** to ensure CI passes. Use `bash scripts/local-check.sh` or run individual tools:
  - `ruff format --check .` - Code formatting (matches CI exactly) - ~0.02 seconds
  - `ruff check .` - Linting - ~0.05 seconds
  - `mypy .` - Type checking - ~11 seconds, **NEVER CANCEL**
  - `pytest -q` - Unit tests - ~1.2 seconds
- **Code formatting is mandatory**: Run `ruff format .` to auto-fix formatting issues before committing. CI will fail if code is not properly formatted.
- Install dev dependencies with `pip install -e .[dev]` to get all required tools.
- Pre-commit hooks are configured but local checks provide faster feedback.

## Known Issues & Notes

### Environment Setup
- **Network access**: Fully configured and working reliably for all package installations
- **pip install timing**: 30-45 seconds expected, includes comprehensive dependency installation
- **npm install timing**: ~45 seconds for documentation tools installation
- **apt install timing**: ~10 seconds for pandoc installation

### Documentation Validation  
- All documentation validation tools now work reliably
- No fallback modes or workarounds needed
- Full toolchain available: markdownlint-cli, mermaid-cli, pandoc

### Environment-Specific Notes
- **Network access**: Fully functional with comprehensive package repository access
- **Installation reliability**: All tools install successfully and reliably
- **Timeout handling**: All timeouts are set with 50% buffer over measured times

### CI Pipeline Compatibility  
- All local commands match CI exactly
- Documentation validation runs successfully with full toolchain
- Code quality checks are identical between local and CI environments
- Network access enables full feature testing locally

## Repository Structure & Key Locations

### Critical Files
- `src/pdf2md/` - Main source code directory
- `tests/` - Unit test suite  
- `scripts/local-check.sh` - Local validation script (matches CI exactly)
- `scripts/validate-md.sh` - Documentation validation
- `pyproject.toml` - Project configuration, dependencies, tool settings
- `.github/workflows/` - CI pipeline definitions
- `AGENTS.md` - Additional agent-specific guidance

### Common File Outputs
```
Repository root structure:
├── .github/
│   ├── copilot-instructions.md (this file)
│   └── workflows/ (CI definitions)
├── src/pdf2md/ (main codebase)
│   ├── __init__.py
│   ├── cli.py (command-line interface)
│   ├── config.py (ToolConfig)
│   └── utils.py (utilities including slugs)
├── tests/ (unit tests)
├── doc/ (project documentation)
├── pdf/ (sample PDF for testing)
├── scripts/ (automation scripts)
├── pyproject.toml (project config)
└── README.md (user documentation)
```

## Development Workflow

### Making Changes
1. **Setup**: Create virtual environment and install dependencies
2. **Validate baseline**: Run `bash scripts/local-check.sh` to ensure clean start
3. **Implement changes**: Follow TDD - write tests first, then implementation
4. **Test frequently**: Run `pytest` after each change
5. **Format code**: Run `ruff format .` before committing
6. **Final validation**: Run `bash scripts/local-check.sh` - **must pass before committing**

### Testing Changes
1. **Unit tests**: `pytest -q` for quick feedback
2. **Type safety**: `mypy .` for type correctness
3. **Code style**: `ruff check .` and `ruff format --check .`
4. **CLI functionality**: Test `pdf2md --help` and basic conversion
5. **Manual scenarios**: Follow validation scenarios above

## Common Commands Reference

### Quick Development Loop
```bash
# After making code changes:
pytest -q                    # Quick test (~1-2 seconds)
ruff format .               # Auto-fix formatting
bash scripts/local-check.sh # Full validation (~15 seconds, NEVER CANCEL)
```

### Debugging & Development
```bash
# Individual tests
pytest tests/test_utils_slugs.py::test_basic_slug_generation -v

# CLI testing
pdf2md --help
pdf2md convert pdf/AUTOMATED_TESTING_IN_MICROSOFT_DYNAMICS_365_BUSI.pdf --out /tmp/debug

# Type checking specific files
mypy src/pdf2md/utils.py

# Check specific formatting
ruff format --check src/pdf2md/
```

### CI Simulation
```bash
# Run exactly what CI runs:
bash scripts/local-check.sh

# Documentation validation:
bash scripts/validate-md.sh doc/*.md
```

**CRITICAL REMINDER**: Always run `bash scripts/local-check.sh` before committing. It runs the same checks as CI and prevents build failures.

## Future Extensions (Do Not Implement Prematurely)
- OCR fallback, glossary extraction, plugin hooks — reference PRD Roadmap; leave clear extension points (module boundaries, stable function signatures).

## Example Orchestration (Target Shape)
```python
# proposed in run.py (future)
from .ingest import iter_spans
from .headings import detect_headings
from .structure import assemble_blocks
from .build_tree import build_document_tree
from .render import render_markdown

def run_conversion(cfg, pdf_path, out_dir, *, max_pages=None):
    spans = iter_spans(pdf_path, cfg, max_pages=max_pages)
    heading_info = detect_headings(spans, cfg)
    blocks = assemble_blocks(spans, heading_info, cfg)
    tree = build_document_tree(blocks, cfg)
    assets = render_markdown(tree, out_dir, cfg)
    return assets
```

## When Adding New Code
- Add/extend a unit test for every new heuristic or transformation.
- Keep new modules under `src/pdf2md/` and update README only when functionality is user-visible.
- Do not break existing public CLI parameters without documenting the change.
- **Run `bash scripts/local-check.sh` before committing** to ensure all code quality checks pass locally (matches CI pipeline exactly).

---
Provide feedback if additional details (e.g., logging format, manifest schema draft) should be added.
