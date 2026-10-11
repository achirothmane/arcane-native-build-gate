import importlib.util
import pathlib
import sys
import unittest

SRC = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "apply_candidates.py"
spec = importlib.util.spec_from_file_location("patch_candidates", SRC)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)

class StrictPatcherTests(unittest.TestCase):
    def test_refuses_missing(self):
        with self.assertRaisesRegex(ValueError, "found 0"):
            m.replace_exact("unrelated source", "specific anchor", "replacement")
    def test_refuses_ambiguous(self):
        with self.assertRaisesRegex(ValueError, "found 2"):
            m.replace_exact("old old", "old", "new")
    def test_replaces_unique(self):
        self.assertEqual(m.replace_exact("prefix OLD suffix", "OLD", "NEW"), "prefix NEW suffix")
    def test_known_versions_and_blobs(self):
        self.assertEqual(len(m.VERSIONS), 3)
        for v in m.VERSIONS:
            self.assertEqual(len(m.VERSIONS[v]["commit"]), 40)
            self.assertGreater(len(m.REPLACEMENTS[v]), 0)
            for sha in m.VERSIONS[v]["file_blobs"].values():
                self.assertEqual(len(sha), 40)
    def test_role_anchor(self):
        a = m.REPLACEMENTS["v2.14.0"][0].needle
        self.assertIn('type="button"\n' + '\t'*7 + 'class="w-full"', a)
        self.assertIn('icon={CopyIcon}', a)
    def test_nav_anchors(self):
        names = [v.path for v in m.REPLACEMENTS["v2.10.2"]]
        self.assertEqual(names.count(m.NAV_ITEM), 2)
        self.assertEqual(names.count(m.NAV), 1)

if __name__ == "__main__":
    unittest.main()
