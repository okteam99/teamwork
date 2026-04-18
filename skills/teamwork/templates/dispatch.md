# Dispatch 文件模板

> 每次 Subagent dispatch 由 PMO 先生成此文件，Subagent 读取后执行，完成时 append Result 区域。
> 位置：`docs/features/{Feature}/dispatch_log/{序号}-{subagent-id}.md`
> 命名规则：序号从 001 起，三位数字，补零；subagent-id 见 agents/README.md §一 速查表（如 rd-develop / arch-code-review / qa-code-review / integration-test / api-e2e / blueprint / designer）
> 并行 dispatch（同一 Stage 内同时发起多个）各用独立文件，序号递增但可视为同一批次

---

## 模板：Dispatch {序号}: {Stage} → {subagent-id}

```markdown
# Dispatch {序号}: {Stage} → {subagent-id}

## Meta
- Feature: {缩写}-F{编号}-{功能名}
- Sub-project: {子项目缩写}（{business / midplatform}）
- Dispatched at: {ISO 8601 时间戳}
- Dispatched by: PMO
- Pre-check level: {L1 / L2 / L3} ✅
- Host: {Claude Code (Task tool) / Codex CLI (agent spawn) / Gemini CLI (主对话) / 主对话降级}
- Model: {opus / sonnet / haiku / 继承主对话}
- Previous dispatch: {前一次相关 dispatch 文件相对路径，无则写「无」}
- Batch: {独立 / 并行批次-{序号}}（并行 dispatch 标注同一批次号，便于 INDEX 汇总）

## Task
{一段话描述任务。保持精简，详细需求靠输入文件。}

## Input files (read in order)
🔴 Subagent 必须按此顺序读取。列表外的文件仅供参考，读与不读由 Subagent 判断。

1. `{SKILL_ROOT}/agents/README.md` ← 通用执行规范（所有 Subagent 必读）
2. `{SKILL_ROOT}/agents/{subagent-id}.md` ← 本角色执行规范
3. `{SKILL_ROOT}/standards/{common|backend|frontend}.md` ← 编码规范
4. `{绝对路径}/PRD.md` ← 需求来源
5. `{绝对路径}/TECH.md` ← 技术方案
6. `{其他必需文件绝对路径}` ← 用途说明

## Additional inline context
{极简 1–5 行，或填「无」。仓库级约束（CLAUDE.md/AGENTS.md/GEMINI.md）可在此直接注入原文。长内容必须走 Input files。}

## 🎯 Key Context（PMO 补充关键点，Subagent 必读）

🔴 **硬规则**：PMO 生成 dispatch 文件时必须逐项判断以下 6 类关键点，**无则写「-」（证明已判断）**，禁止留空或删除字段。无判断痕迹 → Subagent 返回 NEEDS_CONTEXT，PMO 重新生成。

🎯 **只写 Subagent 从 Input files 里读不到的信息**。若信息在输入文件中已有，禁止重复注入（反模式：把 PRD 摘要复制进来）。

### 1. 历史决策锚点
{从本 Feature 上游 Stage / CHG 记录 / Plan Stage 纪要提取的用户已明确拍板的决策。每条附来源引用（文件+位置）。}
- 示例：用户明确选 PostgreSQL，不用 MySQL（来源：Plan Stage PL-PM 讨论纪要 R2 共识项 #3）
- 无则写：`-`

### 2. 本轮聚焦点
{重派或修复场景必填，初派可为空。}
- 派发轮次：{初派 / 重派第 N 轮}
- 本次重点：{上次遗漏的问题 / 新增的审查维度}
- Previous dispatch 问题清单：{引用 `NNN-{subagent}.md` 的 Concerns 段}
- 初派无此类信息 → 写 `-`

### 3. 跨 Feature 约束
{只有 PMO 知道的跨 Feature 冲突/兼容要求。}
- 禁改文件/模块：{路径 + 原因，如「services/auth.py 被 F042 并行修改中，禁改」}
- 兼容要求：{接口 schema / 数据模型 与 F0XX 保持兼容}
- 无则写：`-`

### 4. 已识别风险 / 历史陷阱
{PMO 预检中发现、或 KNOWLEDGE.md / 历史 Bug 留下的教训。}
- 来源：{预检 / KNOWLEDGE.md L{行号} / BUG-XXX}
- 说明：{如「此模块上次因 N+1 查询出过事故，注意 ORM 查询性能」}
- 无则写：`-`

### 5. 降级授权
{PMO 预先授权的降级路径，Subagent 遇到对应问题可直接降级，无需反向咨询 PMO。}
- 示例：Codex CLI 不可用 → 授权降级 Sonnet 执行 Review，必须输出 WARN
- 示例：worktree 创建失败 → 授权直接在主分支执行
- 无则写：`-`

### 6. 优先级 / 容忍度
{本次 dispatch 的质量-进度权衡约束，Subagent 决策时参考。}
- 优先级：{进度优先 / 质量优先 / 平衡}
- DONE_WITH_CONCERNS 接受度：{可接受 / 不可接受（必须 DONE 或 NEEDS_FIX）}
- 无特殊要求 → 写 `平衡 / 可接受`

## Edit scope constraints
- 允许读写：{子项目路径}/（功能代码 + 测试 + 配置）
- 允许读写：{绝对路径}/docs/features/{Feature}/（文档产出）
- 允许只读：{项目根}/docs/（ARCHITECTURE.md / KNOWLEDGE.md 等）
- 允许只读：{SKILL_ROOT}/standards/
- 🚫 禁止：其他子项目路径 / .env / credentials.* / .git/ 直接操作

违反立即停止，记录到 concerns，返回 DONE_WITH_CONCERNS。

## Expected deliverables
- {文件路径 1：做什么}
- {文件路径 2：做什么}
- {测试/构建命令的实际输出}
- {角色报告：如 RD 自查 / arch CR 报告}

## Progress Log（Subagent 维护，每步开始/完成时 append）

🔴 **硬规则**：Subagent 必须在每个 Step 开始和完成时 append 一行到此段，不允许黑盒执行完才一次性补全。
🔴 **目的**：PMO 读本段作为时间轴「回放」呈现给主对话用户，替代无法实现的「实时流」。
🔴 **格式**：`- [HH:MM:SS] {step-name} {动作}（{状态}）{可选备注}`

### 必填事件类型

| 事件 | 何时写 | 示例 |
|------|--------|------|
| 📥 dispatch-received | Subagent 启动读完 dispatch 文件 | `- [10:05:12] dispatch-received 已读取 001-blueprint.md` |
| ▶️ step-start | 每个 Step 开始前 | `- [10:05:30] step-start Step 1: 读取规范文件` |
| ✅ step-done | 每个 Step 成功完成 | `- [10:06:42] step-done Step 1（耗时 1m12s，读取 5 个文件）` |
| ⚠️ step-concern | 执行中发现非阻塞问题 | `- [10:08:01] step-concern Step 3: PRD §4 与 TC-005 预期不一致，已记录 Concerns` |
| ⏸️ step-blocked | 执行被阻塞 | `- [10:09:30] step-blocked Step 4: 测试环境 DB 连接超时 3 次，终止后续` |
| 🔄 degradation | 触发降级路径 | `- [10:10:15] degradation worktree→off，原因：磁盘空间不足` |
| 🏁 subagent-done | 全部步骤完成，即将 append Result | `- [10:15:42] subagent-done 总耗时 10m30s，状态 DONE` |

### 模板段

```
- [HH:MM:SS] dispatch-received 已读取 {本 dispatch 文件名}
- [HH:MM:SS] step-start Step 1: {步骤名}
- [HH:MM:SS] step-done Step 1（耗时 {MmSs}）
- [HH:MM:SS] step-start Step 2: {步骤名}
- ...
- [HH:MM:SS] subagent-done 总耗时 {MmSs}，状态 {DONE/...}
```

### 反模式

```
❌ 全程只写一行「done」→ 失去追溯价值
❌ 每步完成后集中 append 多行 → Subagent 内部崩溃时段会丢失
❌ 不写时间戳 → 无法评估每步耗时
✅ 每个 Step 开始/结束实时 append（允许 step 内部中段也 append 说明进展）
```

## Return format
必须以以下状态之一结束，并 append "Subagent Result" 区域：
- ✅ DONE
- ⚠️ DONE_WITH_CONCERNS
- 🔄 NEEDS_CONTEXT
- 🔁 QUALITY_ISSUE
- ❌ BLOCKED
- 💥 FAILED

状态语义见 `{SKILL_ROOT}/agents/README.md §四 4.3 Subagent 返回状态分级处理`。

---

## Subagent Result

🔴 Subagent 必须在结束前 append 此区域。未 append = FAILED，PMO 不接受产出。

- Status: {DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / QUALITY_ISSUE / BLOCKED / FAILED}
- Completed at: {ISO 8601 时间戳}
- Files read（实际读取的文件清单，用于追溯）:
  - {路径 1}
  - {路径 2}
- Output files（产出/修改的文件）:
  - {路径 1}（+{N} 行 / 修改）
  - {路径 2}
- Test/Build output（关键命令的实际输出片段）:
  ```
  {粘贴关键输出，10-30 行，截断长输出保留头尾}
  ```
- Concerns（DONE_WITH_CONCERNS 必填；其他状态无则写「无」）:
  - {concern 1}
  - {concern 2}
- Degradation（降级事件，触发时必填，遵循 agents/README.md §四 降级 WARN 格式）:
  ```
  ⚠️ WARN [degradation-fallback]
  ├── reason  : {降级原因}
  ├── from    : {原计划路径}
  ├── to      : {实际兜底路径}
  ├── stage   : {Stage 名}
  └── impact  : {影响评估}
  ```
  无降级则写「无」。
- Role report（角色特定报告，格式见各角色规范）:
  {RD 自查报告 / arch CR 报告 / QA 代码审查报告 等}
```

