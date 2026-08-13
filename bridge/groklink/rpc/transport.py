"""Serial transports for GrokLink: sim, Flipper CLI VCP, raw JSON-lines."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any, Optional


def sanitize_json_control_chars(text: str) -> str:
    """Replace bare C0 controls so json.loads does not fail on device bugs.

    Pretty-printed SD manifests once caused skill_list/mission_list to embed
    raw newlines inside string values (Invalid control character). Firmware
    parsers are fixed; keep this as defense-in-depth for older flashes.
    """
    return "".join(ch if ord(ch) >= 0x20 else " " for ch in text)


def loads_json_lenient(text: str) -> Any:
    """json.loads with control-char scrub fallback."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(sanitize_json_control_chars(text))


def find_flipper_port(preferred: str | None = None) -> str | None:
    try:
        from serial.tools import list_ports
    except ImportError:
        return preferred if preferred and preferred != "auto" else None

    if preferred and preferred not in ("auto", "", "sim"):
        return preferred

    scored: list[tuple[int, str]] = []
    for p in list_ports.comports():
        blob = f"{p.description or ''} {p.manufacturer or ''} {p.product or ''} {p.device}"
        score = 0
        for key in ("Flipper", "flipper", "STM32", "CDC", "Serial"):
            if key in blob:
                score += 2
        if "Bluetooth" in blob:
            score -= 3
        if score > 0:
            scored.append((score, p.device))
    scored.sort(reverse=True)
    if scored:
        return scored[0][1]
    ports = list(list_ports.comports())
    return ports[0].device if ports else None


@dataclass
class FlipperCliTransport:
    """
    Talks to device CLI over USB VCP.
    Issues: groklink rpc <json>
    Expects: GROKRPC:{...}
    """

    port: str
    baud: int = 115200
    timeout: float = 12.0
    _ser: Any = None

    def open(self) -> None:
        import serial

        self._ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
        time.sleep(0.35)
        # Clear boot noise / prompt
        self._ser.reset_input_buffer()
        self._write("\r\n")
        self._drain(0.3)

    def close(self) -> None:
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None

    def _write(self, s: str) -> None:
        assert self._ser is not None
        self._ser.write(s.encode("utf-8"))
        self._ser.flush()

    def _drain(self, seconds: float) -> str:
        assert self._ser is not None
        end = time.time() + seconds
        chunks: list[bytes] = []
        while time.time() < end:
            n = self._ser.in_waiting
            if n:
                chunks.append(self._ser.read(n))
            else:
                time.sleep(0.02)
        return b"".join(chunks).decode("utf-8", errors="replace")

    def request_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        assert self._ser is not None
        line = json.dumps(payload, separators=(",", ":"))
        # Escape is unnecessary for simple JSON without quotes issues in CLI args;
        # wrap carefully  -  Flipper CLI splits on spaces, so keep JSON compact no spaces.
        cmd = f"groklink rpc {line}\r\n"
        self._ser.reset_input_buffer()
        self._write(cmd)

        deadline = time.time() + self.timeout
        buf = ""
        while time.time() < deadline:
            chunk = self._ser.read(self._ser.in_waiting or 1)
            if chunk:
                buf += chunk.decode("utf-8", errors="replace")
                marker = buf.find("GROKRPC:")
                if marker >= 0:
                    body = buf[marker + len("GROKRPC:") :].lstrip()
                    # Wait until JSON object is brace-balanced (handles partial CDC reads)
                    if body.startswith("{"):
                        depth = 0
                        in_str = False
                        esc = False
                        for i, ch in enumerate(body):
                            if in_str:
                                if esc:
                                    esc = False
                                elif ch == "\\":
                                    esc = True
                                elif ch == '"':
                                    in_str = False
                                continue
                            if ch == '"':
                                in_str = True
                            elif ch == "{":
                                depth += 1
                            elif ch == "}":
                                depth -= 1
                                if depth == 0:
                                    return loads_json_lenient(body[: i + 1])
            else:
                time.sleep(0.02)
        raise TimeoutError(f"No GROKRPC response on {self.port}. Got: {buf[-240:]!r}")


@dataclass
class JsonLineTransport:
    """Raw length-free JSON lines (future dedicated CDC mux)."""

    port: str
    baud: int = 115200
    timeout: float = 3.0
    _ser: Any = None

    def open(self) -> None:
        import serial

        self._ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
        time.sleep(0.2)

    def close(self) -> None:
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None

    def request_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        assert self._ser is not None
        self._ser.write((json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8"))
        self._ser.flush()
        raw = self._ser.readline()
        if not raw:
            raise TimeoutError("No JSON-line response")
        return loads_json_lenient(raw.decode("utf-8", errors="replace"))
