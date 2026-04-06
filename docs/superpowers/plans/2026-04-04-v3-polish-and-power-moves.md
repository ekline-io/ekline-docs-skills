# EkLine Docs Skills v3.0.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clean up the repo and add 4 new skills (readability, accessibility, content-audit, docs-health) to bring the plugin from 8 to 12 skills at v3.0.0.

**Architecture:** Each new skill follows the existing pattern: a `SKILL.md` defining the agent workflow plus a Python helper script (stdlib only) that outputs JSON. The `docs-health` skill is an orchestrator (SKILL.md only) that calls other skills' scripts. All scripts share common patterns: `find_doc_files()` for directory walking, argparse-style CLI args, JSON stdout output.

**Tech Stack:** Python 3 (stdlib only), Markdown (SKILL.md), JSON (plugin metadata)

---

## File Structure

```
skills/
  readability/
    SKILL.md                          — Agent workflow for readability analysis
    scripts/
      analyze_readability.py          — Computes Flesch-Kincaid, grade level, passive voice %
  accessibility/
    SKILL.md                          — Agent workflow for accessibility checks
    scripts/
      check_accessibility.py          — Checks alt text, heading hierarchy, link text, etc.
  content-audit/
    SKILL.md                          — Agent workflow for content audit
    scripts/
      audit_content.py                — Finds duplicates, thin pages, orphans, structure issues
  docs-health/
    SKILL.md                          — Orchestrator: runs all checks, produces health report card
.claude-plugin/
  plugin.json                         — Updated to v3.0.0, 12 skills
  marketplace.json                    — Updated to list 12 plugins
README.md                             — Updated with new skills
.markdownlint.json                    — Deleted
```

---

### Task 1: Repository cleanup

**Files:**
- Delete: `.markdownlint.json`
- Remove from tracking: `skills/*/scripts/__pycache__/`

- [ ] **Step 1: Remove `__pycache__` files from git tracking**

```bash
git rm --cached -r skills/changelog/scripts/__pycache__/ skills/check-links/scripts/__pycache__/ skills/docs-coverage/scripts/__pycache__/ skills/docs-freshness/scripts/__pycache__/ skills/llms-txt/scripts/__pycache__/ skills/review-docs/scripts/__pycache__/
```

- [ ] **Step 2: Delete `.markdownlint.json`**

```bash
git rm .markdownlint.json
```

- [ ] **Step 3: Verify cleanup**

```bash
git status
```

Expected: deleted `.markdownlint.json`, 6 `__pycache__` removals staged.

- [ ] **Step 4: Commit cleanup**

```bash
git add .gitignore
git commit -m "chore: Remove tracked __pycache__ files and .markdownlint.json"
```

---

### Task 2: Create `readability` helper script

**Files:**
- Create: `skills/readability/scripts/analyze_readability.py`

- [ ] **Step 1: Create the script**

```python
#!/usr/bin/env python3
"""Analyze documentation readability with quantitative metrics.

Computes Flesch-Kincaid Grade Level, Flesch Reading Ease, sentence
complexity, and passive voice percentage for each documentation file.
Outputs a JSON readability report.

Usage:
    python analyze_readability.py [docs_directory] [--file FILE] [--max-files N]

Examples:
    python analyze_readability.py ./docs
    python analyze_readability.py --file docs/guide.md
    python analyze_readability.py ./docs --max-files 50
"""

import json
import os
import re
import sys

# 100 doc files is enough for most projects while keeping analysis fast.
MAX_FILES = 100
MAX_FILES_UPPER = 10_000

# Frontmatter fences (YAML between --- lines at the start of a file)
FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
# Fenced code blocks: ```lang ... ``` or ~~~ ... ~~~
CODE_BLOCK_RE = re.compile(r"(?:```|~~~).*?(?:```|~~~)", re.DOTALL)
# Inline code: `code`
INLINE_CODE_RE = re.compile(r"`[^`]+`")
# HTML tags
HTML_TAG_RE = re.compile(r"<[^>]+>")
# Markdown headings (ATX style)
HEADING_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)
# Markdown image syntax: ![alt](url)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
# Markdown link syntax: [text](url) — replace with just text
LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]+\)")
# Markdown table rows: | cell | cell |
TABLE_RE = re.compile(r"^\|.*\|$", re.MULTILINE)
# Markdown table separator: |---|---|
TABLE_SEP_RE = re.compile(r"^\|[\s:|-]+\|$", re.MULTILINE)
# Bullet/number list markers at start of line
LIST_MARKER_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+", re.MULTILINE)
# Sentence-ending punctuation followed by whitespace or end of string
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
# Vowel groups for syllable counting — each group is roughly one syllable
VOWEL_GROUP_RE = re.compile(r"[aeiouy]+", re.IGNORECASE)
# Common passive voice pattern: form of "to be" + past participle (-ed, -en, -t endings)
# This is a heuristic — not 100% accurate but good enough for scoring.
PASSIVE_RE = re.compile(
    r"\b(?:is|are|was|were|be|been|being)\s+(?:\w+\s+)*?"
    r"(?:\w+(?:ed|en|wn|ht|lt|pt|nt|rn)\b)",
    re.IGNORECASE,
)
# Clause separators for complex sentence detection
CLAUSE_SEP_RE = re.compile(
    r"\b(?:and|but|or|because|although|while|when|if|since|unless"
    r"|however|therefore|moreover|furthermore|nevertheless)\b"
    r"|[;,]",
    re.IGNORECASE,
)


def find_doc_files(root, max_files):
    """Walk directory tree and collect documentation files."""
    doc_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in {
                "node_modules", ".git", "vendor", "dist", "build",
                ".next", "__pycache__", ".claude",
            }
        ]
        for f in sorted(filenames):
            if f.endswith((".md", ".mdx")):
                doc_files.append(os.path.join(dirpath, f))
                if len(doc_files) >= max_files:
                    return doc_files, True
    return doc_files, False


def strip_non_prose(text):
    """Remove frontmatter, code blocks, HTML, images, tables, and Markdown
    formatting to isolate readable prose for analysis."""
    text = FRONTMATTER_RE.sub("", text)
    text = CODE_BLOCK_RE.sub("", text)
    text = INLINE_CODE_RE.sub("", text)
    text = HTML_TAG_RE.sub("", text)
    text = IMAGE_RE.sub("", text)
    text = LINK_RE.sub(r"\1", text)
    text = TABLE_SEP_RE.sub("", text)
    text = TABLE_RE.sub("", text)
    text = HEADING_RE.sub("", text)
    text = LIST_MARKER_RE.sub("", text)
    # Collapse whitespace
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def count_syllables(word):
    """Count syllables in a word using vowel-group heuristic.

    Handles silent-e and common suffixes. Not perfect for all English words
    but accurate enough for readability scoring (±0.5 syllables on average).
    """
    word = word.lower().strip()
    if len(word) <= 2:
        return 1
    # Remove trailing silent-e (e.g., "make" = 1 syllable, not 2)
    if word.endswith("e") and not word.endswith(("le", "ee", "ie")):
        word = word[:-1]
    groups = VOWEL_GROUP_RE.findall(word)
    count = len(groups)
    return max(count, 1)


def split_sentences(text):
    """Split text into sentences. Returns list of non-empty sentences."""
    sentences = SENTENCE_SPLIT_RE.split(text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]


def count_words(text):
    """Count words in text. Returns list of words."""
    return [w for w in re.findall(r"[a-zA-Z']+", text) if len(w) > 0]


