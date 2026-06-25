# Cross-Tool Documentation Skills Hub — Design

**Date:** 2026-06-25
**Status:** Approved (Milestone 1)
**Owner:** EkLine

## 1. Goal

Turn this repository into the public, open-source **hub for documentation and
technical-writing skills**, plus EkLine client plugins, that any technical
writer can install and use out of the box across multiple AI coding tools:
**Claude Code, Cursor, and Codex**.

The repo ships per-tool, hand-authored artifacts (no generator), keeps a
vendor-neutral core that works without any EkLine account, and offers EkLine
integrations as clearly-marked optional power-ups.

This spec covers **Milestone 1 (Foundation + Claude Code reference)** only.
Later milestones are sketched in §10 for context but are not designed here.

## 2. Locked decisions

These were settled during brainstorming and are inputs to this design:

1. **Cross-tool model: hand-maintained parallel sets** per tool. We evaluated a
   single-source generator (`rulesync`, which supports Claude Code / Cursor /
   Codex and Skills) and consciously declined it in favor of explicit per-tool
   control. Shared, tool-agnostic assets may still live once and be referenced.
2. **Positioning: vendor-neutral core + EkLine power-ups.** Most skills run with
   zero EkLine account; EkLine-powered skills are isolated and clearly marked.
3. **EkLine client mechanism is deferred.** Whether the EkLine integration ships
   as an MCP server, a per-tool CLI wrapper, or both is decided in a later
   milestone. The design keeps EkLine-powered code isolated so that choice is
   contained.
4. **Claude Code plugin stays at the repo root.** Validated against the
   superpowers multi-tool plugin: when a plugin is installed,
   `${CLAUDE_PLUGIN_ROOT}` is the plugin's own root, and any runtime asset a
   skill needs must be bundled inside that root. Nesting the plugin under
   `clients/claude-code/` while `shared/` sat at the repo root would put shared
   assets outside the plugin root. Keeping the plugin at the repo root makes
   `shared/` reachable and keeps the existing plugin working.
5. **Version bumps to `3.0.0`** to signal the structural shift.

## 3. Scope

### In scope (Milestone 1)

- Restructure the repo into the hub layout (§4).
- Introduce the `shared/` layer and move tool-agnostic assets into it now (§6).
- Tag every skill as `core` or `ekline` and surface that to users (§5).
- Rewrite `README.md` for the hub vision and add `docs/install/claude-code.md`
  (§7).
- Reserve `clients/cursor/` and `clients/codex/` as documented placeholders.
- Update `plugin.json` / `marketplace.json` descriptions and bump to `3.0.0`
  (§8).
- Verify the Claude Code plugin still loads and runs after the move (§9).

### Out of scope (Milestone 2+)

- Cursor artifacts (`.cursor/rules/*.mdc`, commands).
- Codex artifacts (`AGENTS.md`, `~/.codex/prompts/`).
- The EkLine client integration mechanism (MCP vs CLI).
- Any *new* skills or plugins beyond the existing eight.
- CI / upkeep automation and contribution tooling.

## 4. Target layout

```
/.claude-plugin/
   marketplace.json        # hub manifest (plugin source ".")
   plugin.json             # the Claude Code plugin, at repo root
/skills/                   # Claude Code skills = canonical reference
   changelog/SKILL.md
   check-links/SKILL.md
   docs-coverage/SKILL.md
   docs-freshness/SKILL.md
   llms-txt/SKILL.md
   review-docs/SKILL.md
   review-docs/scripts/run_review.py   # EkLine integration stays isolated here
   style-guide/SKILL.md
   terminology/SKILL.md
/shared/
   references/             # one copy, referenced by skills + later by Cursor/Codex
     style-rules.md
     terminology-rules.md
   scripts/                # one copy of the tool-agnostic core helpers
     parse_commits.py
     extract_links.py
     scan_exports.py
     extract_changes.py
     generate_llms_txt.py
/clients/
   cursor/README.md        # placeholder: "built in Milestone 2"
   codex/README.md         # placeholder: "built in Milestone 2"
/docs/
   install/claude-code.md  # full Claude Code install (M1)
   superpowers/specs/      # this spec and future specs
README.md                  # rewritten for the hub
LICENSE
.gitignore
```

Rationale for the `shared/` split:

