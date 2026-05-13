#!/usr/bin/env python3
"""_feature_context.py 回归套件 · Feature 上下文发现 + 加载。"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
sys.path.insert(0, str(TOOLS))
import _feature_context as fc  # type: ignore  # noqa: E402


def write_state(feature_dir: Path, **overrides) -> Path:
    feature_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "feature_id": overrides.get("feature_id", "AUTH-F042-test"),
        "sub_project": overrides.get("sub_project", "AUTH"),
        "flow_type": overrides.get("flow_type", "Feature"),
        "artifact_root": overrides.get("artifact_root", "auth/docs/features/AUTH-F042-test"),
        "current_stage": overrides.get("current_stage", "dev"),
        "worktree": {
            "strategy": "auto",
            "path": overrides.get("worktree_path", "/abs/.worktree/AUTH-F042-test"),
            "branch": overrides.get("branch", "feature/AUTH-F042-test"),
        },
        "merge_target": overrides.get("merge_target", "staging"),
        "external_cross_review": {
            "model": overrides.get("ext_model"),
        },
    }
    p = feature_dir / "state.json"
    p.write_text(json.dumps(state), encoding="utf-8")
    return p


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="fc_"))
        self.feature_dir = self.tmp / "auth" / "docs" / "features" / "AUTH-F042-test"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)
        # 清环境变量
        os.environ.pop("TEAMWORK_FEATURE", None)


class TestExplicitDiscovery(_Base):
    def test_explicit_dir_happy(self) -> None:
        write_state(self.feature_dir)
        ctx = fc.load(self.feature_dir)
        self.assertIsNotNone(ctx)
        assert ctx is not None
        self.assertEqual(ctx.feature_id, "AUTH-F042-test")
        self.assertEqual(ctx.flow_type, "Feature")
        self.assertEqual(ctx.current_stage, "dev")
        self.assertEqual(ctx.branch, "feature/AUTH-F042-test")
        self.assertEqual(ctx.worktree_path, "/abs/.worktree/AUTH-F042-test")
        self.assertEqual(ctx.merge_target, "staging")
        self.assertIsNone(ctx.ext_model)
        self.assertEqual(ctx.discovery_source, "explicit")

    def test_explicit_dir_missing_state(self) -> None:
        self.feature_dir.mkdir(parents=True)  # 目录有 · state.json 没有
        ctx = fc.load(self.feature_dir)
        self.assertIsNone(ctx)

    def test_explicit_dir_corrupt_state(self) -> None:
        self.feature_dir.mkdir(parents=True)
        (self.feature_dir / "state.json").write_text("{not json", encoding="utf-8")
        ctx = fc.load(self.feature_dir)
        self.assertIsNone(ctx)


class TestEnvDiscovery(_Base):
    def test_env_var_resolved(self) -> None:
        write_state(self.feature_dir)
        os.environ["TEAMWORK_FEATURE"] = str(self.feature_dir)
        ctx = fc.load()
        self.assertIsNotNone(ctx)
        assert ctx is not None
        self.assertEqual(ctx.discovery_source, "env_TEAMWORK_FEATURE")
        self.assertEqual(ctx.feature_id, "AUTH-F042-test")

    def test_env_var_bad_path(self) -> None:
        os.environ["TEAMWORK_FEATURE"] = "/nope/nonexistent"
        ctx = fc.load()
        self.assertIsNone(ctx)


class TestWalkUpDiscovery(_Base):
    def test_walk_from_cwd_finds_state(self) -> None:
        write_state(self.feature_dir)
        # 在 feature_dir 内部某个 sub-dir 启动 · 应能 walk up 找到
        nested = self.feature_dir / "preview"
        nested.mkdir()
        original_cwd = os.getcwd()
        try:
            os.chdir(nested)
            ctx = fc.load()
            self.assertIsNotNone(ctx)
            assert ctx is not None
            self.assertEqual(ctx.discovery_source, "walk_cwd")
        finally:
            os.chdir(original_cwd)

    def test_walk_no_features_segment_skips(self) -> None:
        # state.json 存在但 parent 不含 'features' 段 → walk 不识别
        bad = self.tmp / "random" / "dir"
        bad.mkdir(parents=True)
        (bad / "state.json").write_text(json.dumps({"feature_id": "X"}), encoding="utf-8")
        original_cwd = os.getcwd()
        try:
            os.chdir(bad)
            ctx = fc.load()
            self.assertIsNone(ctx)
        finally:
            os.chdir(original_cwd)


class TestPriority(_Base):
    def test_explicit_overrides_env(self) -> None:
        write_state(self.feature_dir, feature_id="EXPLICIT")
        other = self.tmp / "other" / "docs" / "features" / "OTHER-F1"
        write_state(other, feature_id="FROM_ENV")
        os.environ["TEAMWORK_FEATURE"] = str(other)
        ctx = fc.load(self.feature_dir)
        self.assertIsNotNone(ctx)
        assert ctx is not None
        self.assertEqual(ctx.discovery_source, "explicit")
        self.assertEqual(ctx.feature_id, "EXPLICIT")


class TestPartialFields(_Base):
    def test_missing_worktree_section(self) -> None:
        # 写一个最小 state.json · 仅 feature_id
        self.feature_dir.mkdir(parents=True)
        (self.feature_dir / "state.json").write_text(
            json.dumps({"feature_id": "MINIMAL-F1"}), encoding="utf-8"
        )
        ctx = fc.load(self.feature_dir)
        self.assertIsNotNone(ctx)
        assert ctx is not None
        self.assertEqual(ctx.feature_id, "MINIMAL-F1")
        self.assertIsNone(ctx.branch)
        self.assertIsNone(ctx.worktree_path)
        self.assertIsNone(ctx.merge_target)

    def test_environment_config_fallback(self) -> None:
        """worktree 段缺时 · branch / merge_target fall back 到 environment_config。"""
        self.feature_dir.mkdir(parents=True)
        state = {
            "feature_id": "FALLBACK-F1",
            "environment_config": {
                "branch": "feature/fallback",
                "merge_target": "main",
            },
        }
        (self.feature_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        ctx = fc.load(self.feature_dir)
        assert ctx is not None
        self.assertEqual(ctx.branch, "feature/fallback")
        self.assertEqual(ctx.merge_target, "main")


class TestMergeParam(unittest.TestCase):
    def test_explicit_takes_precedence_no_override(self) -> None:
        v, was = fc.merge_param("explicit", None)
        self.assertEqual(v, "explicit")
        self.assertFalse(was)

    def test_explicit_overrides_context(self) -> None:
        v, was = fc.merge_param("explicit", "from_state")
        self.assertEqual(v, "explicit")
        self.assertTrue(was)

    def test_context_used_when_no_explicit(self) -> None:
        v, was = fc.merge_param(None, "from_state")
        self.assertEqual(v, "from_state")
        self.assertFalse(was)

    def test_both_none_returns_none(self) -> None:
        v, was = fc.merge_param(None, None)
        self.assertIsNone(v)
        self.assertFalse(was)

    def test_empty_string_treated_as_unset(self) -> None:
        v, was = fc.merge_param("", "from_state")
        self.assertEqual(v, "from_state")


if __name__ == "__main__":
    unittest.main()
