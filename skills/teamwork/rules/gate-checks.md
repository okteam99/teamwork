# 门禁规则与流转校验

> 🔴 PMO 每次阶段变更必须遵循此规范。本文件为门禁校验的权威定义。
> 转移表见 [flow-transitions.md](./flow-transitions.md)，预检流程见 [standards/common.md](../standards/common.md)。

## 🔴 流转校验（每次阶段变更必须输出，1 行即可）

**PMO 每次推进到下一阶段时，必须在阶段摘要中输出 1 行校验。缺少 = 非法流转。**

```
格式：📋 {当前阶段} → {目标阶段}（📖 {🚀自动/⏸️暂停/🔀条件}，来源：flow-transitions.md L{行号} "{原文}"）

示例：
📋 PMO 初步分析 → 🔗 Plan Stage（📖 ⏸️暂停，来源：flow-transitions.md L10 "PMO 初步分析 | 🔗 Plan Stage | ⏸️暂停"）
📋 🔗 Plan Stage → PRD 待确认（📖 ⏸️暂停，来源：flow-transitions.md L11 "🔗 Plan Stage | PRD 待确认 | ⏸️暂停"）
```

**🔴 规则**：
```
├── 必须引用 flow-transitions.md 的实际行号 + 原文片段（禁止只写"查 ✅"）
├── 🚀自动 → 禁止在此节点插入任何选择/确认/询问（红线 #12）
├── ⏸️暂停 → 必须等用户明确确认后才能继续
├── 校验不通过（不在转移表中）→ 🔴 禁止流转，输出原因
├── 缺少校验行直接切换阶段 → 违反红线 #5
└── 免输出场景：同一 Stage 内的子步骤 / Subagent 内部步骤（见下方「Stage 内部轻量标记」）
```

## Stage 内部轻量进度标记

**Stage 内部子步骤（如 Blueprint 内的 QA→评审→RD→架构师）不需要完整流转校验，改用轻量标记。**

```
格式：📌 {Stage名} {当前步/总步}: {子步骤名}

示例：
📌 Blueprint 1/4: QA 编写测试用例
📌 Blueprint 2/4: TC 多角色评审
📌 Blueprint 3/4: RD 编写技术方案
📌 Blueprint 4/4: 架构师方案评审

规则：
├── 不需要引用 flow-transitions.md 行号（子步骤不在转移表中）
├── 不需要更新 state.json（Stage 级别才更新，不是子步骤级别）
├── 不需要输出阶段摘要（Stage 完成时统一输出）
├── 子步骤间有内部评审问题 → 内部循环修复，不暂停不上报（除非超 3 轮）
└── 减少的开销：每个 Stage 内部省去 N-1 次完整校验 + N-1 次 state.json 更新
```

## 🔴 门禁检查（校验行之外，PMO 还需确认）

```
PMO 启动阶段 X 前：
├── 1. 项目根目录 CLAUDE.md / AGENTS.md / GEMINI.md → 存在则读取提取约束
├── 2. 前置阶段产物存在（Plan Stage→Blueprint/UI Design，Blueprint Stage→Dev Stage，Dev Stage→Review Stage，Review Stage→Test Stage）
├── 3. 暂停点已获用户确认
└── 4. 不通过 → 🔴 禁止进入，输出缺失项

PMO 不能以「方案简单」「时间紧迫」「用户没提到」为由跳过任何阶段。
跳过的唯一合法路径：RD 申请 → ⏸️ 用户同意。
项目根目录规则文件约束优先于 teamwork 默认规则。
```

## 🔴 state.json 流转状态同步更新（v7.3.2）

**PMO 每次流转后，必须同步更新 `{Feature}/state.json`：**

