# UI 模板（真相归 HTML · 本文件只承载意图 / 追溯 / 审计）

> 🔴 **职责单源**：
> - **视觉真相** = 预览产物（布局 / 组件 / 主色 / 字号 / 间距 / 响应式 / 4 态 / 用户流程交互）· 按 `panorama_medium`：`static-html` → `preview/*.html`；**`same-stack`（v8.58 option B）→ `preview-project/` 源**（跑 `preview.sh` 看实时 dev server · 不出静态 build）
> - **意图 + 追溯 + 审计** = 本 UI.md（panorama 对齐 / AC 覆盖 / Designer 自查 / 变更记录）
>
> 🟢 旧模板的"布局 / 组件表 / 设计标注 / 响应式断点 / 状态设计描述 / 用户流程文字描述"段已删除——这些预览产物是真相，markdown 复述会 drift。
>
> 🔵 **介质分流**（本模板含两套指引 · 按 `panorama_medium` 取用）：**`same-stack`** → 搭 `preview-project/` + 拷 `preview.sh`（见 `templates/preview-project-preview.sh`）· **下方「§全景权威索引」「§HTML 预览稿模板」是 static-html 专用 · same-stack 跳过**；**`static-html`** → 填「§全景权威索引」+ 写「§HTML 预览稿模板」。

