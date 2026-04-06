# Critique: terminology

**Script:** None (reference-only skill)
**Tests:** None
**Overall:** Comprehensive terminology reference. Same enforcement gap as style-guide.

---

## Critical

### No enforcement script (same as style-guide)

All checking is delegated to the agent at runtime. Results are non-deterministic and untestable.

**Action:** Write `skills/terminology/scripts/check_terms.py` that:
- Reads rules from `references/terminology-rules.md`
- Scans docs for prohibited terms (simple regex)
- Flags inconsistent usage (e.g., "log in" vs "login" in the same file)
- Checks product name casing
- Outputs JSON

---

## Medium

### Context-dependent hyphenation rules can't be regex-checked

Lines ~85-92 in terminology-rules.md specify that some terms change based on grammatical role:
- "set up" (verb) vs. "setup" (noun/adjective)
- "log in" (verb) vs. "login" (noun/adjective)
- "back end" (noun) vs. "back-end" (adjective) vs. "backend" (informal)

A regex can detect "setup" vs "set up" but can't determine if the context requires the verb or noun form.

**Action:** For the script, flag all instances of context-dependent terms and let the agent/user decide which form is correct. The script identifies candidates; the agent resolves ambiguity.

### Prohibited terms need context awareness

Line ~154-165: Terms like "dummy" are prohibited, but "dummy variable" is standard statistical terminology. "Master" is prohibited, but "master's degree" is fine.

**Action:** Add context exceptions to the rules. E.g., "dummy — prohibited EXCEPT in 'dummy variable' (statistics)."

### terminology-rules.md may not cover project-specific terms

The reference covers general programming terms but not project-specific terminology. A project using "workspace" and "project" interchangeably needs custom rules.

**Action:** Add a section to terminology-rules.md explaining how to add project-specific terms. Or provide a template.

---

## Low

### UI element terms require product knowledge

Lines ~118-131: Terms like "button", "link", "toggle" are defined, but whether something is a "button" vs. a "link" depends on the actual UI implementation. A terminology checker can't validate this.

**Action:** Document this limitation. These rules are for consistent naming, not for verifying that the term matches the UI component.

### Number formatting rules are locale-dependent

Lines ~170+: Rules about number formatting ("use commas for thousands") assume English/US conventions. International docs may use periods for thousands separators.

**Action:** Note the locale assumption. Consider adding locale-aware formatting rules.

### "Runs automatically" has the same caveat as style-guide

See style-guide critique — requires hook configuration.

**Action:** Same fix: clarify in README.
