# Project Documentation Rules (Non-Obvious Only)
- PRD.md and design.md are normative (define pipeline, invariants, error taxonomy); code stubs align but unimplemented.
- src/pdf2md/ focuses on config/models/utils scaffolding; full ingestion (pdfplumber/pdfminer) absent yet (counterintuitive disconnect).
- Utils assume post-ingestion Spans (e.g., repair_hyphenation on merged lines); no raw PDF handling in current code.
- Doc pipeline: Ingestion → Normalization → Assembly → Promotion → Post-Processing → Rendering (per design.md).
- Manifest omits structural_hash in stub (planned for stability, excludes cross-refs).
- Two config systems? Locales in root for extension? (Irrelevant; project is PDF-to-MD CLI).
