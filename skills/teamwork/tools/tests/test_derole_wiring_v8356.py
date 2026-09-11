"""v8.356 · v8.355 的接线补全(四路 subagent 审计发现)。

用户让派 subagent 整体 review 「是否有描述冲突、冗余」,三路审计共报 33 条,
其中两条 P0、一条 P1 是**真 bug**,全部源于同一个方法错误:v8.355 按「我想到的载体」
逐个改,而不是**先 grep 出全部消费方再改** —— 框架自己就有这条规则(「改契约必 grep
消费方 · 不凭记忆」),没对自己用。漏掉的整个文件:claude-agents/、FLOWS.md、
ROLES.md、docs/prepare.md、docs/conventions.md。

本文件锁住四个具体失效方式,防复发。
"""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import _v8_stage_specs as S  # noqa: E402
from state import TIER_DIMS  # noqa: E402

STATE_PY = ROOT / "tools" / "state.py"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class _NS:
    def __init__(self, feature):
        self.feature = feature


class TestZeroLaneIsNotADeadlock(unittest.TestCase):
    """P0-1:lite 档 goal 有意 0 路,门却硬要 PRD-REVIEW + 非空 verdicts。

    实测复现过的死锁:AI 只交 PRD.md → FAIL;如实写 0 路记录(reviewers/verdicts 空)
    → 仍 FAIL;**只有编造一条根本不存在的裁决才能过** —— 门在逼 AI 造假。

    根因:v8.355 加了「按路数跳过评审产物」,却没给 PRD-REVIEW.md 挂
    `review_artifact=True`,那条改动因此对 goal 永不生效(全仓唯一挂了标记的是
    TECH-REVIEW,而它所在的 blueprint 只在 medium/full 上链、roster 恒非空)——
    CHANGELOG 里「lite/tiny 同受益」当时是一句空话。
    """

    def test_prd_review_is_marked_as_review_artifact(self):
        spec = next(a for a in S.GOAL_SPEC.artifacts if a.path == "PRD-REVIEW.md")
        self.assertTrue(spec.review_artifact, "PRD-REVIEW.md 没挂 review_artifact = 按路数跳过对它空转")

    def test_lite_goal_zero_lane_passes_every_review_gate(self):
        lite = {"current_stage": "goal", "flow_type": "Feature",
                "stage_review_roles": {"goal": [], "review": ["external"]}}
        with tempfile.TemporaryDirectory() as d:
            Path(d, "PRD.md").write_text("# PRD\n", encoding="utf-8")
            for name, fn in (
                ("prd_review_after_prd", S._evidence_review_after_primary("PRD.md", "PRD-REVIEW.md")),
                ("prd_verdicts_all_pass", S._evidence_prd_verdicts_all_pass),
                ("pl_challenge_present", S._evidence_pl_challenge_present),
                ("external_coverage_present", S._evidence_external_coverage_present),
                ("outside_checklist_insight", S._evidence_outside_checklist_insight("PRD-REVIEW.md", "goal")),
            ):
                ok, msg = fn(lite, _NS(d))
                self.assertTrue(ok, f"{name} 在有意 0 路时仍拦:{msg}")

    def test_legacy_state_is_not_loosened(self):
        """🔴 两种「缺失」含义相反(v8.305 判例)—— roster 整个未初始化 ≠ 有意 0 路。

        v8.355 修这个死锁时**又栽了一次同样的坑**(首版把两者混为一谈,被既有测试抓出),
        所以谓词已抽成单函数,不再让每个门自己写一遍。
        """
        legacy = {"current_stage": "goal", "flow_type": "Feature"}   # 无 stage_review_roles
        with tempfile.TemporaryDirectory() as d:
            Path(d, "PRD.md").write_text("# PRD\n", encoding="utf-8")
            for name, fn in (
                ("prd_review_after_prd", S._evidence_review_after_primary("PRD.md", "PRD-REVIEW.md")),
                ("prd_verdicts_all_pass", S._evidence_prd_verdicts_all_pass),
            ):
                ok, _ = fn(legacy, _NS(d))
                self.assertFalse(ok, f"{name} 把未初始化 roster 误当 0 路放行 = 对存量放松")

    def test_zero_lane_predicate_has_one_implementation(self):
        src = _read("tools/_v8_stage_specs.py")
        self.assertIn("def _stage_lanes_deliberately_zero", src)
        # 谓词不许再被就地重写(第三次写错的入口)
        inline = re.findall(r'\(state\.get\("stage_review_roles"\)\s*or\s*\{\}\)\.get\([^)]*\)\s*or\s*\[\]\)', src)
        self.assertLessEqual(len(inline), 1, f"谓词又被就地重写 {len(inline)} 处 · 应走 helper")


