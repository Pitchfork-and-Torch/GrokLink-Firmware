from pathlib import Path
from groklink.research.stream import parse_stream_line, iter_stream_events
from groklink.research.oracle import rank_hottest
from groklink.research.vault import ensure_vault
from groklink.research.curriculum import curriculum_state, mark_lesson
from groklink.research.metrics_html import build_metrics_html
from groklink.research.history import RfHistoryStore
import json


def test_stream_parse():
    ev = parse_stream_line('GROKSTREAM:{"kind":"subghz_rx_done","freq_hz":1,"pulses":2}')
    assert ev and ev["kind"] == "subghz_rx_done"
    assert list(iter_stream_events("noise\nGROKSTREAM:{\"kind\":\"x\"}\n"))


def test_oracle_and_vault(tmp_path: Path):
    h = tmp_path / "h.jsonl"
    store = RfHistoryStore(h)
    store.append_survey(
        {"samples": [{"freq_hz": 433920000, "pulses": 100, "ok": True}]},
        label="a",
    )
    store.append_survey(
        {"samples": [{"freq_hz": 433920000, "pulses": 200, "ok": True}]},
        label="b",
    )
    r = rank_hottest(h)
    assert r["ok"]
    v = ensure_vault(tmp_path / "vault")
    assert (v / "cases").is_dir()


def test_curriculum_and_metrics(tmp_path: Path):
    p = tmp_path / "prog.txt"
    mark_lesson(p, 1)
    st = curriculum_state(p)
    assert st["lessons"][0]["done"] is True
    m = tmp_path / "m.jsonl"
    m.write_text(
        json.dumps({"ts": 1, "metric": "rf.pulses", "value": 5, "tags": {"freq_hz": 433920000}})
        + "\n",
        encoding="utf-8",
    )
    html = build_metrics_html(m, tmp_path / "m.html")
    assert html.exists()
