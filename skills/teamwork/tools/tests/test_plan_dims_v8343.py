"""维度矩阵 + 计划与显式修订点(用户拍板)。

拍板链:
①「把流程、环节、评审力度 3 个维度拆开,交给 AI 组装,给 AI 强烈的提示有权利精简流程、
   降低评审力度、决定评审模型,必须做合理的权衡,不能过度保守」
②「理论上拆出的力度最小可以直接 dev + ship」→ floor 档
③「是否渐进式的流程更合理,当前阶段执行完成再判断下一阶段要做啥,或者至少可以修改」
   → 取「计划 + 显式修订点」形态
④「lite 之后是否需要一个 medium 档,goal 和 blueprint 只有一路冷审」→ 需要
⑤「然后给 AI custom 装配权限」→ --dims / revise-plan

本文件锁四件事:
- **矩阵推出链**:derive_chain 是链的单源,加一档只加一行(medium 就是实现中途加的)。
  静态图降为存量回退,且被「推导边 ⊆ 静态边」锁住,漂了当场红。
- **档是起手点不是终点**:custom 装配(--dims)与逐维修订(revise-plan)都在;
  只报档名不拧是退化情形,不是默认姿态。
- **降档不降三样**:用户主权 / 评审独立性 / 已产生的证据门。
- **计划可改,历史不可改**:修订只影响未走的部分;加与减同价(都只要一行证据),
  轻的偏置留在档默认里、不留在举证难度里 —— 只让「减」举证 = v8.341 的保守偏置原样搬回来。
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

import state as S                      # noqa: E402
import _v8_engine as E                 # noqa: E402
import _v8_stage_specs as SP           # noqa: E402

STATE_PY = str(SKILL_ROOT / "tools" / "state.py")
TIERS = ("micro", "floor", "tiny", "lite", "medium", "full")


class _Args:
    def __init__(self, feature="/nonexistent"):
        self.feature = feature


def _st(tier, **over):
    return {"flow_type": "Feature", "preset": tier, "stage_contracts": {},
            "execution_hints": {},
            "assembly_plan": S.build_assembly_plan(tier, over or None)}


# ─── 1 · 矩阵推出链 ────────────────────────────────────────────────────

class TestMatrixDerivesChain(unittest.TestCase):

    def test_every_tier_derives_expected_chain(self):
        expect = {
            "micro":  ["execute", "ship"],
            "floor":  ["dev", "ship"],
            "tiny":   ["dev", "review", "pm_acceptance", "ship"],
            "lite":   ["goal", "dev", "review", "test", "pm_acceptance", "ship"],
            "medium": ["goal", "blueprint", "dev", "review", "test", "pm_acceptance", "ship"],
            "full":   ["goal", "blueprint", "dev", "review", "test", "pm_acceptance", "ship"],
        }
        for t, chain in expect.items():
            self.assertEqual(S.derive_chain(S.tier_dims(t)), chain, t)

    def test_medium_differs_from_full_only_in_review_intensity(self):
        """加一档不该多一条链 —— medium 与 full 同链、只差 D4(所以它不是结构档)。"""
        self.assertEqual(S.derive_chain(S.tier_dims("medium")),
                         S.derive_chain(S.tier_dims("full")))
        self.assertEqual(S.TIER_DIMS["medium"]["review"]["goal"], ["fast"])
        # v8.346:单路留 external(年检:逐 stage ext>arch · goal 用 fast 合并帽不受影响)
        self.assertEqual(S.TIER_DIMS["medium"]["review"]["blueprint"], ["external"])

    def test_switches_are_orthogonal_to_tier(self):
        """UI 是事实判断、e2e 是验证深度 —— 与轻重正交,任何档都能开。"""
        d = S.tier_dims("lite"); d["ui"] = True; d["verify_depth"] = "test_e2e"
        self.assertEqual(
            S.derive_chain(d),
            ["goal", "ui_design", "dev", "review", "test", "browser_e2e",
             "pm_acceptance", "ship"])

    def test_ship_survives_every_combination(self):
        """ship 在任何组合里都减不掉 —— 用户看见改动的最后一处。"""
        for t in TIERS:
            self.assertEqual(S.derive_chain(S.tier_dims(t))[-1], "ship", t)

    def test_rework_edges_survive_downgrade(self):
        """降档不降返工路径:评审/验收打回照样回 dev。"""
        for t in ("tiny", "lite", "medium", "full"):
            g = S.derive_flow_graph(S.tier_dims(t))
            for point in ("review", "pm_acceptance"):
                if point in g:
                    self.assertIn("dev", g[point], f"{t}.{point}")

    def test_derived_edges_are_subset_of_static_fallback(self):
        """反漂锁:推导图不许发明静态回退图里没有的边(存量 state 走静态图)。"""
        static_key = {"micro": "Feature:micro", "floor": "Feature:floor",
                      "tiny": "Feature:tiny", "lite": "Feature",
                      "medium": "Feature", "full": "Feature"}
        for t, key in static_key.items():
            derived, static = S.derive_flow_graph(S.tier_dims(t)), S.FLOW_BY_TYPE[key]
            for a, nxts in derived.items():
                for b in nxts:
                    self.assertIn(b, static.get(a, []), f"{t}: {a}→{b} 不在 {key}")

    def test_state_py_and_engine_derive_identically(self):
        """v8.293 教训:第二份实现允许存在,前提是被逐档锁死相等。"""
        for t in TIERS:
            d = S.tier_dims(t)
            self.assertEqual(S.derive_chain(d), E.derive_chain(d), t)
            self.assertEqual(S.derive_flow_graph(d), E.derive_flow_graph(d), t)

    def test_flow_key_agrees_across_all_three_impls(self):
        """🔴 v8.352 补锁:本条初版只比了 derive_*,**没比 flow_key** ——
        于是 v8.343 加 floor 档时漏改 specs._flow_key(state.py/engine 给 "Floor"、
        它给 "Feature"),整整九版没人发现,直到 v8.352 写新门用到它才撞出来。
        「第二份实现允许存在的前提是被锁死相等」要锁**全部**归一函数,不是其中一个。
        """
        for t in TIERS:
            st = {"flow_type": "Feature", "preset": t}
            keys = {S.internal_flow_key("Feature", t), E._internal_flow_key(st),
                    SP._flow_key(st)}
            self.assertEqual(len(keys), 1, f"{t}: 三实现解析不一致 → {keys}")


# ─── 2 · 一致性:拆维度必然产生不连贯组合 ───────────────────────────────

class TestCoherence(unittest.TestCase):

    def test_all_tier_defaults_are_coherent(self):
        for t in TIERS:
            self.assertEqual(S.validate_dims(S.tier_dims(t)), [], t)

    def test_na_review_point_rejected(self):
        """N/A ≠ 0 路:配一个不在链上的评审点 = AI 以为那个 stage 会跑。"""
        d = S.merge_dims(S.tier_dims("lite"), {"review": {"blueprint": ["architect"]}})
        self.assertTrue(any("blueprint" in v for v in S.validate_dims(d)))
        d2 = S.merge_dims(S.tier_dims("tiny"), {"review": {"goal": ["pl"]}})
        self.assertTrue(S.validate_dims(d2))

    def test_evidence_gate_off_forces_self_verify(self):
        d = S.merge_dims(S.tier_dims("micro"), {"verify_depth": "test"})
        self.assertTrue(any("verify_depth" in v for v in S.validate_dims(d)))

    def test_zero_route_is_legal_and_distinct_from_na(self):
        """lite 的 goal 是 0 路(在链上不派)· 合法 —— 与 N/A 必须区分得开。"""
        self.assertEqual(S.validate_dims(S.tier_dims("lite")), [])
        self.assertIn("goal", S.derive_chain(S.tier_dims("lite")))
        self.assertEqual(S.TIER_DIMS["lite"]["review"]["goal"], [])


# ─── 3 · 计划落库 · custom 装配 ────────────────────────────────────────

class _CliCase(unittest.TestCase):
    """真跑 CLI —— v8.280 教训:只断言常量、从没真跑 gate 的测试等于没测。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=self.tmp, check=True)
        subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "i"],
                       cwd=self.tmp, check=True,
                       env={"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(self.tmp),
                            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})
        self.env = {"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(self.tmp),
                    "TEAMWORK_BYPASS_PREPARE_CHECK": "1"}

    def init(self, tier, dims=None, fid="T-F001-x"):
        d = self.tmp / "docs" / "features" / fid
        d.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, STATE_PY, "init-feature", "--feature", str(d),
               "--feature-id", fid, "--flow-type", "Feature", "--preset", tier,
               "--merge-target", "main", "--branch", "b", "--worktree-mode", "off"]
        if dims:
            cmd += ["--dims", json.dumps(dims)]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=self.tmp,
                           env=self.env, timeout=60)
        return d, r

    def load(self, d):
        return json.loads((d / "state.json").read_text(encoding="utf-8"))

    def revise(self, d, dim, to, evidence="装配时不知道的事实"):
        r = subprocess.run(
            [sys.executable, STATE_PY, "revise-plan", "--feature", str(d),
             "--dim", dim, "--to", to, "--evidence", evidence],
            capture_output=True, text=True, cwd=self.tmp, env=self.env, timeout=60)
        try:
            return json.loads(r.stdout or r.stderr)
        except json.JSONDecodeError:
            return {"verdict": "PARSE_FAIL", "raw": (r.stdout + r.stderr)[:400]}


