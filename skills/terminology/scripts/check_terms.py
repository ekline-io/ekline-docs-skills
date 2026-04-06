#!/usr/bin/env python3
"""Check documentation files for terminology violations.

Parses rules from terminology-rules.md and scans Markdown files for:
  - Incorrect product/tech names (e.g. "NodeJS" should be "Node.js")
  - Prohibited terms (e.g. "blacklist" should be "blocklist")
  - Context-dependent word forms (e.g. "setup" vs "set up")

Outputs a JSON report to stdout.

Usage:
    python check_terms.py [docs_directory] [--file FILE]

Examples:
    python check_terms.py ./docs
    python check_terms.py --file docs/guide.md
"""

import json
import os
import re
import sys

MAX_FILES = 200
MAX_FILES_UPPER = 10_000

# Path to the rules file, resolved relative to this script.
_RULES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "references",
    "terminology-rules.md",
)

# ---------------------------------------------------------------------------
# Regex constants for stripping non-prose content
# ---------------------------------------------------------------------------

# YAML frontmatter: --- ... --- at the very start of the file
FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
# Fenced code blocks: ``` ... ``` or ~~~ ... ~~~
CODE_BLOCK_RE = re.compile(r"(?:```|~~~).*?(?:```|~~~)", re.DOTALL)
# Inline code: `...`
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")


# ---------------------------------------------------------------------------
# Rules parsing
# ---------------------------------------------------------------------------

