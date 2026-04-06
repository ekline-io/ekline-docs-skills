#!/usr/bin/env python3
"""Scan documentation and generate llms.txt following the specification.

Detects docs platform, classifies pages into sections, resolves URLs,
and outputs structured JSON for the skill to format and write.

Usage:
    python generate_llms_txt.py [docs_directory] [--base-url URL] [--full]

Examples:
    python generate_llms_txt.py ./docs
    python generate_llms_txt.py ./docs --base-url https://docs.example.com
    python generate_llms_txt.py ./docs --full
"""

import json
import os
import re
import sys

# Max pages to include in llms.txt — keeps the index concise and within
# typical LLM context windows (~4K tokens for 150 one-line entries).
MAX_FILES = 200
# llms-full.txt inlines entire page content; cap at 20 files / 200KB to stay
# within LLM context limits and avoid overwhelming token budgets.
MAX_FULL_FILES = 20
MAX_FULL_SIZE_KB = 200

PLATFORM_CONFIGS = {
    "docusaurus": ["docusaurus.config.js", "docusaurus.config.ts"],
    "mintlify": ["mint.json", "mintlify.json"],
    "mkdocs": ["mkdocs.yml", "mkdocs.yaml"],
    "gitbook": [".gitbook.yaml", "book.json"],
    "vitepress": [".vitepress/config.js", ".vitepress/config.ts", ".vitepress/config.mts"],
    "nextra": ["theme.config.jsx", "theme.config.tsx"],
    "astro_starlight": ["astro.config.mjs", "astro.config.ts"],
}

# Rules are evaluated in order — first match wins. This means API pages are
# classified before Guides, which prevents "/api/getting-started" from landing
# in Guides. Pages that match no rule default to the "Docs" section.
CLASSIFICATION_RULES = [
    {"section": "API", "path_patterns": [
        r"/api/", r"/reference/", r"/endpoints?/", r"/rest/", r"/graphql/",
    ], "content_patterns": [
        # Matches headings like "## GET /users"
        r"^#{1,2}\s+(?:GET|POST|PUT|DELETE|PATCH)\s+",
        r"endpoint|request body|response body|status code",
    ]},
    {"section": "Guides", "path_patterns": [
        r"/guide/", r"/guides/", r"/tutorial/", r"/tutorials/",
        r"/how-?to/", r"/walkthrough/", r"/getting-started",
    ], "content_patterns": [
        r"^#{1,2}\s+(?:Step \d|Tutorial|How to)",
        r"(?:in this (?:tutorial|guide))",
    ]},
    {"section": "Blog", "path_patterns": [
        r"/blog/", r"/_posts/", r"/articles/", r"/news/",
        r"/changelog/", r"/release-notes?/",
    ], "content_patterns": []},
    {"section": "Examples", "path_patterns": [
        r"/examples?/", r"/samples?/", r"/quickstart/",
        r"/starter/", r"/demo/", r"/recipes?/",
    ], "content_patterns": []},
]

# Matches YAML front matter delimited by "---" at the start of a file
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
# Matches a top-level heading (# Title) — used to extract page titles
HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def detect_platform(project_root, docs_dir=None):
    search_dirs = [project_root]
    if docs_dir:
        current = os.path.abspath(docs_dir)
        while current != project_root and current != os.path.dirname(current):
            search_dirs.append(current)
            current = os.path.dirname(current)

    for search_dir in search_dirs:
        for platform, config_files in PLATFORM_CONFIGS.items():
            for config in config_files:
                config_path = os.path.join(search_dir, config)
                if os.path.exists(config_path):
                    return platform, config_path
    return None, None


def extract_base_url(platform, config_path):
    if not config_path or not os.path.isfile(config_path):
        return None

    try:
        with open(config_path, "r", errors="replace") as f:
            content = f.read()
    except OSError:
        return None

    if platform == "mintlify":
        match = re.search(r'"url"\s*:\s*"([^"]+)"', content)
        if match:
            return match.group(1).rstrip("/")

    if platform == "docusaurus":
        match = re.search(r"url\s*[:=]\s*['\"]([^'\"]+)", content)
        if match:
            return match.group(1).rstrip("/")

    if platform == "mkdocs":
        match = re.search(r"site_url\s*:\s*(.+)", content)
        if match:
            return match.group(1).strip().strip("'\"").rstrip("/")

    if platform == "gitbook":
        # Gitbook config does not reliably contain a base URL
        return None

    if platform == "astro_starlight":
        match = re.search(r"site\s*:\s*['\"]([^'\"]+)", content)
        if match:
            return match.group(1).rstrip("/")

    if platform == "vitepress":
        # Vitepress base path is not a full URL
        return None

    return None


