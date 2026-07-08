#!/usr/bin/env python3
"""邻域 bug 修复回归套件:verify-ac.py CLI 咬合 + test-complete --run-tests 顺序。

E12 · verify-ac.py CLI 失配(休眠门禁唤醒):
    specs `_evidence_ac_test_binding` 用 `--prd/--tc` 调 templates/verify-ac.py · 旧脚本
    只收位置参数 → `--prd` 被当目录 → 恒「PRD.md 不存在」→ 兼容分支 silent skip ·
    AC↔TC 绑定校验从未真正工作。脚本加 argparse 后 gate 真咬合(绑定齐全 PASS /
    缺绑定 FAIL / Bug·Micro 流程 skip 语义保留)。

E13 · test-complete --run-tests 顺序:
    exit code 注入原发生在 evidence 校验之后 · 单独 --run-tests 先撞
    「缺 --integration-test-exit-code」FAIL。已前移到 persist/evidence 校验之前。

运行:python3 -m pytest skills/teamwork/tools/tests/test_verify_ac_gate.py -q
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
STATE_PY = TOOLS / "state.py"
VERIFY_AC = TOOLS.parent / "templates" / "verify-ac.py"
sys.path.insert(0, str(TOOLS))

import _v8_stage_specs as S  # noqa: E402


PRD_BOUND = """---
acceptance_criteria:
  - id: AC-1
    desc: 用户可登录
  - id: AC-2
    desc: 错误密码被拒
---
# PRD
"""

TC_FULL = """---
tests:
  - id: T-1
    covers_ac: [AC-1]
  - id: T-2
    covers_ac: [AC-2]
---
# TC
"""

TC_PARTIAL = """---
tests:
  - id: T-1
    covers_ac: [AC-1]
