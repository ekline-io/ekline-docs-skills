"""Shared constants across all ekline-docs-skills scripts.

New scripts should import from here. Existing scripts will be migrated
gradually — do not refactor all at once.
"""

# Default cap on documentation files to scan. Override per-skill only when
# justified (e.g., content-audit pairwise comparison, docs-coverage dual scan).
MAX_DOC_FILES = 200

# Directories to skip when walking file trees
EXCLUDE_DIRS = frozenset({
    "node_modules", ".git", "vendor", "dist", "build",
    ".next", "__pycache__", ".claude",
})

# Documentation file extensions
DOC_EXTENSIONS = (".md", ".mdx")