def analyze_file(filepath):
    """Analyze a single documentation file and return metrics."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()

    prose = strip_non_prose(raw)
    if not prose:
        return None

    sentences = split_sentences(prose)
    if len(sentences) < 2:
        return None

    words = count_words(prose)
    if len(words) < 30:
        return None

    total_words = len(words)
    total_sentences = len(sentences)
    total_syllables = sum(count_syllables(w) for w in words)

    # Flesch Reading Ease: 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
    avg_sentence_len = total_words / total_sentences
    avg_syllables_per_word = total_syllables / total_words
    flesch_ease = (
        206.835
        - 1.015 * avg_sentence_len
        - 84.6 * avg_syllables_per_word
    )
    # Clamp to 0-100 range
    flesch_ease = max(0.0, min(100.0, flesch_ease))

    # Flesch-Kincaid Grade Level: 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
    fk_grade = (
        0.39 * avg_sentence_len
        + 11.8 * avg_syllables_per_word
        - 15.59
    )
    fk_grade = max(0.0, fk_grade)

    # Passive voice detection
    passive_count = sum(1 for s in sentences if PASSIVE_RE.search(s))
    passive_pct = (passive_count / total_sentences) * 100

    # Complex sentences: 3+ clause separators
    complex_count = sum(
        1 for s in sentences if len(CLAUSE_SEP_RE.findall(s)) >= 3
    )
    complex_pct = (complex_count / total_sentences) * 100

    # Long sentences (over 25 words)
    long_sentences = []
    for i, s in enumerate(sentences):
        s_words = count_words(s)
        if len(s_words) > 25:
            long_sentences.append({
                "sentence": s[:120] + ("..." if len(s) > 120 else ""),
                "word_count": len(s_words),
            })

    # Letter grade based on Flesch Reading Ease
    if flesch_ease >= 90:
        grade = "A"
    elif flesch_ease >= 80:
        grade = "B"
    elif flesch_ease >= 70:
        grade = "C"
    elif flesch_ease >= 60:
        grade = "D"
    else:
        grade = "F"

    return {
        "file": filepath,
        "metrics": {
            "flesch_reading_ease": round(flesch_ease, 1),
            "flesch_kincaid_grade": round(fk_grade, 1),
            "avg_sentence_length": round(avg_sentence_len, 1),
            "avg_syllables_per_word": round(avg_syllables_per_word, 2),
            "passive_voice_pct": round(passive_pct, 1),
            "complex_sentence_pct": round(complex_pct, 1),
            "total_words": total_words,
            "total_sentences": total_sentences,
        },
        "grade": grade,
        "long_sentences": long_sentences[:5],
    }


def main():
    args = sys.argv[1:]
    docs_dir = "."
    single_file = None
    max_files = MAX_FILES

    i = 0
    while i < len(args):
        if args[i] == "--file" and i + 1 < len(args):
            single_file = args[i + 1]
            i += 2
        elif args[i] == "--max-files" and i + 1 < len(args):
            max_files = min(int(args[i + 1]), MAX_FILES_UPPER)
            i += 2
        elif not args[i].startswith("-"):
            docs_dir = args[i]
            i += 1
        else:
            i += 1

    if single_file:
        if not os.path.isfile(single_file):
            print(json.dumps({"error": "file_not_found", "path": single_file}))
            return
        files = [single_file]
        truncated = False
    else:
        if not os.path.isdir(docs_dir):
            print(json.dumps({"error": "not_a_directory", "path": docs_dir}))
            return
        files, truncated = find_doc_files(docs_dir, max_files)

    if not files:
        print(json.dumps({"error": "no_docs_found", "path": docs_dir}))
        return

    results = []
    for f in files:
        analysis = analyze_file(f)
        if analysis:
            results.append(analysis)

    if not results:
        print(json.dumps({
            "error": "no_analyzable_content",
            "files_scanned": len(files),
        }))
        return

    # Compute overall metrics
    total_ease = sum(r["metrics"]["flesch_reading_ease"] for r in results)
    avg_ease = total_ease / len(results)
    avg_grade_level = sum(
        r["metrics"]["flesch_kincaid_grade"] for r in results
    ) / len(results)

    if avg_ease >= 90:
        overall_grade = "A"
    elif avg_ease >= 80:
        overall_grade = "B"
    elif avg_ease >= 70:
        overall_grade = "C"
    elif avg_ease >= 60:
        overall_grade = "D"
    else:
        overall_grade = "F"

    # Sort by score ascending (worst first) for the report
    results.sort(key=lambda r: r["metrics"]["flesch_reading_ease"])

    report = {
        "summary": {
            "files_analyzed": len(results),
            "files_skipped": len(files) - len(results),
            "files_truncated": truncated,
            "overall_grade": overall_grade,
            "avg_flesch_reading_ease": round(avg_ease, 1),
            "avg_flesch_kincaid_grade": round(avg_grade_level, 1),
        },
        "files": results,
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Make executable**

```bash
chmod +x skills/readability/scripts/analyze_readability.py
```

- [ ] **Step 3: Smoke test against this repo's docs**

```bash
python skills/readability/scripts/analyze_readability.py ./skills --max-files 20
```

Expected: JSON output with `summary.files_analyzed` > 0, each file has `grade` and `metrics`.

- [ ] **Step 4: Verify error handling**

```bash
python skills/readability/scripts/analyze_readability.py /nonexistent
```

Expected: `{"error": "not_a_directory", "path": "/nonexistent"}`

---

### Task 3: Create `readability` SKILL.md

**Files:**
- Create: `skills/readability/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

```markdown
---
name: readability
description: Analyze documentation readability with quantitative metrics. Computes Flesch-Kincaid Grade Level, Reading Ease score, passive voice percentage, and sentence complexity. Grades each file A-F and flags hard-to-read sentences. Use to measure and improve how accessible your docs are to readers.
allowed-tools: Read, Edit, Glob, Bash
metadata:
  author: EkLine
  version: "3.0.0"
  argument-hint: "[docs_directory] [--file FILE]"
---

# Analyze documentation readability

Run the helper script to compute readability metrics, then present results and offer to improve hard-to-read content.

## Inputs

- `$ARGUMENTS` — optional docs directory (defaults to current directory) or `--file FILE` for a single file

## Steps

### 1. Run the helper script

` ` `bash
python scripts/analyze_readability.py $ARGUMENTS
` ` `

Capture the JSON output.

The script handles:

- File discovery (walks directory, skips node_modules/.git/vendor/dist/build)
- Content extraction (strips frontmatter, code blocks, HTML, tables, images)
- Flesch Reading Ease (0-100, higher is easier to read)
- Flesch-Kincaid Grade Level (US school grade needed to understand)
- Passive voice percentage
- Complex sentence ratio (sentences with 3+ clauses)
- Long sentence detection (over 25 words)
- Letter grades: A (90-100), B (80-89), C (70-79), D (60-69), F (below 60)

Max 100 files per run. Files with fewer than 30 words of prose are skipped.

### 2. Handle errors

If the JSON contains an `error` field:

- `not_a_directory` — tell user the specified path is not a valid directory
- `file_not_found` — tell user the specified file does not exist
- `no_docs_found` — tell user no .md/.mdx files were found, suggest a different path
- `no_analyzable_content` — tell user files were found but none had enough prose to analyze

Stop here on error.

### 3. Present the readability report

Show the overall summary:

- Files analyzed and overall grade with average Flesch Reading Ease
- Average Flesch-Kincaid grade level (target: 8th grade or below)

Then show per-file results, worst scores first:

For each file show:
- File path and letter grade
- Flesch Reading Ease score and Flesch-Kincaid grade level
- Passive voice percentage (flag if over 10%)
- If there are long sentences, show up to 3 with word counts

Group the presentation:

**Needs improvement (D and F grades):**
- Show full metrics and long sentences

**Acceptable (C grade):**
- Show score and grade, flag any long sentences

**Good (A and B grades):**
- Show as a compact list with scores

### 4. Offer to improve readability

For files graded D or F, offer to:

1. **Rewrite long sentences** — read the file, find sentences over 25 words, and split or simplify them
2. **Reduce passive voice** — find passive constructions and rewrite in active voice
3. **Simplify vocabulary** — replace complex words with simpler alternatives where meaning is preserved
4. **Skip** — leave for manual review

When rewriting:

- Read the file with the Read tool
- Only change the specific sentences flagged
- Preserve technical accuracy — do not change code terms, API names, or technical concepts
- Keep the same meaning, just make it clearer
- Use the Edit tool to apply changes

After applying changes, re-run the script on modified files and show the updated scores.

### 5. Summary

Show what improved:

- Number of files rewritten
- Score changes (before → after)
- Any files still below grade C that need manual attention
```

Note: Replace ` ` ` with actual triple backticks (escaped here to avoid breaking the code block).

- [ ] **Step 2: Commit readability skill**

```bash
git add skills/readability/
git commit -m "feat: Add readability skill with Flesch-Kincaid scoring"
```

---

### Task 4: Create `accessibility` helper script

**Files:**
- Create: `skills/accessibility/scripts/check_accessibility.py`

- [ ] **Step 1: Create the script**

```python
#!/usr/bin/env python3
"""Check documentation files for accessibility issues.

