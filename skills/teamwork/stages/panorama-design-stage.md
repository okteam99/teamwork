# Panorama Design Stage：全景重建模式（Feature Planning 专用）

> 🟢 **v7.3.4 定位调整**：本 Stage 仅用于 **Feature Planning 流程的全景重建模式**。
> Feature 流程的**全景增量同步**已合并到 [ui-design-stage.md](./ui-design-stage.md)（UI + 全景一次暂停）。
> 🔴 **全景是产品真相**：全景设计（sitemap.md + overview.html）是已确认的设计 + 业务逻辑真相。重建模式风险最高，必须基于用户明确授权。

---

## 本 Stage 职责

**仅在 Feature Planning 场景触发**：基于 PRD / PROJECT / 规划讨论结论，**从零重建** design/sitemap.md + design/preview/overview.html。

典型触发：
- Feature Planning 流程首次规划（design/ 目录不存在）
- Feature Planning 流程涉及**整个子项目**的页面结构重构（砍页面/重排导航/产品方向变更）
- 🌐 Workspace Planning 为新增子项目创建全景

**不包括**：
- Feature 流程的单个 Feature UI + 全景增量 → 去 ui-design-stage.md
- 仅新增一两个页面的小调整 → 去 ui-design-stage.md

---

## Input Contract

### 必读文件（按顺序）

```
├── {SKILL_ROOT}/agents/README.md
├── {SKILL_ROOT}/stages/panorama-design-stage.md（本文件）
├── {SKILL_ROOT}/roles/designer.md
├── {Feature Planning}/PRD.md 或 ROADMAP.md（规划讨论结论）
├── docs/PROJECT.md（产品总览）

重建时参考（存在则必读，作为"上一版真相"的对比基线）：
├── design/sitemap.md（现有，如有）
└── design/preview/overview.html（现有，如有）
```

### Key Context

- 历史决策锚点（产品方向调整 CHG 记录、规划讨论结论）
- 本轮聚焦点（重建目标：补全/转型/重构）
- 跨 Feature 约束
- 已识别风险（🔴 重建风险：可能丢失旧全景中的关键页面 / 破坏用户熟悉的导航结构）
- 降级授权
- 优先级

### 前置依赖

- **Feature Planning 流程中**（不是 Feature 流程）
- PM 已与用户讨论产品方向，规划结论已写入 PRD / ROADMAP
- 用户**已明确授权重建全景**（不是隐式决定）
- state.json.current_stage == "panorama_design"（仅 Planning 流程设置此状态）

---

## Process Contract

### 必做动作

1. **读取现有全景（如有）**
   - 作为"上一版产品真相"的对比基线
   - 列出所有现有页面和导航结构

2. **基于规划结论重建**
   - sitemap.md：新的页面地图（可能包含新增/保留/下线）
   - overview.html：新的全景交互原型

3. **对比差异清单（🔴 必须输出）**
   - 保留的页面：{列表}
   - 新增的页面：{列表}
   - 删除的页面：{列表 + 理由}
   - 重构的导航：{变更摘要}

4. **风险提示（🔴 强制）**
   - 删除的页面是否有用户历史流量？是否有现有 Feature 依赖？
   - 导航重构是否影响已发布产品的用户心智？
   - 有风险项 → DONE_WITH_CONCERNS，要求用户逐条确认

### 过程硬规则

- 🔴 **仅限 Feature Planning**：本 Stage 在 Feature 流程中不会被触发；PMO 若误调度必须拒绝并指向 ui-design-stage.md 的增量模式
- 🔴 **用户授权必达**：重建前必须有用户明确"确认重建"的对话记录（不能仅凭 PMO 判断"应该重建"）
- 🔴 **差异清单必出**：保留/新增/删除/重构四类变更分别列出
- 🔴 **删除页面需理由**：每个被删除的页面必须附理由（来源于规划讨论）
- 🔴 **两者必更**：sitemap.md + overview.html 必须一起更新，不允许只更一个

---

## Output Contract

### 必须产出的文件

| 文件路径 | 格式 | 必需内容 |
|---------|------|---------|
| `design/sitemap.md` | Markdown | 重建后的完整页面地图 + 变更记录段 |
| `design/preview/overview.html` | HTML | 重建后的全景交互原型 |
| `design/CHANGELOG.md`（或 sitemap.md 尾部） | Markdown | 🟡 本次重建的差异清单（保留/新增/删除/重构） |

### 机器可校验条件

- [ ] 两个文件都存在且已更新
- [ ] sitemap.md 包含「变更记录」段（本次重建的差异清单）
- [ ] overview.html 可在浏览器打开
- [ ] 无"⏭️ 跳过"字样（本 Stage 启动即意味着要重建）

### Done 判据

- 两个文件更新
- 差异清单完整
- 有风险项时已列出供用户确认
- `state.json.stage_contracts.panorama_design.output_satisfied = true`

### 返回状态

| 状态 | 条件 | 后续 |
|------|------|------|
| ✅ DONE | 重建完成 + 无风险项 | PMO ⏸️ 用户确认全景重建 |
| ⚠️ DONE_WITH_CONCERNS | 重建完成但有风险（如删除页面可能影响现有用户）| PMO ⏸️ 用户逐条决策 |
| 💥 FAILED | 无法重建（如现有全景损坏 + 无法从规划结论推导） | PMO 处理 |

---

## AI Plan 模式指引

📎 Execution Plan 4 行格式 → [SKILL.md](../SKILL.md#-ai-plan-模式规范v73-新增)。

本 Stage 默认 `subagent`（全景 HTML 产出量大；沿用 Designer Subagent，Opus）。

**Expected duration baseline（v7.3.4）**：30-50 min（全景重建 + 差异清单 + 风险分析）。重建风险最高，不推荐主对话执行。

---

## 执行报告模板

```
📋 Panorama Design Stage 执行报告（全景重建模式）
================================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / FAILED}
├── 执行方式：{主对话 / Subagent}
├── 触发场景：{Feature Planning / Workspace Planning / 首次创建全景}
└── 用户授权重建：✅ 已确认

## 🟡 差异清单（与上一版对比）
### 保留的页面（N）
- {页面1}, {页面2}, ...

### 新增的页面（M）
| 页面 | 用途 | 所在导航位置 |
|------|------|------------|

### 删除的页面（K）🔴 需用户逐条确认
| 页面 | 删除理由 | 规划讨论出处 | 用户确认 |
|------|---------|------------|---------|

### 重构的导航
| 变更摘要 | 理由 | 影响范围 |
|---------|------|---------|

## 🔴 风险提示
- {风险1：如"删除订单列表页可能影响用户习惯"}
- {风险2：如"导航重构影响 AUTH 子项目的登录跳转"}

## 产出文件
├── 📁 design/sitemap.md（🟡 已重建）
├── 📁 design/preview/overview.html（🟡 已重建）
└── 📁 design/CHANGELOG.md（本次重建差异记录）

## Output Contract 校验
├── 两者都更新：✅
├── 差异清单完整：✅
└── 风险项已列出：✅
```
