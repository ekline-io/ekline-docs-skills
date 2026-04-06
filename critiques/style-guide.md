# Critique: style-guide

**Script:** None (reference-only skill)
**Tests:** None
**Overall:** Excellent reference document, but relying entirely on agent-side implementation is a consistency risk.

---

## Critical

### No enforcement script means non-deterministic behavior

The skill describes WHAT to check (banned phrases, heading case, active voice) but provides no HOW. Every agent invocation re-implements the logic, which means:

1. Different agents may interpret rules differently
2. Results vary between runs even on the same file
3. docs-health hardcodes its own subset of rules instead of using this skill's reference

**Impact:** Two runs of `/style-guide` on the same file could flag different issues.

**Action:** Write `skills/style-guide/scripts/check_style.py` that:
- Reads rules from `references/style-rules.md`
- Checks for banned phrases (regex matching)
- Flags heading case violations
- Detects passive voice (reuse readability's pattern)
- Outputs JSON like other scripts
- Acts as the ground truth that docs-health can also call

---

## Medium

### style-rules.md has rules that can't be automated

Some rules require semantic understanding:
- "Use active voice" — needs NLP beyond simple pattern matching
- "Every code example must be complete" — requires understanding code semantics
- "Use second person (you)" — easy to detect "we" but hard to verify all instructions use "you"

**Action:** Separate rules into two tiers:
1. **Automatable:** Banned phrases, heading case, code block formatting — implement in script
2. **Agent-assisted:** Active voice, completeness, tone — leave for agent with clear guidelines

### Vale configuration is disconnected from skill

`.vale.ini` exists with `write-good` styles, but the style-guide skill doesn't reference Vale at all. The `write-good.E-Prime` and `write-good.TooWordy` rules are disabled, which contradicts some style-rules.md guidance.

**Action:** Either integrate Vale into the style-guide workflow or remove `.vale.ini` to avoid confusion.

### Auto-fix suggestions are vague

The SKILL.md mentions auto-fixing "common violations" but doesn't specify which fixes are safe and which need human review.

**Action:** Categorize fixes as:
- **Safe auto-fix:** Banned phrase replacement, heading case
- **Needs review:** Passive-to-active voice rewrites, sentence restructuring

---

## Low

### "Runs automatically" claim needs qualification

README says style-guide "runs automatically when you create or edit doc files." This only works if the user's Claude Code is configured to trigger skills on file changes. It's not a built-in behavior.

**Action:** Clarify: "Runs automatically when configured as a hook. See [Configuration] for setup."

### Missing rule: documentation granularity

style-rules.md covers how to write content but not when to split into multiple files vs. keep together. "When should I create a new page?" is a common question.

**Action:** Low priority. Consider adding guidelines for page length and splitting criteria.