```markdown
---
pages:
  - {id: page1, title: "页面 1"}
panorama_medium: same-stack  # same-stack(推荐 · v8.58 option B:{子项目}/docs/design/preview-project 同栈独立项目 · 源即全景权威 · preview.sh 实时预览 · 不出静态 build)| static-html(兜底 · 手写 CDN HTML)· 详 stages/ui-design-stage.md § Panorama 介质类型
panorama_path: {绝对路径 / null（项目无全景）}  # 全景权威根(workspace 级 panorama 单源)
# v8.17 新模式 · 全景为唯一权威(推荐 · 治本 PTR-F052 双副本不一致 / PTR-F054 介质绕路):
# pages_changed[] 有 → Feature 不存 preview/ 副本 · panorama_file 是唯一权威 · 直接改全景文件
pages_changed:
  - page_id: page1                                          # 必 · 对应 pages[].id
    route_path: /page1                                      # same-stack 必 · 真实 app 目标路由(预览直达 URL = PREVIEW_URL+route_path · 与 sitemap 一致 · / 留给首页设计稿)
    panorama_file: {panorama_path}/preview/page1.html       # static-html 必 / same-stack 可选(渲染该页的源/路由)
    change_range: "本 Feature 改动描述(如:Tabs 与 Table 之间新增 filter 区)"
    acceptance_criteria_refs: [AC-01, AC-03]                # 可选 · 关联 PRD AC
---
# {功能名称} - UI 设计意图 & 追溯

> 🔴 全景宿主：{当前子项目 / 跨子项目→{hosting_subproject}}
> 🔴 panorama_path: {绝对路径 / null（项目无全景）} · 全景权威根
> 🔴 panorama_medium: same-stack(推荐 · v8.58 option B:`{子项目}/docs/design/preview-project` 同栈独立项目 · 源即全景权威 · 真实组件渲染 · 不污染真实工程 · 解新库引入鸡蛋问题 · 验证渲染:拷 `{SKILL_ROOT}/templates/preview-project-preview.sh` 进 preview-project 根 · 后台跑 `bash preview.sh` 读 `PREVIEW_URL=` browse〔dev server · 动态端口 · 不在 teamwork 层起 server〕)| static-html(兜底 · 手写 CDN · 仅作 IA / 视觉层级 / Token 一致性参考 · 介质差异不可像素级仿 live)
> 🟢 **v8.17 全景为唯一权威**:本 Feature 不存 preview/*.html 副本 · 直接编辑 panorama_path/preview/<page>.html(权威) · pages_changed[] 声明本 Feature 改了哪几个 page + 链到权威文件。详 [stages/ui-design-stage.md § 全景为唯一权威](../stages/ui-design-stage.md)。

## 状态
草稿 | 待评审 | 已确认

## 全景权威索引(🔵 **static-html 介质专用** · same-stack 跳过〔权威 = preview-project 源〕· 🔴 v8.17 · 不存 Feature 副本 · 直链全景权威路径)

| 页面 | 全景权威文件 | 状态 |
|------|------|------|
| {页面1} | `{panorama_path}/preview/page1.html` | 正常态 |
| {页面1} | `{panorama_path}/preview/page1-loading.html` | 加载态 |
| {页面1} | `{panorama_path}/preview/page1-empty.html` | 空态 |
| {页面1} | `{panorama_path}/preview/page1-error.html` | 错误态 |

> 📎 视觉描述（布局 / 组件 / 配色 / 字号 / 间距 / 响应式 / 用户流程交互）一律以 HTML 为准 · **HTML 在 panorama_path/preview/ 下 · 不在 Feature 内**。
> 📎 评审 / 验收 / 实现的视觉对照基准 = panorama_path 下 HTML · Feature/UI.md 仅是「改动声明 + 局部决策记录」。
> 🟢 老模式(无 `pages_changed[]` frontmatter)兼容:Feature 内 `preview/*.html` 仍 PASS · 但**新 Feature 推荐用新模式**(避免双副本不一致 · 治本 PTR-F052)。

## UI-AC-COVERAGE（PRD AC 覆盖声明 · 必填）

> 🔴 HTML 区块可加 `data-ac="AC-01"` 锚定便于 grep · 本表是人类阅读的总览。

| AC.id | 描述摘要 | 对应页面 / HTML 区块 | 覆盖状态 |
|-------|---------|---------------------|---------|
| AC-01 | ... | preview/page1.html `#section-x` | ✅ / ⚠️ 需 RD 实现 / ❌ 缺 |

## 变更记录
| 日期 | 变更 | 影响的 HTML 文件 |
|------|------|----------------|

---

## Designer 自查报告（🔴 出口必填 物化 · verify-panorama.py 校验）

> 详细规范 cite [standards/common.md § 四B Designer 自查规范](../standards/common.md)。Designer 完成设计后必填本段 · 5 维度全 ✅ 才进 ⏸️ 用户确认。

### 检查结果汇总
| 维度 | 检查项 | 通过 | 备注 |
|------|------|----|----|
| 1. 全景对齐 | 4 | ?/4 | panorama_path = ... · 宿主 = ... |
| 2. 状态覆盖 | 4×N页 | ?/? | N 个页面 · 每页 4 态（HTML 文件存在性） |
| 3. PRD AC 覆盖 | M | ?/M | 详 UI-AC-COVERAGE 表 |
| 4. 全景增量同步 | 4 | ?/4 | 类型：⏭️ 无 / 🟡 增量 / 🔴 结构性 |
| 5. 结构性变更红线 | 3 | ?/3 | 任一命中即停 Stage |
| 6. 框架基线唯一性| 1 | ?/1 | framework_source = panorama overview.html（cite 路径）· ❌ 不得是历史 Feature preview/*.html |

### 全景对齐证据
- panorama_path: {绝对路径}
- 全景宿主：{当前子项目 / 跨子项目→{hosting_subproject}}
- 风格对照（read panorama/sitemap.md 后摘录 ≥3 条规范 + 本 Feature 遵守说明）：
 1. ...
 2. ...
 3. ...
- 导航位置：{本 Feature 页面在 sitemap 中的层级路径}
- 全景变更类型：⏭️ 无 / 🟡 增量 / 🔴 结构性

#### 🔴 HTML 物化对齐校验＂移"）

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

## HTML 预览稿模板(🔵 **static-html 介质专用** · same-stack 不用〔预览 = preview-project + preview.sh · 见 templates/preview-project-preview.sh〕· 🔴 v8.17:落在全景 · 不在 Feature)

> 🟢 **v8.17 全景为唯一权威**:HTML 文件直接落 `panorama_path/preview/<page>.html` · 不在 Feature 内。
> Feature 每改一个 page 编辑全景文件 + 在 `pages_changed[].panorama_file` 声明。
> 老模式(无 pages_changed[]):HTML 落 `Feature/preview/<page>.html` 副本(向后兼容)。
> AC 追溯:HTML 区块加 `data-ac="AC-XX"` 锚定,便于 grep + 与 UI-AC-COVERAGE 表对账。

```html
<!-- v8.17 推荐:{panorama_path}/preview/<page>.html(全景权威 · 直接编辑) -->
<!-- 老模式: docs/features/F{编号}-{功能名}/preview/<page>.html(Feature 副本) -->
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
