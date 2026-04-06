# Cross-Cutting Critique: ekline-docs-skills v3.0.0

**Date:** 2026-04-06
**Overall Quality:** 7/10
**Readiness:** Good for early adoption, needs polish for production confidence

---

## Test Coverage Gap

Only 3 of 12 skills have tests (readability, accessibility, content-audit). The other 9 have **zero test coverage**:

| Skill | Has Tests | Priority to Add |
|-------|-----------|-----------------|
| readability | Yes (15 tests) | -- |
| accessibility | Yes (19 tests) | -- |
| content-audit | Yes (17 tests) | -- |
| check-links | **No** | **High** — complex anchor/path resolution logic |
| docs-freshness | **No** | **High** — git diff parsing has many edge cases |
| docs-coverage | **No** | **High** — multi-language export detection is fragile |
| changelog | **No** | Medium — conventional commit parsing needs validation |
| llms-txt | **No** | Medium — classification logic untested |
| docs-health | **No** | Low — orchestrator only, depends on other scripts |
| review-docs | N/A | N/A — external tool wrapper |
| style-guide | N/A | N/A — no script |
| terminology | N/A | N/A — no script |

**Action:** Write test suites for check-links, docs-freshness, and docs-coverage before any other feature work.

---

## Inconsistent File Limits

Each skill picks its own limit with no shared rationale:

| Skill | Limit | Why? |
|-------|-------|------|
| readability | 100 files | Unclear |
| accessibility | 200 files | Unclear |
| content-audit | 200 files | Pairwise comparison drives this |
| check-links | 200 files | Unclear |
| docs-coverage | 300 source + 200 doc | Different resource model |
| llms-txt | 150 files | Unclear |
| changelog | 200 commits | Different unit |

**Action:** Define a shared constant (e.g., `MAX_DOC_FILES = 200`) and document why it's that number. Override per-skill only when justified (content-audit's pairwise comparison, docs-coverage's dual scan).

---

## Docs Directory Detection Inconsistency

Different skills look for different fallback directories:

- **docs-health:** `docs/`, `documentation/`, `content/`, `pages/`
- **llms-txt:** `docs/`, `_docs/`, `content/`, `src/content/docs/`
- **docs-freshness:** requires `--docs-dir` or defaults to `docs/`
- **content-audit:** takes explicit argument only

**Action:** Extract a shared `find_docs_dir()` utility that all skills use, with a consistent fallback list.

---

## Two-Tier Skill Architecture (Script vs. Reference-Only)

Skills fall into two categories:

1. **Script-backed** (8 skills): Have a Python helper that does the work and outputs JSON. Deterministic, testable.
2. **Reference-only** (2 skills: style-guide, terminology): Just describe rules. The AI agent must implement checking at runtime. Non-deterministic, untestable.

**Problems with reference-only skills:**
- Different agents may implement checks differently
- No way to validate correctness
- docs-health hardcodes its own banned-phrase list instead of reading from style-rules.md
- Performance varies with agent context

**Action:** Write lightweight Python scripts for style-guide and terminology that do pattern-based checking. Even imperfect automation beats zero automation for consistency.

---

## docs-health Scoring Divergence

The docs-health orchestrator re-implements style and terminology checks inline rather than calling the reference files or delegating to a script. This creates:

1. **Drift:** Banned phrases in docs-health SKILL.md may differ from style-rules.md
2. **Inconsistency:** Running `/style-guide` then `/docs-health` can give different verdicts
3. **Sampling bias:** docs-health checks "up to 10 files" while actual skills check all files

**Action:** Make docs-health call the same scripts/references that individual skills use. Remove duplicated rule lists from the orchestrator.

---

## Python Script Quality Patterns

**Good patterns used consistently:**
- `find_doc_files()` for directory walking with extension filtering
- JSON output to stdout for agent consumption
- `argparse`-style CLI arguments
- Frontmatter and code block stripping before analysis
- `MAX_FILES` limits to prevent runaway execution

**Bad patterns found across multiple scripts:**
- Regex patterns that silently miss valid inputs (passive voice, env vars, endpoint routes)
- No input validation on file paths beyond existence checks
- Error messages that don't suggest fixes
- Hardcoded thresholds without configuration options

---

## README vs. Reality

| Claim | Reality |
|-------|---------|
| "12 skills" | Correct, 12 user-facing skills |
| "No dependencies beyond Python 3" | True for 11/12. review-docs needs ekline-cli + API token |
| "11 of 12 work out of the box" | True |
| Style/terminology "run automatically" | Only if agent is configured to trigger on file edits |
| "Zero-config" | Vale needs `write-good` package installed; .vale.ini exists but isn't used by skills |

---

## Security Considerations

- **check-links:** Uses `curl` for external URLs. The URL is shell-escaped but the implementation should be audited for injection via crafted Markdown links.
- **review-docs:** Asks users to set `EKLINE_EK_TOKEN` as env var. Could leak in shell history if set inline (`EKLINE_EK_TOKEN=... ekline-cli`).
- **All scripts:** Accept arbitrary file paths. Path traversal guards exist in check-links but not in other scripts.

---

## Recommended Priority Order

1. **Write tests** for check-links, docs-freshness, docs-coverage
2. **Fix critical bugs** (see per-skill critiques)
3. **Harmonize** file limits and docs directory detection
4. **Add enforcement scripts** for style-guide and terminology
5. **Fix docs-health** scoring to use shared references
6. **Polish** README accuracy and Vale configuration
