# UI 模板

```markdown
# {功能名称} - UI 设计

> 🔴 全景宿主：{当前子项目 / 跨子项目→{hosting_subproject}}（v7.3.10+P0-123 跨子项目契约 · cite ui-design-stage Step 0 探测结果）
> 🔴 panorama_path: {绝对路径 / null（项目无全景）}

## 状态
草稿 | 待评审 | 已确认

## 预览稿
- [页面1](./preview/page1.html)
- [页面2](./preview/page2.html)

## 用户流程

## 页面结构

### [页面名]

**布局**

**组件**
| 组件 | 类型 | 交互 |
|------|------|------|

**设计标注**
- 主色:
- 字号:
- 间距:

## 响应式
| 断点 | 适配 |
|------|------|

## 状态设计
- 加载态
- 空态
- 错误态

## UI-AC-COVERAGE（PRD AC 覆盖声明 · 必填）
| AC.id | 描述摘要 | 对应页面/组件 | 覆盖状态 |
|-------|---------|--------------|---------|
| AC-01 | ... | ... | ✅ / ⚠️ 需 RD 实现 / ❌ 缺 |

## 变更记录
| 日期 | 变更 |
|------|------|

---

## Designer 自查报告（🔴 出口必填 · v7.3.10+P0-132 物化 · verify-panorama.py 校验）

> 详细规范 cite [standards/common.md § 四B Designer 自查规范](../standards/common.md)。Designer 完成设计后必填本段 · 5 维度全 ✅ 才进 ⏸️ 用户确认。

### 检查结果汇总
| 维度 | 检查项 | 通过 | 备注 |
|------|------|----|----|
| 1. 全景对齐 | 4 | ?/4 | panorama_path = ... · 宿主 = ... |
| 2. 状态覆盖 | 4×N页 | ?/? | N 个页面 · 每页 4 态 |
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

### 全景增量 diff（仅 🟡 增量类型必填）
```diff
sitemap.md 变更：
+ 新增页面 X（位置：根 → A → X）
~ 修改页面 Y（导航文案：旧→新）

overview.html DOM 变更：
+ 新增 <section data-page="X">
~ 修改 <nav> 中页面 Y 链接文案
```

### 自查结论
✅ 自查通过 · 可进入 ⏸️ 用户确认设计稿
```

## HTML 预览稿模板

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
  <!-- 完整的页面预览，包含所有状态 -->
</body>
</html>
```
