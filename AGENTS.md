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

## Guiding Principles: The Zen of Python (PEP 20)

The following aphorisms guide code and documentation choices throughout this repo:

- Beautiful is better than ugly.
- Explicit is better than implicit.
- Simple is better than complex.
- Complex is better than complicated.
- Flat is better than nested.
- Sparse is better than dense.
- Readability counts.
- Special cases aren't special enough to break the rules.
- Although practicality beats purity.
- Errors should never pass silently.
- Unless explicitly silenced.
- In the face of ambiguity, refuse the temptation to guess.
- There should be one-- and preferably only one --obvious way to do it.
- Although that way may not be obvious at first unless you're Dutch.
- Now is better than never.
- Although never is often better than *right* now.
- If the implementation is hard to explain, it's a bad idea.
- If the implementation is easy to explain, it may be a good idea.
- Namespaces are one honking great idea -- let's do more of those!

Source: PEP 20 — The Zen of Python (public domain).

## Critical Patterns/Gotchas
- Determinism: Use utils.deterministic_slug(title, prefix_index=...) with slug_prefix_width for zero-padded ordering; avoid set/dict iteration order.
- Hyphenation: Apply repair_hyphenation only after line merging, before paragraph assembly.
- Heading detection: Start with is_heading_candidate (regex/uppercase heuristics), then font clustering in headings.py.
- I/O: Keep functions pure; restrict writes/image extraction to exporter.py.
- Config: Pass ToolConfig explicitly (no globals); load from YAML/JSON via ToolConfig.from_file.
- Models: Dataclasses for internal; Pydantic for validation (e.g., manifest schema).
- Network policy: Offline by default. Allow network calls only to explicitly
   configured AI provider endpoints when `ai.enabled=true` (e.g., Azure
   OpenAI). All other network activity remains disallowed. The tool is not
   restricted to offline-only operation; it works fully offline and optionally
   online with AI assistance when enabled.
- Implementation phasing: ingest.py → headings.py → structure.py → codeblocks.py/tables.py → figures.py → build_tree.py → render.py → exporter.py → postprocess.py.
- Testing: Prefer TDD‑generated, synthetic PDFs created on‑the‑fly inside tests; optionally use tiny committed fixtures in `tests/fixtures/pdfs` only when necessary. Never add large PDFs. Always check determinism via structural tree hash.

## TDD Policy for Test PDFs

- Create test PDFs as part of the TDD loop (Red→Green→Refactor). Tests generate small, deterministic PDFs at runtime rather than relying on external assets.
- Determinism requirements for generated PDFs:
  - Fixed page size, margins, and draw order
  - Embedded fonts bundled in repo (e.g., DejaVu Sans/Mono)
  - Constantized PDF metadata (CreationDate/Producer)
  - No randomness or timestamps
- Assertion strategy:
  - Early TDD: property‑based assertions (e.g., headings promoted, hyphen repair, list nesting)
  - Stabilized behavior: add golden snapshots (manifest, structural_hash, selected Markdown)
  - Allow intentional updates via `UPDATE_GOLDENS=1` in the environment
- CI guidance:
  - Generate PDFs during tests; run with `--ai=false`
  - Keep any committed fixtures tiny (≤ ~50 KB) and only when generation is impractical
- TDD: Add unit tests for every new heuristic/transformation; ensure no syntax/import errors pre-PR.
- Performance: Stream pages with generators; defer image rasterization post-text extraction.
- Errors: Raise targeted exceptions (e.g., for PDF readability); CLI exits map to codes (1:general, 2:config, 3:I/O, 4:parse).
- CLI stub: Writes partial manifest.json without full processing; --resume planned but unused.
- Lazy imports: __init__.py uses __getattr__ to defer ToolConfig (avoids cycles in tests).
- Global chapter numbering (no per-part reset, log warnings).

## Documentation Validation Rule (Post-Change, Elevated)

