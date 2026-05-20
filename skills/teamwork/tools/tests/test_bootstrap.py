#!/usr/bin/env python3
"""bootstrap.py 回归套件(P0-13 治本 · session 启动 silent 系统维护)。

覆盖:
- find_project_root(主 tree / worktree → 都回主 tree)
- read_skill_version(ok / missing / no-frontmatter / version-field-missing)
- maintain_project_skeletons(创建/已存在/失败)
- check_host_injection(注入段 ok / missing / file_missing)
- scan_v7_state_json(v7 / v8 / 混合)
- cmd_session_bootstrap 端到端(silent emit JSON)

运行:
    python3 -m pytest skills/teamwork/tools/tests/test_bootstrap.py -v
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
SKILL = TOOLS.parent
BOOTSTRAP_PY = TOOLS / "bootstrap.py"

sys.path.insert(0, str(TOOLS))


def make_git_repo(path: Path) -> None:
    """初始化 git repo + 1 commit · 让 find_project_root 找到 .git。"""
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True)
    (path / "init.txt").write_text("init", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "init"], cwd=path, check=True,
        capture_output=True,
    )


# ─── find_project_root ────────────────────────────────────


class TestFindProjectRoot(unittest.TestCase):
    """主 tree / worktree 都应返回主 tree(共享骨架文档)。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.maintree = self.tmp / "main"
        self.maintree.mkdir()
        make_git_repo(self.maintree)
        self.wt = self.tmp / "wt"
        subprocess.run(
            ["git", "worktree", "add", "-b", "feature/x", str(self.wt)],
            cwd=self.maintree, check=True, capture_output=True,
        )

    def tearDown(self):
        subprocess.run(
            ["git", "-C", str(self.maintree), "worktree", "remove", "--force", str(self.wt)],
            capture_output=True,
        )
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_main_tree_returns_main(self):
        from bootstrap import find_project_root
        root = find_project_root(self.maintree)
        self.assertEqual(root.resolve(), self.maintree.resolve())

    def test_worktree_returns_main_tree(self):
        """worktree 内跑 · 应返回主 tree(共享骨架)。"""
        from bootstrap import find_project_root
        root = find_project_root(self.wt)
        # git rev-parse --git-common-dir 应指向主 tree 的 .git
        self.assertEqual(root.resolve(), self.maintree.resolve())


# ─── read_skill_version ──────────────────────────────────


