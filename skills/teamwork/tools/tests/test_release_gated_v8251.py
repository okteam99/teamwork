"""v8.251:release-gated 裁决 —— 拆开「代码门」vs「发版门」。

case:review 卡在物理上不可能本地关闭的 BLOCKER(F-002 真实 rollout/7d soak)· 用户手动介入 4 次。
双向护栏:能 mock 复现的(F-004 WireMock)必须本地做完;真部署/真墙钟才 release-gated deferred。
"""
import argparse
import tempfile
import unittest
from pathlib import Path

import _v8_stage_specs as S


def _review(d: Path, findings_yaml: str):
    (d / "REVIEW.md").write_text(
        "---\nreviewers: [architect, external]\nverdict: APPROVE\nfindings:\n"
        + findings_yaml + "---\n", encoding="utf-8")


def _args(d: Path):
    return argparse.Namespace(feature=str(d), verdict="APPROVE")


class TestGuardBareDeferBlocked(unittest.TestCase):
    def test_bare_deferred_blocker_fails(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            _review(d, "  - {id: F1, severity: BLOCKER, status: deferred, title: x, source: qa}\n")
            ok, msg = S._evidence_review_findings_gate({}, _args(d))
            self.assertFalse(ok)
            self.assertIn("deferred_reason", msg)
            self.assertIn("WireMock", msg)   # 反例进了 hint

    def test_bare_deferred_minor_ok(self):
        # MINOR/NIT deferred 不强制 reason(护栏只管 BLOCKER/MAJOR)
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            _review(d, "  - {id: F1, severity: MINOR, status: deferred, title: x, source: qa}\n")
            ok, _ = S._evidence_review_findings_gate({}, _args(d))
            self.assertTrue(ok)


class TestReleaseGatedPasses(unittest.TestCase):
    def test_release_gated_with_reason_approves(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            _review(d, '  - {id: F1, severity: BLOCKER, status: deferred, title: soak, source: qa, '
                       'deferred_reason: "release-gated · 欠 真实 staging rollout + 7d soak"}\n')
            ok, msg = S._evidence_review_findings_gate({}, _args(d))
            self.assertTrue(ok, msg)

    def test_open_blocker_still_blocks(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            _review(d, "  - {id: F1, severity: BLOCKER, status: open, title: bug, source: arch}\n")
            ok, _ = S._evidence_review_findings_gate({}, _args(d))
            self.assertFalse(ok)


class TestCarryForward(unittest.TestCase):
    def test_extractor_strips_prefix(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            _review(d, '  - {id: F2, severity: BLOCKER, status: deferred, title: t, source: qa, '
                       'deferred_reason: "release-gated · 欠 生产 smoke"}\n'
                       '  - {id: F3, severity: MAJOR, status: fixed, title: done, source: arch}\n')
            rg = S.release_gated_deferrals(d)
            self.assertEqual(len(rg), 1)
            self.assertEqual(rg[0]["id"], "F2")
            self.assertIn("生产 smoke", rg[0]["owed"])
            self.assertNotIn("release-gated", rg[0]["owed"].lower())

    def test_pm_brief_surfaces_obligations(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            _review(d, '  - {id: F2, severity: BLOCKER, status: deferred, title: t, source: qa, '
                       'deferred_reason: "release-gated · 欠 生产 soak"}\n')
            b = S._pm_acceptance_brief({"artifact_root": str(d)})
            self.assertIn("发版后待补证据", b)
            self.assertIn("F2", b)

    def test_pm_brief_clean_when_none(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            _review(d, "  - {id: F1, severity: MAJOR, status: fixed, title: done, source: arch}\n")
            b = S._pm_acceptance_brief({"artifact_root": str(d)})
            self.assertNotIn("发版后待补证据", b)


if __name__ == "__main__":
    unittest.main()
