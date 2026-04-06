# Skill Critiques

Per-skill quality reviews and cross-cutting analysis for ekline-docs-skills v3.0.0.

Each file contains findings organized by severity: **Critical** (bugs / broken behavior), **Medium** (consistency / correctness), and **Low** (polish / edge cases). The `_overview.md` file covers cross-cutting concerns.

## Files

| File | Covers |
|------|--------|
| [_overview.md](_overview.md) | Cross-skill consistency, test gaps, architecture |
| [readability.md](readability.md) | Flesch-Kincaid scoring, syllable counting, passive voice |
| [accessibility.md](accessibility.md) | Alt text, heading hierarchy, link text, color refs |
| [content-audit.md](content-audit.md) | Duplicates, thin pages, orphans, frontmatter |
| [docs-health.md](docs-health.md) | Orchestrator, scoring weights, sampling |
| [check-links.md](check-links.md) | Link extraction, anchor validation, external checks |
| [docs-freshness.md](docs-freshness.md) | Git diff analysis, staleness detection |
| [docs-coverage.md](docs-coverage.md) | Export scanning, doc matching, multi-language |
| [changelog.md](changelog.md) | Commit parsing, categorization, deduplication |
| [llms-txt.md](llms-txt.md) | Platform detection, page classification |
| [review-docs.md](review-docs.md) | EkLine CLI wrapper, external dependency |
| [style-guide.md](style-guide.md) | Reference-only skill, enforcement gap |
| [terminology.md](terminology.md) | Reference-only skill, context-dependent rules |
