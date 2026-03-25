---
name: docs-coverage
description: Measure documentation coverage by analyzing your codebase for exported functions, classes, API endpoints, and CLI commands, then checking if corresponding documentation exists. Reports coverage percentage and lists undocumented items. Use this skill to identify documentation gaps or set coverage targets.
allowed-tools: Read, Glob, Grep, Bash
metadata:
  argument-hint: "[source_directory] [docs_directory]"
---

# Documentation coverage

Measure what percentage of your public API surface is documented.

## Inputs

- `$ARGUMENTS` — optional source directory and docs directory (defaults detected automatically)

## Steps

### 1. Detect project type and structure

Identify the project's language and framework:

```
Glob: **/*.ts, **/*.tsx → TypeScript
Glob: **/*.py → Python
Glob: **/*.go → Go
Glob: **/*.rs → Rust
Glob: **/*.java → Java
```

Also detect the docs directory:
```
Glob: docs/**/*.md
Glob: _docs/**/*.md
Glob: content/**/*.md
```

Exclude `node_modules`, `.git`, `vendor`, `dist`, `build`, `__pycache__` from all scans.

### 2. Extract public API surface

Scan source code for items that should be documented. What counts as "public" depends on the language:

**TypeScript/JavaScript:**
```
Grep: ^export\s+(function|const|class|interface|type|enum)\s+(\w+)
Grep: ^export\s+default\s+(function|class)\s*(\w*)
Grep: module\.exports
```

Also identify:
- API route handlers: `app.get(`, `app.post(`, `router.get(`, `router.post(`
- React components: `export function/const` in `.tsx` files
- CLI commands: argument parser definitions, `yargs`, `commander` definitions
- Configuration options: env var reads, config schema definitions

**Python:**
```
Grep: ^def\s+[a-z]\w+  (public functions — not starting with _)
Grep: ^class\s+\w+
Grep: ^@app\.(get|post|put|delete|patch)
Grep: ^@router\.(get|post|put|delete|patch)
```

**Go:**
```
Grep: ^func\s+[A-Z]\w+  (exported functions start with uppercase)
Grep: ^type\s+[A-Z]\w+\s+(struct|interface)
```

For each item, record:
- Name
- Type (function, class, endpoint, component, config, CLI command)
- File path and line number
- Signature (parameters, return type if available)

### 3. Search documentation for coverage

For each public API item, search the docs:

```
Grep: "{function_name}" in docs/**/*.md
Grep: "{class_name}" in docs/**/*.md
Grep: "{endpoint_path}" in docs/**/*.md
```

An item is considered **documented** if:
- Its name appears in a documentation file (in a heading, code block, or prose)
- OR it has inline documentation (JSDoc, docstring, GoDoc) of 3+ lines

An item is considered **partially documented** if:
- It only has a brief inline comment (1-2 lines)
- OR it is mentioned in docs but without usage examples or parameter descriptions

An item is considered **undocumented** if:
- No mention in documentation files
- No inline documentation

### 4. Calculate coverage

Compute coverage by category:

```yaml
coverage:
  overall: 72%
  by_type:
    functions: 68% (34/50)
    classes: 85% (17/20)
    api_endpoints: 90% (9/10)
    components: 60% (12/20)
    cli_commands: 50% (3/6)
    config_options: 40% (8/20)
  by_directory:
    src/auth/: 90%
    src/api/: 85%
    src/utils/: 45%
    src/components/: 60%
```

### 5. Present the coverage report

```
Documentation Coverage Report
=============================
Project: my-project (TypeScript)
Source: src/ | Docs: docs/

Overall Coverage: 72% (83/116 items documented)

BY TYPE:
  API endpoints    ████████████████████ 90% (9/10)
  Classes          █████████████████░░░ 85% (17/20)
  Functions        █████████████░░░░░░░ 68% (34/50)
  Components       ████████████░░░░░░░░ 60% (12/20)
  CLI commands     ██████████░░░░░░░░░░ 50% (3/6)
  Config options   ████████░░░░░░░░░░░░ 40% (8/20)

BY DIRECTORY:
  src/auth/        ████████████████████ 90%
  src/api/         █████████████████░░░ 85%
  src/components/  ████████████░░░░░░░░ 60%
  src/utils/       █████████░░░░░░░░░░░ 45%

UNDOCUMENTED (high priority — exported, no docs):
  src/utils/retry.ts:15        → retryWithBackoff(fn, options)
  src/utils/cache.ts:8         → createCacheKey(params)
  src/auth/middleware.ts:42    → requireRole(role)
  src/config.ts:20             → REDIS_URL (env var)
  src/config.ts:21             → CACHE_TTL (env var)
  src/config.ts:22             → MAX_RETRIES (env var)

PARTIALLY DOCUMENTED (has brief inline docs only):
  src/api/users.ts:30          → GET /api/users — has JSDoc but no docs page
  src/components/Modal.tsx:12  → Modal — has props type but no usage guide

WELL DOCUMENTED:
  src/auth/login.ts:10         → login() — docs/auth/login.md + JSDoc
  src/api/health.ts:5          → GET /health — docs/api/health.md
```

### 6. Suggest documentation priorities

Based on the report, recommend what to document first:

Priority order:
1. **Public API endpoints** without docs (users depend on these directly)
2. **Exported functions** used by other modules (high coupling)
3. **Configuration options** (users need these to deploy)
4. **CLI commands** (users interact with these directly)
5. **React components** (other developers compose with these)
6. **Utility functions** (lower priority unless widely imported)

For each high-priority undocumented item, offer to:
1. **Generate a documentation stub** — create a doc file with the function signature, parameters, return type, and placeholder sections
2. **Add inline docs** — add JSDoc/docstring to the source code
3. **Skip** — leave for manual documentation

### 7. Track over time (optional)

If the user wants to track coverage over time, offer to:
- Write a `.docs-coverage.json` file with the current metrics
- Compare against previous runs to show improvement or regression
- Suggest adding a coverage check to CI (fail if coverage drops below a threshold)
