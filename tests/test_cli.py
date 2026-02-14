import json
import shutil

import pytest
from click.testing import CliRunner

from aictrl.cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def writable_project(sample_project, tmp_path):
    """Copy fixture to a writable temp directory."""
    dst = tmp_path / "project"
    shutil.copytree(sample_project, dst)
    return dst


class TestBuild:
    def test_build_creates_claude_files(self, runner, writable_project):
        result = runner.invoke(main, ["build", "--project", str(writable_project)])
        assert result.exit_code == 0
        assert "Built 2 skills" in result.output

        # Check Claude skill files
        cr = writable_project / ".claude" / "skills" / "code-review" / "code-review.md"
        assert cr.exists()
        content = cr.read_text()
        assert "---" in content
        assert "description:" in content
        assert "Security vulnerabilities" in content

        tg = writable_project / ".claude" / "skills" / "testing-guide" / "testing-guide.md"
        assert tg.exists()

    def test_build_creates_settings_json(self, runner, writable_project):
        result = runner.invoke(main, ["build", "--project", str(writable_project)])
        assert result.exit_code == 0

        settings = writable_project / ".claude" / "settings.json"
        assert settings.exists()
        data = json.loads(settings.read_text())
        assert "hooks" in data
        assert "PostToolUse" in data["hooks"]

    def test_build_creates_cursor_files(self, runner, writable_project):
        result = runner.invoke(main, ["build", "--project", str(writable_project)])
        assert result.exit_code == 0

        hooks = writable_project / ".cursor" / "hooks.json"
        assert hooks.exists()
        data = json.loads(hooks.read_text())
        assert data["version"] == 1

    def test_build_target_claude_only(self, runner, writable_project):
        result = runner.invoke(main, ["build", "--target", "claude", "--project", str(writable_project)])
        assert result.exit_code == 0
        assert (writable_project / ".claude" / "skills").exists()
        assert not (writable_project / ".cursor").exists()

    def test_build_target_cursor_only(self, runner, writable_project):
        result = runner.invoke(main, ["build", "--target", "cursor", "--project", str(writable_project)])
        assert result.exit_code == 0
        assert (writable_project / ".cursor" / "hooks.json").exists()
        assert not (writable_project / ".claude").exists()

    def test_build_creates_lockfile(self, runner, writable_project):
        result = runner.invoke(main, ["build", "--project", str(writable_project)])
        assert result.exit_code == 0
        assert (writable_project / ".aictrl" / "skills.lock").exists()

    def test_build_updates_gitignore(self, runner, writable_project):
        result = runner.invoke(main, ["build", "--project", str(writable_project)])
        assert result.exit_code == 0

        gitignore = writable_project / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert ".claude/" in content
        assert ".cursor/" in content

    def test_build_missing_config(self, runner, tmp_path):
        result = runner.invoke(main, ["build", "--project", str(tmp_path)])
        assert result.exit_code == 1
        assert "Config not found" in result.output

    def test_build_with_overrides(self, runner, writable_project):
        result = runner.invoke(main, ["build", "--project", str(writable_project)])
        assert result.exit_code == 0

        cr = writable_project / ".claude" / "skills" / "code-review" / "code-review.md"
        content = cr.read_text()
        # Override adds Edit to allowed_tools
        assert "Edit" in content
        # Override replaces team_standards
        assert "Our Team Standards" in content

    def test_build_telemetry_script_executable(self, runner, writable_project):
        result = runner.invoke(main, ["build", "--project", str(writable_project)])
        assert result.exit_code == 0

        sh = writable_project / ".claude" / "hooks" / "skill-telemetry.sh"
        assert sh.exists()
        assert sh.stat().st_mode & 0o111


class TestCheck:
    def test_check_stale_without_build(self, runner, writable_project):
        result = runner.invoke(main, ["check", "--project", str(writable_project)])
        assert result.exit_code == 1
        assert "stale" in result.output.lower()

    def test_check_fresh_after_build(self, runner, writable_project):
        runner.invoke(main, ["build", "--project", str(writable_project)])
        result = runner.invoke(main, ["check", "--project", str(writable_project)])
        assert result.exit_code == 0
        assert "up to date" in result.output.lower()


class TestClean:
    def test_clean_removes_output(self, runner, writable_project):
        runner.invoke(main, ["build", "--project", str(writable_project)])
        assert (writable_project / ".claude").exists()
        assert (writable_project / ".cursor").exists()

        result = runner.invoke(main, ["clean", "--project", str(writable_project)])
        assert result.exit_code == 0
        assert not (writable_project / ".claude").exists()
        assert not (writable_project / ".cursor").exists()

    def test_clean_nothing_to_clean(self, runner, writable_project):
        result = runner.invoke(main, ["clean", "--project", str(writable_project)])
        assert result.exit_code == 0
        assert "Nothing to clean" in result.output


class TestStatus:
    def test_status_after_build(self, runner, writable_project):
        runner.invoke(main, ["build", "--project", str(writable_project)])
        result = runner.invoke(main, ["status", "--project", str(writable_project)])
        assert result.exit_code == 0
        assert "code-review" in result.output
        assert "1.2.3" in result.output
        assert "testing-guide" in result.output
        assert "2.0.1" in result.output

    def test_status_no_lockfile(self, runner, tmp_path):
        result = runner.invoke(main, ["status", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "No lockfile found" in result.output


class TestInit:
    def test_init_creates_scaffold(self, runner, tmp_path):
        result = runner.invoke(main, ["init", "--org-id", "test-org", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "Initialized" in result.output

        assert (tmp_path / ".aictrl" / "config.yaml").exists()
        assert (tmp_path / ".aictrl" / "data" / "org.yaml").exists()
        assert (tmp_path / ".aictrl" / "data" / "skills").is_dir()
        assert (tmp_path / ".aictrl" / "overrides" / "skills").is_dir()

    def test_init_already_exists(self, runner, writable_project):
        result = runner.invoke(main, ["init", "--org-id", "test", "--project", str(writable_project)])
        assert result.exit_code == 1
        assert "already exists" in result.output


class TestInstallHook:
    def test_install_hook_no_git(self, runner, tmp_path):
        result = runner.invoke(main, ["install-hook", "--project", str(tmp_path)])
        assert result.exit_code == 1
        assert "Not a git" in result.output

    def test_install_hook_creates_hook(self, runner, tmp_path):
        (tmp_path / ".git").mkdir()
        result = runner.invoke(main, ["install-hook", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "Installed" in result.output

        hook = tmp_path / ".git" / "hooks" / "post-checkout"
        assert hook.exists()
        assert hook.stat().st_mode & 0o111
        assert "aictrl" in hook.read_text()

    def test_install_hook_already_installed(self, runner, tmp_path):
        (tmp_path / ".git").mkdir()
        runner.invoke(main, ["install-hook", "--project", str(tmp_path)])
        result = runner.invoke(main, ["install-hook", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "already installed" in result.output
