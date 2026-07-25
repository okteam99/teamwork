"""v8.285:standards 减法 —— 砍「模型默认就会」的标准做法,留「逆默认 / 不可能知道」的。

判据(用户讨论后确立):一条规则的价值 = **它与模型默认行为的距离**
- 模型默认就会(TDD/SOLID/命名/mermaid 语法/REST)→ 零价值 · 纯注意力税
- 模型不可能知道(本框架脚本两层结构 / 状态码表 / scratch 路径约定)→ 高价值(信息)
- 模型**默认会做反的**(避免 FK / 兜底算 ROI / 降级必打 WARN)→ **最高价值** · 且模型越强越需要
"""
import unittest
from pathlib import Path

STD = Path(__file__).resolve().parent.parent.parent / "standards"


class TestCommonSlimming(unittest.TestCase):
    def setUp(self):
        self.t = (STD / "common.md").read_text(encoding="utf-8")

    def test_rd_self_check_ceremony_removed(self):
        """216 行 RD 自查规范 + 报告模板已删:零机器消费者 · 零文档引用 · 与 tech.md 完工自查重复。"""
        self.assertNotIn("## 四、RD 自查规范", self.t)
        self.assertNotIn("## RD 自查报告", self.t)

    def test_rescued_real_rules_retained(self):
        """但从中抢救的两条真规则必须还在(证据类硬门 + 真踩坑)。"""
        self.assertIn("Build 必须跑通", self.t)
        self.assertIn("worktree lazy-install", self.t)

    def test_designer_self_check_retained(self):
        """Designer 自查**有机器校验**(verify-panorama.py SELF_CHECK_HEADER)→ 判据① 保留。"""
        self.assertIn("四B、Designer 自查规范", self.t)
        self.assertIn("Designer 自查报告", self.t)

    def test_framework_specific_retained(self):
        """模型不可能知道的框架约定 → 保留。"""
        for k in ("测试脚本约定", "临时产物目录", "权威源单源规则"):
            self.assertIn(k, self.t, f"框架特有约定丢失:{k}")

    def test_inbound_anchors_survive(self):
        """外部引用的锚点不得断链(prd.md→§五 · verify-panorama→§四B · ship/conventions→§六)。"""
        for anchor in ("五、文档流程图规范", "四B、Designer 自查规范", "六、临时产物目录"):
            self.assertIn(anchor, self.t, f"锚点断链:{anchor}")

    def test_slimmed(self):
        self.assertLess(len(self.t.splitlines()), 400, "common.md 应已从 767 瘦到 400 行内")


class TestBackendSlimming(unittest.TestCase):
    def setUp(self):
        self.t = (STD / "backend.md").read_text(encoding="utf-8")

    def test_tdd_single_sourced(self):
        """通用 TDD 手艺单源 tdd.md(tdd.md 本就声明整段吸收本节)。"""
        self.assertIn("单源 [tdd.md](./tdd.md)", self.t)

    def test_counter_default_rules_retained(self):
        """🔴 逆模型默认的规则 = 最高价值 · 一条不能砍。

        FK:模型训练默认「加 FK 保证引用完整性」(教科书)· 本框架明确逆着走 —— 模型越强越自信,
        越需要这条。降级必打 WARN 同理(模型默认静默 fallback)。
        """
        self.assertIn("默认避免", self.t)
        self.assertIn("FOREIGN KEY", self.t)
        self.assertIn("降级/兜底", self.t)

    def test_project_specific_conventions_retained(self):
        """模型猜不到的项目约定 → 保留。"""
        for k in ("统一响应格式", "业务状态码", "迁移文件规则", "非预期分支日志"):
            self.assertIn(k, self.t, f"约定丢失:{k}")


class TestStandardsTotal(unittest.TestCase):
    def test_total_reduced(self):
        total = sum(len((STD / f).read_text(encoding="utf-8").splitlines())
                    for f in ("common.md", "backend.md", "frontend.md", "tdd.md"))
        self.assertLess(total, 1450, f"四件 standards 应已从 1773 瘦下来 · 现 {total}")


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
