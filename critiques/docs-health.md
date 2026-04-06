# Critique: docs-health

**Script:** None (SKILL.md orchestrator only)
**Tests:** None
**Overall:** Good concept, but the inline re-implementation of style/terminology checks creates drift and inconsistency.

---

## Critical

### Style checking is duplicated and divergent

The docs-health SKILL.md hardcodes its own banned-phrase list and checking logic (~line 59-70) instead of reading from `style-guide/references/style-rules.md`. This means:

1. Adding a banned phrase to style-rules.md doesn't update docs-health
2. Running `/style-guide` and `/docs-health` can disagree on the same file
3. The scoring formula `max(0, 100 - violation_count * 5)` is arbitrary and not documented in style-guide

**Action:** Rewrite the style section to read and apply rules from `style-rules.md`. Remove the hardcoded phrase list.

### Terminology checking doesn't use terminology-rules.md

Similar to above — docs-health manually checks terminology instead of referencing the shared rules file.

**Action:** Rewrite to reference `terminology/references/terminology-rules.md`.

---

## Medium

### Sampling bias: "up to 10 files" is not representative

docs-health checks a sample of 10 files for style and terminology. A project with 200 docs could have 190 clean files and 10 problematic ones — or vice versa. The sample may over- or under-represent issues.

**Action:** Either:
- Check all files (style/terminology scripts would make this fast)
- Sample proportionally (10% of files, minimum 10) and scale results
- Document the sampling limitation in the report output

### Score weights are not configurable

Hardcoded weights (Links 25%, Readability 25%, Style 20%, Terminology 15%, Freshness 15%) may not match every team's priorities. An API-heavy project might care more about coverage than style.

**Action:** Accept as default weights but add an optional `--weights` argument or config file.

### Freshness skip doesn't reweight correctly

When freshness is skipped (non-git repo), the SKILL.md says remaining categories "reweight proportionally." But the actual redistribution math isn't specified — the agent must figure it out.

**Action:** Specify the exact redistribution formula. E.g., if freshness (15%) is skipped, the remaining 85% becomes 100%: Links = 25/85 * 100 = 29.4%, etc.

---

## Low

### No caching between runs

Each docs-health invocation re-runs all 5 checks from scratch. For large doc sets, this could be slow.

**Action:** Future consideration — add a cache file (`.docs-health-cache.json`) that stores results with file hashes. Only re-check changed files.

### Report format is nice but not machine-readable

The report card is formatted for human reading (letter grades, bars) but there's no JSON output option for CI integration.

**Action:** Add `--json` flag that outputs structured results alongside the human-readable report.
