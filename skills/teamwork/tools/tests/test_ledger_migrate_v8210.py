#!/usr/bin/env python3
"""v8.210 · PROCESS-LEDGER 旧 schema 表头升级(幂等 · 只在末尾加列 · 旧数据行是有效前缀)。"""
from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE_PY = HERE.parent / "state.py"

_OLD_HDR = ("| Feature | flow | 实走 stages | 时长 | review/test 轮 | external 总/采/驳 "
            "| 角色真 finding | 暂停点 改:默 | bypass/WARN | 反思摘要(≤1 行) |")
_OLD_ROW = "| OLD-F1 | Feature | goal→dev→ship | 2.4h | 1/1 | 3/1/2 | arch:1 | 1:2 | 0/0 | 旧反思 |"


def _proj(ledger_body=None):
    d = Path(tempfile.mkdtemp(prefix="lm-"))
    subprocess.run(["git", "-C", str(d), "init", "-q"], capture_output=True)
    (d / "project-specs").mkdir()
    if ledger_body is not None:
        (d / "project-specs" / "PROCESS-LEDGER.md").write_text(ledger_body, encoding="utf-8")
    return d


def _run(cwd):
    r = subprocess.run([sys.executable, str(STATE_PY), "ledger-migrate"],
                       cwd=str(cwd), capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)


class TestLedgerMigrate(unittest.TestCase):
    def test_old_schema_header_upgraded_rows_untouched(self):
        d = _proj(f"# 台账\n\n{_OLD_HDR}\n|---|---|---|---|---|---|---|---|---|---|\n{_OLD_ROW}\n")
        out = _run(d)
        self.assertEqual(out["verdict"], "OK")
        self.assertTrue(out["migrated"])
        self.assertEqual((out["old_cols"], out["new_cols"]), (10, 13))
        body = (d / "project-specs" / "PROCESS-LEDGER.md").read_text(encoding="utf-8")
        for c in ("各阶段耗时", "用户邮箱", "宿主"):
            self.assertIn(c, body.splitlines()[2])          # 表头升级
        self.assertIn(_OLD_ROW, body)                       # 旧数据行逐字未动

    def test_idempotent(self):
        d = _proj(f"# 台账\n\n{_OLD_HDR}\n|---|---|---|---|---|---|---|---|---|---|\n{_OLD_ROW}\n")
        _run(d)
        out2 = _run(d)
        self.assertEqual(out2["verdict"], "OK")
        self.assertFalse(out2["migrated"])                  # 二次 no-op

    def test_no_ledger_skip(self):
        self.assertEqual(_run(_proj())["verdict"], "SKIP")

    def test_empty_table_skip(self):
        out = _run(_proj("# 台账\n\n(还没有行)\n"))
        self.assertEqual(out["verdict"], "SKIP")            # 无 | Feature | 表头
