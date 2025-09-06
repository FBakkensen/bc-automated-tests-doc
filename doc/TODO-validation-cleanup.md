# Documentation Lint Cleanup Plan

This plan tracks follow-ups to remove broad markdownlint rule disables and make
the docs pass with minimal exceptions.

## Scope

- Files: `doc/design.md`, `doc/prd.md`, `doc/manifest-schema.md`,
  `doc/validation-design.md`.

## Tasks

- Wrap long lines to satisfy MD013 (<= 80 chars).
- Ensure blank lines around headings/lists/tables (MD022, MD032, MD058).
- Convert indented code blocks to fenced blocks (MD046).
- Resolve duplicate headings by renaming or consolidating (MD024).
- Replace inline HTML with Markdown equivalents (MD033).
- Remove spaces inside code spans (MD038).
- Mermaid: quote labels with parentheses/special chars; revalidate with `mmdc`.
- Re-enable rules incrementally; keep disables only where justified.

## Validation

- Run: `bash scripts/validate-md.sh` and expect "Total errors: 0".

## Notes

- Current script uses Pandoc with `-f gfm` to parse GFM reliably.
