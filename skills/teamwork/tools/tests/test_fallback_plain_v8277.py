"""v8.277:兜底清单加 💬 大白话列(暂停点给用户拍板用 · 同 v8.271 AC 大白话哲学)。

两处兜底清单表(templates/tech.md §兜底清单 · stages/blueprint-stage.md §7.5 暂停块)
必须同构(v8.255 教训:同类表不同构 · 抄写即丢列)· 且都带 💬 大白话列。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _fallback_header(text: str) -> str:
    """抽含「保护什么失败场景」的表头行。"""
    for line in text.splitlines():
        if "保护什么失败场景" in line and line.strip().startswith("|"):
            return line
    return ""


class TestFallbackPlainColumn(unittest.TestCase):
    def setUp(self):
        self.tech = (ROOT / "templates" / "tech.md").read_text(encoding="utf-8")
        self.bp = (ROOT / "stages" / "blueprint-stage.md").read_text(encoding="utf-8")

    def test_tech_table_has_plain_column(self):
        h = _fallback_header(self.tech)
        self.assertIn("💬 大白话", h, f"tech.md 兜底表缺大白话列:{h}")

    def test_blueprint_table_has_plain_column(self):
        h = _fallback_header(self.bp)
        self.assertIn("💬 大白话", h, f"blueprint §7.5 兜底表缺大白话列:{h}")

    def test_two_tables_isomorphic(self):
        """两表列集一致(同构 · 防抄写丢列)。"""
        def _cols(h):
            return [c.strip() for c in h.strip().strip("|").split("|")]
        self.assertEqual(_cols(_fallback_header(self.tech)),
                         _cols(_fallback_header(self.bp)),
                         "tech / blueprint 兜底表列集不一致(v8.255:同类表必须同构)")

    def test_plain_column_right_after_name(self):
        """💬 大白话 紧跟兜底名(读:先看名·紧跟人话)。"""
        cols = [c.strip() for c in _fallback_header(self.tech).strip("|").split("|")]
        self.assertEqual(cols[0], "兜底")
        self.assertEqual(cols[1], "💬 大白话")
