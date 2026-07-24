"""Detect band activity deltas vs historical baseline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class BandDelta:
    freq_hz: int
    baseline: float
    current: Optional[int]
    ratio: Optional[float]
    flag: str  # quiet | normal | hot | missing


@dataclass
class DeltaReport:
    bands: list[BandDelta]
    summary: str

    def as_dict(self) -> dict:
        return {
            "summary": self.summary,
            "bands": [
                {
                    "freq_hz": b.freq_hz,
                    "baseline": b.baseline,
                    "current": b.current,
                    "ratio": b.ratio,
                    "flag": b.flag,
                }
                for b in self.bands
            ],
        }


def detect_deltas(
    current_samples: list[dict],
    baseline: dict[int, float],
    *,
    hot_ratio: float = 2.5,
    quiet_ratio: float = 0.35,
) -> DeltaReport:
    bands: list[BandDelta] = []
    hot = 0
    quiet = 0
    for sample in current_samples:
        f = int(sample.get("freq_hz") or 0)
        p = sample.get("pulses")
        base = baseline.get(f, 0.0)
        if p is None or not sample.get("ok", True):
            bands.append(BandDelta(f, base, None, None, "missing"))
            continue
        p = int(p)
        if base <= 0:
            ratio = None
            flag = "hot" if p > 50 else "normal"
        else:
            ratio = p / base
            if ratio >= hot_ratio:
                flag = "hot"
                hot += 1
            elif ratio <= quiet_ratio:
                flag = "quiet"
                quiet += 1
            else:
                flag = "normal"
        bands.append(BandDelta(f, base, p, ratio, flag))

    if not baseline:
        summary = "No baseline yet — this survey becomes the seed history."
    elif hot or quiet:
        summary = f"Delta: {hot} hot band(s), {quiet} quiet band(s) vs baseline."
    else:
        summary = "No large deltas vs baseline."
    return DeltaReport(bands=bands, summary=summary)
