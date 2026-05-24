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

### 7.5 v8.20 物化路径:`state.py external-review`(推荐)

> 🟢 **v8.20 治本 F034 case-AI 5 层根因第 1/2/3 层(没 which / 没 cite / substitute)** —— 调用本身也物化 · PMO 不需要自己拼 codex/claude 命令 / 不需要选 reviewer profile / 不需要管 frontmatter 命名。

```bash
state.py external-review \
  --feature <path> \
  --stage {goal,blueprint,review} \
  --host {claude-code,codex-cli,gemini-cli} \
  [--model {codex,claude}]   # 显式覆盖 · 默认按 host 自动映射(claude-code→codex / codex-cli→claude)
  [--commit <SHA>]           # 缺省 state.stage_contracts.<stage>.auto_commit / git HEAD
  [--base <branch>]          # 缺省 state.merge_target
  [--title <title>]          # 缺省 "<feature_id> · <stage> stage external review"
  [--dry-run]                # 只输出将跑的命令 · 不实际调 CLI
```

#### 工具内部 7 步 SOP(对应 case 5 层根因)

| Step | 动作 | 治本根因 |
|---|---|---|
| 1 | host → model 自动映射 + 异质校验(同源 BLOCK) | 第 5 层(R3 降级)|
| 2 | `which <cli>` 验工具在 · 不在 BLOCK + hint(绝不 substitute)| 第 3 层(substitute)|
| 3 | stage → reviewer profile 自动选(prd-reviewer / blueprint-reviewer / reviewer)| 第 2 层(没 cite 范式)|
| 4 | commit / base 从 state.json fallback | 第 1 层(效率 · 减心智)|
| 5 | 跑 CLI(同步 · 5min timeout · capture stdout)| 第 1 层(自动)|
| 6 | 落 `external-cross-review/<stage>-<model>.md`(自动 frontmatter + body)| 第 4 层(透明伪装 = 文件名 + frontmatter 自动合规)|
| 7 | emit JSON 含 file_path / model_version / finding_count_estimate | 第 4 层(audit 留痕)|

#### F034 case 用 v8.20 重跑

```
$ state.py external-review --feature services/core/.../F034 --stage review --host claude-code
# step 1:host=claude-code → model=codex(自动)
# step 2:which codex → /opt/homebrew/bin/codex ✅
# step 3:stage=review → profile=codex-agents/reviewer.toml
# step 4:commit=state.stage_contracts.dev.auto_commit / base=state.merge_target
# step 5:跑 codex review --commit ... --base ... --title ...
# step 6:落 external-cross-review/review-codex.md(frontmatter review_model=codex-cli 0.133.0)
# step 7:emit OK + finding_count_estimate=12
```

→ PMO 不需要 grep F033 / 不需要拼 codex 命令 / 不需要管文件名 · 一条命令完成。

#### v8.19(校验)vs v8.20(主路径)互补

- **v8.19** = 兜底防御层(若 PMO 手工绕过 v8.20 自己写文件 · 仍被拦)
- **v8.20** = 推荐主路径 + 完全自动化

两者不冲突 · v8.20 的产物天然符合 v8.19 校验(文件名 + frontmatter 都自动合规)。

### 7.6 v8.21 进一步简化 · PMO 心智 2 参数(host 自动探测)

> 🟢 **v8.21 治本"PMO 还要知道宿主细节"** —— v8.20 PMO 还要传 `--host`(主对话宿主 enum)· v8.21 把 host 探测也物化 · PMO 心智 = `--feature` + `--stage` **(2 个业务参数)**。

#### 命令简化

```bash
# v8.20 PMO 心智 3 参数
state.py external-review --feature <path> --stage review --host claude-code

# v8.21 PMO 心智 2 参数(host 自动探测)
state.py external-review --feature <path> --stage review
```

#### host 探测优先级

1. **`--host` 显式传**(高级用户 / 覆盖 audit)
2. **`~/.teamwork/host_audit.json`**(bootstrap 跑成功后自动写)
3. env fallback(预留 hook · 暂未实现)

`bootstrap.py` 跑一次 = 写 `host_audit.json` · 此后所有 state.py 命令自动用此 host。

#### 失败模式

PMO 跑 `state.py external-review --feature ... --stage review` 但既没传 --host 也没 audit:
```
FAIL · --host 未传 + 无法自动探测(~/.teamwork/host_audit.json 不存在)
hint:二选一
  ① 跑 bootstrap 一次(python3 {SKILL_ROOT}/tools/bootstrap.py --host <claude-code|codex-cli|gemini-cli>)
     · 之后所有 state.py 命令自动用此 host
  ② 显式传 --host claude-code(或对应宿主)
v8.21 设计:bootstrap 跑过一次后 · PMO 心智 = --feature + --stage(2 个业务参数)· host 全自动
```

#### 透明留痕

emit JSON 含 `host_source` 字段(`explicit` / `audit` / `env`)· PMO 看到 host 来自哪里。

#### v8.20 vs v8.21 对比

| 维度 | v8.20 | v8.21 |
|---|---|---|
| PMO 必传参数 | `--feature` + `--stage` + `--host`(3 个)| `--feature` + `--stage`(2 个)|
| host 来源 | PMO 显式传 | bootstrap audit 自动读 |
| host_source emit | 无 | 有(explicit / audit / env)|

PMO 心智负担 -33% · 治本"PMO 不该关心的内部细节"(host enum / 宿主映射等)。

---

末。
