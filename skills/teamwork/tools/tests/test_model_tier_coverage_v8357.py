"""v8.357 · 档位覆盖:不要用高档模型做底智商任务(用户拍板)。

起因(aon-main DEV-F260910162653):用户问「你做测试用的是什么模型」,那边 AI 答
「实现路继承 Fable 5.1 · 验证档任务用 sonnet · 正式测试证据另派 sonnet」—— **完全合规**,
因为 SKILL 的白名单本来就写着「执行测试 · 单测 · 集成测试 · e2e」降验证档。
用户接连拍板:「涉及测试的都降档」→「测试和验证类任务都要降档」→「你全局检查下,
不需要用高档模型做底智商任务」→「ship 也用验证档模型」→「micro 默认使用执行档」。

🔴 全局扫描查出的真缺口(不是「没写规则」,是**规则没覆盖到的面**):
  ① **白名单只管派发时定档,管不到已派出的执行型 agent 内部做什么** ——
     实现路继承主模型,却在里面跑全量 vitest + 变异验证 = 拿深度档干机械活;
  ② **test-stage 零档位声明**(browser-e2e 有、test 没有)—— 整个 stage 就是
     「把实现说好了变成机器可验的证据」,却默认继承会话主模型,是最大的漏口;
  ③ **execute-stage 零声明** —— micro 的准入白名单已经把改动卡死成零逻辑变更
     (文案/样式/常量),门槛最低的 stage 反而没有档位约束;
  ④ **ship-stage 零声明** —— push/MR/合入监控/CI 日志/归档誊抄全是搬运活;
  ⑤ **一处真冲突**:白名单写「冷审执行」降验证档,而 goal/blueprint 写
     「冷审必用主模型 · 不许降到验证档」—— 两条硬规则直接打架。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class TestThreeTiersHaveOneDefinition(unittest.TestCase):
    """档位枚举必须单源 —— 两套定义 = 两套理解(本 session 反复的教训)。"""

    def test_tier_enum_declared_once(self):
        hits = []
        for f in list((ROOT / "stages").glob("*.md")) + list((ROOT / "standards").glob("*.md")) \
                + [ROOT / "SKILL.md"] + list((ROOT / "tools").glob("*.py")):
            hits += re.findall(r"tier=<[^>]*>", f.read_text(encoding="utf-8", errors="replace"))
        self.assertTrue(hits, "档位枚举消失了")
        self.assertEqual(set(hits), {"tier=<验证|执行|深度>"}, f"出现第二套档位定义:{set(hits)}")

    def test_each_tier_has_a_decidable_criterion(self):
        """🔴 判据必须可判 —— 「校验/枚举型 vs 判断/创造型」是形容词式分类,分不了界。"""
        sk = _read("SKILL.md")
        self.assertIn("照着已有清单核对", sk)
        self.assertIn("按既定方案把东西写出来", sk)
        self.assertIn("要想出清单上没有的东西", sk)

    def test_execution_tier_is_no_longer_missing_from_the_criterion(self):
        """三档里「执行」原先在判据中根本没出现(只有验证/不降档两极)。"""
        seg = re.search(r"定档判据\(三档各一句\)[^\n]*", _read("SKILL.md"))
        self.assertIsNotNone(seg)
        self.assertIn("`执行`", seg.group(0))


class TestWhitelistNamingAndScope(unittest.TestCase):
    def test_whitelist_names_tests_explicitly(self):
        """原名「验证类白名单」—— 用户问的是「测试」,名字让人以为不管测试。"""
        self.assertIn("测试与验证类白名单", _read("SKILL.md"))

    def test_whitelist_covers_the_mechanical_test_work(self):
        sk = _read("SKILL.md")
        for item in ("变异验证", "全量套件跑批", "基线/指纹采集", "覆盖率统计"):
            self.assertIn(item, sk, f"白名单漏了 {item}")

    def test_cold_review_conflict_is_resolved(self):
        """🔴 白名单曾写「冷审执行」降验证档,而 goal/blueprint 写「冷审不许降」。"""
        sk = _read("SKILL.md")
        self.assertNotIn("冷审执行", sk, "仍与 goal/blueprint 的「冷审必用主模型」冲突")
        self.assertIn("冷审验证轮", sk)
        self.assertIn("首轮全量冷审属判断型,不降", sk)
        # 另一侧照旧成立
        for rel in ("stages/goal-stage.md", "stages/blueprint-stage.md"):
            self.assertIn("不许降到验证档", _read(rel), f"{rel} 的高档要求丢了")


class TestInlineWorkHasABoundary(unittest.TestCase):
    """白名单只管派发时定档 —— 已派出的执行型 agent 内部做什么,得另有边界。"""

    def test_skill_states_the_inline_boundary(self):
        sk = _read("SKILL.md")
        self.assertIn("执行型 subagent 的内联测试有边界", sk)
        self.assertIn("最小自测", sk)
        for item in ("全量套件", "变异验证", "正式测试证据"):
            self.assertIn(item, sk, f"边界没点名 {item}")

    def test_dev_stage_points_at_the_single_source(self):
        dev = _read("stages/dev-stage.md")
        self.assertIn("模型档位不自定", dev, "dev 的「测试节奏 AI 自定」会被读成档位也自定")
        self.assertIn("另派验证档", dev)


class TestEveryMechanicalStageDeclaresItsTier(unittest.TestCase):
    """🔴 用户拍板「不需要用高档模型做底智商任务」—— 逐 stage 对账,不靠印象。"""

    MECHANICAL = {
        "stages/test-stage.md": "测试与验证类",
        "stages/ship-stage.md": "验证档",
        "stages/browser-e2e-stage.md": "验证档",
        "stages/execute-stage.md": "执行档",
    }
    # 判断型:要想出清单上没有的东西 —— 降档会直接伤产出
    JUDGEMENT = ("stages/diagnose-stage.md", "stages/ui-design-stage.md",
                 "stages/pm-acceptance-stage.md")

    def test_mechanical_stages_declare_a_tier(self):
        for rel, kw in self.MECHANICAL.items():
            t = _read(rel)
            self.assertIn("🎚️", t, f"{rel} 缺档位声明 —— 默认继承会话主模型")
            self.assertIn(kw, t, f"{rel} 的档位声明没点名 {kw}")

    def test_judgement_stages_are_not_downgraded(self):
        for rel in self.JUDGEMENT:
            self.assertNotIn("默认验证档", _read(rel), f"{rel} 是判断型 · 不该降档")

    def test_micro_is_execution_not_verification(self):
        """micro 改的是文案/常量,但那仍是「写出来」—— 按判据归执行档(用户拍板)。"""
        t = _read("stages/execute-stage.md")
        self.assertIn("默认执行档", t)
        self.assertNotIn("默认验证档", t)
        self.assertIn("不归验证档", t, "没说清为什么不是验证档 · 下次会被改回去")

    def test_ship_keeps_the_implementation_exception(self):
        """ship 降验证档,但 CI 红要改代码那段是实现活 —— 例外必须写明,否则会用验证档写代码。"""
        t = _read("stages/ship-stage.md")
        self.assertIn("CI 红", t)
        self.assertIn("按实现路的档走", t)


class TestRuleLivesInTheFrameworkNotAProjectMemory(unittest.TestCase):
    """🔴 载体归位:模型分档是**框架级**规则。

    起因 case 里,那边的 AI 把用户拍板写进了 `~/.claude/projects/<项目>/memory/` ——
    换个项目就失效,下个项目的 AI 还会把同样的问题再问用户一遍。
    """

    def test_tier_rules_are_in_skill_and_stages(self):
        self.assertIn("测试与验证类白名单", _read("SKILL.md"))
        self.assertIn("🎚️", _read("stages/test-stage.md"))

    def test_red_budget_and_gates_respected(self):
        sk = _read("SKILL.md")
        self.assertLess(sk.count("🔴"), 55, "SKILL 🔴 密度门")


if __name__ == "__main__":
    unittest.main()
