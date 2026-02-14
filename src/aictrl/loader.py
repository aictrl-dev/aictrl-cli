from pathlib import Path
from dataclasses import dataclass, field

import yaml

from .config import get_skills_dir


@dataclass
class SkillData:
    slug: str
    name: str
    description: str
    version: str
    instructions: str
    sections: dict[str, str] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    file_structure: dict | None = None
    content_files: dict[str, str] = field(default_factory=dict)


def load_skills(project_root: Path) -> list[SkillData]:
    skills_dir = get_skills_dir(project_root)
    if not skills_dir.exists():
        return []

    skills = []
    for yaml_file in sorted(skills_dir.glob("*.yaml")):
        skill = _parse_skill_yaml(yaml_file)
        skills.append(skill)

    return skills


def load_skill(yaml_path: Path) -> SkillData:
    return _parse_skill_yaml(yaml_path)


def _parse_skill_yaml(yaml_path: Path) -> SkillData:
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    if not data:
        raise ValueError(f"Empty skill file: {yaml_path}")

    if "slug" not in data:
        raise ValueError(f"Skill file missing 'slug': {yaml_path}")

    return SkillData(
        slug=data["slug"],
        name=data.get("name", data["slug"]),
        description=data.get("description", ""),
        version=data.get("version", "0.0.0"),
        instructions=data.get("instructions", ""),
        sections=data.get("sections", {}),
        tags=data.get("tags", []),
        allowed_tools=data.get("allowed_tools", []),
        metadata=data.get("metadata", {}),
        file_structure=data.get("file_structure"),
        content_files=data.get("content_files", {}),
    )
