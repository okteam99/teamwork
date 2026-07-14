"""v8.241:退役词表回归网(全库文档审计的制度化产物)。

背景:五次大改版(v8.204 外审默认反转 / v8.211 注入退役 / v8.219 四段化 /
v8.220-223 流程收缩 / v8.233-234 ship 终点)各留扫尾债 · 一次审计清出 83 处。
本测试把「版本收缩后的旧词表残留」变成 pre-push 硬门:退役词只允许出现在
带 legacy 标注的句子里(当句白名单)· 新增裸残留 = 测试红。
"""
import re
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent.parent

# 退役词 → 编译后的模式(Micro 用英文边界防误伤 microservice 等)
RETIRED_PATTERNS = {
    "敏捷需求": re.compile("敏捷需求"),
    "Micro": re.compile(r"(?<![A-Za-z0-9_-])Micro(?![A-Za-z0-9_])"),
    "blueprint_lite": re.compile(r"blueprint[_-]lite"),
    "teamwork_version": re.compile(r"teamwork_version"),
    "Goal-Plan": re.compile(r"Goal-Plan"),
}

# 当句含任一标记 = 合法 legacy 标注/机器内部键说明 · 放行
LINE_WHITELIST = re.compile(
    "legacy|存量|退役|已并入|DEPRECATED|向前兼容|不再产|别名"
    "|_flow_key|内部键|LEGACY_FLOW_ALIASES|M 已退役|M 为"
)

SCAN_GLOBS = [
    "SKILL.md", "FLOWS.md",
    "docs/prepare.md", "docs/conventions.md", "docs/feature-planning.md",
    "docs/teamwork-space-guide.md",
    "stages/*.md", "templates/*.md", "roles/*.md", "agents/*.md",
]

# 整文件豁免:存量 in-flight 服务文件(v8.223 已知保留项)
FILE_EXEMPT = {"blueprint-lite-stage.md"}


class TestRetiredVocabSweep(unittest.TestCase):
    def test_no_bare_retired_vocab(self):
        offenders: list[str] = []
        for pattern in SCAN_GLOBS:
            for f in sorted(SKILL_ROOT.glob(pattern)):
                if f.name in FILE_EXEMPT:
                    continue
                for lineno, line in enumerate(
                        f.read_text(encoding="utf-8").splitlines(), 1):
                    if LINE_WHITELIST.search(line):
                        continue
                    for word, rx in RETIRED_PATTERNS.items():
                        if rx.search(line):
                            offenders.append(
                                f"{f.relative_to(SKILL_ROOT)}:{lineno} [{word}] {line.strip()[:100]}")
        self.assertEqual(
            offenders, [],
            "退役词裸残留(当句无 legacy 标注):\n" + "\n".join(offenders)
            + "\n→ 要么改成现行词表(Feature/Bug + preset)· 要么在当句加 legacy/存量 标注")


if __name__ == "__main__":
    unittest.main()
