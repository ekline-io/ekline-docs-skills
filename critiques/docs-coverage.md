# Critique: docs-coverage

**Script:** `skills/docs-coverage/scripts/scan_exports.py`
**Tests:** None
**Overall:** Ambitious multi-language export scanner. Works well for common patterns but has gaps in endpoint detection and doc matching.

---

## Critical

### No tests for the most language-sensitive script

scan_exports.py (550 lines) detects exports across TypeScript, Python, and Go using regex. Regex-based code analysis is fragile — one missed pattern or false positive breaks the coverage report.

**Action:** Write tests for each language covering:
- Named exports, default exports, re-exports (TypeScript)
- `__all__`, class/function definitions, `@app.route` (Python)
- Capitalized functions, exported variables, interfaces (Go)
- Endpoint detection (Express, Flask, FastAPI)
- JSDoc / docstring detection
- False positive rejection (internal functions, test helpers)

---

## Medium

### JSDoc detection looks backward incorrectly

Line ~125-137: `has_jsdoc()` scans backward from the export line looking for `/**`. But it doesn't verify the JSDoc comment is attached to the correct symbol. A comment above function A could be counted as JSDoc for function B below it.

**Action:** Check that the JSDoc comment is immediately above the target (no blank lines or other code between them).

### TypeScript endpoint patterns miss common setups

Line ~69: Pattern `(?:app|router)\.\s*(get|post|...)` misses:
- Mounted routers: `app.use('/api', router)` — endpoints under `/api/` are invisible
- Variable routers: `const api = express.Router()` then `api.get('/users', ...)`
- NestJS decorators: `@Get('/users')`, `@Post('/users')`
- tRPC: `t.router({ users: t.procedure.query(...) })`

**Action:** Add NestJS decorator patterns at minimum (widely used). Document unsupported frameworks.

### Python endpoint detection gaps

Lines ~210-232: Detects `@app.route()` and `@app.get()` for Flask/FastAPI. Missing:
- Django URL patterns: `path('api/users/', views.user_list)`
- Starlette routes: `Route('/api/users', endpoint=user_list)`
- `@blueprint.route()` (Flask blueprints)

**Action:** Add Django `path()` and `urlpatterns` detection (Django is the most popular Python web framework).

### Doc search produces false positives

Line ~322-325: Searching for a function name in docs uses regex that matches the name anywhere, including:
- Comments about the function in another function's docs
- Changelog entries mentioning the function
- Example code that calls the function

**Action:** Require the function name to appear in a heading, code block, or definition context rather than anywhere in the file.

---

## Low

### Go interfaces not detected as public API

Go interfaces (e.g., `type Reader interface { ... }`) are public API when capitalized, but the script only detects functions and variables.

**Action:** Add Go interface detection.

### "Partially documented" status is confusing

A symbol with inline JSDoc/docstring but no dedicated doc page is marked "partially documented." Users may not understand whether this is good or bad.

**Action:** Clarify in the output: "Has inline docs (JSDoc/docstring) but no dedicated documentation page."

### Docs type heuristic can misclassify

Line ~511: Classifies docs as "API reference" vs. "product docs" based on code mention density. A tutorial with many code examples could be misclassified.

**Action:** Use a more robust heuristic (check for OpenAPI specs, dedicated `/api/` directory, file naming patterns).
