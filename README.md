# EkLine Docs Skills

**The open-source hub for documentation & technical-writing skills across AI coding tools** — by [EkLine](https://ekline.io).

A growing collection of skills that help technical writers and engineers review, lint, and maintain their documentation directly inside their AI coding tool. Most skills work **out of the box with no account or API key**. A few optional skills connect to EkLine for deeper review.

> **One skill set, every tool.** These skills use the portable [`SKILL.md`](https://cursor.com/docs/skills) standard — supported natively by Claude Code, Cursor, and Codex — so the same skills install into all three with no rewriting (see [Installation](#installation)).

## Skills

Six skills, in two tiers.

### Works out of the box (no EkLine account)

| Skill | What it does |
|-------|--------------|
| [`style-guide`](skills/style-guide/SKILL.md) | Enforces voice, tone, and formatting — active voice, second person, present tense, banned phrases, heading case. |
| [`terminology`](skills/terminology/SKILL.md) | Checks documentation for consistent, approved terminology and flags prohibited or inconsistent terms. |
| [`check-links`](skills/check-links/SKILL.md) | Finds broken internal links and missing anchors, optionally validates external URLs, detects orphaned pages. |
| [`docs-coverage`](skills/docs-coverage/SKILL.md) | Measures what percentage of your public API surface is documented (TypeScript, Python, Go). |
| [`changelog`](skills/changelog/SKILL.md) | Generates structured changelog entries from git history in [Keep a Changelog](https://keepachangelog.com/) format. |

### EkLine-connected (optional power-up)

| Skill | What it does | Requires |
|-------|--------------|----------|
| [`review-docs`](skills/review-docs/SKILL.md) | Runs the [EkLine Docs Reviewer](https://docs.ekline.io/reviewer/overview/) on your docs and applies recommended fixes. | `ekline-cli` + token |

## Installation

| Tool | Status | Guide |
|------|--------|-------|
| **Claude Code** | ✅ Available | [docs/install/claude-code.md](docs/install/claude-code.md) |
| **Cursor** | ✅ Available | [docs/install/cursor.md](docs/install/cursor.md) |
| **Codex** | ✅ Available | [docs/install/codex.md](docs/install/codex.md) |

**Claude Code** — add the marketplace and install the plugin:

```text
/plugin marketplace add ekline-io/ekline-docs-skills
/plugin install ekline-docs-skills
```

**Cursor & Codex** — both read `~/.agents/skills/`, so one install covers both:

```bash
git clone https://github.com/ekline-io/ekline-docs-skills.git && cd ekline-docs-skills
mkdir -p ~/.agents/skills
for d in skills/*/; do ln -sfn "$(pwd)/$d" ~/.agents/skills/"$(basename "$d")"; done
```

Full per-tool steps are in the install guides linked above.

## EkLine power-up prerequisites

Only the `review-docs` skill needs these; every other skill runs without them. Setup is identical across all tools — see [EkLine CLI & token setup](docs/install/ekline-cli.md).

## Customizing rules

Each skill bundles its own rules:

- **Style rules** — [`skills/style-guide/references/style-rules.md`](skills/style-guide/references/style-rules.md)
- **Terminology rules** — [`skills/terminology/references/terminology-rules.md`](skills/terminology/references/terminology-rules.md)

## Repository layout

```
.claude-plugin/      Claude Code plugin + marketplace manifests
skills/              Portable SKILL.md skills — self-contained (each ships its
                     own scripts/ and references/), work in all three tools
docs/install/        Per-tool installation guides
```

## Supported file types

`.md`, `.mdx`, `.rst`, `.adoc`, `.txt`, `.html`

## Contributing

This is an open-source hub — contributions of new documentation skills are welcome. Because the skills use the portable SKILL.md standard, a new skill works across Claude Code, Cursor, and Codex at once. Open an issue or pull request.

## License

[MIT](LICENSE)
