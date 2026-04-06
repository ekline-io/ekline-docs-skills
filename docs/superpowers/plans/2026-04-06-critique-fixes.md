# Implementation Plan: Fix All Issues from Critiques

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 9 CRITICAL, 27 MEDIUM, and 21 LOW issues identified across the 12 per-skill critiques and cross-cutting `_overview.md`.

**Architecture:** Each fix follows the existing pattern — Python scripts (stdlib only) output JSON. Two new enforcement scripts (style-guide, terminology) parse rules from reference Markdown files. Shared utilities go in `skills/_shared/`.

**Tech Stack:** Python 3 (stdlib only), Markdown (SKILL.md), JSON output

---

## Dependency Graph

```
Phase 1 (Fixtures)
    |
    v
Phase 2 (Critical Bugs) -----> Phase 3 (Missing Tests)
    |                               |
    v                               v
Phase 4 (New Scripts) --------> Phase 5 (docs-health fix)
    |                               |
    v                               v
Phase 6 (Medium fixes) ------> Phase 7 (Shared utilities)
                                    |
                                    v
                               Phase 8 (Low fixes + polish)
```

Phases 2 and 3 can run in parallel. Phase 4 must complete before Phase 5. Phase 6 can start after Phase 3. Phase 8 is final polish.

---

## Phase 1: Test Infrastructure and Fixtures

### Task 1.1: Verify/fix test fixtures

**Files:** `tests/fixtures/*.md`, `tests/conftest.py`

- [ ] Verify `tests/fixtures/simple_doc.md` exists with ~150 words, 1 h1, 2 h2s
- [ ] Verify `tests/fixtures/thin_page.md` exists with < 30 words
- [ ] Verify `tests/fixtures/accessibility_issues.md` has `![]()` and `[click here]()`
- [ ] Verify `tests/fixtures/duplicate_a.md` and `duplicate_b.md` have >60% Jaccard similarity
- [ ] Create `tests/conftest.py` with `PROJECT_ROOT` and `FIXTURES_DIR` constants
- [ ] Run `python -m pytest tests/ -v` — all 51 existing tests pass

---

## Phase 2: CRITICAL Bug Fixes

### Task 2.1: Fix content-audit frontmatter false positives

**File:** `skills/content-audit/scripts/audit_content.py` (lines 357-367)

- [ ] Change the block at line 362-367: files without any frontmatter should get a single `"note": "File has no frontmatter"` with `"missing_fields": []` instead of listing all expected fields
- [ ] Add test in `tests/test_content_audit.py`: 3 temp files (2 with frontmatter, 1 without) — assert the no-frontmatter file has `missing_fields == []`

### Task 2.2: Fix changelog deduplication regex

**File:** `skills/changelog/scripts/parse_commits.py` (line 195)

- [ ] Replace `r"\s*\(#\d+\)\s*$"` with `r"\s*\(#\d+\)"` (remove `$` anchor)
- [ ] Apply same fix at line 215 if present
- [ ] Write test in new `tests/test_changelog.py`: two entries with same text but PR ref in different positions → deduplicate to one

### Task 2.3: Fix changelog vulnerability keyword regex

**File:** `skills/changelog/scripts/parse_commits.py` (line 56)

- [ ] Replace `r"\b(security|vulnerabilit|CVE-)\b"` with `r"\b(?:security|vulnerabilit\w*|CVE-\d+)\b"`
- [ ] Add tests: "fix vulnerability in auth" → Security, "fix CVE-2024-1234" → Security

### Task 2.4: Fix check-links heading_to_anchor for international text

**File:** `skills/check-links/scripts/extract_links.py` (lines 55-67)

- [ ] Add `flags=re.ASCII` to the `re.sub(r"[^\w\s-]", ...)` call so `\w` only matches `[a-zA-Z0-9_]`
- [ ] Write tests in new `tests/test_check_links.py`:
  - `"Getting started"` → `"getting-started"`
  - `"What's new in v2.0"` → `"whats-new-in-v20"`
  - `"FAQ & Troubleshooting"` → `"faq--troubleshooting"` or `"faq-troubleshooting"`

