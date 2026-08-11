"""v8.317:复杂度信号 1 收窄「跨独立部署服务 → 跨独立 git 仓库」· 三载体统一(用户拍板)。

实证(matrixpower · Published-Model-Discovery):前后端联动小改(platform-api 目录规则 +
Console 表单必填)触发复杂度门,推荐先做 Feature Planning —— 用户选 2 纠正。

诊断出**三载体两口径**:判定权威 prepare §2.1 写「跨独立部署服务」(例子含「独立部署单元」),
而 planning-check emit 与 feature-planning §0 写的是「跨仓库联动」—— AI 跟了权威载体,
于是 monorepo 里两个独立部署的服务也命中。**但部署拓扑不影响一个 feature 装不装得下**:
真正的承载边界是 git 仓库(worktree 是仓库级 · MR 是仓库级 · 同 repo 全栈改动一个 MR 原子交付,
正是本 case 实际发生的事)。旧口径下 monorepo 每次前后端联动都要多付一轮 1/2 选择。

收窄后与「业务交付视角 · feature 可跨子项目」直接对齐;真命中的基本是跨仓库大变更,
暂停点模板写死推荐 Planning 反而合理(用户选保留)。
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class TestSignalNarrowedToRepoBoundary(unittest.TestCase):

    def setUp(self):
        self.t = _read("docs/prepare.md")

    def test_signal_is_git_repo_based(self):
        self.assertIn("跨独立 git 仓库", self.t)
        self.assertIn("一个 worktree / 一个 MR 装不下", self.t, "缺承载机制 why → 会被当成任意规定")

    def test_monorepo_multi_deploy_explicitly_exempt(self):
        """🔴 核心豁免:同 repo 多部署单元不计入 —— 不写明,例子列会再次把它拉回门内。"""
        self.assertIn("多独立部署单元(后端 + Console + 管理后台)不计入", self.t)
        self.assertIn("一个 worktree 原子交付", self.t)

    def test_scale_still_guarded_by_bl_signal(self):
        """收窄不是放飞:规模由「影响 ≥2 BL」兜 · 部署协调由 WS 串行约束管 —— 两个接盘都点名。"""
        self.assertIn("规模用「影响 ≥2 BL」判", self.t)
        self.assertIn("跨子项目方向", self.t)


class TestThreeCarriersUnified(unittest.TestCase):
    """三载体两口径是本 case 的根因之一 —— 统一后旧口径清零(测试锁)。"""

    CARRIERS = ("docs/prepare.md", "docs/feature-planning.md", "SKILL.md", "tools/state.py")

    def test_old_wordings_zeroed(self):
        for rel in self.CARRIERS:
            t = _read(rel)
            self.assertNotIn("跨独立部署服务", t, f"{rel} 旧口径残留")
            self.assertNotIn("跨仓库联动", t, f"{rel} 第二旧口径残留")

    def test_all_carriers_use_new_wording(self):
        for rel in self.CARRIERS:
            self.assertIn("跨独立 git 仓库", _read(rel), f"{rel} 未统一新口径")

    def test_planning_check_emit_carries_exemption(self):
        """动作点 emit 也要带豁免 —— 只写信号名,monorepo 场景 AI 还是会拿不准。"""
        self.assertIn("同 repo 多部署单元不计入", _read("tools/state.py"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
