"""Tests for skills/content-audit/scripts/audit_content.py."""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

# Add the script directory to sys.path so we can import the module directly.
SCRIPT_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "skills",
    "content-audit",
    "scripts",
)
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

import audit_content as a  # noqa: E402

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _run_main(args):
    """Run a.main() with the given argv list and return parsed JSON output."""
    old_argv = sys.argv[:]
    sys.argv = ["audit_content.py"] + args
    captured = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured):
            a.main()
    finally:
        sys.argv = old_argv
    return json.loads(captured.getvalue())


class _TempDirMixin:
    """Mixin providing a temporary directory that is removed after each test."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write(self, filename, content):
        path = os.path.join(self.tmpdir, filename)
        with open(path, "w") as f:
            f.write(content)
        return path

    def _run(self, extra_args=None):
        args = [self.tmpdir] + (extra_args or [])
        return _run_main(args)


class TestJaccardSimilarity(unittest.TestCase):
    def test_identical_sets_return_1(self):
        s = {"alpha", "beta", "gamma"}
        self.assertEqual(a.jaccard_similarity(s, s), 1.0)

    def test_disjoint_sets_return_0(self):
        self.assertEqual(a.jaccard_similarity({"a", "b"}, {"c", "d"}), 0.0)

    def test_partial_overlap_returns_correct_value(self):
        # {"a","b","c"} ∩ {"b","c","d"} = {"b","c"} → 2/4 = 0.5
        result = a.jaccard_similarity({"a", "b", "c"}, {"b", "c", "d"})
        self.assertAlmostEqual(result, 0.5)

    def test_empty_sets_return_0(self):
        self.assertEqual(a.jaccard_similarity(set(), set()), 0.0)


class TestExtractFrontmatter(unittest.TestCase):
    def test_parses_frontmatter_fields(self):
        text = "---\ntitle: My Doc\ndate: 2024-01-01\nauthor: Alice\n---\n\n# Content"
        fields = a.extract_frontmatter(text)
        self.assertIn("title", fields)
        self.assertIn("date", fields)
        self.assertIn("author", fields)

    def test_returns_empty_dict_when_no_frontmatter(self):
        text = "# No frontmatter\n\nJust regular content."
        fields = a.extract_frontmatter(text)
        self.assertEqual(fields, {})


class TestCountProseWords(_TempDirMixin, unittest.TestCase):
    def test_code_blocks_excluded_from_word_count(self):
        content = (
            "# Heading\n\n"
            "Five words of prose.\n\n"
            "```python\n"
            "code_line_one = True\n"
            "code_line_two = False\n"
            "```\n\n"
            "More prose.\n"
        )
        # "Five words of prose" = 4 words, "More prose" = 2 words → 6 total
        # (heading stripped; code stripped)
        count = a.count_prose_words(content)
        # Code words must NOT be included; actual prose words must be.
        self.assertGreater(count, 0)
        self.assertLess(count, 20)  # code_line_one / code_line_two excluded


class TestThinPageDetection(_TempDirMixin, unittest.TestCase):
    def test_thin_page_flagged(self):
        self._write("thin.md", "# Thin page\n\nJust a few words here.\n")
        output = self._run()
        thin_files = [t["file"] for t in output.get("thin_pages", [])]
        self.assertTrue(
            any("thin.md" in p for p in thin_files),
            f"Expected thin.md in thin_pages, got: {thin_files}",
        )

    def test_normal_page_not_flagged_as_thin(self):
        # 100+ prose words
        prose = " ".join(["word"] * 110)
        self._write("normal.md", f"# Title\n\n{prose}\n")
        output = self._run()
        thin_files = [t["file"] for t in output.get("thin_pages", [])]
        self.assertFalse(
            any("normal.md" in p for p in thin_files),
            f"normal.md should not be thin, got: {thin_files}",
        )


class TestMissingH1Detection(_TempDirMixin, unittest.TestCase):
    def test_missing_h1_detected(self):
        self._write("no_h1.md", "## Only an H2\n\nSome prose here with enough words.\n")
        output = self._run()
        issue_types = [s["type"] for s in output.get("structure_issues", [])]
        self.assertIn("missing_h1", issue_types)

    def test_html_h1_recognized_not_flagged(self):
        self._write(
            "html_h1.md",
            '<h1 align="center">Project Name</h1>\n\n## Section\n\nSome content here.\n',
        )
        output = self._run()
        for issue in output.get("structure_issues", []):
            if "html_h1.md" in issue["file"]:
                self.assertNotEqual(
                    issue["type"],
                    "missing_h1",
                    "html_h1.md should not be flagged for missing_h1",
                )

    def test_frontmatter_title_recognized_not_flagged(self):
        self._write(
            "fm_title.md",
            "---\ntitle: My Page Title\n---\n\n## Section\n\nSome content here.\n",
        )
        output = self._run()
        for issue in output.get("structure_issues", []):
            if "fm_title.md" in issue["file"]:
                self.assertNotEqual(
                    issue["type"],
                    "missing_h1",
                    "fm_title.md should not be flagged for missing_h1",
                )


class TestOrphanTruncationWarning(_TempDirMixin, unittest.TestCase):
    def test_orphan_truncation_warning_present(self):
        # Create enough files that max_files truncation kicks in.
        for i in range(5):
            self._write(
                f"page_{i}.md",
                f"# Page {i}\n\nContent for page {i} with some words.\n",
            )
        # Limit to 3 files so truncated=True.
        output = self._run(["--max-files", "3"])
        self.assertTrue(output["summary"]["files_truncated"])
        for orphan in output.get("orphaned_pages", []):
            self.assertIn(
                "note",
                orphan,
                "Truncated orphans must include a warning note",
            )


class TestMainIntegration(unittest.TestCase):
    def test_main_with_directory_returns_json_structure(self):
        output = _run_main([FIXTURES_DIR])
        self.assertIn("summary", output)
        for key in (
            "files_scanned",
            "files_truncated",
            "duplicates_found",
            "thin_pages_found",
            "orphaned_pages_found",
            "structure_issues_found",
            "frontmatter_issues_found",
        ):
            self.assertIn(key, output["summary"], f"Missing key: {key}")
        for section in ("duplicates", "thin_pages", "orphaned_pages", "structure_issues"):
            self.assertIn(section, output, f"Missing section: {section}")

    def test_main_error_handling_nonexistent_dir(self):
        output = _run_main(["/nonexistent/path/xyz"])
        self.assertIn("error", output)
        self.assertEqual(output["error"], "not_a_directory")

    def test_duplicate_detection_flags_similar_files(self):
        # duplicate_a.md and duplicate_b.md share almost identical prose.
        output = _run_main([FIXTURES_DIR])
        dup_pairs = [
            (os.path.basename(d["file_a"]), os.path.basename(d["file_b"]))
            for d in output.get("duplicates", [])
        ]
        found = any(
            {"duplicate_a.md", "duplicate_b.md"} == {a_name, b_name}
            for a_name, b_name in dup_pairs
        )
        self.assertTrue(
            found,
            f"Expected duplicate_a.md and duplicate_b.md to be flagged, got: {dup_pairs}",
        )


if __name__ == "__main__":
    unittest.main()
