"""PC-side RF anomaly scoring from history baselines.

Never triggers TX. Research/lab use only. Not a medical device.
Scores are heuristic pulse-edge ratios, not protocol or threat IDs.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from groklink.research.delta import detect_deltas
from groklink.research.engagement import load_engagement, stamp_record
from groklink.research.history import RfHistoryStore


def score_anomaly(
    history_path: Path,
    *,
    hot_ratio: float = 2.5,
    quiet_ratio: float = 0.35,
    engagement: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Compare last survey in history to prior baseline; emit risk-ish score 0-100.

    score is for lab prioritization only - not clinical, not security certainty.
    """
    store = RfHistoryStore(history_path)
    rows = store.load_rows()
    surveys = [r for r in rows if r.get("kind") == "survey"]
    if not surveys:
        return stamp_record(
            {
                "ok": False,
                "error": "no surveys in history",
                "score": 0,
                "flags": [],
                "never_auto_tx": True,
            },
            engagement,
        )

    latest = surveys[-1]
    samples = latest.get("samples") or []
    baseline = store.baseline_by_freq(exclude_last_n_surveys=1)
    report = detect_deltas(
        samples,
        baseline,
        hot_ratio=hot_ratio,
        quiet_ratio=quiet_ratio,
    )

    hot = [b for b in report.bands if b.flag == "hot"]
    quiet = [b for b in report.bands if b.flag == "quiet"]
    # Simple score: each hot +20, each quiet +5, cap 100
    score = min(100, len(hot) * 20 + len(quiet) * 5)

    flags = []
    for b in report.bands:
        if b.flag in ("hot", "quiet"):
            flags.append(
                {
                    "freq_hz": b.freq_hz,
                    "flag": b.flag,
                    "baseline": b.baseline,
                    "current": b.current,
                    "ratio": b.ratio,
                }
            )

    return stamp_record(
        {
            "ok": True,
            "score": score,
            "summary": report.summary,
            "flags": flags,
            "hot_count": len(hot),
            "quiet_count": len(quiet),
            "baseline_bands": len(baseline),
            "latest_ts": latest.get("ts"),
            "never_auto_tx": True,
            "not_threat_intel": True,
            "disclaimer": (
                "Heuristic pulse-edge anomaly for authorized lab use only. "
                "Not protocol ID, not attack detection, not a medical device."
            ),
            "scored_ts": time.time(),
        },
        engagement if engagement is not None else load_engagement(),
    )


def write_anomaly_report(history_path: Path, out_json: Path, **kwargs: Any) -> Path:
    result = score_anomaly(history_path, **kwargs)
    out_json = Path(out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return out_json
