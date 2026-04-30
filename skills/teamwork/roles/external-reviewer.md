# External Reviewer（外部模型评审角色）

> v7.3.10+P0-38 新增。原 v7.3.10+P0-24 / P0-28 的"外部模型"独立维度升格为评审角色，与 PL/RD/QA/Designer/PMO/Architect 平级，统一进入各 Stage 的评审角色组合（review_roles[]）。
> 🔴 立场独立性是本角色的核心价值——任何让 external 与主对话模型同源的设计变更都违反角色契约。

**触发**：在 Plan / Blueprint / Review Stage 入口被 PMO 实例化为 review_roles[] 之一时启动。

**执行方式**：仅 `external-shell`（不允许 main-conversation / subagent，立场独立性要求物理隔离）。

---

## 一、角色定位（核心价值）

🔴 **唯一不可替代的价值**：训练语料 + 推理偏差与主对话模型**统计独立**。

```
内部评审角色（PL/RD/QA/Designer/PMO/Architect）：
  └── 同一主对话模型在不同 prompt 下的输出
  └── 注意力分布相关，存在"同模型盲点"
  └── 4-5 个角色并行评审仍然可能错过同类型的 finding

external 评审角色（codex / claude）：
  └── 真正不同的模型（异质训练语料 + 异质推理偏差）
  └── 训练语料内的反例分布与主对话模型独立
  └── 捕捉同模型多角色评审看不到的盲点
```

🔴 **核心约束**：external 必须是与主对话模型**异质**的真实模型实例。

```
主对话宿主         external 候选     合理性
─────────────────────────────────────────────────
claude-opus       codex-cli         ✅ 异质（OpenAI 训练）
claude-opus       claude-cli        ❌ 同源（同 Anthropic 训练）→ 不应启用
codex-cli         claude-cli        ✅ 异质
codex-cli         codex-cli         ❌ 同源
```

init Stage 角色可用性扫描时（detect-external-model.py）必须按异质性筛选，**同源外部模型即使可用也应从 available_roles 剔除 external**。

---

## 二、可用性来源（triage Stage 决定，v7.3.10+P0-38-A 修订）

`state.available_roles[]` 是否包含 `external` 由 triage Stage Step 4 的角色可用性扫描决定（v7.3.10+P0-38-A 修订自 P0-38）：

```
triage Stage Step 4：
  ├── 探测主对话宿主（host_main_model）
  ├── 探测可用 CLI（claude-cli / codex-cli）
  ├── 异质性匹配：找到与主对话模型异质的外部 CLI
  ├── 找到 → state.available_roles[] 加 "external"
  │           state.external_cross_review.model = "codex" or "claude"
  └── 未找到 → state.available_roles[] 不含 "external"
              state.external_cross_review.model = null
              state.concerns 加 INFO 条目（不报警，仅信息记录）
```

🟢 **v7.3.10+P0-38-A 设计意图**：每次 Feature 启动时实时扫描（不在 init），反映运行时环境变化（用户中途装/卸 CLI 即生效）；available_roles 不是会话级常量，是 Feature 决策时快照。

triage Step 8 输出 execution_plan_skeleton 时，execution_hints 文本中的 external 角色仅在 available_roles 含 external 时出现——不可用时 **PMO 不在 hint 中提及 external**，用户面无感降级。

---

## 三、通用评审契约（与具体 Stage 无关）

🔴 **以下原则跨所有 Stage 通用**，不写"在 Goal-Plan Stage 就...在 Blueprint 就..."的分支判断。具体 Stage 下的评审目标（target / target_files / dimensions / forbidden_files / output_path）由调用方（PMO 在 Stage 入口）通过 dispatch context 注入。

### 3.1 立场独立性硬约束

🔴 必须读：调用方在 dispatch context 中指定的 `target_files[]`
🔴 必须不读：调用方在 dispatch context 中指定的 `forbidden_files[]`（通常含同 Stage 的内部评审产物，如 PRD-REVIEW.md / TC-REVIEW.md / pmo-internal-review.md）
🔴 必须不读：state.json（防止读流程上下文污染独立性）

🔴 **违反 = 角色契约失败**：dispatch 失败 → state.concerns 加 BLOCK 条目 → 用户决策。

### 3.2 评审深度要求

🔴 不接受橡皮图章：必须给至少 1 条实质 finding。

```
finding schema（统一）：
  id          # 角色前缀 + 序号，如 EXT-1
  severity    # high | medium | low | info
  category    # technical-consistency | business-alignment | ux | quality | business-decision
  description # 1-2 句问题描述
  suggestion  # 建议改法（具体方向）
  rationale   # 为什么这是问题（原理性解释）
```

🔴 即便"无明显问题"也必须输出至少 1 条 info 级 finding + 在文末列出"已检查的维度"（防止表面无 finding 实际未真实评审）。

### 3.3 输出 schema（统一）

YAML frontmatter + 文末"已检查的维度"段：

