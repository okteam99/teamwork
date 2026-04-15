# UI Design Stage：当前 Feature UI 设计

> PMO 在用户确认 PRD 后（需要 UI 时）启动本 Stage。
> 🔴 只做当前 Feature 的 UI 设计，不动全景文件（sitemap.md / overview.html）。
> 全景设计同步在 Panorama Design Stage 独立执行。

---

## 一、设计意图

```
UI Design Stage = 单个 Feature 的 UI 设计
├── 产出 UI.md（设计规范文档）
├── 产出 preview/*.html（HTML 预览稿）
├── 产出验收标准覆盖声明
└── 🔴 不动 design/sitemap.md 和 design/preview/overview.html
```

---

## 二、输入文件

```
PMO 启动时必须注入：
├── agents/README.md                                ← 通用规范
├── stages/ui-design-stage.md                       ← 本文件
├── roles/designer.md                               ← Designer 角色规范
├── docs/features/F{编号}-{功能名}/PRD.md           ← 已确认的 PRD
├── templates/ui.md                                 ← UI 设计模板
│
🔴 全景基准（存在时必须注入，不是可选）：
├── design/sitemap.md                               ← 全景页面地图（Designer 必须参照风格/配色/布局）
├── design/preview/{相关页面}.html                   ← 全景中与本 Feature 同名的预览稿（如 onboarding.html）
│   └── PMO 根据 PRD 涉及的页面，从 design/preview/ 中筛选对应的全景 HTML 注入
│
可选文件：
├── docs/KNOWLEDGE.md                               ← 用户设计偏好
└── docs/PROJECT.md                                 ← 产品总览
```

---

## 三、执行流程

```
🔴 进度追踪：每个 Step 开始时报告进度（宿主支持 TodoWrite 时使用，否则输出 markdown 进度块），禁止黑盒执行。

Step 1: 读取所有规范文件 + PRD 验收标准

Step 2: 设计 UI
        ├── 按 PRD 需求设计页面/组件
        ├── 输出 UI.md（布局、颜色、字体、间距、交互状态）
        ├── 输出 preview/*.html（Tailwind CSS HTML 预览）
        │   ├── 每个页面/状态一个 HTML 文件
        │   └── 必须覆盖：正常态、空态、加载态、错误态
        └── 输出验收标准覆盖声明（PRD AC 逐条对照）

Step 3: 产出汇总
        └── 输出 UI Design Stage 执行报告
```

---

## 四、返回状态

```
├── ✅ DONE → PMO ⏸️ 用户确认设计稿
├── ⚠️ DONE_WITH_CONCERNS → 有非阻塞问题（PRD 描述不清等）
└── 💥 FAILED → 无法完成设计
```

---

## 五、红线

```
🔴 进度可见：每个 Step 必须报告进度（TodoWrite 或 markdown 进度块），禁止黑盒执行
🔴 必须对齐全景：有全景文件时，Feature UI 必须与全景的风格/配色/布局/语言保持一致
🔴 不动全景：禁止修改 design/sitemap.md 和 design/preview/overview.html
🔴 HTML 预览必出：每个页面必须有 HTML 预览稿（Tailwind CSS）
🔴 状态覆盖：每页必须覆盖正常/空/加载/错误状态
🔴 验收标准覆盖声明必出：逐条对照 PRD AC
```

---

## 六、输出格式

```
📋 UI Design Stage 执行报告（F{编号}-{功能名}）
================================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / FAILED}
├── 页面数：{N}
└── 预览文件：{列表}

## 验收标准覆盖声明
| AC | 覆盖状态 | 设计说明 |
|----|----------|----------|

## 产出文件
├── 📁 UI.md
├── 📁 preview/*.html
└── 📁 验收标准覆盖声明

## Concerns（如有）
```
