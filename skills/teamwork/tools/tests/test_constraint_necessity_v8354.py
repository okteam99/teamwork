"""v8.354 · PRD 需求简洁性:限制必要性(用户拍板)。

用户原话:「我们是否有PRD 需求简洁性的评审约束,例如不要扩展没必要的功能,不要做没必要的限制。」

查证结果:**加法侧有三层挡**(goal 6.5 功能优先·复杂度守恒 · PL 质疑七问「范围最小化」·
PRD 起草思考规范),**减法侧零命中** —— 搜遍 stages/roles/templates/standards 找不到任何
对着「限制」的简洁性判据。

🔴 为什么是结构性盲区(不是漏写):
  · PL 的 mandate 是把范围**往下压** —— 加法有对抗角色,减法没有;
  · **限制读起来永远像「最小范围」**,越保守越显得克制,没人会替你质疑它;
  · 代价不对称:多做一个功能 = 浪费工时(起草/评审当场看得见)·
    多加一条限制 = **用户真想做的事做不了**,而且要到上线才发现。

本版落三处载体(形容词不产生行为,槽位才产生 —— v8.334/337/341/351 连续实证):
  ① 判据一句话:**这条限制是「业务真要求的」还是「我加的」?**(与 v8.352 生效闸同构)
  ② 载体复用 v8.350 那张表:§Out of Scope → §Out of Scope 与限制,
     「性质」列收两族取值 · 「我加的」→ 末列必须写**不加会出什么事**,写不出就删掉;
  ③ 对抗角色:PL 质疑六问 → **七问**,第④问 = 限制必要性。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class TestSevenChallengesRenamed(unittest.TestCase):
    """六问 → 七问 必须跨全部载体一起改(单点改 = 下次读到旧数目的人按旧的做)。"""

    CARRIERS = [
        "roles/product-lead.md",
        "stages/goal-stage.md",
        "templates/prd.md",
        "tools/_v8_stage_specs.py",
        "tools/_v8_engine.py",
        "tools/state.py",
        "SKILL.md",
    ]

    def test_no_six_challenge_reference_left(self):
        """全仓不许再出现「六问」—— 数目对不上的引用会让人漏掉第七问。"""
        stale = []
        for sub in ("stages", "roles", "templates", "standards", "tools", "SKILL.md"):
            p = ROOT / sub
            files = [p] if p.is_file() else [
                f for f in p.rglob("*")
                if f.is_file() and f.suffix in (".md", ".py")
                and "__pycache__" not in str(f)
                # 测试文件可以合法引用历史(「六问 → 七问」本身就是被测事实)
                and "tools/tests/" not in str(f.relative_to(ROOT))
            ]
            for f in files:
                if "六问" in f.read_text(encoding="utf-8", errors="replace"):
                    stale.append(str(f.relative_to(ROOT)))
        self.assertEqual(stale, [], f"残留「六问」引用:{stale}")

    def test_seven_challenges_present_in_every_carrier(self):
        for rel in self.CARRIERS:
            self.assertIn("七问", _read(rel), f"{rel} 未同步到七问")

    def test_constraint_necessity_is_the_new_challenge(self):
        """新增的那一问必须点名「限制必要性」,不能只是把数字改大。"""
        for rel in ("roles/product-lead.md", "stages/goal-stage.md"):
            self.assertIn("限制必要性", _read(rel), f"{rel} 七问里没有限制必要性")

    def test_pl_challenge_gate_lists_seven(self):
        """PL-CHALLENGE 缺段提示要把七个名字都念出来(念漏 = AI 只做六个)。"""
        specs = _read("tools/_v8_stage_specs.py")
        m = re.search(r"PL 须按质疑七问\(([^)]*)\)", specs)
        self.assertIsNotNone(m, "缺 PL-CHALLENGE 提示")
        names = m.group(1).replace('"', "").replace("\n", "").replace(" ", "").strip("/").split("/")
        self.assertEqual(len(names), 7, f"提示里只有 {len(names)} 问:{names}")
        self.assertIn("限制必要性", names)

    def test_existing_behavior_ordinal_moved_to_seventh(self):
        """既有行为变更原是第⑥ · 插入限制必要性后是第⑦ —— 序号引用必须跟着挪。"""
        prd = _read("templates/prd.md")
        self.assertNotIn("⑥ 既有行为变更", prd)
        self.assertIn("⑦ 既有行为变更", prd)
        self.assertIn("质疑七问⑦ 既有行为变更", _read("stages/ui-design-stage.md"))


class TestCriterionIsAQuestionNotAnAdjective(unittest.TestCase):
    """判据必须是可判问句(v8.349/350/352 同法)—— 「不要做没必要的限制」本身不可判。"""

    def test_criterion_question_present(self):
        for rel in ("stages/goal-stage.md", "roles/product-lead.md", "templates/prd.md"):
            txt = _read(rel)
            self.assertIn("业务真要求", txt, f"{rel} 缺判据的一侧")
            self.assertIn("我加的", txt, f"{rel} 缺判据的另一侧")

    def test_my_own_constraint_must_state_consequence_or_be_dropped(self):
        """「我加的」不是标完就完 —— 要么写出不加会出什么事,要么删掉(闭合处置)。"""
        for rel in ("stages/goal-stage.md", "roles/product-lead.md", "templates/prd.md"):
            txt = _read(rel)
            self.assertIn("不加会出什么事", txt, f"{rel} 缺后果格")
            self.assertTrue(
                re.search(r"(去掉|删掉|删)", txt),
                f"{rel} 没写「写不出就去掉」这一半 —— 只标性质不处置 = 记账不治病",
            )

    def test_why_only_constraints_get_a_challenge(self):
        """理由要留在文档里:加法侧已有三层挡、减法侧没有对抗角色 + 代价不对称。"""
        goal = _read("stages/goal-stage.md")
        self.assertIn("减法侧", goal)
        self.assertIn("对抗角色", goal)
        self.assertRegex(goal, r"上线才发现")


class TestOutOfScopeCarriesConstraints(unittest.TestCase):
    """载体复用 v8.350 那张表 —— 不新增节(PRD 瘦身门只剩几行余量 · 双载体必漂)。"""

    def setUp(self):
        self.prd = _read("templates/prd.md")
        m = re.search(r"(?ms)^##\s*Out of Scope.*?(?=^##\s|\Z)", self.prd)
        self.assertIsNotNone(m, "§Out of Scope 段没了")
        self.seg = m.group(0)

    def test_section_covers_constraints_too(self):
        self.assertIn("## Out of Scope 与限制", self.prd)

    def test_no_separate_constraint_section(self):
        """限制不许另开一节 —— 排除与限制是同一个判断的两半,分家必漂。"""
        heads = re.findall(r"(?m)^##\s*(.+)$", self.prd)
        self.assertEqual(
            [h for h in heads if "限制" in h], ["Out of Scope 与限制（🔴 必填）"], heads
        )

    def test_table_has_both_polarities_and_consequence_column(self):
        self.assertIn("性质", self.seg)
        self.assertIn("不加会出什么事", self.seg)
        for v in ("技术限制", "🔴 我的解释", "业务真要求", "🔴 我加的"):
            self.assertIn(v, self.seg, f"表里缺性质取值 {v}")

    def test_prd_still_under_slimming_gate(self):
        """v8.283 瘦身门 —— 服从门裁(v8.303 判例):压措辞,不改门限。"""
        self.assertLess(len(self.prd.splitlines()), 340)


class TestGateChecksConstraintCarrier(unittest.TestCase):
    """机器门:② 槽从「只查性质列」扩到「还要有限制必要性判据列」。"""

    def setUp(self):
        import importlib
        import sys

        sys.path.insert(0, str(ROOT / "tools"))
        self.specs = importlib.import_module("_v8_stage_specs")

    def _args(self, tmp):
        class A:
            feature = tmp

        return A()

    def _prd_body(self, oos: str) -> str:
        return (
            "## 意图对照\n"
            "| 用户说的词 | 我理解成 | 依据 | 若这条理解错了 → 最坏会怎样 |\n"
            "|---|---|---|---|\n"
            "| Link | 全部投放链接 | 用户说过 | 点击不回传 |\n"
            "① 术语解释对照 ② 排除与限制定性 ③ 反向验证:AC 覆盖了两个入口\n\n"
            + oos
        )

    def test_missing_consequence_column_fails(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "PRD.md").write_text(
                self._prd_body("## Out of Scope\n| 不做的事 | 性质 | 理由 |\n|---|---|---|\n| A | 技术限制 | x |\n"),
                encoding="utf-8",
            )
            ok, msg = self.specs._evidence_intent_reconciliation({}, self._args(d))
            self.assertFalse(ok)
            self.assertIn("限制必要性", msg)

    def test_full_table_passes(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "PRD.md").write_text(
                self._prd_body(
                    "## Out of Scope 与限制\n"
                    "| 不做的事 / 加的限制 | 性质 | 理由（🔴「我加的」写\"不加会出什么事\"） |\n"
                    "|---|---|---|\n"
                    "| 不做 A | 技术限制 | 上游没这接口 |\n"
                    "| 限制 B 上限 20 | 🔴 我加的 | 不加会出什么事:一次拉全量会打爆列表接口 |\n"
                ),
                encoding="utf-8",
            )
            ok, msg = self.specs._evidence_intent_reconciliation({}, self._args(d))
            self.assertTrue(ok, msg)

    def test_template_as_is_is_not_enough(self):
        """v8.350 教训:模板原样必须过不了门 —— 否则门形同虚设。"""
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "PRD.md").write_text(self.prd_text(), encoding="utf-8")
            ok, _ = self.specs._evidence_intent_reconciliation({}, self._args(d))
            self.assertFalse(ok, "模板原样竟然过门了")

    def prd_text(self):
        return _read("templates/prd.md")


class TestGoalBriefTellsAI(unittest.TestCase):
    """派单文案要带上这一问 —— 只改模板不改 brief = AI 照旧只想六问(v8.346 读写两端实证)。"""

    def test_brief_mentions_constraint_polarity(self):
        specs = _read("tools/_v8_stage_specs.py")
        m = re.search(r"🎯 \*\*意图对照\*\*.{0,1200}", specs, re.S)
        self.assertIsNotNone(m)
        seg = m.group(0)
        self.assertIn("业务真要求", seg)
        self.assertIn("我加的", seg)
        self.assertIn("不加会出什么事", seg)


if __name__ == "__main__":
    unittest.main()
