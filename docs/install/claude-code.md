# Install for Claude Code

EkLine Docs Skills ships as a Claude Code plugin. The seven core skills work
with no account or API key; the optional `review-docs` skill needs the EkLine
CLI and a token (see [prerequisites](#ekline-power-up-prerequisites)).

## Option A — Plugin marketplace (recommended)

Add this repository as a marketplace and install the plugin:

```text
/plugin marketplace add ekline-io/ekline-docs-skills
/plugin install ekline-docs-skills
```

Claude Code fetches the plugin, registers all eight skills, and keeps them
updated when you re-run `/plugin marketplace update`.

## Option B — Git clone

Clone the repository into a Claude Code skills directory:

```bash
# Project-level (available in this project only)
git clone https://github.com/ekline-io/ekline-docs-skills.git \
  .claude/skills/ekline-docs-skills

# Or user-level (available in all projects)
git clone https://github.com/ekline-io/ekline-docs-skills.git \
  ~/.claude/skills/ekline-docs-skills
```

> **Note on shared assets.** Skills load helper scripts from `shared/scripts/`
> and rule files from `shared/references/`, resolved relative to the plugin
> root. Cloning the **whole repository** (as above) keeps those paths intact.
> Do not copy individual `skills/<name>/` directories on their own — they depend
> on the `shared/` layer.

## Verify the install

In Claude Code, the skills become available as `/`-commands. Confirm by running
a core skill that needs no setup:

```text
/changelog
/llms-txt
```

If the skills appear and run, the install is good.

## EkLine power-up prerequisites

These are required **only** for the `review-docs` skill. Skip this section if
you only use the core skills.

### 1. Install `ekline-cli`

**macOS:**

```bash
curl -L https://github.com/ekline-io/ekline-cli-binaries/releases/latest/download/ekline-cli-macos.tar.gz | tar xz
chmod +x ekline-cli
sudo mv ekline-cli /usr/local/bin/
```

**Linux:**

```bash
curl -L https://github.com/ekline-io/ekline-cli-binaries/releases/latest/download/ekline-cli-linux.tar.gz | tar xz
chmod +x ekline-cli
sudo mv ekline-cli /usr/local/bin/
```

**Windows:**

Download `ekline-cli-windows.zip` from the
[release page](https://github.com/ekline-io/ekline-cli-binaries/releases/latest)
and add it to your `PATH`.

If the binary is not on your `PATH`, set `EKLINE_CLI` to its full path.

### 2. Set your EkLine token

Get a token from the [EkLine Dashboard](https://ekline.io/dashboard) and export
it:

```bash
export EKLINE_EK_TOKEN=your_token_here
```

`EK_TOKEN` is also accepted.

### 3. Optional: project config

If your project has an `ekline.config.json`, the CLI picks up its settings
automatically (style guide, framework, ignore rules, and so on).

## Environment variables

| Variable | Description |
|----------|-------------|
| `EKLINE_EK_TOKEN` or `EK_TOKEN` | EkLine API token (for `review-docs`) |
| `EKLINE_CLI` | Path to the `ekline-cli` binary if it is not on `PATH` |
