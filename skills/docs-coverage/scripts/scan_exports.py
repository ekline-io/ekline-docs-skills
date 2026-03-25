#!/usr/bin/env python3
"""Scan codebase for public API surface and check documentation coverage.

Extracts exported functions, classes, endpoints, config options, and CLI
commands from source code, then checks if corresponding documentation exists.
Outputs a JSON coverage report.

Usage:
    python scan_exports.py [source_dir] [--docs-dir DIR] [--max-files N]

Examples:
    python scan_exports.py ./src --docs-dir ./docs
    python scan_exports.py ./src
    python scan_exports.py . --max-files 100
"""

import json
import os
import re
import sys

MAX_SOURCE_FILES = 300
MAX_SOURCE_FILES_UPPER = 10_000
MAX_DOC_FILES = 200
MIN_NAME_LENGTH = 4
MIN_SEARCH_LENGTH = 6

EXCLUDE_DIRS = {
    "node_modules", ".git", "vendor", "dist", "build", ".next",
    "__pycache__", ".pytest_cache", "coverage", ".nyc_output",
    "test", "tests", "__tests__", "__test__", "spec", "specs",
    "fixtures", "mocks", "__mocks__", "migrations", "seeds",
}

EXCLUDE_FILE_PATTERNS = [
    re.compile(r"\.test\.[jt]sx?$"),
    re.compile(r"\.spec\.[jt]sx?$"),
    re.compile(r"_test\.py$"),
    re.compile(r"test_\w+\.py$"),
    re.compile(r"_test\.go$"),
    re.compile(r"conftest\.py$"),
    re.compile(r"setup\.py$"),
    re.compile(r"\.stories\.[jt]sx?$"),
    re.compile(r"\.d\.ts$"),
]

TS_PATTERNS = {
    "function": re.compile(r"^export\s+(?:async\s+)?function\s+(\w+)"),
    "const_arrow": re.compile(r"^export\s+(?:const|let)\s+(\w+)\s*="),
    "class": re.compile(r"^export\s+(?:abstract\s+)?class\s+(\w+)"),
    "interface": re.compile(r"^export\s+interface\s+(\w+)"),
    "type": re.compile(r"^export\s+type\s+(\w+)"),
    "default_function": re.compile(r"^export\s+default\s+(?:async\s+)?function\s+(\w+)"),
    "default_class": re.compile(r"^export\s+default\s+class\s+(\w+)"),
    "endpoint": re.compile(r"""(?:app|router)\.\s*(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]"""),
    "module_exports_fn": re.compile(r"^(?:module\.)?exports\.(\w+)\s*=\s*function"),
    "module_exports_val": re.compile(r"^(?:module\.)?exports\.(\w+)\s*="),
}

PY_PATTERNS = {
    "function": re.compile(r"^(?:async\s+)?def\s+([a-z]\w+)\s*\("),
    "class": re.compile(r"^class\s+(\w+)"),
    "endpoint_flask": re.compile(r"""@(?:app|bp|blueprint)\.\s*(?:route|get|post|put|delete)\s*\(\s*['"]([^'"]+)"""),
    "endpoint_fastapi": re.compile(r"""@(?:app|router)\.\s*(?:get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)"""),
}

GO_PATTERNS = {
    "function": re.compile(r"^func\s+([A-Z]\w+)\s*\("),
    "method": re.compile(r"^func\s+\([^)]+\)\s+([A-Z]\w+)\s*\("),
    "type": re.compile(r"^type\s+([A-Z]\w+)\s+(?:struct|interface)"),
}


def should_skip_file(filepath):
    for pattern in EXCLUDE_FILE_PATTERNS:
        if pattern.search(filepath):
            return True
    return False


