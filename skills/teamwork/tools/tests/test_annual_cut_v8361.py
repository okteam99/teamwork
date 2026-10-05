"""年检提效(用户拍板「都做」):砍掉价值不高的环节。

数据源 aon-core PROCESS-LEDGER(2026-08-16 后 128 个 Feature)+ 174 份流程复盘:
① 门禁纯开销:mtime 顺序门 / 产物必须在同一个 commit
② 测试证据被文档提交作废 → 重跑
③ pm_acceptance 与 ship1 两次拍同一个发布决定(台账 rejected_with_feedback 0 次)
④ 流程复盘文档每单必写,自评几乎不产信号
⑤ medium 档单路评审仍单独维护 TC.md
"""
import argparse
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

import _v8_engine as E  # noqa: E402
import _v8_stage_specs as S  # noqa: E402


def _git(cwd, *a):
    subprocess.run(["git", "-C", str(cwd), *a], check=True, capture_output=True)


def _repo(tmp):
    root = Path(tmp)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@t")
    _git(root, "config", "user.name", "t")
    (root / "src").mkdir()
    (root / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    feat = root / "docs" / "features" / "F1"
    feat.mkdir(parents=True)
    (feat / "PRD.md").write_text("# PRD\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root, feat


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _head(root):
    return subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()


class TestGateOverheadCut(unittest.TestCase):

    def test_mtime_order_gate_removed(self):
        names = [c.name for c in S.GOAL_SPEC.evidence_checks]
        self.assertNotIn("prd_review_after_prd", names)
        self.assertFalse(hasattr(S, "_evidence_review_after_primary"))

    def test_artifact_committed_earlier_in_stage_counts(self):
        with tempfile.TemporaryDirectory() as t:
            root, feat = _repo(t)
            started = _now()
            time.sleep(1.1)
            (feat / "TEST-REPORT.md").write_text("# report\n", encoding="utf-8")
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "report")
            (root / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "code")
            self.assertTrue(E._artifact_committed_in_stage(feat, "TEST-REPORT.md", _head(root), started))

    def test_uncommitted_edit_still_fails(self):
        with tempfile.TemporaryDirectory() as t:
            root, feat = _repo(t)
            started = _now()
            time.sleep(1.1)
            (feat / "TEST-REPORT.md").write_text("# v1\n", encoding="utf-8")
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "report")
            (feat / "TEST-REPORT.md").write_text("# v2 改了没提交\n", encoding="utf-8")
            self.assertFalse(E._artifact_committed_in_stage(feat, "TEST-REPORT.md", _head(root), started))

    def test_artifact_from_before_stage_fails(self):
        """上一轮的旧报告不能冒充本 stage 产物。"""
        with tempfile.TemporaryDirectory() as t:
            root, feat = _repo(t)
            time.sleep(1.1)
            started = _now()
            self.assertFalse(E._artifact_committed_in_stage(feat, "PRD.md", _head(root), started))


class TestFingerprintIgnoresProcessDocs(unittest.TestCase):

    def test_doc_commit_keeps_fingerprint(self):
        with tempfile.TemporaryDirectory() as t:
            root, feat = _repo(t)
            before = S._worktree_fingerprint(feat)
            self.assertTrue(before)
            (feat / "TEST-REPORT.md").write_text("# report\n", encoding="utf-8")
            (feat / "state.json").write_text("{}\n", encoding="utf-8")
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "docs")
            (feat / "PRD.md").write_text("# PRD v2\n", encoding="utf-8")   # 未提交的文档改动也不算
            self.assertEqual(before, S._worktree_fingerprint(feat))

    def test_code_change_moves_fingerprint(self):
        with tempfile.TemporaryDirectory() as t:
            root, feat = _repo(t)
            before = S._worktree_fingerprint(feat)
            (root / "src" / "a.py").write_text("x = 3\n", encoding="utf-8")
            self.assertNotEqual(before, S._worktree_fingerprint(feat))

    def test_e2e_script_in_feature_dir_still_counts(self):
        with tempfile.TemporaryDirectory() as t:
            root, feat = _repo(t)
            before = S._worktree_fingerprint(feat)
            (feat / "e2e").mkdir()
            (feat / "e2e" / "smoke.py").write_text("assert True\n", encoding="utf-8")
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "e2e")
            self.assertNotEqual(before, S._worktree_fingerprint(feat))

    def test_legacy_declared_hash_still_accepted(self):
        with tempfile.TemporaryDirectory() as t:
            root, feat = _repo(t)
            ns = argparse.Namespace(feature=str(feat),
                                    test_tree_hash=S._worktree_fingerprint_legacy(feat))
            ok, _ = S._evidence_test_evidence_fresh({}, ns)
            self.assertTrue(ok)

    def test_recipe_uses_single_source_command(self):
        self.assertIn("state.py tree-hash", E._verification_recipe("test", "/f"))


