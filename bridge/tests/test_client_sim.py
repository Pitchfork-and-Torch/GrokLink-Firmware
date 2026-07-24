from groklink.rpc.client import GrokLinkClient


def test_sim_session_and_rx() -> None:
    c = GrokLinkClient()
    r = c.connect("sim")
    assert r["ok"] is True
    assert r.get("api") == 2
    st = c.status()
    assert st["agent_running"] is True
    assert "2.0.0" in st.get("firmware_version", "")
    rx = c.subghz_rx(433920000, 1000)
    assert rx["ok"] is True


def test_sim_freq_out_of_range() -> None:
    c = GrokLinkClient()
    c.connect("sim")
    bad = c.subghz_rx(2400000000, 1000)
    assert bad["ok"] is False


def test_sim_spectrum_and_methods() -> None:
    c = GrokLinkClient()
    c.connect("sim")
    m = c.methods()
    assert m["ok"] is True
    assert "spectrum_scan" in (m.get("methods") or [])
    s = c.spectrum_scan(200)
    assert s["ok"] is True
    assert s.get("samples")


def test_sim_tx_needs_confirm() -> None:
    c = GrokLinkClient()
    c.connect("sim")
    deny = c.subghz_tx("/ext/test.sub", confirm_id="nope")
    assert deny["ok"] is False
    conf = c.confirm("subghz_tx")
    assert conf["ok"] is True
    allow = c.subghz_tx("/ext/test.sub", confirm_id=conf["confirm_id"])
    assert allow["ok"] is True
    assert allow.get("tx_mode") == "ack_file"
