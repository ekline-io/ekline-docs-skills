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
