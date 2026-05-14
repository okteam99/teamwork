# External Reviewer 角色（External · 外部模型评审角色 · v7.3.10+P0-92 4 段重构）

> External Reviewer 作为唯一异质模型评审角色：训练语料 + 推理偏差与主对话模型**统计独立**。本文件按 **4 段极简结构 + Stage 速查 + 协同**（v7.3.10+P0-85 风格 C）：角色定位 / 评审职责 / 职能职责 / 特殊职责。
>
> 🔗 **评审契约速查**（v7.3.10+P0-92）：
> - 评审 verdict + finding severity → [standards/review-verdict.md](../standards/review-verdict.md)
> - 评审 scope → [standards/review-scope.md](../standards/review-scope.md)（External 在 prd / blueprint / code-review 三 scope）
> - **External 异质性硬约束** → [standards/external-model.md](../standards/external-model.md)
> - 🔴 **External 合规使用边界**（v7.3.10+P0-104 OpenAI ToS 合规） → [standards/external-model-usage.md](../standards/external-model-usage.md)（只读 / 评审 / 不执行 / 不写文件 · 物理拦截 cyber abuse 信号）
>
> v7.3.10+P0-38 创建 · v7.3.10+P0-38-A 修订（available_roles 决定迁到 triage Step 4）· v7.3.10+P0-72 PMO 直接判定（不再用脚本）· v7.3.10+P0-83 删 Goal-Plan external（仅 Blueprint/Review 适用）· v7.3.10+P0-104 加合规边界 cite（codex 账号 abuse 警告 case）。

**触发**：在 Blueprint / Review Stage 入口被 PMO 实例化为 review_roles[] 之一时启动。

**执行方式**：仅 `external-shell`（不允许 main-conversation / subagent · 立场独立性要求物理隔离）。

---

## 一、角色定位

🔴 **唯一不可替代的价值**：训练语料 + 推理偏差与主对话模型**统计独立**。

```
内部评审角色（PL/RD/QA/Designer/PMO/Architect）：
  └── 同一主对话模型在不同 prompt 下的输出
  └── 注意力分布相关 · 存在"同模型盲点"
  └── 4-5 个角色并行评审仍可能错过同类型 finding

External 评审角色（codex / claude）：
  └── 真正不同的模型（异质训练语料 + 异质推理偏差）
  └── 训练语料内的反例分布与主对话模型独立
  └── 捕捉同模型多角色评审看不到的盲点
```

🔴 **核心约束**：External 必须是与主对话模型**异质**的真实模型实例。

| 主对话宿主 | External 候选 | 合理性 |
|-----------|---------------|--------|
| claude-opus | codex-cli | ✅ 异质（OpenAI 训练）|
| claude-opus | claude-cli | ❌ 同源（同 Anthropic 训练）→ 不应启用 |
| codex-cli | claude-cli | ✅ 异质 |
| codex-cli | codex-cli | ❌ 同源 |

triage Stage Step 4 角色可用性扫描时（v7.3.10+P0-72 PMO 直接判定）必须按异质性筛选 · **同源外部模型即使可用也应从 available_roles 剔除 external**。

---

## 二、评审职责（核心 · 跨 stage 通用契约）

### 2.1 评审入口（按 stage）

| Stage | 评审对象 | External 角色 | context 物化文件 |
|-------|---------|---------------|-----------------|
| **Goal-Plan** | ❌ 不参与（v7.3.10+P0-83 删）| - | - |
| **Blueprint** | TC + TECH（异质视角）| 🟢 默认启用（v7.3.10+P0-153 翻转 P0-13 OFF · review_roles[] 默认含 external · 用户可 opt-out）| `codex-agents/blueprint-reviewer.toml` 或 `claude-agents/reviewer.md` |
| **Review** | 代码 + 单测（异质视角 · 默认推荐 ON）| 🟡 条件性（review_roles[] 含 external · 默认 ON 兼容 P0-28）| `codex-agents/reviewer.toml` 或 `claude-agents/reviewer.md` |

📎 **设计含义**：External 是**单一角色** · 不同 Stage 的差异通过"context 物化文件不同"表达 · 不通过角色内部分支表达——这与 RD / 架构师角色规范设计一致（不写"在 X Stage 评审什么、在 Y Stage 写什么"）。

### 2.2 评审 verdict + finding severity

🔗 **单源**：[standards/review-verdict.md](../standards/review-verdict.md)

### 2.3 评审 scope

🔗 **单源**：[standards/review-scope.md](../standards/review-scope.md)

### 2.4 立场独立性硬约束

