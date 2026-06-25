# Conventions — authoring & shipping

How to build and ship changes to this hub so everything stays cross-tool, free by
default, and consistent.

## Anatomy of a skill

```
skills/<name>/
  SKILL.md          required — the instructions + frontmatter
  scripts/          optional — helper scripts the skill runs
  references/       optional — rule files / data the skill reads
```

A skill is a **self-contained, portable unit**. You can copy or symlink a single
`skills/<name>/` directory and it works on its own — that is what makes it run in
Claude Code, Cursor, and Codex alike.

### SKILL.md frontmatter

```yaml
---
name: my-skill                     # kebab-case, must match the directory name
description: One sentence on what it does + "Use when…" so the agent knows when to
  invoke it. Be specific and trigger-oriented.
allowed-tools: Read, Edit, Glob, Bash   # Claude Code hint; ignored elsewhere, harmless
metadata:
  author: EkLine
  version: "3.0.0"
  tier: core                       # core (no account) | ekline (needs ekline-cli + token)
  argument-hint: "[arg ...]"       # optional
---
```

- `name` + `description` are the only load-bearing fields across all three tools.
  A sharp, "use when…" description is what makes the agent pick the skill correctly.
- `tier: ekline` skills must open with a Requirements banner (see `review-docs`) and
  link to setup via an **absolute GitHub URL** (skills install outside this repo).

### Path references inside SKILL.md

- Run scripts skill-relative: `python scripts/<name>.py $ARGUMENTS`.
- Read references skill-relative: `references/<name>.md`.
- **Never** use `${CLAUDE_PLUGIN_ROOT}` or `../../` — those break in Cursor/Codex.

### Helper script contract

- **Python, standard library only** — no `pip install`, so it runs out of the box.
- Print a single **JSON object to stdout**.
- Signal failure with an `"error"` field (e.g. `not_a_git_repo`, `not_a_directory`)
  rather than crashing; the SKILL.md documents how to handle each.
- Be **deterministic** and **bounded** (cap files/URLs processed, e.g. max 200).

## Adding a skill (checklist)

1. Create `skills/<name>/SKILL.md` (+ `scripts/`, `references/` as needed), following
   the anatomy above. Default to `tier: core`.
2. Verify the script runs from the skill dir and emits valid JSON.
3. Add a row to the README skill catalog and bump the **skill count** ("Six skills…").
4. Update the descriptions in `.claude-plugin/plugin.json` and
   `.claude-plugin/marketplace.json` if the skill changes the toolkit's summary.
5. No registration needed: Claude Code auto-discovers `skills/`; Cursor/Codex pick it
   up via `~/.agents/skills/` (see `docs/install/`).

## Removing a skill (checklist)

1. `git rm -r skills/<name>`.
2. Remove its README row; fix the skill count.
3. Scrub mentions from `plugin.json`, `marketplace.json`, and any install-doc examples
   (e.g. the `/verify` command list in `docs/install/claude-code.md`).
4. Grep the repo for the skill name and its outputs to catch stragglers.

## Shipping a release

- Bump the version in **`plugin.json`**, **`marketplace.json`** (top-level + plugin
  entry), and each skill's `metadata.version` together.
- Validate before committing:
  - `python3 -c "import json; json.load(open('.claude-plugin/plugin.json')); json.load(open('.claude-plugin/marketplace.json'))"`
  - Run a core skill's script end-to-end from its directory.
  - Grep for stale paths/refs (`shared/`, `${CLAUDE_PLUGIN_ROOT}`, removed skill names).
  - Optionally run the `plugin-validator` agent (plugin-dev) for a structural check.
- Work on a feature branch; commit in small, logically-scoped commits.

## Cross-tool install (how users consume this)

**Recommended, any tool:** [`npx skills`](https://github.com/vercel-labs/skills) — the
cross-tool skill package manager. `npx skills add ekline-io/ekline-docs-skills`
auto-detects the user's agent(s), discovers the skills in `skills/`, and installs the
chosen ones.

Native per-tool paths:

| Tool | Mechanism |
|------|-----------|
| Claude Code | Plugin marketplace (`/plugin install`) or clone into `.claude/skills/` |
| Cursor | Remote Rule (GitHub) import, or reads `.cursor/skills/` / `.agents/skills/` / `~/…` globals (GitHub import has a known 2026 bug where skills may not appear) |
| Codex | `$skill-installer install <url>` (to `~/.codex/skills/`), or reads `.codex/skills/` / `.agents/skills/` / `~/.codex/skills/` |

Cursor **and** Codex both read `~/.agents/skills/`, so one manual install there serves
both. Full steps live in `docs/install/`.

## Supported documentation file types

`.md`, `.mdx`, `.rst`, `.adoc`, `.txt`, `.html`
