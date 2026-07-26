"""v8.295:stage 耗时归因采集 —— 补上「有数字没归因」那一环。

机器早已采到 duration / await / active_minutes(v8.276),但那只回答「花了多久」,
不回答「花在哪」。实证 SVC-PLATFORM-F260726 复盘的最大发现恰恰是归因:
blueprint 6 波往返里波 5、6 是**纯文档对齐无设计价值**,双档同步吃掉 ~35% 轮次 / ~25% token。

🔴 为什么这不是又一道「环节化自检」(v8.283 判定会衰减的那类):
它不让 AI 自查做得好不好 —— 采的是**AI 自己算不出、事后也复原不了的事实**;
且它是**验证提效改动是否起效的唯一手段**(v8.294 的收敛期归一 / TC 边界 / 投机窗准入
都声称能砍协调开销,没有这列数据就无法证伪)。

载体复用既有的三层(state.json → ship 聚合 → PROCESS-LEDGER),**不新建文件夹** ——
`docs/audit/` 是前车之鉴:22 个文件,代码自陈「审计只写不读」。
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from _v8_ship import _stage_cost_summary  # noqa: E402
import _v8_engine as E  # noqa: E402

STATE_PY = ROOT / "tools" / "state.py"


def _run(*args):
    r = subprocess.run([sys.executable, str(STATE_PY), *args],
                       capture_output=True, text=True, timeout=30)
    try:
        return r.returncode, json.loads(r.stdout)
    except (ValueError, json.JSONDecodeError):
        return r.returncode, {"_raw": r.stdout, "_err": r.stderr}


class TestStageCostCommand(unittest.TestCase):

    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="tw-sc-v8295-"))
        self.addCleanup(shutil.rmtree, self.d, ignore_errors=True)
        (self.d / "state.json").write_text(json.dumps({
            "feature_id": "F001", "flow_type": "Feature", "current_stage": "blueprint",
            "completed_stages": [], "stage_contracts": {},
            "created_at": "2026-07-26T00:00:00Z",
        }), encoding="utf-8")

    def _state(self):
        return json.loads((self.d / "state.json").read_text(encoding="utf-8"))

    def test_records_into_state(self):
        rc, out = _run("stage-cost", "--feature", str(self.d), "--stage", "blueprint",
                       "--rounds", "6", "--overhead-rounds", "2",
                       "--kinds", "双档同步;门禁重试", "--note", "TECH↔TC 跨 agent 往返")
        self.assertEqual(rc, 0, out)
        rec = self._state()["stage_cost"][0]
        self.assertEqual(rec["rounds"], 6)
        self.assertEqual(rec["overhead_rounds"], 2)
        self.assertEqual(rec["kinds"], ["双档同步", "门禁重试"])
        self.assertIn("往返", rec["note"])

    def test_zero_overhead_is_still_data(self):
        """零开销必须能记 —— 「这次没开销」和「没记录」是两回事,年检要分得开。"""
        rc, _ = _run("stage-cost", "--feature", str(self.d), "--stage", "review",
                     "--rounds", "3", "--overhead-rounds", "0")
        self.assertEqual(rc, 0)
        self.assertEqual(self._state()["stage_cost"][0]["overhead_rounds"], 0)

    def test_overhead_cannot_exceed_total(self):
        rc, out = _run("stage-cost", "--feature", str(self.d), "--stage", "dev",
                       "--rounds", "2", "--overhead-rounds", "5")
        self.assertEqual(rc, 1)
        self.assertIn("不能大于", out.get("error", ""))

    def test_not_a_gate(self):
        """非门禁:没记过 stage-cost 也不该影响任何 complete —— 台账列留空是有效前缀。"""
        self.assertNotIn("stage_cost", self._state())
        self.assertIsNone(_stage_cost_summary(self._state()))


class TestLedgerAggregation(unittest.TestCase):

    def test_summary_is_ratio_plus_pointer_only(self):
        """v8.297:台账单元格 ≤1 行 —— 只放可查表算账的比值 + 指针,叙述归复盘文档。"""
        state = {"stage_cost": [
            {"stage": "goal", "rounds": 3, "overhead_rounds": 0, "kinds": [], "note": ""},
            {"stage": "blueprint", "rounds": 6, "overhead_rounds": 2,
             "kinds": ["双档同步"], "note": "TECH↔TC 表数与错误码往返 —— 一段很长的归因叙述"},
        ]}
        cell = _stage_cost_summary(state, "docs/retros/F1-process.md")
        self.assertIn("2/9", cell, "比值要留在台账(年检查表即得 · 不必开文档)")
        self.assertIn("docs/retros/F1-process.md", cell, "缺指针 = 叙述找不到")
        self.assertNotIn("TECH↔TC", cell, "归因叙述不该再挤进单元格")
        self.assertNotIn("双档同步", cell)
        self.assertLessEqual(len(cell.splitlines()), 1, "单元格必须单行")

    def test_retro_path_convention(self):
        from _v8_ship import _process_retro_path  # type: ignore
        self.assertEqual(_process_retro_path({}, "F002"), "docs/retros/F002-process.md")
        self.assertEqual(_process_retro_path({"sub_project": "apps/partner"}, "SVC-F1"),
                         "apps/partner/docs/retros/SVC-F1-process.md")

    def test_summary_none_when_unrecorded(self):
        """无记录 → None(台账列留空 = 有效前缀 · 该 feature 早于该指标 · 诚实)。"""
        self.assertIsNone(_stage_cost_summary({}))
        self.assertIsNone(_stage_cost_summary({"stage_cost": []}))

    def test_ship_archive_emits_the_cell(self):
        import _v8_ship as S  # type: ignore
        src = (ROOT / "tools" / "_v8_ship.py").read_text(encoding="utf-8")
        self.assertIn('"ledger_stage_cost": _stage_cost_summary(state,', src,
                      "ship1 archive 未 emit 台账数据源")
        self.assertIn('"ledger_process_retro_path"', src, "未 emit 流程复盘落点")
        self.assertTrue(hasattr(S, "_stage_cost_summary"))


class TestLedgerSchemaDiscipline(unittest.TestCase):
    """🔴 schema 演进纪律:新列只在**末尾**加 —— 中间插列会让旧行错位、年检读错列。"""

    def test_new_column_is_last(self):
        t = (ROOT / "templates" / "process-ledger.md").read_text(encoding="utf-8")
        header = next(l for l in t.splitlines() if l.startswith("| Feature |"))
        cols = [c.strip() for c in header.strip("|").split("|")]
        self.assertTrue(cols[-1].startswith("⏱️ 耗时归因"),
                        f"耗时归因不在末列(违反 schema 演进纪律):{cols[-1]}")

    def test_header_and_separator_and_example_widths_match(self):
        t = (ROOT / "templates" / "process-ledger.md").read_text(encoding="utf-8")
        lines = t.splitlines()
        header = next(l for l in lines if l.startswith("| Feature |"))
        i = lines.index(header)
        sep, example = lines[i + 1], lines[i + 2]
        n = len(header.strip("|").split("|"))
        self.assertEqual(len(sep.strip("|").split("|")), n, "分隔行列数与表头不符")
        self.assertEqual(len(example.strip("|").split("|")), n, "示例行列数与表头不符")

    def test_column_documented_with_command_and_rationale(self):
        t = (ROOT / "templates" / "process-ledger.md").read_text(encoding="utf-8")
        self.assertIn("state.py stage-cost", t, "新列没写怎么产生 = 没人会填")
        self.assertIn("ledger_stage_cost", t, "没写数据源 = 会被肉眼估算")


class TestHintAtTheRightMoment(unittest.TestCase):
    """提示放 complete emit 而非写进各 stage 文档:机器在正确的时刻提醒,不靠文档记忆。

    且只在**有多轮往返成本**的 stage 提 —— 13 个 stage 都来一遍就退化成
    v8.283 判定会衰减的「环节化自检」。
    """

    def test_hint_only_for_cost_bearing_stages(self):
        self.assertIsNotNone(E._stage_cost_hint("blueprint", "/f", 318))
        self.assertIsNotNone(E._stage_cost_hint("review", "/f", 40))
        for skip in ("ship", "pm_acceptance", "panorama_sync", "diagnose", "execute"):
            self.assertIsNone(E._stage_cost_hint(skip, "/f", 10),
                              f"{skip} 不该提示(无多轮往返成本 · 提了就是仪式税)")

    def test_hint_carries_runnable_command_and_urgency(self):
        h = E._stage_cost_hint("blueprint", "/abs/feat", 318)
        self.assertIn("stage-cost", h)
        self.assertIn("/abs/feat", h, "提示要给可直接跑的命令(带真实 feature 路径)")
        self.assertIn("318", h, "要回显本 stage 实际耗时,否则 AI 得自己去查")
        self.assertIn("趁现在记", h, "缺时效性说明 → 会被推迟到 ship 时靠 mtime 反推")

    def test_hint_wired_into_complete_emit(self):
        src = (ROOT / "tools" / "_v8_engine.py").read_text(encoding="utf-8")
        self.assertIn('"stage_cost_hint": _sc_hint', src, "提示未接进 complete emit")




class TestLedgerInstructionNamesEveryEmitField(unittest.TestCase):
    """列建了没人填 = 白建 —— v8.295 加完列,写台账行的指令里漏点了它(本门禁就是为此立的)。

    ship-stage §16 是 PMO 写台账行的唯一指令。每多一个 `ledger_*` emit 字段,
    这里就必须点名,否则 PMO 不知道该抄它 → 新列永远空着,而空着与「该 feature 早于该指标」
    在台账上无法区分(有效前缀语义被污染)。
    """

    LEDGER_EMIT_FIELDS = ("ledger_timing", "ledger_authoring_preventability",
                          "ledger_stage_cost", "ledger_process_retro_path")

    def test_ship_stage_instruction_names_all_ledger_fields(self):
        doc = (ROOT / "stages" / "ship-stage.md").read_text(encoding="utf-8")
        missing = [f for f in self.LEDGER_EMIT_FIELDS if f not in doc]
        self.assertEqual(missing, [], f"ship-stage §16 未告诉 PMO 抄这些 emit 字段:{missing}")

    def test_every_ledger_emit_field_is_covered_by_this_test(self):
        """反向锁:_v8_ship.py 里新增 ledger_* emit 字段 → 必须同步进本清单与 ship-stage 指令。"""
        import re
        src = (ROOT / "tools" / "_v8_ship.py").read_text(encoding="utf-8")
        emitted = set(re.findall(r'"(ledger_[a-z_]+)":', src))
        unknown = emitted - set(self.LEDGER_EMIT_FIELDS)
        self.assertEqual(unknown, set(),
                         f"新增了 ledger emit 字段但没接进台账指令与本门禁:{sorted(unknown)}")




class TestProcessRetroDoc(unittest.TestCase):
    """v8.297:归因叙述与流程反思从台账单元格搬到独立复盘文档。

    起因(用户):「耗时归因和阶段流程反思不该写到 PROCESS-LEDGER,因为写不下」——
    台账一行一 feature、单元格 ≤1 行,而「这 318 分钟花在哪」恰恰是最值钱的那段。
    顺带把原本**只 emit 不落盘**的 digest 四问也接了进来(说完就蒸发 · 年检读不到)。
    """

    def test_template_exists_and_states_its_boundary(self):
        t = (ROOT / "templates" / "process-retro.md").read_text(encoding="utf-8")
        self.assertIn("docs/retros/", t)
        # 与同目录业务复盘的分工必须写死,否则两份会混成一锅
        self.assertIn("业务复盘", t, "未划清与 docs/retros/<id>.md(业务/工程复盘)的边界")
        self.assertIn("只复盘 teamwork 流程本身", t)

    def test_template_carries_all_four_sections(self):
        t = (ROOT / "templates" / "process-retro.md").read_text(encoding="utf-8")
        for sec in ("各阶段耗时", "耗时归因", "流程反思", "起草可预防性"):
            self.assertIn(sec, t, f"复盘模板缺 §{sec}")

    def test_template_has_operational_criterion_for_overhead(self):
        """「什么算协调开销」必须可判定,否则每人一把尺、跨 feature 不可比。"""
        t = (ROOT / "templates" / "process-retro.md").read_text(encoding="utf-8")
        self.assertIn("产生了新的设计判断或新的实现", t, "缺开销判据 = 数据不可比")

    def test_ship_stage_wires_doc_into_planning_artifacts(self):
        """复盘不进 --planning-artifacts = 不随 MR 合入 = 白写。"""
        doc = (ROOT / "stages" / "ship-stage.md").read_text(encoding="utf-8")
        self.assertIn("process-retro.md", doc, "§16 未指向复盘模板")
        self.assertIn("planning-artifacts", doc)

    def test_digest_four_questions_now_persisted(self):
        doc = (ROOT / "stages" / "ship-stage.md").read_text(encoding="utf-8")
        self.assertIn("四问同时写进流程复盘文档", doc,
                      "digest 仍是「只 emit 不落盘」—— 说完即蒸发,年检读不到")

    def test_ledger_note_points_at_the_doc(self):
        t = (ROOT / "templates" / "process-ledger.md").read_text(encoding="utf-8")
        self.assertIn("process-retro.md", t, "台账未指向复盘文档 = 指针断裂")
        self.assertIn("归因叙述不写这里", t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
