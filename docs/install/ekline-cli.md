# EkLine CLI & token setup

These steps are required **only** for the `review-docs` skill, the one
EkLine-connected power-up. Every other skill in this toolkit runs with no
account or API key — skip this page if you only use the core skills.

This setup is identical across Claude Code, Cursor, and Codex.

## 1. Install `ekline-cli`

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

## 2. Set your EkLine token

Get a token from the [EkLine Dashboard](https://ekline.io/dashboard) and export
it:

```bash
export EKLINE_EK_TOKEN=your_token_here
```

`EK_TOKEN` is also accepted.

## 3. Optional: project config

If your project has an `ekline.config.json`, the CLI picks up its settings
automatically (style guide, framework, ignore rules, and so on).

## Environment variables

| Variable | Description |
|----------|-------------|
| `EKLINE_EK_TOKEN` or `EK_TOKEN` | EkLine API token (for `review-docs`) |
| `EKLINE_CLI` | Path to the `ekline-cli` binary if it is not on `PATH` |
