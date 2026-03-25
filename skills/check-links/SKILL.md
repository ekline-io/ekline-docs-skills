---
name: check-links
description: Scan documentation files for broken internal links, missing anchors, and optionally validate external URLs. Reports dead links with locations and suggests fixes. Use this skill before publishing docs or as a periodic health check.
allowed-tools: Read, Glob, Grep, Bash
metadata:
  argument-hint: "[docs_directory] [--external]"
---

# Check documentation links

Find broken links across all documentation files.

## Inputs

- `$ARGUMENTS` — optional docs directory (defaults to common doc paths) and optional `--external` flag to also check external URLs

## Steps

### 1. Find documentation files

If `$ARGUMENTS` specifies a directory, use it. Otherwise, search for doc files:

```
Glob: docs/**/*.md, docs/**/*.mdx
Glob: _docs/**/*.md, _docs/**/*.mdx
Glob: content/**/*.md, content/**/*.mdx
Glob: **/*.md (fallback, exclude node_modules, .git, vendor)
```

### 2. Extract all links from each file

For each documentation file, find all links using these patterns:

**Markdown links:**
```
Grep: \[([^\]]*)\]\(([^)]+)\)
```

**Reference-style links:**
```
Grep: \[([^\]]*)\]\[([^\]]*)\]
Grep: ^\[([^\]]*)\]:\s*(.+)$
```

**HTML links:**
```
Grep: href="([^"]+)"
Grep: src="([^"]+)"
```

**Anchor targets:**
```
Grep: ^#{1,6}\s+(.+)$  (headings become anchors)
Grep: <a\s+name="([^"]+)"
Grep: id="([^"]+)"
```

For each link, record:
- Source file and line number
- Link text
- Link target (URL or path)
- Link type (internal path, internal anchor, external URL, email)

### 3. Validate internal links

For each internal link (relative paths, not starting with `http`):

**File links** (e.g., `./getting-started.md`, `../api/auth.md`):
- Resolve the path relative to the source file
- Check if the target file exists using Glob
- If the link has an anchor (e.g., `./auth.md#setup`), also check the anchor exists

**Anchor-only links** (e.g., `#configuration`):
- Check that the current file has a heading matching the anchor
- Convert heading text to anchor format: lowercase, replace spaces with hyphens, remove special characters

**Image links** (e.g., `./images/diagram.png`, `../assets/screenshot.jpg`):
- Check if the image file exists

### 4. Validate external links (if --external flag)

Only if the user included `--external` in arguments:

For each external URL (starting with `http://` or `https://`):

```bash
curl -sL -o /dev/null -w "%{http_code}" --max-time 10 "{url}"
```

Classify responses:
- `200` — OK
- `301`, `302` — Redirect (note the destination)
- `403`, `404`, `410` — Broken
- `429` — Rate limited (skip, note for retry)
- Timeout — Note as unreachable

Rate limit: Check at most 5 URLs per second to avoid being blocked.

### 5. Check for orphaned anchors and images

Look for potential issues:
- Images referenced in docs that do not exist
- Documentation files that are not linked from any other doc (orphaned pages)
- Anchor definitions that are never referenced (informational only)

### 6. Present the link report

```
Link Check Report
=================
Scanned: 32 documentation files
Links found: 245 (180 internal, 50 external, 15 images)

BROKEN INTERNAL LINKS:
  docs/getting-started.md:42
    [Configuration guide](./configuration.md)
    Target file does not exist
    Suggestion: Did you mean ./config.md?

  docs/api/auth.md:15
    [See setup instructions](#setup-instructions)
    Anchor #setup-instructions not found in this file
    Available anchors: #setup, #configuration, #troubleshooting

  docs/guides/deploy.md:78
    ![Architecture diagram](../images/arch-v1.png)
    Image file does not exist

BROKEN EXTERNAL LINKS:
  docs/resources.md:23
    [API Reference](https://api.example.com/v1/docs)
    HTTP 404 — Not Found

REDIRECTS:
  docs/contributing.md:10
    [Code of Conduct](http://example.com/coc)
    301 → https://example.com/code-of-conduct
    Suggestion: Update to the redirect target

ORPHANED PAGES (not linked from any other doc):
  docs/advanced/custom-plugins.md
  docs/troubleshooting/common-errors.md

Summary:
  Broken internal: 3
  Broken external: 1
  Redirects: 1
  Orphaned pages: 2
```

### 7. Offer fixes

For broken internal links, offer to:
1. **Auto-fix file links** — if a similar file exists (fuzzy match), update the link
2. **Auto-fix anchors** — if the heading exists with slightly different text, update the anchor
3. **Remove dead links** — replace the link with plain text
4. **Skip** — leave for manual review

When auto-fixing:
- Use the Edit tool to update the link in place
- Preserve the link text unchanged
- Only change the link target
