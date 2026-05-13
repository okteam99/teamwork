#!/usr/bin/env python3
"""post-feature.py 回归套件 · scripts-policy R-SP-1 / R-SP-4 / R-SP-5。"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
SCRIPT = TOOLS / "post-feature.py"


def run(args: list[str], expect_exit: int | None = None) -> tuple[int, dict]:
    cmd = [sys.executable, str(SCRIPT), *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    raw = r.stdout if r.returncode != 2 else (r.stdout or r.stderr)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise AssertionError(
            f"non-JSON stdout (R-SP-4 violation)\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}"
        )
    if expect_exit is not None:
        assert r.returncode == expect_exit, (
            f"exit {r.returncode} ≠ {expect_exit}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}"
        )
    return r.returncode, payload


def write_state(features_dir: Path, feature_id: str, **overrides) -> Path:
    fdir = features_dir / feature_id
    fdir.mkdir(parents=True, exist_ok=True)
    state = {
        "feature_id": feature_id,
        "feature_name": overrides.get("name", f"Test feature {feature_id}"),
        "current_stage": overrides.get("current_stage", "completed"),
        "ship": {
            "phase": overrides.get("phase", "merged"),
            "shipped": overrides.get("shipped", "merged"),
            "merge_commit_hash": overrides.get("merge_commit", "abc123def456"),
        },
    }
    state_path = fdir / "state.json"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    return state_path


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pf_"))
        self.project = self.tmp / "proj"
        self.features = self.project / "docs" / "features"
        self.features.mkdir(parents=True)
        self.roadmap = self.project / "docs" / "ROADMAP.md"
        self.knowledge = self.project / "docs" / "KNOWLEDGE.md"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def base_args(self, feature_id: str = "F001") -> list[str]:
        return [
            "--project-dir", str(self.project),
            "--features-dir", "docs/features",
            "--feature-id", feature_id,
            "--roadmap", "docs/ROADMAP.md",
            "--knowledge", "docs/KNOWLEDGE.md",
        ]


class TestHappy(_Base):
    def test_render_into_existing_markers(self) -> None:
        write_state(self.features, "F001", name="Alpha", current_stage="completed")
        write_state(self.features, "F002", name="Beta", current_stage="dev",
                    phase="pushed", shipped="")
        self.roadmap.write_text(
            "# Roadmap\n\n"
            "## 优先级\n手维护内容\n\n"
            "<!-- TEAMWORK_ROADMAP_BEGIN:auto-generated -->\n"
            "OLD_CONTENT\n"
            "<!-- TEAMWORK_ROADMAP_END:auto-generated -->\n\n"
            "## 切片关系\n手维护内容\n",
            encoding="utf-8",
        )
        self.knowledge.write_text(
            "# Knowledge\n\n## F001 经验\n...\n", encoding="utf-8"
        )

        code, payload = run(self.base_args("F001"), expect_exit=0)
        self.assertEqual(payload["verdict"], "OK")
        self.assertEqual(payload["features_scanned"], 2)
        self.assertEqual(payload["features_completed"], 1)
        self.assertEqual(payload["features_in_progress"], 1)
        self.assertEqual(payload["knowledge"]["knowledge"], "present")
        self.assertEqual(payload["roadmap"]["roadmap"], "updated")

        text = self.roadmap.read_text(encoding="utf-8")
        self.assertNotIn("OLD_CONTENT", text)
        self.assertIn("总 Feature：**2**", text)
        self.assertIn("已完成：**1**", text)
        self.assertIn("F001", text)
        self.assertIn("F002", text)
        # marker 外内容必须保留
        self.assertIn("## 优先级\n手维护内容", text)
        self.assertIn("## 切片关系\n手维护内容", text)

    def test_idempotent_rerun(self) -> None:
        write_state(self.features, "F001")
        self.roadmap.write_text(
            "<!-- TEAMWORK_ROADMAP_BEGIN:auto-generated -->\n"
            "x\n"
            "<!-- TEAMWORK_ROADMAP_END:auto-generated -->\n",
            encoding="utf-8",
        )
        self.knowledge.write_text("F001\n", encoding="utf-8")
        run(self.base_args("F001"), expect_exit=0)
        first = self.roadmap.read_text(encoding="utf-8")
        # 二次运行：generated-at 会变 · 但表格 + 统计应一致
        run(self.base_args("F001"), expect_exit=0)
        second = self.roadmap.read_text(encoding="utf-8")
        # 提取 marker 之间的"统计 + 表格"部分（去 generated-at 行）
        def strip_ts(s: str) -> str:
            return "\n".join(
                line for line in s.splitlines() if "generated-at" not in line
            )
        self.assertEqual(strip_ts(first), strip_ts(second))


class TestWarnings(_Base):
    def test_missing_knowledge_warns(self) -> None:
        write_state(self.features, "F001")
        self.roadmap.write_text(
            "<!-- TEAMWORK_ROADMAP_BEGIN:auto-generated -->\n"
            "x\n"
            "<!-- TEAMWORK_ROADMAP_END:auto-generated -->\n",
            encoding="utf-8",
        )
        # 不写 KNOWLEDGE.md
        code, payload = run(self.base_args("F001"), expect_exit=1)
        self.assertEqual(payload["verdict"], "WARN")
        self.assertEqual(payload["knowledge"]["knowledge"], "not_found")
        self.assertIn("knowledge:not_found", payload["warnings"])

    def test_missing_feature_in_knowledge_warns(self) -> None:
        write_state(self.features, "F001")
        self.roadmap.write_text(
            "<!-- TEAMWORK_ROADMAP_BEGIN:auto-generated -->\n"
            "x\n"
            "<!-- TEAMWORK_ROADMAP_END:auto-generated -->\n",
            encoding="utf-8",
        )
        self.knowledge.write_text("# Knowledge\n", encoding="utf-8")
        code, payload = run(self.base_args("F001"), expect_exit=1)
        self.assertEqual(payload["verdict"], "WARN")
        self.assertEqual(payload["knowledge"]["knowledge"], "missing_feature_id")

    def test_missing_roadmap_marker_warns(self) -> None:
        write_state(self.features, "F001")
        self.roadmap.write_text("# Roadmap\n\nno markers here\n", encoding="utf-8")
        self.knowledge.write_text("F001\n", encoding="utf-8")
        code, payload = run(self.base_args("F001"), expect_exit=1)
        self.assertEqual(payload["verdict"], "WARN")
        self.assertEqual(payload["roadmap"]["roadmap"], "marker_missing")
        text = self.roadmap.read_text(encoding="utf-8")
        # 不得改动 ROADMAP（marker 缺 = 等用户首次插入）
        self.assertEqual(text, "# Roadmap\n\nno markers here\n")

    def test_missing_roadmap_file_warns(self) -> None:
        write_state(self.features, "F001")
        # 不写 ROADMAP.md
        self.knowledge.write_text("F001\n", encoding="utf-8")
        code, payload = run(self.base_args("F001"), expect_exit=1)
        self.assertEqual(payload["verdict"], "WARN")
        self.assertEqual(payload["roadmap"]["roadmap"], "not_found")


class TestFailure(_Base):
    def test_corrupt_state_json_blocks(self) -> None:
        # 构造非法 state.json
        bad = self.features / "F001"
        bad.mkdir()
        (bad / "state.json").write_text("{not json", encoding="utf-8")
        self.roadmap.write_text(
            "<!-- TEAMWORK_ROADMAP_BEGIN:auto-generated -->\nx\n"
            "<!-- TEAMWORK_ROADMAP_END:auto-generated -->\n",
            encoding="utf-8",
        )
        code, payload = run(self.base_args("F001"), expect_exit=2)
        self.assertEqual(payload["verdict"], "FAIL")
        self.assertIn("errors", payload)

    def test_missing_project_dir_blocks(self) -> None:
        args = self.base_args("F001")
        # 替换 project-dir 为不存在路径
        idx = args.index("--project-dir") + 1
        args[idx] = str(self.tmp / "nope")
        code, payload = run(args, expect_exit=2)
        self.assertEqual(payload["verdict"], "FAIL")


class TestDryRun(_Base):
    def test_dry_run_does_not_write(self) -> None:
        write_state(self.features, "F001")
        original = (
            "<!-- TEAMWORK_ROADMAP_BEGIN:auto-generated -->\nOLD\n"
            "<!-- TEAMWORK_ROADMAP_END:auto-generated -->\n"
        )
        self.roadmap.write_text(original, encoding="utf-8")
        self.knowledge.write_text("F001\n", encoding="utf-8")
        code, payload = run(self.base_args("F001") + ["--dry-run"], expect_exit=0)
        self.assertEqual(payload["verdict"], "OK")
        self.assertTrue(payload.get("dry_run"))
        self.assertEqual(payload["roadmap"]["roadmap"], "would_update")
        # 文件未变
        self.assertEqual(self.roadmap.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
