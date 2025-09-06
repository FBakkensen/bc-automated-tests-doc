# PRD: Technical PDF to Structured Markdown Conversion Tool

## 1. Overview

A Python-based command-line tool that ingests a technical PDF book (e.g.,
"AUTOMATED TESTING IN MICROSOFT DYNAMICS 365 BUSINESS CENTRAL") and produces a
clean, semantically structured multi-file Markdown corpus suitable for static
site generators (e.g., MkDocs, Docusaurus) or GitHub browsing. It removes non-
content noise (advertisements, repeated headers/footers, page numbers,
watermarks), preserves logical structure (parts, chapters, sections, code
listings, tables, callouts), and extracts embedded images (diagrams, figures)
while keeping references consistent.

<!-- markdownlint-disable MD013 MD012 MD032 MD022 MD058 MD024 -->

Primary objective: High-fidelity, human-editable Markdown with minimal post-
processing.

Network policy: Offline by default. When `ai.enabled=true`, the tool may make
calls only to explicitly configured AI provider endpoints (e.g., Azure OpenAI);
all other network calls remain disallowed. The tool is not restricted to
offline-only operation; it functions fully offline and optionally online with
AI assistance when enabled.

## 2. Goals & Success Criteria

- Accurate reconstruction of document hierarchy (Part > Chapter > Section >

  Subsection) to depth level 4.

- Preserve and format: headings, paragraphs, bullet/numbered lists, tables,

  images, figure captions, inline code, block code, callouts (Note/Tip/Warning),
  footnotes, and cross-references.

- Remove boilerplate: running headers, footers, page numbers, TOC pages

  (optional), copyright pages, blank pages.

- Extract images with deterministic filenames and relative links.
- Idempotent: running tool twice yields same output with no spurious diffs.
- ≥ 98% of code blocks retained without line breaks corruption (manual spot QA

  metric).

- CLI completes on a ~300-page technical PDF in < 90 seconds on a modern laptop

  (baseline optimization target, not hard SLA).

## 3. Out of Scope (Initial Version)

- OCR for scanned PDFs (assumes text-based PDF). (Future: Tesseract fallback.)
- Math formula LaTeX reconstruction (pass through as plain text or inline code

  style if detected).

- Semantic deduplication of near-identical figures.
- Automatic glossary extraction or index synthesis.


## 4. Users & Use Cases

- Tech authors migrating legacy PDF content to Markdown.
- Engineering teams building internal doc portals.
- Open-source maintainers publishing book-format content to docs sites.


## 5. Input / Output Specification

### Input

- Single PDF file path. (Future: folder batch mode.)
- Optional config file (`yaml` or `json`) to override heuristics.


### Output

Canonical directory structure (example for a book with Parts & Chapters):

```text
output/
   book/
      00_frontmatter_preface.md
      01_part_i_overview.md
      02_chapter_01_introduction.md
      03_chapter_02_architecture.md
      04_chapter_03_data-model.md
      05_part_ii_advanced-topics.md
      06_chapter_04_performance.md
      07_appendix_a_reference.md
   assets/images/
      fig_001_introduction-overview.png
      fig_002_architecture-pipeline.png
      fig_003_performance-profile.svg
   manifest.json
   toc.yml   (optional)
```

#### File Naming Policy

- Prefix: zero-padded sequential index (width = `slug_prefix_width`, default 2)

  reflecting pre-order traversal of top-level logical units (frontmatter faux-
  section → parts → chapters → appendices).

- Chapter filename schema: `<index>_chapter_<chapterNumber>_<slugified-title>.md`.

- Part filename schema: `<index>_part_<roman-or-decimal>_<slugified-title>.md`

  (Roman numerals from source text preserved after normalization if detected
  `Part I|II|III`; else decimal sequence).

- Appendix filename schema: `<index>_appendix_<letter>_<slugified-title>.md`.
- Front matter (if present but not explicitly titled) synthesized as

  `00_frontmatter_preface.md` using extracted metadata title or first heading as
  basis.

- Slugification identical to runtime slug generator (lowercase, hyphenation,

  punctuation stripped) ensuring cross-link anchors match filename suffix
  segments.

#### Chapter Numbering with Parts

- If Parts detected (headings matching `Part\s+([IVXLC]+|\d+)`), chapter ordinal

  numbering (e.g., `Chapter 1`, `Chapter 2`) increments globally across all
  parts (no reset). This avoids ambiguous references like two distinct “Chapter
  1”.

- If explicit per-part numbering restarts are present in source (rare), tool

  logs warning `chapter_number_reset_detected` and still maintains global
  incremental assignment. Original heading text retained verbatim in Markdown.

#### Image / Figure Asset Naming

- Figure IDs assigned by appearance order post noise filtering & before caption

  binding.

- Filename pattern: `fig_<zero-padded-3>_<primary-caption-slug>.ext` where

  primary-caption-slug is first 4–6 meaningful words of stripped caption (stop-
  words removed) joined with hyphens. If caption absent →
  `fig_<id>_uncaptioned.ext`.

- Collisions (same slug for different figures): append `-n` where n increments

  starting at 2; deterministic due to appearance order.

- Vector images preserved as `.svg` if extractable; raster fallback uses

  configured `image_format`.

#### TOC (Optional)

- `toc.yml` generated only when `--toc` enabled; ordering mirrors manifest

  sections. Each entry: `title`, `file` (relative path). Appendices grouped
  after final chapter.

#### Cross-References & Anchors

- Internal Markdown anchor for each heading is its slug (already prefixed for

  ordering). References link using `#<slug>`; file-local anchors do not
  duplicate file path if link target is within same file.

- Figure references use figure slug only; no file path prefix because figures

  share global slug namespace and links rely on nearest section file context
  when rendered.

#### Determinism Guarantees

- Adding a new appendix or part only affects indices of subsequently generated

  files; earlier indices and structural hash change accordingly (expected,
  logged). No retroactive renumbering outside insertion point.

- Regenerating with identical inputs yields identical filenames bit-for-bit.


#### Failure Handling

- On attempt to write a file whose path already exists with differing content

  and `--resume` set, file is skipped and event logged; manifest still rewritten
  to reflect prior run.

- On slug collision that cannot be resolved after applying suffix `-n` up to

  `-9`, pipeline aborts with exit code 4, logging `unresolvable_slug_collision`
  (extremely unlikely under prefix scheme).

### Markdown Conventions

- Tables emitted in GitHub-flavored Markdown.
- Callouts mapped to blockquotes with leading label: `> **Note:** ...`.


## 6. Functional Requirements

1. Parse PDF layout into ordered text spans with positional metadata (x, y, font

   size, style, page number).

