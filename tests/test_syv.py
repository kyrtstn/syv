"""syv v5.3 stdlib test suite — run with: python -m unittest discover -s tests -v"""
import copy
import gzip
import json
import os
import shutil
import sys
import tempfile
import unittest

import importlib.machinery
import importlib.util

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYV_PATH = os.path.join(REPO_ROOT, "syv")

_loader = importlib.machinery.SourceFileLoader("syv_mod", SYV_PATH)
_spec = importlib.util.spec_from_loader("syv_mod", _loader)
syv = importlib.util.module_from_spec(_spec)
_loader.exec_module(syv)


class Base(unittest.TestCase):
    def setUp(self):
        self._config = copy.deepcopy(syv.CONFIG)
        self._dry = syv.DRY_RUN_MODE
        syv.DRY_RUN_MODE = False
        self.tmp = tempfile.mkdtemp(prefix="syv_test_")

    def tearDown(self):
        syv.CONFIG.clear()
        syv.CONFIG.update(self._config)
        syv.DRY_RUN_MODE = self._dry
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, content):
        fp = os.path.join(self.tmp, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        mode = "wb" if isinstance(content, bytes) else "w"
        with open(fp, mode, encoding=None if isinstance(content, bytes) else "utf-8") as f:
            f.write(content)
        return fp


class TestManifestKeys(Base):
    def test_relative_keys_avoid_collision(self):
        self.assertEqual(syv.manifest_key_for(os.path.join(self.tmp, "js", "app.js"), self.tmp), "js/app.js")
        self.assertEqual(syv.manifest_key_for(os.path.join(self.tmp, "admin", "app.js"), self.tmp), "admin/app.js")

    def test_validate_allows_subdir_rejects_traversal(self):
        syv.validate_manifest_keys({"js/app.js": "js/app.js?v=12345678", "a/b/c.css": "a/b/c.css?v=abcdef12"})
        for bad in ("../evil.js", "/abs.js", "~/x.js", "a\\b.js", "C:/win.js"):
            with self.assertRaises(syv.SecurityError):
                syv.validate_manifest_keys({bad: "x"})


class TestIgnoreInclude(Base):
    def test_backcompat_exact_and_glob(self):
        syv.CONFIG["ignore"] = ["node_modules"]
        self.assertTrue(syv.is_ignored(os.path.join("x", "node_modules", "y")))
        syv.CONFIG["ignore"] = ["*.map"]
        self.assertTrue(syv.is_ignored("/dist/app.js.map"))
        self.assertFalse(syv.is_ignored("/dist/app.js"))

    def test_exclude_wins_over_compressible(self):
        syv.CONFIG["exclude"] = ["*.map"]
        syv.CONFIG["include"] = []
        self.assertFalse(syv.should_include("/dist/app.js.map"))
        self.assertTrue(syv.should_include("/dist/app.js"))

    def test_include_filter(self):
        syv.CONFIG["include"] = ["js/*"]
        syv.CONFIG["exclude"] = []
        self.assertTrue(syv.should_include("js/app.js"))
        self.assertFalse(syv.should_include("css/a.css"))


class TestConfig(Base):
    def test_workers_gzip_timeout_validation(self):
        errs = syv.validate_config({"port": 8080, "ttl": 1, "silent_mode": False, "ignore": [],
                                    "workers": 99, "gzip_level": 99, "include": [], "exclude": [],
                                    "timeout": 999, "headers": {}, "allowlist": [], "log_file": None})
        fields = [e.target for e in errs]
        self.assertIn("workers", fields)
        self.assertIn("gzip_level", fields)
        self.assertIn("timeout", fields)

    def test_getters_clamp(self):
        syv.CONFIG["workers"] = 0
        self.assertGreaterEqual(syv.get_workers(), 1)
        syv.CONFIG["workers"] = 99
        self.assertEqual(syv.get_workers(), 32)
        syv.CONFIG["gzip_level"] = 99
        self.assertEqual(syv.get_gzip_level(), 9)
        syv.CONFIG["gzip_level"] = 0
        self.assertEqual(syv.get_gzip_level(), 1)

    def test_headers_merge(self):
        syv.CONFIG["headers"] = {"Authorization": "Bearer x"}
        h = syv.get_request_headers()
        self.assertEqual(h["Authorization"], "Bearer x")
        self.assertIn("User-Agent", h)


class TestURLSafety(Base):
    def test_localhost_ok_external_blocked_allowlist(self):
        syv.validate_url_safe("http://127.0.0.1:8080/")
        with self.assertRaises(syv.SYVSSRFRiskError):
            syv.validate_url_safe("http://example.com/")
        syv.CONFIG["allowlist"] = ["staging.internal"]
        syv.validate_url_safe("http://staging.internal/")
        with self.assertRaises(syv.SYVSSRFRiskError):
            syv.validate_url_safe("http://evil.com/")


class TestBuildCheck(Base):
    def _scaffold(self):
        self._write("js/app.js", "console.log('hi');\n")
        self._write("admin/app.js", "console.log('admin');\n")
        self._write("css/s.css", "body{color:red}\n")
        self._write("index.html", '<script src="js/app.js"></script><script src="admin/app.js"></script>')

    def test_build_manifest_gz_and_idempotent(self):
        self._scaffold()
        syv.compress_payloads(self.tmp)
        with open(os.path.join(self.tmp, "build_manifest.json"), encoding="utf-8") as f:
            m1 = json.load(f)
        self.assertIn("js/app.js", m1)
        self.assertIn("admin/app.js", m1)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "js", "app.js.gz")))
        with open(os.path.join(self.tmp, "index.html"), encoding="utf-8") as f:
            html1 = f.read()
        self.assertIn("?v=", html1)
        # Two script refs -> exactly two version queries, never stacked (?v=...?v=)
        self.assertEqual(html1.count("?v="), 2)
        # Second build: HTML must be byte-identical (idempotent), check must pass
        syv.compress_payloads(self.tmp)
        with open(os.path.join(self.tmp, "index.html"), encoding="utf-8") as f:
            html2 = f.read()
        self.assertEqual(html1, html2)
        self.assertTrue(syv.check_directory(self.tmp))

    def test_check_fails_on_missing_gz(self):
        self._scaffold()
        syv.compress_payloads(self.tmp)
        os.remove(os.path.join(self.tmp, "js", "app.js.gz"))
        self.assertFalse(syv.check_directory(self.tmp))

    def test_gz_is_valid(self):
        self._write("a.js", "x" * 2000)
        syv.compress_payloads(self.tmp)
        with gzip.open(os.path.join(self.tmp, "a.js.gz"), "rb") as f:
            self.assertTrue(len(f.read()) > 0)


if __name__ == "__main__":
    unittest.main()
