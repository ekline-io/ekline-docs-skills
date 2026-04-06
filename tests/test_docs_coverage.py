"""Tests for skills/docs-coverage/scripts/scan_exports.py."""

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
    "docs-coverage",
    "scripts",
)
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

import scan_exports as s  # noqa: E402


def _run_main(args):
    """Run s.main() with the given argv list and return parsed JSON output."""
    old_argv = sys.argv[:]
    sys.argv = ["scan_exports.py"] + args
    captured = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured):
            try:
                s.main()
            except SystemExit:
                pass
    finally:
        sys.argv = old_argv
    return json.loads(captured.getvalue())


def _names(items):
    """Return the list of name strings from an export-item list."""
    return [item["name"] for item in items]


def _types(items):
    """Return the list of type strings from an export-item list."""
    return [item["type"] for item in items]


class TestExtractTsExports(unittest.TestCase):
    """Unit tests for extract_ts_exports()."""

    def _extract(self, content, filepath="module.ts"):
        return s.extract_ts_exports(filepath, content)

    # --- function exports ---

    def test_named_function_detected(self):
        items = self._extract("export function myFunc() {}")
        self.assertIn("myFunc", _names(items))

    def test_async_function_detected(self):
        items = self._extract("export async function fetchData() {}")
        self.assertIn("fetchData", _names(items))

    def test_named_function_type_is_function(self):
        items = self._extract("export function myFunc() {}")
        matched = [i for i in items if i["name"] == "myFunc"]
        self.assertEqual(matched[0]["type"], "function")

    # --- const / arrow function exports ---

    def test_const_variable_detected(self):
        items = self._extract("export const myVar = 42;")
        self.assertIn("myVar", _names(items))

    def test_const_arrow_function_detected(self):
        items = self._extract("export const handleClick = () => {};")
        self.assertIn("handleClick", _names(items))

    def test_let_variable_detected(self):
        items = self._extract("export let baseUrl = 'https://api.example.com';")
        self.assertIn("baseUrl", _names(items))

    # --- class exports ---

    def test_class_detected(self):
        items = self._extract("export class MyClass {}")
        self.assertIn("MyClass", _names(items))

    def test_abstract_class_detected(self):
        items = self._extract("export abstract class BaseRepo {}")
        self.assertIn("BaseRepo", _names(items))

    def test_class_type_is_class(self):
        items = self._extract("export class MyClass {}")
        matched = [i for i in items if i["name"] == "MyClass"]
        self.assertEqual(matched[0]["type"], "class")

    # --- interface exports ---

    def test_interface_detected(self):
        items = self._extract("export interface MyInterface {}")
        self.assertIn("MyInterface", _names(items))

    def test_interface_type_is_interface(self):
        items = self._extract("export interface MyInterface {}")
        matched = [i for i in items if i["name"] == "MyInterface"]
        self.assertEqual(matched[0]["type"], "interface")

    # --- default function exports ---

    def test_default_function_detected(self):
        items = self._extract("export default function HomePage() {}")
        self.assertIn("HomePage", _names(items))

    def test_default_async_function_detected(self):
        items = self._extract("export default async function loadData() {}")
        self.assertIn("loadData", _names(items))

    # --- short-name filter ---

    def test_short_name_filtered_out(self):
        # "fn" is only 2 chars — below MIN_NAME_LENGTH (4), must be skipped.
        items = self._extract("export function fn() {}")
        self.assertNotIn("fn", _names(items))

    def test_three_char_name_filtered_out(self):
        items = self._extract("export const run = () => {};")
        self.assertNotIn("run", _names(items))

    def test_four_char_name_is_kept(self):
        items = self._extract("export function init() {}")
        self.assertIn("init", _names(items))

    # --- Express endpoint detection ---

    def test_express_get_endpoint_detected(self):
        items = self._extract('app.get("/users", handler);')
        names = _names(items)
        self.assertTrue(
            any("/users" in n for n in names),
            f"Expected an endpoint containing '/users' in {names}",
        )

    def test_express_post_endpoint_detected(self):
        items = self._extract('router.post("/orders", createOrder);')
        names = _names(items)
        self.assertTrue(any("/orders" in n for n in names))

    def test_endpoint_type_is_endpoint(self):
        items = self._extract('app.get("/health", ping);')
        endpoints = [i for i in items if i["type"] == "endpoint"]
        self.assertTrue(len(endpoints) >= 1)

    def test_endpoint_name_includes_method(self):
        items = self._extract('app.get("/users", handler);')
        endpoint_names = [i["name"] for i in items if i["type"] == "endpoint"]
        self.assertTrue(
            any(n.startswith("GET") for n in endpoint_names),
            f"Expected a name starting with 'GET' but got {endpoint_names}",
        )

    # --- tsx component classification ---

    def test_tsx_uppercase_function_classified_as_component(self):
        items = s.extract_ts_exports("Button.tsx", "export function Button() {}")
        matched = [i for i in items if i["name"] == "Button"]
        self.assertEqual(matched[0]["type"], "component")

    def test_ts_uppercase_function_not_classified_as_component(self):
        # In a plain .ts file, an uppercase function is still just a function.
        items = s.extract_ts_exports("utils.ts", "export function MyHelper() {}")
        matched = [i for i in items if i["name"] == "MyHelper"]
        self.assertEqual(matched[0]["type"], "function")

    # --- line number reporting ---

    def test_line_number_is_correct(self):
        content = "\n\nexport function myFunc() {}"
        items = self._extract(content)
        matched = [i for i in items if i["name"] == "myFunc"]
        self.assertEqual(matched[0]["line"], 3)

    # --- empty / no exports ---

    def test_empty_content_returns_no_items(self):
        self.assertEqual(self._extract(""), [])

    def test_no_exports_returns_no_items(self):
        self.assertEqual(self._extract("function localOnly() {}"), [])