1. Heading Detection:
- Use font size clustering + bold/uppercase heuristics.
- Numeration patterns: `Part I`, `Chapter 2`, `1.2.3`, `Appendix A`.
- Build hierarchical tree preserving order.
1. Paragraph Assembly:
- Merge line fragments by proximity and hyphenation resolution.
- Preserve intentional blank lines (e.g., before code or lists).
1. List Detection:
- Recognize bullets (`•`, `-`, `*`) and ordered patterns (`1.`, `a)`, `(i)`),

     indent-based nesting (x-offset deltas).

1. Code Block Extraction:
- Detect multi-line monospaced or indented regions; maintain whitespace

     faithfully.

1. Inline Code:
- Short monospaced spans embedded in regular paragraphs -> wrap in backticks.
1. Image Extraction:
- Export vector and raster objects where possible (fallback: page raster cropping around figure region if compound grouping is detected).

- Associate nearest preceding or following caption (pattern: `Figure \d+:` or

italic smaller font) and store in alt text.

1. Table Reconstruction:
- Detect ruled lines or column-aligned text boxes (grid inference via

x-coordinate clustering).

- Output Markdown table; fallback to preformatted fenced block if ambiguous.
1. Footnotes:
- Detect superscript markers and trailing page footnote region based on

y-position at page bottom. 10. Cross-Reference Normalization:

- Convert `See Chapter 3` to internal relative link if target heading slug

exists. 11. Slug Generation:

- Deterministic: lowercase, hyphenate, remove punctuation, prefix with

sequence for ordering. 12. Manifest Generation:

- Produce `manifest.json` adhering to canonical schema (see [doc/manifest-

schema.md](manifest-schema.md)) with deterministic ordering and structural
     hash. 13. TOC Export:

- Optional YAML structure for MkDocs or JSON for dynamic sites. 14. Config

Overrides:

- External file controlling heuristic thresholds, feature toggles, and

safety limits. 15. Logging & Verbosity Levels:

- Structured logging with adjustable verbosity (`--verbose`, `--quiet`). 16.

Dry Run Mode:

- Output detected structure summary without writing Markdown/assets. 17.

Resume Mode:

- Skip already converted assets unless `--force`.


## 7. Non-Functional Requirements

- Deterministic output given identical inputs + config.
- Modular code (separate concerns: parsing, semantic modeling, rendering,

  exporters).

- Logging uses standard library `logging` with structured contexts.
- Python version: 3.11+.


## 8. Technology Choices

- PDF Parsing: `pdfminer.six` / `pdfplumber` wrapper.
- Image Extraction: `pypdf` first; fallback `pdf2image` (Poppler) only when

  needed.

- Table Detection: `pdfplumber` tables + custom alignment fallback.
- CLI: `typer` (ergonomics) with clean subcommands.
- Config Serialization: `pydantic` models + YAML via `pyyaml`.
- Slugification: `python-slugify` or custom deterministic implementation.
- Language Detection (optional): basic heuristics; optional `pygments.lexers`

  when `--language-detect` enabled.

## 9. High-Level Architecture

Layers:

1. Ingestion Layer: Loads PDF pages, extracts raw layout objects.


Core Data Classes (conceptual):

```text
Span {text, bbox, font_name, font_size, style_flags, page}
Node {type, children, meta}
Figure {image_path, caption_raw, caption, caption_source, caption_confidence, alt, page, bbox}
CodeBlock {language, lines, page_span}
Table {rows, page_span, confidence}
ManifestEntry {slug, title, level, file, parent, pages}
```

### 9.1 Canonical Data Model & Transformation Contracts

Purpose: remove ambiguity around intermediate representations, ensure
deterministic, testable boundaries.

#### 9.1.1 Entities

- Span (immutable): Minimal textual unit directly traceable to original PDF

  extraction. Fields: `text: str`, `bbox: (x0,y0,x1,y1)`, `font_name`,
  `font_size: float`, `style_flags: set[str]` (e.g., {bold, italic, mono,
  smallcaps}), `page: int`, `line_id` (optional derived), `order_index: int`
  (monotonic global sequence). No mutation after creation.

- Block (assembled, mutable during construction, then frozen): Logical

  contiguous content group derived from one or more Spans. `block_type` enum:
  Paragraph, List, ListItem, CodeBlock, Table, FigurePlaceholder,
  FootnotePlaceholder, HeadingCandidate, EmptyLine, RawNoise (for optional
  filtering). Common fields: `spans: list[Span]`, `bbox`, `page_span:
  (first_page,last_page)`, `meta: dict`. Specialized metadata keys:
  `list_level`, `code_language`, `table_confidence`, `figure_bbox`.

- SectionNode (hierarchical structural unit): Represents Part / Chapter /

  Section / Subsection. Fields: `title: str`, `level: int` (1-based within
  logical doc hierarchy, not Markdown depth), `slug: str|None` (assigned in
  post-processing), `blocks: list[Block]`, `children: list[SectionNode]`,
  `pages: (first,last)`.

- DocumentTree: Root container with `sections: list[SectionNode]`, plus

  registries (slug index, figure map, footnote map) built deterministically.

Rationale: Separate structural hierarchy (SectionNode) from linear content
grouping (Block) to keep heuristics orthogonal (e.g., list detection never
mutates SectionNode ordering; heading clustering only promotes Blocks to
SectionNodes).

#### 9.1.2 Stage Contracts

| Stage | Input | Output | Allowed Mutations | Disallowed Actions |
|-------|-------|--------|-------------------|--------------------|
| Ingestion | PDF bytes/pages | Raw layout artifacts | None (stream only) | Reordering, semantic inference |
| Normalization | Raw artifacts | Ordered Spans | Coordinate rounding, font/style flag derivation | Dropping non-empty text, merging across pages |
| Span Assembly (Line & Hyphen Repair) | Spans | Updated Spans (new line_id) | Hyphen removal (Span text concatenation producing replacement Spans), line id assignment | Changing original order_index, altering unrelated Span text |
| Block Assembly | Spans | Blocks | Grouping spans, list nesting, code boundary detection | Reordering spans across blocks, content rewriting (except hyphen repair already done) |
| Heading Semantics | Blocks | SectionNodes + Blocks | Promote HeadingCandidate blocks into SectionNodes; attach following content until next equal/higher heading | Changing Paragraph text, removing Blocks (except explicit noise filter rules) |
| Post-Processing | SectionNodes tree | SectionNodes tree (augmented) | Slug assignment, cross-link resolution, footnote association, figure caption binding, noise block pruning if flagged | Structural reordering (other than deterministic slug prefixing), content mutation |
| Rendering | Final tree | Markdown strings + assets | Formatting, escaping, deterministic file naming | Injecting runtime timestamps, nondeterministic UUIDs |

