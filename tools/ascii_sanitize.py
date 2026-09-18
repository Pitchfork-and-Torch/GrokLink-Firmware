#!/usr/bin/env python3
"""Replace fancy Unicode punctuation with ASCII for GitHub rendering safety."""
from pathlib import Path

REPLACES = {
    "\u2192": "->",  # right arrow
    "\u2190": "<-",  # left arrow
    "\u21d2": "=>",  # double arrow
    "\u2014": " - ",  # em dash
    "\u2013": "-",  # en dash
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2026": "...",
    "\u00d7": "x",
    "\u2264": "<=",
    "\u2265": ">=",
    "\u00b7": "-",
    "\u2705": "[OK]",
    # Common UTF-8 mis-decoded as Windows-1252
    "\u00e2\u20ac\u2122": "'",  # not always exact
}

# Mojibake sequences as they appear when UTF-8 is read as Latin-1 then saved
MOJI = {
    "->": "->",
    "<-": "<-",
    "-": " - ",
    "-": "-",
    """: '"',
    """: '"',
    "'": "'",
    "'": "'",
    "...": "...",
}

EXTS = {".md", ".txt", ".py", ".ps1", ".sh", ".c", ".h", ".json", ".toml", ".fam", ".proto"}
SKIP = {".git", "__pycache__", "egg-info", ".venv", "node_modules"}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    updated = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP or part.endswith(".egg-info") for part in path.parts):
            continue
        if path.suffix.lower() not in EXTS and path.name not in {
            "LICENSE",
            "CHANGELOG",
            "SECURITY",
            "CHANGELOG.md",
            "SECURITY.md",
        }:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        orig = text
        for a, b in REPLACES.items():
            text = text.replace(a, b)
        for a, b in MOJI.items():
            text = text.replace(a, b)
        if text != orig:
            path.write_text(text, encoding="utf-8", newline="\n")
            updated += 1
            print(f"fixed {path.relative_to(root)}")

    left = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in EXTS:
            continue
        if any(part in SKIP for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "\u2192" in text or "\u2190" in text or "-> in text:
            left.append(str(path.relative_to(root)))
    print(f"updated={updated}")
    print(f"remaining_arrows={left}")


if __name__ == "__main__":
    main()
