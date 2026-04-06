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

```bash
python scripts/analyze_readability.py $ARGUMENTS
```

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

## Known Limitations

- Readability scores (Flesch-Kincaid) are calibrated for **English-language content only**. Non-English docs will produce meaningless scores.
- Passive voice detection is heuristic-based and may miss complex constructions (e.g., "is very carefully managed").
- Bullet list items are treated as individual sentences, which can lower average sentence length.
