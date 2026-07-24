"""
GrokRPC client.

Transports:
  - sim: offline simulator
  - cli: Flipper USB CLI (`groklink rpc ...` -> GROKRPC:)
  - json: raw JSON-lines (future dedicated mux)
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from groklink import EDU_ACK, __version__
from groklink.rpc.transport import (
    FlipperCliTransport,
    JsonLineTransport,
    find_flipper_port,
)


@dataclass
class GrokLinkClient:
    port: Optional[str] = None
    baud: int = 115200
    timeout: float = 12.0
    session_id: Optional[str] = None
    mode: str = "sim"  # sim | cli | json
    _req_id: int = 0
    _transport: Any = field(default=None, repr=False)
    _sim_confirms: dict[str, str] = field(default_factory=dict)

    def connect(self, port: Optional[str] = None, transport: Optional[str] = None) -> dict[str, Any]:
        """
        port: COM port, 'sim', or 'auto'
        transport: 'sim' | 'cli' | 'json' | None (auto)
        """
        port = port or self.port or os.environ.get("GROKLINK_PORT", "auto")
        transport = transport or os.environ.get("GROKLINK_TRANSPORT")

        if port == "sim" or transport == "sim":
            self.mode = "sim"
            self.port = "sim"
            self._transport = None
            return self.session_start()

        if port == "auto":
            resolved = find_flipper_port("auto")
            if not resolved:
                # Fall back to sim if no device  -  convenient for demos
                self.mode = "sim"
                self.port = "sim"
                return self.session_start()
            port = resolved

        if transport is None:
            # Default real device path is Flipper CLI VCP
            transport = "cli"

        self.port = port
        self.mode = transport
        if transport == "cli":
            t = FlipperCliTransport(port=port, baud=self.baud, timeout=self.timeout)
            t.open()
            self._transport = t
        elif transport == "json":
            t = JsonLineTransport(port=port, baud=self.baud, timeout=self.timeout)
            t.open()
            self._transport = t
        else:
            raise ValueError(f"Unknown transport: {transport}")

        return self.session_start()

    def close(self) -> None:
        if self._transport is not None:
            try:
                self._transport.close()
            except Exception:
                pass
            self._transport = None
        self.session_id = None

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def request(self, method: str, **fields: Any) -> dict[str, Any]:
        payload = {"id": self._next_id(), "method": method, **fields}
        if self.session_id and "session_id" not in payload:
            payload["session_id"] = self.session_id

        if self.mode == "sim":
            return self._sim_handle(payload)

        assert self._transport is not None
        return self._transport.request_json(payload)

    def session_start(self) -> dict[str, Any]:
        resp = self.request(
            "session_start",
            client="groklink-py",
            client_version=__version__,
            edu_ack=EDU_ACK,
        )
        if resp.get("ok"):
            self.session_id = resp.get("session_id")
        return resp

    def status(self) -> dict[str, Any]:
        return self.request("status")

    def confirm(self, action: str, ttl: int = 60, rationale: str = "") -> dict[str, Any]:
        return self.request("confirm", action=action, ttl=ttl, rationale=rationale)

    def mission_list(self) -> dict[str, Any]:
        return self.request("mission_list")

    def mission_start(self, mission_id: str, confirm_id: Optional[str] = None) -> dict[str, Any]:
        fields: dict[str, Any] = {"mission_id": mission_id}
        if confirm_id:
            fields["confirm_id"] = confirm_id
        return self.request("mission_start", **fields)

    def skill_list(self) -> dict[str, Any]:
        return self.request("skill_list")

    def skill_reload(self) -> dict[str, Any]:
        return self.request("skill_reload")

    def subghz_rx(self, freq_hz: int, duration_ms: int = 1000) -> dict[str, Any]:
        return self.request("subghz_rx", freq_hz=freq_hz, duration_ms=duration_ms)

    def subghz_tx(self, file_path: str, confirm_id: str, freq_hz: int = 0) -> dict[str, Any]:
        return self.request(
            "subghz_tx",
            file_path=file_path,
            confirm_id=confirm_id,
            freq_hz=freq_hz,
        )

    def spectrum_scan(self, duration_ms: int = 500) -> dict[str, Any]:
        # Multi-band scan can take several seconds on device
        old = self.timeout
        try:
            if self._transport is not None and hasattr(self._transport, "timeout"):
                self._transport.timeout = max(old, 45.0)
            return self.request("spectrum_scan", duration_ms=duration_ms)
        finally:
            if self._transport is not None and hasattr(self._transport, "timeout"):
                self._transport.timeout = old

    def methods(self) -> dict[str, Any]:
        return self.request("methods")

    def ir_rx(self, duration_ms: int = 1000) -> dict[str, Any]:
        return self.request("ir_rx", duration_ms=duration_ms)

    def gpio_read(self, pin: int) -> dict[str, Any]:
        return self.request("gpio_read", pin=pin)

    def gpio_write(self, pin: int, value: int, confirm_id: str) -> dict[str, Any]:
        return self.request("gpio_write", pin=pin, value=value, confirm_id=confirm_id)

    def mission_reload(self) -> dict[str, Any]:
        return self.request("mission_reload")

    def radio_reset(self) -> dict[str, Any]:
        return self.request("radio_reset")

    def radio_status(self) -> dict[str, Any]:
        return self.request("radio_status")

    def radio_trip(self, reason: str = "lab_trip") -> dict[str, Any]:
        """Force device radio circuit breaker OPEN (lab research)."""
        return self.request("radio_trip", reason=reason)

    def _sim_handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        mid = payload["id"]
        method = payload["method"]
        if method in ("ping", "methods"):
            return {
                "id": mid,
                "ok": True,
                "api": 2,
                "version": "2.0.0-sim",
                "methods": [
                    "ping",
                    "methods",
                    "status",
                    "session_start",
                    "confirm",
                    "mission_list",
                    "mission_start",
                    "mission_reload",
                    "skill_list",
                    "skill_reload",
                    "subghz_rx",
                    "subghz_tx",
                    "spectrum_scan",
                    "ir_rx",
                    "gpio_read",
                    "gpio_write",
                    "radio_reset",
                    "radio_status",
                    "radio_trip",
                ],
            }
        if method == "session_start":
            if payload.get("edu_ack") != EDU_ACK:
                return {"id": mid, "ok": False, "error": "edu_ack required"}
            sid = f"sim-{uuid.uuid4().hex[:8]}"
            self.session_id = sid
            return {
                "id": mid,
                "ok": True,
                "session_id": sid,
                "agent_version": "2.0.0-sim",
                "api": 2,
                "safety_mode": "strict",
                "features": ["missions", "skills", "stream", "safety", "spectrum", "ir_rx", "gpio"],
                "sd_ok": True,
                "agent_running": True,
                "freq_min_hz": 281000000,
                "freq_max_hz": 928000000,
                "rx_max_ms": 5000,
            }
        if method == "status":
            return {
                "id": mid,
                "ok": True,
                "firmware_version": "groklink-2.0.0-sim",
                "agent_version": "2.0.0-sim",
                "api": 2,
                "battery_pct": 87,
                "sd_present": True,
                "agent_running": True,
                "safety_mode": "strict",
                "skill_count": 1,
                "mission_count": 1,
                "last_audit_hash": "c0ffee01",
                "tx_mode": "ack_file",
                "radio_breaker": False,
                "radio_faults": 0,
            }
        if method == "confirm":
            action = payload.get("action", "subghz_tx")
            cid = f"c{uuid.uuid4().hex[:8]}"
            self._sim_confirms[cid] = action
            return {
                "id": mid,
                "ok": True,
                "result": "confirm_issued",
                "confirm_id": cid,
                "expires_in_sec": payload.get("ttl", 60),
            }
        if method == "mission_list":
            return {
                "id": mid,
                "ok": True,
                "missions": [
                    {
                        "id": "lab_scan_433",
                        "name": "Lab passive 433.92 MHz scan",
                        "autonomous": True,
                    }
                ],
            }
        if method == "mission_start":
            return {"id": mid, "ok": True, "message": "started (sim)"}
        if method == "skill_list":
            return {
                "id": mid,
                "ok": True,
                "skills": [{"id": "lab_pulse_counter", "version": "1.0.0", "risk": 1}],
            }
        if method == "skill_reload":
            return {"id": mid, "ok": True}
        if method == "subghz_rx":
            freq = int(payload.get("freq_hz") or 433920000)
            if freq < 281000000 or freq > 928000000:
                return {
                    "id": mid,
                    "ok": False,
                    "safety": "deny",
                    "message": "freq out of range",
                }
            return {
                "id": mid,
                "ok": True,
                "safety": "allow",
                "freq_hz": freq,
                "duration_ms": payload.get("duration_ms", 1000),
                "json_meta": json.dumps({"pulses": 0, "sim": True}),
            }
        if method == "spectrum_scan":
            return {
                "id": mid,
                "ok": True,
                "safety": "allow",
                "duration_ms": payload.get("duration_ms", 500),
                "samples": [[433920000, 0], [300000000, 0], [868350000, 0]],
            }
        if method == "ir_rx":
            return {"id": mid, "ok": True, "safety": "allow", "duration_ms": payload.get("duration_ms", 1000)}
        if method == "gpio_read":
            return {"id": mid, "ok": True, "pin": payload.get("pin", 0), "value": 0}
        if method == "gpio_write":
            cid = payload.get("confirm_id")
            if not cid or cid not in self._sim_confirms:
                return {"id": mid, "ok": False, "safety": "confirm_needed", "message": "confirm token required"}
            del self._sim_confirms[cid]
            return {
                "id": mid,
                "ok": True,
                "safety": "allow",
                "pin": payload.get("pin", 0),
                "value": payload.get("value", 0),
            }
        if method == "mission_reload":
            return {"id": mid, "ok": True, "mission_count": 1}
        if method == "radio_reset":
            return {"id": mid, "ok": True, "message": "radio breaker reset", "breaker_open": False, "faults": 0}
        if method == "radio_trip":
            return {
                "id": mid,
                "ok": True,
                "message": "radio breaker OPEN",
                "breaker_open": True,
                "faults": 3,
                "last_fault": payload.get("reason") or "lab_trip",
            }
        if method == "radio_status":
            return {"id": mid, "ok": True, "breaker_open": False, "faults": 0, "last_fault": "", "can_start": True}
        if method == "subghz_tx":
            cid = payload.get("confirm_id")
            if not cid or cid not in self._sim_confirms:
                return {
                    "id": mid,
                    "ok": False,
                    "safety": "confirm_needed",
                    "message": "confirm token required",
                }
            del self._sim_confirms[cid]
            return {
                "id": mid,
                "ok": True,
                "safety": "allow",
                "tx_mode": "ack_file",
                "message": "tx ack (file ok; radio encoder gated) (sim)",
            }
        return {"id": mid, "ok": False, "error": f"unknown method {method}"}


def list_serial_ports() -> list[str]:
    try:
        from serial.tools import list_ports
    except ImportError:
        return []
    return [p.device for p in list_ports.comports()]
