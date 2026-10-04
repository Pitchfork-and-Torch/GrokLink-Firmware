"""Parse GROKSTREAM lines from mixed CLI/serial output."""

from __future__ import annotations

import json
import re
from typing import Any, Iterator

_STREAM_RE = re.compile(r"GROKSTREAM:\s*(\{.*\})")


def parse_stream_line(line: str) -> dict[str, Any] | None:
    m = _STREAM_RE.search(line)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        try:
            from groklink.rpc.transport import loads_json_lenient

            return loads_json_lenient(m.group(1))
        except Exception:
            return None


def iter_stream_events(text: str) -> Iterator[dict[str, Any]]:
    for line in text.splitlines():
        ev = parse_stream_line(line)
        if ev:
            yield ev