```
更新内容（从 flow-transitions.md 查出并写入 JSON）：
├── current_stage → 新阶段 ID
├── completed_stages → append 上一个 Stage
├── legal_next_stages → 查转移表
├── forbidden_transitions → 非相邻阶段
├── stage_contracts[current_stage] → input_satisfied / started_at
├── updated_at / updated_by → pmo
└── 更新时机：校验通过 → Write state.json → 切换角色 / 启动下一 Stage

🔴「forbidden_transitions」是硬约束：目标在列表中 → 阻塞 + 报错
compact 恢复时：读 state.json → 🔴 必须跟 flow-transitions.md 交叉校验
├── state.json 中的 legal_next_stages 与转移表一致 → 信任
├── 不一致 → 以 flow-transitions.md 为准，修正 state.json
└── state.json 可能被 PMO 误写入错误内容，不可无条件信任
state.json 缺失 → PMO 基于 Feature 目录现有文件和 flow-transitions.md 重建后再继续

🟢 v7.3.2：state.json 已替代 STATUS.md 成为 Feature 目录唯一状态文件。
   遇到遗留的 STATUS.md → 不删（历史保留），但 PMO 不再更新。
```

---

## 🔴 Stage 完成前 git 干净（v7.3.9 硬规则，P0 集中化）

**所有 Stage 在 `output_satisfied=true` 之前，PMO 必须执行 git 干净检查。本规则是所有 Stage 的统一门禁，各 Stage md 仅作引用。**

### 通用校验流程

```
PMO 执行：git status --porcelain

├── 空输出 → ✅ 继续流转，写 output_satisfied=true
└── 非空输出 → PMO auto-commit（不询问用户，不等待）：
    1. git add -A
    2. git commit -m "F{编号}: {Stage 名} - {简述}"
    3. 将 commit hash 写入 state.json.stage_contracts.{stage}.auto_commit
       ├── 单值字段（plan / ui_design / blueprint / blueprint_lite / dev / browser_e2e / ship）
       │   → auto_commit: "{hash}"（覆盖写；同 Stage 若触发多次则保留最后一次）
       └── 数组字段（review / test）
           → auto_commit: [...]（append；多轮 QUALITY_ISSUE 修复各一条）
    4. commit 成功后才允许 output_satisfied=true
```

### 各 Stage 的 commit message 规范

```
├── Plan Stage         : "F{编号}: Plan Stage - {简述}"           （例：PRD / PRD-REVIEW / discuss 产物）
├── UI Design Stage    : "F{编号}: UI Design Stage - {简述}"      （例：UI.md / preview/*.html / sitemap）
├── Blueprint Stage    : "F{编号}: Blueprint Stage - {简述}"      （例：TC.md / TECH.md / 评审文件）
├── BlueprintLite Stage: "F{编号}: BlueprintLite Stage - {简述}"  （例：TC.md / IMPL-PLAN.md）
├── Dev Stage          : "F{编号}: Dev Stage - {简述}"            （例：功能代码 + 单测）
├── Review Stage       : "F{编号}: Review Stage - fix {简述}"     （每轮修复独立 commit）
├── Test Stage         : "F{编号}: Test Stage - {简述}"           （例：测试脚本 / 环境修复 / 回归补测）
├── Browser E2E Stage  : "F{编号}: Browser E2E Stage - {简述}"    （例：截图 / 测试报告）
└── Ship Stage         : 见 stages/ship-stage.md（Ship 有专属 commit 链）
```

### 设计动机

```
├── 给下一 Stage 提供稳定 diff 锚点（Review 看 Dev 的 diff、Ship 看完整历史）
├── 避免改动悬浮在工作区，防止 Compact 或会话崩溃丢失进度
├── 给 Ship Stage sanitize_log 留下可追溯的原子 commit 单元
└── auto_commit 数组 / 单值字段差异源于 QUALITY_ISSUE 循环语义：
    Review / Test 可多轮修复 → 数组；其他 Stage 单次产出 → 单值
```

### 免除场景（不触发 auto-commit 的例外）

```
├── Stage 报 BLOCKED / FAILED 返回：由 PMO 根据情况决定是否 commit
├── 纯讨论阶段（无文件产出）：git status --porcelain 自然为空，无需特殊处理
└── 用户明确要求"本次改动不 commit"：PMO 暂停并记录用户决策，不强制 auto-commit
```

### 各 Stage md 引用格式

各 Stage md 的「过程硬规则」章节只需保留一行引用：

```
- 🔴 **Stage 完成前 git 干净** → 遵循 [rules/gate-checks.md#stage-完成前-git-干净v739-硬规则p0-集中化](../rules/gate-checks.md#-stage-完成前-git-干净v739-硬规则p0-集中化)
```

不再在各 Stage md 中重复 6 行详细流程，避免文案多点漂移。
