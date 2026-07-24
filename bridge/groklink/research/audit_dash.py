"""Build a local HTML dashboard from audit JSONL text."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def parse_audit_lines(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"raw": line})
    return rows


def build_audit_html(rows: list[dict[str, Any]], out_html: Path) -> Path:
    out_html = Path(out_html)
    trs = []
    for r in rows[-500:]:
        if "raw" in r:
            trs.append(f"<tr><td colspan=5><code>{_esc(r['raw'])}</code></td></tr>")
            continue
        trs.append(
            "<tr>"
            f"<td>{_esc(str(r.get('ts','')))}</td>"
            f"<td>{_esc(str(r.get('actor','')))}</td>"
            f"<td>{_esc(str(r.get('action','')))}</td>"
            f"<td>{_esc(str(r.get('result','')))}</td>"
            f"<td>{_esc(str(r.get('reason', r.get('detail',''))))}</td>"
            "</tr>"
        )
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/><title>GrokLink audit</title>
<style>
body{{font-family:system-ui,sans-serif;background:#111;color:#eee;margin:1.5rem}}
table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #333;padding:.4rem;font-size:13px}}
th{{background:#222;text-align:left}} code{{font-size:12px}}
</style></head><body>
<h1>GrokLink audit log</h1>
<p>Educational lab integrity view. Last {min(500,len(rows))} rows.</p>
<table><thead><tr><th>ts</th><th>actor</th><th>action</th><th>result</th><th>detail</th></tr></thead>
<tbody>
{''.join(trs)}
</tbody></table>
</body></html>
"""
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")
    return out_html


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
