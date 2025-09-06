# Project Architecture Rules (Non-Obvious Only)
- Stubbed CLI hides full flow: Config → (future) Ingest Spans → Utils process → Assemble Blocks/Nodes → Build DocumentTree → Render MD/assets → Export with manifest/toc.
- Hidden deps: __init__.py lazy __getattr__ avoids import cycles (essential for lightweight tests).
- Counterintuitive: --manifest writes partial without validation; --resume skips via manifest checks (planned).
- Global chapter numbering mandatory (log warnings on resets; no per-part).
- I/O isolation: Pure functions until exporter.py (no early writes/images).
- Phasing strict: Follow module order to avoid coupling (ingest.py first).
- No network (PRD); use generators for streaming (defer rasterization).
- Dataclass invariants: Hierarchical Node with pre-order slugs/indexes.
- Testing matrix in design.md: Cover heuristics, determinism, edge cases (synthetic fixtures only).
