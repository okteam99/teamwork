#!/usr/bin/env python3
"""v8.364 · 提效方案第 1 批:清规则冲突 + 确认围绕决策。

- pause-mark 必须写明「用户的回答会定下哪个决定」· 空 → 拒绝
- prepare-check --preset 接受全部起手档(floor 预览不再退回全链)
- micro 准入失败不再一律 full · 定档单源两处不打架
- 缺产品规划时,明确的 Feature/Bug 执行任务不停
"""
from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))
from _v8_engine import close_open_pause  # noqa: E402
STATE_PY = str(HERE.parent / "state.py")
JUDGMENT = json.dumps({"sections_reviewed": ["§2.1", "§2.2"], "matched_signals": [],
                       "recommended_flow_type": "Feature", "ai_rationale": "t"})


def _run(*args, cwd=None, env=None):
    return subprocess.run([sys.executable, STATE_PY, *args], capture_output=True, text=True,
                          cwd=cwd, env=env, timeout=60)


class TestPauseDecision(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp()) / "feat"
        self.d.mkdir()
        (self.d / "state.json").write_text(json.dumps(
            {"feature_id": "X-F1", "current_stage": "goal", "concerns": []}), encoding="utf-8")

    def _state(self):
        return json.loads((self.d / "state.json").read_text(encoding="utf-8"))

    def test_missing_decision_rejected(self):
        r = _run("pause-mark", "--feature", str(self.d), "--label", "进展同步")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("不该停", r.stdout + r.stderr)
        self.assertNotIn("open_pause", self._state())

    def test_blank_decision_rejected(self):
        r = _run("pause-mark", "--feature", str(self.d), "--decision", "   ")
        self.assertNotEqual(r.returncode, 0)

    def test_decision_recorded_through_close(self):
        r = _run("pause-mark", "--feature", str(self.d), "--label", "PRD 确认",
                 "--decision", "退款是否纳入范围")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        st = self._state()
        self.assertEqual(st["open_pause"]["decision"], "退款是否纳入范围")
        close_open_pause(st)
        self.assertEqual(st["pause_log"][-1]["decision"], "退款是否纳入范围")


class TestPreparePreset(unittest.TestCase):
    def _preview(self, preset):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "docs" / "features").mkdir(parents=True)
        r = _run("prepare-check", "--feature-id-prefix", "TEST",
                 "--features-root", str(tmp / "docs" / "features"), "--flow-type", "Feature",
                 "--preset", preset, "--user-intent", "t", "--admission-judgment", JUDGMENT,
                 cwd=tmp, env={"PATH": "/usr/bin:/bin", "HOME": str(tmp),
                               "TEAMWORK_PREPARE_AUDIT_PATH": str(tmp / "a.jsonl")})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return [c["stage"] for c in json.loads(r.stdout).get("stage_chain_preview", [])]

    def test_floor_preview_is_dev_ship(self):
        self.assertEqual(self._preview("floor"), ["dev", "ship"])

    def test_every_feature_preset_accepted(self):
        from state import FEATURE_PRESETS
        for p in FEATURE_PRESETS:
            self.assertTrue(self._preview(p), p)


class TestRuleText(unittest.TestCase):
    def read(self, rel):
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_micro_fail_not_forced_full(self):
        s = self.read("docs/prepare.md")
        self.assertNotIn("任一不满足 → `preset=full`", s)
        self.assertNotIn("否则 preset=full", s)

    def test_prepare_closed_set_lists_all_presets(self):
        s = self.read("docs/prepare.md")
        self.assertIn("full|medium|lite|tiny|floor|micro", s)

    def test_single_source_per_moment(self):
        s = self.read("SKILL.md")
        self.assertNotIn("判定权威 = [docs/prepare.md]", s)
        self.assertIn("定档只有两个时刻", s)

    def test_no_absolute_test_proof_wording(self):
        for rel in ("FLOWS.md", "docs/prepare.md", "stages/goal-stage.md"):
            self.assertNotIn("完全证明", self.read(rel), rel)

    def test_prepare_auto_proceed_section(self):
        self.assertIn("免停条件", self.read("docs/prepare.md"))


class TestColdStartNoStopForExecution(unittest.TestCase):
    def test_action_text(self):
        import bootstrap
        src = Path(bootstrap.__file__).read_text(encoding="utf-8")
        self.assertIn("明确的 Feature/Bug 执行任务(mode B)→ **不停**", src)


if __name__ == "__main__":
    unittest.main()
