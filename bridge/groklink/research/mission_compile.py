"""Compile safe passive missions (log + short RX only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def compile_passive_mission(
    mission_id: str,
    *,
    freq_hz: int = 433_920_000,
    duration_ms: int = 400,
    name: str | None = None,
) -> dict[str, Any]:
    duration_ms = max(100, min(int(duration_ms), 1000))
    return {
        "id": mission_id,
        "name": name or f"Passive {freq_hz / 1e6:.3f} MHz",
        "version": 1,
        "autonomous": False,
        "safety": {"max_risk_class": "passive_rx", "require_confirm": False},
        "steps": [
            {"op": "log", "message": f"start {mission_id}"},
            {
                "op": "subghz_rx",
                "freq_hz": int(freq_hz),
                "duration_ms": duration_ms,
                "modulation": "auto",
            },
            {"op": "log", "message": f"done {mission_id}"},
        ],
        "compiler": "groklink.research.mission_compile",
        "notes": "PC-compiled; autonomous=false; single short RX only.",
    }


def write_mission(out_dir: Path, mission: dict[str, Any]) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    mid = mission["id"]
    path = out_dir / f"{mid}.mission.json"
    path.write_text(json.dumps(mission, indent=2) + "\n", encoding="utf-8")
    return path
