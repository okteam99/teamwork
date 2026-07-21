"""v8.275:暂停点投递位置(回合终文 · 先启动监控再贴卡)+ migration 门目录级匹配 + 配方 target_commit。

实证 case(IOS-F005 会话):ship1 卡片贴出后同回合又调 await-merge · 宿主不渲染回合中段文本 ·
卡片被吞 · 用户被迫问「url 发下」;OfflineOriginMigrationStore.swift 被 migration 子串误伤;
degraded 配方产物缺 target_commit → --verify-fixes 找不到上轮 FAIL。
"""
import unittest
from pathlib import Path

import _v8_ship as SHIP

TOOLS = Path(__file__).resolve().parent.parent


class TestMigrationPathMatch(unittest.TestCase):
    def test_business_components_not_matched(self):
        for f in ("Sources/OfflineOriginMigrationStore.swift",
                  "web/components/LegacyOriginMigrationCallout.tsx",
                  "docs/migration-notes.md"):
            self.assertIsNone(SHIP._MIGRATION_PATH_RE.search(f.lower()), f)

    def test_db_migration_paths_matched(self):
        for f in ("db/migrations/001_add_users.sql",
                  "backend/migration/V2__add_index.sql",
                  "db/migrate/20260721_create.rb",
                  "alembic/versions/abc123_add.py"):
            self.assertIsNotNone(SHIP._MIGRATION_PATH_RE.search(f.lower()), f)


class TestPauseDeliveryOrder(unittest.TestCase):
    def test_push_hint_carries_final_message_rule(self):
        src = (TOOLS / "_v8_ship.py").read_text(encoding="utf-8")
        self.assertIn("先后台启动", src)
        self.assertIn("回合终文", src)
        self.assertIn("零工具调用", src)

    def test_skill_r5b_carries_delivery_position(self):
        skill = (TOOLS.parent / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("投递位置", skill)
        self.assertIn("回合最后一条输出", skill)

    def test_degraded_recipe_carries_target_commit(self):
        src = (TOOLS / "state.py").read_text(encoding="utf-8")
        self.assertIn('f"       target_commit: {commit}', src)