```yaml
---
perspective: external-codex | external-claude
target: prd | blueprint | code-review
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

🔴 PMO 接收输出后必须校验 frontmatter 字段齐备 + findings 非空（≥1 条）+ forbidden_files_acknowledged 完整。

---

## 四、调用 context 来源（已物化的文件）

external 角色"在不同 Stage 评审什么"由调用方（PMO 在 Stage 入口）通过现有文件物化，不在角色规范里写 Stage 分支：

| Stage | context 物化文件 |
|-------|----------------|
| Plan | `codex-agents/prd-reviewer.toml` 或 `claude-agents/reviewer.md`（按 model 选）|
| Blueprint | `codex-agents/blueprint-reviewer.toml` 或 `claude-agents/reviewer.md` |
| Review | `codex-agents/reviewer.toml` 或 `claude-agents/reviewer.md` |

每个文件的 developer_instructions / prompt 段已包含：
- target_files（必读文件）
- review_dimensions（评审维度）
- forbidden_files（不能读的文件）
- output_path（产出位置）

📎 **设计含义**：external 是**单一角色**，三种 target 的差异通过"context 物化文件不同"表达，不通过角色内部分支表达——这与 RD 角色规范的设计一致（roles/rd.md 不写"在 Goal-Plan Stage 评审什么、在 Dev Stage 写什么"，这些写在 Stage spec 和各类 standards 里）。

---

## 五、PMO 在 Stage 入口的实例化职责

PMO 在 Plan / Blueprint / Review Stage 入口（不是 triage Stage）做以下决策：

```
Step 1：读 execution_hints + state.available_roles（v7.3.10+P0-38-A 修订）
   ├── 来自 state.execution_plan_skeleton.stages[{stage}].execution_hints（文本，含启用建议）
   └── 必读 + cite 原文 + 决策时参考

Step 2：基于上游产物（PRD / TC+TECH / 代码）判断 external 是否实际启用
   ├── 启用条件：execution_hints 推荐 external + state.available_roles 含 external + 产物复杂度足够（PMO 智能信号）
   └── 不启用：hint 不推荐 external 或 available_roles 不含，或产物简单到外部视角边际收益低

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

🔴 **PMO 不在角色规范里维护 Stage 分支**——分支由"PMO 在 Stage 入口的实例化逻辑"承担，本文件只描述通用契约。

---

## 六、失败降级

| 失败原因 | 处理 |
|---------|------|
| init 探测时同源外部不可用 | available_roles 不含 external；triage 推荐不出现 external；流程不阻塞 |
| Stage 入口 dispatch 失败（CLI 错误 / 网络 / 超时）| 重试 ≤2 次；仍失败 → state.concerns 加 WARN + 标记本次外部评审 SKIPPED + 不阻塞 Stage 完成（依靠内部多视角评审兜底）|
| 输出 schema 不合法（frontmatter 缺字段 / findings 为空）| 重试 ≤1 次；仍不合法 → state.concerns 加 WARN + 标记 INVALID + PMO 在 Stage 摘要引用 stderr 摘要 |
| forbidden_files_acknowledged 不完整 | 视为立场独立性违规 → state.concerns 加 BLOCK + ⏸️ 用户决策（强制接受 / 重做 external 评审 / 跳过外部视角）|

🔴 关键原则：external 是**质量增强**角色，不是流程必需角色。其失败不应阻塞 Stage 完成（除非 forbidden 违规这种立场独立性事件）。

---

## 七、与其他角色 / 文件的关系

| 文件 | 关系 |
|------|------|
| [roles/pmo.md](./pmo.md) | PMO 是 external 角色的调度方（在 Stage 入口实例化 + dispatch + 接收输出）|
| [stages/init-stage.md](../stages/init-stage.md) | init Stage 不做角色扫描（v7.3.10+P0-38-A 回退）|
| [stages/triage-stage.md](../stages/triage-stage.md) | triage Step 4 决定 external 是否进入 available_roles + Step 8 在 execution_hints 文本中给建议（仅当可用）|
| [stages/goal-plan-stage.md](../stages/goal-plan-stage.md) | Goal-Plan Stage 入口实例化时决策 external 启用 |
| [stages/blueprint-stage.md](../stages/blueprint-stage.md) | Blueprint Stage 入口同上 |
| [stages/review-stage.md](../stages/review-stage.md) | Review Stage 入口同上 |
| [codex-agents/{prd,blueprint,reviewer}.toml](../codex-agents/) | external 角色在三种 target 下的 codex CLI context 物化 |
| [claude-agents/reviewer.md](../claude-agents/reviewer.md) | external 角色的 claude CLI 调用 prompt 物化 |
| [claude-agents/invoke.md](../claude-agents/invoke.md) | external（claude 实例）的 shell 调用范本 |
| [templates/external-cross-review.md](../templates/external-cross-review.md) | 外部评审 6 项 checklist + 输出 schema 详细模板 |
| [templates/detect-external-model.py](../templates/detect-external-model.py) | init Stage 调用，判断 external 是否可用 |

---

## 八、立场独立性的最后强调（不可妥协）

🔴 **任何让 external 与主对话模型同源的设计变更都违反本角色契约。**

具体禁止：
- ❌ 让主对话模型 cosplay external（如 prompt 模拟"你是 codex"但实际是 claude 在跑）
- ❌ external 角色 dispatch 时复用主对话已有的 context（如 PRD-REVIEW.md / discuss/*.md）
- ❌ 在 Subagent 模式下"假装独立"（即便 fresh context，仍是同模型）
- ❌ 用主对话模型作为 external 的 fallback（同源外部不可用 → 直接 OFF，不降级到主对话）

如果违反，外部模型评审失去全部价值——它的训练语料独立性消失，与多一次内部评审无差异。

🔴 PMO 在每次 dispatch external 时必须 cite 一行：
```
✅ external 角色启用：model={codex|claude}，主对话宿主={claude|codex}（异质性已确认）
```

异质性未确认或同源 → 不允许 dispatch。
