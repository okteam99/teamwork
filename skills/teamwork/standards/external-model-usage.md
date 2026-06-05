# 外部模型合规使用规范

> 🔴 **本文件是 teamwork 调用外部模型(codex / gemini / claude-cli 等)的唯一权威源**。SKILL.md 红线 R1(代码写权归 RD)+ R7(证据闭环)顶层 cite 本文件。
>
> 🟢 **抽出来源**: 实战触发——用户分享 codex 账号收到 OpenAI "cyber abuse" 警告 · 根因是 teamwork 把 codex CLI 当 AI agent 后端用(5/8 profile full sandbox + service_tier=fast + hooks 自动触发 + AI 编排 AI)。
>
> 🟢 **PMO 主路径** = `state.py external-review --feature <path> --stage <stage>` · 详 `state.py external-review --help` + §十一 异质性硬约束。PMO 心智 = 2 个业务参数 · host / model / which / profile / 文件命名 全自动。本文 §五/§六 是底层实现 · 已物化到工具 · PMO 不必读。

---

## 一、核心原则（4 条硬约束）

```
1. 只读约束：外部模型只能读代码 · 不写代码库 · 不能执行命令
 ├── codex 路径：物理拦截 · 所有 codex profile sandbox_mode = "read-only"（写被 sandbox 挡 · 无 liveness 文件）
 └── claude doc 模式：唯一例外 = 启动写 `review_start.log`（liveness 信号 · 非评审产物 · `--allowedTools Write` 限范围 + state.py 跑完清理）· 其余一律不写

2. 评审角色约束：外部模型在 teamwork 中**只承担评审角色**
 ├── reviewer.toml（代码评审）/ blueprint-reviewer.toml（蓝图评审）/ prd-reviewer.toml（PRD 评审）
 └── ❌ 禁止承担 dev / test / e2e / design / planner 等"自主执行"角色

3. 输出约束：外部模型只输出 markdown 评审记录
 └── 不输出 patch · 不输出可执行脚本 · 不输出"我已修改了 X 文件"

4. 调用频率约束：受 review_roles[] 控制 · 用户可 opt-out
 ├── 每个 Stage 实例化时 PMO 决策 active_roles 是否含 external
 └── Blueprint + Review **默认含** · 用户在 PMO 初步分析决策项呈现时可显式 opt-out
```

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
| `blueprint-reviewer.toml` | read-only | TC + TECH 蓝图评审 | Blueprint Stage external 角色（**opt-out**） |
| `prd-reviewer.toml` | read-only | PRD 评审 | Goal Stage external 角色（opt-in） |

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

> 🟡 **已物化**:`state.py external-review` 内置 prompt 注入(claude 路径读 `claude-agents/reviewer.md` 模板 · codex 路径 codex CLI 自带 review 模式)。PMO 不必读本节 · 仅 debug / 适配新 reviewer 模型时参考。

调用 codex 时 prompt 头部**必须**包含以下角色边界声明:

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

> 🟡 **已物化**:`state.py external-review` 内置 profile 选择(stage→profile mapping)+ 校验 profile 文件存在 + 校验 reviewer.toml sandbox=read-only(代码内 enforce)。PMO 不必读本节 · 仅 codex profile 配置变更时参考。

