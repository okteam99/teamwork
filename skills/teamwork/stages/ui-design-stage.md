# UI Design Stage

---

## Panorama 介质类型(🔴 ui_design 启动前必决)

teamwork 支持两种 panorama 介质 · 项目应在 ui_design 启动前明确,写入 `UI.md` frontmatter `panorama_medium`:

| medium | 适用 | 优点 | 缺点 |
|---|---|---|---|
| `same-stack`(**推荐**) | 项目前端栈已定 | 像素级 fidelity by construction · dev「UI 还原」= 真渲染 diff | 需前端栈 + mock data 设施(/design/* 路由 + MockDataProvider) |
| `static-html`(兜底) | 前端栈未定 / Designer-only / Greenfield POC | 零 build chain · designer 独立产出 | 介质差异 → **不可能像素级仿 live**(系统字体 vs webfont · CDN Tailwind 编译时机 · shadcn 语义 token 缺失 等)· **仅作 IA / 视觉层级 / Token 一致性参考** |

🔴 **硬规则**:
- 项目 `PROJECT.md` 声明了前端栈(`frontend_stack` 非空)→ panorama **必须 `same-stack`** · 用 `static-html` 即规范违规
- 「前端栈已定 + panorama 仍 `static-html`」= **dirty state** · 必须开 Feature 把 panorama 迁到 `same-stack` · 不可永久 hack(治本 PTR-F052 case · 4 轮调像素仍有差异 = 介质差异不可调和的实证)
- `UI.md` frontmatter 缺 `panorama_medium` → verify-panorama / UI_DESIGN_SPEC 视作 `static-html`(向后兼容 · 但新建 Feature 必显式声明)

---

## 怎么做

### 1. 加载上下文
读 PRD.md(用户场景)· sitemap.md(信息架构)· KNOWLEDGE.md(项目级 UI 规范)· `PROJECT.md § 技术栈`(决定 panorama_medium)

### 2. Designer 起草 UI.md
frontmatter `pages: [{id, title}]` + `panorama_medium: same-stack|static-html` 必 · body §页面列表 / §交互流 / §视觉规范 / §字段映射(对应 PRD.AC)

### 3. 产出 panorama(按 `panorama_medium` 分支)

- **`same-stack`**:在项目前端仓加 `/design/<page-id>` 路由(或同效)· 用项目自身组件 + MockDataProvider 注入 fixture 数据 · `UI.md` 引用这些 design route 的真实 URL · **不产** `preview/*.html`
- **`static-html`**:每 page.id 对应 `preview/<page.id>.html` · 静态 HTML + Tailwind CDN · 不只是静态图 · 含可点击交互

### 4. sitemap 同步
若涉及全景变更 · 同步 sitemap.md(项目根)· 防破坏现有路由

### 5. ⏸️ 用户预览确认(R5 暂停点)
🔴 emit R5 标准 1/2/3(模板见 [SKILL.md § R5(b)](../SKILL.md)):
1. **确认 UI · 进入 blueprint** 💡 推荐 — `ui_design-complete` → 自动转 blueprint
2. **要改设计** — Designer 按你的反馈改 UI.md + preview
3. **其他指示**

📚 决策参考:`preview/<page>.html`

### 6. complete
`state.py ui_design-complete --feature X --auto-commit Y --artifacts UI.md,preview/`

---

## 必读 cite 清单(P0-11 · 各 substep 动手前主对话输出)

| Substep | 必读 spec | 段 | cite 关键点 |
|---------|----------|----|------------|
| 1. 加载上下文 | `roles/designer.md` | § Telos + 创作要点 | UX 视角 |
| 2. Designer 起草 UI.md | `roles/designer.md` | § 创作要点 | frontmatter pages[] + body 4 段 |
| 3. 产出 panorama | `roles/designer.md` | § HTML 预览 / § Design Route | 按 `panorama_medium` 走 · same-stack 用 /design/* 路由 · static-html 产 preview/*.html · 含可交互 |
| 4. sitemap 同步 | — | — | (无 cite 要求 · 若涉及全景) |
| 5. ⏸️ 用户预览确认 | — | — | (无) |
| 6. complete | — | — | (无) |


📎 **cite 纪律**(输出格式 / 强约束 / 为什么 cite)· 单源详 [../STAGES.md § 2 P0-11 cite 纪律](../STAGES.md)

## 质量基线

📎 **物化拦截**(均按 `panorama_medium` 适配):
- **`static-html`**:preview HTML 文件名 = `<page.id>.html`(物化校验 `pages[].id` 对应 .html 存在 · 错位 → ui_design-complete FAIL);`verify-panorama.py` 走完整校验(self-check + host marker + preview count + panorama_path)
- **`same-stack`**:不要求 `preview/*.html` 存在 · `verify-panorama.py` 跳过 HTML 文件相关检查(不卡流程)· 仅校验 UI.md 自查报告 + frontmatter
- `stage_contracts.ui_design.output_satisfied=true` → dev-start 自动触发 UI 还原校验段(dev-stage §3 按 medium 分支)

**preview SOP**(违反 → dev 还原 / pm_acceptance 打回):
- 抽公共组件 / CSS class · preview 引用统一样式表 · 不每页 inline(维护噩梦)
- preview HTML 含点击 / 表单 / 跳转(真实交互)· 不只是静态图 · 让 dev 可 verify 交互

**sitemap 改动**:必显式列影响范围 · 主对话与相关 Feature owner 协调(防破坏现有路由)

---

## Output Contract(产物形态参考)

### `UI.md`
frontmatter `pages: [{id, title}]` · body 4 段(页面列表 / 交互流 / 视觉规范 / 字段映射)

### panorama 产物(按 `panorama_medium`)
- **`static-html`**:`preview/*.html` 至少 1 文件 · `pages[].id` 全有对应 · 可交互
- **`same-stack`**:项目前端仓 `/design/<page-id>` 路由 · `UI.md` 引用真实 URL · 无 `preview/*.html`(规范允许)

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `UI_DESIGN_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