class TestBriefAgreesWithGates(unittest.TestCase):
    """P0-2:brief 是运行时权威,它说「去 pl 就免对抗段」而门已改按路数判。

    默认档就会踩:medium 的 goal roster=["external"],AI 照 brief 写完整单路冷审、
    因不含 pl 而没写 PL-CHALLENGE → goal-complete FAIL,且是唯一拦截项。
    """

    def test_goal_brief_no_longer_promises_role_based_exemption(self):
        b = S._goal_brief({"stage_review_roles": {"goal": ["external"]}})
        for stale in ("去 pl → PL 质疑免", "roster 含 pl", "roster 含 external"):
            self.assertNotIn(stale, b, f"goal brief 仍承诺按角色豁免:{stale}")
        self.assertIn("不减清单", b, "没说清「少配一条 lane 不减清单」")

    def test_all_three_briefs_list_the_insight_deliverable(self):
        """门要 💡,brief 的「结果(完成判定)」却没列 —— 读取端接线、写入端没接。"""
        for name, fn, st in (
            ("goal", S._goal_brief, {"stage_review_roles": {"goal": ["pl", "external"]}}),
            ("blueprint", S._blueprint_brief, {"stage_review_roles": {"blueprint": ["architect", "external"]}}),
            ("review", S._review_brief, {"stage_review_roles": {"review": ["architect", "external"]}}),
        ):
            b = fn(st)
            self.assertIn("清单外洞察", b, f"{name} brief 交付清单漏 💡")
            self.assertIn("不决定查什么", b, f"{name} brief 没声明 lane 语义")

    def test_briefs_dropped_the_role_axis(self):
        b = S._goal_brief({})
        self.assertNotIn("路数×角色×模型", b)
        self.assertNotIn("×谁×", b)


class TestExternalPromptCarriesTheChecklist(unittest.TestCase):
    """P1-3:external lane 拿到的 prompt 里完全没有统一清单(写入端没接的最严重一例)。

    tiny/lite/medium/Bug 四条默认路径上,review 的**唯一**冷审路就是 external;
    文档承诺「N 路都过全清单三段」,而这一路的 prompt 从头到尾没提三段 ——
    coverage 只能由主对话代笔,而主对话代笔正是该 stage 明令禁止的热审。
    """

    def test_prompt_template_carries_all_three_sections(self):
        t = _read("claude-agents/reviewer.md")
        for k in ("对抗段", "证否句式", "清单外洞察", "rival 设计强制", "限制是业务真要求"):
            self.assertIn(k, t, f"reviewer.md 缺 {k}")

    def test_prompt_output_schema_has_the_new_fields(self):
        t = _read("claude-agents/reviewer.md")
        for f in ("coverage:", "challenge:", "outside_checklist_insight:"):
            self.assertIn(f, t, f"输出 schema 缺 {f} · 门查不到就等于没交")

    def test_rendered_prompt_actually_contains_them(self):
        """🔴 只改模板不够 —— 要验**渲染出来的那份**(模板有主体提取逻辑)。"""
        with tempfile.TemporaryDirectory() as d:
            feat = Path(d) / "feat"
            feat.mkdir()
            (feat / "state.json").write_text(json.dumps({
                "feature_id": "F1", "flow_type": "Feature", "current_stage": "review",
                "completed_stages": [], "stage_contracts": {},
                "created_at": "2026-09-10T00:00:00Z",
                "stage_review_roles": {"review": ["architect", "external"]},
            }), encoding="utf-8")
            (feat / "TECH.md").write_text("# TECH\n", encoding="utf-8")
            r = subprocess.run(
                [sys.executable, str(STATE_PY), "external-review",
                 "--feature", str(feat), "--stage", "review"],
                capture_output=True, text=True, timeout=60)
            out = json.loads(r.stdout or r.stderr)
            doc = next((out[k] for k in ("prompt_doc", "prompt_doc_path", "prompt_path") if k in out), None)
            self.assertIsNotNone(doc, f"没拿到 prompt doc:{list(out)[:8]}")
            txt = Path(doc).read_text(encoding="utf-8")
            for k in ("清单外洞察", "outside_checklist_insight", "证否", "coverage"):
                self.assertIn(k, txt, f"渲染出的 external prompt 缺 {k}")


