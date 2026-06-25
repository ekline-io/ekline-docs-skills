# Install for Claude Code

EkLine Docs Skills ships as a Claude Code plugin. The seven core skills work
with no account or API key; the optional `review-docs` skill needs the EkLine
CLI and a token (see [prerequisites](#ekline-power-up-prerequisites)).

## Option A — Plugin marketplace (recommended)

Add this repository as a marketplace and install the plugin:

```text
/plugin marketplace add ekline-io/ekline-docs-skills
/plugin install ekline-docs-skills
```

Claude Code fetches the plugin, registers all eight skills, and keeps them
updated when you re-run `/plugin marketplace update`.

## Option B — Git clone

Clone the repository into a Claude Code skills directory:

```bash
# Project-level (available in this project only)
git clone https://github.com/ekline-io/ekline-docs-skills.git \
  .claude/skills/ekline-docs-skills

# Or user-level (available in all projects)
git clone https://github.com/ekline-io/ekline-docs-skills.git \
  ~/.claude/skills/ekline-docs-skills
```

> **Self-contained skills.** Each skill directory bundles everything it needs
> (its `SKILL.md` plus any `scripts/` and `references/`), so individual skills
> are portable — you can copy or symlink a single `skills/<name>/` directory and
> it works on its own. This is also what lets the same skills run in Cursor and
> Codex (see those install guides).

## Verify the install

In Claude Code, the skills become available as `/`-commands. Confirm by running
a core skill that needs no setup:

```text
/changelog
/llms-txt
```

If the skills appear and run, the install is good.

## EkLine power-up prerequisites

The `review-docs` skill needs the EkLine CLI and a token. Every other skill runs
without them. Setup is identical across all tools — see
[EkLine CLI & token setup](ekline-cli.md).
