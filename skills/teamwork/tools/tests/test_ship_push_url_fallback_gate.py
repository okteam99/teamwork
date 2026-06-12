#!/usr/bin/env python3
"""v8.37 治本 SVC-CORE-B007 case:url-fallback 退化拦截测试。

case:AI 在 glab 1.92.1 已装 + 已认证条件下 · 仍传 --mr-creation-method url-fallback
+ --mr-create-url <git push hint URL>(MR 创建表单 URL)· 规范 P0-113 明文禁止 · state.py
未拦截 · 用户察觉后手动跑 glab mr create + raw-write 才补救。

v8.37 治本:_handle_ship_push 在 url-fallback 时检测 git_host → CLI 可用性 ·
CLI 装+认证 → BLOCK · 除非显式 --accept-cli-unavailable --reason --user-confirmed。

测试矩阵:
1. CLI 可用(mock) + url-fallback + 不带 bypass → BLOCK
2. CLI 可用 + 带完整 bypass → PASS + WARN + concerns + bypass_log
3. CLI 可用 + bypass 缺 --reason → BLOCK
4. CLI 可用 + bypass 缺 --user-confirmed → BLOCK(require_user_confirmed)
5. CLI 未装(which 失败) + url-fallback → PASS(退化合理)
6. CLI 装但未认证(auth status 失败) + url-fallback → PASS(退化合理)
7. git_host=gitee(无 CLI 映射) + url-fallback → PASS
8. cli-glab method → 跳过校验

运行:
    python3 -m pytest skills/teamwork/tools/tests/test_ship_push_url_fallback_gate.py -v
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
sys.path.insert(0, str(TOOLS))


class TestCheckCliAvailableForHost(unittest.TestCase):
    """_check_cli_available_for_host helper 单测。"""

    def test_v837_unknown_host_returns_no_cli_mapping(self):
        from _v8_ship import _check_cli_available_for_host  # type: ignore
        r = _check_cli_available_for_host("gitee")
        self.assertFalse(r["available"])
        self.assertIn("no_cli_mapping_for_host", r["reason"])

    def test_v837_github_maps_to_gh(self):
        from _v8_ship import _check_cli_available_for_host, SHIP_GIT_HOST_TO_CLI
        self.assertEqual(SHIP_GIT_HOST_TO_CLI["github"], "gh")
        self.assertEqual(SHIP_GIT_HOST_TO_CLI["gitlab"], "glab")
        self.assertEqual(SHIP_GIT_HOST_TO_CLI["gitlab-self-hosted"], "glab")

    def test_v837_cli_not_installed_when_which_fails(self):
        """mock which 失败 → not_installed reason。"""
        from _v8_ship import _check_cli_available_for_host  # type: ignore

        def fake_run(cmd, **kwargs):
            class R:
                returncode = 1
                stdout = ""
                stderr = "not found"
            return R()

        with mock.patch("_v8_ship.subprocess.run", side_effect=fake_run):
            r = _check_cli_available_for_host("github")
        self.assertFalse(r["available"])
        self.assertEqual(r["reason"], "gh_not_installed")
        self.assertIn("brew install gh", r["hint_install"])

    def test_v837_cli_not_authenticated_when_auth_status_fails(self):
        """mock which OK 但 auth status 失败 → not_authenticated reason。"""
        from _v8_ship import _check_cli_available_for_host  # type: ignore

        def fake_run(cmd, **kwargs):
            class R:
                returncode = 0 if cmd[0] == "which" else 1
                stdout = "/usr/bin/glab" if cmd[0] == "which" else ""
                stderr = "" if cmd[0] == "which" else "not logged in"
            return R()

        with mock.patch("_v8_ship.subprocess.run", side_effect=fake_run):
            r = _check_cli_available_for_host("gitlab")
        self.assertFalse(r["available"])
        self.assertEqual(r["reason"], "glab_not_authenticated")

    def test_v837_cli_available_when_both_ok(self):
        """mock which + auth status 都 OK → available。"""
        from _v8_ship import _check_cli_available_for_host  # type: ignore

        def fake_run(cmd, **kwargs):
            class R:
                returncode = 0
                stdout = "/usr/bin/" + cmd[0]
                stderr = ""
            return R()

        with mock.patch("_v8_ship.subprocess.run", side_effect=fake_run):
            r = _check_cli_available_for_host("gitlab-self-hosted")
        self.assertTrue(r["available"])
        self.assertEqual(r["cli_name"], "glab")
        self.assertEqual(r["reason"], "installed_and_authenticated")


class TestHandleShipPushUrlFallbackGate(unittest.TestCase):
    """_handle_ship_push url-fallback BLOCK / bypass 集成测试。

    用 fake state + Namespace + mock subprocess 模拟 CLI 状态。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-v837-"))
        # 准备 fake state(current_stage=ship · phase=archived —— v8.145 push 前必先 archive)
        self.state = {
            "current_stage": "ship",
            "feature_id": "TEST-B007",
            "ship": {"phase": "archived"},
            "concerns": [],
        }

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _mock_cli_available(self):
        """返回 patch context · 让 _check_cli_available_for_host 报"可用"。"""
        return mock.patch(
            "_v8_ship._check_cli_available_for_host",
            return_value={"available": True, "cli_name": "glab",
                          "reason": "installed_and_authenticated"},
        )

    def _mock_cli_unavailable(self, reason="glab_not_installed"):
        return mock.patch(
            "_v8_ship._check_cli_available_for_host",
            return_value={"available": False, "cli_name": "glab",
                          "reason": reason},
        )

    def _args(self, **overrides):
        import argparse
        base = {
            "git_host": "gitlab-self-hosted",
            "mr_creation_method": "url-fallback",
            "mr_url": None,
            "mr_create_url": "http://gitlab.example.com/repo/-/merge_requests/new?source=x",
            "feature_head_commit": "abc123",
            "feature_pushed_at": None,
            "accept_cli_unavailable": False,
            "user_confirmed": False,
            "reason": None,
        }
        base.update(overrides)
        ns = argparse.Namespace(**base)
        return ns

    def _run_push(self, args) -> tuple[int, dict]:
        """跑 _handle_ship_push · 捕 emit_json sys.exit 与返回 dict。"""
        from _v8_ship import _handle_ship_push  # type: ignore
        # _handle_ship_push 在 FAIL 时 emit_json + sys.exit · OK 时 return dict
        try:
            r = _handle_ship_push(self.state, args)
            return 0, r
        except SystemExit as e:
            # emit_json 走 sys.exit · 捕获 exit_code(stdout 已 emit JSON)
            return int(e.code or 0), {}

    def test_v837_block_when_cli_available_no_bypass(self):
        """CLI 装好+认证 + url-fallback + 无 bypass → BLOCK。"""
        import io
        args = self._args()
        with self._mock_cli_available(), \
             mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
            code, _ = self._run_push(args)
            out = stdout.getvalue()
        self.assertEqual(code, 1)
        d = json.loads(out)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("url-fallback", d["error"])
        self.assertIn("glab", d["error"])
        self.assertIn("P0-113", d["error"])
        self.assertIn("--accept-cli-unavailable", d["hint"])
        self.assertEqual(d["cli_check"]["available"], True)

    def test_v837_pass_when_cli_available_with_full_bypass(self):
        """CLI 装好+认证 + url-fallback + 完整 bypass → PASS + WARN + concerns + bypass_log。"""
        args = self._args(
            accept_cli_unavailable=True,
            user_confirmed=True,
            reason="网络隔离不能访问 GitLab API",
        )
        with self._mock_cli_available():
            code, r = self._run_push(args)
        self.assertEqual(code, 0)
        self.assertEqual(r["verdict"], "PASS")
        self.assertEqual(r["phase"], "pushed")
        # WARN 字段
        self.assertIn("fallback_bypass_warning", r)
        self.assertIn("glab 已装+已认证", r["fallback_bypass_warning"])
        self.assertIn("网络隔离不能访问 GitLab API", r["fallback_bypass_warning"])
        # concerns 留痕
        self.assertEqual(len(self.state["concerns"]), 1)
        self.assertIn("v8.37", self.state["concerns"][0])
        # bypass_log 写入
        ship = self.state["ship"]
        self.assertEqual(len(ship["bypass_log"]), 1)
        bl = ship["bypass_log"][0]
        self.assertEqual(bl["type"], "url_fallback_when_cli_available")
        self.assertEqual(bl["cli_name"], "glab")
        self.assertEqual(bl["reason"], "网络隔离不能访问 GitLab API")

    def test_v837_block_when_bypass_missing_reason(self):
        """CLI 装好 + accept_cli_unavailable + user_confirmed 但缺 reason → BLOCK。"""
        import io
        args = self._args(
            accept_cli_unavailable=True,
            user_confirmed=True,
            reason="",  # 空
        )
        with self._mock_cli_available(), \
             mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
            code, _ = self._run_push(args)
            out = stdout.getvalue()
        self.assertEqual(code, 1)
        d = json.loads(out)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("--reason", d["error"])

    def test_v837_block_when_bypass_missing_user_confirmed(self):
        """CLI 装好 + accept_cli_unavailable + reason 但缺 user_confirmed → BLOCK。"""
        import io
        args = self._args(
            accept_cli_unavailable=True,
            user_confirmed=False,  # 缺
            reason="网络隔离",
        )
        with self._mock_cli_available(), \
             mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
            code, _ = self._run_push(args)
            out = stdout.getvalue()
        self.assertEqual(code, 1)
        # require_user_confirmed 走 emit FAIL · 不强校 error 内容(由共用 helper 决定)
        d = json.loads(out)
        self.assertEqual(d["verdict"], "FAIL")

    def test_v837_pass_when_cli_not_installed(self):
        """CLI 未装 + url-fallback → PASS(退化合理 · 不拦)。"""
        args = self._args()
        with self._mock_cli_unavailable("glab_not_installed"):
            code, r = self._run_push(args)
        self.assertEqual(code, 0)
        self.assertEqual(r["verdict"], "PASS")
        # 不应有 WARN
        self.assertNotIn("fallback_bypass_warning", r)
        self.assertEqual(self.state.get("concerns", []), [])

    def test_v837_pass_when_cli_not_authenticated(self):
        """CLI 装了但未认证 + url-fallback → PASS(退化合理)。"""
        args = self._args()
        with self._mock_cli_unavailable("glab_not_authenticated"):
            code, r = self._run_push(args)
        self.assertEqual(code, 0)
        self.assertEqual(r["verdict"], "PASS")

    def test_v837_pass_when_no_cli_mapping(self):
        """git_host=gitee(无 CLI 映射) + url-fallback → PASS。"""
        args = self._args(git_host="gitee")
        with self._mock_cli_unavailable("no_cli_mapping_for_host(gitee)"):
            code, r = self._run_push(args)
        self.assertEqual(code, 0)
        self.assertEqual(r["verdict"], "PASS")

    def test_v837_skip_check_for_cli_method(self):
        """cli-glab method → 跳过 v8.37 校验(本来就是 CLI-first)。"""
        args = self._args(
            mr_creation_method="cli-glab",
            mr_url="http://gitlab.example.com/repo/-/merge_requests/299",
            mr_create_url=None,
        )
        # 即使 mock CLI 可用 · 走 cli-glab 路径不触发 v8.37 校验
        with self._mock_cli_available():
            code, r = self._run_push(args)
        self.assertEqual(code, 0)
        self.assertEqual(r["verdict"], "PASS")
        self.assertNotIn("fallback_bypass_warning", r)


if __name__ == "__main__":
    unittest.main(verbosity=2)
