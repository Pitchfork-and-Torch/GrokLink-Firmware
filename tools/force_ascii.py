#!/usr/bin/env python3
from pathlib import Path

EXTS = {".md", ".txt", ".py", ".ps1", ".sh", ".c", ".h", ".json", ".toml", ".fam", ".proto"}
NAMES = {"LICENSE", "CHANGELOG.md", "SECURITY.md"}


def to_ascii(s: str) -> str:
    if s.startswith("\ufeff"):
        s = s[1:]
    out: list[str] = []
    for ch in s:
        o = ord(ch)
        if o < 128:
            out.append(ch)
            continue
        if ch in "\u2192\u21d2":
            out.append("->")
        elif ch == "\u2190":
            out.append("<-")
        elif ch == "\u2013":
            out.append("-")
        elif ch == "\u2014":
            out.append(" - ")
        elif ch in "\u2018\u2019":
            out.append("'")
        elif ch in "\u201c\u201d":
            out.append('"')
        elif ch == "\u2026":
            out.append("...")
        elif ch == "\u2502":  # |
            out.append("|")
        elif ch == "\u2500":  # -
            out.append("-")
        elif ch in "\u251c\u2514\u2510\u250c\u2518\u252c\u2534\u2524\u251c":
            out.append("+")
        elif ch in "\u25bc\u25b2\u25b6\u25c0\u25b8":  # triangles
            out.append("v" if ch == "\u25bc" else ">")
        else:
            # drop other non-ascii (including broken mojibake fragments)
            pass
    return "".join(out)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    n = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(x in path.parts for x in (".git", "__pycache__", ".venv")):
            continue
        if path.suffix.lower() not in EXTS and path.name not in NAMES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        fixed = to_ascii(text)
        if fixed != text:
            path.write_text(fixed, encoding="ascii", newline="\n")
            n += 1
            print("ascii", path.relative_to(root))
    print("updated", n)

    left = 0
    for path in root.rglob("*.md"):
        if ".git" in path.parts:
            continue
        t = path.read_text(encoding="utf-8")
        if any(ord(c) > 127 for c in t):
            left += 1
            print("still", path.relative_to(root))
    print("left_md", left)


if __name__ == "__main__":
    main()
