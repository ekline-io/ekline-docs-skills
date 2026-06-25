# Install for Cursor

Cursor (2.4+) supports [Agent Skills](https://cursor.com/docs/skills) natively — it
reads the same `SKILL.md` files this repo ships, so there is nothing to rewrite.
Pick whichever install fits.

## Option A — `npx skills` (recommended)

[`npx skills`](https://github.com/vercel-labs/skills) is a cross-tool package manager
for agent skills. It installs straight into Cursor:

```bash
npx skills add ekline-io/ekline-docs-skills -a cursor
```

It lists the six skills and lets you choose which to install (drop `-a cursor` to let
it auto-detect every agent you have). Skills land in `.agents/skills/` for the
project, which Cursor reads.

Install a single skill with `--skill`:

```bash
npx skills add ekline-io/ekline-docs-skills -a cursor --skill review-docs
```

## Option B — Import from GitHub (native)

Cursor can import skills from a repository URL:

1. Open **Customize** in the sidebar → **Rules** → **Add Rule**.
2. Choose **Remote Rule (GitHub)**.
3. Paste `https://github.com/ekline-io/ekline-docs-skills`.

Cursor keeps the import synced with the source repository.

> **Known issue (2026).** Some Cursor versions accept the GitHub import but don't list
> the skills under **Settings → Skills**. If that happens, use Option A or C.

> **Plugin packaging.** This repo also ships a `.cursor-plugin/plugin.json` manifest,
> so it can be published to and installed from the
> [Cursor plugin marketplace](https://cursor.com/docs/plugins). Until it is published
> there, use Option A or C.

## Option C — Manual (symlink or copy)

Cursor discovers skills from `.cursor/skills/` and `.agents/skills/` (project) and
`~/.cursor/skills/` and `~/.agents/skills/` (global). Installing into
`~/.agents/skills/` covers **both Cursor and Codex** at once:

```bash
git clone https://github.com/ekline-io/ekline-docs-skills.git && cd ekline-docs-skills
mkdir -p ~/.agents/skills
for d in skills/*/; do ln -sfn "$(pwd)/$d" ~/.agents/skills/"$(basename "$d")"; done
```

Symlinks keep the skills updated when you `git pull`. To copy instead (for example on
Windows without developer mode), replace the `ln -sfn` line with
`cp -R "$d" ~/.agents/skills/`.

## Using the skills

Cursor applies a skill automatically when your task matches its description, or you
can invoke one explicitly by typing `/` in chat and picking it by name. The proactive
skills (`style-guide`, `terminology`) trigger when you work on documentation files.

## EkLine power-up (optional)

Only the `review-docs` skill needs the EkLine CLI and a token. Setup is the same
across all tools — see [EkLine CLI & token setup](ekline-cli.md).