class TestInitWritesPlan(_CliCase):

    def test_every_tier_inits_and_starts_at_chain_head(self):
        for t in TIERS:
            d, r = self.init(t, fid=f"T-F00{TIERS.index(t)}-x")
            self.assertEqual(r.returncode, 0, f"{t}: {r.stdout}{r.stderr}")
            st = self.load(d)
            dims = st["assembly_plan"]["dims"]
            self.assertEqual(st["current_stage"], S.derive_chain(dims)[0], t)

    def test_zero_route_points_get_explicit_empty_key(self):
        """v8.337「零也显式」的机器版:不写键 = 修订想加回来没有落点。"""
        d, _ = self.init("lite")
        roles = self.load(d)["stage_review_roles"]
        self.assertIn("goal", roles)
        self.assertEqual(roles["goal"], [])

    def test_non_tier_rosters_survive(self):
        """计划只管随档变的四个评审点 —— test/browser_e2e 的默认 roster 不许被抹掉。"""
        d, _ = self.init("full")
        self.assertEqual(self.load(d)["stage_review_roles"].get("test"), ["qa"])

    def test_custom_dims_merge_onto_tier(self):
        d, r = self.init("medium", {"verify_depth": "test_e2e",
                                    "review": {"blueprint": ["architect", "dba"]}})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        st = self.load(d)
        self.assertIn("browser_e2e", S.derive_chain(st["assembly_plan"]["dims"]))
        self.assertEqual(st["stage_review_roles"]["blueprint"], ["architect", "dba"])
        self.assertEqual(st["stage_review_roles"]["goal"], ["fast"])   # 没拧的沿用档默认

    def test_incoherent_custom_dims_rejected_at_init(self):
        _, r = self.init("lite", {"review": {"blueprint": ["architect"]}})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("不连贯", r.stdout + r.stderr)


