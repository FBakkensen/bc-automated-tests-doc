#!/usr/bin/env python3
import sys
from pathlib import Path
import textwrap

def reflow_markdown(content: str, width: int = 80) -> str:
    lines = content.splitlines()
    out = []
    in_fence = False
    fence_marker = None

    def flush_para(buf):
        if not buf:
            return
        text = " ".join(s.strip() for s in buf)
        wrapped = textwrap.fill(text, width=width)
        out.extend(wrapped.splitlines())

    para_buf = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        # Handle fenced code blocks
        if stripped.startswith("```"):
            if para_buf:
                flush_para(para_buf)
                para_buf = []
            if in_fence:
                in_fence = False
                fence_marker = None
            else:
                in_fence = True
                fence_marker = stripped[:3]
            out.append(line)
            i += 1
            continue

        if in_fence:
            out.append(line)
            i += 1
            continue

        # Tables or headings or HTML comments: do not wrap
        if (stripped.startswith("|") or stripped.startswith("#") or
            stripped.startswith("<!--") or stripped.startswith(">") or
            stripped.startswith("=") or stripped.startswith("-") and not stripped.startswith("- ")):
            if para_buf:
                flush_para(para_buf)
                para_buf = []
            out.append(line)
            i += 1
            continue

        # List items: reflow with indentation preserved
        if stripped.startswith(('- ', '* ', '+ ')) or any(stripped.startswith(f"{n}. ") for n in map(str, range(1,10))):
            if para_buf:
                flush_para(para_buf)
                para_buf = []
            # collect following lines that are part of this list item (until blank or new item)
            prefix = line[:len(line) - len(stripped)]
            bullet, rest = stripped.split(' ', 1)
            item_lines = [rest]
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                nstr = nxt.lstrip()
                if not nstr:
                    break
                if nstr.startswith(('- ', '* ', '+ ')) or any(nstr.startswith(f"{n}. ") for n in map(str, range(1,10))):
                    break
                if nstr.startswith("```"):
                    break
                item_lines.append(nxt.strip())
                j += 1
            text = " ".join(s.strip() for s in item_lines)
            wrapped = textwrap.fill(text, width=width - len(prefix) - len(bullet) - 1)
            wrapped_lines = wrapped.splitlines()
            if wrapped_lines:
                out.append(f"{prefix}{bullet} {wrapped_lines[0]}")
                for wl in wrapped_lines[1:]:
                    out.append(f"{prefix}{' ' * (len(bullet) + 1)}{wl}")
            i = j
            continue

        # Blank line flushes paragraph
        if not stripped:
            if para_buf:
                flush_para(para_buf)
                para_buf = []
            out.append("")
            i += 1
            continue

        # Default: accumulate paragraph
        para_buf.append(line)
        i += 1

    if para_buf:
        flush_para(para_buf)

    return "\n".join(out) + "\n"


def main():
    paths = [Path(p) for p in sys.argv[1:]]
    for p in paths:
        data = p.read_text(encoding='utf-8')
        new = reflow_markdown(data, width=80)
        p.write_text(new, encoding='utf-8')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: reflow_md.py <files...>")
        sys.exit(1)
    main()

