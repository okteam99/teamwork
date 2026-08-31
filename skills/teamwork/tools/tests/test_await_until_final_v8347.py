"""await-merge 后台化时会自己退出(实证 case)。

case(aon-core SVC-CORE-B260831064524):消费 AI 按 spec 用 `nohup ... >> /tmp/` 后台启动
await-merge,9 分钟窗口用尽 emit WAITING 后 sys.exit —— WAITING 里那句「AI 应自动重跑」
进了没人读的文件,监控就此永久结束;人几分钟后才点合并,ship2 只能手动补跑。

根因两层:
① **窗口按错的对象定**:默认 18×30s=9min,而等的是「人去平台点合并」—— 小时级
   (框架自己的原始痛点数据是 132h 长尾)· 差三个数量级;
② **载体缺口来自运行姿态**:命令从没说过自己必须在前台跑,而 spec 明确让它「后台启动」——
   于是「AI 应自动重跑」这句承诺在后台没有任何东西接得住(形容词式承诺的又一变体:
   这次不是措辞糊,是**执行姿态**把载体拿掉了)。
"""
import subprocess
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

import _v8_ship as SH        # noqa: E402

STATE_PY = str(SKILL_ROOT / "tools" / "state.py")
SHIP_MD = SKILL_ROOT / "stages" / "ship-stage.md"


class TestDefaultWindow(unittest.TestCase):

    def test_default_window_is_hour_scale(self):
        """等人点合并是小时级 —— 9 分钟的默认值在实证里跑输给了人的反应时间。"""
        self.assertEqual(SH.AWAIT_MERGE_DEFAULT_CHECKS, 120)
        self.assertGreaterEqual(SH.AWAIT_MERGE_DEFAULT_CHECKS * 30 / 60, 60)  # ≥1h

    def test_cli_default_matches_constant(self):
        out = subprocess.run([sys.executable, STATE_PY, "await-merge", "--help"],
                             capture_output=True, text=True, timeout=30).stdout
        flat = " ".join(out.split())
        self.assertIn(str(SH.AWAIT_MERGE_DEFAULT_CHECKS), flat)
        self.assertIn("--until-final", flat)


class TestBackgroundedWarning(unittest.TestCase):
    """非 tty 且未加 --until-final → WAITING 必须说破「我不会自己续等」。"""

    @classmethod
    def setUpClass(cls):
        import json
        r = subprocess.run(
            [sys.executable, STATE_PY, "await-merge",
             "--mr-url", "https://github.com/nonexistent-owner/nonexistent-repo/pull/1",
             "--interval", "5", "--max-checks", "1"],
            capture_output=True, text=True, timeout=120)
        cls.out = json.loads(r.stdout)

    def test_exits_waiting_not_crash(self):
        self.assertEqual(self.out["verdict"], "WAITING")
        self.assertIn("waited_minutes", self.out)      # 等了多久要写出来 · 否则看不出窗口多短

    def test_warning_names_the_mechanism_and_the_fix(self):
        w = self.out.get("backgrounded_warning", "")
        self.assertTrue(w, "非 tty 必须带警告")
        self.assertIn("不是 tty", w)
        self.assertIn("不会自己续等", w)
        self.assertIn("--until-final", w)              # 给出口 · 不是只报告问题

    def test_warning_absent_when_interactive(self):
        """前台跑时不该噪 —— 警告只对真出问题的姿态发。"""
        import inspect
        src = inspect.getsource(SH.cmd_await_merge)
        self.assertIn("backgrounded = not sys.stdout.isatty()", src)
        self.assertIn("if backgrounded else {}", src)


class TestUntilFinalLoop(unittest.TestCase):

    def test_until_final_ignores_max_checks(self):
        import inspect
        src = inspect.getsource(SH.cmd_await_merge)
        self.assertIn("if not until_final and i >= max_checks:", src)
        self.assertIn("if until_final or i < max_checks - 1:", src)   # 末轮也要 sleep

    def test_terminal_states_still_exit(self):
        """自续等不能变成永不退出 —— MERGED/CLOSED/CI 归因到自己仍是终态。"""
        import inspect
        src = inspect.getsource(SH.cmd_await_merge)
        for v in ('"MERGED"', '"CLOSED"', '"CI_FAILING"'):
            self.assertIn(v, src, v)


class TestCarriersSynced(unittest.TestCase):
    """三处载体必须同步 —— spec 让后台跑、emit 抄给用户、命令自己;漏一处就复发。"""

    def test_spec_tells_background_runs_to_use_until_final(self):
        t = SHIP_MD.read_text(encoding="utf-8")
        self.assertIn("--until-final", t)
        self.assertIn("后台跑必须带 `--until-final`", t)
        self.assertIn("等待窗按「等的是什么」定", t)

    def test_push_emit_command_text_carries_flag(self):
        """截图 case 里消费 AI 抄的就是 emit 里这句 —— 它不带 flag,后面全错。"""
        src = (SKILL_ROOT / "tools" / "_v8_ship.py").read_text(encoding="utf-8")
        self.assertIn("await-merge --feature <本路径> --until-final", src)
        self.assertIn("`await-merge --until-final` 30s 轮询", src)   # 用户卡片

    def test_why_recorded_as_posture_not_wording(self):
        t = SHIP_MD.read_text(encoding="utf-8")
        self.assertIn("载体缺口可以是运行姿态造成的", t)


if __name__ == "__main__":
    unittest.main()