### Task 2.5: Fix check-links URL safety validation

**File:** `skills/check-links/scripts/extract_links.py` (lines 282-306)

- [ ] In `is_safe_external_url()`, add rejection for shell metacharacters: `` if any(c in url for c in '`$(){}|;'): return False ``
- [ ] Write test: `is_safe_external_url("http://example.com$(whoami)")` → `False`

---

## Phase 3: Write Missing Tests (can run parallel with Phase 2)

### Task 3.1: Tests for check-links (`tests/test_check_links.py`)

- [ ] `TestHeadingToAnchor` (~8 tests): ASCII, special chars, code, links, emoji, international, consecutive hyphens, empty
- [ ] `TestExtractLinks` (~6 tests): inline, reference-style, HTML href, inside code blocks (skipped), image, fragment-only
- [ ] `TestClassifyLink` (~5 tests): external, internal, anchor, email, image
- [ ] `TestValidateInternalLink` (~8 tests): existing fragment, missing fragment, relative file, missing file, route resolution, path traversal, anchor in file, wrong heading
- [ ] `TestIsSafeExternalUrl` (~5 tests): valid HTTP, valid HTTPS, file:// rejected, data: rejected, injection chars rejected
- [ ] Verify: `python -m pytest tests/test_check_links.py -v`

### Task 3.2: Tests for docs-freshness (`tests/test_docs_freshness.py`)

- [ ] `TestExtractSymbolsFromDiff` (~10 tests): Python/TS/Go functions, endpoints, env vars, config keys, short symbol filter, class/interface, empty diff
- [ ] `TestSearchDocsForSymbol` (~4 tests): found in code block (high), inline code (high), prose (low), not found
- [ ] `TestInputValidation` (~3 tests): invalid range chars, valid range, max-files bounds
- [ ] Verify: `python -m pytest tests/test_docs_freshness.py -v`

### Task 3.3: Tests for docs-coverage (`tests/test_docs_coverage.py`)

- [ ] `TestExtractTsExports` (~8 tests): function, const, class, interface, default, Express endpoint, short names filtered, TSX component
- [ ] `TestExtractPyExports` (~5 tests): def, class, Flask route, FastAPI route, private skipped
- [ ] `TestExtractGoExports` (~4 tests): public func, method, type struct, lowercase skipped
- [ ] `TestHasJsdoc` (~3 tests): adjacent JSDoc → True, no JSDoc → False, gap → False
- [ ] `TestCheckDocumentation` (~4 tests): documented, partial, undocumented, skipped
- [ ] Verify: `python -m pytest tests/test_docs_coverage.py -v`

### Task 3.4: Tests for changelog (`tests/test_changelog.py`)

- [ ] `TestClassifyConventional` (~6 tests): feat, fix(scope), feat!, chore, docs, unknown type
- [ ] `TestClassifyKeyword` (~5 tests): add, fix, remove, BREAKING CHANGE, update
- [ ] `TestDeduplicate` (~3 tests): same text deduped, PR refs merged, different kept
- [ ] `TestFormatEntry` (~3 tests): prefix stripped, PR appended, first letter capitalized
- [ ] `TestExtractPrIssueRefs` (~3 tests): PR#42, fixes #10, no refs
- [ ] Verify: `python -m pytest tests/test_changelog.py -v`

### Task 3.5: Tests for llms-txt (`tests/test_llms_txt.py`)

- [ ] `TestClassifyPage` (~5 tests): /api/ → API, /guides/ → Guides, /blog/ → Blog, /examples/ → Examples, root → Docs
- [ ] `TestExtractPageInfo` (~4 tests): frontmatter title, h1 only, neither, empty file
- [ ] `TestFilepathToUrl` (~3 tests): with base URL, index collapse, no base URL
- [ ] `TestDetectPlatform` (~3 tests): docusaurus, mkdocs, nothing
- [ ] Verify: `python -m pytest tests/test_llms_txt.py -v`