# ─── 4 · 显式修订点 ───────────────────────────────────────────────────

class TestRevisionPoint(_CliCase):

    def test_both_directions_cost_one_line_of_evidence(self):
        """⚖️ 加与减同价 —— 只让「减」举证 = v8.341 的保守偏置原样搬回来。"""
        d, _ = self.init("tiny")
        up = self.revise(d, "verify_depth", "test", "改动横跨 3 个服务 · diff 看不出集成行为")
        self.assertEqual(up["verdict"], "OK")
        self.assertEqual(up["direction"], "加")
        down = self.revise(d, "review.pm_acceptance", "", "用户明确说盯 MR diff 即可")
        self.assertEqual(down["verdict"], "OK")
        self.assertEqual(down["direction"], "减")
        for r in (up, down):
            self.assertTrue(r["evidence"])

    def test_evidence_is_required(self):
        d, _ = self.init("tiny")
        r = subprocess.run(
            [sys.executable, STATE_PY, "revise-plan", "--feature", str(d),
             "--dim", "verify_depth", "--to", "test"],
            capture_output=True, text=True, cwd=self.tmp, env=self.env, timeout=60)
        self.assertNotEqual(r.returncode, 0)

    def test_revision_updates_chain_and_roster_together(self):
        """计划改了 roster 不跟 = 又一处双载体 —— 锁住它们同步。"""
        d, _ = self.init("tiny")
        self.revise(d, "review.review", "architect,external", "改动落在鉴权路径上")
        st = self.load(d)
        self.assertEqual(st["stage_review_roles"]["review"], ["architect", "external"])
        self.assertEqual(st["assembly_plan"]["dims"]["review"]["review"],
                         ["architect", "external"])

    def test_revisions_are_logged_with_direction(self):
        """校准闭环的数据源:方向 + 证据逐条留痕。"""
        d, _ = self.init("lite")
        self.revise(d, "verify_depth", "test_e2e", "有前端改动 · 装配时不知道")
        revs = self.load(d)["assembly_plan"]["revisions"]
        self.assertEqual(len(revs), 1)
        for k in ("at_stage", "dim", "from", "to", "evidence", "at"):
            self.assertIn(k, revs[0], k)

    def test_noop_when_value_unchanged(self):
        d, _ = self.init("lite")
        self.assertEqual(self.revise(d, "verify_depth", "test", "同值")["verdict"], "NOOP")

    def test_orphaned_review_point_pruned_and_reported(self):
        """降维带出的孤儿评审点:剪了要说 —— 静默修正 = 用户看不见形状变了。"""
        d, _ = self.init("medium")
        r = self.revise(d, "spec_depth", "prd", "调研后确认只有一种写法 · TECH 是照抄实现")
        self.assertEqual(r["verdict"], "OK")
        self.assertEqual(r["pruned_review_points"], ["blueprint"])
        self.assertNotIn("blueprint", r["chain_after"])


