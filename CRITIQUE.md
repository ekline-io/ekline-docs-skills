# Skills Critique and Improvement Tracker

Harsh assessment of all 5 new skills (llms-txt, docs-freshness, changelog, check-links, docs-coverage) created 2026-03-25. This document tracks what's wrong, what needs fixing, and the status of each fix.

---

## Systemic Issues

These problems affect all 5 new skills equally.

### S1. No real-world testing
- [x] **Fixed** (2026-03-25)

**Problem:** Not a single skill has been run against a real project. The existing skills had real substance (run_review.py, style-rules.md, terminology-rules.md). Our 5 new skills are pure prose instructions with no backing implementation — elaborate prompts hoping Claude figures it out.

**Fix:** Tested helper scripts against 3 real repos. Results below.

**Test matrix:**

| Skill | Express.js (small) | p0-docs (147 md files) | ekline-app (737 TS + 27 docs) |
|-------|--------------------|------------------------|-------------------------------|
| llms-txt | [ ] | [ ] | [ ] |
| docs-freshness | n/a | n/a | [x] 28 symbols, 1 likely stale |
| changelog | [x] 7 commits, 2 entries | n/a | [x] 8 commits, 8 entries |
| check-links | n/a | [x] 434 links, 12 broken | n/a |
| docs-coverage | [x] 39 items, 38% cov | n/a | [x] 67 items, 1% cov |

**Issues found and fixed during testing:**
- changelog: Ticket prefixes (EK-1234:) caused everything to classify as "Changed" → fixed with prefix stripping
- docs-coverage: .js/.jsx files not supported → fixed, Express.js now detects 39 items
- docs-freshness: Short env var names (`key`, 3 chars) caused false positives → raised MIN_SYMBOL_LENGTH to 6
- check-links: Emoji characters in heading anchors caused false broken link reports → fixed with emoji stripping

---

### S2. No token budgets or sampling strategies
- [x] **Fixed** (2026-03-25)

**Problem:** On real projects, these skills will consume enormous context. docs-freshness on 50 changed files + 100 doc pages = 50+ git diff commands + 200+ Grep queries = 50,000-100,000 tokens easily. Users will hit context limits before the skill finishes. No skill says "if there are more than X, prioritize" — they all say "do everything."

**Fix:** Add explicit limits to every skill:
- [ ] Max files to analyze per run (e.g., 30 changed files, 50 doc files)
- [ ] Prioritization strategy when over limit (by diff size, by recency, by directory)
- [ ] "If the project has more than X, ask the user to narrow the scope"
- [ ] Token-aware batching for tool calls

---

### S3. No error handling or graceful degradation
- [x] **Fixed** (2026-03-25)

**Problem:** None of the skills handle edge cases. What happens when:
- No git history? (docs-freshness, changelog)
- Monorepo with 10,000 files? (docs-coverage)
- 500+ doc files? (llms-txt, check-links)
- 5,000 commits in range? (changelog)
- Unsupported language? (docs-coverage)
- External URLs behind Cloudflare? (check-links)

**Fix:** Add explicit error handling blocks to every skill:
- [ ] "If no git repo detected, tell the user and exit"
- [ ] "If more than N files/commits, warn and offer to sample"
- [ ] "If language not supported, list supported languages and exit"
- [ ] Fallback behaviors for every step that depends on external state

---

### S4. No helper scripts for deterministic work
- [x] **Fixed** (2026-03-25)

**Problem:** The existing `review-docs` skill works well because `run_review.py` does the heavy, deterministic parsing and hands Claude a clean JSON summary. Our new skills ask Claude to be both the data processor AND the interpreter. Claude is a bad data processor — it hallucinates patterns, miscounts, and loses track of large datasets.

**Fix:** Add Python/bash helper scripts for:
- [ ] `docs-freshness/scripts/extract_changes.py` — parse git diffs, extract changed symbols, cross-reference docs, output clean JSON
- [ ] `changelog/scripts/parse_commits.py` — parse git log, classify commits, extract PR/issue refs, output JSON
- [ ] `docs-coverage/scripts/scan_exports.py` — extract public API surface per language, output JSON
- [ ] `check-links/scripts/extract_links.py` — parse all links from docs, validate internal links, output JSON

Claude then interprets the pre-processed data and presents/acts on it — what it's actually good at.

---

### S5. Fake example outputs set undeliverable expectations
- [x] **Partially fixed** (2026-03-25) — SKILL.md files now reference script JSON output instead of showing fake reports. Full real example outputs still TODO.

**Problem:** Every skill shows a clean, fabricated report. Users run the skill and get something that looks nothing like the example — maybe a wall of text, maybe a half-finished report, maybe hallucinated findings. We're marketing a screenshot of a product that doesn't exist.

