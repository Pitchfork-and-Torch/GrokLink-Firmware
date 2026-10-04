from pathlib import Path
from groklink.research.mission_compile import compile_passive_mission, write_mission
from groklink.research.casefile import create_casefile, sha256_file
from groklink.research.sim_replay import replay_jsonl
from groklink.research.graph import build_personality_html
from groklink.research.audit_dash import parse_audit_lines, build_audit_html
from groklink.research.heartbeat import run_heartbeat
from groklink.research.sd_deploy import deploy_skills_tree
from groklink.research.metrics import LocalMetrics
import json


def test_mission_compile(tmp_path: Path):
    m = compile_passive_mission("t1", freq_hz=433920000, duration_ms=400)
    assert m["autonomous"] is False
    p = write_mission(tmp_path, m)
    assert p.exists()


def test_casefile(tmp_path: Path):
    cap = tmp_path / "c.jsonl"
    cap.write_text('{"ok":true}\n', encoding="utf-8")
    path = create_casefile(tmp_path / "case1", title="t", hypothesis="h", capture_path=cap)
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["capture_sha256"] == sha256_file(tmp_path / "case1" / "c.jsonl")


def test_replay():
    # use in-memory path from repo examples if present
    p = Path(__file__).resolve().parents[2] / "examples" / "leisure_explore_public.jsonl"
    if p.exists():
        s = replay_jsonl(p)
        assert s["events"] > 0


def test_graph_and_audit(tmp_path: Path):
    hist = tmp_path / "h.jsonl"
    hist.write_text(
        json.dumps(
            {
                "kind": "survey",
                "ts": 1,
                "samples": [{"freq_hz": 433920000, "pulses": 10, "ok": True}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    html = build_personality_html(hist, tmp_path / "g.html")
    assert html.exists()
    rows = parse_audit_lines('{"ts":1,"actor":"rpc","action":"status","result":"allow"}\n')
    path = build_audit_html(rows, tmp_path / "a.html")
    assert path.exists()


def test_heartbeat(tmp_path: Path):
    row = run_heartbeat(lambda: {"ok": True, "agent_running": True, "firmware_version": "x"}, log_path=tmp_path / "hb.jsonl")
    assert row["ok"] is True


def test_deploy_and_metrics(tmp_path: Path):
    src = tmp_path / "skills" / "s1"
    src.mkdir(parents=True)
    (src / "manifest.json").write_text("{}", encoding="utf-8")
    sd = tmp_path / "sd"
    deployed = deploy_skills_tree(tmp_path / "skills", sd)
    assert "s1" in deployed
    m = LocalMetrics(tmp_path / "m.jsonl")
    m.from_survey({"samples": [{"ok": True, "pulses": 3, "freq_hz": 1}]}, label="t")
    assert (tmp_path / "m.jsonl").exists()