class TestPlanRevisableNotHistory(_CliCase):
    """🔴 计划可改 · 历史不可改。"""

    def _walk(self, d, stages):
        """用合规通道(raw-write)制造「已走过」的前置态 —— 直改 state.json 会被 checksum 守卫拦。"""
        subprocess.run(
            [sys.executable, STATE_PY, "raw-write", "--feature", str(d),
             "--set", f"completed_stages={json.dumps(stages)}",
             "--reason", "test:制造已走过的前置态"],
            capture_output=True, text=True, cwd=self.tmp, env=self.env, timeout=60)

    def test_walked_stage_cannot_be_dropped(self):
        d, _ = self.init("medium")
        self._walk(d, ["goal", "blueprint", "dev"])
        r = self.revise(d, "spec_depth", "prd", "想事后免掉 TECH")
        self.assertEqual(r["verdict"], "FAIL")
        # 🔴 拒的**理由**必须是「已走过」,不是「组合不连贯」——
        # 守卫写了却走不到,是本框架反复复发的「规则立了没接线」
        self.assertIn("已走过", r["error"])

    def test_evidence_gate_cannot_be_loosened_after_dev(self):
        d, _ = self.init("medium")
        self._walk(d, ["goal", "blueprint", "dev"])
        r = self.revise(d, "evidence_gate", "false", "想事后免掉测试证据")
        self.assertEqual(r["verdict"], "FAIL")
        self.assertIn("不许回溯", r["error"])

    def test_unwalked_part_still_revisable(self):
        d, _ = self.init("medium")
        self._walk(d, ["goal", "blueprint", "dev"])
        self.assertEqual(self.revise(d, "review.pm_acceptance", "",
                                     "用户说盯 MR diff 即可")["verdict"], "OK")


# ─── 5 · 门与转移读计划 ───────────────────────────────────────────────

