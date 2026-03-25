#!/usr/bin/env python3
"""Extract code changes and cross-reference against documentation.

Parses git diffs to identify changed functions, endpoints, configs, and
types, then searches documentation files for references to those changes.
Outputs a JSON freshness report.

Usage:
    python extract_changes.py [commit_range] [--docs-dir DIR] [--max-files N]

Examples:
    python extract_changes.py                           # last tag..HEAD
    python extract_changes.py main..HEAD --docs-dir docs
    python extract_changes.py HEAD~20..HEAD
"""

import json
import os
import re
import subprocess
import sys

MAX_CHANGED_FILES = 50
MAX_DOC_FILES = 100
MIN_SYMBOL_LENGTH = 6

CODE_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs", ".java", ".rb",
    ".cs", ".swift", ".kt", ".scala", ".c", ".cpp", ".h",
}

FUNCTION_PATTERNS = {
    ".ts":  re.compile(r"^[-+]\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)"),
    ".tsx": re.compile(r"^[-+]\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)"),
    ".js":  re.compile(r"^[-+]\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)"),
    ".jsx": re.compile(r"^[-+]\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)"),
    ".py":  re.compile(r"^[-+]\s*(?:async\s+)?def\s+(\w+)"),
    ".go":  re.compile(r"^[-+]\s*func\s+(?:\([^)]+\)\s+)?(\w+)"),
}

CONST_EXPORT_PATTERN = re.compile(r"^[-+]\s*export\s+(?:const|let|var)\s+(\w+)")
CLASS_PATTERN = re.compile(r"^[-+]\s*(?:export\s+)?class\s+(\w+)")
TYPE_PATTERN = re.compile(r"^[-+]\s*(?:export\s+)?(?:interface|type)\s+(\w+)")
ENDPOINT_PATTERN = re.compile(r"""(?:app|router)\.\s*(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]""")
ENV_VAR_PATTERN = re.compile(r"""(?:process\.env\.|os\.environ\.get\(|os\.getenv\()['"]?(\w+)""")
CONFIG_KEY_PATTERN = re.compile(r"""(?:config|settings|options)\s*[\[.]?\s*['"](\w+)""")


def run_git(args):
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip(), result.returncode


def find_range(user_range):
    if user_range and ".." in user_range:
        return user_range

    if user_range:
        return f"{user_range}~1..{user_range}"

    latest_tag, rc = run_git(["describe", "--tags", "--abbrev=0"])
    if rc == 0 and latest_tag:
        return f"{latest_tag}..HEAD"

    first_commit, rc = run_git(["log", "--since=30 days ago", "--format=%H", "--reverse"])
    if rc == 0 and first_commit:
        first = first_commit.split("\n")[0]
        return f"{first}..HEAD"

    return "HEAD~30..HEAD"


def get_changed_files(commit_range, max_files):
    raw, rc = run_git(["diff", "--name-only", commit_range])
    if rc != 0 or not raw:
        return [], False

    all_files = [f for f in raw.split("\n") if f.strip()]
    code_files = [f for f in all_files if os.path.splitext(f)[1] in CODE_EXTENSIONS]

    truncated = len(code_files) > max_files
    return code_files[:max_files], truncated


