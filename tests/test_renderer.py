import json

from aictrl.config import load_config, load_org
from aictrl.loader import load_skills
from aictrl.merger import merge_overrides
from aictrl.renderer import render_all, create_templates_env, write_output_files
from aictrl.targets.base import OutputFile


def test_render_all_produces_files(sample_project):
    config = load_config(sample_project)
    org = load_org(sample_project)
    skills = load_skills(sample_project)
    merged = merge_overrides(skills, sample_project)

    files = render_all(merged, config, org, sample_project)
    paths = [f.path for f in files]

    # Claude target files
    assert ".claude/skills/code-review/code-review.md" in paths
    assert ".claude/skills/testing-guide/testing-guide.md" in paths
    assert ".claude/settings.json" in paths
    assert ".claude/hooks/skill-telemetry.sh" in paths

    # Cursor target files
    assert ".cursor/hooks.json" in paths
    assert ".cursor/hooks/skill-telemetry.sh" in paths


def test_render_claude_skill_has_frontmatter(sample_project):
    config = load_config(sample_project)
    org = load_org(sample_project)
    skills = load_skills(sample_project)

    files = render_all(skills, config, org, sample_project, target_names=["claude"])
    cr_file = next(f for f in files if "code-review.md" in f.path)

    assert cr_file.content.startswith("---")
    assert "description:" in cr_file.content
    assert "code review" in cr_file.content.lower()


def test_render_claude_skill_has_instructions(sample_project):
    config = load_config(sample_project)
    org = load_org(sample_project)
    skills = load_skills(sample_project)

    files = render_all(skills, config, org, sample_project, target_names=["claude"])
    cr_file = next(f for f in files if "code-review.md" in f.path)

    assert "Security vulnerabilities" in cr_file.content
    assert "Performance issues" in cr_file.content


def test_render_claude_settings_has_hook(sample_project):
    config = load_config(sample_project)
    org = load_org(sample_project)
    skills = load_skills(sample_project)

    files = render_all(skills, config, org, sample_project, target_names=["claude"])
    settings_file = next(f for f in files if f.path == ".claude/settings.json")

    settings = json.loads(settings_file.content)
    assert "hooks" in settings
    assert "PostToolUse" in settings["hooks"]
    assert org.id in settings_file.content


def test_render_claude_telemetry_executable(sample_project):
    config = load_config(sample_project)
    org = load_org(sample_project)
    skills = load_skills(sample_project)

    files = render_all(skills, config, org, sample_project, target_names=["claude"])
    telemetry = next(f for f in files if f.path == ".claude/hooks/skill-telemetry.sh")

    assert telemetry.executable is True
    assert "#!/bin/bash" in telemetry.content


def test_render_cursor_hooks_json(sample_project):
    config = load_config(sample_project)
    org = load_org(sample_project)
    skills = load_skills(sample_project)

    files = render_all(skills, config, org, sample_project, target_names=["cursor"])
    hooks_file = next(f for f in files if f.path == ".cursor/hooks.json")

    hooks = json.loads(hooks_file.content)
    assert hooks["version"] == 1
    assert "afterMCPExecution" in hooks["hooks"]
    assert org.id in hooks_file.content


def test_render_single_target(sample_project):
    config = load_config(sample_project)
    org = load_org(sample_project)
    skills = load_skills(sample_project)

    files = render_all(skills, config, org, sample_project, target_names=["claude"])
    paths = [f.path for f in files]

    assert any(".claude/" in p for p in paths)
    assert not any(".cursor/" in p for p in paths)


def test_render_unknown_target_raises(sample_project):
    config = load_config(sample_project)
    org = load_org(sample_project)
    skills = load_skills(sample_project)

    try:
        render_all(skills, config, org, sample_project, target_names=["windsurf"])
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "windsurf" in str(e)


def test_write_output_files(tmp_path, sample_project):
    config = load_config(sample_project)
    org = load_org(sample_project)
    skills = load_skills(sample_project)

    files = render_all(skills, config, org, sample_project, target_names=["claude"])
    count = write_output_files(files, tmp_path)

    assert count == len(files)
    assert (tmp_path / ".claude" / "skills" / "code-review" / "code-review.md").exists()
    assert (tmp_path / ".claude" / "settings.json").exists()

    # Check telemetry script is executable
    telemetry_path = tmp_path / ".claude" / "hooks" / "skill-telemetry.sh"
    assert telemetry_path.exists()
    assert telemetry_path.stat().st_mode & 0o111  # executable bit set


def test_render_with_overrides(sample_project):
    config = load_config(sample_project)
    org = load_org(sample_project)
    skills = load_skills(sample_project)
    merged = merge_overrides(skills, sample_project)

    files = render_all(merged, config, org, sample_project, target_names=["claude"])
    cr_file = next(f for f in files if "code-review.md" in f.path)

    # Override added "Edit" to allowed_tools
    assert "Edit" in cr_file.content
    # Override replaced team_standards section
    assert "Our Team Standards" in cr_file.content
