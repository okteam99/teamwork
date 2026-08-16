"""v8.285:standards 减法 —— 砍「模型默认就会」的标准做法,留「逆默认 / 不可能知道」的。

判据(用户讨论后确立):一条规则的价值 = **它与模型默认行为的距离**
- 模型默认就会(TDD/SOLID/命名/mermaid 语法/REST)→ 零价值 · 纯注意力税
- 模型不可能知道(本框架脚本两层结构 / 状态码表 / scratch 路径约定)→ 高价值(信息)
- 模型**默认会做反的**(避免 FK / 兜底算 ROI / 降级必打 WARN)→ **最高价值** · 且模型越强越需要
"""
import unittest
from pathlib import Path

STD = Path(__file__).resolve().parent.parent.parent / "standards"
ROOT = Path(__file__).resolve().parent.parent.parent


def _r(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


class TestCommonSlimming(unittest.TestCase):
    """v8.285 立的清剿成果 · v8.331 载体合并后按新家逐条核(内容不许复活/丢失)。"""

    def test_rd_self_check_ceremony_removed(self):
        t = _r("standards/tech-rules.md")
        self.assertNotIn("## 四、RD 自查规范", t)
        self.assertNotIn("## RD 自查报告", t)

    def test_rescued_real_rules_retained(self):
        self.assertIn("Build 必须跑通", _r("standards/tech-rules.md"))
        self.assertIn("worktree lazy-install", _r("docs/conventions.md"))

    def test_designer_self_check_retained(self):
        t = _r("stages/ui-design-stage.md")          # v8.331:§四B 迁附录
        self.assertIn("Designer 自查规范", t)
        self.assertIn("Designer 自查报告", t)

    def test_framework_specific_retained(self):
        self.assertIn("两层脚本结构", _r("standards/scripts-policy.md"))
        self.assertIn("临时产物目录", _r("docs/conventions.md"))
        self.assertIn("权威源单源", _r("standards/tech-rules.md"))

    def test_inbound_anchors_survive(self):
        """外部引用的锚点不得断链(载体合并后的新锚)。"""
        self.assertIn("12.48 临时产物目录", _r("docs/conventions.md"))
        self.assertIn("Mermaid", _r("standards/tech-rules.md"))
        self.assertIn("附录 · Designer 自查规范", _r("stages/ui-design-stage.md"))

    def test_slimmed(self):
        files = sorted(f.name for f in STD.glob("*.md"))
        self.assertEqual(files, ["external-model-usage.md", "scripts-policy.md", "tech-rules.md"])


class TestBackendSlimming(unittest.TestCase):
    def setUp(self):
        self.t = _r("standards/tech-rules.md")

    def test_tdd_prescription_removed(self):
        self.assertNotIn("tdd.md", self.t)
        self.assertIn("只管结果不规定手段", self.t)

    def test_counter_default_rules_retained(self):
        """🔴 逆模型默认的规则 = 最高价值 · 一条不能砍(FK / 降级 WARN)。"""
        self.assertIn("默认避免", self.t)
        self.assertIn("FOREIGN KEY", self.t)
        self.assertIn("降级/兜底", self.t)

    def test_project_specific_conventions_retained(self):
        self.assertIn("统一响应格式", self.t)
        self.assertIn("业务状态码", self.t)
        self.assertIn("日志 CR 门", self.t)
        self.assertIn("迁移文件命名与起号纪律", _r("docs/conventions.md"))


class TestStandardsTotal(unittest.TestCase):
    def test_total_reduced(self):
        # v8.331:三文件合一 · standards 总量守恒锁在 test_hard_rules_v8286(<560)
        total = sum(len((STD / f.name).read_text(encoding="utf-8").splitlines())
                    for f in STD.glob("*.md"))
        self.assertLess(total, 560, f"standards 总量应 <560 行 · 现 {total}")


class TestFourSectionRollout(unittest.TestCase):
    """v8.285:四段结构推广完成 —— 防「标准说 X · 文件做 Y」再次发生(v8.284 根因)。"""

    STAGES = Path(__file__).resolve().parent.parent.parent / "stages"
    # 记录在案的例外(STAGES.md §3 明写):ship = 命令序列操作手册 · blueprint-lite = 已废弃
    EXEMPT = {"ship-stage.md", "blueprint-lite-stage.md"}

    def test_all_stages_follow_four_section(self):
        missing = []
        for f in sorted(self.STAGES.glob("*-stage.md")):
            if f.name in self.EXEMPT:
                continue
            t = f.read_text(encoding="utf-8")
            if "## ① 目标" not in t or "## ② 硬规则" not in t:
                missing.append(f.name)
        self.assertEqual(missing, [], f"未按 STAGES.md §3 四段结构:{missing}")

    def test_old_structure_gone_except_exempt(self):
        offenders = []
        for f in sorted(self.STAGES.glob("*-stage.md")):
            if f.name in self.EXEMPT:
                continue
            t = f.read_text(encoding="utf-8")
            if "\n## 怎么做" in t or "\n## 质量基线" in t:
                offenders.append(f.name)
        self.assertEqual(offenders, [], f"仍带旧结构段:{offenders}")

    def test_exemptions_documented_in_standard(self):
        """例外必须写在 STAGES.md 里 —— 不许有沉默的例外。"""
        s = (self.STAGES.parent / "STAGES.md").read_text(encoding="utf-8")
        self.assertIn("ship-stage.md", s)
        self.assertIn("例外", s)
