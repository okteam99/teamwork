"""v8.358 · 多轮审查的幻觉风险(用户提问 → 拍板)。

用户:「多轮审查是否容易幻觉出来一些不存在的场景」→「落」→
「这个场景在本 feature 的真实输入下会发生吗,这个反问会应用在 goal 和 tech 阶段么」。

查证结论:框架的防幻觉机制相当完整(code_evidence 防「猜测式 finding」· 逐条裁决
质疑→确认→回读真实代码 · adversarial_self_check · 对抗复现「复现不出降 MINOR」·
rejected 词表含 false positive),**但装反了**:

  `grep -c "禁全量重扫|范围锁定"` → review=1 · goal=0 · blueprint=0

  · review **有代码可 grounding**,finding 能被回读证伪 —— 却锁得最严;
  · goal/blueprint 是**纯文档评审**,「这个需求可能有问题」既证实不了也证伪不了
    —— 却允许并鼓励 Round 2+「找新」(goal-stage 原文如此)。
  Round 1 把真问题找完后仍被要求找新,剩下能找的只有边角。

而 v8.355 新增的 ⚔️/💡 两段恰恰是**必填产出 + 零证据要求**的组合(`code_evidence`
只管 `technical-consistency`,够不着 `premise-challenge` 和清单外洞察)—— 产出压力
被加强了,grounding 却没跟上。

🔴 本版最关键的一条是**用户追问逼出来的**:防幻觉判据「真实输入下会发生吗」
**不能原样用在 goal**,否则与 v8.350 的范围收窄防御正面冲突(详下方测试)。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class TestScopeLockCoversDocumentReviews(unittest.TestCase):
    """范围锁定要推广到纯文档评审 —— 那里才是多轮幻觉的高发处。"""

    def test_all_three_stages_lock_round_two(self):
        for rel in ("stages/goal-stage.md", "stages/blueprint-stage.md", "stages/review-stage.md"):
            t = _read(rel)
            self.assertIn("禁全量重扫", t, f"{rel} 的 Round 2+ 没有范围锁定")

    def test_goal_no_longer_asks_for_new_findings(self):
        """原文要求 Round 2+「核实 fix + 找新」—— 真问题找完后,「找新」只能挖边角。"""
        t = _read("stages/goal-stage.md")
        self.assertNotIn("核实 fix + 找新", t)
        self.assertIn("修订处的连带影响", t)

    def test_new_findings_need_a_why_not_found_earlier(self):
        for rel in ("stages/goal-stage.md", "stages/blueprint-stage.md", "stages/review-stage.md"):
            self.assertIn("为何首轮未发现", _read(rel), f"{rel} 缺新 finding 的举证要求")

    def test_document_review_rationale_is_recorded(self):
        """why 要留在文档里 —— 否则下次有人会把锁去掉。"""
        for rel in ("stages/goal-stage.md", "stages/blueprint-stage.md"):
            t = _read(rel)
            self.assertIn("纯文档评审", t, f"{rel} 没说清为什么文档评审更需要锁")


class TestChallengeAndInsightNeedGrounding(unittest.TestCase):
    """⚔️/💡 = 必填产出 + 零证据要求 —— 幻觉最高发的组合。"""

    def test_skill_requires_a_concrete_anchor(self):
        sk = _read("SKILL.md")
        self.assertIn("指认落点", sk)
        self.assertIn("说不出具体落点", sk)

    def test_skill_names_the_coverage_hole_in_code_evidence(self):
        """必须写明「code_evidence 够不着这两段」—— 否则会被误以为已有证据门覆盖。"""
        sk = _read("SKILL.md")
        self.assertIn("premise-challenge", sk)
        self.assertRegex(sk, r"code_evidence[^。]*technical-consistency")

    def test_filling_is_not_the_goal(self):
        """🔴 出口存在 ≠ 压力不存在 —— 必须明说「编一个比空着更贵」。"""
        self.assertIn("编一个出来比空着更贵", _read("SKILL.md"))


class TestCriterionHasAGoalException(unittest.TestCase):
    """🔴 本版最关键的一条(用户追问逼出来的)。

    「这个场景在真实输入下会发生吗」在 review/blueprint 成立,在 **goal 不成立**:

      · PRD 阶段**正在定义什么是「真实输入」** → 拿它驳回质疑是**循环论证**;
      · 更危险的是它会给「悄悄收窄范围」一个正当理由 —— v8.350 的实证事故正是这个
        形状(狭义解释某能力并排除另一半,PRD 完全自洽,dev 与 review 都在认真验证
        一个错误的范围定义)。

    两条规则方向相反,必须显式分流,否则防幻觉会吃掉防范围收窄。
    """

    def test_blueprint_and_review_may_drop_it(self):
        sk = _read("SKILL.md")
        m = re.search(r"真实输入下会发生吗.{0,400}", sk, re.S)
        self.assertIsNotNone(m)
        seg = m.group(0)
        self.assertIn("降级或撤回", seg)
        self.assertIn("blueprint", seg)

    def test_goal_must_escalate_not_drop(self):
        sk = _read("SKILL.md")
        m = re.search(r"真实输入下会发生吗.{0,500}", sk, re.S)
        seg = m.group(0)
        self.assertIn("循环论证", seg, "没说清为什么 goal 不适用")
        self.assertIn("§待决策项", seg, "goal 的出口必须是转交用户,不是撤回")

    def test_goal_stage_carries_the_same_exception(self):
        """运行时读的是 stage doc —— 只写在 SKILL 里不够。"""
        g = _read("stages/goal-stage.md")
        self.assertIn("不许用「真实输入下不会发生」驳回质疑", g)
        self.assertIn("范围未定", g)

    def test_exception_is_tied_to_the_scope_narrowing_defense(self):
        """与 v8.350「这个排除是做不到还是我选的边界」是同一判据 · 不能各走各的。"""
        g = _read("stages/goal-stage.md")
        self.assertIn("做不到", g)
        self.assertIn("我选的边界", g)

    def test_the_two_rules_do_not_cancel_each_other(self):
        """回归锁:防幻觉与防范围收窄都要在,且 goal 侧以「转交」而非「撤回」收口。"""
        g = _read("stages/goal-stage.md")
        self.assertIn("禁全量重扫", g)          # 防幻觉
        self.assertIn("进 §待决策项", g)         # 防范围收窄
        # goal 不得出现「撤回」式处置
        m = re.search(r"不许用「真实输入下不会发生」驳回质疑.{0,220}", g, re.S)
        self.assertNotIn("撤回", m.group(0), "goal 侧不该给出撤回出口")


if __name__ == "__main__":
    unittest.main()
