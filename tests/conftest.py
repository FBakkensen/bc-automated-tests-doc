from __future__ import annotations

import os
import sys
from pathlib import Path


def _ensure_paths() -> None:
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    for p in (str(root), str(src)):
        if p not in sys.path:
            sys.path.insert(0, p)


_ensure_paths()

# Ensure deterministic environment for tests
os.environ.setdefault("PYTHONHASHSEED", "0")
