"""archive preflight:反向引用扫描 + retro path 物理校验(P1-6)。

case ①(aon-core G-TEST-003):测试 `include_str!` 引用 feature 目录下 fixture ·
archive 按设计把目录从分支删除 → 整个测试二进制编不出来 · cargo check **红 11 天**
(交付完成之日 = 编译失败之日)—— 归档前没人问「repo 里还有谁引用这个目录」。

case ②(supersdk):根级模块 sub_project="SDK" 被 path mapper 拼成不存在的
`SDK/docs/retros` · 同一仓里三种互相矛盾的落点 + 幽灵 `CA/` 目录进了 git。
"""
import argparse
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
TOOLS = SKILL_ROOT / "tools"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS / "tests"))

from _v8_ship import _process_retro_path  # noqa: E402
import test_ship_v8145_flow as _flow  # noqa: E402


class TestBackrefPreflight(_flow._ShipFlowBase):

    def _add_referencing_file(self):
        src = self.wt / "src_test.rs"
        src.write_text(
            f'const F: &str = include_str!("docs/features/{self.FID}/goal/PRD.md");\n',
            encoding="utf-8")
        _flow._git(self.wt, "add", "src_test.rs")
        _flow._git(self.wt, "commit", "-qm", "test refs fixture")

    def test_tracked_reference_blocks_archive(self):
        self._add_referencing_file()
        _, d = self._archive("--no-planning-changes", "--archive-desc", "x")
        self.assertEqual(d.get("verdict"), "PENDING", d)
        self.assertEqual(d.get("pending_step"), "archive-backref")
        self.assertIn("src_test.rs", d.get("referencing_files", []))
        self.assertIn("archive-ref-exception", d.get("next_action", ""))

    def test_exception_flag_passes_and_audited(self):
        self._add_referencing_file()
        _, d = self._archive("--no-planning-changes", "--archive-desc", "x",
                             "--archive-ref-exception", "fixture 下版本迁出")
        self.assertEqual(d.get("verdict"), "PASS", d)
        import json
        st = json.loads((self.wt / self.feat_rel / "state.json")
                        .read_text(encoding="utf-8"))
        self.assertEqual(st["ship"]["archive_ref_exception"], "fixture 下版本迁出")

    def test_no_reference_passes_clean(self):
        _, d = self._archive("--no-planning-changes", "--archive-desc", "x")
        self.assertEqual(d.get("verdict"), "PASS", d)

    def test_archive_zip_string_not_false_positive(self):
        """`_archive/<id>.zip` 类字符串(INDEX 翻牌行形态)不触发 —— 归档后引用本就该指 zip。"""
        note = self.wt / "NOTE.md"
        note.write_text(
            f"归档见 docs/features/_archive/{self.FID}.zip\n", encoding="utf-8")
        _flow._git(self.wt, "add", "NOTE.md")
        _flow._git(self.wt, "commit", "-qm", "note")
        _, d = self._archive("--no-planning-changes", "--archive-desc", "x")
        self.assertEqual(d.get("verdict"), "PASS", d)


class TestRetroPathValidation(unittest.TestCase):

    def test_existing_subproject_prefixed(self):
        import tempfile
        root = Path(tempfile.mkdtemp(prefix="rp-"))
        (root / "apps" / "demo").mkdir(parents=True)
        p = _process_retro_path({"sub_project": "apps/demo"}, "X-F1", str(root))
        self.assertEqual(p, "apps/demo/docs/retros/X-F1-process.md")

    def test_missing_subproject_falls_back_to_root(self):
        """supersdk 原案:sub_project 目录不存在 → 根级 · 不造幽灵目录。"""
        import tempfile
        root = Path(tempfile.mkdtemp(prefix="rp-"))
        p = _process_retro_path({"sub_project": "SDK"}, "X-F1", str(root))
        self.assertEqual(p, "docs/retros/X-F1-process.md")

    def test_no_root_keeps_legacy_behavior(self):
        p = _process_retro_path({"sub_project": "SDK"}, "X-F1")
        self.assertEqual(p, "SDK/docs/retros/X-F1-process.md")

    def test_no_subproject_root_level(self):
        self.assertEqual(_process_retro_path({}, "X-F1", "/nonexistent"),
                         "docs/retros/X-F1-process.md")


class TestSpecCarrier(unittest.TestCase):

    def test_ship_stage_documents_preflight(self):
        doc = (SKILL_ROOT / "stages" / "ship-stage.md").read_text(encoding="utf-8")
        self.assertIn("反向引用 preflight", doc)
        self.assertIn("archive-ref-exception", doc)


if __name__ == "__main__":
    unittest.main()
