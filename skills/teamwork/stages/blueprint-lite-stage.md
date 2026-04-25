# BlueprintLite Stage：轻量蓝图（敏捷需求专用）

> 敏捷需求流程中，用户确认精简 PRD 后进入本 Stage。产出简化版 TC + 实现计划，为 Dev Stage 提供蓝图。
> 🔴 不做 TC 技术评审、不做架构师评审（敏捷砍掉的环节）。
> 🔴 契约优先：执行方式由 AI 在 Plan 模式自主规划（推荐主对话）。

---

## 本 Stage 职责

敏捷需求的轻量蓝图：保持"先规划后编码"，但砍掉 Feature 流程的重量级评审。QA 写简化 TC + RD 写实现计划。

---

## Input Contract

### 必读文件（按顺序）

```
├── {SKILL_ROOT}/stages/blueprint-lite-stage.md（本文件）
├── {SKILL_ROOT}/roles/qa.md（TC 编写规范）
├── {SKILL_ROOT}/roles/rd.md（实现计划规范）
├── {SKILL_ROOT}/templates/tc.md（精简版）
├── {SKILL_ROOT}/standards/common.md
└── {Feature}/PRD.md（已确认的精简 PRD）

可选：
├── docs/architecture/ARCHITECTURE.md
└── docs/KNOWLEDGE.md
```

### Key Context（逐项判断，无则 `-`）

- 历史决策锚点、本轮聚焦点、跨 Feature 约束、已识别风险、降级授权、优先级

### 前置依赖

- `{Feature}/PRD.md` 存在且确认（敏捷精简版）
- `state.json.current_stage == "blueprint_lite"`
- Feature 类型 = 敏捷需求（满足准入条件：≤5 文件 + 无 UI + 无架构变更）

---

## 入口 Read 顺序（v7.3.10+P0-23 固定）

🔴 按以下顺序 Read，字节一致利于 prompt cache 命中。详见 [standards/prompt-cache.md](../standards/prompt-cache.md)。

```
Step 1: roles/qa.md, roles/rd.md                       ← 角色层（L0 稳定）
Step 2: templates/tc.md                                ← 模板层（L0 稳定）
Step 3: {Feature}/PRD.md                               ← Feature 既有产物（L2）
Step 4: {Feature}/state.json                           ← 🔴 最后，动态入口（L3）
```

🔴 R3 约束：state.json 入口 Read 1 次 → 中段 0 读写 → 出口 Read 1 次 + Write 1 次；全 Stage ≤ 5 次。

---

## Process Contract

### 必做动作

1. **QA 编写简化版 TC**
   - 按 PRD 验收标准逐条写 BDD 用例
   - 只覆盖核心场景（正常流程 + 主要异常）
   - 不要求完整的边界/并发/性能场景
   - TC.md frontmatter 填 `tests[]`（与 Feature 流程相同结构）

2. **RD 编写实现计划**
   - 文件清单（新增/修改）
   - 改动要点（每个文件的核心变更）
   - 测试策略（单测 + 集成测覆盖点）

### 过程硬规则

- 🔴 **角色规范必读且 cite**：QA → `roles/qa.md`；RD → `roles/rd.md`
- 🔴 **不做评审**：BlueprintLite 不含 TC 技术评审和架构师评审（敏捷核心精简点）
- 🔴 **不替代 Blueprint**：Feature 流程仍走完整 Blueprint Stage
- 🔴 **TC 质量下限**：即使精简，每条 PRD AC 至少对应 1 条 BDD 用例（AC→test 覆盖仍强制）
- 🔴 **Dev Stage 不变**：BlueprintLite 产出后，Dev Stage 按标准流程执行
- 🔴 **Stage 完成前 git 干净** → 统一遵循 [rules/gate-checks.md § Stage 完成前 git 干净](../rules/gate-checks.md#-stage-完成前-git-干净v739-硬规则p0-集中化)（本 Stage commit message：`F{编号}: BlueprintLite Stage - {简述}`；典型产物：TC.md / IMPL-PLAN.md）

---

## Output Contract

### 必须产出的文件

| 文件路径 | 格式 | 必需字段 |
|---------|------|---------|
| `{Feature}/TC.md` | Markdown + YAML frontmatter | `feature_id`, `tests[]`（含 covers_ac） |
| `{Feature}/IMPL-PLAN.md`（或嵌入执行报告） | Markdown | 文件清单、改动要点、测试策略 |

### 机器可校验条件

- [ ] TC.md frontmatter 可 YAML 解析
- [ ] 每条 PRD AC 有对应测试（`covers_ac` 反查覆盖）
- [ ] TC 用例数 ≥ PRD AC 数
- [ ] 实现计划包含文件清单（至少 1 个文件）

### Done 判据

- 产出文件存在且通过格式校验
- AC↔test 覆盖校验通过
- `state.json.stage_contracts.blueprint_lite.output_satisfied = true`

### 返回状态

| 状态 | 条件 | 后续 |
|------|------|------|
| ✅ DONE | TC + 实现计划就绪 | 进入 Dev Stage |
| ⚠️ DONE_WITH_CONCERNS | PRD 有歧义但可继续 | PMO ⏸️ 用户确认 |
| 💥 FAILED | PRD 不够清晰无法产出蓝图 | PMO ⏸️ 用户补充 |

---

## AI Plan 模式指引

📎 Execution Plan 4 行格式（含 Estimated）→ [SKILL.md](../SKILL.md#-ai-plan-模式规范v73-新增)。

本 Stage 默认 `main-conversation`（敏捷流程精髓是快速闭环，Subagent 冷启动不划算）。仅当主对话 context 已紧张时切 `subagent`。

**Expected duration baseline（v7.3.3）**：8-15 min（主对话精简 TC + 实现计划）。

---

## 执行报告模板

```
📋 BlueprintLite 执行报告（{功能编号}-{功能名}）
================================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / FAILED}
├── 执行方式：{主对话 / Subagent}
├── TC：{N} 条 BDD，覆盖 AC {M}/{总 AC}
└── 标注：敏捷-精简（不含边界/并发/性能场景）

## TC 概况
├── 用例数：{N}
├── 覆盖 AC：{M}/{总 AC}
└── Covers_ac 反查：✅ 全覆盖

## 实现计划
| 文件 | 操作 | 改动要点 |
|------|------|----------|

## 测试策略
├── 单测：{覆盖点}
└── 集成测试：{覆盖点}

## Output Contract 校验
├── TC YAML：✅
├── AC 覆盖：✅
└── 文件清单：✅

## Concerns（如有）
```
