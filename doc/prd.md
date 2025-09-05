# PRD: Technical PDF to Structured Markdown Conversion Tool

## 1. Overview
A Python-based command-line tool that ingests a technical PDF book (e.g., "AUTOMATED TESTING IN MICROSOFT DYNAMICS 365 BUSINESS CENTRAL") and produces a clean, semantically structured multi-file Markdown corpus suitable for static site generators (e.g., MkDocs, Docusaurus) or GitHub browsing. It removes non-content noise (advertisements, repeated headers/footers, page numbers, watermarks), preserves logical structure (parts, chapters, sections, code listings, tables, callouts), and extracts embedded images (diagrams, figures) while keeping references consistent.

Primary objective: High-fidelity, human-editable Markdown with minimal post-processing.

## 2. Goals & Success Criteria
- Accurate reconstruction of document hierarchy (Part > Chapter > Section > Subsection) to depth level 4.
- Preserve and format: headings, paragraphs, bullet/numbered lists, tables, images, figure captions, inline code, block code, callouts (Note/Tip/Warning), footnotes, and cross-references.
- Remove boilerplate: running headers, footers, page numbers, TOC pages (optional), copyright pages, blank pages.
- Extract images with deterministic filenames and relative links.
- Idempotent: running tool twice yields same output with no spurious diffs.
- ≥ 98% of code blocks retained without line breaks corruption (manual spot QA metric).
- CLI completes on a ~300-page technical PDF in < 90 seconds on a modern laptop (baseline optimization target, not hard SLA).

## 3. Out of Scope (Initial Version)
- OCR for scanned PDFs (assumes text-based PDF). (Future: Tesseract fallback.)
- Math formula LaTeX reconstruction (pass through as plain text or inline code style if detected).
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
Root output folder structure (example):
```
output/
  assets/images/
    fig_001_intro.png
    fig_002_pipeline.png
  book/
    00_preface.md
    01_part_i_overview.md
    02_chapter_01_introduction.md
    03_chapter_02_architecture.md
    ...
  manifest.json
  toc.yml (optional for MkDocs)
```

### Markdown Conventions
- H1 reserved for top-level book title (single file `index.md` or first chapter). Subsequent files start at H2 (configurable) or keep natural depth with normalization.
- Use fenced code blocks with language inference (heuristic from first line / keywords) e.g. `al`, `powershell`, `json`, `yaml`.
- Tables emitted in GitHub-flavored Markdown.
- Callouts mapped to blockquotes with leading label: `> **Note:** ...`.
- Footnotes: Convert to GFM footnote syntax: `Here is a ref.[^1]` and `[^1]: Footnote text` appended at file end.

## 6. Functional Requirements
1. Parse PDF layout into ordered text spans with positional metadata (x, y, font size, style, page number).
2. Heading Detection:
   - Use font size clustering + bold/uppercase heuristics.
   - Numeration patterns: `Part I`, `Chapter 2`, `1.2.3`, `Appendix A`.
   - Build hierarchical tree preserving order.
3. Paragraph Assembly:
   - Merge line fragments by proximity and hyphenation resolution.
   - Preserve intentional blank lines (e.g., before code or lists).
4. List Detection:
   - Recognize bullets (`•`, `-`, `*`) and ordered patterns (`1.`, `a)`, `(i)`), indent-based nesting (x-offset deltas).
5. Code Block Extraction:
   - Monospaced font detection OR bounding box uniform width OR leading indent threshold.
   - Avoid wrapping lines; reconstruct original spacing.
6. Inline Code:
   - Short monospaced spans embedded in regular paragraphs -> wrap in backticks.
7. Image Extraction:
   - Export vector and raster objects where possible (fallback: page raster cropping around figure region if compound grouping is detected).
   - Associate nearest preceding or following caption (pattern: `Figure \d+:` or italic smaller font) and store in alt text.
8. Table Reconstruction:
   - Detect ruled lines or column-aligned text boxes (grid inference via x-coordinate clustering).
   - Output Markdown table; fallback to preformatted fenced block if ambiguous.
9. Footnotes:
   - Detect superscript markers and trailing page footnote region based on y-position at page bottom.
10. Cross-Reference Normalization:
    - Convert `See Chapter 3` to internal relative link if target heading slug exists.
11. Slug Generation:
    - Deterministic: lowercase, hyphenate, remove punctuation, prefix with sequence for ordering.
12. Manifest Generation:
    - JSON listing: title, slug, file path, heading level, parent slug, page span, figure map.
13. TOC Export:
    - Optional YAML structure for MkDocs or JSON for dynamic sites.
14. Config Overrides:
    - Provide a config file enabling threshold tuning (font clusters, min heading size, list indent delta, hyphenation patterns, figure caption regex, exclude pages ranges, merge small caps to normal case).
