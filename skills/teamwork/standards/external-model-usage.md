# 外部模型合规使用规范

> 🔴 **本文件是 teamwork 调用外部模型（codex / gemini / claude-cli 等）的唯一权威源**。SKILL.md 红线 R1（代码写权归 RD）+ R7（证据闭环）顶层 cite 本文件。
>
> 🟢 **抽出来源**： 实战触发——用户分享 codex 账号收到 OpenAI "cyber abuse" 警告 · 根因是 teamwork 把 codex CLI 当 AI agent 后端用（5/8 profile full sandbox + service_tier=fast + hooks 自动触发 + AI 编排 AI）。

---

## 一、核心原则（4 条硬约束）

```
1. 只读约束：外部模型只能读代码 · 不能写文件 · 不能执行命令
 └── 物理拦截：所有 codex profile sandbox_mode = "read-only"

2. 评审角色约束：外部模型在 teamwork 中**只承担评审角色**
 ├── reviewer.toml（代码评审）/ blueprint-reviewer.toml（蓝图评审）/ prd-reviewer.toml（PRD 评审）
 └── ❌ 禁止承担 dev / test / e2e / design / planner 等"自主执行"角色

3. 输出约束：外部模型只输出 markdown 评审记录
 └── 不输出 patch · 不输出可执行脚本 · 不输出"我已修改了 X 文件"

4. 调用频率约束：受 review_roles[] 控制 · 用户可 opt-out
 ├── 每个 Stage 实例化时 PMO 决策 active_roles 是否含 external
 └── Blueprint + Review **默认含**＼�· 用户在 PMO 初步分析决策项呈现时可显式 opt-out
```

---

## 二、为什么必须合规（OpenAI ToS 视角）

> 实战触发：用户 codex 账号收到 OpenAI "cyber abuse" 警告。根因如下。

### 触发 OpenAI 自动检测的信号

| 信号 | 检测视角 |
|------|---------|
| 5/8 profile sandbox_mode = "full" | 自主任意命令执行能力 |
| AI 编排 AI（PMO 自动 spawn codex） | 自动化机器人行为 · 非人类交互 |
| service_tier = "fast" 全局 | API 级程序化优化信号 |
| 结构化 YAML 输出 + machine-verifiable | 把 CLI 当 API 后端用（绕过付费 API） |
| codex-agents/hooks.json 持久化触发 | 持久化机器人 |
| 链式 dispatch（一个完成触发下一个） | 自动化 pipeline |

### OpenAI 的 ToS 红线

**OpenAI 不允许将 Codex CLI 作为另一个 AI 的后端执行引擎**。teamwork 早期把 codex 当"全能 AI agent 替身"用 → 触发 cyber abuse 检测。

---

## 三、合规架构

```
✅ 合规姿态：
 主对话（Claude Code）
 ↓ 评审请求
 codex CLI（read-only 评审 profile · 输出 markdown）
 ↓ 评审记录
 主对话整合 → 用户决策
 ↓
 实际代码改动由主对话 RD 角色身份切换执行
 （不通过 codex）

❌ 禁止姿态－）：
 主对话 → codex (full sandbox · planner/rd/tester/designer/e2e) → 自主写代码 / 跑测试 / 执行 E2E
```

---

## 四、profile 分类

### ✅ 评审类（活跃 · teamwork 主流程使用）

| profile | sandbox | 用途 | dispatch 时机 |
|---------|---------|------|--------------|
| `reviewer.toml` | read-only | 代码评审（独立视角） | Review Stage external 角色（opt-in） |
| `blueprint-reviewer.toml` | read-only | TC + TECH 蓝图评审 | Blueprint Stage external 角色（**opt-out** �） |
| `prd-reviewer.toml` | read-only | PRD 评审 | Plan Stage external 角色（opt-in） |

### 🔴 已废弃