class TestReadSkillVersion(unittest.TestCase):
    """版本号自读 SKILL.md frontmatter(单源 · 不由 AI 传 · 治本 case)。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_reads_version_from_frontmatter(self):
        from bootstrap import read_skill_version
        (self.tmp / "SKILL.md").write_text(
            "---\nname: teamwork\nversion: v8.0.0\n---\n# body\n", encoding="utf-8",
        )
        result = read_skill_version(self.tmp)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["version"], "v8.0.0")

    def test_skill_md_not_found(self):
        from bootstrap import read_skill_version
        result = read_skill_version(self.tmp)
        self.assertEqual(result["status"], "skill_md_not_found")
        self.assertIsNone(result["version"])

    def test_no_frontmatter(self):
        from bootstrap import read_skill_version
        (self.tmp / "SKILL.md").write_text("# no frontmatter\n", encoding="utf-8")
        result = read_skill_version(self.tmp)
        self.assertEqual(result["status"], "no_frontmatter")
        self.assertIsNone(result["version"])

    def test_version_field_missing(self):
        from bootstrap import read_skill_version
        (self.tmp / "SKILL.md").write_text(
            "---\nname: teamwork\n---\n# body\n", encoding="utf-8",
        )
        result = read_skill_version(self.tmp)
        self.assertEqual(result["status"], "version_field_missing")
        self.assertIsNone(result["version"])


# ─── maintain_project_skeletons ──────────────────────────


class TestMaintainProjectSkeletons(unittest.TestCase):
    """骨架文档检查/创建(幂等)。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.skill_root = self.tmp / "skill"
        self.templates_dir = self.skill_root / "templates"
        self.templates_dir.mkdir(parents=True)
        # 模拟 templates
        for name in ["knowledge.md", "troubleshooting.md", "glossary.md"]:
            (self.templates_dir / name).write_text(f"# {name}", encoding="utf-8")

        self.project_root = self.tmp / "project"
        self.project_root.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_all_created_on_fresh_project(self):
        from bootstrap import maintain_project_skeletons
        result = maintain_project_skeletons(self.skill_root, self.project_root)
        self.assertEqual(
            sorted(result["created"]),
            ["GLOSSARY.md", "KNOWLEDGE.md", "TROUBLESHOOTING.md"],
        )
        self.assertEqual(result["existed"], [])
        self.assertEqual(result["migrated"], [])
        self.assertEqual(result["failed"], [])
        # 实际文件创建在 project-specs/ 下 · 不散在仓库根
        specs = self.project_root / "project-specs"
        for name in ["KNOWLEDGE.md", "TROUBLESHOOTING.md", "GLOSSARY.md"]:
            self.assertTrue((specs / name).exists(), f"project-specs/{name} 未创建")
            self.assertFalse((self.project_root / name).exists(), f"{name} 不应散在仓库根")

    def test_idempotent_existed(self):
        """重复跑 · project-specs/ 下已存在文件不重创建。"""
        from bootstrap import maintain_project_skeletons
        specs = self.project_root / "project-specs"
        specs.mkdir()
        (specs / "KNOWLEDGE.md").write_text("user content", encoding="utf-8")

        result = maintain_project_skeletons(self.skill_root, self.project_root)
        self.assertIn("KNOWLEDGE.md", result["existed"])
        self.assertNotIn("KNOWLEDGE.md", result["created"])
        self.assertNotIn("KNOWLEDGE.md", result["migrated"])
        # 用户内容未被覆盖
        self.assertEqual(
            (specs / "KNOWLEDGE.md").read_text(encoding="utf-8"),
            "user content",
        )

    def test_migrates_legacy_root_files(self):
        """仓库根遗留旧散放文件 → 自动迁移进 project-specs/。"""
        from bootstrap import maintain_project_skeletons
        (self.project_root / "KNOWLEDGE.md").write_text("legacy content", encoding="utf-8")

        result = maintain_project_skeletons(self.skill_root, self.project_root)
        self.assertIn("KNOWLEDGE.md", result["migrated"])
        self.assertNotIn("KNOWLEDGE.md", result["created"])
        # 旧散放文件已移走 · 内容保留在 project-specs/
        self.assertFalse((self.project_root / "KNOWLEDGE.md").exists())
        self.assertEqual(
            (self.project_root / "project-specs" / "KNOWLEDGE.md").read_text(encoding="utf-8"),
            "legacy content",
        )

    def test_template_not_found_fails(self):
        """templates/ 缺骨架模板 → failed list 记录。"""
        from bootstrap import maintain_project_skeletons
        # 删 templates 中的 knowledge.md
        (self.templates_dir / "knowledge.md").unlink()

        result = maintain_project_skeletons(self.skill_root, self.project_root)
        self.assertEqual(len(result["failed"]), 1)
        self.assertEqual(result["failed"][0]["doc"], "KNOWLEDGE.md")
        self.assertIn("template not found", result["failed"][0]["reason"])

    def test_workspace_migrate_legacy(self):
        """legacy 下划线 teamwork_space.md → 连字符 teamwork-space.md。"""
        from bootstrap import maintain_workspace_filename
        (self.project_root / "teamwork_space.md").write_text("registry", encoding="utf-8")
        result = maintain_workspace_filename(self.project_root)
        self.assertEqual(result["status"], "migrated")
        self.assertTrue((self.project_root / "teamwork-space.md").exists())
        self.assertFalse((self.project_root / "teamwork_space.md").exists())
        self.assertEqual(
            (self.project_root / "teamwork-space.md").read_text(encoding="utf-8"),
            "registry",
        )

    def test_workspace_already_canonical(self):
        """已是连字符名 → ok · 不动。"""
        from bootstrap import maintain_workspace_filename
        (self.project_root / "teamwork-space.md").write_text("x", encoding="utf-8")
        self.assertEqual(
            maintain_workspace_filename(self.project_root)["status"], "ok")

    def test_workspace_none_is_na(self):
        """单项目仓库无 workspace 文件 → n_a。"""
        from bootstrap import maintain_workspace_filename
        self.assertEqual(
            maintain_workspace_filename(self.project_root)["status"], "n_a")