def extract_symbols_from_diff(diff_text, file_ext):
    symbols = {
        "added": [],
        "removed": [],
        "modified": [],
        "endpoints_added": [],
        "endpoints_removed": [],
        "env_vars": [],
        "config_keys": [],
    }

    func_pattern = FUNCTION_PATTERNS.get(file_ext)
    added_funcs = set()
    removed_funcs = set()

    for line in diff_text.split("\n"):
        if not line or line.startswith(("diff ", "index ", "--- ", "+++ ", "@@")):
            continue

        is_added = line.startswith("+")
        is_removed = line.startswith("-")

        if not is_added and not is_removed:
            continue

        if func_pattern:
            match = func_pattern.match(line)
            if match:
                name = match.group(1)
                if len(name) >= MIN_SYMBOL_LENGTH:
                    if is_added:
                        added_funcs.add(name)
                    else:
                        removed_funcs.add(name)

        for pattern, key in [
            (CONST_EXPORT_PATTERN, None),
            (CLASS_PATTERN, None),
            (TYPE_PATTERN, None),
        ]:
            match = pattern.match(line)
            if match:
                name = match.group(1)
                if len(name) >= MIN_SYMBOL_LENGTH:
                    if is_added:
                        added_funcs.add(name)
                    else:
                        removed_funcs.add(name)

        for match in ENDPOINT_PATTERN.finditer(line):
            endpoint = match.group(2)
            if is_added:
                symbols["endpoints_added"].append(endpoint)
            elif is_removed:
                symbols["endpoints_removed"].append(endpoint)

        for match in ENV_VAR_PATTERN.finditer(line):
            symbols["env_vars"].append(match.group(1))

        for match in CONFIG_KEY_PATTERN.finditer(line):
            key = match.group(1)
            if len(key) >= MIN_SYMBOL_LENGTH:
                symbols["config_keys"].append(key)

    only_removed = removed_funcs - added_funcs
    only_added = added_funcs - removed_funcs
    modified = added_funcs & removed_funcs

    symbols["added"] = sorted(only_added)
    symbols["removed"] = sorted(only_removed)
    symbols["modified"] = sorted(modified)

    symbols["env_vars"] = sorted(set(symbols["env_vars"]))
    symbols["config_keys"] = sorted(set(symbols["config_keys"]))
    symbols["endpoints_added"] = sorted(set(symbols["endpoints_added"]))
    symbols["endpoints_removed"] = sorted(set(symbols["endpoints_removed"]))

    return symbols


def find_doc_files(docs_dir, max_files):
    doc_files = []
    search_dirs = [docs_dir] if docs_dir != "auto" else ["docs", "_docs", "content", "."]

    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        for dirpath, dirnames, filenames in os.walk(search_dir):
            dirnames[:] = [
                d for d in dirnames
                if d not in {"node_modules", ".git", "vendor", "dist", "build", ".next"}
            ]
            for f in filenames:
                if f.endswith((".md", ".mdx")):
                    doc_files.append(os.path.join(dirpath, f))
                    if len(doc_files) >= max_files:
                        return doc_files
        if doc_files:
            break

    return doc_files


def search_docs_for_symbol(symbol, doc_files):
    references = []

    code_pattern = re.compile(
        rf"(?:`[^`]*{re.escape(symbol)}[^`]*`"
        rf"|{re.escape(symbol)}\s*\("
        rf"|{re.escape(symbol)}\s*=)"
    )

    prose_pattern = re.compile(rf"\b{re.escape(symbol)}\b")

    for filepath in doc_files:
        try:
            with open(filepath, "r", errors="replace") as f:
                content = f.read()
        except OSError:
            continue

        lines = content.split("\n")
        in_code_block = False

        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                if prose_pattern.search(line):
                    references.append({
                        "file": filepath,
                        "line": line_num,
                        "context": "code_block",
                        "confidence": "high",
                    })
            else:
                if code_pattern.search(line):
                    references.append({
                        "file": filepath,
                        "line": line_num,
                        "context": "inline_code",
                        "confidence": "high",
                    })
                elif prose_pattern.search(line):
                    references.append({
                        "file": filepath,
                        "line": line_num,
                        "context": "prose",
                        "confidence": "low",
                    })

    return references