Scans Markdown files for missing alt text, heading hierarchy violations,
non-descriptive link text, color-only references, missing code block
languages, overly long alt text, and tables without headers.
Outputs a JSON accessibility report.

Usage:
    python check_accessibility.py [docs_directory] [--file FILE] [--max-files N]

Examples:
    python check_accessibility.py ./docs
    python check_accessibility.py --file docs/guide.md
"""

import json
import os
import re
import sys

MAX_FILES = 200
MAX_FILES_UPPER = 10_000
# Alt text longer than 125 chars should be a figure caption instead (WCAG best practice)
MAX_ALT_LENGTH = 125

# Empty alt text: ![](url) or ![ ](url)
EMPTY_ALT_RE = re.compile(r"!\[\s*\]\(")
# Image with alt text: ![alt text](url) — captures the alt text
IMAGE_ALT_RE = re.compile(r"!\[([^\]]+)\]\(")
# ATX headings: # through ######
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
# Non-descriptive link text patterns (case-insensitive)
BAD_LINK_TEXT_RE = re.compile(
    r"\[(?:click\s+here|here|this\s+link|read\s+more|link|this|more|more\s+info)\]\(",
    re.IGNORECASE,
)
# Color-only references: "the red button", "shown in green", "highlighted in blue"
COLOR_REF_RE = re.compile(
    r"\b(?:the\s+)?(?:red|green|blue|yellow|orange|purple|pink|gray|grey|brown|black|white)"
    r"\s+(?:button|text|section|area|highlight(?:ed)?|box|indicator|badge|banner|icon|dot|circle|label)\b",
    re.IGNORECASE,
)
# Fenced code block opening WITHOUT a language specifier
# Matches ``` or ~~~ at start of line with optional whitespace but no language
BARE_FENCE_RE = re.compile(r"^(?:```|~~~)\s*$", re.MULTILINE)
# Fenced code block opening WITH a language specifier (to count total)
LANG_FENCE_RE = re.compile(r"^(?:```|~~~)\w+", re.MULTILINE)
# Table row: | cell | cell |
TABLE_ROW_RE = re.compile(r"^\|.+\|$", re.MULTILINE)
# Table separator row: |---|---|  or | :---: | --- |
TABLE_SEP_RE = re.compile(r"^\|[\s:|-]+\|$")


def find_doc_files(root, max_files):
    """Walk directory tree and collect documentation files."""
    doc_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in {
                "node_modules", ".git", "vendor", "dist", "build",
                ".next", "__pycache__", ".claude",
            }
        ]
        for f in sorted(filenames):
            if f.endswith((".md", ".mdx")):
                doc_files.append(os.path.join(dirpath, f))
                if len(doc_files) >= max_files:
                    return doc_files, True
    return doc_files, False


def check_file(filepath):
    """Run all accessibility checks on a single file. Returns list of findings."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    lines = content.split("\n")
    findings = []

    # --- Check 1: Images without alt text ---
    for i, line in enumerate(lines, 1):
        for match in EMPTY_ALT_RE.finditer(line):
            findings.append({
                "type": "missing_alt_text",
                "severity": "error",
                "line": i,
                "message": "Image has no alt text",
                "context": line.strip()[:120],
                "suggestion": "Add descriptive alt text: ![description of image](...)",
            })

    # --- Check 2: Alt text too long ---
    for i, line in enumerate(lines, 1):
        for match in IMAGE_ALT_RE.finditer(line):
            alt = match.group(1)
            if len(alt) > MAX_ALT_LENGTH:
                findings.append({
                    "type": "long_alt_text",
                    "severity": "info",
                    "line": i,
                    "message": f"Alt text is {len(alt)} chars (max recommended: {MAX_ALT_LENGTH})",
                    "context": alt[:80] + "...",
                    "suggestion": "Move long descriptions to a figure caption below the image",
                })

    # --- Check 3: Heading hierarchy ---
    heading_levels = []
    for match in HEADING_RE.finditer(content):
        level = len(match.group(1))
        line_num = content[:match.start()].count("\n") + 1
        heading_levels.append((level, line_num, match.group(2).strip()))

    # Check for multiple h1s
    h1_count = sum(1 for level, _, _ in heading_levels if level == 1)
    if h1_count > 1:
        h1_lines = [
            (ln, text) for level, ln, text in heading_levels if level == 1
        ]
        for ln, text in h1_lines[1:]:
            findings.append({
                "type": "multiple_h1",
                "severity": "error",
                "line": ln,
                "message": f"Multiple h1 headings found (this is the {h1_count}th). Documents should have one h1.",
                "context": f"# {text}",
                "suggestion": "Demote to h2 or remove duplicate h1",
            })

    # Check for skipped heading levels (h1 -> h3, etc.)
    for idx in range(1, len(heading_levels)):
        prev_level = heading_levels[idx - 1][0]
        curr_level, curr_line, curr_text = heading_levels[idx]
        if curr_level > prev_level + 1:
            findings.append({
                "type": "skipped_heading_level",
                "severity": "error",
                "line": curr_line,
                "message": f"Heading level skipped: h{prev_level} to h{curr_level}",
                "context": f"{'#' * curr_level} {curr_text}",
                "suggestion": f"Use h{prev_level + 1} instead of h{curr_level}",
            })

    # --- Check 4: Non-descriptive link text ---
    for i, line in enumerate(lines, 1):
        for match in BAD_LINK_TEXT_RE.finditer(line):
            findings.append({
                "type": "non_descriptive_link",
                "severity": "warning",
                "line": i,
                "message": "Link text is not descriptive",
                "context": line.strip()[:120],
                "suggestion": "Use descriptive text that makes sense without surrounding context",
            })

    # --- Check 5: Color-only references ---
    for i, line in enumerate(lines, 1):
        for match in COLOR_REF_RE.finditer(line):
            findings.append({
                "type": "color_only_reference",
                "severity": "warning",
                "line": i,
                "message": f"Color-only reference: \"{match.group()}\"",
                "context": line.strip()[:120],
                "suggestion": "Add a non-color identifier (e.g., shape, label, position) for screen reader users",
            })

    # --- Check 6: Code blocks without language ---
    for i, line in enumerate(lines, 1):
        if BARE_FENCE_RE.match(line):
            findings.append({
                "type": "missing_code_language",
                "severity": "info",
                "line": i,
                "message": "Fenced code block has no language specified",
                "context": line.strip(),
                "suggestion": "Add a language identifier (e.g., ```python, ```bash, ```json)",
            })

    # --- Check 7: Tables without headers ---
    table_blocks = []
    in_table = False
    table_start = 0
    table_rows = []
    for i, line in enumerate(lines, 1):
        is_table_row = bool(TABLE_ROW_RE.match(line))
        if is_table_row and not in_table:
            in_table = True
            table_start = i
            table_rows = [line]
        elif is_table_row and in_table:
            table_rows.append(line)
        elif not is_table_row and in_table:
            in_table = False
            if len(table_rows) >= 2:
                table_blocks.append((table_start, table_rows))
            table_rows = []

    if in_table and len(table_rows) >= 2:
        table_blocks.append((table_start, table_rows))

    for start_line, rows in table_blocks:
        if len(rows) >= 2 and not TABLE_SEP_RE.match(rows[1]):
            findings.append({
                "type": "table_without_headers",
                "severity": "warning",
                "line": start_line,
                "message": "Table appears to have no header row (missing separator after first row)",
                "context": rows[0].strip()[:120],
                "suggestion": "Add a separator row after the header: | --- | --- |",
            })

    return findings


