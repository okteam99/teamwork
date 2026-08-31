"""四档流程:micro / tiny / lite / full(用户拍板)。

拍板链:
①「我们是否考虑加回多档流程」→ 加;
②「tiny  dev → review(单路 architect)→ pm_acceptance → ship
   lite  dev(TC 并行)→ 单路 architect → test → pm_acceptance → ship  这样合理么」;
③「lite 是否也要有 PRD,不要 TC,要 verify-ac」;
④「lite 是不是可以被 full 装配出来」→ 是。

设计要点(本文件锁的就是这三条):
- **档数 ≠ preset 数**:四档、三 preset。preset 只给「不立就走不通链」的档
  (micro 跳 review/test · tiny 无 goal/blueprint 入口);lite 与 full 只差
  「跳 blueprint」一条边 → 加直边 + 装配旋钮,不加图。多一张转移图 = 多一处要
  同步的口径,legacy lite/blueprint_lite 正是这么烂掉的(三份 flow-key 实现对
  同一输入解析出两张不同的图)。
- **降档不降用户主权**:lite 保留 PRD 与终确认停等;降的是文档与路数,不是拍板权。
- **降档不降独立性**:tiny/lite 单路 architect 仍须错开模型(单路不变式)。
- **绑定载体换而不撤**:lite 无 TC → AC↔测试绑定改走 PRD `acceptance_criteria[].test_refs`,
  且校验**引用真实存在**(TC 模式的老坑:点名一个全仓不存在的函数,覆盖率照样全绿)。
"""
import subprocess
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

import state as S                                    # noqa: E402
import _v8_engine as E                               # noqa: E402
import _v8_stage_specs as SP                         # noqa: E402


class _Args:
    feature = "/nonexistent-feature-dir"


def _feature(preset="full", **hints):
    return {"flow_type": "Feature", "preset": preset,
            "execution_hints": hints, "stage_contracts": {}}


# ─── 1 · 档数 ≠ preset 数 ──────────────────────────────────────────────

class TestPresetsAreStructuralOnly(unittest.TestCase):

    def test_tiers_named_but_only_structural_ones_get_graphs(self):
        """v8.343 supersede:档名全部可选(六档)· 但只有结构档有自己的静态图。

        本条 v8.342 初版断言「lite 不是 preset」—— 那是当时的实现手段(避免多一张图),
        不是原则。v8.343 让链从维度推导之后,档名不再意味着一张图,于是 lite/medium
        可以当档名给出。原则(不许多一张图)由下一条 test_lite_adds_no_graph 继续守。
        """
        for t in ("full", "medium", "lite", "tiny", "floor", "micro"):
            self.assertIn(t, S.FEATURE_PRESETS, t)
            self.assertIn(t, S.TIER_DIMS, t)
            self.assertIn(t, S.TIER_ADMISSION, t)      # 每档必须有一句可判入场问句

    def test_lite_adds_no_graph(self):
        """最强锁:lite 不许有自己的转移图 —— 它就是 Feature 图。"""
        self.assertNotIn("Feature:lite", S.FLOW_BY_TYPE)
        lite = _feature(blueprint_needed=False)
        self.assertIs(E._resolve_flow_graph(lite, S.FLOW_BY_TYPE), S.FEATURE_FLOW)
        self.assertEqual(SP._flow_key(lite), "Feature")   # 不是第四个流键

    def test_cli_exposes_all_tiers_and_custom(self):
        out = subprocess.run(
            [sys.executable, str(SKILL_ROOT / "tools" / "state.py"), "init-feature", "--help"],
            capture_output=True, text=True, timeout=30).stdout
        flat = " ".join(out.split())          # argparse 按宽度折行 · 断言不吃换行位置
        self.assertIn("{full,medium,lite,tiny,floor,micro}", flat)
        # 🔴 档只是起手点 —— custom 入口必须在同一处可见,否则 AI 只会在六个名字里挑
        self.assertIn("--dims", flat)
        self.assertIn("档只是起手点", flat)


# ─── 2 · tiny:独立 preset · 零文档 · 无 test ────────────────────────────

