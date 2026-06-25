# EkLine Docs Skills

**The open-source hub for documentation & technical-writing skills across AI coding tools** — by [EkLine](https://ekline.io).

A growing collection of skills that help technical writers and engineers review, lint, and maintain their documentation directly inside their AI coding tool. Most skills work **out of the box with no account or API key**. A few optional skills connect to EkLine for deeper review.

> **Cross-tool roadmap.** Claude Code is supported today. Cursor and Codex are next — the repo is structured so each tool gets its own hand-authored, native artifacts (see [Installation](#installation)).

## Skills

Eight skills, in two tiers.

### Works out of the box (no EkLine account)

| Skill | What it does |
|-------|--------------|
| [`style-guide`](skills/style-guide/SKILL.md) | Enforces voice, tone, and formatting — active voice, second person, present tense, banned phrases, heading case. |
| [`terminology`](skills/terminology/SKILL.md) | Checks documentation for consistent, approved terminology and flags prohibited or inconsistent terms. |
| [`check-links`](skills/check-links/SKILL.md) | Finds broken internal links and missing anchors, optionally validates external URLs, detects orphaned pages. |
| [`docs-freshness`](skills/docs-freshness/SKILL.md) | Detects stale docs by comparing recent code changes against documentation. |
| [`docs-coverage`](skills/docs-coverage/SKILL.md) | Measures what percentage of your public API surface is documented (TypeScript, Python, Go). |
| [`changelog`](skills/changelog/SKILL.md) | Generates structured changelog entries from git history in [Keep a Changelog](https://keepachangelog.com/) format. |
| [`llms-txt`](skills/llms-txt/SKILL.md) | Generates an [`llms.txt`](https://llmstxt.org) file to make your docs discoverable by LLMs. |

### EkLine-connected (optional power-up)

| Skill | What it does | Requires |
|-------|--------------|----------|
| [`review-docs`](skills/review-docs/SKILL.md) | Runs the [EkLine Docs Reviewer](https://docs.ekline.io/reviewer/overview/) on your docs and applies recommended fixes. | `ekline-cli` + token |

## Installation

| Tool | Status | Guide |
|------|--------|-------|
| **Claude Code** | ✅ Available | [docs/install/claude-code.md](docs/install/claude-code.md) |
| **Cursor** | 🔜 Coming soon | [clients/cursor/](clients/cursor/) |
| **Codex** | 🔜 Coming soon | [clients/codex/](clients/codex/) |

The fastest path for Claude Code:

```bash
# Add this repo as a plugin marketplace, then install the plugin
/plugin marketplace add ekline-io/ekline-docs-skills
/plugin install ekline-docs-skills
```

Full steps, including the `git clone` alternative and EkLine prerequisites, are in the [Claude Code install guide](docs/install/claude-code.md).

## EkLine power-up prerequisites

Only the `review-docs` skill needs these. Everything else runs without them.

- **`ekline-cli`** — install per the [Claude Code install guide](docs/install/claude-code.md#ekline-power-up-prerequisites).
- **EkLine token** — get one from the [EkLine Dashboard](https://ekline.io/dashboard) and set `EKLINE_EK_TOKEN` (or `EK_TOKEN`).

## Customizing rules

Rules live in the shared layer so every tool reads the same source:

- **Style rules** — [`shared/references/style-rules.md`](shared/references/style-rules.md)
- **Terminology rules** — [`shared/references/terminology-rules.md`](shared/references/terminology-rules.md)

## Repository layout

```
.claude-plugin/      Claude Code plugin + marketplace manifests
skills/              Claude Code skills (canonical reference)
shared/
  references/        Style & terminology rules (one source of truth)
  scripts/           Tool-agnostic helper scripts
clients/             Per-tool artifacts (cursor/, codex/ — coming soon)
docs/install/        Per-tool installation guides
```

## Supported file types

`.md`, `.mdx`, `.rst`, `.adoc`, `.txt`, `.html`

## Contributing

This is an open-source hub — contributions of new documentation skills and per-tool ports are welcome. Open an issue or pull request.

## License

[MIT](LICENSE)
