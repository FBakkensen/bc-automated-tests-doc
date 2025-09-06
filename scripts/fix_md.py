#!/usr/bin/env python3
import re
import sys
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,6})\s+")
LIST_RE = re.compile(r"^\s*(?:[-+*]\s+|\d+\.\s+)")
TABLE_RE = re.compile(r"^\|.*\|?$")
FENCE_OPEN_RE = re.compile(r"^```(.*)$")


def ensure_blank_around_blocks(lines: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        # Headings
        if HEADING_RE.match(line):
            if out and out[-1].strip() != "":
                out.append("")
            out.append(line)
            # ensure blank after
            if i + 1 < n and lines[i + 1].strip() != "":
                out.append("")
            i += 1
            continue

        # Code fences
        m = FENCE_OPEN_RE.match(line)
        if m:
            info = m.group(1).strip()
            lang = info.split()[0] if info else ""
            if not lang:
                line = "```text"
            if out and out[-1].strip() != "":
                out.append("")
            out.append(line)
            i += 1
            # pass through until closing fence
            while i < n and not lines[i].strip().startswith("```"):
                out.append(lines[i])
                i += 1
            if i < n:
                out.append(lines[i])
                i += 1
            if i < n and lines[i].strip() != "":
                out.append("")
            continue

        # Tables: group consecutive table lines
        if TABLE_RE.match(line):
            if out and out[-1].strip() != "":
                out.append("")
            while i < n and TABLE_RE.match(lines[i]):
                out.append(lines[i])
                i += 1
            if i < n and lines[i].strip() != "":
                out.append("")
            continue

        # Lists: surround with blank lines and normalize prefix numbers to '1.'
        if LIST_RE.match(line):
            if out and out[-1].strip() != "":
                out.append("")
            # capture list block
            while i < n and (LIST_RE.match(lines[i]) or lines[i].strip() == ""):
                if LIST_RE.match(lines[i]):
                    # remove unintended leading spaces for top-level items
                    li = re.sub(r"^\s+", "", lines[i])
                    # normalize ordered list numbering to '1.'
                    li = re.sub(r"^(\d+)\.\s+", "1. ", li)
                    out.append(li)
                else:
                    out.append("")
                i += 1
            if i < n and lines[i].strip() != "":
                out.append("")
            continue

        # Default
        out.append(line)
        i += 1
    return out


def fix_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


def main(paths: list[str]) -> None:
    for p in paths:
        path = Path(p)
        text = path.read_text(encoding='utf-8')
        lines = text.splitlines()
        lines = ensure_blank_around_blocks(lines)
        # Remove stray leading spaces before top-level list markers
        lines = [re.sub(r"^\s+([-+*]\s+|\d+\.\s+)", r"\1", ln) for ln in lines]
        new = "\n".join(lines)
        new = fix_trailing_newline(new)
        path.write_text(new, encoding='utf-8')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: fix_md.py <files...>")
        sys.exit(1)
    main(sys.argv[1:])
