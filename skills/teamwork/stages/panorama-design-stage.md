# Panorama Design Stage：全景设计同步更新

> 用户确认 Feature UI 后，PMO 判断是否涉及全景更新。涉及 → 进入本 Stage；不涉及 → 跳过。
> 🔴 目标：同步更新 `design/sitemap.md` + `design/preview/overview.html`，保持全景与最新 Feature 一致。
> 🔴 契约优先：执行方式由 AI 自主规划（默认推荐 Subagent）。

---

## 本 Stage 职责

- **增量模式**（Feature 流程）：将本次 Feature 的页面合并进全景
- **全景重建模式**（Feature Planning 流程）：基于 PRD/PROJECT 重建 sitemap + overview

---

## Input Contract

### 必读文件（按顺序）

```
├── {SKILL_ROOT}/agents/README.md
├── {SKILL_ROOT}/stages/panorama-design-stage.md（本文件）
├── {SKILL_ROOT}/roles/designer.md
├── {Feature}/UI.md + preview/*.html                 ← UI Design Stage 产出
├── {Feature}/PRD.md（验收标准 / 页面范围）

现有全景（存在则必读）：
├── design/sitemap.md
└── design/preview/overview.html
```

### Key Context

- 历史决策锚点（既定页面导航模式）
- 本轮聚焦点
- 跨 Feature 约束
- 已识别风险
- 降级授权
- 优先级

### 前置依赖

- UI Design Stage 已完成，Feature UI 已确认
- PMO 已判断本次涉及全景更新（或 Feature Planning 全景重建）
- state.json.current_stage == "panorama_design"

### 触发条件

```
Feature 流程触发：
├── 新增页面 / 修改页面结构 / 变更导航关系 → 增量合并
└── 纯样式/交互调整（不影响页面结构）→ 跳过，不进入本 Stage

Feature Planning 流程触发：
└── Planning 涉及页面结构变更 → 全景重建模式
```

---

## Process Contract

### 必做动作

**增量模式（Feature 流程默认）**：
1. 读取现有 sitemap.md + overview.html
2. 将本次 Feature 页面合并进全景
   - sitemap.md：新增页面 → 更新清单 + 导航图；修改页面 → 更新状态/描述
   - overview.html：将本次 Feature 的页面合并进全景原型，高亮标注变更
3. 产出更新后的 sitemap.md + overview.html

**全景重建模式（Feature Planning 流程）**：
1. 基于 PRD / PROJECT.md / 规划讨论结论从零重建
2. 产出全新 sitemap.md + overview.html

### 过程硬规则

- 🔴 **角色规范必读且 cite**：必读 `roles/designer.md`，产出前 cite 要点
- 🔴 **design/ 是产品 UI 的 SSoT**：不可跳过更新
- 🔴 **两者必更**：每次必须输出 sitemap.md + overview.html，两者都更新

---

## Output Contract

### 必须产出的文件

| 文件路径 | 格式 | 必需内容 |
|---------|------|---------|
| `design/sitemap.md` | Markdown | 页面清单 + 导航图 + 本次变更标注 |
| `design/preview/overview.html` | HTML | 全景原型（含本次 Feature 页面，变更高亮）|

### 机器可校验条件

- [ ] 两个文件都存在且已更新（modified time 晚于 Stage 开始时间）
- [ ] sitemap.md 包含本次 Feature 涉及的页面
- [ ] overview.html 可在浏览器打开

### Done 判据

- 两个文件都更新且通过格式校验
- `state.json.stage_contracts.panorama_design.output_satisfied = true`

### 返回状态

| 状态 | 条件 | 后续 |
|------|------|------|
| ✅ DONE | 全景已更新 | PMO ⏸️ 用户确认全景 |
| 💥 FAILED | 无法更新（缺少现有全景等）| PMO 处理 |

---

## AI Plan 模式指引（非强制）

- **方案 A（推荐）**：Subagent 执行
  - 全景 HTML 产出量大，Subagent 隔离主对话
  - 默认沿用 Designer Subagent（Opus）

- **方案 B**：主对话执行
  - 适合：仅增量合并一两个页面、主对话有用户介入需要

🔴 AI 开始本 Stage 前必须输出 Execution Plan 块。

---

## 执行报告模板

```
📋 Panorama Design Stage 执行报告（F{编号}-{功能名}）
==================================================

## 执行概况
├── 最终状态：{DONE / FAILED}
├── 执行方式：{主对话 / Subagent}
├── 模式：{增量 / 全景重建}
└── 变更页面数：{N}

## 产出文件
├── 📁 design/sitemap.md（已更新）
└── 📁 design/preview/overview.html（已更新）

## Output Contract 校验
├── 两者都更新：✅
├── sitemap 含本 Feature 页面：✅
└── overview.html 可打开：✅
```
