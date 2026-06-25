# Install for Codex

Codex supports [Agent Skills](https://developers.openai.com/codex/skills) natively
(since December 2025) and a [plugin system](https://developers.openai.com/codex/plugins)
that bundles them. This repo ships both the skills and a `.codex-plugin/` manifest, so
pick whichever install fits.

## Option A — `npx skills` (recommended)

[`npx skills`](https://github.com/vercel-labs/skills) is a cross-tool package manager
for agent skills. It installs straight into Codex:

```bash
npx skills add ekline-io/ekline-docs-skills -a codex
```

It lists the six skills and lets you choose which to install (drop `-a codex` to let
it auto-detect every agent you have). Install a single skill with `--skill <name>`.

## Option B — Native Codex plugin

This repo is packaged as a Codex plugin (`.codex-plugin/plugin.json` plus a
`.agents/plugins/marketplace.json`). Add the marketplace from GitHub, then install the
plugin from the browser:

```bash
codex plugin marketplace add ekline-io/ekline-docs-skills
```

Then open the plugin browser inside Codex and install **ekline-docs-skills**:

```text
/plugins
```

Installing the plugin registers all six skills at once. (No hot-reload — new skills
take effect in a new session.)

## Option C — Single skill via `$skill-installer`

To grab one skill without the plugin, run the built-in installer inside Codex with the
skill's GitHub URL, then restart Codex:

```text
$skill-installer install https://github.com/ekline-io/ekline-docs-skills/tree/main/skills/review-docs
```

Swap the trailing skill name for any of `changelog`, `check-links`, `docs-coverage`,
`style-guide`, `terminology`. Skills install to `~/.codex/skills/`.

## Option D — Manual (symlink or copy)

Codex also reads `.agents/skills/` (scanned from your working directory up to the repo
root) and `~/.agents/skills/`. Installing into `~/.agents/skills/` covers **both Codex
and Cursor** at once:

```bash
git clone https://github.com/ekline-io/ekline-docs-skills.git && cd ekline-docs-skills
mkdir -p ~/.agents/skills
for d in skills/*/; do ln -sfn "$(pwd)/$d" ~/.agents/skills/"$(basename "$d")"; done
```

Replace `ln -sfn` with `cp -R "$d" ~/.agents/skills/` to copy instead of symlink.

## Using the skills

Codex loads a skill automatically when your task matches its description, or you can
invoke one explicitly with `/skills` or by typing `$` to mention it. The proactive
skills (`style-guide`, `terminology`) trigger when you work on documentation files.

## EkLine power-up (optional)

Only the `review-docs` skill needs the EkLine CLI and a token. Setup is the same
across all tools — see [EkLine CLI & token setup](ekline-cli.md).
