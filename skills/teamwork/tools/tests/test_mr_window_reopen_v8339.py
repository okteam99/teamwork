"""MR 窗口期修复:pushed 后同 feature 回 dev · 不开 Bug 流(用户拍板)。

case(supersdk):ship1 已 push,PR 上 3 个已知代码 blocker —— 消费 AI 按
「Ship 后不可回」判成「必须开 Bug 流再合回」。用户纠偏:直接在当前 feature
回 dev 修,不要新开 bug —— MR 反馈循环是交付的一部分,逼开 Bug 流 =
把「改 PR」变成新立项(新 worktree/新链/新文档全套税)。

机器:jump-to-stage 在 pushed 态开唯一放行口(--to dev + --reason ·
ship.reopened_fixes[] + concerns WARN 双留痕);其余目标照旧拒;
push 重跑本就支持 rerecord。边界:平台已合并 → Bug 流。
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
TOOLS = SKILL_ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from _v8_engine import save_state  # noqa: E402


def _feature(ship_phase="pushed"):
    d = Path(tempfile.mkdtemp(prefix="mrw-")) / "feat"
    d.mkdir(parents=True)
    st = {
        "feature_id": "X-F900-mrfix",
        "flow_type": "Feature",
        "current_stage": "completed",
        "legal_next_stages": [],
        "completed_stages": ["goal", "blueprint", "dev", "review", "test",
                             "pm_acceptance", "ship"],
        "ship": {"phase": ship_phase, "mr_url": "http://x/pr/1"},
        "stage_contracts": {},
    }
    save_state(d / "state.json", st)
    return d


def _run(*args):
    r = subprocess.run([sys.executable, str(TOOLS / "state.py"), *args],
                       capture_output=True, text=True, timeout=30)
    for out in (r.stdout, r.stderr):          # die() 走 stderr · emit 走 stdout
        try:
            return json.loads(out)
        except ValueError:
            continue
    return {"_raw": r.stdout, "_err": r.stderr}


class TestReopenPath(unittest.TestCase):

    def test_pushed_to_dev_with_reason_allowed(self):
        d = _feature()
        out = _run("jump-to-stage", "--feature", str(d), "--to", "dev",
                   "--reason", "MR 修复:artifact 路径 blocker")
        self.assertEqual(out.get("verdict"), "OK", out)
        st = json.loads((d / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(st["current_stage"], "dev")
        self.assertEqual(st["ship"]["phase"], "pushed")            # MR 还开着 · 事实不变
        self.assertEqual(st["ship"]["reopened_fixes"][0]["reason"],
                         "MR 修复:artifact 路径 blocker")
        self.assertTrue(any("mr-window-reopen" in c for c in st["concerns"]))
        self.assertIn("ship", st["completed_stages"])              # 历史不动

    def test_pushed_to_other_stage_still_blocked(self):
        d = _feature()
        out = _run("jump-to-stage", "--feature", str(d), "--to", "review",
                   "--reason", "x")
        self.assertEqual(out.get("verdict"), "FAIL", out)
        self.assertIn("唯一放行口", out.get("hint", ""))
        self.assertIn("Bug 流", out.get("hint", ""))

    def test_reset_prev_hint_points_to_reopen(self):
        d = _feature()
        out = _run("reset-prev", "--feature", str(d), "--reason", "x")
        self.assertEqual(out.get("verdict"), "FAIL", out)
        self.assertIn("jump-to-stage --to dev", out.get("hint", ""))

    def test_unpushed_states_unaffected(self):
        d = _feature(ship_phase=None)
        out = _run("jump-to-stage", "--feature", str(d), "--to", "dev",
                   "--reason", "普通回退")
        self.assertEqual(out.get("verdict"), "OK", out)
        st = json.loads((d / "state.json").read_text(encoding="utf-8"))
        self.assertNotIn("reopened_fixes", st["ship"])             # 非窗口期不记


class TestSpecCarriers(unittest.TestCase):

    def test_ship_stage_section(self):
        t = (SKILL_ROOT / "stages" / "ship-stage.md").read_text(encoding="utf-8")
        seg = t.split("## MR 窗口期修复", 1)[1].split("\n## ")[0]
        self.assertIn("不开 Bug 流", seg[:80])
        self.assertIn("rerecord", seg)                             # push 重跑更新同一 MR
        self.assertIn("不重开", seg)                                # zip 初版墓碑
        self.assertIn("平台已合并**后的问题 → Bug 流", seg)          # 边界
        self.assertIn("新立项", seg)                                # why

    def test_skill_chain_carries_pointer(self):
        t = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("窗口期发现问题 → 同 feature `jump-to-stage --to dev` 修 · 不开 Bug 流", t)


if __name__ == "__main__":
    unittest.main()
