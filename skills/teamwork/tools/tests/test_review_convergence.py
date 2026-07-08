#!/usr/bin/env python3
"""review 收敛协议回归套件(severity 门槛 + findings 台账 + 验证轮 + 轮次预算)。

治本「review 10+ 轮不收敛」四根因:
- A:verdict 二元无严重度门槛 → findings 四级 + review-complete 物化门槛(两向)
- B:Round 2+ 全量重审随机采样新 nit → 验证轮 brief(范围锁定 + 台账注入)
- C:finding 无机器台账 · rejected 可复活 → stage_contracts.review.findings_ledger 跨轮合并
- D:无轮次上限 → max_review_rounds 预算 + R5 升级暂停点(--user-confirmed --reason 逃生)
- E:APPROVE 收口前修复后 external 验证(--verify-fixes)轻量物化

运行:python3 -m pytest skills/teamwork/tools/tests/test_review_convergence.py -q
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
STATE_PY = TOOLS / "state.py"
sys.path.insert(0, str(TOOLS))

import _v8_engine as E  # noqa: E402
import _v8_stage_specs as S  # noqa: E402


def _git(cwd: Path, *args: str) -> tuple[int, str]:
    r = subprocess.run(["git", *args], cwd=str(cwd),
                       capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout.strip()


def _run_state(cwd: Path, *args: str, expect_exit: int = 0) -> dict:
    r = subprocess.run([sys.executable, str(STATE_PY), *args],
                       cwd=str(cwd), capture_output=True, text=True, timeout=60)
    assert r.returncode == expect_exit, (
        f"exit {r.returncode} ≠ {expect_exit}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}")
    out = r.stdout if r.stdout.strip() else r.stderr
    start = out.index("{")
    depth = 0
    for i in range(start, len(out)):
        if out[i] == "{":
            depth += 1
        elif out[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(out[start:i + 1])
    raise AssertionError(f"无法解析 JSON · stdout={r.stdout!r} stderr={r.stderr!r}")


def _write_findings_md(path: Path, verdict: str, findings=None,
                       include_key: bool = True, style: str = "flow") -> None:
    """写 REVIEW.md:findings=[(id, severity, status, title), ...] · None+include_key → findings: []。"""
    lines = ["---", "reviewers: [architect, qa]", f"verdict: {verdict}"]
    if include_key:
        if findings is None:
            lines.append("findings: []")
        elif style == "flow":
            lines.append("findings:")
            for fid, sev, status, title in findings:
                lines.append(
                    f'  - {{id: {fid}, severity: {sev}, status: {status}, '
                    f'title: "{title}", source: qa}}')
        else:  # block style
            lines.append("findings:")
            for fid, sev, status, title in findings:
                lines.append(f"  - id: {fid}")
                lines.append(f"    severity: {sev}")
                lines.append(f"    status: {status}")
                lines.append(f'    title: "{title}"')
                lines.append("    source: qa")
    lines += ["---", "", "# REVIEW", "详见各视角评审。"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ─── 1 · findings 解析(flow / block / 缺失 / 空 / 非法) ────────────────


class TestParseReviewFindings(unittest.TestCase):
    def setUp(self):
        self.feat = Path(tempfile.mkdtemp(prefix="tw-findings-"))

    def tearDown(self):
        shutil.rmtree(self.feat, ignore_errors=True)

    def test_flow_style_parses_and_normalizes(self):
        _write_findings_md(self.feat / "REVIEW.md", "NEEDS_REVISION",
                           [("F1", "major", "OPEN", "缺 X, 校验")])
        findings, err = S.parse_review_findings(self.feat)
        self.assertEqual(err, "")
        self.assertEqual(findings, [{
            "id": "F1", "severity": "MAJOR", "status": "open",
            "title": "缺 X, 校验", "source": "qa"}])

    def test_block_style_parses(self):
        _write_findings_md(self.feat / "REVIEW.md", "NEEDS_REVISION",
                           [("F2", "BLOCKER", "open", "数据损坏")], style="block")
        findings, err = S.parse_review_findings(self.feat)
        self.assertEqual(err, "")
        self.assertEqual(findings[0]["id"], "F2")
        self.assertEqual(findings[0]["severity"], "BLOCKER")

    def test_missing_key_returns_none(self):
        _write_findings_md(self.feat / "REVIEW.md", "APPROVE", include_key=False)
        findings, err = S.parse_review_findings(self.feat)
        self.assertIsNone(findings)
        self.assertEqual(err, "")

    def test_empty_list_returns_empty(self):
        _write_findings_md(self.feat / "REVIEW.md", "APPROVE", findings=None)
        findings, err = S.parse_review_findings(self.feat)
        self.assertEqual(findings, [])
        self.assertEqual(err, "")

    def test_missing_file_returns_none(self):
        findings, err = S.parse_review_findings(self.feat)
        self.assertIsNone(findings)
        self.assertEqual(err, "")

    def test_invalid_severity_errors(self):
        _write_findings_md(self.feat / "REVIEW.md", "NEEDS_REVISION",
                           [("F1", "CRITICAL", "open", "x")])
        findings, err = S.parse_review_findings(self.feat)
        self.assertIsNone(findings)
        self.assertIn("severity", err)

    def test_invalid_status_errors(self):
        _write_findings_md(self.feat / "REVIEW.md", "NEEDS_REVISION",
                           [("F1", "MAJOR", "wontfix", "x")])
        findings, err = S.parse_review_findings(self.feat)
        self.assertIsNone(findings)
        self.assertIn("status", err)

    def test_duplicate_id_errors(self):
        _write_findings_md(self.feat / "REVIEW.md", "NEEDS_REVISION",
                           [("F1", "MAJOR", "open", "a"), ("F1", "NIT", "open", "b")])
        findings, err = S.parse_review_findings(self.feat)
        self.assertIsNone(findings)
        self.assertIn("重复", err)


# ─── 2 · severity 门槛(两向 · 单元) ───────────────────────────────────


class TestFindingsSeverityGate(unittest.TestCase):
    def setUp(self):
        self.feat = Path(tempfile.mkdtemp(prefix="tw-sevgate-"))

    def tearDown(self):
        shutil.rmtree(self.feat, ignore_errors=True)

    def _gate(self, verdict):
        return S._evidence_review_findings_gate({}, NS(feature=str(self.feat), verdict=verdict))

    def test_nr_with_open_major_passes(self):
        _write_findings_md(self.feat / "REVIEW.md", "NEEDS_REVISION",
                           [("F1", "MAJOR", "open", "确定性 bug")])
        ok, err = self._gate("NEEDS_REVISION")
        self.assertTrue(ok, err)

    def test_nr_minor_only_blocks_with_upgrade_hint(self):
        """全部 open finding 为 MINOR/NIT → NEEDS_REVISION 不合法(收敛核心规则)。"""
        _write_findings_md(self.feat / "REVIEW.md", "NEEDS_REVISION",
                           [("F1", "MINOR", "open", "改进"), ("F2", "NIT", "open", "风格")])
        ok, err = self._gate("NEEDS_REVISION")
        self.assertFalse(ok)
        self.assertIn("APPROVE", err)          # 指路:改 APPROVE(advisory 随行)
        self.assertIn("MAJOR", err)            # 或给出升级为 MAJOR 的依据

    def test_nr_fixed_major_open_minor_blocks(self):
        """open 的只剩 MINOR(MAJOR 已 fixed)→ 不能再打回。"""
        _write_findings_md(self.feat / "REVIEW.md", "NEEDS_REVISION",
                           [("F1", "MAJOR", "fixed", "已修"), ("F2", "MINOR", "open", "改进")])
        ok, _ = self._gate("NEEDS_REVISION")
        self.assertFalse(ok)

    def test_nr_without_findings_blocks(self):
        _write_findings_md(self.feat / "REVIEW.md", "NEEDS_REVISION", include_key=False)
        ok, err = self._gate("NEEDS_REVISION")
        self.assertFalse(ok)
        self.assertIn("必须列出 finding", err)

    def test_nr_empty_findings_blocks(self):
        _write_findings_md(self.feat / "REVIEW.md", "NEEDS_REVISION", findings=None)
        ok, _ = self._gate("NEEDS_REVISION")
        self.assertFalse(ok)

    def test_approve_with_open_blocker_blocks(self):
        _write_findings_md(self.feat / "REVIEW.md", "APPROVE",
                           [("F1", "BLOCKER", "open", "安全")])
        ok, err = self._gate("APPROVE")
        self.assertFalse(ok)
        self.assertIn("F1", err)

    def test_approve_with_open_minor_passes_as_advisory(self):
        _write_findings_md(self.feat / "REVIEW.md", "APPROVE",
                           [("F1", "MINOR", "open", "advisory"), ("F2", "NIT", "open", "风格")])
        ok, err = self._gate("APPROVE")
        self.assertTrue(ok, err)

    def test_approve_clean_no_findings_passes(self):
        _write_findings_md(self.feat / "REVIEW.md", "APPROVE", include_key=False)
        ok, err = self._gate("APPROVE")
        self.assertTrue(ok, err)

    def test_approve_all_resolved_passes(self):
        _write_findings_md(self.feat / "REVIEW.md", "APPROVE",
                           [("F1", "MAJOR", "fixed", "已修"),
                            ("F2", "BLOCKER", "rejected", "误报"),
                            ("F3", "MINOR", "deferred", "进 PENDING")])
        ok, err = self._gate("APPROVE")
        self.assertTrue(ok, err)

    def test_schema_error_blocks_both_verdicts(self):
        _write_findings_md(self.feat / "REVIEW.md", "APPROVE",
                           [("F1", "HUGE", "open", "非法枚举")])
        ok, err = self._gate("APPROVE")
        self.assertFalse(ok)
        self.assertIn("解析失败", err)


# ─── 3 · findings_ledger 跨轮合并(单元) ───────────────────────────────


class TestFindingsLedgerMerge(unittest.TestCase):
    def test_merge_overwrites_status_keeps_round_opened(self):
        contract: dict = {"rounds": [{"round": 1}]}
        r1 = contract["rounds"][0]
        S.merge_findings_ledger(contract, [
            {"id": "F1", "severity": "MAJOR", "status": "open", "title": "a", "source": "qa"},
            {"id": "F2", "severity": "MINOR", "status": "open", "title": "b", "source": "arch"},
        ], r1)
        self.assertEqual(r1["new_findings_count"], 2)
        self.assertEqual(r1["carried_open_count"], 0)

        r2 = {"round": 2}
        contract["rounds"].append(r2)
        S.merge_findings_ledger(contract, [
            {"id": "F1", "severity": "MAJOR", "status": "fixed", "title": "a", "source": "qa"},
            {"id": "F3", "severity": "NIT", "status": "open", "title": "c", "source": "external"},
        ], r2)
        ledger = {e["id"]: e for e in contract["findings_ledger"]}
        self.assertEqual(ledger["F1"]["status"], "fixed")          # 后轮覆盖
        self.assertEqual(ledger["F1"]["round_opened"], 1)          # 保留首现轮
        self.assertEqual(ledger["F1"]["last_updated_round"], 2)
        self.assertEqual(ledger["F2"]["status"], "open")           # 快照未含 → 原样保留
        self.assertEqual(ledger["F3"]["round_opened"], 2)
        self.assertEqual(r2["new_findings_count"], 1)              # 仅 F3 新
        self.assertEqual(r2["carried_open_count"], 1)              # F2 open 且 round_opened<2


# ─── 4 · 验证轮 brief 切换与内容(单元) ─────────────────────────────────


class TestVerifyRoundBrief(unittest.TestCase):
    def test_round1_brief_is_full_review_with_schema(self):
        b = S._review_brief({})
        self.assertIn("Review Stage", b)
        self.assertIn("findings 机读台账", b)
        self.assertIn("NEEDS_REVISION 须 ≥1 条 open BLOCKER/MAJOR", b)
        self.assertNotIn("验证轮", b.splitlines()[0])

    def test_round2_brief_switches_to_verify_round(self):
        state = {"stage_contracts": {"review": {
            "rounds": [
                {"round": 1, "review_commit": "abcdef1234567890", "verdict": "NEEDS_REVISION",
                 "fix_commit": "f" * 40},
                {"round": 2, "review_commit": None, "fix_commit": None},
            ],
            "findings_ledger": [
                {"id": "F1", "severity": "MAJOR", "status": "open",
                 "title": "缺校验", "source": "qa", "round_opened": 1},
                {"id": "F2", "severity": "NIT", "status": "rejected",
                 "title": "风格", "source": "external", "round_opened": 1},
            ],
        }}}
        b = S._review_brief(state)
        self.assertIn("验证轮", b)
        self.assertIn("禁全量重扫", b)
        self.assertIn("不得复提", b)                     # rejected 不复活
        self.assertIn("钟摆", b)                         # 方向相反 → 升暂停点
        self.assertIn("abcdef123456..HEAD", b)           # 修复 diff 范围锁定
        self.assertIn("--verify-fixes", b)               # external 增量频率
        self.assertIn("| F1 | MAJOR | open |", b)        # 台账注入
        self.assertIn("| F2 | NIT | rejected |", b)
        self.assertIn("为何首轮未发现", b)               # 新 finding 两来源之一

    def test_round2_brief_without_ledger_prompts_backfill(self):
        state = {"stage_contracts": {"review": {"rounds": [{"round": 1}, {"round": 2}]}}}
        b = S._review_brief(state)
        self.assertIn("验证轮", b)
        self.assertIn("台账为空", b)


# ─── 5 · 全流程:review-complete 门槛 + 台账 + 验证轮 + external 验证 ────


class _ReviewFlowCase(unittest.TestCase):
    """临时 git repo + review stage 就绪的 feature。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-revflow-"))
        _git(self.tmp, "init", "-b", "main")
        _git(self.tmp, "config", "user.email", "t@t.co")
        _git(self.tmp, "config", "user.name", "t")
        self.feat = self.tmp / "docs" / "features" / "F1"
        self.feat.mkdir(parents=True)
        (self.tmp / "seed.txt").write_text("seed", encoding="utf-8")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-m", "seed")
        (self.feat / "state.json").write_text(json.dumps({
            "feature_id": "F1", "flow_type": "Feature", "current_stage": "review",
            "merge_target": "main", "artifact_root": str(self.feat),
            "stage_contracts": {}, "completed_stages": [], "concerns": [],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        # review 产物齐(external 为异质命名 · 非 yolo 无实跑日志要求)
        (self.feat / "REVIEW-arch.md").write_text("# arch", encoding="utf-8")
        (self.feat / "REVIEW-qa.md").write_text("# qa", encoding="utf-8")
        ext = self.feat / "external-cross-review"
        ext.mkdir()
        (ext / "review-codex.md").write_text(
            "---\nreview_model: codex\n---\n# ext", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    @property
    def feat_rel(self) -> str:
        return "docs/features/F1"

    def _state(self) -> dict:
        return json.loads((self.feat / "state.json").read_text(encoding="utf-8"))

    def _complete(self, verdict: str, expect_exit: int = 0) -> dict:
        return _run_state(self.tmp, "review-complete", "--feature", self.feat_rel,
                          "--verdict", verdict, expect_exit=expect_exit)

    def _fix_and_touch_log(self, log: bool = True) -> None:
        """review-fix + (可选)写 fix 后 external 实跑日志(--verify-fixes 证据)。"""
        rc, head = _git(self.tmp, "rev-parse", "HEAD")
        _run_state(self.tmp, "review-fix", "--feature", self.feat_rel,
                   "--auto-commit", head)
        if log:
            d = self.feat / "external-review-prompts"
            d.mkdir(exist_ok=True)
            time.sleep(0.05)
            (d / "review-codex-20990101T000000Z.log").write_text("ran", encoding="utf-8")


class TestReviewCompleteGateFlow(_ReviewFlowCase):
    def test_nr_without_findings_fails_complete(self):
        _write_findings_md(self.feat / "REVIEW.md", "NEEDS_REVISION", include_key=False)
        d = self._complete("NEEDS_REVISION", expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        names = [e["name"] for e in d["failed_evidence"]]
        self.assertIn("findings_severity_gate", names)

    def test_nr_minor_only_fails_complete(self):
        _write_findings_md(self.feat / "REVIEW.md", "NEEDS_REVISION",
                           [("F1", "MINOR", "open", "改进")])
        d = self._complete("NEEDS_REVISION", expect_exit=1)
        names = [e["name"] for e in d["failed_evidence"]]
        self.assertIn("findings_severity_gate", names)

    def test_clean_approve_round1_passes_and_transitions(self):
        _write_findings_md(self.feat / "REVIEW.md", "APPROVE", include_key=False)
        d = self._complete("APPROVE")
        self.assertEqual(d["verdict"], "PASS")
        self.assertEqual(d["transitioned_to"], "test")

    def test_full_loop_ledger_verify_round_and_approve(self):
        """round1 NR(2 findings)→ fix → retry(验证轮 brief)→ round2 APPROVE(台账合并)。"""
        # round 1:MAJOR + MINOR 都 open → NEEDS_REVISION 合法
        _write_findings_md(self.feat / "REVIEW.md", "NEEDS_REVISION",
                           [("F1", "MAJOR", "open", "确定性 bug"),
                            ("F2", "MINOR", "open", "改进建议")])
        d = self._complete("NEEDS_REVISION")
        self.assertEqual(d["verdict"], "PASS")
        self.assertIsNone(d["transitioned_to"])
        st = self._state()
        rc = st["stage_contracts"]["review"]
        self.assertEqual(rc["rounds"][0]["new_findings_count"], 2)
        self.assertEqual(rc["rounds"][0]["carried_open_count"], 0)
        ledger = {e["id"]: e for e in rc["findings_ledger"]}
        self.assertEqual(ledger["F1"]["round_opened"], 1)

        # fix + fix 后 external 日志
        self._fix_and_touch_log()

        # retry → 验证轮 brief(范围锁定 + 台账)
        d = _run_state(self.tmp, "review-retry", "--feature", self.feat_rel)
        self.assertEqual(d["verdict"], "PASS")
        self.assertEqual(d["round"], 2)
        self.assertIn("验证轮", d["next_stage_brief"])
        self.assertIn("禁全量重扫", d["next_stage_brief"])
        self.assertIn("F1", d["next_stage_brief"])
        self.assertIn("--verify-fixes", d["next_stage_brief"])
        self.assertIn("验证轮", d["next_action_brief"])

        # round 2:F1 fixed · F2 仍 open(MINOR = advisory)→ APPROVE 合法
        _write_findings_md(self.feat / "REVIEW.md", "APPROVE",
                           [("F1", "MAJOR", "fixed", "确定性 bug"),
                            ("F2", "MINOR", "open", "改进建议")])
        d = self._complete("APPROVE")
        self.assertEqual(d["verdict"], "PASS")
        self.assertEqual(d["transitioned_to"], "test")
        st = self._state()
        rc = st["stage_contracts"]["review"]
        ledger = {e["id"]: e for e in rc["findings_ledger"]}
        self.assertEqual(ledger["F1"]["status"], "fixed")       # 后轮覆盖
        self.assertEqual(ledger["F1"]["round_opened"], 1)       # 首现轮保留
        self.assertEqual(rc["rounds"][1]["new_findings_count"], 0)
        self.assertEqual(rc["rounds"][1]["carried_open_count"], 1)  # F2 仍 open

    def test_approve_after_fix_requires_external_verify_log(self):
        """rounds≥2 + 有 fix + 无 fix 后 external 日志 → APPROVE FAIL(hint 指 --verify-fixes)。"""
        _write_findings_md(self.feat / "REVIEW.md", "NEEDS_REVISION",
                           [("F1", "MAJOR", "open", "bug")])
        self._complete("NEEDS_REVISION")
        self._fix_and_touch_log(log=False)   # 不写日志
        _run_state(self.tmp, "review-retry", "--feature", self.feat_rel)
        _write_findings_md(self.feat / "REVIEW.md", "APPROVE",
                           [("F1", "MAJOR", "fixed", "bug")])
        d = self._complete("APPROVE", expect_exit=1)
        failed = {e["name"]: e for e in d["failed_evidence"]}
        self.assertIn("external_verified_after_fix", failed)
        self.assertIn("--verify-fixes", failed["external_verified_after_fix"]["error"])
        # 补日志后 → PASS
        pd = self.feat / "external-review-prompts"
        pd.mkdir(exist_ok=True)
        time.sleep(0.05)
        (pd / "review-codex-20990101T000001Z.log").write_text("ran", encoding="utf-8")
        d = self._complete("APPROVE")
        self.assertEqual(d["verdict"], "PASS")

    def test_disable_external_skips_verify_after_fix_gate(self):
        """localconfig disable_external_review=true → fix 后无日志也可 APPROVE(单模型 opt-out)。"""
        (self.tmp / ".teamwork_localconfig.json").write_text(
            json.dumps({"disable_external_review": True}), encoding="utf-8")
        # ext 产物换降级自审(config-disabled 模式門禁接受)
        (self.feat / "external-cross-review" / "review-codex.md").write_text(
            "---\nreview_model: claude-self\ndegraded: true\nheterogeneous: false\n---\n# self",
            encoding="utf-8")
        _write_findings_md(self.feat / "REVIEW.md", "NEEDS_REVISION",
                           [("F1", "MAJOR", "open", "bug")])
        self._complete("NEEDS_REVISION")
        self._fix_and_touch_log(log=False)
        _run_state(self.tmp, "review-retry", "--feature", self.feat_rel)
        _write_findings_md(self.feat / "REVIEW.md", "APPROVE",
                           [("F1", "MAJOR", "fixed", "bug")])
        d = self._complete("APPROVE")
        self.assertEqual(d["verdict"], "PASS")


# ─── 6 · 轮次预算 + 升级暂停点 + --user-confirmed 逃生 ──────────────────


class TestReviewRoundBudget(_ReviewFlowCase):
    def _one_failed_round(self):
        _write_findings_md(self.feat / "REVIEW.md", "NEEDS_REVISION",
                           [("F1", "MAJOR", "open", "确定性 bug"),
                            ("F2", "NIT", "open", "命名风格")])
        self._complete("NEEDS_REVISION")
        self._fix_and_touch_log()

    def test_over_budget_retry_fails_with_pause_markdown(self):
        (self.tmp / ".teamwork_localconfig.json").write_text(
            json.dumps({"max_review_rounds": 1}), encoding="utf-8")
        self._one_failed_round()
        d = _run_state(self.tmp, "review-retry", "--feature", self.feat_rel,
                       expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        md = d["pause_options_markdown"]
        self.assertIn("⏸️ review 已 1 轮未收敛", md)
        self.assertIn("max_review_rounds=1", md)
        self.assertIn("- MAJOR:F1(确定性 bug)", md)   # 按 severity 分组列 id+title
        self.assertIn("- NIT:F2(命名风格)", md)
        self.assertIn("1. 仅修 BLOCKER/MAJOR 后收口 💡 推荐", md)
        self.assertIn("2. 继续完整修复", md)
        self.assertIn("3. 按现状 APPROVE", md)
        # 未放行 → 不加新 round
        st = self._state()
        self.assertEqual(len(st["stage_contracts"]["review"]["rounds"]), 1)

    def test_user_confirmed_without_reason_fails(self):
        (self.tmp / ".teamwork_localconfig.json").write_text(
            json.dumps({"max_review_rounds": 1}), encoding="utf-8")
        self._one_failed_round()
        d = _run_state(self.tmp, "review-retry", "--feature", self.feat_rel,
                       "--user-confirmed", expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("--reason", d["error"])

    def test_user_confirmed_with_reason_opens_round_and_warns(self):
        (self.tmp / ".teamwork_localconfig.json").write_text(
            json.dumps({"max_review_rounds": 1}), encoding="utf-8")
        self._one_failed_round()
        d = _run_state(self.tmp, "review-retry", "--feature", self.feat_rel,
                       "--user-confirmed", "--reason", "用户拍板:继续完整修复")
        self.assertEqual(d["verdict"], "PASS")
        self.assertEqual(d["round"], 2)
        st = self._state()
        self.assertTrue(any("review-retry 超预算放行" in c and "用户拍板" in c
                            for c in st["concerns"]),
                        f"concerns 缺超预算 WARN:{st['concerns']}")

    def test_within_budget_retry_needs_no_flag(self):
        """默认预算 3:round 1→2 正常开 · 无需 --user-confirmed。"""
        self._one_failed_round()
        d = _run_state(self.tmp, "review-retry", "--feature", self.feat_rel)
        self.assertEqual(d["verdict"], "PASS")
        self.assertEqual(d["round"], 2)
        self.assertEqual(d["max_review_rounds"], 3)

    def test_test_retry_unaffected_by_budget(self):
        """预算仅 review:test-retry 不受 max_review_rounds 影响(无该参数逻辑)。"""
        (self.tmp / ".teamwork_localconfig.json").write_text(
            json.dumps({"max_review_rounds": 1}), encoding="utf-8")
        # 直接单元验证:_localconfig_max_review_rounds 只被 review 分支消费
        self.assertEqual(E._localconfig_max_review_rounds(self.feat), 1)


class TestBudgetHelpers(unittest.TestCase):
    def test_default_when_no_localconfig(self):
        d = Path(tempfile.mkdtemp())
        (d / ".git").mkdir()
        self.assertEqual(E._localconfig_max_review_rounds(d), E.DEFAULT_MAX_REVIEW_ROUNDS)
        self.assertEqual(E.DEFAULT_MAX_REVIEW_ROUNDS, 3)

    def test_localconfig_override_and_invalid_fallback(self):
        d = Path(tempfile.mkdtemp())
        (d / ".git").mkdir()
        cfg = d / ".teamwork_localconfig.json"
        cfg.write_text(json.dumps({"max_review_rounds": 5}), encoding="utf-8")
        sub = d / "docs" / "features" / "F1"
        sub.mkdir(parents=True)
        self.assertEqual(E._localconfig_max_review_rounds(sub), 5)
        cfg.write_text(json.dumps({"max_review_rounds": 0}), encoding="utf-8")
        self.assertEqual(E._localconfig_max_review_rounds(sub), 3)
        cfg.write_text(json.dumps({"max_review_rounds": "many"}), encoding="utf-8")
        self.assertEqual(E._localconfig_max_review_rounds(sub), 3)

    def test_pause_markdown_groups_by_severity(self):
        md = E._build_review_budget_pause(3, 3, [
            {"id": "F1", "severity": "BLOCKER", "status": "open", "title": "安全"},
            {"id": "F2", "severity": "MINOR", "status": "open", "title": "改进"},
            {"id": "F3", "severity": "MAJOR", "status": "fixed", "title": "已修"},
        ])
        self.assertIn("已 3 轮未收敛", md)
        self.assertIn("- BLOCKER:F1(安全)", md)
        self.assertIn("- MINOR:F2(改进)", md)
        self.assertNotIn("F3", md)   # 非 open 不列
        self.assertIn("请选择:", md)


if __name__ == "__main__":
    unittest.main(verbosity=2)
