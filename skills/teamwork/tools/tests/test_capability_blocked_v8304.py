"""v8.304:区分「执行失败」与「评审失败」+ 回收零工具 reviewer profile。

实证(aon-core · 宿主 codex):goal 冷审派 `prd-reviewer` 后返回
`files_read: []` / `status: FAILED` / `no authorized read-only file access`,整个 goal 被阻断。

🔴 根因链(全部读文件核实):
  ① 被删的 `codex-agents/prd-reviewer.toml` **故意零工具** ——
     「READ-ONLY · Cannot write files via shell · Cannot execute commands」。
     因为**旧架构把待评审文件 inline 进 prompt**,reviewer 不需要自己读。
  ② 现配方只 inline 一部分:`STAGE_REVIEW_FILES` = goal→[PRD] · blueprint→[TC,TECH] · **review→[]**;
     **上游 WS 与真实代码从不 inline**。v8.291 改 subagent 冷审 + v8.303 立「读真实代码」硬要求
     → 零工具 profile **架构性不兼容**,不是配置没调好。
  ③ **v8.293 删了 skill 侧的源,却没写回收逻辑** —— 已部署副本留在用户项目里继续被宿主选中。
     bootstrap 只有 hook 的清理,没有 `.codex/agents/*.toml` 的。

修两侧:bootstrap **由部署改为回收**(签名守卫)· 门禁把这类失败判成 **CAPABILITY_BLOCKED**
并给处置指引 —— 旧门禁只报「产物不合规」,把**能力缺失说成评审问题**,用户被迫自己排查一轮。
"""
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import _v8_stage_specs as S  # noqa: E402

_STATE = {"current_stage": "goal", "stage_review_roles": {"goal": ["pl", "external"]}}


def _artifact(body: str):
    d = Path(tempfile.mkdtemp(prefix="tw-cap-v8304-"))
    ex = d / "external-cross-review"
    ex.mkdir()
    (ex / "goal-sonnet.md").write_text(body, encoding="utf-8")
    return S._evidence_external_review_artifact(_STATE, NS(feature=str(d)))


HEAD = "---\nreview_via: subagent\nreview_model: sonnet\n"


class TestCapabilityBlockedDetection(unittest.TestCase):

    def test_empty_files_read_is_blocked(self):
        ok, msg = _artifact(HEAD + "files_read: []\n---\n无法读取任何文件\n")
        self.assertFalse(ok)
        self.assertIn("CAPABILITY_BLOCKED", msg)

    def test_line_based_parser_string_form_also_caught(self):
        """🔴 `parse_frontmatter` 是**行式解析不是真 YAML** —— `files_read: []` 解析成字符串 `'[]'`。

        首版按 list 判空,实测**静默漏判**(该红的绿了)。判定必须对两种形态都成立。
        """
        from _v8_stage_specs import parse_frontmatter  # type: ignore
        d = Path(tempfile.mkdtemp()); f = d / "x.md"
        f.write_text(HEAD + "files_read: []\n---\nx\n", encoding="utf-8")
        self.assertIsInstance(parse_frontmatter(f).get("files_read"), str,
                              "解析器行为变了 —— 判定逻辑要跟着复核")
        self.assertFalse(_artifact(HEAD + "files_read: []\n---\nx\n")[0])

    def test_status_failed_is_blocked(self):
        ok, msg = _artifact(HEAD + "status: FAILED\n---\nx\n")
        self.assertFalse(ok)
        self.assertIn("CAPABILITY_BLOCKED", msg)

    def test_body_signature_is_blocked(self):
        ok, msg = _artifact(HEAD + "---\nno authorized read-only file access\n")
        self.assertFalse(ok)
        self.assertIn("CAPABILITY_BLOCKED", msg)

    def test_normal_review_passes(self):
        ok, _ = _artifact(HEAD + "files_read: [PRD.md, src/x.rs]\n---\n正常评审\n")
        self.assertTrue(ok, "正常产物被误判成能力缺失")

    def test_missing_field_is_backward_compatible(self):
        """🔴 `files_read` **缺失不算** —— 存量产物没这个字段。宁可漏判,不可把正常评审误判。"""
        ok, _ = _artifact(HEAD + "---\n旧产物无该字段\n")
        self.assertTrue(ok)

    def test_message_separates_execution_from_review_failure(self):
        """诊断信息是这条的全部价值:不说清「这不是 NEEDS_REVISION」,用户还得自己排查一轮。"""
        _, msg = _artifact(HEAD + "files_read: []\n---\nx\n")
        self.assertIn("执行失败", msg)
        self.assertIn("不是 NEEDS_REVISION", msg)
        self.assertIn("文件读取能力", msg, "未给处置方向")
        self.assertIn("预算没被消耗", msg,
                      "未说明轮次未计数 → 用户会以为浪费了一轮评审预算")


class TestLegacyProfileReclaimed(unittest.TestCase):
    """v8.293 删源却没回收已部署副本 —— 本 session 反复抓的形态,这次后果是**阻塞用户流程**。"""

    def _maintain(self, files: dict):
        from bootstrap import maintain_host_hooks  # type: ignore
        proj = Path(tempfile.mkdtemp(prefix="tw-reclaim-"))
        agents = proj / ".codex" / "agents"
        agents.mkdir(parents=True)
        for name, body in files.items():
            (agents / name).write_text(body, encoding="utf-8")
        return maintain_host_hooks(ROOT, proj, "codex-cli"), agents

    def test_signed_profiles_removed(self):
        r, agents = self._maintain({
            "prd-reviewer.toml": 'name="prd-reviewer"\n# Teamwork PRD Cross-Reviewer\n',
            "reviewer.toml": 'name="reviewer"\n# Teamwork reviewer\n',
        })
        self.assertEqual(sorted(r.get("legacy_codex_agents_removed", [])),
                         ["prd-reviewer.toml", "reviewer.toml"])
        self.assertEqual(sorted(p.name for p in agents.iterdir()), [])

    def test_user_authored_same_name_is_kept(self):
        """签名守卫 —— 误删用户自建配置比留着旧 profile 更糟。"""
        r, agents = self._maintain({
            "blueprint-reviewer.toml": 'name="mine"\n# 我自己写的 · 无签名\n'})
        self.assertIn("blueprint-reviewer.toml", r.get("kept_foreign_codex_agents", []))
        self.assertTrue((agents / "blueprint-reviewer.toml").exists())

    def test_no_longer_deploys_anything(self):
        r, _ = self._maintain({})
        self.assertEqual(r.get("codex_agents_deployed", []), [])


class TestRecipeAndTemplateStateTheRequirement(unittest.TestCase):

    def test_recipe_demands_file_read_capability(self):
        src = (ROOT / "tools" / "state.py").read_text(encoding="utf-8")
        self.assertIn("必须有文件读取能力", src)
        self.assertIn("files_read", src, "配方未要求产物记 files_read = 证据无处可取")

    def test_reviewer_template_header_is_current(self):
        """原头部还写着 `claude -p` 与 `_run_claude_review` —— 前者 v8.291 退役、后者 v8.293 删除。"""
        t = (ROOT / "claude-agents" / "reviewer.md").read_text(encoding="utf-8")
        self.assertIn("必须有文件读取能力", t)
        i = t.index("## Prompt 主体") if "## Prompt 主体" in t else len(t)
        header = t[:i]
        self.assertNotIn("调起 `claude -p`", header, "头部仍描述已退役的 CLI 调用路径")


if __name__ == "__main__":
    unittest.main(verbosity=2)