---

## Phase 4: New Enforcement Scripts (CRITICAL)

### Task 4.1: Create style-guide enforcement script

**File:** `skills/style-guide/scripts/check_style.py` (~200 lines)

- [ ] Parse banned phrases table from `references/style-rules.md` dynamically
- [ ] Accept docs directory argument, use `find_doc_files()` pattern
- [ ] For each file: strip frontmatter + code blocks, check banned phrases (case-insensitive), check heading case, check bare code fences
- [ ] Output JSON: `{summary: {files_scanned, total_violations, by_severity}, files: [{file, findings: [...]}]}`
- [ ] Create `tests/test_style_guide.py` (~10 tests): banned phrase detected, heading case violation, bare fence, clean file, frontmatter excluded, code blocks excluded

### Task 4.2: Create terminology enforcement script

**File:** `skills/terminology/scripts/check_terms.py` (~250 lines)

- [ ] Parse term tables from `references/terminology-rules.md` dynamically
- [ ] Extract (incorrect_variant, correct_term) pairs from each table
- [ ] Accept docs directory argument
- [ ] For each file: strip frontmatter + code blocks, check incorrect variants, check prohibited terms, flag context-dependent terms
- [ ] Output JSON with same structure as check_style.py
- [ ] Create `tests/test_terminology.py` (~8 tests): "NodeJS" → "Node.js", prohibited terms detected, correct terms pass, code blocks excluded, context-dependent terms flagged

### Task 4.3: Update SKILL.md files

- [ ] `skills/style-guide/SKILL.md`: Add Step 0 to run `scripts/check_style.py` before agent checks
- [ ] `skills/terminology/SKILL.md`: Add Step 0 to run `scripts/check_terms.py` before agent checks

---

## Phase 5: Fix docs-health Scoring Divergence (CRITICAL)

### Task 5.1: Rewrite docs-health style/terminology sections

**File:** `skills/docs-health/SKILL.md`

- [ ] Replace inline style checking (lines ~57-69) with: `python ../style-guide/scripts/check_style.py <docs_dir>`
- [ ] Replace inline terminology checking (lines ~71-84) with: `python ../terminology/scripts/check_terms.py <docs_dir>`
- [ ] Remove all hardcoded banned phrase lists from docs-health
- [ ] Score formula: `max(0, 100 - (summary.total_violations * 5))`

### Task 5.2: Specify exact freshness redistribution

- [ ] Add explicit formula: Links=29%, Readability=30%, Style=23%, Terminology=18% when freshness skipped

---

## Phase 6: MEDIUM Fixes

### Task 6.1: Readability improvements

- [ ] Add syllable corpus test (~20 words) in `tests/test_readability.py`
- [ ] Add `--max-sentence-length` CLI arg (default 25) to `analyze_readability.py`
- [ ] Add "Known Limitations" section to `skills/readability/SKILL.md`

### Task 6.2: Accessibility improvements

- [ ] Add whitespace-only alt text test to `tests/test_accessibility.py`
- [ ] Add HTML `<img>` without alt detection: `<img\s+(?![^>]*\balt=)[^>]*/?>`
- [ ] Expand `BAD_LINK_TEXT_RE` with: "this page", "this document", "more info", "learn more", "see here"
- [ ] Add mixed heading format test (Markdown + HTML in same file)

### Task 6.3: Content-audit improvements

- [ ] Lower sentence length threshold from 20 to 10 chars (line ~110)
- [ ] Lower `MIN_SENTENCES_FOR_COMPARISON` from 5 to 3 (line ~27)
- [ ] In SKILL.md, clarify "fewer than 100 words (< 100)"

### Task 6.4: Check-links improvements

- [ ] Use `os.path.realpath()` for path traversal guard (line ~215)
- [ ] Add shortcut reference link detection: `(?<!\[)\[([^\]]+)\](?!\[|\()`

