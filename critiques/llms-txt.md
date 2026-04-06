# Critique: llms-txt

**Script:** `skills/llms-txt/scripts/generate_llms_txt.py`
**Tests:** None
**Overall:** Useful utility for AI discoverability. Platform detection works but classification needs tuning.

---

## Critical

None.

---

## Medium

### Platform detection doesn't handle monorepos

Lines ~29-37: Checks for Docusaurus, MkDocs, etc. in order. A monorepo with both `docusaurus.config.js` (for public docs) and `mkdocs.yml` (for internal docs) will always pick Docusaurus. No way for user to specify which.

**Action:** If multiple platforms detected, list them and ask the user to choose, or accept a `--platform` flag.

### Content pattern regex missing MULTILINE flag

Line ~45: Pattern `^#{1,2}` only matches start of string, not start of line. In multiline content, this means only the first heading in a file is checked for classification.

**Action:** Add `re.MULTILINE` flag to content pattern matching.

### No tests

Classification logic (API vs. Guide vs. Tutorial vs. Reference) depends on filename and content patterns. Without tests, changes to classification rules could silently break output.

**Action:** Write tests with fixture files:
- A file with API-style headings -> classified as API
- A file with step-by-step instructions -> classified as Guide
- A file in `api/` directory -> classified as API by path
- Ambiguous files -> verify first-match-wins behavior

---

## Low

### 150-file limit is arbitrary

No documented rationale for why 150 files is the cap. Large documentation sites (Kubernetes, React) can have 500+ files.

**Action:** Increase to 200 (match other skills) or make configurable.

### No handling of llms.txt format updates

The `llms.txt` specification is evolving. If the format changes, the script would need updates.

**Action:** Pin the spec version in the output header (e.g., `# llms.txt v1.0`) and link to the spec.

### Missing base_url detection for some platforms

Some platforms (Hugo, Jekyll) have base URLs in config files (`baseURL`, `url`) that should be prepended to doc paths. The script may fall back to relative paths when absolute URLs would be better.

**Action:** Extract base URL from platform config files when available.
