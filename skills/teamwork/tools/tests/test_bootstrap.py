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
        for name in ["knowledge.md", "troubleshooting.md", "glossary.md", "dev-rules.md",
                     "architecture-workspace.md"]:
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
            ["ARCHITECTURE.md", "DEV-RULES.md", "GLOSSARY.md", "KNOWLEDGE.md", "TROUBLESHOOTING.md"],
        )
        self.assertEqual(result["existed"], [])
        self.assertEqual(result["migrated"], [])
        self.assertEqual(result["failed"], [])
        # 实际文件创建在 project-specs/ 下 · 不散在仓库根
        specs = self.project_root / "project-specs"
        for name in ["KNOWLEDGE.md", "TROUBLESHOOTING.md", "GLOSSARY.md", "DEV-RULES.md", "ARCHITECTURE.md"]:
            self.assertTrue((specs / name).exists(), f"project-specs/{name} 未创建")
            self.assertFalse((self.project_root / name).exists(), f"{name} 不应散在仓库根")

    def test_dev_rules_present_not_modified(self):
        """v8.96:DEV-RULES.md 人维护 —— 已存在则 existed(不 created · 内容**绝不改**)。"""
        from bootstrap import maintain_project_skeletons
        specs = self.project_root / "project-specs"
        specs.mkdir(parents=True, exist_ok=True)
        original = "# 人手写的开发规范\n禁止直接拼 SQL\n"
        (specs / "DEV-RULES.md").write_text(original, encoding="utf-8")
        result = maintain_project_skeletons(self.skill_root, self.project_root)
        self.assertIn("DEV-RULES.md", result["existed"])
        self.assertNotIn("DEV-RULES.md", result["created"])
        self.assertEqual((specs / "DEV-RULES.md").read_text(encoding="utf-8"), original,
                         "已存在的 DEV-RULES.md 不可被 bootstrap 改动(人维护)")

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
        # teamwork 维护 entries 全预填 → already_present(v8.85 review_start.log · v8.89 local_env)
        (self.tmp / ".gitignore").write_text(
            "node_modules/\n.worktree/\n.teamwork_localconfig.json\n"
            ".claude/scheduled_tasks.lock\n.claude/agents.lock\n"
            "review_start.log\n.teamwork-local-env/\n"
        )
        result = maintain_gitignore_worktree(self.tmp)
        self.assertEqual(result["status"], "already_present")

    # ── v8.89:本地敏感配置目录 .teamwork-local-env/ ──
    def test_local_env_created_with_double_gitignore(self):
        from bootstrap import maintain_local_env
        skill = Path(__file__).resolve().parents[1]  # skills/teamwork
        r = maintain_local_env(skill, self.tmp)
        self.assertEqual(r["status"], "created")
        env = self.tmp / ".teamwork-local-env"
        self.assertTrue((env / "config.properties").exists())
        # 目录内 .gitignore = 防御纵深(忽略全部内容)
        self.assertEqual((env / ".gitignore").read_text().strip().splitlines()[-1], "*")

    def test_local_env_existing_not_overwritten(self):
        """已存在 secret → skip 不覆盖(只补缺失 .gitignore)。"""
        from bootstrap import maintain_local_env
        skill = Path(__file__).resolve().parents[1]
        env = self.tmp / ".teamwork-local-env"; env.mkdir()
        (env / "config.properties").write_text("DB_PASSWORD=keepme\n", encoding="utf-8")
        r = maintain_local_env(skill, self.tmp)
        self.assertEqual(r["status"], "existed")
        self.assertIn("keepme", (env / "config.properties").read_text())

    def test_local_env_opt_out_disabled(self):
        from bootstrap import maintain_local_env
        skill = Path(__file__).resolve().parents[1]
        (self.tmp / ".teamwork_localconfig.json").write_text(
            json.dumps({"local_env_auto_create": False}), encoding="utf-8")
        r = maintain_local_env(skill, self.tmp)
        self.assertEqual(r["status"], "disabled")
        self.assertFalse((self.tmp / ".teamwork-local-env").exists())

    def test_v831_harness_locks_appended(self):
        """v8.31 治本 INFRA-F025 G2:harness 锁文件自动 ignore。"""
        from bootstrap import maintain_gitignore_worktree
        result = maintain_gitignore_worktree(self.tmp)
        self.assertEqual(result["status"], "appended")
        text = (self.tmp / ".gitignore").read_text()
        self.assertIn(".claude/scheduled_tasks.lock", text)
        self.assertIn(".claude/agents.lock", text)

    def test_v835_skip_when_project_root_eq_skill_root(self):
        """v8.35 Bug B(命中 a):project_root == skill_root → skip。"""
        from bootstrap import maintain_gitignore_worktree
        result = maintain_gitignore_worktree(self.tmp, skill_root=self.tmp)
        self.assertEqual(result["status"], "skipped_skill_root_self")
        self.assertIn("project_root == skill_root", result["reason"])
        # 验证 .gitignore 真没被创建
        self.assertFalse((self.tmp / ".gitignore").exists())

    def test_v835_skip_when_skill_root_nested_in_same_git_repo(self):
        """v8.35 Bug B(命中 b):skill_root 是 project_root 子目录 + 同 git 仓 → skip。

        case 用户问"自动升级是否符合预期" 2026-05-27:
        teamwork repo 把 skills/teamwork/ 作为 skill 仓嵌在子目录 · 开发场景下:
        project_root=/teamwork · skill_root=/teamwork/skills/teamwork · 二者同一 git 仓 ·
        bootstrap 改 /teamwork/.gitignore 后 state.py update-skill 立即 BLOCK。
        """
        from bootstrap import maintain_gitignore_worktree
        # 在 tmp(git repo)下面造一个 skills/teamwork 子目录模拟 skill_root
        nested = self.tmp / "skills" / "teamwork"
        nested.mkdir(parents=True)
        result = maintain_gitignore_worktree(self.tmp, skill_root=nested)
        self.assertEqual(result["status"], "skipped_skill_root_self")
        self.assertIn("同一个 git 仓", result["reason"])
        # 验证 .gitignore 真没被创建
        self.assertFalse((self.tmp / ".gitignore").exists())

    def test_v835_skill_root_none_still_works(self):
        """v8.35:skill_root 参数 optional · 不传仍按 v8.31 行为(向后兼容)。"""
        from bootstrap import maintain_gitignore_worktree
        result = maintain_gitignore_worktree(self.tmp)  # 不传 skill_root
        self.assertEqual(result["status"], "appended")
        self.assertIn(".worktree/", (self.tmp / ".gitignore").read_text())

    def test_v835_skill_root_diff_from_project_root_proceeds(self):
        """v8.35:skill_root != project_root + 不同 git 仓 → 正常 maintain(用户项目场景)。"""
        import subprocess
        from bootstrap import maintain_gitignore_worktree
        # fake_skill 必须是独立 git 仓 · 否则 git rev-parse --show-toplevel 可能命中外层仓
        fake_skill = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=str(fake_skill), check=True)
        try:
            result = maintain_gitignore_worktree(self.tmp, skill_root=fake_skill)
            self.assertEqual(result["status"], "appended")
        finally:
            shutil.rmtree(fake_skill, ignore_errors=True)

    def test_v835_consecutive_same_header_deduped(self):
        """v8.35 Bug C:连续同 header 的 entries 共用一个 header(不重复)。

        v8.31 加 .claude/scheduled_tasks.lock + .claude/agents.lock 用了相同 header ·
        但 v8.31 实现每个 entry 都重写 header · 导致 .gitignore 里同句出现 2 次 · 难看。
        v8.35 修:连续同 header 只写第一次。
        """
        from bootstrap import maintain_gitignore_worktree
        result = maintain_gitignore_worktree(self.tmp)
        self.assertEqual(result["status"], "appended")
        text = (self.tmp / ".gitignore").read_text()
        harness_header = "# Teamwork harness locks (session pid · 不该 commit · v8.31)"
        # 连续两个 harness locks entries 应共用一个 header(只出现 1 次)
        self.assertEqual(text.count(harness_header), 1,
                         f"重复 header 应 dedup · 实际出现 {text.count(harness_header)} 次:\n{text}")
        # 两个 pattern 都还在
        self.assertIn(".claude/scheduled_tasks.lock", text)
        self.assertIn(".claude/agents.lock", text)

    def test_v835_different_headers_not_deduped(self):
        """v8.35:不同 header 不 dedup · 各写各的(.worktree/ vs harness locks)。"""
        from bootstrap import maintain_gitignore_worktree
        result = maintain_gitignore_worktree(self.tmp)
        self.assertEqual(result["status"], "appended")
        text = (self.tmp / ".gitignore").read_text()
        # 不同的 4 个 header 都应存在
        self.assertIn("# Teamwork worktree root (default)", text)
        self.assertIn("# Teamwork local config + bootstrap state", text)
        self.assertIn("# Teamwork harness locks", text)


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


