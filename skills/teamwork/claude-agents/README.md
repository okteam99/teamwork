# Claude Agent 调用规范（v7.3.10+P0-24 新建）

> **定位**：本目录定义"以 Claude CLI 作为外部模型时"的 shell 调用规范。
>
> 与 `codex-agents/` 的差异：
> - `codex-agents/*.toml` 是 **Codex CLI 原生 agent 定义格式**（Codex CLI 主对话用 toml 调起的子 agent）
> - `claude-agents/` 是 **Codex CLI / Gemini CLI 等其他主对话 shell 调用 Claude CLI 子进程的范本** —— Claude Code CLI 不需要 toml，通过命令行参数 + 输入重定向调用
>
> **何时使用**：
> - 主对话宿主 = `codex-cli` 且 `state.external_cross_review.model = claude` 时
> - 主对话宿主 = `gemini-cli` 且 `state.external_cross_review.model = claude` 时（暂未实现）
> - **不**适用于：主对话宿主 = `claude-code`（同源约束，外部模型不能选 claude）
>
> 权威规范见 [standards/external-model.md](../standards/external-model.md)。

---

## 一、前置条件

主对话主机（如 Codex CLI 主对话）shell 调用 `claude` CLI 前必须满足：

| # | 条件 | 检查方式 |
|---|------|---------|
| 1 | `claude` CLI 已安装 | `command -v claude` 或 `which claude` |
| 2 | `claude` CLI 已认证（三种方式之一，见下「认证方式」段）| 运行时调用失败时捕获 stderr 处理 |
| 3 | 主对话有 bash / shell 工具 | Codex CLI 默认支持 |
| 4 | 网络可达 Anthropic API | 运行时调用失败时捕获处理 |

🔴 PMO 调用 `templates/detect-external-model.py` 时只检查 #1（CLI 安装），不查 #2（认证状态）——因 OAuth 状态无法可靠检测，延后到运行时失败处理（见 [standards/external-model.md](../standards/external-model.md) §六 E3）。

### 认证方式（v7.3.10+P0-65 实战补充）

按推荐度排：

| # | 方式 | 适用 | 优点 | 缺点 |
|---|------|------|------|------|
| A | **OAuth 登录**（`claude` 交互 → `/login`）| Claude Code 主对话宿主 / 终端直接调用 | 复用 Claude.ai Pro/Max 订阅 / 不占 API 计费 | macOS Keychain 存 token / **Codex 等沙箱宿主子进程不继承** |
| B | **`CLAUDE_CODE_OAUTH_TOKEN` env var** | **Codex CLI 主对话宿主 / 脚本 / CI 推荐** | 复用 Pro/Max 订阅 / 不占 API 计费 / 跨沙箱稳定 | 需先 `claude setup-token` 生成长期 token |
| C | **`ANTHROPIC_API_KEY` env var** | 团队共享 / 非订阅用户 / Tier 1+ API 计费 | 设置最简 / 跨平台兼容 | 按 token 计费独立于 Claude.ai 订阅 |

🔴 **Codex 沙箱已知限制**（实证 2026-04-30）：Codex CLI 默认沙箱**不继承** macOS Keychain，OAuth 登录态在沙箱外可见、沙箱内 `claude auth status` 报 `Not logged in`。**Codex 主对话宿主下推荐用方式 B（`CLAUDE_CODE_OAUTH_TOKEN`）**。

#### 方式 B 配置步骤（Codex 沙箱推荐）

```bash
# 1. 在沙箱外（普通终端）生成 token
claude setup-token
# → 输出：CLAUDE_CODE_OAUTH_TOKEN=...

# 2. 写入 shell config
echo 'export CLAUDE_CODE_OAUTH_TOKEN=...' >> ~/.zshrc
source ~/.zshrc

# 3. 重启 Codex CLI（让它继承新 env）

# 4. 沙箱内验证
claude -p "say hi"  # 应输出回应
```

🔴 **token 不要进 git**（`.gitignore` 已默认排除 `~/.zshrc` / `.envrc`，但用 `direnv` / `1password` CLI 注入更安全）。

#### 官方文档参考

- [CLI Reference](https://code.claude.com/docs/en/cli-reference)：`claude -p`（非交互调用）/ `claude auth status` / `claude setup-token`
- [IAM 认证文档](https://code.claude.com/docs/en/iam)：macOS Keychain 存储说明 + `CLAUDE_CODE_OAUTH_TOKEN` 适用场景
- [环境变量参考](https://code.claude.com/docs/en/env-vars)：`CLAUDE_CODE_OAUTH_TOKEN` / `ANTHROPIC_API_KEY` 等

---

## 二、文件索引

| 文件 | 用途 |
|------|------|
| `README.md` | 本文件：调用规范总览、前置条件 |
| `reviewer.md` | 外部 review 的 prompt 模板（PRD / Blueprint / 代码三场景共用） |
| `invoke.md` | 主对话 shell 调用 `claude` CLI 的命令范本 + stderr 捕获 + 降级处理 |

---

## 三、调用流程概览

```
PMO（在 Codex CLI 主对话内执行）
  │
  ├── Step 1: 起草 dispatch 文件
  │   dispatch_log/{NNN}-external-claude-review.md
  │
  ├── Step 2: 准备 prompt
  │   读 claude-agents/reviewer.md 模板
  │   注入：被审查产物路径列表 + checklist 类型（PRD / Blueprint / 代码）
  │
  ├── Step 3: shell 调用 claude CLI（详见 invoke.md）
  │   bash 命令模板：
  │     cat <prompt-file> | claude --print --model claude-sonnet-4-6 --output-format text > <output-file>
  │
  ├── Step 4: 捕获 stderr + exit code
  │   exit code != 0 →
  │     - state.concerns 加 WARN（含 stderr 摘要）
  │     - state.external_cross_review.reviewer_dispatches[].status = "failed"
  │     - 降级单视角 review，不阻塞流程
  │   exit code == 0 →
  │     - 解析 output 文件（YAML frontmatter 头部 + body）
  │     - 落盘到 external-cross-review/{stage}-claude.md
  │     - state.external_cross_review.reviewer_dispatches[].status = "completed"
  │
  └── Step 5: PMO 整合（见 templates/external-cross-review.md §五）
      内部 review 对比 / finding 分类 / 合入多视角评审 / 更新 review-log
```

---

## 四、与 codex-agents/ 的对照

| 维度 | `codex-agents/` | `claude-agents/` |
|------|----------------|------------------|
| 文件格式 | `.toml`（Codex CLI 原生 agent 定义） | `.md`（prompt 模板 + shell 范本） |
| 调用方式 | Codex CLI 主对话用 agent name 调起 | 主对话 bash 调用 `claude --print` |
| 适用宿主 | Codex CLI 主对话用 codex-agents/，或其他主对话 shell 调 codex CLI | Codex CLI 主对话 shell 调 Claude CLI |
| 子 agent 可见性 | Codex 子 agent 是独立 fresh session | Claude CLI 单次调用即独立 session |

---

## 五、扩展性

未来若需要 Gemini CLI 作为外部模型，会新建 `gemini-agents/` 目录，规范结构与本目录对称。`templates/detect-external-model.py` 的 `CANDIDATES` 列表加一行 `gemini` 即可。

---

## 六、版本记录

- v7.3.10+P0-24（首次发布）：建立 Claude CLI 作为外部模型的调用规范，配合 standards/external-model.md
