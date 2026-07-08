#!/usr/bin/env python3
"""v8.178 · 测试基线失败集差分 gate 回归套件。

治本(实证 audit ×8 · 跨 3 次 harvest 欠最久):brownfield 共享套件预存在失败(base 即红)·
每个 feature 重复人肉 stash-baseline 甄别「正交 vs 回归」。project-specs/test-baseline.md 登记成
项目级单源 → test/dev gate 改差分:当前失败 ⊆ 基线(0 新增)→ 红 base 也放行;有新增 = 回归/新预存在。

运行:python3 -m pytest skills/teamwork/tools/tests/test_test_baseline_v8178.py -q
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

HERE = Path(__file__).resolve().parent
STATE_PY = HERE.parent / "state.py"
sys.path.insert(0, str(HERE.parent))

import _v8_stage_specs as S  # noqa: E402


def _proj(*registered):
    """临时项目 · project-specs/test-baseline.md 含给定登记项 · 返回 feature 路径。"""
    root = Path(tempfile.mkdtemp(prefix="tb-"))
    (root / "project-specs").mkdir()
    feat = root / "apps" / "x" / "docs" / "features" / "F1"
    feat.mkdir(parents=True)
    rows = "".join(f"| {r} | cargo | abc | 历史债 | 2026-06-19 |\n" for r in registered)
    (root / "project-specs" / "test-baseline.md").write_text(
        "# 测试基线失败集\n\n| 失败用例 (id) | 套件/命令 | 基线 commit | 原因（谁的债 · 何时清） | 登记于 |\n"
        "|---|---|---|---|---|\n" + rows, encoding="utf-8")
    return feat


class TestRegistryRead(unittest.TestCase):
    def test_reads_registered_ids_skips_header(self):
        feat = _proj("suite::a", "suite::b")
        ids = S._read_test_baseline(feat)
        self.assertEqual(ids, {"suite::a", "suite::b"})

    def test_absent_registry_empty(self):
        root = Path(tempfile.mkdtemp(prefix="tb0-"))
        (root / "project-specs").mkdir()
        feat = root / "f"; feat.mkdir()
        self.assertEqual(S._read_test_baseline(feat), set())

    def test_find_specs_root_walks_up(self):
        feat = _proj("x::y")
        root = S._find_specs_root(feat)
        self.assertTrue((root / "project-specs").is_dir())


class TestDiff(unittest.TestCase):
    def test_new_vs_excluded(self):
        feat = _proj("suite::a")
        new, excl = S._test_new_failures(NS(current_failures="suite::a, suite::NEW", feature=feat))
        self.assertEqual(new, ["suite::NEW"])
        self.assertEqual(excl, ["suite::a"])


class TestDevGate(unittest.TestCase):
    def test_green_passes(self):
        ok, _ = S._evidence_test_exit_code_zero({}, NS(test_exit_code=0))
        self.assertTrue(ok)

    def test_red_diff_clean_passes(self):
        feat = _proj("suite::a", "suite::b")
        ok, _ = S._evidence_test_exit_code_zero(
            {}, NS(test_exit_code=1, current_failures="suite::a,suite::b", feature=feat))
        self.assertTrue(ok)

    def test_red_with_new_blocks(self):
        feat = _proj("suite::a")
        ok, msg = S._evidence_test_exit_code_zero(
            {}, NS(test_exit_code=1, current_failures="suite::a,suite::NEW", feature=feat))
        self.assertFalse(ok)
        self.assertIn("新增", msg)
        self.assertIn("suite::NEW", msg)

    def test_red_without_current_failures_blocks_with_hint(self):
        # 红 + 没传 --current-failures → block(向后兼容 · 提示走差分)
        ok, msg = S._evidence_test_exit_code_zero({}, NS(test_exit_code=1))
        self.assertFalse(ok)
        self.assertIn("test-baseline", msg)

    def test_red_no_registry_all_new_blocks(self):
        # 干净项目(无注册表)突然红 → 全算新增 → block(= 真回归)
        root = Path(tempfile.mkdtemp(prefix="tbn-")); (root / "project-specs").mkdir()
        feat = root / "f"; feat.mkdir()
        ok, _ = S._evidence_test_exit_code_zero(
            {}, NS(test_exit_code=1, current_failures="suite::x", feature=feat))
        self.assertFalse(ok)


class TestTestGateTransition(unittest.TestCase):
    def test_integration_diff_clean_persisted(self):
        """差分结果由 persist_args_to_evidence 落 evidence(校验函数是纯谓词 · 不写 args)。"""
        feat = _proj("suite::a")
        args = NS(integration_test_exit_code=1, current_failures="suite::a", feature=feat)
        ok, _ = S._evidence_integration_test_present({}, args)
        self.assertTrue(ok)
        self.assertFalse(hasattr(args, "integration_diff_clean"))  # 纯谓词:不写 args
        st = {}
        S.persist_args_to_evidence("test", st, args)
        self.assertIs(
            st["stage_contracts"]["test"]["evidence"]["integration_diff_clean"], True)
        self.assertEqual(st["execution_hints"]["integration_new_failures"], [])

    def test_transition_diff_clean_advances(self):
        st = {"stage_contracts": {"test": {"evidence": {
            "integration_test_exit_code": 1, "e2e_test_exit_code": 0,
            "integration_diff_clean": True}}}}
        self.assertEqual(S._test_transition(st), "pm_acceptance")

    def test_transition_new_failures_stays(self):
        st = {"stage_contracts": {"test": {"evidence": {
            "integration_test_exit_code": 1, "e2e_test_exit_code": 0,
            "integration_diff_clean": False}}}}
        self.assertIsNone(S._test_transition(st))

    def test_transition_e2e_red_stays_even_if_int_clean(self):
        # e2e 仍严格 0 · 不走差分
        st = {"stage_contracts": {"test": {"evidence": {
            "integration_test_exit_code": 1, "e2e_test_exit_code": 1,
            "integration_diff_clean": True}}}}
        self.assertIsNone(S._test_transition(st))


class TestCli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="tbc-"))
        (self.root / "project-specs").mkdir()
        self.feat = self.root / "apps" / "x" / "docs" / "features" / "F1"
        self.feat.mkdir(parents=True)

    def _run(self, *a):
        r = subprocess.run([sys.executable, str(STATE_PY), "test-baseline",
                            "--feature", str(self.feat), *a],
                           capture_output=True, text=True, timeout=30)
        return r, (json.loads(r.stdout) if r.stdout.strip().startswith("{") else None)

    def test_add_creates_and_lists(self):
        _, out = self._run("--add", "--test-id", "suite::a", "--suite", "cargo", "--reason", "历史债")
        self.assertEqual(out["verdict"], "OK")
        self.assertTrue((self.root / "project-specs" / "test-baseline.md").is_file())
        _, lst = self._run("--list")
        self.assertIn("suite::a", lst["baseline"])

    def test_add_requires_reason(self):
        _, out = self._run("--add", "--test-id", "suite::a")
        self.assertEqual(out["verdict"], "FAIL")

    def test_diff_reports_new(self):
        self._run("--add", "--test-id", "suite::a", "--reason", "债")
        _, out = self._run("--diff", "--current", "suite::a, suite::NEW")
        self.assertEqual(out["verdict"], "NEW_FAILURES")
        self.assertEqual(out["new"], ["suite::NEW"])
        self.assertEqual(out["excluded"], ["suite::a"])

    def test_diff_clean_ok(self):
        self._run("--add", "--test-id", "suite::a", "--reason", "债")
        _, out = self._run("--diff", "--current", "suite::a")
        self.assertEqual(out["verdict"], "OK")
        self.assertEqual(out["new"], [])


if __name__ == "__main__":
    unittest.main()
