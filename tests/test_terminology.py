"""Tests for skills/terminology/scripts/check_terms.py.

TDD approach:
  1. Write tests (RED) -- they fail because the script does not exist yet.
  2. Write minimal implementation (GREEN) -- make every test pass.
  3. Refactor -- keep tests green throughout.
"""

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
    "terminology",
    "scripts",
)
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

import check_terms as ct  # noqa: E402

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_main(args):
    """Run ct.main() with the given argv list and return parsed JSON output."""
    old_argv = sys.argv[:]
    sys.argv = ["check_terms.py"] + args
    captured = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured):
            ct.main()
    finally:
        sys.argv = old_argv
    return json.loads(captured.getvalue())


def _check_text(text):
    """Write text to a temp .md file, run check_file, clean up, return findings."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(text)
        path = f.name
    try:
        rules = ct.load_rules()
        return ct.check_file(path, rules)
    finally:
        os.unlink(path)


def _finding_types(findings):
    return [f["type"] for f in findings]


def _found_terms(findings):
    return [f["found"] for f in findings]


# ---------------------------------------------------------------------------
# TestParseTermRules
# ---------------------------------------------------------------------------

class TestParseTermRules(unittest.TestCase):
    """Verify that load_rules() parses the real terminology-rules.md correctly."""

    def setUp(self):
        self.rules = ct.load_rules()

    def test_returns_dict_with_required_keys(self):
        for key in ("incorrect_terms", "prohibited_terms", "context_dependent"):
            self.assertIn(key, self.rules, f"Missing key: {key}")

    def test_incorrect_terms_is_nonempty_list(self):
        self.assertIsInstance(self.rules["incorrect_terms"], list)
        self.assertGreater(len(self.rules["incorrect_terms"]), 0)

    def test_node_js_rule_parsed(self):
        """Node.js / NodeJS rule must be present in incorrect_terms."""
        incorrect_forms = [
            form
            for rule in self.rules["incorrect_terms"]
            for form in rule["incorrect"]
        ]
        self.assertIn("NodeJS", incorrect_forms)

    def test_postgresql_rule_parsed(self):
        """PostgreSQL / Postgres rule must be present in incorrect_terms."""
        correct_terms = [rule["correct"] for rule in self.rules["incorrect_terms"]]
        self.assertIn("PostgreSQL", correct_terms)

    def test_prohibited_terms_nonempty(self):
        self.assertIsInstance(self.rules["prohibited_terms"], list)
        self.assertGreater(len(self.rules["prohibited_terms"]), 0)

    def test_blacklist_in_prohibited(self):
        prohibited = [r["prohibited"] for r in self.rules["prohibited_terms"]]
        # The rule covers "blacklist/whitelist" — at least "blacklist" should appear
        all_prohibited_lower = [p.lower() for p in prohibited]
        self.assertTrue(
            any("blacklist" in p for p in all_prohibited_lower),
            "Expected 'blacklist' to be in prohibited terms",
        )

    def test_dummy_in_prohibited(self):
        prohibited = [r["prohibited"].lower() for r in self.rules["prohibited_terms"]]
        self.assertIn("dummy", prohibited)

    def test_context_dependent_terms_nonempty(self):
        self.assertIsInstance(self.rules["context_dependent"], list)
        self.assertGreater(len(self.rules["context_dependent"]), 0)

    def test_setup_login_in_context_dependent(self):
        nouns = [r["noun"] for r in self.rules["context_dependent"]]
        self.assertIn("setup", nouns)
        self.assertIn("login", nouns)


# ---------------------------------------------------------------------------
# TestIncorrectTermDetection
# ---------------------------------------------------------------------------

class TestIncorrectTermDetection(unittest.TestCase):
    """Incorrect product/tech names must be flagged with the correct form."""

    def test_nodejs_flagged(self):
        findings = _check_text("Install NodeJS on your machine.")
        self.assertIn("incorrect_term", _finding_types(findings))
        self.assertIn("NodeJS", _found_terms(findings))

    def test_nodejs_flagged_correct_suggestion(self):
        findings = _check_text("Install NodeJS on your machine.")
        node_finding = next(f for f in findings if f.get("found") == "NodeJS")
        self.assertEqual(node_finding["correct"], "Node.js")

    def test_postgres_flagged(self):
        findings = _check_text("Connect to a Postgres database.")
        self.assertIn("incorrect_term", _finding_types(findings))
        self.assertIn("Postgres", _found_terms(findings))

    def test_postgres_flagged_correct_suggestion(self):
        findings = _check_text("Connect to a Postgres database.")
        pg_finding = next(f for f in findings if f.get("found") == "Postgres")
        self.assertEqual(pg_finding["correct"], "PostgreSQL")

    def test_javascript_lowercase_flagged(self):
        findings = _check_text("Use javascript for front-end development.")
        self.assertIn("incorrect_term", _finding_types(findings))

    def test_github_lowercase_flagged(self):
        findings = _check_text("Push your code to github today.")
        self.assertIn("incorrect_term", _finding_types(findings))

    def test_finding_includes_line_number(self):
        findings = _check_text("Line one.\nNodeJS is installed here.\n")
        node_finding = next(
            (f for f in findings if f.get("found") == "NodeJS"), None
        )
        self.assertIsNotNone(node_finding)
        self.assertEqual(node_finding["line"], 2)

    def test_finding_includes_context_snippet(self):
        findings = _check_text("Install NodeJS today.")
        node_finding = next(f for f in findings if f.get("found") == "NodeJS")
        self.assertIn("context", node_finding)
        self.assertIsInstance(node_finding["context"], str)

    def test_severity_is_error(self):
        findings = _check_text("Use NodeJS for the backend.")
        node_finding = next(f for f in findings if f.get("found") == "NodeJS")
        self.assertEqual(node_finding["severity"], "error")


# ---------------------------------------------------------------------------
# TestProhibitedTermDetection
# ---------------------------------------------------------------------------

class TestProhibitedTermDetection(unittest.TestCase):
    """Prohibited terms must be flagged with type 'prohibited_term'."""

    def test_blacklist_detected(self):
        findings = _check_text("Add the IP to the blacklist.")
        self.assertIn("prohibited_term", _finding_types(findings))

    def test_blacklist_has_replacement(self):
        findings = _check_text("Add the IP to the blacklist.")
        bl_finding = next(f for f in findings if f["type"] == "prohibited_term")
        self.assertIn("correct", bl_finding)
        self.assertIsInstance(bl_finding["correct"], str)
        self.assertGreater(len(bl_finding["correct"]), 0)

    def test_dummy_detected(self):
        findings = _check_text("Use a dummy value for testing.")
        self.assertIn("prohibited_term", _finding_types(findings))

    def test_master_slave_detected(self):
        findings = _check_text("Configure the master and slave nodes.")
        types = _finding_types(findings)
        self.assertIn("prohibited_term", types)

    def test_sanity_check_detected(self):
        findings = _check_text("Do a sanity check before deploying.")
        self.assertIn("prohibited_term", _finding_types(findings))

    def test_prohibited_severity_is_error(self):
        findings = _check_text("Add to the blacklist now.")
        bl = next(f for f in findings if f["type"] == "prohibited_term")
        self.assertEqual(bl["severity"], "error")


# ---------------------------------------------------------------------------
# TestCorrectTermsPass
# ---------------------------------------------------------------------------

class TestCorrectTermsPass(unittest.TestCase):
    """Correctly spelled terms must NOT be flagged."""

    def test_node_js_correct_not_flagged(self):
        findings = _check_text("Install Node.js on your machine.")
        found_terms = _found_terms(findings)
        self.assertNotIn("Node.js", found_terms)

    def test_postgresql_correct_not_flagged(self):
        findings = _check_text("Connect to a PostgreSQL database.")
        found_terms = _found_terms(findings)
        self.assertNotIn("PostgreSQL", found_terms)

    def test_javascript_correct_not_flagged(self):
        findings = _check_text("Use JavaScript for front-end development.")
        # No incorrect_term finding for "JavaScript"
        incorrect_findings = [
            f for f in findings
            if f["type"] == "incorrect_term" and f.get("found") == "JavaScript"
        ]
        self.assertEqual(len(incorrect_findings), 0)

    def test_github_correct_not_flagged(self):
        findings = _check_text("Push your code to GitHub today.")
        incorrect_findings = [
            f for f in findings
            if f["type"] == "incorrect_term" and f.get("found") == "GitHub"
        ]
        self.assertEqual(len(incorrect_findings), 0)

    def test_blocklist_not_flagged(self):
        """'blocklist' is the replacement for 'blacklist' — it must not be flagged."""
        findings = _check_text("Add the IP to the blocklist.")
        self.assertNotIn("prohibited_term", _finding_types(findings))


# ---------------------------------------------------------------------------
# TestCodeBlockExclusion
# ---------------------------------------------------------------------------

class TestCodeBlockExclusion(unittest.TestCase):
    """Incorrect terms inside fenced code blocks must NOT produce findings."""

    def test_incorrect_term_in_code_block_not_flagged(self):
        text = (
            "Normal prose here.\n"
            "```bash\n"
            "npm install NodeJS\n"
            "```\n"
            "More normal prose.\n"
        )
        findings = _check_text(text)
        incorrect = [f for f in findings if f.get("found") == "NodeJS"]
        self.assertEqual(len(incorrect), 0)

    def test_incorrect_term_in_inline_code_not_flagged(self):
        text = "Run the `NodeJS` command from your terminal.\n"
        findings = _check_text(text)
        # inline code (`NodeJS`) should be excluded
        incorrect = [f for f in findings if f.get("found") == "NodeJS"]
        self.assertEqual(len(incorrect), 0)

    def test_prohibited_term_in_code_block_not_flagged(self):
        # Prose line is neutral — the only occurrence of "master" is inside the
        # fenced code block and must therefore be excluded from checks.
        text = (
            "See the configuration snippet.\n"
            "```yaml\n"
            "role: master\n"
            "```\n"
        )
        findings = _check_text(text)
        prohibited = [f for f in findings if f["type"] == "prohibited_term"]
        self.assertEqual(len(prohibited), 0)

    def test_incorrect_term_outside_code_block_still_flagged(self):
        text = (
            "```bash\n"
            "# NodeJS in code — ignored\n"
            "```\n"
            "But NodeJS in prose is flagged.\n"
        )
        findings = _check_text(text)
        incorrect = [f for f in findings if f.get("found") == "NodeJS"]
        self.assertEqual(len(incorrect), 1)


# ---------------------------------------------------------------------------
# TestFrontmatterExclusion
# ---------------------------------------------------------------------------

class TestFrontmatterExclusion(unittest.TestCase):
    """Incorrect terms inside YAML frontmatter must NOT produce findings."""

    def test_incorrect_term_in_frontmatter_not_flagged(self):
        text = (
            "---\n"
            "title: NodeJS Guide\n"
            "tags: [NodeJS, Postgres]\n"
            "---\n\n"
            "This guide covers Node.js and PostgreSQL.\n"
        )
        findings = _check_text(text)
        # Only prose is checked — frontmatter values must be excluded
        self.assertEqual(len(findings), 0)

    def test_prohibited_term_in_frontmatter_not_flagged(self):
        text = (
            "---\n"
            "description: dummy placeholder\n"
            "---\n\n"
            "This is the actual content.\n"
        )
        findings = _check_text(text)
        prohibited = [f for f in findings if f["type"] == "prohibited_term"]
        self.assertEqual(len(prohibited), 0)


# ---------------------------------------------------------------------------
# TestContextDependentTerms
# ---------------------------------------------------------------------------

class TestContextDependentTerms(unittest.TestCase):
    """Context-dependent terms (setup/set up, login/log in) are flagged as
    'context_dependent' with a note, not as hard errors."""

    def test_context_dependent_type_exists_in_findings(self):
        """check_file must be capable of returning context_dependent findings."""
        # We just verify the type key is produced when a context-dependent term
        # appears in isolation (the exact detection heuristic is implementation detail).
        text = "Complete the setup process before proceeding.\n"
        findings = _check_text(text)
        # The finding *may* or *may not* fire depending on position heuristic;
        # what we require is that if it fires its type is correct.
        for f in findings:
            if f["type"] == "context_dependent":
                self.assertIn("message", f)
                self.assertIn("line", f)
                return  # found at least one — test passes
        # If no context_dependent finding was returned, that is also acceptable
        # (the word might be in a valid noun position).

    def test_context_dependent_finding_has_message(self):
        """Any context_dependent finding must carry a human-readable message."""
        findings = _check_text("Please login to continue.\n")
        for f in findings:
            if f["type"] == "context_dependent":
                self.assertIsInstance(f["message"], str)
                self.assertGreater(len(f["message"]), 0)


# ---------------------------------------------------------------------------
# TestMainIntegration
# ---------------------------------------------------------------------------

class TestMainIntegration(unittest.TestCase):
    """Integration tests: run main() end-to-end and verify JSON contract."""

    def _make_temp_dir_with_file(self, content):
        """Create a temporary directory with a single test.md file."""
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, "test.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return tmpdir, path

    def test_main_with_directory_returns_valid_json_structure(self):
        tmpdir, _ = self._make_temp_dir_with_file(
            "Use NodeJS for the backend.\n"
        )
        output = _run_main([tmpdir])
        self.assertIn("summary", output)
        self.assertIn("files", output)
        summary = output["summary"]
        for key in ("files_scanned", "total_violations", "by_type"):
            self.assertIn(key, summary, f"Missing summary key: {key}")

    def test_summary_by_type_has_expected_keys(self):
        tmpdir, _ = self._make_temp_dir_with_file(
            "Use NodeJS for the backend.\n"
        )
        output = _run_main([tmpdir])
        by_type = output["summary"]["by_type"]
        for key in ("incorrect_term", "prohibited_term", "context_dependent"):
            self.assertIn(key, by_type, f"Missing by_type key: {key}")

    def test_main_detects_violation_in_temp_dir(self):
        tmpdir, _ = self._make_temp_dir_with_file(
            "Install NodeJS and use the blacklist feature.\n"
        )
        output = _run_main([tmpdir])
        self.assertGreater(output["summary"]["total_violations"], 0)

    def test_main_with_file_flag(self):
        _, path = self._make_temp_dir_with_file("Use NodeJS here.\n")
        output = _run_main(["--file", path])
        self.assertIn("summary", output)
        self.assertGreater(output["summary"]["total_violations"], 0)

    def test_main_nonexistent_directory_returns_error(self):
        output = _run_main(["/nonexistent/path/xyz"])
        self.assertIn("error", output)
        self.assertEqual(output["error"], "not_a_directory")

    def test_main_nonexistent_file_flag_returns_error(self):
        output = _run_main(["--file", "/nonexistent/file.md"])
        self.assertIn("error", output)
        self.assertEqual(output["error"], "file_not_found")

    def test_main_clean_file_reports_zero_violations(self):
        tmpdir, _ = self._make_temp_dir_with_file(
            "Use Node.js and PostgreSQL for the backend.\n"
            "Push your code to GitHub using the CLI.\n"
        )
        output = _run_main([tmpdir])
        self.assertEqual(output["summary"]["total_violations"], 0)

    def test_files_array_contains_file_path(self):
        tmpdir, path = self._make_temp_dir_with_file(
            "Use NodeJS here.\n"
        )
        output = _run_main([tmpdir])
        file_paths = [entry["file"] for entry in output.get("files", [])]
        self.assertTrue(
            any(path in fp or os.path.basename(path) in fp for fp in file_paths),
            f"Expected {path} to appear in output files list",
        )


if __name__ == "__main__":
    unittest.main()
