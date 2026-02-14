from pathlib import Path

ENTRIES_TO_ADD = [".claude/", ".cursor/"]


def ensure_gitignore(project_root: Path) -> list[str]:
    """Ensure .claude/ and .cursor/ are in .gitignore.

    Returns list of entries that were added (empty if all already present).
    """
    gitignore_path = project_root / ".gitignore"

    existing_lines: list[str] = []
    if gitignore_path.exists():
        existing_lines = gitignore_path.read_text().splitlines()

    existing_set = {line.strip() for line in existing_lines}

    added = []
    for entry in ENTRIES_TO_ADD:
        if entry not in existing_set:
            added.append(entry)

    if added:
        with open(gitignore_path, "a") as f:
            if existing_lines and existing_lines[-1].strip():
                f.write("\n")
            f.write("# Build output from aictrl\n")
            for entry in added:
                f.write(f"{entry}\n")

    return added