- The five **core** helper scripts are tool-agnostic and become shared once.
- `run_review.py` is the **EkLine** integration and stays inside the
  `review-docs` skill, isolated, because its delivery mechanism is being
  redesigned in a later milestone (MCP vs CLI). Sharing it now would couple the
  deferred decision into the shared layer.

## 5. Skill tiering (vendor-neutral vs EkLine)

| Tier | Skills | Requires EkLine? |
|------|--------|------------------|
| **core** (out of the box) | `style-guide`, `terminology`, `check-links`, `docs-freshness`, `docs-coverage`, `changelog`, `llms-txt` | No |
| **ekline** (optional power-up) | `review-docs` | Yes — `ekline-cli` + token |

How the tier is surfaced:

- **Frontmatter:** add `metadata.tier: core | ekline` to every `SKILL.md`.
- **Requirements banner:** each `ekline`-tier skill opens with a one-line note
  stating it needs `ekline-cli` and a token, with a link to install steps.
- **README grouping:** skills are listed under "Works out of the box" and
  "EkLine-connected" headings so the distinction is obvious at a glance.

Skills remain **flat** under `skills/` (one directory per skill). We do not group
them into `skills/core/` vs `skills/ekline/` subfolders, to avoid risking Claude
Code's skill discovery, which expects `skills/<name>/SKILL.md`.

## 6. Shared-asset mechanism

> **Superseded by §11 (Milestone 2).** This `shared/` layer was reversed when M2
> research found that `SKILL.md` is now a cross-tool standard (Claude Code,
> Cursor, Codex) and that each asset is used by exactly one skill. Skills are now
> self-contained. This section is kept for historical context.

### File moves

| From | To |
|------|----|
| `skills/changelog/scripts/parse_commits.py` | `shared/scripts/parse_commits.py` |
| `skills/check-links/scripts/extract_links.py` | `shared/scripts/extract_links.py` |
| `skills/docs-coverage/scripts/scan_exports.py` | `shared/scripts/scan_exports.py` |
| `skills/docs-freshness/scripts/extract_changes.py` | `shared/scripts/extract_changes.py` |
| `skills/llms-txt/scripts/generate_llms_txt.py` | `shared/scripts/generate_llms_txt.py` |
| `skills/style-guide/references/style-rules.md` | `shared/references/style-rules.md` |
| `skills/terminology/references/terminology-rules.md` | `shared/references/terminology-rules.md` |
| `skills/review-docs/scripts/run_review.py` | *unchanged (stays isolated)* |

### SKILL.md updates

- All script invocations become plugin-root-relative:
  `python ${CLAUDE_PLUGIN_ROOT}/shared/scripts/<script>.py`. This also fixes a
  latent fragility — relative `python scripts/<x>.py` only resolves if the
  working directory happens to be the skill directory.
- `review-docs` invocation becomes
  `python ${CLAUDE_PLUGIN_ROOT}/skills/review-docs/scripts/run_review.py`.
- Reference-file paths in `style-guide` and `terminology` point to
  `${CLAUDE_PLUGIN_ROOT}/shared/references/<file>.md`.

### Payoff

In Milestone 2, the Cursor and Codex instruction files reference the same
`shared/` scripts and references (those tools consume the cloned repo directly),
so the *logic and rule content live once*; only the per-tool packaging is
hand-authored. Establishing `shared/` now is the foundation that makes M2 a
fill-in rather than a re-layout.

## 7. README and install docs

- **README.md** is rewritten to present the repo as the open-source hub for
  documentation skills across Claude Code, Cursor, and Codex, by EkLine. It
  contains: what it is, the skill catalog grouped by tier (§5), a per-tool
  install matrix (Claude Code = available; Cursor / Codex = coming soon),
  prerequisites for the EkLine tier, contributing pointer, and license.
- **docs/install/claude-code.md** documents both install paths: adding the
  marketplace and installing the plugin, and the `git clone` alternative into a
  `.claude/skills` directory. Includes the EkLine prerequisites for the
  `review-docs` skill.
- **clients/cursor/README.md** and **clients/codex/README.md** are short
  placeholders stating support arrives in Milestone 2, so the structure is
  visible without shipping empty promises.

## 8. Manifests and naming

- `plugin.json` and `marketplace.json`: update `description` to the
  hub / vendor-neutral framing; bump `version` to `3.0.0` in both.
- **Plugin name stays `ekline-docs-skills`.** Renaming would break existing
  installs and the marketplace identity. The friendlier "hub" title lives in the
  README, not in the manifest `name`.
