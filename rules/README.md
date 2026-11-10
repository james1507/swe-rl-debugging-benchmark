# Project rules

These rules apply to every maintainer and AI tool working on the repository. Task-solving agents receive only their exported workspace and task instruction, not these maintainer documents.

| Rule | Read when | Purpose |
|---|---|---|
| [Architecture](architecture.md) | Before changing code or adding files | Keep module ownership and dependency direction clear |
| [Benchmark integrity](benchmark-integrity.md) | Before changing any task, runner or report | Preserve intentional bugs and trustworthy scoring |
| [Development](development.md) | For every change | English, small changes, validation and native tools |
| [Verification and demos](verification.md) | Before handing off work | Run appropriate checks and keep public evidence honest |

Start with [AGENTS.md](../AGENTS.md) and [CONTRIBUTING.md](../CONTRIBUTING.md). Rules define concrete constraints, not an approval process; continue autonomously within the user's authorized scope.

## Tool entry points

- General AI coding tools: root `AGENTS.md`.
- Cursor: `.cursor/rules/project.mdc`.
- Claude Code: root `CLAUDE.md`.
- GitHub Copilot: `.github/copilot-instructions.md`.
- Other tools and human contributors: read `AGENTS.md` explicitly.

Adapters point to the same rules. Do not duplicate full policies in tool-specific files or assume every tool discovers them automatically.
