---
name: terminology
description: Ensures consistent language and terminology across all documentation. Checks terms against terminology rules and flags inconsistencies. Run this skill proactively whenever documentation files (.md, .mdx, .rst, .adoc, .txt, .html) are created or modified.
allowed-tools: Read, Grep, Glob
metadata:
  author: EkLine
  version: "2.0.0"
---

# Validate Terminology

Check documentation for terminology consistency against approved terms.

**Reference**: [references/terminology-rules.md](references/terminology-rules.md) contains all approved terms, variants to avoid, and formatting rules.

## Terminology Checking Process

### Step 0: Run automated checks

```bash
python scripts/check_terms.py <docs_dir_or_file>
```

Parse the JSON output. The automated checks cover:
- Incorrect term variants (e.g., "NodeJS" → "Node.js")
- Prohibited terms (e.g., "blacklist" → "blocklist")
- Context-dependent terms flagged for review (e.g., "setup" vs "set up")

Use the automated findings as the baseline, then supplement with agent-level checks for context-dependent rules and within-document consistency.

### Step 1: Load Approved Terms

Read [references/terminology-rules.md](references/terminology-rules.md) to get:

- Product and feature names (exact capitalization)
- Technical terms (programming, infrastructure)
- Action verbs (preferred vs avoided)
- UI element terms
- Prohibited terms

### Step 2: Extract Terms from Document

Identify all potentially controlled terms:

- Product/feature names
- Technical concepts
- UI element names
- Code identifiers mentioned in prose
- Action verbs in instructions

### Step 3: Compare Against Approved List

```text
For each term found:
  ├── Is it in the approved list?
  │     YES → Check for exact match (case, spacing)
  │     NO → Flag for review
  │
  └── Does it match a "variant to avoid"?
        YES → Flag as terminology violation
        NO → Continue
```

### Step 4: Check Consistency Within Document

Even if a term isn't in the controlled list:

- Is it used consistently throughout?
- First usage should establish the pattern
- All subsequent uses should match

### Step 5: Return Findings

Internally, create a terminology report with the following structure.

```yaml
terminology_report:
  document: "path/to/file.md"

  violations:
    - term_found: "api-key"
      approved_term: "API key"
      rule_reference: "references/terminology-rules.md#technical-terms"
      locations: ["line 42", "line 87"]
      severity: error

  inconsistencies:
    - term: "config file"
      variants_found: ["config file", "configuration file"]
      locations:
        "config file": ["line 10"]
        "configuration file": ["line 45"]
      recommendation: "Use 'configuration file' consistently"
      severity: warning

  undefined_terms:
    - term: "webhook"
      first_use: "line 23"
      recommendation: "Add definition or link to glossary"
      severity: info

  summary:
    errors: 2
    warnings: 1
    info: 1
    compliant: false
```

Then present the report in a user-friendly way.

## Enforcement Levels

| Level | Trigger | Action |
|-------|---------|--------|
| **Error** | Term contradicts `references/terminology-rules.md` | Must fix before publishing |
| **Warning** | Term inconsistent within document | Should fix |
| **Info** | Term not in controlled list | Verify intent |

## Integration Points

- **Rules reference**: [references/terminology-rules.md](references/terminology-rules.md)

## Common Checks

Quick validation patterns (full lists in [references/terminology-rules.md](references/terminology-rules.md):

```bash
# Check for common violations
Grep: "api-key|API Key|Api Key"     → Should be "API key"
Grep: "NodeJS|node\.js|Nodejs"      → Should be "Node.js"
Grep: "click here"                  → Should be descriptive link text
Grep: "blacklist|whitelist"         → Should be blocklist/allowlist
```