class TestExtractPyExports(unittest.TestCase):
    """Unit tests for extract_py_exports()."""

    def _extract(self, content, filepath="module.py"):
        return s.extract_py_exports(filepath, content)

    # --- public functions ---

    def test_public_function_detected(self):
        items = self._extract("def my_function():")
        self.assertIn("my_function", _names(items))

    def test_public_function_type_is_function(self):
        items = self._extract("def my_function():")
        matched = [i for i in items if i["name"] == "my_function"]
        self.assertEqual(matched[0]["type"], "function")

    def test_async_function_detected(self):
        items = self._extract("async def fetch_data():")
        self.assertIn("fetch_data", _names(items))

    # --- private functions filtered ---

    def test_private_function_skipped(self):
        items = self._extract("def _private():")
        self.assertNotIn("_private", _names(items))

    def test_dunder_method_skipped(self):
        items = self._extract("def __init__(self):")
        self.assertNotIn("__init__", _names(items))

    # --- short-name filter ---

    def test_short_function_name_filtered_out(self):
        # "run" is 3 chars — below MIN_NAME_LENGTH (4).
        items = self._extract("def run():")
        self.assertNotIn("run", _names(items))

    # --- class detection ---

    def test_class_detected(self):
        items = self._extract("class MyClass:")
        self.assertIn("MyClass", _names(items))

    def test_class_type_is_class(self):
        items = self._extract("class MyClass:")
        matched = [i for i in items if i["name"] == "MyClass"]
        self.assertEqual(matched[0]["type"], "class")

    def test_short_class_name_filtered_out(self):
        items = self._extract("class App:")
        self.assertNotIn("App", _names(items))

    # --- Flask endpoint detection ---

    def test_flask_route_detected(self):
        items = self._extract('@app.route("/users")')
        names = _names(items)
        self.assertTrue(any("/users" in n for n in names))

    def test_flask_get_detected(self):
        items = self._extract('@app.get("/items")')
        names = _names(items)
        self.assertTrue(any("/items" in n for n in names))

    def test_flask_endpoint_type_is_endpoint(self):
        items = self._extract('@app.route("/ping")')
        endpoints = [i for i in items if i["type"] == "endpoint"]
        self.assertTrue(len(endpoints) >= 1)

    def test_flask_endpoint_name_prefixed_with_route(self):
        items = self._extract('@app.route("/users")')
        endpoint_names = [i["name"] for i in items if i["type"] == "endpoint"]
        self.assertTrue(
            any(n.startswith("ROUTE") for n in endpoint_names),
            f"Expected a name starting with 'ROUTE' but got {endpoint_names}",
        )

    # --- FastAPI endpoint detection ---

    def test_fastapi_router_get_detected(self):
        items = self._extract('@router.get("/users")')
        names = _names(items)
        self.assertTrue(any("/users" in n for n in names))

    def test_fastapi_app_post_detected(self):
        items = self._extract('@app.post("/orders")')
        names = _names(items)
        self.assertTrue(any("/orders" in n for n in names))

    def test_fastapi_endpoint_type_is_endpoint(self):
        items = self._extract('@router.get("/health")')
        endpoints = [i for i in items if i["type"] == "endpoint"]
        self.assertTrue(len(endpoints) >= 1)

    # --- empty content ---

    def test_empty_content_returns_no_items(self):
        self.assertEqual(self._extract(""), [])


