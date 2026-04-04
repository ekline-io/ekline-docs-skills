---
name: accessibility
description: Check documentation for accessibility issues including missing alt text, heading hierarchy violations, non-descriptive links, color-only references, missing code block languages, and tables without headers. Runs a helper script that scans doc files and reports findings with fix suggestions. Use before publishing or as a periodic quality check.
allowed-tools: Read, Edit, Glob, Bash
metadata:
  author: EkLine
  version: "3.0.0"
  argument-hint: "[docs_directory] [--file FILE]"
---

# Check documentation accessibility

Run the helper script to find accessibility issues, then present results and offer fixes.

## Inputs

- `$ARGUMENTS` — optional docs directory (defaults to current directory) or `--file FILE` for a single file

## Steps

### 1. Run the helper script

```bash
python scripts/check_accessibility.py $ARGUMENTS
```

Capture the JSON output.

The script checks for:

- Images without alt text (error)
- Heading hierarchy violations — skipped levels, multiple h1s (error)
- Non-descriptive link text — "click here", "here", "read more" (warning)
- Color-only references — "the red button", "highlighted in green" (warning)
- Tables without header rows (warning)
- Missing code block language identifiers (info)
- Alt text exceeding 125 characters (info)

Max 200 files per run.

### 2. Handle errors

If the JSON contains an `error` field:

- `not_a_directory` — tell user the specified path is not a valid directory
- `file_not_found` — tell user the specified file does not exist
- `no_docs_found` — tell user no .md/.mdx files were found, suggest a different path

Stop here on error.

### 3. Present the accessibility report

Show a summary:

- Files scanned, files with issues
- Breakdown: X errors, Y warnings, Z info items
- If `files_truncated` is true, note that the file limit was reached

Then list findings grouped by severity:

**Errors (must fix):**

For each file with errors, show:
- File path
- Each finding: type, line number, message, and suggestion
- Show the context line for reference

**Warnings (should fix):**

Same format as errors.

**Info (best practices):**

Show as a compact list — file path, line number, and message.

### 4. Offer fixes

For each file with errors or warnings, offer to fix:

1. **Missing alt text** — read the file, find the image, look at the image filename and surrounding context to suggest descriptive alt text. If unable to determine, insert `[TODO: describe this image]` as a placeholder.
2. **Heading hierarchy** — adjust heading levels to maintain proper nesting. Prefer demoting the wrong heading rather than promoting surrounding headings.
3. **Non-descriptive links** — read the link target and surrounding paragraph to suggest better link text that describes the destination.
4. **Missing code language** — look at the code block content to detect the language and add it.
5. **Skip all** — leave for manual review

When applying fixes:

- Read the file with the Read tool
- Use the Edit tool to make targeted changes
- Only change the specific issue — do not modify surrounding content
- For alt text, prefer short descriptions (under 125 chars) that convey the image's purpose

After applying fixes, re-run the script on modified files and show the updated counts.

### 5. Summary

Report what was fixed:

- Number of issues fixed by type
- Number of issues remaining
- Any files that still have errors requiring manual attention
