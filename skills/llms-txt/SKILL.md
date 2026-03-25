---
name: llms-txt
description: Generate an llms.txt file for your project following the llms.txt specification. Makes your documentation discoverable and consumable by large language models. Use this skill when setting up a new docs site or improving AI discoverability.
allowed-tools: Read, Glob, Grep, Write
metadata:
  argument-hint: "[docs_directory]"
---

# Generate llms.txt

Generate a well-structured `llms.txt` file that makes your project documentation consumable by large language models, following the [llms.txt specification](https://llmstxt.org).

## Inputs

- `$ARGUMENTS` — the documentation directory to scan (defaults to common doc paths if not provided)

## Steps

### 1. Locate documentation files

Search for the documentation root. Check these paths in order:

```
Glob: docs/**/*.md, docs/**/*.mdx
Glob: _docs/**/*.md, _docs/**/*.mdx
Glob: content/**/*.md, content/**/*.mdx
Glob: src/pages/docs/**/*.md, src/pages/docs/**/*.mdx
Glob: README.md
```

If `$ARGUMENTS` is provided, use that path instead.

Also look for project metadata:

```
Read: package.json (name, description)
Read: README.md (first paragraph)
Read: ekline.config.json (if exists)
```

### 2. Extract project identity

From the metadata files, determine:

- **Project name** — from `package.json` name field, or top-level heading in README
- **Project description** — from `package.json` description, or first paragraph of README
- **Project URL** — from `package.json` homepage, or repository URL

### 3. Categorize documentation pages

Read each documentation file and classify it into sections:

| Section | Description | Examples |
|---------|-------------|---------|
| Docs | Core documentation pages | Getting started, installation, configuration |
| API | API reference pages | Endpoints, methods, parameters |
| Guides | Tutorials and how-to guides | Step-by-step walkthroughs |
| Blog | Blog posts and announcements | Release notes, case studies |
| Examples | Code examples and samples | Quickstart, integrations |

For each file, extract:
- The title (first H1 heading or frontmatter title)
- A one-line description (first paragraph or frontmatter description)
- The relative file path

### 4. Generate llms.txt

Produce the file following this exact format:

```markdown
# {Project Name}

> {One-line project description}

## Docs

- [{Page Title}]({url_or_path}): {One-line description}
- [{Page Title}]({url_or_path}): {One-line description}

## API

- [{Page Title}]({url_or_path}): {One-line description}

## Guides

- [{Page Title}]({url_or_path}): {One-line description}

## Examples

- [{Page Title}]({url_or_path}): {One-line description}
```

Rules:
- H1 is the project name (exactly one)
- Blockquote immediately after H1 is the project summary
- Each section is an H2
- Each entry is a Markdown link with a colon-separated description
- Only include sections that have entries
- Order entries within each section by importance (getting started first, advanced topics last)
- Use relative paths for local docs, full URLs for hosted docs

### 5. Also generate llms-full.txt (optional)

If the total documentation is under 100 files, offer to generate `llms-full.txt` — a single file containing the full content of all documentation pages, separated by headers:

```markdown
# {Project Name}

> {One-line project description}

---

## {Page Title}

{Full page content}

---

## {Page Title}

{Full page content}
```

This is useful for smaller projects where LLMs can consume all docs in a single context.

### 6. Write the file

Write `llms.txt` to the project root directory. If `llms-full.txt` was generated, write that too.

Present a summary:
- Number of pages indexed
- Sections created
- Total documentation size
- Suggestion to add `llms.txt` to the site's public root (e.g., `public/llms.txt` for Next.js)

### 7. Validate

Check the generated file:
- Exactly one H1
- Blockquote present after H1
- All links point to files that exist
- No empty sections
- No duplicate entries
