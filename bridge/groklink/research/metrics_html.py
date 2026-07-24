"""HTML time-series-ish view from local metrics JSONL."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


def build_metrics_html(metrics_path: Path, out_html: Path) -> Path:
    rows = []
    if metrics_path.exists():
        for line in metrics_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    by_freq: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for r in rows:
        if r.get("metric") != "rf.pulses":
            continue
        tags = r.get("tags") or {}
        f = str(tags.get("freq_hz", "?"))
        by_freq[f].append((float(r.get("ts") or 0), float(r.get("value") or 0)))

    blocks = []
    for f, pts in sorted(by_freq.items(), key=lambda x: x[0]):
        latest = pts[-1][1] if pts else 0
        blocks.append(f"<div class='card'><h3>{int(f)/1e6 if f.isdigit() else f} MHz</h3><p>n={len(pts)} latest={latest:.0f}</p></div>")

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"/><title>GrokLink metrics</title>
<style>body{{font-family:system-ui;background:#0d1117;color:#e6edf3;margin:2rem}}
.card{{background:#161b22;padding:1rem;margin:.5rem 0;border-radius:8px;border:1px solid #30363d}}
</style></head><body><h1>Local RF metrics</h1>
{''.join(blocks) or '<p>No metrics yet. Run spectrum with metrics writer.</p>'}
</body></html>"""
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")
    return out_html
