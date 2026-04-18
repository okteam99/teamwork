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
