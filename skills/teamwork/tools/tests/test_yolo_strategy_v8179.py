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


def _ext_feature(ext_disabled, review_via, host="claude-code", stage="review"):
    """造 feature dir + external-cross-review + (可选)localconfig disable_external_review。"""
    root = Path(tempfile.mkdtemp(prefix="yx-"))
    if ext_disabled:
        (root / ".teamwork_localconfig.json").write_text(
            json.dumps({"disable_external_review": True}), encoding="utf-8")
    feat = root / "feat"
    (feat / "external-cross-review").mkdir(parents=True)
    fm = ("---\nreview_model: claude-subagent-degraded\nheterogeneous: false\n"
          "degraded: true\ndegraded_mode: config-disabled\n")
    if review_via:
        fm += f"review_via: {review_via}\n"
    fm += "---\n评审正文"
    (feat / "external-cross-review" / "review-claude-subagent-degraded.md").write_text(fm, encoding="utf-8")
    state = {"yolo": True, "host": host, "current_stage": stage}
    return state, NS(feature=str(feat))


class TestYoloExternalGate(unittest.TestCase):
    def test_single_model_cold_subagent_passes(self):
        # yolo + disable_external_review + review_via:subagent → 放行(治本:旧闸误 BLOCK 单模型)
        state, args = _ext_feature(ext_disabled=True, review_via="subagent")
        ok, _ = S._evidence_external_review_artifact(state, args)
        self.assertTrue(ok)

    def test_single_model_without_subagent_blocks(self):
        # yolo + 单模型 + 缺 review_via:subagent(疑热审/手写)→ BLOCK
        state, args = _ext_feature(ext_disabled=True, review_via=None)
        ok, msg = S._evidence_external_review_artifact(state, args)
        self.assertFalse(ok)
        self.assertIn("subagent 冷审", msg)

    def test_heterogeneous_yolo_without_runlog_blocks(self):
        # 非单模型 yolo · 异质评审缺实跑日志 → 原 BLOCK 文案(未被本次改动放松)
        root = Path(tempfile.mkdtemp(prefix="yh-"))
        (root / ".teamwork_localconfig.json").write_text(  # v8.204:opt-in 异质(默认已关)
            json.dumps({"disable_external_review": False}), encoding="utf-8")
        feat = root / "feat"
        (feat / "external-cross-review").mkdir(parents=True)
        (feat / "external-cross-review" / "review-codex.md").write_text(
            "---\nreview_model: codex\n---\nx", encoding="utf-8")
        ok, msg = S._evidence_external_review_artifact(
            {"yolo": True, "host": "claude-code", "current_stage": "review"},
            NS(feature=str(feat)))
        self.assertFalse(ok)
        self.assertIn("实跑证据", msg)

    def test_non_yolo_single_model_passes(self):
        # 非 yolo + 单模型降级:1644 闸只对 yolo 生效 · 普通模式不卡实跑日志
        state, args = _ext_feature(ext_disabled=True, review_via=None)
        state["yolo"] = False
        ok, _ = S._evidence_external_review_artifact(state, args)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
