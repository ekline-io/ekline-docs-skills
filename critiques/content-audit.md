# Critique: content-audit

**Script:** `skills/content-audit/scripts/audit_content.py`
**Tests:** `tests/test_content_audit.py` (17 tests)
**Overall:** Most complex script. Good test coverage but has a noisy frontmatter detection algorithm.

---

## Critical

### Frontmatter "expected fields" logic creates noise

Line ~345: computes threshold as 50% of files **that have frontmatter**. If 10 files have frontmatter (with fields like `title`, `description`) and 90 files don't, the "expected" fields come from those 10, but then all 90 files without frontmatter get flagged as missing those fields.

**Impact:** In a mixed project (some MDX with frontmatter, some plain Markdown without), this produces dozens of false positives.

**Action:** Only flag frontmatter issues within the population of files that already have frontmatter. Files with zero frontmatter should get a single "no frontmatter found" note, not per-field violations.

---

## Medium

### Duplicate detection skips short files

Line ~27: `MIN_SENTENCES_FOR_COMPARISON = 5` means files with fewer than 5 sentences aren't compared. Two nearly-identical thin pages (e.g., redirect stubs, changelog entries) will never be flagged as duplicates.

**Action:** Lower the threshold to 3, or add a separate "exact match" check for files under the threshold (byte-level comparison after stripping whitespace).

### Sentence normalization drops short sentences

Line ~108-111: sentences under 20 characters are dropped. A file of many short sentences ("Click save.", "Enter name.", "Press OK.") returns an empty sentence set and is skipped for comparison.

**Action:** Lower the minimum to 10 characters, or remove the filter entirely (Jaccard handles noise well).

### Orphan detection nav config patterns are incomplete

Line ~167-173: checks `_sidebar.md`, `mkdocs.yml`, `docusaurus.config.js`, `mint.json`, `_meta.json`, `_category_.json`. Missing:
- `docusaurus.config.ts` (TypeScript variant)
- `book.toml` (mdBook / Rust)
- `antora.yml` (Antora)
- `vuepress` config files
- YAML array syntax in mkdocs

**Action:** Add the TypeScript variant at minimum (Docusaurus v3 defaults to `.ts`). Others are lower priority.

---

## Low

### Thin page threshold off-by-one

Script uses `< 100` words while SKILL.md says "under 100 words". These mean the same thing, but the SKILL.md could be read as "fewer than 100" vs. "100 or fewer". Pedantic but worth clarifying.

**Action:** Pick one and make both consistent: "fewer than 100 words (< 100)".

### Jaccard similarity doesn't weight sentence length

All sentences contribute equally to the similarity score. A shared one-word sentence ("Overview") contributes as much as a shared 50-word paragraph. This can inflate similarity scores for files that share generic headings.

**Action:** Low priority. Could weight by sentence length or use character-level Jaccard, but the current approach is fast and good enough for flagging candidates.

### No deduplication across directories

Line ~185: "Only compare files within the same directory tree." This misses cross-directory duplicates (e.g., `docs/v1/setup.md` copied to `docs/v2/setup.md`).

**Action:** Add an optional `--cross-directory` flag for broader comparison. Keep same-directory as default for performance.
