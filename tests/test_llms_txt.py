"""Tests for skills/llms-txt/scripts/generate_llms_txt.py."""

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
    "llms-txt",
    "scripts",
)
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

import generate_llms_txt as g  # noqa: E402


def _run_main(args):
    """Run g.main() with the given argv list and return (parsed JSON, exit code)."""
    old_argv = sys.argv[:]
    sys.argv = ["generate_llms_txt.py"] + args
    captured = io.StringIO()
    exit_code = 0
    try:
        with contextlib.redirect_stdout(captured):
            g.main()
    except SystemExit as exc:
        exit_code = exc.code if exc.code is not None else 0
    finally:
        sys.argv = old_argv
    return json.loads(captured.getvalue()), exit_code


def _write_temp_md(directory, filename, content):
    """Write a Markdown file inside directory and return its path."""
    path = os.path.join(directory, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    return path


class TestClassifyPage(unittest.TestCase):
    """classify_page() assigns sections based on the file's relative path."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _path_in(self, subdir, filename="page.md"):
        """Return an absolute path inside self.tmp/subdir without creating it."""
        return os.path.join(self.tmp, subdir, filename)

    def test_api_directory_classifies_as_api(self):
        path = self._path_in("api")
        result = g.classify_page(path, self.tmp)
        self.assertEqual(result, "API")

    def test_guides_directory_classifies_as_guides(self):
        path = self._path_in("guides")
        result = g.classify_page(path, self.tmp)
        self.assertEqual(result, "Guides")

    def test_guide_singular_directory_classifies_as_guides(self):
        path = self._path_in("guide")
        result = g.classify_page(path, self.tmp)
        self.assertEqual(result, "Guides")

    def test_blog_directory_classifies_as_blog(self):
        path = self._path_in("blog")
        result = g.classify_page(path, self.tmp)
        self.assertEqual(result, "Blog")

    def test_examples_directory_classifies_as_examples(self):
        path = self._path_in("examples")
        result = g.classify_page(path, self.tmp)
        self.assertEqual(result, "Examples")

    def test_root_file_classifies_as_docs_default(self):
        path = self._path_in("", "introduction.md")
        result = g.classify_page(path, self.tmp)
        self.assertEqual(result, "Docs")

    def test_reference_directory_classifies_as_api(self):
        path = self._path_in("reference")
        result = g.classify_page(path, self.tmp)
        self.assertEqual(result, "API")

    def test_tutorial_directory_classifies_as_guides(self):
        path = self._path_in("tutorial")
        result = g.classify_page(path, self.tmp)
        self.assertEqual(result, "Guides")


class TestExtractPageInfo(unittest.TestCase):
    """extract_page_info() pulls title and description from Markdown content."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_yaml_frontmatter_title_and_description_extracted(self):
        content = (
            "---\n"
            "title: Getting Started\n"
            "description: Learn how to set up the project.\n"
            "---\n\n"
            "Some introductory paragraph here.\n"
        )
        path = _write_temp_md(self.tmp, "page.md", content)
        title, description, size = g.extract_page_info(path)
        self.assertEqual(title, "Getting Started")
        self.assertEqual(description, "Learn how to set up the project.")

    def test_h1_heading_used_as_title_when_no_frontmatter(self):
        content = "# Installation Guide\n\nFollow these steps to install the package.\n"
        path = _write_temp_md(self.tmp, "install.md", content)
        title, description, size = g.extract_page_info(path)
        self.assertEqual(title, "Installation Guide")

    def test_description_falls_back_to_first_paragraph_when_no_frontmatter(self):
        content = "# Title\n\nThis is the first paragraph with enough text to qualify.\n"
        path = _write_temp_md(self.tmp, "page.md", content)
        title, description, size = g.extract_page_info(path)
        self.assertEqual(
            description, "This is the first paragraph with enough text to qualify."
        )

    def test_filename_used_as_title_when_no_heading_and_no_frontmatter(self):
        content = "Just some plain text without any heading.\n"
        path = _write_temp_md(self.tmp, "my-feature-page.md", content)
        title, description, size = g.extract_page_info(path)
        # Filename-derived title should be non-empty and title-cased from the slug.
        self.assertIsNotNone(title)
        self.assertGreater(len(title), 0)

    def test_empty_file_returns_filename_fallback_title(self):
        path = _write_temp_md(self.tmp, "empty-doc.md", "")
        title, description, size = g.extract_page_info(path)
        # Should not crash; title derived from filename.
        self.assertIsNotNone(title)

    def test_file_size_returned_correctly(self):
        content = "# Title\n\nSome content.\n"
        path = _write_temp_md(self.tmp, "sized.md", content)
        title, description, size = g.extract_page_info(path)
        self.assertEqual(size, os.path.getsize(path))

    def test_frontmatter_title_takes_precedence_over_h1(self):
        content = (
            "---\n"
            "title: Frontmatter Title\n"
            "---\n\n"
            "# H1 Heading\n\n"
            "Some body text that is long enough to be a description.\n"
        )
        path = _write_temp_md(self.tmp, "page.md", content)
        title, description, size = g.extract_page_info(path)
        self.assertEqual(title, "Frontmatter Title")

    def test_nonexistent_file_returns_none_triple(self):
        title, description, size = g.extract_page_info("/nonexistent/path/file.md")
        self.assertIsNone(title)
        self.assertIsNone(description)
        self.assertEqual(size, 0)


class TestDetectPlatform(unittest.TestCase):
    """detect_platform() identifies the docs framework from config files."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _touch(self, filename):
        path = os.path.join(self.tmp, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w").close()
        return path

    def test_docusaurus_config_js_detected(self):
        self._touch("docusaurus.config.js")
        platform, config_path = g.detect_platform(self.tmp)
        self.assertEqual(platform, "docusaurus")
        self.assertIsNotNone(config_path)

    def test_mkdocs_yml_detected(self):
        self._touch("mkdocs.yml")
        platform, config_path = g.detect_platform(self.tmp)
        self.assertEqual(platform, "mkdocs")
        self.assertIsNotNone(config_path)

    def test_mintlify_mint_json_detected(self):
        self._touch("mint.json")
        platform, config_path = g.detect_platform(self.tmp)
        self.assertEqual(platform, "mintlify")

    def test_empty_directory_returns_none(self):
        platform, config_path = g.detect_platform(self.tmp)
        self.assertIsNone(platform)
        self.assertIsNone(config_path)

    def test_vitepress_config_detected(self):
        self._touch(".vitepress/config.js")
        platform, config_path = g.detect_platform(self.tmp)
        self.assertEqual(platform, "vitepress")


class TestMainIntegration(unittest.TestCase):
    """main() end-to-end: JSON output shape and error handling."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_nonexistent_directory_returns_error_json(self):
        output, exit_code = _run_main(["/nonexistent/path/xyz"])
        self.assertIn("error", output)
        self.assertEqual(output["error"], "not_a_directory")
        self.assertNotEqual(exit_code, 0)

    def test_valid_docs_directory_returns_structured_json(self):
        _write_temp_md(
            self.tmp,
            "index.md",
            "# Welcome\n\nThis is the project introduction page.\n",
        )
        _write_temp_md(
            self.tmp,
            "guide/setup.md",
            "# Setup Guide\n\nFollow these steps to configure the system.\n",
        )
        output, exit_code = _run_main([self.tmp])
        self.assertEqual(exit_code, 0)
        for key in (
            "project_name",
            "sections",
            "total_files",
            "platform_detected",
            "base_url",
            "can_generate_full",
        ):
            self.assertIn(key, output, f"Missing key in output: {key}")

    def test_valid_docs_directory_pages_appear_in_sections(self):
        _write_temp_md(
            self.tmp,
            "intro.md",
            "# Introduction\n\nThis page introduces the product.\n",
        )
        _write_temp_md(
            self.tmp,
            "api/endpoints.md",
            "# Endpoints\n\nThis page documents the REST endpoints.\n",
        )
        output, exit_code = _run_main([self.tmp])
        self.assertEqual(exit_code, 0)
        sections = output.get("sections", {})
        all_titles = [
            page["title"]
            for pages in sections.values()
            for page in pages
        ]
        self.assertIn("Introduction", all_titles)
        self.assertIn("Endpoints", all_titles)

    def test_empty_directory_with_no_md_files_returns_error_json(self):
        output, exit_code = _run_main([self.tmp])
        self.assertIn("error", output)
        self.assertNotEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
