# Critique: check-links

**Script:** `skills/check-links/scripts/extract_links.py`
**Tests:** None
**Overall:** Most complex script (469 lines). Solid link extraction but has anchor validation bugs and potential security concerns.

---

## Critical

### heading_to_anchor() breaks on international text

Line ~55-67: The function strips emoji and special characters with `re.sub(r"[^\w\s-]", "", text.lower())`. But `\w` in Python regex without `re.ASCII` flag matches Unicode word characters, so accented letters are kept. However, the overall normalization doesn't match GitHub's actual anchor algorithm for all cases:

- GitHub: "Qu'est-ce que c'est" -> `quest-ce-que-cest` (strips apostrophes, collapses)
- Script: May produce different results depending on Python's Unicode handling

**Impact:** False "broken anchor" errors on docs with non-ASCII headings.

**Action:** Test against GitHub's actual anchor generation for a set of international headings. Consider using a reference implementation.

### No tests for the most complex script

469 lines of link extraction, path resolution, anchor validation, and external URL checking — all untested.

**Action:** Write tests covering:
- Internal link resolution (relative, absolute, with anchors)
- Anchor generation from headings (ASCII, Unicode, special chars)
- Orphan page detection
- Route-style link resolution
- Edge cases: empty links, self-links, fragment-only links

---

## Medium

### External URL checking uses curl with potential injection risk

Line ~282-306: URLs are passed to `curl` via subprocess. While non-HTTP schemes are blocked, a crafted URL like `http://example.com$(whoami)` in a Markdown link could theoretically escape.

**Action:** Use `shlex.quote()` on the URL before passing to subprocess, or use Python's `urllib.request` instead of shelling out to curl.

### Route-style link resolution is incomplete

Line ~155-160: Tries patterns like `path.md`, `path/index.md`, `path/README.md`. Missing:
- `path/index.mdx` (Docusaurus)
- `path.mdx` (Next.js)
- `path/page.md` or `path/page.mdx`

**Action:** Add `.mdx` variants to the resolution patterns.

### Relative link normalization is fragile

Line ~215: Uses `os.path.normpath()` which handles `./` and `../` but doesn't canonicalize symlinks or case-insensitive filesystems (macOS).

**Action:** Use `os.path.realpath()` for canonicalization, then compare against the doc root to prevent path traversal.

---

## Low

### Anchor comparison case sensitivity

Line ~174: Anchor comparison is case-insensitive, but GitHub's actual anchor algorithm is case-sensitive for the generated ID. A link to `#Setup` won't match a heading that generates `#setup`.

**Action:** Make comparison case-sensitive to match GitHub behavior. Add a suggestion when a case-insensitive match exists.

### Reference-style links detection

The script handles `[text][ref]` and `[ref]: url` style links, but doesn't handle shortcut reference links `[ref]` (no second bracket pair). These are valid Markdown.

**Action:** Add detection for shortcut reference links.

### No rate limiting for external URL checks

If a doc set has 100 links to the same domain, `curl` will hit it 100 times in rapid succession. Some servers will rate-limit or block this.

**Action:** Add a per-domain delay (e.g., 1 second between requests to the same host) or batch by domain.