def find_source_files(root, max_files):
    files_by_lang = {"typescript": [], "python": [], "go": []}
    total = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

        for f in filenames:
            filepath = os.path.join(dirpath, f)
            if should_skip_file(filepath):
                continue

            if f.endswith((".ts", ".tsx", ".js", ".jsx", ".mjs")):
                files_by_lang["typescript"].append(filepath)
            elif f.endswith(".py"):
                files_by_lang["python"].append(filepath)
            elif f.endswith(".go"):
                files_by_lang["go"].append(filepath)
            else:
                continue

            total += 1
            if total >= max_files:
                return files_by_lang, True

    return files_by_lang, False


def has_jsdoc(lines, target_line_idx):
    for i in range(target_line_idx - 1, max(target_line_idx - 10, -1), -1):
        stripped = lines[i].strip()
        if stripped == "*/":
            for j in range(i - 1, max(i - 30, -1), -1):
                if "/**" in lines[j]:
                    doc_lines = [lines[k].strip() for k in range(j, i + 1)
                                 if lines[k].strip() and lines[k].strip() not in ("/**", "*/", "*")]
                    return len(doc_lines) >= 2
            return False
        if stripped and not stripped.startswith("//") and not stripped.startswith("*"):
            break
    return False


def has_docstring(lines, target_line_idx):
    for i in range(target_line_idx + 1, min(target_line_idx + 3, len(lines))):
        stripped = lines[i].strip()
        if stripped.startswith(('"""', "'''")):
            return True
        if stripped and not stripped.startswith("#"):
            break
    return False


def has_godoc(lines, target_line_idx):
    if target_line_idx > 0:
        prev = lines[target_line_idx - 1].strip()
        return prev.startswith("//")
    return False


def extract_ts_exports(filepath, content):
    items = []
    lines = content.split("\n")
    is_tsx = filepath.endswith(".tsx")

    for line_num, line in enumerate(lines):
        for item_type, pattern in TS_PATTERNS.items():
            if item_type == "endpoint":
                for match in pattern.finditer(line):
                    method = match.group(1).upper()
                    path = match.group(2)
                    items.append({
                        "name": f"{method} {path}",
                        "type": "endpoint",
                        "file": filepath,
                        "line": line_num + 1,
                        "has_inline_docs": False,
                    })
                continue

            match = pattern.match(line)
            if match:
                name = match.group(1)
                if len(name) < MIN_NAME_LENGTH:
                    continue

                classified_type = item_type
                if item_type in ("function", "const_arrow", "default_function"):
                    if is_tsx and name[0].isupper():
                        classified_type = "component"
                    else:
                        classified_type = "function"
                elif item_type in ("class", "default_class"):
                    classified_type = "class"

                items.append({
                    "name": name,
                    "type": classified_type,
                    "file": filepath,
                    "line": line_num + 1,
                    "has_inline_docs": has_jsdoc(lines, line_num),
                })

    return items


def extract_py_exports(filepath, content):
    items = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines):
        for match in PY_PATTERNS["endpoint_flask"].finditer(line):
            items.append({
                "name": f"ROUTE {match.group(1)}",
                "type": "endpoint",
                "file": filepath,
                "line": line_num + 1,
                "has_inline_docs": False,
            })

        for match in PY_PATTERNS["endpoint_fastapi"].finditer(line):
            items.append({
                "name": f"ROUTE {match.group(1)}",
                "type": "endpoint",
                "file": filepath,
                "line": line_num + 1,
                "has_inline_docs": False,
            })

        match = PY_PATTERNS["function"].match(line)
        if match:
            name = match.group(1)
            if name.startswith("_") or len(name) < MIN_NAME_LENGTH:
                continue
            items.append({
                "name": name,
                "type": "function",
                "file": filepath,
                "line": line_num + 1,
                "has_inline_docs": has_docstring(lines, line_num),
            })
            continue

        match = PY_PATTERNS["class"].match(line)
        if match:
            name = match.group(1)
            if len(name) < MIN_NAME_LENGTH:
                continue
            items.append({
                "name": name,
                "type": "class",
                "file": filepath,
                "line": line_num + 1,
                "has_inline_docs": has_docstring(lines, line_num),
            })

    return items


