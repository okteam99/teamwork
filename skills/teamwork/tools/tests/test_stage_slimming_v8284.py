"""v8.284:四段结构转正(STAGES.md §3)+ 批次二 stage 减法(ui-design/blueprint/ship)。

根因发现:四段结构卡在 3/13 不是偷懒 —— STAGES.md §3 仍**必含**「怎么做 + 质量基线」,
已迁移的 dev/review/goal 反而不符书面规范,未迁移的在忠实遵守旧条款。本版改标准解锁推广。
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


class TestStagesStandard(unittest.TestCase):
    def setUp(self):
        self.t = (ROOT / "STAGES.md").read_text(encoding="utf-8")

    def test_four_section_is_standard(self):
        for seg in ("① 目标(telos)", "② 硬规则(白名单", "③ 建议手段菜单", "④ Output Contract"):
            self.assertIn(seg, self.t, f"四段结构缺:{seg}")

    def test_old_mandate_removed(self):
        """旧条款(必含 怎么做 + 质量基线)已废 —— 它是推广的实际阻塞。"""
        self.assertNotIn("| `## 怎么做` | substep 序列", self.t)
        self.assertNotIn("| `## 质量基线` | 物化拦截清单", self.t)

    def test_hard_rule_criteria_documented(self):
        """②硬规则的保留判据 = 治结构风险不教干活(证据/独立采样/用户主权/纯机械)。"""
        for k in ("证据/验证", "独立采样", "用户主权", "纯机械操作", "不该进②的"):
            self.assertIn(k, self.t, f"判据缺:{k}")


class TestUiDesignSlimming(unittest.TestCase):
    def setUp(self):
        self.t = (ROOT / "stages" / "ui-design-stage.md").read_text(encoding="utf-8")

    def test_frontend_commonsense_details_cut(self):
        """⑦ 教学示例:前端常识**规则行**已删(模型内建 · 原文自陈的理由已随模型能力失效)。

        注:v8.284 删除留痕行会提到这些词(说明删了什么)· 故断言规则行形态而非词本身。
        """
        for rule_line in ("- **反馈**:hover", "- **触控/指针**:可点元素",
                          "- **排版**:复用既有字阶", "- **颜色**:复用既有语义色",
                          "- **间距**:既有 4/8px scale"):
            self.assertNotIn(rule_line, self.t, f"前端常识规则行回归:{rule_line}")
        # 失效前提的原文表述不得留存
        self.assertNotIn("模型对交互体验缺天生判断力(实战反馈", self.t)

    def test_judgments_retained(self):
        """但判据保留(完备四态/可恢复/边界退化/一致>独特/文案用户视角)。"""
        for k in ("完备四态必设计", "可恢复", "边界退化想过", "一致 > 独特", "文案从用户视角"):
            self.assertIn(k, self.t, f"判据丢失:{k}")

    def test_ceremony_self_check_converted(self):
        """⑨ 环节化自检:v8.263 裁定的最后一处漏网 → 改写法注。"""
        self.assertNotIn("Designer 自查报告对 **A 段逐项过**", self.t)
        self.assertIn("写法非环节", self.t)

    def test_materialized_gates_retained(self):
        """①③ 物化闸 + 用户主权暂停点一条未动。"""
        for k in ("_check_same_stack_preview_project", "用户预览确认",
                  "随设计一并改", "verify-panorama.py", "IA 镜像律", "分层同构律"):  # v8.336:sitemap 改动归 ui_design 本体
            self.assertIn(k, self.t, f"必保留项丢失:{k}")


class TestBlueprintSlimming(unittest.TestCase):
    def setUp(self):
        self.t = (ROOT / "stages" / "blueprint-stage.md").read_text(encoding="utf-8")

    def test_tech_section_contradiction_fixed(self):
        """🐛 修真实缺陷:§3 与 Output Contract 曾给 9 段 vs 5 段两份矛盾的 TECH 清单。

        断言实质(结构以模板为单源 · 无第二份段落清单)· 不锁措辞 —— v8.285 四段结构重排后措辞已变。
        """
        self.assertNotIn("§模块 / §数据 / §接口 / §依赖 / §风险", self.t)
        self.assertIn("templates/tech.md", self.t)          # 指向模板单源
        self.assertIn("单源", self.t)

    def test_evidence_requirements_retained(self):
        """① 证据要求保留(现状基线 grounded / 消费方 grep / SQL 给理由)。"""
        for k in ("grounded 真实代码", "grep 消费方", "必给理由"):
            self.assertIn(k, self.t, f"证据要求丢失:{k}")

    def test_independence_and_sovereignty_retained(self):
        """②③ 独立采样 + 用户主权一条未动。"""
        for k in ("不喂主对话起草心路", "互不喂对方产出", "模型错开",
                  "变更点明细是本暂停点的正文", "cross_review_coverage"):
            self.assertIn(k, self.t, f"必保留项丢失:{k}")


class TestShipSlimming(unittest.TestCase):
    def setUp(self):
        self.t = (ROOT / "stages" / "ship-stage.md").read_text(encoding="utf-8")

    def test_delivery_order_stated_once(self):
        """⑧ 重复:投递次序曾在三处各说一遍 · 收敛为单源。"""
        self.assertEqual(self.t.count("先后台启动"), 1, "投递次序应只说一次")
        self.assertIn("回合终文", self.t)

    def test_all_gates_retained(self):
        """ship 只砍旁白 —— 门禁/命令/红线一条未动(判据①③④)。"""
        for k in ("git add -A <feature_dir>/", "翻牌验收门", "verify-delivered",
                  "绝不在合并前删 worktree", "--distill", "bl-flip-exception",
                  "auto_mode=true` 也必停", "user_card"):
            self.assertIn(k, self.t, f"门禁丢失:{k}")
