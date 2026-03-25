# Skills Critique and Improvement Tracker

Harsh assessment of all 5 new skills (llms-txt, docs-freshness, changelog, check-links, docs-coverage) created 2026-03-25. This document tracks what's wrong, what needs fixing, and the status of each fix.

---

## Systemic Issues

These problems affect all 5 new skills equally.

### S1. No real-world testing
- [ ] **Fixed**

**Problem:** Not a single skill has been run against a real project. The existing skills had real substance (run_review.py, style-rules.md, terminology-rules.md). Our 5 new skills are pure prose instructions with no backing implementation — elaborate prompts hoping Claude figures it out.

**Fix:** Test each skill against 2-3 real open-source repos (e.g., Fastify, Express, EkLine's own docs). Record actual output. Fix prompts based on what actually happens vs. what we expected. Replace fake example outputs with real ones.

**Test matrix:**

| Skill | Small repo (<20 docs) | Medium repo (20-100 docs) | Large repo (100+ docs) | EkLine docs |
|-------|----------------------|--------------------------|----------------------|-------------|
| llms-txt | [ ] | [ ] | [ ] | [ ] |
| docs-freshness | [ ] | [ ] | [ ] | [ ] |
| changelog | [ ] | [ ] | [ ] | [ ] |
| check-links | [ ] | [ ] | [ ] | [ ] |
| docs-coverage | [ ] | [ ] | [ ] | [ ] |

---

### S2. No token budgets or sampling strategies
- [ ] **Fixed**

**Problem:** On real projects, these skills will consume enormous context. docs-freshness on 50 changed files + 100 doc pages = 50+ git diff commands + 200+ Grep queries = 50,000-100,000 tokens easily. Users will hit context limits before the skill finishes. No skill says "if there are more than X, prioritize" — they all say "do everything."

**Fix:** Add explicit limits to every skill:
- [ ] Max files to analyze per run (e.g., 30 changed files, 50 doc files)
- [ ] Prioritization strategy when over limit (by diff size, by recency, by directory)
- [ ] "If the project has more than X, ask the user to narrow the scope"
- [ ] Token-aware batching for tool calls

---

### S3. No error handling or graceful degradation
- [ ] **Fixed**

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
- [ ] **Fixed**

**Problem:** The existing `review-docs` skill works well because `run_review.py` does the heavy, deterministic parsing and hands Claude a clean JSON summary. Our new skills ask Claude to be both the data processor AND the interpreter. Claude is a bad data processor — it hallucinates patterns, miscounts, and loses track of large datasets.

**Fix:** Add Python/bash helper scripts for:
- [ ] `docs-freshness/scripts/extract_changes.py` — parse git diffs, extract changed symbols, cross-reference docs, output clean JSON
- [ ] `changelog/scripts/parse_commits.py` — parse git log, classify commits, extract PR/issue refs, output JSON
- [ ] `docs-coverage/scripts/scan_exports.py` — extract public API surface per language, output JSON
- [ ] `check-links/scripts/extract_links.py` — parse all links from docs, validate internal links, output JSON

Claude then interprets the pre-processed data and presents/acts on it — what it's actually good at.

---

### S5. Fake example outputs set undeliverable expectations
- [ ] **Fixed**

**Problem:** Every skill shows a clean, fabricated report. Users run the skill and get something that looks nothing like the example — maybe a wall of text, maybe a half-finished report, maybe hallucinated findings. We're marketing a screenshot of a product that doesn't exist.

**Fix:**
- [ ] Run each skill on a real repo and capture the actual output
- [ ] Replace all example outputs with real ones (or clearly mark them as "example format")
- [ ] Add a note about expected output variance

---

## Skill-Specific Issues

### llms-txt

#### L1. Classification is non-deterministic
- [ ] **Fixed**

**Problem:** "Categorize docs into Docs/API/Guides/Blog/Examples" relies entirely on Claude's judgment. Same file could be "Docs" one time, "Guides" the next. No classification rules, just vibes.

**Fix:** Add a `classification-rules.md` reference file with concrete heuristics:
- Files in `api/` or containing OpenAPI schemas → API
- Files with numbered steps or "tutorial" in path → Guides
- Files in `blog/` or `_posts/` → Blog
- Files with "example" in path or primarily code blocks → Examples
- Everything else → Docs
- Allow user override via frontmatter (`category: guide`)

---

#### L2. Generates file paths, not URLs
- [ ] **Fixed**

**Problem:** The skill outputs `./docs/getting-started.md` but users hosting on Mintlify, GitBook, or Docusaurus need URLs like `https://docs.example.com/getting-started`. File paths are useless for hosted docs sites.

**Fix:**
- [ ] Detect docs platform from config files (docusaurus.config.js, mintlify.json, mkdocs.yml, etc.)
- [ ] If platform detected, generate URL paths using the platform's routing conventions
- [ ] If base URL found in config, use it as prefix
- [ ] Fall back to relative file paths only when no platform or URL is detected
- [ ] Add a `--base-url` argument option

---

#### L3. llms-full.txt is a token bomb
- [ ] **Fixed**

**Problem:** Generating llms-full.txt for 50+ files means reading and concatenating hundreds of thousands of tokens into a single file. The skill says "under 100 files" but even 30 medium docs could be 200K+ tokens.

**Fix:**
- [ ] Lower the threshold significantly (e.g., under 20 files and under 50KB total)
- [ ] Calculate total size before generating — read file sizes, not contents
- [ ] Warn user of total size before writing
- [ ] Consider generating a truncated version (first N lines of each doc) for larger projects

---

#### L4. No handling for docs-as-code platforms
- [ ] **Fixed**

**Problem:** Docusaurus uses sidebars.js for ordering. MkDocs uses mkdocs.yml nav. Mintlify uses mint.json. The skill ignores all of these and guesses ordering by "importance" (undefined).

**Fix:**
- [ ] Read sidebars.js, mkdocs.yml, mint.json, etc. when present
- [ ] Use the platform's nav structure to determine page order and hierarchy
- [ ] Use the platform's section names instead of generic Docs/API/Guides

---

### docs-freshness

#### F1. Grep produces massive false positives
- [ ] **Fixed**

**Problem:** Grepping `"authenticate"` in docs matches `"We authenticate users using OAuth"` — prose that has nothing to do with the `authenticate()` function. Common words like `create`, `update`, `get`, `delete` would match everything.

**Fix:**
- [ ] Grep for function names with code context: backtick-wrapped terms, function call syntax `functionName(`, import statements
- [ ] Require matches inside code blocks or backticks for common-word function names
- [ ] Weight code-block matches higher than prose matches
- [ ] Add a confidence score to each finding: "high confidence (exact code reference)" vs "low confidence (prose mention)"
- [ ] Filter out generic words under 6 characters from the search

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
- [ ] **Fixed**

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
- [ ] **Fixed**

**Problem:** "Add error handling for removed endpoints" matches both "add" (Added) and "removed" (Removed). Which category wins? The skill doesn't specify precedence rules.

**Fix:**
- [ ] Define explicit precedence: first keyword match wins (scan left to right)
- [ ] Or better: classify based on the verb at the start of the message, not keywords anywhere in it
- [ ] Add a "manual review" category for ambiguous commits
- [ ] Add a helper script that does the classification deterministically

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
- [ ] **Fixed**

**Problem:** The argument-hint mentions `--format keepachangelog|conventional|custom` but only Keep a Changelog format is actually specified. The flag does nothing.

**Fix:** Either:
- [ ] Remove the --format flag entirely (ship one format, make it good)
- [ ] Or implement all three formats with complete specifications for each

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
- [ ] **Fixed**

**Problem:** The skill specifies regex with capture groups like `\[([^\]]*)\]\(([^)]+)\)` but the Grep tool returns matching lines, not capture groups. The skill's instructions don't match the actual tool API.

**Fix:**
- [ ] Rewrite as actual tool invocations that return line content
- [ ] Or better: add a `scripts/extract_links.py` that parses Markdown properly (using a real Markdown parser, not regex) and outputs a JSON list of links with file/line/target
- [ ] Regex-based Markdown link extraction is fragile — links in code blocks, comments, and escaped brackets will cause false positives/negatives

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
- [ ] **Fixed**

**Problem:** Grepping function names like `get`, `create`, `update` in docs matches everything. Even specific names like `retryWithBackoff` could match prose discussing retry patterns without actually documenting the function.

**Fix:**
- [ ] Same fix as F1: search for code-context matches (backticks, code blocks, function call syntax)
- [ ] Skip single-word function names under 8 chars for doc search (too many false positives)
- [ ] Require matches in heading or code block for it to count as "documented"
- [ ] Add a helper script that does precise matching

---

#### D2. Python regex matches everything, not just public API
- [ ] **Fixed**

**Problem:** `^def\s+[a-z]\w+` matches every function in every file — test helpers, migration scripts, build scripts, fixtures, conftest functions, CLI scripts. Massive noise.

**Fix:**
- [ ] Exclude test files (`*_test.py`, `test_*.py`, `tests/`, `conftest.py`)
- [ ] Exclude common non-API directories (`migrations/`, `scripts/`, `fixtures/`)
- [ ] Only scan files in the specified source directory, not the entire repo
- [ ] For Python specifically: only count functions in `__init__.py` or files explicitly imported in `__init__.py` as "public"

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
- [ ] **Fixed**

**Problem:** Lists TypeScript, Python, Go, Rust, Java in detection but only provides regex patterns for TypeScript, Python, and Go. Rust and Java have no patterns defined. Even the three "supported" languages have naive patterns.

**Fix:**
- [ ] Remove Rust and Java from the language detection until patterns are implemented and tested
- [ ] Or add real patterns for all 5
- [ ] Add a `coverage-patterns.md` reference file with tested regex per language
- [ ] Be honest: "Currently supports TypeScript and Python. Go support is experimental."

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
