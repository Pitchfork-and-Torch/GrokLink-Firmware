"""Phase 2 lab exports / engagement / anomaly (no hardware)."""

from __future__ import annotations

import json
from pathlib import Path

from groklink.research.anomaly import score_anomaly
from groklink.research.casefile import create_casefile
from groklink.research.engagement import save_engagement, stamp_audit_jsonl, stamp_record
from groklink.research.export_lab import (
    export_experimental_fhir_bundle,
    export_history_csv,
    export_history_json,
)


def test_engagement_stamp(tmp_path: Path):
    p = tmp_path / "eng.json"
    save_engagement(
        operator_id="op-lab",
        engagement_id="eng-001",
        site_label="bench-a",
        roe_ack=True,
        path=p,
    )
    from groklink.research.engagement import load_engagement

    eng = load_engagement(p)
    row = stamp_record({"action": "status", "result": "allow"}, eng)
    assert row["operator_id"] == "op-lab"
    assert row["engagement_id"] == "eng-001"
    assert row["not_medical_device"] is True


def test_stamp_audit_and_casefile(tmp_path: Path):
    eng_path = tmp_path / "eng.json"
    save_engagement(operator_id="o1", engagement_id="e1", path=eng_path)
    # monkey via env-less: pass engagement into stamp
    from groklink.research.engagement import load_engagement

    eng = load_engagement(eng_path)
    audit_in = tmp_path / "a.jsonl"
    audit_in.write_text(
        '{"ts":1,"actor":"rpc","action":"status","result":"allow"}\nnoise\n',
        encoding="utf-8",
    )
    audit_out = tmp_path / "a_stamped.jsonl"
    # stamp_audit uses default engagement file - inject by writing DEFAULT
    # Use direct API with engagement arg via stamp_record path:
    meta = stamp_audit_jsonl(audit_in, audit_out, engagement=eng)
    assert meta["stamped_rows"] == 1
    line = audit_out.read_text(encoding="utf-8").strip()
    data = json.loads(line)
    assert data["engagement_id"] == "e1"

    # casefile with explicit ids
    cf = create_casefile(
        tmp_path / "case",
        title="t",
        hypothesis="h",
        operator_id="o1",
        engagement_id="e1",
        use_engagement_file=False,
    )
    manifest = json.loads(cf.read_text(encoding="utf-8"))
    assert manifest["engagement_id"] == "e1"
    assert manifest["not_medical_device"] is True


def test_export_and_anomaly(tmp_path: Path):
    hist = tmp_path / "h.jsonl"
    # baseline survey + hot survey
    rows = [
        {
            "kind": "survey",
            "ts": 1.0,
            "samples": [{"freq_hz": 433920000, "pulses": 100, "ok": True}],
        },
        {
            "kind": "survey",
            "ts": 2.0,
            "samples": [{"freq_hz": 433920000, "pulses": 400, "ok": True}],
        },
    ]
    hist.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    csv_path = export_history_csv(hist, tmp_path / "out.csv")
    assert csv_path.exists()
    text = csv_path.read_text(encoding="utf-8")
    assert "433920000" in text
    assert "not_medical_device" in text

    jpath = export_history_json(hist, tmp_path / "out.json")
    assert jpath.exists()

    fpath = export_experimental_fhir_bundle(hist, tmp_path / "fhir.json")
    bundle = json.loads(fpath.read_text(encoding="utf-8"))
    assert bundle["resourceType"] == "Bundle"
    assert bundle["entry"]
    assert "research-only" in json.dumps(bundle)

    report = score_anomaly(hist)
    assert report["ok"] is True
    assert report["never_auto_tx"] is True
    assert report["score"] >= 0
