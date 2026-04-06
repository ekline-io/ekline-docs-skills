"""Tests for skills/changelog/scripts/parse_commits.py."""

import os
import sys
import unittest

# Add the script directory to sys.path so we can import the module directly.
SCRIPT_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "skills",
    "changelog",
    "scripts",
)
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

import parse_commits as p  # noqa: E402


class TestClassifyConventional(unittest.TestCase):
    """classify_conventional parses Conventional Commit subjects."""

    def test_feat_returns_added_category(self):
        category, description, breaking = p.classify_conventional("feat: add login")
        self.assertEqual(category, "Added")
        self.assertEqual(description, "add login")
        self.assertFalse(breaking)

    def test_fix_with_scope_returns_fixed_category(self):
        category, description, breaking = p.classify_conventional(
            "fix(auth): resolve timeout"
        )
        self.assertEqual(category, "Fixed")
        self.assertEqual(description, "resolve timeout")
        self.assertFalse(breaking)

    def test_breaking_bang_sets_breaking_flag(self):
        category, description, breaking = p.classify_conventional(
            "feat!: breaking change"
        )
        self.assertEqual(category, "Added")
        self.assertEqual(description, "breaking change")
        self.assertTrue(breaking)

    def test_chore_returns_skip_category(self):
        category, description, breaking = p.classify_conventional("chore: update deps")
        self.assertEqual(category, "skip")
        self.assertEqual(description, "update deps")
        self.assertFalse(breaking)

    def test_docs_returns_documentation_category(self):
        category, description, breaking = p.classify_conventional(
            "docs: update README"
        )
        self.assertEqual(category, "Documentation")
        self.assertEqual(description, "update README")
        self.assertFalse(breaking)

    def test_non_conventional_returns_none_triple(self):
        category, description, breaking = p.classify_conventional(
            "random text not conventional"
        )
        self.assertIsNone(category)
        self.assertIsNone(description)
        self.assertFalse(breaking)


class TestClassifyKeyword(unittest.TestCase):
    """classify_keyword maps commit subjects to categories via heuristics."""

    def test_add_prefix_returns_added(self):
        self.assertEqual(p.classify_keyword("add new feature"), "Added")

    def test_fix_prefix_returns_fixed(self):
        self.assertEqual(p.classify_keyword("fix bug in parser"), "Fixed")

    def test_remove_prefix_returns_removed(self):
        self.assertEqual(p.classify_keyword("remove deprecated API"), "Removed")

    def test_breaking_change_keyword_returns_breaking_changes(self):
        self.assertEqual(
            p.classify_keyword("BREAKING CHANGE: new auth flow"), "Breaking Changes"
        )

    def test_update_prefix_returns_changed(self):
        self.assertEqual(p.classify_keyword("update dependencies"), "Changed")

    def test_unknown_subject_defaults_to_changed(self):
        self.assertEqual(p.classify_keyword("miscellaneous housekeeping"), "Changed")


class TestClassifyCommit(unittest.TestCase):
    """classify_commit integrates conventional parsing, body inspection, and keyword
    fallback to produce (category, description) pairs."""

    def test_conventional_with_breaking_change_in_body(self):
        commit = {
            "subject": "feat: new authentication flow",
            "body": "BREAKING CHANGE: old tokens are no longer accepted",
        }
        category, description = p.classify_commit(commit)
        self.assertEqual(category, "Breaking Changes")
        self.assertEqual(description, "new authentication flow")

    def test_non_conventional_falls_back_to_keyword(self):
        commit = {
            "subject": "fix critical crash on startup",
            "body": "",
        }
        category, description = p.classify_commit(commit)
        self.assertEqual(category, "Fixed")
        self.assertEqual(description, "fix critical crash on startup")

    def test_unknown_subject_defaults_to_changed(self):
        commit = {
            "subject": "miscellaneous housekeeping",
            "body": "",
        }
        category, description = p.classify_commit(commit)
        self.assertEqual(category, "Changed")
        self.assertEqual(description, "miscellaneous housekeeping")


