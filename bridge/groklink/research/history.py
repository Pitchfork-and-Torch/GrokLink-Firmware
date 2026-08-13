"""Append-only RF sample history (JSONL) for delta detection."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional


class RfHistoryStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append_survey(self, survey: dict[str, Any], *, label: str = "") -> None:
        row = {
            "kind": "survey",
            "ts": time.time(),
            "label": label,
            **survey,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")

    def append_sample(
        self,
        freq_hz: int,
        pulses: Optional[int],
        *,
        duration_ms: int = 400,
        ok: bool = True,
        label: str = "",
    ) -> None:
        row = {
            "kind": "sample",
            "ts": time.time(),
            "label": label,
            "freq_hz": freq_hz,
            "pulses": pulses,
            "duration_ms": duration_ms,
            "ok": ok,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")

    def load_rows(self, limit: int = 5000) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows[-limit:]

    def baseline_by_freq(self, exclude_last_n_surveys: int = 1) -> dict[int, float]:
        """Median pulses per freq from historical survey samples (exclude recent)."""
        rows = self.load_rows()
        surveys = [r for r in rows if r.get("kind") == "survey"]
        if exclude_last_n_surveys > 0 and len(surveys) > exclude_last_n_surveys:
            surveys = surveys[:-exclude_last_n_surveys]
        buckets: dict[int, list[int]] = {}
        for s in surveys:
            for sample in s.get("samples") or []:
                if not sample.get("ok"):
                    continue
                f = sample.get("freq_hz")
                p = sample.get("pulses")
                if f is None or p is None:
                    continue
                buckets.setdefault(int(f), []).append(int(p))
        out: dict[int, float] = {}
        for f, vals in buckets.items():
            vals = sorted(vals)
            mid = len(vals) // 2
            out[f] = float(vals[mid]) if vals else 0.0
        return out
