#!/usr/bin/env python3
"""Extract and validate links from documentation files.

Parses Markdown files for all link types (inline, reference, image, HTML),
validates internal links exist, and reports broken links as JSON.

Usage:
    python extract_links.py [docs_directory] [--external] [--max-files N]

Examples:
    python extract_links.py ./docs
    python extract_links.py ./docs --external
    python extract_links.py . --max-files 50
"""

import json
import os
import re
import subprocess
import sys
import urllib.parse

MAX_FILES = 200
MAX_EXTERNAL_CHECKS = 50

MARKDOWN_LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
REFERENCE_LINK_USE = re.compile(r"\[([^\]]*)\]\[([^\]]*)\]")
REFERENCE_LINK_DEF = re.compile(r"^\[([^\]]+)\]:\s*(.+)$", re.MULTILINE)
HTML_HREF = re.compile(r'(?:href|src)=["\']([^"\']+)["\']')
HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def find_doc_files(root, max_files):
    doc_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in {"node_modules", ".git", "vendor", "dist", "build", ".next", "__pycache__"}
        ]
        for f in filenames:
            if f.endswith((".md", ".mdx")):
                doc_files.append(os.path.join(dirpath, f))
                if len(doc_files) >= max_files:
                    return doc_files, True
    return doc_files, False


def heading_to_anchor(text):
    text = re.sub(r"[\U00010000-\U0010ffff]", "", text)
    text = re.sub(r"[\u2000-\u3300\ufe0f\u200d]", "", text)
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def extract_anchors(content):
    anchors = set()
    for match in HEADING.finditer(content):
        anchors.add(heading_to_anchor(match.group(2)))

    for match in re.finditer(r'(?:id|name)=["\']([^"\']+)["\']', content):
        anchors.add(match.group(1))

    return anchors


def extract_links(filepath, content):
    links = []
    ref_defs = {}

    for match in REFERENCE_LINK_DEF.finditer(content):
        ref_defs[match.group(1).lower()] = match.group(2).strip()

    lines = content.split("\n")
    in_code_block = False

    for line_num, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        for match in MARKDOWN_LINK.finditer(line):
            links.append({
                "file": filepath,
                "line": line_num,
                "text": match.group(1),
                "target": match.group(2).split()[0],
                "type": classify_link(match.group(2).split()[0]),
            })

        for match in REFERENCE_LINK_USE.finditer(line):
            ref_key = (match.group(2) or match.group(1)).lower()
            target = ref_defs.get(ref_key, "")
            if target:
                links.append({
                    "file": filepath,
                    "line": line_num,
                    "text": match.group(1),
                    "target": target,
                    "type": classify_link(target),
                })

        for match in HTML_HREF.finditer(line):
            links.append({
                "file": filepath,
                "line": line_num,
                "text": "",
                "target": match.group(1),
                "type": classify_link(match.group(1)),
            })

    return links


