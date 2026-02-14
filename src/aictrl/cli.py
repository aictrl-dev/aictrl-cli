import shutil
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .config import load_config, load_org, AICTRL_DIR
from .loader import load_skills
from .merger import merge_overrides
from .renderer import render_all, write_output_files, TARGETS
from .lockfile import write_lockfile, read_lockfile, is_stale
from .gitignore import ensure_gitignore

console = Console()


@click.group()
def main():
    """Skill build tool — compiles .aictrl/ definitions into tool-specific output."""
    pass


@main.command()
@click.option("--target", type=click.Choice(list(TARGETS.keys())), help="Build only a specific target")
@click.option("--project", default=".", help="Project root directory")
def build(target, project):
    """Build .claude/ and .cursor/ from .aictrl/ data."""
    project_root = Path(project).resolve()

    try:
        config = load_config(project_root)
        org = load_org(project_root)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("Run 'aictrl init' to set up .aictrl/ first.")
        sys.exit(1)

    skills = load_skills(project_root)
    if not skills:
        console.print("[yellow]No skills found in .aictrl/data/skills/[/yellow]")
        sys.exit(0)

    merged = merge_overrides(skills, project_root)

    target_names = [target] if target else None
    files = render_all(merged, config, org, project_root, target_names=target_names)
    count = write_output_files(files, project_root)

    write_lockfile(project_root, merged)
    added_to_gitignore = ensure_gitignore(project_root)

    targets_built = target_names or config.targets
    console.print(f"[green]Built {len(merged)} skills → {count} files[/green] ({', '.join(targets_built)})")
    if added_to_gitignore:
        console.print(f"  Added to .gitignore: {', '.join(added_to_gitignore)}")


@main.command()
@click.option("--project", default=".", help="Project root directory")
def check(project):
    """Check if build is stale (exit code 1 if stale)."""
    project_root = Path(project).resolve()

    try:
        config = load_config(project_root)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    skills = load_skills(project_root)
    merged = merge_overrides(skills, project_root)

    if is_stale(project_root, merged):
        console.print("[yellow]Build is stale.[/yellow] Run 'aictrl build' to update.")
        sys.exit(1)
    else:
        console.print("[green]Build is up to date.[/green]")
        sys.exit(0)


@main.command()
@click.option("--project", default=".", help="Project root directory")
def clean(project):
    """Remove build output (.claude/ and .cursor/)."""
    project_root = Path(project).resolve()
    removed = []

    for target_cls in TARGETS.values():
        target_dir = project_root / target_cls.output_dir
        if target_dir.exists():
            shutil.rmtree(target_dir)
            removed.append(target_cls.output_dir)

    if removed:
        console.print(f"[green]Cleaned:[/green] {', '.join(removed)}")
    else:
        console.print("Nothing to clean.")


@main.command()
@click.option("--project", default=".", help="Project root directory")
def status(project):
    """Show current skill versions from lockfile."""
    project_root = Path(project).resolve()
    lock = read_lockfile(project_root)

    if lock is None:
        console.print("[yellow]No lockfile found.[/yellow] Run 'aictrl build' first.")
        sys.exit(0)

    table = Table(title="Installed Skills")
    table.add_column("Skill", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Hash", style="dim", max_width=16)

    for entry in lock.skills:
        table.add_row(entry.slug, entry.version, entry.content_hash[:16])

    console.print(table)


@main.command()
@click.option("--org-id", required=True, help="Organization ID")
@click.option("--api-url", default="https://aictrl.dev", help="API base URL")
@click.option("--project", default=".", help="Project root directory")
def init(org_id, api_url, project):
    """Initialize .aictrl/ scaffold in current directory."""
    import yaml

    project_root = Path(project).resolve()
    aictrl_dir = project_root / AICTRL_DIR

    if aictrl_dir.exists():
        console.print(f"[yellow].aictrl/ already exists at {aictrl_dir}[/yellow]")
        sys.exit(1)

    telemetry_url = f"{api_url}/api/telemetry"

    # Create directory structure
    (aictrl_dir / "data" / "skills").mkdir(parents=True)
    (aictrl_dir / "overrides" / "skills").mkdir(parents=True)

    # Write config.yaml
    config = {
        "org_id": org_id,
        "api_url": api_url,
        "telemetry_url": telemetry_url,
        "targets": ["claude", "cursor"],
    }
    with open(aictrl_dir / "config.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Write org.yaml
    org = {
        "id": org_id,
        "name": org_id,
        "slug": org_id,
        "telemetry_url": telemetry_url,
    }
    with open(aictrl_dir / "data" / "org.yaml", "w") as f:
        yaml.dump(org, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]Initialized .aictrl/ at {aictrl_dir}[/green]")
    console.print("  Add skill YAML files to .aictrl/data/skills/")
    console.print("  Then run 'aictrl build'")


@main.command("install-hook")
@click.option("--project", default=".", help="Project root directory")
def install_hook(project):
    """Install git post-checkout hook to auto-build on checkout."""
    project_root = Path(project).resolve()
    hooks_dir = project_root / ".git" / "hooks"

    if not hooks_dir.parent.exists():
        console.print("[red]Not a git repository.[/red]")
        sys.exit(1)

    hooks_dir.mkdir(exist_ok=True)
    hook_path = hooks_dir / "post-checkout"

    hook_content = """#!/bin/bash
# Auto-build skills on checkout (installed by aictrl)
if command -v aictrl &> /dev/null && [ -d ".aictrl" ]; then
  aictrl build --project "$(git rev-parse --show-toplevel)" 2>/dev/null || true
fi
"""

    if hook_path.exists():
        existing = hook_path.read_text()
        if "aictrl" in existing:
            console.print("[yellow]Hook already installed.[/yellow]")
            sys.exit(0)
        # Append to existing hook
        with open(hook_path, "a") as f:
            f.write("\n" + hook_content)
        console.print("[green]Appended aictrl hook to existing post-checkout.[/green]")
    else:
        hook_path.write_text(hook_content)
        hook_path.chmod(0o755)
        console.print("[green]Installed post-checkout hook.[/green]")
