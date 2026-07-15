"""v8.248 · ws-progress BL 撞号判别(bug 2:by_bl 全局首见即胜 · 张冠李戴)。

BL-NNN 各项目独立递增(conventions §4)· 三子项目各有 BL-001 时 · 勿手改自动块每次刷新都写错。
"""
import tempfile
import unittest
from pathlib import Path

from state import _pick_bl_row


def _cand(root: Path, rel_rm: str, sub: str, f_id: str = "") -> tuple:
    rm = root / rel_rm
    return (sub, {"bl": "BL-001", "name": "x", "f_id": f_id, "ws": "WS-01"}, rm)


class TestPickBlRow(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="blpick-"))

    def test_single_candidate_passthrough(self):
        c = _cand(self.root, "apps/partner/docs/ROADMAP.md", "partner")
        self.assertIs(_pick_bl_row({"bl": "BL-001", "target": "SVC"}, [c], {}, self.root), c)

    def test_registry_docs_root_wins_over_scan_order(self):
        wrong = _cand(self.root, "apps/partner/docs/ROADMAP.md", "partner")
        right = _cand(self.root, "services/platform/docs/ROADMAP.md", "platform")
        reg = {"SVC": "services/platform/docs/features", "PTR": "apps/partner/docs/features"}
        picked = _pick_bl_row({"bl": "BL-001", "target": "SVC"}, [wrong, right], reg, self.root)
        self.assertEqual(picked, right)
        picked2 = _pick_bl_row({"bl": "BL-001", "target": "PTR"}, [wrong, right], reg, self.root)
        self.assertEqual(picked2, wrong)

    def test_f_id_prefix_fallback_without_registry(self):
        a = _cand(self.root, "apps/partner/docs/ROADMAP.md", "partner", f_id="PTR-F033")
        b = _cand(self.root, "services/platform/docs/ROADMAP.md", "platform", f_id="")
        picked = _pick_bl_row({"bl": "BL-001", "target": "PTR"}, [b, a], {}, self.root)
        self.assertEqual(picked, a)

    def test_no_target_keeps_old_first_wins(self):
        a = _cand(self.root, "a/docs/ROADMAP.md", "a")
        b = _cand(self.root, "b/docs/ROADMAP.md", "b")
        self.assertIs(_pick_bl_row({"bl": "BL-001", "target": ""}, [a, b], {}, self.root), a)


if __name__ == "__main__":
    unittest.main()
