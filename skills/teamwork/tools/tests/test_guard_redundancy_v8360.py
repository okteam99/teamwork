"""v8.360 · 防过度防护:先问冗余,再算 ROI(用户拍板)。

起因 case(SVC-CORE payout 两态 · 财务账本):TECH 列了 7 项 DB 守卫。用户问
「有必要做这个 check 么,是不是代码保障就好了」→「你看下还有哪些不必要的 check,
减少过渡保护」。AI 第二轮自己分出三组,**第一组「纯冗余,建议全删」** ——
理由是「它们只是把后面必然发生的失败提前说清楚,**删了行为不变**」:
  · up 前置断言「无 status='failed' 行」→ 紧接着重建的列 CHECK 对存量行本来就会 23514;
  · 三条常驻 grep 门「零引用」→ 删掉的表和函数编译期就报错。

🔴 关键:这些冗余是在**冷审 26 条全部处置、Round 2 双路 APPROVE 之后**,靠用户
追问两次才挖出来的。框架明明有 ROI 规则(v8.266/v8.279)却没拦住,三层原因:

  ① **分类漏网(决定性)**:ROI 算账的对象定义是「降级兜底/安全兜底(fallback /
     degradation / 重试熔断 / 防御层)」= 出错时怎么办(fail-safe);而 DB CHECK /
     trigger / 前置断言是**不让错发生**(guard)。实证:那份 TECH 白纸黑字写着
     「🛡️ 兜底清单:无」,同时挂着 7 项 DB 守卫 —— 整条算账流程从未触发。
  ② **ROI 对守卫天然算得过**:财务账本脏数据后果极高 → 概率×后果永远立得住。
     v8.279 自己就写了「安全加固/兜底降级听着最负责任故最难驳」。
  ③ **冷审拦不住**:冷审 mandate 是找缺陷,而「多一道无害的断言」读起来是更严谨 ——
     **防护读起来永远像更负责任**(同 v8.354「限制读起来永远像最小范围」)。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class TestGuardsAreInScope(unittest.TestCase):
    """① 分类漏网是决定性的 —— 清单说「无」,后面全不发生。"""

    GUARD_KINDS = ("DB CHECK", "trigger", "前置断言", "常驻门禁")

    def test_list_renamed_to_cover_guards(self):
        t = _read("templates/tech.md")
        self.assertIn("**🛡️ 兜底与守卫清单**", t)
        self.assertIn("不止 fail-safe", t)

    def test_guard_kinds_are_enumerated(self):
        """不枚举就还是靠 AI 自己归类 —— 而它上次把 7 项守卫归成了「无兜底」。"""
        t = _read("templates/tech.md")
        for k in self.GUARD_KINDS:
            self.assertIn(k, t, f"tech.md 未点名守卫类型 {k}")

    def test_pause_trigger_follows_the_rename(self):
        """命名漏一类 → 暂停点触发条件跟着漏 → 用户根本看不到这些守卫。"""
        bp = _read("stages/blueprint-stage.md")
        self.assertIn("🛡️ 兜底与守卫清单非空", bp)
        self.assertNotIn("🛡️ 兜底清单非空", bp)

    def test_every_consumer_was_updated(self):
        """v8.356 的教训:改跨文档语义前先 grep 出全部消费方,别凭记忆。"""
        stale = []
        for sub in ("SKILL.md", "stages", "templates", "standards", "tools"):
            p = ROOT / sub
            files = [p] if p.is_file() else [
                f for f in p.rglob("*")
                if f.is_file() and f.suffix in (".md", ".py")
                and "__pycache__" not in str(f) and "tools/tests/" not in str(f.relative_to(ROOT))
            ]
            for f in files:
                txt = f.read_text(encoding="utf-8", errors="replace")
                if re.search(r"§兜底清单|兜底清单非空|\*\*🛡️ 兜底清单\*\*", txt):
                    stale.append(str(f.relative_to(ROOT)))
        self.assertEqual(stale, [], f"仍有消费方用旧名:{stale}")


class TestRedundancyIsAskedBeforeROI(unittest.TestCase):
    """② 顺序不可换 —— ROI 对纯冗余也会算出「保留」(成本十几行 vs 后果极高)。"""

    def test_criterion_is_a_decidable_question(self):
        t = _read("templates/tech.md")
        self.assertIn("这道防护删掉之后,行为会变吗?", t)

    def test_three_way_split_is_spelled_out(self):
        """三分法正是那个 AI 第二轮自己得出的 —— 固化下来就不用等用户问两次。"""
        t = _read("templates/tech.md")
        self.assertIn("纯冗余,直接删", t)
        self.assertIn("只在绕过正常路径时变", t)
        self.assertRegex(t, r"正常路径就变.{0,40}功能")

    def test_order_is_explicit_and_justified(self):
        t = _read("templates/tech.md")
        self.assertIn("顺序不可换", t)
        self.assertRegex(t, r"ROI 对纯冗余也会算出「保留」")

    def test_redundant_ones_do_not_enter_the_roi_table(self):
        """进了表就会被算出「保留」—— 必须在入表前拦掉。"""
        t = _read("templates/tech.md")
        self.assertIn("不进下方清单、不用算 ROI", t)
        self.assertIn("不该出现在本表", t)

    def test_table_carries_the_column(self):
        t = _read("templates/tech.md")
        m = re.search(r"\| 兜底/守卫 \|[^\n]*", t)
        self.assertIsNotNone(m, "清单表头未更新")
        self.assertIn("删了行为会变吗", m.group(0))


class TestReviewSideHasTheChallenge(unittest.TestCase):
    """③ 冷审拦不住 —— 防护读起来永远像更负责任,所以要写成对抗题目。"""

    def test_blueprint_challenge_section_carries_guard_necessity(self):
        bp = _read("stages/blueprint-stage.md")
        self.assertIn("守卫必要性", bp)
        self.assertIn("这道守卫是需求要求的,还是我加的?", bp)

    def test_my_own_guard_must_survive_a_stronger_test(self):
        """🔴 「不加会出什么事」还不够 —— 那件事**不能已被别的机制拦住**,否则就是冗余。"""
        bp = _read("stages/blueprint-stage.md")
        self.assertIn("那件事不会被别的机制拦住", bp)

    def test_rationale_names_the_shared_disease(self):
        bp = _read("stages/blueprint-stage.md")
        self.assertIn("防护读起来永远像更负责任", bp)
        self.assertIn("限制读起来永远像最小范围", bp, "没接上 v8.354 的同族判断")

    def test_external_review_protocol_asks_redundancy_first(self):
        """external 天然偏加防御层 —— 它的 finding 裁决侧也要先问冗余。"""
        e = _read("standards/external-model-usage.md")
        self.assertIn("删了行为会变吗", e)
        self.assertIn("不进 ROI", e)


class TestExistingDefensesSurvive(unittest.TestCase):
    """回归锁:新判据不能把既有的 ROI / 兜底透出吃掉(两者是先后不是取代)。"""

    def test_roi_accounting_still_required(self):
        t = _read("templates/tech.md")
        self.assertIn("概率×后果", t)
        self.assertIn("ROI 结论", t)

    def test_kept_items_still_surface_to_user(self):
        t = _read("templates/tech.md")
        self.assertIn("随 §7.5 暂停点透出给用户拍板", t)
        self.assertIn("💬 大白话", t)

    def test_density_gate_respected(self):
        """v8.283 价值门:规则要带 why —— 加规则就得加 why,不许只堆 🔴。"""
        t = _read("templates/tech.md")
        self.assertLess(t.count("🔴") / max(t.count("why"), 1), 12)


if __name__ == "__main__":
    unittest.main()