def extract_go_exports(filepath, content):
    items = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines):
        for item_type, pattern in GO_PATTERNS.items():
            match = pattern.match(line)
            if match:
                name = match.group(1)
                if len(name) < MIN_NAME_LENGTH:
                    continue
                items.append({
                    "name": name,
                    "type": "function" if item_type in ("function", "method") else "type",
                    "file": filepath,
                    "line": line_num + 1,
                    "has_inline_docs": has_godoc(lines, line_num),
                })

    return items


def find_doc_files(docs_dir, max_files):
    doc_files = []
    search_dirs = [docs_dir] if docs_dir != "auto" else ["docs", "_docs", "content", "ekline-docs"]

    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        for dirpath, dirnames, filenames in os.walk(search_dir):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            for f in filenames:
                if f.endswith((".md", ".mdx")):
                    doc_files.append(os.path.join(dirpath, f))
                    if len(doc_files) >= max_files:
                        return doc_files
        if doc_files:
            break

    return doc_files


def check_documentation(item, doc_contents):
    name = item["name"]

    if item["type"] == "endpoint":
        search_term = name.split(" ", 1)[1] if " " in name else name
    else:
        search_term = name

    if len(search_term) < MIN_SEARCH_LENGTH:
        return "skipped"

    code_pattern = re.compile(
        rf"(?:`[^`]*{re.escape(search_term)}[^`]*`"
        rf"|#{1,6}\s+.*{re.escape(search_term)})"
    )

    for filepath, content in doc_contents.items():
        if code_pattern.search(content):
            return "documented"

    if item.get("has_inline_docs"):
        return "partial"

    return "undocumented"


