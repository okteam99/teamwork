# Claude CLI Shell 调用范本（v7.3.10+P0-24）

> **用途**：主对话（Codex CLI 等异质宿主）通过 shell 调用 `claude` CLI 子进程做外部 review 时的标准范本。
>
> **前提**：宿主主对话有 bash / shell 工具；用户已在本机装 `claude` CLI 且已认证。
>
> 🔴 **Codex 主对话宿主下的认证特殊处理**（v7.3.10+P0-65 实证）：Codex 沙箱不继承 macOS Keychain → OAuth 登录态在沙箱内不可见。**推荐用 `CLAUDE_CODE_OAUTH_TOKEN` env var**（`claude setup-token` 生成 + 写入 shell config + 重启 Codex CLI），详见 [claude-agents/README.md § 认证方式](./README.md)。

---

## 一、最小调用范本

### 1.1 基础命令

```bash
cat <prompt-file> | claude --print --model claude-sonnet-4-6 --output-format text > <output-file> 2> <stderr-file>
echo $? > <exitcode-file>
```

### 1.2 完整 wrapper 函数（PMO 在主对话内嵌入 bash）

```bash
# 参数：
#   $1: prompt 文件路径（已替换好占位符的 reviewer.md）
#   $2: 输出文件路径（external-cross-review/{stage}-claude.md）
#   $3: dispatch 文件路径（dispatch_log/{NNN}-external-claude-review.md）

invoke_claude_external_review() {
  local prompt_file="$1"
  local output_file="$2"
  local dispatch_file="$3"

  # 准备 stderr / exit code 临时文件
  local stderr_file="${output_file}.stderr"
  local exitcode_file="${output_file}.exitcode"

  # 检查 claude CLI 是否可用
  if ! command -v claude > /dev/null 2>&1; then
    echo "ERROR: claude CLI 未安装" > "$stderr_file"
    echo "127" > "$exitcode_file"
    return 127
  fi

  # 实际调用
  cat "$prompt_file" \
    | claude --print --model claude-sonnet-4-6 --output-format text \
    > "$output_file" 2> "$stderr_file"
  local rc=$?
  echo "$rc" > "$exitcode_file"

  return $rc
}
```

---

## 二、PMO 调用流程

```
Step 1: 准备 prompt 文件
  - Read claude-agents/reviewer.md
  - 替换占位符（{target}/{feature_name}/{stage}/{file_list}）
  - 写入临时 prompt 文件：dispatch_log/{NNN}-external-claude-review.prompt.md

Step 2: 准备输出文件路径
  - output_file = external-cross-review/{stage}-claude.md
  - 确保目录存在

Step 3: 调用 wrapper
  - bash 运行 invoke_claude_external_review

Step 4: 检查 exit code
  - exit code == 0:
    ├── 校验 output_file 含合法 YAML frontmatter
    ├── 校验 perspective == "external-claude"
    ├── 校验 target / generated_at / files_read / findings 等字段齐备
    ├── 校验失败 → 重跑（≤2 次），仍失败 → 走"调用失败"分支
    └── 校验通过 → state.external_cross_review.reviewer_dispatches[].status = "completed"
  - exit code != 0（调用失败）:
    ├── Read stderr 文件，提取摘要（前 5 行 / 200 字符）
    ├── state.concerns 加 WARN 条目
    │     {
    │       "type": "external_cross_review_failed",
    │       "model": "claude",
    │       "stage": "{stage}",
    │       "exit_code": "{rc}",
    │       "stderr_summary": "{摘要}",
    │       "occurred_at": "{ISO 8601 UTC}"
    │     }
    ├── state.external_cross_review.reviewer_dispatches[].status = "failed"
    ├── 跳过该 Stage 的外部 review，继续主对话 review 链路
    └── 在 PMO 完成报告中显式列出"外部 review 降级"

Step 5: 清理临时文件
  - 保留 output_file（产物）
  - 删除 .stderr / .exitcode / .prompt.md 临时文件（可选，调试时保留）
```

---

## 三、常见 stderr 模式 + 处理

| stderr 关键字 | 含义 | state.concerns type |
|--------------|------|--------------------|
| `Authentication required` / `Unauthorized` / `401` | 未认证 | `external_auth_missing` |
| `network error` / `Connection refused` / `Timeout` | 网络问题 | `external_network_failure` |
| `rate limit` / `quota exceeded` / `429` | 配额 / 限速 | `external_rate_limit` |
| `model not found` / `invalid model` | 模型名错误（CLI 升级导致） | `external_model_unavailable` |
| `JSON decode error` / `parse error` | 输出格式异常（claude CLI bug 或被截断） | `external_output_malformed` |
| 无明确关键字 + exit code != 0 | 未知错误 | `external_unknown_error` |

无论哪种类型，处理路径相同：state.concerns + 降级单视角 review。

---

## 四、独立性约束（与 reviewer.md 配套）

shell 调用时**必须**确保 prompt 文件中：
- 不含其他角色（架构师 / QA / PMO 自身）已写的评审产物路径
- 不含 PRD-REVIEW.md / TC-REVIEW.md / TECH-REVIEW.md / discuss/* / pmo-internal-review.md 等评审草稿

PMO 在准备 prompt 文件时必须 grep 校验 `{file_list}`，发现违规路径时拒绝调用并记录 concerns。

---

## 五、模型版本配置

默认调用 `--model claude-sonnet-4-6`。可在 `.teamwork_localconfig.md` 配置覆盖：

```yaml
external_claude_model: claude-sonnet-4-6  # 默认
# 或
external_claude_model: claude-opus-4-6     # 高质量
# 或
external_claude_model: claude-haiku-4-5    # 低成本
```

PMO 在调用前读取 localconfig，未配置则用默认值。

---

## 六、与 codex-agents 调用的差异

| 维度 | codex CLI 调用 | claude CLI 调用 |
|------|---------------|-----------------|
| 主对话宿主 | claude-code（用 Task 调起 codex-agents 中的 toml） | codex-cli（shell 调起 claude --print） |
| 调用接口 | `Task(subagent_type, ...)` 或宿主原生机制 | `bash` 工具 + `claude` CLI |
| Prompt 注入 | toml 内 `developer_instructions` 静态 | shell 调用前主对话替换占位符 |
| 输出获取 | Task 返回值 | stdout 重定向到文件 |
| 错误处理 | Task 工具抛异常 | exit code + stderr 捕获 |

---

## 七、版本记录

- v7.3.10+P0-24（首次发布）：建立 Codex CLI 主对话调用 Claude CLI 子进程的 shell 范本 + 失败降级路径
