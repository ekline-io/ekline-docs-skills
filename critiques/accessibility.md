# Critique: accessibility

**Script:** `skills/accessibility/scripts/check_accessibility.py`
**Tests:** `tests/test_accessibility.py` (19 tests)
**Overall:** Well-designed with good coverage. A few regex edge cases.

---

## Critical

None.

---

## Medium

### Empty alt text regex doesn't catch whitespace-only alt text

Line ~28: `!\[\s*\]` matches `![]` but not `![   ]` (multiple spaces inside brackets). The `\s*` quantifier IS zero-or-more whitespace, so this should work. However, the test only validates truly empty `![]` — no test for `![   ](image.png)`.

**Action:** Add a test case for whitespace-only alt text to confirm the regex handles it.

### Missing check: HTML `<img>` tags without alt attribute

The script checks Markdown image syntax but doesn't scan for `<img src="..." />` without `alt`. MDX files commonly use HTML image tags.

**Action:** Add a pattern for `<img` tags missing the `alt` attribute. This is especially important for `.mdx` files.

### Heading hierarchy check doesn't handle HTML headings in all cases

The test file `html_heading.md` tests `<h1>` tags, but the script's heading extraction may not handle mixed Markdown + HTML headings in the same file consistently.

**Action:** Verify the script handles files with both `# Heading` and `<h2>Heading</h2>` in the same file. Add a mixed-format test.

---

## Low

### Color reference detection is English-only

Pattern at line ~39 only matches English color words (red, green, blue, etc.) paired with English UI element words. Non-English docs or hex color references like "the #FF0000 button" are missed.

**Action:** Document as a known limitation. Consider adding hex color pattern detection.

### Non-descriptive link text list could be expanded

Current list: "click here", "here", "this link", "read more", "link". Missing common offenders:
- "this page"
- "this document"  
- "more info"
- "learn more"
- "see here"

**Action:** Expand the list. The SKILL.md already mentions some of these but the regex doesn't match all of them.

### Tables without headers check

The detection requires the second row to be a separator (`|[\s-:]+|`). Some Markdown renderers support tables without explicit separator rows (GFM requires them, but some tools don't).

**Action:** Low priority — GFM is the dominant Markdown flavor and requires separators.
