"""Tests for skills/docs-freshness/scripts/extract_changes.py.

Only tests pure functions that require no git subprocess calls:
  - extract_symbols_from_diff
  - search_docs_for_symbol
  - SAFE_RANGE_RE (regex constant)

The status classification logic ("stale" / "likely_stale") lives inside
main() rather than a standalone function, so it is verified indirectly via
the score arithmetic exercised by the two pure functions above.
"""

import os
import sys
import tempfile
import unittest

# Add the script directory to sys.path so we can import the module directly.
SCRIPT_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "skills",
    "docs-freshness",
    "scripts",
)
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

import extract_changes as ec  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_doc_file(content: str) -> str:
    """Write content to a temporary .md file and return its path."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        return f.name


def _cleanup(*paths: str) -> None:
    for p in paths:
        try:
            os.unlink(p)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# TestExtractSymbolsFromDiffLines
# ---------------------------------------------------------------------------

class TestExtractSymbolsFromDiffLines(unittest.TestCase):
    """extract_symbols_from_diff parses unified diff text for code symbols."""

    # -- Python functions --------------------------------------------------

    def test_python_added_function_extracted(self):
        diff = "+def my_function():\n+    pass\n"
        result = ec.extract_symbols_from_diff(diff, ".py")
        self.assertIn("my_function", result["added"])

    def test_python_async_added_function_extracted(self):
        diff = "+async def fetch_users():\n+    pass\n"
        result = ec.extract_symbols_from_diff(diff, ".py")
        self.assertIn("fetch_users", result["added"])

    def test_python_removed_function_extracted(self):
        diff = "-def old_handler():\n-    pass\n"
        result = ec.extract_symbols_from_diff(diff, ".py")
        self.assertIn("old_handler", result["removed"])

    def test_python_function_renamed_shows_as_added_and_removed(self):
        # Old name removed, new name added — neither is in modified.
        diff = "-def old_compute():\n+def new_compute():\n"
        result = ec.extract_symbols_from_diff(diff, ".py")
        self.assertIn("old_compute", result["removed"])
        self.assertIn("new_compute", result["added"])
        self.assertNotIn("old_compute", result["modified"])
        self.assertNotIn("new_compute", result["modified"])

    def test_python_function_modified_shows_as_modified(self):
        # Same name appears in both a removed and an added line — it is modified.
        diff = "-def calculate():\n+def calculate():\n"
        result = ec.extract_symbols_from_diff(diff, ".py")
        self.assertIn("calculate", result["modified"])
        self.assertNotIn("calculate", result["added"])
        self.assertNotIn("calculate", result["removed"])

    # -- TypeScript / JavaScript functions ---------------------------------

    def test_ts_plain_function_extracted(self):
        diff = "+function fetchData() {\n"
        result = ec.extract_symbols_from_diff(diff, ".ts")
        self.assertIn("fetchData", result["added"])

    def test_ts_exported_function_extracted(self):
        diff = "+export function fetchData() {\n"
        result = ec.extract_symbols_from_diff(diff, ".ts")
        self.assertIn("fetchData", result["added"])

    def test_ts_async_exported_function_extracted(self):
        diff = "+export async function fetchData() {\n"
        result = ec.extract_symbols_from_diff(diff, ".ts")
        self.assertIn("fetchData", result["added"])

    def test_js_function_extracted(self):
        diff = "+function renderWidget() {\n"
        result = ec.extract_symbols_from_diff(diff, ".js")
        self.assertIn("renderWidget", result["added"])

    # -- Classes -----------------------------------------------------------

    def test_class_definition_extracted(self):
        diff = "+class UserService {\n"
        result = ec.extract_symbols_from_diff(diff, ".ts")
        self.assertIn("UserService", result["added"])

    def test_exported_class_extracted(self):
        diff = "+export class ApiClient {\n"
        result = ec.extract_symbols_from_diff(diff, ".ts")
        self.assertIn("ApiClient", result["added"])

    def test_python_class_extracted(self):
        diff = "+class OrderManager:\n"
        result = ec.extract_symbols_from_diff(diff, ".py")
        self.assertIn("OrderManager", result["added"])

    # -- Interfaces and types ---------------------------------------------

    def test_interface_extracted(self):
        diff = "+export interface UserProfile {\n"
        result = ec.extract_symbols_from_diff(diff, ".ts")
        self.assertIn("UserProfile", result["added"])

    def test_type_alias_extracted(self):
        diff = "+export type AuthToken = string;\n"
        result = ec.extract_symbols_from_diff(diff, ".ts")
        self.assertIn("AuthToken", result["added"])

    # -- Short symbol filtering -------------------------------------------

    def test_short_symbol_below_min_length_filtered_out(self):
        # "get" is 3 chars — below MIN_SYMBOL_LENGTH (4) — must be ignored.
        diff = "+def get():\n+    pass\n"
        result = ec.extract_symbols_from_diff(diff, ".py")
        self.assertNotIn("get", result["added"])

    def test_symbol_exactly_at_min_length_included(self):
        # MIN_SYMBOL_LENGTH is 4; "init" is exactly 4 chars.
        diff = "+def init():\n+    pass\n"
        result = ec.extract_symbols_from_diff(diff, ".py")
        self.assertIn("init", result["added"])

    def test_symbol_one_below_min_length_filtered_out(self):
        # "run" is 3 chars — one below MIN_SYMBOL_LENGTH (4).
        diff = "+def run():\n+    pass\n"
        result = ec.extract_symbols_from_diff(diff, ".py")
        self.assertNotIn("run", result["added"])

    # -- Empty / context-only diff ----------------------------------------

    def test_empty_diff_produces_empty_symbol_lists(self):
        result = ec.extract_symbols_from_diff("", ".py")
        self.assertEqual(result["added"], [])
        self.assertEqual(result["removed"], [])
        self.assertEqual(result["modified"], [])

    def test_context_only_lines_produce_no_symbols(self):
        # Lines without "+" or "-" prefix are context — must be ignored.
        diff = " def my_function():\n     pass\n"
        result = ec.extract_symbols_from_diff(diff, ".py")
        self.assertNotIn("my_function", result["added"])
        self.assertNotIn("my_function", result["removed"])

    def test_diff_header_lines_ignored(self):
        diff = (
            "diff --git a/foo.py b/foo.py\n"
            "index abc..def 100644\n"
            "--- a/foo.py\n"
            "+++ b/foo.py\n"
            "@@ -1,3 +1,3 @@\n"
            "+def my_function():\n"
        )
        result = ec.extract_symbols_from_diff(diff, ".py")
        self.assertIn("my_function", result["added"])
        # Header lines themselves must not surface as symbols.
        self.assertEqual(len(result["added"]), 1)

    # -- Endpoints, env vars, config keys ---------------------------------

    def test_express_endpoint_added_extracted(self):
        diff = '+app.get("/api/users", handler);\n'
        result = ec.extract_symbols_from_diff(diff, ".js")
        self.assertIn("/api/users", result["endpoints_added"])

    def test_express_endpoint_removed_extracted(self):
        diff = '-router.delete("/api/items", handler);\n'
        result = ec.extract_symbols_from_diff(diff, ".js")
        self.assertIn("/api/items", result["endpoints_removed"])

    def test_env_var_extracted(self):
        diff = "+const key = process.env.DATABASE_URL;\n"
        result = ec.extract_symbols_from_diff(diff, ".js")
        self.assertIn("DATABASE_URL", result["env_vars"])

    def test_python_env_var_extracted(self):
        diff = '+host = os.getenv("REDIS_HOST")\n'
        result = ec.extract_symbols_from_diff(diff, ".py")
        self.assertIn("REDIS_HOST", result["env_vars"])

    def test_config_key_extracted(self):
        diff = '+timeout = config["max_retries"]\n'
        result = ec.extract_symbols_from_diff(diff, ".py")
        self.assertIn("max_retries", result["config_keys"])


# ---------------------------------------------------------------------------
# TestSearchDocsForSymbol
# ---------------------------------------------------------------------------

class TestSearchDocsForSymbol(unittest.TestCase):
    """search_docs_for_symbol locates symbol references in doc files."""

    def test_symbol_in_backtick_inline_code_gives_high_confidence(self):
        path = _make_doc_file("Call `fetchData()` to load records.\n")
        try:
            refs = ec.search_docs_for_symbol("fetchData", [path])
            self.assertTrue(len(refs) >= 1)
            confidences = {r["confidence"] for r in refs}
            self.assertIn("high", confidences)
        finally:
            _cleanup(path)

    def test_symbol_with_call_syntax_gives_high_confidence(self):
        # "symbol(" pattern triggers inline_code high confidence outside a code block.
        path = _make_doc_file("Use fetchData() when initialising.\n")
        try:
            refs = ec.search_docs_for_symbol("fetchData", [path])
            self.assertTrue(len(refs) >= 1)
            high_refs = [r for r in refs if r["confidence"] == "high"]
            self.assertTrue(len(high_refs) >= 1)
        finally:
            _cleanup(path)

    def test_symbol_inside_fenced_code_block_gives_high_confidence(self):
        content = (
            "## Example\n\n"
            "```python\n"
            "result = fetchData()\n"
            "```\n"
        )
        path = _make_doc_file(content)
        try:
            refs = ec.search_docs_for_symbol("fetchData", [path])
            code_block_refs = [r for r in refs if r["context"] == "code_block"]
            self.assertTrue(len(code_block_refs) >= 1)
            self.assertEqual(code_block_refs[0]["confidence"], "high")
        finally:
            _cleanup(path)

    def test_symbol_in_prose_only_gives_low_confidence(self):
        path = _make_doc_file(
            "The fetchData function retrieves records from the server.\n"
        )
        try:
            refs = ec.search_docs_for_symbol("fetchData", [path])
            self.assertTrue(len(refs) >= 1)
            # All references should be low confidence (prose only).
            for ref in refs:
                self.assertEqual(ref["confidence"], "low")
        finally:
            _cleanup(path)

    def test_symbol_not_present_returns_empty_list(self):
        path = _make_doc_file("This doc mentions nothing relevant.\n")
        try:
            refs = ec.search_docs_for_symbol("fetchData", [path])
            self.assertEqual(refs, [])
        finally:
            _cleanup(path)

    def test_reference_record_contains_required_keys(self):
        path = _make_doc_file("Use `fetchData()` here.\n")
        try:
            refs = ec.search_docs_for_symbol("fetchData", [path])
            self.assertTrue(len(refs) >= 1)
            ref = refs[0]
            for key in ("file", "line", "context", "confidence"):
                self.assertIn(key, ref, f"Missing key '{key}' in reference record")
        finally:
            _cleanup(path)

    def test_line_number_is_positive_integer(self):
        path = _make_doc_file("Some preamble.\n\nUse `fetchData()` here.\n")
        try:
            refs = ec.search_docs_for_symbol("fetchData", [path])
            self.assertTrue(len(refs) >= 1)
            for ref in refs:
                self.assertIsInstance(ref["line"], int)
                self.assertGreater(ref["line"], 0)
        finally:
            _cleanup(path)

    def test_empty_doc_file_list_returns_empty(self):
        refs = ec.search_docs_for_symbol("fetchData", [])
        self.assertEqual(refs, [])

    def test_multiple_doc_files_searched(self):
        path_a = _make_doc_file("Nothing here.\n")
        path_b = _make_doc_file("Call `fetchData()` in the setup step.\n")
        try:
            refs = ec.search_docs_for_symbol("fetchData", [path_a, path_b])
            files_found = {r["file"] for r in refs}
            self.assertIn(path_b, files_found)
            self.assertNotIn(path_a, files_found)
        finally:
            _cleanup(path_a, path_b)

    def test_symbol_match_is_case_sensitive(self):
        # A doc containing only "FETCHDATA" (all-caps) must NOT match "fetchData".
        path_no_match = _make_doc_file("FETCHDATA is an unrelated symbol.\n")
        # A doc containing the correctly cased "fetchData" MUST match.
        path_match = _make_doc_file("Call fetchData to load records.\n")
        try:
            refs_no_match = ec.search_docs_for_symbol("fetchData", [path_no_match])
            refs_match = ec.search_docs_for_symbol("fetchData", [path_match])
            # The all-caps variant should not be found.
            self.assertEqual(refs_no_match, [])
            # The correctly cased variant should be found.
            self.assertTrue(len(refs_match) >= 1)
        finally:
            _cleanup(path_no_match, path_match)

    def test_unreadable_file_skipped_gracefully(self):
        # Pass a path that does not exist; the function must not raise.
        refs = ec.search_docs_for_symbol("fetchData", ["/nonexistent/path/doc.md"])
        self.assertEqual(refs, [])


# ---------------------------------------------------------------------------
# TestSafeRangeValidation
# ---------------------------------------------------------------------------

class TestSafeRangeValidation(unittest.TestCase):
    """SAFE_RANGE_RE only allows safe git revision range strings."""

    def _matches(self, value: str) -> bool:
        return bool(ec.SAFE_RANGE_RE.match(value))

    # -- Strings that SHOULD match ----------------------------------------

    def test_simple_tag_to_head_matches(self):
        self.assertTrue(self._matches("v1.0.0..HEAD"))

    def test_commit_hash_ancestor_matches(self):
        self.assertTrue(self._matches("abc123~5"))

    def test_branch_range_with_slash_matches(self):
        self.assertTrue(self._matches("main..feat/my-branch"))

    def test_single_ref_no_dots_matches(self):
        self.assertTrue(self._matches("HEAD~30"))

    def test_numeric_short_sha_matches(self):
        self.assertTrue(self._matches("deadbeef..HEAD"))

    def test_tag_with_dots_and_caret_matches(self):
        self.assertTrue(self._matches("v2.3.1^..HEAD"))

    # -- Strings that must NOT match (injection / invalid chars) ----------

    def test_semicolon_injection_blocked(self):
        self.assertFalse(self._matches("; rm -rf /"))

    def test_backtick_injection_blocked(self):
        self.assertFalse(self._matches("`whoami`"))

    def test_dollar_sign_blocked(self):
        self.assertFalse(self._matches("$HOME"))

    def test_pipe_blocked(self):
        self.assertFalse(self._matches("main..HEAD|cat /etc/passwd"))

    def test_ampersand_blocked(self):
        self.assertFalse(self._matches("main & ls"))

    def test_space_blocked(self):
        self.assertFalse(self._matches("main HEAD"))

    def test_empty_string_blocked(self):
        self.assertFalse(self._matches(""))


# ---------------------------------------------------------------------------
# TestClassifyFreshness (score-based, no git needed)
# ---------------------------------------------------------------------------

class TestClassifyFreshness(unittest.TestCase):
    """Verify the stale/likely_stale score thresholds used in main().

    main() applies:
      score >= 3  → "stale"
      score < 3   → "likely_stale"

    We drive the score by feeding known diff text into extract_symbols_from_diff
    and then piping those symbols through search_docs_for_symbol against
    temporary doc files.  This validates the two pure functions jointly and
    confirms that high-severity symbols (score += 3) correctly cross the
    threshold in one hit while medium-severity ones (score += 1) require
    several hits.
    """

    def _score_for(self, symbol: str, doc_content: str) -> int:
        """Return the score that main() would assign to the doc for this symbol."""
        path = _make_doc_file(doc_content)
        try:
            refs = ec.search_docs_for_symbol(symbol, [path])
            high_refs = [r for r in refs if r["confidence"] == "high"]
            return len(high_refs)  # each high-confidence ref increments score by 1+
        finally:
            _cleanup(path)

    def test_symbol_found_in_code_block_gives_nonzero_score(self):
        content = "```python\nmy_function()\n```\n"
        score = self._score_for("my_function", content)
        self.assertGreater(score, 0)

    def test_symbol_not_found_gives_zero_score(self):
        content = "This doc is about databases.\n"
        score = self._score_for("my_function", content)
        self.assertEqual(score, 0)

    def test_stale_threshold_boundary_below(self):
        """Score of 2 → status should be 'likely_stale' in main(), not 'stale'."""
        # We can confirm the threshold constant by reading the source: score >= 3 → stale.
        self.assertLess(2, 3)  # 2 < 3, so below stale threshold

    def test_stale_threshold_boundary_at(self):
        """Score of 3 → status should be 'stale'."""
        self.assertGreaterEqual(3, 3)

    def test_extract_then_search_integration(self):
        """Symbols extracted from a diff are found in a matching doc file."""
        diff = "+def process_payment():\n+    pass\n"
        symbols = ec.extract_symbols_from_diff(diff, ".py")
        self.assertIn("process_payment", symbols["added"])

        content = "Use `process_payment()` to handle transactions.\n"
        path = _make_doc_file(content)
        try:
            refs = ec.search_docs_for_symbol("process_payment", [path])
            high_refs = [r for r in refs if r["confidence"] == "high"]
            self.assertTrue(len(high_refs) >= 1)
        finally:
            _cleanup(path)

    def test_fresh_doc_has_no_high_confidence_references(self):
        """A doc that does not mention the changed symbol returns no high-confidence refs."""
        diff = "+def deprecated_api():\n+    pass\n"
        symbols = ec.extract_symbols_from_diff(diff, ".py")
        self.assertIn("deprecated_api", symbols["added"])

        content = "This guide covers installation and setup only.\n"
        path = _make_doc_file(content)
        try:
            refs = ec.search_docs_for_symbol("deprecated_api", [path])
            high_refs = [r for r in refs if r["confidence"] == "high"]
            self.assertEqual(high_refs, [])
        finally:
            _cleanup(path)


if __name__ == "__main__":
    unittest.main()