---
# TC(AC-2 无覆盖)
"""


def _run_verify_ac(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(VERIFY_AC), *args],
                          capture_output=True, text=True, timeout=30)


class _FeatureDirCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-vac-"))
        self.feat = self.tmp / "F001"
        self.feat.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, prd: str = PRD_BOUND, tc: str = TC_FULL):
        (self.feat / "PRD.md").write_text(prd, encoding="utf-8")
        (self.feat / "TC.md").write_text(tc, encoding="utf-8")


# ─── 1 · verify-ac.py CLI:--prd/--tc + 位置参数兼容 ────────────────────


class TestVerifyAcCli(_FeatureDirCase):
    def test_prd_tc_flags_full_coverage_rc0(self):
        self._write()
        r = _run_verify_ac("--prd", str(self.feat / "PRD.md"), "--tc", str(self.feat / "TC.md"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("覆盖校验通过", r.stdout)

    def test_prd_tc_flags_missing_coverage_rc3(self):
        self._write(tc=TC_PARTIAL)
        r = _run_verify_ac("--prd", str(self.feat / "PRD.md"), "--tc", str(self.feat / "TC.md"))
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("AC-2", r.stdout)
        self.assertIn("缺测试覆盖", r.stdout)

    def test_positional_form_still_works(self):
        self._write()
        r = _run_verify_ac(str(self.feat))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_prd_without_tc_usage_error_rc1(self):
        self._write()
        r = _run_verify_ac("--prd", str(self.feat / "PRD.md"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("成对", r.stderr)

    def test_no_args_usage_rc1(self):
        r = _run_verify_ac()
        self.assertEqual(r.returncode, 1)
        self.assertIn("usage", r.stderr)

    def test_prd_flag_missing_file_rc1_with_message(self):
        """--prd 指向不存在文件 → 明确报 PRD.md 不存在(specs 兼容分支消费的字面)。"""
        r = _run_verify_ac("--prd", str(self.feat / "PRD.md"), "--tc", str(self.feat / "TC.md"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("PRD.md 不存在", r.stderr)


# ─── 2 · _evidence_ac_test_binding 真咬合 ──────────────────────────────


class TestAcTestBindingGateBites(_FeatureDirCase):
    def _gate(self, flow_type: str = "Feature"):
        return S._evidence_ac_test_binding(
            {"flow_type": flow_type}, NS(feature=str(self.feat)))

    def test_full_binding_passes(self):
        self._write()
        ok, err = self._gate()
        self.assertTrue(ok, err)

    def test_missing_binding_fails_not_silent_skip(self):
        """缺绑定 → 真 FAIL(修前:--prd 被旧脚本当目录 → silent skip 恒 PASS)。"""
        self._write(tc=TC_PARTIAL)
        ok, err = self._gate()
        self.assertFalse(ok, "休眠门禁应已唤醒:缺 AC 覆盖必须 FAIL")
        self.assertIn("verify-ac.py FAIL", err)

    def test_no_frontmatter_prd_fails(self):
        (self.feat / "PRD.md").write_text("# 裸 PRD 无 frontmatter", encoding="utf-8")
        (self.feat / "TC.md").write_text(TC_FULL, encoding="utf-8")
        ok, err = self._gate()
        self.assertFalse(ok)
        self.assertIn("verify-ac.py FAIL", err)

    def test_bug_flow_skips_without_prd(self):
        """Bug 流程无 PRD/TC(规格 = bugfix/BUG-*.md)→ skip 语义保留。"""
        ok, reason = self._gate(flow_type="Bug")
        self.assertTrue(ok)
        self.assertIn("skipped", reason)

    def test_micro_flow_skips(self):
        ok, reason = self._gate(flow_type="Micro")
        self.assertTrue(ok)
        self.assertIn("skipped", reason)

    def test_feature_flow_missing_prd_fails(self):
        """Feature 流程 PRD 缺失 → FAIL(不 skip · 与 Bug 流程区分)。"""
        (self.feat / "TC.md").write_text(TC_FULL, encoding="utf-8")
        ok, err = self._gate()
        self.assertFalse(ok)
        self.assertIn("PRD.md 或 TC.md 不存在", err)


# ─── 3 · test-complete --run-tests 顺序(E13) ──────────────────────────


def _git(cwd: Path, *args: str) -> tuple[int, str]:
    r = subprocess.run(["git", *args], cwd=str(cwd),
                       capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout.strip()


def _run_state(cwd: Path, *args: str, expect_exit: int = 0) -> dict:
    r = subprocess.run([sys.executable, str(STATE_PY), *args],
                       cwd=str(cwd), capture_output=True, text=True, timeout=120)
    assert r.returncode == expect_exit, (
        f"exit {r.returncode} ≠ {expect_exit}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}")
    out = r.stdout if r.stdout.strip() else r.stderr
    start = out.index("{")
    depth = 0
    for i in range(start, len(out)):
        if out[i] == "{":
            depth += 1
        elif out[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(out[start:i + 1])
    raise AssertionError(f"无法解析 JSON · stdout={r.stdout!r} stderr={r.stderr!r}")


class TestRunTestsOrder(unittest.TestCase):
    """--run-tests 单独使用(不带 --integration-test-exit-code)不再先撞缺参数 FAIL。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-runtests-"))
        _git(self.tmp, "init", "-b", "main")
        _git(self.tmp, "config", "user.email", "t@t.co")
        _git(self.tmp, "config", "user.name", "t")
        self.feat = self.tmp / "docs" / "features" / "B1"
        self.feat.mkdir(parents=True)
        # Bug 流程:无 PRD/TC(ac_test_binding skip)· 聚焦 --run-tests 注入顺序
        (self.feat / "state.json").write_text(json.dumps({
            "feature_id": "B1", "flow_type": "Bug", "current_stage": "test",
            "merge_target": "main", "artifact_root": str(self.feat),
            "stage_contracts": {}, "completed_stages": [], "concerns": [],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        (self.feat / "TEST-REPORT.md").write_text("# report", encoding="utf-8")
        (self.feat / "e2e").mkdir()
        (self.feat / "e2e" / "t.py").write_text("print('ok')", encoding="utf-8")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-m", "test artifacts")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _cmd(self, exit_code: int) -> str:
        return f'"{sys.executable}" -c "import sys; sys.exit({exit_code})"'

    def test_run_tests_alone_green_passes(self):
        """单独 --run-tests(绿)→ 注入 exit_code=0 · 不撞「缺 --integration-test-exit-code」。"""
        d = _run_state(self.tmp, "test-complete", "--feature", "docs/features/B1",
                       "--run-tests", "--test-cmd", self._cmd(0),
                       "--e2e-test-exit-code", "0")
        self.assertEqual(d["verdict"], "PASS")
        self.assertEqual(d["transitioned_to"], "pm_acceptance")
        self.assertEqual(d["test_run_result"]["exit_code"], 0)
        st = json.loads((self.feat / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(
            st["stage_contracts"]["test"]["evidence"]["integration_test_exit_code"], 0)
        self.assertTrue((self.feat / "test-stdout.log").exists())

    def test_run_tests_alone_red_stays_in_stage(self):
        """单独 --run-tests(红)→ 注入非 0 · 留 test stage 走 fix-retry(非缺参数 FAIL)。"""
        d = _run_state(self.tmp, "test-complete", "--feature", "docs/features/B1",
                       "--run-tests", "--test-cmd", self._cmd(1),
                       "--e2e-test-exit-code", "0")
        self.assertEqual(d["verdict"], "PASS")          # complete 记录本轮 · 留 stage
        self.assertIsNone(d["transitioned_to"])
        self.assertIn("fix_retry_hint", d)
        self.assertEqual(d["test_run_result"]["exit_code"], 1)
        self.assertNotIn("缺 --integration-test-exit-code", json.dumps(d, ensure_ascii=False))
        st = json.loads((self.feat / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(
            st["stage_contracts"]["test"]["evidence"]["integration_test_exit_code"], 1)

    def test_run_tests_without_cmd_still_blocks_with_guidance(self):
        """--run-tests 无 cmd 来源 → 明确 FAIL 指路(localconfig / --test-cmd)· 行为保留。"""
        d = _run_state(self.tmp, "test-complete", "--feature", "docs/features/B1",
                       "--run-tests", "--e2e-test-exit-code", "0", expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("--run-tests 但", d["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
