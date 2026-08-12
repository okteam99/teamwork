"""v8.306:测试证据的两个维度 —— 谁跑的(自我申报)+ 对应哪份代码(零信任重算)。

实证(aon-core):AI **在主窗口直接跑了测试**,用户问「为什么没切验证档」它才发现。
自陈:「沿用了『主编排收口测试』的做法,漏掉了 v8.299 的硬规则」——
🔴 **规则它读过**(自己引用了版本号),但**提醒在 stage-start、动作在几十个工具调用之后**。
与 v8.299 派发声明、v8.301 命令时点是**同一个失效机理**。

它随后提了一份四层改进(verification receipt)。逐条按**可验证性**分级后:

  🟢 **tree-hash 绑定** —— complete 时**自己重算**,不读任何申报字段 = **零信任** ·
     挡的是今天完全没挡的洞:「先绿、后改、仍拿旧日志过门」。**最该做。**
  🟡 **runner/tier/model 申报** —— AI 自己写,**拦得住「忘了」拦不住「故意」**。
     而这次恰恰是忘了,所以有效;但不能按「防伪造」宣传(提案原文说「这一个门禁就能直接
     防住我刚才的错误」—— 过誉了,已在条文里标清能力边界)。
  🔴 **agent_task_id 作硬门** —— **跨宿主不可得**(Codex 与 Claude Code 的 subagent 标识不同)·
     硬门会在某些宿主上变成**注定失败的门**(v8.301 刚立的判据)· **不做**。

`main-window` 是**允许的值**,但走 v8.299 的例外协议:需 `--user-confirmed`,否则 BLOCK ——
**失误变得可见,而不是被静默吞掉**。
"""
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import _v8_stage_specs as S  # noqa: E402
import _v8_engine as E  # noqa: E402


def _repo():
    d = Path(tempfile.mkdtemp(prefix="tw-vr-v8306-"))
    subprocess.run(["git", "-C", str(d), "init", "-q"], capture_output=True)
    (d / "a.txt").write_text("v1", encoding="utf-8")
    subprocess.run(["git", "-C", str(d), "add", "-A"], capture_output=True)
    subprocess.run(["git", "-C", str(d), "-c", "user.email=t@x", "-c", "user.name=t",
                    "commit", "-qm", "init"], capture_output=True)
    return d


class TestTreeHashIsZeroTrust(unittest.TestCase):
    """🟢 本版唯一完全可机验的一条 —— complete 自己算,不信申报。"""

    def test_fingerprint_covers_uncommitted_changes(self):
        """只绑 HEAD 不够 —— 未提交改动同样让旧日志失效。"""
        d = _repo()
        fp1 = S._worktree_fingerprint(d)
        (d / "a.txt").write_text("v2", encoding="utf-8")   # 未提交
        self.assertNotEqual(fp1, S._worktree_fingerprint(d),
                            "未提交改动没进指纹 → 「改了但没提交」仍能拿旧日志过门")

    def test_matching_fingerprint_passes(self):
        d = _repo()
        ok, _ = S._evidence_test_evidence_fresh({}, NS(feature=str(d),
                                                       test_tree_hash=S._worktree_fingerprint(d)))
        self.assertTrue(ok)

    def test_code_changed_after_tests_blocks(self):
        """🔴 核心:测完再改代码 → 那份 stdout 证明不了现在这份代码。"""
        d = _repo()
        fp = S._worktree_fingerprint(d)
        (d / "a.txt").write_text("测完又改了", encoding="utf-8")
        ok, msg = S._evidence_test_evidence_fresh({}, NS(feature=str(d), test_tree_hash=fp))
        self.assertFalse(ok)
        self.assertIn("测试证据已过期", msg)
        self.assertIn("重跑测试", msg, "未给处置方向")
        self.assertIn("不要 bypass", msg, "未堵 bypass → 这道门会被逃生通道绕过")

    def test_missing_hash_is_backward_compatible(self):
        """存量 in-flight feature 没有这个参数 —— 降级放行但点名,不能把它们卡死。"""
        d = _repo()
        ok, msg = S._evidence_test_evidence_fresh({}, NS(feature=str(d), test_tree_hash=""))
        self.assertTrue(ok)
        self.assertIn("存量兼容", msg)

    def test_non_git_degrades_open(self):
        """🔴 绝不因环境问题 BLOCK —— 注定失败的门比没有门更糟(v8.301)。"""
        ok, _ = S._evidence_test_evidence_fresh(
            {}, NS(feature="/tmp/tw-definitely-not-a-repo", test_tree_hash="abc"))
        self.assertTrue(ok)


