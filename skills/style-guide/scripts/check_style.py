#!/usr/bin/env python3
"""Check documentation files against the EkLine style guide.

Parses banned phrases from style-rules.md and checks each Markdown file for:
  - Banned phrases (case-insensitive)
  - Title Case headings (should be sentence case)
  - Fenced code blocks with no language specifier

Outputs a JSON report to stdout.

Usage:
    python check_style.py [docs_directory] [--file FILE] [--max-files N]

Examples:
    python check_style.py ./docs
    python check_style.py --file docs/guide.md
"""

import json
import os
import re
import sys

MAX_FILES = 200
MAX_FILES_UPPER = 10_000

# Path to the style-rules reference file, relative to this script.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STYLE_RULES_PATH = os.path.join(_SCRIPT_DIR, "..", "references", "style-rules.md")

# YAML frontmatter block at the very start of the file.
FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
# Fenced code blocks (``` or ~~~, opening and closing fence).
CODE_BLOCK_RE = re.compile(r"(?:```|~~~).*?(?:```|~~~)", re.DOTALL)
# ATX headings: # through ######  — captures hashes and heading text.
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
# Opening fence line that has NO language identifier.
BARE_FENCE_RE = re.compile(r"^(?:```|~~~)\s*$", re.MULTILINE)
# Opening fence line that HAS a language identifier (used to skip those lines).
LANG_FENCE_RE = re.compile(r"^(?:```|~~~)\w", re.MULTILINE)

# Threshold: flag a heading as Title Case when this many non-first words start
# with an uppercase letter (ignoring short prepositions and conjunctions).
_TITLE_CASE_THRESHOLD = 2
_LOWERCASE_WORDS = frozenset(
    "a an the and but or nor for so yet as at by in of on to up via with from"
    " into onto over past than that".split()
)


