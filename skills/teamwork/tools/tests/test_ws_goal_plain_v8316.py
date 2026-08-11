"""v8.316:WS feature 总览加「大白话目标」列 + 「子项目」改「涉及子项目」(用户两条拍板)。

实证(WS-11 截图):总览表「功能」列是技术短语(「SuperRun 数据库连接注入」)—— 扫一眼
看不出每条 feature 做完后谁能干什么;且「子项目」列名与 v8.314「feature 可跨多个子项目」
的语义已不符(单数暗示)。

设计要点:
- **与 v8.314 的「交付物」槽合一,单名「大白话目标」** —— 昨天刚立的 交付物(这条单独上线后
  谁得到什么)与本次要的大白话目标是同一概念;一个概念两个名字必漂(v8.308 五维/六维现行判例),
  故全链统一:拆解讨论稿槽 · WS `features[].goal_plain` · body 行 · ws-progress 总览表列,四处同名。
- 数据链:讨论稿必答 → 落 frontmatter `goal_plain`(机读)→ ws-progress 名册驱动直出表列 ——
  空着显「—」即可见(载体承载 · 不配门)。
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import state as S  # noqa: E402


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class TestParserPicksGoalPlain(unittest.TestCase):

    def _ws(self, body: str) -> Path:
        d = Path(tempfile.mkdtemp(prefix="tw-ws316-"))
        p = d / "WS-09-x.md"
        p.write_text(body, encoding="utf-8")
        return p

    def test_goal_plain_parsed(self):
        p = self._ws(
            "<!-- TEAMWORK-MACHINE\n"
            "ws_id: WS-09\n"
            "features:\n"
            "  - id: WS-09-S1\n"
            "    target: CA\n"
            "    bl: BL-034\n"
            '    goal_plain: "用户能把自己的数据库接进 Console"\n'
            '    scope: "BYO 端到端"\n'
            "-->\n# WS-09\n")
        feats = S._parse_ws_features(p)
        self.assertEqual(len(feats), 1)
        self.assertEqual(feats[0]["goal_plain"], "用户能把自己的数据库接进 Console")

    def test_missing_goal_plain_defaults_empty(self):
        """存量 WS 没有该字段 —— 解析不许炸 · 缺省空串(表里显「—」)。"""
        p = self._ws(
            "<!-- TEAMWORK-MACHINE\nfeatures:\n"
            "  - id: WS-09-S1\n    target: CA\n    bl: BL-034\n"
            '    scope: "..."\n-->\n# WS-09\n')
        feats = S._parse_ws_features(p)
        self.assertEqual(feats[0].get("goal_plain", ""), "")


class TestTableRendersNewColumns(unittest.TestCase):

    def _render(self, items):
        block, _ = S._render_ws_progress("WS-09", items, 1, True)
        return block

    def test_header_renamed_and_column_added(self):
        out = self._render([{
            "bl": "BL-034", "name": "BYO 接入", "status": "✅ 已交付", "stage": "",
            "f_id": "CA-F1", "ws": "WS-09", "subproject": "CA", "short": "S1",
            "goal_plain": "用户能把自己的数据库接进 Console"}])
        self.assertIn("| feature | BL | 涉及子项目 | 功能 | 大白话目标 | 状态 | 当前阶段 | F |", out)
        self.assertIn("用户能把自己的数据库接进 Console", out)
        self.assertNotIn("| 子项目 |", out, "旧列名残留(v8.314:feature 可跨子项目 · 单数列名误导)")

    def test_empty_goal_shows_dash_not_crash(self):
        """孤儿行 / 存量名册没有 goal_plain —— 渲染必须容缺。"""
        out = self._render([{
            "bl": "BL-035", "name": "连接注入", "status": "待开始", "stage": "",
            "f_id": "", "ws": "WS-09", "subproject": "CA", "short": "S3"}])
        self.assertIn("| 连接注入 | — |", out)


class TestSingleNameAcrossChain(unittest.TestCase):
    """一个概念一个名字:讨论稿槽 / frontmatter 字段 / body 行 / 表列 四处同名。"""

    def test_template_has_field_and_body_line(self):
        t = _read("templates/workstream.md")
        self.assertIn("goal_plain:", t)
        self.assertIn("大白话目标", t)
        self.assertIn("写不出可感知目标 = 横切件并回宿主", t)

    def test_old_name_fully_retired(self):
        """「业务交付物」/独立的「交付物」槽名在三个载体清零 —— 双名并存 = 漂移种子。"""
        for rel in ("docs/feature-planning.md", "templates/workstream.md"):
            t = _read(rel)
            self.assertNotIn("业务交付物", t, f"{rel} 旧名残留")
        import importlib
        importlib.reload(S)
        hits = [i for i in S.PLANNING_CHECKLIST if "业务交付物" in i["item"]]
        self.assertEqual(hits, [], "checklist 旧名残留")

    def test_discussion_draft_names_the_field(self):
        """讨论稿槽点名 goal_plain 落点 —— 讨论产出与落盘字段有名字链路,不靠意会。"""
        t = _read("docs/feature-planning.md")
        self.assertIn("features[].goal_plain", t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