#### 9.1.3 Determinism & Purity Rules

1. Spans are assigned a global `order_index` strictly increasing by page then

   reading order; this index is never modified.

1. All sorting uses explicit keys (e.g., `order_index`, `slug`).
1. Hashable structural signature (future) will serialize: list of SectionNodes

   (level, slug) + per-block hash of concatenated Span texts.

1. Tie-breaking in heuristics must use lexicographic text or bbox numeric

   ordering.

1. Slug generation: `deterministic_slug(title, prefix_index,

   width=slug_prefix_width)`; prefix_index derived from pre-order traversal of
   SectionNodes.

1. No stage may delete non-empty user-visible text unless an explicit noise rule

   matches and is logged.

1. Post-processing additions (footnote definitions, link rewrites, captions)

   must be reproducible from inputs.

- Immutable: Span objects (including fields after creation) and any frozen Block

  once added to a SectionNode.

- Mutable (during their construction phase only): Blocks prior to freeze,

  SectionNode lists (`children`, `blocks`) during tree assembly.

- Freezing occurs immediately after a SectionNode's children determination

  completes for a given heading level.

#### 9.1.5 Error & Logging Hooks

- Each stage emits structured log events: `{stage, action, counts, pages}`.
- If a Block type confidence < threshold (e.g., table_confidence <

  config.table_confidence_min) it is downgraded to a CodeBlock-like preformatted
  block with a `meta.fallback_reason`.

This subsection formally supersedes earlier informal uses of "Token"; the
canonical term is "Span".

## 10. Detailed Algorithms & Heuristics

### Heading Clustering

- Collect all font sizes; k-means (k<=6) or simple frequency sorting.
- Assign tiers by descending size; merge tiers whose difference < epsilon

  (configurable, default 1pt).

- Classify candidates by: large font + (bold OR all-caps OR leading

  numeral/keyword `Part|Chapter|Appendix`).

### Heading Number Extraction & Normalization

Goal: Derive stable numeric identifiers (chapter_number, section_path) from
heading texts to support cross-reference resolution and ordering sanity checks
without mutating original displayed titles.

#### Detection Order

1. Explicit Part: `^Part\s+([IVXLC]+|\d+)\b` → part_order increment (roman

   preserved separately).

1. Explicit Chapter: `^Chapter\s+(\d+)\b` → chapter_number candidate.
1. Appendix: `^Appendix\s+([A-Z])\b` → appendix_letter.
1. Dotted Section Path: leading pattern `^(\d+(?:\.\d+)*)\b` (e.g., 3.2.1)

   capturing hierarchical numeric path.

1. Fallback: No explicit numbering → assigned implicit sequence within parent

   (not exposed for cross-ref path strings to avoid fabricating numbers).

#### Normalization Rules

- Chapter numbers never reset after Parts; encountering a Chapter 1 after a

  prior Chapter N>1 logs `chapter_number_reset_detected` and assigns next global
  number N+1 internally while preserving raw text.

- Dotted paths validated: each segment must be positive integer; if a segment

  jumps by >1 (e.g., 3.2 → 3.5 skipping 3.3/3.4) log `section_gap_detected`;
  gaps do not cause renumbering.

- Appendices ordered after final chapter; letters must be strictly increasing

  A,B,C...; out-of-order letter logs `appendix_out_of_order` but retains
  original.

- Mixed style (e.g., some sections dotted, others not) results in only dotted

  headings populating numeric path; non-dotted siblings get no path (excluded
  from section path based cross-ref resolution) but still have slugs.

#### Data Attachment

Per SectionNode meta keys:

```text
meta.chapter_number: int | null
meta.section_path: list[int] | null   # e.g., [3,2,1]
meta.appendix_letter: str | null
meta.part_order: int | null
```

#### Determinism

- Extraction runs once after Heading Clustering; no mutation of titles.
- Roman numerals converted to decimal only for internal ordering; original

  retained in filenames and display.

- Implicit sequence assignment uses SectionNode pre-order index within same

  parent scope.

#### Error / Edge Handling

- Duplicate explicit chapter number (two separate headings both "Chapter 5")

  logs `duplicate_chapter_number` and second is treated as if number absent
  (implicit sequence path) to prevent cross-ref ambiguity.

- Section path containing segment > 99 logs `section_segment_large` (still

  accepted).

- Overly deep path (depth > 6) truncated for path storage but full text

  retained.

#### Configuration Keys

- `numbering_validate_gaps` (bool, default true): emit warnings on gaps.
- `numbering_allow_chapter_resets` (bool, default false): if true, do NOT remap

  restarted Chapter 1; use distinct internal counter bracketed by part (less
  deterministic, not recommended).

- `numbering_max_depth` (int, default 6): truncate deeper paths.


#### Testing

- Gap detection: synthetic sequence 1,2,4 logs one gap.
- Chapter reset case: Chapter 1,2,3,1 → reset logged and remapped to 4 (default

  settings).

- Appendix order mis-sequence: Appendix A, Appendix C → out-of-order log; cross-

  ref to Appendix B unresolved.

- Mixed numbering styles: ensure undotted headings do not appear resolvable by

  numeric path patterns.

Non-goals: Automatic gap filling or renumber rewriting; deriving numbers from
small-caps stylistic cues alone.

### Appendix Detection Heuristics

Goal: Recognize appendices (and annexes) that appear after the main chapter
sequence, assign stable ordering, and integrate with numbering & cross-reference
logic without mutating visible titles.

#### Pattern Evaluation Order

Evaluation runs immediately AFTER Heading Number Extraction. Ordered built-in
default patterns (case-insensitive):

1. `^Appendix\s+([A-Z])\b`
1. `^Annex\s+([A-Z0-9])\b`


User-supplied `appendix_patterns` (if non-empty) are PREPENDED (higher
precedence). Future (not initial) toggle `appendix_patterns_replace` could
replace defaults entirely.

#### Identifier Normalization

- Alphabetic: single letter A–Z captured as canonical key. Behavior for case

  controlled by `appendix_letter_case` (upper|lower|preserve; default upper).

- Alphanumeric annex ids (e.g., `Annex 1`) are logged

  (`appendix_numeric_identifier_ignored`) and not treated as formal appendices
  (remain regular sections) in initial version.

#### Constraints & Ordering

1. An appendix candidate before the first detected Chapter is ignored

   (`appendix_early_ignored`).

1. Strictly increasing non-repeating letter sequence A,B,C,...; duplicate letter

   logs `appendix_duplicate_letter` and second occurrence downgraded to normal
   section (unless future flag permits duplicates).

