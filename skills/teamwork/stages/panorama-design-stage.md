# Panorama Stage：全景设计同步更新

> PMO 在用户确认 Feature UI 设计后，判断是否涉及全景更新（新增页面/修改结构/变更导航）。
> 涉及 → dispatch 本 Stage；不涉及 → 显式输出「⏭️ 全景无需更新」跳过。
> 🔴 目标：同步更新 design/sitemap.md + design/preview/overview.html，保持全景设计与最新 Feature 一致。

---

## 一、触发条件

```
PMO 在 UI Design Stage 用户确认后判断：
├── 涉及全景更新（新增页面/修改页面结构/变更导航关系）→ dispatch 本 Stage
├── 不涉及（纯样式/交互调整，不影响页面结构）→ 跳过
└── Feature Planning 流程的全景重建模式 → 使用本 Stage（全量重建模式）
```

---

## 二、输入文件

```
├── agents/README.md
├── stages/panorama-stage.md（本文件）
├── roles/designer.md
├── 本次 Feature 的 UI.md + preview/*.html（UI Design Stage 产出）
├── 现有 design/sitemap.md（如存在）
├── 现有 design/preview/overview.html（如存在）
└── PRD.md 验收标准（确认页面范围）
```

---

## 三、执行模式

```
增量模式（Feature 流程，默认）：
├── 读取现有 sitemap.md + overview.html
├── 将本次 Feature 的页面合并进全景
│   ├── sitemap.md：新增页面 → 更新页面清单 + 导航图；修改页面 → 更新状态/描述
│   └── overview.html：将本次 Feature 的页面合并进全景原型，高亮标注变更
└── 产出更新后的 sitemap.md + overview.html

全景重建模式（Feature Planning 流程）：
├── 从零重建 sitemap.md + overview.html
├── 基于 PRD/PROJECT.md 的产品全景设计
└── 产出全新的 sitemap.md + overview.html
```

---

## 四、返回状态

```
├── ✅ DONE → 全景已更新，PMO → ⏸️ 用户确认全景
└── 💥 FAILED → 无法更新（缺少现有全景文件等）→ PMO 处理
```

---

## 五、红线

```
🔴 design/ 是产品 UI 的 Single Source of Truth，不可跳过更新
🔴 每次更新必须输出 sitemap.md + overview.html，两者都更新
```
