"""测试数据库按 feature 隔离 · 不共用(用户拍板)。

起因:aon-core 178 份复盘 14 份记共享测试库事故(并发同库伪失败 / 跨 worktree migration 污染 /
TRUNCATE 清表 / 撞专用库护栏才发现)。规则:项目规范优先 → 否则独立库 → 不够才独立容器。
"""
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

import _v8_engine as E  # noqa: E402
import _v8_ship as H  # noqa: E402


def _read(rel):
    return (SKILL_ROOT / rel).read_text(encoding="utf-8")


class TestNamespace(unittest.TestCase):

    def test_derived_from_feature_timestamp(self):
        self.assertEqual(E.test_env_namespace("SVC-CORE-F260924034827-Finance-Chain-Closeout"),
                         "tw_f260924034827")

    def test_distinct_features_distinct_keys(self):
        a = E.test_env_namespace("SVC-CORE-F260924034827-A")
        b = E.test_env_namespace("SVC-CORE-F260924034828-A")
        self.assertNotEqual(a, b)

    def test_fallback_is_db_name_safe(self):
        ns = E.test_env_namespace("weird id/with spaces")
        self.assertRegex(ns, r"^tw_[0-9a-z_]+$")


class TestCarriers(unittest.TestCase):

    def test_recipe_names_the_isolated_db(self):
        r = E._verification_recipe("test", "/f", "SVC-CORE-F260924034827-X")
        self.assertIn("tw_f260924034827", r)
        self.assertIn("不写、不 reset 共享测试库", r)
        self.assertIn("项目规范", r)

    def test_stage_rules(self):
        self.assertIn("测试数据库按 feature 隔离", _read("stages/test-stage.md"))
        self.assertIn("跑集成测试同样按 feature 隔离数据库", _read("stages/dev-stage.md"))

    def test_policy_order_project_then_db_then_container(self):
        t = _read("standards/scripts-policy.md")
        seg = t.split("### 测试环境隔离", 1)[1].split("\n### ", 1)[0]
        self.assertLess(seg.index("按项目"), seg.index("独立数据库"))
        self.assertLess(seg.index("独立数据库"), seg.index("独立容器只在库级隔离不够时用"))
        self.assertIn("--ns <key>", seg)

    def test_push_emits_teardown_hint(self):
        h = H._test_env_teardown_hint({"feature_id": "SVC-CORE-F260924034827-X"})
        self.assertIn("--ns tw_f260924034827", h)
        self.assertIn("不支持 --ns 的 teardown 别跑", h)


if __name__ == "__main__":
    unittest.main(verbosity=2)
