# Copilot Project Instructions: pdf2md

These instructions guide AI coding agents contributing to this repository. Focus on delivering the PDF→Structured Markdown pipeline incrementally while preserving determinism and testability.

## Project Purpose
Convert technical, text-based PDFs into a multi-file, semantically structured Markdown corpus (chapters, sections, code blocks, tables, figures, footnotes, manifest, optional TOC) with high fidelity and deterministic output.

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
- **ALWAYS run local checks before committing** to ensure CI passes. Use `bash scripts/local-check.sh` or run individual tools:
  - `ruff format --check .` - Code formatting (matches CI exactly)
  - `ruff check .` - Linting 
  - `mypy .` - Type checking
  - `pytest -q` - Unit tests
- **Code formatting is mandatory**: Run `ruff format .` to auto-fix formatting issues before committing. CI will fail if code is not properly formatted.
- Install dev dependencies with `pip install -e .[dev]` to get all required tools.
- Pre-commit hooks are configured but local checks provide faster feedback.

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
