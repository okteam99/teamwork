"""YOLO 两段式:待确认项攒在 yolo/* 隔离分支(用户拍板)。

拍板原文:「yolo 合入 staging 前需要有风险总结文档,每个 feature 合入时在 yolo 目标分支
记一下待确认信息,留到 yolo 分支合入 target 分支时确认。yolo 必须先合入目标 yolo 分支,
yolo/ 开头的。」

治的是实证事故(协议 v1.0 强制 header → 存量调用方全 400 → 线上请求归零):
AI **识别到了**风险(旧调用方会 400)、**写进了文档**(Bug 影响评估 + MR 风险清单),
但**文档是终点** —— 没有任何通道能把「写下来的风险」变成「必须停的等待」;
那条 Bug 走的正是 yolo,diagnose 方案确认被自动跳过。

设计要点:
- 隔离分支**不是多一道墙**,是**待确认项的落脚处** —— 零 stop 不等于零确认,
  只是把确认**延后并批量化**到 yolo/* → 真 target 那一刻;
- 两个入口(init-feature / set-mode)同约束 —— 否则「先普通启动再切 yolo」是现成的绕过口;
- `yolo-promote` **不代替用户点合并**,只保证「合之前摆到台面上过」。
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

from state import _is_yolo_branch, YOLO_BRANCH_PREFIX       # noqa: E402
from _v8_ship import _append_yolo_pending, YOLO_PENDING_FILE  # noqa: E402

STATE_PY = str(SKILL_ROOT / "tools" / "state.py")


class TestBranchGuard(unittest.TestCase):

    def test_prefix_predicate(self):
        self.assertEqual(YOLO_BRANCH_PREFIX, "yolo/")
        for ok in ("yolo/integration", "yolo/dev-int", "YOLO/x"):
            self.assertTrue(_is_yolo_branch(ok), ok)
        for bad in ("staging", "dev", "main", "", "myolo/x", "yolo"):
            self.assertFalse(_is_yolo_branch(bad), bad)

    def test_staging_is_rejected_not_just_main(self):
        """v8.63 只挡了 main —— 但 staging 常是生产前最后一站,事故正是从那儿出去的。"""
        self.assertFalse(_is_yolo_branch("staging"))

    def test_both_entrypoints_guarded(self):
        """init-feature 与 set-mode 同守 —— 否则「先普通启动再切 yolo」直接绕过两段式。"""
        src = (SKILL_ROOT / "tools" / "state.py").read_text(encoding="utf-8")
        self.assertEqual(src.count("_is_yolo_branch(merge_target)"), 1)
        self.assertIn("if not _is_yolo_branch(new_mt):", src)      # set-mode
        self.assertIn("所有入口同约束", src)

    def test_main_branch_gate_still_first(self):
        """主分支门要先判 —— 它的报错更具体(不得直接进 main),前缀门是兜底。"""
        src = (SKILL_ROOT / "tools" / "state.py").read_text(encoding="utf-8")
        self.assertLess(src.index("yolo 模式禁止 merge_target 是主分支"),
                        src.index("yolo 的 merge_target 必须是 `yolo/` 前缀"))


class TestPendingLedger(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_appends_row_with_header(self):
        r = _append_yolo_pending(self.tmp, {"feature_id": "A-F1"}, "风险X", "会 · KA 客户端")
        self.assertEqual(r["status"], "appended")
        t = (self.tmp / YOLO_PENDING_FILE).read_text(encoding="utf-8")
        self.assertIn("| Feature |", t)
        self.assertIn("A-F1", t)
        self.assertIn("⬜ 待确认", t)
        self.assertIn("会 · KA 客户端", t)

    def test_idempotent_archive_is_reentrant(self):
        _append_yolo_pending(self.tmp, {"feature_id": "A-F1"}, "x", "否")
        r = _append_yolo_pending(self.tmp, {"feature_id": "A-F1"}, "y", "否")
        self.assertEqual(r["status"], "already_present")
        self.assertEqual((self.tmp / YOLO_PENDING_FILE).read_text(encoding="utf-8").count("A-F1"), 1)

    def test_header_states_why_not_just_what(self):
        _append_yolo_pending(self.tmp, {"feature_id": "A-F1"}, "x", "否")
        t = (self.tmp / YOLO_PENDING_FILE).read_text(encoding="utf-8")
        self.assertIn("没有人在看", t)
        self.assertIn("文档是终点", t)          # 事故的机理要写在台账上

    def test_missing_header_is_backfilled(self):
        (self.tmp / YOLO_PENDING_FILE).write_text("旧内容\n", encoding="utf-8")
        _append_yolo_pending(self.tmp, {"feature_id": "A-F1"}, "x", "否")
        self.assertIn("| Feature |", (self.tmp / YOLO_PENDING_FILE).read_text(encoding="utf-8"))


class TestPromote(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        _append_yolo_pending(self.tmp, {"feature_id": "BREAK-1"},
                             "协议强制 header · 存量调用方将 400", "会 · 未带 header 的 KA/REST")
        _append_yolo_pending(self.tmp, {"feature_id": "SAFE-1"}, "无 · 纯新增", "否")

    def _run(self, *extra):
        r = subprocess.run([sys.executable, STATE_PY, "yolo-promote", "--root", str(self.tmp), *extra],
                           capture_output=True, text=True, timeout=60)
        return json.loads(r.stdout or r.stderr)

    def test_lists_pending_and_flags_breaking(self):
        d = self._run()
        self.assertEqual(d["verdict"], "PENDING")
        self.assertEqual(d["total"], 2)
        self.assertEqual(d["pending"], 2)
        self.assertEqual(d["breaking"], 1)          # 破坏性的要单独计数,不能淹在总数里
        self.assertIn("BREAK-1", [i["feature"] for i in d["pending_items"]])

    def test_next_action_asks_the_three_slots(self):
        """破坏性的那几条要问三槽 —— 现存调用方 / 兼容期 / 回滚条件。"""
        na = self._run()["next_action"]
        self.assertIn("现存调用方", na)
        self.assertIn("灰度", na)
        self.assertIn("回滚条件", na)
        self.assertIn("继续讨论", na)               # v8.338:方向类停等第 2 项恒定

    def test_confirm_all_closes_and_is_verifiable(self):
        self.assertEqual(self._run("--confirm-all")["confirmed"], 2)
        after = self._run()
        self.assertEqual(after["verdict"], "OK")
        self.assertEqual(after["pending"], 0)

    def test_promote_does_not_merge(self):
        """确认口不代替用户点合并 —— 只保证摆到台面上过。"""
        src = (SKILL_ROOT / "tools" / "_v8_ship.py").read_text(encoding="utf-8")
        seg = src.split("def cmd_yolo_promote", 1)[1].split("\ndef ", 1)[0]
        self.assertIn("不代替用户点合并", seg)
        self.assertNotIn("_git([\"merge\"", seg)

    def test_missing_ledger_fails_with_hint(self):
        tmp = Path(tempfile.mkdtemp())
        r = subprocess.run([sys.executable, STATE_PY, "yolo-promote", "--root", str(tmp)],
                           capture_output=True, text=True, timeout=60)
        d = json.loads(r.stdout or r.stderr)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("yolo/*", d["hint"])


class TestArchiveGate(unittest.TestCase):

    def test_archive_requires_risk_summary_under_yolo(self):
        src = (SKILL_ROOT / "tools" / "_v8_ship.py").read_text(encoding="utf-8")
        self.assertIn('"pending_step": "yolo-risk-summary"', src)
        self.assertIn('str(state.get("merge_target") or "").lower().startswith("yolo/")', src)
        self.assertIn("--yolo-risk", src)

    def test_ledger_rides_the_archive_commit(self):
        """随归档 commit 原子合入 —— 否则台账留在本地,合过去的分支上没有它。"""
        src = (SKILL_ROOT / "tools" / "_v8_ship.py").read_text(encoding="utf-8")
        self.assertIn('adds.append(_yolo_pending["file"])', src)

    def test_decidable_question_in_gate_text(self):
        src = (SKILL_ROOT / "tools" / "_v8_ship.py").read_text(encoding="utf-8")
        self.assertIn("今天能成功的请求", src)
        self.assertIn("当作会", src)              # 保守偏置 · 代价不对称


class TestSpecCarriers(unittest.TestCase):

    def test_skill_states_two_stage(self):
        t = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`yolo/` 前缀的隔离分支", t)
        self.assertIn("staging 也不行", t)
        self.assertIn("yolo-promote", t)
        self.assertIn("把确认延后并批量化", t)      # 不是加墙 · 是给出口

    def test_ship_stage_section(self):
        t = (SKILL_ROOT / "stages" / "ship-stage.md").read_text(encoding="utf-8")
        seg = t.split("YOLO 两段式", 1)[1].split("\n## ", 1)[0]
        self.assertIn("YOLO-PENDING.md", seg)
        self.assertIn("今天能成功的请求", seg)
        self.assertIn("文档是终点", seg)

    def test_red_budget_under_gate(self):
        t = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(t.count("🔴"), 55)


if __name__ == "__main__":
    unittest.main()
