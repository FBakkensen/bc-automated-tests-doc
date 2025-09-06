from __future__ import annotations

import re
from collections.abc import Iterable

from slugify import slugify as _slugify

SLUG_SAFE_REMOVE = ["'", '"']


def deterministic_slug(text: str, prefix_index: int | None = None, width: int = 2) -> str:
    base = text.strip().lower()
    for ch in SLUG_SAFE_REMOVE:
        base = base.replace(ch, "")
    s = _slugify(base)
    if prefix_index is not None:
        return f"{prefix_index:0{width}d}-{s}"
    return s


HYPHENATION_RE = re.compile(r"([A-Za-z]{3,})-$")


def repair_hyphenation(lines: Iterable[str]) -> list[str]:
    result: list[str] = []
    pending = None
    for line in lines:
        line = line.rstrip()
        if pending is not None:
            if line and line[0].islower():
                result.append(pending + line)
            else:
                result.append(pending + "-" + line)
            pending = None
            continue
        if HYPHENATION_RE.search(line):
            pending = line[:-1]
        else:
            result.append(line)
    if pending is not None:
        result.append(pending)
    return result


HEADING_PATTERN = re.compile(
    r"^(part\s+\w+|chapter\s+\d+|appendix\s+[a-zA-Z]|"
    r"\d+(?:\.\d+){0,3})\b",
    re.IGNORECASE,
)


def is_heading_candidate(text: str) -> bool:
    if len(text) > 180:
        return False
    if HEADING_PATTERN.match(text.strip()):
        return True
    # heuristic: many uppercase words
    words = text.split()
    return bool(words and sum(1 for w in words if w.isupper() and len(w) > 2) / len(words) >= 0.6)
