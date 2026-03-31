---
name: changelog
description: Generate a structured changelog entry from git history. Runs a helper script that analyzes commits and categorizes them (Added, Changed, Fixed, Removed, Security, Breaking Changes). Presents results in Keep a Changelog format. Use before a release or to catch up on missing entries.
allowed-tools: Read, Edit, Glob, Bash
metadata:
  author: EkLine
  version: "2.0.0"
  argument-hint: "[version_or_range]"
---

# Generate changelog

Run the helper script to parse git history, then present and optionally write the results.

## Inputs

- `$ARGUMENTS` — optional version tag or commit range (e.g., `v1.3.0`, `v1.2.0..v1.3.0`, `HEAD~20..HEAD`)

## Steps

### 1. Run the helper script

```bash
python scripts/parse_commits.py $ARGUMENTS
```

Capture the JSON output. The script handles range detection, commit parsing, conventional commit classification, keyword heuristics, PR/issue extraction, and deduplication.

Max 200 commits per run.

### 2. Handle errors

If the JSON contains an `error` field:

- `not_a_git_repo` — tell user to run from inside a git repository
- `no_commits` — tell user no commits were found in the given range, suggest a different range

Stop here on error.

### 3. Present the changelog entry

Using the `categories` object from the JSON, format a Keep a Changelog entry:

```markdown
## [Unreleased] - YYYY-MM-DD

### Breaking Changes
- {text from entries}

### Added
- {text from entries}

### Changed
- {text from entries}

### Fixed
- {text from entries}

### Removed
- {text from entries}

### Security
- {text from entries}
```

Only include categories that have entries. Use the `text` field from each entry directly — the script already formats entries with imperative mood and PR references.

Show the user:

- Number of commits analyzed (`total_commits_analyzed`)
- Number of entries generated (`total_changelog_entries`)
- Number skipped as internal (`total_skipped`)
- The full formatted entry

### 4. Ask the user

Ask whether they want to:

1. Write the entry to `CHANGELOG.md`
2. Just see the output (done)

### 5. Write to CHANGELOG.md

If the user wants to write:

**If `CHANGELOG.md` exists:**

- Read it with the Read tool
- Insert the new entry after the file header (before the first `## [` line)
- Preserve all existing content

**If `CHANGELOG.md` does not exist:**

- Create it with the standard header:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

{generated entry here}
```

Use the Edit tool to insert content.
