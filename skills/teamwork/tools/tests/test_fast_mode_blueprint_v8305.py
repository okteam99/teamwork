"""v8.305:fast_mode 的 blueprint 被门禁强制跑 external —— 四个面的同一族 bug。

实证(aon-core · fast_mode=true):`blueprint-complete` FAIL 要 external,而**同一 stage 的 brief
明写「blueprint 评审跳过」** —— brief 与门禁直接对立。AI(正确地)不篡改 state、不 bypass,
于是**真跑了一轮冷审** → **fast_mode 承诺的提速被静默取消,用户白付一轮**。

四个面:
  ① `_evidence_external_review_artifact` 的守卫 `if stage_roles and "external" not in stage_roles`
     把「**有意配空**」当「**未配置 → 按默认要 external**」;而同文件的 `reviewers_match` 对同一状态
     判 `if not required: return True`(skip)—— **两个 evidence check 语义相反**。
  ② fast_mode 靠**键缺失**表达「blueprint 评审整段去掉」,而缺失读不出「有意」还是「忘了」。
  ③ `change-review-roles` 要求 stage **已在** dict 里 —— 而 fast 恰恰把 blueprint 去掉了 →
     用户**无法自救**,只剩 bypass。
  ④ `fast` 是 fast_mode 自己写进 roster 的伪角色,**却不在 `REVIEW_ROLE_ENUM`** →
     fast 模式下 `change-review-roles` 连把当前值传回去都被判非法角色 = 该模式下整条命令不可用。

🔴 修 ① 时首版**过宽**(把「roster 整个缺失」也判 skip),被既有测试当场抓出 ——
两种「缺失」含义相反:非空 roster 缺本 stage = 有意去掉;roster 整个空 = 未初始化(legacy)。
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import _v8_stage_specs as S  # noqa: E402
from _v8_engine import REVIEW_ROLE_ENUM  # noqa: E402

STATE_PY = ROOT / "tools" / "state.py"


def _gate(state):
    d = Path(tempfile.mkdtemp(prefix="tw-fast-v8305-"))
    return S._evidence_external_review_artifact(state, NS(feature=str(d)))


class TestEmptyRosterSemantics(unittest.TestCase):
    """① 空 roster = 有意不评审 —— 但只在 roster 整体已初始化时。"""

    def test_fast_mode_explicit_empty_skips(self):
        ok, msg = _gate({"current_stage": "blueprint", "stage_review_roles": {
            "goal": ["fast"], "blueprint": [], "review": ["fast"]}})
        self.assertTrue(ok, f"fast_mode 的 blueprint 仍被要求 external:{msg}")

    def test_fast_mode_legacy_missing_key_also_skips(self):
        """存量 state(v8.305 前的 fast)是键缺失形态 —— 也必须 skip,否则 in-flight feature 卡死。"""
        ok, msg = _gate({"current_stage": "blueprint", "stage_review_roles": {
            "goal": ["fast"], "review": ["fast"]}})
        self.assertTrue(ok, f"存量 fast state 仍被卡:{msg}")

    def test_uninitialized_roster_still_requires_external(self):
        """🔴 首版修法过宽的地方:roster **整个缺失** ≠ 有意去掉,是未初始化 —— 仍按默认要求。"""
        ok, _ = _gate({"current_stage": "review"})
        self.assertFalse(ok, "roster 未初始化时不该放行 —— 那会让 legacy state 静默跳过外审")

    def test_normal_feature_with_external_still_enforced(self):
        ok, _ = _gate({"current_stage": "blueprint",
                       "stage_review_roles": {"blueprint": ["architect", "external"]}})
        self.assertFalse(ok, "正常 roster 含 external 时必须照常拦")

    def test_two_evidence_checks_agree_on_empty(self):
        """② 同一状态在两个 check 里必须同义 —— 语义分裂正是本 bug 的根。"""
        st = {"current_stage": "blueprint", "stage_review_roles": {
            "goal": ["fast"], "blueprint": [], "review": ["fast"]}}
        d = Path(tempfile.mkdtemp())
        ok_ext, _ = S._evidence_external_review_artifact(st, NS(feature=str(d)))
        mk = S._evidence_reviewers_match("TECH-REVIEW.md") if hasattr(
            S, "_evidence_reviewers_match") else None
        self.assertTrue(ok_ext)
        if mk:
            ok_rm, _ = mk(st, NS(feature=str(d)))
            self.assertTrue(ok_rm, "reviewers_match 与 external 门对空 roster 判断不一致")


class TestFastModeMaterializesIntent(unittest.TestCase):
    """③ 靠「键缺失」表达意图读不出「有意」还是「忘了」—— fast 必须显式写 blueprint: []。"""

    def test_fast_mode_writes_explicit_empty_blueprint(self):
        src = (ROOT / "tools" / "state.py").read_text(encoding="utf-8")
        self.assertIn('"blueprint": []', src, "fast_mode 未显式物化 blueprint 空 roster")


class TestChangeReviewRolesIsUsableUnderFast(unittest.TestCase):
    """④+③ 用户必须能自救 —— 否则遇到这类配置缺口只剩 bypass(而 bypass 该被拒)。"""

    def _feature(self):
        d = Path(tempfile.mkdtemp(prefix="tw-crr-v8305-"))
        (d / "state.json").write_text(json.dumps({
            "feature_id": "F1", "flow_type": "Feature", "current_stage": "blueprint",
            "completed_stages": [], "stage_contracts": {},
            "created_at": "2026-07-28T00:00:00Z",
            "stage_review_roles": {"goal": ["fast"], "review": ["fast"]},
        }), encoding="utf-8")
        return d

    def _run(self, d, *a):
        r = subprocess.run([sys.executable, str(STATE_PY), "change-review-roles",
                            "--feature", str(d), *a], capture_output=True, text=True, timeout=30)
        out = r.stdout or r.stderr
        try:
            return r.returncode, json.loads(out)
        except (ValueError, json.JSONDecodeError):
            return r.returncode, {"raw": out[:200]}

    def test_fast_pseudo_role_is_a_legal_roster_value(self):
        """框架自己往 roster 写 `fast`,枚举却不认 —— 自产自拒。"""
        self.assertIn("fast", REVIEW_ROLE_ENUM)

    def test_can_clear_a_stage_not_yet_in_roster(self):
        d = self._feature()
        rc, out = self._run(d, "--stage", "blueprint", "--roles", "",
                            "--reason", "fast_mode 明确不评审 blueprint")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.get("verdict"), "OK",
                         "应**物化**显式空(不是 NOOP)—— 意图要留在 state 与 audit 里")
        roles = json.loads((d / "state.json").read_text(encoding="utf-8"))["stage_review_roles"]
        self.assertEqual(roles.get("blueprint"), [])

    def test_can_add_roles_to_a_stage_not_yet_in_roster(self):
        d = self._feature()
        rc, out = self._run(d, "--stage", "blueprint", "--roles", "architect,external",
                            "--reason", "加回 blueprint 评审")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.get("after"), ["architect", "external"])

    def test_fast_roster_can_be_adjusted(self):
        """fast 模式下改 goal 角色 —— v8.305 前因 `fast` 非法角色而整条命令不可用。"""
        d = self._feature()
        rc, out = self._run(d, "--stage", "goal", "--roles", "pl,external",
                            "--reason", "fast 下改回全量 goal 评审")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.get("after"), ["pl", "external"])

    def test_non_review_stage_still_rejected(self):
        """放宽不等于放开 —— 没有评审语义的 stage 仍要拦。"""
        d = self._feature()
        rc, out = self._run(d, "--stage", "ship", "--roles", "qa", "--reason", "x")
        self.assertEqual(rc, 2)
        self.assertIn("没有评审语义", str(out.get("error", "")))


class TestBriefAndGateAgree(unittest.TestCase):
    """brief 说「跳过」而门禁要 external —— 同一 stage 两套口径,是本 bug 最直观的表征。"""

    def test_fast_blueprint_brief_says_skip_and_gate_agrees(self):
        brief = S.BLUEPRINT_SPEC.brief_template_fn({"fast_mode": True})
        self.assertIn("评审跳过", brief)
        ok, _ = _gate({"current_stage": "blueprint", "stage_review_roles": {
            "goal": ["fast"], "blueprint": [], "review": ["fast"]}})
        self.assertTrue(ok, "brief 说跳过 · 门禁却拦 —— 两套口径")


if __name__ == "__main__":
    unittest.main(verbosity=2)