class TestEnsureLocalconfigComplete(unittest.TestCase):
    """v8.91:bootstrap 启动自愈 localconfig —— 缺字段(_bootstrap 段 + 新增开关)补默认值。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.skill_root = Path(tempfile.mkdtemp())  # 不等于 project_root

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        shutil.rmtree(self.skill_root, ignore_errors=True)

    def _read(self):
        import json as _json
        from bootstrap import LOCALCONFIG_FILE
        return _json.loads((self.tmp / LOCALCONFIG_FILE).read_text(encoding="utf-8"))

    def test_backfills_missing_bootstrap_and_toggles_preserving_user_values(self):
        import json as _json
        from bootstrap import ensure_localconfig_complete, LOCALCONFIG_FILE
        # 用户设了 merge_target/worktree · 缺 _bootstrap + 新开关
        (self.tmp / LOCALCONFIG_FILE).write_text(
            _json.dumps({"merge_target": "dev", "worktree": "off"}), encoding="utf-8")
        r = ensure_localconfig_complete(self.tmp, self.skill_root)
        self.assertEqual(r["status"], "backfilled")
        data = self._read()
        # 用户值保留(不覆盖)
        self.assertEqual(data["merge_target"], "dev")
        self.assertEqual(data["worktree"], "off")
        # 新开关补默认
        self.assertEqual(data["archive_on_ship"], True)
        self.assertEqual(data["disable_heterogeneous_review"], False)
        self.assertEqual(data["local_env_auto_create"], True)
        self.assertEqual(data["id_strategy"], "utc-yymmddhhmmss")
        # _bootstrap 段补全 4 子键
        self.assertEqual(sorted(data["_bootstrap"].keys()),
                         ["host", "last_maintain_at", "last_maintain_results", "skill_version"])

    def test_partial_bootstrap_subkeys_backfilled(self):
        """_bootstrap 存在但缺子键 → 只补缺的 · 保留已有(治本 skip_maintain 时缺口)。"""
        import json as _json
        from bootstrap import ensure_localconfig_complete, LOCALCONFIG_FILE
        full = {k: "x" for k in ("worktree", "worktree_root_path", "scope",
                                 "merge_target", "worktree_cleanup", "mr_url_template",
                                 "id_strategy", "archive_on_ship", "local_env_auto_create",
                                 "disable_heterogeneous_review")}
        full["_bootstrap"] = {"skill_version": "v8.90", "host": "codex-cli"}  # 缺 2 子键
        (self.tmp / LOCALCONFIG_FILE).write_text(_json.dumps(full), encoding="utf-8")
        r = ensure_localconfig_complete(self.tmp, self.skill_root)
        self.assertEqual(r["status"], "backfilled")
        self.assertEqual(set(r["added_bootstrap"]), {"last_maintain_at", "last_maintain_results"})
        data = self._read()
        self.assertEqual(data["_bootstrap"]["skill_version"], "v8.90")  # 已有保留
        self.assertEqual(data["_bootstrap"]["host"], "codex-cli")
        self.assertEqual(data["_bootstrap"]["last_maintain_results"], {})

    def test_complete_config_no_rewrite(self):
        import json as _json
        from bootstrap import ensure_localconfig_complete, LOCALCONFIG_FILE
        # 先补全一次
        (self.tmp / LOCALCONFIG_FILE).write_text(_json.dumps({"worktree": "auto"}), encoding="utf-8")
        ensure_localconfig_complete(self.tmp, self.skill_root)
        mtime = (self.tmp / LOCALCONFIG_FILE).stat().st_mtime_ns
        r = ensure_localconfig_complete(self.tmp, self.skill_root)  # 第二次
        self.assertEqual(r["status"], "complete")
        self.assertEqual((self.tmp / LOCALCONFIG_FILE).stat().st_mtime_ns, mtime)  # 未写盘

    def test_absent_not_created(self):
        from bootstrap import ensure_localconfig_complete, LOCALCONFIG_FILE
        r = ensure_localconfig_complete(self.tmp, self.skill_root)
        self.assertEqual(r["status"], "skipped_absent")
        self.assertFalse((self.tmp / LOCALCONFIG_FILE).exists())

    def test_skill_root_skipped(self):
        from bootstrap import ensure_localconfig_complete
        r = ensure_localconfig_complete(self.skill_root, self.skill_root)
        self.assertEqual(r["status"], "skipped_skill_root")


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
            ["ARCHITECTURE.md", "DEV-RULES.md", "GLOSSARY.md", "KNOWLEDGE.md", "TROUBLESHOOTING.md"],
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

    def _run_and_get_gates(self):
        result = subprocess.run(
            ["python3", str(BOOTSTRAP_PY),
             "--host", "claude-code",
             "--skill-root", str(SKILL)],
            cwd=str(self.project), capture_output=True, text=True, check=True,
        )
        return json.loads(result.stdout).get("flow_gates", [])

    def test_cold_start_gate_present_when_no_product_overview(self):
        """v8.116:无 product-overview/ → emit cold_start_product_planning_recommended gate。

        teamwork-space.md(地图)由 bootstrap 自动建 → gate 不再 fire 于无 teamwork-space.md ·
        改 fire 于无 product-overview(产品规划上游)。setUp 裸 git 仓(无 PO)→ gate 在 + 地图自动建。
        """
        gates = self._run_and_get_gates()
        cs = next((g for g in gates
                   if g.get("gate") == "cold_start_product_planning_recommended"), None)
        self.assertIsNotNone(cs, "无 product-overview 时必 emit cold_start_product_planning_recommended")
        for k in ("trigger", "checks", "action", "skip_consequence",
                  "teamwork_space_status", "authoritative_order", "spec"):
            self.assertIn(k, cs, f"gate 必含 {k} 字段")
        self.assertIn("product-overview", cs["action"])
        self.assertIn("产品规划", cs["action"])
        self.assertIn("PRODUCT-OVERVIEW-INTEGRATION", cs["spec"])
        # teamwork-space.md 已自动建(骨架)· N≥1:无 PO 也有地图
        self.assertEqual(cs["teamwork_space_status"], "created")
        self.assertTrue((self.project / "teamwork-space.md").exists(),
                        "无 PO 也必自动建 teamwork-space.md 地图骨架(N≥1)")

    def test_cold_start_gate_absent_when_product_overview_exists(self):
        """v8.116:product-overview/ 存在 → 产品规划上游已有 · 不再 emit cold_start gate
        (改由 product_overview_planning_spec_required 接管)。"""
        (self.project / "product-overview").mkdir()
        gates = self._run_and_get_gates()
        cs = next((g for g in gates
                   if g.get("gate") == "cold_start_product_planning_recommended"), None)
        self.assertIsNone(cs, "product-overview 存在时不应 emit cold_start gate")
        self.assertTrue(any(g.get("gate") == "product_overview_planning_spec_required"
                            for g in gates), "PO 存在 → planning_spec_required 接管")

    def test_teamwork_space_auto_created_with_knowledge_entries(self):
        """v8.116:teamwork-space.md 缺失 → bootstrap 自动建骨架(知识入口探测 + 子项目清单空表)· 幂等。"""
        (self.project / "project-specs").mkdir(exist_ok=True)
        (self.project / "external").mkdir(exist_ok=True)

        def _run():
            r = subprocess.run(
                ["python3", str(BOOTSTRAP_PY), "--host", "claude-code", "--skill-root", str(SKILL)],
                cwd=str(self.project), capture_output=True, text=True, check=True)
            return json.loads(r.stdout)

        data = _run()
        self.assertEqual(data["checks"]["teamwork_space"]["status"], "created")
        space = (self.project / "teamwork-space.md").read_text(encoding="utf-8")
        self.assertIn("知识入口", space)
        self.assertIn("project-specs", space)      # 探测到的节点
        self.assertIn("external", space)
        self.assertIn("代码", space)                # 末行 代码=唯一真相
        # v8.117:project-specs/ARCHITECTURE.md(skeletons 自动建)→ 知识入口探测到 系统架构 行
        self.assertIn("系统架构", space)
        self.assertIn("ARCHITECTURE.md", space)
        self.assertIn("待规划填充", space)           # 子项目清单空表占位 · 无示例数据行
        # 幂等:二次跑 → existed(不覆盖用户/规划已填内容)
        self.assertEqual(_run()["checks"]["teamwork_space"]["status"], "existed")

    def test_session_entry_priority_when_cold_start(self):
        """v8.51:cold_start(无 teamwork-space)→ emit session_entry_priority(② 补规划 + ③ 任务)。

        治本 gcpdev case 2026-05-29:PMO 把升级/补规划降脚注、优先级倒置 → 物化优先级到 bootstrap 输出。
        (① 升级 取决于网络/版本比较 · 不在此断言;② 补规划 由 cold_start 确定性触发)
        """
        result = subprocess.run(
            ["python3", str(BOOTSTRAP_PY),
             "--host", "claude-code", "--skill-root", str(SKILL)],
            cwd=str(self.project), capture_output=True, text=True, check=True,
        )
        data = json.loads(result.stdout)
        self.assertIn("session_entry_priority", data,
                      "cold_start 时必 emit session_entry_priority(物化入口优先级)")
        sp = data["session_entry_priority"]
        order_text = " ".join(sp["order"])
        self.assertIn("补规划", order_text, "② 补规划 必在(cold_start 触发)")
        self.assertIn("任务", order_text, "③ 任务 必在(且应排在补规划之后)")
        self.assertLess(order_text.index("补规划"), order_text.index("任务"),
                        "补规划 必排在 任务 之前(优先级序)")
        self.assertIn("脚注", sp["rule"], "rule 必强调不可降脚注(治本优先级倒置)")

    def test_pmo_must_read_digest_at_top_survives_truncation(self):
        """v8.60:pmo_must_read digest 在输出顶部(survive head -5)· 治本 case
        `bootstrap.py | head -50` 切掉 skill_update_check(JSON 后位)→ PMO 漏升级提示 +
        误判"bootstrap 没检查升级"。"""
        result = subprocess.run(
            ["python3", str(BOOTSTRAP_PY),
             "--host", "claude-code", "--skill-root", str(SKILL)],
            cwd=str(self.project), capture_output=True, text=True, check=True,
        )
        data = json.loads(result.stdout)
        # 字段存在 + 在头部(verdict/command 之后 · 位置 ≤ 2 · 截断也能见)
        self.assertIn("pmo_must_read", data)
        self.assertLessEqual(list(data.keys()).index("pmo_must_read"), 2,
                             "pmo_must_read 必在头部(survive 截断)")
        mr = data["pmo_must_read"]
        # 含禁截断警告
        self.assertIn("禁", mr)
        self.assertIn("head", mr)
        # cold_start(setUp 裸 git 仓无 teamwork-space)触发 → digest 必提 flow_gates
        self.assertIn("flow_gates", mr)
        # 🔴 截断鲁棒性实测:head -5 仍见 pmo_must_read(直接复现 bug 场景)
        head5 = "\n".join(result.stdout.splitlines()[:5])
        self.assertIn("pmo_must_read", head5,
                      "head -5 必见 pmo_must_read(治本 head -50 吞 forewarn)")


class TestWriteHostAudit(unittest.TestCase):
    """v8.21:bootstrap.write_host_audit 写 ~/.teamwork/host_audit.json。

    治本 PMO 心智 · external-review 等下游命令自动读 · 不再要 PMO 传 --host。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="host-audit-"))
        self.audit_path = self.tmp / "host_audit.json"
        self._prev = os.environ.get("TEAMWORK_HOST_AUDIT_PATH")
        os.environ["TEAMWORK_HOST_AUDIT_PATH"] = str(self.audit_path)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self._prev is None:
            os.environ.pop("TEAMWORK_HOST_AUDIT_PATH", None)
        else:
            os.environ["TEAMWORK_HOST_AUDIT_PATH"] = self._prev

    def test_write_host_audit_creates_file(self):
        sys.path.insert(0, str(TOOLS))
        import bootstrap  # type: ignore
        ok = bootstrap.write_host_audit("claude-code")
        self.assertTrue(ok)
        self.assertTrue(self.audit_path.exists())
        data = json.loads(self.audit_path.read_text(encoding="utf-8"))
        self.assertEqual(data["host"], "claude-code")
        self.assertIn("timestamp", data)

    def test_write_host_audit_overwrites_existing(self):
        sys.path.insert(0, str(TOOLS))
        import bootstrap  # type: ignore
        bootstrap.write_host_audit("claude-code")
        bootstrap.write_host_audit("codex-cli")
        data = json.loads(self.audit_path.read_text(encoding="utf-8"))
        self.assertEqual(data["host"], "codex-cli")  # 后者覆盖 · 保留最新

    def test_write_host_audit_creates_parent_dir(self):
        """audit_path 父目录不存在 → 自动 mkdir -p。"""
        deep_path = self.tmp / "deep" / "nested" / "host_audit.json"
        os.environ["TEAMWORK_HOST_AUDIT_PATH"] = str(deep_path)
        sys.path.insert(0, str(TOOLS))
        import bootstrap  # type: ignore
        ok = bootstrap.write_host_audit("gemini-cli")
        self.assertTrue(ok)
        self.assertTrue(deep_path.exists())

    def test_host_audit_path_helper_respects_env_override(self):
        sys.path.insert(0, str(TOOLS))
        import bootstrap  # type: ignore
        p = bootstrap._host_audit_path()
        self.assertEqual(p, self.audit_path)  # env 覆盖生效


