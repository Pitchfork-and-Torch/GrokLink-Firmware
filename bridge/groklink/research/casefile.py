"""Lab casefile manifests (hypothesis + integrity)."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def create_casefile(
    case_dir: Path,
    *,
    title: str,
    hypothesis: str,
    freqs_hz: Optional[list[int]] = None,
    notes: str = "",
    capture_path: Optional[Path] = None,
    operator_id: str = "",
    engagement_id: str = "",
    site_label: str = "",
    use_engagement_file: bool = True,
) -> Path:
    case_dir = Path(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)
    capture_sha = ""
    capture_name = ""
    if capture_path and Path(capture_path).exists():
        capture_name = Path(capture_path).name
        dest = case_dir / capture_name
        if Path(capture_path).resolve() != dest.resolve():
            dest.write_bytes(Path(capture_path).read_bytes())
        capture_sha = sha256_file(dest)

    op = operator_id
    eng = engagement_id
    site = site_label
    if use_engagement_file:
        try:
            from groklink.research.engagement import load_engagement

            e = load_engagement()
            op = op or str(e.get("operator_id") or "")
            eng = eng or str(e.get("engagement_id") or "")
            site = site or str(e.get("site_label") or "")
        except Exception:
            pass

    manifest = {
        "title": title,
        "hypothesis": hypothesis,
        "created_ts": time.time(),
        "freqs_hz": freqs_hz or [],
        "notes": notes,
        "capture": capture_name,
        "capture_sha256": capture_sha,
        "authorized_lab": True,
        "operator_id": op,
        "engagement_id": eng,
        "site_label": site,
        "not_medical_device": True,
        "disclaimer": (
            "Educational authorized use only. Not a medical device. "
            "Not for diagnosis, treatment, or patient-connected care."
        ),
    }
    path = case_dir / "CASEFILE.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path