class TestRunnerDeclaration(unittest.TestCase):
    """🟡 自我申报 —— 治「忘了」,不治「故意」。条文里必须标清这条边界。"""

    def _check(self, **kw):
        return S._evidence_test_runner_declared({}, NS(**kw))

    def test_missing_runner_blocks_with_actionable_options(self):
        ok, msg = self._check(test_runner="")
        self.assertFalse(ok)
        for opt in ("subagent", "main-window", "ci"):
            self.assertIn(opt, msg, f"报错未列出可选值 {opt} → 用户要去翻文档")

    def test_subagent_passes_and_flags_missing_model(self):
        ok, msg = self._check(test_runner="subagent", test_runner_model="")
        self.assertTrue(ok, "model 缺失不该 BLOCK(它只是观测)")
        self.assertIn("unspecified", msg, "未提示台账会记 unspecified")

    def test_main_window_needs_user_authorization(self):
        """v8.299 用户拍板:验证类白名单的例外**不许 AI 自决**。"""
        ok, msg = self._check(test_runner="main-window", user_confirmed=False)
        self.assertFalse(ok)
        self.assertIn("不许 AI 自决", msg)
        self.assertIn("自我合理化", msg, "未点名失败机制 → 会被当成官僚要求")

    def test_authorized_main_window_passes_but_warns(self):
        ok, msg = self._check(test_runner="main-window", user_confirmed=True)
        self.assertTrue(ok, "拿到授权仍拦 = 例外协议形同虚设")
        self.assertIn("WARN", msg, "例外未留痕 → 年检看不到这类例外的频次")

    def test_docstring_states_the_trust_boundary(self):
        """🔴 提案原文说「这一个门禁就能直接防住我刚才的错误」—— 过誉。

        它拦的是「忘了」。不标清这条边界,读者会高估这道门、进而放松其他把关。
        """
        doc = S._evidence_test_runner_declared.__doc__ or ""
        self.assertIn("自我申报", doc)
        self.assertIn("拦不住", doc, "未标清能力边界")


class TestRecipeAtTheActionPoint(unittest.TestCase):
    """规则读过仍然漏 —— 因为提醒与动作之间隔了太多 context。配方要在 start 就给全。"""

    def test_only_for_test_bearing_stages(self):
        self.assertIsNotNone(E._verification_recipe("dev", "/f"))
        self.assertIsNotNone(E._verification_recipe("test", "/f"))
        for s in ("goal", "blueprint", "review", "ship"):
            self.assertIsNone(E._verification_recipe(s, "/f"),
                              f"{s} 不跑测试 · 提了就是仪式税")

    def test_recipe_is_end_to_end_runnable(self):
        """派发 + 采指纹 + complete 参数 —— 三步都要给,缺一步 AI 就得自己拼。"""
        r = E._verification_recipe("dev", "/abs/feat")
        self.assertIn("tier=验证", r, "缺派发声明格式")
        self.assertIn("sha256", r, "缺采指纹的可跑命令")
        self.assertIn("--test-tree-hash", r)
        self.assertIn("--test-runner subagent", r)
        self.assertIn("/abs/feat", r, "命令未带真实路径")

    def test_recipe_names_the_exception_protocol(self):
        r = E._verification_recipe("dev", "/f")
        self.assertIn("不许 AI 自决", r)
        self.assertIn("--user-confirmed", r)

    def test_wired_into_stage_start_emit(self):
        src = (ROOT / "tools" / "_v8_engine.py").read_text(encoding="utf-8")
        self.assertIn('"verification_recipe": _vr', src, "配方未接进 stage-start emit")

    def test_subagent_capability_requirement_stated(self):
        """v8.304 的教训:零工具 subagent 跑不了测试 —— 配方要写明需要什么能力。"""
        r = E._verification_recipe("dev", "/f")
        self.assertIn("命令执行", r)


class TestGateWiredIntoDevSpec(unittest.TestCase):

    def test_both_checks_registered(self):
        names = [getattr(e, "name", "") for e in (S.STAGE_SPECS["dev"].evidence_checks or [])]
        self.assertIn("test_evidence_fresh", names)
        self.assertIn("test_runner_declared", names)

    def test_reuses_existing_user_confirmed_flag(self):
        """不新造同义 flag —— 逃生授权早有 `--user-confirmed`(bypass 协议在用)。"""
        src = (ROOT / "tools" / "_v8_stage_specs.py").read_text(encoding="utf-8")
        self.assertNotIn("user_authorized", src, "新造了同义 flag")


if __name__ == "__main__":
    unittest.main(verbosity=2)