1. Out-of-order letter (A, C, B) logs `appendix_out_of_order`; later B still

   recognized if not previously used; no reordering.

1. Page Break Requirement: When `appendix_requires_page_break=true` (default)

   the heading must be the first textual block (post-noise filtering) on its
   page else ignored (`appendix_missing_page_break`).

1. Hierarchical Level: Controlled by `appendix_level`:
- `chapter` (default) – Appendices share level with chapters.
- `part` – Treat appendices as top-level peers to Parts (affects `level`

     field and slug prefix ordering but not structural hash differentiation
     rules).

#### Interaction with Numbering & Slugs

- Appendices never increment chapter numbering; filenames already defined

  `<index>_appendix_<letter>_<slug>.md` remain unchanged.

- Slug uniqueness enforced across all sections; appendix detection adds

  `meta.appendix_letter` used for cross-reference resolution (`Appendix A`).

- Structural hash includes appendix sections identically to others (no

  exclusion).

#### Logging Events

`appendix_detected`, `appendix_out_of_order`, `appendix_duplicate_letter`,
`appendix_missing_page_break`, `appendix_early_ignored`,
`appendix_numeric_identifier_ignored`.

#### Determinism

- Pre-order traversal evaluation; deterministic pattern ordering.
- Conflicts resolved by pattern list order (user > defaults).


#### Configuration Keys

- `appendix_patterns: []` (empty -> defaults only; else prepended)
- `appendix_letter_case: upper`
- `appendix_requires_page_break: true`
- `appendix_level: chapter`


#### Testing

- Custom pattern precedence overshadowing default.
- Early appendix ignored.
- Page-break requirement enforced.
- Duplicate letter demotion.
- Out-of-order detection.
- Cross-reference success for valid letters; failure for numeric annex ids.


Non-goals (initial): Multi-letter (AA) appendices, roman numeral appendices,
automatic insertion of missing letters, cross-reference to numeric Annex
identifiers.

### Hyphenation Repair

- Regex `([A-Za-z]{3,})-$` at line end + next line starts lowercase -> merge

  without hyphen.

- Maintain exception list for domain-specific tokens.


### List Nesting

- Track current indent stack; new bullet indent within tolerance -> same level;

  deeper -> push; shallower -> pop until fit.

### Code Block Detection

- Consecutive spans with monospaced font OR uniform leading indent ≥ 4 spaces

  across ≥ 2 lines.

- Stop when blank line or style break.


### Table Extraction Fallback

- Group spans by y-lines (tolerance ±2px) then cluster x-start positions; build

  grid.

- If inconsistent column count across >30% rows -> mark `confidence<0.5` ->

  fallback to preformatted.

### Figure Caption Resolution

Goal: Deterministically bind each extracted Figure image to at most one caption
text block.

#### Inputs

- Figure candidate: bbox + page.
- Caption candidates (same page) if:
1. Regex `figure_caption_pattern` (default `^(Figure|Fig\.)`, case-

      insensitive) at start.

1. OR smaller than median body font AND italic, within distance threshold.
- Distance threshold: `figure_caption_distance` (default 150px) edge-to-edge.


#### Pre-Filtering

Compute vertical gap g and direction (below/above/overlap). Drop if g >
threshold. Limit text considered to first `figure_caption_max_lines` lines for
scoring.

#### Scoring

Components: S_pattern (1 or 0), S_position (below=1, overlap=0.6, above=0.4),
S_distance = 1 - g/threshold (clamped ≥0), S_font (1 if size <= median*ratio or
italic, else 0.4). Weighted sum with weights (pattern 0.35, position 0.25,
distance 0.25, font 0.15) configurable; must sum to 1 (±1e-6) or config error
(exit 2).

#### Tie-Breaking (after rounding score to 4 decimals)

1. Higher S_pattern.
1. Smaller g.
1. Direction priority below > above > overlap.
1. Lexicographically smallest normalized text.


#### Output

Chosen caption fields: `caption_raw`, stripped `caption` (remove leading
Figure/Fig number when `figure_caption_strip_prefix` true), `alt` (first
sentence truncated 80 chars), `caption_source`, `caption_confidence` (score
rounded 3 decimals). None found -> empty caption, confidence 0.0.

#### Edge Cases

Shared caption for stacked figures: assign to closest; if gap diff <5px assign
to both and log duplicate. Page-break split captions: not associated; log only.
Tiny inline icons ignored.

#### Determinism

Use Decimal quantized to 6 places internal; 4 for tie compare; 3 stored.
Candidate ordering sorted by (gap, direction_rank, order_index).

#### Logging

Events: `score`, `tie_break`, `duplicate_caption_assignment` with figure ids and
chosen candidate.

#### Testing

Scoring ordering, tie-break hierarchy, prefix stripping, duplicate caption path,
weight sum validation, determinism across runs.

### Cross-Reference Normalization

Goal: Convert textual references (chapters, sections, figures, appendices) into
stable internal Markdown links when targets exist, without destabilizing
structural hashing. Provide deterministic handling for unresolved references.

#### Scope

- Supports references to: Chapters (e.g., "Chapter 5"), Sections ("Section 3.2"

  / "Sec. 3.2.1"), Figures ("Figure 7" / "Fig. 7"), Appendices ("Appendix A").

- Optional resolving of Figures and Appendices guarded by config toggles.


#### Patterns

Configured via ordered list `xref_patterns` (first match wins). Default set
(case-insensitive unless overridden):

1. `\bSee\s+Chapter\s+(\d+)\b`
1. `\bChapter\s+(\d+)\b`
1. `\bSection\s+((?:\d+\.)*\d+)\b`
1. `\bSec\.\s+((?:\d+\.)*\d+)\b`
1. `\bFigure\s+(\d+)\b`
1. `\bFig\.\s+(\d+)\b`
1. `\bAppendix\s+([A-Z])\b`


Each pattern declares a `type` (chapter|section|figure|appendix) implicitly by
position. Users may extend or reorder; removal of a pattern disables that
reference type.

#### Resolution Pipeline

1. Collect candidate text segments during Post-Processing after slug assignment

   (ensures all section slugs known).

1. For each SectionNode's textual Blocks (Paragraph / ListItem / CodeBlock

   caption lines ignored): scan linearly; apply patterns in order; record non-
   overlapping matches (leftmost-first, longest-first within same start index).

1. Normalize target key:
- Chapter: integer N → find SectionNode with level=1 (or classification

     policy) whose sequential chapter index == N.

- Section: dotted path (e.g., 3.2.1) → navigate by pre-order tracking numeric

     heading enumerations (requires prior heading number extraction; if absent,
     attempt by ordinal sequence within parent). If mismatch, unresolved.

