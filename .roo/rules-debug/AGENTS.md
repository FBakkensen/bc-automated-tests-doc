# Project Debug Rules (Non-Obvious Only)
- CLI stub writes {"status": "stub"} manifest without processing (hidden flow disconnect).
- Config raises raw exceptions without Typer handling (silent CLI failures possible).
- No logging module yet; future structured logs (e.g., {"stage": "xref", "action": "unresolved"}).
- Tests require conftest.py sys.path hack; fails without it due to src/ layout.
- Dry-run previews structure but skips writes (stubbed; check cfg.model_dump() output).
- PRD errors: Map to specific exit codes (2: invalid config weights); investigate via targeted exceptions.
- Determinism checks: Hash serialized DocumentTree for stability (implement in tests).
- Performance: Limit parallelism to I/O-bound image steps post-validation (generators for pages).