---

## PMO 使用流程

```
Step 1: Dispatch 前
├── PMO 从本模板复制生成 dispatch 文件
├── 路径：docs/features/{Feature}/dispatch_log/{序号}-{subagent-id}.md
├── 填充 Meta / Task / Input files / Edit scope / Expected deliverables / Return format
├── 🔴 PMO 在主对话用 TodoWrite **预声明** Subagent 即将执行的 Step 列表
│   ├── 内容从 stage 文件的「执行流程」章节抽取
│   ├── 粒度：与 dispatch 文件 Expected deliverables 对齐（一个产出 = 一个 todo）
│   └── 用户在主对话立刻看到「接下来要做哪 N 步」
└── 保存文件（🔴 此文件写入完成是 dispatch 的前置条件）

Step 2: Dispatch
├── 根据宿主调用 Subagent（Task 工具 / Codex agent spawn / 主对话）
├── Subagent prompt 极简（~5 行）：
│   「你是 Teamwork {角色}。请读取以下 dispatch 文件并执行任务：
│    {dispatch 文件绝对路径}
│    完成后按文件末尾 "Subagent Result" 模板 append 执行结果。」
└── 不再在 prompt 中重复描述任务（所有内容都在 dispatch 文件里）

Step 3: Subagent 完成后
├── PMO 读取 dispatch 文件确认 Result 已 append
├── 未 append → 视为 FAILED，触发降级兜底流程（并写入 WARN）
├── 已 append 但状态异常 → 按 agents/README.md §四 4.3 处理
├── 🔴 PMO 读 dispatch 文件的 `Progress Log` 段，作为「时间轴回放」呈现给主对话用户
│   ├── 把每个 step-start/step-done 转成主对话 TodoWrite 状态更新
│   ├── 异常事件（degradation / step-blocked / step-concern）单独高亮显示
│   └── 失败/超时时 Progress Log 是排查根因的第一手资料
└── 根据 Result 更新 INDEX.md（见下方 INDEX 模板）

Step 4: INDEX 维护
├── 每次 dispatch 完成后，PMO 在 dispatch_log/INDEX.md 追加一行
└── INDEX 作为 Feature 全局 dispatch 视图
```

