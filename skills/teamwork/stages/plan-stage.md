# Plan Stage：需求定义（PM 写 PRD + PL-PM 讨论 + 多角色技术评审）

> 在用户确认流程类型后进入本 Stage。产出一份经过产品对齐 + 技术评审的合格 PRD。
> 🔴 契约优先：本文件规范 Input / Process / Output 三契约。执行方式由 AI 在 Plan 模式自主规划（见 SKILL.md「AI Plan 模式规范」）。

---

## 本 Stage 职责

产出经过产品方向对齐 + 多视角技术评审的定稿 PRD，为后续 Stage 锁定需求边界。PRD 中的 AC 必须结构化以便与测试强绑定。

---

## Input Contract

### 必读文件（按顺序）

```
├── {SKILL_ROOT}/agents/README.md                    ← 通用规范
├── {SKILL_ROOT}/stages/plan-stage.md                ← 本文件
├── {SKILL_ROOT}/roles/pm.md                         ← PM 角色 + PRD 技术评审规范
├── {SKILL_ROOT}/roles/product-lead.md               ← PL 角色（讨论用）
├── {SKILL_ROOT}/templates/prd.md                    ← PRD 模板（含 AC 结构化 frontmatter）
└── {SKILL_ROOT}/standards/common.md                 ← 通用开发规范

可选（存在则读取）：
├── docs/PROJECT.md                                  ← 产品总览
├── docs/KNOWLEDGE.md                                ← 项目知识库
├── docs/architecture/ARCHITECTURE.md                ← 架构文档（技术评审参考）
└── design/sitemap.md                                ← 全景设计（有 UI 时参考）
```

### Key Context（PMO 必须逐项判断，无则写 `-`）

- 历史决策锚点：上游 Stage / CHG 记录 / Plan Stage 纪要中的决策
- 本轮聚焦点：重派或修订场景必填
- 跨 Feature 约束：与其他进行中 Feature 的冲突/兼容
- 已识别风险：来自 KNOWLEDGE.md / 预检 / 历史 Bug
- 降级授权：PL 不可用时是否可由 PM 单独推进等
- 优先级 / 容忍度：进度优先 / 质量优先 / 平衡

### 前置依赖

- PMO 初步分析已输出且用户已确认流程类型
- state.json.current_stage == "plan"
- 无其他阻塞项（blocking.pending_user_confirmations 为空）

---

## Process Contract

### 必做动作

1. **PM 起草 PRD 初稿**（按 `roles/pm.md` + `templates/prd.md`）
   - 必须包含「交付预期」section（用户视角的变化 + 验证方式）
   - AC 结构化（按 templates/prd.md 的 YAML frontmatter）
   - 不允许 TBD / 待补充

2. **PL-PM 讨论**（产品方向对齐）
   - 最多 3 轮讨论
   - 达成共识 → PM 按共识更新 PRD
   - 有分歧 → 记录分歧项，标记为待用户决策

3. **多视角技术评审**（RD / Designer / QA / PMO）
   - 按 `roles/pm.md`「PRD 技术评审规范」执行
   - 产出 PRD-REVIEW.md
   - 汇总问题 + 建议

4. **PRD 定稿**
   - PM 按评审结论更新 PRD
   - 标记状态为「待用户确认」

### 过程硬规则

- 🔴 **角色规范必读且 cite**：切换到每个视角（PM/PL/RD/Designer/QA/PMO）前，必须先 Read 对应 `roles/{id}.md`，并在产出前 cite 该角色的关键要点（"📖 本视角遵循：roles/pm.md §Y 的 X 项约束"）
- 🔴 **PL-PM 讨论独立性**：PL 和 PM 各自表达观点，不能一方主导
- 🔴 **技术评审完整性**：必须覆盖 RD / Designer（如有 UI）/ QA / PMO 四个视角
- 🔴 **PRD 质量下限**：不能留 TBD / 待补充；验收标准必须量化可验证
- 🔴 **讨论轮次控制**：PL-PM 最多 3 轮，超出则记录分歧返回
- 🔴 **AC 结构化**：每条 AC 必须有 id / description / priority 字段（test_refs 在 Blueprint Stage 填入）

### 多视角独立性要求

