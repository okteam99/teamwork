"""v8.294:localconfig 在 worktree 里读不到 —— 五个读取者共享的先天缺陷。

根因:`.teamwork_localconfig.json` 是**本地配置、不入 git**(bootstrap 自动 gitignore),
只存在于**主工作树**。而五份独立实现都是「向上找 · 遇 `.git` 停」—— linked worktree 的根
有 `.git`(**文件**形式)却没有配置 → 全部静默回退默认值。teamwork 默认 `worktree: auto`,
等于这五项配置在真实 feature 上从来没生效过。

case 实证(SVC-PLATFORM-F260726):localconfig `fast_mode: true` · init-feature 后
state.json 无该键 · goal/blueprint 按全量 roster 跑。用户既没拿到速度、也不知道为什么慢。

不是漂移 —— 五份副本**生下来就都是错的**。故门禁锁两件事:解析器行为 + 只有一份实现。
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from _v8_engine import (  # noqa: E402
    load_localconfig, _idle_threshold_minutes, _localconfig_max_review_rounds,
)
from _v8_ship import _read_archive_on_ship  # noqa: E402
from state import _read_fast_mode, _read_id_strategy  # noqa: E402


CONFIG = {
    "fast_mode": True,
    "id_strategy": "sequential",
    "idle_threshold_minutes": 45,
    "max_review_rounds": 5,
    "archive_on_ship": False,
}


class _Layout:
    """主工作树(.git 目录 + localconfig)+ linked worktree(.git 文件 · 无 localconfig)。"""

    def __init__(self, with_config=True):
        self.root = Path(tempfile.mkdtemp(prefix="tw-lc-v8294-"))
        self.main = self.root / "proj"
        (self.main / ".git").mkdir(parents=True)
        if with_config:
            (self.main / ".teamwork_localconfig.json").write_text(
                json.dumps(CONFIG), encoding="utf-8")
        self.main_feature = self.main / "docs" / "features" / "F001"
        self.main_feature.mkdir(parents=True)

        self.wt = self.main / ".worktree" / "F001"
        self.wt_feature = self.wt / "docs" / "features" / "F001"
        self.wt_feature.mkdir(parents=True)
        (self.wt / ".git").write_text(
            f"gitdir: {self.main}/.git/worktrees/F001\n", encoding="utf-8")

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


class TestResolverCrossesWorktreeBoundary(unittest.TestCase):

    def setUp(self):
        self.L = _Layout()
        self.addCleanup(self.L.cleanup)

    def test_main_tree_reads_config(self):
        self.assertEqual(load_localconfig(self.L.main_feature), CONFIG)

    def test_worktree_reads_main_tree_config(self):
        """🔴 回归核心:worktree 内的 feature 目录必须读到主工作树的配置。"""
        self.assertEqual(load_localconfig(self.L.wt_feature), CONFIG,
                         "worktree 里读不到主工作树 localconfig(v8.294 修的就是这个)")

    def test_all_five_accessors_agree_across_worktree(self):
        """五个读取者在主树与 worktree 里必须给出同一结果。"""
        for label, d in (("main", self.L.main_feature), ("worktree", self.L.wt_feature)):
            with self.subTest(tree=label):
                self.assertIs(_read_fast_mode(d), True)
                self.assertEqual(_read_id_strategy(d), "sequential")
                self.assertEqual(_idle_threshold_minutes(d), 45)
                self.assertEqual(_localconfig_max_review_rounds(d), 5)
                self.assertIs(_read_archive_on_ship(str(d)), False)

    def test_no_config_falls_back_to_defaults(self):
        """配置真不存在时才回退默认 —— 修法不能变成「到处乱找」。"""
        L = _Layout(with_config=False)
        self.addCleanup(L.cleanup)
        self.assertIsNone(load_localconfig(L.wt_feature))
        self.assertIs(_read_fast_mode(L.wt_feature), False)
        self.assertEqual(_idle_threshold_minutes(L.wt_feature), 30)
        self.assertEqual(_localconfig_max_review_rounds(L.wt_feature), 3)
        self.assertIs(_read_archive_on_ship(str(L.wt_feature)), True)

    def test_broken_gitdir_pointer_is_safe(self):
        """`.git` 文件内容损坏 → 安全回退,不抛异常、不无限找。"""
        L = _Layout(with_config=False)
        self.addCleanup(L.cleanup)
        (L.wt / ".git").write_text("not a gitdir pointer\n", encoding="utf-8")
        self.assertIsNone(load_localconfig(L.wt_feature))

    def test_malformed_json_falls_back(self):
        L = _Layout()
        self.addCleanup(L.cleanup)
        (L.main / ".teamwork_localconfig.json").write_text("{ broken", encoding="utf-8")
        self.assertIsNone(load_localconfig(L.wt_feature))
        self.assertIs(_read_fast_mode(L.wt_feature), False)


class TestSingleImplementation(unittest.TestCase):
    """五份副本同一个先天缺陷 —— 修完只准剩一份实现。"""

    def test_no_open_coded_localconfig_walks(self):
        """除解析器自身外,不得再有「向上找 localconfig」的手写遍历。"""
        bad = []
        for rel in ("tools/state.py", "tools/_v8_engine.py", "tools/_v8_ship.py",
                    "tools/_v8_stage_specs.py"):
            lines = (ROOT / rel).read_text(encoding="utf-8").splitlines()
            for i, line in enumerate(lines, 1):
                if "_LOCALCONFIG_NAME" in line or "def load_localconfig" in line:
                    continue
                if ".teamwork_localconfig.json" not in line:
                    continue
                # 附近出现 parents 遍历 = 又一份手写向上找
                window = "\n".join(lines[max(0, i - 4):i + 4])
                if "node.parents" in window or "*node.parents" in window or ".parents]" in window:
                    bad.append(f"{rel}:{i}")
        self.assertEqual(bad, [], f"又出现手写 localconfig 向上遍历(应走 load_localconfig):{bad}")


class TestFastModeVisible(unittest.TestCase):
    """复盘 R3 的第二诉求:静默回退是双输 —— 用户既没拿到速度、也不知道为什么慢。"""

    def _brief(self, **kw):
        import argparse
        from state import _init_feature_next_brief  # type: ignore
        args = argparse.Namespace(worktree_mode="off", feature="/tmp/f", flow_type="Feature")
        return _init_feature_next_brief(args, "goal", **kw)

    def test_three_states_each_name_their_source(self):
        on = self._brief(cfg_fast=True, effective_fast=True)
        self.assertIn("fast_mode", on)
        self.assertIn("localconfig", on)

        overridden = self._brief(cfg_fast=True, effective_fast=False)
        self.assertIn("yolo", overridden, "配置开了但被 yolo 覆盖 —— 必须说明白为什么没生效")

        off = self._brief(cfg_fast=False, effective_fast=False)
        self.assertIn("fast_mode", off)
        # 三态互不相同(否则等于没回显)
        self.assertEqual(len({on, overridden, off}), 3)


class TestRivalDesignRequired(unittest.TestCase):
    """§二 的根因:简洁性 checklist 是**验证式**的(作者的理由成立吗),盲区只有**生成式**才破。

    实证 SVC-PLATFORM-F260726:「内部运营账户」标记设计成 singleton 指针表 + 独立审计表,
    四问确实跑了,但参照物由作者叙事给定(能否并入 monetization_config —— 冻结面,当然不能),
    没人问「这个设定的自然归属实体是谁」。用户一句「打到 account 表上」→ 6 新表变 4 新表 + 2 列。
    """

    def test_architect_role_carries_rival_rule(self):
        t = (ROOT / "roles" / "architect.md").read_text(encoding="utf-8")
        self.assertIn("替代形态", t)
        self.assertIn("不构成通过条件", t, "缺「赢了被否方案不算通过」这半句 = 规则可被绕开")

    def test_blueprint_runtime_brief_carries_rival_rule(self):
        """只改 stage doc 到不了 AI —— brief 才是运行时真正被读到的。"""
        import _v8_stage_specs as S  # type: ignore
        brief = S.BLUEPRINT_SPEC.brief_template_fn({})
        self.assertIn("替代形态", brief)




class TestTcResponsibilityBoundary(unittest.TestCase):
    """R1 根因:TC 越界持有 TECH 内容(表数 27→33→31 / 错误码清单)→ TECH 每动一次两档跨 agent 往返。

    双文档同步吃掉 blueprint ~35% 轮次 / ~25% token,而其中一半不是「两个文档」造成的,
    是 TC 装了不该装的东西。故不合并文档,而是给 TC 一条**可判定**的边界。
    """

    def test_tc_template_states_telos_and_operational_test(self):
        t = (ROOT / "templates" / "tc.md").read_text(encoding="utf-8")
        self.assertIn("职责边界", t)
        # 判据必须是可判定的一句话 —— 软性描述会被绕过
        self.assertIn("换实现就要改", t, "缺一句话判据 = 边界不可判定")
        for kw in ("表数量", "存储形态", "可观测行为", "边界与异常"):
            self.assertIn(kw, t, f"TC 边界缺项:{kw}")

    def test_tc_template_keeps_contract_value_nuance(self):
        """断言到的错误码要写具体(否则不叫断言)· 但维护清单 = 复述 —— 这个分寸不能丢。"""
        t = (ROOT / "templates" / "tc.md").read_text(encoding="utf-8")
        self.assertIn("契约值", t)
        self.assertIn("清单", t)

    def test_blueprint_output_contract_points_at_boundary(self):
        t = (ROOT / "stages" / "blueprint-stage.md").read_text(encoding="utf-8")
        self.assertIn("换实现就要改", t, "blueprint ④ 未把 TC 边界透出")

    def test_roles_carry_boundary_pointer(self):
        qa = (ROOT / "roles" / "qa.md").read_text(encoding="utf-8")
        rd = (ROOT / "roles" / "rd.md").read_text(encoding="utf-8")
        self.assertIn("换实现就要改", qa)
        self.assertIn("实现形态归这里", rd, "RD 侧未明确实现形态归 TECH")


class TestDraftPhaseRoleMerge(unittest.TestCase):
    """角色的两种用法:起草期 = 分工标签(可合并)· 评审期 = 独立采样点(必须隔离)。

    合错方向的代价不对称:起草期不合 = 白付协调成本;评审期合了 = 多视角退化成一个视角 × N 份
    (v8.155 实证:in-context architect 在 goal 只产鼓掌)。
    """

    def test_roles_index_states_the_criterion(self):
        t = (ROOT / "ROLES.md").read_text(encoding="utf-8")
        self.assertIn("起草期", t)
        self.assertIn("评审期", t)
        self.assertIn("独立采样点", t)
        # v8.309:断言实证实质而非版本字面量(spec 已清版本标 · 实证叙事保留)
        self.assertIn("实证", t, "缺「评审期不能合」的实证依据 = 规则会被当成可商量的")
        self.assertIn("只产鼓掌", t, "实证内容(in-context 热审只产鼓掌)被清丢")

    def test_convergence_unified_not_parallel(self):
        """起草期并行拿加速,收敛期归一砍往返 —— 两句都要在。"""
        t = (ROOT / "stages" / "blueprint-stage.md").read_text(encoding="utf-8")
        self.assertIn("收敛期归一", t)
        self.assertIn("不派 agent", t, "机械同步项仍在派 agent = R1 的往返成本没砍掉")


class TestSpeculationWindowAdmission(unittest.TestCase):
    """R2:投机窗原有**时点**纪律(只在终确认后)但无**开放决策数**条件。

    「终确认改:默 ≈ 全默」的统计前提只在单决策上成立;多个结构性开放项时,
    草稿必须押某一组合,用户改选任意一项都触发差量重写(实证 ~1.3x token)。
    """

    def test_goal_stage_doc_has_admission_rule(self):
        t = (ROOT / "stages" / "goal-stage.md").read_text(encoding="utf-8")
        self.assertIn("准入纪律", t)
        self.assertIn("≤1", t)

    def test_goal_runtime_brief_carries_admission(self):
        """时点纪律在 brief 里,准入纪律也必须在 —— 否则运行时看不到。"""
        import _v8_stage_specs as S  # type: ignore
        brief = S.GOAL_SPEC.brief_template_fn({})
        self.assertIn("投机", brief)
        self.assertIn("≤1", brief, "goal brief 未带投机准入条件")


if __name__ == "__main__":
    unittest.main(verbosity=2)
