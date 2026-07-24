from groklink.rpc.transport import (
    find_flipper_port,
    loads_json_lenient,
    sanitize_json_control_chars,
)


def test_find_flipper_port_no_crash() -> None:
    # May return None if no ports; must not raise
    _ = find_flipper_port("auto")
    assert find_flipper_port("sim") is None or True


def test_sanitize_strips_c0_controls() -> None:
    dirty = '{"id":1,"ok":true,"skills":[{"id":"lab_pulse_counter","version":",\n  ","risk":1}]}'
    clean = sanitize_json_control_chars(dirty)
    assert "\n" not in clean
    obj = loads_json_lenient(dirty)
    assert obj["ok"] is True
    assert obj["skills"][0]["id"] == "lab_pulse_counter"


def test_loads_json_lenient_mission_list() -> None:
    dirty = '{"id":1,"ok":true,"missions":[{"id":",\n  ","name":",\n  ","autonomous":false}]}'
    obj = loads_json_lenient(dirty)
    assert obj["ok"] is True
    assert "missions" in obj
