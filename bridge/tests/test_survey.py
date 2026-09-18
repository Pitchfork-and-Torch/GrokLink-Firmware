from groklink.research.survey import LabBandSurvey, CircuitBreaker
from groklink.research.delta import detect_deltas
from groklink.research.history import RfHistoryStore
from pathlib import Path
import tempfile


def test_survey_happy_path():
    def rx(freq, ms):
        return {"ok": True, "safety": "allow", "json_meta": '{"pulses": 10}', "duration_ms": ms}

    s = LabBandSurvey(rx, bands_hz=[433920000, 300000000], duration_ms=200, settle_s=0.01)
    r = s.run()
    assert len(r.samples) == 2
    assert all(x.ok for x in r.samples)
    assert not r.breaker_open


def test_circuit_breaker_trips():
    def rx(freq, ms):
        raise RuntimeError("ClearCommError failed")

    s = LabBandSurvey(
        rx,
        bands_hz=[433920000, 300000000, 315000000],
        duration_ms=200,
        settle_s=0.01,
        breaker=CircuitBreaker(max_failures=2),
    )
    r = s.run()
    assert r.breaker_open
    assert len(r.samples) <= 2


def test_delta_hot_band():
    baseline = {433920000: 100.0, 300000000: 50.0}
    current = [
        {"freq_hz": 433920000, "pulses": 400, "ok": True},
        {"freq_hz": 300000000, "pulses": 40, "ok": True},
    ]
    rep = detect_deltas(current, baseline)
    flags = {b.freq_hz: b.flag for b in rep.bands}
    assert flags[433920000] == "hot"
    assert flags[300000000] == "normal"


def test_history_roundtrip(tmp_path: Path):
    store = RfHistoryStore(tmp_path / "rf.jsonl")
    store.append_survey(
        {
            "samples": [
                {"freq_hz": 433920000, "pulses": 100, "ok": True, "duration_ms": 400},
            ]
        },
        label="t1",
    )
    store.append_survey(
        {
            "samples": [
                {"freq_hz": 433920000, "pulses": 110, "ok": True, "duration_ms": 400},
            ]
        },
        label="t2",
    )
    base = store.baseline_by_freq(exclude_last_n_surveys=1)
    assert 433920000 in base

def test_delta_hot_without_baseline_count():
    """Zero/missing baseline still counts a hot band in the summary."""
    baseline = {433920000: 0.0}
    current = [{"freq_hz": 433920000, "pulses": 100, "ok": True}]
    rep = detect_deltas(current, baseline)
    assert rep.bands[0].flag == "hot"
    assert "1 hot" in rep.summary



def test_baseline_excludes_sole_survey(tmp_path: Path):
    """One survey with exclude=1 must yield an empty baseline (not self)."""
    store = RfHistoryStore(tmp_path / "rf.jsonl")
    store.append_survey(
        {
            "samples": [
                {"freq_hz": 433920000, "pulses": 100, "ok": True, "duration_ms": 400},
            ]
        },
        label="only",
    )
    assert store.baseline_by_freq(exclude_last_n_surveys=1) == {}
    store.append_survey(
        {
            "samples": [
                {"freq_hz": 433920000, "pulses": 400, "ok": True, "duration_ms": 400},
            ]
        },
        label="second",
    )
    base = store.baseline_by_freq(exclude_last_n_surveys=1)
    assert base == {433920000: 100.0}


def test_load_rows_zero_limit_empty(tmp_path: Path):
    """limit=0 / negative must return [] (not the full file via rows[-0:])."""
    store = RfHistoryStore(tmp_path / "rf.jsonl")
    store.append_sample(433920000, 10)
    store.append_sample(433920000, 20)
    assert len(store.load_rows(limit=5000)) == 2
    assert store.load_rows(limit=0) == []
    assert store.load_rows(limit=-1) == []
    assert len(store.load_rows(limit=1)) == 1