15. Logging & Verbosity Levels (`--verbose`, `--quiet`).
16. Dry Run Mode (`--dry-run`) outputs only the detected structure summary.
17. Resume Mode: skip already converted assets unless `--force`.

## 7. Non-Functional Requirements
- Deterministic output given identical inputs + config.
- Modular code (separate concerns: parsing, semantic modeling, rendering, exporters).
- Testable pure functions for heuristics.
- Performance: Single pass streaming where feasible; avoid full-page rasterization unless extracting images.
- Memory Footprint: Under 1 GB for 400-page PDF typical.
- Logging uses standard library `logging` with structured contexts.
- Python version: 3.11+.

## 8. Technology Choices
- PDF Parsing: `pdfminer.six` (text + layout) or `pdfplumber` wrapper for convenience.
- Image Extraction: `pypdf` for embedded objects; fallback: `pdf2image` (Poppler) only when necessary.
- Table Detection: Leverage `pdfplumber` table extraction + custom alignment fallback.
- CLI: `typer` (preferred for ergonomics) or `argparse` minimal fallback.
- Config Serialization: `pydantic` models (validation) + YAML via `pyyaml`.
- Slugification: `python-slugify` or small custom deterministic function.
- Language detection for code: lightweight heuristics; optionally `pygments.lexers.guess_lexer` guarded by performance flag.

## 9. High-Level Architecture
Layers:
1. Ingestion Layer: Loads PDF pages, extracts raw layout objects.
2. Normalization Layer: Converts raw spans to canonical `Token` objects (text, bbox, font attrs, page).
3. Semantic Detection Layer: Builds `DocumentTree` (nodes: Part, Chapter, Section, Paragraph, List, CodeBlock, Table, Figure, Footnote).
4. Post-Processing Layer: Cross-linking, footnote resolution, slug assignment, dedup removal.
5. Rendering Layer: Walks tree and emits Markdown fragments per logical chapter file.
6. Export Layer: Writes files, images, manifest, toc.

Core Data Classes (conceptual):
```
Span {text, bbox, font_name, font_size, style_flags, page}
Node {type, children, meta}
Figure {image_path, caption, alt, page, bbox}
CodeBlock {language, lines, page_span}
Table {rows, page_span, confidence}
ManifestEntry {slug, title, level, file, parent, pages}
```

## 10. Detailed Algorithms & Heuristics
### Heading Clustering
- Collect all font sizes; k-means (k<=6) or simple frequency sorting.
- Assign tiers by descending size; merge tiers whose difference < epsilon (configurable, default 1pt).
- Classify candidates by: large font + (bold OR all-caps OR leading numeral/keyword `Part|Chapter|Appendix`).

### Hyphenation Repair
- Regex `([A-Za-z]{3,})-$` at line end + next line starts lowercase -> merge without hyphen.
- Maintain exception list for domain-specific tokens.

### List Nesting
- Track current indent stack; new bullet indent within tolerance -> same level; deeper -> push; shallower -> pop until fit.

### Code Block Detection
- Consecutive spans with monospaced font OR uniform leading indent ≥ 4 spaces across ≥ 2 lines.
- Stop when blank line or style break.

### Table Extraction Fallback
- Group spans by y-lines (tolerance ±2px) then cluster x-start positions; build grid.
- If inconsistent column count across >30% rows -> mark `confidence<0.5` -> fallback to preformatted.

### Figure Caption Association
- Candidate caption within 150px vertical distance from figure bbox; prefer below; must match regex `^(Figure|Fig\.)` or italic smaller font.

### Cross-Reference Linking
- Regex `Chapter\s+(\d+)` -> map to chapter slug index.

## 11. CLI Design
Example:
```
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
```
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
```

## 13. Testing Strategy
- Unit Tests: heuristics (hyphenation, heading detection, list nesting, slug generation, code block detection).
- Integration: run on sample curated mini-PDFs with known expected Markdown snapshots (use approval tests / golden files).
- Property Tests: slug uniqueness, stable tree (rerun parse -> identical structure hash).
- Performance Benchmark: measure pages/second on fixture PDF.
- Regression: store manifest hash to detect structural drift.

## 14. Logging & Observability
- Structured log lines: phase, page, action, counts.
- `--debug-dump` option to emit intermediate JSON (spans, nodes) for a subset of pages.

## 15. Error Handling
- Graceful skip of unsupported image objects with warning.
- Explicit exceptions for: unreadable PDF, output path not writable, config parse error.
- Non-zero exit codes: 1 (general), 2 (config), 3 (I/O), 4 (parse fatal).

## 16. Security & Compliance
- No external network calls during conversion.
- Handle untrusted PDFs defensively: limit resource usage, optional sandbox note (future).

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

## 21. Open Questions
- Should we support splitting very large chapters automatically by heading depth? (config?)
- Do we normalize Part/Chapter numbering gaps or retain original numbering (in case of skipped numbers)?
- Provide plugin hooks for custom transformations?

---
End of PRD.