All agents must validate documentation in the `doc/` directory (e.g., `doc/design.md`, `doc/prd.md`) immediately AFTER making changes that touch those files. Validation is not required prior to edits, and it is not required when merely referencing docs without modifying them. This rule applies to all modes (code, architect, etc.) to enforce documentation integrity.

### When to Run
- Run validation only when your changes modify one or more files under `doc/`.
- Run it as a post-change step before concluding the task/PR.

### How to Run (Elevated)
- Always execute `scripts/validate-md.sh` with elevated permissions so Mermaid rendering (headless Chromium) and other tooling can run reliably in sandboxes/CI.
- Example (Codex CLI): invoke the shell with `with_escalated_permissions=true` and a brief justification. Equivalent local shells may use `sudo` or environment-specific elevation.

Command:
`bash scripts/validate-md.sh`

### Tool Checks and Failures
The script ensures that required tools are installed and functional:
- markdownlint-cli
- @mermaid-js/mermaid-cli (mmdc)
- pandoc

If any tool is missing, the script fails with a non-zero exit code and provides clear installation instructions, such as:
- For Windows: `choco install pandoc; npm install -g @mermaid-js/mermaid-cli markdownlint-cli`
- For Linux: Use appropriate package managers (e.g., `apt install pandoc`). For npm, it is recommended to configure a local prefix to avoid using `sudo`: `npm config set prefix '~/.npm-global'` then `npm install -g @mermaid-js/mermaid-cli markdownlint-cli`.

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

## Zero‑Tolerance Policy (Warnings & Lint Errors)

- Markdown: All documentation under `doc/` must pass validation with zero warnings or errors. Fix issues rather than suppressing rules (e.g., avoid blanket `markdownlint` disables; use local reflow or rule‑specific exceptions only when justified and documented).
- Python: Source and tests must be clean under the configured tools with zero warnings/errors:
  - `ruff format` – no diffs in CI
  - `ruff check` – zero findings (E, F, B, I ruleset)
  - `mypy` – no type errors (project baseline; strictness may increase over time)
- CI is configured to fail on any violation. Pre‑commit hooks should be used locally to catch issues early.

## Pre-Commit Hooks (Standard Framework)

- This repo uses the pre-commit framework to run checks automatically on commit.
- Setup (one-time per machine or sandbox):
  - `pip install pre-commit` (or `pip install .[dev]`)
  - `pre-commit install`
  - Optional: `pre-commit run --all-files` for a full first pass
- Hooks included:
  - Commit stage (fast, offline):
    - Markdown lint (lightweight): runs `scripts/validate-md.sh` in lint-only mode with
      `LINT_ONLY=true LINT_FALLBACK_OK=true SKIP_PANDOC=true VALIDATE_MERMAID=skip`
      so it never requires Node/Pandoc in the sandbox; still enforces trailing whitespace
      and long-line checks.
    - Ruff format (check-only) and Ruff lint
    - Mypy type check
    - Unit tests via `pytest -q` (scaffold-only tests until development starts)
  - Pre-push stage (deeper docs validation):
    - Full `scripts/validate-md.sh` with
      `VALIDATE_MERMAID=warn_on_sandbox` to avoid false failures when a headless browser
      is not available in constrained environments; CI runs with full toolchain (Mermaid,
      Pandoc, markdownlint) and enforces strict validation.
- Policy:
  - Commits are blocked until hooks pass (zero warnings/errors). Fix issues or re-run after autofixes.
  - Documentation validation runs as a post-change requirement. In this sandbox, commit-time
    uses lightweight lint; pre-push and CI enforce full validation. Use elevated permissions
    where necessary for headless rendering.

### Sandbox Notes (Agent Environment)

- The agent runs with a local virtualenv `.venv` and a writable pre-commit cache
  at `.pre-commit-cache` (`PRE_COMMIT_HOME`), so hooks execute without writing to
  `$HOME`.
- Hooks are configured as local (system-language) to avoid fetching remote hook repositories;
  they use already-installed tools (Ruff, Mypy, Pytest) and the in-repo validator script.