class TestCoverageIsOwedByEveryLane(unittest.TestCase):
    """A6:review 的 coverage 门是角色白名单(architect/qa),lane 标识仍在决定「要不要交」。

    roster=["pl"] 或 ["fast"] 时,它与 cross_review_coverage 双双放行 = 零 coverage 强制。
    """

    def _run(self, roster):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "REVIEW.md").write_text("reviewers: []\nverdict: APPROVE\n", encoding="utf-8")
            return S._evidence_review_role_coverage(
                {"stage_review_roles": {"review": roster}}, _NS(d))

    def test_non_external_lanes_all_owe_coverage(self):
        for roster in (["pl"], ["fast"], ["r1", "r2"], ["architect", "external"]):
            ok, _ = self._run(roster)
            self.assertFalse(ok, f"roster={roster} 竟不用申报 coverage")

    def test_external_only_defers_to_its_own_artifact(self):
        ok, msg = self._run(["external"])
        self.assertTrue(ok, "external lane 的 coverage 在 external-cross-review/,此门应放行")
        self.assertIn("external", msg)

    def test_no_role_whitelist_left(self):
        self.assertNotIn("_REVIEW_MAIN_ROLES", _read("tools/_v8_stage_specs.py"))


class TestInsightGateAcceptsLaneFirstLayout(unittest.TestCase):
    """P2-5:窗口遇任何 markdown 标题即断,而「段名 + 按 lane 分小节」正好用 ###。

    该布局与 REVIEW.md frontmatter 挂 per-lane 子键的结构同构,AI 会平移过去。
    """

    def _gate(self, body):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "REVIEW.md").write_text("reviewers: [architect]\n" + body, encoding="utf-8")
            return S._evidence_outside_checklist_insight("REVIEW.md", "review")(
                {"stage_review_roles": {"review": ["architect"]}}, _NS(d))

    def test_lane_first_layout_passes(self):
        ok, msg = self._gate("## 💡 清单外洞察\n\n### architect lane\n- 结果集搬运量没在清单里。\n")
        self.assertTrue(ok, msg)

    def test_other_valid_layouts_still_pass(self):
        for body in ("## 💡 清单外洞察\n\n- 并发写入路径没覆盖。\n",
                     'outside_checklist_insight:\n  architect: "搬运量没在清单里"\n',
                     'outside_checklist_insight: "无 · 依赖面与 AC 都在清单内"\n'):
            ok, msg = self._gate(body)
            self.assertTrue(ok, f"{body[:28]!r} → {msg}")

    def test_placeholder_and_bare_none_still_rejected(self):
        """🔴 放宽窗口不等于放松门 —— 占位符原样和单字「无」必须仍被拒。"""
        for body in ('outside_checklist_insight: "{清单外洞察:清单没问、但我认为该关注的 —— ≥1 条}"\n',
                     'outside_checklist_insight: "无"\n'):
            ok, _ = self._gate(body)
            self.assertFalse(ok, f"{body[:34]!r} 竟然过门")


class TestOuterDocsWereNotForgottenAgain(unittest.TestCase):
    """v8.355 漏掉的整批文件 —— 锁住它们,下次改评审语义时会被一起抓出。"""

    OUTER = ("ROLES.md", "FLOWS.md", "docs/prepare.md", "docs/conventions.md")

    def test_no_retired_fast_label_in_outer_docs(self):
        for rel in self.OUTER:
            t = _read(rel)
            self.assertNotIn("[fast]", t, f"{rel} 仍写退役的 fast roster")
            self.assertNotIn("fast_mode", t, f"{rel} 仍把 fast_mode 当可配项")

    def test_outer_docs_dropped_the_role_axis(self):
        self.assertNotIn("路数 × 角色 × 模型", _read("FLOWS.md"))
        self.assertNotIn("逐 stage 逐角色", _read("docs/prepare.md"))

    def test_flows_medium_matches_code(self):
        """FLOWS 的档位描述必须与 TIER_DIMS 一致(它曾是唯一还写 architect 的地方)。"""
        f = _read("FLOWS.md")
        self.assertNotIn("review〔architect 单路〕", f)
        self.assertEqual(TIER_DIMS["tiny"]["review"]["review"], ["external"])
        self.assertEqual(TIER_DIMS["medium"]["review"]["goal"], ["external"])


if __name__ == "__main__":
    unittest.main()
