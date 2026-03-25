---
name: docs-freshness
description: Detect stale documentation by comparing recent code changes against docs. Finds docs that reference changed functions, APIs, configs, or features and flags them for update. Use this skill after merging code changes, before a release, or as a periodic health check.
allowed-tools: Read, Glob, Grep, Bash
metadata:
  argument-hint: "[branch_or_commit_range] [docs_directory]"
---

# Detect stale documentation

Compare recent code changes against documentation files to find docs that may be outdated.

## Inputs

- `$ARGUMENTS` — optional branch or commit range (defaults to changes in the last 30 days), and/or a docs directory path

## Steps

### 1. Determine the change scope

Parse `$ARGUMENTS` to identify:
- A git commit range (e.g., `main..HEAD`, `v1.2.0..v1.3.0`, `HEAD~20..HEAD`)
- A docs directory (e.g., `./docs`)

If no commit range is provided, default to the last 30 days:

```bash
git log --since="30 days ago" --format="%H" | tail -1
```

Use that as the start commit compared against HEAD.

If no docs directory is specified, search for common doc paths:

```
Glob: docs/**/*.md
Glob: _docs/**/*.md
Glob: content/**/*.md
Glob: README.md
```

### 2. Extract code changes

Get all meaningful code changes in the range:

```bash
git diff --name-only {start}..{end} -- '*.ts' '*.tsx' '*.js' '*.jsx' '*.py' '*.go' '*.rs' '*.java' '*.rb'
```

For each changed code file, extract:

```bash
git diff {start}..{end} -- {file}
```

From the diff, identify:
- **Renamed or removed functions/methods** — function signatures that changed
- **Changed API endpoints** — route definitions, URL patterns
- **Modified configuration options** — env vars, config keys, CLI flags
- **Renamed files or directories** — moved modules
- **Changed types/interfaces** — exported types that consumers depend on
- **Changed CLI commands or flags** — argument parsing changes

### 3. Build a change inventory

Create a structured list of what changed:

```yaml
changes:
  - type: function_renamed
    old_name: "authenticate"
    new_name: "authenticateUser"
    file: "src/auth.ts"

  - type: endpoint_changed
    old_path: "/api/v1/users"
    new_path: "/api/v2/users"
    file: "src/routes/users.ts"

  - type: config_added
    name: "REDIS_URL"
    file: "src/config.ts"

  - type: function_removed
    name: "deprecatedHelper"
    file: "src/utils.ts"
```

### 4. Search documentation for references

For each change in the inventory, search all documentation files:

```
Grep: "authenticate" in docs/**/*.md
Grep: "/api/v1/users" in docs/**/*.md
Grep: "deprecatedHelper" in docs/**/*.md
```

Also check for:
- Code blocks containing the old function/endpoint names
- Links pointing to renamed or moved files
- Configuration examples using changed config keys
- CLI examples with changed flags

### 5. Score freshness

For each documentation file, calculate a freshness score:

| Factor | Impact |
|--------|--------|
| References a renamed function | High staleness |
| References a removed function | Critical staleness |
| References a changed API endpoint | High staleness |
| References old configuration keys | Medium staleness |
| Has not been modified since code changed | Low staleness signal |
| References files that were renamed/moved | High staleness |

Assign an overall score:
- **Fresh** (0 references to changed code)
- **Possibly stale** (references unchanged code near changed code)
- **Likely stale** (1-2 direct references to changed code)
- **Stale** (3+ direct references, or references removed code)

### 6. Present the freshness report

Output a report grouped by severity:

```
Documentation Freshness Report
==============================
Analyzed: 45 doc files against 23 code changes (last 30 days)

STALE (action required):
  docs/api/authentication.md
    - References `authenticate()` — renamed to `authenticateUser()` (src/auth.ts:42)
    - References `/api/v1/users` — endpoint moved to `/api/v2/users` (src/routes/users.ts:15)

  docs/getting-started.md
    - References `MONGO_URI` config — renamed to `DATABASE_URL` (src/config.ts:8)

LIKELY STALE (review recommended):
  docs/guides/deployment.md
    - References `startServer()` — function signature changed (src/server.ts:20)

POSSIBLY STALE (low confidence):
  docs/architecture.md
    - Last modified 45 days ago, references code in src/core/ which had 3 changes

FRESH:
  docs/contributing.md — No references to changed code
  docs/license.md — No references to changed code

Summary: 2 stale, 1 likely stale, 1 possibly stale, 2 fresh
```

### 7. Offer to draft updates

For each stale document, offer to:
1. **Show the specific lines** that need updating with the old and new values
2. **Draft an update** — read the doc, apply the necessary changes based on the code diff
3. **Skip** — just flag it for manual review

When drafting updates:
- Read both the doc file and the new code to understand the change
- Update function names, API paths, config keys to match new code
- Update code examples to use the new API
- Add notes about breaking changes if relevant
- Do NOT change content unrelated to the code changes