🔴 **必须读**：调用方在 dispatch context 中指定的 `target_files[]`
🔴 **必须不读**：调用方在 dispatch context 中指定的 `forbidden_files[]`（通常含同 Stage 的内部评审产物 · 如 PRD-REVIEW.md / TC-REVIEW.md / pmo-internal-review.md）
🔴 **必须不读**：state.json（防止读流程上下文污染独立性）
🔴 **违反 = 角色契约失败**：dispatch 失败 → state.concerns 加 BLOCK 条目 → 用户决策

### 2.5 评审深度要求

🔴 **不接受橡皮图章**：必须给至少 1 条实质 finding。

🔴 **即便"无明显问题"也必须输出至少 1 条 info 级 finding** + 在文末列出"已检查的维度"（防表面无 finding 实际未真实评审）。

### 2.6 输出 schema（统一 · 跨 stage 通用）

YAML frontmatter + 文末"已检查的维度"段：

```yaml
---
perspective: external-codex | external-claude
target: blueprint | code-review
target_files: [...]
forbidden_files_acknowledged: [...]   # 显式声明已遵守不读
generated_at: <ISO 8601 UTC>
findings: [...]
findings_summary: { high: N, medium: N, low: N, info: N }
---

# {Stage} 外部评审报告

## findings
{每条 finding 详细展开}

## 已检查的维度（防表面 PASS）
- 维度 1: {结论}
- 维度 2: {结论}
- ...
```

**finding schema（统一）**：

```
id          # 角色前缀 + 序号 · 如 EXT-1
severity    # high | medium | low | info
category    # technical-consistency | business-alignment | ux | quality | business-decision
description # 1-2 句问题描述
suggestion  # 建议改法（具体方向）
rationale   # 为什么这是问题（原理性解释）
```

🔴 PMO 接收输出后必须校验 frontmatter 字段齐备 + findings 非空（≥1 条）+ forbidden_files_acknowledged 完整。

### 2.7 评审反模式（不可妥协）

🔴 **任何让 External 与主对话模型同源的设计变更都违反本角色契约。**

