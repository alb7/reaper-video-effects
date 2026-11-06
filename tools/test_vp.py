"""Tests for tools/vp.py.  Run:  python3 -m unittest discover -s tools"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import vp  # noqa: E402

P = pathlib.Path("t.eel")


def code_msgs(src):
    return [f.msg for f in vp.check_code(P, vp.strip_comments_and_strings(src))]


def param_msgs(*lines):
    return [f.msg for f in vp.check_params(P, list(enumerate(lines, 1)))]


class TernaryRules(unittest.TestCase):
    def test_unparenthesized_rhs_ternary_flagged(self):
        self.assertTrue(any("right of an assignment" in m for m in code_msgs("x = a ? 1 : 2;")))

    def test_parenthesized_rhs_ternary_ok(self):
        self.assertEqual(code_msgs("x = (a ? 1 : 2);"), [])

    def test_assignment_in_branch_flagged(self):
        self.assertTrue(any("inside a ternary branch" in m for m in code_msgs("a ? b : c = 0;")))

    def test_parenthesized_branch_ok(self):
        self.assertEqual(code_msgs("a ? (b = 1) : (c = 0);"), [])

    def test_statement_separator_resets(self):
        self.assertEqual(code_msgs("a ? b : c; x = 1;"), [])

    def test_comparisons_are_not_assignments(self):
        self.assertEqual(code_msgs("(a == 1 && b <= 2 && c >= 3 && d != 4) ? (e = 1);"), [])

    def test_compound_assignment(self):
        self.assertTrue(code_msgs("y += a ? 1 : 2;"))


class Structure(unittest.TestCase):
    def test_unbalanced(self):
        self.assertTrue(any("never closed" in m for m in code_msgs("loop(3, x += 1;")))
        self.assertTrue(any("unmatched" in m for m in code_msgs("x = 1);")))

    def test_case_clash(self):
        self.assertTrue(any("ignore case" in m for m in code_msgs("t = 1; T = 2;")))

    def test_comments_and_strings_ignored(self):
        self.assertEqual(code_msgs('// x = a ? 1 : 2\n/* T t */ s = "a ? b = c";'), [])


class Params(unittest.TestCase):
    def test_good(self):
        self.assertEqual(param_msgs("//@param1:size 'Size' 0.5 0 1 0.5 0.01"), [])

    def test_space_after_param_ok(self):
        self.assertEqual(param_msgs("//@param 1:size 'Size' 0.5 0 1"), [])

    def test_default_out_of_range(self):
        self.assertTrue(param_msgs("//@param1:size 'Size' 2 0 1"))

    def test_duplicate_index_and_var(self):
        msgs = param_msgs("//@param1:a 'A' 0 0 1", "//@param1:A 'B' 0 0 1")
        self.assertTrue(any("index 1 already" in m for m in msgs))
        self.assertTrue(any("already used" in m and "ignore case" in m for m in msgs))

    def test_builtin_clash(self):
        self.assertTrue(param_msgs("//@param1:time 'T' 0 0 1"))

    def test_missing_var(self):
        self.assertTrue(param_msgs("//@param1 'Size' 0 0 1"))


class RealScripts(unittest.TestCase):
    def test_repo_is_clean(self):
        found = vp.check_repo()
        self.assertEqual([str(f) for f in found], [])


if __name__ == "__main__":
    unittest.main()