- Figure: integer F → match figure id by its ordinal (fig_00F) on appearance

     order.

- Appendix: letter L → map to Part/Appendix section nodes designated as

     appendices (future; initial pass: unresolved unless heading starts with
     "Appendix L").

1. If resolved: generate Markdown link `[original_text](#target-slug)` where

   `target-slug` is section or figure slug. For figures, use figure slug; for
   chapters/sections use section slug.

1. If unresolved: apply `xref_unresolved_policy`:
- `keep`: leave original text unchanged.
- `annotate` (default): append `[‡]` and log at INFO once per distinct

     unresolved normalized key; no manifest entry.

- `drop`: remove only the match token (leave surrounding text).
1. Limit: If resolved references for a single SectionNode exceed

   `xref_max_per_section`, stop further resolution in that node (log rate-limit
   event) to guard pathological content.

#### Manifest Interaction

- Only resolved references are included in `cross_references` array.
- New manifest field shape (adds `type`): `{ source_section_id, target_slug,

  text, type }`.

- `cross_references` is PURPOSELY EXCLUDED from structural hash (as previously)

  to ensure late additions (e.g., enabling figure resolution) do not destabilize
  core structure; this exclusion is reaffirmed here.

- Unresolved references never appear with null target (eliminates ambiguous

  entries).

#### Determinism

- Pattern evaluation order fixed by configuration list order.
- Non-overlapping selection: sort candidate matches by (start_index,

  -match_length) ensuring longest at same position wins.

- Tie cases (same text & span) cannot occur after non-overlapping filter; if

  they do (config error), first sequential occurrence kept.

- Case-insensitive matching when `xref_case_insensitive=true` applied by

  lowercasing both candidate text and patterns except capture groups preserved
  as-is for link text.

#### Safety / Failure Modes

- If numeric target exceeds known count (e.g., "Chapter 99"), treat as

  unresolved.

- Patterns that yield empty group or malformed number skipped.
- If all patterns disabled (empty list) and `xref_enable=true`, system emits

  warning and produces no links.

#### Logging

Events (one per source section aggregation): `{stage:'xref', action:'resolved',
count}` `{stage:'xref', action:'unresolved', key, policy}` `{stage:'xref',
action:'rate_limited', section_id, limit}` `{stage:'xref',
action:'pattern_disabled', pattern}`

#### Configuration Keys (see Section 12 additions)

- `xref_enable` (bool, default true)
- `xref_patterns` (ordered list of regex strings)
- `xref_case_insensitive` (bool, default true)
- `xref_unresolved_policy` (enum: annotate|keep|drop; default annotate)
- `xref_max_per_section` (int, default 100)
- `xref_resolve_figures` (bool, default true)
- `xref_resolve_appendices` (bool, default false initial)


#### Testing

- Unit: resolution of each reference type to correct slug.
- Unresolved policies: annotate adds marker; keep leaves raw; drop removes

  token.

- Rate limit triggers with synthetic > limit references.
- Determinism: same input/config yields identical link set ordering.
- Manifest integrity: resolved refs included with correct `type`; unresolved

  excluded.

- Pattern override test: custom pattern order changes which ambiguous match is

  chosen (documented reproducibly).

#### Non-Goals (Initial)

- Cross-page context inference for ambiguous numbering (assumes numbering

  consistent).

- Appendix letter remapping beyond explicit heading parsing.
- Hash inclusion of cross references (explicitly excluded for stability).


This section supersedes earlier single-line description of cross-reference
linking.

### Noise Filtering Policy

Goal: Safely remove repetitive non-content artifacts (running headers, footers,
page numbers, watermarks) without risking user content loss while preserving
determinism.

#### 10.X.1 Taxonomy

- Running Header: Identical (case/whitespace-normalized) line appearing on >=

  `noise_min_repetition_ratio` proportion of pages at y-position within top band
  (`noise_header_top_px`).

- Running Footer: Same criteria within bottom band (`noise_footer_bottom_px`).
- Page Number: Standalone numeric (optionally prefixed with 'Page' / 'PAGE')

  centered or within footer band; pattern: `^(page\s+)?\d{1,4}$`.

- Watermark: Low-opacity or rotated text (future; out-of-scope initial) —

  placeholder classification only (not removed initially).

- Copyright Line: High-frequency line containing © or '(c)' plus year pattern.


#### 10.X.2 Processing Order

Executed AFTER Normalization (Spans) and BEFORE Span Assembly (hyphen repair) to
prevent accidental hyphen merging across noise boundaries.

#### 10.X.3 Detection Algorithm

1. Collect candidate textual Spans within header band (y0 <

   `noise_header_top_px`) and footer band (y1 > page_height -
   `noise_footer_bottom_px`).

1. Normalize text: trim, collapse multiple spaces, lowercase.
1. Frequency Map: count occurrences across pages; compute ratio `count /

   total_pages`.

1. Mark as removable if:
- Ratio >= `noise_min_repetition_ratio` AND
- Length < `noise_max_chars` AND
- Not matched by allowlist regexes (`noise_keep_patterns`) AND
- If page number pattern, always removable unless page in

     `noise_protect_numeric_pages`.

1. Watermarks: currently logged only (`action='detect_watermark_candidate'`)

   unless `enable_watermark_removal` becomes true (future feature flag).

1. Removal: Flagged Spans are excluded from downstream processing; log each

   unique removed normalized text once at INFO and each occurrence at DEBUG.

#### 10.X.4 Safety & Overrides

- Allowlist (`noise_keep_patterns`) evaluated last to retain content even if

  frequency threshold met.

- Blocklist (`noise_drop_patterns`) applied after frequency classification to

  permit removing rare but known boilerplate.

- Dry-run outputs JSON summary of proposed removals with up to N sample page

  numbers per unique text.

- Fail-safe: if prospective removals exceed `noise_max_drop_ratio` of total Span

  count, abort with exit code 4 unless `--force`.

#### 10.X.5 Determinism

- Evaluation order fixed: frequency -> blocklist -> allowlist -> classification.
- Stable hash of normalized text (e.g., sha1) included in debug logs for

  diffing.

#### 10.X.6 Non-Goals (Initial)

- Removing rotated/transparent watermarks (log only).
- Language-aware semantic noise detection.


#### 10.X.7 Metrics

- Counters emitted: `noise.removed_count`, `noise.unique_removed`,

  `noise.header_candidates`, `noise.footer_candidates`,
  `noise.retained_due_allowlist`.

#### 10.X.8 Testing

- Unit: synthetic pages with variable header/footer repetition to test threshold

  boundaries.

