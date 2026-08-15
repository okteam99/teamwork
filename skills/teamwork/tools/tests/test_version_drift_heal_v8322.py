"""升级传导:版本漂移入口自愈。

case(supersdk 实证):skill 全局副本静默升 37 版 · per-project bootstrap 20 天没跑 ·
`last_update_check_result` 还在说 up_to_date · 台账 61% 旧列宽 · gitignore 水位停在
三十版前 ——「提示用户去跑 bootstrap」被证明不发生。

治法(与 scratch 清理同构:挂在积灰机器自己会跑到的命令上):
- state.py 入口 best-effort 自愈:台账 schema(表头+旧行补宽)+ gitignore 重放 + marker;
- 重量级(chmod/hooks/host 注入/升级 R5)仍归 session bootstrap,不越权;
- state.json 写路径盖 `_schema_version`,读路径只拦「来自未来」。
"""
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
TOOLS = SKILL_ROOT / "tools"
STATE_PY = TOOLS / "state.py"
sys.path.insert(0, str(TOOLS))

from _v8_engine import (  # noqa: E402
    STATE_SCHEMA_VERSION,
    heal_version_drift,
    load_state,
    locate_localconfig,
    migrate_process_ledger,
    read_skill_frontmatter_version,
    save_state,
)

OLD_HDR = "| Feature | 类型 | 实走 | a | b | 反思摘要 |"
OLD_SEP = "|---|---|---|---|---|---|"
OLD_ROW = "| X-F001 | Feature | goal→dev | 1 | 2 | 旧反思 |"
CANON_HDR = "| Feature | 类型 | 实走 | a | b | 反思摘要 | 各阶段耗时 | 宿主 | ⏱️ 耗时归因 |"
CANON_SEP = "|---|---|---|---|---|---|---|---|---|"
FULL_ROW = "| X-F002 | Feature | goal→ship | 1 | 2 | 新反思 | goal 3m | codex-cli | 0/3 |"


def _fake_skill(version="v8.900.1"):
    d = Path(tempfile.mkdtemp(prefix="skill-"))
    (d / "SKILL.md").write_text(f"---\nname: teamwork\nversion: {version}\n---\n# t\n",
                                encoding="utf-8")
    (d / "templates").mkdir()
    (d / "templates" / "process-ledger.md").write_text(
        f"# 模板\n\n{CANON_HDR}\n{CANON_SEP}\n", encoding="utf-8")
    return d


def _consumer(marker_version="v8.100.1", marker=True, ledger=True):
    d = Path(tempfile.mkdtemp(prefix="proj-"))
    subprocess.run(["git", "-C", str(d), "init", "-q"], capture_output=True, check=True)
    cfg = {"worktree": "auto"}
    if marker:
        cfg["_bootstrap"] = {"skill_version": marker_version, "host": "codex-cli"}
    (d / ".teamwork_localconfig.json").write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if ledger:
        (d / "project-specs").mkdir()
        (d / "project-specs" / "PROCESS-LEDGER.md").write_text(
            f"# 台账\n\n{OLD_HDR}\n{OLD_SEP}\n{OLD_ROW}\n{FULL_ROW}\n\n后记\n",
            encoding="utf-8")
    return d


class TestHealVersionDrift(unittest.TestCase):

    def test_drift_heals_ledger_gitignore_marker(self):
        skill, proj = _fake_skill(), _consumer()
        res = heal_version_drift(proj, skill)
        self.assertIsNotNone(res)
        self.assertEqual(res["from"], "v8.100.1")
        self.assertEqual(res["to"], "v8.900.1")
        body = (proj / "project-specs" / "PROCESS-LEDGER.md").read_text(encoding="utf-8")
        lines = body.splitlines()
        self.assertIn(CANON_HDR, lines)                       # 表头升级
        row = next(l for l in lines if l.startswith("| X-F001 |"))
        self.assertTrue(row.startswith(OLD_ROW))              # 内容前缀逐字不动
        self.assertEqual(row.count("|") - 1, 9)               # 补 — 到表头宽
        self.assertIn(FULL_ROW, lines)                        # 满宽行逐字不动
        self.assertIn("后记", body)                            # 表外正文不动
        gi = (proj / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".teamwork-scratch*", gi)               # gitignore 水位重放
        cfg = json.loads((proj / ".teamwork_localconfig.json").read_text(encoding="utf-8"))
        sm = cfg["_bootstrap"]["state_migrate"]
        self.assertEqual((sm["from"], sm["to"]), ("v8.100.1", "v8.900.1"))
        self.assertEqual(cfg["_bootstrap"]["skill_version"], "v8.100.1")  # 不冒充 full bootstrap

    def test_second_call_noop(self):
        skill, proj = _fake_skill(), _consumer()
        heal_version_drift(proj, skill)
        before = (proj / ".teamwork_localconfig.json").read_text(encoding="utf-8")
        self.assertIsNone(heal_version_drift(proj, skill))    # state_migrate.to 命中 → 快路径
        self.assertEqual((proj / ".teamwork_localconfig.json").read_text(encoding="utf-8"), before)

    def test_no_marker_not_taken_over(self):
        """从未 bootstrap 的项目不接管 —— 首铺归 session bootstrap。"""
        skill, proj = _fake_skill(), _consumer(marker=False)
        before = (proj / ".teamwork_localconfig.json").read_text(encoding="utf-8")
        self.assertIsNone(heal_version_drift(proj, skill))
        self.assertEqual((proj / ".teamwork_localconfig.json").read_text(encoding="utf-8"), before)

    def test_version_equal_noop(self):
        skill = _fake_skill("v8.100.1")
        proj = _consumer("v8.100.1")
        self.assertIsNone(heal_version_drift(proj, skill))

    def test_skill_inside_project_guarded(self):
        """框架仓自身/内嵌开发 → 不自愈(同 bootstrap 跨仓污染守卫)。"""
        proj = _consumer()
        inner = proj / "skills" / "teamwork"
        inner.mkdir(parents=True)
        (inner / "SKILL.md").write_text("---\nversion: v8.900.1\n---\n", encoding="utf-8")
        self.assertIsNone(heal_version_drift(proj, inner))

    def test_no_localconfig_noop(self):
        d = Path(tempfile.mkdtemp(prefix="bare-"))
        subprocess.run(["git", "-C", str(d), "init", "-q"], capture_output=True, check=True)
        self.assertIsNone(heal_version_drift(d, _fake_skill()))