def _parse_table_rows(section_text):
    """Return list of cell-lists for each data row (skip header and separator)."""
    rows = []
    for line in section_text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        # Skip separator rows like |---|---|
        if re.match(r"^\|[\s:|-]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
    return rows


def _split_variants(text):
    """Split a comma-separated list of incorrect variants into clean strings."""
    return [v.strip() for v in text.split(",") if v.strip()]


def load_rules(rules_path=None):
    """Parse terminology-rules.md and return a structured rules dict.

    Returns:
        {
            "incorrect_terms": [{"correct": str, "incorrect": [str, ...], "notes": str}],
            "prohibited_terms": [{"prohibited": str, "use_instead": str, "reason": str}],
            "context_dependent": [{"noun": str, "verb": str, "notes": str}],
        }
    """
    path = rules_path or _RULES_PATH
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    incorrect_terms = []
    prohibited_terms = []
    context_dependent = []

    # Split on markdown horizontal rules or major section headings
    # We process the file section by section.
    sections = re.split(r"\n---\n", content)

    for section in sections:
        # --- Prohibited Terms table (Prohibited | Use Instead | Reason) ---
        if "Prohibited Terms" in section or "Never use these" in section:
            rows = _parse_table_rows(section)
            for cells in rows:
                if len(cells) < 2:
                    continue
                # Header row will have "Prohibited" as first cell
                if cells[0].lower() == "prohibited":
                    continue
                prohibited_terms.append({
                    "prohibited": cells[0],
                    "use_instead": cells[1] if len(cells) > 1 else "",
                    "reason": cells[2] if len(cells) > 2 else "",
                })
            continue

        # --- Context-dependent (One Word vs Two Words) ---
        # Table has: Correct (Noun) | Correct (Verb) | Notes
        if "One Word vs Two Words" in section or "Correct (Noun)" in section:
            rows = _parse_table_rows(section)
            for cells in rows:
                if len(cells) < 2:
                    continue
                if "correct" in cells[0].lower() or "noun" in cells[0].lower():
                    continue
                context_dependent.append({
                    "noun": cells[0].strip(),
                    "verb": cells[1].strip(),
                    "notes": cells[2].strip() if len(cells) > 2 else "",
                })
            continue

        # --- Incorrect terms: tables with Correct | Incorrect | Notes ---
        # Covers Product Names, Auth & Security, Programming Terms, Infrastructure
        rows = _parse_table_rows(section)
        for cells in rows:
            if len(cells) < 2:
                continue
            # Skip header rows
            if cells[0].lower() in ("correct", "element type", "action",
                                     "rule", "as noun", "element type"):
                continue
            correct = cells[0].strip()
            incorrect_raw = cells[1].strip() if len(cells) > 1 else ""
            notes = cells[2].strip() if len(cells) > 2 else ""
            variants = _split_variants(incorrect_raw)
            if correct and variants:
                incorrect_terms.append({
                    "correct": correct,
                    "incorrect": variants,
                    "notes": notes,
                })

    return {
        "incorrect_terms": incorrect_terms,
        "prohibited_terms": prohibited_terms,
        "context_dependent": context_dependent,
    }


# ---------------------------------------------------------------------------
# Exclusion ranges
# ---------------------------------------------------------------------------

def _get_excluded_ranges(content):
    """Return set of line numbers (1-based) inside frontmatter or code blocks."""
    excluded = set()

    fm_match = FRONTMATTER_RE.match(content)
    if fm_match:
        end_line = content[: fm_match.end()].count("\n") + 1
        excluded.update(range(1, end_line + 1))

    for match in CODE_BLOCK_RE.finditer(content):
        start = content[: match.start()].count("\n") + 1
        end = content[: match.end()].count("\n") + 1
        excluded.update(range(start, end + 1))

    return excluded


def _strip_inline_code(line):
    """Replace inline code spans with spaces of equal length to preserve column
    offsets while preventing matches inside backtick spans."""
    return INLINE_CODE_RE.sub(lambda m: " " * len(m.group()), line)


# ---------------------------------------------------------------------------
# Per-file checking
# ---------------------------------------------------------------------------

def check_file(filepath, rules):
    """Check a single file for terminology violations.

    Returns a list of finding dicts.  Each finding has:
        type, severity, line, found, correct, message, context
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    lines = content.split("\n")
    excluded = _get_excluded_ranges(content)
    findings = []

    # --- Incorrect terms ---
    for rule in rules["incorrect_terms"]:
        correct = rule["correct"]
        for wrong in rule["incorrect"]:
            if not wrong:
                continue
            # Use word-boundary matching; escape the wrong term for regex safety
            pattern = re.compile(r"\b" + re.escape(wrong) + r"\b")
            for i, raw_line in enumerate(lines, 1):
                if i in excluded:
                    continue
                search_line = _strip_inline_code(raw_line)
                for match in pattern.finditer(search_line):
                    findings.append({
                        "type": "incorrect_term",
                        "severity": "error",
                        "line": i,
                        "found": wrong,
                        "correct": correct,
                        "message": (
                            f'Use "{correct}" instead of "{wrong}"'
                        ),
                        "context": raw_line.strip()[:120],
                    })

    # --- Prohibited terms ---
    for rule in rules["prohibited_terms"]:
        prohibited = rule["prohibited"]
        use_instead = rule["use_instead"]
        # Some entries are "term1/term2" — split and check each
        variants = [v.strip() for v in prohibited.split("/") if v.strip()]
        for variant in variants:
            pattern = re.compile(r"\b" + re.escape(variant) + r"\b", re.IGNORECASE)
            for i, raw_line in enumerate(lines, 1):
                if i in excluded:
                    continue
                search_line = _strip_inline_code(raw_line)
                for match in pattern.finditer(search_line):
                    findings.append({
                        "type": "prohibited_term",
                        "severity": "error",
                        "line": i,
                        "found": match.group(),
                        "correct": use_instead,
                        "message": (
                            f'"{match.group()}" is prohibited. '
                            f'Use "{use_instead}" instead.'
                        ),
                        "context": raw_line.strip()[:120],
                    })

    # --- Context-dependent terms ---
    for rule in rules["context_dependent"]:
        noun_form = rule["noun"]
        verb_form = rule["verb"]
        notes = rule["notes"]
        pattern = re.compile(
            r"\b" + re.escape(noun_form) + r"\b", re.IGNORECASE
        )
        for i, raw_line in enumerate(lines, 1):
            if i in excluded:
                continue
            search_line = _strip_inline_code(raw_line)
            for match in pattern.finditer(search_line):
                findings.append({
                    "type": "context_dependent",
                    "severity": "info",
                    "line": i,
                    "found": match.group(),
                    "correct": noun_form,
                    "message": (
                        f'"{match.group()}" may be context-dependent. '
                        f'Use "{noun_form}" (noun) or "{verb_form}" (verb). '
                        f"{notes}"
                    ),
                    "context": raw_line.strip()[:120],
                })

    return findings


# ---------------------------------------------------------------------------
# Directory walker
# ---------------------------------------------------------------------------

def find_doc_files(root, max_files):
    """Walk directory tree and collect Markdown documentation files."""
    doc_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in {
                "node_modules", ".git", "vendor", "dist", "build",
                ".next", "__pycache__", ".claude",
            }
        ]
        for fname in sorted(filenames):
            if fname.endswith((".md", ".mdx")):
                doc_files.append(os.path.join(dirpath, fname))
                if len(doc_files) >= max_files:
                    return doc_files, True
    return doc_files, False


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

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

    rules = load_rules()

    file_results = []
    type_counts = {"incorrect_term": 0, "prohibited_term": 0, "context_dependent": 0}

    for filepath in files:
        findings = check_file(filepath, rules)
        if findings:
            for finding in findings:
                ftype = finding["type"]
                if ftype in type_counts:
                    type_counts[ftype] += 1
            file_results.append({
                "file": filepath,
                "findings": findings,
            })

    total = sum(type_counts.values())

    report = {
        "summary": {
            "files_scanned": len(files),
            "total_violations": total,
            "by_type": type_counts,
        },
        "files": file_results,
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
