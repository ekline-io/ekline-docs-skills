"""Tests for skills/accessibility/scripts/check_accessibility.py."""

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
    "accessibility",
    "scripts",
)
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

import check_accessibility as c  # noqa: E402

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _run_main(args):
    """Run c.main() with the given argv list and return parsed JSON output."""
    old_argv = sys.argv[:]
    sys.argv = ["check_accessibility.py"] + args
    captured = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured):
            c.main()
    finally:
        sys.argv = old_argv
    return json.loads(captured.getvalue())


def _check_text(text):
    """Write text to a temp file, run check_file, clean up, and return findings."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(text)
        path = f.name
    try:
        return c.check_file(path)
    finally:
        os.unlink(path)


def _finding_types(findings):
    return [f["type"] for f in findings]


class TestImageAltText(unittest.TestCase):
    def test_empty_alt_text_detected(self):
        findings = _check_text("![](image.png)")
        self.assertIn("missing_alt_text", _finding_types(findings))

    def test_valid_alt_text_not_flagged(self):
        findings = _check_text("![description of the image](image.png)")
        self.assertNotIn("missing_alt_text", _finding_types(findings))
        self.assertNotIn("long_alt_text", _finding_types(findings))

    def test_long_alt_text_detected(self):
        long_alt = "A" * 130
        findings = _check_text(f"![{long_alt}](image.png)")
        self.assertIn("long_alt_text", _finding_types(findings))


class TestHeadingHierarchy(unittest.TestCase):
    def test_skipped_heading_level_detected(self):
        # h1 directly to h3 skips h2 — should be flagged.
        text = "# Main heading\n\n### Skipped to h3\n\nSome content."
        findings = _check_text(text)
        self.assertIn("skipped_heading_level", _finding_types(findings))

    def test_valid_heading_hierarchy_not_flagged(self):
        text = "# H1\n\n## H2\n\n### H3\n\n## H2b\n\n### H3b\n\nText here."
        findings = _check_text(text)
        self.assertNotIn("skipped_heading_level", _finding_types(findings))

    def test_multiple_h1_detected(self):
        text = "# First H1\n\nSome text.\n\n# Second H1\n\nMore text."
        findings = _check_text(text)
        self.assertIn("multiple_h1", _finding_types(findings))


class TestLinkText(unittest.TestCase):
    def test_non_descriptive_link_detected(self):
        text = "For more info, [click here](https://example.com)."
        findings = _check_text(text)
        self.assertIn("non_descriptive_link", _finding_types(findings))

    def test_descriptive_link_not_flagged(self):
        text = "See the [installation guide](https://example.com) for details."
        findings = _check_text(text)
        self.assertNotIn("non_descriptive_link", _finding_types(findings))


class TestColorReferences(unittest.TestCase):
    def test_color_reference_detected(self):
        text = "Press the red button to continue."
        findings = _check_text(text)
        self.assertIn("color_only_reference", _finding_types(findings))


class TestCodeBlockLanguage(unittest.TestCase):
    def test_bare_fence_detected(self):
        # An unclosed fence has no paired closing fence, so it is not captured
        # by CODE_BLOCK_RE and its line is not excluded — the checker then flags
        # the bare ``` opening line.
        text = "# Title\n\nSome text.\n\n```\ncode without a language or closing fence\n"
        findings = _check_text(text)
        self.assertIn("missing_code_language", _finding_types(findings))

    def test_headings_inside_code_blocks_ignored(self):
        # A # comment inside a fenced python block must NOT be treated as a heading.
        text = "```python\n# This is a Python comment, not a heading\ndef hello():\n    pass\n```\n"
        findings = _check_text(text)
        self.assertNotIn("skipped_heading_level", _finding_types(findings))
        self.assertNotIn("multiple_h1", _finding_types(findings))

    def test_headings_inside_frontmatter_ignored(self):
        # A # comment inside YAML frontmatter must NOT be treated as a heading.
        text = (
            "---\n"
            "# YAML comment\n"
            "title: Test document\n"
            "---\n\n"
            "# Real heading\n\n"
            "Content here.\n"
        )
        findings = _check_text(text)
        # The only real heading is h1; there should be no hierarchy or multiple-h1 issues.
        self.assertNotIn("multiple_h1", _finding_types(findings))
        self.assertNotIn("skipped_heading_level", _finding_types(findings))


class TestTableHeaders(unittest.TestCase):
    def test_table_without_headers_detected(self):
        # A table where the second row is NOT a separator row should be flagged.
        text = "| Column 1 | Column 2 |\n| Data 1 | Data 2 |\n"
        findings = _check_text(text)
        self.assertIn("table_without_headers", _finding_types(findings))

    def test_well_formed_table_not_flagged(self):
        text = "| Column 1 | Column 2 |\n| --- | --- |\n| Data 1 | Data 2 |\n"
        findings = _check_text(text)
        self.assertNotIn("table_without_headers", _finding_types(findings))


class TestMainIntegration(unittest.TestCase):
    def test_main_with_directory_returns_json_structure(self):
        output = _run_main([FIXTURES_DIR])
        self.assertIn("summary", output)
        self.assertIn("files", output)
        summary = output["summary"]
        for key in (
            "files_scanned",
            "files_with_issues",
            "files_truncated",
            "total_issues",
            "errors",
            "warnings",
            "info",
        ):
            self.assertIn(key, summary, f"Missing key: {key}")

    def test_main_error_handling_nonexistent_dir(self):
        output = _run_main(["/nonexistent/path/xyz"])
        self.assertIn("error", output)
        self.assertEqual(output["error"], "not_a_directory")

    def test_main_detects_issues_in_fixture(self):
        # The accessibility_issues.md fixture should produce at least one finding.
        output = _run_main([FIXTURES_DIR])
        all_finding_types = [
            f["type"]
            for file_result in output.get("files", [])
            for f in file_result.get("findings", [])
        ]
        # We know accessibility_issues.md has missing alt text and a bad link.
        self.assertIn("missing_alt_text", all_finding_types)
        self.assertIn("non_descriptive_link", all_finding_types)


if __name__ == "__main__":
    unittest.main()