| profile | 原用途 | 替代方案 |
|---------|------|---------|
| `rd-developer.toml` | TDD 开发 | 主对话 RD 角色身份切换（roles/rd.md） |
| `tester.toml` | 集成测试 + API E2E | 主对话 QA 身份切换 + 项目测试命令 |
| `planner.toml` | PM + PL 写 PRD | 主对话 PM/PL 身份切换 + prd-reviewer 评审 |
| `designer.toml` | UI 设计 | 主对话 Designer 身份切换 |
| `e2e-runner.toml` | Browser E2E | 主对话 + Browser MCP（codex 无浏览器能力） |

> 🔴 deprecated profile 已强制 sandbox=read-only · 即便用户手动 ad-hoc 调用也不会触发 cyber abuse 信号。

---

## 五、prompt 注入硬规则

调用 codex 时 prompt 头部**必须**包含以下角色边界声明：

```
You are a code reviewer in the Teamwork framework.

🔴 STRICT CONSTRAINTS:
- You are READ-ONLY. Cannot write files. Cannot execute commands.
- Your output is markdown review records ONLY.
- Do NOT generate patches, scripts, or commit messages.
- Do NOT claim to have "modified", "fixed", or "implemented" anything.
- If you find issues, describe them — do not "auto-fix".

If asked to do anything outside review (write code, run tests, modify files):
respond "Out of scope. Teamwork uses external models for review only."
```

详见 `claude-agents/reviewer.md` 的 prompt 模板。

---

## 六、配置约束清单

```
codex-agents/*.toml 必须满足：
□ sandbox_mode = "read-only"（无例外 · 含 deprecated profile）
□ 不含 service_tier = "fast"（删除该�）
□ 不含 approval_policy 显式声明（走 codex 默认 = on-request）
□ 评审类 profile 的 developer_instructions 含「only review · no write · no exec」
□ deprecated profile 的 description 以 "[DEPRECATED ]" 起首
□ codex-agents/ 目录下不含 hooks.json（删除 · 持久化触发信号）
```

---

## 七、违规处置

| 违规类型 | 处置 |
|---------|------|
| 新增 profile sandbox=full | 阻断（codex CLI 启动时 fail · 红线 R1 违规） |
| 评审 profile 输出 patch / 写文件 | PMO 主对话整合时丢弃该输出 + 告警 |
| 主对话尝试 dispatch deprecated profile | 阻断 + 提示走身份切换替代 |
| 用户手动调用 deprecated profile（read-only） | 允许（已强制 read-only · 无 cyber abuse 风险） |

---

## 八、与 SKILL.md 红线的关系

**SKILL.md 红线 R1（代码写权归 RD）** 顶层：
> 外部模型仅用于只读评审 · 不参与代码写权 · 详见 standards/external-model-usage.md

**SKILL.md 红线 R7（证据闭环）** 顶层：
> 外部模型评审输出走主对话审计 · 不得作为自主 AI agent 后端 · 详见 standards/external-model-usage.md

红线层只保留一句话引用 · 详细 profile 配置 / prompt 注入 / 违规处置全部落本文件单源。

---

## 九、相关文件

- `codex-agents/*.toml` — codex profile 配置（全部 read-only · 无 service_tier）
- `claude-agents/reviewer.md` — 评审 prompt 模板（含 strict constraints 头）
- `claude-agents/invoke.md` — shell 调用规范
- `roles/external-reviewer.md` — external 角色契约
- `templates/external-cross-review.md` — 评审记录模板

---

## 十、申诉模板（用户使用）

如收到 OpenAI cyber abuse 警告，可参考以下申诉要点：

```
Subject: Codex CLI usage clarification (account: <email>)

This account uses Codex CLI as a review-only assistant within a software
development workflow (Teamwork framework · open source).

After reviewing OpenAI's terms, I have updated my configuration:
- All Codex profiles are now sandbox_mode = "read-only"
- Removed service_tier = "fast" (was originally for response speed)
- Removed automated hooks (no persistent triggers)
- 5 non-review profiles deprecated (won't be invoked by main flow)

Codex is now invoked only for:
1. Code review (read-only · output: markdown review records)
2. PRD review (read-only · output: markdown review records)
3. Architecture review (read-only · output: markdown review records)

Each invocation is preceded by a human pause point in the main session.
This is not an autonomous AI-controlling-AI setup.

Reference: standards/external-model-usage.md in the Teamwork skill repository.
```

