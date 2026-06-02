# Changelog

> 📦 v8.83 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**只留最近 1 版**(每次发布把上一版迁入归档)。

## v8.84 · 外部评审 claude 不再指定模型 · 用 CLI 默认值(dev-only)

> 用户拍板:外部评审调 claude 时**不要 `--model` 指定模型 · 用默认值**。承接 v8.30「工具不假设模型名」原则(当时只治了 codex 的虚构 `gpt-5-codex` · claude 路径仍硬编码 `claude-sonnet-4-6`)。

### 变更
- `_run_claude_review`:去掉 `--model claude-sonnet-4-6` · cmd = `claude -p <prompt> --output-format text`(模型随用户 claude CLI 默认配置 · 不再硬编码可能过时/虚构的模型名)。删掉无用的 `model_name` 形参。
- dry-run `preview_command` 同步去 `--model`。
- 落产物 frontmatter 的 `review_model` 仍记 `_detect_cli_version`(实际 CLI 版本)· 真实可审计。

### 背景(本版前的排查)
- 实测 claude 外审命令**本身正常**:state.py 同款调用单跑 ~14s 返回合法 YAML 评审 · CLI 2.1.160 接受该模型名 · 无 tool_use 卡死。先前 case 的「卡死」是**并发限流**下 `claude -p` 静默阻塞 + 调用方提前 kill 并伪造 `tool_error` 越过外审门禁所致 —— 非命令缺陷。去硬编码模型名是顺手的健壮性改进(随用户配置 · 不赌模型名存在)。

### 验证
- pytest:**3 failed / 460 passed**(baseline 3 = scan-spec 既有失败 · 零回归)。`test_v843_run_claude_review_prompt_in_argv_not_stdin` 断言从 `assertIn('--model')` 改 `assertNotIn('--model')` 锚定新行为。
