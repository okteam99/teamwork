"""v8.291:跨厂商异质模型评审彻底退役 —— 第三视角唯一形态 = 错开模型 subagent 冷审。

用户拍板理由:codex / gemini CLI 冷启动 + 安全审查慢路径 + 登录/网络/MCP 故障面,
实测严重拖慢流程(台账:codex exec 挂死 98m · "Additional safety checks" 慢路径)。
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS = ROOT / "tools"


class TestMachineryRemoved(unittest.TestCase):
    def test_cli_helpers_gone(self):
        import state
        for fn in ("_preflight_external", "_external_timeout_sec", "_detect_cli_version",
                   "_check_external_review_quality", "_read_disable_external_review"):
            self.assertFalse(hasattr(state, fn), f"跨厂商机械残留:{fn}")

    def test_config_option_retired(self):
        import bootstrap
        import _v8_stage_specs as S
        self.assertNotIn("disable_external_review", bootstrap.LOCALCONFIG_CONFIG_DEFAULTS)
        self.assertFalse(hasattr(S, "_localconfig_disable_external"))

    def test_codex_agents_dir_gone(self):
        self.assertFalse((ROOT / "codex-agents").exists())

    def test_command_has_no_cross_vendor_flags(self):
        import state, inspect
        src = inspect.getsource(state.cmd_external_review)
        for tok in ("subprocess.Popen", "codex exec", "--strict-mcp-config"):
            self.assertNotIn(tok, src, f"命令仍在 exec CLI:{tok}")


class TestSubagentContractEnforced(unittest.TestCase):
    """新契约:隔离 subagent + 照实申报模型 + yolo 实跑证据。"""

    def test_gate_requires_subagent_and_model(self):
        import _v8_stage_specs as S
        src = S._evidence_external_review_artifact.__doc__ or ""
        self.assertIn("隔离 subagent", src)
        self.assertIn("照实申报模型", src)

    def test_yolo_non_internalization_preserved(self):
        """v8.67 不内化律必须存活(换代证据 = prompt doc)—— 这是判据①,不随机械退役。"""
        import inspect, _v8_stage_specs as S
        src = inspect.getsource(S._evidence_external_review_artifact)
        self.assertIn("yolo", src)
        self.assertIn("_external_run_log_exists", src)


class TestDocsConsistent(unittest.TestCase):
    def test_adjudication_discipline_survived(self):
        """§裁决纪律与模型无关 · 被 5 处引用 · 必须存活。"""
        t = (ROOT / "standards" / "external-model-usage.md").read_text(encoding="utf-8")
        for k in ("裁决三态", "举证责任对称", "默认姿态 = 质疑", "安全加固 / 兜底降级"):
            self.assertIn(k, t, f"裁决纪律丢失:{k}")

    def test_no_stale_optout_references(self):
        """全库不得再出现 disable_external_review 作为活配置(只允许退役说明)。"""
        bad = []
        for f in (list(ROOT.rglob("*.md")) + list(ROOT.rglob("*.py"))
                  + list(ROOT.rglob("*.json"))):   # v8.293:漏 .json 让模板里的活配置躲过一版
            if "CHANGELOG" in f.name or "RETRO" in f.name or f.name.startswith("test_"):
                continue
            for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if "disable_external_review" in line and "退役" not in line:
                    bad.append(f"{f.relative_to(ROOT)}:{i}")
        self.assertEqual(bad, [], f"仍把 disable_external_review 当活配置:{bad}")

    def test_single_form_documented(self):
        t = (ROOT / "standards" / "external-model-usage.md").read_text(encoding="utf-8")
        self.assertIn("唯一形态", t)
        self.assertIn("不 exec 任何子进程", t)