**Fix:**
- [ ] Run each skill on a real repo and capture the actual output
- [ ] Replace all example outputs with real ones (or clearly mark them as "example format")
- [ ] Add a note about expected output variance

---

## Skill-Specific Issues

### llms-txt

#### L1. Classification is non-deterministic
- [x] **Fixed** (2026-03-25)

**Problem:** "Categorize docs into Docs/API/Guides/Blog/Examples" relied entirely on Claude's judgment.

**Fix:** Helper script (generate_llms_txt.py) implements deterministic classification:
- [x] Path-based rules: api/, reference/ → API; guide/, tutorial/, getting-started → Guides; blog/, _posts/ → Blog; examples/, quickstart/ → Examples; everything else → Docs
- [x] Tested on p0-docs: 145 Docs + 2 Guides (correct)
- [x] Tested on ekline-app: 17 Docs, 1 Guide, 1 Blog, 5 Examples (correct)

---

#### L2. Generates file paths, not URLs
- [x] **Fixed** (2026-03-25)

**Problem:** The skill output file paths, but hosted docs need URLs.

**Fix:** Helper script implements:
- [x] Platform detection: Docusaurus, Mintlify, MkDocs, GitBook, Astro Starlight, VitePress, Nextra
- [x] Base URL extraction from platform config files (site_url, site, url fields)
- [x] URL path generation: strips .md extension, converts to URL-friendly paths
- [x] `--base-url` argument for manual override
- [x] Falls back to relative file paths when no URL is detected
- [x] Tested: ekline-app correctly detects Astro Starlight platform

---

#### L3. llms-full.txt is a token bomb
- [x] **Fixed** (2026-03-25)

**Problem:** Generating llms-full.txt for 50+ files would dump hundreds of thousands of tokens.

**Fix:**
- [x] Lowered threshold to 20 files AND 200KB total (was "under 100 files")
- [x] Script pre-calculates total size from file sizes (no content reading needed)
- [x] Returns `can_generate_full: false` with `full_warning` message when over limits
- [x] Tested: Express.js (4 files, 133KB) → eligible. p0-docs (147 files, 646KB) → correctly rejected

---

#### L4. No handling for docs-as-code platforms
- [x] **Partially fixed** (2026-03-25)

**Problem:** Docusaurus uses sidebars.js for ordering. MkDocs uses mkdocs.yml nav. Mintlify uses mint.json.

**Fix:**
- [x] Platform detection for 7 platforms (Docusaurus, Mintlify, MkDocs, GitBook, Astro Starlight, VitePress, Nextra)
- [x] Base URL extraction from platform configs
- [x] Parent directory traversal to find config when docs dir is nested
- [ ] TODO: Read sidebars.js / mkdocs.yml nav for page ordering (currently uses keyword-based priority)
- [ ] TODO: Use platform section names instead of generic Docs/API/Guides

---

### docs-freshness

#### F1. Grep produces massive false positives
- [x] **Fixed** (2026-03-25)

**Problem:** Grepping `"authenticate"` in docs matches `"We authenticate users using OAuth"` — prose that has nothing to do with the `authenticate()` function. Common words like `create`, `update`, `get`, `delete` would match everything.

**Fix:** Helper script (extract_changes.py) implements:
- [x] Code-context matching: backtick-wrapped terms, function call syntax `functionName(`, assignment syntax
- [x] Code-block matches scored as "high confidence", prose matches as "low confidence"
- [x] Only high-confidence matches trigger staleness flags
- [x] Symbols under 6 characters filtered out (MIN_SYMBOL_LENGTH = 6)

---

#### F2. "Possibly stale" category is meaningless
- [ ] **Fixed**

**Problem:** "References unchanged code near changed code" is too vague. Claude will either flag everything or nothing. What does "near" mean? Same file? Same directory? Same module?

**Fix:** Either:
- [ ] Remove this category entirely (keep only Fresh / Likely Stale / Stale)
- [ ] Or define it precisely: "Doc references a function in a file where other functions changed, but this specific function did not change"

---

#### F3. 30-day default is arbitrary and dangerous
- [ ] **Fixed**

**Problem:** Active projects could have 500+ commits in 30 days. The diff output would be enormous and exceed context limits.

**Fix:**
- [ ] Default to last tag-to-HEAD (or last 50 commits if no tags)
- [ ] Cap at a maximum diff size (e.g., 100 changed files)
- [ ] If over limit, show the user what's in scope and ask to narrow

---

#### F4. No helper script for diff parsing
- [x] **Fixed** (2026-03-25)

**Problem:** Asking Claude to parse raw git diffs for function renames, endpoint changes, etc. is unreliable. Git diffs are complex and Claude will miss things or hallucinate patterns.

**Fix:**
- [ ] Create `scripts/extract_changes.py` that:
  - Runs git diff
  - Parses changed function signatures (using tree-sitter or regex per language)
  - Cross-references against doc files
  - Outputs a clean JSON summary for Claude to interpret

