---
name: style-guide
description: Enforces documentation style, voice, and tone consistency. Validates against style rules and existing documentation patterns. Run this skill proactively whenever documentation files (.md, .mdx, .rst, .adoc, .txt, .html) are created or modified.
allowed-tools: Read, Glob, Grep
metadata:
  author: EkLine
  version: "2.0.0"
---

# Style Guide Skill

Ensure consistent voice, tone, and style across all documentation.

## Core Style Rules

Reference: [references/style-rules.md](references/style-rules.md)

### Voice and Tone

| Aspect | Requirement | Example |
|--------|-------------|---------|
| Voice | Active | "The function returns..." ✅ / "...is returned" ❌ |
| Person | Second (you/your) | "You can configure..." ✅ / "Users can..." ❌ |
| Tense | Present | "This creates..." ✅ / "This will create..." ❌ |
| Lead | Verb-first | "Install the CLI" ✅ / "You should install..." ❌ |

### Banned Phrases

These phrases are NEVER allowed:

- "Please note that..."
- "It's worth mentioning..."
- "In order to..." (use "To...")
- "Basically...", "Simply...", "Just..."
- "We are happy to announce..."
- "In this section we will..."
- "Easy", "easily" (subjective)

### Formatting Rules

| Element | Rule |
|---------|------|
| Headings | Sentence case ("Getting started" not "Getting Started") |
| Code blocks | Always specify language |
| Lists | Numbered for sequences, bullets for non-sequential |
| Tables | Use for parameters, options, comparisons |

## Style Profile Schema

When detecting patterns, use the following structure:

```json
{
  "source_files_analyzed": 3,
  "detected_patterns": {
    "voice": "active | passive | mixed",
    "person": "first | second | third | mixed",
    "heading_style": "sentence | title | lowercase",
    "list_style": "bullets | numbers | both",
    "code_block_style": "fenced | indented"
  },
  "matches_rules": true | false,
  "deviations_from_rules": ["list of differences"]
}
```

Present the findings in a user-friendly manner.

## Compliance Report Schema

When validating content, use the following structure:

```json
{
  "compliant": true | false,
  "score": 85,
  "violations": [
    {
      "rule": "active_voice",
      "location": "line 42",
      "found": "The configuration is loaded by the system",
      "suggestion": "The system loads the configuration",
      "severity": "high | medium | low"
    }
  ],
  "terminology_issues": [],
  "formatting_issues": [],
  "summary": {
    "high_severity": 0,
    "medium_severity": 2,
    "low_severity": 5
  }
}
```

Present the findings in a user-friendly manner.

## Checking Workflow

```text
Content to validate
        │
        ▼
┌───────────────────┐
│  Voice Check      │ → Is it active voice?
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  Banned Phrases   │ → Any prohibited words?
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  Terminology      │ → Consistent terms? (invoke terminology skill)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  Formatting       │ → Proper structure?
└───────────────────┘
        │
        ▼
   Compliance Report
```

## Integration Points

- **Rules reference**: [references/style-rules.md](references/style-rules.md)

## Auto-Fix Capabilities

Some violations can be auto-fixed:

| Violation | Auto-Fix |
|-----------|----------|
| "In order to..." | Replace with "To..." |
| "Please note that..." | Remove phrase |
| Title case headings | Convert to sentence case |

Other violations require manual review:

- Passive voice (context-dependent)
- Missing sections (content needed)
- Technical inaccuracies (verification needed)