def parse_banned_phrases():
    """Parse the banned-phrases table from style-rules.md.

    Returns a list of dicts with keys:
        phrase      - the banned phrase (lower-cased for matching)
        suggestion  - the recommended replacement
    """
    rules_path = os.path.normpath(STYLE_RULES_PATH)
    with open(rules_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Locate the "## Banned Phrases" section.
    section_match = re.search(r"^## Banned Phrases\b.*?(?=^## |\Z)", content,
                              re.MULTILINE | re.DOTALL)
    if not section_match:
        return []

    section = section_match.group()

    # Match table data rows:  | phrase | why | use instead |
    # Skip the header row (contains "Banned Phrase") and separator rows (---|).
    row_re = re.compile(r"^\|([^|]+)\|([^|]+)\|([^|]+)\|", re.MULTILINE)
    phrases = []
    for match in row_re.finditer(section):
        raw_phrase = match.group(1).strip().strip('"')
        raw_suggestion = match.group(3).strip()

        # Skip the header row and separator rows.
        if raw_phrase.lower().startswith("banned") or set(raw_phrase) <= set("-: "):
            continue

        # Strip markdown formatting (bold, italic, backticks).
        raw_phrase = re.sub(r"[*_`]", "", raw_phrase).strip()
        raw_suggestion = re.sub(r"[*_`]", "", raw_suggestion).strip()

        if raw_phrase:
            phrases.append({
                "phrase": raw_phrase.lower(),
                "suggestion": raw_suggestion,
            })

    return phrases


# Module-level cache so phrases are only parsed once per process.
_BANNED_PHRASES = None


def _get_banned_phrases():
    global _BANNED_PHRASES
    if _BANNED_PHRASES is None:
        _BANNED_PHRASES = parse_banned_phrases()
    return _BANNED_PHRASES


def get_excluded_ranges(content):
    """Return a set of 1-based line numbers inside frontmatter or code blocks.

    The opening fence line of a code block IS included in the excluded set so
    that headings and banned phrases inside code blocks are not flagged.
    Bare-fence detection uses a separate helper that does not consult this set.
    """
    excluded = set()

    fm_match = FRONTMATTER_RE.match(content)
    if fm_match:
        end_line = content[: fm_match.end()].count("\n") + 1
        excluded.update(range(1, end_line + 1))

    for match in CODE_BLOCK_RE.finditer(content):
        start_line = content[: match.start()].count("\n") + 1
        end_line = content[: match.end()].count("\n") + 1
        excluded.update(range(start_line, end_line + 1))

    return excluded


def get_frontmatter_lines(content):
    """Return a set of 1-based line numbers that are inside YAML frontmatter."""
    fm_match = FRONTMATTER_RE.match(content)
    if not fm_match:
        return set()
    end_line = content[: fm_match.end()].count("\n") + 1
    return set(range(1, end_line + 1))


def _is_title_case(heading_text):
    """Return True when two or more non-trivial words after the first are
    Title-Cased, which indicates the author used Title Case instead of
    sentence case."""
    words = heading_text.split()
    if len(words) < 2:
        return False

    # Count words after the first that are capitalised and not short stop-words.
    capped_count = sum(
        1
        for word in words[1:]
        if word and word[0].isupper() and word.lower() not in _LOWERCASE_WORDS
    )
    return capped_count >= _TITLE_CASE_THRESHOLD


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


def check_file(filepath):
    """Run all style checks on a single file. Returns list of findings."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    lines = content.split("\n")
    findings = []
    excluded = get_excluded_ranges(content)
    banned_phrases = _get_banned_phrases()

    # --- Check 1: Banned phrases ---
    for entry in banned_phrases:
        phrase = entry["phrase"]
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        for i, line in enumerate(lines, 1):
            if i in excluded:
                continue
            for match in pattern.finditer(line):
                findings.append({
                    "type": "banned_phrase",
                    "severity": "high",
                    "line": i,
                    "message": f'Banned phrase: "{match.group()}"',
                    "context": line.strip()[:120],
                    "suggestion": entry["suggestion"],
                })

    # --- Check 2: Heading sentence case ---
    for match in HEADING_RE.finditer(content):
        line_num = content[: match.start()].count("\n") + 1
        if line_num in excluded:
            continue
        heading_text = match.group(2).strip()
        if _is_title_case(heading_text):
            findings.append({
                "type": "heading_case",
                "severity": "medium",
                "line": line_num,
                "message": f'Heading appears to use Title Case: "{heading_text}"',
                "context": match.group().strip()[:120],
                "suggestion": (
                    "Use sentence case: capitalise only the first word and proper nouns."
                ),
            })

    # --- Check 3: Bare code fences (no language specifier) ---
    # Walk lines tracking open/close state so the opening fence line itself can
    # be inspected — it is excluded from banned-phrase checks but IS the line we
    # need to report here.
    frontmatter_lines = get_frontmatter_lines(content)
    fence_open_re = re.compile(r"^(?:```|~~~)")
    in_fence = False
    for i, line in enumerate(lines, 1):
        if i in frontmatter_lines:
            continue
        if fence_open_re.match(line):
            if not in_fence:
                # This is an opening fence.
                in_fence = True
                if BARE_FENCE_RE.match(line):
                    findings.append({
                        "type": "bare_code_fence",
                        "severity": "low",
                        "line": i,
                        "message": "Fenced code block has no language specifier",
                        "context": line.strip(),
                        "suggestion": (
                            "Add a language identifier, e.g. ```python, ```bash, ```json"
                        ),
                    })
            else:
                # This is a closing fence.
                in_fence = False

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
    else:
        if not os.path.isdir(docs_dir):
            print(json.dumps({"error": "not_a_directory", "path": docs_dir}))
            return
        files, _ = find_doc_files(docs_dir, max_files)

    if not files:
        print(json.dumps({"error": "no_docs_found", "path": docs_dir}))
        return

    all_findings = []
    type_counts = {"banned_phrase": 0, "heading_case": 0, "bare_code_fence": 0}
    total_violations = 0

    for filepath in files:
        file_findings = check_file(filepath)
        if file_findings:
            for finding in file_findings:
                ftype = finding["type"]
                type_counts[ftype] = type_counts.get(ftype, 0) + 1
                total_violations += 1
            all_findings.append({
                "file": filepath,
                "findings": file_findings,
            })

    report = {
        "summary": {
            "files_scanned": len(files),
            "total_violations": total_violations,
            "by_type": type_counts,
        },
        "files": all_findings,
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
