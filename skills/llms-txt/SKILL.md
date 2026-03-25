---
name: llms-txt
description: Generate an llms.txt file for your project following the llms.txt specification. Runs a helper script that detects your docs platform, classifies pages into sections, and resolves URLs. Makes documentation discoverable by large language models. Use when setting up a new docs site or improving AI discoverability.
allowed-tools: Read, Glob, Bash, Write
metadata:
  argument-hint: "[docs_directory] [--base-url URL] [--full]"
---

# Generate llms.txt

Run the helper script to scan documentation, then format and write the llms.txt file.

## Inputs

- `$ARGUMENTS` — optional docs directory, `--base-url URL` for hosted docs, `--full` to also generate llms-full.txt

## Steps

### 1. Run the helper script

```bash
python scripts/generate_llms_txt.py $ARGUMENTS
```

The script handles:
- Docs directory auto-detection (docs/, _docs/, content/, src/content/docs/)
- Platform detection (Docusaurus, Mintlify, MkDocs, GitBook, Astro Starlight, VitePress)
- Base URL extraction from platform config files
- Page title and description extraction (frontmatter then H1 fallback)
- Deterministic classification: API (api/, reference/ paths), Guides (guide/, tutorial/, getting-started paths), Blog (blog/, _posts/ paths), Examples (examples/, quickstart/ paths), Docs (everything else)
- Priority ordering (getting-started and overview pages first)

Max 150 files per run. llms-full.txt limited to 20 files / 200KB.

### 2. Handle errors

If the JSON contains an `error` field:
- `no_docs_found` — tell user no documentation files found, suggest passing a directory
- `not_a_directory` — tell user the path is not a valid directory

### 3. Format llms.txt

Using the `sections` object from the JSON, build the file:

```markdown
# {project_name}

> {project_description}

## {Section Name}

- [{title}]({url}): {description}
```

Rules:
- Exactly one H1 (project name)
- Blockquote immediately after H1 (project description)
- Each section is an H2 — only include sections that have pages
- Each entry is a Markdown link with colon-separated description
- Use the `url` field from the JSON (already resolved to URLs if base_url was found, otherwise relative paths)

### 4. Present summary and ask user

Show:
- Platform detected (if any) and base URL
- Number of files indexed and total size
- Section breakdown (e.g., "Docs: 17, Guides: 1, Examples: 5")
- If `full_warning` is present, show it

Ask whether to:
1. Write `llms.txt` to project root
2. Write to a custom path (e.g., `public/llms.txt` for Next.js)
3. Just show the output

### 5. Generate llms-full.txt (if --full and eligible)

Only if `can_generate_full` is true in the JSON:
- Read each file listed in `full_files` using the Read tool
- Concatenate into a single file with the format:

```markdown
# {project_name}

> {project_description}

---

## {Page Title}

{Full page content}
```

Write to the same directory as llms.txt.

### 6. Write the file

Use the Write tool to create llms.txt (and llms-full.txt if applicable).

Suggest to the user:
- Add to site's public root for web serving
- Add to `.gitignore` if generated (or commit if hand-curated)
- Regenerate periodically as docs change
