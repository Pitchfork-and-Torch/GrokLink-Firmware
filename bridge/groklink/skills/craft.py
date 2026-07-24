"""
Skill crafting  -  analyze capture logs and emit a new skill package.

In production, this is where terminal Grok / an LLM is called to propose
decoders and mission steps. Here we provide a deterministic scaffold that
Grok can fill, plus a hook for external model completion.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class CraftResult:
    skill_id: str
    out_dir: Path
    summary: str
    files: list[str]


def _slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")[:32] or "crafted_skill"


def analyze_log_lines(lines: list[str]) -> dict[str, Any]:
    """Lightweight heuristic analysis (no ML required)."""
    pulses = 0
    freqs: list[int] = []
    actions: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            actions.append("raw_text")
            continue
        actions.append(
            str(obj.get("action") or obj.get("method") or obj.get("op") or obj.get("kind") or "event")
        )
        meta = obj.get("json_meta") or obj.get("meta") or {}
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except json.JSONDecodeError:
                meta = {}
        if isinstance(meta, dict) and "pulses" in meta:
            try:
                pulses += int(meta["pulses"])
            except (TypeError, ValueError):
                pass
        if "freq_hz" in obj and obj.get("freq_hz") is not None:
            try:
                freqs.append(int(obj["freq_hz"]))
            except (TypeError, ValueError):
                pass

    # Prefer freq with highest pulse sum when available, else modal freq
    dominant_freq = max(set(freqs), key=freqs.count) if freqs else 433920000
    return {
        "event_count": len(lines),
        "pulse_total": pulses,
        "dominant_freq_hz": dominant_freq,
        "action_hist": {a: actions.count(a) for a in set(actions)},
        "suggested_risk": "passive_rx",
    }


def craft_skill_from_log(
    log_path: Path,
    out_dir: Path,
    skill_name: Optional[str] = None,
    *,
    llm_notes: Optional[str] = None,
) -> CraftResult:
    """
    Generate a skill folder ready for SD deploy under /ext/groklink/skills/<id>/.

    llm_notes: optional free-text from terminal Grok describing protocol hints.
    """
    text = log_path.read_text(encoding="utf-8", errors="replace")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    analysis = analyze_log_lines(lines)

    skill_id = _slug(skill_name or f"crafted_{analysis['dominant_freq_hz']}")
    dest = out_dir / skill_id
    dest.mkdir(parents=True, exist_ok=True)

    manifest = {
        "id": skill_id,
        "version": "0.1.0",
        "description": f"Auto-crafted from {log_path.name}",
        "risk_class": analysis["suggested_risk"],
        "hw": ["subghz"],
        "entry": "rules",
        "has_fap": False,
        "educational": True,
        "source_log": str(log_path.name),
        "analysis": analysis,
        "llm_notes": llm_notes or "",
    }
    rules = {
        "params": {
            "default_freq_hz": analysis["dominant_freq_hz"],
            # Short RX keeps USB control plane responsive (prefer 1s lab windows)
            "default_duration_ms": 1000,
        },
        "on_run": [
            {
                "op": "subghz_rx",
                "freq_hz": analysis["dominant_freq_hz"],
                "duration_ms": 1000,
            },
            {"op": "log", "message": f"crafted skill {skill_id} complete"},
        ],
    }
    protocol = {
        "type": "heuristic",
        "freq_hz": analysis["dominant_freq_hz"],
        "notes": llm_notes
        or "Replace with decoder details after Grok analysis. No TX by default.",
        "tx_enabled": False,
    }
    readme = f"""# Skill `{skill_id}`

Crafted by GrokLink skill craft.

## Analysis
```json
{json.dumps(analysis, indent=2)}
```

## Deploy
Copy this folder to Flipper SD:
`/ext/groklink/skills/{skill_id}/`

Then: `groklink skill reload` or reboot agent.

## Safety
Default is **passive RX only**. Do not enable TX without authorization and confirm tokens.
"""

    files = {
        "manifest.json": json.dumps(manifest, indent=2) + "\n",
        "rules.json": json.dumps(rules, indent=2) + "\n",
        "protocol.json": json.dumps(protocol, indent=2) + "\n",
        "README.md": readme,
    }
    written: list[str] = []
    for name, content in files.items():
        p = dest / name
        p.write_text(content, encoding="utf-8")
        written.append(str(p))

    # Optional FAP C stub for ufbt users
    fap_stub = dest / "fap_stub.c"
    fap_stub.write_text(
        f"""/* Auto-generated FAP stub for skill {skill_id}
 * Build with ufbt into applications_user when you need a UI.
 * v1.0 skills can run as rules-only without a FAP.
 */
#include <furi.h>
/* TODO: implement app for {skill_id} */
int32_t {skill_id}_app(void* p) {{
    UNUSED(p);
    return 0;
}}
""",
        encoding="utf-8",
    )
    written.append(str(fap_stub))

    summary = (
        f"Crafted skill '{skill_id}' freq={analysis['dominant_freq_hz']} "
        f"events={analysis['event_count']} risk={analysis['suggested_risk']}"
    )
    return CraftResult(skill_id=skill_id, out_dir=dest, summary=summary, files=written)


def deploy_skill_to_sd_tree(skill_dir: Path, sd_groklink_root: Path) -> Path:
    """Copy skill into an SD card mirror tree (offline deploy)."""
    import shutil

    target = sd_groklink_root / "skills" / skill_dir.name
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(skill_dir, target)
    return target
