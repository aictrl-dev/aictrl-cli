from jinja2 import Environment

from .base import BuildTarget, OutputFile


class CursorTarget(BuildTarget):
    name = "cursor"
    output_dir = ".cursor"

    def render(self, skills: list[dict], org: dict, templates_env: Environment) -> list[OutputFile]:
        files: list[OutputFile] = []

        # Render hooks.json with telemetry config
        hooks_template = templates_env.get_template("cursor/hooks.json.j2")
        hooks_content = hooks_template.render(org=org)
        files.append(OutputFile(path=".cursor/hooks.json", content=hooks_content))

        # Render telemetry shell script
        telemetry_template = templates_env.get_template("cursor/telemetry.sh.j2")
        telemetry_content = telemetry_template.render(org=org)
        files.append(OutputFile(
            path=".cursor/hooks/skill-telemetry.sh",
            content=telemetry_content,
            executable=True,
        ))

        return files