---

## INDEX.md 模板（dispatch_log 目录下）

```markdown
# Dispatch 索引 - {Feature 全名}

> 本 Feature 所有 Subagent dispatch 的汇总视图。详情见对应文件。

## 全景表

| # | Stage | Subagent | 发起时间 | 结果状态 | 耗时 | 降级 | 关键约束 | 文件 |
|---|-------|----------|----------|----------|------|------|----------|------|
| 001 | Blueprint | blueprint | 2026-04-16 10:05 | ✅ DONE | 4m | 无 | PG 强制、质量优先 | [001-blueprint.md](./001-blueprint.md) |
| 002 | Dev | rd-develop | 2026-04-16 10:32 | ✅ DONE | 8m | 无 | 禁改 auth.py（F042 并行） | [002-rd-develop.md](./002-rd-develop.md) |
| 003 | Review | arch-code-review | 2026-04-16 10:45 | ⚠️ DONE_WITH_CONCERNS | 3m | 无 | 聚焦 N+1 查询风险 | [003-arch-code-review.md](./003-arch-code-review.md) |
| 004 | Review | codex-review | 2026-04-16 10:45 | 💥 FAILED → 主对话降级 | 6m | ⚠️ Codex 不可用 | 授权降级 Sonnet | [004-codex-review.md](./004-codex-review.md) |

> 「关键约束」列：摘录 dispatch 文件 Key Context 中非 `-` 的最关键一条，便于人工审查时一眼识别本 Feature 累积的历史决策/风险。

## 降级事件汇总

| # | 降级类型 | 原因 | 影响 |
|---|---------|------|------|
| 004 | Codex → Sonnet | Codex CLI 不可用 | 模型能力差异，需用户关注 Review 质量 |

## 并行批次

- 批次-1：003（arch-CR）∥ 004（codex）∥ 005（qa-CR） — Review Stage 三路并行
```