- Property: page permutation does not change removal set.
- Regression: snapshot of dry-run noise removal proposal for fixture.


### Orphan Heading Demotion

Definition: An orphan heading is a heading-derived SectionNode whose immediate
content (prior to the next heading of level <= its own) contains zero non-empty
non-heading Blocks.

Algorithm (applied after initial heading promotion, single pass top-down):

1. For each SectionNode S (pre-order), inspect its `blocks` until encountering

   (a) another HeadingCandidate promoted to SectionNode of level <= S.level, or
   (b) first non-heading Block.

1. If case (a) occurs before any non-heading Block and

   `config.demote_orphan_headings` is true, demote S:

- Convert S's heading Block back into a Paragraph Block with meta:

     `{demoted_from_heading: True, reason: 'orphan'}`.

- Remove S from its parent's children list; re-run promotion check locally

     for the demoted Block (it will usually remain a paragraph).

- Do not renumber existing slugs already assigned to earlier siblings; slug

     indices skip the demoted node to preserve determinism.

1. Log event: `{stage='heading_semantics', action='demote_orphan_heading',

   title, level, page}`.

1. If case (b) occurs (legitimate content), retain S untouched.
1. Nested deeper heading (level > S.level) without intervening content is

   accepted (interpreted as structural shorthand) and not demoted.

Non-Goals:

- Do not attempt to merge consecutive headings into compound titles (keeps

  pipeline simpler).

- Do not demote if a footnote-only or figure-only block appears (these count as

  content).

Complexity: O(N) over SectionNodes; no global rebuild required.

Config toggle: `demote_orphan_headings` (default true). When false, orphan
sections are retained and annotated with `meta.empty_section=True`.

### 9.2 Manifest Schema & Deterministic Serialization

See [doc/manifest-schema.md](manifest-schema.md) for the canonical manifest
schema and deterministic serialization details.

## 11. CLI Design

Example:

```text
pdf2md convert book.pdf --out output --config config.yml --toc --manifest --force
pdf2md dry-run book.pdf
```

Options:

- `convert <pdf_path>` main command.
- `--out PATH` output root.
- `--config FILE` optional configuration.
- `--toc/--no-toc` generate toc file.
- `--manifest/--no-manifest` generate manifest.
- `--force` overwrite existing.
- `--resume` skip existing.
- `--max-pages N` for debugging.
- `--verbose / -v` repeatable.
- `--language-detect` enable expensive code language inference.


## 12. Configuration Schema (Draft)

```text
font_cluster_epsilon: 1.0
min_heading_font_size: null  # override auto-detected tier
list_indent_tolerance: 6
code_min_lines: 2
code_indent_threshold: 4
figure_caption_distance: 150
exclude_pages: []
heading_normalize: true
slug_prefix_width: 2
linkify_cross_references: true
table_confidence_min: 0.5
image_format: png
image_dpi: 200
footnote_merge: true
language_detection: false
demote_orphan_headings: true
noise_header_top_px: 120
noise_footer_bottom_px: 120
noise_min_repetition_ratio: 0.6
noise_max_chars: 80
noise_max_drop_ratio: 0.05
noise_keep_patterns: []
noise_drop_patterns: []
noise_protect_numeric_pages: []
enable_watermark_removal: false
figure_caption_prefer_below: true
figure_caption_max_lines: 3
figure_caption_pattern: '^(Figure|Fig\.)'
figure_caption_font_smaller_ratio: 0.92
figure_caption_weight_pattern: 0.35
figure_caption_weight_position: 0.25
figure_caption_weight_distance: 0.25
figure_caption_weight_font: 0.15
figure_caption_strip_prefix: true
figure_caption_decimal_precision: 6
xref_enable: true
xref_case_insensitive: true
xref_unresolved_policy: annotate   # annotate|keep|drop
xref_max_per_section: 100
xref_resolve_figures: true
xref_resolve_appendices: false
xref_patterns: []

### 12.1 Configuration Reference Table
| Key | Type | Default | Description | Fatal Validation Condition |
|-----|------|---------|-------------|----------------------------|
| font_cluster_epsilon | float | 1.0 | Max diff to merge font tiers | <=0 |
| min_heading_font_size | float/null | null | Override auto tier floor | <0 |
| list_indent_tolerance | int | 6 | Pixel delta for same list level | <0 |
| code_min_lines | int | 2 | Minimum lines to classify code block | <1 |
| code_indent_threshold | int | 4 | Leading space count for code heuristic | <0 |
| figure_caption_distance | int | 150 | Max px gap figure↔caption | <=0 |
| exclude_pages | list[int] | [] | Pages to skip entirely | any <1 |
| heading_normalize | bool | true | Normalize heading whitespace | n/a |
| slug_prefix_width | int | 2 | Zero-pad width for file prefix | <1 |
| linkify_cross_references | bool | true | (Deprecated) superseded by `xref_enable`; retained for backward compatibility if present true implies `xref_enable` | n/a |
| table_confidence_min | float | 0.5 | Threshold to accept table classification | <0 or >1 |
| image_format | enum | png | Output raster image format | unsupported format |
| image_dpi | int | 200 | DPI for rasterization fallback | <50 |
| footnote_merge | bool | true | Merge multiline footnotes | n/a |
| language_detection | bool | false | Enable expensive language detection | n/a |
| demote_orphan_headings | bool | true | Demote empty headings | n/a |
| noise_header_top_px | int | 120 | Header band height | <0 |
| noise_footer_bottom_px | int | 120 | Footer band height | <0 |
| noise_min_repetition_ratio | float | 0.6 | Frequency threshold for noise | <=0 or >1 |
| noise_max_chars | int | 80 | Max chars for noise candidate | <1 |
| noise_max_drop_ratio | float | 0.05 | Abort if removals exceed ratio | <=0 or >=0.5 |
| noise_keep_patterns | list[str] | [] | Regex allowlist | invalid regex |
| noise_drop_patterns | list[str] | [] | Regex blocklist | invalid regex |
| noise_protect_numeric_pages | list[int] | [] | Pages to retain page numbers | any <1 |
| enable_watermark_removal | bool | false | Future watermark removal toggle | n/a |
| figure_caption_prefer_below | bool | true | Bias below figure in tie | n/a |
| figure_caption_max_lines | int | 3 | Lines of caption text to score | <1 |
| figure_caption_pattern | regex | ^(Figure|Fig\.) | Caption prefix regex | invalid regex |
| figure_caption_font_smaller_ratio | float | 0.92 | Size ratio for caption detection | <=0 or >=1 |
| figure_caption_weight_pattern | float | 0.35 | Scoring weight | negative |
| figure_caption_weight_position | float | 0.25 | Scoring weight | negative |
| figure_caption_weight_distance | float | 0.25 | Scoring weight | negative |
| figure_caption_weight_font | float | 0.15 | Scoring weight | negative |
| figure_caption_strip_prefix | bool | true | Remove 'Figure n:' prefix | n/a |
| figure_caption_decimal_precision | int | 6 | Internal scoring precision | <1 |
| xref_enable | bool | true | Enable cross-reference normalization | n/a |
| xref_case_insensitive | bool | true | Case-insensitive pattern matching | n/a |
| xref_unresolved_policy | enum | annotate | Unresolved ref policy | invalid enum |
| xref_max_per_section | int | 100 | Rate-limit per section | <1 |
| xref_resolve_figures | bool | true | Enable figure references | n/a |
| xref_resolve_appendices | bool | false | Enable appendix references | n/a |
| xref_patterns | list[regex] | [] | Override/extend default patterns | invalid regex |
| numbering_validate_gaps | bool | true | Warn on numbering gaps | n/a |
| numbering_allow_chapter_resets | bool | false | Honor chapter resets | n/a |
| numbering_max_depth | int | 6 | Truncate deep section path | <1 |
| appendix_patterns | list[regex] | [] | Prepend appendix patterns | invalid regex |
| appendix_letter_case | enum | upper | Letter case normalization | invalid enum |
| appendix_requires_page_break | bool | true | Enforce page break rule | n/a |
| appendix_level | enum | chapter | Appendix hierarchy level | invalid enum |
| numbering_error_strict | bool | false | Escalate numbering anomalies | n/a |

Weight Sum Validation: sum(figure_caption_weight_*) MUST equal 1 ±1e-6 else `config_weight_sum_invalid` (exit 2). Deprecated key `linkify_cross_references` triggers a warning and is ignored if `xref_enable` explicitly set; if only deprecated key present the tool maps it to `xref_enable` for backward compatibility (no fatal).
numbering_validate_gaps: true
numbering_allow_chapter_resets: false
numbering_max_depth: 6
# Appendix detection
appendix_patterns: []
appendix_letter_case: upper
appendix_requires_page_break: true
appendix_level: chapter

# Numbering strictness
numbering_error_strict: false

### 12.2 AI Integration Configuration

AI assistance is optional and disabled by default. When enabled, only the
configured provider may be contacted.

- `ai.enabled` (bool, default false)
- `ai.provider` (enum: `azure_openai`)
- `ai.min_confidence` (float, default 0.85)
- `ai.timeout_s` (int, default 15)
- `ai.max_concurrent` (int, default 2)
- `ai.max_tokens` (int, default 256)
- `ai.temperature` (float, default 0.0)
- `ai.top_p` (float, default 1.0)
- `ai.cache_dir` (string, default `.ai-cache` under output root)
- `ai.cache_mode` (enum: `read_write`|`readonly`|`refresh`; default `read_write`)
- `ai.redact_snippets` (bool, default true)
- `ai.fail_on_error` (bool, default false)
- `ai.use_cases` (list[str], default `[]`) — subset of
  ["headings","codeblocks","captions","noise","tables"].

Azure-specific keys:
- `ai.azure.endpoint` (url)
- `ai.azure.deployment` (string)
- `ai.azure.api_version` (string)
- `ai.azure.api_key_env` (string; env var name holding the key)

# Cross reference (deduplicated; patterns empty = internal defaults)
xref_enable: true
xref_case_insensitive: true
xref_unresolved_policy: annotate   # annotate|keep|drop
xref_max_per_section: 100
xref_resolve_figures: true
xref_resolve_appendices: false
xref_patterns: []
```

