#!/usr/bin/env python3
"""流程减负回归套件(review 收敛协议的配套减负项)。

覆盖:
- 敏捷需求默认评审角色:review 去 external(opt-in 加回)· goal 冷审 2→1 + pl(保 PL challenge)
- Micro distill 简表:sanitize 只强制 knowledge 一键 · 其余 5 键自动填「无(Micro)」· 其他 flow 不变
- browser_e2e 去独立用户暂停:截图为 evidence · 供 pm_acceptance 决策参考
- pm_acceptance brief 列 browser_e2e 截图为决策参考材料

运行:python3 -m pytest skills/teamwork/tools/tests/test_flow_deburden.py -q
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
STATE_PY = TOOLS / "state.py"
sys.path.insert(0, str(TOOLS))

import _v8_engine as E  # noqa: E402
import _v8_stage_specs as S  # noqa: E402


# ─── 1 · 敏捷需求 review 角色减负 ───────────────────────────────────────


class TestAgileReviewRoles(unittest.TestCase):
    def test_agile_review_drops_external(self):
        self.assertEqual(E.DEFAULT_REVIEW_ROLES[("敏捷需求", "review")],
                         ["architect", "qa"])

    def test_agile_goal_one_cold_reviewer_plus_pl(self):
        """冷审 2→1 + pl(保 PL challenge 门禁 · _evidence_pl_challenge_present 消费 pl)。"""
        roles = E.DEFAULT_REVIEW_ROLES[("敏捷需求", "goal")]
        self.assertIn("pl", roles)
        cold = [r for r in roles if r not in ("pl",)]
        self.assertEqual(len(cold), 1, f"敏捷 goal 冷审角色应 1 个 · got {roles}")

    def test_feature_review_roles_unchanged(self):
        self.assertEqual(E.DEFAULT_REVIEW_ROLES[("Feature", "review")],
                         ["architect", "qa", "external"])
        self.assertEqual(E.DEFAULT_REVIEW_ROLES[("Feature", "goal")],
                         ["qa", "architect", "pl"])

    def test_build_default_roles_snapshot(self):
        roles = E.build_default_stage_review_roles("敏捷需求")
        self.assertNotIn("external", roles["review"])
        self.assertIn("pl", roles["goal"])

    def test_external_evidence_gate_skips_for_agile_snapshot(self):
        """新敏捷 feature(roles 无 external)→ external_review_artifact 自动 skip。"""
        state = {"current_stage": "review",
                 "stage_review_roles": {"review": ["architect", "qa"]}}
        ok, reason = S._evidence_external_review_artifact(
            state, NS(feature=str(Path(tempfile.mkdtemp()))))
        self.assertTrue(ok)
        self.assertIn("skipped", reason)

    def test_chain_preview_reflects_new_roles(self):
        preview = {p["stage"]: p for p in E.build_stage_chain_preview("敏捷需求")}
        self.assertEqual(preview["review"]["reviewers"], ["architect", "qa"])
        self.assertIn("opt-in", preview["review"]["reason"])
        self.assertIn("pl", preview["goal"]["reviewers"])

    def test_pl_challenge_gate_now_applies_to_agile_goal(self):
        """敏捷 goal 含 pl → PRD-REVIEW 无 PL-CHALLENGE 段被拦(门禁随角色生效)。"""
        feat = Path(tempfile.mkdtemp())
        (feat / "PRD-REVIEW.md").write_text(
            "---\nverdicts: {qa: APPROVE}\n---\n无质疑\n", encoding="utf-8")
        state = {"stage_review_roles": E.build_default_stage_review_roles("敏捷需求")}
        ok, err = S._evidence_pl_challenge_present(state, NS(feature=str(feat)))
        self.assertFalse(ok)
        self.assertIn("PL-CHALLENGE", err)
        shutil.rmtree(feat, ignore_errors=True)


# ─── 2 · Micro distill 简表 ────────────────────────────────────────────


def _write_state(feat: Path, fid: str, flow_type: str) -> None:
    feat.mkdir(parents=True, exist_ok=True)
    (feat / "state.json").write_text(json.dumps({
        "feature_id": fid, "flow_type": flow_type, "current_stage": "ship",
        "merge_target": "main", "ship": {}, "stage_contracts": {}, "concerns": [],
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def _sanitize(feat: Path, distill, expect: int) -> dict:
    argv = [sys.executable, str(STATE_PY), "ship-phase", "--action", "sanitize",
            "--feature", str(feat)]
    if distill is not None:
        argv += ["--distill", distill]
    r = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    assert r.returncode == expect, f"rc {r.returncode} ≠ {expect}\n{r.stdout}\n{r.stderr}"
    raw = r.stdout if r.stdout.strip().startswith("{") else (r.stdout or r.stderr)
    return json.loads(raw) if raw.strip().startswith("{") else {}


class TestMicroDistillLite(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-micro-distill-"))
        self.feat = self.tmp / "docs" / "features" / "PTR-M900-micro"
        _write_state(self.feat, "PTR-M900-micro", "Micro")
        self._prev = os.environ.get("TEAMWORK_BYPASS_CHECKSUM")
        os.environ["TEAMWORK_BYPASS_CHECKSUM"] = "1"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self._prev is None:
            os.environ.pop("TEAMWORK_BYPASS_CHECKSUM", None)
        else:
            os.environ["TEAMWORK_BYPASS_CHECKSUM"] = self._prev

    def test_micro_knowledge_only_passes_and_autofills(self):
        d = _sanitize(self.feat, json.dumps({"knowledge": "gotcha: preview 端口漂移"}), 0)
        self.assertEqual(d["verdict"], "PASS")
        for k in ("adr", "reg", "retro", "architecture", "db_schema"):
            self.assertEqual(d["distill"][k], "无(Micro)")
        self.assertEqual(d["distill"]["knowledge"], "gotcha: preview 端口漂移")
        st = json.loads((self.feat / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(st["ship"]["distill"]["architecture"], "无(Micro)")
        self.assertIn("distilled_at", st["ship"]["distill"])

    def test_micro_missing_knowledge_blocks(self):
        d = _sanitize(self.feat, json.dumps({"adr": "none"}), 1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("knowledge", str(d))

    def test_micro_no_distill_hint_mentions_lite_form(self):
        d = _sanitize(self.feat, None, 1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("Micro 简表", d["hint"])
        self.assertEqual(d["distill_keys"], ["knowledge"])

    def test_micro_explicit_other_keys_kept(self):
        """Micro 显式填了其他键 → 保留显式值 · 不被自动值覆盖。"""
        d = _sanitize(self.feat, json.dumps(
            {"knowledge": "none", "adr": "promoted ADR-9"}), 0)
        self.assertEqual(d["distill"]["adr"], "promoted ADR-9")
        self.assertEqual(d["distill"]["reg"], "无(Micro)")


class TestNonMicroDistillUnchanged(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-feat-distill-"))
        self.feat = self.tmp / "docs" / "features" / "PTR-F901-feat"
        _write_state(self.feat, "PTR-F901-feat", "Feature")
        self._prev = os.environ.get("TEAMWORK_BYPASS_CHECKSUM")
        os.environ["TEAMWORK_BYPASS_CHECKSUM"] = "1"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self._prev is None:
            os.environ.pop("TEAMWORK_BYPASS_CHECKSUM", None)
        else:
            os.environ["TEAMWORK_BYPASS_CHECKSUM"] = self._prev

    def test_feature_still_requires_all_six(self):
        d = _sanitize(self.feat, json.dumps({"knowledge": "none"}), 1)
        self.assertEqual(d["verdict"], "FAIL")
        for k in ("adr", "reg", "retro", "architecture", "db_schema"):
            self.assertIn(k, str(d))

    def test_feature_full_six_passes(self):
        d = _sanitize(self.feat, json.dumps({
            "knowledge": "none", "adr": "none", "reg": "none",
            "retro": "n/a", "architecture": "no-change", "db_schema": "no-change"}), 0)
        self.assertEqual(d["verdict"], "PASS")
        self.assertNotIn("无(Micro)", json.dumps(d["distill"], ensure_ascii=False))


# ─── 3 · browser_e2e 去独立用户暂停 ────────────────────────────────────


class TestBrowserE2ENoPause(unittest.TestCase):
    def test_pause_point_is_evidence_for_pm_acceptance(self):
        app = S.BROWSER_E2E_SPEC.authorized_pause_point
        self.assertIn("无用户暂停", app)
        self.assertIn("evidence", app)
        self.assertIn("pm_acceptance", app)
        self.assertNotIn("等确认", app)

    def test_screenshots_still_hard_artifact(self):
        """截图仍是硬产物要求(artifacts glob)· 只是不再单独停。"""
        globs = [a.glob for a in S.BROWSER_E2E_SPEC.artifacts if a.glob]
        self.assertIn("screenshots/*.png", globs)

    def test_brief_states_no_standalone_pause(self):
        b = S._browser_e2e_brief({})
        self.assertIn("无独立用户暂停", b)
        self.assertIn("pm_acceptance", b)

    def test_no_pause_headline_set_unchanged(self):
        """「无用户暂停」不含「无暂停」子串 → 不误入无暂停 stage 抬头集合(与 review 同口径)。"""
        self.assertNotIn("无暂停", S.BROWSER_E2E_SPEC.authorized_pause_point.split("·")[0])


class TestPmAcceptanceBriefListsScreenshots(unittest.TestCase):
    def test_brief_mentions_browser_e2e_screenshots(self):
        b = S._pm_acceptance_brief({})
        self.assertIn("browser_e2e 截图", b)
        self.assertIn("决策参考", b)

    def test_brief_keeps_r5_decision_discipline(self):
        b = S._pm_acceptance_brief({})
        self.assertIn("R5", b)
        self.assertIn("approved_and_ship", b)


if __name__ == "__main__":
    unittest.main(verbosity=2)