class TestMigrateLedgerCore(unittest.TestCase):

    def test_pad_only_when_header_already_canonical(self):
        """supersdk 形态:表头已最新 · 旧行仍短 → 只补行。"""
        skill = _fake_skill()
        proj = _consumer()
        led = proj / "project-specs" / "PROCESS-LEDGER.md"
        led.write_text(f"{CANON_HDR}\n{CANON_SEP}\n{OLD_ROW}\n{FULL_ROW}\n", encoding="utf-8")
        res = migrate_process_ledger(led, skill)
        self.assertTrue(res["changed"])
        self.assertFalse(res["migrated_header"])
        self.assertEqual(res["padded_rows"], 1)
        res2 = migrate_process_ledger(led, skill)             # 幂等
        self.assertFalse(res2["changed"])
        self.assertEqual(res2["padded_rows"], 0)

    def test_overwide_and_malformed_rows_untouched(self):
        """只补不裁:超宽行/无尾竖线行逐字不动。"""
        skill = _fake_skill()
        proj = _consumer()
        over = FULL_ROW + " 多 | 出 |"
        broken = "| X-F003 | 断行没有尾竖线"
        led = proj / "project-specs" / "PROCESS-LEDGER.md"
        led.write_text(f"{CANON_HDR}\n{CANON_SEP}\n{over}\n{broken}\n", encoding="utf-8")
        migrate_process_ledger(led, skill)
        body = led.read_text(encoding="utf-8")
        self.assertIn(over, body.splitlines())
        self.assertIn(broken, body.splitlines())

    def test_no_ledger_skip(self):
        self.assertEqual(
            migrate_process_ledger(Path(tempfile.mkdtemp()) / "PROCESS-LEDGER.md",
                                   _fake_skill())["status"], "skip")


class TestEntryHook(unittest.TestCase):
    """真跑 state.py:自愈在任何命令前发生 · 输出走 stderr 不污染 stdout JSON。"""

    def test_state_py_heals_before_command(self):
        proj = _consumer()                                    # marker v8.100.1 vs 真 skill 版本 → 漂移
        r = subprocess.run([sys.executable, str(STATE_PY), "ledger-migrate"],
                           cwd=str(proj), capture_output=True, text=True, timeout=30)
        self.assertIn("version-drift-healed", r.stderr)
        json.loads(r.stdout)                                  # stdout 仍是纯 JSON
        cfg = json.loads((proj / ".teamwork_localconfig.json").read_text(encoding="utf-8"))
        current = read_skill_frontmatter_version(SKILL_ROOT)
        self.assertEqual(cfg["_bootstrap"]["state_migrate"]["to"], current)
        row = next(l for l in (proj / "project-specs" / "PROCESS-LEDGER.md")
                   .read_text(encoding="utf-8").splitlines() if l.startswith("| X-F001 |"))
        canon_width = row.count("|") - 1
        self.assertGreater(canon_width, 6)                    # 已按真模板宽补齐

    def test_fixture_without_marker_stays_silent(self):
        proj = _consumer(marker=False)
        r = subprocess.run([sys.executable, str(STATE_PY), "ledger-migrate"],
                           cwd=str(proj), capture_output=True, text=True, timeout=30)
        self.assertNotIn("version-drift-healed", r.stderr)


class TestSchemaVersionStamp(unittest.TestCase):

    def test_save_state_stamps(self):
        d = Path(tempfile.mkdtemp(prefix="st-"))
        p = d / "state.json"
        save_state(p, {"feature_id": "X-F001"})
        data = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(data["_schema_version"], STATE_SCHEMA_VERSION)
        self.assertTrue(data["_state_checksum"].startswith("sha256:"))

    def test_atomic_write_stamps(self):
        import state as state_mod
        d = Path(tempfile.mkdtemp(prefix="st-"))
        p = d / "state.json"
        state_mod.atomic_write(p, {"feature_id": "X-F001"})
        data = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(data["_schema_version"], STATE_SCHEMA_VERSION)

    def test_load_state_rejects_future_schema(self):
        d = Path(tempfile.mkdtemp(prefix="st-"))
        (d / "state.json").write_text(
            json.dumps({"feature_id": "X", "_schema_version": STATE_SCHEMA_VERSION + 99}),
            encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as cm:
                load_state(str(d))
            self.assertEqual(cm.exception.code, 2)

    def test_load_state_accepts_past_and_missing(self):
        d = Path(tempfile.mkdtemp(prefix="st-"))
        (d / "state.json").write_text(json.dumps({"feature_id": "X"}), encoding="utf-8")
        _, st = load_state(str(d))
        self.assertEqual(st["feature_id"], "X")

    def test_locate_localconfig_returns_path(self):
        proj = _consumer()
        self.assertEqual(locate_localconfig(proj),
                         (proj / ".teamwork_localconfig.json").resolve())


if __name__ == "__main__":
    unittest.main()
