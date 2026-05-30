#!/usr/bin/env python3
"""v8.57:tools/preview.py 测试(单 hub UI 预览静态服务 · 治本端口冲突)。

设计:
- preview.py 是独立元工具(parallel update.py / bootstrap.py)
- 用隔离 TEAMWORK_PREVIEW_ROOT(tempdir)+ 临时空闲端口 · 不污染 ~/.teamwork
- 单元测试直接 import 函数 · e2e 走 subprocess(hub 是 detached 子进程)
- tearDown 必停 hub · 防泄漏进程
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
PREVIEW_PY = TOOLS / "preview.py"
PY = "/opt/homebrew/opt/python@3.14/bin/python3.14"
if not Path(PY).exists():
    PY = sys.executable
sys.path.insert(0, str(TOOLS))


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _run(args, env, timeout=15):
    return subprocess.run([PY, str(PREVIEW_PY), *args],
                          capture_output=True, text=True, timeout=timeout, env=env)


class TestPreviewUnit(unittest.TestCase):
    """纯函数单元测试(不起 server)。"""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="tw-preview-unit-")
        os.environ["TEAMWORK_PREVIEW_ROOT"] = self.root
        # 强制 reimport 让模块用新 env(各测试独立)
        for m in list(sys.modules):
            if m == "preview":
                del sys.modules[m]
        import preview  # noqa
        self.preview = preview

    def tearDown(self):
        os.environ.pop("TEAMWORK_PREVIEW_ROOT", None)
        shutil.rmtree(self.root, ignore_errors=True)

    def test_slugify(self):
        f = self.preview._slugify
        self.assertEqual(f("F002-antd Migration"), "f002-antd-migration")
        self.assertEqual(f("docs/design"), "docs-design")
        self.assertEqual(f("  --weird!!--  "), "weird")
        self.assertEqual(f(""), "preview")

    def test_register_load_unregister(self):
        p = self.preview
        d = Path(self.root) / "somedir"
        d.mkdir()
        p._register("slugA", d, "FeatA", "projX")
        reg = p._load_registry()
        self.assertIn("slugA", reg)
        self.assertEqual(reg["slugA"]["feature"], "FeatA")
        self.assertEqual(reg["slugA"]["project"], "projX")
        self.assertTrue(p._unregister("slugA"))
        self.assertNotIn("slugA", p._load_registry())
        self.assertFalse(p._unregister("nope"))

    def test_prune_removes_stale(self):
        p = self.preview
        live = Path(self.root) / "live"
        live.mkdir()
        gone = Path(self.root) / "gone"
        gone.mkdir()
        p._register("live", live, None, None)
        p._register("gone", gone, None, None)
        shutil.rmtree(gone)  # 变 stale
        removed = p._prune_registry()
        self.assertEqual(removed, ["gone"])
        self.assertIn("live", p._load_registry())
        self.assertNotIn("gone", p._load_registry())

    def test_resolve_serve_dir_from_feature_ui_md(self):
        """--feature 读 UI.md pages_changed[].panorama_file 父目录。"""
        p = self.preview
        feat = Path(self.root) / "F001-demo"
        feat.mkdir()
        panorama = Path(self.root) / "subproj" / "docs" / "design" / "preview"
        panorama.mkdir(parents=True)
        (panorama / "page1.html").write_text("<h1>x</h1>")
        ui_md = feat / "UI.md"
        ui_md.write_text(
            "---\npages_changed:\n  - page_id: page1\n"
            f"    panorama_file: {panorama / 'page1.html'}\n---\n# UI\n")
        args = type("A", (), {"dir": None, "feature": str(feat), "slug": None})()
        serve_dir, label, source = p._resolve_serve_dir(args)
        self.assertEqual(serve_dir, panorama.resolve())
        self.assertEqual(label, "F001-demo")
        self.assertIn("panorama_file", source)

    def test_resolve_serve_dir_legacy_preview(self):
        """无 pages_changed → fallback feature/preview。"""
        p = self.preview
        feat = Path(self.root) / "F002-legacy"
        prev = feat / "preview"
        prev.mkdir(parents=True)
        (prev / "a.html").write_text("x")
        args = type("A", (), {"dir": None, "feature": str(feat), "slug": None})()
        serve_dir, label, source = p._resolve_serve_dir(args)
        self.assertEqual(serve_dir, prev.resolve())
        self.assertEqual(source, "feature/preview")


class TestPreviewE2E(unittest.TestCase):
    """e2e:起 detached hub · serve / fetch / reuse / list / stop。"""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="tw-preview-e2e-")
        self.port = _free_port()
        self.env = dict(os.environ)
        self.env["TEAMWORK_PREVIEW_ROOT"] = self.root
        self.env["TEAMWORK_PREVIEW_PORT"] = str(self.port)
        # 两个 fake 预览目录
        self.d1 = Path(self.root) / "feat1_preview"
        self.d1.mkdir()
        (self.d1 / "page1.html").write_text("<!doctype html><h1>PAGE-ONE</h1>")
        (self.d1 / "page2.html").write_text("<!doctype html><h1>PAGE-TWO</h1>")
        self.d2 = Path(self.root) / "feat2_preview"
        self.d2.mkdir()
        (self.d2 / "main.html").write_text("<h1>FEAT-TWO</h1>")

    def tearDown(self):
        _run(["stop", "--all"], self.env)
        time.sleep(0.2)
        shutil.rmtree(self.root, ignore_errors=True)

    def _fetch(self, path: str, timeout=3) -> tuple[int, str]:
        url = f"http://127.0.0.1:{self.port}{path}"
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
            return e.code, ""

    def test_serve_registers_and_serves(self):
        r = _run(["serve", "--dir", str(self.d1), "--slug", "feat-one"], self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["verdict"], "OK")
        self.assertEqual(out["slug"], "feat-one")
        self.assertEqual(out["hub_port"], self.port)
        self.assertIn("page1.html", out["page_urls"])
        # fetch the real page through hub
        code, body = self._fetch("/feat-one/page1.html")
        self.assertEqual(code, 200)
        self.assertIn("PAGE-ONE", body)
        # health marker
        code, body = self._fetch("/__teamwork_hub__")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["magic"], "teamwork-preview-hub")

    def test_second_serve_reuses_hub_no_new_port(self):
        """核心:并行 session 第二次 serve 复用同一 hub · 不抢新端口。"""
        r1 = _run(["serve", "--dir", str(self.d1), "--slug", "f1"], self.env)
        out1 = json.loads(r1.stdout)
        self.assertFalse(out1["hub_reused"])  # 第一次启动
        r2 = _run(["serve", "--dir", str(self.d2), "--slug", "f2"], self.env)
        out2 = json.loads(r2.stdout)
        self.assertTrue(out2["hub_reused"])           # 复用!
        self.assertEqual(out2["hub_port"], self.port)  # 同端口
        self.assertEqual(out1["hub_pid"], out2["hub_pid"])  # 同进程
        # 两个 slug 都可访问
        self.assertEqual(self._fetch("/f1/page1.html")[0], 200)
        self.assertEqual(self._fetch("/f2/main.html")[0], 200)

    def test_path_traversal_blocked(self):
        _run(["serve", "--dir", str(self.d1), "--slug", "ff"], self.env)
        # urllib 不会规范化 → 直送 raw '..'(curl 会 · urllib 不会)
        code, _ = self._fetch("/ff/../../../../etc/passwd")
        self.assertIn(code, (403, 404))  # 绝不 200

    def test_list_shows_entries(self):
        _run(["serve", "--dir", str(self.d1), "--slug", "la"], self.env)
        _run(["serve", "--dir", str(self.d2), "--slug", "lb"], self.env)
        r = _run(["list"], self.env)
        out = json.loads(r.stdout)
        self.assertTrue(out["hub_running"])
        self.assertEqual(out["registry_count"], 2)
        slugs = {e["slug"] for e in out["entries"]}
        self.assertEqual(slugs, {"la", "lb"})

    def test_stop_all_kills_hub(self):
        _run(["serve", "--dir", str(self.d1), "--slug", "sa"], self.env)
        self.assertEqual(self._fetch("/__teamwork_hub__")[0], 200)
        r = _run(["stop", "--all"], self.env)
        out = json.loads(r.stdout)
        self.assertIsNotNone(out["hub_killed_pid"])
        time.sleep(0.4)
        # hub 已停 → 连不上
        with self.assertRaises(Exception):
            urllib.request.urlopen(
                f"http://127.0.0.1:{self.port}/__teamwork_hub__", timeout=1)

    def test_stop_slug_unregisters(self):
        _run(["serve", "--dir", str(self.d1), "--slug", "keep"], self.env)
        _run(["serve", "--dir", str(self.d2), "--slug", "drop"], self.env)
        r = _run(["stop", "--slug", "drop"], self.env)
        out = json.loads(r.stdout)
        self.assertEqual(out["unregistered"], "drop")
        # keep 仍在 · hub 仍服务
        lst = json.loads(_run(["list"], self.env).stdout)
        slugs = {e["slug"] for e in lst["entries"]}
        self.assertEqual(slugs, {"keep"})

    def test_serve_missing_dir_fails(self):
        r = _run(["serve", "--dir", str(Path(self.root) / "nope")], self.env)
        self.assertEqual(r.returncode, 1)
        out = json.loads(r.stdout)
        self.assertEqual(out["verdict"], "FAIL")


class TestPreviewHelp(unittest.TestCase):
    def test_help_runs_independently(self):
        r = subprocess.run([PY, str(PREVIEW_PY), "--help"],
                           capture_output=True, text=True, timeout=10)
        self.assertEqual(r.returncode, 0)
        self.assertIn("serve", r.stdout)
        self.assertIn("preview.py", r.stdout)

    def test_serve_help_has_flags(self):
        r = subprocess.run([PY, str(PREVIEW_PY), "serve", "--help"],
                           capture_output=True, text=True, timeout=10)
        self.assertEqual(r.returncode, 0)
        self.assertIn("--dir", r.stdout)
        self.assertIn("--feature", r.stdout)
        self.assertIn("--slug", r.stdout)


if __name__ == "__main__":
    unittest.main()
