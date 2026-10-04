"""Local metrics sink: append JSONL metrics for lab time series."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class LocalMetrics:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, name: str, value: float, **tags: Any) -> None:
        row = {"ts": time.time(), "metric": name, "value": value, "tags": tags}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")

    def from_survey(self, survey: dict[str, Any], label: str = "") -> None:
        for s in survey.get("samples") or []:
            if s.get("ok") and s.get("pulses") is not None:
                self.write(
                    "rf.pulses",
                    float(s["pulses"]),
                    freq_hz=s.get("freq_hz"),
                    label=label,
                )
