"""格式门禁前置化(P0-3)。

case:两项目耗时归因 26-28% 轮次 = 纯协调开销,归因高度同质(「格式门禁重试 ·
spec 字段名未预读」「dev-complete 的 test-runner 门在 dev-start 没预告 · complete
时才拒」);aon-core 复盘:外审产物 YAML **单空格缩进**列表被解析为空 `files_read`
→ CAPABILITY_BLOCKED 误报 —— 一个缩进空格换一轮返工。

两刀:
1. start brief 自动附「complete 时机器校验」块 —— 与门禁读**同一份 spec 对象**,
   门禁改了预告自动跟(手写 brief 必然漂移,载体防漂移不靠人同步两处)。
2. parse_frontmatter 列表缩进兼容 1-4 空格 —— 格式门禁的解析器必须比它拦的格式宽一档。
"""
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
TOOLS = SKILL_ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from _v8_engine import _render_complete_contract, parse_frontmatter  # noqa: E402
from _v8_stage_specs import BROWSER_E2E_SPEC, GOAL_SPEC, STAGE_SPECS  # noqa: E402


def _fm(text: str):
    p = Path(tempfile.mkdtemp(prefix="fm-")) / "x.md"
    p.write_text(text, encoding="utf-8")
    return parse_frontmatter(p)


class TestFrontmatterIndentTolerance(unittest.TestCase):

    def test_single_space_list_parses(self):
        """aon 伤亡原型:单空格缩进列表整行被丢 → files_read 空 → 误报。"""
        fm = _fm("---\nreview_via: subagent\nfiles_read:\n - a.md\n - b.md\n---\nbody\n")
        self.assertEqual(fm["files_read"], ["a.md", "b.md"])

    def test_two_to_four_space_lists_parse(self):
        for n in (2, 3, 4):
            pad = " " * n
            fm = _fm(f"---\nfiles_read:\n{pad}- a.md\n{pad}- b.md\n---\n")
            self.assertEqual(fm["files_read"], ["a.md", "b.md"], f"缩进 {n} 空格")

    def test_deep_indent_still_ignored(self):
        """5+ 空格 = 嵌套结构,行式解析不装懂 —— 保持忽略(只放宽到常见手写变体)。"""
        fm = _fm("---\nfiles_read:\n      - deep.md\n---\n")
        self.assertEqual(fm["files_read"], [])

    def test_key_value_untouched(self):
        fm = _fm("---\nreview_model: opus\nfiles_read:\n - a.md\nverdict: PASS\n---\n")
        self.assertEqual(fm["review_model"], "opus")
        self.assertEqual(fm["verdict"], "PASS")
        self.assertEqual(fm["files_read"], ["a.md"])


class TestCompleteContractBlock(unittest.TestCase):

    def test_renders_artifacts_and_evidence_from_same_spec(self):
        block = _render_complete_contract(GOAL_SPEC)
        self.assertIn("complete 时机器校验", block)
        self.assertIn("PRD.md", block)
        self.assertIn("frontmatter 必含 acceptance_criteria", block)
        for e in GOAL_SPEC.evidence_checks:
            self.assertIn(f"`{e.name}`", block)          # 每条 evidence 点名 · 含 description

    def test_browser_e2e_artifacts_announced(self):
        block = _render_complete_contract(BROWSER_E2E_SPEC)
        self.assertIn("screenshots/*.png", block)
        self.assertIn("BROWSER-TEST-REPORT.md", block)

    def test_every_gated_stage_gets_nonempty_block(self):
        """反向锁:有 artifacts/evidence 的 stage,start 预告块必非空 —— 新 spec 自动纳入。"""
        for name, spec in STAGE_SPECS.items():
            if spec.artifacts or spec.evidence_checks:
                self.assertTrue(_render_complete_contract(spec),
                                f"{name} 有 complete 门禁却无 start 预告块")

    def test_empty_spec_renders_nothing(self):
        gateless = [s for s in STAGE_SPECS.values()
                    if not s.artifacts and not s.evidence_checks]
        for s in gateless:
            self.assertEqual(_render_complete_contract(s), "")

    def test_start_flow_appends_block_before_emit(self):
        """源码顺序锁:brief 装配紧跟 brief_template_fn(手写 brief 漂移不再可能漏预告)。"""
        src = (TOOLS / "_v8_engine.py").read_text(encoding="utf-8")
        i_tpl = src.index("brief = stage_spec.brief_template_fn(state)")
        i_ctr = src.index("brief += _render_complete_contract(stage_spec)")
        i_emit = src.index('"next_action_brief": brief')
        self.assertTrue(i_tpl < i_ctr < i_emit)

    def test_dev_test_runner_gate_announced_at_start(self):
        """aon 复盘原案:dev-complete 的 test-runner 门必须在 dev-start 可见。"""
        dev = STAGE_SPECS["dev"]
        block = _render_complete_contract(dev)
        names = " ".join(e.name for e in dev.evidence_checks)
        if "test_runner" in names or "tree_hash" in names:
            self.assertRegex(block, r"test[_-]runner|tree[_-]hash")


if __name__ == "__main__":
    unittest.main()
