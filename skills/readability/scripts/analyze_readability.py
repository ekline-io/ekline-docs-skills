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
# Markdown headings (ATX style) — match entire line so heading text is removed
HEADING_RE = re.compile(r"^#{1,6}\s+.*$", re.MULTILINE)
# MDX/JSX import and export statements (e.g. `import Tabs from '@theme/Tabs'`)
MDX_IMPORT_RE = re.compile(r"^(?:import|export)\s+.*$", re.MULTILINE)
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
    text = MDX_IMPORT_RE.sub("", text)
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
    """Split text into sentences. Returns list of non-empty sentences.

    Splits first on line boundaries so that list items and headings without
    trailing punctuation each become their own sentence, then splits again on
    sentence-ending punctuation within each line.
    """
    lines = text.split("\n")
    sentences = []
    for line in lines:
        # Split each line on sentence-ending punctuation
        parts = SENTENCE_SPLIT_RE.split(line)
        sentences.extend(parts)
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
