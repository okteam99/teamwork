# UI Design Stage

---

## 怎么做

### 1. 加载上下文
读 PRD.md(用户场景)· sitemap.md(信息架构)· KNOWLEDGE.md(项目级 UI 规范)

### 2. Designer 起草 UI.md
frontmatter `pages: [{id, title}]` 必 · body §页面列表 / §交互流 / §视觉规范 / §字段映射(对应 PRD.AC)

### 3. 产出 preview/*.html
每 page.id 对应 `<page.id>.html` · 不只是静态图 · 含可点击交互

### 4. sitemap 同步
若涉及全景变更 · 同步 sitemap.md(项目根)· 防破坏现有路由

### 5. ⏸️ 用户预览确认
给用户预览 URL · 等确认

### 6. complete
`state.py ui_design-complete --feature X --auto-commit Y --artifacts UI.md,preview/`

---

## 必读 cite 清单(P0-11 · 各 substep 动手前主对话输出)

| Substep | 必读 spec | 段 | cite 关键点 |
|---------|----------|----|------------|
| 1. 加载上下文 | `roles/designer.md` | § Telos + 创作要点 | UX 视角 |
| 2. Designer 起草 UI.md | `roles/designer.md` | § 创作要点 | frontmatter pages[] + body 4 段 |
| 3. 产出 preview/*.html | `roles/designer.md` | § HTML 预览 | 可交互 · 不只是静态图 |
| 4. sitemap 同步 | — | — | (无 cite 要求 · 若涉及全景) |
| 5. ⏸️ 用户预览确认 | — | — | (无) |
| 6. complete | — | — | (无) |


**输出格式**(每个 substep 动手前必在主对话输出):
```
📖 cite:
- <spec> § <段>:"<引该段 1 句关键原文 · 证明真读>"
```

**强约束**(R5+P0-11 软约束 · 用户监督):
- 标 "—" 的 substep 无 cite 要求(状态机操作 / 用户暂停 / 已物化)
- 其余 substep **动手前必输出 cite 块** · 缺 cite 视为 process 违规(用户可叫停)
- cite 必含 § 段标题 + 至少 1 句原文(原文必真实存在于该 spec · 不可瞎编)
- AI 在 stage 内多次切角色 · 每次切换前重新 cite 该角色规范

**为什么 cite**:
- brief 列路径(P0-4)只解决"AI 找不到路径"· 不保证 AI 真读
- complete 时校验太晚(AI 已做完)
- substep 动手前 cite = 事前提醒 · 强制 AI 翻一眼 spec
- 物化死角(state.py 看不到 markdown Read 动作)· 软约束 + 用户监督兜底

## 注意事项

### 坑 1 · preview HTML 命名错位
page.id ≠ 文件名 → ui_design-complete FAIL(物化校验 pages[].id 对应 .html 存在)。
 **对策**:文件名严格 = `<page.id>.html`

### 坑 2 · 每页 inline 样式 / 不复用基础组件
视觉不一致 · 维护噩梦。
 **对策**:抽公共组件 / CSS class · preview 引用统一样式表

### 坑 3 · preview 只是静态图
Dev 还原时无法 verify 交互。
 **对策**:preview HTML 含点击 / 表单 / 跳转 · 真实交互

### 坑 4 · sitemap 更新破坏现有路由
其他 Feature 跑现有路由 fail。
 **对策**:sitemap 改动必显式列影响范围 · 主对话与相关 Feature owner 协调

### 坑 5 · UI 改动未通知 dev stage
Dev 漏跑 verify-panorama · 还原偏差到 pm_acceptance 才发现。
 **对策**:ui_design 完成时显式标记 stage_contracts.ui_design.output_satisfied=true · dev-start 自动触发 UI 还原校验段(brief 中提醒)

---

## Output Contract(产物形态参考)

### `UI.md`
frontmatter `pages: [{id, title}]` · body 4 段(页面列表 / 交互流 / 视觉规范 / 字段映射)

### `preview/*.html`
至少 1 文件 · pages[].id 全有对应 · 可交互

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `UI_DESIGN_SPEC`
- 入口规范:[../TRIAGE.md](../TRIAGE.md)