---

### changelog

#### C1. Keyword classification is naive and ambiguous
- [x] **Fixed** (2026-03-25)

**Problem:** "Add error handling for removed endpoints" matches both "add" (Added) and "removed" (Removed). Which category wins? The skill doesn't specify precedence rules.

**Fix:** Helper script (parse_commits.py) implements:
- [x] Conventional commit detection first (type: prefix)
- [x] Ticket prefix stripping (EK-1234:, PROJ-456:) before keyword analysis
- [x] Keywords matched at start of message only (not anywhere in it)
- [x] Explicit precedence: Breaking > Security > Added > Fixed > Removed > Changed
- [x] Deduplication by normalized subject

---

#### C2. Deduplication is hand-waved
- [ ] **Fixed**

**Problem:** "Deduplicate same change described in multiple commits" is a genuinely hard problem. How does Claude know commit A and commit B describe the same change? It often can't.

**Fix:**
- [ ] Group by PR number first (most reliable dedup signal)
- [ ] For non-PR commits, group by modified files + similar message text
- [ ] When in doubt, keep both entries rather than risking data loss
- [ ] Let the user resolve ambiguous duplicates

---

#### C3. --format flag is a lie
- [x] **Fixed** (2026-03-25)

**Problem:** The argument-hint mentioned `--format keepachangelog|conventional|custom` but only Keep a Changelog format was specified.

**Fix:** Removed the flag from metadata. Only Keep a Changelog format is supported — shipped one format, made it good.

---

#### C4. Squash-and-merge detection is impossible from git log
- [ ] **Fixed**

**Problem:** "Merge squash-and-merge commits with their PR descriptions" requires the GitHub API to get PR descriptions. Git log alone doesn't have this data.

**Fix:**
- [ ] Remove this claim unless we add GitHub API integration
- [ ] Or: detect squash-merge commits (they often have "(#123)" in the subject) and note the PR number, but don't claim to have the PR description
- [ ] Optional: if `gh` CLI is available, fetch PR descriptions

---

### check-links

#### K1. Grep patterns don't match how the tool works
- [x] **Fixed** (2026-03-25)

**Problem:** The skill specified regex with capture groups but the Grep tool returns matching lines, not capture groups.

**Fix:** Added `scripts/extract_links.py` that does the parsing:
- [x] Proper Markdown link extraction (inline, reference-style, HTML)
- [x] Skips links inside code blocks (tracks fenced code block state)
- [x] Validates internal links, anchors, and images
- [x] Outputs clean JSON for Claude to present and act on
- [x] Tested on p0-docs: found 434 links, 12 real broken links

---

#### K2. Rate limiting instruction will be ignored
- [ ] **Fixed**

**Problem:** "Check at most 5 URLs per second" — Claude has no mechanism to rate-limit Bash calls. This instruction is unenforceable and will be ignored.

**Fix:**
- [ ] Move external link checking to a helper script that handles rate limiting
- [ ] Or batch URLs: "Run 5 curl commands, then pause 1 second, then 5 more"
- [ ] Or just check external links sequentially (one curl per tool call has natural rate limiting)

---

#### K3. curl will get blocked by most modern sites
- [ ] **Fixed**

**Problem:** Sites with Cloudflare, bot protection, or JavaScript-rendered responses will return 403 for `curl`. This will produce a flood of false "broken" links.

**Fix:**
- [ ] Set a proper User-Agent header in curl
- [ ] Classify 403 separately from 404 — "403 may be bot protection, not a broken link"
- [ ] Add HEAD request before GET (lighter, less likely to be blocked)
- [ ] Accept 403 as "indeterminate, likely OK" rather than "broken"
- [ ] Let user opt out of external checking by default (make --external genuinely optional, not recommended)

---

#### K4. Fuzzy matching for broken link suggestions
- [ ] **Fixed**

**Problem:** "If a similar file exists (fuzzy match), update the link" — Claude will make incorrect suggestions confidently. Fuzzy matching file names is error-prone.

**Fix:**
- [ ] Only suggest when edit distance is very small (1-2 chars) or the file name differs only by extension
- [ ] Show the suggestion but never auto-apply without user confirmation
- [ ] List all files in the same directory as alternatives rather than guessing

---

### docs-coverage

#### D1. Function name search is hopelessly imprecise
- [x] **Fixed** (2026-03-25)

**Problem:** Grepping function names like `get`, `create`, `update` in docs matches everything.

**Fix:** Helper script (scan_exports.py) implements:
- [x] Searches for backtick-wrapped names or heading mentions only
- [x] Names under 6 chars skipped from doc search (MIN_SEARCH_LENGTH)
- [x] Names under 4 chars skipped from extraction entirely (MIN_NAME_LENGTH)
- [x] Tested on ekline-app: 67 items, 1% documented (realistic for internal code with product docs)

