"""Render a simple HTML RF personality graph from history JSONL."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def build_personality_html(history_path: Path, out_html: Path) -> Path:
    history_path = Path(history_path)
    out_html = Path(out_html)
    rows: list[dict[str, Any]] = []
    if history_path.exists():
        for line in history_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # series: freq -> list of (ts, pulses)
    series: dict[int, list[tuple[float, int]]] = defaultdict(list)
    for r in rows:
        if r.get("kind") == "survey":
            ts = float(r.get("ts") or 0)
            for s in r.get("samples") or []:
                if s.get("ok") and s.get("pulses") is not None:
                    series[int(s["freq_hz"])].append((ts, int(s["pulses"])))
        elif r.get("kind") == "sample" and r.get("ok") and r.get("pulses") is not None:
            series[int(r["freq_hz"])].append((float(r.get("ts") or 0), int(r["pulses"])))

    # simple bar chart of latest survey
    latest = next((r for r in reversed(rows) if r.get("kind") == "survey"), None)
    bars = ""
    if latest:
        samples = [s for s in (latest.get("samples") or []) if s.get("ok")]
        max_p = max((int(s.get("pulses") or 0) for s in samples), default=1) or 1
        for s in samples:
            p = int(s.get("pulses") or 0)
            mhz = int(s["freq_hz"]) / 1e6
            w = int(100 * p / max_p)
            bars += (
                f'<div class="row"><span class="mhz">{mhz:.3f}</span>'
                f'<div class="bar" style="width:{w}%"></div>'
                f'<span class="p">{p}</span></div>\n'
            )

    series_json = json.dumps(
        {str(k): v for k, v in sorted(series.items())},
        ensure_ascii=True,
    )

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<title>GrokLink RF personality</title>
<style>
body{{font-family:system-ui,sans-serif;background:#0b1020;color:#e8eefc;margin:2rem}}
h1{{font-weight:600}} .row{{display:flex;align-items:center;margin:.35rem 0;gap:.5rem}}
.mhz{{width:5.5rem;font-variant-numeric:tabular-nums}}
.bar{{height:1rem;background:linear-gradient(90deg,#39c,#6f6);border-radius:4px}}
.p{{width:4rem;text-align:right}}
.note{{opacity:.75;max-width:40rem}}
</style></head><body>
<h1>GrokLink lab RF personality</h1>
<p class="note">Latest survey pulse edges (not decoded packets). Educational lab use only.</p>
{bars or "<p>No survey data yet. Run: groklink hw spectrum --history ...</p>"}
<script type="application/json" id="series">{series_json}</script>
</body></html>
"""
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")
    return out_html
