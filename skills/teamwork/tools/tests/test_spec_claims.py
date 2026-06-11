#!/usr/bin/env python3
"""spec 数字宣称一致性校验(v8.122 物化 · 治本 v8.121 review 发现的「数字写死多处 · 演进必漂」)。

校验(代码 = 唯一真相):
- STAGES.md §1 索引行集合 == STAGE_SPECS 全集(漏 stage / 幽灵 stage 都 FAIL · v8.121 曾漏 diagnose)
- 现行 md 的「N stage」数字宣称 == len(STAGE_SPECS)(v8.121 曾同时存在 10/11 两种口径)
- README 版本徽章(major.minor) == SKILL.md frontmatter version 前缀(v8.121 曾滞后 33 版 · patch 段不比 ·
  auto-bump 只动 patch 不影响本校验)
- 现行 md 引用的 cold_start_* gate 名在 bootstrap.py/state.py 真实存在(v8.116 改名残留类)

repo-only 文件(README*)在安装副本不存在 → 自动跳过对应断言。

运行:
    python3 -m pytest skills/teamwork/tools/tests/test_spec_claims.py -v
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = SKILL_ROOT.parents[1]  # 仅 repo checkout 有 README/README-EN · 安装副本无

sys.path.insert(0, str(SKILL_ROOT / "tools"))
from _v8_stage_specs import STAGE_SPECS  # noqa: E402


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _current_md_files() -> list[Path]:
    """SKILL_ROOT 下现行 md(排除 CHANGELOG / 归档 / tools 内部)。"""
    out = []
    for f in SKILL_ROOT.rglob("*.md"):
        rp = str(f.relative_to(SKILL_ROOT))
        if "CHANGELOG" in rp or "archive" in rp.lower() or rp.startswith(("tools/", ".pytest_cache")):
            continue
        out.append(f)
    return out


class TestStagesIndexComplete(unittest.TestCase):
    """STAGES.md §1 索引必须与 STAGE_SPECS 一一对应。"""

    def test_stages_index_rows_equal_stage_specs(self):
        text = _read(SKILL_ROOT / "STAGES.md")
        rows = re.findall(r"^\|\s*([a-z][a-z0-9_]*)\s*\|\s*\[stages/", text, re.M)
        self.assertEqual(
            sorted(rows), sorted(STAGE_SPECS),
            f"STAGES.md 索引({sorted(rows)}) != STAGE_SPECS({sorted(STAGE_SPECS)})"
            " · 漏行(如 v8.121 前漏 diagnose)或幽灵行",
        )


class TestStageCountClaims(unittest.TestCase):
    """「N stage」/「N-stage」数字宣称必须等于 len(STAGE_SPECS)。"""

    CLAIM = re.compile(r"(\d+)[ -]stage\b", re.IGNORECASE)

    def _files(self) -> list[Path]:
        files = [SKILL_ROOT / "SKILL.md", SKILL_ROOT / "STAGES.md",
                 REPO_ROOT / "README.md", REPO_ROOT / "README-EN.md"]
        return [f for f in files if f.exists()]

    def test_stage_count_claims_match_specs(self):
        expected = len(STAGE_SPECS)
        for f in self._files():
            for m in self.CLAIM.finditer(_read(f)):
                self.assertEqual(
                    int(m.group(1)), expected,
                    f"{f.name}: 宣称「{m.group(0)}」 != STAGE_SPECS 实际 {expected}"
                    " · 数字宣称漂移(v8.121 曾 10/11 并存)",
                )


class TestReadmeVersionBadge(unittest.TestCase):
    """README 版本徽章(major.minor) == SKILL.md frontmatter version 前缀。

    auto-bump 只递增 patch 段(v8.X → v8.X.1)· 徽章语义为 major.minor → patch 不参与比较。
    真正的漂移向量 = 人工 minor bump 时忘改 README(v8.87 case 即此类)。
    """

    BADGE = re.compile(r"(?:Version: |当前 |Currently )\*\*v(\d+)\.(\d+)(?:\.\d+)?\*\*")

    def test_badges_match_skill_minor(self):
        m = re.search(r"^version:\s*v(\d+)\.(\d+)", _read(SKILL_ROOT / "SKILL.md"), re.M)
        self.assertIsNotNone(m, "SKILL.md frontmatter 无 version 字段")
        expected = (m.group(1), m.group(2))

        checked_any = False
        for name in ("README.md", "README-EN.md"):
            f = REPO_ROOT / name
            if not f.exists():  # 安装副本无 README → skip
                continue
            badges = self.BADGE.findall(_read(f))
            self.assertTrue(badges, f"{name}: 未找到版本徽章(Version:/当前/Currently **vX.Y**)")
            for b in badges:
                self.assertEqual(
                    b, expected,
                    f"{name}: 徽章 v{b[0]}.{b[1]} != SKILL.md v{expected[0]}.{expected[1]}"
                    " · minor bump 时须同步 README(v8.87 滞后 case)",
                )
            checked_any = True
        if not checked_any:
            self.skipTest("repo README 不存在(安装副本环境)")


class TestGateNamesExist(unittest.TestCase):
    """现行 md 引用的 cold_start_* gate 名必须存在于 bootstrap.py/state.py(防改名残留)。"""

    GATE = re.compile(r"\bcold_start_[a-z_]+\b")

    def test_cold_start_gate_names_exist_in_code(self):
        code = (_read(SKILL_ROOT / "tools" / "bootstrap.py")
                + _read(SKILL_ROOT / "tools" / "state.py"))
        for f in _current_md_files():
            for tok in set(self.GATE.findall(_read(f))):
                self.assertIn(
                    tok, code,
                    f"{f.relative_to(SKILL_ROOT)}: gate `{tok}` 不存在于 bootstrap.py/state.py"
                    "(v8.116 改名残留类 · 文档引用了已不存在的 gate)",
                )


if __name__ == "__main__":
    unittest.main()