def classify_link(target):
    if target.startswith("mailto:"):
        return "email"
    if target.startswith(("http://", "https://")):
        return "external"
    if target.startswith("#"):
        return "anchor"
    if any(target.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")):
        return "image"
    return "internal"


def validate_internal_link(link, doc_files_set, anchors_by_file):
    target = link["target"]
    source_dir = os.path.dirname(link["file"])

    if target.startswith("#"):
        anchor = target[1:]
        file_anchors = anchors_by_file.get(link["file"], set())
        if anchor.lower() in {a.lower() for a in file_anchors}:
            return {"status": "ok"}
        similar = [a for a in file_anchors if a.lower().startswith(anchor.lower()[:5])]
        return {
            "status": "broken",
            "reason": f"Anchor #{anchor} not found in file",
            "available_anchors": sorted(file_anchors)[:10],
            "suggestions": similar[:3],
        }

    path_part, _, anchor_part = target.partition("#")

    if path_part:
        resolved = os.path.normpath(os.path.join(source_dir, path_part))

        if os.path.exists(resolved):
            if anchor_part:
                file_anchors = anchors_by_file.get(resolved, set())
                if not file_anchors:
                    try:
                        with open(resolved, "r", errors="replace") as f:
                            file_anchors = extract_anchors(f.read())
                    except OSError:
                        file_anchors = set()

                if anchor_part.lower() not in {a.lower() for a in file_anchors}:
                    return {
                        "status": "broken",
                        "reason": f"File exists but anchor #{anchor_part} not found",
                        "available_anchors": sorted(file_anchors)[:10],
                    }
            return {"status": "ok"}

        candidates = []
        parent = os.path.dirname(resolved)
        basename = os.path.basename(resolved)
        if os.path.isdir(parent):
            for f in os.listdir(parent):
                if f.lower().startswith(basename[:3].lower()) and f.endswith((".md", ".mdx")):
                    candidates.append(f)

        return {
            "status": "broken",
            "reason": "Target file does not exist",
            "resolved_path": resolved,
            "suggestions": candidates[:3],
        }

    return {"status": "ok"}


def check_external_link(url):
    try:
        result = subprocess.run(
            ["curl", "-sL", "-o", "/dev/null", "-w", "%{http_code}",
             "--max-time", "10", "-A",
             "Mozilla/5.0 (compatible; EkLine-LinkChecker/1.0)", url],
            capture_output=True, text=True, timeout=15,
        )
        code = int(result.stdout.strip())
        if code == 200:
            return {"status": "ok", "http_code": code}
        if code in (301, 302, 307, 308):
            return {"status": "redirect", "http_code": code}
        if code == 403:
            return {"status": "indeterminate", "http_code": code, "reason": "403 Forbidden — may be bot protection"}
        if code == 429:
            return {"status": "rate_limited", "http_code": code}
        if code in (404, 410):
            return {"status": "broken", "http_code": code, "reason": f"HTTP {code}"}
        return {"status": "unknown", "http_code": code}
    except (subprocess.TimeoutExpired, ValueError, OSError):
        return {"status": "timeout", "reason": "Request timed out after 10s"}


def main():
    args = sys.argv[1:]
    docs_dir = "."
    check_external = False
    max_files = MAX_FILES

    i = 0
    while i < len(args):
        if args[i] == "--external":
            check_external = True
        elif args[i] == "--max-files" and i + 1 < len(args):
            max_files = int(args[i + 1])
            i += 1
        elif not args[i].startswith("-"):
            docs_dir = args[i]
        i += 1

    if not os.path.isdir(docs_dir):
        print(json.dumps({"error": "not_a_directory", "message": f"'{docs_dir}' is not a directory"}))
        sys.exit(1)

    doc_files, truncated = find_doc_files(docs_dir, max_files)
    if not doc_files:
        print(json.dumps({"error": "no_docs_found", "message": f"No .md/.mdx files found in '{docs_dir}'"}))
        sys.exit(1)

    all_links = []
    anchors_by_file = {}
    doc_files_set = set(os.path.normpath(f) for f in doc_files)
    linked_files = set()

    for filepath in doc_files:
        try:
            with open(filepath, "r", errors="replace") as f:
                content = f.read()
        except OSError:
            continue

        anchors_by_file[filepath] = extract_anchors(content)
        file_links = extract_links(filepath, content)
        all_links.extend(file_links)

    broken_internal = []
    broken_external = []
    redirects = []
    ok_count = 0
    external_count = 0
    internal_count = 0
    anchor_count = 0
    image_count = 0

    for link in all_links:
        link_type = link["type"]

        if link_type == "email":
            continue

        if link_type in ("internal", "anchor", "image"):
            if link_type == "anchor":
                anchor_count += 1
            elif link_type == "image":
                image_count += 1
            else:
                internal_count += 1
                linked_files.add(
                    os.path.normpath(os.path.join(os.path.dirname(link["file"]), link["target"].split("#")[0]))
                )

            result = validate_internal_link(link, doc_files_set, anchors_by_file)
            if result["status"] == "broken":
                broken_internal.append({**link, "validation": result})
            else:
                ok_count += 1

        elif link_type == "external":
            external_count += 1
            if check_external and len(broken_external) + len(redirects) < MAX_EXTERNAL_CHECKS:
                result = check_external_link(link["target"])
                if result["status"] == "broken":
                    broken_external.append({**link, "validation": result})
                elif result["status"] == "redirect":
                    redirects.append({**link, "validation": result})
                elif result["status"] == "ok":
                    ok_count += 1
            else:
                ok_count += 1

    orphaned = []
    for filepath in doc_files:
        norm = os.path.normpath(filepath)
        if norm not in linked_files and not filepath.endswith(("README.md", "index.md", "index.mdx")):
            orphaned.append(filepath)

    output = {
        "docs_directory": docs_dir,
        "files_scanned": len(doc_files),
        "files_truncated": truncated,
        "total_links": len(all_links),
        "summary": {
            "internal": internal_count,
            "anchors": anchor_count,
            "images": image_count,
            "external": external_count,
            "ok": ok_count,
            "broken_internal": len(broken_internal),
            "broken_external": len(broken_external),
            "redirects": len(redirects),
            "orphaned_pages": len(orphaned),
        },
        "broken_internal": [
            {
                "file": b["file"],
                "line": b["line"],
                "text": b["text"],
                "target": b["target"],
                "reason": b["validation"].get("reason", ""),
                "suggestions": b["validation"].get("suggestions", []),
                "available_anchors": b["validation"].get("available_anchors", []),
            }
            for b in broken_internal
        ],
        "broken_external": [
            {
                "file": b["file"],
                "line": b["line"],
                "target": b["target"],
                "http_code": b["validation"].get("http_code"),
                "reason": b["validation"].get("reason", ""),
            }
            for b in broken_external
        ],
        "redirects": [
            {
                "file": r["file"],
                "line": r["line"],
                "target": r["target"],
                "http_code": r["validation"].get("http_code"),
            }
            for r in redirects
        ],
        "orphaned_pages": orphaned[:20],
    }

    print(json.dumps(output, indent=2))
    sys.exit(1 if broken_internal or broken_external else 0)


if __name__ == "__main__":
    main()
