#!/usr/bin/env python3
"""v8.179 · yolo 策略调整回归套件。

三处调整:① 异质 review 受 localconfig `disable_external_review` 控制(已存在 · 单源)·
② yolo + 单模型 → init-feature 醒目警告 + 降级评审必须 subagent 冷审(修 1644 闸误 BLOCK)·
③ yolo 预研门:正式自主前必产 YOLO-PREFLIGHT.md(深入调研 + 核心决策用户确认)· init-feature 校验。

运行:python3 -m pytest skills/teamwork/tools/tests/test_yolo_strategy_v8179.py -q
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import state as ST          # noqa: E402
import _v8_stage_specs as S  # noqa: E402


class TestPreflightGate(unittest.TestCase):
    def _pf(self, text):
        d = Path(tempfile.mkdtemp(prefix="yp-"))
        f = d / "YOLO-PREFLIGHT.md"
        f.write_text(text, encoding="utf-8")
        return f

    def test_missing_blocks(self):
        ok, why = ST._check_yolo_preflight(Path(tempfile.mkdtemp()) / "YOLO-PREFLIGHT.md")
        self.assertFalse(ok)
        self.assertIn("不存在", why)

    def test_sentinel_present_blocks(self):
        f = self._pf("# x\n<!-- YOLO-PREFLIGHT-UNFILLED -->\n## 核心\n用户确认: ok")
        ok, why = ST._check_yolo_preflight(f)
        self.assertFalse(ok)
        self.assertIn("哨兵", why)

    def test_missing_sections_blocks(self):
        f = self._pf("# x\n随便写写没有结构")
        self.assertFalse(ST._check_yolo_preflight(f)[0])

    def test_filled_passes(self):
        f = self._pf("# x\n## 1. 深入调研\n...\n## 2. 核心重要决策\n...\n## 3. 用户确认\n用户已逐条拍板 · 授权")
        self.assertTrue(ST._check_yolo_preflight(f)[0])


def _ext_feature(review_via, with_prompt_doc=True, stage="review"):
    """造 feature dir + external-cross-review 产物(v8.291 新契约)+ (可选)prompt doc 实跑证据。"""
    root = Path(tempfile.mkdtemp(prefix="yx-"))
    feat = root / "feat"
    (feat / "external-cross-review").mkdir(parents=True)
    fm = "---\nreview_model: opus-subagent\n"
    if review_via:
        fm += f"review_via: {review_via}\n"
    fm += "---\n评审正文"
    (feat / "external-cross-review" / "review-opus.md").write_text(fm, encoding="utf-8")
    if with_prompt_doc:                      # yolo 不内化律要的实跑证据
        pd = feat / "external-review-prompts"
        pd.mkdir(parents=True, exist_ok=True)
        (pd / f"{stage}-subagent-review-20260531T000000Z.md").write_text("p", encoding="utf-8")
    return {"yolo": True, "current_stage": stage}, NS(feature=str(feat))


class TestYoloExternalGate(unittest.TestCase):
    """v8.179 单模型放行 · v8.291 换代:跨厂商异质退役 —— 契约 = subagent + 申报模型 + yolo 实跑证据。"""

    def test_subagent_cold_review_passes(self):
        state, args = _ext_feature(review_via="subagent")
        ok, msg = S._evidence_external_review_artifact(state, args)
        self.assertTrue(ok, msg)

    def test_without_subagent_blocks(self):
        state, args = _ext_feature(review_via=None)
        ok, msg = S._evidence_external_review_artifact(state, args)
        self.assertFalse(ok)
        self.assertIn("必须 subagent", msg)

    def test_yolo_without_prompt_doc_blocks(self):
        """yolo 不内化律:产物合规但没跑过命令 → BLOCK(防手写自盖章)。"""
        state, args = _ext_feature(review_via="subagent", with_prompt_doc=False)
        ok, msg = S._evidence_external_review_artifact(state, args)
        self.assertFalse(ok)
        self.assertIn("实跑证据", msg)

    def test_non_yolo_needs_no_prompt_doc(self):
        state, args = _ext_feature(review_via="subagent", with_prompt_doc=False)
        state["yolo"] = False
        ok, msg = S._evidence_external_review_artifact(state, args)
        self.assertTrue(ok, msg)


if __name__ == "__main__":
    unittest.main()
