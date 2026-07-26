"""v8.292:WS 拆解按交付内聚 · 不按评审面 · 尽量不拆太多(用户拍板)。

原判据把「评审 blast radius」列为合法拆分理由 —— 那正是「按评审面拆」:
横切出来的件各自**不能独立上线**(前端等后端 / 后端没人用),feature 数与协调成本上升,
而评审总量并没变少。本版把交付内聚定为**唯一主判据**,默认姿态改为**合并**。
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
STATE_PY = HERE.parent / "state.py"


class TestSplitCriteriaDocumented(unittest.TestCase):
    def setUp(self):
        self.t = (ROOT / "docs" / "feature-planning.md").read_text(encoding="utf-8")

    def test_delivery_cohesion_is_sole_criterion(self):
        self.assertIn("交付内聚(唯一主判据", self.t)
        self.assertIn("默认合并 · 拆分是例外", self.t)

    def test_review_surface_explicitly_forbidden(self):
        self.assertIn("不按评审面拆", self.t)
        for phrase in ("改动面大不好评审", "不能独立上线"):
            self.assertIn(phrase, self.t, f"缺反模式说明:{phrase}")

    def test_blast_radius_removed_from_justifications(self):
        """「blast radius(评审不可收)」不再是保持独立的硬理由。"""
        self.assertNotIn("blast radius", self.t)
        self.assertIn("硬理由**只有三类**", self.t)

    def test_oversized_cohesive_unit_has_guidance(self):
        """内聚单元太大时的正解:更小的纵切 或 接受多轮 —— 不是横切。"""
        self.assertIn("更小的内聚切片", self.t)
        self.assertIn("接受多轮评审", self.t)

    def test_template_and_checklist_synced(self):
        ws = (ROOT / "templates" / "workstream.md").read_text(encoding="utf-8")
        self.assertIn("不按评审面切", ws)
        st = (HERE.parent / "state.py").read_text(encoding="utf-8")
        self.assertIn("按评审面横切", st)      # planning-check 清单同步


class TestWsLintGranularityBackpressure(unittest.TestCase):
    """粒度反压物化:> 6 个 BL → WARN(不 FAIL —— 拆得对不对是判断题)。"""

    def _ws(self, n_features):
        tmp = Path(tempfile.mkdtemp(prefix="tw-wsg-"))
        subprocess.run(["git", "init", "-q", str(tmp)], check=True)
        d = tmp / "product-overview" / "workstream"
        d.mkdir(parents=True)
        feats = "\n".join(
            f"    - id: F{i}\n      current_state: 读过 src/a{i}.py · 缺口 X" for i in range(1, n_features + 1))
        (d / "WS-01.md").write_text(
            "<!-- TEAMWORK-MACHINE\nws_id: WS-01\nui_panorama_confirmed: N-A\n"
            f"features:\n{feats}\n-->\n\n# WS-01\n\n"
            "<!-- WS-PROGRESS:START -->\n<!-- WS-PROGRESS:END -->\n"
            "<!-- WS-DAG:START -->\n<!-- WS-DAG:END -->\n", encoding="utf-8")
        return tmp

    def _lint(self, tmp):
        r = subprocess.run([sys.executable, str(STATE_PY), "ws-lint", "--ws", "WS-01"],
                           cwd=str(tmp), capture_output=True, text=True, timeout=60)
        out = r.stdout or r.stderr
        s = out.index("{"); depth = 0
        for i in range(s, len(out)):
            if out[i] == "{": depth += 1
            elif out[i] == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(out[s:i + 1])
        return {}

    def test_seven_features_warns(self):
        d = self._lint(self._ws(7))
        self.assertIn("granularity_warnings", d)
        w = " ".join(d["granularity_warnings"])
        self.assertIn("默认合并", w)
        self.assertIn("不按评审面拆", w)

    def test_six_features_no_warning(self):
        d = self._lint(self._ws(6))
        self.assertNotIn("granularity_warnings", d)

    def test_warning_is_not_a_failure(self):
        """反压是 WARN 不是 FAIL —— 拆 7 件可能是对的,机器只摆问题不代拍板。"""
        d = self._lint(self._ws(9))
        self.assertIn("granularity_warnings", d)
        self.assertNotIn("granularity", " ".join(d.get("missing", [])))
