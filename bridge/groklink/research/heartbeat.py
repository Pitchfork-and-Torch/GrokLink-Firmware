"""Status-only heartbeat with optional circuit-broken gentle band sample."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable, Optional


def run_heartbeat(
    status_fn: Callable[[], dict[str, Any]],
    *,
    rx_fn: Optional[Callable[[int, int], dict[str, Any]]] = None,
    gentle_freq_hz: int = 433_920_000,
    gentle_ms: int = 300,
    log_path: Optional[Path] = None,
    allow_radio: bool = False,
) -> dict[str, Any]:
    row: dict[str, Any] = {"ts": time.time(), "kind": "heartbeat"}
    try:
        st = status_fn()
        row["status"] = {
            "ok": st.get("ok"),
            "firmware_version": st.get("firmware_version"),
            "api": st.get("api"),
            "agent_running": st.get("agent_running"),
            "safety_mode": st.get("safety_mode"),
            "radio_breaker": st.get("radio_breaker"),
        }
        row["ok"] = bool(st.get("ok") and st.get("agent_running"))
    except Exception as e:
        row["ok"] = False
        row["error"] = str(e)[:200]

    if allow_radio and row.get("ok") and rx_fn is not None:
        try:
            r = rx_fn(gentle_freq_hz, gentle_ms)
            row["gentle_rx"] = {
                "ok": r.get("ok"),
                "freq_hz": gentle_freq_hz,
                "json_meta": r.get("json_meta"),
                "safety": r.get("safety"),
            }
        except Exception as e:
            row["gentle_rx"] = {"ok": False, "error": str(e)[:160]}

    if log_path:
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")
    return row
