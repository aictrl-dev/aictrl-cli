# aictrl

Build tool for AI coding skills — compiles skill definitions into tool-specific output for Claude Code, Cursor, and other AI coding assistants.

Think **dbt for AI skills**: define your team's coding skills once in YAML, build them into the format each tool expects.

## Install

```bash
pip install aictrl
```

## Quick Start

If your repo already has an `.aictrl/` directory (set up by [aictrl.dev](https://aictrl.dev) or manually):

```bash
aictrl build
```

This reads skill definitions from `.aictrl/data/skills/` and renders them into `.claude/` and `.cursor/` folders.

To start from scratch:

```bash
aictrl init --org-id my-org
# Add skill YAML files to .aictrl/data/skills/
aictrl build
```

## Commands

| Command | Description |
|---------|-------------|
| `aictrl build` | Build `.claude/` and `.cursor/` from skill data |
| `aictrl build --target claude` | Build only Claude Code output |
| `aictrl build --target cursor` | Build only Cursor output |
| `aictrl check` | Check if build is stale (CI-friendly, exits 1 if stale) |
| `aictrl clean` | Remove build output |
| `aictrl status` | Show installed skill versions |
| `aictrl init` | Initialize `.aictrl/` scaffold |
| `aictrl install-hook` | Install git post-checkout hook for auto-builds |

## How It Works

### Directory Structure

```
your-repo/
├── .aictrl/                    # Committed to git
│   ├── config.yaml             # Org connection config
│   ├── skills.lock             # Locked versions + checksums
│   ├── data/
│   │   ├── org.yaml            # Organization metadata
│   │   └── skills/             # Skill definitions (YAML)
│   │       ├── code-review.yaml
│   │       └── testing-guide.yaml
│   └── overrides/
│       └── skills/             # Team customizations (partial YAML)
│           └── code-review.yaml
├── .claude/                    # Gitignored — built output
│   ├── skills/
│   │   └── code-review/
│   │       └── code-review.md
│   ├── settings.json
│   └── hooks/
│       └── skill-telemetry.sh
└── .cursor/                    # Gitignored — built output
    ├── hooks.json
    └── hooks/
        └── skill-telemetry.sh
```

### Build Flow

```
.aictrl/data/skills/code-review.yaml   (base skill from aictrl)
  + .aictrl/overrides/skills/code-review.yaml  (team customizations)
  → rendered through Jinja2 templates
  → .claude/skills/code-review/code-review.md
  → .cursor/ hook configs
```

### Skill YAML Format

Each skill is a self-contained YAML file:

```yaml
slug: code-review
name: code-review
description: "Guides thorough code reviews"
version: "1.2.3"

instructions: |
  You are a code review assistant. Focus on:
  1. Security vulnerabilities
  2. Performance implications
  3. Code readability

sections:
  checklist: |
    ## Review Checklist
    - [ ] No hardcoded secrets
    - [ ] Error handling is complete

tags: [review, quality]
allowed_tools: [Bash, Read, Grep]
```

### Overrides

Customize skills for your team without forking. Create partial YAML files in `overrides/skills/`:

```yaml
# .aictrl/overrides/skills/code-review.yaml
# Only include fields you want to change.

allowed_tools:
  - Bash
  - Read
  - Grep
  - Edit

sections:
  team_standards: |
    ## Our Standards
    - Always check test coverage
    - Review error handling patterns
```

Merge rules:
- **Scalars**: override replaces base
- **Lists**: override replaces base entirely
- **Dicts**: deep merge (override keys win)
- **`_delete: [key1, key2]`**: removes keys from base

Overrides survive skill updates — when aictrl pushes new skill versions, your customizations are merged on top automatically.

## Auto-build on Checkout

Install a git hook so skills rebuild after `git pull`, `git checkout`, or `git merge`:

```bash
aictrl install-hook
```

## CI Integration

Use `aictrl check` in CI to ensure builds aren't stale:

```yaml
# .github/workflows/ci.yml
- name: Check skills are built
  run: |
    pip install aictrl
    aictrl check
```

## Integration with aictrl.dev

[aictrl.dev](https://aictrl.dev) manages skills centrally and pushes updates to your repos via PR:

1. aictrl creates a PR updating `.aictrl/data/skills/` and `skills.lock`
2. Your team reviews and merges
3. Developers run `aictrl build` (or it auto-builds via post-checkout hook)
4. `.claude/` and `.cursor/` are regenerated with latest skills + your overrides

## License

MIT