### Task 6.5: Docs-freshness improvements

- [ ] Lower `MIN_SYMBOL_LENGTH` from 6 to 4 (line ~32)
- [ ] Add bracket notation env var patterns: `process.env["X"]`, `os.environ["X"]`
- [ ] Add git range validation with helpful error message

### Task 6.6: Docs-coverage improvements

- [ ] Fix JSDoc adjacency: verify no non-blank lines between JSDoc `*/` and target
- [ ] Add NestJS decorator patterns: `@Get("/users")`, `@Post("/users")`

### Task 6.7: LLMs-txt improvements

- [ ] Add `re.MULTILINE` flag to content pattern matching in `classify_page()`
- [ ] Increase `MAX_FILES` from 150 to 200
- [ ] Add `--platform` flag for monorepo override

### Task 6.8: Review-docs improvements

- [ ] Improve CLI-not-found error: suggest `/docs-health` as alternative
- [ ] Add token security note to SKILL.md

### Task 6.9: Changelog improvements

- [ ] Add `--include-docs` flag to include "Documentation" commits
- [ ] Add GitLab MR pattern (`!NNN`) to PR/issue ref extraction

---

## Phase 7: Shared Utilities

### Task 7.1: Create shared constants

**File:** `skills/_shared/constants.py`

- [ ] Define `MAX_DOC_FILES = 200`, `EXCLUDE_DIRS`, `DOC_EXTENSIONS`
- [ ] Use in new scripts (check_style.py, check_terms.py)

### Task 7.2: Create shared find_docs_dir

**File:** `skills/_shared/find_docs.py`

- [ ] Unified candidate list: docs, _docs, documentation, content, src/content/docs, pages/docs, pages
- [ ] Use in new scripts, leave existing scripts for gradual migration

---

## Phase 8: LOW Fixes and Polish

### Task 8.1: README corrections

- [ ] Fix "runs automatically" claims for style-guide and terminology
- [ ] Add "Known limitations" section

### Task 8.2: Readability LOW fixes

- [ ] Add English-only note to SKILL.md
- [ ] Strip bullet markers before sentence splitting in `analyze_readability.py`

### Task 8.3: Accessibility LOW fixes

- [ ] Add hex color pattern detection

### Task 8.4: Check-links LOW fixes

- [ ] Make anchor comparison case-sensitive (match GitHub behavior)
- [ ] Add per-domain rate limiting for external URL checks

### Task 8.5: Docs-freshness LOW fixes

- [ ] Add confidence level definitions to SKILL.md
- [ ] Add file rename handling in git diffs

### Task 8.6: Docs-coverage LOW fixes

- [ ] Clarify "partially documented" wording in SKILL.md
- [ ] Improve docs type heuristic with `/api/` directory check

### Task 8.7: LLMs-txt LOW fixes

- [ ] Pin spec version in output
- [ ] Extract base URL from Hugo/Jekyll configs (future enhancement note)

### Task 8.8: Vale configuration cleanup

- [ ] Add clarifying comment to `.vale.ini` explaining it's optional, not used by skills

---

## Success Criteria

- [ ] All existing 51 tests pass after Phase 1
- [ ] All 9 CRITICAL issues resolved after Phases 2-5
- [ ] Test coverage increases from 3/12 to 10/12 skills
- [ ] Total test count exceeds 150 (currently 51)
- [ ] `check_style.py` and `check_terms.py` produce valid JSON
- [ ] `docs-health` SKILL.md has no hardcoded phrase/term lists
- [ ] `python -m pytest tests/ -v` runs clean with zero failures
- [ ] No files exceeding 800 lines

## Files Summary

**New files (18):** tests/conftest.py, 5 test files, 2 enforcement scripts, 2 shared utilities, this plan, plus 6 fixture files already exist

**Modified files (17):** 8 Python scripts, 6 SKILL.md files, README.md, .vale.ini, 1 test file
