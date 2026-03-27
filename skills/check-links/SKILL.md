---
name: check-links
description: Scan documentation files for broken internal links, missing anchors, and optionally validate external URLs. Runs a helper script that extracts all links, validates them, and reports broken links with suggestions. Use before publishing docs or as a periodic health check.
allowed-tools: Read, Edit, Glob, Bash
metadata:
  author: EkLine
  version: "2.0.0"
  argument-hint: "[docs_directory] [--external]"
---

# Check documentation links

Run the helper script to find broken links, then present results and offer fixes.

## Inputs

- `$ARGUMENTS` — optional docs directory (defaults to current directory) and optional `--external` flag to validate external URLs

## Steps

### 1. Run the helper script

```bash
python scripts/extract_links.py $ARGUMENTS
```

If the user included `--external`, pass it through. Capture the JSON output.

The script handles file discovery, link extraction (Markdown, reference-style, HTML), internal link validation, anchor checking, and optional external URL checking.

Max 200 files per run. External checks limited to 50 URLs.

### 2. Handle errors

If the JSON contains an `error` field:

- `not_a_directory` — tell user the specified path is not a valid directory
- `no_docs_found` — tell user no .md/.mdx files were found, suggest a different path

Stop here on error.

### 3. Present the link report

Show a summary from the `summary` object:

- Files scanned (`files_scanned`)
- Total links found, broken down: internal, anchors, images, external
- If `files_truncated` is true, note that the file limit was reached

Then group broken links by type:

**Broken internal links** (`broken_internal` array):

- Show file path and line number
- Show the link text and target
- Show the reason (e.g., "Target file does not exist", "Anchor not found")
- If `suggestions` are available, show them as recommended replacements
- If `available_anchors` are listed, show the valid anchors for the target file

**Broken external links** (`broken_external` array):

- Show file path, line number, and target URL
- Show HTTP status code and reason

**Redirects** (`redirects` array):

- Show file path, line number, target URL, and HTTP status code
- Suggest updating the URL to the redirect target

**Orphaned pages** (`orphaned_pages` array):

- List doc files not linked from any other doc (excluding README.md and index files)
- These may be unreachable from navigation

### 4. Offer fixes for broken internal links

For each broken internal link that has suggestions:

- Show the suggested fix
- Ask if the user wants to apply it

For broken internal links without suggestions:

- Offer to remove the link (replace with plain text) or skip

### 5. Apply fixes

Use the Edit tool to update links in place:

- Preserve the link text unchanged
- Only change the link target
- For anchor fixes, update only the anchor portion
- For file path fixes, replace the full path with the suggested file
- For redirects, replace the old URL with the redirect destination

After applying fixes, summarize what was changed:

- Number of links fixed
- Number of links skipped for manual review