class TestTinyPreset(unittest.TestCase):

    def setUp(self):
        self.st = _feature("tiny")

    def test_chain_matches_user_wording(self):
        """拍板原文:dev → review(单路 architect)→ pm_acceptance → ship。"""
        g = S.resolve_flow_graph("Feature", "tiny")
        self.assertEqual(g["dev"], ["review"])
        self.assertIn("pm_acceptance", g["review"])
        self.assertIn("ship", g["pm_acceptance"])
        self.assertNotIn("test", g)                   # 无 test stage(diff 可验)
        self.assertNotIn("goal", g)                   # 零文档 → 无 goal/blueprint 入口
        self.assertNotIn("blueprint", g)

    def test_review_failure_still_returns_to_dev(self):
        """降档不降返工路径 —— NEEDS_REVISION 照样回 dev。"""
        self.assertIn("dev", S.resolve_flow_graph("Feature", "tiny")["review"])

    def test_initial_stage_is_dev(self):
        self.assertEqual(
            S.DEFAULT_INITIAL_STAGE[S.internal_flow_key("Feature", "tiny")], "dev")

    def test_flow_key_consistent_across_three_impls(self):
        """v8.293 教训:同一输入必须在 state.py / engine / specs 解析成同一个键。"""
        self.assertEqual(S.internal_flow_key("Feature", "tiny"), "Tiny")
        self.assertEqual(E._internal_flow_key(self.st), "Tiny")
        self.assertEqual(SP._flow_key(self.st), "Tiny")
        self.assertIs(E._resolve_flow_graph(self.st, S.FLOW_BY_TYPE),
                      S.resolve_flow_graph("Feature", "tiny"))

    def test_gates_that_would_deadlock_are_open(self):
        """tiny 没有 blueprint/PRD/test —— 这三道门必须对它放行,否则链根本走不动。"""
        self.assertTrue(SP._check_blueprint_or_alt_done(self.st, _Args()))
        self.assertTrue(SP._check_prd_or_bug_report(self.st, _Args()))
        self.assertTrue(SP._check_test_done_or_micro(self.st, _Args()))

    def test_review_approve_skips_test(self):
        st = dict(self.st, stage_contracts={
            "review": {"output_satisfied": True, "evidence": {"verdict": "APPROVE"}}})
        nxt = SP._review_transition(st)
        self.assertEqual(nxt, "pm_acceptance")
        self.assertIn(nxt, S.resolve_flow_graph("Feature", "tiny")["review"])  # 转移合法

    def test_ac_binding_gate_skips(self):
        ok, msg = SP._evidence_ac_test_binding(self.st, _Args())
        self.assertTrue(ok)
        self.assertIn("skipped", msg)

    def test_roster_is_single_route_plus_pm(self):
        """v8.346 年检反转:单路从 architect 改 external(逐 stage 产出 ext>arch · 总量 2.1×)。

        本条初版锁死 architect —— 那是 v8.342 推的,没有数据支撑;289 行台账说被砍掉的
        恰是产出最高的一路。锁的实质(**单路 + PM**)不变,换的是留哪一路。"""
        r = E.build_default_stage_review_roles("Feature", "tiny")
        self.assertEqual(r.get("review"), ["external"])
        self.assertEqual(len(r.get("review")), 1)          # 仍是单路
        self.assertEqual(r.get("pm_acceptance"), ["pm"])

    def test_prepare_check_previews_tiny_chain(self):
        """定了 tiny 却预览出 11-stage 全链 = 已减掉的税又摆回用户面前(配置立了没接线)。"""
        import json
        import tempfile
        tmp = Path(tempfile.mkdtemp())
        (tmp / "docs" / "features").mkdir(parents=True)
        judgment = json.dumps({"sections_reviewed": ["§2.1", "§2.2"], "matched_signals": [],
                               "recommended_flow_type": "Feature", "ai_rationale": "t"})

        def preview(preset):
            r = subprocess.run(
                [sys.executable, str(SKILL_ROOT / "tools" / "state.py"), "prepare-check",
                 "--feature-id-prefix", "TEST",
                 "--features-root", str(tmp / "docs" / "features"),
                 "--flow-type", "Feature", "--preset", preset,
                 "--user-intent", "t", "--admission-judgment", judgment],
                capture_output=True, text=True, timeout=30, cwd=tmp)
            return [c["stage"] for c in json.loads(r.stdout).get("stage_chain_preview", [])]

        self.assertEqual(preview("tiny"), ["dev", "review", "pm_acceptance", "ship"])
        self.assertEqual(preview("micro"), ["execute", "ship"])
        self.assertIn("goal", preview("full"))          # full 回归:仍是全链

    def test_chain_preview_shows_reviewers(self):
        """preview 按内部键查 roster —— 原实现用 raw flow_type 查恒 miss(Micro 无条目才没暴露)。"""
        preview = {c["stage"]: c["reviewers"] for c in E.build_stage_chain_preview("Feature:tiny")}
        self.assertEqual(preview["review"], ["external"])
        self.assertEqual(preview["pm_acceptance"], ["pm"])

    def test_dev_brief_gives_spec_carrier(self):
        b = SP.DEV_SPEC.brief_template_fn(self.st)
        self.assertIn("理解卡", b)
        self.assertIn("回显", b)                       # 零文档 → 理解必须显式对齐一次
        self.assertNotIn("按 TECH.md 实现代码", b)      # 别让它去找不存在的 TECH

    def test_review_brief_scopes_to_blocker(self):
        b = SP.REVIEW_SPEC.brief_template_fn(self.st)
        self.assertIn("只拦 BLOCKER", b)
        self.assertIn("错开模型", b)


