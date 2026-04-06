---
name: docs-coverage
description: Measure documentation coverage by scanning your codebase for exported functions, classes, API endpoints, and CLI commands, then checking if docs exist. Runs a helper script that reports coverage percentage, breakdowns by type and directory, and lists undocumented items. Supports TypeScript/JavaScript, Python, and Go.
allowed-tools: Read, Edit, Glob, Bash
metadata:
  author: EkLine
  version: "2.0.0"
  argument-hint: "[source_directory] [--docs-dir DIR]"
---

# Documentation coverage

Run the helper script to measure what percentage of your public API surface is documented.

## Inputs

- `$ARGUMENTS` — optional source directory and optional `--docs-dir DIR` for the docs directory

## Steps

### 1. Run the helper script

```bash
python scripts/scan_exports.py $ARGUMENTS
```

Pass `--docs-dir DIR` if the user specifies a docs directory. Capture the JSON output.

The script handles:

- Source file discovery (excludes test files, node_modules, vendor, dist, build)
- Export extraction: functions, classes, interfaces, types, const exports, components, API endpoints
- Inline doc detection: JSDoc for TS/JS, docstrings for Python, GoDoc for Go
- Doc file scanning to check if each export is mentioned in documentation
- Coverage calculation by type and directory

Supports TypeScript/JavaScript, Python, and Go. Max 300 source files per run.

### 2. Handle errors and empty results

If the JSON contains an `error` field:

- `not_a_directory` — tell user the specified path is not a valid directory

If `total_public_items` is 0:

- Tell user no public API items were found, suggest checking the source directory path

Stop here if error or nothing found.

### 3. Present the coverage report

Show overall coverage from `overall_coverage`:

- Percentage, documented count, partial count, undocumented count, total

Show **coverage by type** from `by_type`:

- For each type (endpoint, class, function, component, type, interface), show percentage and counts
- Use a simple bar or fraction format

Show **coverage by directory** from `by_directory`:

- Top directories with their coverage percentages

### 4. Show undocumented items prioritized by type

List items from the `undocumented` array, grouped and prioritized:

1. **Endpoints** — users depend on these directly
2. **Functions** — high coupling, used by other modules
3. **Classes** — core abstractions
4. **Types/interfaces** — lower priority unless widely used

For each item show: name, file path, and line number.

Also show `partial` items — these have inline docs (JSDoc, docstring, or GoDoc) but no dedicated documentation page. They may or may not need a separate page depending on the project's documentation strategy.

### 5. Offer to generate doc stubs

For high-priority undocumented items, offer to:

1. **Generate a doc stub** — read the source file, extract the signature and parameters, create a documentation template in the docs directory
2. **Add inline docs** — read the source file, add JSDoc/docstring/GoDoc comment above the export
3. **Skip** — leave for manual documentation

When generating stubs:

- Read the source file with the Read tool to understand the function/class
- Create a Markdown file with: title, description placeholder, parameters, return type, and a usage example placeholder
- Use the Edit tool or Write tool as appropriate
- Place generated docs in the docs directory matching the source file structure

After generating stubs, summarize:

- Number of doc stubs created
- Number of inline docs added
- Updated coverage percentage estimate
