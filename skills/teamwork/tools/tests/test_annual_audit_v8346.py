"""年检 P0 三修(aon-core / supersdk / aib · 289 行台账实证)。

年检口径:三个消费项目全在 v8.344.1 · 台账 16 列 canonical · 样本 210/71/8。

三条 P0 都是**用数据推翻或补上框架自己的设计**:
① 降档砍错了路:逐 stage 真 finding 产出 external > architect(goal 275:178 ·
   blueprint 76:57 · review 87:53 · 总量 1546:735 = 2.1× · 采纳率 82.3%),
   而 v8.341-343 把 tiny/lite/medium 的单路默认全配成 architect —— 那个理由
   (「异质冷审边际收益压不过协调开销」)是推的,没有数据。
② worktree 巡检挂错了地方:v8.325 把「不覆盖存量 ask」的补偿设计成「每 session 报告」,
   但报告只在 bootstrap 调 —— 而 v8.322 **刚刚**证明 bootstrap 在积灰项目上不跑。
   实测 aon-core 14 个 worktree / 18G。
③ 复发防御清单只有读取端:v8.278 让 dev brief 每次读它,却没有任何动作写它 ——
   可预防率常年 70.5%(1461/2072),而清单 aon-core 0 条 / aib 0 条 / supersdk 3 条。
"""
import subprocess
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

import state as S            # noqa: E402
import _v8_engine as E       # noqa: E402


# ─── P0-1 · 单路留 external ────────────────────────────────────────────

class TestSingleRouteKeepsHighestYield(unittest.TestCase):

    def test_light_tiers_single_route_is_external(self):
        for tier in ("tiny", "lite"):
            self.assertEqual(S.TIER_DIMS[tier]["review"]["review"], ["external"], tier)

    def test_medium_blueprint_and_review_single_external(self):
        m = S.TIER_DIMS["medium"]["review"]
        self.assertEqual(m["blueprint"], ["external"])
        self.assertEqual(m["review"], ["external"])
        self.assertEqual(m["goal"], ["fast"])        # goal 用合并帽 · 不受本条影响

    def test_still_single_route_not_widened(self):
        """反转的是**留哪一路**,不是把路数加回去 —— 别把修 bug 修成撤销降档。"""
        for tier in ("tiny", "lite"):
            for point, roles in S.TIER_DIMS[tier]["review"].items():
                self.assertLessEqual(len(roles), 1, f"{tier}.{point}")

    def test_full_keeps_both_routes(self):
        """full 不动:两路并行时 architect 与 external 各司其职。"""
        f = S.TIER_DIMS["full"]["review"]
        self.assertEqual(f["review"], ["architect", "external"])
        self.assertEqual(f["blueprint"], ["architect", "external"])

    def test_static_tiny_roster_matches_dims(self):
        """静态回退表与维度表必须同口径(两份载体必漂 · 这里逐档比对)。"""
        self.assertEqual(E.build_default_stage_review_roles("Feature", "tiny")["review"],
                         S.TIER_DIMS["tiny"]["review"]["review"])

    def test_evidence_recorded_in_spec(self):
        """判据必须带实测数字 —— 否则下一版又会凭直觉改回去(本条就是这么发生的)。"""
        t = (SKILL_ROOT / "stages" / "goal-stage.md").read_text(encoding="utf-8")
        self.assertIn("只留一路时留 `external`", t)
        self.assertIn("275:178", t)          # goal 逐 stage 实测
        self.assertIn("2.1×", t)
        self.assertIn("82.3%", t)


# ─── P0-2 · worktree 巡检挂到会跑的命令上 ──────────────────────────────

class TestWorktreeSweepCarrier(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        src = (SKILL_ROOT / "tools" / "_v8_ship.py").read_text(encoding="utf-8")
        cls.src = src
        cls.seg = src.split("def cmd_main_sync", 1)[-1].split("\ndef ", 1)[0] \
            if "def cmd_main_sync" in src else src

    def test_sweep_runs_in_main_sync(self):
        self.assertIn("prune_merged_worktrees", self.src)
        self.assertIn("worktree_sweep", self.src)

    def test_sweep_cannot_break_finalize(self):
        """巡检不许炸收尾 —— 它是附带动作,不是收尾的前置。"""
        i = self.src.index("prune_merged_worktrees(main_wt)")
        window = self.src[i - 400:i + 200]
        self.assertIn("try:", window)
        self.assertIn("巡检不许炸收尾", window)

    def test_why_names_the_repeated_mistake(self):
        """v8.322 的教训写在 v8.325 前面一版,v8.325 仍踩了 —— 这个 why 必须留住。"""
        i = self.src.index("v8.346(年检实证)")
        seg = self.src[i:i + 700]
        self.assertIn("bootstrap", seg)
        self.assertIn("v8.322", seg)
        self.assertIn("18G", seg)            # 实测后果
        self.assertIn("积压发生的那个时点", seg)   # 载体判据

    def test_bootstrap_call_site_kept(self):
        """bootstrap 那条不删 —— 它对「用户真的跑了 bootstrap」仍有效,只是不能是唯一入口。"""
        bs = (SKILL_ROOT / "tools" / "bootstrap.py").read_text(encoding="utf-8")
        self.assertIn("prune_merged_worktrees(project_root)", bs)


# ─── P0-3 · 复发防御清单接上写入端 ────────────────────────────────────

class TestDefenseListWriteSide(unittest.TestCase):

    def test_preventability_emits_ready_skeleton(self):
        """数据算好了别让人誊抄(v8.323 形状)—— 给现成骨架,判断留人。"""
        src = (SKILL_ROOT / "tools" / "state.py").read_text(encoding="utf-8")
        seg = src.split("def cmd_review_preventability", 1)[1].split("\ndef ", 1)[0]
        self.assertIn("defense_list_entry", seg)
        self.assertIn("skeleton", seg)
        self.assertIn("复发防御清单", seg)
        self.assertIn("写时防", seg)          # 写祈使句不写事故复述
        self.assertIn('entry["preventable"] > 0', seg)   # 只在真有可预防时出

    def test_archive_gate_requires_the_entry(self):
        src = (SKILL_ROOT / "tools" / "_v8_ship.py").read_text(encoding="utf-8")
        self.assertIn('"pending_step": "defense-list"', src)
        self.assertIn("authoring_preventability", src)
        self.assertIn("KNOWLEDGE.md", src)

    def test_gate_has_an_audited_escape(self):
        """例外要有出口且留痕(纯环境抖动确实没什么可沉淀)· 年检看频次。"""
        src = (SKILL_ROOT / "tools" / "_v8_ship.py").read_text(encoding="utf-8")
        self.assertIn("no_defense_entry", src)
        self.assertIn("年检看这个例外的频次", src)

    def test_gate_only_fires_when_preventable(self):
        """没有可预防 finding 的 feature 不该被这道门拦(不为不重要的事加复杂度)。"""
        src = (SKILL_ROOT / "tools" / "_v8_ship.py").read_text(encoding="utf-8")
        seg = src.split('pending_step": "defense-list"', 1)[0][-900:]
        self.assertIn('int(e.get("preventable") or 0) > 0', seg)

    def test_flag_exposed_on_cli(self):
        out = subprocess.run(
            [sys.executable, str(SKILL_ROOT / "tools" / "state.py"), "ship-phase", "--help"],
            capture_output=True, text=True, timeout=30).stdout
        self.assertIn("--no-defense-entry", " ".join(out.split()))


if __name__ == "__main__":
    unittest.main()