def extract_project_name(project_root, docs_dir=None):
    name, desc, url = "", "", ""

    # 1. Try README.md (most human-readable project name)
    for readme_loc in [project_root, docs_dir]:
        if not readme_loc:
            continue
        readme_path = os.path.join(readme_loc, "README.md")
        if os.path.isfile(readme_path):
            try:
                with open(readme_path, "r", errors="replace") as f:
                    content = f.read(4000)
                match = HEADING_RE.search(content)
                if match:
                    name = match.group(1).strip()
                lines = content.split("\n")
                for line in lines:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#") and not stripped.startswith("---") and len(stripped) > 20:
                        desc = stripped
                        break
                if name:
                    break
            except OSError:
                pass

    # 2. Try platform config for title (Astro site title, etc.)
    if docs_dir:
        for config_name in ["astro.config.mjs", "astro.config.ts", "docusaurus.config.js", "docusaurus.config.ts"]:
            # Check docs_dir and parents
            current = os.path.abspath(docs_dir)
            for _ in range(5):
                config_path = os.path.join(current, config_name)
                if os.path.isfile(config_path):
                    try:
                        with open(config_path, "r", errors="replace") as f:
                            config_content = f.read(5000)
                        title_match = re.search(r"title\s*:\s*['\"]([^'\"]+)", config_content)
                        if title_match and not name:
                            name = title_match.group(1).strip()
                    except OSError:
                        pass
                    break
                parent = os.path.dirname(current)
                if parent == current:
                    break
                current = parent

    # 3. Try package.json (fallback — often has technical names like "next-firebase-saas-kit")
    pkg_path = os.path.join(project_root, "package.json")
    if os.path.isfile(pkg_path):
        try:
            with open(pkg_path, "r") as f:
                pkg = json.load(f)
            if not name:
                name = pkg.get("name", "")
            if not desc:
                desc = pkg.get("description", "")
            if not url:
                url = pkg.get("homepage", "")
        except (json.JSONDecodeError, OSError):
            pass

    if not name:
        name = os.path.basename(project_root)

    return name, desc, url


def find_doc_files(docs_dir, max_files):
    files = []
    for dirpath, dirnames, filenames in os.walk(docs_dir):
        dirnames[:] = [
            d for d in dirnames
            if d not in {"node_modules", ".git", "vendor", "dist", "build", ".next", ".vitepress"}
        ]
        for f in sorted(filenames):
            if f.endswith((".md", ".mdx")) and not f.startswith("."):
                files.append(os.path.join(dirpath, f))
                if len(files) >= max_files:
                    return files, True
    return files, False


