# Documentation Skills for Claude Code by EkLine

A Claude Code plugin that reviews, fixes, and improves your documentation using [EkLine](https://ekline.io) — with built-in style enforcement, terminology checks, readability scoring, accessibility audits, content analysis, stale docs detection, link validation, coverage measurement, changelog generation, and LLM-readiness tooling.

## Skills

### Health and analysis

#### `docs-health`

Runs a comprehensive documentation health check — combines link validation, readability scoring, style compliance, terminology consistency, and freshness detection into a single report card with an overall score.

```
/docs-health ./docs
/docs-health ./docs --skip-freshness
```

- Produces a unified report card with letter grades per category
- Computes an overall health score (0-100) with weighted categories
- Ranks the top issues to fix first, prioritized by impact
- Offers to fix issues directly or focus on a specific category

#### `readability`

Analyzes documentation readability with quantitative metrics.

```
/readability ./docs
/readability --file docs/guide.md
```

- Computes Flesch-Kincaid Grade Level (target: 8th grade or below)
- Computes Flesch Reading Ease score (target: 60+)
- Detects passive voice, complex sentences, and overly long sentences
- Grades each file A-F and offers to rewrite hard-to-read content

#### `content-audit`

Audits documentation for structural problems that accumulate silently.

```
/content-audit ./docs
/content-audit ./docs --min-words 50 --similarity-threshold 0.7
```

- Finds near-duplicate content across pages using sentence-level similarity
- Detects thin pages with too little content
- Identifies orphaned pages not linked from anywhere
- Flags pages missing headings, structure, or consistent frontmatter
- Suggests merges, expansions, and structural fixes

#### `accessibility`

Checks documentation for accessibility issues.

```
/accessibility ./docs
/accessibility --file docs/guide.md
```

- Finds images without alt text
- Validates heading hierarchy (no skipped levels, single h1)
- Flags non-descriptive link text ("click here", "read more")
- Detects color-only references that exclude screen reader users
- Checks for missing code block languages and tables without headers

### Quality enforcement

#### `review-docs`

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

#### `style-guide`

Enforces documentation style, voice, and tone consistency.

- Checks for active voice, second person, present tense
- Flags banned phrases ("please note that", "in order to", "simply", etc.)
- Validates heading case, code block formatting, and list style
- Auto-fixes common violations like banned phrases and heading case
- Runs proactively when documentation files are created or modified

Rules are defined in `skills/style-guide/references/style-rules.md`.

#### `terminology`

Checks documentation for consistent terminology against a configurable set of rules.

- Validates product names, technical terms, action verbs, and UI elements
- Flags prohibited terms and inconsistent usage within a document
- Runs proactively when documentation files are created or modified

Rules are defined in `skills/terminology/references/terminology-rules.md`.

#### `check-links`

Scans documentation for broken links and missing anchors.

```
/check-links ./docs
/check-links ./docs --external
```

- Validates all internal file links and anchor references
- Optionally checks external URLs for 404s and redirects
- Detects orphaned pages not linked from any other doc
- Offers auto-fix for broken internal links with fuzzy matching

### Documentation health

#### `docs-freshness`

Detects stale documentation by comparing recent code changes against docs.

```
/docs-freshness
/docs-freshness main..HEAD ./docs
/docs-freshness v1.2.0..v1.3.0
```

- Analyzes git diffs for renamed functions, changed APIs, modified configs
- Searches docs for references to changed code
- Scores each doc file: Fresh, Possibly stale, Likely stale, or Stale
- Offers to draft updates for stale documentation

#### `docs-coverage`

Measures what percentage of your public API surface is documented.

```
/docs-coverage
/docs-coverage ./src ./docs
```

- Scans exported functions, classes, API endpoints, CLI commands, and config options
- Checks if corresponding documentation exists (in docs or inline)
- Reports coverage by type (functions, endpoints, components) and by directory
- Suggests documentation priorities and offers to generate stubs
- Supports TypeScript, Python, and Go

### Generation

#### `changelog`

Generates structured changelog entries from git history.

```
/changelog
/changelog v1.3.0
/changelog v1.2.0..v1.3.0
```

- Parses conventional commits or free-form commit messages
- Categorizes changes: Added, Changed, Fixed, Removed, Security, Breaking Changes
- Extracts PR and issue references
- Writes to CHANGELOG.md in [Keep a Changelog](https://keepachangelog.com/) format

#### `llms-txt`

Generates an `llms.txt` file for your project following the [llms.txt specification](https://llmstxt.org).

```
/llms-txt
/llms-txt ./docs
```

- Scans documentation files and extracts titles, descriptions, and categories
- Produces a structured `llms.txt` with sections (Docs, API, Guides, Examples)
- Optionally generates `llms-full.txt` with complete doc content for smaller projects
- Validates the output against the llms.txt specification

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

Clone into your Claude Code skills directory:

```bash
# Project-level (recommended)
git clone https://github.com/ekline-io/ekline-docs-skills.git .claude/skills/ekline-docs-skills

# Or user-level (available in all projects)
git clone https://github.com/ekline-io/ekline-docs-skills.git ~/.claude/skills/ekline-docs-skills
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

- **Terminology rules** — edit `skills/terminology/references/terminology-rules.md`
- **Style rules** — edit `skills/style-guide/references/style-rules.md`

## Supported File Types

`.md`, `.mdx`, `.rst`, `.adoc`, `.txt`, `.html`

## License

[MIT](LICENSE)
