from jinja2 import Environment

from .base import BuildTarget, OutputFile


class ClaudeTarget(BuildTarget):
    name = "claude"
    output_dir = ".claude"

    def render(self, skills: list[dict], org: dict, templates_env: Environment) -> list[OutputFile]:
        files: list[OutputFile] = []

        # Render each skill as a markdown file
        skill_template = templates_env.get_template("claude/skill.md.j2")
        for skill in skills:
            content = skill_template.render(skill=skill, org=org)
            path = f".claude/skills/{skill['slug']}/{skill['slug']}.md"
            files.append(OutputFile(path=path, content=content))

            # Write content_files if present
            for file_path, file_content in skill.get("content_files", {}).items():
                full_path = f".claude/skills/{skill['slug']}/{file_path}"
                files.append(OutputFile(path=full_path, content=file_content))

        # Render settings.json with hook config
        settings_template = templates_env.get_template("claude/settings.json.j2")
        settings_content = settings_template.render(org=org)
        files.append(OutputFile(path=".claude/settings.json", content=settings_content))

        # Render telemetry shell script
        telemetry_template = templates_env.get_template("claude/telemetry.sh.j2")
        telemetry_content = telemetry_template.render(org=org)
        files.append(OutputFile(
            path=".claude/hooks/skill-telemetry.sh",
            content=telemetry_content,
            executable=True,
        ))

        return files