def main():
    args = sys.argv[1:]
    source_dir = "."
    docs_dir = "auto"
    max_files = MAX_SOURCE_FILES

    i = 0
    while i < len(args):
        if args[i] == "--docs-dir" and i + 1 < len(args):
            docs_dir = args[i + 1]
            i += 2
            continue
        if args[i] == "--max-files" and i + 1 < len(args):
            try:
                max_files = int(args[i + 1])
            except ValueError:
                print(json.dumps({"error": "invalid_argument",
                                  "message": "--max-files must be an integer"}))
                sys.exit(1)
            if max_files < 1 or max_files > MAX_SOURCE_FILES_UPPER:
                print(json.dumps({"error": "invalid_argument",
                                  "message": f"--max-files must be between 1 and {MAX_SOURCE_FILES_UPPER}"}))
                sys.exit(1)
            i += 2
            continue
        if not args[i].startswith("-"):
            source_dir = args[i]
        i += 1

    if not os.path.isdir(source_dir):
        print(json.dumps({"error": "not_a_directory", "message": f"'{source_dir}' is not a directory"}))
        sys.exit(1)

    files_by_lang, truncated = find_source_files(source_dir, max_files)

    primary_lang = max(files_by_lang.items(), key=lambda x: len(x[1]))[0] if any(files_by_lang.values()) else "unknown"

    all_items = []

    for filepath in files_by_lang["typescript"]:
        try:
            with open(filepath, "r", errors="replace") as f:
                content = f.read()
            all_items.extend(extract_ts_exports(filepath, content))
        except OSError:
            continue

    for filepath in files_by_lang["python"]:
        try:
            with open(filepath, "r", errors="replace") as f:
                content = f.read()
            all_items.extend(extract_py_exports(filepath, content))
        except OSError:
            continue

    for filepath in files_by_lang["go"]:
        try:
            with open(filepath, "r", errors="replace") as f:
                content = f.read()
            all_items.extend(extract_go_exports(filepath, content))
        except OSError:
            continue

    if not all_items:
        print(json.dumps({
            "source_dir": source_dir,
            "primary_language": primary_lang,
            "message": "No public API items found.",
            "total_items": 0,
        }))
        sys.exit(0)

    doc_files = find_doc_files(docs_dir, MAX_DOC_FILES)
    doc_contents = {}
    for filepath in doc_files:
        try:
            with open(filepath, "r", errors="replace") as f:
                doc_contents[filepath] = f.read()
        except OSError:
            continue

    by_type = {}
    by_dir = {}
    documented_count = 0
    partial_count = 0
    undocumented_items = []
    partial_items = []

    for item in all_items:
        status = check_documentation(item, doc_contents) if doc_contents else "undocumented"

        item_type = item["type"]
        item_dir = os.path.dirname(item["file"])

        by_type.setdefault(item_type, {"total": 0, "documented": 0, "partial": 0})
        by_type[item_type]["total"] += 1

        by_dir.setdefault(item_dir, {"total": 0, "documented": 0})
        by_dir[item_dir]["total"] += 1

        if status == "documented":
            documented_count += 1
            by_type[item_type]["documented"] += 1
            by_dir[item_dir]["documented"] += 1
        elif status == "partial":
            partial_count += 1
            by_type[item_type]["partial"] += 1
            partial_items.append({
                "name": item["name"],
                "type": item["type"],
                "file": item["file"],
                "line": item["line"],
                "reason": "Has inline docs but no dedicated documentation page",
            })
        elif status == "undocumented":
            undocumented_items.append({
                "name": item["name"],
                "type": item["type"],
                "file": item["file"],
                "line": item["line"],
            })

    total = len(all_items)
    overall_pct = round((documented_count / total) * 100) if total > 0 else 0

    type_coverage = {}
    for t, data in sorted(by_type.items()):
        pct = round((data["documented"] / data["total"]) * 100) if data["total"] > 0 else 0
        type_coverage[t] = {
            "documented": data["documented"],
            "partial": data.get("partial", 0),
            "total": data["total"],
            "percentage": pct,
        }

    dir_coverage = {}
    for d, data in sorted(by_dir.items(), key=lambda x: x[1]["total"], reverse=True)[:15]:
        pct = round((data["documented"] / data["total"]) * 100) if data["total"] > 0 else 0
        dir_coverage[d] = {
            "documented": data["documented"],
            "total": data["total"],
            "percentage": pct,
        }

    # Detect docs type: if docs mention product features but not code symbols, it's product docs
    has_api_ref_docs = False
    code_mentions_in_docs = 0
    for content in doc_contents.values():
        backtick_matches = re.findall(r"`[^`]+\(\)`", content)
        code_mentions_in_docs += len(backtick_matches)
        if re.search(r"(?i)api\s+reference|function\s+reference|class\s+reference", content):
            has_api_ref_docs = True

    if has_api_ref_docs or code_mentions_in_docs > 20:
        docs_type = "api_reference"
        docs_type_note = "Docs appear to be API reference documentation — coverage percentage is directly meaningful."
    else:
        docs_type = "product_docs"
        docs_type_note = "Docs appear to be product/user-facing documentation (not API reference). Low coverage is expected — product docs describe features, not individual code exports. Consider this a map of what COULD be documented, not what SHOULD be."

    result = {
        "source_dir": source_dir,
        "docs_dir": docs_dir,
        "primary_language": primary_lang,
        "docs_type": docs_type,
        "docs_type_note": docs_type_note,
        "source_files_scanned": sum(len(v) for v in files_by_lang.values()),
        "source_files_truncated": truncated,
        "doc_files_found": len(doc_files),
        "total_public_items": total,
        "overall_coverage": {
            "documented": documented_count,
            "partial": partial_count,
            "undocumented": len(undocumented_items),
            "total": total,
            "percentage": overall_pct,
        },
        "by_type": type_coverage,
        "by_directory": dir_coverage,
        "undocumented": undocumented_items[:30],
        "partial": partial_items[:15],
    }

    print(json.dumps(result, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
