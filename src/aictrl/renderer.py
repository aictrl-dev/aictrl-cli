from pathlib import Path
from dataclasses import asdict

from jinja2 import Environment, FileSystemLoader, PackageLoader, ChoiceLoader

from .config import AictrlConfig, OrgData, AICTRL_DIR
from .loader import SkillData
from .targets.base import OutputFile, BuildTarget
from .targets.claude import ClaudeTarget
from .targets.cursor import CursorTarget


TARGETS: dict[str, type[BuildTarget]] = {
    "claude": ClaudeTarget,
    "cursor": CursorTarget,
}


def create_templates_env(project_root: Path) -> Environment:
    """Create Jinja2 environment with template loaders.

    Looks for templates in:
    1. .aictrl/templates/ (project-local overrides, checked first)
    2. Bundled package templates (fallback)
    """
    loaders = []

    local_templates = project_root / AICTRL_DIR / "templates"
    if local_templates.exists():
        loaders.append(FileSystemLoader(str(local_templates)))

    loaders.append(PackageLoader("aictrl", "templates"))

    return Environment(
        loader=ChoiceLoader(loaders),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_all(
    skills: list[SkillData],
    config: AictrlConfig,
    org: OrgData,
    project_root: Path,
    target_names: list[str] | None = None,
) -> list[OutputFile]:
    """Render all output files for the specified targets."""
    env = create_templates_env(project_root)

    targets_to_build = target_names or config.targets
    org_dict = asdict(org)

    all_files: list[OutputFile] = []
    for target_name in targets_to_build:
        target_cls = TARGETS.get(target_name)
        if target_cls is None:
            raise ValueError(f"Unknown target: {target_name}. Available: {list(TARGETS.keys())}")

        target = target_cls()
        skill_dicts = [asdict(s) for s in skills]
        files = target.render(skill_dicts, org_dict, env)
        all_files.extend(files)

    return all_files


def write_output_files(files: list[OutputFile], project_root: Path) -> int:
    """Write rendered output files to disk. Returns count of files written."""
    count = 0
    for f in files:
        out_path = project_root / f.path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(f.content)
        if f.executable:
            out_path.chmod(0o755)
        count += 1
    return count
