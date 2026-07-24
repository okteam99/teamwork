"""v8.281:起草可预防性 —— 每次评审后记录 findings 可预防率 + 缺的起草考虑点 · ship 聚合进台账。

用途:年检据台账「🛡️ 起草可预防性」列判 PRD/TECH 起草考虑点缺不缺(反复缺同一条=真缺口补框架)。
非门禁 · 纯数据采集(不记不拦 ship · 列留空是有效前缀)。
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE_PY = HERE.parent / "state.py"
sys.path.insert(0, str(HERE.parent))
import _v8_ship as SHIP  # noqa: E402


def _run(cwd, *a, expect=0):
    r = subprocess.run([sys.executable, str(STATE_PY), *a], cwd=str(cwd),
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == expect, f"{r.returncode}\n{r.stdout}\n{r.stderr}"
    out = r.stdout if r.stdout.strip() else r.stderr
    s = out.index("{"); depth = 0
    for i in range(s, len(out)):
        if out[i] == "{": depth += 1
        elif out[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(out[s:i+1])


class TestSummary(unittest.TestCase):
    def test_none_when_empty(self):
        self.assertIsNone(SHIP._authoring_preventability_summary({}))

    def test_aggregate_across_reviews(self):
        st = {"authoring_preventability": [
            {"stage": "blueprint", "preventable": 1, "total": 3, "missing": ["迁移前历史预检"]},
            {"stage": "review", "preventable": 2, "total": 6, "missing": ["并发时序", "迁移前历史预检"]},
        ]}
        cell = SHIP._authoring_preventability_summary(st)
        self.assertIn("3/9 可预防", cell)          # 1+2 / 3+6
        self.assertIn("并发时序", cell)
        self.assertEqual(cell.count("迁移前历史预检"), 1)  # 去重

    def test_no_missing_renders_count_only(self):
        st = {"authoring_preventability": [{"stage": "review", "preventable": 0, "total": 4, "missing": []}]}
        self.assertEqual(SHIP._authoring_preventability_summary(st), "0/4 可预防")


class TestRecordCommand(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-prev-"))
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.tmp)], check=True)
        for k, v in (("user.email", "t@t.co"), ("user.name", "t")):
            subprocess.run(["git", "-C", str(self.tmp), "config", k, v], check=True)
        (self.tmp / "s.txt").write_text("x")
        subprocess.run(["git", "-C", str(self.tmp), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(self.tmp), "commit", "-qm", "s"], check=True)
        _run(self.tmp, "init-feature", "--feature", "docs/features/F1", "--feature-id", "F1",
             "--flow-type", "Feature", "--merge-target", "main", "--branch", "feature/f1",
             "--worktree-mode", "off")

    def test_record_appends_to_state(self):
        d = _run(self.tmp, "review-preventability", "--feature", "docs/features/F1",
                 "--stage", "review", "--preventable", "2", "--total", "5",
                 "--missing", "并发时序;错误处理边界", "--note", "两条 stale 类")
        self.assertEqual(d["verdict"], "OK")
        st = json.loads((self.tmp / "docs/features/F1/state.json").read_text())
        ap = st["authoring_preventability"]
        self.assertEqual(len(ap), 1)
        self.assertEqual(ap[0]["preventable"], 2)
        self.assertEqual(ap[0]["missing"], ["并发时序", "错误处理边界"])

    def test_non_gating_optional(self):
        # 不记录 → state 无该字段 · 不影响其它命令(留空是有效前缀)
        st = json.loads((self.tmp / "docs/features/F1/state.json").read_text())
        self.assertNotIn("authoring_preventability", st)


class TestLedgerHeader(unittest.TestCase):
    def test_template_and_separator_column_count_match(self):
        import state as ST
        h = ST._canonical_ledger_header()
        self.assertIsNotNone(h)
        self.assertEqual(h[0].count("|"), h[1].count("|"))
        self.assertIn("起草可预防性", h[0])
