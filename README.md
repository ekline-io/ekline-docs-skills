# EkLine Docs Reviewer Plugin for Claude Code

A Claude Code plugin that reviews, fixes, and improves your documentation using [EkLine](https://ekline.io) and built-in style and terminology checks.

## Skills

### `review-docs`

Runs [EkLine Docs Reviewer](https://docs.ekline.io/reviewer/overview/) on your documentation and applies recommended fixes.

```
/review-docs ./docs
/review-docs docs/guide.md docs/api.md
```

- Reviews a directory, specific files, or just uncommitted git changes
- Presents findings grouped by file with rule IDs and AI suggestions
- Offers to apply fixes automatically, one by one, or by category
- Re-runs the review after applying fixes to verify

Requires `ekline-cli` and an EkLine token. See [Prerequisites](#prerequisites) below.

### `terminology`

Checks documentation for consistent terminology against a configurable set of rules.

- Validates product names, technical terms, action verbs, and UI elements
- Flags prohibited terms and inconsistent usage within a document
- Runs proactively when documentation files are created or modified

Rules are defined in `skills/terminology/terminology-rules.md`.

### `style-guide`

Enforces documentation style, voice, and tone consistency.

- Checks for active voice, second person, present tense
- Flags banned phrases ("please note that", "in order to", "simply", etc.)
- Validates heading case, code block formatting, and list style
- Auto-fixes common violations like banned phrases and heading case
- Runs proactively when documentation files are created or modified

Rules are defined in `skills/style-guide/style-rules.md`.

## Prerequisites

### EkLine CLI (for `review-docs` only)

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

Download `ekline-cli-windows.zip` from the [Release Page](https://github.com/ekline-io/ekline-cli-binaries/releases/latest) and add to your PATH.

### EkLine Token (for `review-docs` only)

Get a token from the [EkLine Dashboard](https://ekline.io/dashboard) and set it as an environment variable:

```bash
export EKLINE_EK_TOKEN=your_token_here
```

`EK_TOKEN` is also accepted.

## Installation

From the Claude Code marketplace:

```
/plugin install ekline-docs-reviewer
```

Or to install from a local directory during development:

```bash
claude --plugin-dir /path/to/docs-reviewer
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `EKLINE_EK_TOKEN` or `EK_TOKEN` | EkLine API token |
| `EKLINE_CLI` | Path to `ekline-cli` binary (if not on PATH) |

### EkLine Config

If your project has an `ekline.config.json`, the CLI picks up its settings automatically (style guide, framework, ignore rules, etc.).

### Customizing Rules

- **Terminology rules** — edit `skills/terminology/terminology-rules.md`
- **Style rules** — edit `skills/style-guide/style-rules.md`

## Supported File Types

`.md`, `.mdx`, `.rst`, `.adoc`, `.txt`, `.html`

## License

[MIT](LICENSE)