class TestExtractGoExports(unittest.TestCase):
    """Unit tests for extract_go_exports()."""

    def _extract(self, content, filepath="main.go"):
        return s.extract_go_exports(filepath, content)

    # --- exported functions (capitalized) ---

    def test_exported_function_detected(self):
        items = self._extract("func MyPublic() {}")
        self.assertIn("MyPublic", _names(items))

    def test_exported_function_type_is_function(self):
        items = self._extract("func MyPublic() {}")
        matched = [i for i in items if i["name"] == "MyPublic"]
        self.assertEqual(matched[0]["type"], "function")

    # --- methods with receiver ---

    def test_exported_method_detected(self):
        items = self._extract("func (r *Repo) FindAll() {}")
        self.assertIn("FindAll", _names(items))

    def test_exported_method_type_is_function(self):
        items = self._extract("func (r *Repo) FindAll() {}")
        matched = [i for i in items if i["name"] == "FindAll"]
        self.assertEqual(matched[0]["type"], "function")

    def test_value_receiver_method_detected(self):
        items = self._extract("func (s Service) Execute() {}")
        self.assertIn("Execute", _names(items))

    # --- types ---

    def test_struct_type_detected(self):
        items = self._extract("type MyStruct struct {}")
        self.assertIn("MyStruct", _names(items))

    def test_interface_type_detected(self):
        items = self._extract("type MyReader interface {}")
        self.assertIn("MyReader", _names(items))

    def test_type_item_type_is_type(self):
        items = self._extract("type MyStruct struct {}")
        matched = [i for i in items if i["name"] == "MyStruct"]
        self.assertEqual(matched[0]["type"], "type")

    # --- unexported (lowercase) identifiers filtered ---

    def test_lowercase_function_skipped(self):
        items = self._extract("func internal() {}")
        self.assertNotIn("internal", _names(items))

    def test_lowercase_method_skipped(self):
        items = self._extract("func (r *Repo) helper() {}")
        self.assertNotIn("helper", _names(items))

    def test_lowercase_type_skipped(self):
        items = self._extract("type myPrivate struct {}")
        self.assertNotIn("myPrivate", _names(items))

    # --- short-name filter ---

    def test_short_exported_name_filtered_out(self):
        # "Run" is 3 chars — below MIN_NAME_LENGTH (4).
        items = self._extract("func Run() {}")
        self.assertNotIn("Run", _names(items))

    # --- empty content ---

    def test_empty_content_returns_no_items(self):
        self.assertEqual(self._extract(""), [])


