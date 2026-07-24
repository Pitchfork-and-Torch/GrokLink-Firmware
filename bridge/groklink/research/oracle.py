"""Contrast oracle: rank hottest bands from RF history."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from groklink.research.history import RfHistoryStore


def rank_hottest(history_path: Path, *, last_n_surveys: int = 5) -> dict[str, Any]:
    store = RfHistoryStore(history_path)
    rows = [r for r in store.load_rows() if r.get("kind") == "survey"]
    if not rows:
        return {"ok": False, "message": "no surveys in history", "ranking": []}
    recent = rows[-last_n_surveys:]
    totals: dict[int, list[int]] = {}
    for survey in recent:
        for s in survey.get("samples") or []:
            if not s.get("ok") or s.get("pulses") is None:
                continue
            f = int(s["freq_hz"])
            totals.setdefault(f, []).append(int(s["pulses"]))
    ranking = []
    for f, vals in totals.items():
        avg = sum(vals) / len(vals)
        ranking.append(
            {
                "freq_hz": f,
                "mhz": round(f / 1e6, 3),
                "avg_pulses": round(avg, 1),
                "samples": len(vals),
                "max_pulses": max(vals),
            }
        )
    ranking.sort(key=lambda x: x["avg_pulses"], reverse=True)
    next_probe = ranking[0]["freq_hz"] if ranking else 433_920_000
    return {
        "ok": True,
        "surveys_used": len(recent),
        "ranking": ranking,
        "next_probe_hz": next_probe,
        "summary": (
            f"Hottest avg: {ranking[0]['mhz']} MHz ({ranking[0]['avg_pulses']} pulses)"
            if ranking
            else "empty"
        ),
    }
