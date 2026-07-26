"""v8.290:流程文档整体精简 —— 保底线 · 不限制模型发挥 · 砍没必要的 HOW。

用户原则:「保住底线规则,其余不限制模型发挥,精简没必要的 HOW」
示例:架构视角只需「架构要合理、防止未来维护成本过高」· 至于怎么设计 AI 自决。
"""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


class TestSkillSlimming(unittest.TestCase):
    def setUp(self):
        self.t = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_no_monster_line(self):
        """行 205 曾单行 3173 字符塞 8+ 条独立规则(everything red = nothing red 的极端)。"""
        longest = max(len(l) for l in self.t.splitlines())
        self.assertLess(longest, 700, f"出现超长行({longest} 字符)· 一行塞多条规则 = 每条都拿不到权重")

    def test_red_density_controlled(self):
        n = self.t.count("🔴")
        self.assertLess(n, 55, f"🔴 {n} 个 —— 只有命中判据①-⑤(证据/独立采样/主权/机械/逆默认)才配标红")

    def test_command_list_is_pointer_not_copy(self):
        """🐛 实测漂移:原清单声称 ≈55 命令,实际 52 个里 11 个从未出现(整个 micro 流程都漏了)。

        指针 + 复制被指向内容 = 副本必漂。改为分类概览 + `--help` 权威。
        """
        self.assertIn("权威 = `state.py --help`", self.t)
        self.assertNotIn("goal-start / goal-complete", self.t)   # 逐条枚举已删

    def test_routing_critical_commands_still_visible(self):
        """但语义特殊(routing 级)的必须留 —— 它们的语义 --help 给不出。"""
        for c in ("init-feature", "ship-phase", "await-merge", "ship-finalize",
                  "main-sync", "recover", "raw-write", "pause-mark"):
            self.assertIn(c, self.t, f"routing 级命令丢失:{c}")

    def test_bottom_lines_retained(self):
        """底线一条不能少(判据①-⑤)。"""
        for k in ("授权暂停点", "worktree", "R5", "bypass", "triage",
                  "错开", "投递位置", "独立采样"):     # 🔴 锁实质不锁措辞(本轮第三次教训)
            self.assertIn(k, self.t, f"底线丢失:{k}")


class TestNoDanglingSectionRefs(unittest.TestCase):
    def test_skill_blueprint_ref_fixed(self):
        """🐛 SKILL 曾指 blueprint § 7.5,该章节已随四段结构重构消失。"""
        self.assertNotIn("blueprint-stage.md § 7.5", (ROOT / "SKILL.md").read_text(encoding="utf-8"))


class TestRoleTelosAutonomy(unittest.TestCase):
    """用户原则的落点:底线说清 · HOW 明确交还模型。"""

    def test_architect_states_bottom_line_not_how(self):
        t = (ROOT / "roles" / "architect.md").read_text(encoding="utf-8")
        self.assertIn("别让未来的维护成本过高", t)      # 底线
        self.assertIn("架构怎么设计 —— AI 自决", t)      # HOW 交还

    def test_rd_states_autonomy(self):
        t = (ROOT / "roles" / "rd.md").read_text(encoding="utf-8")
        self.assertIn("怎么实现 AI 自决", t)


class TestProjectSpecsListsInSync(unittest.TestCase):
    """v8.290:SKILL 路由表与 conventions §13 目录表列的 project-specs 文件必须一致。

    两者不是重复(一个给「何时读」路由 · 一个给「目录结构 + 维护方」)· 不该合并;
    但**文件清单会一起漂** —— v8.258/259 加 RELEASE-GUIDE 时就要同时改两处(靠人工七点清单)。
    把人工警惕换成机器守护。
    """

    def test_lists_match(self):
        import re
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        conv = (ROOT / "docs" / "conventions.md").read_text(encoding="utf-8")
        in_skill = set(re.findall(r"project-specs/([A-Za-z-]+\.md)", skill))
        # conventions §13 的 project-specs 单元格
        m = re.search(r"`project-specs/`[^|]*\|([^|]*)\|", conv)
        self.assertIsNotNone(m, "conventions §13 缺 project-specs 行")
        in_conv = set(re.findall(r"`([A-Za-z-]+\.md)`", m.group(1)))
        only_skill = in_skill - in_conv
        only_conv = in_conv - in_skill
        self.assertEqual(
            (only_skill, only_conv), (set(), set()),
            f"project-specs 清单漂移 —— 仅 SKILL 有:{only_skill} · 仅 conventions 有:{only_conv}"
            "(新增项目级文档要同时接 SKILL 路由表 + conventions §13)")