# ─── 3 · lite:full 的装配形态 ──────────────────────────────────────────

class TestLiteAssembly(unittest.TestCase):

    def setUp(self):
        self.lite = _feature(blueprint_needed=False, ui_design_needed=False)
        self.lite["stage_contracts"] = {"goal": {"output_satisfied": True}}

    def test_knob_is_explicit_false_only(self):
        """保守偏置:不传 / true 都走 full —— 没给判断就别替用户降档。"""
        self.assertTrue(SP._blueprint_skipped(self.lite))
        self.assertFalse(SP._blueprint_skipped(_feature()))
        self.assertFalse(SP._blueprint_skipped(_feature(blueprint_needed=True)))

    def test_knob_persisted_from_goal_complete(self):
        from argparse import Namespace
        st = {}
        SP.persist_args_to_evidence("goal", st, Namespace(
            needs_ui="false", needs_blueprint="false", needs_browser_e2e=None))
        self.assertIs(st["execution_hints"]["blueprint_needed"], False)

    def test_goal_and_ui_design_route_to_dev(self):
        self.assertEqual(SP._goal_transition(self.lite), "dev")
        ui = _feature(blueprint_needed=False, ui_design_needed=True)
        self.assertEqual(SP._goal_transition(ui), "ui_design")     # UI 优先 · 两旋钮独立
        self.assertEqual(SP._ui_design_transition(ui), "dev")

    def test_direct_edges_are_legal_transitions(self):
        """旋钮拧了但图上没边 = 装配当场卡死 —— 锁这条边真存在。"""
        self.assertIn("dev", S.FEATURE_FLOW["goal"])
        self.assertIn("dev", S.FEATURE_FLOW["ui_design"])

    def test_dev_prerequisite_falls_back_to_goal(self):
        """跳 blueprint 后 dev 前置换成 goal 完成 —— 不是无条件放行。"""
        self.assertTrue(SP._check_blueprint_or_alt_done(self.lite, _Args()))
        not_done = dict(self.lite, stage_contracts={})
        self.assertFalse(SP._check_blueprint_or_alt_done(not_done, _Args()))

    def test_lite_keeps_test_stage(self):
        """与 tiny 的分界:lite 需跑链路 —— pm 前置照卡 test。"""
        self.assertFalse(SP._check_test_done_or_micro(self.lite, _Args()))
        st = dict(self.lite, stage_contracts={
            "review": {"output_satisfied": True, "evidence": {"verdict": "APPROVE"}}})
        self.assertEqual(SP._review_transition(st), "test")

    def test_lite_keeps_prd_requirement(self):
        """用户拍板「lite 也要有 PRD」—— PRD 门不因降档松开。"""
        self.assertFalse(SP._check_prd_or_bug_report(self.lite, _Args()))

    def test_full_regression_untouched(self):
        full = _feature(ui_design_needed=False)
        self.assertEqual(SP._goal_transition(full), "blueprint")
        self.assertEqual(SP._ui_design_transition(full), "blueprint")
        self.assertFalse(SP._check_blueprint_or_alt_done(full, _Args()))


# ─── 4 · verify-ac test-refs:换载体 · 且校验引用真实存在 ────────────────

_PRD = """<!-- TEAMWORK-MACHINE
feature_id: "X-F001-x"
acceptance_criteria:
  - id: AC-1
    test_refs: {refs}
-->
"""


