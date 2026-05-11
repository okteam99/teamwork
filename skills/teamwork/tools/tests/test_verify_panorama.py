#!/usr/bin/env python3
"""verify-panorama.py 回归套件 · 5 维度物化校验。"""

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
SCRIPT = TOOLS / "verify-panorama.py"


def run(args: list[str], expect_exit: int = 0) -> dict:
    cmd = [sys.executable, str(SCRIPT), *args]
    r = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ})
    assert r.returncode == expect_exit, (
        f"exit {r.returncode} ≠ {expect_exit}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    )
    raw = r.stdout if r.returncode == 0 else (r.stdout or r.stderr)
    return json.loads(raw)


PASSING_UI_MD = """# Test UI

> 🔴 全景宿主：当前子项目
> 🔴 panorama_path: /tmp/x

## 预览稿
- [page1](./preview/page1.html)

## Designer 自查报告（出口必填）

### 检查结果汇总
| 维度 | 检查项 | 通过 | 备注 |
|------|------|----|----|
| 1. 全景对齐 | 4 | 4/4 | OK |
| 2. 状态覆盖 | 4 | 4/4 | OK |
| 3. PRD AC 覆盖 | 2 | 2/2 | OK |
| 4. 全景增量同步 | 4 | 4/4 | ⏭️ 无变更 |
| 5. 结构性变更红线 | 3 | 3/3 | 无 |

### 自查结论
✅ 自查通过 · 可进入 ⏸️ 用户确认
"""


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self.fix = Path(tempfile.mkdtemp(prefix="vp_"))
        (self.fix / "preview").mkdir()
        (self.fix / "preview" / "page1.html").write_text("<html/>")

    def tearDown(self) -> None:
        shutil.rmtree(self.fix, ignore_errors=True)


class TestSelfCheckSection(_Base):
    def test_missing_self_check(self) -> None:
        (self.fix / "UI.md").write_text("# x\n", encoding="utf-8")
        d = run(["--feature", str(self.fix), "--no-panorama"], expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertTrue(any("Designer 自查报告" in e for e in d["checks_failed"]))

    def test_missing_dimension(self) -> None:
        (self.fix / "UI.md").write_text(
            "# x\n## Designer 自查报告\n维度 1 OK\n", encoding="utf-8")
        d = run(["--feature", str(self.fix), "--no-panorama"], expect_exit=1)
        self.assertTrue(any("结构性变更红线" in e for e in d["checks_failed"]))

    def test_unfilled_placeholder(self) -> None:
        (self.fix / "UI.md").write_text(
            "# x\n## Designer 自查报告\n"
            "1. 全景对齐 | 4 | ?/4\n2. 状态覆盖 | 4 | ?/4\n"
            "3. AC 覆盖 | 2 | ?/2\n4. 全景增量同步 | 4 | ?/4\n"
            "5. 结构性变更红线 | 3 | ?/3\n✅ 自查通过\n",
            encoding="utf-8",
        )
        d = run(["--feature", str(self.fix), "--no-panorama"], expect_exit=1)
        self.assertTrue(any("占位符" in e for e in d["checks_failed"]))


class TestPanoramaHostMarker(_Base):
    def test_no_panorama_requires_marker(self) -> None:
        (self.fix / "UI.md").write_text(PASSING_UI_MD, encoding="utf-8")
        d = run(["--feature", str(self.fix), "--no-panorama"], expect_exit=1)
        # PASSING_UI_MD 顶部没有「项目无全景基准」字样
        self.assertTrue(any("无全景" in e for e in d["checks_failed"]))

    def test_no_panorama_with_marker_passes(self) -> None:
        (self.fix / "UI.md").write_text(
            "# x\n> ⚠️ 项目无全景基准\n" + PASSING_UI_MD.split("##", 1)[0] +
            PASSING_UI_MD[PASSING_UI_MD.find("## Designer"):],
            encoding="utf-8",
        )
        d = run(["--feature", str(self.fix), "--no-panorama"])
        self.assertEqual(d["verdict"], "PASS")

    def test_panorama_path_requires_host_marker(self) -> None:
        # 给一个有 sitemap 的 panorama_path · 但 UI.md 缺「全景宿主」
        pano = Path(tempfile.mkdtemp(prefix="pano_"))
        (pano / "sitemap.md").write_text("# sitemap")
        (self.fix / "UI.md").write_text(
            "# x\n## Designer 自查报告\n"
            "1. 全景对齐 | 4 | 4/4\n2. 状态覆盖 | 4 | 4/4\n"
            "3. AC 覆盖 | 2 | 2/2\n4. 全景增量同步 | 4 | 4/4\n"
            "5. 结构性变更红线 | 3 | 3/3\n✅ 自查通过\n",
            encoding="utf-8",
        )
        d = run(["--feature", str(self.fix), "--panorama-path", str(pano)], expect_exit=1)
        self.assertTrue(any("全景宿主" in e for e in d["checks_failed"]))
        shutil.rmtree(pano, ignore_errors=True)


class TestPanoramaPathValid(_Base):
    def test_invalid_path_fails(self) -> None:
        (self.fix / "UI.md").write_text(PASSING_UI_MD, encoding="utf-8")
        d = run(["--feature", str(self.fix),
                 "--panorama-path", "/nonexistent/xyz123"], expect_exit=1)
        self.assertTrue(any("panorama_path 不存在" in e for e in d["checks_failed"]))


class TestPreviewCount(_Base):
    def test_referenced_html_missing(self) -> None:
        # UI.md 引用 page99.html · 但实际不存在
        ui = PASSING_UI_MD.replace("page1.html", "page99.html")
        (self.fix / "UI.md").write_text(
            "> ⚠️ 项目无全景基准\n" + ui, encoding="utf-8")
        d = run(["--feature", str(self.fix), "--no-panorama"], expect_exit=1)
        self.assertTrue(any("preview HTML" in e for e in d["checks_failed"]))


class TestEnvVar(_Base):
    def test_TEAMWORK_FEATURE_env(self) -> None:
        (self.fix / "UI.md").write_text(
            "> ⚠️ 项目无全景基准\n" + PASSING_UI_MD, encoding="utf-8")
        env = {**os.environ, "TEAMWORK_FEATURE": str(self.fix)}
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--no-panorama"],
            capture_output=True, text=True, env=env,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr or r.stdout)
        d = json.loads(r.stdout)
        self.assertEqual(d["verdict"], "PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
