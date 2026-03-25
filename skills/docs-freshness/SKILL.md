---
name: docs-freshness
description: Detect stale documentation by comparing recent code changes against docs. Runs a helper script that extracts changed symbols from git diffs and cross-references them against documentation files. Flags docs that reference modified or removed code. Use after merging changes or before a release.
allowed-tools: Read, Edit, Glob, Grep, Bash
metadata:
  argument-hint: "[commit_range] [--docs-dir DIR]"
---

# Detect stale documentation

Run the helper script to find docs that reference changed code, then present results and offer to draft updates.

## Inputs

- `$ARGUMENTS` — optional commit range (e.g., `main..HEAD`, `v1.2.0..v1.3.0`, `HEAD~20..HEAD`) and optional `--docs-dir DIR`

## Steps

### 1. Run the helper script

```bash
python scripts/extract_changes.py $ARGUMENTS
```

Pass `--docs-dir DIR` if the user specifies a docs directory. Capture the JSON output.

The script handles:
- Range detection (tag-based, commit range, or last 30 days default)
- Diff parsing to extract changed symbols (functions, classes, types, consts)
- Endpoint detection (Express/Flask/FastAPI route changes)
- Environment variable and config key tracking
- Doc file discovery and cross-referencing with high/low confidence matching

Max 50 changed code files analyzed per run. Symbols under 6 characters are filtered out to reduce false positives.

### 2. Handle errors and empty results

If the JSON contains an `error` field:
- `not_a_git_repo` — tell user to run from inside a git repository

If `stale_docs` is empty:
- Report the range analyzed, number of code files changed, number of docs searched
- Tell user all docs appear fresh — no references to changed code found

Stop here if error or no stale docs.

### 3. Present stale docs grouped by severity

Show a summary:
- Range analyzed, code files changed, symbols tracked, doc files searched
- Counts: stale, likely_stale, fresh

Then list stale docs grouped by status:

**Stale (action required)** — docs with `status: "stale"`:
- Show file path and score
- For each finding, show: the symbol referenced, what changed (removed/modified/endpoint removed/env var), and the source file

**Likely stale (review recommended)** — docs with `status: "likely_stale"`:
- Same format as above

### 4. Show triggering symbols

For each stale doc, list the specific symbols from the `findings` array that triggered the staleness flag:
- `symbol` — the name that was found in the doc
- `type` — what happened: `removed_symbol`, `modified_symbol`, `removed_endpoint`, `env_var_changed`
- `source_file` — the code file where the change occurred
- `doc_line` — the line in the doc that references the symbol
- `context` — whether the reference is in a `code_block` or `inline_code`

This helps the user understand exactly what needs updating and where.

### 5. Offer to draft updates

For each stale doc, offer to:
1. **Read and update** — read the stale doc and the changed source code, then draft specific updates to fix the stale references
2. **Skip** — leave for manual review

When drafting updates:
- Read the doc file with the Read tool
- Read the relevant source file to understand the new code
- Update only the stale references (function names, endpoints, config keys)
- Update code examples that use renamed or removed APIs
- Do NOT change content unrelated to the code changes
- Use the Edit tool to apply changes

After applying updates, summarize:
- Number of docs updated
- Number of stale references fixed
- Any docs left for manual review
