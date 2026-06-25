# EkLine Docs Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Works in Claude Code · Cursor · Codex](https://img.shields.io/badge/works%20in-Claude%20Code%20%C2%B7%20Cursor%20%C2%B7%20Codex-5b21b6)
![Skills: 6](https://img.shields.io/badge/skills-6-0ea5e9)

**Documentation and technical-writing skills for your AI coding agent.** Review,
lint, and maintain your docs without leaving Claude Code, Cursor, or Codex — by
[EkLine](https://ekline.io).

- **Works out of the box** — five of the six skills need no account or API key.
- **One install, every tool** — the same skills run natively in Claude Code,
  Cursor, and Codex.
- **Free core, optional EkLine power-ups** — use the core forever; connect EkLine
  when you want its deeper review.

## Why

Docs drift from code, links rot, and the same term gets written three different
ways. These skills put a documentation reviewer inside the agent you already write
with — so you catch issues, generate changelogs, and measure coverage in the same
place you edit, instead of bolting on a separate pipeline.

## What you get

### Core — no account needed

| Skill | What it does |
|-------|--------------|
| [`style-guide`](skills/style-guide/SKILL.md) | Enforces voice, tone, and formatting — active voice, second person, present tense, banned phrases, heading case. |
| [`terminology`](skills/terminology/SKILL.md) | Keeps terminology consistent and flags prohibited or inconsistent terms. |
| [`check-links`](skills/check-links/SKILL.md) | Finds broken internal links and missing anchors, optionally validates external URLs, and detects orphaned pages. |
| [`docs-coverage`](skills/docs-coverage/SKILL.md) | Measures how much of your public API surface is documented (TypeScript, Python, Go). |
| [`changelog`](skills/changelog/SKILL.md) | Generates structured changelog entries from git history in [Keep a Changelog](https://keepachangelog.com/) format. |

### EkLine power-up — optional

| Skill | What it does | Needs |
|-------|--------------|-------|
| [`review-docs`](skills/review-docs/SKILL.md) | Runs the [EkLine Docs Reviewer](https://docs.ekline.io/reviewer/overview/) on your docs and applies the recommended fixes. | `ekline-cli` + token |

## Quick start

### Fastest — any tool

[`npx skills`](https://github.com/vercel-labs/skills) is a cross-tool package manager
for agent skills. It auto-detects Claude Code, Cursor, and Codex, lists the six
skills, and installs the ones you pick:

```bash
npx skills add ekline-io/ekline-docs-skills
```

Target specific tools with `-a` (e.g. `-a cursor -a codex`), or grab one skill with
`--skill review-docs`.

### Native per-tool install

Each tool has its own plugin/skill system, and this repo is packaged as a native plugin
for all three (`.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`).

- **Claude Code** — `/plugin marketplace add ekline-io/ekline-docs-skills`, then
  `/plugin install ekline-docs-skills`.
- **Codex** — `codex plugin marketplace add ekline-io/ekline-docs-skills`, then install
  **ekline-docs-skills** from the `/plugins` browser.
- **Cursor** — Customize → Rules → Add Rule → **Remote Rule (GitHub)** → paste the repo
  URL (a `.cursor-plugin` manifest is included for marketplace publishing too).

Full steps, global vs per-project installs, and manual fallbacks are in the per-tool
guides: [Claude Code](docs/install/claude-code.md) · [Cursor](docs/install/cursor.md)
· [Codex](docs/install/codex.md).

## Using the skills

Once installed, your agent picks the right skill automatically from your request.
You can also invoke one explicitly — in Cursor type `/` and choose it; in Codex use
`/skills` or `$`. The proactive skills (`style-guide`, `terminology`) trigger on
their own when you edit documentation files.

Try saying:

| You want to… | Ask your agent | Skill |
|--------------|----------------|-------|
| Review docs for style and best practices | *“review the docs in ./docs”* | `review-docs` |
| Find broken links | *“check ./docs for broken links”* (add external URLs too) | `check-links` |
| Draft a changelog | *“generate a changelog for v1.2.0..v1.3.0”* | `changelog` |
| See what's undocumented | *“what's the doc coverage for ./src”* | `docs-coverage` |
| Enforce style and terminology | happens automatically as you edit docs | `style-guide`, `terminology` |

## EkLine power-up (optional)

Only `review-docs` needs the EkLine CLI and a token; every other skill runs without
them. Setup is the same across all tools — see
[EkLine CLI & token setup](docs/install/ekline-cli.md).

## Customizing rules

The style and terminology checks read editable rule files you can tune to your
house style:

- **Style rules** — [`skills/style-guide/references/style-rules.md`](skills/style-guide/references/style-rules.md)
- **Terminology rules** — [`skills/terminology/references/terminology-rules.md`](skills/terminology/references/terminology-rules.md)

**Supported file types:** `.md`, `.mdx`, `.rst`, `.adoc`, `.txt`, `.html`

## How it works

Each skill is a self-contained, portable
[`SKILL.md`](https://cursor.com/docs/skills) directory — the open standard now read
natively by Claude Code, Cursor, and Codex. Install a skill once and it works in all
three; no per-tool rewrites.

```
.claude-plugin/   Claude Code plugin + marketplace manifests
skills/<name>/     SKILL.md (+ scripts/, references/) — self-contained, portable
docs/install/      Per-tool installation guides
```

## Contributing

Contributions of new documentation skills are welcome. Because skills use the
portable SKILL.md standard, a new skill works across Claude Code, Cursor, and Codex
at once. See [`.claude/conventions.md`](.claude/conventions.md) for how to author and
ship one, then open an issue or pull request.

## License

[MIT](LICENSE)