class TestCheckSkillUpdate(unittest.TestCase):
    """v8.24:bootstrap.check_skill_update · GitHub raw 探测线上版本 + R5 1/2 prompt。

    用 file:// URL 模拟 GitHub raw response · 避免依赖外网。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="skill-update-"))
        self.fake_skill_md = self.tmp / "SKILL.md"
        self._prev = os.environ.get("TEAMWORK_SKILL_UPDATE_URL")
        os.environ["TEAMWORK_SKILL_UPDATE_URL"] = f"file://{self.fake_skill_md}"
        sys.path.insert(0, str(TOOLS))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self._prev is None:
            os.environ.pop("TEAMWORK_SKILL_UPDATE_URL", None)
        else:
            os.environ["TEAMWORK_SKILL_UPDATE_URL"] = self._prev

    def _write_fake_remote(self, version: str):
        self.fake_skill_md.write_text(
            f"---\nname: teamwork\nversion: {version}\n---\nbody\n",
            encoding="utf-8")

    # ── 版本比较 ──
    def test_up_to_date(self):
        import bootstrap  # type: ignore
        self._write_fake_remote("v8.23")
        d = bootstrap.check_skill_update("v8.23")
        self.assertEqual(d["status"], "up_to_date")
        self.assertEqual(d["latest_version"], "v8.23")

    def test_outdated_emits_r5_prompt(self):
        """治本 case 核心:落后 → emit R5 1/2 选项。"""
        import bootstrap  # type: ignore
        self._write_fake_remote("v8.23")
        d = bootstrap.check_skill_update("v8.21")
        self.assertEqual(d["status"], "outdated")
        self.assertEqual(d["latest_version"], "v8.23")
        self.assertIn("upgrade_prompt", d)
        # R5 1/2 prompt 关键内容
        prompt = d["upgrade_prompt"]
        self.assertIn("v8.21", prompt)
        self.assertIn("v8.23", prompt)
        self.assertIn("1.", prompt)  # 选项 1
        self.assertIn("2.", prompt)  # 选项 2
        self.assertIn("升级", prompt)
        self.assertIn("跳过", prompt)
        # v8.42:update 命令改 python3 SKILL_ROOT/tools/update.py(独立脚本)
        self.assertIn("tools/update.py", prompt)
        # 不应再含 state.py update-skill 字面(已抽离)
        self.assertNotIn("state.py update-skill", prompt)

    def test_local_newer_than_remote_still_up_to_date(self):
        """本地 > 线上(测试场景 / 用户改了本地)→ up_to_date(不 emit downgrade prompt)。"""
        import bootstrap  # type: ignore
        self._write_fake_remote("v8.20")
        d = bootstrap.check_skill_update("v8.23")
        self.assertEqual(d["status"], "up_to_date")

    # ── 版本 tuple 比较(防 v8.10 vs v8.9 字符串比较 bug)──
    def test_version_tuple_compares_numerically(self):
        """v8.10 > v8.9 · 不是 v8.10 < v8.9(ascii 比较)。"""
        import bootstrap  # type: ignore
        self._write_fake_remote("v8.10")
        d = bootstrap.check_skill_update("v8.9")
        self.assertEqual(d["status"], "outdated")  # 8.10 真的 > 8.9
        d2 = bootstrap.check_skill_update("v8.10")
        self.assertEqual(d2["status"], "up_to_date")

    # ── parse failure ──
    def test_parse_failed_when_no_version_in_remote(self):
        import bootstrap  # type: ignore
        self.fake_skill_md.write_text("no version here", encoding="utf-8")
        d = bootstrap.check_skill_update("v8.21")
        self.assertEqual(d["status"], "parse_failed")

    # ── network failure ──
    def test_network_failure_silent_skip(self):
        """URL 不存在 → network_failed · 不抛异常 · bootstrap 不阻塞。"""
        import bootstrap  # type: ignore
        os.environ["TEAMWORK_SKILL_UPDATE_URL"] = "file:///tmp/nonexistent-xyz.md"
        d = bootstrap.check_skill_update("v8.21")
        self.assertEqual(d["status"], "network_failed")
        self.assertIn("reason", d)

    # ── helper 单元 ──
    def test_parse_skill_version_extracts_frontmatter(self):
        import bootstrap  # type: ignore
        self.assertEqual(
            bootstrap._parse_skill_version("---\nname: x\nversion: v8.99\n---\n"),
            "v8.99",
        )
        self.assertIsNone(
            bootstrap._parse_skill_version("no version"),
        )

    def test_version_tuple_parse(self):
        import bootstrap  # type: ignore
        self.assertEqual(bootstrap._version_tuple("v8.23"), (8, 23, 0))
        self.assertEqual(bootstrap._version_tuple("v8.10"), (8, 10, 0))
        self.assertEqual(bootstrap._version_tuple("v8.0.5"), (8, 0, 5))
        self.assertEqual(bootstrap._version_tuple("garbage"), (0, 0, 0))

    # ── v8.39:channel 支持(用户拍板 · 默认 main · dev 用于尝鲜)──

    def test_v839_default_channel_is_main(self):
        """v8.39:check_skill_update 不传 channel · emit channel=main(向后兼容)。"""
        import bootstrap  # type: ignore
        self._write_fake_remote("v8.39")
        d = bootstrap.check_skill_update("v8.39")
        self.assertEqual(d["channel"], "main")

    def test_v839_explicit_dev_channel(self):
        """v8.39:check_skill_update 传 channel=dev · emit channel=dev。"""
        import bootstrap  # type: ignore
        self._write_fake_remote("v8.40")
        d = bootstrap.check_skill_update("v8.39", channel="dev")
        self.assertEqual(d["channel"], "dev")
        self.assertEqual(d["status"], "outdated")
        # 尝鲜 channel 在 prompt 必加 ⚠️ 提示
        self.assertIn("dev", d["upgrade_prompt"])
        self.assertIn("尝鲜", d["upgrade_prompt"])
        # update 命令必带 --channel dev(v8.42 update.py 命令格式)
        self.assertIn("--channel dev", d["upgrade_prompt"])
        self.assertIn("tools/update.py", d["upgrade_prompt"])

    def test_v839_main_channel_prompt_no_warning(self):
        """v8.39:main channel 是默认 · prompt 不加尝鲜警告。"""
        import bootstrap  # type: ignore
        self._write_fake_remote("v8.40")
        d = bootstrap.check_skill_update("v8.39", channel="main")
        self.assertEqual(d["status"], "outdated")
        # main 不显示 --channel 参数(简洁默认)
        self.assertNotIn("--channel", d["upgrade_prompt"])
        self.assertNotIn("尝鲜", d["upgrade_prompt"])

    def test_v839_read_update_channel_default_main(self):
        """v8.39:_read_update_channel · 无 config 文件 → main。"""
        import bootstrap  # type: ignore
        # 新空目录 · 无 .teamwork_localconfig.json
        self.assertEqual(bootstrap._read_update_channel(self.tmp), "main")

    def test_v839_read_update_channel_from_localconfig(self):
        """v8.39:_read_update_channel · config 有 update_channel=dev → dev。"""
        import bootstrap  # type: ignore
        (self.tmp / ".teamwork_localconfig.json").write_text(
            json.dumps({"update_channel": "dev"}), encoding="utf-8")
        self.assertEqual(bootstrap._read_update_channel(self.tmp), "dev")

    def test_v839_read_update_channel_corrupt_config_falls_back_main(self):
        """v8.39:_read_update_channel · config 损坏 → main(silent · 不阻塞)。"""
        import bootstrap  # type: ignore
        (self.tmp / ".teamwork_localconfig.json").write_text(
            "not json {{{", encoding="utf-8")
        self.assertEqual(bootstrap._read_update_channel(self.tmp), "main")

    def test_v839_read_update_channel_non_string_falls_back_main(self):
        """v8.39:_read_update_channel · update_channel 非 string → main。"""
        import bootstrap  # type: ignore
        (self.tmp / ".teamwork_localconfig.json").write_text(
            json.dumps({"update_channel": 123}), encoding="utf-8")
        self.assertEqual(bootstrap._read_update_channel(self.tmp), "main")

    def test_v839_read_update_channel_empty_string_falls_back_main(self):
        """v8.39:_read_update_channel · update_channel='' → main(空串视作未设)。"""
        import bootstrap  # type: ignore
        (self.tmp / ".teamwork_localconfig.json").write_text(
            json.dumps({"update_channel": "  "}), encoding="utf-8")
        self.assertEqual(bootstrap._read_update_channel(self.tmp), "main")


class TestKnowledgeGraphIntegrity(unittest.TestCase):
    """v8.115:知识图谱**结构可达性**校验(归档 INDEX↔zip 对账 + 节点登记 · WARN-only)。
    🔴 只查可达性 · 不查内容新鲜度(内容=代码唯一真相)。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-kg-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _space(self, text="# Teamwork Space\n"):
        (self.tmp / "teamwork-space.md").write_text(text, encoding="utf-8")

    def _archive(self, rows=(), zips=()):
        adir = self.tmp / "docs" / "features" / "_archive"
        adir.mkdir(parents=True, exist_ok=True)
        lines = ["| Feature | 描述 | 交付归档时间 | 归档物 |", "| --- | --- | --- | --- |"]
        for fid in rows:
            lines.append(f"| {fid} | x | t | `{fid}.zip` |")
        (adir / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        for fid in zips:
            (adir / f"{fid}.zip").write_bytes(b"PK\x03\x04")
        return adir

    def test_no_space_skipped(self):
        from bootstrap import check_knowledge_graph_integrity
        self.assertEqual(check_knowledge_graph_integrity(self.tmp)["status"], "skipped")

    def test_clean_ok(self):
        from bootstrap import check_knowledge_graph_integrity
        (self.tmp / "external").mkdir()
        (self.tmp / "project-specs").mkdir()
        self._space("# TS\n知识入口:external/ · project-specs/\n")
        self._archive(rows=["F-001"], zips=["F-001"])
        r = check_knowledge_graph_integrity(self.tmp)
        self.assertEqual(r["status"], "ok", r)

    def test_orphan_zip_leaks(self):
        """zip 无 INDEX 行 = 已交付但翻不到(孤儿)。"""
        from bootstrap import check_knowledge_graph_integrity
        self._space()
        self._archive(rows=[], zips=["F-ORPHAN"])
        r = check_knowledge_graph_integrity(self.tmp)
        self.assertEqual(r["status"], "leaks_found")
        self.assertTrue(any("F-ORPHAN" in x and "孤儿" in x for x in r["leaks"]), r)

    def test_dangling_row_leaks(self):
        """INDEX 行无 zip = 断指针(悬空)。"""
        from bootstrap import check_knowledge_graph_integrity
        self._space()
        self._archive(rows=["F-GONE"], zips=[])
        r = check_knowledge_graph_integrity(self.tmp)
        self.assertEqual(r["status"], "leaks_found")
        self.assertTrue(any("F-GONE" in x and "悬空" in x for x in r["leaks"]), r)

    def test_matched_archive_no_leak(self):
        """INDEX 行 + 匹配 zip → 无归档死角。"""
        from bootstrap import check_knowledge_graph_integrity
        self._space()
        self._archive(rows=["F-1", "F-2"], zips=["F-1", "F-2"])
        self.assertEqual(check_knowledge_graph_integrity(self.tmp)["status"], "ok")

    def test_unregistered_node_leaks(self):
        """external/ 存在但 teamwork-space.md 未提及 = 知识入口死角。"""
        from bootstrap import check_knowledge_graph_integrity
        self._space("# TS · 没列任何节点\n")
        (self.tmp / "external").mkdir()
        r = check_knowledge_graph_integrity(self.tmp)
        self.assertEqual(r["status"], "leaks_found")
        self.assertTrue(any("external" in x and "未登记" in x for x in r["leaks"]), r)

    def test_registered_node_no_leak(self):
        """external/ 存在且地图提及 → 不报。"""
        from bootstrap import check_knowledge_graph_integrity
        self._space("# TS\n知识入口 · external/ 在此\n")
        (self.tmp / "external").mkdir()
        self.assertEqual(check_knowledge_graph_integrity(self.tmp)["status"], "ok")

    def test_scope_note_present_on_leaks(self):
        """leaks 必带 scope_note(结构可达 ≠ 内容最新 · 防 checker 自身成误导信号 · v8.105 教训)。"""
        from bootstrap import check_knowledge_graph_integrity
        self._space()
        self._archive(rows=[], zips=["F-X"])
        r = check_knowledge_graph_integrity(self.tmp)
        self.assertIn("不代表内容最新", r.get("scope_note", ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
