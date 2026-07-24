"""Replay public jsonl captures into analysis without hardware."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def replay_jsonl(path: Path) -> dict[str, Any]:
    path = Path(path)
    pulses_by_freq: dict[int, list[int]] = defaultdict(list)
    methods: dict[str, int] = defaultdict(int)
    events = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        events += 1
        m = obj.get("method") or obj.get("tag") or obj.get("kind") or "event"
        methods[str(m)] += 1
        meta = obj.get("json_meta")
        pulses = obj.get("pulses")
        if pulses is None and isinstance(meta, str):
            try:
                pulses = json.loads(meta).get("pulses")
            except json.JSONDecodeError:
                pulses = None
        freq = obj.get("freq_hz")
        if freq is not None and pulses is not None:
            pulses_by_freq[int(freq)].append(int(pulses))

    summary = {
        "file": path.name,
        "events": events,
        "methods": dict(methods),
        "freq_pulse_stats": {
            str(f): {
                "n": len(vals),
                "min": min(vals),
                "max": max(vals),
                "avg": sum(vals) / len(vals),
            }
            for f, vals in sorted(pulses_by_freq.items())
            if vals
        },
    }
    return summary
