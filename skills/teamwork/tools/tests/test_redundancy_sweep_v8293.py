"""v8.293:全库冗余清理 —— 死代码不复活 · 退役声明与正文不打架。

本轮清的三类冗余(判据:是否还有消费者 / 是否与现行规则矛盾 / 是否同一教义写多遍):
  ① 死岛 —— v8.291 砍 external CLI 入口时只砍了 cmd_external_review,被调链整座留下(state.py 586 行);
  ② 退役声明贴在头上、正文一字未改(roles/external-reviewer.md · stages/review-stage.md 硬规则 1);
  ③ 同一批教义在一个文件里写三遍(external-model-usage.md §二)。
断言都对**实质**不对措辞(RETRO 教训:锁字面的测试会在下一次改写时假红)。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


class TestDeadIslandGone(unittest.TestCase):
    """v8.291 退役的跨厂商 CLI 机械 —— 入口和被调链都不该留。"""

    def test_state_py_cli_runners_gone(self):
        src = (ROOT / "tools" / "state.py").read_text(encoding="utf-8")
        for name in ("_build_codex_prompt", "_run_codex_review", "_run_claude_review",
                     "_build_claude_review_cmd", "_run_streamed_to_log", "_detect_host",
                     "_ack_block", "_review_ack_status", "_prompt_doc_stale_reason",
                     "_build_verify_fixes_block", "EXTERNAL_HOST_TO_MODEL",
                     "EXTERNAL_REVIEW_TIMEOUT_SEC", "_FINDING_POSTURE_HINT"):
            self.assertNotIn(f"def {name}", src, f"死函数复活:{name}")
            self.assertNotIn(f"\n{name} = ", src, f"死常量复活:{name}")

    def test_scaffold_command_gone(self):
        """scaffold-review-prompt:零文档引用 · 用途已被 external-review 自写 prompt-doc 取代。"""
        src = (ROOT / "tools" / "state.py").read_text(encoding="utf-8")
        self.assertNotIn("cmd_scaffold_review_prompt", src)
        self.assertNotIn("SCAFFOLD_PROMPT_DOC_TEMPLATE", src)

    def test_hetero_checker_and_its_constants_gone(self):
        """🔴 EXTERNAL_REVIEW_SAME_CONTEXT_BLOCKED 把 "subagent" 列为必 BLOCK ——

        而 v8.291 后 subagent 恰是唯一合法形态。这块常量留着就是雷:任何人重新接上
        这个 checker,拦的就是唯一支持的路径。
        """
        src = (ROOT / "tools" / "_v8_stage_specs.py").read_text(encoding="utf-8")
        for name in ("_check_external_hetero", "_host_to_family",
                     "EXTERNAL_REVIEW_HETERO_KEYWORDS", "EXTERNAL_REVIEW_SAME_CONTEXT_BLOCKED",
                     "_MODEL_FAMILY_KEYWORDS"):
            self.assertNotIn(name, src, f"连锁孤儿复活:{name}")

    def test_no_dangling_references_to_deleted_symbols(self):
        """删函数最常见的伤:调用点没跟着删。"""
        for f in ("tools/state.py", "tools/_v8_stage_specs.py", "tools/_v8_engine.py"):
            src = (ROOT / f).read_text(encoding="utf-8")
            self.assertNotIn("EXTERNAL_STAGE_TO_PROFILE[", src, f"{f} 仍在用已删的 dict")


class TestRetirementNoticesMatchBody(unittest.TestCase):
    """头上贴退役声明、正文照旧 —— 本轮抓到两处,不许复发。"""

    def test_external_reviewer_role_body_is_current(self):
        t = (ROOT / "roles" / "external-reviewer.md").read_text(encoding="utf-8")
        # 正文不该再写「claude 主时调 codex」「OpenAI ToS」「文件名必含 codex/gemini 字面」
        self.assertNotIn("ToS", t, "仍写着跨厂商合规条款")
        self.assertNotIn("claude 主时调 codex", t)
        self.assertNotIn("白名单模型字面", t)
        # 该说的仍在:错开模型 + 隔离 subagent + 不喂起草心路
        self.assertIn("subagent", t)
        self.assertIn("≠", t, "缺「model ≠ 会话主模型」不变式")

    def test_review_stage_rule1_matches_rule10(self):
        """v8.289 退役 REVIEW-<role>.md —— 硬规则 1 曾还在要求各自落该文件,与规则 10 直接打架。"""
        t = (ROOT / "stages" / "review-stage.md").read_text(encoding="utf-8")
        rules = [l for l in t.splitlines() if l.startswith("1. **评审独立性**")]
        self.assertEqual(len(rules), 1, "硬规则 1 缺失")
        self.assertNotIn("REVIEW-{role}.md", rules[0], "硬规则 1 仍要求产出已退役的 per-role 文件")
        self.assertIn("REVIEW.md", rules[0])

    def test_review_stage_rule_numbers_unique(self):
        """曾出现两个 8(退役条目替换时没重排)—— 编号重复让「规则 N」的互指失效。"""
        t = (ROOT / "stages" / "review-stage.md").read_text(encoding="utf-8")
        nums = re.findall(r"^(\d+)\. ", t, re.M)
        self.assertEqual(len(nums), len(set(nums)), f"硬规则编号有重复:{nums}")

    def test_no_retired_cli_flags_in_flow_docs(self):
        """--preflight / --self-review-fallback 是 v8.291 删掉的 CLI 机械。"""
        bad = []
        for f in list((ROOT / "stages").glob("*.md")) + list((ROOT / "roles").glob("*.md")) \
                + list((ROOT / "templates").glob("*.md")) + list((ROOT / "templates").glob("*.json")):
            for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if "退役" in line or "已删" in line:
                    continue
                if "--self-review-fallback" in line or "--preflight" in line:
                    bad.append(f"{f.relative_to(ROOT)}:{i}")
        self.assertEqual(bad, [], f"流程文档仍挂着已删的 CLI flag:{bad}")


class TestSectionRefsResolve(unittest.TestCase):
    """指针必须指向真实存在的章节 —— §11/§十一/§12 在 v8.291 精简后已不存在。"""

    def test_external_model_usage_headings_self_consistent(self):
        t = (ROOT / "standards" / "external-model-usage.md").read_text(encoding="utf-8")
        self.assertIn("## 二、裁决纪律", t)
        # 二级标题是「二」· 三级子节就不能还叫 12.x
        self.assertNotIn("### 12.", t, "章节号自相矛盾(§二 下挂 12.x)")

    def test_inbound_refs_point_at_existing_sections(self):
        headings = (ROOT / "standards" / "external-model-usage.md").read_text(encoding="utf-8")
        bad = []
        for f in list(ROOT.rglob("*.md")) + list(ROOT.rglob("*.py")):
            rel = str(f.relative_to(ROOT))
            if "CHANGELOG" in rel or "RETRO" in rel or "docs/audit" in rel or f.name.startswith("test_"):
                continue
            txt = f.read_text(encoding="utf-8", errors="replace")
            # 只认「§ + 中文数字/阿拉伯数字」这一种章节记法 · 后面的 markdown 语法不算
            for m in re.finditer(r"external-model-usage(?:\.md)?[^\n]{0,40}?§([一二三四五六七八九十百]+|[\d.]+)", txt):
                sec = m.group(1)
                if sec in ("一", "二"):
                    continue
                bad.append(f"{rel} → §{sec}")
        self.assertEqual(bad, [], f"引用了不存在的章节(现只有 §一 / §二):{bad}")
        self.assertIn("## 一、", headings)


class TestTddMeansRemovedEverywhere(unittest.TestCase):
    """v8.287:框架只管结果不规定 TDD 手段 —— 模板里曾留着红绿词表与凭空的覆盖率阈值。"""

    def test_tc_template_has_no_tdd_gate(self):
        t = (ROOT / "templates" / "tc.md").read_text(encoding="utf-8")
        self.assertNotIn("测试先于实现", t, "TC 模板仍规定 TDD 手段")
        self.assertNotIn("后端覆盖率", t, "凭空造的阈值(standards/backend.md 里根本没有)")

    def test_tech_template_step_table_has_no_red_green(self):
        t = (ROOT / "templates" / "tech.md").read_text(encoding="utf-8")
        self.assertNotIn("🔴 Red / 🟢 Green", t, "实现步骤表仍是 TDD 词表(与同节「节奏 AI 自定」矛盾)")




class TestAgileLegacyGone(unittest.TestCase):
    """v8.293:「敏捷需求」/ lite / blueprint_lite 整条 legacy 删除。

    删的理由不是「没人用」,是**三份 flow-key 实现对同一输入解析出不同的转移图**:
    state.py → Feature+full(无 blueprint_lite 的图)· _v8_engine.py → Feature+lite(含 blueprint_lite),
    而 engine 的注释还声称与 state.py「严格同口径」。三份实现无一被测到该输入。
    选边只是把分歧藏起来;lite 档 v8.223 已退役,链本身是 Feature 链的 needs-ui=false 剖面(纯冗余)。
    """

    CODE_FILES = ("tools/state.py", "tools/_v8_engine.py", "tools/_v8_stage_specs.py", "tools/_v8_ship.py")

    def test_no_agile_flow_in_code(self):
        for f in self.CODE_FILES:
            src = (ROOT / f).read_text(encoding="utf-8")
            for line in src.splitlines():
                if "v8.293" in line or "已删" in line or "整条" in line:
                    continue   # 退役说明放行
                self.assertNotIn("敏捷需求", line, f"{f} 仍有敏捷需求逻辑:{line.strip()[:70]}")
                self.assertNotIn("blueprint_lite", line, f"{f} 仍有 blueprint_lite:{line.strip()[:70]}")

    def test_lite_preset_fully_gone(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        from state import FEATURE_PRESETS, LEGACY_FLOW_ALIASES, FLOW_BY_TYPE  # type: ignore
        self.assertNotIn("lite", FEATURE_PRESETS)
        self.assertNotIn("敏捷需求", LEGACY_FLOW_ALIASES)
        self.assertNotIn("Feature:lite", FLOW_BY_TYPE)

    def test_three_flow_key_impls_agree(self):
        """三份实现必须对同一 state 给一致结论 —— 这正是 v8.293 之前失守的地方。"""
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        from state import internal_flow_key, resolve_flow_graph, FLOW_BY_TYPE  # type: ignore
        import _v8_engine as E      # type: ignore
        import _v8_stage_specs as S  # type: ignore
        for ft, pre in (("Feature", "full"), ("Feature", "micro"), ("Bug", "full"), ("Micro", "full")):
            st = {"flow_type": ft, "preset": pre}
            self.assertEqual(internal_flow_key(ft, pre), E._internal_flow_key(st),
                             f"state.py 与 engine 对 {st} 的内部键不一致")
            self.assertEqual(E._internal_flow_key(st), S._flow_key(st),
                             f"engine 与 specs 对 {st} 的内部键不一致")
            self.assertEqual(resolve_flow_graph(ft, pre), E._resolve_flow_graph(st, FLOW_BY_TYPE),
                             f"两份 resolve_flow_graph 对 {st} 解析出不同的图")

    def test_blueprint_lite_stage_doc_gone(self):
        self.assertFalse((ROOT / "stages" / "blueprint-lite-stage.md").exists())


class TestE2ERegistryRetired(unittest.TestCase):
    """e2e-registry:241 行模板 + ship distill 的 reg 槽位 —— 全库零入口(没有任何文档
    说 REG case 长什么样 / 放哪 / 怎么建),却在 ship 要求逐项申报。用户拍板整条退役。"""

    def test_template_and_distill_slot_gone(self):
        self.assertFalse((ROOT / "templates" / "e2e-registry.md").exists())
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        from _v8_ship import DISTILL_KEYS  # type: ignore
        self.assertNotIn("reg", DISTILL_KEYS)
        self.assertNotIn("reg", (ROOT / "stages" / "ship-stage.md").read_text(encoding="utf-8").split("--distill '{")[1].split("}'")[0])


class TestLocalconfigSingleSource(unittest.TestCase):
    """bootstrap 的默认值曾靠一句注释「🔴 与模板保持同步(新增字段两处都加)」——

    按框架自己的教义,靠自觉的同步该换成物化门。第三份副本(config.md 的 125 行字段文档)
    已删成指针;剩下这两份是代码与模板,机械对齐即可。
    """

    def test_bootstrap_defaults_match_template(self):
        import json, re
        tpl = json.loads((ROOT / "templates" / "teamwork_localconfig.json").read_text(encoding="utf-8"))
        src = (ROOT / "tools" / "bootstrap.py").read_text(encoding="utf-8")
        i = src.index("LOCALCONFIG_CONFIG_DEFAULTS = {")
        block = src[i:src.index("\n}", i)]
        code_keys = set(re.findall(r'^\s{4}"([a-z_]+)":', block, re.M))
        tpl_keys = {k for k in tpl if not k.startswith("_")}
        self.assertEqual(tpl_keys, code_keys,
                         f"localconfig 模板与 bootstrap 默认值漂移 · 只在模板 {sorted(tpl_keys-code_keys)} · "
                         f"只在代码 {sorted(code_keys-tpl_keys)}")


class TestUiContractMatchesTemplate(unittest.TestCase):
    """templates/ui.md 明令「视觉描述不在本文复述」,而 stage/role 曾要求 body 必含
    §页面列表/§交互流/§视觉规范/§字段映射 —— 模板里没有这四段。Designer 照哪边写都违反另一边。"""

    def test_no_phantom_sections_named(self):
        for f in ("stages/ui-design-stage.md", "roles/designer.md"):
            t = (ROOT / f).read_text(encoding="utf-8")
            for line in t.splitlines():
                if "v8.293" in line:
                    continue
                self.assertNotIn("§页面列表", line, f"{f} 点名模板里不存在的段")
                self.assertNotIn("§字段映射", line, f"{f} 点名模板里不存在的段")


class TestMarkdownFencesBalanced(unittest.TestCase):
    """v8.293 自伤实证:按 `## 标题` 切段时切掉了 adr-index.md 的围栏闭合(模板正文
    整个包在 ```markdown 里)。加这道门 —— 切文档一律回来验围栏。"""

    # HEAD 起就是奇数的(用 \\`\\`\\` 转义写法 / 单开围栏)· 不在本门范围
    # v8.307/308:backend(断栏已修)· frontend(重写零围栏)· common(§三/四B 压缩后配平)移出豁免收紧门
    KNOWN_ODD = {"bug-report.md", "project.md", "roadmap.md"}

    def test_edited_docs_have_balanced_fences(self):
        bad = []
        for d in ("templates", "stages", "roles", "standards"):
            for f in sorted((ROOT / d).glob("*.md")):
                if f.name in self.KNOWN_ODD:
                    continue
                n = sum(1 for l in f.read_text(encoding="utf-8").splitlines() if l.strip().startswith("```"))
                if n % 2:
                    bad.append(f"{d}/{f.name}({n})")
        self.assertEqual(bad, [], f"代码围栏未闭合(切段时截断?):{bad}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
