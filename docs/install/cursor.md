# Install for Cursor

Cursor (2.4+) supports [Agent Skills](https://cursor.com/docs/skills) natively —
it reads the same `SKILL.md` files this repo ships, so there is nothing to
rewrite. Cursor discovers skills from `.cursor/skills/` and `.agents/skills/`
(project) and `~/.cursor/skills/` and `~/.agents/skills/` (global), and also
loads skills from Claude and Codex directories.

## Install (global — recommended)

Installing into `~/.agents/skills/` makes the skills available in **both Cursor
and Codex** at once.

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

## Install (single project)

To scope the skills to one project, symlink or copy them into that project's
`.cursor/skills/` (or `.agents/skills/`) directory instead:

```bash
mkdir -p /path/to/project/.cursor/skills
for d in skills/*/; do
  ln -sfn "$(pwd)/$d" /path/to/project/.cursor/skills/"$(basename "$d")"
done
```

## Using the skills

Cursor applies a skill automatically when your task matches its description, or
you can invoke one explicitly by typing `/` in chat and picking it by name. The
proactive skills (`style-guide`, `terminology`) trigger when you work on
documentation files.

## EkLine power-up (optional)

Only the `review-docs` skill needs the EkLine CLI and a token. Setup is the same
across all tools — see [EkLine CLI & token setup](ekline-cli.md).
