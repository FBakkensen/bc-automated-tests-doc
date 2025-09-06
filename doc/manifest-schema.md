# Manifest Schema Specification

<!-- markdownlint-disable  -->

This document defines the canonical manifest schema for the pdf2md tool,
extracted and normative from the PRD. It includes the top-level shape, field
invariants, canonical serialization for hash, determinism rules, backward
compatibility strategy, error handling, minimal example, and planned JSON
Schema.

## Objective

Provide a stable contract for downstream tooling (site generators, regression
tests) and enable structural change detection.

### Top-Level Shape

```jsonc
{
   "schema_version": "1.0.0",         // semantic version of manifest schema
   "document": {                       // global document metadata
      "title": "...",                 // derived from first top-level heading or PDF metadata
      "page_span": [1, 312],            // inclusive first/last page numbers
      "sections_count": 42,
      "figures_count": 18,
      "footnotes_count": 27
   },
   "sections": [                       // pre-order traversal list
      {
         "id": "sec_0001",             // stable id (prefix + zero-padded sequence)
         "slug": "01-chapter-introduction", // includes numeric ordering prefix
         "parent_id": null,              // null for root-level sections
         "level": 1,                     // logical hierarchy level (Part=1 or Chapter=1 depending on top classification policy)
         "order_index": 1,               // 1-based sequence across all sections pre-order
         "title": "Introduction",
         "file": "book/02_chapter_01_introduction.md", // relative path
         "page_span": [5, 17]
      }
      // ... further sections
   ],
   "figures": [                        // optional; empty array if none
      {
         "id": "fig_001",
         "section_id": "sec_0005",      // nearest ancestor section id
         "page": 23,
         "image_path": "assets/images/fig_001_intro.png",
         "caption_raw": "Figure 1: Pipeline overview",
         "caption": "Pipeline overview",
         "caption_source": "below",
         "caption_confidence": 0.982,
         "alt": "Pipeline overview",
         "slug": "fig-001-pipeline-overview" // used for internal references
      }
   ],
   "footnotes": [                      // optional; collected globally or per file
      { "id": "fn_001", "ref_text": "...", "section_id": "sec_0003" }
   ],
   "assets": [                         // non-figure assets (future: tables rendered as images, etc.)
      { "path": "assets/images/fig_002_pipeline.png", "type": "image" }
   ],
   "cross_references": [               // normalized cross-ref mapping (optional initial population)
      { "source_section_id": "sec_0008", "target_slug": "03-chapter-02-architecture", "text": "See Chapter 2" }
   ],
   "structural_hash": "sha256:...",    // hash over canonical serialization rules below
   "generated_with": {
      "tool": "pdf2md",
      "version": "0.1.0"
   }
}
```

### Field Invariants

- `schema_version`: Semantic version. Increment patch for additive non-breaking

  fields, minor for backward-compatible structural extension, major for breaking
  changes.

- `sections` ordering: Strict pre-order traversal; parents always precede

  descendants; `order_index` equals position in array (1-based) — duplicate
  disallowed.

- `id` formats: `sec_` + zero-padded width (config-independent width = 4),

  `fig_` + 3 digits, `fn_` + 3 digits.

- `slug` uniqueness: Global uniqueness across sections and figures (figure slugs

  may share numeric prefix domain separate from sections to avoid collision, but
  still must not duplicate any section slug).

- `page_span[0] <= page_span[1]` and inclusive.
- `structural_hash` must change if any of: section ordering, titles, slugs, page

  spans, figure ids/captions/paths; it must NOT change on: tool version,
  generated_with.tool, or future added optional arrays (backward compatible
  additions excluded from hash input).

### Canonical Serialization for Hash

1. Construct a Python dict with only keys: `sections`, `figures`, `footnotes` (optional),
   each mapped to arrays of minimal projection objects:

- Section projection: `{id, slug, parent_id, level, order_index, title, page_span}`
- Figure projection: `{id, section_id, page, image_path, caption, caption_source, caption_confidence, slug}`
- Cross Reference projection (not part of structural hash): `{source_section_id, target_slug, text, type}`
- Footnote projection: `{id, section_id, ref_text}`

1. Sort arrays by `order_index` (sections) or numeric suffix of id (figures/footnotes) even if already in order (idempotent).

1. Serialize to JSON with: UTF-8, separators `(, :)` (no whitespace), keys

   sorted lexicographically, ensure deterministic float formatting (not
   currently needed but policy documented).

1. Compute SHA-256 over the resulting bytes; prefix with `sha256:`.

### Determinism Rules

- Manifest writing uses the exact field order shown (though JSON clients should

  not rely on ordering; we guarantee it for diff readability).

- All arrays present even if empty (except optional `figures`, `footnotes`,

  `cross_references` which may be omitted if empty ONLY if a config flag
  `omit_empty_manifest_arrays` is added later — not in initial version).

- No timestamps included to avoid nondeterminism. `generated_with.version` is

  allowed and excluded from hash.

### Backward Compatibility Strategy

- Additive fields must be documented in a new subsection and appended without altering existing semantics.

- Removal or renaming triggers major version bump and migration note.
- Structural hash excludes future additive fields by design.

### Error Handling

- If duplicate slugs detected, abort with exit code 4 (parse fatal) before

  writing manifest.

- If hash computation fails (unexpected serialization error), raise and abort

  (no partial manifest written).

### Example Minimal Manifest (No Figures / Footnotes)

```json
{
   "schema_version": "1.0.0",
   "document": {"title": "Sample Doc", "page_span": [1,10], "sections_count": 2, "figures_count": 0, "footnotes_count": 0},
   "sections": [
      {"id": "sec_0001", "slug": "01-intro", "parent_id": null, "level": 1, "order_index": 1, "title": "Intro", "page_span": [1,2]},
      {"id": "sec_0002", "slug": "02-overview", "parent_id": null, "level": 1, "order_index": 2, "title": "Overview", "page_span": [3,10]}
   ],
   "figures": [],
   "footnotes": [],
   "assets": [],
   "cross_references": [],
   "structural_hash": "sha256:4d2c..."
}
```

This schema definition is normative; implementation must reject unknown top-
level keys unless a future `extensions` object is defined.

### Manifest Schema (Planned)

The formal machine-readable JSON Schema is deferred to implementation phase to
keep current scope PRD-only. All normative constraints remain described in prose
(Sections 9.2.1–9.2.7). When introduced, the schema must not retroactively
tighten rules without a `schema_version` minor/major bump.
