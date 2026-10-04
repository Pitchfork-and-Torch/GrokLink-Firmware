"""Deploy skill packages to Flipper SD via storage write_chunk (small files only)."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable


def deploy_skill_dir(port: str, skill_dir: Path, *, remote_root: str = "/ext/groklink/skills") -> list[str]:
    import serial

    skill_dir = Path(skill_dir)
    skill_id = skill_dir.name
    remote_dir = f"{remote_root}/{skill_id}"
    written: list[str] = []

    ser = serial.Serial(port, 115200, timeout=3, write_timeout=15)
    time.sleep(0.4)

    def cmd(line: str, wait: float = 0.35) -> str:
        ser.reset_input_buffer()
        ser.write((line + "\r\n").encode())
        ser.flush()
        time.sleep(wait)
        n = ser.in_waiting
        return ser.read(n or 0).decode("utf-8", "replace")

    def write_file(remote: str, data: bytes) -> None:
        cmd(f"storage remove {remote}", 0.25)
        size = len(data)
        ser.reset_input_buffer()
        ser.write(f"storage write_chunk {remote} {size}\r\n".encode())
        ser.flush()
        time.sleep(0.12)
        if ser.in_waiting:
            ser.read(ser.in_waiting)
        ser.write(data)
        ser.flush()
        time.sleep(0.12 + size / 80000)
        if ser.in_waiting:
            ser.read(ser.in_waiting)

    cmd("")
    cmd(f"storage mkdir {remote_root}")
    cmd(f"storage mkdir {remote_dir}")
    for f in sorted(skill_dir.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix.lower() not in {".json", ".md", ".txt", ".c"}:
            continue
        # skip large lessons optional? include all text
        data = f.read_bytes()
        if len(data) > 12000:
            continue  # skip huge files over serial
        rel = f.relative_to(skill_dir).as_posix()
        remote = f"{remote_dir}/{rel}"
        parent = "/".join(remote.split("/")[:-1])
        cmd(f"storage mkdir {parent}", 0.2)
        if f.suffix.lower() in {".json", ".md", ".txt", ".c"}:
            try:
                data = data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
            except UnicodeDecodeError:
                pass
        write_file(remote, data)
        written.append(rel)

    ser.close()
    return written


def deploy_all_skills(port: str, skills_root: Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for d in sorted(p for p in Path(skills_root).iterdir() if p.is_dir()):
        out[d.name] = deploy_skill_dir(port, d)
        time.sleep(0.4)
    return out
