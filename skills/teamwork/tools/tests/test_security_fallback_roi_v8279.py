"""v8.279:安全加固/兜底降级 = external finding 过度设计高发区 · 采纳前必过 ROI。

缺口:blueprint §4 已有兜底 ROI · 但 external 裁决单源 §12 + goal/review finding 姿态
只泛说「过度设计」· 没点名这两类最难驳最易盲采。ROI 门(v8.265/266)接到裁决路径。
"""
import unittest
from pathlib import Path

import _v8_stage_specs as S

ROOT = Path(__file__).resolve().parent.parent.parent


class TestSecurityFallbackROI(unittest.TestCase):
    def test_adjudication_source_names_both_classes(self):
        d = (ROOT / "standards" / "external-model-usage.md").read_text(encoding="utf-8")
        self.assertIn("安全加固 / 兜底降级 = 过度设计高发区", d)
        self.assertIn("ROI", d)

    def test_goal_external_counterlens_names_them(self):
        g = (ROOT / "stages" / "goal-stage.md").read_text(encoding="utf-8")
        self.assertIn("安全加固/兜底降级 finding 尤其过 ROI", g)

    def test_review_finding_posture_brief_names_them(self):
        b = S._review_brief({})
        self.assertIn("安全加固/兜底降级最易盲采", b)
        self.assertIn("必过 ROI", b)

    def test_architect_telos_names_them(self):
        a = (ROOT / "roles" / "architect.md").read_text(encoding="utf-8")
        self.assertIn("安全加固/兜底降级是过度设计最高发区", a)
