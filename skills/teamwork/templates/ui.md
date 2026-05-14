# UI 模板（v7.3.10+P0-140 瘦身 · 视觉真相归 HTML · 本文件只承载意图 / 追溯 / 审计）

> 🔴 **职责单源（v7.3.10+P0-140）**：
> - **视觉真相** = `preview/*.html`（布局 / 组件 / 主色 / 字号 / 间距 / 响应式 / 4 态 / 用户流程交互）
> - **意图 + 追溯 + 审计** = 本 UI.md（panorama 对齐 / AC 覆盖 / Designer 自查 / 变更记录）
>
> 🟢 旧模板的"布局 / 组件表 / 设计标注 / 响应式断点 / 状态设计描述 / 用户流程文字描述"段已删除——这些 HTML 是真相，markdown 复述会 drift。

```markdown
# {功能名称} - UI 设计意图 & 追溯

> 🔴 全景宿主：{当前子项目 / 跨子项目→{hosting_subproject}}（v7.3.10+P0-123 跨子项目契约 · cite ui-design-stage Step 0 探测结果）
> 🔴 panorama_path: {绝对路径 / null（项目无全景）}

## 状态
草稿 | 待评审 | 已确认

## 预览稿索引（🔴 HTML 是视觉真相 · 本表只索引）

| 页面 | 文件 | 状态 |
|------|------|------|
| {页面1} | [preview/page1.html](./preview/page1.html) | 正常态 |
| {页面1} | [preview/page1-loading.html](./preview/page1-loading.html) | 加载态 |
| {页面1} | [preview/page1-empty.html](./preview/page1-empty.html) | 空态 |
| {页面1} | [preview/page1-error.html](./preview/page1-error.html) | 错误态 |

> 📎 视觉描述（布局 / 组件 / 配色 / 字号 / 间距 / 响应式 / 用户流程交互）一律以 HTML 为准。
> 📎 评审 / 验收 / 实现的视觉对照基准 = HTML，不是本文件。

## UI-AC-COVERAGE（PRD AC 覆盖声明 · 必填）

> 🔴 HTML 区块可加 `data-ac="AC-01"` 锚定便于 grep · 本表是人类阅读的总览。

| AC.id | 描述摘要 | 对应页面 / HTML 区块 | 覆盖状态 |
|-------|---------|---------------------|---------|
| AC-01 | ... | preview/page1.html `#section-x` | ✅ / ⚠️ 需 RD 实现 / ❌ 缺 |

## 变更记录
| 日期 | 变更 | 影响的 HTML 文件 |
|------|------|----------------|

---

## Designer 自查报告（🔴 出口必填 · v7.3.10+P0-132 物化 · verify-panorama.py 校验）

> 详细规范 cite [standards/common.md § 四B Designer 自查规范](../standards/common.md)。Designer 完成设计后必填本段 · 5 维度全 ✅ 才进 ⏸️ 用户确认。

### 检查结果汇总
| 维度 | 检查项 | 通过 | 备注 |
|------|------|----|----|
| 1. 全景对齐 | 4 | ?/4 | panorama_path = ... · 宿主 = ... |
| 2. 状态覆盖 | 4×N页 | ?/? | N 个页面 · 每页 4 态（HTML 文件存在性） |
| 3. PRD AC 覆盖 | M | ?/M | 详 UI-AC-COVERAGE 表 |
| 4. 全景增量同步 | 4 | ?/4 | 类型：⏭️ 无 / 🟡 增量 / 🔴 结构性 |
| 5. 结构性变更红线 | 3 | ?/3 | 任一命中即停 Stage |

### 全景对齐证据
- panorama_path: {绝对路径}
- 全景宿主：{当前子项目 / 跨子项目→{hosting_subproject}}
- 风格对照（read panorama/sitemap.md 后摘录 ≥3 条规范 + 本 Feature 遵守说明）：
  1. ...
  2. ...
  3. ...
- 导航位置：{本 Feature 页面在 sitemap 中的层级路径}
- 全景变更类型：⏭️ 无 / 🟡 增量 / 🔴 结构性

#### 🔴 HTML 物化对齐校验（v7.3.10+P0-147 必填 · 治本"自查写 ✅ 但 HTML 实际漂移"）

```bash
python3 {SKILL_ROOT}/tools/diff-html-vs-panorama.py \
  --panorama {panorama_path}/preview/overview.html \
  --feature-dir {Feature_dir}/preview
```

- verdict: ☐ OK / ☐ WARN / ☐ FAIL
- 命中 extra colors（如有 · 列 token 名 + 修复路径）：
- 命中 extra font sizes（如有）：
- 命中 extra layouts（如有）：
- 缺 required landmarks（如有 · main 等）：
- 工具 stdout JSON 入 state.json.ui_substeps_config.html_diff_evidence

### 全景增量 diff（仅 🟡 增量类型必填）
\`\`\`diff
sitemap.md 变更：
+ 新增页面 X（位置：根 → A → X）
~ 修改页面 Y（导航文案：旧→新）

overview.html DOM 变更：
+ 新增 <section data-page="X">
~ 修改 <nav> 中页面 Y 链接文案
\`\`\`

### 自查结论
✅ 自查通过 · 可进入 ⏸️ 用户确认设计稿
```

## HTML 预览稿模板（🔴 视觉真相的唯一载体）

> Feature 每页面每状态独立一个 HTML 文件（覆盖 4 态：正常 / 加载 / 空 / 错误）。
> AC 追溯：HTML 区块加 `data-ac="AC-XX"` 锚定，便于 grep + 与 UI-AC-COVERAGE 表对账。

```html
<!-- docs/features/F{编号}-{功能名}/preview/页面名.html -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>UI-XXX 预览</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
  <!-- 视觉真相在此 · 布局 / 组件 / 配色 / 字号 / 间距 / 响应式 / 交互 / 状态全在 HTML -->
  <!-- AC 锚定示例：<section data-ac="AC-01">...</section> -->
</body>
</html>
```
