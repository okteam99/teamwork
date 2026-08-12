"""v8.298:档位错配门禁 —— 每个字段放在能承载它的载体上。

起因(v8.297 用户指出):耗时归因塞进台账单元格「写不下」。顺着这条线整体 review 流程文档,
把错配形态归成四类,并给「率/频次」这一族立了可机检的门。

  ① 叙述塞单行槽 —— 表格单元格要求写多维判断(v8.297 已修 · teamwork-space/pending 本就配了外迁纪律)
  ② 可算字段埋叙述 —— 要跨 feature 算账的数字混在自由文本里(本版修两处)
  ③ 只 emit 不落盘 —— 产物瞬时而消费方在事后(v8.297 已修 digest 四问)
  ④ 落盘但读不到 —— 落机器本地/未跟踪路径(v8.296 已退役 docs/audit)

🔴 本文件锁的是 ②:框架反复声明「消费方」与 kill criteria,但判据要成立,
**分子分母必须真能从台账取到**。取不出的判据 = 写着好看、年检算不出来。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
LEDGER = ROOT / "templates" / "process-ledger.md"


def _ledger_columns():
    header = next(l for l in LEDGER.read_text(encoding="utf-8").splitlines()
                  if l.startswith("| Feature |"))
    return [c.strip() for c in header.strip("|").split("|")]


class TestRateCriteriaHaveDataSource(unittest.TestCase):
    """每条「率 / 占比 / 频次」判据,分子分母都要有落点。"""

    # 判据 → 台账里承载它的列(列名子串)
    RATE_CRITERIA = {
        "external confirmed 率": "external",
        "角色真 finding 率": "角色真 finding",
        "暂停点 all-default 率": "暂停点",
        "起草可预防性": "起草可预防性",
        "协调开销占比": "耗时归因",
    }

    def test_each_rate_criterion_maps_to_a_column(self):
        cols = " | ".join(_ledger_columns())
        missing = [k for k, col in self.RATE_CRITERIA.items() if col not in cols]
        self.assertEqual(missing, [], f"这些判据在台账里没有承载列:{missing}")

    def test_pl_challenge_rate_is_extractable(self):
        """goal-stage 声明「PL-CHALLENGE 采纳率进台账」—— 曾无落点(列 7 示例只有 review 侧角色)。

        取不出 = 「长期零采纳 = 过场信号 · 收紧判据」这条 kill criteria 根本用不了。
        """
        t = LEDGER.read_text(encoding="utf-8")
        self.assertIn("pl", t.lower(), "台账未提及 pl 角色")
        self.assertIn("goal 侧", t, "未说明「角色真 finding」列要覆盖 goal 侧角色")
        self.assertIn("零也要写", t, "零值不写 → 「零 finding」与「没这个角色」分不开")
        g = (ROOT / "stages" / "goal-stage.md").read_text(encoding="utf-8")
        self.assertIn("角色真 finding", g, "goal-stage 的观测声明未落到具体列")

    def test_new_precedent_is_countable(self):
        """kill criteria 说「连续数月无新判例 → 流程仪式砍半」—— 判例是叙述,得能数。"""
        t = LEDGER.read_text(encoding="utf-8")
        self.assertIn("判例:", t, "台账未给「新判例」可 grep 的前缀约定")
        s = (ROOT / "stages" / "ship-stage.md").read_text(encoding="utf-8")
        self.assertIn("判例:", s, "kill criteria 未说明怎么数新判例")
        r = (ROOT / "templates" / "process-retro.md").read_text(encoding="utf-8")
        self.assertIn("判例:", r, "复盘模板未要求回填台账前缀 → 前缀永远不会出现")


class TestLedgerHoldsOnlyQueryableFields(unittest.TestCase):
    """台账装可算的,复盘装叙述的 —— 两边都要写明分工,否则下次又会塞错。"""

    def test_ledger_declares_what_does_not_belong(self):
        t = LEDGER.read_text(encoding="utf-8")
        self.assertIn("归因叙述不写这里", t)
        self.assertIn("process-retro.md", t, "台账未指向叙述的去处 = 只说不许,没说去哪")

    def test_retro_doc_declares_what_does_not_belong(self):
        t = (ROOT / "templates" / "process-retro.md").read_text(encoding="utf-8")
        self.assertIn("不写业务内容", t, "复盘未划清与业务复盘的边界 → 两份会混成一锅")

    def test_schema_discipline_still_intact(self):
        """修 ② 不许靠加列 —— 加列有成本(旧行留空),能用约定解决就不动 schema。"""
        cols = _ledger_columns()
        self.assertEqual(len(cols), 16, f"台账列数意外变化({len(cols)})· v8.298 应只改约定不加列")


class TestNoEmitOnlyDeliverables(unittest.TestCase):
    """③ 类:声明了事后消费方的产物,不能只存在于 emit 里。"""

    def test_digest_four_questions_are_persisted(self):
        s = (ROOT / "stages" / "ship-stage.md").read_text(encoding="utf-8")
        self.assertIn("四问同时写进流程复盘文档", s)

    def test_no_doc_claims_emit_only_for_annual_review_data(self):
        """扫一遍:凡声明「年检 / kill criteria」要用的产物,不得同时标「不落盘」。"""
        bad = []
        for d in ("stages", "templates", "docs"):
            for f in sorted((ROOT / d).glob("*.md")):
                # CHANGELOG / RETRO 是**历史记录不是现行规范** —— 它们本来就要描述被修掉的旧问题
                # (本门禁首跑就被自己的 v8.298 entry 拌了一跤)· 与全库其他扫描同约定
                if "CHANGELOG" in f.name or "RETRO" in f.name:
                    continue
                for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                    # 豁免按实质不按版本标(spec 已清版本标):引用旧反模式同时声明「同时写进」落盘的行不算
                    if ("年检" in line or "kill criteria" in line) and \
                       re.search(r"只 ?emit|仅 ?emit|不落盘", line) and "同时写进" not in line:
                        bad.append(f"{d}/{f.name}:{i}")
        self.assertEqual(bad, [], f"年检数据源被声明为只 emit 不落盘:{bad}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
