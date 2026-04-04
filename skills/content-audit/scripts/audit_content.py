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
# HTML heading tags: <h1>, <h1 class="...">, <h1 align="center">
HTML_H1_RE = re.compile(r"<h1[\s>]", re.IGNORECASE)
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
                # Check for Docusaurus autogenerated sidebars
                if f in ("sidebars.js", "sidebars.ts", "docusaurus.config.js", "docusaurus.config.ts"):
                    if "autogenerated" in config_content:
                        # Find dirName values
                        for dir_match in re.finditer(r'dirName:\s*["\']([^"\']*)["\']', config_content):
                            auto_dir = dir_match.group(1)
                            if auto_dir == ".":
                                auto_dir = ""
                            # Mark all doc files under this directory as referenced
                            docs_base = os.path.dirname(config_path)
                            auto_path = os.path.join(docs_base, auto_dir) if auto_dir else docs_base
                            for auto_dirpath, _, auto_filenames in os.walk(auto_path):
                                for auto_f in auto_filenames:
                                    if auto_f.endswith((".md", ".mdx")):
                                        resolved = os.path.normpath(os.path.join(auto_dirpath, auto_f))
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

    if truncated:
        for orphan in orphaned_pages:
            orphan["note"] = "File set was truncated — this page may be linked from files not scanned"

    # --- Structure issues ---
    structure_issues = []
    for filepath, content in file_data.items():
        headings = list(HEADING_RE.finditer(content))

        # No h1 at all
        has_h1 = any(len(m.group(1)) == 1 for m in headings)
        # Also check for HTML <h1> tags (e.g. <h1 align="center">)
        if not has_h1:
            has_h1 = bool(HTML_H1_RE.search(content))
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
            "orphan_detection_truncated": truncated,
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
