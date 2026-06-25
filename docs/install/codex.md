# Install for Codex

Codex supports [Agent Skills](https://developers.openai.com/codex/skills)
natively (since December 2025) — it reads the same `SKILL.md` files this repo
ships, so there is nothing to rewrite. Codex discovers skills from
`.codex/skills/` and `.agents/skills/` (scanned from your working directory up
to the repository root) and from `~/.codex/skills/` and `~/.agents/skills/`
(personal).

## Install (personal — recommended)

Installing into `~/.agents/skills/` makes the skills available in **both Codex
and Cursor** at once.

```bash
git clone https://github.com/ekline-io/ekline-docs-skills.git
cd ekline-docs-skills

mkdir -p ~/.agents/skills
for d in skills/*/; do
  ln -sfn "$(pwd)/$d" ~/.agents/skills/"$(basename "$d")"
done
```

Symlinks keep the skills updated when you `git pull`. To copy instead of
symlink (for example on Windows without developer mode), replace the `ln -sfn`
line with `cp -R "$d" ~/.agents/skills/`.

## Install (single project, committed)

To share the skills with everyone on a project, check them into the project's
`.codex/skills/` directory:

```bash
mkdir -p /path/to/project/.codex/skills
for d in skills/*/; do
  cp -R "$d" /path/to/project/.codex/skills/
done
```

## Using the skills

Codex loads a skill automatically when your task matches its description, or you
can invoke one explicitly with `/skills` or by typing `$` to mention it. The
proactive skills (`style-guide`, `terminology`) trigger when you work on
documentation files.

## EkLine power-up (optional)

Only the `review-docs` skill needs the EkLine CLI and a token. Setup is the same
across all tools — see [EkLine CLI & token setup](ekline-cli.md).