class TestTestRefsBinding(unittest.TestCase):

    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "tests").mkdir()
        (self.tmp / "tests" / "test_a.py").write_text(
            "def test_real_case():\n    assert True\n", encoding="utf-8")

    def _run(self, refs):
        prd = self.tmp / "PRD.md"
        prd.write_text(_PRD.format(refs=refs), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SKILL_ROOT / "templates" / "verify-ac.py"),
             "--prd", str(prd), "--mode", "test-refs", "--repo-root", str(self.tmp)],
            capture_output=True, text=True, timeout=30)

    def test_real_reference_passes(self):
        self.assertEqual(self._run('["tests/test_a.py::test_real_case"]').returncode, 0)

    def test_file_only_reference_passes(self):
        self.assertEqual(self._run('["tests/test_a.py"]').returncode, 0)

    def test_empty_refs_fail(self):
        r = self._run("[]")
        self.assertEqual(r.returncode, 3)
        self.assertIn("test_refs 为空", r.stdout)

    def test_missing_file_fails(self):
        self.assertEqual(self._run('["tests/test_ghost.py"]').returncode, 3)

    def test_named_case_that_does_not_exist_fails(self):
        """本模式存在的理由:TC 模式只核 id 对得上,点名的函数不存在照样全绿。"""
        r = self._run('["tests/test_a.py::test_never_written"]')
        self.assertEqual(r.returncode, 3)
        self.assertIn("用例名未出现", r.stdout)

    def test_tc_mode_still_default(self):
        """默认档不受影响:不传 --mode 仍走 AC↔TC 覆盖校验。"""
        out = subprocess.run(
            [sys.executable, str(SKILL_ROOT / "templates" / "verify-ac.py"), "--help"],
            capture_output=True, text=True, timeout=30).stdout
        flat = " ".join(out.split())
        self.assertIn("{tc,test-refs}", flat)
        self.assertIn("tc(默认)", flat)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "verify_ac", SKILL_ROOT / "templates" / "verify-ac.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertTrue(hasattr(mod, "verify_test_refs"))


class TestGateRoutesToTestRefs(unittest.TestCase):
    """门不休眠:lite 下 ac_test_binding 换口径而不是 skip。"""

    def test_lite_gate_runs_and_fails_without_refs(self):
        import tempfile
        tmp = Path(tempfile.mkdtemp())
        (tmp / "PRD.md").write_text(_PRD.format(refs="[]"), encoding="utf-8")
        st = _feature(blueprint_needed=False)
        st["worktree"] = {"path": str(tmp)}

        class A:
            feature = str(tmp)

        ok, msg = SP._evidence_ac_test_binding(st, A())
        self.assertFalse(ok, "lite 无 TC 时门必须仍咬合(校验 test_refs)· 不许 skip")
        self.assertIn("verify-ac.py FAIL", msg)

    def test_code_root_prefers_worktree(self):
        st = _feature(blueprint_needed=False)
        st["worktree"] = {"path": str(SKILL_ROOT)}
        self.assertEqual(SP._code_root_for(st, Path("/nonexistent")), SKILL_ROOT)


# ─── 5 · spec 侧载体 ───────────────────────────────────────────────────

class TestSpecCarriers(unittest.TestCase):

    def test_flows_lists_every_tier_with_admission(self):
        """v8.343:FLOWS 从「档表」升级成「维度 + 档表」· 每档一行 telos。"""
        t = (SKILL_ROOT / "FLOWS.md").read_text(encoding="utf-8")
        for tier in ("full", "medium", "lite", "tiny", "floor", "micro"):
            self.assertIn(f"Feature · `{tier}`", t, tier)
        self.assertIn("链由维度推导", t)
        self.assertIn("起手点不是终点", t)      # 档可拧 · 不是六选一
        self.assertIn("零独立图", t)            # v8.293 真正要防的东西

    def test_goal_stage_carries_dimension_matrix(self):
        t = (SKILL_ROOT / "stages" / "goal-stage.md").read_text(encoding="utf-8")
        self.assertIn("[blueprint 进/跳]", t)
        for d in ("D1 规格深度", "D2 证据门", "D3 验证深度", "D4 评审力度"):
            self.assertIn(d, t, d)
        self.assertIn("--needs-blueprint", t)
        self.assertIn("显式修订点", t)          # v8.343 计划 + 修订点

    def test_prd_template_documents_lite_carrier(self):
        t = (SKILL_ROOT / "templates" / "prd.md").read_text(encoding="utf-8")
        seg = next(l for l in t.splitlines() if l.strip().startswith("test_refs: []"))
        self.assertIn("lite", seg)
        self.assertIn("真实存在", seg)


if __name__ == "__main__":
    unittest.main()
