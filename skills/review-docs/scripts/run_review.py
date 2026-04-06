#!/usr/bin/env python3
"""Run EkLine Docs Reviewer and output results.

Handles prerequisite checks, determines the review mode (specific files,
git changes, or full directory), invokes the CLI, and prints a JSON summary
to stdout for the calling skill to interpret.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile


def find_cli():
    """Return the path to ekline-cli, or None."""
    env_path = os.environ.get("EKLINE_CLI")
    if env_path and os.path.isfile(env_path):
        return env_path
    return shutil.which("ekline-cli")


def find_token():
    """Return the EkLine token, or None."""
    return os.environ.get("EKLINE_EK_TOKEN") or os.environ.get("EK_TOKEN")


def has_git_changes(directory):
    """Check if directory is in a git repo with uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=directory,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except FileNotFoundError:
        return False


def resolve_content_directory(args):
    """Determine the content directory from arguments.

    Returns the directory path, falling back to ekline.config.json's
    contentDirectory or '.' if nothing else is specified.
    """
    if args and os.path.isdir(args[0]):
        return args[0]
    if os.path.isfile("ekline.config.json"):
        try:
            with open("ekline.config.json") as f:
                config = json.load(f)
            dirs = config.get("contentDirectory")
            if isinstance(dirs, list) and dirs:
                return dirs[0]
            if isinstance(dirs, str):
                return dirs
        except (json.JSONDecodeError, OSError):
            pass
    return "."


def common_directory(files):
    """Find the deepest directory that contains all specified files."""
    abs_paths = [os.path.abspath(f) for f in files]
    common = os.path.commonpath(abs_paths)
    if os.path.isfile(common):
        common = os.path.dirname(common)
    return common


def resolve_args(raw_args):
    """Classify arguments as specific files or a content directory."""
    if not raw_args:
        return "directory", [], resolve_content_directory([])

    # Check if all arguments are existing files
    if all(os.path.isfile(a) for a in raw_args):
        content_dir = common_directory(raw_args)
        return "files", raw_args, content_dir

    # Otherwise treat first arg as content directory
    return "directory", [], resolve_content_directory(raw_args)


def build_command(cli, token, mode, files, content_dir, output_path):
    """Build the ekline-cli command list."""
    cmd = [cli, "--ek-token", token, "--ai-suggestions", "-o", output_path]

    if mode == "files":
        cmd += ["--content-directory", content_dir, "--changed-files", ",".join(files)]
    elif mode == "git_changes":
        cmd += ["--content-directory", content_dir, "--changes-from-git"]
    else:
        cmd += ["--content-directory", content_dir]

    return cmd


def main():
    raw_args = sys.argv[1:]

    # --- Prerequisites ---
    cli = find_cli()
    if not cli:
        print(json.dumps({
            "error": "cli_not_found",
            "message": (
                "ekline-cli not found. Install from "
                "https://github.com/ekline-io/ekline-cli-binaries/releases/latest "
                "or set EKLINE_CLI env var. For a similar check without ekline-cli, "
                "try the /docs-health skill."
            ),
        }))
        sys.exit(1)

    token = find_token()
    if not token:
        print(json.dumps({
            "error": "token_not_found",
            "message": "No token found. Set EKLINE_EK_TOKEN or EK_TOKEN.",
        }))
        sys.exit(1)

    # --- Determine review mode ---
    arg_type, files, content_dir = resolve_args(raw_args)

    if arg_type == "files":
        mode = "files"
        output_ext = ".jsonl"
    elif arg_type == "directory" and has_git_changes(content_dir):
        mode = "git_changes"
        output_ext = ".patch"
    else:
        mode = "full"
        output_ext = ".jsonl"

    output_path = os.path.join(
        tempfile.gettempdir(), f"ekline-review-results{output_ext}"
    )

    # --- Run CLI ---
    cmd = build_command(cli, token, mode, files, content_dir, output_path)

    result = subprocess.run(cmd, capture_output=True, text=True)

    # --- Output summary and results ---
    summary = {
        "mode": mode,
        "output_format": output_ext.lstrip("."),
        "content_dir": content_dir,
        "files": files,
        "cli_exit_code": result.returncode,
        "cli_stderr": result.stderr.strip() if result.stderr else None,
    }

    if result.returncode != 0:
        summary["error"] = "cli_failed"
        summary["message"] = result.stderr.strip() if result.stderr else "ekline-cli exited with a non-zero status"

    # Read the output file contents and include in summary
    try:
        with open(output_path) as f:
            summary["results"] = f.read()
    except OSError:
        summary["results"] = None
    finally:
        # Clean up temporary file
        try:
            os.remove(output_path)
        except OSError:
            pass

    print(json.dumps(summary))
    sys.exit(0 if result.returncode == 0 else 1)


if __name__ == "__main__":
    main()
