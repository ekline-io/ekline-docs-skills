# Critique: readability

**Script:** `skills/readability/scripts/analyze_readability.py`
**Tests:** `tests/test_readability.py` (15 tests)
**Overall:** Solid implementation with good test coverage. Minor heuristic inaccuracies.

---

## Critical

None.

---

## Medium

### Syllable counting accuracy is unvalidated

The heuristic at ~line 116 removes trailing 'e' except for 'le', 'ee', 'ie'. Claims +/-0.5 accuracy but this isn't tested against a known corpus.

**Examples of likely miscounts:**
- "appetite" -> "appetit" -> 3 syllables (actual: 3, OK)
- "create" -> "creat" -> 2 syllables (actual: 2, OK)
- "recipe" -> keeps 'e' -> 3 syllables (actual: 3, OK)
- "machete" -> keeps 'e' -> 3 syllables (actual: 3, OK)

Heuristic works reasonably well for English but will break on borrowed words ("fiance", "resume" as noun).

**Action:** Add a test case with ~20 known words and expected syllable counts to catch regressions.

### Passive voice regex misses complex constructions

Pattern `\b(?:is|are|...)\s+(?:\w+\s+)*?(?:\w+(?:ed|en|...)\b)` uses non-greedy matching with `\w+\s+` groups. Misses:

- "is very carefully managed" (adverb between be-verb and participle)
- "was by the team approved" (prepositional phrase in between)
- "has been being used" (complex progressive passive)

**Action:** Accept that this is a heuristic and document the known limitations in the SKILL.md. Or switch to a simpler approach: just count be-verb + past-participle adjacency (miss some, but fewer false positives).

---

## Low

### Sentence splitting treats bullet lists as sentences

Line ~123 splits on newlines AND punctuation. A bullet list like:
```
- Click save.
- Enter name.
- Press submit.
```
Produces 3 "sentences" of 2 words each, pulling the average sentence length way down and inflating readability scores.

**Action:** Strip bullet markers before splitting, or detect list context and skip those lines from sentence-level metrics.

### Hardcoded 25-word threshold for long sentences

Technical docs often need longer sentences for precision. A 25-word sentence explaining an API parameter might be perfectly clear.

**Action:** Make the threshold configurable via `--max-sentence-length`. Keep 25 as default.

### Grade level formula assumes English

Flesch-Kincaid is calibrated for English. Running it on translated or multilingual docs will produce meaningless scores.

**Action:** Add a note in SKILL.md that scores are only meaningful for English content. Consider detecting non-English text and skipping those files.
