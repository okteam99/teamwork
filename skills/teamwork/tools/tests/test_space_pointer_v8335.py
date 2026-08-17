"""teamwork-space 入口注入 CLAUDE.md / AGENTS.md(用户拍板)。

目标:不用 teamwork 的 agent 也能充分了解项目 —— 宿主标准指令文件即知识地图入口。
与 v8.211 注入退役的边界:当年退的是**流程指令**(非 teamwork 用户被迫吃);
本块受众相反(正是为他们服务)· 内容零流程指令 · marker 不同族不被 legacy 清理误删。
"""
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

from bootstrap import (  # noqa: E402
    SPACE_POINTER_BLOCK,
    maintain_host_injection,
    maintain_space_pointer,
)


def _proj(space=True):
    d = Path(tempfile.mkdtemp(prefix="sp-"))
    if space:
        (d / "teamwork-space.md").write_text("# Teamwork Space\n", encoding="utf-8")
    return d


class TestInjection(unittest.TestCase):

    def test_creates_both_files_when_missing(self):
        d = _proj()
        res = maintain_space_pointer(d)
        self.assertEqual(res["status"], "ok")
        for f in ("CLAUDE.md", "AGENTS.md"):
            self.assertEqual(res["results"][f], "created")
            body = (d / f).read_text(encoding="utf-8")
            self.assertIn("teamwork-space.md", body)
            self.assertIn("无论是否使用 teamwork 流程", body)

    def test_prepends_preserving_user_content(self):
        d = _proj()
        (d / "CLAUDE.md").write_text("# 我的项目规则\n用户内容勿动\n", encoding="utf-8")
        maintain_space_pointer(d)
        body = (d / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertTrue(body.startswith("<!-- TEAMWORK-SPACE-POINTER"))  # 顶部 · 发现性
        self.assertIn("用户内容勿动", body)

    def test_idempotent_and_in_place_update(self):
        d = _proj()
        maintain_space_pointer(d)
        res2 = maintain_space_pointer(d)
        self.assertEqual(res2["results"]["CLAUDE.md"], "up_to_date")
        # 旧版块 → 原位重写不重复
        stale = SPACE_POINTER_BLOCK.replace("v1", "v0").replace("知识入口单源", "旧文案")
        (d / "AGENTS.md").write_text(stale + "\n尾部用户内容\n", encoding="utf-8")
        res3 = maintain_space_pointer(d)
        self.assertEqual(res3["results"]["AGENTS.md"], "block_updated")
        body = (d / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(body.count("TEAMWORK-SPACE-POINTER v1"), 1)
        self.assertNotIn("旧文案", body)
        self.assertIn("尾部用户内容", body)

    def test_skip_without_space_file(self):
        d = _proj(space=False)
        res = maintain_space_pointer(d)
        self.assertEqual(res["status"], "skipped_no_space_file")
        self.assertFalse((d / "CLAUDE.md").exists())


class TestBoundaryWithV8211(unittest.TestCase):
    """注入退役的边界:零流程指令 · legacy 清理不误删新块。"""

    def test_block_has_no_process_directives(self):
        for banned in ("PMO", "worktree", "Subagent", "state.py", "R5"):
            self.assertNotIn(banned, SPACE_POINTER_BLOCK, banned)

    def test_legacy_cleaner_leaves_new_block(self):
        d = _proj()
        maintain_space_pointer(d)
        res = maintain_host_injection(SKILL_ROOT, d, "claude-code", "vX")
        self.assertEqual(res["status"], "clean")
        self.assertIn("TEAMWORK-SPACE-POINTER",
                      (d / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_wired_into_session_bootstrap(self):
        src = (SKILL_ROOT / "tools" / "bootstrap.py").read_text(encoding="utf-8")
        self.assertIn('"space_pointer": space_pointer', src)


if __name__ == "__main__":
    unittest.main()