class TestDeduplicate(unittest.TestCase):
    """deduplicate merges entries whose descriptions normalise to the same text."""

    def _make_entry(self, description, prs=None, issues=None):
        return {
            "hash": "abc12345",
            "description": description,
            "author": "Test Author",
            "date": "2024-01-01T00:00:00Z",
            "refs": {"prs": prs or [], "issues": issues or []},
            "original_subject": description,
        }

    def test_duplicate_descriptions_collapse_to_one_entry(self):
        entries = [
            self._make_entry("add login feature", prs=["42"]),
            self._make_entry("add login feature", prs=["43"]),
        ]
        result = p.deduplicate(entries)
        self.assertEqual(len(result), 1)

    def test_duplicate_pr_refs_are_merged(self):
        entries = [
            self._make_entry("add login feature", prs=["42"]),
            self._make_entry("add login feature", prs=["43"]),
        ]
        result = p.deduplicate(entries)
        merged_prs = set(result[0]["refs"]["prs"])
        self.assertIn("42", merged_prs)
        self.assertIn("43", merged_prs)

    def test_pr_ref_in_description_still_deduplicates(self):
        # Both descriptions normalise to the same text once the "(#N)" suffix is
        # stripped, confirming the regex fix that handles mid-string PR refs too.
        entries = [
            self._make_entry("add login feature (#42)"),
            self._make_entry("add login feature (#43)"),
        ]
        result = p.deduplicate(entries)
        self.assertEqual(len(result), 1)

    def test_different_descriptions_both_kept(self):
        entries = [
            self._make_entry("add login feature"),
            self._make_entry("fix session expiry"),
        ]
        result = p.deduplicate(entries)
        self.assertEqual(len(result), 2)


class TestFormatEntry(unittest.TestCase):
    """format_entry produces a clean, human-readable changelog line."""

    def _make_entry(self, description, prs=None):
        return {
            "description": description,
            "refs": {"prs": prs or [], "issues": []},
        }

    def test_conventional_prefix_stripped_from_description(self):
        # format_entry strips the "feat: " prefix and capitalises the first letter.
        entry = self._make_entry("feat: add user authentication")
        result = p.format_entry(entry)
        self.assertFalse(result.startswith("feat:"))
        self.assertIn("Add user authentication", result)

    def test_pr_ref_appended_in_parentheses(self):
        entry = self._make_entry("add user authentication", prs=["42"])
        result = p.format_entry(entry)
        self.assertIn("(#42)", result)

    def test_first_letter_capitalised(self):
        entry = self._make_entry("add user authentication")
        result = p.format_entry(entry)
        self.assertTrue(result[0].isupper())

    def test_existing_pr_number_in_description_not_duplicated(self):
        # The inline "(#42)" in the description is stripped before the ref is
        # re-appended, so it should appear exactly once.
        entry = self._make_entry("add user authentication (#42)", prs=["42"])
        result = p.format_entry(entry)
        self.assertEqual(result.count("(#42)"), 1)


class TestExtractPrIssueRefs(unittest.TestCase):
    """extract_pr_issue_refs finds PR numbers and closing issue references."""

    def test_bare_pr_number_after_space_extracted(self):
        # The PR regex matches "#N" when preceded by whitespace or start-of-line.
        # A bare " #42" at the end of a subject is the canonical extractable form.
        refs = p.extract_pr_issue_refs("feat: add login #42")
        self.assertIn("42", refs["prs"])

    def test_pr_number_in_parentheses_not_extracted_by_this_function(self):
        # "(#42)" has "(" before "#", which the PR regex does not match.
        # Parenthesised refs are stripped/re-appended by format_entry, not extracted here.
        refs = p.extract_pr_issue_refs("feat: add login (#42)")
        self.assertNotIn("42", refs["prs"])

    def test_multiple_closing_keywords_extract_issues(self):
        refs = p.extract_pr_issue_refs("fixes #10 and closes #20")
        self.assertIn("10", refs["issues"])
        self.assertIn("20", refs["issues"])

    def test_no_refs_returns_empty_lists(self):
        refs = p.extract_pr_issue_refs("no refs here")
        self.assertEqual(refs["prs"], [])
        self.assertEqual(refs["issues"], [])

    def test_merge_pull_request_line_extracts_pr(self):
        refs = p.extract_pr_issue_refs("Merge pull request #99 from org/branch")
        self.assertIn("99", refs["prs"])


class TestSecurityClassification(unittest.TestCase):
    """Keyword rules correctly route security-related commits to the Security category."""

    def test_vulnerability_keyword_classified_as_security(self):
        self.assertEqual(p.classify_keyword("fix vulnerability in auth"), "Security")

    def test_cve_identifier_classified_as_security(self):
        self.assertEqual(p.classify_keyword("fix CVE-2024-1234"), "Security")

    def test_security_prefix_classified_as_security(self):
        self.assertEqual(p.classify_keyword("security patch for XSS"), "Security")


if __name__ == "__main__":
    unittest.main()
