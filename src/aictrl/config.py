from pathlib import Path
from dataclasses import dataclass, field

import yaml


AICTRL_DIR = ".aictrl"
CONFIG_FILE = "config.yaml"
ORG_FILE = "data/org.yaml"
SKILLS_DIR = "data/skills"
OVERRIDES_DIR = "overrides/skills"
LOCK_FILE = "skills.lock"


@dataclass
class AictrlConfig:
    org_id: str
    api_url: str
    telemetry_url: str
    targets: list[str] = field(default_factory=lambda: ["claude", "cursor"])


@dataclass
class OrgData:
    id: str
    name: str
    slug: str
    telemetry_url: str


def load_config(project_root: Path) -> AictrlConfig:
    config_path = project_root / AICTRL_DIR / CONFIG_FILE
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    return AictrlConfig(
        org_id=data["org_id"],
        api_url=data["api_url"],
        telemetry_url=data["telemetry_url"],
        targets=data.get("targets", ["claude", "cursor"]),
    )


def load_org(project_root: Path) -> OrgData:
    org_path = project_root / AICTRL_DIR / ORG_FILE
    if not org_path.exists():
        raise FileNotFoundError(f"Org data not found: {org_path}")

    with open(org_path) as f:
        data = yaml.safe_load(f)

    return OrgData(
        id=data["id"],
        name=data["name"],
        slug=data["slug"],
        telemetry_url=data["telemetry_url"],
    )


def get_aictrl_dir(project_root: Path) -> Path:
    return project_root / AICTRL_DIR


def get_skills_dir(project_root: Path) -> Path:
    return project_root / AICTRL_DIR / SKILLS_DIR


def get_overrides_dir(project_root: Path) -> Path:
    return project_root / AICTRL_DIR / OVERRIDES_DIR


def get_lock_path(project_root: Path) -> Path:
    return project_root / AICTRL_DIR / LOCK_FILE