---

#### D2. Python regex matches everything, not just public API
- [x] **Fixed** (2026-03-25)

**Problem:** `^def\s+[a-z]\w+` matches every function in every file — test helpers, migration scripts, build scripts, fixtures, conftest functions, CLI scripts.

**Fix:** Helper script (scan_exports.py) implements:
- [x] Excludes test directories: test/, tests/, __tests__, spec/, specs/
- [x] Excludes test files: *_test.py, test_*.py, conftest.py, *.spec.ts, *.test.ts
- [x] Excludes non-API directories: migrations/, seeds/, fixtures/, mocks/
- [x] Excludes .d.ts files, .stories.tsx files, setup.py
- [x] Only scans within the specified source directory

---

#### D3. JSDoc line counting is ambiguous
- [ ] **Fixed**

**Problem:** "Has inline documentation of 3+ lines" — is `/**` a line? Is `*/` a line? Is `@param` a line? Different interpretations give different scores. Runs will be inconsistent.

**Fix:**
- [ ] Define precisely: "3+ lines of content excluding the opening `/**`, closing `*/`, and empty lines"
- [ ] Or simplify: "Has a JSDoc/docstring comment (any length)" counts as inline docs
- [ ] Better yet: put this logic in a helper script with exact rules

---

#### D4. Claims 5 languages, delivers maybe 2
- [x] **Fixed** (2026-03-25)

**Problem:** Listed TypeScript, Python, Go, Rust, Java in detection but only had regex patterns for 3. Rust and Java had no patterns.

**Fix:**
- [x] Removed Rust and Java from language detection and description
- [x] Added JS/JSX/MJS support (Express.js now works — tested: 39 items found)
- [x] Added module.exports pattern detection for CommonJS
- [x] Description updated: "Supports TypeScript/JavaScript, Python, Go"

---

#### D5. No filtering of internal/private exports
- [ ] **Fixed**

**Problem:** In TypeScript, `export` doesn't always mean "public API for consumers." Barrel files re-export internal modules. Types exported for testing aren't part of the public API.

**Fix:**
- [ ] Focus on entry point files (package.json "main"/"exports", index.ts)
- [ ] Skip files in `internal/`, `__tests__/`, `test/` directories
- [ ] Weight items by import count (more imported = more important to document)
- [ ] Let user specify which directories are "public API" via arguments

---

## Priority Order for Fixes

### Phase 1: Make them not embarrassing (before publishing)
1. Add token budgets and limits to all skills (S2)
2. Add basic error handling to all skills (S3)
3. Fix the Grep false-positive problem for docs-freshness (F1) and docs-coverage (D1)
4. Remove --format flag lie from changelog (C3)
5. Remove unsupported languages from docs-coverage (D4)
6. Fix check-links regex to match actual tool API (K1)

### Phase 2: Make them actually work (week 2)
7. Test all skills on real repos (S1)
8. Add helper scripts for docs-freshness and changelog (S4, F4, C1)
9. Add classification-rules.md for llms-txt (L1)
10. Fix URL generation for hosted docs (L2)
11. Replace fake outputs with real ones (S5)

### Phase 3: Make them great (ongoing)
12. Add helper scripts for docs-coverage and check-links (D1, K1)
13. Add docs platform detection for llms-txt (L4)
14. Add GitHub API integration for changelog PR descriptions (C4)
15. Expand docs-coverage to more languages with tested patterns (D4)

---

## Log

| Date | Change | Issues Addressed |
|------|--------|-----------------|
| 2026-03-25 | Initial skills created, critique document written | — |
| 2026-03-25 | Added 4 helper scripts (parse_commits.py, extract_links.py, extract_changes.py, scan_exports.py) | S4 |
| 2026-03-25 | Tested all scripts against ekline-app, p0-docs, Express.js | S1 |
| 2026-03-25 | Fixed ticket prefix handling in changelog | C1, C3 |
| 2026-03-25 | Added JS/JSX support and module.exports detection in docs-coverage | D4 |
| 2026-03-25 | Fixed emoji anchor handling in check-links | K1 |
| 2026-03-25 | Raised MIN_SYMBOL_LENGTH to 6 in docs-freshness | F1 |
| 2026-03-25 | Updated all 4 SKILL.md files to use scripts instead of manual instructions | S2, S3, S4, S5 |
| 2026-03-25 | Added token limits to all skills (50 files, 200 commits, etc.) | S2 |
| 2026-03-25 | Added error handling for all script error codes | S3 |
| 2026-03-25 | Added llms-txt helper script with platform detection, deterministic classification, URL generation | L1, L2, L3, L4 |
| 2026-03-25 | Tested llms-txt against p0-docs (147 files), ekline-app (24 docs), Express.js (4 files) | S1 |
