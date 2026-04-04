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
