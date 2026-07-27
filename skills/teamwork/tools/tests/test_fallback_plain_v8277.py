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

    def test_blueprint_points_to_single_source(self):
        """v8.284 手段升级:blueprint 不再自带同构副本 · 改「照抄 TECH §兜底清单」+ 点名大白话列。

        v8.277 目的 = 暂停点贴出的表别丢列;原手段 = 两表同构。但同一文件里实测到该模式的漂移
        (§3 与 Output Contract 对 TECH 段落给出 9 段 vs 5 段两份矛盾清单)—— 只有一处定义才不会漂。
        """
        self.assertIn("照抄 TECH §兜底清单", self.bp)
        self.assertIn("💬 大白话列", self.bp)          # 列要求仍在暂停点可见
        self.assertNotIn("| 兜底 | 💬 大白话 | 保护什么失败场景", self.bp)  # 不再有第二份定义

    def test_tech_is_single_source(self):
        """tech.md 是兜底清单的唯一定义处 · 列顺序:兜底 → 💬 大白话 → …"""
        cols = [c.strip() for c in _fallback_header(self.tech).strip().strip("|").split("|")]
        self.assertEqual(cols[0], "兜底")
        self.assertEqual(cols[1], "💬 大白话")
