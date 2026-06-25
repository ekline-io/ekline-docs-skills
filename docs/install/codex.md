# Install for Codex

Codex supports [Agent Skills](https://developers.openai.com/codex/skills) natively
(since December 2025) — it reads the same `SKILL.md` files this repo ships, so there
is nothing to rewrite. Pick whichever install fits.

## Option A — `npx skills` (recommended)

[`npx skills`](https://github.com/vercel-labs/skills) is a cross-tool package manager
for agent skills. It installs straight into Codex:

```bash
npx skills add ekline-io/ekline-docs-skills -a codex
```

It lists the six skills and lets you choose which to install (drop `-a codex` to let
it auto-detect every agent you have). Install a single skill with
`--skill <name>`.

## Option B — `$skill-installer` (native, inside Codex)

Codex ships a built-in installer. From inside a Codex session, install a skill by its
GitHub URL, then restart Codex so it loads:

```text
$skill-installer install https://github.com/ekline-io/ekline-docs-skills/tree/main/skills/review-docs
```

Repeat per skill, swapping the trailing skill name (`changelog`, `check-links`,
`docs-coverage`, `style-guide`, `terminology`). Skills install to `~/.codex/skills/`.
Restart Codex to pick them up.

## Option C — Manual (symlink or copy)

Codex discovers skills from `.codex/skills/` and `.agents/skills/` (scanned from your
working directory up to the repo root) and from `~/.codex/skills/` and
`~/.agents/skills/` (personal). Installing into `~/.agents/skills/` covers **both
Codex and Cursor** at once:

```bash
git clone https://github.com/ekline-io/ekline-docs-skills.git && cd ekline-docs-skills
mkdir -p ~/.agents/skills
for d in skills/*/; do ln -sfn "$(pwd)/$d" ~/.agents/skills/"$(basename "$d")"; done
```

Symlinks keep the skills updated when you `git pull`. To copy instead (for example on
Windows without developer mode), replace the `ln -sfn` line with
`cp -R "$d" ~/.agents/skills/`. To share with a whole project, check the skill
directories into the project's `.codex/skills/`.

## Using the skills

Codex loads a skill automatically when your task matches its description, or you can
invoke one explicitly with `/skills` or by typing `$` to mention it. The proactive
skills (`style-guide`, `terminology`) trigger when you work on documentation files.

## EkLine power-up (optional)

Only the `review-docs` skill needs the EkLine CLI and a token. Setup is the same
across all tools — see [EkLine CLI & token setup](ekline-cli.md).
