---
name: changelog
description: Generate a structured changelog entry from git history. Analyzes commits, PRs, and tags to produce a well-organized CHANGELOG.md entry categorized by type (Added, Changed, Fixed, Removed). Use this skill before a release or to catch up on missing changelog entries.
allowed-tools: Read, Glob, Grep, Bash
metadata:
  argument-hint: "[version_or_range] [--format keepachangelog|conventional|custom]"
---

# Generate changelog

Analyze git history and produce a structured changelog entry.

## Inputs

- `$ARGUMENTS` — optional version tag or commit range (e.g., `v1.3.0`, `v1.2.0..v1.3.0`, `HEAD~20..HEAD`), and optional format flag

## Steps

### 1. Determine the range

If a version is provided (e.g., `v1.3.0`):

```bash
git describe --tags --abbrev=0 HEAD^ 2>/dev/null
```

Use the previous tag as the start, and the provided version (or HEAD) as the end.

If a range is provided (e.g., `v1.2.0..v1.3.0`), use it directly.

If nothing is provided, use the range from the most recent tag to HEAD:

```bash
git describe --tags --abbrev=0 2>/dev/null
```

If no tags exist, use the last 50 commits.

### 2. Gather commits

```bash
git log {start}..{end} --format="%H|%s|%b|%an|%ae|%aI" --no-merges
```

Also gather merge commits to find PR references:

```bash
git log {start}..{end} --merges --format="%H|%s|%b"
```

### 3. Parse and categorize

Classify each commit into changelog categories:

**If using conventional commits** (detected by `type:` or `type(scope):` prefix):

| Prefix | Category |
|--------|----------|
| `feat:` | Added |
| `fix:` | Fixed |
| `refactor:` | Changed |
| `perf:` | Changed (Performance) |
| `docs:` | Documentation |
| `test:` | skip (internal) |
| `chore:` | skip (internal) |
| `ci:` | skip (internal) |
| `BREAKING CHANGE:` | Breaking Changes |

**If not using conventional commits**, analyze the commit message:
- Messages containing "add", "new", "create", "implement", "introduce" → **Added**
- Messages containing "fix", "resolve", "patch", "correct", "handle" → **Fixed**
- Messages containing "change", "update", "modify", "refactor", "improve", "enhance" → **Changed**
- Messages containing "remove", "delete", "drop", "deprecate" → **Removed**
- Messages containing "security", "vulnerability", "CVE" → **Security**
- Messages containing "breaking" or prefixed with `!` → **Breaking Changes**

### 4. Extract PR and issue references

From commit messages and bodies, extract:
- PR numbers: `#123`, `(#123)`, `Merge pull request #123`
- Issue references: `Fixes #456`, `Closes #789`, `Resolves #101`

### 5. Group and deduplicate

- Group entries by category
- Deduplicate (same change described in multiple commits)
- Merge squash-and-merge commits with their PR descriptions
- Order categories: Breaking Changes → Added → Changed → Fixed → Removed → Security → Documentation

### 6. Generate the changelog entry

**Keep a Changelog format** (default):

```markdown
## [{version}] - {YYYY-MM-DD}

### Breaking Changes

- Renamed `authenticate()` to `authenticateUser()` for clarity (#234)

### Added

- Add support for Redis caching in the query layer (#210)
- Add `--verbose` flag to CLI output (#215)

### Changed

- Improve error messages for authentication failures (#220)
- Update minimum Node.js version to 18 (#225)

### Fixed

- Fix race condition in concurrent file uploads (#212)
- Resolve memory leak in WebSocket handler (#218)

### Removed

- Remove deprecated `legacyAuth` module (#230)
```

Rules for writing entries:
- Start each entry with a verb in imperative mood ("Add", not "Added" or "Adds")
- Include PR/issue numbers in parentheses at the end
- Keep entries to one line (wrap details into the PR)
- Be specific — "Fix race condition in concurrent file uploads" not "Fix bug"
- Group related changes into a single entry when appropriate
- Skip commits that are purely internal (test fixes, CI changes, dependency bumps) unless they affect users

### 7. Write or update CHANGELOG.md

Check if `CHANGELOG.md` exists:

**If it exists:**
- Read the existing file
- Insert the new entry after the header and before the previous version
- Preserve existing content unchanged

**If it does not exist:**
- Create a new file with the standard header:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

{generated entries here}
```

### 8. Present summary

Show the user:
- Number of commits analyzed
- Number of changelog entries generated per category
- The full generated entry for review before writing
- Ask if they want to write it to `CHANGELOG.md` or just output the text
