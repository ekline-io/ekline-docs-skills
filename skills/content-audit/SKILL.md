---
name: content-audit
description: Audit documentation for structural problems including near-duplicate content, thin pages, orphaned pages, missing structure, and inconsistent frontmatter. Runs a helper script that analyzes the docs directory and reports issues with actionable suggestions. Use periodically or before major releases to catch silent quality problems.
allowed-tools: Read, Edit, Glob, Grep, Bash
metadata:
  author: EkLine
  version: "3.0.0"
  argument-hint: "[docs_directory] [--min-words N] [--similarity-threshold N]"
---

# Audit documentation content

Run the helper script to find structural problems, then present results and offer to fix them.

## Inputs

- `$ARGUMENTS` — optional docs directory (defaults to current directory), `--min-words N` (default 100), `--similarity-threshold N` (default 0.60)

## Steps

### 1. Run the helper script

```bash
python scripts/audit_content.py $ARGUMENTS
```

Capture the JSON output.

The script checks for:

- Near-duplicate content (Jaccard similarity on normalized sentences, flags pairs above threshold)
- Thin pages (fewer than N words of prose, excluding frontmatter and code blocks)
- Orphaned pages (not linked from any other doc and not in any nav config file)
- Missing structure (no h1, no headings at all, long pages without subsections)
- Inconsistent frontmatter (fields present in 50%+ of files but missing from others)

Max 200 files per run.

### 2. Handle errors

If the JSON contains an `error` field:

- `not_a_directory` — tell user the specified path is not a valid directory
- `no_docs_found` — tell user no .md/.mdx files were found, suggest a different path

Stop here on error.

### 3. Present the audit report

Show a summary line:

- "Scanned X files: Y near-duplicates, Z thin pages, W orphans, V structure issues, U frontmatter inconsistencies"

Then present each category that has findings:

**Near-duplicate content** (`duplicates` array):

For each pair:
- Show both file paths and similarity percentage
- Recommend: review whether they should be merged, or one should link to the other

**Thin pages** (`thin_pages` array):

For each file:
- Show file path and word count
- If under 30 words, suggest deleting or merging into a parent page
- If 30-99 words, suggest expanding with more detail

**Orphaned pages** (`orphaned_pages` array):

For each file:
- Show file path
- Note it is not linked from any other doc or navigation config
- Suggest adding a link from a related page or adding to navigation

**Structure issues** (`structure_issues` array):

For each file:
- Show file path, issue type, and message
- `missing_h1` — suggest adding an h1 or a title in frontmatter
- `no_headings` — suggest adding section headings for scannability
- `no_subsections` — suggest breaking the page into sections with h2 headings

**Frontmatter inconsistencies** (`frontmatter_issues` array):

For each file:
- Show file path and which fields are missing
- Show which fields are expected (present in majority of files)

### 4. Offer to fix issues

Offer actions by category:

1. **Duplicates** — for each pair, offer to:
   - Read both files and show a side-by-side comparison of overlapping content
   - Suggest which file to keep as the canonical version
   - Draft a redirect or "see also" link from the duplicate to the canonical page
   - Skip

2. **Thin pages** — offer to:
   - Read the page and surrounding pages to suggest additional content
   - Merge into a parent page
   - Skip

3. **Orphans** — offer to:
   - Search for related pages using Grep on the orphan's title/topic
   - Add a link from the most relevant related page
   - Skip

4. **Structure** — offer to:
   - Add missing h1 headings
   - Add subsection headings for long pages (suggest splits based on content)
   - Skip

5. **Frontmatter** — offer to:
   - Add missing frontmatter fields with sensible defaults (title from h1, description from first paragraph)
   - Skip

When applying fixes, use the Read tool to understand context and the Edit tool for targeted changes.

### 5. Summary

Report what was addressed:

- Number of issues fixed by category
- Number of issues skipped for manual review
- Overall recommendation for next steps
