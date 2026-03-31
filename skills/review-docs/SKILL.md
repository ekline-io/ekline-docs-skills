---
name: review-docs
description: Run EkLine Docs Reviewer on documentation files and apply the recommended fixes. Use this skill when reviewing technical documentation for style and best practices, or after creating or writing technical documentation.
metadata:
  author: EkLine
  version: "2.0.0"
  argument-hint: "[content_directory or file1 file2 ...]"
---

Review documentation files using EkLine Docs Reviewer and apply the recommended fixes.

## Inputs

- `$ARGUMENTS` — one or more specific files, or a content directory to review (defaults to `.` if not provided)

## Steps

### 1. Run the review script

Run the helper script, passing through the user's arguments:

```bash
python scripts/run_review.py $ARGUMENTS
```

The script handles all prerequisite checks, CLI invocation, and cleanup. It prints a JSON summary to stdout with these fields:

- `mode` — `"files"`, `"git_changes"`, or `"full"`
- `output_format` — `"jsonl"` or `"patch"`
- `results` — the full contents of the review output (JSONL lines or patch text)
- `cli_exit_code` — exit code from ekline-cli
- `error` / `message` — present if something went wrong

If the script exits with a non-zero status, check the JSON output:

- `"cli_not_found"` — tell the user to install ekline-cli or set `EKLINE_CLI`:
  - **macOS:** `curl -L https://github.com/ekline-io/ekline-cli-binaries/releases/latest/download/ekline-cli-macos.tar.gz | tar xz && chmod +x ekline-cli && sudo mv ekline-cli /usr/local/bin/`
  - **Linux:** `curl -L https://github.com/ekline-io/ekline-cli-binaries/releases/latest/download/ekline-cli-linux.tar.gz | tar xz && chmod +x ekline-cli && sudo mv ekline-cli /usr/local/bin/`
  - **Windows:** Download `ekline-cli-windows.zip` from the [Release Page](https://github.com/ekline-io/ekline-cli-binaries/releases/latest) and add to your PATH
- `"token_not_found"` — tell the user to set `EKLINE_EK_TOKEN` or `EK_TOKEN` (token from <https://ekline.io/dashboard>)
- `"cli_failed"` — show the error message from `cli_stderr`

### 2. Parse and present findings

Parse the `results` field from the JSON summary.

**If `output_format` is `"patch"` (git changes mode):**

Parse the patch text and present a summary to the user:

- Total number of suggested changes
- Which files are affected
- A description of each change

**If `output_format` is `"jsonl"` (file or full review mode):**

Parse each line of the `results` field as a JSON object representing an issue found.

Present a summary to the user:

- Total number of issues found
- Breakdown by category (style, grammar, terminology, structure)
- List the issues grouped by file, showing:
  - File path and line number
  - Rule ID (e.g., EK00037)
  - Description of the issue
  - The AI suggestion for fixing it (if available)

### 3. Apply fixes

**If a `.patch` file was produced:**

Read and interpret the patch file. For each hunk, identify the target file, the original lines, and the suggested replacement. Present each change to the user with context, then ask if they want to:

1. **Apply all changes** — use the Edit tool to apply every suggested change from the patch
2. **Review one by one** — go through each change and let the user accept or skip
3. **Skip** — discard the patch

**If a `.jsonl` file was produced:**

Ask the user if they want to:

1. **Apply all fixes** — apply every AI suggestion automatically
2. **Review one by one** — go through each fix and let the user accept or skip
3. **Apply fixes for a specific category only** (e.g., only grammar fixes)
4. **Skip** — just leave the report as-is

When applying fixes from JSONL, use the Edit tool to make the changes in each file. For each fix:

- Read the file
- Apply the suggested replacement at the indicated line
- Confirm the change was made

After applying fixes (in either mode), re-run the review script to verify the fixes resolved the issues and no new issues were introduced.

### 4. Clean up

The script automatically removes the temporary output file, so no cleanup is needed.
