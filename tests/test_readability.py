"""Tests for skills/readability/scripts/analyze_readability.py."""

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
    "readability",
    "scripts",
)
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

import analyze_readability as r  # noqa: E402

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _run_main(args):
    """Run r.main() with the given argv list and return parsed JSON output."""
    old_argv = sys.argv[:]
    sys.argv = ["analyze_readability.py"] + args
    captured = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured):
            r.main()
    finally:
        sys.argv = old_argv
    return json.loads(captured.getvalue())


class TestCountSyllables(unittest.TestCase):
    def test_hello_has_two_syllables(self):
        self.assertEqual(r.count_syllables("hello"), 2)

    def test_the_has_one_syllable(self):
        self.assertEqual(r.count_syllables("the"), 1)

    def test_documentation_has_five_syllables(self):
        self.assertEqual(r.count_syllables("documentation"), 5)

    def test_single_letter_a_has_one_syllable(self):
        self.assertEqual(r.count_syllables("a"), 1)


class TestStripNonProse(unittest.TestCase):
    def test_removes_yaml_frontmatter(self):
        text = "---\ntitle: Test\ndate: 2024-01-01\n---\n\nSome prose here."
        result = r.strip_non_prose(text)
        self.assertNotIn("title:", result)
        self.assertIn("Some prose here.", result)

    def test_removes_fenced_code_blocks(self):
        text = "Before.\n```python\nprint('hi')\n```\nAfter."
        result = r.strip_non_prose(text)
        self.assertNotIn("print", result)
        self.assertIn("Before.", result)
        self.assertIn("After.", result)

    def test_removes_mdx_import_lines(self):
        text = "import Tabs from '@theme/Tabs'\n\nSome prose."
        result = r.strip_non_prose(text)
        self.assertNotIn("import", result)
        self.assertIn("Some prose.", result)

    def test_preserves_markdown_link_text(self):
        text = "[click here](https://example.com)"
        result = r.strip_non_prose(text)
        self.assertIn("click here", result)
        self.assertNotIn("https://example.com", result)

    def test_heading_text_not_in_output(self):
        text = "## My Special Heading\n\nSome text here."
        result = r.strip_non_prose(text)
        self.assertNotIn("My Special Heading", result)
        self.assertIn("Some text here.", result)


class TestSplitSentences(unittest.TestCase):
    def test_splits_on_newlines(self):
        text = "Item one\nItem two\nItem three"
        sentences = r.split_sentences(text)
        self.assertGreaterEqual(len(sentences), 2)
        self.assertTrue(any("Item one" in s for s in sentences))
        self.assertTrue(any("Item two" in s for s in sentences))

    def test_splits_on_sentence_ending_punctuation(self):
        text = "Hello world. Goodbye world."
        sentences = r.split_sentences(text)
        self.assertEqual(len(sentences), 2)
        self.assertIn("Hello world.", sentences)
        self.assertIn("Goodbye world.", sentences)


class TestAnalyzeFile(unittest.TestCase):
    def test_returns_none_for_short_files(self):
        path = os.path.join(FIXTURES_DIR, "thin_page.md")
        result = r.analyze_file(path)
        self.assertIsNone(result)

    def test_returns_grade_for_normal_file(self):
        path = os.path.join(FIXTURES_DIR, "simple_doc.md")
        result = r.analyze_file(path)
        self.assertIsNotNone(result)
        self.assertIn(result["grade"], ("A", "B", "C", "D", "F"))

    def test_flesch_score_clamped_to_0_100(self):
        path = os.path.join(FIXTURES_DIR, "simple_doc.md")
        result = r.analyze_file(path)
        self.assertIsNotNone(result)
        ease = result["metrics"]["flesch_reading_ease"]
        self.assertGreaterEqual(ease, 0.0)
        self.assertLessEqual(ease, 100.0)

    def test_heading_text_not_in_prose_analysis(self):
        # A file where the heading has complex vocabulary should not inflate
        # the metrics — the heading words must be stripped before analysis.
        content = (
            "## Incomprehensible Unimplementable Extraordinarily\n\n"
            "This is simple text. Easy to read. Short words only. "
            "Quick to learn. Just try it. You will see. "
            "It is good. Read along. Keep going now. "
            "Simple stuff here. Nothing hard. Just plain text.\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(content)
            path = f.name
        try:
            result_with_heading = r.analyze_file(path)
        finally:
            os.unlink(path)

        # Now write only the prose without the heading
        prose_only = (
            "This is simple text. Easy to read. Short words only. "
            "Quick to learn. Just try it. You will see. "
            "It is good. Read along. Keep going now. "
            "Simple stuff here. Nothing hard. Just plain text.\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(prose_only)
            path2 = f.name
        try:
            result_prose_only = r.analyze_file(path2)
        finally:
            os.unlink(path2)

        # Both may return None for very short content, but if they both have
        # results the Flesch scores should be the same (heading stripped).
        if result_with_heading and result_prose_only:
            self.assertAlmostEqual(
                result_with_heading["metrics"]["flesch_reading_ease"],
                result_prose_only["metrics"]["flesch_reading_ease"],
                delta=1.0,
            )


class TestMainIntegration(unittest.TestCase):
    def test_main_with_directory_returns_json_structure(self):
        output = _run_main([FIXTURES_DIR])
        self.assertIn("summary", output)
        self.assertIn("files", output)
        summary = output["summary"]
        for key in (
            "files_analyzed",
            "files_skipped",
            "files_truncated",
            "overall_grade",
            "avg_flesch_reading_ease",
            "avg_flesch_kincaid_grade",
        ):
            self.assertIn(key, summary, f"Missing key: {key}")

    def test_main_with_nonexistent_dir_returns_error_json(self):
        output = _run_main(["/nonexistent/path/xyz"])
        self.assertIn("error", output)
        self.assertEqual(output["error"], "not_a_directory")


if __name__ == "__main__":
    unittest.main()
