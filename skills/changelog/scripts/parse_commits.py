#!/usr/bin/env python3
"""Parse git history and produce structured changelog data.

Classifies commits into changelog categories (Added, Changed, Fixed,
Removed, Security, Breaking Changes) using conventional commit prefixes
or keyword heuristics. Outputs a JSON summary for the skill to interpret.

Usage:
    python parse_commits.py [range] [--max-commits N]

Examples:
    python parse_commits.py                     # last tag..HEAD
    python parse_commits.py v1.2.0..v1.3.0      # specific range
    python parse_commits.py HEAD~20..HEAD        # last 20 commits
    python parse_commits.py --max-commits 100    # limit commits
"""

import json
import os
import re
import subprocess
import sys

MAX_COMMITS = 200
MAX_COMMITS_UPPER = 10_000
SEPARATOR = "<<<COMMIT_SEP>>>"
SAFE_RANGE_RE = re.compile(r"^[a-zA-Z0-9_.~^/\-]+(\.\.[a-zA-Z0-9_.~^/\-]+)?$")

CONVENTIONAL_MAP = {
    "feat": "Added",
    "fix": "Fixed",
    "refactor": "Changed",
    "perf": "Changed",
    "docs": "Documentation",
    "style": "skip",
    "test": "skip",
    "chore": "skip",
    "ci": "skip",
    "build": "skip",
}

SKIP_CATEGORIES = {"skip", "Documentation"}

KEYWORD_RULES = [
    (r"\bBREAKING[\s_-]?CHANGE\b", "Breaking Changes"),
    (r"\b(security|vulnerabilit|CVE-)\b", "Security"),
    (r"^(add|implement|introduce|create|support)\b", "Added"),
    (r"^(fix|resolve|patch|correct|handle|repair)\b", "Fixed"),
    (r"^(remove|delete|drop|deprecate|disable)\b", "Removed"),
    (r"^(change|update|modify|refactor|improve|enhance|upgrade|bump|migrate)\b", "Changed"),
]

TICKET_PREFIX = re.compile(r"^[A-Z]+-\d+[:\s]+\s*")


def run_git(args, cwd=None):
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.stdout.strip(), result.returncode


def find_range(user_range):
    if user_range and ".." in user_range:
        return user_range, None

    if user_range and not user_range.startswith("-"):
        prev_tag, rc = run_git(["describe", "--tags", "--abbrev=0", f"{user_range}^"])
        if rc == 0 and prev_tag:
            return f"{prev_tag}..{user_range}", None
        return f"{user_range}~50..{user_range}", None

    latest_tag, rc = run_git(["describe", "--tags", "--abbrev=0"])
    if rc == 0 and latest_tag:
        return f"{latest_tag}..HEAD", None

    return None, None


def get_commits(commit_range, max_commits):
    fmt = f"%H{SEPARATOR}%s{SEPARATOR}%b{SEPARATOR}%an{SEPARATOR}%aI"

    args = ["log", f"--format={fmt}", "--no-merges"]
    if commit_range:
        args.append(commit_range)
    else:
        args.append(f"-{max_commits}")

    raw, rc = run_git(args)
    if rc != 0 or not raw:
        return []

    commits = []
    for line in raw.split("\n"):
        parts = line.split(SEPARATOR)
        if len(parts) < 5:
            continue
        commits.append({
            "hash": parts[0][:8],
            "subject": parts[1].strip(),
            "body": parts[2].strip(),
            "author": parts[3].strip(),
            "date": parts[4].strip(),
        })

    return commits[:max_commits]


def extract_pr_issue_refs(text):
    refs = {"prs": [], "issues": []}
    pr_matches = re.findall(r"(?:^|\s|Merge pull request )#(\d+)", text)
    refs["prs"] = list(set(pr_matches))

    issue_patterns = re.findall(
        r"(?:fix(?:es)?|close[sd]?|resolve[sd]?)\s+#(\d+)", text, re.IGNORECASE
    )
    refs["issues"] = list(set(issue_patterns))
    return refs


def classify_conventional(subject):
    match = re.match(r"^(\w+)(?:\(([^)]*)\))?(!)?:\s*(.+)$", subject)
    if not match:
        return None, None, False

    commit_type = match.group(1).lower()
    scope = match.group(2)
    breaking = match.group(3) == "!"
    description = match.group(4)

    category = CONVENTIONAL_MAP.get(commit_type)
    if not category:
        return None, None, False

    return category, description, breaking


def classify_keyword(subject):
    cleaned = TICKET_PREFIX.sub("", subject).strip()
    lower = cleaned.lower()

    for pattern, category in KEYWORD_RULES:
        if re.search(pattern, lower, re.IGNORECASE):
            return category

    return "Changed"


