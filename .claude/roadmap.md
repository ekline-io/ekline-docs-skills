# Roadmap & status

Where the hub is and where it's going. Update the status as milestones land.

## Done

- **M1 — Hub foundation.** Restructured the repo into the cross-tool hub: skill
  tiering (`core` / `ekline`), manifest reframing, version `3.0.0`, README hub
  framing, and the Claude Code install guide. (An interim `shared/` asset layer from
  this milestone was reversed in M2 — see [decisions.md](decisions.md).)
- **M2 — Portable cross-tool SKILL.md.** Made every skill self-contained and portable
  so the same `SKILL.md` runs natively in Claude Code, Cursor, and Codex. Added
  install guides for all three (Cursor/Codex via `~/.agents/skills/`) and the neutral
  `docs/install/ekline-cli.md` for the EkLine prerequisites.

## Next

### M3 — EkLine client mechanism (the deferred decision)
Decide and build how `review-docs` delivers its EkLine integration. Options on the
table:
- **MCP server** — build the EkLine integration once as an MCP server; all three
  tools connect natively. Best reliability; one server to publish/maintain.
- **Per-tool CLI wrapper** — keep shelling out to `ekline-cli` from the skill.
- **Both** — MCP primary, CLI fallback.
The integration is already isolated inside `review-docs`, so this can be done without
touching the other skills.

### M4 — New skills & EkLine plugins
Grow the catalog. Because skills are portable `SKILL.md`, each new skill works across
all three tools at once (follow [conventions.md](conventions.md)).

### M5 — Upkeep & contribution
- CI to validate manifests + `SKILL.md` frontmatter and run a smoke test of each
  helper script.
- A contribution guide (how to propose/add a skill).
- A repeatable release process.

## Open questions

- **M3:** MCP vs CLI vs both for the EkLine client — not yet decided.
- **CI:** what minimal automated checks give the most safety (manifest validity,
  skill discovery, script smoke tests)?
- **Distribution:** should we also publish to any tool-specific skill registries/
  marketplaces beyond the Claude Code marketplace?