- `marketplace.json` plugin `source` stays `"./"` (repo root is the plugin root).

## 9. Error handling, edge cases, and verification

### Edge cases

- **`${CLAUDE_PLUGIN_ROOT}` resolution.** Confirm the variable resolves for both
  marketplace installs and the `git clone` path during implementation; if a skill
  can run outside a plugin context, document the clone-based fallback in the
  install doc.
- **Windows paths.** Keep script invocations forward-slashed and rely on the
  Python interpreter for path handling; avoid shell-specific path assumptions.
- **EkLine tier failures** already have defined states in `run_review.py`
  (`cli_not_found`, `token_not_found`, `cli_failed`); the move does not change
  them.

### Verification (Milestone 1 is "done" when)

1. `plugin.json` and `marketplace.json` validate (run the `plugin-validator`
   agent).
2. All eight skills are still discovered by Claude Code.
3. At least one core skill (e.g., `changelog`) runs end-to-end with its helper
   now under `shared/` via `${CLAUDE_PLUGIN_ROOT}`.
4. A repo-wide search finds no dangling references to the old
   `skills/*/scripts/` or `skills/*/references/` paths (READMEs, SKILL.md files,
   docs).
5. The Vale and markdownlint configs remain removed (done in prior cleanup).

## 10. Roadmap (later milestones — context only, not designed here)

- **M2 — Cross-tool (done):** delivered as a portable `SKILL.md` set instead of
  hand-authored per-tool parallel sets — see §11.
- **M3 — EkLine client:** decide and build the EkLine integration mechanism
  (MCP server vs per-tool CLI wrapper vs both).
- **M4 — New skills/plugins:** additional documentation skills and EkLine client
  plugins.
- **M5 — Upkeep:** CI checks, contribution guide, release process to keep the
  hub current.

## 11. Milestone 2 — Portable SKILL.md (supersedes the shared/ layer)

### Finding

`SKILL.md` is now a native, cross-tool standard:

- **Cursor** (2.4+) supports Agent Skills — reads `SKILL.md`, discovers them in
  `.cursor/skills/` and `.agents/skills/` (plus the `~/...` globals), and also
  loads Claude and Codex skill directories.
- **Codex** (since Dec 2025) supports Agent Skills — a directory with `SKILL.md`
  plus optional scripts/references, discovered in `.codex/skills/`,
  `.agents/skills/` (scanned to the repo root), and `~/.codex/skills/`.

Both tools also read `~/.agents/skills/`, so a single install there serves both.
The premise behind hand-maintaining parallel per-tool sets — incompatible
formats — no longer holds; all three tools consume the same `SKILL.md`.

### Decision

Ship **one portable, self-contained `SKILL.md` set** and register it per tool,
rather than hand-authoring native Cursor/Codex artifacts.

### Changes from Milestone 1

- **Reverse the `shared/` layer.** Each script and reference moves back into its
  own skill directory; `shared/` is removed. Each asset was used by exactly one
  skill, so `shared/` provided no deduplication and only broke self-containment.
- **Self-contained paths.** Each SKILL.md invokes `scripts/<name>.py` and reads
  `references/<name>.md` relative to its own directory — portable across all
  three tools, with no `${CLAUDE_PLUGIN_ROOT}`.
- **Remove `clients/` placeholders.** There are no per-tool artifacts to author.
- **Install guides.** `docs/install/cursor.md` and `docs/install/codex.md`
  install via `~/.agents/skills/` (one install covers both). The EkLine CLI /
  token prerequisites are factored into the neutral `docs/install/ekline-cli.md`.
- **README** reframed around portable `SKILL.md`; the install matrix marks all
  three tools available.

### Retained from Milestone 1

Skill tiering (`metadata.tier` core/ekline), the EkLine requirements banner,
the manifest hub framing, and the `3.0.0` version bump all stand.

### Verification (Milestone 2 is "done" when)

1. No references to `shared/` or `${CLAUDE_PLUGIN_ROOT}` remain in skills, README,
   or docs.
2. Each skill is self-contained (its `scripts/` and/or `references/` sit inside
   the skill directory) and a core skill runs end-to-end from its own directory.
3. `plugin-validator` still passes; all eight skills remain discoverable.
4. Install guides exist for Claude Code, Cursor, and Codex, and the README matrix
   marks all three available.