## 13. Testing Strategy

- Unit Tests: heuristics (hyphenation on Span sequences, heading detection

  promoting Blocks to SectionNodes, list nesting, slug generation, code block
  detection, table fallback classification, figure caption resolution scoring).

- Figure Caption Resolution: scoring components, tie-breaking precedence,

   prefix stripping, duplicate caption shared case, weight sum validation error
   path.

- Integration: run on sample curated mini-PDFs with known expected Markdown

  snapshots (use approval tests / golden files).

- Property Tests: slug uniqueness, stable DocumentTree hash (rerun pipeline ->

  identical serialized signature), ordering invariants (Span order_index
  strictly increasing), absence of unexpected Block type mutations.

- Performance Benchmark: measure pages/second on fixture PDF.
- Regression: store manifest hash to detect structural drift.
- Manifest Structure: validate via internal assertions reflecting prose spec

   (ids, slug uniqueness, structural_hash determinism) until external JSON
   Schema is added in a future iteration.

- Orphan Heading Tests: sequences (H2,H2), (H2,H3), (H2,H2,Paragraph) verifying

   demotion only in first case with config true; ensure no demotion when
   `demote_orphan_headings=false`.

- Noise Filtering: threshold, allowlist/blocklist precedence, over-removal

   abort, determinism (same hash after page permutation).

- Figure Manifest Fields: caption change affects hash (since caption in

   projection); alt change alone does not; confidence precision stable.

- Cross References: unresolved policy behaviors; only resolved appear in

   manifest; enabling/disabling figure resolution does not change structural
   hash; pattern order deterministic.

- Numbering Extraction: gap detection, chapter reset remap, appendix ordering,

   depth truncation.

- Appendix Detection: pattern precedence, early ignore, page break requirement,

   duplicate/out-of-order letters, numeric annex ignored, cross-reference
   resolution.

- Strict Numbering Mode: `numbering_error_strict=true` escalates duplicate

   chapter number or appendix duplicate letter to fatal (exit 4).

- Slug Collision Fatal: synthetic exhaustion test triggers

   `unresolvable_slug_collision` (exit 4) without partial manifest.

- Config Validation: invalid caption weight sum (sum != 1) → exit 2; bad regex

   in `appendix_patterns` → exit 2.

## 14. Logging & Observability

- Structured log lines: phase, page, action, counts.
- `--debug-dump` option to emit intermediate JSON (spans, nodes) for a subset of

  pages.

## 15. Error Handling & Taxonomy

Aim: Explicit classification of failures/anomalies with deterministic exit
codes. Warnings never abort; only categorized fatal errors do.

### 15.1 Categories

- CONFIG (exit code 2): Invalid/conflicting user configuration or schema

  violations.

- IO (exit code 3): Filesystem or PDF access failures.
- PARSE (exit code 4): Irrecoverable structural issues that would produce

  ambiguous/unstable output.

- GENERAL (exit code 1): Unhandled exceptions (fallback). Goal: near-zero

  occurrence.

