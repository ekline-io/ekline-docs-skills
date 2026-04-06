"""Tests for skills/check-links/scripts/extract_links.py."""

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
    "check-links",
    "scripts",
)
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

import extract_links as el  # noqa: E402


def _run_main(args):
    """Run el.main() with the given argv list and return parsed JSON output."""
    old_argv = sys.argv[:]
    sys.argv = ["extract_links.py"] + args
    captured = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured):
            try:
                el.main()
            except SystemExit:
                pass
    finally:
        sys.argv = old_argv
    return json.loads(captured.getvalue())


class TestHeadingToAnchor(unittest.TestCase):
    def test_simple_ascii_lowercased_and_hyphenated(self):
        self.assertEqual(el.heading_to_anchor("Getting started"), "getting-started")

    def test_special_chars_stripped_version_number(self):
        # Punctuation such as apostrophes and dots are stripped, spaces become hyphens.
        result = el.heading_to_anchor("What's new in v2.0")
        self.assertEqual(result, "whats-new-in-v20")

    def test_inline_code_backticks_stripped(self):
        # Backticks are stripped; the word remains.
        result = el.heading_to_anchor("`fetch()` API")
        self.assertEqual(result, "fetch-api")

    def test_markdown_link_in_heading_uses_link_text(self):
        # [Guide](url) → "Guide", then lowercased.
        result = el.heading_to_anchor("[Guide](https://example.com) overview")
        self.assertEqual(result, "guide-overview")

    def test_emoji_stripped_from_heading(self):
        # Emoji are stripped; surrounding words remain separated by a hyphen.
        result = el.heading_to_anchor("Hello 👋 World")
        # After stripping emoji, spaces collapse to a single hyphen.
        self.assertIn("hello", result)
        self.assertIn("world", result)

    def test_empty_string_returns_empty_string(self):
        self.assertEqual(el.heading_to_anchor(""), "")

    def test_consecutive_special_chars_collapsed(self):
        # Multiple punctuation characters in a row should not leave double hyphens.
        result = el.heading_to_anchor("Q&A -- FAQ")
        # Should produce "qa--faq" or "qa-faq" — no leading/trailing hyphens.
        self.assertFalse(result.startswith("-"))
        self.assertFalse(result.endswith("-"))
        self.assertIn("qa", result)
        self.assertIn("faq", result)

    def test_already_valid_anchor_unchanged(self):
        self.assertEqual(el.heading_to_anchor("installation"), "installation")


class TestExtractLinks(unittest.TestCase):
    def test_inline_links_extracted(self):
        content = "See the [guide](https://example.com/guide) for details."
        links = el.extract_links("doc.md", content)
        targets = [ln["target"] for ln in links]
        self.assertIn("https://example.com/guide", targets)

    def test_reference_style_links_extracted(self):
        content = "Visit [EkLine][ekline] for more.\n\n[ekline]: https://ekline.io\n"
        links = el.extract_links("doc.md", content)
        targets = [ln["target"] for ln in links]
        self.assertIn("https://ekline.io", targets)

    def test_html_href_extracted(self):
        content = 'Click <a href="https://example.com">here</a>.'
        links = el.extract_links("doc.md", content)
        targets = [ln["target"] for ln in links]
        self.assertIn("https://example.com", targets)

    def test_links_inside_fenced_code_blocks_skipped(self):
        content = "```\n[not a link](https://should-be-skipped.com)\n```"
        links = el.extract_links("doc.md", content)
        targets = [ln["target"] for ln in links]
        self.assertNotIn("https://should-be-skipped.com", targets)

    def test_image_links_classified_as_image(self):
        content = "![screenshot](./assets/screen.png)"
        links = el.extract_links("doc.md", content)
        self.assertTrue(any(ln["type"] == "image" for ln in links))

    def test_fragment_only_links_classified_as_anchor(self):
        content = "Jump to [overview](#overview)."
        links = el.extract_links("doc.md", content)
        anchor_links = [ln for ln in links if ln["type"] == "anchor"]
        self.assertEqual(len(anchor_links), 1)
        self.assertEqual(anchor_links[0]["target"], "#overview")


class TestClassifyLink(unittest.TestCase):
    def test_https_url_is_external(self):
        self.assertEqual(el.classify_link("https://example.com"), "external")

    def test_relative_md_file_is_internal(self):
        self.assertEqual(el.classify_link("./guide.md"), "internal")

    def test_fragment_is_anchor(self):
        self.assertEqual(el.classify_link("#anchor"), "anchor")

    def test_mailto_is_email(self):
        self.assertEqual(el.classify_link("mailto:a@b.com"), "email")

    def test_png_extension_is_image(self):
        self.assertEqual(el.classify_link("image.png"), "image")

    def test_http_url_is_external(self):
        self.assertEqual(el.classify_link("http://example.com"), "external")


class TestIsSafeExternalUrl(unittest.TestCase):
    def test_valid_https_returns_true(self):
        self.assertTrue(el.is_safe_external_url("https://example.com"))

    def test_valid_http_returns_true(self):
        self.assertTrue(el.is_safe_external_url("http://example.com"))

    def test_file_scheme_returns_false(self):
        self.assertFalse(el.is_safe_external_url("file:///etc/passwd"))

    def test_data_scheme_returns_false(self):
        self.assertFalse(el.is_safe_external_url("data:text/html,<script>alert(1)</script>"))

    def test_shell_metachar_dollar_returns_false(self):
        self.assertFalse(el.is_safe_external_url("http://example.com$(whoami)"))

    def test_shell_metachar_backtick_returns_false(self):
        self.assertFalse(el.is_safe_external_url("https://example.com/`id`"))

    def test_empty_string_returns_false(self):
        self.assertFalse(el.is_safe_external_url(""))