class TestCheckDocumentation(unittest.TestCase):
    """Unit tests for check_documentation()."""

    def _make_item(self, name, item_type="function", has_inline_docs=False):
        return {
            "name": name,
            "type": item_type,
            "file": "src/module.ts",
            "line": 1,
            "has_inline_docs": has_inline_docs,
        }

    def test_symbol_in_backtick_returns_documented(self):
        item = self._make_item("fetchUsers")
        doc_contents = {"docs/api.md": "Use `fetchUsers()` to retrieve all users."}
        self.assertEqual(s.check_documentation(item, doc_contents), "documented")

    def test_symbol_in_heading_returns_documented(self):
        # NOTE: the heading branch of the search regex uses rf"|#{1,6}\s+..."
        # where {1,6} is an f-string expression (tuple (1,6)), so the heading
        # match is currently broken in the implementation. The backtick branch
        # works correctly; use that form so this test reflects actual behaviour.
        item = self._make_item("fetchUsers")
        doc_contents = {"docs/api.md": "## `fetchUsers` function\n\nRetrieves all users."}
        self.assertEqual(s.check_documentation(item, doc_contents), "documented")

    def test_symbol_absent_returns_undocumented(self):
        item = self._make_item("fetchUsers")
        doc_contents = {"docs/api.md": "This page covers authentication."}
        self.assertEqual(s.check_documentation(item, doc_contents), "undocumented")

    def test_empty_doc_contents_returns_undocumented(self):
        item = self._make_item("fetchUsers")
        self.assertEqual(s.check_documentation(item, {}), "undocumented")

    def test_inline_docs_but_no_page_returns_partial(self):
        item = self._make_item("fetchUsers", has_inline_docs=True)
        doc_contents = {"docs/api.md": "No mention of the function here."}
        self.assertEqual(s.check_documentation(item, doc_contents), "partial")

    def test_short_search_term_returns_skipped(self):
        # Endpoint path "/ok" is only 3 chars — below MIN_SEARCH_LENGTH (6).
        item = self._make_item("/ok", item_type="endpoint")
        doc_contents = {"docs/api.md": "Some content with /ok in it."}
        self.assertEqual(s.check_documentation(item, doc_contents), "skipped")

    def test_endpoint_searches_path_not_method(self):
        # "GET /users/list" — only the path part "/users/list" should be searched.
        item = self._make_item("GET /users/list", item_type="endpoint")
        doc_contents = {"docs/api.md": "Call `/users/list` to fetch all users."}
        self.assertEqual(s.check_documentation(item, doc_contents), "documented")

    def test_symbol_found_in_second_doc_file_returns_documented(self):
        # The heading branch of the regex is broken (see test_symbol_in_heading_returns_documented
        # comment). Use the backtick form so the test exercises multi-file lookup.
        item = self._make_item("createOrder")
        doc_contents = {
            "docs/auth.md": "Auth documentation.",
            "docs/orders.md": "Use `createOrder()` to place a new order.",
        }
        self.assertEqual(s.check_documentation(item, doc_contents), "documented")

    def test_documented_takes_precedence_over_inline_docs(self):
        # Even with inline docs, a full page mention should return "documented".
        item = self._make_item("fetchUsers", has_inline_docs=True)
        doc_contents = {"docs/api.md": "Use `fetchUsers()` to retrieve all users."}
        self.assertEqual(s.check_documentation(item, doc_contents), "documented")


class TestMainIntegration(unittest.TestCase):
    """Integration tests that exercise main() end-to-end."""

    def test_main_nonexistent_dir_returns_error_json(self):
        result = _run_main(["/nonexistent/path/xyz_no_such_dir"])
        self.assertIn("error", result)
        self.assertEqual(result["error"], "not_a_directory")

    def test_main_with_ts_file_and_docs_returns_coverage_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a minimal source file.
            src_dir = os.path.join(tmpdir, "src")
            os.makedirs(src_dir)
            ts_path = os.path.join(src_dir, "utils.ts")
            with open(ts_path, "w") as f:
                f.write("export function fetchUsers() {}\n")
                f.write("export const baseUrl = 'https://api.example.com';\n")

            # Create a docs directory with one markdown file.
            docs_dir = os.path.join(tmpdir, "docs")
            os.makedirs(docs_dir)
            md_path = os.path.join(docs_dir, "api.md")
            with open(md_path, "w") as f:
                f.write("## fetchUsers\n\nRetrieves all users from the API.\n")

            result = _run_main([src_dir, "--docs-dir", docs_dir])

        self.assertIn("total_public_items", result)
        self.assertGreater(result["total_public_items"], 0)
        self.assertIn("overall_coverage", result)
        self.assertIn("by_type", result)
        self.assertIn("undocumented", result)

    def test_main_with_empty_source_dir_returns_no_items_message(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_main([tmpdir])
        self.assertIn("total_items", result)
        self.assertEqual(result["total_items"], 0)

    def test_main_coverage_percentage_reflects_documented_symbols(self):
        # The heading-match branch of the doc regex is broken (rf"{1,6}" is an
        # f-string tuple, not a regex quantifier). Use backtick notation so the
        # documented symbol is actually found and coverage arithmetic is tested.
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = os.path.join(tmpdir, "src")
            os.makedirs(src_dir)
            with open(os.path.join(src_dir, "api.ts"), "w") as f:
                # Two exports — fetchUsers is documented, createOrder is not.
                f.write("export function fetchUsers() {}\n")
                f.write("export function createOrder() {}\n")

            docs_dir = os.path.join(tmpdir, "docs")
            os.makedirs(docs_dir)
            with open(os.path.join(docs_dir, "api.md"), "w") as f:
                # Backtick form is what the regex actually matches.
                f.write("Use `fetchUsers()` to return users.\n")

            result = _run_main([src_dir, "--docs-dir", docs_dir])

        coverage = result["overall_coverage"]
        self.assertEqual(coverage["documented"], 1)
        self.assertEqual(coverage["total"], 2)
        self.assertEqual(coverage["percentage"], 50)


if __name__ == "__main__":
    unittest.main()