- PL 和 PM 的讨论纪要必须分开记录（`discuss/PL-FEEDBACK-R{N}.md` 和 `PM-RESPONSE-R{N}.md`）
- 多视角技术评审的每个视角独立输出评审意见（不互相引用）

---

## Output Contract

### 必须产出的文件

| 文件路径 | 格式 | 必需字段 |
|---------|------|---------|
| `{Feature}/PRD.md` | Markdown + YAML frontmatter | `feature_id`, `acceptance_criteria[]` (id, description, priority), 交付预期, 影响范围 |
| `{Feature}/PRD-REVIEW.md` | Markdown | 4 个视角的评审意见（RD/Designer/QA/PMO）+ 汇总问题清单 |
| `{Feature}/discuss/PL-FEEDBACK-R{N}.md` | Markdown | PL 视角反馈（每轮一个文件） |
| `{Feature}/discuss/PM-RESPONSE-R{N}.md` | Markdown | PM 对 PL 反馈的回应 |

### 机器可校验条件

- [ ] PRD.md frontmatter 可 YAML 解析（`yq '.feature_id' PRD.md` 成功）
- [ ] `acceptance_criteria[]` 至少 1 条，每条有 id/description/priority
- [ ] 无 TBD / 待补充 / TODO（`grep -iE "TBD|待补充|TODO" PRD.md` 为空）
- [ ] 多视角评审 4 个视角都有意见（或显式标注"无意见"+ 理由）

### Done 判据

- 所有产出文件存在且通过格式校验
- PL-PM 讨论已达成共识或记录分歧
- 多视角评审已完成且无 🔴 阻塞问题
- `state.json.stage_contracts.plan.output_satisfied = true`

### 返回状态

| 状态 | 条件 | 后续 |
|------|------|------|
| ✅ DONE | 产出完整 + 评审通过 + 无分歧 | PMO ⏸️ 用户确认 PRD |
| ⚠️ DONE_WITH_CONCERNS | PRD 定稿但有 PL-PM 分歧 / 评审建议 | PMO ⏸️ 用户逐项决策 |
| 💥 FAILED | 需求不清晰无法产出 | 返回错误 + 部分产出 |

---

## AI Plan 模式指引

📎 Execution Plan 4 行格式（含 Estimated）→ [SKILL.md「AI Plan 模式规范」](../SKILL.md#-ai-plan-模式规范v73-新增)。默认 approach → [agents/README.md §一](../agents/README.md#一执行方式参考默认推荐--判断原则)。

本 Stage 默认 `main-conversation`（多视角 prompt 切换 + 用户讨论）。典型偏离：需求极清晰、无用户介入 → `subagent`。

**Expected duration baseline（v7.3.3）**：20-40 min（主对话 / 含 PL-PM 讨论）；需求清晰走 Subagent 一次闭环可降至 15-20 min。AI 在 Execution Plan 的 `Estimated` 字段按本 Feature 规模（预期 AC 数、讨论复杂度）校准。

---

## 执行报告模板（Output Contract 的输出呈现）

```
📋 Plan Stage 执行报告（F{编号}-{功能名}）
================================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / FAILED}
├── 执行方式：{主对话 / Subagent / 混合}（来自 Execution Plan）
├── PL-PM 讨论：{R1 收敛 / R2 收敛 / 有分歧}
├── 技术评审：{通过 / 有建议已纳入 / 有问题}
└── PRD 验收标准数：{N} 条（AC 结构化已校验）

## PL-PM 讨论纪要
├── 讨论轮次：{1-3}
├── 共识项：{N} 条
├── 分歧项：{M} 条（待用户决策）
└── PRD 修改：{已纳入的修改摘要}

## 技术评审报告
{按 PRD-REVIEW.md 格式}

## 产出文件
├── 📁 PRD.md（定稿，AC 结构化）
├── 📁 PRD-REVIEW.md（评审记录）
└── 📁 discuss/PL-FEEDBACK-R{N}.md + PM-RESPONSE-R{N}.md

## Output Contract 校验
├── YAML frontmatter：✅ 可解析
├── AC 数量：{N}（≥1）
├── 无 TBD/TODO：✅
└── 4 视角评审：✅ 全覆盖
```