- ❌ 让主对话模型 cosplay external（如 prompt 模拟"你是 codex"但实际是 claude 在跑）
- ❌ External 角色 dispatch 时复用主对话已有 context（如 PRD-REVIEW.md / discuss/*.md）
- ❌ 在 Subagent 模式下"假装独立"（即便 fresh context · 仍是同模型）
- ❌ 用主对话模型作为 External 的 fallback（同源外部不可用 → 直接 OFF · 不降级到主对话）

如果违反 · External 模型评审失去全部价值——它的训练语料独立性消失 · 与多一次内部评审无差异。

🔴 PMO 在每次 dispatch external 时必须 cite 一行：
```
✅ External 角色启用：model={codex|claude} · 主对话宿主={claude|codex}（异质性已确认）
```

异质性未确认或同源 → 不允许 dispatch。

---

## 三、职能职责（External 角色无独立产出 · 仅评审输出）

### 3.1 核心产出

| 产物 | 触发时机 | Schema |
|------|---------|--------|
| **{Feature}/external-cross-review/{stage}-{model}.md** | Blueprint / Review Stage 实例化时 | §2.6 输出 schema |

### 3.2 可用性来源（triage Stage 决定）

`state.available_roles[]` 是否包含 `external` 由 triage Stage Step 4 角色可用性扫描决定（v7.3.10+P0-38-A 修订 · v7.3.10+P0-72 PMO 直接判定）：

```
triage Stage Step 4：
  ├── PMO 自报主对话宿主（host_main_model · 不读项目目录标记）
  ├── bash `command -v {cli}` 检查可用 CLI（claude / codex）
  ├── 异质性匹配：找到与主对话模型异质的外部 CLI
  ├── 找到 → state.available_roles[] 加 "external"
  │           state.external_cross_review.model = "codex" or "claude"
  └── 未找到 → state.available_roles[] 不含 "external"
              state.external_cross_review.model = null
              state.concerns 加 INFO 条目（不报警 · 仅信息记录）
```

🟢 **设计意图**：每次 Feature 启动时实时扫描（不在 init）· 反映运行时环境变化（用户中途装/卸 CLI 即生效）· available_roles 不是会话级常量 · 是 Feature 决策时快照。

triage Step 8 输出 execution_plan_skeleton 时 · execution_hints 文本中的 external 角色仅在 available_roles 含 external 时出现——不可用时 PMO 不在 hint 中提及 external · 用户面无感降级。

### 3.3 PMO 在 Stage 入口的实例化职责

PMO 在 Blueprint / Review Stage 入口（不是 triage Stage）做以下决策：

```
Step 1：读 execution_hints + state.available_roles
   ├── 来自 state.execution_plan_skeleton.stages[{stage}].execution_hints（文本 · 含启用建议）
   └── 必读 + cite 原文 + 决策时参考

Step 2：基于上游产物（PRD / TC+TECH / 代码）判断 external 是否实际启用
   ├── 启用条件：execution_hints 推荐 external + state.available_roles 含 external + 产物复杂度足够（PMO 智能信号）
   └── 不启用：hint 不推荐 external 或 available_roles 不含 · 或产物简单到外部视角边际收益低

Step 3：实例化决策
   ├── execution: external-shell（角色契约硬约束）
   ├── model: state.external_cross_review.model（codex 或 claude）
   ├── context 物化文件：codex-agents/{stage}-reviewer.toml 或 claude-agents/reviewer.md
   └── 写入 {stage}_substeps_config.review_roles[].role = "external"

Step 4：dispatch + 接收输出 + 校验 schema
   ├── 调用 codex CLI 或 claude CLI（参考 v7.3.10+P0-37 的 high+fast 默认）
   ├── 接收 {Feature}/external-cross-review/{stage}-{model}.md
   └── 校验 frontmatter + findings 非空 + forbidden_files_acknowledged 完整
```

🔴 **PMO 不在角色规范里维护 Stage 分支**——分支由"PMO 在 Stage 入口的实例化逻辑"承担 · 本文件只描述通用契约。

### 3.4 失败降级

| 失败原因 | 处理 |
|---------|------|
| init 探测时同源外部不可用 | available_roles 不含 external · triage 推荐不出现 external · 流程不阻塞 |
| Stage 入口 dispatch 失败（CLI 错误 / 网络 / 超时）| 重试 ≤2 次；仍失败 → state.concerns 加 WARN + 标记本次外部评审 SKIPPED + 不阻塞 Stage 完成（依靠内部多视角评审兜底）|
| 输出 schema 不合法（frontmatter 缺字段 / findings 为空）| 重试 ≤1 次；仍不合法 → state.concerns 加 WARN + 标记 INVALID + PMO 在 Stage 摘要引用 stderr 摘要 |
| forbidden_files_acknowledged 不完整 | 视为立场独立性违规 → state.concerns 加 BLOCK + ⏸️ 用户决策（强制接受 / 重做 / 跳过外部视角）|

🔴 **关键原则**：External 是**质量增强**角色 · 不是流程必需角色。其失败不应阻塞 Stage 完成（除非 forbidden 违规这种立场独立性事件）。

---

## 四、Stage 应用速查

| Stage | External 参与 | 主要工作 | context 物化文件 |
|-------|---------------|---------|-----------------|
| **Goal-Plan** | ❌ 不参与（v7.3.10+P0-83 删）| - | - |
| **UI Design** | ❌ 不参与 | - | - |
| **Blueprint** | 🟡 条件性 | TC + TECH 异质视角评审 | `codex-agents/blueprint-reviewer.toml` 或 `claude-agents/reviewer.md` |
| **Dev** | ❌ 不参与 | - | - |
| **Review** | 🟡 条件性（默认 ON）| 代码异质视角评审（异质模型代码评审是核心价值）| `codex-agents/reviewer.toml` 或 `claude-agents/reviewer.md` |
| **Test / Browser E2E / PM 验收 / Ship** | ❌ 不参与 | - | - |

---

## 五、与其他角色 / 文件的关系

| 文件 | 关系 |
|------|------|
| [roles/pmo.md](./pmo.md) | PMO 是 External 角色的调度方（在 Stage 入口实例化 + dispatch + 接收输出）|
| [stages/triage-stage.md](../stages/triage-stage.md) | init Stage 不做角色扫描（v7.3.10+P0-38-A 回退）|
| [stages/triage-stage.md](../stages/triage-stage.md) | triage Step 4 决定 external 是否进入 available_roles + Step 8 在 execution_hints 文本中给建议（仅当可用）|
| [stages/blueprint-stage.md](../stages/blueprint-stage.md) | Blueprint Stage 入口实例化时决策 external 启用 |
| [stages/review-stage.md](../stages/review-stage.md) | Review Stage 入口同上 · 默认推荐 ON |
| [codex-agents/{prd,blueprint,reviewer}.toml](../codex-agents/) | External 角色在三种 target 下的 codex CLI context 物化 |
| [claude-agents/reviewer.md](../claude-agents/reviewer.md) | External 角色的 claude CLI 调用 prompt 物化 |
| [claude-agents/invoke.md](../claude-agents/invoke.md) | External（claude 实例）的 shell 调用范本 |
| [templates/external-cross-review.md](../templates/external-cross-review.md) | 外部评审 6 项 checklist + 输出 schema 详细模板 |
| [standards/external-model.md](../standards/external-model.md) | 异质性核心规范 + E1/E2/E3 规则单源 |
| [架构师 / QA / RD / PM / Designer / PL / PMO 7 内部角色] | 内部评审与 external 形成同模型/异质模型的视角互补 · 独立性硬约束（互不引用 review 报告）|