def main():
    args = sys.argv[1:]
    docs_dir = "auto"
    max_changed = MAX_CHANGED_FILES
    user_range = None

    i = 0
    while i < len(args):
        if args[i] == "--docs-dir" and i + 1 < len(args):
            docs_dir = args[i + 1]
            i += 2
            continue
        if args[i] == "--max-files" and i + 1 < len(args):
            max_changed = int(args[i + 1])
            i += 2
            continue
        if not user_range and not args[i].startswith("-"):
            user_range = args[i]
        i += 1

    _, rc = run_git(["rev-parse", "--git-dir"])
    if rc != 0:
        print(json.dumps({"error": "not_a_git_repo", "message": "Not inside a git repository."}))
        sys.exit(1)

    commit_range = find_range(user_range)

    changed_files, truncated = get_changed_files(commit_range, max_changed)
    if not changed_files:
        print(json.dumps({
            "range": commit_range,
            "message": "No code files changed in this range.",
            "changed_files": 0,
            "stale_docs": [],
        }))
        sys.exit(0)

    all_symbols = {
        "removed": {},
        "modified": {},
        "endpoints_removed": {},
        "env_vars": {},
    }

    for filepath in changed_files:
        ext = os.path.splitext(filepath)[1]
        diff_text, rc = run_git(["diff", commit_range, "--", filepath])
        if rc != 0 or not diff_text:
            continue

        symbols = extract_symbols_from_diff(diff_text, ext)

        for sym in symbols["removed"]:
            all_symbols["removed"][sym] = filepath
        for sym in symbols["modified"]:
            all_symbols["modified"][sym] = filepath
        for ep in symbols["endpoints_removed"]:
            all_symbols["endpoints_removed"][ep] = filepath
        for ev in symbols["env_vars"]:
            all_symbols["env_vars"][ev] = filepath

    doc_files = find_doc_files(docs_dir, MAX_DOC_FILES)
    if not doc_files:
        print(json.dumps({
            "range": commit_range,
            "changed_files": len(changed_files),
            "message": "No documentation files found to check.",
            "docs_searched": docs_dir,
            "stale_docs": [],
        }))
        sys.exit(0)

    doc_findings = {}

    all_search_symbols = {}
    for sym, src in all_symbols["removed"].items():
        all_search_symbols[sym] = {"type": "removed_symbol", "source": src, "severity": "high"}
    for sym, src in all_symbols["modified"].items():
        all_search_symbols[sym] = {"type": "modified_symbol", "source": src, "severity": "medium"}
    for ep, src in all_symbols["endpoints_removed"].items():
        all_search_symbols[ep] = {"type": "removed_endpoint", "source": src, "severity": "high"}
    for ev, src in all_symbols["env_vars"].items():
        if len(ev) < MIN_SYMBOL_LENGTH:
            continue
        all_search_symbols[ev] = {"type": "env_var_changed", "source": src, "severity": "medium"}

    for symbol, meta in all_search_symbols.items():
        refs = search_docs_for_symbol(symbol, doc_files)
        high_confidence_refs = [r for r in refs if r["confidence"] == "high"]

        if high_confidence_refs:
            for ref in high_confidence_refs:
                doc_file = ref["file"]
                if doc_file not in doc_findings:
                    doc_findings[doc_file] = {"findings": [], "score": 0}

                doc_findings[doc_file]["findings"].append({
                    "symbol": symbol,
                    "type": meta["type"],
                    "source_file": meta["source"],
                    "doc_line": ref["line"],
                    "context": ref["context"],
                    "severity": meta["severity"],
                })

                if meta["severity"] == "high":
                    doc_findings[doc_file]["score"] += 3
                else:
                    doc_findings[doc_file]["score"] += 1

    stale_docs = []
    for doc_file, data in sorted(doc_findings.items(), key=lambda x: -x[1]["score"]):
        if data["score"] >= 3:
            status = "stale"
        elif data["score"] >= 1:
            status = "likely_stale"
        else:
            status = "possibly_stale"

        stale_docs.append({
            "file": doc_file,
            "status": status,
            "score": data["score"],
            "findings": data["findings"][:10],
        })

    result = {
        "range": commit_range,
        "changed_code_files": len(changed_files),
        "changed_files_truncated": truncated,
        "symbols_tracked": len(all_search_symbols),
        "doc_files_searched": len(doc_files),
        "stale_docs": stale_docs,
        "fresh_docs": len(doc_files) - len(stale_docs),
        "summary": {
            "stale": len([d for d in stale_docs if d["status"] == "stale"]),
            "likely_stale": len([d for d in stale_docs if d["status"] == "likely_stale"]),
            "fresh": len(doc_files) - len(stale_docs),
        },
    }

    print(json.dumps(result, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
