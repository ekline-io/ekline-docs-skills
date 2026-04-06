# EkLine Docs Skills v3.0.0 — Polish + Power Moves

**Date:** 2026-04-04
**Status:** Approved
**Approach:** Cleanup existing repo + add 4 high-impact skills
**Goal:** Drive adoption and GitHub stars by making the plugin look professional and delivering immediate value

## Context

EkLine docs-skills is a Claude Code plugin providing documentation quality tools. Currently at v2.0.0 with 8 skills focused on auditing and enforcement. The plugin is being positioned as the company's flagship product.

### Competitive landscape

- **Doc Detective** — docs-as-tests niche (executable documentation, CI validation)
- **Red Hat Docs Agent Tools** — enterprise workflow niche (JIRA integration, CQA assessment, modular docs)
- **EkLine** — universal documentation quality toolkit (platform-agnostic, anyone with docs)

### What's missing

All 8 existing skills are audit/enforcement focused. Nothing helps writers understand the overall health of their docs at a glance, and nothing measures readability quantitatively. The repo has minor hygiene issues that hurt first impressions.

## Scope

### Cleanup

1. **Remove `__pycache__` from git tracking** — 6 `.pyc` files are tracked despite `.gitignore` having `__pycache__/`. Run `git rm --cached` to untrack.
2. **Remove `.markdownlint.json`** — Only disables 3 rules (`MD013`, `MD041`, `MD060`), adds clutter. Vale already covers markdown quality via write-good styles.
3. **Bump version to 3.0.0** — Going from 8 to 12 skills is a major release.
4. **Update `plugin.json` and `marketplace.json`** — Reflect new skill count and descriptions.
5. **Update `README.md`** — Add new skills, improve descriptions for marketplace appeal.

### New skill: `readability`

Quantitative readability analysis of documentation files.

**Helper script:** `scripts/analyze_readability.py`

**Metrics computed per file:**

| Metric | Target | Description |
|--------|--------|-------------|
| Flesch-Kincaid Grade Level | 8 or below | US school grade needed to understand the text |
| Flesch Reading Ease | 60+ | 0-100 scale, higher is easier |
| Average sentence length | 25 words max | Flags sentences exceeding threshold |
| Passive voice percentage | 10% max | Percentage of sentences using passive voice |
| Complex sentence ratio | informational | Sentences with 3+ clauses (reported but not scored) |

**Composite score formula:** The per-file score is the Flesch Reading Ease score (0-100), which already incorporates sentence length and word complexity. The script also reports the other metrics alongside for context, but the letter grade is based on Flesch Reading Ease:

- A: 90-100 (excellent readability)
- B: 80-89 (good)
- C: 70-79 (acceptable)
- D: 60-69 (needs improvement)
- F: below 60 (hard to read)

**SKILL.md workflow:**

1. Run `analyze_readability.py` with docs directory or specific files
2. Present per-file scores with letter grades
3. Flag worst offenders (lowest scores, longest sentences)
4. Offer to rewrite the hardest-to-read sentences

**Arguments:** `[docs_directory] [--file FILE]`

**Dependencies:** Python stdlib only. Syllable counting via a simple algorithm (count vowel groups), no NLTK required.

**File limits:** Max 100 files per run.

### New skill: `docs-health`

Orchestrator that runs multiple checks in one pass and produces a unified health report card.

**Implementation:** SKILL.md only — no helper script. Calls existing scripts directly and combines results.

**Checks run in sequence:**

1. Style guide — pattern matching per SKILL.md rules
2. Terminology — pattern matching per SKILL.md rules
3. Check links — via `check-links/scripts/extract_links.py`
4. Docs freshness — via `docs-freshness/scripts/extract_changes.py` (skipped if not a git repo)
5. Readability — via `readability/scripts/analyze_readability.py`

**Report card format:**

```
Documentation Health Report
===========================
Overall Score: B+ (82/100)

  Links        A   (96/100)  — 2 broken out of 147
  Readability  B+  (84/100)  — avg grade level 7.2
  Style        B   (80/100)  — 12 violations across 8 files
  Terminology  A-  (90/100)  — 3 inconsistencies
  Freshness    C+  (68/100)  — 4 stale docs detected

Top 5 issues to fix first:
  1. docs/api/auth.md — stale (references removed endpoint)
  2. docs/guide/setup.md — grade level 12.1 (too complex)
  3. docs/api/users.md — 3 broken internal links
```

**Scoring weights:**

| Category | Weight | Rationale |
|----------|--------|-----------|
| Links | 25% | Broken links are the most visible quality issue |
| Readability | 25% | Directly impacts user comprehension |
| Style | 20% | Consistency matters but is less critical than correctness |
| Terminology | 15% | Important for consistency, lower individual impact |
| Freshness | 15% | Matters most around releases, less day-to-day |

**Score computation per category:**

- **Links:** `(1 - broken_count / total_links) * 100`, floor 0
- **Readability:** Average Flesch Reading Ease across files, scaled to 0-100
- **Style:** `(1 - violation_count / total_checks) * 100`, floor 0. Style and terminology don't have helper scripts — they are agent-driven checks. The docs-health SKILL.md instructs the agent to sample up to 10 files, apply the rules from `style-guide/references/style-rules.md`, count violations (banned phrases, passive voice, heading case), and compute the score. This is approximate but consistent enough for a health report.
- **Terminology:** `(1 - inconsistency_count / total_terms_checked) * 100`, floor 0. Same approach as style — agent samples files, applies rules from `terminology/references/terminology-rules.md`, counts inconsistencies.
- **Freshness:** `(fresh_count / total_docs) * 100`. Skipped if not a git repo (remaining categories reweight proportionally).