### 15.2 Canonical Error Codes

CONFIG:

- `config_parse_error` – YAML/JSON load failure.
- `config_invalid_value` – value outside allowed domain (generic fallback).
- `config_weight_sum_invalid` – figure caption weight components do not sum to 1

  ±1e-6.

- `config_regex_invalid` – supplied regex fails to compile.
- `config_conflict` – mutually exclusive options (future placeholder).
- `config_unknown_key` – extraneous key when future strict mode enabled.


IO:

- `pdf_unreadable`
- `output_path_unwritable`
- `image_write_failed` (fatal only if all figures fail)


PARSE:

- `unresolvable_slug_collision`
- `duplicate_slug_detected`
- `structural_hash_failure`
- `over_removal_abort`
- `numbering_strict_violation` (triggered only when

  `numbering_error_strict=true` on duplicate chapter number or appendix
  duplicate letter)

WARN / INFO (non-fatal): `chapter_number_reset_detected`,
`duplicate_chapter_number`, `section_gap_detected`, `appendix_out_of_order`,
`appendix_duplicate_letter`, `appendix_missing_page_break`,
`appendix_early_ignored`, `appendix_numeric_identifier_ignored`,
`figure_extraction_failed` (per-figure), `figure_caption_weight_sum_adjusted`
(future), `xref_unresolved`, noise counters, orphan heading demotions, table
fallback notices.

### 15.3 Structured Error Object

When emitting a fatal error (and `--debug-json-errors` set) the tool prints
JSON:

```text
{"category":"CONFIG","code":"config_weight_sum_invalid","message":"Figure caption weights sum 0.93 != 1.0","context":{"sum":0.93,"weights":[0.35,0.25,0.25,0.08]}}
```

`context` keys must be deterministic primitive scalars/arrays.

### 15.4 Exit Code Mapping

| Category | Exit |
|----------|------|
| CONFIG   | 2 |
| IO       | 3 |
| PARSE    | 4 |
| GENERAL  | 1 |

### 15.5 Escalation Rules

1. First PARSE error aborts; subsequent suppressed (DEBUG only).
1. CONFIG validation halts before PDF processing.
1. `numbering_error_strict=false` keeps anomalies as WARN; true escalates to

   PARSE.

1. All figure extraction failures escalate to IO; partial failures remain WARN

   entries.

### 15.6 Testing

- Mapping representative errors to exit codes.
- Simulated slug collision exhaustion.
- Noise over-removal triggering `over_removal_abort`.
- Strict numbering escalation toggle.
- Invalid regex in `appendix_patterns`.


### 15.7 Non-Goals

- I18n of error messages.
- Partial retries or auto-healing.


This taxonomy supersedes earlier minimal bullet list.

## 16. Security & Compliance

- External network calls are permitted only to explicitly configured AI providers
  (e.g., Azure OpenAI) when `ai.enabled=true`. All non-AI network calls remain
  disallowed.
- Determinism with AI: Use temperature=0, top_p=1; record provider deployment
  identifiers and `system_fingerprint` (when available). Persist AI decisions in
  a cache keyed by stable features to ensure re-run stability; cache refresh is
  explicit.
- Privacy: Minimize payloads (features/snippets), support redaction, and avoid
  sending full-page text. Keys are provided via environment variables.
- Failure policy: Timeouts and bounded retries; fallback to heuristics if the
  provider is unavailable. Optional `ai.fail_on_error` to escalate.
- Handle untrusted PDFs defensively: limit resource usage; sandboxing remains
  optional (future).

## 17. Performance Considerations

- Lazy page iteration; avoid materializing all spans before classification.
- Cache font style mapping.
- Parallel image extraction (thread pool) after text pass (I/O bound).


## 18. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Inconsistent PDF structure | Misclassification | Provide manual override config + debug dumps |
| Complex tables | Loss of fidelity | Confidence fallback to fenced block |
| Figure extraction failures | Missing visuals | Fallback raster crop by bbox hints |
| Over-aggressive noise removal | Lost content | Dry-run preview + whitelist patterns |
| Performance degradation on large PDFs | Slow conversion | Profiling + caching + optional feature flags |
| Ambiguous heading levels | Incorrect nesting | Font cluster epsilon + manual overrides |

## 19. Roadmap (Future Enhancements)

- Batch processing directory mode.
- Web UI (FastAPI) with preview diff.
- Embedded vector (SVG) extraction for diagrams.
- Glossary & index extraction heuristics.
- Multi-language output transformations.
- AI-assisted semantic section labeling.


## 20. Acceptance Checklist

- [ ] Run on target sample book PDF -> outputs hierarchical Markdown.
- [ ] Images extracted and linked with alt text.
- [ ] Manifest and (optional) TOC generated.
- [ ] Code blocks preserved with indentation.
- [ ] No leftover page numbers or running headers in output text.
- [ ] Deterministic rerun (hash stable).
- [ ] Filenames follow prefix + semantic pattern (parts/chapters/appendices)

  with no collisions.

- [ ] Chapter numbers remain globally incremental even with Parts present

  (logged warning if source restarts numbering).

- [ ] Numbering extraction logs gaps/resets without altering visible titles.
- [ ] Appendix detection: only post-chapter appendices recognized; out-of-order

   logged; duplicate letter handled per spec.

- [ ] Error taxonomy: representative CONFIG/IO/PARSE cases produce documented

   exit codes.

- [ ] Strict numbering mode aborts on duplicate chapter number or appendix

   duplicate letter with exit 4.

- [ ] Config validation rejects invalid caption weight sums and bad appendix

   regex patterns.

- [ ] Manifest passes internal structural validation (ids/slug patterns, hash

   determinism) per prose spec.

- [ ] Deprecated `linkify_cross_references` handled with warning and does not

   cause divergence.

## 21. Open Questions

- Should we support splitting very large chapters automatically by heading

  depth? (config?)

- Do we normalize Part/Chapter numbering gaps or retain original numbering (in

  case of skipped numbers)?

- Provide plugin hooks for custom transformations?


---
Editorial Note (Structural Cleanup 2025-09-05): Functional Requirements
renumbered (added explicit items for Code Block Extraction, Inline Code, Config
Overrides, Logging, Dry Run, Resume). Restored missing Section 8 (Technology
Choices) separated from Non-Functional Requirements. Updated Figure data model
line with new caption fields. No semantic behavior changes beyond clarification.
Editorial Note (Schema Rollback 2025-09-05): Removed external
`tests/schema/manifest.schema.json` file to align with PRD-only refinement
mandate. Section 9.2.8 now marks schema as planned; manifest validation remains
prose-driven until schema is formally introduced.

---
End of PRD.
