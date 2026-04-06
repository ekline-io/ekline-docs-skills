"""Shared utility for finding the documentation directory.

All skills should use the same candidate list so users get consistent
behavior regardless of which skill they invoke.
"""

import os

# Ordered list of candidate directories. All skills use the same list.
DOC_DIR_CANDIDATES = [
    "docs", "_docs", "documentation", "content",
    "src/content/docs", "pages/docs", "pages",
]


def find_docs_dir(explicit_dir=None, project_root=None):
    """Find the documentation directory.

    Args:
        explicit_dir: User-provided directory path (takes priority).
        project_root: Project root to search from (defaults to cwd).

    Returns:
        Resolved directory path, or None if not found.
    """
    if explicit_dir and explicit_dir != "auto":
        if os.path.isdir(explicit_dir):
            return explicit_dir
        return None

    root = project_root or os.getcwd()
    for candidate in DOC_DIR_CANDIDATES:
        path = os.path.join(root, candidate)
        if os.path.isdir(path):
            return path

    # Fallback: current directory if it contains doc files
    for f in os.listdir(root):
        if f.endswith((".md", ".mdx")):
            return root

    return None
