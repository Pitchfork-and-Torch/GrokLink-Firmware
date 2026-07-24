"""Run flipper RF literacy curriculum checklist."""

from __future__ import annotations

from pathlib import Path
from typing import Any


LESSONS = [
    {"id": 1, "title": "ISM bands overview", "action": "read docs/WHAT_WE_LEARNED.md"},
    {"id": 2, "title": "Listen first", "action": "status + one short subghz_rx 433.92"},
    {"id": 3, "title": "Safety gates", "action": "session with bad edu_ack then good"},
    {"id": 4, "title": "USB discipline", "action": "close qFlipper; one serial owner"},
    {"id": 5, "title": "Site personality", "action": "hw spectrum --history ..."},
    {"id": 6, "title": "TX ethics", "action": "tx without confirm must deny"},
]


def curriculum_state(progress_path: Path) -> dict[str, Any]:
    done: set[int] = set()
    if progress_path.exists():
        for line in progress_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.isdigit():
                done.add(int(line))
    items = []
    for les in LESSONS:
        items.append({**les, "done": les["id"] in done})
    next_les = next((x for x in items if not x["done"]), None)
    return {"lessons": items, "next": next_les, "complete": next_les is None}


def mark_lesson(progress_path: Path, lesson_id: int) -> None:
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    with progress_path.open("a", encoding="utf-8") as f:
        f.write(f"{lesson_id}\n")
