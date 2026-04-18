# UI Design Stage：当前 Feature UI 设计

> 用户确认 PRD 后（需要 UI 时）进入本 Stage。
> 🔴 只做当前 Feature 的 UI 设计，不动全景文件（sitemap.md / overview.html）—— 全景同步在 Panorama Design Stage。
> 🔴 契约优先：执行方式由 AI 自主规划（HTML 产出量大，默认推荐 Subagent）。

---

## 本 Stage 职责

产出 UI 设计规范 + HTML 预览稿，覆盖所有页面状态（正常/空/加载/错误）。

---

## Input Contract

### 必读文件（按顺序）

```
├── {SKILL_ROOT}/agents/README.md
├── {SKILL_ROOT}/stages/ui-design-stage.md（本文件）
├── {SKILL_ROOT}/roles/designer.md                 ← Designer 角色规范
├── {SKILL_ROOT}/templates/ui.md                   ← UI 设计模板
└── {Feature}/PRD.md（已确认）

🔴 全景基准（存在时必读，不是可选）：
├── design/sitemap.md                              ← 全景页面地图（风格/配色/布局基准）
└── design/preview/{相关页面}.html                  ← 全景中与本 Feature 相关的预览稿

可选：
├── docs/KNOWLEDGE.md                              ← 用户设计偏好
└── docs/PROJECT.md                                ← 产品总览
```

### Key Context（逐项判断，无则 `-`）

- 历史决策锚点（既定设计语言、配色规范、组件库）
- 本轮聚焦点（重派/修订场景必填）
- 跨 Feature 约束（与并行 UI Feature 的一致性）
- 已识别风险
- 降级授权
- 优先级 / 容忍度

### 前置依赖

- `{Feature}/PRD.md` 存在且确认
- state.json.current_stage == "ui_design"

---

## Process Contract

### 必做动作

1. **按 PRD 需求设计页面 / 组件**
   - 布局、颜色、字体、间距、交互状态
   - 如有全景基准，必须对齐风格/配色/布局/语言

2. **产出 UI.md**（设计规范文档）

3. **产出 HTML 预览稿**
   - Tailwind CSS
   - 每个页面 / 状态一个 HTML 文件
   - 必须覆盖：正常态、空态、加载态、错误态

4. **产出验收标准覆盖声明**
   - 对照 PRD 的 AC 逐条声明"UI 是否支撑该 AC"

### 过程硬规则

- 🔴 **角色规范必读且 cite**：必读 `roles/designer.md`，产出前 cite 要点
- 🔴 **必须对齐全景**：有全景文件时，Feature UI 必须与全景风格/配色/布局/语言一致
- 🔴 **不动全景**：禁止修改 `design/sitemap.md` 和 `design/preview/overview.html`
- 🔴 **HTML 预览必出**：每个页面必须有 HTML 预览稿（Tailwind CSS）
- 🔴 **状态覆盖**：每页必须覆盖正常 / 空 / 加载 / 错误
- 🔴 **验收标准覆盖声明必出**：逐条对照 PRD AC

---

## Output Contract

### 必须产出的文件

| 文件路径 | 格式 | 必需内容 |
|---------|------|---------|
| `{Feature}/UI.md` | Markdown | 布局 / 颜色 / 字体 / 间距 / 交互状态 / 与全景基准的对齐说明 |
| `{Feature}/preview/*.html` | HTML + Tailwind | 每页面每状态一个文件 |
| `{Feature}/UI-AC-COVERAGE.md`（或 UI.md 尾部）| Markdown 表 | 逐条 PRD AC 对应的 UI 支撑 |

### 机器可校验条件

- [ ] UI.md 存在
- [ ] `preview/` 目录下至少一个 HTML 文件
- [ ] HTML 引用 Tailwind CDN 或构建后的 CSS
- [ ] 每个页面覆盖 4 种状态（可通过 HTML 文件命名或 UI.md 声明校验）
- [ ] AC 覆盖声明覆盖 PRD 所有 AC

### Done 判据

- 所有产出文件存在
- PRD AC 全部有 UI 支撑声明
- `state.json.stage_contracts.ui_design.output_satisfied = true`

### 返回状态

| 状态 | 条件 | 后续 |
|------|------|------|
| ✅ DONE | 设计完成 + AC 全覆盖 | PMO ⏸️ 用户确认设计稿 |
| ⚠️ DONE_WITH_CONCERNS | PRD 描述不清等非阻塞问题 | PMO ⏸️ 用户确认 |
| 💥 FAILED | 无法完成设计 | 返回错误 + 部分产出 |

---

## AI Plan 模式指引（非强制）

典型方案：

- **方案 A（推荐）**：Subagent 一次性产出
  - 适合：HTML 产出量大（多页面 × 多状态），主对话 context 会被挤占
  - 按 [Dispatch 文件协议](../agents/README.md#四dispatch-文件协议) 生成 dispatch 文件
  - 推荐模型：Opus（设计审美 + HTML 质量）

- **方案 B**：主对话执行
  - 适合：小改动（只改一个页面、一两个状态）
  - 用户需要边讨论边调整

🔴 AI 开始本 Stage 前必须输出 Execution Plan 块。

---

## 执行报告模板

```
📋 UI Design Stage 执行报告（F{编号}-{功能名}）
================================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / FAILED}
├── 执行方式：{主对话 / Subagent}
├── 页面数：{N}
└── 预览文件数：{M}

## 验收标准覆盖声明
| AC | 覆盖状态 | 设计说明 |
|----|----------|----------|

## 产出文件
├── 📁 UI.md
├── 📁 preview/*.html（{M} 个）
└── 📁 UI-AC-COVERAGE.md

## Output Contract 校验
├── UI.md 存在：✅
├── preview/ 非空：✅
├── 状态覆盖完整：✅
└── AC 全覆盖：✅

## Concerns（如有）
```
