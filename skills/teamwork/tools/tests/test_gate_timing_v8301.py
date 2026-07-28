"""v8.301:不在门禁的适用阶段之前跑它 —— 注定失败的调用比不调用更糟。

实证(SVC-CORE-F260728):AI 在 **goal 阶段**手跑 `verify-ac.py`,必然 FAIL
(TC.md 是 blueprint 产物),只能自辩「预期的失败」。三件事同时成立:

  ① 它想验的「AC 机读块本身」**早已由 goal-complete 的 prd_template_conformance 校验** → 纯冗余;
  ② 诱导源是 `templates/prd.md` 机读块头的「verify-ac + goal-complete 解析此块」——
     陈述属实,但摆在 goal 阶段的 PRD 里就读成「去跑 verify-ac 验一下」·**属实的话摆错位置也会误导**;
  ③ 工具给的是**裸失败**(「TC.md 不存在」),没告诉调用方「你不该在这个时点调我」。

🔴 危害不在这一次浪费:**「预期的 FAIL」一旦被正常化,真 FAIL 就会被同样对待** ——
门禁的全部价值在于「红了就是有事」。
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
VERIFY_AC = ROOT / "templates" / "verify-ac.py"


class TestVerifyAcRoutesInsteadOfBareFailing(unittest.TestCase):

    def _run_without_tc(self):
        d = Path(tempfile.mkdtemp(prefix="tw-gate-timing-"))
        (d / "PRD.md").write_text(
            '<!-- TEAMWORK-MACHINE\nfeature_id: "F1"\nacceptance_criteria:\n  - id: AC-1\n-->\n',
            encoding="utf-8")
        return subprocess.run([sys.executable, str(VERIFY_AC), str(d)],
                              capture_output=True, text=True, timeout=30)

    def test_still_fails_so_downstream_gates_keep_working(self):
        """🔴 不能为了「好看」改成 exit 0 —— blueprint-complete / test-complete 的门依赖这个非零退出。"""
        self.assertEqual(self._run_without_tc().returncode, 1,
                         "TC 缺失必须仍是 FAIL,否则 blueprint/test 的 AC 覆盖门被拆")

    def test_message_routes_the_caller(self):
        """裸失败 → 路由信息:谁在什么时候跑我 · 你想验的东西归谁管。"""
        err = self._run_without_tc().stderr
        self.assertIn("blueprint", err, "未说明 TC 是哪个阶段的产物")
        self.assertIn("prd_template_conformance", err,
                      "未指路「AC 机读块本身由谁校验」→ 调用方还是会手跑本脚本")
        self.assertIn("无需手跑", err, "未明说不该在此时点调用")


class TestInducementRemoved(unittest.TestCase):
    """属实但摆错位置的话也会误导 —— PRD 模板把 verify-ac 与 goal-complete 并列写在机读块头。"""

    def test_prd_template_does_not_invite_goal_stage_run(self):
        t = (ROOT / "templates" / "prd.md").read_text(encoding="utf-8")
        self.assertNotIn("verify-ac + goal-complete 解析此块", t, "诱导源复活")
        self.assertIn("goal 阶段不必手跑 verify-ac", t, "未反向说明 → 下个读者还会跑")

    def test_templates_index_states_when_it_runs(self):
        t = (ROOT / "templates" / "README.md").read_text(encoding="utf-8")
        self.assertIn("blueprint-complete / test-complete 自动跑", t)
        self.assertIn("goal 阶段不适用", t)


class TestPolicyGeneralizesTheLesson(unittest.TestCase):
    """只修这一处不够 —— 「在门禁适用阶段之前跑它」是可复发的类。"""

    def test_policy_states_both_criteria(self):
        t = (ROOT / "standards" / "scripts-policy.md").read_text(encoding="utf-8")
        self.assertIn("这个门管的产物,现在存在吗", t, "缺判据①")
        self.assertIn("evidence_checks", t, "缺判据②(先查该 stage 已有的门)")

    def test_policy_names_the_real_harm(self):
        t = (ROOT / "standards" / "scripts-policy.md").read_text(encoding="utf-8")
        self.assertIn("真 FAIL 就会被同样对待", t,
                      "只说浪费一次 → 读者会觉得无所谓;真正的危害是 FAIL 被训练成噪声")

    def test_policy_assigns_the_tool_side_duty(self):
        """调用方纪律靠自觉会衰减;工具侧「给路由信息」是结构性的那一半。"""
        t = (ROOT / "standards" / "scripts-policy.md").read_text(encoding="utf-8")
        self.assertIn("给路由信息而不是裸失败", t)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestCommandsClassifiedByMemoryObligation(unittest.TestCase):
    """v8.301(用户拍板):该减的不是**脚本数量**,是**AI 需要记住的数量** —— 两回事。

    实测:56 子命令 = 30 流转 + 26 辅助;辅助里只有 6 个出现在流程 brief,20 个靠 AI 自己记。
    但那 20 个要分开看:10 个是**逃生口**(AI 主动跑才是问题 · 不记正确),
    10 个是**该在时点推却没推**的真缺口。

    🔴 删有用的命令 = 丢功能;**让命令在正确时点被 emit** = 零记忆负担 + 功能全留。
    verify-ac 那个 case 正是证明:问题不是脚本多,是 AI **记住了一个它不该在那个时点跑的脚本**。
    """

    def _skill(self):
        return (ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_three_buckets_by_memory_not_by_function(self):
        t = self._skill()
        self.assertIn("必记", t)
        self.assertIn("不必记(流程在动作点推给你)", t)
        self.assertIn("不必记也别主动跑", t, "逃生口未单列 → 又会和该推送的混一起")

    def test_criterion_is_stated_and_operational(self):
        """判据要能判:有确定动作时点 → 接 emit;没有 → 不进提醒。"""
        t = self._skill()
        self.assertIn("有没有一个确定的动作时点", t)
        self.assertIn("不许只写进文档", t, "缺这半句 → B 类会退化成「写进文档就算了」")

    def test_doc_is_not_arrival_is_explained(self):
        t = self._skill()
        self.assertIn("写进 stage 文档 ≠ 到达", t,
                      "不说明失效机理 → 下次还会认为「文档写了就够」")


class TestActionPointPushes(unittest.TestCase):
    """把 B 类真接进动作点 —— 照 v8.295 `stage_cost_hint` 的形态。"""

    def _engine(self):
        import sys as _s
        _s.path.insert(0, str(ROOT / "tools"))
        import _v8_engine as E  # type: ignore
        return E

    def test_preventability_fires_only_on_converged_review(self):
        E = self._engine()
        self.assertIsNotNone(E._preventability_hint("review", "/f", "APPROVE"))
        self.assertIsNotNone(E._preventability_hint("goal", "/f", None))
        self.assertIsNone(E._preventability_hint("review", "/f", "NEEDS_REVISION"),
                          "未收敛就提 = 数据会在多轮里重复记")
        for s in ("dev", "test", "ship", "execute"):
            self.assertIsNone(E._preventability_hint(s, "/f", "APPROVE"),
                              f"{s} 无评审 findings · 提了就是仪式税")

    def test_preventability_hint_is_runnable_and_explains_zero_case(self):
        E = self._engine()
        h = E._preventability_hint("review", "/abs/feat", "APPROVE")
        self.assertIn("review-preventability", h)
        self.assertIn("/abs/feat", h, "缺真实路径 → AI 还要自己拼")
        self.assertIn("--preventable 0", h,
                      "未说明零可预防也要记 → 「全 emergent」与「没记录」会被混同")

    def test_wired_into_complete_emit(self):
        src = (ROOT / "tools" / "_v8_engine.py").read_text(encoding="utf-8")
        self.assertIn('"preventability_hint": _pv_hint', src)

    def test_ledger_migrate_pushed_before_append(self):
        """`ledger-migrate` 必须在 append **之前**跑 —— 漏了会让新行按旧表头错位。"""
        src = (ROOT / "tools" / "_v8_ship.py").read_text(encoding="utf-8")
        self.assertIn("ledger-migrate", src, "ship1 brief 未推 ledger-migrate")
        self.assertIn("写台账行之前先跑", src, "未说明时序 → 会在 append 之后才跑(等于没跑)")
        self.assertIn("按旧表头错位", src, "未点名后果 → 会被当成可选步骤")

    def test_add_concern_intentionally_not_pushed(self):
        """反面用例:`add-concern`(auto skip 留痕)的动作点是 **AI 自己决定跳暂停点那一刻** ——

        机器观测不到,没有可挂的 emit。按本版判据「没有确定动作时点 → 不进提醒」,
        它留在文档里是**自洽的**,不是遗漏。锁住这个判断,免得后来者硬塞一个假时点。
        """
        src = (ROOT / "tools" / "_v8_engine.py").read_text(encoding="utf-8")
        self.assertNotIn("add-concern", src,
                         "给 add-concern 硬塞了 emit 时点 —— 但 auto skip 是 AI 内部决定,机器看不到")
