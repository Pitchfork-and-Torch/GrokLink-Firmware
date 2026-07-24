"""Offline SD skill deploy into a mirror tree."""

from __future__ import annotations

import shutil
from pathlib import Path


def deploy_skills_tree(skills_src: Path, sd_groklink_root: Path) -> list[str]:
    """Copy each skill package under skills_src into sd_groklink_root/skills/."""
    skills_src = Path(skills_src)
    root = Path(sd_groklink_root)
    dest_skills = root / "skills"
    dest_skills.mkdir(parents=True, exist_ok=True)
    deployed: list[str] = []
    for skill_dir in sorted(p for p in skills_src.iterdir() if p.is_dir()):
        target = dest_skills / skill_dir.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(skill_dir, target)
        deployed.append(skill_dir.name)
    return deployed