class TestAcceptanceMergedIntoShip1(unittest.TestCase):

    def test_brief_does_not_stop_when_ac_pass(self):
        b = S._pm_acceptance_brief({})
        self.assertIn("AC 全过**不在此停**", b)
        self.assertIn("「✅ 验收」段", b)
        self.assertIn("AI 不可自决", b)              # 没过时照旧停

    def test_pause_point_is_conditional(self):
        self.assertIn("AC 全过不停", S.PM_ACCEPTANCE_SPEC.authorized_pause_point)

    def test_ship1_card_carries_acceptance(self):
        t = (SKILL_ROOT / "stages" / "ship-stage.md").read_text(encoding="utf-8")
        self.assertIn("**点合并 = 验收通过并发布**", t)
        self.assertIn("要改 <问题>", t)

    def test_skill_pause_table_updated(self):
        t = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("→ ⑤ pm_acceptance 三选项 →", t)
        self.assertIn("点合并 = 验收通过并发布", t)


class TestProcessRetroOnDemand(unittest.TestCase):

    def test_quiet_feature_needs_no_retro(self):
        st = {"stage_cost": [{"rounds": 10, "overhead_rounds": 1}]}
        self.assertEqual(S.process_retro_reasons(st), [])
        self.assertIn("不写流程复盘", S._retro_line(st))

    def test_triggers(self):
        self.assertTrue(S.process_retro_reasons({"stage_cost": [{"rounds": 10, "overhead_rounds": 4}]}))
        self.assertTrue(S.process_retro_reasons({"bypass_log": [{}]}))
        self.assertTrue(S.process_retro_reasons(
            {"stage_contracts": {"review": {"rounds": [{}, {}, {}]}}}))
        self.assertTrue(S.process_retro_reasons({"ship": {"reopened_fixes": [{}]}}))

    def test_case_reflection_forces_retro(self):
        import _v8_ship as H
        ns = argparse.Namespace(ledger_reflection="判例:xxx")
        self.assertIsNotNone(H._retro_path_if_needed({}, "F1", None, ns))
        ns = argparse.Namespace(ledger_reflection="常规")
        self.assertIsNone(H._retro_path_if_needed({}, "F1", None, ns))


class TestMediumHasNoTC(unittest.TestCase):

    MEDIUM = {"assembly_plan": {"tier": "medium", "dims": {"spec_depth": "prd_tech"}},
              "flow_type": "Feature", "current_stage": "blueprint"}

    def test_tc_skipped_only_for_medium_and_lite(self):
        self.assertTrue(S._tc_skipped(self.MEDIUM))
        self.assertFalse(S._tc_skipped({"assembly_plan": {"tier": "full",
                                                          "dims": {"spec_depth": "prd_tech"}}}))

    def test_blueprint_tc_artifact_skippable(self):
        tc = next(a for a in S.BLUEPRINT_SPEC.artifacts if a.path == "TC.md")
        self.assertTrue(tc.skip_if(self.MEDIUM))

    def test_binding_deferred_to_test_stage(self):
        with tempfile.TemporaryDirectory() as t:
            Path(t, "PRD.md").write_text("# PRD\n", encoding="utf-8")
            ok, msg = S._evidence_ac_test_binding(self.MEDIUM, argparse.Namespace(feature=t))
            self.assertTrue(ok, msg)
            self.assertIn("test 阶段", msg)

    def test_briefs_switch_carrier(self):
        self.assertIn("medium 档不产 `TC.md`", S._blueprint_brief(self.MEDIUM))
        self.assertIn("test_refs", S._dev_brief(self.MEDIUM))


if __name__ == "__main__":
    unittest.main(verbosity=2)