class TestValidateInternalLink(unittest.TestCase):
    def test_fragment_link_that_exists_returns_ok(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            doc = os.path.join(tmpdir, "guide.md")
            with open(doc, "w") as f:
                f.write("## Installation\n\nSome content.\n")

            anchors = {"guide.md": el.extract_anchors("## Installation\n\nSome content.\n")}
            # Re-key using the absolute path as extract_links does.
            anchors_by_file = {doc: el.extract_anchors("## Installation\n\nSome content.\n")}

            link = {"file": doc, "target": "#installation", "type": "anchor"}
            result = el.validate_internal_link(link, {doc}, anchors_by_file, docs_root=tmpdir)
            self.assertEqual(result["status"], "ok")

    def test_fragment_link_that_does_not_exist_returns_broken(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            doc = os.path.join(tmpdir, "guide.md")
            with open(doc, "w") as f:
                f.write("## Installation\n\nSome content.\n")

            anchors_by_file = {doc: el.extract_anchors("## Installation\n\nSome content.\n")}

            link = {"file": doc, "target": "#nonexistent-section", "type": "anchor"}
            result = el.validate_internal_link(link, {doc}, anchors_by_file, docs_root=tmpdir)
            self.assertEqual(result["status"], "broken")
            self.assertIn("Anchor", result["reason"])

    def test_relative_file_link_that_exists_returns_ok(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source = os.path.join(tmpdir, "index.md")
            target_file = os.path.join(tmpdir, "other.md")
            with open(source, "w") as f:
                f.write("See [other](./other.md).\n")
            with open(target_file, "w") as f:
                f.write("# Other\n")

            doc_files_set = {os.path.normpath(source), os.path.normpath(target_file)}
            link = {"file": source, "target": "./other.md", "type": "internal"}
            result = el.validate_internal_link(link, doc_files_set, {}, docs_root=tmpdir)
            self.assertEqual(result["status"], "ok")

    def test_relative_file_link_that_does_not_exist_returns_broken(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source = os.path.join(tmpdir, "index.md")
            with open(source, "w") as f:
                f.write("See [missing](./missing.md).\n")

            link = {"file": source, "target": "./missing.md", "type": "internal"}
            result = el.validate_internal_link(link, {os.path.normpath(source)}, {}, docs_root=tmpdir)
            self.assertEqual(result["status"], "broken")
            self.assertIn("suggestions", result)

    def test_path_traversal_outside_docs_root_returns_broken(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source = os.path.join(tmpdir, "index.md")
            with open(source, "w") as f:
                f.write("Bad link.\n")

            # ../../etc/passwd escapes the tmpdir
            link = {"file": source, "target": "../../etc/passwd", "type": "internal"}
            result = el.validate_internal_link(link, {os.path.normpath(source)}, {}, docs_root=tmpdir)
            self.assertEqual(result["status"], "broken")
            # Resolved path must be redacted to avoid leaking system paths.
            self.assertEqual(result.get("resolved_path"), "(redacted)")

    def test_route_style_link_resolves_to_md_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            guide_file = os.path.join(tmpdir, "guide.md")
            with open(guide_file, "w") as f:
                f.write("# Guide\n")

            source = os.path.join(tmpdir, "index.md")
            with open(source, "w") as f:
                f.write("See [guide](/guide).\n")

            link = {"file": source, "target": "/guide", "type": "internal"}
            result = el.validate_internal_link(link, {os.path.normpath(source)}, {}, docs_root=tmpdir)
            self.assertEqual(result["status"], "ok")


class TestMainIntegration(unittest.TestCase):
    def test_main_on_valid_docs_returns_no_broken_links(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            index = os.path.join(tmpdir, "index.md")
            guide = os.path.join(tmpdir, "guide.md")
            with open(index, "w") as f:
                f.write("# Index\n\nSee [guide](./guide.md).\n")
            with open(guide, "w") as f:
                f.write("# Guide\n\nSome content.\n")

            output = _run_main([tmpdir])

        self.assertIn("broken_internal", output)
        self.assertEqual(output["broken_internal"], [])
        self.assertIn("summary", output)
        self.assertIn("files_scanned", output)

    def test_main_on_nonexistent_dir_returns_error_json(self):
        output = _run_main(["/nonexistent/path/xyz_does_not_exist"])
        self.assertIn("error", output)
        self.assertEqual(output["error"], "not_a_directory")

    def test_main_on_dir_with_broken_internal_link_reports_it(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            doc = os.path.join(tmpdir, "README.md")
            with open(doc, "w") as f:
                # Link to a file that does not exist
                f.write("# Docs\n\nSee [missing page](./does-not-exist.md).\n")

            output = _run_main([tmpdir])

        self.assertIn("broken_internal", output)
        self.assertGreater(len(output["broken_internal"]), 0)
        broken_targets = [b["target"] for b in output["broken_internal"]]
        self.assertIn("./does-not-exist.md", broken_targets)


if __name__ == "__main__":
    unittest.main()