**After presenting the report:** Offers to fix issues starting from highest impact. Delegates fixes to the individual skill workflows.

**Arguments:** `[docs_directory] [--skip-freshness] [--skip-external]`

### New skill: `accessibility`

Checks documentation for accessibility issues.

**Helper script:** `scripts/check_accessibility.py`

**Checks performed:**

| Check | Severity | Description |
|-------|----------|-------------|
| Images without alt text | error | `![](image.png)` with empty or missing alt text |
| Heading hierarchy violations | error | Skipping levels (h1 to h3), multiple h1s per file |
| Non-descriptive links | warning | Link text is "click here", "here", "this link", "read more", "link" |
| Color-only references | warning | Text like "the red button", "highlighted in green", "shown in blue" |
| Missing code block language | info | Fenced code blocks without a language identifier |
| Long alt text | info | Alt text exceeding 125 characters (should be a caption instead) |
| Tables without headers | warning | Tables that lack a header row (first row not followed by separator) |

**Detection patterns (Python regex):**

- Empty alt: `!\[\s*\]\(` 
- Heading levels: extract ATX heading levels (`#{1,6}`) per file, check sequence
- Non-descriptive links: `\[(?:click here|here|this link|read more|link)\]\(` (case-insensitive)
- Color references: `\b(?:the\s+)?(?:red|green|blue|yellow|orange|purple)\s+(?:button|text|section|area|highlight|box|indicator)\b` (case-insensitive)
- Missing code language: ` ```\s*\n ` (opening fence with no language)
- Alt text length: extract alt text from `!\[([^\]]+)\]`, check length
- Table headers: detect tables via `\|.*\|` rows, check if second row is separator `\|[\s-:]+\|`

**Output:** JSON grouped by file, each finding has: `type`, `severity`, `line`, `message`, `suggestion`

**SKILL.md workflow:**

1. Run `check_accessibility.py` with docs directory or specific file
2. Present summary (X errors, Y warnings, Z info)
3. List findings by severity, grouped by file
4. Offer auto-fixes: add alt text placeholders (`[TODO: add alt text]`), fix heading levels, rewrite non-descriptive link text

**Arguments:** `[docs_directory] [--file FILE]`

**Dependencies:** Python stdlib only.

**File limits:** Max 200 files per run.

### New skill: `content-audit`

Finds structural problems: duplicates, orphans, thin pages, inconsistent structure.

**Helper script:** `scripts/audit_content.py`

**Checks performed:**

| Check | Description |
|-------|-------------|
| Near-duplicate content | Jaccard similarity on normalized sentences between file pairs. Flags pairs above 60% similarity. |
| Thin pages | Pages with fewer than 100 words of content (excluding frontmatter, code blocks, headings). Configurable via `--min-words`. |
| Orphaned pages | Pages not linked from any other doc AND not in any nav config. Checks: `_sidebar.md`, `mkdocs.yml`, `docusaurus.config.js`, `mint.json`, `_meta.json`, `_category_.json`. Excludes README/index files. |
| Missing structure | Pages without an h1, pages with no headings at all, pages over 500 words with no subsections. |
| Inconsistent frontmatter | Detects which frontmatter fields are common across the docs set and flags files missing those fields. A field is considered "expected" if 50%+ of files have it. |

**Similarity algorithm (no external dependencies):**

1. Extract content from each file (strip frontmatter, code blocks, HTML tags)
2. Split into sentences (split on `.`, `!`, `?` followed by whitespace)
3. Normalize: lowercase, strip extra whitespace
4. For each file pair, compute Jaccard similarity: `|intersection| / |union|` of sentence sets
5. Only compare files within the same directory tree (not cross-project)
6. Skip comparison if either file has fewer than 5 sentences

**Output:** JSON with categories: `duplicates` (array of pairs with similarity score), `thin_pages` (array with word count), `orphaned_pages` (array), `structure_issues` (array with issue type), `frontmatter_issues` (array with missing fields)

**SKILL.md workflow:**

1. Run `audit_content.py` with docs directory
2. Present summary: "3 near-duplicates, 7 thin pages, 2 orphans, 4 structure issues"
3. Show details per category
4. Offer actions: suggest merging duplicates, flesh out thin pages, link orphans into nav, add missing frontmatter

**Arguments:** `[docs_directory] [--min-words N] [--similarity-threshold N]`

**Dependencies:** Python stdlib only.

**File limits:** Max 200 files per run. Pairwise comparison capped at 200 files (19,900 pairs max — fast with sentence-level Jaccard).

## File structure (new/changed files)

```
ekline-docs-skills/
├── skills/
│   ├── readability/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── analyze_readability.py
│   ├── docs-health/
│   │   └── SKILL.md                        (no scripts — orchestrator only)
│   ├── accessibility/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── check_accessibility.py
│   └── content-audit/
│       ├── SKILL.md
│       └── scripts/
│           └── audit_content.py
├── .claude-plugin/
│   ├── plugin.json                         (updated: v3.0.0, 12 skills)
│   └── marketplace.json                    (updated: 12 plugins listed)
├── README.md                               (updated: new skills documented)
└── .markdownlint.json                      (deleted)
```

## Out of scope

- No external Python dependencies (everything uses stdlib)
- No CI/CD integration (future consideration)
- No platform-specific features (stays universal)
- No JIRA/Linear/GitHub Issues integration
- No docs-as-tests functionality
- Style-guide and terminology remain separate skills (consolidation is a future consideration)

## Success criteria

- All 12 skills work correctly when invoked via Claude Code
- `docs-health` produces a unified report card combining all checks
- All helper scripts produce valid JSON output
- No regressions in existing 8 skills
- README clearly documents all 12 skills with usage examples
- Repo looks clean: no tracked `__pycache__`, no unnecessary config files