def extract_page_info(filepath):
    try:
        with open(filepath, "r", errors="replace") as f:
            content = f.read(5000)
    except OSError:
        return None, None, 0

    full_size = os.path.getsize(filepath)
    title = None
    description = None

    fm_match = FRONTMATTER_RE.match(content)
    if fm_match:
        fm_text = fm_match.group(1)
        title_match = re.search(r"^title\s*:\s*['\"]?(.+?)['\"]?\s*$", fm_text, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
        desc_match = re.search(r"^description\s*:\s*['\"]?(.+?)['\"]?\s*$", fm_text, re.MULTILINE)
        if desc_match:
            description = desc_match.group(1).strip()

    if not title:
        h1_match = HEADING_RE.search(content)
        if h1_match:
            title = h1_match.group(1).strip()

    if not title:
        title = os.path.splitext(os.path.basename(filepath))[0].replace("-", " ").replace("_", " ").title()

    if not description:
        text_after_heading = content
        if fm_match:
            text_after_heading = content[fm_match.end():]
        for line in text_after_heading.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("```") and len(stripped) > 20:
                description = stripped[:200]
                break

    return title, description or "", full_size


def classify_page(filepath, docs_dir):
    rel_path = os.path.relpath(filepath, docs_dir).lower()

    for rule in CLASSIFICATION_RULES:
        for pattern in rule["path_patterns"]:
            if re.search(pattern, "/" + rel_path):
                return rule["section"]

    return "Docs"


def filepath_to_url(filepath, docs_dir, base_url, platform):
    rel = os.path.relpath(filepath, docs_dir)
    rel = rel.replace("\\", "/")

    name, ext = os.path.splitext(rel)
    if name.endswith("/index") or name == "index":
        name = name.rsplit("/index", 1)[0] or ""

    url_path = name.replace(" ", "-").lower()
    url_path = "/".join(
        re.sub(r"^\d+-", "", segment) for segment in url_path.split("/")
    )

    if base_url:
        return f"{base_url}/{url_path}".rstrip("/")
    return rel


def prioritize_pages(pages):
    priority_keywords = ["getting-started", "quickstart", "installation", "overview", "introduction", "index", "readme"]

    def sort_key(page):
        lower = page["rel_path"].lower()
        for i, kw in enumerate(priority_keywords):
            if kw in lower:
                return (0, i, lower)
        return (1, 0, lower)

    return sorted(pages, key=sort_key)


def main():
    args = sys.argv[1:]
    docs_dir = None
    base_url = None
    generate_full = False
    force_platform = None

    i = 0
    while i < len(args):
        if args[i] == "--base-url" and i + 1 < len(args):
            base_url = args[i + 1].rstrip("/")
            if not re.match(r"^https?://", base_url):
                print(json.dumps({"error": "invalid_base_url",
                                  "message": "Base URL must start with http:// or https://"}))
                sys.exit(1)
            i += 2
            continue
        if args[i] == "--platform" and i + 1 < len(args):
            force_platform = args[i + 1]
            i += 2
            continue
        if args[i] == "--full":
            generate_full = True
            i += 1
            continue
        if not args[i].startswith("-") and not docs_dir:
            docs_dir = args[i]
        i += 1

    project_root = os.getcwd()

    if not docs_dir:
        for candidate in ["docs", "_docs", "content", "src/content/docs", "src/pages/docs", "pages/docs"]:
            if os.path.isdir(candidate):
                docs_dir = candidate
                break
        if not docs_dir:
            if os.path.isfile("README.md"):
                docs_dir = "."
            else:
                print(json.dumps({
                    "error": "no_docs_found",
                    "message": "No documentation directory found. Tried: docs/, _docs/, content/. Pass a directory as argument."
                }))
                sys.exit(1)

    if not os.path.isdir(docs_dir):
        print(json.dumps({"error": "not_a_directory", "message": f"'{docs_dir}' is not a directory."}))
        sys.exit(1)

    if force_platform:
        platform = force_platform
        config_path = None
    else:
        platform, config_path = detect_platform(project_root, docs_dir)
    if not base_url and platform and config_path:
        base_url = extract_base_url(platform, config_path)

    project_name, project_desc, project_url = extract_project_name(project_root, docs_dir)
    if not project_name:
        project_name = os.path.basename(project_root)

    doc_files, truncated = find_doc_files(docs_dir, MAX_FILES)
    if not doc_files:
        print(json.dumps({
            "error": "no_docs_found",
            "message": f"No .md/.mdx files found in '{docs_dir}'."
        }))
        sys.exit(1)

    sections = {}
    total_size = 0

    for filepath in doc_files:
        title, description, file_size = extract_page_info(filepath)
        if not title:
            continue

        section = classify_page(filepath, docs_dir)
        rel_path = os.path.relpath(filepath, docs_dir)
        url = filepath_to_url(filepath, docs_dir, base_url, platform)
        total_size += file_size

        page = {
            "title": title,
            "description": description,
            "url": url,
            "rel_path": rel_path,
            "file_size": file_size,
        }

        sections.setdefault(section, []).append(page)

    section_order = ["Docs", "API", "Guides", "Blog", "Examples"]
    ordered_sections = {}
    for sec in section_order:
        if sec in sections:
            ordered_sections[sec] = prioritize_pages(sections[sec])

    can_generate_full = (
        generate_full
        and len(doc_files) <= MAX_FULL_FILES
        and total_size <= MAX_FULL_SIZE_KB * 1024
    )

    full_warning = None
    if generate_full and not can_generate_full:
        reasons = []
        if len(doc_files) > MAX_FULL_FILES:
            reasons.append(f"{len(doc_files)} files exceeds limit of {MAX_FULL_FILES}")
        if total_size > MAX_FULL_SIZE_KB * 1024:
            reasons.append(f"{total_size // 1024}KB exceeds limit of {MAX_FULL_SIZE_KB}KB")
        full_warning = f"Cannot generate llms-full.txt: {'; '.join(reasons)}"

    result = {
        "project_name": project_name,
        "project_description": project_desc,
        "project_url": project_url or base_url or "",
        "docs_directory": docs_dir,
        "platform_detected": platform,
        "base_url": base_url,
        "total_files": len(doc_files),
        "total_size_kb": round(total_size / 1024),
        "files_truncated": truncated,
        "sections": ordered_sections,
        "can_generate_full": can_generate_full,
        "full_warning": full_warning,
        "full_files": [os.path.relpath(f, docs_dir) for f in doc_files] if can_generate_full else [],
    }

    print(json.dumps(result, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
