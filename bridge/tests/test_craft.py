import json
from pathlib import Path

from groklink.skills.craft import analyze_log_lines, craft_skill_from_log


def test_analyze_and_craft(tmp_path: Path) -> None:
    log = tmp_path / "sample.jsonl"
    log.write_text(
        "\n".join(
            [
                json.dumps({"action": "subghz_rx", "freq_hz": 433920000, "json_meta": {"pulses": 12}}),
                json.dumps({"action": "subghz_rx", "freq_hz": 433920000, "json_meta": {"pulses": 3}}),
            ]
        ),
        encoding="utf-8",
    )
    analysis = analyze_log_lines(log.read_text(encoding="utf-8").splitlines())
    assert analysis["dominant_freq_hz"] == 433920000
    assert analysis["pulse_total"] == 15

    out = tmp_path / "skills"
    result = craft_skill_from_log(log, out, skill_name="lab_demo")
    assert result.skill_id == "lab_demo"
    assert (result.out_dir / "manifest.json").exists()
    man = json.loads((result.out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert man["risk_class"] == "passive_rx"
