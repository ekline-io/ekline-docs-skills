# Critique: docs-freshness

**Script:** `skills/docs-freshness/scripts/extract_changes.py`
**Tests:** None
**Overall:** Clever approach using git diffs, but pattern matching has gaps and there are no tests.

---

## Critical

### No tests

Git diff parsing is inherently fragile — different git versions, merge strategies, and diff formats can produce different output. Without tests, regressions will go unnoticed.

**Action:** Write tests with fixture diffs covering:
- Function renames (Python, TypeScript, Go)
- Endpoint changes (Express, Flask, FastAPI)
- Config key changes
- Environment variable changes
- Multi-language diffs in the same commit
- Merge commits vs. regular commits

---

## Medium

### MIN_SYMBOL_LENGTH = 6 is too strict

Line ~32: Symbols shorter than 6 characters are filtered out. Common API symbols that would be missed:
- `fetch`, `query`, `route`, `parse`, `build` (5 chars)
- `init`, `send`, `stop`, `load` (4 chars)
- `run`, `get`, `set`, `put` (3 chars)

**Impact:** Staleness of docs referencing these short-named functions won't be detected.

**Action:** Lower to 3 or 4 characters. The risk of false positives from short names is lower than the risk of missing real staleness.

### Environment variable pattern misses bracket notation

Line ~62: Pattern `(?:process\.env\.|os\.environ\.get\(|os\.getenv\()` misses:
- `process.env[MY_VAR]` (bracket notation in Node.js)
- `os.environ["MY_VAR"]` (dict access in Python)
- `std::env::var("MY_VAR")` (Rust)
- `System.getenv("MY_VAR")` (Java)

**Action:** Add bracket notation patterns for at least Node.js and Python.

### Config key extraction is too simple

Line ~64: Only extracts single-level config keys. Nested configs like `config.database.host` or `settings.DATABASES.default.ENGINE` only capture the first level.

**Action:** Extract the full dotted path up to the value assignment.

---

## Low

### No handling of file renames in git diffs

If a source file is renamed (`git mv old.ts new.ts`), the diff shows the rename but the script may not track that docs referencing `old.ts` are now stale.

**Action:** Parse git's rename detection (`diff --find-renames`) and flag docs that reference the old filename.

### Confidence levels ("high" / "low") are not clearly defined

The SKILL.md mentions high and low confidence matching but doesn't define what makes a match high vs. low confidence.

**Action:** Document the criteria. E.g., "High = exact function name match in a code reference. Low = partial name match or keyword proximity."

### Git range parsing edge cases

If a user passes an invalid range like `v1.0.0..v2.0.0` where `v1.0.0` doesn't exist, the script should fail gracefully with a helpful message.

**Action:** Validate the git range before running the diff and provide a clear error.
