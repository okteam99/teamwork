#!/usr/bin/env python3
"""v8.81 ship1 知识沉淀闸门(distill)回归。

sanitize --distill 知识层 6 项决策硬校验 + 迁移↔schema 一致性机械校验。

运行:python3 -m pytest skills/teamwork/tools/tests/test_ship_distill_v881.py -v
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
STATE_PY = TOOLS / "state.py"

DISTILL_KEYS = ("knowledge", "adr", "reg", "retro", "architecture", "db_schema")
DISTILL_OK = json.dumps({
    "knowledge": "none", "adr": "none", "reg": "none",
    "retro": "n/a", "architecture": "no-change", "db_schema": "no-change",
})


def _git(cwd, *a):
    r = subprocess.run(["git", *a], cwd=str(cwd), capture_output=True, text=True, timeout=15)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _write_state(feat: Path, fid: str) -> None:
    feat.mkdir(parents=True, exist_ok=True)
    (feat / "state.json").write_text(json.dumps({
        "feature_id": fid, "flow_type": "Feature", "current_stage": "ship",
        "merge_target": "main", "ship": {}, "stage_contracts": {}, "concerns": [],
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def _sanitize(feat: Path, distill, expect: int) -> dict:
    argv = [sys.executable, str(STATE_PY), "ship-phase", "--action", "sanitize",
            "--feature", str(feat)]
    if distill is not None:
        argv += ["--distill", distill]
    r = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    assert r.returncode == expect, f"rc {r.returncode} ≠ {expect}\n{r.stdout}\n{r.stderr}"
    raw = r.stdout if r.stdout.strip().startswith("{") else (r.stdout or r.stderr)
    return json.loads(raw) if raw.strip().startswith("{") else {}


class TestDistillGateV881(unittest.TestCase):
    """distill 6 项决策硬校验(缺 / 非法 / 缺项 → BLOCK · 全填 → 记录)。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-distill-"))
        self.feat = self.tmp / "docs" / "features" / "PTR-F700-distill"
        _write_state(self.feat, "PTR-F700-distill")
        self._prev = os.environ.get("TEAMWORK_BYPASS_CHECKSUM")
        os.environ["TEAMWORK_BYPASS_CHECKSUM"] = "1"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self._prev is None:
            os.environ.pop("TEAMWORK_BYPASS_CHECKSUM", None)
        else:
            os.environ["TEAMWORK_BYPASS_CHECKSUM"] = self._prev

    def test_missing_distill_blocks(self):
        d = _sanitize(self.feat, None, 1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("distill", d["error"])

    def test_valid_distill_records(self):
        d = _sanitize(self.feat, DISTILL_OK, 0)
        self.assertEqual(d["verdict"], "PASS")
        for k in DISTILL_KEYS:
            self.assertIn(k, d["distill"])
        st = json.loads((self.feat / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(st["ship"]["distill"]["architecture"], "no-change")
        self.assertIn("distilled_at", st["ship"]["distill"])

    def test_missing_key_blocks(self):
        partial = json.dumps({"knowledge": "none", "adr": "none", "reg": "none",
                              "retro": "n/a", "architecture": "no-change"})  # 缺 db_schema
        d = _sanitize(self.feat, partial, 1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("db_schema", str(d))

    def test_empty_value_blocks(self):
        empty = json.dumps({**json.loads(DISTILL_OK), "adr": "  "})  # 空白值
        d = _sanitize(self.feat, empty, 1)
        self.assertEqual(d["verdict"], "FAIL")

    def test_invalid_json_blocks(self):
        d = _sanitize(self.feat, "{not json", 1)
        self.assertEqual(d["verdict"], "FAIL")


class TestMigrationSchemaCheckV881(unittest.TestCase):
    """迁移↔schema:migration 在 diff + db_schema 声明无变更 + schema 文档未更 → BLOCK。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-migsch-"))
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        _git(self.repo, "init", "-b", "main")
        _git(self.repo, "config", "user.email", "t@x.com")
        _git(self.repo, "config", "user.name", "t")
        (self.repo / "README.md").write_text("init", encoding="utf-8")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-m", "init")
        _git(self.repo, "checkout", "-b", "feat/x")
        mig = self.repo / "db" / "migrations"
        mig.mkdir(parents=True)
        (mig / "20260601_add_table.sql").write_text("CREATE TABLE foo();", encoding="utf-8")
        self.feat = self.repo / "docs" / "features" / "PTR-F701-mig"
        _write_state(self.feat, "PTR-F701-mig")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-m", "feat + migration")
        self._prev = os.environ.get("TEAMWORK_BYPASS_CHECKSUM")
        os.environ["TEAMWORK_BYPASS_CHECKSUM"] = "1"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self._prev is None:
            os.environ.pop("TEAMWORK_BYPASS_CHECKSUM", None)
        else:
            os.environ["TEAMWORK_BYPASS_CHECKSUM"] = self._prev

    def _run(self, db_schema, expect):
        distill = json.dumps({"knowledge": "none", "adr": "none", "reg": "none",
                              "retro": "n/a", "architecture": "no-change",
                              "db_schema": db_schema})
        return _sanitize(self.feat, distill, expect)

    def test_migration_with_no_db_change_blocks(self):
        d = self._run("no-change", 1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("migration", str(d).lower())

    def test_migration_with_declared_change_passes(self):
        # db_schema 声明有变更 → 不矛盾(假设 AI 已更 database-schema.md)→ 放行
        d = self._run("updated foo table", 0)
        self.assertEqual(d["verdict"], "PASS")


if __name__ == "__main__":
    unittest.main()
