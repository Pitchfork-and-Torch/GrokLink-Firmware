#!/usr/bin/env python3
from pathlib import Path
import re

EXTS = {".md", ".txt", ".py", ".ps1", ".sh", ".c", ".h", ".json", ".toml", ".fam", ".proto"}


def clean(text: str) -> str:
    pairs = [
        ("\u2192", "->"),
        ("\u2190", "<-"),
        ("\u21d2", "=>"),
        ("\u2014", " - "),
        ("\u2013", "-"),
        ("\u2018", "'"),
        ("\u2019", "'"),
        ("\u201c", '"'),
        ("\u201d", '"'),
        ("\u2026", "..."),
        ("\u00d7", "x"),
        ("\u2264", "<="),
        ("\u2265", ">="),
        ("\u00b7", "-"),
        ("\u2705", "[OK]"),
        # UTF-8 interpreted as cp1252 then stored
        ("\u00e2\u20ac\u201c", "-"),  # en dash variants
        ("\u00e2\u20ac\u201d", " - "),
        ("\u00e2\u20ac\u2122", "'"),
        ("\u00e2\u20ac\u0153", '"'),
        ("\u00e2\u20ac\u009d", '"'),
        ("\u00e2\u20ac\u02dc", "'"),
        ("\u00e2\u20ac\u00a6", "..."),
        ("\u00e2\u20ac\u02c6", '"'),
    ]
    for a, b in pairs:
        text = text.replace(a, b)

    # Explicit mojibake strings (as typed when UTF-8 -> Latin-1)
    text = text.replace("->", "->")
    text = text.replace("<-", "<-")
    text = text.replace("-", " - ")
    text = text.replace("-", "-")
    text = text.replace(""", '"')
    text = text.replace(""", '"')
    text = text.replace("'", "'")
    text = text.replace("'", "'")
    text = text.replace("...", "...")

    # Broad mop-up of remaining '' mojibake clusters
    text = re.sub(r"-", "-", text)
    text = re.sub(r"->", "->", text)
    text = re.sub(r"", "", text)

    # README HTML entities that looked broken
    text = text.replace("**< ~80-120 KB**", "**< ~80-120 KB**")
    text = text.replace("**< 12 KB**", "**< 12 KB**")
    text = text.replace("<", "<")
    text = text.replace(">", ">")
    return text


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    n = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in EXTS and path.name not in {"LICENSE", "CHANGELOG.md", "SECURITY.md"}:
            continue
        if any(x in path.parts for x in (".git", "__pycache__", ".venv")):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fixed = clean(text)
        if fixed != text:
            path.write_text(fixed, encoding="utf-8", newline="\n")
            n += 1
            print("fixed", path.relative_to(root))
    print("updated", n)

    # report leftovers
    for path in root.rglob("*.md"):
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            if "" in line or "\u2192" in line or "\u2014" in line:
                print(f"LEFT {path.relative_to(root)}:{i}: {line[:140]}")


if __name__ == "__main__":
    main()
