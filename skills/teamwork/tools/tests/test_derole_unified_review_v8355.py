"""v8.355 · 去角色:冷审清单统一 · fast 退役 · 查询性能与数据量(用户拍板)。

用户:「我想进一步弱化角色,甚至去掉角色,在每一个阶段把审核需要的注意事项合并到一起,
流程只是保障冷审的力度,几个冷审,冷审的模型是什么,冷审结论要有模版文档,结束要填好,
除了必要的检查项之外,还需要写 AI 认为需要关注的」+「fast 模式彻底删除吧」。

查证结果:**框架已经自己走了一半** ——
  · roster 表里 qa/architect 早已「默认并入外审覆盖方向」(方向制吃掉角色制);
  · 年检实证 external〔方向清单〕产出 2.1× architect〔角色关注点〕· 采纳率 82.3%,
    v8.343 据此定了「只留一路时留 external」;
  · fast_mode 的「单 agent 兼两帽」本身就是一份能跑的合并清单实现。

所以本版做的是**把合并从降档手段提升为默认结构**,并解耦出路数:
  D4 从「路数 × 角色 × 模型」降成「路数 × 模型」。

🔴 关键设计(改动面最小 · 零迁移):**roster 标签不动**,让 `pl`/`external`/`architect`
从「角色」降为 **lane 标识** —— 只决定**产物落点**与是否跨会话隔离,**不决定查什么**。
于是 TIER_DIMS、默认值、reviewers_match、cross_review_coverage 全部无需改动,
存量 feature 的 state 也不用迁移。

清单三段:⚔️ 对抗(证否句式 · 不许打勾)· 🔍 核对(可「查过无发现」)· 💡 清单外洞察。
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import _v8_stage_specs as S  # noqa: E402
import _v8_engine as E  # noqa: E402
from state import TIER_DIMS  # noqa: E402

STAGES = {"goal": "stages/goal-stage.md",
          "blueprint": "stages/blueprint-stage.md",
          "review": "stages/review-stage.md"}


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class _NS:
    def __init__(self, feature):
        self.feature = feature


class TestFastModeIsGone(unittest.TestCase):
    """fast 与 D4 是同一个旋钮的两套表达 —— 双载体必漂,删旋钮留维度。"""

    def test_no_behavioral_fast_mode_left_in_code(self):
        """允许注释/退役检测提及,但不许再有 `state.get("fast_mode")` 这类分支。"""
        bad = []
        for f in (ROOT / "tools").glob("*.py"):
            for i, ln in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if re.search(r'(state|st)\.get\(\s*["\']fast_mode["\']', ln):
                    bad.append(f"{f.name}:{i}")
        self.assertEqual(bad, [], f"仍有 fast_mode 行为分支:{bad}")

    def test_no_fast_in_user_facing_docs(self):
        bad = []
        for rel in ("SKILL.md", "templates/teamwork_localconfig.json",
                    *STAGES.values()):
            if "fast_mode" in _read(rel) or "fast 模式" in _read(rel):
                bad.append(rel)
        self.assertEqual(bad, [], f"文档仍在讲 fast:{bad}")

    def test_round_cap_has_a_single_source(self):
        """封顶只剩 localconfig 一个来源(原来 fast 是第二个收紧点)。"""
        self.assertFalse(hasattr(E, "FAST_MAX_REVIEW_ROUNDS"))
        self.assertEqual(E.DEFAULT_MAX_REVIEW_ROUNDS, 3)

    def test_medium_goal_lane_is_a_real_lane(self):
        """medium 的 goal 从伪角色 `fast` 换成真 lane —— 清单统一后单路就是单路。"""
        self.assertEqual(TIER_DIMS["medium"]["review"]["goal"], ["external"])

    def test_legacy_fast_label_still_accepted(self):
        """🔴 存量 feature 的 roster 里还写着 `fast` —— 摘掉枚举会让它们连
        `change-review-roles` 传回当前值都被拒(v8.305 踩过一次)。"""
        self.assertIn("fast", E.REVIEW_ROLE_ENUM)

    def test_retirement_is_announced_not_silent(self):
        """静默变严和静默回退是同一种双输 —— 存量配置必须被告知迁移路径。"""
        src = _read("tools/state.py")
        self.assertIn("fast-mode-retired", src)
        self.assertIn("_read_retired_fast_flag", src)


class TestChecklistIsUnified(unittest.TestCase):
    """每个 stage 一份清单 · N 路都过 · lane 标识不决定查什么。"""

    def test_every_stage_declares_the_three_sections(self):
        for stage, rel in STAGES.items():
            txt = _read(rel)
            for seg in ("⚔️", "🔍", "💡 **清单外洞察**" if stage == "goal" else "💡"):
                self.assertIn(seg, txt, f"{rel} 缺清单段 {seg}")
            self.assertIn("清单外洞察", txt, f"{rel} 缺 💡 清单外洞察")

    def test_lane_label_does_not_decide_what_to_check(self):
        """这是去角色的核心命题 —— 三个 stage doc 都要把它说出来。"""
        for rel in STAGES.values():
            self.assertIn("只决定产物落点", _read(rel), f"{rel} 没声明 lane 语义")

    def test_challenge_section_forbids_ticking(self):
        """⚔️ 对抗项混进中性核对就会退化成打勾 —— 必须写成证否句式。"""
        for rel in STAGES.values():
            txt = _read(rel)
            self.assertIn("证否句式", txt, f"{rel} 对抗段没要求证否形式")
            self.assertIn("不许写 ✅", txt, f"{rel} 没禁打勾")

    def test_skill_carries_the_bottom_line(self):
        sk = _read("SKILL.md")
        self.assertIn("冷审清单统一", sk)
        self.assertIn("lane 标识", sk)
        self.assertIn("路数 × 模型", sk)


class TestGatesFollowLaneCountNotRole(unittest.TestCase):
    """门的触发条件从「roster 含某角色」改成「有没有冷审路」。"""

    def test_zero_lane_passes_both_goal_gates(self):
        st = {"stage_review_roles": {"goal": []}}
        for fn in (S._evidence_pl_challenge_present, S._evidence_external_coverage_present):
            ok, _ = fn(st, _NS("/nonexistent"))
            self.assertTrue(ok, f"{fn.__name__} 在 0 路时该放行")

    def test_any_lane_owes_both_sections(self):
        """🔴 旧行为:roster 不含 pl 就免对抗段 / 不含 external 就免 coverage = 两条缝。"""
        for roster in (["external"], ["pl"], ["architect", "qa"]):
            st = {"stage_review_roles": {"goal": roster}}
            for fn in (S._evidence_pl_challenge_present, S._evidence_external_coverage_present):
                ok, _ = fn(st, _NS("/nonexistent"))
                self.assertFalse(ok, f"roster={roster} 时 {fn.__name__} 不该放行")

    def test_artifact_skip_now_keys_on_lane_count(self):
        src = _read("tools/_v8_engine.py")
        self.assertIn("if art_spec.review_artifact and not _stage_lanes", src,
                      "评审产物跳过条件应按路数,不按退役的 fast_mode")


class TestOutsideChecklistInsightGate(unittest.TestCase):
    """💡 清单外洞察 = 框架的自发现通道(清单查已知风险 · 这格捞清单还不知道的)。"""

    def _gate(self, tmp, stage="goal", artifact="PRD-REVIEW.md", roster=("external",)):
        fn = S._evidence_outside_checklist_insight(artifact, stage)
        return fn({"stage_review_roles": {stage: list(roster)}}, _NS(str(tmp)))

    def test_zero_lane_skips(self):
        ok, _ = self._gate("/nonexistent", roster=())
        self.assertTrue(ok)

    def test_missing_section_fails_and_names_the_alternative(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "PRD-REVIEW.md").write_text("reviewers: [external]\n", encoding="utf-8")
            ok, msg = self._gate(d)
            self.assertFalse(ok)
            self.assertIn("清单外洞察", msg)
            self.assertIn("无", msg, "必须告诉对方「想不出可以写无+理由」,否则会硬凑")

    def test_explicit_none_with_reason_passes(self):
        """🔴 硬凑 = 新仪式 —— 显式「无 + 为什么」必须是合法答案。"""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "PRD-REVIEW.md").write_text(
                "reviewers: [external]\noutside_checklist_insight: \"无 · AC 与依赖面都在清单内\"\n",
                encoding="utf-8")
            ok, msg = self._gate(d)
            self.assertTrue(ok, msg)

    def test_template_placeholder_is_not_enough(self):
        """v8.350 教训:占位符原样抄必须过不了门,否则门形同虚设。"""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "PRD-REVIEW.md").write_text(
                'reviewers: [external]\n'
                'outside_checklist_insight: "{清单外洞察:清单没问、但我认为该关注的 —— ≥1 条}"\n',
                encoding="utf-8")
            ok, msg = self._gate(d)
            self.assertFalse(ok, "模板占位符竟然过门了")

    def test_registered_on_all_three_stages(self):
        for spec, stage in ((S.GOAL_SPEC, "goal"), (S.BLUEPRINT_SPEC, "blueprint"),
                            (S.REVIEW_SPEC, "review")):
            names = [c.name for c in spec.evidence_checks]
            self.assertIn("outside_checklist_insight", names, f"{stage} 未注册洞察门")


class TestD4DropsTheRoleAxis(unittest.TestCase):
    def test_assembly_card_asks_lanes_and_model_only(self):
        g = _read("stages/goal-stage.md")
        self.assertIn("是否需要 × 几路 × 什么模型 × 理由", g)
        self.assertIn("不选角色", g)

    def test_d4_row_names_lanes_times_model(self):
        self.assertRegex(_read("stages/goal-stage.md"), r"D4 评审力度.{0,40}路数 × 模型")

    def test_adding_review_means_adding_lanes(self):
        self.assertIn("**加路数**,不是加角色", _read("stages/goal-stage.md"))


class TestRetiredRolesPointAtTheChecklist(unittest.TestCase):
    """角色文件不能只是被掏空 —— 评审 mandate 迁走后要留指针,起草职责保留。"""

    def test_review_seats_are_retired_with_a_pointer(self):
        for rel in ("roles/architect.md", "roles/qa.md"):
            self.assertIn("不再是独立评审席位", _read(rel), f"{rel} 未声明席位退役")

    def test_external_is_described_as_a_lane_not_a_person(self):
        self.assertIn("lane 标识,不是角色", _read("roles/external-reviewer.md"))

    def test_drafting_duties_survive(self):
        """🔴 去的是评审角色,不是流程职能 —— TC/TECH 起草职责必须还在。"""
        self.assertIn("TC.md 起草", _read("roles/qa.md"))
        self.assertIn("TECH.md 起草", _read("roles/rd.md"))


class TestQueryPerformanceAndDataVolume(unittest.TestCase):
    """实证 case:BQ 查询 1s 完成,45MB 结果集搬回 0.2 核服务端聚合 → 线上 13–19s。

    🔴 旧 §查询性能 的四项判据(索引/全表扫/N+1/分页)在那个 case 里**全绿** ——
    不是漏填,是**问错了问题**:它只问「查询快不快」,不问「结果搬多少回来」。
    """

    def setUp(self):
        self.tech = _read("templates/tech.md")

    def test_section_renamed_to_cover_both_halves(self):
        self.assertIn("### 查询性能与数据量", self.tech)
        self.assertIn("查询 + 搬运两段都算", self.tech)

    def test_trigger_widened_beyond_sql(self):
        """BQ / ES / Mongo / HTTP 批拉是同一形状 —— 触发条件不能只写 SQL。"""
        self.assertIn("涉批量数据读取时必填", self.tech)

    def test_transfer_ratio_column_exists(self):
        """比值是**算出来**的,不是判断出来的(同「代价要算不要被告知」)。"""
        self.assertIn("调用方最终要多少 vs 搬回来多少", self.tech)
        self.assertRegex(self.tech, r"数量级.{0,30}架构问题")

    def test_fallbacks_are_not_a_speed_argument(self):
        self.assertIn("兜底 ≠ 够快", self.tech)
        for word in ("超时", "分页", "费用上限", "连接数上限"):
            self.assertIn(word, self.tech, f"没点名兜底手段 {word}")

    def test_fast_enough_must_name_the_spec(self):
        self.assertIn("「够快」必须带规格", self.tech)

    def test_selfcheck_and_blueprint_rule_agree(self):
        """读取端接线、写入端没接 = 白改 —— 自查清单与 blueprint 硬规则都要同步。"""
        self.assertIn("§查询性能与数据量", self.tech)
        bp = _read("stages/blueprint-stage.md")
        self.assertIn("查询 + 搬运两段都算", bp)
        self.assertNotIn("§查询性能涉 SQL", bp)


if __name__ == "__main__":
    unittest.main()
