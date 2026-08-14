"""评审模型错开机器门(P1-5)。

case(supersdk CA):双路冷审实测同为 opus-5(主审路未继承会话模型)= 盲区相关,
补派错开模型盲审**当场查出 2 条 BLOCKER** —— SKILL 的「评审模型必错开」是纯规则,
产物只申报不比对(规则存在 ≠ 规则执行)。

治法:主审产物 frontmatter 申报 `review_models`(列表形态适配行式解析)·
evidence check 与外审 `review_model` 合并比对 —— ≥2 路申报且全同 → complete 拒;
<2 可比对(存量未申报 / 单路)→ skip 并在 hint 教申报;ultra-ingest 不参与。
"""
import argparse
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

from _v8_stage_specs import (  # noqa: E402
    BLUEPRINT_SPEC,
    GOAL_SPEC,
    REVIEW_SPEC,
    _evidence_review_models_staggered,
)

CHECK = _evidence_review_models_staggered("REVIEW.md")


def _feature(primary_fm: str = "", ext_files: dict | None = None):
    d = Path(tempfile.mkdtemp(prefix="stag-"))
    if primary_fm:
        (d / "REVIEW.md").write_text(f"---\n{primary_fm}\n---\nbody\n", encoding="utf-8")
    if ext_files:
        ed = d / "external-cross-review"
        ed.mkdir()
        for name, fm in ext_files.items():
            (ed / name).write_text(f"---\n{fm}\n---\nbody\n", encoding="utf-8")
    return d


def _run(d):
    return CHECK({}, argparse.Namespace(feature=str(d)))


class TestStaggerGate(unittest.TestCase):

    def test_all_same_model_fails(self):
        """supersdk 原案:主审 + 外审全 opus-5 → 拒。"""
        d = _feature("reviewers: [architect]\nreview_models:\n - architect: claude-opus-5",
                     {"review-a.md": "review_via: subagent\nreview_model: claude-opus-5"})
        ok, msg = _run(d)
        self.assertFalse(ok)
        self.assertIn("盲区相关", msg)
        self.assertIn("bypass 协议", msg)                     # 例外走既有留痕通道 · 不发明新旗

    def test_staggered_passes(self):
        d = _feature("review_models:\n - architect: claude-opus-5",
                     {"review-a.md": "review_via: subagent\nreview_model: claude-fable-5"})
        ok, msg = _run(d)
        self.assertTrue(ok)
        self.assertIn("已错开", msg)

    def test_case_insensitive_compare(self):
        d = _feature("review_models:\n - architect: Claude-Opus-5",
                     {"review-a.md": "review_via: subagent\nreview_model: claude-opus-5"})
        ok, msg = _run(d)
        self.assertFalse(ok)

    def test_legacy_primary_skips_with_teaching_hint(self):
        """存量产物没有 review_models → skip · hint 教新产物怎么申报。"""
        d = _feature("reviewers: [architect]\nverdict: APPROVE",
                     {"review-a.md": "review_via: subagent\nreview_model: claude-opus-5"})
        ok, msg = _run(d)
        self.assertTrue(ok)
        self.assertIn("存量兼容", msg)
        self.assertIn("review_models", msg)

    def test_single_route_skips(self):
        d = _feature("review_models:\n - architect: claude-opus-5")
        ok, msg = _run(d)
        self.assertTrue(ok)
        self.assertIn("skipped", msg)

    def test_ultra_ingest_not_compared(self):
        """/code-review ultra 摄入产物模型不由框架派发 · 不参与错开比对。"""
        d = _feature("review_models:\n - architect: claude-opus-5",
                     {"review-u.md": "review_via: ultra-ingest\nreview_model: claude-opus-5"})
        ok, _ = _run(d)
        self.assertTrue(ok)                                   # 可比对仅 1 路 → skip

    def test_two_externals_same_model_fails_without_primary(self):
        d = _feature("", {"review-a.md": "review_via: subagent\nreview_model: terra",
                          "review-b.md": "review_via: subagent\nreview_model: terra"})
        ok, msg = _run(d)
        self.assertFalse(ok)

    def test_single_space_indent_declaration_parses(self):
        """申报用单空格缩进也认(v8.324 解析器放宽 · 申报格式不再是新的格式税)。"""
        d = _feature("review_models:\n - architect: opus\n - qa: fable",
                     {"review-a.md": "review_via: subagent\nreview_model: opus"})
        ok, msg = _run(d)
        self.assertTrue(ok)                                   # fable ≠ opus → 错开成立


class TestRegistration(unittest.TestCase):

    def test_registered_in_three_review_stages(self):
        for spec in (GOAL_SPEC, BLUEPRINT_SPEC, REVIEW_SPEC):
            names = [e.name for e in spec.evidence_checks]
            self.assertIn("review_models_staggered", names, spec.name)

    def test_start_brief_preannounces_gate(self):
        """v8.324 契约块自动带上本门 —— 新 evidence 不需要另写预告。"""
        from _v8_engine import _render_complete_contract
        for spec in (GOAL_SPEC, BLUEPRINT_SPEC, REVIEW_SPEC):
            self.assertIn("review_models_staggered", _render_complete_contract(spec))

    def test_stage_docs_declare_contract(self):
        for rel in ("stages/goal-stage.md", "stages/blueprint-stage.md",
                    "stages/review-stage.md"):
            doc = (SKILL_ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("review_models", doc, rel)
            self.assertIn("盲区相关", doc, rel)


if __name__ == "__main__":
    unittest.main()