---

## 七、异质性硬约束(v8.19 治本 SVC-CORE-F034 case)

> 🔴 **实战触发**:F034 review stage PMO 没找到 `which codex` · 选用 `Agent subagent_type=general-purpose` 起 Claude isolated context 自审 · 标 frontmatter `review_model: claude-opus-4-isolated-context` 「透明」· 用户察觉后承认违 R3 红线。

### 7.1 异质性定义(不可妥协)

**external review = 异质模型审查** —— 与主对话宿主模型**统计独立**的 LLM 提供独立视角。

| 类型 | 算不算异质? | 理由 |
|---|---|---|
| 主对话 Claude → codex CLI(GPT) | ✅ 算 | 训练语料 / 推理倾向独立 |
| 主对话 Claude → gemini CLI(Google) | ✅ 算 | 同上 |
| 主对话 Codex → claude-cli | ✅ 算 | 反向也成立(看宿主) |
| 主对话 Claude → `Agent subagent_type=general-purpose` | ❌ **不算** | 同模型 · 同盲点 · isolated context 只隔离对话历史 · 不隔离模型权重 |
| 主对话 Claude → claude-cli 子进程 | ❌ **不算** | 同模型自审 |
| 用 frontmatter `review_model: claude-isolated` 标"透明" | ❌ **不算** | 透明 ≠ 合规;透明只承认"我做了不达标" · 不替代"做达标" |

### 7.2 文件命名硬规约(state.py 物化校验)

`external-cross-review/*.md` 文件名 + frontmatter `review_model` 字段必须:

```
✅ 白名单(必含其一 · case-insensitive):codex / gpt / gemini / deepseek / qwen / llama / grok / mistral
❌ 黑名单(必不含): claude / anthropic / isolated / subagent / general-purpose / self
```

合法示例:
- `code-codex.md` / `prd-gemini.md` / `tech-deepseek.md`
- frontmatter `review_model: codex-1.0` / `review_model: gpt-5-pro`

违规示例(state.py BLOCKED):
- `code-claude-isolated.md`(命中黑名单 `claude` + `isolated`)
- `code-subagent.md`(命中黑名单 `subagent`)
- `external-review.md`(模糊 · 无白名单字面)
- frontmatter `review_model: claude-opus-4-isolated-context`(命中黑名单)

state.py 在 `<stage>-complete` evidence 校验时物化拦截 · 详 `_evidence_external_review_artifact`(_v8_stage_specs.py · v8.19+)。

### 7.3 PMO 调用前必做(防 F034 反模式)

```
Step 1:`which codex`(/ gemini / 其他白名单 CLI)
        ├── ✅ 在 → 跑(走合规 §三 架构)
        └── ❌ 不在 → STOP 问用户:
              "external review 候选 CLI 都不在(已查 codex/gemini/...) ·
               请提供 ① 安装哪个 / ② change-review-roles 移除 external(留 audit)"
              · 绝不 substitute(不用 Agent subagent 自审)

Step 2:跑前 cite 上游 Feature 1 个范例(grep F033/external-cross-review/*codex*)
        · 验证范式一致(文件命名 / frontmatter / verdict 结构)

Step 3:跑命令 · 落 *-codex.md / *-gemini.md / 等真异质模型文件
```

### 7.4 反模式黑名单(case 实证)

| 反模式 | 案例 | 治本 |
|---|---|---|
| Agent subagent 当 external 自审 | F034 PRD/TECH/Code 3 阶段 fall(2026-05-24)| 7.2 文件名校验 BLOCKED |
| 透明 frontmatter 伪装合规 | `review_model: claude-isolated` 自承"不达标"但仍提交 | 7.2 frontmatter 校验 BLOCKED |
| 看到工具不在就 substitute | "/codex 是 user-only skill 不能 invoke → 用 Agent 起" | 7.3 必先 `which` · 不在 stop |
| 没 cite 上游 Feature 范式 | F033 既有 `*-codex.md` 在 worktree 内 · F034 没 grep | 7.3 跑前 cite 范例 |

---

末。
