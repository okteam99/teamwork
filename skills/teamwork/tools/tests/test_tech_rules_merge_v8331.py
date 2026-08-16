"""standards 载体合并:tech-rules 三时点唯一必读(用户拍板)。

拍板链:①「整理为技术架构及方案的 review 要点一个文件…没必要拆太多文档」
②「就叫 tech-rules.md 把 hard-rules 也整合进来,技术方案起草、review、dev 开发时必读」
③「明确指出必须读项目的 dev-rules.md(标准路径)· 需同时满足项目规范和本规范 ·
   冲突部分以项目规范为准」。

终态:standards/ = tech-rules + external-model-usage + scripts-policy(3 文件);
HARD-RULES / common / backend 退役 —— 内容按消费时点归位:评审门 → tech-rules §三,
执行环境约定(scratch/起号)→ conventions,脚本契约 → scripts-policy §7,
Designer 自查 → ui-design-stage 附录。
"""
import re
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))
TR = SKILL_ROOT / "standards" / "tech-rules.md"


class TestProjectRulesContract(unittest.TestCase):
    """用户拍板三句 · 逐句锁在文件头。"""

    @classmethod
    def setUpClass(cls):
        cls.head = TR.read_text(encoding="utf-8").split("## 一、")[0]

    def test_must_read_project_rules_with_standard_path(self):
        self.assertIn("必须同时读并满足项目规范", self.head)
        self.assertIn("`project-specs/DEV-RULES.md`", self.head)     # 标准路径明示
        self.assertIn("`project-specs/ARCHITECTURE.md`", self.head)

    def test_both_must_hold_project_wins_conflicts(self):
        self.assertIn("本规范与项目规范需同时满足", self.head)
        self.assertIn("冲突部分以项目规范为准", self.head)

    def test_missing_dev_rules_fallback(self):
        """DEV-RULES 不存在 → 只读本文件 + 提示固化(AI 不代写)。"""
        self.assertIn("DEV-RULES 不存在", self.head)
        self.assertIn("AI 不代写", self.head)

    def test_three_moments_declared(self):
        self.assertIn("方案起草 · dev 开发 · review 三时点唯一必读",
                      TR.read_text(encoding="utf-8").splitlines()[0])


class TestMergedShape(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.t = TR.read_text(encoding="utf-8")

    def test_five_sections(self):
        for s in ("## 一、逆模型默认", "## 二、框架/项目约定", "## 三、方案与架构门",
                  "## 四、前端专项", "## 五、收口自查表"):
            self.assertIn(s, self.t)

    def test_review_gates_absorbed_from_backend(self):
        """backend 的评审门(动词是「评审必查/CR 阻塞」)整体入 §三。"""
        for k in ("FK 决策门", "日志 CR 门", "Schema 变更门", "缺失即阻塞",
                  "架构师 Tech Review BLOCKER", "存量服务已有明确一致的接口风格"):
            self.assertIn(k, self.t)

    def test_retired_files_gone(self):
        std = SKILL_ROOT / "standards"
        for dead in ("HARD-RULES.md", "common.md", "backend.md"):
            self.assertFalse((std / dead).exists(), f"{dead} 应已退役")

    def test_no_dangling_references_repo_wide(self):
        """最强锁:全库(除测试/历史)零悬空引用 —— 退役文件不许再被指。"""
        bad = []
        for f in list(SKILL_ROOT.rglob("*.md")) + list(SKILL_ROOT.rglob("*.py")):
            rel = str(f.relative_to(SKILL_ROOT))
            if (f.name.startswith("test_") or "CHANGELOG" in f.name
                    or "RETRO" in f.name or "audit" in rel):
                continue
            body = f.read_text(encoding="utf-8", errors="replace")
            for dead in ("standards/HARD-RULES", "standards/common", "standards/backend"):
                if dead in body:
                    bad.append(f"{rel} → {dead}")
        self.assertEqual(bad, [], bad)


class TestContentRelocation(unittest.TestCase):
    """内容按消费时点归位 —— 不是删除,是搬家(逐处点名)。"""

    def test_scratch_single_source_in_conventions(self):
        conv = (SKILL_ROOT / "docs" / "conventions.md").read_text(encoding="utf-8")
        self.assertIn("12.48 临时产物目录(scratch)", conv)
        self.assertIn("回收三通道", conv)
        self.assertIn("12.49 迁移文件命名与起号纪律", conv)
        self.assertIn("取 merge_target tip 上的最大 timestamp", conv)

    def test_script_contract_in_scripts_policy(self):
        sp = (SKILL_ROOT / "standards" / "scripts-policy.md").read_text(encoding="utf-8")
        self.assertIn("## 7. 测试脚本两层契约", sp)
        self.assertIn("test-env-setup.sh", sp)
        self.assertNotIn("迁移路径(已完结)", sp)          # 历史段随手清
        self.assertNotIn("已存在的 python 工具", sp)

    def test_designer_check_in_ui_stage(self):
        ui = (SKILL_ROOT / "stages" / "ui-design-stage.md").read_text(encoding="utf-8")
        self.assertIn("附录 · Designer 自查规范", ui)
        self.assertIn("框架基线唯一性", ui)


class TestThreeMomentWiring(unittest.TestCase):
    """三时点载体接线(spec 到达 · v8.321 教训)。"""

    def test_blueprint_dev_review_all_wired(self):
        for stage, anchor in (("blueprint", "起草重点 §三"),
                              ("dev", "standards/tech-rules.md"),
                              ("review", "tech-rules 对照")):
            t = (SKILL_ROOT / "stages" / f"{stage}-stage.md").read_text(encoding="utf-8")
            self.assertIn(anchor, t, stage)

    def test_reviewer_prompt_carries_baseline(self):
        prompt = (SKILL_ROOT / "claude-agents" / "reviewer.md").read_text(encoding="utf-8")
        self.assertIn("standards/tech-rules.md", prompt)
        self.assertIn("冲突以项目为准", prompt)

    def test_dev_brief_carries_tech_rules(self):
        from _v8_stage_specs import DEV_SPEC
        brief = DEV_SPEC.brief_template_fn({})
        self.assertIn("tech-rules", brief)
        self.assertNotIn("HARD-RULES", brief)

    def test_blueprint_and_review_briefs_wired(self):
        """三时点的动作点载体:stage 文档有 ≠ brief 有(规则要在执行入口)。"""
        from _v8_stage_specs import BLUEPRINT_SPEC, REVIEW_SPEC
        bb = BLUEPRINT_SPEC.brief_template_fn({})
        self.assertIn("起草对照 `standards/tech-rules.md`", bb)
        self.assertIn("起草读的就是 review 会查的", bb)
        rb = REVIEW_SPEC.brief_template_fn({})
        self.assertIn("评审对照基线 `standards/tech-rules.md`", rb)
        self.assertIn("冲突以项目为准", rb)

    def test_no_version_tags_in_new_file(self):
        hits = re.findall(r"v8\.\d+", TR.read_text(encoding="utf-8"))
        self.assertEqual(hits, [], hits)


if __name__ == "__main__":
    unittest.main()
