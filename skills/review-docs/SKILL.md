---
name: review-docs
description: Run EkLine Docs Reviewer on documentation files and apply the recommended fixes. Use this skill when reviewing technical documentation for style and best practices, or after creating or writing technical documentation.
metadata:
  author: EkLine
  version: "3.0.1"
  tier: ekline
  argument-hint: "[content_directory or file1 file2 ...]"
---

Review documentation with EkLine Docs Reviewer, evaluate each suggestion critically, and apply only the improvements that hold up.

> **Requirements (EkLine power-up):** This skill needs the `ekline-cli` binary and an EkLine token (`EKLINE_EK_TOKEN` or `EK_TOKEN`). See [EkLine CLI & token setup](https://github.com/ekline-io/ekline-docs-skills/blob/main/docs/install/ekline-cli.md) for setup. Every other skill in this toolkit runs with no EkLine account.

## Inputs

- `$ARGUMENTS` — optional. One or more specific files, or a content directory to review.
  - **No arguments** — reviews the pending git changes in the current repo, or the full directory if the repo is clean.
  - **A directory** — reviews that directory.
  - **Specific files** — reviews just those files.

## Workflow

### 1. Run the review script

Run the helper script, passing through the user's arguments:

```bash
python scripts/run_review.py $ARGUMENTS
```

The script handles prerequisite checks, mode selection, CLI invocation, and cleanup. It prints a JSON summary to stdout with these fields:

- `mode` — `"files"`, `"git_changes"`, or `"full"`
- `output_format` — `"jsonl"` or `"patch"`
- `results` — the full review output (JSONL lines or patch text)
- `cli_exit_code` — exit code from `ekline-cli`
- `error` / `message` / `cli_stderr` — present only when something went wrong

If the script exits non-zero, read `error` and respond per the table below — do **not** proceed to evaluation.

| `error` | What to tell the user |
|---------|-----------------------|
| `cli_not_found` | `ekline-cli` isn't installed. Set `EKLINE_CLI` to its path, or install it (see below). |
| `token_not_found` | No auth token. Set `EKLINE_EK_TOKEN` or `EK_TOKEN` (token from <https://ekline.io/dashboard>). |
| `cli_failed` | The CLI failed — show the message from `cli_stderr` and suggest troubleshooting. |
| _(no error, empty `results`)_ | "No issues found." Nothing to apply. |

Install commands for `cli_not_found`:

- **macOS:** `curl -L https://github.com/ekline-io/ekline-cli-binaries/releases/latest/download/ekline-cli-macos.tar.gz | tar xz && chmod +x ekline-cli && sudo mv ekline-cli /usr/local/bin/`
- **Linux:** `curl -L https://github.com/ekline-io/ekline-cli-binaries/releases/latest/download/ekline-cli-linux.tar.gz | tar xz && chmod +x ekline-cli && sudo mv ekline-cli /usr/local/bin/`
- **Windows:** Download `ekline-cli-windows.zip` from the [Release Page](https://github.com/ekline-io/ekline-cli-binaries/releases/latest) and add it to your `PATH`.

### 2. Evaluate each suggestion

The review output is a set of style suggestions — not orders. Judge each one before presenting or applying it.

**Accept when the suggestion:**

- Improves clarity without changing meaning
- Fixes grammar or typos
- Converts passive voice to active voice
- Removes banned phrases ("simply", "just", "easy", "obviously", "basically", "please note that", "in order to", "click here")
- Fixes formatting — heading case, code block languages, and list parallelism
- Improves sentence structure

**Reject when the suggestion:**

- Changes technical meaning or accuracy
- Removes important context or nuance
- Introduces phrasing more awkward than the original
- Conflicts with project-specific terminology
- Over-simplifies a complex technical concept
- Would change content inside a code block — code blocks are out of scope

**When uncertain:** err toward clarity improvements, but reject any change that feels off even if the reason is hard to articulate. Surface rejected suggestions so the user can override.

### 3. Present the findings

**If `output_format` is `"patch"` (git-changes mode):** parse the unified diff and summarize — total suggested changes, which files are affected, and a one-line description of each change.

**If `output_format` is `"jsonl"` (files or full mode):** parse each line as a JSON issue and summarize — the total issue count, a breakdown by category such as style, grammar, terminology, and structure, and the issues grouped by file. For each issue, show the path and line, the rule ID such as `EK00037`, the issue, and the AI suggestion when available.

### 4. Apply approved fixes

Ask the user how to proceed:

1. **Apply all accepted changes** — apply every suggestion you accepted in step 2.
2. **Review one by one** — walk through each change; the user accepts or skips.
3. **Apply one category only** — JSONL mode; for example, grammar fixes only.
4. **Skip** — leave the report as-is.

When applying, use the `Edit` tool to make each change surgically:

- Read the current file.
- Match the exact original text and replace only the specific lines the suggestion targets.
- **Never rewrite an entire file.** Only change the lines indicated.
- If an edit fails on a file, skip it, continue with the others, and note the failure in the summary.


### 5. Report back

Summarize the run:

```
## Docs Review Summary

**Mode:** <files | git_changes | full>
**Changes applied:** <count>
**Suggestions rejected:** <count>

### Applied
- `path/to/file.md`: <brief description>

### Rejected
- `path/to/file.md` line <N>: <reason>

### Notes
<recurring patterns, skipped files, or "None.">
```

## Constraints

1. **Never change code blocks.** Style rules apply to prose only.
2. **Preserve technical accuracy.** Reject any suggestion that changes meaning.
3. **Respect intentional formatting.** Tables, diagrams, and structured content exist for a reason.
4. **Edit surgically.** Change only the lines a suggestion targets — never rewrite whole files.
5. **Be transparent.** The summary must list what was applied and what was rejected, with reasons.
6. **Always use the script.** Never invoke `ekline-cli` directly — the script handles binary discovery, auth, mode, and flags.
