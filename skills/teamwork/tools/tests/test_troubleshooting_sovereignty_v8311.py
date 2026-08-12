"""v8.311:TROUBLESHOOTING 收归用户主权(用户裁定:AI 不在流程中改它 · AI 可以自动改 KNOWLEDGE)。

实况:框架有两处明确指示 AI 写它(SKILL「连法缺失 → 补进它」· feature-planning 同款),
且 conventions §13 清单里它**没标维护方** —— 旁边 DEV-RULES/UI-RULES 都标了「人维护」,
它和 GLOSSARY 裸着 · **归类本身就是漏的**(没归类的文件,写入权默认漂向 AI)。

裁定后的分工(镜像 DEV-RULES 模式):
- TROUBLESHOOTING = **人维护运维手册**(连接方式 / 操作步骤 · 用户按项目栈填)· AI 只读 + 提示;
- AI 实操中发现/摸索出的连法 → 记 **KNOWLEDGE**(AI 沉淀 · 用户裁定明确保留 AI 写权)
  + **提示用户**固化进 TROUBLESHOOTING · 不代写;
- bootstrap 建空骨架不算写内容(DEV-RULES/UI-RULES 同款 · 骨架≠内容)。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
HISTORY = {"docs/CHANGELOG.md", "docs/CHANGELOG-ARCHIVE.md", "docs/RETRO-LEDGER.md"}

WRITE_VERBS = re.compile(r"补进|写进|写入|更新进|追加进|沉淀进|append")
EXEMPT = re.compile(r"提示用户|不代写|不在流程中")


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class TestNoAiWritePathRemains(unittest.TestCase):

    def test_no_spec_instructs_ai_to_write_troubleshooting(self):
        """🔴 机器门:任何 spec 行「TROUBLESHOOTING + 写动词」而无「提示用户/不代写」豁免 → 红。

        原两处违例(SKILL:496 / feature-planning:78)都写着「连法缺失 → 补进」——
        指示 AI 写用户主权文件。
        """
        offenders = []
        for p in ROOT.rglob("*.md"):
            if "pytest_cache" in str(p) or str(p.relative_to(ROOT)) in HISTORY:
                continue
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if "TROUBLESHOOTING" in line and WRITE_VERBS.search(line) \
                        and not EXEMPT.search(line):
                    offenders.append(f"{p.relative_to(ROOT)}:{i}")
        self.assertEqual(offenders, [], f"仍有指示 AI 写 TROUBLESHOOTING 的条文:{offenders}")


class TestClassificationExplicit(unittest.TestCase):
    """归类要显式 —— 没归类的文件写入权会默认漂向 AI。"""

    def test_conventions_marks_human_maintained(self):
        t = _read("docs/conventions.md")
        self.assertIn("`TROUBLESHOOTING.md`(**人维护**", t,
                      "conventions §13 清单未标维护方(DEV-RULES/UI-RULES 都标了)")

    def test_skill_doc_table_marks_it(self):
        t = _read("SKILL.md")
        self.assertIn("人维护 · AI 不代写**) |", t)

    def test_template_header_states_sovereignty_and_redirect(self):
        t = _read("templates/troubleshooting.md")
        self.assertIn("人维护", t)
        self.assertIn("AI 不在流程中代写", t)
        self.assertIn("KNOWLEDGE.md", t, "缺转记路径 —— AI 摸出的连法要有地方去,否则丢失")

    def test_knowledge_boundary_table_has_the_row(self):
        """KNOWLEDGE 边界表是「什么写哪」的单源 —— 运维连法这行此前缺失。"""
        t = _read("templates/knowledge.md")
        self.assertIn("TROUBLESHOOTING.md", t)
        self.assertIn("运维操作步骤", t)


class TestRedirectFlowConsistent(unittest.TestCase):
    """两处原违例改成同一条转记流:记 KNOWLEDGE(AI 沉淀)+ 提示用户固化。"""

    def test_skill_redirect(self):
        t = _read("SKILL.md")
        i = t.index("AI 自己需连环境")
        seg = t[i:i + 400]
        self.assertIn("KNOWLEDGE.md", seg)
        self.assertIn("提示用户", seg)
        self.assertIn("不代写", seg)

    def test_feature_planning_redirect(self):
        t = _read("docs/feature-planning.md")
        i = t.index("调研需 live 环境数据")
        seg = t[i:i + 400]
        self.assertIn("KNOWLEDGE.md", seg)
        self.assertIn("提示用户", seg)

    def test_knowledge_stays_ai_writable(self):
        """用户裁定的另一半:KNOWLEDGE 保持 AI 可自动写 —— 防收权时把它一起误收。"""
        t = _read("templates/knowledge.md")
        self.assertIn("AI 沉淀", t)
        self.assertIn("写入硬时机", t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
