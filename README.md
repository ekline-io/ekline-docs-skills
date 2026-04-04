# EkLine Docs Skills

**12 documentation skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that find problems, enforce standards, and fix your docs.**

Get a full health report, readability scores, broken link detection, accessibility audits, and more — directly in your terminal.

```
> /docs-health ./docs

Documentation Health Report
===========================
Overall Score: B+ (84/100)

  Links        A   (96/100)  — 2 broken out of 147
  Readability  B+  (82/100)  �� avg grade level 7.2
  Style        B   (80/100)  — 12 violations across 8 files
  Terminology  A-  (90/100)  — 3 inconsistencies
  Freshness    C+  (68/100)  — 4 stale docs detected

Top 5 issues to fix first:
  1. docs/api/auth.md — stale (references removed endpoint)
  2. docs/guide/setup.md — grade level 12.1 (too complex)
  3. docs/api/users.md — 3 broken internal links
  ...
```

## Quick start

```bash
# Install (one command)
git clone https://github.com/ekline-io/ekline-docs-skills.git ~/.claude/skills/ekline-docs-skills

# Try it
/docs-health ./docs
```

That's it. All 12 skills are available immediately — no API keys, no config, no dependencies beyond Python 3.

## What's included

| Skill | What it does | Try it |
|-------|-------------|--------|
| **[docs-health](#docs-health)** | Full health report card with overall score | `/docs-health ./docs` |
| **[readability](#readability)** | Flesch-Kincaid grade level + letter grades | `/readability ./docs` |
| **[accessibility](#accessibility)** | Alt text, heading hierarchy, link text | `/accessibility ./docs` |
| **[content-audit](#content-audit)** | Duplicates, orphans, thin pages | `/content-audit ./docs` |
| **[style-guide](#style-guide)** | Voice, tone, banned phrases | Runs automatically |
| **[terminology](#terminology)** | Consistent terms across docs | Runs automatically |
| **[check-links](#check-links)** | Broken links and missing anchors | `/check-links ./docs` |
| **[docs-freshness](#docs-freshness)** | Stale docs vs. code changes | `/docs-freshness` |
| **[docs-coverage](#docs-coverage)** | API surface documentation % | `/docs-coverage` |
| **[review-docs](#review-docs)** | Full review via EkLine CLI | `/review-docs ./docs` |
| **[changelog](#changelog)** | Generate changelog from git | `/changelog` |
| **[llms-txt](#llms-txt)** | Generate llms.txt for LLMs | `/llms-txt` |

> 11 of 12 skills work out of the box. Only `review-docs` requires an [EkLine token](#ekline-cli-for-review-docs-only).

---

## Skills

### docs-health

The one-command overview. Runs link validation, readability analysis, style checks, terminology checks, and freshness detection — then combines everything into a single report card with an A-F grade.

```
/docs-health ./docs
/docs-health ./docs --skip-freshness --skip-external
```

Offers to fix issues after presenting the report, starting from highest impact.

### readability

Scores every doc file with quantitative readability metrics.

```
/readability ./docs
/readability --file docs/guide.md
```

- **Flesch-Kincaid Grade Level** — target 8th grade or below for docs
- **Flesch Reading Ease** — 0-100 scale, higher is easier
- **Passive voice %** — flags files over 10%
- **Long sentences** — flags sentences over 25 words
- Grades each file **A through F** and offers to rewrite hard-to-read content

### accessibility

Catches accessibility issues that affect screen reader users and compliance requirements.

```
/accessibility ./docs
/accessibility --file docs/guide.md
```

- Images without alt text (error)
- Heading levels skipped — h1 to h3 (error)
- Multiple h1 headings (error)
- Non-descriptive links — "click here", "read more" (warning)
- Color-only references — "the red button" (warning)
- Tables without headers (warning)
- Code blocks without language (info)

### content-audit

Finds the structural problems that accumulate silently over time.

```
/content-audit ./docs
/content-audit ./docs --min-words 50 --similarity-threshold 0.7
```

- **Near-duplicate pages** — sentence-level similarity detection
- **Thin pages** — under 100 words of actual content
- **Orphaned pages** — not linked from anywhere (checks nav configs too)
- **Missing structure** — no h1, no subsections on long pages
- **Frontmatter gaps** — inconsistent metadata across docs

### style-guide

Enforces voice, tone, and formatting consistency. **Runs automatically** when you create or edit doc files.

- Active voice, second person, present tense
- Flags banned phrases ("please note that", "in order to", "simply")
- Heading case, code block formatting, list style
- Auto-fixes common violations

Customize: edit [`skills/style-guide/references/style-rules.md`](skills/style-guide/references/style-rules.md)

### terminology

Keeps terminology consistent across your docs. **Runs automatically** when you create or edit doc files.

- Validates product names, technical terms, UI elements
- Flags prohibited terms (e.g., "blacklist" should be "blocklist")
- Catches inconsistent usage within a document

Customize: edit [`skills/terminology/references/terminology-rules.md`](skills/terminology/references/terminology-rules.md)

### check-links

Finds broken links before your readers do.

```
/check-links ./docs
/check-links ./docs --external
```

- Validates internal file links and anchor references
- Optionally checks external URLs for 404s and redirects
- Detects orphaned pages not linked from any other doc
- Auto-fixes broken links with fuzzy matching

### docs-freshness

Detects docs that have fallen behind the code.

```
/docs-freshness
/docs-freshness main..HEAD
/docs-freshness v1.2.0..v1.3.0
```

- Analyzes git diffs for renamed functions, changed APIs, modified configs
- Cross-references docs for mentions of changed code
- Scores each file: Fresh, Possibly stale, Likely stale, Stale
- Offers to draft updates for stale references

### docs-coverage

Measures what percentage of your public API is documented.

```
/docs-coverage
/docs-coverage ./src ./docs
```

- Scans exported functions, classes, endpoints, CLI commands, config options
- Reports coverage by type and directory
- Suggests priorities and offers to generate doc stubs
- Supports TypeScript, Python, and Go

### review-docs

Full documentation review powered by [EkLine](https://docs.ekline.io/reviewer/overview/).

```
/review-docs ./docs
/review-docs docs/guide.md docs/api.md
```

- Reviews a directory, specific files, or uncommitted changes
- Presents findings with rule IDs and AI suggestions
- Applies fixes automatically, one by one, or by category

> Requires `ekline-cli` and an EkLine token. See [setup](#ekline-cli-for-review-docs-only) below.

### changelog

Generates a structured changelog from git history.

```
/changelog
/changelog v1.3.0
/changelog v1.2.0..v1.3.0
```

- Parses conventional commits or free-form messages
- Categorizes: Added, Changed, Fixed, Removed, Security, Breaking
- Writes [Keep a Changelog](https://keepachangelog.com/) format

### llms-txt

Generates an [`llms.txt`](https://llmstxt.org) file for LLM discoverability.

```
/llms-txt
/llms-txt ./docs
```

- Scans docs and extracts titles, descriptions, categories
- Produces structured `llms.txt` with Docs, API, Guides, Examples sections
- Optionally generates `llms-full.txt` with complete content

---

## Installation

**Project-level** (recommended — team shares the same skills):

```bash
git clone https://github.com/ekline-io/ekline-docs-skills.git .claude/skills/ekline-docs-skills
```

**User-level** (available in all your projects):

```bash
git clone https://github.com/ekline-io/ekline-docs-skills.git ~/.claude/skills/ekline-docs-skills
```

### Supported file types

`.md`, `.mdx`, `.rst`, `.adoc`, `.txt`, `.html`

---

## Configuration

### Customizing rules

Both the style guide and terminology rules are plain Markdown files you can edit:

- **Style rules** — [`skills/style-guide/references/style-rules.md`](skills/style-guide/references/style-rules.md)
- **Terminology rules** — [`skills/terminology/references/terminology-rules.md`](skills/terminology/references/terminology-rules.md)

### EkLine CLI (for `review-docs` only)

<details>
<summary>Setup instructions (only needed if you want to use <code>/review-docs</code>)</summary>

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

**Token:**

Get a token from the [EkLine Dashboard](https://ekline.io/dashboard) and set it:

```bash
export EKLINE_EK_TOKEN=your_token_here
```

</details>

---

## License

[MIT](LICENSE)
