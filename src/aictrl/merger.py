from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

import yaml

from .config import get_overrides_dir
from .loader import SkillData


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override dict onto base dict.

    Rules:
    - Scalars: override replaces base
    - Lists: override replaces base (not appended)
    - Dicts: deep merge (override keys win)
    - Special key `_delete` with a list of keys removes those keys from result
    """
    result = deepcopy(base)

    for key, value in override.items():
        if key == "_delete":
            if isinstance(value, list):
                for k in value:
                    result.pop(k, None)
            continue

        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)

    return result


def load_overrides(project_root: Path) -> dict[str, dict]:
    """Load all override files from .aictrl/overrides/skills/.

    Returns a dict mapping skill slug to override data.
    """
    overrides_dir = get_overrides_dir(project_root)
    if not overrides_dir.exists():
        return {}

    overrides = {}
    for yaml_file in sorted(overrides_dir.glob("*.yaml")):
        slug = yaml_file.stem
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        if data:
            overrides[slug] = data

    return overrides


def merge_overrides(skills: list[SkillData], project_root: Path) -> list[SkillData]:
    """Apply overrides to skill data.

    Loads override files from .aictrl/overrides/skills/ and deep-merges
    matching overrides onto each skill's data.
    """
    overrides = load_overrides(project_root)
    if not overrides:
        return skills

    merged = []
    for skill in skills:
        override = overrides.get(skill.slug)
        if override is None:
            merged.append(skill)
            continue

        skill_dict = asdict(skill)
        merged_dict = deep_merge(skill_dict, override)
        merged.append(SkillData(**merged_dict))

    return merged