class TestGatesReadPlan(unittest.TestCase):

    def test_gates_open_exactly_where_chain_omits_the_stage(self):
        cases = [("floor", SP._check_prd_or_bug_report, True),
                 ("floor", SP._check_test_done_or_micro, True),
                 ("floor", SP._check_pm_approved_ship, True),      # 验收回 MR diff
                 ("tiny", SP._check_test_done_or_micro, True),
                 ("tiny", SP._check_pm_approved_ship, False),      # tiny 有 pm 口 · 照卡
                 ("lite", SP._check_prd_or_bug_report, False),     # lite 要 PRD
                 ("lite", SP._check_test_done_or_micro, False),    # lite 要 test
                 ("full", SP._check_blueprint_or_alt_done, False)]
        for tier, fn, expect in cases:
            self.assertEqual(fn(_st(tier), _Args()), expect, f"{tier}/{fn.__name__}")

    def test_floor_dev_goes_straight_to_ship(self):
        self.assertEqual(SP._dev_transition(_st("floor")), "ship")
        self.assertEqual(SP._dev_transition(_st("tiny")), "review")

    def test_transitions_follow_the_chain(self):
        st = _st("lite")
        st["stage_contracts"]["review"] = {"output_satisfied": True,
                                           "evidence": {"verdict": "APPROVE"}}
        self.assertEqual(SP._review_transition(st), "test")
        self.assertEqual(SP._goal_transition(_st("lite")), "dev")
        self.assertEqual(SP._goal_transition(_st("medium")), "blueprint")

    def test_needs_flags_write_through_to_plan(self):
        """双载体防线:--needs-* 必须落进 dims,否则链推导读不到、开关等于没接。"""
        from argparse import Namespace
        st = _st("full")
        SP.persist_args_to_evidence("goal", st, Namespace(
            needs_ui="true", needs_blueprint="false", needs_browser_e2e="true"))
        dims = st["assembly_plan"]["dims"]
        self.assertIs(dims["ui"], True)
        self.assertEqual(dims["spec_depth"], "prd")
        self.assertEqual(dims["verify_depth"], "test_e2e")
        self.assertNotIn("blueprint", dims["review"])          # 孤儿评审点随之剪掉
        self.assertEqual(SP._goal_transition(st), "ui_design")

    def test_legacy_state_without_plan_still_works(self):
        """存量 state 无 assembly_plan → 回退静态图 · 不许因本版卡死。"""
        legacy = {"flow_type": "Feature", "preset": "full", "stage_contracts": {},
                  "execution_hints": {"ui_design_needed": False}}
        self.assertEqual(SP._goal_transition(legacy), "blueprint")
        self.assertIs(E._resolve_flow_graph(legacy, S.FLOW_BY_TYPE), S.FEATURE_FLOW)


class TestPlanCheckpoint(unittest.TestCase):

    def test_checkpoint_asks_a_decidable_question(self):
        st = _st("full")
        st["completed_stages"] = ["goal"]
        ck = E.build_plan_checkpoint(st, "blueprint", "/f")
        self.assertIn("装配时不知道的事实", ck["question"])
        self.assertNotIn("要不要改", ck["question"])       # 形容词式问句 · 永远答得出「不改」
        self.assertIn("revise-plan", ck["revise_cmd"])
        self.assertIn("不停等", ck["note"])
        self.assertNotIn("blueprint", ck["remaining"])     # 刚完成的不算剩余

    def test_no_checkpoint_without_plan(self):
        self.assertIsNone(E.build_plan_checkpoint(
            {"flow_type": "Feature"}, "dev", "/f"))


# ─── 6 · spec 载体 ────────────────────────────────────────────────────

class TestSpecCarriers(unittest.TestCase):

    def test_goal_stage_carries_matrix_and_revision_rule(self):
        t = (SKILL_ROOT / "stages" / "goal-stage.md").read_text(encoding="utf-8")
        for d in ("D1 规格深度", "D2 证据门", "D3 验证深度", "D4 评审力度"):
            self.assertIn(d, t, d)
        self.assertIn("显式修订点", t)
        self.assertIn("加与减同价", t)
        self.assertIn("计划可改 · 历史不可改", t)
        self.assertIn("档只是起手点", t)

    def test_goal_brief_carries_dims_and_checkpoint(self):
        b = SP.GOAL_SPEC.brief_template_fn({})
        for tier in TIERS:
            self.assertIn(tier, b, tier)
        self.assertIn("拧四维不是挑档名", b)
        self.assertIn("plan_checkpoint", b)
        self.assertIn("加与减同价", b)

    def test_flows_declares_derivation(self):
        t = (SKILL_ROOT / "FLOWS.md").read_text(encoding="utf-8")
        self.assertIn("链由维度推导", t)
        self.assertIn("起手点不是终点", t)
        self.assertIn("降档不降三样", t)


if __name__ == "__main__":
    unittest.main()
