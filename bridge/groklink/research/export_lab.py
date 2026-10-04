"""Export lab history / case data to CSV, JSON bundle, experimental FHIR-shaped JSON.

NOT a medical device. Exports are research artifacts only - never use for care.
Experimental FHIR Observation bundles are deliberately non-clinical and unlabeled
as real patient Observations.
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any, Optional

from groklink.research.engagement import DISCLAIMER, load_engagement, stamp_record
from groklink.research.history import RfHistoryStore


def history_samples_flat(history_path: Path, limit: int = 5000) -> list[dict[str, Any]]:
    store = RfHistoryStore(history_path)
    rows = store.load_rows(limit=limit)
    flat: list[dict[str, Any]] = []
    for r in rows:
        ts = r.get("ts")
        label = r.get("label") or ""
        if r.get("kind") == "survey":
            for s in r.get("samples") or []:
                flat.append(
                    {
                        "ts": ts,
                        "label": label,
                        "kind": "survey_sample",
                        "freq_hz": s.get("freq_hz"),
                        "pulses": s.get("pulses"),
                        "ok": s.get("ok", True),
                        "duration_ms": s.get("duration_ms"),
                    }
                )
        elif r.get("kind") == "sample":
            flat.append(
                {
                    "ts": ts,
                    "label": label,
                    "kind": "sample",
                    "freq_hz": r.get("freq_hz"),
                    "pulses": r.get("pulses"),
                    "ok": r.get("ok", True),
                    "duration_ms": r.get("duration_ms"),
                }
            )
    return flat


def export_history_csv(
    history_path: Path,
    out_csv: Path,
    *,
    engagement: Optional[dict[str, Any]] = None,
) -> Path:
    eng = engagement if engagement is not None else load_engagement()
    rows = history_samples_flat(history_path)
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "ts",
        "label",
        "kind",
        "freq_hz",
        "pulses",
        "ok",
        "duration_ms",
        "operator_id",
        "engagement_id",
        "site_label",
        "not_medical_device",
    ]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            stamped = stamp_record(row, eng)
            w.writerow({k: stamped.get(k, "") for k in fields})
    return out_csv


def export_history_json(
    history_path: Path,
    out_json: Path,
    *,
    engagement: Optional[dict[str, Any]] = None,
) -> Path:
    eng = engagement if engagement is not None else load_engagement()
    payload = stamp_record(
        {
            "kind": "groklink_history_export",
            "source": str(history_path),
            "exported_ts": time.time(),
            "samples": history_samples_flat(history_path),
        },
        eng,
    )
    out_json = Path(out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out_json


def export_experimental_fhir_bundle(
    history_path: Path,
    out_json: Path,
    *,
    engagement: Optional[dict[str, Any]] = None,
    max_obs: int = 50,
) -> Path:
    """Write a research-only FHIR-shaped Bundle of Observations.

    Explicitly not clinical: category research, no Patient resource, device is
    research tool. Do not submit to EHR without clinical review and redesign.
    """
    eng = engagement if engagement is not None else load_engagement()
    samples = history_samples_flat(history_path)[:max_obs]
    entries = []
    for i, s in enumerate(samples):
        freq = s.get("freq_hz") or 0
        pulses = s.get("pulses")
        if pulses is None:
            continue
        obs = {
            "resourceType": "Observation",
            "id": f"groklink-rf-{i}",
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "survey",
                            "display": "Survey",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "https://example.local/groklink",
                        "code": "subghz-pulse-count",
                        "display": "SubGHz pulse edge count (research)",
                    }
                ],
                "text": f"Passive SubGHz edges at {freq} Hz (research only)",
            },
            "valueInteger": int(pulses),
            "note": [
                {
                    "text": DISCLAIMER
                    + f" engagement_id={eng.get('engagement_id','')} operator_id={eng.get('operator_id','')}"
                }
            ],
            "device": {
                "display": "GrokLink research appliance (not a medical device)"
            },
            "extension": [
                {
                    "url": "https://example.local/groklink/freq_hz",
                    "valueInteger": int(freq),
                },
                {
                    "url": "https://example.local/groklink/not_medical_device",
                    "valueBoolean": True,
                },
            ],
        }
        if s.get("ts"):
            # FHIR instant-ish
            obs["effectiveDateTime"] = time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(s["ts"]))
            )
        entries.append({"resource": obs})

    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "meta": {
            "tag": [
                {
                    "system": "https://example.local/groklink",
                    "code": "research-only",
                    "display": "Not for clinical use",
                }
            ]
        },
        "entry": entries,
        "extension": [
            {
                "url": "https://example.local/groklink/disclaimer",
                "valueString": DISCLAIMER,
            },
            {
                "url": "https://example.local/groklink/engagement_id",
                "valueString": str(eng.get("engagement_id") or ""),
            },
        ],
    }
    out_json = Path(out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    return out_json
