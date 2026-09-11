"""已确认意图入 PRD:机器搬运 · 全链唯一锚点(用户拍板)。

拍板:「是否需要把确认的意图写到 PRD,在 PRD 背景信息下增加一个已确认用户意图,
防止关键信息丢失,后续流程按错误的方向走。」

查证结果(缺口确认):prepare 确认过的意图此前**只活在对话里** ——
`prepare-check --user-intent` 只写进用户级 `~/.teamwork/prepare_check_audit.jsonl`
(不在 feature 内 · 不进 git · `init-feature` 根本不收这个参数),PRD 模板里也没有槽位。
于是模板头那句「PRD 的脊 = prepare 已确认的意图 · **冷审据此核对**」是**空头承诺**:
冷审没有可核对的对象,只能核对「PRD 内部自洽」——而范围被收窄时 PRD 恰恰完全自洽。

两起事故(协议 header → 线上归零 · AON Link → 投放点击不回传)的共同上游都是
「用户原话只在 PM 的 context 里」,会话一压缩 / 换 session / 派 subagent 就没了。

🔴 关键设计:**机器搬运,不靠 AI 记得抄** —— 只加模板槽位的话又是一个
「靠 AI 自觉」的载体,本仓多版实证过那种不成立。
"""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

from _v8_stage_specs import (_evidence_confirmed_intent as CHK,    # noqa: E402
                             GOAL_SPEC)

STATE_PY = str(SKILL_ROOT / "tools" / "state.py")
PRD_TPL = (SKILL_ROOT / "templates" / "prd.md").read_text(encoding="utf-8")
GOAL_MD = (SKILL_ROOT / "stages" / "goal-stage.md").read_text(encoding="utf-8")


def _tpl_section():
    return re.search(r"(?ms)^## 已确认意图.*?(?=^## 用户故事)", PRD_TPL).group(0)


class TestMachineCarry(unittest.TestCase):
    """① 机器搬运:init-feature 收意图 → state.confirmed_intent。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=self.tmp, check=True)
        subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "i"], cwd=self.tmp,
                       check=True, env={"PATH": "/usr/bin:/bin:/usr/local/bin",
                                        "HOME": str(self.tmp), "GIT_AUTHOR_NAME": "t",
                                        "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                                        "GIT_COMMITTER_EMAIL": "t@t"})

    def _init(self, *extra):
        d = self.tmp / "docs" / "features" / "T-F001-x"
        d.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [sys.executable, STATE_PY, "init-feature", "--feature", str(d),
             "--feature-id", "T-F001-x", "--flow-type", "Feature",
             "--merge-target", "main", "--branch", "b", "--worktree-mode", "off", *extra],
            capture_output=True, text=True, cwd=self.tmp, timeout=60,
            env={"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(self.tmp),
                 "TEAMWORK_BYPASS_PREPARE_CHECK": "1"})
        return json.loads((d / "state.json").read_text(encoding="utf-8"))

    def test_intent_lands_in_state(self):
        st = self._init("--user-intent", "投放链接的点击要能回传 Meta",
                        "--intent-understanding", "恢复 Statics click 导出",
                        "--intent-scope", "做 static 路径 · 不做历史补发",
                        "--intent-existing", "否")
        ci = st["confirmed_intent"]
        self.assertEqual(ci["user_words"], "投放链接的点击要能回传 Meta")
        self.assertEqual(ci["scope"], "做 static 路径 · 不做历史补发")
        self.assertIn("confirmed_at", ci)
        self.assertEqual(ci["amendments"], [])      # 改口 append 的位置先留好

    def test_field_present_even_when_not_passed(self):
        """字段恒在(空值)—— 缺失与「没传」要在 state 上分得开。"""
        self.assertIn("confirmed_intent", self._init())


class TestBriefRenders(unittest.TestCase):
    """② 消费时点:goal brief 把原话渲染出来,起草与冷审都直接拿到。"""

    def test_renders_words_when_present(self):
        b = GOAL_SPEC.brief_template_fn({"confirmed_intent": {
            "user_words": "投放链接的点击要能回传 Meta", "understanding": "恢复 click 导出",
            "scope": "做 static · 不做补发", "existing_behavior": "否"}})
        self.assertIn("投放链接的点击要能回传 Meta", b)
        self.assertIn("原样搬运", b)
        self.assertIn("冷审据此核对", b)

    def test_warns_loudly_when_absent(self):
        """存量 feature / 没传 —— 必须**显式喊出来**,不能静默(静默 = 又一次丢信息)。"""
        b = GOAL_SPEC.brief_template_fn({})
        self.assertIn("state 里没有", b)
        self.assertIn("补回 PRD §已确认意图", b)

    def test_amendments_surface(self):
        b = GOAL_SPEC.brief_template_fn({"confirmed_intent": {
            "user_words": "x", "amendments": [{"note": "原本只做 A · 改为 A+B"}]}})
        self.assertIn("中途修订 1 条", b)
        self.assertIn("不覆盖", b)


class TestGate(unittest.TestCase):
    """③ 机器门:PRD 必有该节 + 原话非空非占位。"""

    def _chk(self, body):
        d = Path(tempfile.mkdtemp())
        (d / "PRD.md").write_text(body, encoding="utf-8")

        class A:
            feature = str(d)
        return CHK({}, A())

    def test_missing_section_fails(self):
        ok, msg = self._chk("# X\n## 背景\nx\n")
        self.assertFalse(ok)
        self.assertIn("冷审唯一能拿到的用户原话", msg)

    def test_placeholder_words_fail(self):
        ok, msg = self._chk("# X\n" + _tpl_section())
        self.assertFalse(ok)
        self.assertIn("用户原话为空或仍是占位", msg)
        self.assertIn("全链唯一的锚点", msg)

    def test_real_words_pass(self):
        ok, msg = self._chk("# X\n" + _tpl_section().replace(
            "{「…」}", "「投放链接的点击要能回传 Meta」"))
        self.assertTrue(ok, msg)

    def test_registered_on_goal(self):
        self.assertIn("confirmed_intent", [e.name for e in GOAL_SPEC.evidence_checks])


class TestCarriers(unittest.TestCase):

    def test_template_section_is_required_core(self):
        self.assertIn("**已确认意图** / 用户故事", PRD_TPL)     # 列进必填核
        seg = _tpl_section()
        for k in ("🗣️", "🎯", "🧩", "📦", "🔁", "✏️"):
            self.assertIn(k, seg, k)
        self.assertIn("原样搬不润色", seg)
        self.assertIn("append", seg)                        # 改口不覆盖

    def test_head_pointer_not_duplicated(self):
        """模板头原来那句「PRD 的脊 = prepare 已确认的意图」有了真载体 → 不再重复一遍。"""
        self.assertNotIn("PRD 的脊 = prepare 已确认的意图", PRD_TPL)
        self.assertIn("PRD 的脊", _tpl_section())            # 说法搬进了本节

    def test_stage_rule_names_the_gap_and_division(self):
        rule = GOAL_MD.split("已确认意图入 PRD", 1)[1].split("\n4.5 ", 1)[0]
        self.assertIn("空头承诺", rule)
        self.assertIn("冷审没有可核对的对象", rule)
        self.assertIn("prepare_check_audit.jsonl", rule)     # 点名旧落点
        self.assertIn("本条是把锚点搬进来", rule)              # 与 4.5 分工
        self.assertIn("4.5 是**拿锚点核对**", rule)

    def test_slimming_gate_respected(self):
        self.assertLess(len(PRD_TPL.splitlines()), 340)


if __name__ == "__main__":
    unittest.main()
