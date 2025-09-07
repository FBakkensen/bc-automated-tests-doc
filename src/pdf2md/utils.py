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

    # Check if this base text slug (without prefix) has been used before
    collision_count = sum(1 for slug in used_slugs if _extract_base_slug(slug) == base_text_slug)

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

    used_slugs.add(result_slug)
    return result_slug


def _extract_base_slug(full_slug: str) -> str:
    """Extract the base slug text from a full slug (removing prefix and collision suffix).

    Examples:
        >>> _extract_base_slug("01-introduction")
        'introduction'
        >>> _extract_base_slug("02-introduction-3")
        'introduction'
        >>> _extract_base_slug("introduction-2")
        'introduction'
    """
    # Remove numeric prefix if present (format: "NNN-...")
    if "-" in full_slug and full_slug.split("-", 1)[0].isdigit():
        without_prefix = full_slug.split("-", 1)[1]
    else:
        without_prefix = full_slug

    # Remove collision suffix if present (format: "...-N" where N is a number)
    parts = without_prefix.rsplit("-", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0]
    return without_prefix


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
