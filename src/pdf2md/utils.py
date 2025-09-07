from __future__ import annotations

import re
from collections.abc import Iterable

from slugify import slugify as _slugify

SLUG_SAFE_REMOVE = ["'", '"']

# Module-level cache to track base slug counts per used_slugs set
# This avoids the need to reverse-engineer base slugs from final slugs
_base_slug_cache: dict[int, dict[str, int]] = {}


def deterministic_slug(text: str, prefix_index: int | None = None, width: int = 2) -> str:
    base = text.strip().lower()
    for ch in SLUG_SAFE_REMOVE:
        base = base.replace(ch, "")
    s = _slugify(base)
    if prefix_index is not None:
        return f"{prefix_index:0{width}d}-{s}"
    return s


def generate_unique_slug(
    text: str, prefix_index: int | None, width: int, used_slugs: set[str]
) -> str:
    """Generate a unique slug, adding collision suffix if needed.

    Args:
        text: The text to slugify
        prefix_index: Optional numeric prefix index
        width: Width for zero-padding the prefix
        used_slugs: Set of already used slugs to check for collisions

    Returns:
        A unique slug, with collision suffix (-2, -3, etc.) if needed

    Examples:
        >>> used = set()
        >>> slug1 = generate_unique_slug("Test", 1, 2, used)
        >>> slug1
        '01-test'
        >>> used.add(slug1)
        >>> slug2 = generate_unique_slug("Test", 2, 2, used)
        >>> slug2
        '02-test-2'
    """
    # Generate the base slug without considering collisions first
    base_text_slug = deterministic_slug(text, prefix_index=None, width=width)

    # Get or create base slug counter for this used_slugs set
    # This avoids the need to reverse-engineer base slugs from final slugs
    cache_key = id(used_slugs)
    if cache_key not in _base_slug_cache:
        _base_slug_cache[cache_key] = {}

    base_counts = _base_slug_cache[cache_key]
    collision_count = base_counts.get(base_text_slug, 0)

    if collision_count == 0:
        # No collision, use the normal slug
        result_slug = deterministic_slug(text, prefix_index, width)
    else:
        # Collision detected, add suffix
        suffix = collision_count + 1
        if prefix_index is not None:
            result_slug = f"{prefix_index:0{width}d}-{base_text_slug}-{suffix}"
        else:
            result_slug = f"{base_text_slug}-{suffix}"

    # Update counts
    base_counts[base_text_slug] = collision_count + 1
    used_slugs.add(result_slug)
    return result_slug


def clear_slug_cache() -> None:
    """Clear the internal slug cache to prevent memory leaks.

    This should be called when you're done with a set of used_slugs
    to prevent the cache from growing indefinitely.
    """
    global _base_slug_cache
    _base_slug_cache.clear()


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
    r"^(part\s+\w+|chapter\s+\d+|appendix\s+[a-zA-Z]|" r"\d+(?:\.\d+){0,3})\b",
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