```
codex-agents/*.toml 必须满足：
□ sandbox_mode = "read-only"（无例外 · 含 deprecated profile）
□ 不含 service_tier = "fast"（删除该项）
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

- `tools/state.py` external-review 命令 — 调用主路径(详 `state.py external-review --help`)
- `codex-agents/*.toml` — codex profile 配置(全部 read-only · 无 service_tier · state.py 内部按 stage 自动选)
- `claude-agents/reviewer.md` — claude CLI 评审 prompt 模板(state.py 路径自动 pipe 给 claude -p)
- `roles/external-reviewer.md` — external 角色契约
- `templates/external-cross-review.md` — 评审记录模板(§五 整合流程已物化)
- (历史 `claude-agents/invoke.md` / `claude-agents/README.md` / `codex-agents/README.md` 已删除 · 调用细节进 state.py)

---

## 十一、异质性硬约束

> 🔴 **实战触发**:F034 review stage PMO 没找到 `which codex` · 选用 `Agent subagent_type=general-purpose` 起 Claude isolated context 自审 · 标 frontmatter `review_model: claude-opus-4-isolated-context` 「透明」· 用户察觉后承认违 R3 红线。
>
> 🟢 **本节是 PMO 主路径权威源** —— 顶部简介已指向此节 · §五/§六 是已物化的底层细节。

### 11.1 异质性定义(不可妥协)

**external review = 异质模型审查** —— 与主对话宿主模型**统计独立**的 LLM 提供独立视角。

| 类型 | 算不算异质? | 理由 |
|---|---|---|
| 主对话 Claude → codex CLI(GPT) | ✅ 算 | 训练语料 / 推理倾向独立 |
| 主对话 Claude → gemini CLI(Google) | ✅ 算 | 同上 |
| 主对话 Codex → claude-cli | ✅ 算 | 反向也成立(看宿主) |
| 主对话 Claude → `Agent subagent_type=general-purpose` | ❌ **不算** | 同模型 · 同盲点 · isolated context 只隔离对话历史 · 不隔离模型权重 |
| 主对话 Claude → claude-cli 子进程 | ❌ **不算** | 同模型自审 |
| 用 frontmatter `review_model: claude-isolated` 标"透明" | ❌ **不算** | 透明 ≠ 合规;透明只承认"我做了不达标" · 不替代"做达标" |

> **诚实降级自审(self-review-fallback)**:异质 CLI **客观不可用**(未装/未登录/配额满·已重试失败)时 · 可 `external-review --self-review-fallback --reason '...'` 跑同模型 fresh exec 自审 —— 但它**仍是上表第 4 行(不算异质)**,故落 `self-review/`(不进 `external-cross-review/`)· **不满足 P0-154**。它只是异质不可用时的**弱安全网 + audit evidence**,要继续仍须修环境重跑真异质、或 `change-review-roles` 显式移除 external。**绝不**用它冒充异质通过门禁。
>
> **单模型 opt-out(`disable_heterogeneous_review`)**:只有一个模型的用户可在 `.teamwork_localconfig.json` 设 `disable_heterogeneous_review: true`(默认 false)· 则 `external-review` **自动**降级为宿主自身模型 exec 自审 · 落 `external-cross-review/`(**满足 P0-154** · frontmatter 标 `heterogeneous:false degraded:true degraded_mode:config-disabled`)· 让单模型用户能走完流程。代价:**非异质 · 同盲点 · 交叉 review 质量下降** —— 故每次 `bootstrap` 启动**持续 WARN** 提醒(`checks.heterogeneous_review.status=disabled` + `pmo_must_read`)· 建议装好第二个模型 CLI 后删此项恢复异质。与 self-review-fallback 的区别:后者是**临时 stopgap**(不满足门禁)· 本项是**项目级长期策略**(满足门禁 · 但被 startup WARN 持续提醒)。

### 11.2 文件命名硬规约(state.py 物化校验)

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

state.py 在 `<stage>-complete` evidence 校验时物化拦截 · 详 `_evidence_external_review_artifact`(_v8_stage_specs.py)。

### 11.3 PMO 调用前必做(防 F034 反模式)

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

### 11.4 反模式黑名单(case 实证)

| 反模式 | 案例 | 治本 |
|---|---|---|
| Agent subagent 当 external 自审 | F034 PRD/TECH/Code 3 阶段 fall(2026-05-24)| 7.2 文件名校验 BLOCKED |
| 透明 frontmatter 伪装合规 | `review_model: claude-isolated` 自承"不达标"但仍提交 | 7.2 frontmatter 校验 BLOCKED |
| 看到工具不在就 substitute | "/codex 是 user-only skill 不能 invoke → 用 Agent 起" | 7.3 必先 `which` · 不在 stop |
| 没 cite 上游 Feature 范式 | F033 既有 `*-codex.md` 在 worktree 内 · F034 没 grep | 7.3 跑前 cite 范例 |

