"""v8.280:micro 状态机 preset-aware gate 修复(实证:aifriends 4 行合规 bump 走 micro 撞死门)。

根因:engine 通用 gate 用 raw state.flow_type="Feature" 比 allowed_flow_types=["Micro"](legacy 键)
→ execute-start 恒 FAIL;图查 flow_by_type.get("Feature") 拿 full 图(execute→ship 错路由)。
现有 micro 测试只断言 spec 常量、从没真跑 gate → 漏网。本套件真跑 execute-start/complete。
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _v8_engine as E

HERE = Path(__file__).resolve().parent
STATE_PY = HERE.parent / "state.py"


def _run_state(cwd, *args, expect_exit=0):
    r = subprocess.run([sys.executable, str(STATE_PY), *args],
                       cwd=str(cwd), capture_output=True, text=True, timeout=60)
    assert r.returncode == expect_exit, (
        f"exit {r.returncode} ≠ {expect_exit}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}")
    out = r.stdout if r.stdout.strip() else r.stderr
    s = out.index("{"); depth = 0
    for i in range(s, len(out)):
        if out[i] == "{": depth += 1
        elif out[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(out[s:i + 1])
    raise AssertionError(f"no json · {out!r}")


class TestFlowKeyResolvers(unittest.TestCase):
    def test_internal_flow_key_micro(self):
        self.assertEqual(E._internal_flow_key({"flow_type": "Feature", "preset": "micro"}), "Micro")

    def test_internal_flow_key_full_and_bug(self):
        self.assertEqual(E._internal_flow_key({"flow_type": "Feature", "preset": "full"}), "Feature")
        self.assertEqual(E._internal_flow_key({"flow_type": "Bug"}), "Bug")

    def test_internal_flow_key_legacy_value(self):
        self.assertEqual(E._internal_flow_key({"flow_type": "Micro"}), "Micro")

    def test_resolve_flow_graph_micro_gets_micro_not_full(self):
        fbt = {"Feature": {"goal": ["blueprint"]}, "Feature:micro": {"execute": ["ship"]}, "Bug": {}}
        g = E._resolve_flow_graph({"flow_type": "Feature", "preset": "micro"}, fbt)
        self.assertEqual(g, {"execute": ["ship"]})   # 🔴 关键:micro 拿 micro 图 · 非 full

    def test_resolve_flow_graph_full_unchanged(self):
        fbt = {"Feature": {"goal": ["blueprint"]}, "Feature:micro": {"execute": ["ship"]}}
        g = E._resolve_flow_graph({"flow_type": "Feature", "preset": "full"}, fbt)
        self.assertEqual(g, {"goal": ["blueprint"]})


class TestMicroGateEndToEnd(unittest.TestCase):
    """真跑 state.py:init micro → execute-start 不再撞 flow_type 死门。"""
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-microgate-"))
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.tmp)], check=True)
        subprocess.run(["git", "-C", str(self.tmp), "config", "user.email", "t@t.co"], check=True)
        subprocess.run(["git", "-C", str(self.tmp), "config", "user.name", "t"], check=True)
        (self.tmp / "seed.txt").write_text("x")
        subprocess.run(["git", "-C", str(self.tmp), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(self.tmp), "commit", "-qm", "seed"], check=True)

    def test_micro_execute_start_passes_gate(self):
        d = _run_state(self.tmp, "init-feature", "--feature", "docs/features/MIC-1",
                       "--feature-id", "MIC-1", "--flow-type", "Feature", "--preset", "micro",
                       "--merge-target", "main", "--branch", "feature/mic-1",
                       "--worktree-mode", "off")
        st = json.loads((self.tmp / "docs/features/MIC-1/state.json").read_text())
        self.assertEqual(st["flow_type"], "Feature")
        self.assertEqual(st["preset"], "micro")
        self.assertEqual(st["current_stage"], "execute")
        # 🔴 核心回归:execute-start 不再 FAIL(旧版 allowed_flow_types=["Micro"] vs raw "Feature")
        r = _run_state(self.tmp, "execute-start", "--feature", "docs/features/MIC-1")
        self.assertNotEqual(r.get("verdict"), "FAIL", f"execute-start 仍撞死门:{r}")
