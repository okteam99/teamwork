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


📎 **cite 纪律**(输出格式 / 强约束 / 为什么 cite)· 单源详 [../STAGES.md § 2 P0-11 cite 纪律](../STAGES.md)

## 质量基线

📎 **物化拦截**:
- preview HTML 文件名 = `<page.id>.html`(物化校验 `pages[].id` 对应 .html 存在 · 错位 → ui_design-complete FAIL)
- `stage_contracts.ui_design.output_satisfied=true` → dev-start 自动触发 UI 还原校验段

**preview SOP**(违反 → dev 还原 / pm_acceptance 打回):
- 抽公共组件 / CSS class · preview 引用统一样式表 · 不每页 inline(维护噩梦)
- preview HTML 含点击 / 表单 / 跳转(真实交互)· 不只是静态图 · 让 dev 可 verify 交互

**sitemap 改动**:必显式列影响范围 · 主对话与相关 Feature owner 协调(防破坏现有路由)

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
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