def classify_commit(commit):
    subject = commit["subject"]
    body = commit.get("body", "")
    full_text = f"{subject}\n{body}"

    category, description, breaking = classify_conventional(subject)

    if category:
        if breaking or re.search(r"BREAKING[\s_-]?CHANGE", full_text):
            return "Breaking Changes", description or subject
        return category, description or subject

    if re.search(r"BREAKING[\s_-]?CHANGE", full_text):
        return "Breaking Changes", subject

    category = classify_keyword(subject)
    return category, subject


def deduplicate(entries):
    seen_subjects = {}
    deduped = []

    for entry in entries:
        normalized = re.sub(r"\s*\(#\d+\)\s*$", "", entry["description"]).lower().strip()
        normalized = re.sub(r"^(feat|fix|refactor|chore|docs|perf|ci|test)(\([^)]*\))?!?:\s*", "", normalized)

        if normalized in seen_subjects:
            existing = seen_subjects[normalized]
            existing["refs"]["prs"].extend(entry["refs"]["prs"])
            existing["refs"]["issues"].extend(entry["refs"]["issues"])
            continue

        seen_subjects[normalized] = entry
        deduped.append(entry)

    return deduped


def format_entry(entry):
    desc = entry["description"]
    desc = re.sub(r"^(feat|fix|refactor|chore|docs|perf|ci|test)(\([^)]*\))?!?:\s*", "", desc)
    desc = re.sub(r"\s*\(#\d+\)\s*$", "", desc)
    desc = desc[0].upper() + desc[1:] if desc else desc

    pr_refs = entry["refs"]["prs"]
    if pr_refs:
        ref_str = ", ".join(f"#{pr}" for pr in sorted(set(pr_refs)))
        desc = f"{desc} ({ref_str})"

    return desc


def main():
    args = sys.argv[1:]
    max_commits = MAX_COMMITS

    user_range = None
    i = 0
    while i < len(args):
        if args[i] == "--max-commits" and i + 1 < len(args):
            try:
                max_commits = int(args[i + 1])
            except ValueError:
                print(json.dumps({"error": "invalid_argument",
                                  "message": "--max-commits must be an integer"}))
                sys.exit(1)
            if max_commits < 1 or max_commits > MAX_COMMITS_UPPER:
                print(json.dumps({"error": "invalid_argument",
                                  "message": f"--max-commits must be between 1 and {MAX_COMMITS_UPPER}"}))
                sys.exit(1)
            i += 2
            continue
        if not user_range:
            if not SAFE_RANGE_RE.match(args[i]):
                print(json.dumps({"error": "invalid_range",
                                  "message": f"Commit range contains invalid characters: {args[i]}"}))
                sys.exit(1)
            user_range = args[i]
        i += 1

    is_git_repo, rc = run_git(["rev-parse", "--git-dir"])
    if rc != 0:
        print(json.dumps({"error": "not_a_git_repo", "message": "Not inside a git repository."}))
        sys.exit(1)

    commit_range, _ = find_range(user_range)

    commits = get_commits(commit_range, max_commits)
    if not commits:
        print(json.dumps({
            "error": "no_commits",
            "message": f"No commits found in range: {commit_range or 'last ' + str(max_commits)}",
            "range": commit_range,
        }))
        sys.exit(1)

    categorized = {}
    skipped = 0

    for commit in commits:
        category, description = classify_commit(commit)

        if category in SKIP_CATEGORIES:
            skipped += 1
            continue

        refs = extract_pr_issue_refs(f"{commit['subject']}\n{commit.get('body', '')}")

        entry = {
            "hash": commit["hash"],
            "description": description,
            "author": commit["author"],
            "date": commit["date"],
            "refs": refs,
            "original_subject": commit["subject"],
        }

        categorized.setdefault(category, []).append(entry)

    category_order = [
        "Breaking Changes", "Added", "Changed", "Fixed", "Removed", "Security",
    ]

    output_categories = {}
    for cat in category_order:
        entries = categorized.get(cat, [])
        if entries:
            deduped = deduplicate(entries)
            output_categories[cat] = [
                {
                    "text": format_entry(e),
                    "hash": e["hash"],
                    "refs": e["refs"],
                }
                for e in deduped
            ]

    total_entries = sum(len(v) for v in output_categories.values())

    result = {
        "range": commit_range or f"last {max_commits} commits",
        "total_commits_analyzed": len(commits),
        "total_skipped": skipped,
        "total_changelog_entries": total_entries,
        "categories": output_categories,
    }

    print(json.dumps(result, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
