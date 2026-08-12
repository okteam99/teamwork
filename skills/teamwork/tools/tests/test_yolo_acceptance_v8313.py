"""v8.313:yolo 自动验收物化 + 外部世界动作边界(实证 SDK-F260809171303 · 用户两次拍板)。

case:yolo 跑到 pm_acceptance,AI 停下等 1/2/3,说「发布决策是强制确认点 YOLO 也不能跳过」。
判定:**AI 没编规则 —— 它忠实执行了到达动作点的 brief**。`_pm_acceptance_brief` 原先无条件写
「decision 是用户决策点 · 停等 1/2/3」,整个函数没有 yolo 分支;而 SKILL yolo 表明写
「pm_acceptance = 自动 approved_and_ship + WARN」。**spec 承诺的模式行为从未物化,
工具在动作点反向覆盖 —— fast_mode(brief 说跳过 · 门禁要 external)同族第二例。**

第二层(用户拍板「合入后单独停给用户」):case 里的「发布」= npm 公网发包 + 建公开仓。
yolo 的安全模型是分支门(merge_target 非 main · 主分支人工提升),但外部动作**不经过分支** ——
「零 stop」字面执行会让幻觉级错误直接入公网且不可撤。AI 停下的直觉方向对、挂点错:
该挡的是外部发布(合入后单独停),不是验收与合入(自动)。
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import _v8_stage_specs as S  # noqa: E402


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class TestYoloBriefAutomates(unittest.TestCase):
    """brief 是动作点载体 —— yolo 的自动必须写在它身上,不能只写在 SKILL。"""

    def test_yolo_brief_does_not_stop(self):
        b = S._pm_acceptance_brief({"yolo": True})
        self.assertNotIn("等用户回 1/2/3", b, "yolo brief 仍要求停等 = 本 case 原样复发")
        self.assertNotIn("AI 不可自决", b)
        self.assertIn("approved_and_ship", b)
        self.assertIn("不 emit 三选项", b)

    def test_yolo_brief_keeps_audit_trail(self):
        """自动 ≠ 无痕:WARN concern 是 yolo 健康度的审计数据源。"""
        b = S._pm_acceptance_brief({"yolo": True})
        self.assertIn("add-concern", b)
        self.assertIn("WARN", b)

    def test_yolo_brief_keeps_acceptance_work(self):
        """跳过的只是用户确认 · AC 对照不许跳(自动 ≠ 免验收)。"""
        b = S._pm_acceptance_brief({"yolo": True})
        self.assertIn("AC 对照", b)
        self.assertIn("验收工作不跳过", b)

    def test_yolo_brief_allows_reject_loop(self):
        """自动路径不是硬过:AC 真有问题走 rejected 回修(yolo 自主解决)。"""
        b = S._pm_acceptance_brief({"yolo": True})
        self.assertIn("rejected_with_feedback", b)
        self.assertIn("不硬过", b)

    def test_non_yolo_brief_unchanged(self):
        """非 yolo(含 auto_mode)照旧停 —— 产品决策权是用户专属。"""
        b = S._pm_acceptance_brief({})
        self.assertIn("等用户回 1/2/3", b)
        self.assertIn("AI 不可自决", b)
        self.assertNotIn("yolo · 自动验收", b)

    def test_release_gated_carryforward_survives_in_yolo(self):
        """release-gated 待补证据在 yolo 自动路径同样要随行(欠的账不因自动而消失)。"""
        import tempfile
        d = Path(tempfile.mkdtemp(prefix="tw-yolo-rg-"))
        (d / "REVIEW.md").write_text(
            "---\nreviewers: [external]\nverdict: APPROVE\nfindings:\n"
            "  - {id: F1, severity: MAJOR, status: deferred, title: \"soak 未跑\", source: qa, "
            "deferred_reason: \"release-gated · 欠 7d 生产 soak\"}\n---\n",
            encoding="utf-8")
        b = S._pm_acceptance_brief({"yolo": True, "artifact_root": str(d)})
        self.assertIn("release-gated", b, "yolo 自动路径丢了发版后待补证据的随行")


class TestExternalWorldBoundary(unittest.TestCase):
    """外部世界动作(公网发布/建公开仓/生产部署)= 分支门保护不了的不可逆面。"""

    def test_yolo_brief_carves_out_external_actions(self):
        b = S._pm_acceptance_brief({"yolo": True})
        self.assertIn("外部世界动作", b)
        self.assertIn("单独停给用户", b)
        self.assertIn("不得以「有外部发布」为由", b,
                      "缺反向护栏 → 本 case 的错法(把验收也停掉)会复发")

    def test_skill_yolo_section_defines_the_boundary(self):
        t = _read("SKILL.md")
        self.assertIn("外部世界动作边界", t)
        self.assertIn("不经过分支门", t)
        self.assertIn("RELEASE-GUIDE", t)
        self.assertIn("不在「零 stop」范围", t)

    def test_stage_doc_no_longer_contradicts_skill(self):
        """三载体同口径:SKILL 表(自动)· brief(自动)· stage doc(唯一例外 = yolo)。"""
        t = _read("stages/pm-acceptance-stage.md")
        self.assertIn("唯一例外 = `yolo`", t)
        self.assertIn("自动 `approved_and_ship`", t)
        self.assertIn("外部世界动作", t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
