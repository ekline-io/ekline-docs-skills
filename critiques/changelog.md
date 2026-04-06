# Critique: changelog

**Script:** `skills/changelog/scripts/parse_commits.py`
**Tests:** None
**Overall:** Functional conventional-commit parser with good categorization. Has a dedup bug and some pattern gaps.

---

## Critical

### Deduplication regex only matches trailing PR references

Line ~195: `re.sub(r"\s*\(#\d+\)\s*$", ...)` assumes PR refs are at the end of the subject. Commits like `feat: something (#123) for module` with PR refs mid-string won't be deduplicated.

**Impact:** Duplicate changelog entries when the same change appears with different commit messages referencing the same PR.

**Action:** Match PR refs anywhere in the string, not just at the end.

---

## Medium

### Vulnerability keyword typo in regex

Line ~56: Pattern `\bsecurity|vulnerabilit|CVE-\b` matches "vulnerabilit" (missing 'y'). While this catches the stem, it could also match false positives in non-security contexts. The `\b` word boundary is also misplaced — it should wrap the entire alternation, not just the first/last term.

**Correct pattern:** `\b(?:security|vulnerabilit\w*|CVE-\d+)\b`

**Action:** Fix the regex and add word boundaries around the full alternation.

### "Documentation" category is in SKIP_CATEGORIES

Line ~48: `SKIP_CATEGORIES` includes "Documentation", so `docs:` conventional commits are silently dropped from the changelog. Users who want to document documentation changes in their changelog can't.

**Action:** Make `SKIP_CATEGORIES` configurable, or at least mention this behavior in the SKILL.md.

### No tests

Conventional commit parsing has many edge cases:
- `feat(scope): description` — scoped commits
- `feat!: description` — breaking change shorthand
- Multi-line commit bodies with `BREAKING CHANGE:` footer
- Non-conventional commits with heuristic classification

**Action:** Write tests covering at least 10 commit message formats.

---

## Low

### BREAKING CHANGE detection is redundant

Lines ~179-184: Breaking changes are detected twice — once via the `!` shorthand in `classify_commit` and again via the `BREAKING CHANGE` keyword in the body/footer parser.

**Action:** Not a bug (both paths produce the correct result), but simplify to one code path.

### Merge commits are skipped entirely

`--no-merges` flag means merge commit messages are never parsed. Some teams use merge commits as their primary commit style (squash-and-merge PRs).

**Action:** Add an option `--include-merges` for teams that use merge commits. Keep `--no-merges` as default.

### PR/issue reference extraction is GitHub-specific

Pattern matches `(#123)` style GitHub references. GitLab uses `!123` for MRs and `#123` for issues. Bitbucket uses different patterns.

**Action:** Add GitLab MR pattern (`!NNN`) and document platform assumptions.
