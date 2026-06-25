# EkLine Docs Skills — project guide

The open-source hub for **documentation & technical-writing skills** that run inside
AI coding tools (Claude Code, Cursor, Codex), maintained by EkLine. This file is the
entry point; deeper context lives in [`.claude/`](.claude/).

## What this is

A set of portable `SKILL.md` skills that help technical writers review, lint, and
maintain docs. Most work with **no account or API key**; one optionally connects to
EkLine.

## North star (ethos)

- **Usable out of the box.** A technical writer should install and get value with
  zero setup. Never gate the core behind an account.
- **One skill, every tool.** Author each skill once as a self-contained `SKILL.md`;
  it runs natively in Claude Code, Cursor, and Codex. No generators, no per-tool
  rewrites.
- **Vendor-neutral core + EkLine power-ups.** The core is tool-agnostic and free;
  EkLine integrations are clearly marked, optional add-ons.
- **Self-contained & deterministic.** Each skill bundles its own scripts/references;
  helper scripts are stdlib-only Python that emit JSON.

## Golden rules (read before changing things)

1. **Keep skills self-contained.** `skills/<name>/` holds its own `SKILL.md` +
   `scripts/` + `references/`. There is no `shared/` layer. Paths inside `SKILL.md`
   are skill-relative (`scripts/x.py`, `references/x.md`) — never
   `${CLAUDE_PLUGIN_ROOT}` (it does not exist in Cursor/Codex).
2. **Core stays free.** New skills default to `metadata.tier: core` and must not
   require an EkLine account. Only EkLine-powered skills get `tier: ekline` plus a
   Requirements banner.
3. **Cross-tool by default.** Don't put Claude-Code-only constructs in skill bodies.
   The same `SKILL.md` must work in all three tools.
4. **Helper scripts:** Python, standard library only (no pip installs), print JSON to
   stdout, signal failure with an `"error"` field, and cap their work (e.g. max N
   files).
5. **Update the surface together.** Adding/removing a skill means updating the README
   catalog + skill count and the descriptions in `.claude-plugin/plugin.json` and
   `marketplace.json`.
6. **Doc links inside skills** that point at this repo use absolute GitHub URLs
   (skills install outside the repo, so relative paths break).

## Repo map

| Path | What |
|------|------|
| `skills/<name>/` | The skills — `SKILL.md` (+ `scripts/`, `references/`) |
| `.claude-plugin/` | Claude Code plugin (`plugin.json`) + marketplace (`marketplace.json`) |
| `docs/install/` | Per-tool install guides (claude-code, cursor, codex, ekline-cli) |
| `docs/superpowers/` | Internal design specs — **gitignored**, not published |

## Deeper context in `.claude/`

- [decisions.md](.claude/decisions.md) — the engineering decision log (what we chose and why)
- [conventions.md](.claude/conventions.md) — how to author a skill and ship an update

## Current state

Version **3.0.0**. Six skills: `style-guide`, `terminology`, `check-links`,
`docs-coverage`, `changelog` (core) + `review-docs` (EkLine power-up). Milestones
**M1 (hub foundation)** and **M2 (portable cross-tool SKILL.md)** are done;
**M3 (EkLine client mechanism)** is next.
