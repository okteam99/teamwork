"""本地测试与 MR CI 同构性对照(实证 case)。

case(aon-main DEV-F260830125314):TEST-REPORT 只记录 `cargo check -p aon-api-gateway`
(只验编译),而 MR CI 跑的是 `cd services && cargo clippy --locked -- -D warnings`
—— 一条 clippy 漏到 CI 才炸,MR 窗口期多烧一整轮。

🔴 关键细节(决定了修法):那个 AI **试过** grep CI 配置,但猜的是
`.gitlab-ci.yml .gitlab/ci/*.yml` → 返回空;真配置在 GitLab include 进来的
`infra/ci/api-gateway.yml`。所以这不是「AI 偷懒」,是**它不知道去哪儿找** ——
该由机器把清单端出来(v8.323「数据算好别让人誊抄」),而不是让每个 AI 自己猜路径。

设计刻意的边界:**不要求本地跑 CI 全集**(有些 job 要 infra 凭据 / 太慢,强行复现是纯税)。
要求的是「看过 + 对每条给出处置」,且**跑不了的必须显式列出** —— 那就是「已知会在 CI
才发现」的清单,写出来风险才可见(v8.337 零也显式)。
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

from _v8_engine import scan_ci_commands          # noqa: E402

STATE_PY = str(SKILL_ROOT / "tools" / "state.py")


class TestScanner(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def _w(self, rel, text):
        f = self.tmp / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")

    def test_finds_gitlab_include_layout(self):
        """本 case 的形状:真命令在 include 进来的 infra/ci/*.yml,不在根 .gitlab-ci.yml。"""
        self._w(".gitlab-ci.yml", "include:\n  - local: infra/ci/api-gateway.yml\n")
        self._w("infra/ci/api-gateway.yml",
                "lint:\n  stage: lint\n  script:\n"
                "    - rustup component add clippy\n"
                "    - cd services && cargo clippy --locked -- -D warnings\n")
        r = scan_ci_commands(self.tmp)
        cmds = [c for cs in r.values() for _, c in cs]
        self.assertIn("cd services && cargo clippy --locked -- -D warnings", cmds)

    def test_finds_github_workflows(self):
        self._w(".github/workflows/ci.yml",
                "jobs:\n  t:\n    steps:\n      - run: cargo test --locked\n")
        cmds = [c for cs in scan_ci_commands(self.tmp).values() for _, c in cs]
        self.assertIn("cargo test --locked", cmds)

    def test_yaml_keys_are_not_commands(self):
        """`stage: lint` / `name: Build` 是 YAML 键,不是命令 —— 混进来会淹掉真命令。"""
        self._w(".gitlab-ci.yml",
                "lint:\n  stage: lint\n  name: Build\n  script:\n    - npm run lint\n")
        cmds = [c for cs in scan_ci_commands(self.tmp).values() for _, c in cs]
        self.assertIn("npm run lint", cmds)
        self.assertNotIn("stage: lint", cmds)
        self.assertNotIn("name: Build", cmds)

    def test_only_gate_commands_not_deploy(self):
        """部署/发布类不是本地该复现的 —— 收进来只会让清单没法看。"""
        self._w(".gitlab-ci.yml",
                "a:\n  script:\n    - kubectl apply -f k8s/\n    - npm test\n")
        cmds = [c for cs in scan_ci_commands(self.tmp).values() for _, c in cs]
        self.assertIn("npm test", cmds)
        self.assertFalse([c for c in cmds if c.startswith("kubectl apply")])

    def test_line_numbers_reported(self):
        """要给文件:行 —— 否则 AI 还得自己再找一遍(等于没端清单)。"""
        self._w(".gitlab-ci.yml", "a:\n  script:\n    - npm test\n")
        (ln, cmd), = [(ln, c) for cs in scan_ci_commands(self.tmp).values() for ln, c in cs]
        self.assertEqual(ln, 3)

    def test_no_ci_config_returns_empty(self):
        self.assertEqual(scan_ci_commands(self.tmp), {})

    def test_skips_vendor_and_worktree(self):
        self._w("node_modules/x/.github/workflows/a.yml", "jobs:\n  t:\n    steps:\n      - run: npm test\n")
        self._w(".worktree/F1/.gitlab-ci.yml", "a:\n  script:\n    - npm test\n")
        self.assertEqual(scan_ci_commands(self.tmp), {})


class TestCommand(unittest.TestCase):

    def test_cli_emits_commands_and_next_action(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / ".gitlab-ci.yml").write_text(
            "a:\n  script:\n    - cargo clippy --locked -- -D warnings\n", encoding="utf-8")
        r = subprocess.run([sys.executable, STATE_PY, "ci-commands", "--root", str(tmp)],
                           capture_output=True, text=True, timeout=60)
        d = json.loads(r.stdout)
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["gate_commands"], 1)
        self.assertIn("本地已跑", d["next_action"])
        self.assertIn("跑不了的也要写", d["next_action"])

    def test_cli_handles_repo_without_ci(self):
        tmp = Path(tempfile.mkdtemp())
        r = subprocess.run([sys.executable, STATE_PY, "ci-commands", "--root", str(tmp)],
                           capture_output=True, text=True, timeout=60)
        d = json.loads(r.stdout)
        self.assertEqual(d["config_files"], 0)
        self.assertIn("无 CI 配置", d["next_action"])   # 不是报错 · 给可写的处置


class TestCarriers(unittest.TestCase):

    def test_test_brief_carries_it_at_consumption_point(self):
        from _v8_stage_specs import TEST_SPEC
        b = TEST_SPEC.brief_template_fn({})
        self.assertIn("CI 门禁对照", b)
        self.assertIn("ci-commands", b)
        self.assertIn("跑不了", b)
        self.assertIn("别自己猜 CI 配置路径", b)      # case 的关键细节要在动作点说

    def test_stage_rule_states_the_boundary(self):
        t = (SKILL_ROOT / "stages" / "test-stage.md").read_text(encoding="utf-8")
        seg = t.split("CI 门禁对照", 1)[1].split("\n3. ")[0]
        self.assertIn("不要求本地跑全集", seg)         # 边界:防它长成新的税
        self.assertIn("零也显式", seg)
        self.assertIn("这一条是防", seg)               # 与 ship 侧归因(治)的分工

    def test_report_template_has_the_slot(self):
        t = (SKILL_ROOT / "templates" / "test-report.md").read_text(encoding="utf-8")
        self.assertIn("§2.5 CI 门禁对照", t)
        self.assertIn("⚠️ 跑不了", t)                  # 三态槽位 · 不是自由文本
        self.assertIn("已知会在 CI 才发现", t)

    def test_ship_side_attribution_untouched(self):
        """防与治不重叠:ship 的 CI 归因(v8.345)不因本版变化。"""
        from _v8_ship import attribute_ci_failures
        r = attribute_ci_failures(["build"], {"build"}, True)
        self.assertEqual(r["pre_existing"], ["build"])


if __name__ == "__main__":
    unittest.main()
