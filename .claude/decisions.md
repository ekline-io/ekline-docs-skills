# Engineering decisions

The decisions that shape this repo, with the reasoning behind them. When you make a
significant architectural or product decision, add it here — capture the *why*, not
just the *what*, and note any decision it supersedes.

---

## Ethos & positioning

### Vendor-neutral core + EkLine power-ups
The hub is positioned so any technical writer can use it **out of the box with no
EkLine account**. The core skills are tool-agnostic and free. EkLine integrations are
optional, clearly-marked power-ups (`metadata.tier: ekline`) with a Requirements
banner. Today only `review-docs` is an EkLine skill.
**Why:** maximizes adoption and trust; the funnel to EkLine comes from value, not a
gate.

---

## Architecture

### Cross-tool delivery = one portable, self-contained `SKILL.md` set
**Decision:** Ship a single self-contained `SKILL.md` set and register it per tool.
No generator, no hand-authored per-tool artifacts.
**Why:** `SKILL.md` is now a native standard in Claude Code, Cursor (2.4+), and Codex
(skills launched Dec 2025). Cursor and Codex both also read `~/.agents/skills/`, so
one install covers both. This delivers the cross-tool goal with the least
duplication.
**Consequences:** each skill is self-contained (its `scripts/` and `references/` live
inside the skill dir); `SKILL.md` paths are skill-relative, never
`${CLAUDE_PLUGIN_ROOT}` (which only exists in Claude Code).
**Evolution (important):** we first chose "hand-maintain parallel sets per tool" and
explicitly rejected a single-source generator (`rulesync`) — under the assumption the
three tools had incompatible formats. Discovering native `SKILL.md` support in all
three invalidated that premise, so we pivoted. This is why an early `shared/` layer
(M1) was reversed in M2.

### No `shared/` layer — skills are self-contained
We briefly centralized helper scripts and rule files into a top-level `shared/`
directory (M1), then reversed it (M2).
**Why reversed:** each script/reference is used by exactly one skill, so `shared/`
deduplicated nothing — and it broke the self-containment that Cursor/Codex need to
discover a skill as a portable unit.

### Claude Code plugin lives at the repo root
The repo root *is* the plugin root (`.claude-plugin/` + `skills/` at root).
**Why:** when a plugin installs, `${CLAUDE_PLUGIN_ROOT}` resolves to the plugin's own
root, so anything a skill needs at runtime must be bundled inside it. Keeping the
plugin at the repo root keeps everything reachable. (Validated against the
superpowers multi-tool plugin layout.)

### EkLine client mechanism — deferred (M3)
How `review-docs` ships its EkLine integration — an MCP server, a per-tool CLI
wrapper, or both — is **undecided**. The integration is kept isolated inside the
`review-docs` skill (it is the only skill touching `ekline-cli`) so the choice stays
contained and can be made without disturbing the rest.

---

## Product / housekeeping

### Versioning: `3.0.0` for the hub restructure
The cross-tool hub restructure bumped `plugin.json`, `marketplace.json`, and every
skill's `metadata.version` to `3.0.0`. The plugin **name** stays `ekline-docs-skills`
(renaming would break existing installs and the marketplace identity).

### Internal design specs are not published
`docs/superpowers/` holds brainstorming/design specs. It is **gitignored** — working
material, not part of the public hub. Curated, durable project knowledge lives in
`.claude/` (this directory) instead.

