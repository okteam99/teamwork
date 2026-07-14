#!/usr/bin/env python3
"""v8.186 · ws-lint(WS 文档最新模板符合性校验)回归套件。

治本(实证 AON WS-012):AI 做 feature-planning 写 WS 时抄项目里旧/混合格式 · 无符合性检查 ·
只有用户主动问「按最新模板写的么」才发现。ws-lint 对照 templates/workstream.md 硬性形态:
TEAMWORK-MACHINE 块(非裸 ---)+ WS-PROGRESS/WS-DAG 标记区 + 必备 frontmatter(含 v8.185 ui_panorama_confirmed)。

运行:python3 -m pytest skills/teamwork/tools/tests/test_ws_lint_v8186.py -q
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE_PY = HERE.parent / "state.py"
sys.path.insert(0, str(HERE.parent))

from state import _lint_ws_doc  # noqa: E402

_GOOD = """<!-- TEAMWORK-MACHINE · WS
ws_id: WS-01
status: 📝 草稿
ui_panorama: N-A
ui_panorama_confirmed: N-A
承接执行线:
  - Line 1
affected_subprojects:
  - X
features:
  - id: WS-01-S1
    bl: null
    current_state: "已有 router 骨架(apps/x/src/router.ts)· 真缺口=查询页"
-->
# WS-01
<!-- WS-PROGRESS:START x -->
（待）
<!-- WS-PROGRESS:END -->
<!-- WS-DAG:START x -->
（待）
<!-- WS-DAG:END -->
"""

# WS-012 复刻:裸 --- frontmatter · 缺 ui_panorama/confirmed/承接执行线/affected · 无标记区
_OLD = """---
ws_id: WS-12
status: planned
features:
  - id: WS-12-S1
---
# WS-12
正文
"""


class TestLint(unittest.TestCase):
    def test_conformant_empty(self):
        self.assertEqual(_lint_ws_doc(_GOOD), [])

    def test_old_format_flags_all(self):
        miss = " ".join(_lint_ws_doc(_OLD))
        self.assertIn("TEAMWORK-MACHINE", miss)          # 裸 --- → 要注释块
        self.assertIn("ui_panorama_confirmed", miss)     # v8.185 字段缺
        self.assertIn("承接执行线", miss)
        self.assertIn("WS-PROGRESS", miss)               # 无进度标记区
        self.assertIn("WS-DAG", miss)                    # 无 DAG 标记区

    def test_machine_block_present_no_complaint(self):
        # 有 TEAMWORK-MACHINE 就不报「裸 ---」
        miss = _lint_ws_doc(_GOOD)
        self.assertFalse(any("TEAMWORK-MACHINE" in m for m in miss))

    def test_missing_one_field_only(self):
        # 全对但少 ui_panorama_confirmed → 只报这一项相关
        txt = _GOOD.replace("ui_panorama_confirmed: N-A\n", "")
        miss = _lint_ws_doc(txt)
        self.assertTrue(any("ui_panorama_confirmed" in m for m in miss))
        self.assertFalse(any("WS-PROGRESS" in m for m in miss))


class TestCli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="wsl-"))
        (self.root / "product-overview" / "workstream").mkdir(parents=True)

    def _write(self, name, body):
        f = self.root / "product-overview" / "workstream" / name
        f.write_text(body, encoding="utf-8")
        return f

    def _run(self, *a):
        r = subprocess.run([sys.executable, str(STATE_PY), "ws-lint", *a],
                           capture_output=True, text=True, timeout=30, cwd=str(self.root))
        return json.loads(r.stdout) if r.stdout.strip().startswith("{") else None

    def test_conformant_ok(self):
        self._write("WS-01-good.md", _GOOD)
        out = self._run("--ws", "WS-01")
        self.assertEqual(out["verdict"], "OK")
        self.assertTrue(out["conformant"])

    def test_old_nonconformant(self):
        self._write("WS-12-old.md", _OLD)
        out = self._run("--ws", "WS-12")
        self.assertEqual(out["verdict"], "NONCONFORMANT")
        self.assertFalse(out["conformant"])
        self.assertTrue(out["missing"])
        self.assertIn("别抄", out["hint"])

    def test_missing_ws_fail(self):
        out = self._run("--ws", "WS-99")
        self.assertEqual(out["verdict"], "FAIL")


if __name__ == "__main__":
    unittest.main()


class TestV8197LineCheck(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="wsl7-"))
        (self.root / "product-overview" / "workstream").mkdir(parents=True)
        ws = _GOOD.replace("承接执行线:\n  - Line 1", "承接执行线:\n  - Line 1\n  - Line 4")
        (self.root / "product-overview" / "workstream" / "WS-01-x.md").write_text(ws, encoding="utf-8")

    def _run(self):
        r = subprocess.run([sys.executable, str(STATE_PY), "ws-lint", "--ws", "WS-01"],
                           capture_output=True, text=True, timeout=30, cwd=str(self.root))
        return json.loads(r.stdout)

    def test_ghost_line_flagged(self):
        (self.root / "product-overview" / "X_业务架构与产品规划.md").write_text(
            "## 执行线列表\n- Line 1 · 主线\n", encoding="utf-8")   # 无 Line 4
        out = self._run()
        self.assertEqual(out["verdict"], "NONCONFORMANT")
        self.assertTrue(any("幽灵 Line" in m for m in out["missing"]))

    def test_lines_exist_ok(self):
        (self.root / "product-overview" / "X_业务架构与产品规划.md").write_text(
            "## 执行线列表\n- Line 1 · 主线\n- Line 4 · 工具链\n", encoding="utf-8")
        self.assertEqual(self._run()["verdict"], "OK")

    def test_no_arch_doc_skips(self):
        self.assertEqual(self._run()["verdict"], "OK")   # 无业务架构 → skip 不误报


class TestCurrentStateDepthV8239(unittest.TestCase):
    """v8.239 · 调研深度信号:current_state 缺失/占位 = 拆解未 grounded 实际代码。"""
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="wsl9-"))
        (self.root / "product-overview" / "workstream").mkdir(parents=True)

    def _run(self, body):
        (self.root / "product-overview" / "workstream" / "WS-01-x.md").write_text(body, encoding="utf-8")
        r = subprocess.run([sys.executable, str(STATE_PY), "ws-lint", "--ws", "WS-01"],
                           capture_output=True, text=True, timeout=30, cwd=str(self.root))
        return json.loads(r.stdout)

    def test_placeholder_flagged(self):
        body = _GOOD.replace('bl: null', 'bl: null\n    current_state: "<🔴 由实际代码调研得:...>"')
        out = self._run(body)
        self.assertEqual(out["verdict"], "NONCONFORMANT")
        self.assertTrue(any("占位" in m for m in out["missing"]))

    def test_missing_flagged(self):
        body = _GOOD.replace('    current_state: "已有 router 骨架(apps/x/src/router.ts)· 真缺口=查询页"\n', "")
        out = self._run(body)
        self.assertTrue(any("current_state 缺失" in m for m in out["missing"]))

    def test_grounded_passes(self):
        body = _GOOD.replace('bl: null',
            'bl: null\n    current_state: "已有 router 骨架(apps/x/src/router.ts)· 真缺口=查询页(无对应文件)"')
        out = self._run(body)
        self.assertFalse(any("current_state" in m for m in out["missing"]))
