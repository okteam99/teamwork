"""台账自动落行(P0-2)。

case:supersdk 47% 归档 feature 台账无行(最近 8 次 ship 漏 3 次 · 人工 append 必漏);
aon-core 复盘原话「emit 提供了已算好的字段 · 台账行仍需人工 append · 若 archive 能
直接落行可再省一轮」;supersdk 判例「精确 ledger_timing 仅在 archive 后 emit ·
需归档后补提交」(时序矛盾)。

治法:archive 直接拼行 + append + 纳入归档 commit(机器格确定性自算 · 判断格走
--ledger-* 参数 · 反思摘要必填 gate)。锁:列宽对齐模板单源 / 单元格净化 /
幂等 / 建表 / 旧 schema 先迁移 / 行随 HEAD 原子合入 / brief 不再教手工 append。
"""
import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
TOOLS = SKILL_ROOT / "tools"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS / "tests"))

from _v8_engine import canonical_ledger_header  # noqa: E402
from _v8_ship import _append_ledger_row, _compose_ledger_row  # noqa: E402
import test_ship_v8145_flow as _flow  # noqa: E402

CANON_WIDTH = canonical_ledger_header(SKILL_ROOT)[0].count("|") - 1


def _mkrepo():
    d = Path(tempfile.mkdtemp(prefix="lar-"))
    subprocess.run(["git", "-C", str(d), "init", "-q"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.email", "t@x.com"],
                   capture_output=True, check=True)
    return d


def _state():
    return {
        "feature_id": "X-F900-demo",
        "flow_type": "Feature",
        "sub_project": "apps/demo",
        "host": "codex-cli",
        "completed_stages": ["goal", "dev", "ship"],
        "stage_contracts": {
            "goal": {"started_at": "2026-08-14T00:00:00Z", "completed_at": "2026-08-14T00:30:00Z",
                     "duration_minutes": 30},
            "dev": {"duration_minutes": 40, "completed_at": "2026-08-14T01:10:00Z"},
        },
        "bypass_log": [{"stage": "test"}],
        "concerns": ["t WARN a", "t WARN b", "info 无关"],
        "stage_cost": [{"rounds": 9, "overhead_rounds": 2}],
        "authoring_preventability": [{"preventable": 3, "total": 12, "missing": ["并发时序"]}],
    }


def _args(**kw):
    base = {"ledger_reflection": "判例:测试反思", "ledger_rounds": None,
            "ledger_external": None, "ledger_findings": None, "ledger_pauses": None}
    base.update(kw)
    return argparse.Namespace(**base)


class TestComposeRow(unittest.TestCase):

    def test_width_matches_template_single_source(self):
        row, _ = _compose_ledger_row(_state(), _args(), str(_mkrepo()), "", "X-F900-demo")
        self.assertEqual(row.count("|") - 1, CANON_WIDTH)

    def test_machine_cells_deterministic(self):
        row, defaulted = _compose_ledger_row(_state(), _args(), str(_mkrepo()), "", "X-F900-demo")
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        self.assertEqual(cells[0], "X-F900-demo")
        self.assertEqual(cells[1], "Feature")
        self.assertEqual(cells[2], "goal→dev→ship")
        self.assertEqual(cells[8], "1/2")                      # bypass_log 1 · concerns WARN 2
        self.assertEqual(cells[12], "codex-cli")               # 宿主
        self.assertIn("3/12 可预防", cells[14])
        self.assertIn("2/9 轮", cells[15])
        # sub_project 目录在 fixture repo 里不存在 → retro path 物理校验回退根级(不造幽灵目录)
        self.assertIn("docs/retros/X-F900-demo-process.md", cells[15])
        self.assertNotIn("apps/demo/docs", cells[15])
        self.assertEqual(defaulted,
                         ["review/test 轮", "external 总/采/驳", "角色真 finding", "暂停点 改:默"])

    def test_judgment_args_land_and_sanitize(self):
        row, defaulted = _compose_ledger_row(
            _state(), _args(ledger_rounds="1/1", ledger_external="3/1/2",
                            ledger_findings="pl:2 / arch:1", ledger_pauses="1:2",
                            ledger_reflection="坏|字符\n换行"),
            str(_mkrepo()), "", "X-F900-demo")
        self.assertEqual(defaulted, [])
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        self.assertEqual(cells[4], "1/1")
        self.assertEqual(cells[5], "3/1/2")
        self.assertEqual(row.count("|") - 1, CANON_WIDTH)      # 竖线被净化 · 表没破
        self.assertIn("坏∣字符 换行", row)


class TestAppendRow(unittest.TestCase):

    ROW = "| X-F900-demo |" + " — |" * (CANON_WIDTH - 1)

    def test_creates_ledger_from_template_when_missing(self):
        wt = _mkrepo()
        res = _append_ledger_row(str(wt), self.ROW, "X-F900-demo")
        self.assertEqual(res["status"], "appended")
        self.assertTrue(res["created"])
        body = (wt / "project-specs" / "PROCESS-LEDGER.md").read_text(encoding="utf-8")
        self.assertIn(canonical_ledger_header(SKILL_ROOT)[0], body)
        self.assertIn(self.ROW, body)

    def test_idempotent_by_feature_id(self):
        wt = _mkrepo()
        _append_ledger_row(str(wt), self.ROW, "X-F900-demo")
        res2 = _append_ledger_row(str(wt), self.ROW, "X-F900-demo")
        self.assertEqual(res2["status"], "exists")
        body = (wt / "project-specs" / "PROCESS-LEDGER.md").read_text(encoding="utf-8")
        self.assertEqual(body.count("X-F900-demo"), 1)

    def test_old_schema_migrated_before_append(self):
        """旧表头 + 短行的存量台账:先迁移(表头升级 + 旧行补宽)再落新行。"""
        wt = _mkrepo()
        specs = wt / "project-specs"
        specs.mkdir()
        (specs / "PROCESS-LEDGER.md").write_text(
            "# 台账\n\n| Feature | flow | 反思摘要 |\n|---|---|---|\n"
            "| OLD-F1 | Bug | 旧行 |\n", encoding="utf-8")
        res = _append_ledger_row(str(wt), self.ROW, "X-F900-demo")
        self.assertEqual(res["status"], "appended")
        lines = (specs / "PROCESS-LEDGER.md").read_text(encoding="utf-8").splitlines()
        old = next(l for l in lines if l.startswith("| OLD-F1 |"))
        self.assertEqual(old.count("|") - 1, CANON_WIDTH)      # 旧行已补宽
        self.assertTrue(lines[-1].startswith("| X-F900-demo |"))  # 新行插在表尾


class TestArchiveIntegration(_flow._ShipFlowBase):
    """真跑 archive:gate / 落行 / 原子入 commit / 幂等 / brief。"""

    def test_missing_reflection_pending(self):
        _, d = _flow._run_state(self.wt, "ship-phase", "--action", "archive",
                                "--feature", self.feature_arg,
                                "--no-planning-changes", "--archive-desc", "x")
        self.assertEqual(d.get("verdict"), "PENDING", d)
        self.assertEqual(d.get("pending_step"), "ledger-row")
        self.assertIn("--ledger-reflection", d.get("next_action", ""))

    def test_row_lands_in_archive_commit(self):
        _, d = self._archive("--no-planning-changes", "--archive-desc", "x",
                             "--ledger-reflection", "判例:自动落行", "--ledger-rounds", "1/1")
        self.assertEqual(d.get("verdict"), "PASS", d)
        lr = d.get("ledger_row") or {}
        self.assertEqual(lr.get("status"), "appended", lr)
        self.assertIn("角色真 finding", lr.get("defaulted_cells", []))
        rc, out, _ = _flow._git(self.wt, "show", "HEAD:project-specs/PROCESS-LEDGER.md")
        self.assertEqual(rc, 0, "台账应随归档 commit 原子入 HEAD")
        row = next(l for l in out.splitlines() if l.startswith(f"| {self.FID} |"))
        self.assertEqual(row.count("|") - 1, CANON_WIDTH)
        self.assertIn("判例:自动落行", row)
        self.assertIn("1/1", row)
        brief = d.get("next_action_brief", "")
        self.assertIn("台账行已自动落", brief)
        self.assertNotIn("写台账行之前先跑", brief)

    def test_rerun_no_duplicate_row(self):
        self._archive("--no-planning-changes", "--archive-desc", "x")
        _, d2 = self._archive("--no-planning-changes", "--archive-desc", "x")
        self.assertTrue(d2.get("already_archived"), d2)
        _, out, _ = _flow._git(self.wt, "show", "HEAD:project-specs/PROCESS-LEDGER.md")
        self.assertEqual(out.count(f"| {self.FID} |"), 1)


if __name__ == "__main__":
    unittest.main()
