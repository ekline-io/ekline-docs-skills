"""Tests for skills/style-guide/scripts/check_style.py."""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

# Add the script directory to sys.path so we can import the module directly.
SCRIPT_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "skills",
    "style-guide",
    "scripts",
)
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

import check_style as c  # noqa: E402

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _run_main(args):
    """Run c.main() with the given argv list and return parsed JSON output."""
    old_argv = sys.argv[:]
    sys.argv = ["check_style.py"] + args
    captured = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured):
            c.main()
    finally:
        sys.argv = old_argv
    return json.loads(captured.getvalue())


def _check_text(text):
    """Write text to a temp file, run check_file, and return findings."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(text)
        path = f.name
    try:
        return c.check_file(path)
    finally:
        os.unlink(path)


def _finding_types(findings):
    return [f["type"] for f in findings]


class TestParseBannedPhrases(unittest.TestCase):
    """Verify parse_banned_phrases() reads the real style-rules.md correctly."""

    def test_returns_non_empty_list(self):
        phrases = c.parse_banned_phrases()
        self.assertIsInstance(phrases, list)
        self.assertGreater(len(phrases), 0)

    def test_each_entry_has_required_keys(self):
        phrases = c.parse_banned_phrases()
        for entry in phrases:
            self.assertIn("phrase", entry, f"Missing 'phrase' key in: {entry}")
            self.assertIn("suggestion", entry, f"Missing 'suggestion' key in: {entry}")

    def test_known_phrase_parsed(self):
        phrases = c.parse_banned_phrases()
        all_phrases = [p["phrase"].lower() for p in phrases]
        self.assertIn("simply", all_phrases)

    def test_known_phrase_in_order_to_parsed(self):
        phrases = c.parse_banned_phrases()
        all_phrases = [p["phrase"].lower() for p in phrases]
        self.assertIn("in order to", all_phrases)

    def test_known_phrase_please_note_parsed(self):
        phrases = c.parse_banned_phrases()
        all_phrases = [p["phrase"].lower() for p in phrases]
        self.assertIn("please note that", all_phrases)


class TestBannedPhraseDetection(unittest.TestCase):
    """check_file() detects banned phrases in normal prose."""

    def test_please_note_that_detected(self):
        findings = _check_text("Please note that you should configure this first.\n")
        self.assertIn("banned_phrase", _finding_types(findings))

    def test_in_order_to_detected(self):
        findings = _check_text("In order to run the server, install the package.\n")
        self.assertIn("banned_phrase", _finding_types(findings))

    def test_simply_detected(self):
        findings = _check_text("Simply run the following command to get started.\n")
        self.assertIn("banned_phrase", _finding_types(findings))

    def test_banned_phrase_case_insensitive(self):
        # "IN ORDER TO" upper-case should still be flagged.
        findings = _check_text("IN ORDER TO configure the database, do this.\n")
        self.assertIn("banned_phrase", _finding_types(findings))

    def test_clean_text_not_flagged(self):
        text = (
            "# Getting started\n\n"
            "Run the following command to install the package.\n\n"
            "Configure the database connection before starting the server.\n"
        )
        findings = _check_text(text)
        self.assertNotIn("banned_phrase", _finding_types(findings))

    def test_finding_includes_suggestion(self):
        findings = _check_text("In order to proceed, read the docs.\n")
        banned = [f for f in findings if f["type"] == "banned_phrase"]
        self.assertTrue(len(banned) > 0)
        self.assertIn("suggestion", banned[0])
        self.assertIn("line", banned[0])
        self.assertIn("message", banned[0])


class TestHeadingCaseDetection(unittest.TestCase):
    """check_file() flags Title Case headings that should be sentence case."""

    def test_title_case_heading_flagged(self):
        # Multiple capitalised content words — Title Case pattern.
        findings = _check_text("## Getting Started With Authentication\n\nSome text.\n")
        self.assertIn("heading_case", _finding_types(findings))

    def test_sentence_case_not_flagged(self):
        findings = _check_text("## Getting started with authentication\n\nSome text.\n")
        self.assertNotIn("heading_case", _finding_types(findings))

    def test_single_word_heading_not_flagged(self):
        # A single capitalised word is fine (it's the first word).
        findings = _check_text("## Overview\n\nSome text.\n")
        self.assertNotIn("heading_case", _finding_types(findings))

    def test_heading_with_proper_noun_not_flagged(self):
        # A heading whose only capital-after-first is a known proper noun pattern
        # with just one extra capitalised word should not be flagged if it doesn't
        # meet the multi-word threshold. This tests boundary tolerance.
        findings = _check_text("## Configure PostgreSQL\n\nSome text.\n")
        # With only two words and one proper noun this should NOT be flagged.
        self.assertNotIn("heading_case", _finding_types(findings))


class TestBareCodeFence(unittest.TestCase):
    """check_file() detects fenced code blocks that have no language specifier."""

    def test_bare_fence_detected(self):
        text = "Some text.\n\n```\ncode without language\n```\n"
        findings = _check_text(text)
        self.assertIn("bare_code_fence", _finding_types(findings))

    def test_fence_with_language_not_flagged(self):
        text = "Some text.\n\n```python\nprint('hello')\n```\n"
        findings = _check_text(text)
        self.assertNotIn("bare_code_fence", _finding_types(findings))

    def test_finding_has_required_fields(self):
        text = "Some text.\n\n```\ncode\n```\n"
        findings = _check_text(text)
        bare = [f for f in findings if f["type"] == "bare_code_fence"]
        self.assertTrue(len(bare) > 0)
        first = bare[0]
        self.assertIn("line", first)
        self.assertIn("severity", first)
        self.assertIn("message", first)


class TestContentExclusion(unittest.TestCase):
    """Banned phrases inside code blocks and frontmatter must NOT be flagged."""

    def test_banned_phrase_inside_code_block_not_flagged(self):
        text = (
            "# Overview\n\n"
            "```python\n"
            "# Simply call the function\n"
            "please_note_that = 'this is a variable'\n"
            "```\n\n"
            "Normal prose here.\n"
        )
        findings = _check_text(text)
        self.assertNotIn("banned_phrase", _finding_types(findings))

    def test_banned_phrase_in_frontmatter_not_flagged(self):
        text = (
            "---\n"
            "description: Simply a test page\n"
            "title: In order to configure\n"
            "---\n\n"
            "# Overview\n\n"
            "Normal prose with no banned phrases.\n"
        )
        findings = _check_text(text)
        self.assertNotIn("banned_phrase", _finding_types(findings))

    def test_heading_case_inside_code_block_not_flagged(self):
        # A Title Case line inside a code block must not be checked as a heading.
        text = (
            "```bash\n"
            "## Getting Started With Auth\n"
            "echo hello\n"
            "```\n\n"
            "Normal text.\n"
        )
        findings = _check_text(text)
        self.assertNotIn("heading_case", _finding_types(findings))


class TestMainIntegration(unittest.TestCase):
    """main() produces valid JSON with the required structure."""

    def test_main_with_directory_returns_json_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write a clean doc so there is at least one file to scan.
            doc_path = os.path.join(tmpdir, "clean.md")
            with open(doc_path, "w") as f:
                f.write("# Overview\n\nNormal prose with no issues.\n")
            output = _run_main([tmpdir])

        self.assertIn("summary", output)
        self.assertIn("files", output)
        summary = output["summary"]
        for key in ("files_scanned", "total_violations", "by_type"):
            self.assertIn(key, summary, f"Missing key in summary: {key}")
        by_type = summary["by_type"]
        for key in ("banned_phrase", "heading_case", "bare_code_fence"):
            self.assertIn(key, by_type, f"Missing by_type key: {key}")

    def test_main_with_nonexistent_dir_returns_error(self):
        output = _run_main(["/nonexistent/path/xyz"])
        self.assertIn("error", output)
        self.assertEqual(output["error"], "not_a_directory")

    def test_main_detects_violations_in_violating_doc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            doc_path = os.path.join(tmpdir, "violations.md")
            with open(doc_path, "w") as f:
                f.write(
                    "# Overview\n\n"
                    "Simply run this command in order to get started.\n\n"
                    "```\ncode without language\n```\n"
                )
            output = _run_main([tmpdir])

        all_types = [
            f["type"]
            for file_result in output.get("files", [])
            for f in file_result.get("findings", [])
        ]
        self.assertIn("banned_phrase", all_types)
        self.assertIn("bare_code_fence", all_types)


if __name__ == "__main__":
    unittest.main()
