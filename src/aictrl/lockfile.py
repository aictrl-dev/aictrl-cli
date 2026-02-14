import hashlib
from dataclasses import dataclass, asdict
from pathlib import Path

import yaml

from .config import get_lock_path
from .loader import SkillData


@dataclass
class LockEntry:
    slug: str
    version: str
    content_hash: str


@dataclass
class LockFile:
    version: int
    skills: list[LockEntry]


def compute_skill_hash(skill: SkillData) -> str:
    """Compute SHA256 hash of a skill's serialized YAML content."""
    data = {
        "slug": skill.slug,
        "name": skill.name,
        "description": skill.description,
        "version": skill.version,
        "instructions": skill.instructions,
        "sections": skill.sections,
        "tags": skill.tags,
        "allowed_tools": skill.allowed_tools,
        "metadata": skill.metadata,
    }
    content = yaml.dump(data, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


def read_lockfile(project_root: Path) -> LockFile | None:
    lock_path = get_lock_path(project_root)
    if not lock_path.exists():
        return None

    with open(lock_path) as f:
        data = yaml.safe_load(f)

    if not data:
        return None

    entries = []
    for entry in data.get("skills", []):
        entries.append(LockEntry(
            slug=entry["slug"],
            version=entry["version"],
            content_hash=entry["content_hash"],
        ))

    return LockFile(version=data.get("version", 1), skills=entries)


def write_lockfile(project_root: Path, skills: list[SkillData]) -> None:
    lock_path = get_lock_path(project_root)
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    entries = []
    for skill in sorted(skills, key=lambda s: s.slug):
        entries.append({
            "slug": skill.slug,
            "version": skill.version,
            "content_hash": compute_skill_hash(skill),
        })

    data = {"version": 1, "skills": entries}

    with open(lock_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def is_stale(project_root: Path, skills: list[SkillData]) -> bool:
    """Check if the lockfile is stale (skills have changed since last build)."""
    lock = read_lockfile(project_root)
    if lock is None:
        return True

    lock_map = {e.slug: e for e in lock.skills}
    current_slugs = {s.slug for s in skills}
    lock_slugs = {e.slug for e in lock.skills}

    if current_slugs != lock_slugs:
        return True

    for skill in skills:
        entry = lock_map.get(skill.slug)
        if entry is None:
            return True
        if entry.version != skill.version:
            return True
        if entry.content_hash != compute_skill_hash(skill):
            return True

    return False