def main():
    args = sys.argv[1:]
    docs_dir = "."
    single_file = None
    max_files = MAX_FILES

    i = 0
    while i < len(args):
        if args[i] == "--file" and i + 1 < len(args):
            single_file = args[i + 1]
            i += 2
        elif args[i] == "--max-files" and i + 1 < len(args):
            max_files = min(int(args[i + 1]), MAX_FILES_UPPER)
            i += 2
        elif not args[i].startswith("-"):
            docs_dir = args[i]
            i += 1
        else:
            i += 1

    if single_file:
        if not os.path.isfile(single_file):
            print(json.dumps({"error": "file_not_found", "path": single_file}))
            return
        files = [single_file]
        truncated = False
    else:
        if not os.path.isdir(docs_dir):
            print(json.dumps({"error": "not_a_directory", "path": docs_dir}))
            return
        files, truncated = find_doc_files(docs_dir, max_files)

    if not files:
        print(json.dumps({"error": "no_docs_found", "path": docs_dir}))
        return

    all_findings = []
    files_with_issues = 0
    severity_counts = {"error": 0, "warning": 0, "info": 0}

    for filepath in files:
        findings = check_file(filepath)
        if findings:
            files_with_issues += 1
            for finding in findings:
                severity_counts[finding["severity"]] += 1
            all_findings.append({
                "file": filepath,
                "findings": findings,
            })

    report = {
        "summary": {
            "files_scanned": len(files),
            "files_with_issues": files_with_issues,
            "files_truncated": truncated,
            "total_issues": sum(severity_counts.values()),
            "errors": severity_counts["error"],
            "warnings": severity_counts["warning"],
            "info": severity_counts["info"],
        },
        "files": all_findings,
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Make executable**

```bash
chmod +x skills/accessibility/scripts/check_accessibility.py
```

- [ ] **Step 3: Smoke test against this repo's docs**

```bash
python skills/accessibility/scripts/check_accessibility.py ./skills --max-files 20
```

Expected: JSON output with `summary.files_scanned` > 0.

- [ ] **Step 4: Verify error handling**

```bash
python skills/accessibility/scripts/check_accessibility.py /nonexistent
```

Expected: `{"error": "not_a_directory", "path": "/nonexistent"}`

---

### Task 5: Create `accessibility` SKILL.md

**Files:**
- Create: `skills/accessibility/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

```markdown
---
name: accessibility
description: Check documentation for accessibility issues including missing alt text, heading hierarchy violations, non-descriptive links, color-only references, missing code block languages, and tables without headers. Runs a helper script that scans doc files and reports findings with fix suggestions. Use before publishing or as a periodic quality check.
allowed-tools: Read, Edit, Glob, Bash
metadata:
  author: EkLine
  version: "3.0.0"
  argument-hint: "[docs_directory] [--file FILE]"
---

# Check documentation accessibility

Run the helper script to find accessibility issues, then present results and offer fixes.

## Inputs

- `$ARGUMENTS` — optional docs directory (defaults to current directory) or `--file FILE` for a single file

## Steps

### 1. Run the helper script

` ` `bash
python scripts/check_accessibility.py $ARGUMENTS
` ` `

Capture the JSON output.

The script checks for:

- Images without alt text (error)
- Heading hierarchy violations — skipped levels, multiple h1s (error)
- Non-descriptive link text — "click here", "here", "read more" (warning)
- Color-only references — "the red button", "highlighted in green" (warning)
- Tables without header rows (warning)
- Missing code block language identifiers (info)
- Alt text exceeding 125 characters (info)

Max 200 files per run.

### 2. Handle errors

If the JSON contains an `error` field:

- `not_a_directory` — tell user the specified path is not a valid directory
- `file_not_found` — tell user the specified file does not exist
- `no_docs_found` — tell user no .md/.mdx files were found, suggest a different path

Stop here on error.

### 3. Present the accessibility report

Show a summary:

- Files scanned, files with issues
- Breakdown: X errors, Y warnings, Z info items
- If `files_truncated` is true, note that the file limit was reached

Then list findings grouped by severity:

**Errors (must fix):**

For each file with errors, show:
- File path
- Each finding: type, line number, message, and suggestion
- Show the context line for reference

**Warnings (should fix):**

Same format as errors.

**Info (best practices):**

Show as a compact list — file path, line number, and message.

### 4. Offer fixes

For each file with errors or warnings, offer to fix:

1. **Missing alt text** — read the file, find the image, look at the image filename and surrounding context to suggest descriptive alt text. If unable to determine, insert `[TODO: describe this image]` as a placeholder.
2. **Heading hierarchy** — adjust heading levels to maintain proper nesting. Prefer demoting the wrong heading rather than promoting surrounding headings.
3. **Non-descriptive links** — read the link target and surrounding paragraph to suggest better link text that describes the destination.
4. **Missing code language** — look at the code block content to detect the language and add it.
5. **Skip all** — leave for manual review

When applying fixes:

- Read the file with the Read tool
- Use the Edit tool to make targeted changes
- Only change the specific issue — do not modify surrounding content
- For alt text, prefer short descriptions (under 125 chars) that convey the image's purpose

After applying fixes, re-run the script on modified files and show the updated counts.

### 5. Summary

Report what was fixed:

- Number of issues fixed by type
- Number of issues remaining
- Any files that still have errors requiring manual attention
```

Note: Replace ` ` ` with actual triple backticks.

- [ ] **Step 2: Commit accessibility skill**

```bash
git add skills/accessibility/
git commit -m "feat: Add accessibility skill with alt text, heading, and link checks"
```

---

### Task 6: Create `content-audit` helper script

**Files:**
- Create: `skills/content-audit/scripts/audit_content.py`

- [ ] **Step 1: Create the script**

```python
#!/usr/bin/env python3
"""Audit documentation for structural problems.

Finds near-duplicate content, thin pages, orphaned pages, structure
issues, and inconsistent frontmatter. Outputs a JSON audit report.

Usage:
    python audit_content.py [docs_directory] [--min-words N] [--similarity-threshold N] [--max-files N]

Examples:
    python audit_content.py ./docs
    python audit_content.py ./docs --min-words 50 --similarity-threshold 0.7
"""

import json
import os
import re
import sys

MAX_FILES = 200
MAX_FILES_UPPER = 10_000
# Default minimum word count for "thin page" detection
DEFAULT_MIN_WORDS = 100
# Default Jaccard similarity threshold for near-duplicate detection
DEFAULT_SIMILARITY = 0.60
# Files with fewer than 5 sentences are too short for meaningful comparison
MIN_SENTENCES_FOR_COMPARISON = 5
# Pages over this word count with no subheadings need structure
LONG_PAGE_THRESHOLD = 500

# Frontmatter fences
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
# Fenced code blocks
CODE_BLOCK_RE = re.compile(r"(?:```|~~~).*?(?:```|~~~)", re.DOTALL)
# HTML tags
HTML_TAG_RE = re.compile(r"<[^>]+>")
# ATX headings
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
# Markdown links: [text](target)
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
# Sentence endings
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")

# Navigation config files to check for orphan detection
NAV_CONFIGS = [
    "_sidebar.md", "mkdocs.yml", "docusaurus.config.js", "docusaurus.config.ts",
    "mint.json", "_meta.json", "_category_.json", "sidebars.js", "sidebars.ts",
    "navigation.yml", "nav.yml", "toc.yml",
]

# Files that are typically entry points and should not be flagged as orphans
INDEX_FILES = {
    "readme.md", "index.md", "index.mdx", "readme.mdx",
    "_index.md", "_index.mdx",
}


def find_doc_files(root, max_files):
    """Walk directory tree and collect documentation files."""
    doc_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in {
                "node_modules", ".git", "vendor", "dist", "build",
                ".next", "__pycache__", ".claude",
            }
        ]
        for f in sorted(filenames):
            if f.endswith((".md", ".mdx")):
                doc_files.append(os.path.join(dirpath, f))
                if len(doc_files) >= max_files:
                    return doc_files, True
    return doc_files, False


def strip_content(text):
    """Remove frontmatter, code blocks, and HTML to isolate prose."""
    text = FRONTMATTER_RE.sub("", text)
    text = CODE_BLOCK_RE.sub("", text)
    text = HTML_TAG_RE.sub("", text)
    return text.strip()


def extract_frontmatter(text):
    """Extract frontmatter fields as a dict. Returns empty dict if none."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).split("\n"):
        if ":" in line:
            key = line.split(":", 1)[0].strip()
            if key and not key.startswith("#"):
                fields[key] = True
    return fields


def extract_sentences(text):
    """Split text into normalized sentences for comparison."""
    prose = strip_content(text)
    # Remove headings for sentence extraction
    prose = HEADING_RE.sub("", prose)
    sentences = SENTENCE_RE.split(prose)
    normalized = set()
    for s in sentences:
        s = re.sub(r"\s+", " ", s.strip().lower())
        if len(s) > 20:
            normalized.add(s)
    return normalized


def jaccard_similarity(set_a, set_b):
    """Compute Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def count_prose_words(text):
    """Count words in prose content (excluding frontmatter, code, headings)."""
    prose = strip_content(text)
    prose = HEADING_RE.sub("", prose)
    words = re.findall(r"[a-zA-Z]+", prose)
    return len(words)


def find_linked_files(files, root):
    """Find all files that are linked from any other file."""
    linked = set()
    for filepath in files:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        for match in MD_LINK_RE.finditer(content):
            target = match.group(2).split("#")[0].split("?")[0].strip()
            if target and not target.startswith(("http://", "https://", "mailto:", "#")):
                # Resolve relative path
                base_dir = os.path.dirname(filepath)
                resolved = os.path.normpath(os.path.join(base_dir, target))
                linked.add(resolved)
    return linked


def find_nav_referenced_files(root):
    """Find files referenced in navigation config files."""
    referenced = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in {"node_modules", ".git", "vendor", "dist", "build"}
        ]
        for f in filenames:
            if f in NAV_CONFIGS:
                config_path = os.path.join(dirpath, f)
                with open(config_path, "r", encoding="utf-8", errors="replace") as fh:
                    config_content = fh.read()
                # Extract any file-like references (paths ending in .md/.mdx or path segments)
                for match in re.finditer(r'["\']([^"\']+\.mdx?)["\']', config_content):
                    ref = match.group(1)
                    resolved = os.path.normpath(os.path.join(dirpath, ref))
                    referenced.add(resolved)
                # Also check for bare path references without extension
                for match in re.finditer(r'["\'/]([a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_-]+)*)["\']', config_content):
                    ref = match.group(1)
                    for ext in (".md", ".mdx"):
                        resolved = os.path.normpath(
                            os.path.join(dirpath, ref + ext)
                        )
                        referenced.add(resolved)
    return referenced


def main():
    args = sys.argv[1:]
    docs_dir = "."
    min_words = DEFAULT_MIN_WORDS
    similarity_threshold = DEFAULT_SIMILARITY
    max_files = MAX_FILES

    i = 0
    while i < len(args):
        if args[i] == "--min-words" and i + 1 < len(args):
            min_words = int(args[i + 1])
            i += 2
        elif args[i] == "--similarity-threshold" and i + 1 < len(args):
            similarity_threshold = float(args[i + 1])
            i += 2
        elif args[i] == "--max-files" and i + 1 < len(args):
            max_files = min(int(args[i + 1]), MAX_FILES_UPPER)
            i += 2
        elif not args[i].startswith("-"):
            docs_dir = args[i]
            i += 1
        else:
            i += 1

    if not os.path.isdir(docs_dir):
        print(json.dumps({"error": "not_a_directory", "path": docs_dir}))
        return

    files, truncated = find_doc_files(docs_dir, max_files)

    if not files:
        print(json.dumps({"error": "no_docs_found", "path": docs_dir}))
        return

    # Read all files
    file_data = {}
    for filepath in files:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        file_data[filepath] = content

    # --- Near-duplicate detection ---
    duplicates = []
    sentence_sets = {}
    for filepath, content in file_data.items():
        sents = extract_sentences(content)
        if len(sents) >= MIN_SENTENCES_FOR_COMPARISON:
            sentence_sets[filepath] = sents

    checked = set()
    for file_a in sentence_sets:
        for file_b in sentence_sets:
            if file_a >= file_b:
                continue
            pair_key = (file_a, file_b)
            if pair_key in checked:
                continue
            checked.add(pair_key)

            sim = jaccard_similarity(sentence_sets[file_a], sentence_sets[file_b])
            if sim >= similarity_threshold:
                duplicates.append({
                    "file_a": file_a,
                    "file_b": file_b,
                    "similarity": round(sim * 100, 1),
                })

    duplicates.sort(key=lambda d: d["similarity"], reverse=True)

    # --- Thin pages ---
    thin_pages = []
    for filepath, content in file_data.items():
        word_count = count_prose_words(content)
        if word_count < min_words:
            thin_pages.append({
                "file": filepath,
                "word_count": word_count,
            })

    thin_pages.sort(key=lambda t: t["word_count"])

    # --- Orphaned pages ---
    linked_files = find_linked_files(files, docs_dir)
    nav_files = find_nav_referenced_files(docs_dir)
    all_referenced = linked_files | nav_files

    orphaned_pages = []
    for filepath in files:
        basename = os.path.basename(filepath).lower()
        if basename in INDEX_FILES:
            continue
        abs_path = os.path.normpath(filepath)
        if abs_path not in all_referenced:
            orphaned_pages.append({"file": filepath})

    # --- Structure issues ---
    structure_issues = []
    for filepath, content in file_data.items():
        headings = list(HEADING_RE.finditer(content))

        # No h1 at all
        has_h1 = any(len(m.group(1)) == 1 for m in headings)
        # Check frontmatter title as h1 substitute
        fm = extract_frontmatter(content)
        if not has_h1 and "title" not in fm:
            structure_issues.append({
                "file": filepath,
                "type": "missing_h1",
                "message": "Page has no h1 heading and no title in frontmatter",
            })

        # No headings at all (for non-trivial files)
        word_count = count_prose_words(content)
        if not headings and word_count > 50:
            structure_issues.append({
                "file": filepath,
                "type": "no_headings",
                "message": f"Page has {word_count} words but no headings for structure",
            })

        # Long page with no subsections (only h1, no h2+)
        if word_count > LONG_PAGE_THRESHOLD:
            has_sub = any(len(m.group(1)) >= 2 for m in headings)
            if not has_sub:
                structure_issues.append({
                    "file": filepath,
                    "type": "no_subsections",
                    "message": f"Page has {word_count} words but no subsections (h2+)",
                })

    # --- Inconsistent frontmatter ---
    frontmatter_data = {}
    for filepath, content in file_data.items():
        fm = extract_frontmatter(content)
        if fm:
            frontmatter_data[filepath] = set(fm.keys())

    # Find fields that appear in 50%+ of files with frontmatter
    frontmatter_issues = []
    if frontmatter_data:
        all_fields = {}
        for fields in frontmatter_data.values():
            for field in fields:
                all_fields[field] = all_fields.get(field, 0) + 1

        threshold = len(frontmatter_data) * 0.5
        expected_fields = {
            f for f, count in all_fields.items() if count >= threshold
        }

        for filepath, fields in frontmatter_data.items():
            missing = expected_fields - fields
            if missing:
                frontmatter_issues.append({
                    "file": filepath,
                    "missing_fields": sorted(missing),
                })

        # Also flag files WITHOUT any frontmatter when most files have it
        files_with_fm = len(frontmatter_data)
        if files_with_fm > len(files) * 0.5:
            for filepath in files:
                if filepath not in frontmatter_data:
                    frontmatter_issues.append({
                        "file": filepath,
                        "missing_fields": sorted(expected_fields),
                        "note": "File has no frontmatter at all",
                    })

    report = {
        "summary": {
            "files_scanned": len(files),
            "files_truncated": truncated,
            "duplicates_found": len(duplicates),
            "thin_pages_found": len(thin_pages),
            "orphaned_pages_found": len(orphaned_pages),
            "structure_issues_found": len(structure_issues),
            "frontmatter_issues_found": len(frontmatter_issues),
        },
        "duplicates": duplicates,
        "thin_pages": thin_pages,
        "orphaned_pages": orphaned_pages,
        "structure_issues": structure_issues,
        "frontmatter_issues": frontmatter_issues,
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Make executable**

```bash
chmod +x skills/content-audit/scripts/audit_content.py
```

- [ ] **Step 3: Smoke test against this repo's docs**

```bash
python skills/content-audit/scripts/audit_content.py ./skills --max-files 20
```

Expected: JSON output with `summary.files_scanned` > 0.

- [ ] **Step 4: Verify error handling**

```bash
python skills/content-audit/scripts/audit_content.py /nonexistent
```

Expected: `{"error": "not_a_directory", "path": "/nonexistent"}`

---

### Task 7: Create `content-audit` SKILL.md

**Files:**
- Create: `skills/content-audit/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

```markdown
---
name: content-audit
description: Audit documentation for structural problems including near-duplicate content, thin pages, orphaned pages, missing structure, and inconsistent frontmatter. Runs a helper script that analyzes the docs directory and reports issues with actionable suggestions. Use periodically or before major releases to catch silent quality problems.
allowed-tools: Read, Edit, Glob, Grep, Bash
metadata:
  author: EkLine
  version: "3.0.0"
  argument-hint: "[docs_directory] [--min-words N] [--similarity-threshold N]"
---

# Audit documentation content

Run the helper script to find structural problems, then present results and offer to fix them.

## Inputs

- `$ARGUMENTS` — optional docs directory (defaults to current directory), `--min-words N` (default 100), `--similarity-threshold N` (default 0.60)

## Steps

### 1. Run the helper script

` ` `bash
python scripts/audit_content.py $ARGUMENTS
` ` `

Capture the JSON output.

The script checks for:

- Near-duplicate content (Jaccard similarity on normalized sentences, flags pairs above threshold)
- Thin pages (fewer than N words of prose, excluding frontmatter and code blocks)
- Orphaned pages (not linked from any other doc and not in any nav config file)
- Missing structure (no h1, no headings at all, long pages without subsections)
- Inconsistent frontmatter (fields present in 50%+ of files but missing from others)

Max 200 files per run.

### 2. Handle errors

If the JSON contains an `error` field:

- `not_a_directory` — tell user the specified path is not a valid directory
- `no_docs_found` — tell user no .md/.mdx files were found, suggest a different path

Stop here on error.

### 3. Present the audit report

Show a summary line:

- "Scanned X files: Y near-duplicates, Z thin pages, W orphans, V structure issues, U frontmatter inconsistencies"

Then present each category that has findings:

**Near-duplicate content** (`duplicates` array):

For each pair:
- Show both file paths and similarity percentage
- Recommend: review whether they should be merged, or one should link to the other

**Thin pages** (`thin_pages` array):

For each file:
- Show file path and word count
- If under 30 words, suggest deleting or merging into a parent page
- If 30-99 words, suggest expanding with more detail

**Orphaned pages** (`orphaned_pages` array):

For each file:
- Show file path
- Note it is not linked from any other doc or navigation config
- Suggest adding a link from a related page or adding to navigation

**Structure issues** (`structure_issues` array):

For each file:
- Show file path, issue type, and message
- `missing_h1` — suggest adding an h1 or a title in frontmatter
- `no_headings` — suggest adding section headings for scannability
- `no_subsections` — suggest breaking the page into sections with h2 headings

**Frontmatter inconsistencies** (`frontmatter_issues` array):

For each file:
- Show file path and which fields are missing
- Show which fields are expected (present in majority of files)

### 4. Offer to fix issues

Offer actions by category:

1. **Duplicates** — for each pair, offer to:
   - Read both files and show a side-by-side comparison of overlapping content
   - Suggest which file to keep as the canonical version
   - Draft a redirect or "see also" link from the duplicate to the canonical page
   - Skip

2. **Thin pages** — offer to:
   - Read the page and surrounding pages to suggest additional content
   - Merge into a parent page
   - Skip

3. **Orphans** — offer to:
   - Search for related pages using Grep on the orphan's title/topic
   - Add a link from the most relevant related page
   - Skip

4. **Structure** — offer to:
   - Add missing h1 headings
   - Add subsection headings for long pages (suggest splits based on content)
   - Skip

5. **Frontmatter** — offer to:
   - Add missing frontmatter fields with sensible defaults (title from h1, description from first paragraph)
   - Skip

When applying fixes, use the Read tool to understand context and the Edit tool for targeted changes.

### 5. Summary

Report what was addressed:

- Number of issues fixed by category
- Number of issues skipped for manual review
- Overall recommendation for next steps
```

Note: Replace ` ` ` with actual triple backticks.

- [ ] **Step 2: Commit content-audit skill**

```bash
git add skills/content-audit/
git commit -m "feat: Add content-audit skill with duplicate and orphan detection"
```

---

### Task 8: Create `docs-health` orchestrator SKILL.md

**Files:**
- Create: `skills/docs-health/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

```markdown
---
name: docs-health
description: Run a comprehensive documentation health check that combines link validation, readability analysis, style guide compliance, terminology consistency, and docs freshness into a single report card with an overall score. The one-command overview of your documentation quality. Use for periodic health checks, before releases, or to understand where to focus improvement efforts.
allowed-tools: Read, Edit, Glob, Grep, Bash
metadata:
  author: EkLine
  version: "3.0.0"
  argument-hint: "[docs_directory] [--skip-freshness] [--skip-external]"
---

# Documentation health check

Run multiple documentation quality checks and produce a unified health report card with an overall score.

## Inputs

- `$ARGUMENTS` — optional docs directory (defaults to current directory), `--skip-freshness` to skip git-based freshness checks, `--skip-external` to skip external URL validation

## Steps

### 1. Determine the docs directory

Parse `$ARGUMENTS` for the docs directory. If not specified, look for common doc directories in order: `docs/`, `documentation/`, `content/`, `pages/`. If none found, use the current directory.

Store the resolved docs directory path — all subsequent scripts use it.

### 2. Run the link check

```bash
python ../check-links/scripts/extract_links.py <docs_dir>
```

If `--skip-external` was NOT passed, add `--external` flag.

From the JSON output, compute the links score:

- Count total links (internal + external) from `summary`
- Count broken links from `broken_internal` and `broken_external` arrays
- **Links score** = `(1 - broken_count / total_links) * 100` (floor at 0, cap at 100)
- If no links found, score = 100

Record: score, broken count, total count, top 3 broken links (file + target).

### 3. Run the readability analysis

```bash
python ../readability/scripts/analyze_readability.py <docs_dir>
```

From the JSON output:

- **Readability score** = `summary.avg_flesch_reading_ease` (already 0-100)
- Record: score, average grade level, count of files graded D or F, worst 3 files (path + grade)

### 4. Run the style guide check

Read `../style-guide/references/style-rules.md` for the rules.

Sample up to 10 documentation files from `<docs_dir>`. For each file, check for:

- **Banned phrases**: search for "please note that", "it's worth mentioning", "in order to", "basically", "simply", "just", "easy", "easily", "we are happy to announce", "in this section we will" (case-insensitive)
- **Passive voice in headings**: headings containing "is", "are", "was", "were" + past participle
- **Heading case**: headings that use Title Case instead of Sentence case (more than 2 capitalized words)
- **Missing code block language**: fenced code blocks without a language identifier

Count total violations across all sampled files.

- **Style score** = `max(0, 100 - (violation_count * 5))` — each violation costs 5 points, floor at 0
- Record: score, violation count, top 3 violations (file + line + type)

### 5. Run the terminology check

Read `../terminology/references/terminology-rules.md` for the approved terms.

Using the same sampled files from step 4, check for:

- Known wrong variants (e.g., "NodeJS" instead of "Node.js", "api-key" instead of "API key")
- Prohibited terms (e.g., "blacklist", "whitelist", "master/slave")
- Inconsistent usage of the same concept within a file

Count total inconsistencies.

- **Terminology score** = `max(0, 100 - (inconsistency_count * 5))` — each issue costs 5 points, floor at 0
- Record: score, inconsistency count, top 3 issues (file + term found + correct term)

### 6. Run the freshness check (unless skipped)

If `--skip-freshness` was passed, or the directory is not inside a git repo, skip this step and note it in the report.

```bash
python ../docs-freshness/scripts/extract_changes.py <docs_dir>
```

From the JSON output:

- Count docs by status: fresh, likely_stale, stale
- **Freshness score** = `(fresh_count / total_docs) * 100`
- Record: score, stale count, total docs, top 3 stale docs (file + reason)

### 7. Compute overall score and present the report card

**Scoring weights (when all 5 categories run):**

| Category | Weight |
|----------|--------|
| Links | 25% |
| Readability | 25% |
| Style | 20% |
| Terminology | 15% |
| Freshness | 15% |

If freshness was skipped, redistribute its 15% proportionally:

| Category | Weight (no freshness) |
|----------|-----------------------|
| Links | 29% |
| Readability | 29% |
| Style | 24% |
| Terminology | 18% |

**Overall score** = weighted sum of category scores.

**Letter grade:**
- A+: 95-100, A: 90-94, A-: 87-89
- B+: 83-86, B: 80-82, B-: 77-79
- C+: 73-76, C: 70-72, C-: 67-69
- D+: 63-66, D: 60-62, D-: 57-59
- F: below 57

**Present the report card:**

```
Documentation Health Report
===========================
Overall Score: [grade] ([score]/100)

  Links        [grade]  ([score]/100)  — [summary]
  Readability  [grade]  ([score]/100)  — [summary]
  Style        [grade]  ([score]/100)  — [summary]
  Terminology  [grade]  ([score]/100)  — [summary]
  Freshness    [grade]  ([score]/100)  — [summary]

Top 5 issues to fix first:
  1. [highest impact issue across all categories]
  2. ...
  3. ...
  4. ...
  5. ...
```

For the "Top 5 issues" list, prioritize:
1. Errors (broken links, stale docs referencing removed code)
2. High-impact readability issues (files graded F)
3. Terminology errors (prohibited terms)
4. Style violations
5. Warnings and info items

### 8. Offer to fix issues

After presenting the report, offer:

1. **Fix top 5 issues** — work through each issue using the appropriate skill's fix workflow
2. **Focus on one category** — let user pick which category to improve
3. **Export report** — save the report card as a Markdown file in the docs directory
4. **Done** — end the health check

When fixing issues, delegate to the appropriate skill's workflow:
- Broken links → follow check-links fix workflow
- Readability → follow readability rewrite workflow
- Style violations → apply auto-fixes from style-guide
- Terminology → apply correct terms
- Stale docs → follow docs-freshness update workflow
```

Note: Replace backtick escapes with actual triple backticks.

- [ ] **Step 2: Commit docs-health skill**

```bash
git add skills/docs-health/
git commit -m "feat: Add docs-health orchestrator with unified report card"
```

---

### Task 9: Update plugin metadata

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Update `plugin.json`**

```json
{
  "name": "ekline-docs-skills",
  "description": "EkLine documentation toolkit — 12 skills for reviewing, enforcing style, checking terminology, validating links, detecting stale docs, measuring coverage, scoring readability, auditing content, checking accessibility, generating changelogs, creating llms.txt, and running full health checks",
  "version": "3.0.0",
  "author": {
    "name": "EkLine",
    "email": "support@ekline.io"
  },
  "category": "documentation"
}
```

- [ ] **Step 2: Update `marketplace.json`**

```json
{
  "name": "ekline-docs-skills",
  "description": "Claude Code documentation toolkit — 12 skills for reviewing, enforcing style, checking terminology, validating links, detecting stale docs, measuring coverage, scoring readability, auditing content, checking accessibility, generating changelogs, creating llms.txt, and running full health checks. Powered by EkLine.",
  "owner": {
    "name": "EkLine",
    "email": "support@ekline.io",
    "url": "https://ekline.io"
  },
  "plugins": [
    {
      "name": "ekline-docs-skills",
      "description": "EkLine documentation toolkit — review, enforce style, check terminology, validate links, detect stale docs, measure coverage, score readability, audit content, check accessibility, generate changelogs, create llms.txt, and run full health checks",
      "category": "documentation",
      "version": "3.0.0",
      "source": "./",
      "author": {
        "name": "EkLine",
        "email": "support@ekline.io"
      }
    }
  ]
}
```

- [ ] **Step 3: Commit metadata updates**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: Bump to v3.0.0 with 12 skills in plugin metadata"
```

---

### Task 10: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README with new skills and improved structure**

The full README should be:

```markdown
# Documentation Skills for Claude Code by EkLine

A Claude Code plugin that reviews, fixes, and improves your documentation using [EkLine](https://ekline.io) — with built-in style enforcement, terminology checks, readability scoring, accessibility audits, content analysis, stale docs detection, link validation, coverage measurement, changelog generation, and LLM-readiness tooling.

## Skills

### Health and analysis

#### `docs-health`

Runs a comprehensive documentation health check — combines link validation, readability scoring, style compliance, terminology consistency, and freshness detection into a single report card with an overall score.

```
/docs-health ./docs
/docs-health ./docs --skip-freshness
```

- Produces a unified report card with letter grades per category
- Computes an overall health score (0-100) with weighted categories
- Ranks the top issues to fix first, prioritized by impact
- Offers to fix issues directly or focus on a specific category

#### `readability`

Analyzes documentation readability with quantitative metrics.

```
/readability ./docs
/readability --file docs/guide.md
```

- Computes Flesch-Kincaid Grade Level (target: 8th grade or below)
- Computes Flesch Reading Ease score (target: 60+)
- Detects passive voice, complex sentences, and overly long sentences
- Grades each file A-F and offers to rewrite hard-to-read content

#### `content-audit`

Audits documentation for structural problems that accumulate silently.

```
/content-audit ./docs
/content-audit ./docs --min-words 50 --similarity-threshold 0.7
```

- Finds near-duplicate content across pages using sentence-level similarity
- Detects thin pages with too little content
- Identifies orphaned pages not linked from anywhere
- Flags pages missing headings, structure, or consistent frontmatter
- Suggests merges, expansions, and structural fixes

#### `accessibility`

Checks documentation for accessibility issues.

```
/accessibility ./docs
/accessibility --file docs/guide.md
```

- Finds images without alt text
- Validates heading hierarchy (no skipped levels, single h1)
- Flags non-descriptive link text ("click here", "read more")
- Detects color-only references that exclude screen reader users
- Checks for missing code block languages and tables without headers

### Quality enforcement

#### `review-docs`

Runs [EkLine Docs Reviewer](https://docs.ekline.io/reviewer/overview/) on your documentation and applies recommended fixes.

```
/review-docs ./docs
/review-docs docs/guide.md docs/api.md
```

- Reviews a directory, specific files, or just uncommitted git changes
- Presents findings grouped by file with rule IDs and AI suggestions
- Offers to apply fixes automatically, one by one, or by category
- Re-runs the review after applying fixes to verify

Requires `ekline-cli` and an EkLine token. See [Prerequisites](#prerequisites) below.

#### `style-guide`

Enforces documentation style, voice, and tone consistency.

- Checks for active voice, second person, present tense
- Flags banned phrases ("please note that", "in order to", "simply", etc.)
- Validates heading case, code block formatting, and list style
- Auto-fixes common violations like banned phrases and heading case
- Runs proactively when documentation files are created or modified

Rules are defined in `skills/style-guide/references/style-rules.md`.

#### `terminology`

Checks documentation for consistent terminology against a configurable set of rules.

- Validates product names, technical terms, action verbs, and UI elements
- Flags prohibited terms and inconsistent usage within a document
- Runs proactively when documentation files are created or modified

Rules are defined in `skills/terminology/references/terminology-rules.md`.

#### `check-links`

Scans documentation for broken links and missing anchors.

```
/check-links ./docs
/check-links ./docs --external
```

- Validates all internal file links and anchor references
- Optionally checks external URLs for 404s and redirects
- Detects orphaned pages not linked from any other doc
- Offers auto-fix for broken internal links with fuzzy matching

### Documentation health

#### `docs-freshness`

Detects stale documentation by comparing recent code changes against docs.

```
/docs-freshness
/docs-freshness main..HEAD ./docs
/docs-freshness v1.2.0..v1.3.0
```

- Analyzes git diffs for renamed functions, changed APIs, modified configs
- Searches docs for references to changed code
- Scores each doc file: Fresh, Possibly stale, Likely stale, or Stale
- Offers to draft updates for stale documentation

#### `docs-coverage`

Measures what percentage of your public API surface is documented.

```
/docs-coverage
/docs-coverage ./src ./docs
```

- Scans exported functions, classes, API endpoints, CLI commands, and config options
- Checks if corresponding documentation exists (in docs or inline)
- Reports coverage by type (functions, endpoints, components) and by directory
- Suggests documentation priorities and offers to generate stubs
- Supports TypeScript, Python, and Go

### Generation

#### `changelog`

Generates structured changelog entries from git history.

```
/changelog
/changelog v1.3.0
/changelog v1.2.0..v1.3.0
```

- Parses conventional commits or free-form commit messages
- Categorizes changes: Added, Changed, Fixed, Removed, Security, Breaking Changes
- Extracts PR and issue references
- Writes to CHANGELOG.md in [Keep a Changelog](https://keepachangelog.com/) format

#### `llms-txt`

Generates an `llms.txt` file for your project following the [llms.txt specification](https://llmstxt.org).

```
/llms-txt
/llms-txt ./docs
```

- Scans documentation files and extracts titles, descriptions, and categories
- Produces a structured `llms.txt` with sections (Docs, API, Guides, Examples)
- Optionally generates `llms-full.txt` with complete doc content for smaller projects
- Validates the output against the llms.txt specification

## Prerequisites

### EkLine CLI (for `review-docs` only)

**macOS:**

```bash
curl -L https://github.com/ekline-io/ekline-cli-binaries/releases/latest/download/ekline-cli-macos.tar.gz | tar xz
chmod +x ekline-cli
sudo mv ekline-cli /usr/local/bin/
```

**Linux:**

```bash
curl -L https://github.com/ekline-io/ekline-cli-binaries/releases/latest/download/ekline-cli-linux.tar.gz | tar xz
chmod +x ekline-cli
sudo mv ekline-cli /usr/local/bin/
```

**Windows:**

Download `ekline-cli-windows.zip` from the [Release Page](https://github.com/ekline-io/ekline-cli-binaries/releases/latest) and add to your PATH.

### EkLine Token (for `review-docs` only)

Get a token from the [EkLine Dashboard](https://ekline.io/dashboard) and set it as an environment variable:

```bash
export EKLINE_EK_TOKEN=your_token_here
```

`EK_TOKEN` is also accepted.

## Installation

Clone into your Claude Code skills directory:

```bash
# Project-level (recommended)
git clone https://github.com/ekline-io/ekline-docs-skills.git .claude/skills/ekline-docs-skills

# Or user-level (available in all projects)
git clone https://github.com/ekline-io/ekline-docs-skills.git ~/.claude/skills/ekline-docs-skills
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `EKLINE_EK_TOKEN` or `EK_TOKEN` | EkLine API token |
| `EKLINE_CLI` | Path to `ekline-cli` binary (if not on PATH) |

### EkLine Config

If your project has an `ekline.config.json`, the CLI picks up its settings automatically (style guide, framework, ignore rules, etc.).

### Customizing Rules

- **Terminology rules** — edit `skills/terminology/references/terminology-rules.md`
- **Style rules** — edit `skills/style-guide/references/style-rules.md`

## Supported File Types

`.md`, `.mdx`, `.rst`, `.adoc`, `.txt`, `.html`

## License

[MIT](LICENSE)
```

- [ ] **Step 2: Commit README update**

```bash
git add README.md
git commit -m "docs: Update README for v3.0.0 with 12 skills"
```

---

### Task 11: Integration smoke test

**Files:** None (testing only)

- [ ] **Step 1: Verify all skill directories exist**

```bash
ls -la skills/readability/SKILL.md skills/readability/scripts/analyze_readability.py skills/accessibility/SKILL.md skills/accessibility/scripts/check_accessibility.py skills/content-audit/SKILL.md skills/content-audit/scripts/audit_content.py skills/docs-health/SKILL.md
```

Expected: all 7 files listed.

- [ ] **Step 2: Run readability against this repo**

```bash
python skills/readability/scripts/analyze_readability.py . --max-files 20
```

Expected: JSON with `summary.files_analyzed` > 0 and valid grades.

- [ ] **Step 3: Run accessibility against this repo**

```bash
python skills/accessibility/scripts/check_accessibility.py . --max-files 20
```

Expected: JSON with `summary.files_scanned` > 0.

- [ ] **Step 4: Run content-audit against this repo**

```bash
python skills/content-audit/scripts/audit_content.py . --max-files 20
```

Expected: JSON with `summary.files_scanned` > 0.

- [ ] **Step 5: Verify all scripts handle errors**

```bash
python skills/readability/scripts/analyze_readability.py /nonexistent && python skills/accessibility/scripts/check_accessibility.py /nonexistent && python skills/content-audit/scripts/audit_content.py /nonexistent
```

Expected: each outputs `{"error": "not_a_directory", ...}`.

- [ ] **Step 6: Verify no tracked __pycache__ files**

```bash
git ls-files '*__pycache__*'
```

Expected: no output (empty).

- [ ] **Step 7: Verify .markdownlint.json is gone**

```bash
test -f .markdownlint.json && echo "STILL EXISTS" || echo "REMOVED"
```

Expected: `REMOVED`.

- [ ] **Step 8: Verify plugin version**

```bash
grep '"version"' .claude-plugin/plugin.json
```

Expected: `"version": "3.0.0"`.