# ─── maintain_host_injection ─────────────────────────────


class TestMaintainHostInjection(unittest.TestCase):
    """CLAUDE.md / AGENTS.md / GEMINI.md 注入段同步(改 check → maintain)。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_host_unknown(self):
        from bootstrap import maintain_host_injection
        result = maintain_host_injection(self.tmp, self.tmp, "unknown", "v8.x")
        self.assertEqual(result["status"], "host_unknown")

    def test_skipped_when_sync_drift_missing(self):
        """skill_root 不含 sync-drift.py → skipped(不阻塞)。"""
        from bootstrap import maintain_host_injection
        # tmp 当 skill_root 用 · 不含 tools/sync-drift.py
        result = maintain_host_injection(self.tmp, self.tmp, "claude-code", "v8.x")
        self.assertEqual(result["status"], "skipped")

    def test_other_host_files_skipped_when_absent(self):
        """v8.14:非当前 host 文件不存在 → skipped_not_present(不主动建)。

        模拟真实 skill_root + project_root + 仅有 CLAUDE.md(无 AGENTS / GEMINI)。
        """
        from bootstrap import maintain_host_injection
        # 用真实 skill 仓库 sync-drift + 模板
        skill_root = Path(__file__).resolve().parent.parent.parent
        project_root = Path(tempfile.mkdtemp())
        try:
            # 只创建 CLAUDE.md(主 host 文件)· 不创建 AGENTS / GEMINI
            (project_root / "CLAUDE.md").write_text("# project\n")
            result = maintain_host_injection(
                skill_root, project_root, "claude-code", "v8.x",
            )
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["primary_file"], "CLAUDE.md")
            # CLAUDE.md 应同步成功
            self.assertEqual(result["results"]["CLAUDE.md"]["status"], "synced")
            # AGENTS.md / GEMINI.md 不存在 · 应 skipped_not_present
            self.assertEqual(result["results"]["AGENTS.md"]["status"], "skipped_not_present")
            self.assertEqual(result["results"]["GEMINI.md"]["status"], "skipped_not_present")
        finally:
            shutil.rmtree(project_root, ignore_errors=True)


# ─── maintain_chmod_tools / maintain_gitignore_worktree ─────────


class TestMaintainChmodTools(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "tools").mkdir()
        (self.tmp / "templates").mkdir()
        (self.tmp / "tools" / "x.py").write_text("#!/usr/bin/env python3\n")
        (self.tmp / "templates" / "y.py").write_text("#!/usr/bin/env python3\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_chmod(self):
        from bootstrap import maintain_chmod_tools
        result = maintain_chmod_tools(self.tmp)
        self.assertEqual(result["tools_py"], 1)
        self.assertEqual(result["templates_py"], 1)
        self.assertEqual(result["failed"], [])
        # 验证可执行位
        import os, stat
        self.assertTrue(os.stat(self.tmp / "tools" / "x.py").st_mode & stat.S_IXUSR)


class TestMaintainGitignoreWorktree(unittest.TestCase):
    def setUp(self):
        import subprocess
        self.tmp = Path(tempfile.mkdtemp())
        # 初始化 git repo(否则 maintain_gitignore_worktree 会 skip)
        subprocess.run(["git", "init", "-q"], cwd=str(self.tmp), check=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_gitignore_created_when_absent(self):
        from bootstrap import maintain_gitignore_worktree
        result = maintain_gitignore_worktree(self.tmp)
        self.assertEqual(result["status"], "appended")
        text = (self.tmp / ".gitignore").read_text()
        self.assertIn(".worktree/", text)
        self.assertIn(".teamwork_localconfig.json", text)

    def test_gitignore_appended_when_present(self):
        from bootstrap import maintain_gitignore_worktree
        (self.tmp / ".gitignore").write_text("node_modules/\n")
        result = maintain_gitignore_worktree(self.tmp)
        self.assertEqual(result["status"], "appended")
        text = (self.tmp / ".gitignore").read_text()
        self.assertIn("node_modules/", text)
        self.assertIn(".worktree/", text)
        self.assertIn(".teamwork_localconfig.json", text)

    def test_gitignore_already_present(self):
        from bootstrap import maintain_gitignore_worktree
        (self.tmp / ".gitignore").write_text(
            "node_modules/\n.worktree/\n.teamwork_localconfig.json\n"
        )
        result = maintain_gitignore_worktree(self.tmp)
        self.assertEqual(result["status"], "already_present")


# ─── bootstrap marker(版本门禁) ──────────────────────────


class TestBootstrapMarker(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_read_returns_empty_when_missing(self):
        from bootstrap import read_bootstrap_marker
        self.assertEqual(read_bootstrap_marker(self.tmp), {})

    def test_read_returns_empty_when_corrupt(self):
        from bootstrap import read_bootstrap_marker, LOCALCONFIG_FILE
        (self.tmp / LOCALCONFIG_FILE).write_text("not json{{{")
        self.assertEqual(read_bootstrap_marker(self.tmp), {})

    def test_write_then_read_roundtrip(self):
        from bootstrap import read_bootstrap_marker, write_bootstrap_marker
        ok = write_bootstrap_marker(
            self.tmp, "v8.6", "claude-code",
            {"chmod": "ok", "hooks": "deployed"},
        )
        self.assertTrue(ok)
        marker = read_bootstrap_marker(self.tmp)
        self.assertEqual(marker["skill_version"], "v8.6")
        self.assertEqual(marker["host"], "claude-code")
        self.assertEqual(marker["last_maintain_results"]["chmod"], "ok")
        self.assertIn("last_maintain_at", marker)

    def test_write_preserves_user_config_segment(self):
        """write _bootstrap 段时 · 不能丢用户的 config 字段。"""
        import json as _json
        from bootstrap import (
            read_localconfig, write_bootstrap_marker, LOCALCONFIG_FILE,
        )
        # 用户先编辑 config
        (self.tmp / LOCALCONFIG_FILE).write_text(_json.dumps({
            "worktree": "auto",
            "worktree_root_path": ".worktree",
            "scope": "all",
            "merge_target": "staging",
        }, indent=2))
        # bootstrap 写 _bootstrap
        write_bootstrap_marker(self.tmp, "v8.6", "claude-code", {"chmod": "ok"})
        # config 字段保留 + _bootstrap 加入
        cfg = read_localconfig(self.tmp)
        self.assertEqual(cfg["worktree"], "auto")
        self.assertEqual(cfg["worktree_root_path"], ".worktree")
        self.assertEqual(cfg["scope"], "all")
        self.assertEqual(cfg["merge_target"], "staging")
        self.assertEqual(cfg["_bootstrap"]["skill_version"], "v8.6")


# ─── scan_v7_state_json ──────────────────────────────────


class TestScanV7StateJson(unittest.TestCase):
    """扫 docs/features/*/state.json 找需 migrate 的。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.features = self.tmp / "docs" / "features"
        self.features.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_no_features_dir_returns_empty(self):
        from bootstrap import scan_v7_state_json
        empty = Path(tempfile.mkdtemp())
        try:
            result = scan_v7_state_json(empty)
            self.assertEqual(result, [])
        finally:
            shutil.rmtree(empty, ignore_errors=True)

    def test_v8_features_not_pending(self):
        from bootstrap import scan_v7_state_json
        f = self.features / "F001"
        f.mkdir()
        (f / "state.json").write_text(
            json.dumps({"schema_version": "v8.0", "feature_id": "F001"}),
            encoding="utf-8",
        )
        result = scan_v7_state_json(self.tmp)
        self.assertEqual(result, [])

    def test_v7_features_pending(self):
        from bootstrap import scan_v7_state_json
        f = self.features / "F001"
        f.mkdir()
        # v7 没 schema_version 字段
        (f / "state.json").write_text(
            json.dumps({"feature_id": "F001", "current_stage": "dev"}),
            encoding="utf-8",
        )
        result = scan_v7_state_json(self.tmp)
        self.assertEqual(len(result), 1)
        self.assertIn("F001/state.json", result[0])


# ─── 端到端:cmd_session_bootstrap ──────────────────────


class TestCmdSessionBootstrapE2E(unittest.TestCase):
    """端到端跑 bootstrap.py · 验证 silent emit JSON 含 4 项检查。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.project = self.tmp / "project"
        self.project.mkdir()
        make_git_repo(self.project)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_end_to_end_silent_emit(self):
        result = subprocess.run(
            [
                "python3", str(BOOTSTRAP_PY),
                "--host", "claude-code",
                "--skill-root", str(SKILL),
                "--skill-version", "v8.0.0",
            ],
            cwd=str(self.project),
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["verdict"], "PASS")
        self.assertIn("checks", data)
        self.assertIn("skill_version", data["checks"])
        self.assertIn("skeletons", data["checks"])
        self.assertIn("host_injection", data["checks"])
        self.assertIn("v7_features_pending_migrate", data["checks"])

    def test_idempotent_second_run_no_skeleton_created(self):
        """第二次跑 · 骨架文档已 existed · 不重创建。"""
        # 第一次
        subprocess.run(
            ["python3", str(BOOTSTRAP_PY),
             "--host", "claude-code",
             "--skill-root", str(SKILL),
             "--skill-version", "v8.0.0"],
            cwd=str(self.project), capture_output=True, text=True, check=True,
        )
        # 第二次
        result = subprocess.run(
            ["python3", str(BOOTSTRAP_PY),
             "--host", "claude-code",
             "--skill-root", str(SKILL),
             "--skill-version", "v8.0.0"],
            cwd=str(self.project), capture_output=True, text=True, check=True,
        )
        data = json.loads(result.stdout)
        self.assertEqual(data["checks"]["skeletons"]["created"], [])
        self.assertEqual(
            sorted(data["checks"]["skeletons"]["existed"]),
            ["GLOSSARY.md", "KNOWLEDGE.md", "TROUBLESHOOTING.md"],
        )

    def test_emits_flow_gates_forewarn(self):
        """v8.14:bootstrap emit 必含 flow_gates · forewarn AI 下游硬墙。

        治本 PTR-F054 prepare 跳过 case:AI 在 bootstrap 输出里就看到
        「init-feature 会校验 prepare-check audit」· 知道跳过会撞墙 · 主动先跑 prepare-check。
        """
        result = subprocess.run(
            ["python3", str(BOOTSTRAP_PY),
             "--host", "claude-code",
             "--skill-root", str(SKILL)],
            cwd=str(self.project), capture_output=True, text=True, check=True,
        )
        data = json.loads(result.stdout)
        self.assertIn("flow_gates", data,
                      "bootstrap 必 emit flow_gates 段(v8.14 forewarn)")
        gates = data["flow_gates"]
        self.assertIsInstance(gates, list)
        self.assertGreaterEqual(len(gates), 1)
        # prepare_check_required_before_init_feature 必须在
        prep_gate = next(
            (g for g in gates
             if g.get("gate") == "prepare_check_required_before_init_feature"),
            None,
        )
        self.assertIsNotNone(prep_gate,
                             "必含 prepare_check_required_before_init_feature 门禁说明")
        # 关键字段完整(机制描述 · 不是宣誓)
        for k in ("trigger", "checks", "action", "skip_consequence", "bypass_env"):
            self.assertIn(k, prep_gate, f"flow_gate 必含 {k} 字段")
        self.assertIn("prepare-check", prep_gate["action"])
        self.assertIn("TEAMWORK_BYPASS_PREPARE_CHECK", prep_gate["bypass_env"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