---

## 设计原则

```
1. 🔴 一次 dispatch 一个文件（含并行的每一次）
   不合并到单文件避免并发写冲突；不按 Stage 合并避免历史缺失。

2. 🔴 Subagent prompt 极简（~5 行），所有上下文通过 dispatch 文件传递
   Subagent 不再接收长 prompt 注入；Task 工具 prompt 只指向 dispatch 文件路径。

3. 🔴 Subagent 必须 append Result，否则视为 FAILED
   硬规则，写进 agents/README.md。PMO 有权在未 append 时标记降级并自行补全。

4. 🔴 文件即审计单元：Input files 清单、实际 Files read 清单都在同一文件里
   「PMO 声称给了什么」vs「Subagent 实际看了什么」对比一目了然。

5. 🔴 并行 dispatch 各自独立文件，Batch 字段标注同批次
   避免并发写；INDEX.md 的「并行批次」段聚合视图。

6. 🔴 重新 dispatch（NEEDS_CONTEXT 补充后）→ 新文件 + Previous dispatch 字段指向前一次
   保留完整历史轨迹。

7. 🔴 Key Context 必须逐项判断（无则写 `-`），严禁留空或删除字段
   无判断痕迹的 dispatch 文件 → Subagent 返回 NEEDS_CONTEXT。
   只写 Subagent 从 Input files 里读不到的信息，禁止复制 PRD/TECH 摘要。

8. 🔴 Progress 可见性双保险：主对话 TodoWrite 预声明 + dispatch 文件 Progress Log
   由于 Subagent → 主对话无实时通道（宿主 API 同步阻塞），采用：
   ├── 前置：PMO 在主对话 TodoWrite 预声明 Subagent 的 Step 列表（Stage 执行流程）
   ├── 中途：Subagent 每步 append Progress Log（时间戳 + 事件）
   └── 事后：PMO 读 Progress Log 转成主对话 Todo 状态更新 + 高亮异常
   禁止 Subagent「黑盒跑完一次性回报」——Progress Log 是硬交付物。
```

---

## 生命周期

```
├── Feature 进行中：dispatch_log/ 持续累积，每次 Subagent dispatch 新增一个文件 + 更新 INDEX
├── Feature ✅ 完成：
│   ├── PMO 扫描所有 dispatch 文件，提取降级 WARN / DONE_WITH_CONCERNS / 重复 dispatch 等教训
│   ├── 写入 KNOWLEDGE.md「本 Feature dispatch 复盘」章节
│   └── dispatch_log/ 保留不删（可能用于后续排查）
└── Feature 归档：随 Feature 目录整体归档
```
