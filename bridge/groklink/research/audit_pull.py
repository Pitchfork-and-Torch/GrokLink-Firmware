"""Pull audit log from device via storage read CLI."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional


def pull_audit_via_serial(port: str, out_path: Path, *, remote: str = "/ext/groklink/logs/audit.jsonl") -> Path:
    import serial

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ser = serial.Serial(port, 115200, timeout=3, write_timeout=5)
    time.sleep(0.4)
    ser.reset_input_buffer()
    ser.write(b"\r\n")
    time.sleep(0.2)
    ser.read(ser.in_waiting or 0)
    ser.write(f"storage read {remote}\r\n".encode())
    ser.flush()
    time.sleep(1.5)
    raw = ser.read(ser.in_waiting or 65536).decode("utf-8", "replace")
    # More data?
    end = time.time() + 2.0
    while time.time() < end:
        n = ser.in_waiting
        if n:
            raw += ser.read(n).decode("utf-8", "replace")
            end = time.time() + 0.5
        else:
            time.sleep(0.05)
    ser.close()
    # Strip CLI noise: keep lines that look like JSON
    lines = []
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("{") and s.endswith("}"):
            lines.append(s)
    out_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return out_path
