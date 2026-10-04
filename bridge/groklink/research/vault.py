"""Create private vault layout under ~/.groklink/vault (not for git)."""

from __future__ import annotations

from pathlib import Path


def ensure_vault(root: Path | None = None) -> Path:
    root = Path(root or (Path.home() / ".groklink" / "vault"))
    for sub in ("cases", "history", "audit", "metrics", "raw"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    readme = root / "README.txt"
    if not readme.exists():
        readme.write_text(
            "Private GrokLink vault. Do not commit to public GitHub.\n"
            "cases/ history/ audit/ metrics/ raw/\n",
            encoding="utf-8",
        )
    return root
