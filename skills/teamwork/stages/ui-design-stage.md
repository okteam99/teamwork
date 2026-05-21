# UI Design Stage

---

## 🟢 全景为唯一权威(v8.17 · 推荐新模式 · 治本 PTR-F052 双副本 / PTR-F054 介质绕路)

> 老模式(Feature 内存 `preview/*.html` 副本)与全景权威版本**必然脱节**(PTR-F052 实证 · static-html 介质 dirty state · 4 轮调像素仍有差异)。
> 新模式:**全景 `panorama_path/preview/<page>.html` 是唯一权威 · Feature 不存副本** · UI.md 改为「全景改动声明 + 局部决策记录」。

### frontmatter 新字段(替代 Feature 内 preview/ 副本)

```yaml
---
pages:
  - {id: offers, title: "Offers"}
panorama_medium: static-html               # 介质类型(不变)
panorama_path: apps/partner/docs/design    # 全景权威根
pages_changed:                              # v8.17:有此字段 → 进入新模式
  - page_id: offers                         # 必 · 对应 pages[].id
    panorama_file: apps/partner/docs/design/preview/offers.html  # 必 · 全景权威路径
    change_range: "Tabs 与 Table 之间新增 filter 区"               # 可选 · 本 Feature 改动描述
    acceptance_criteria_refs: [AC-1, AC-3] # 可选 · 关联 PRD AC
---
```

### Feature 执行流程(v8.17)

1. ui_design 阶段:Designer 直接编辑 `panorama_path/preview/<page>.html`(全景权威 · worktree 内改 · merge 后同步全景)
2. UI.md 写 `pages_changed[]` 声明本 Feature 改了哪几个 page + 改动范围
3. ui_design-complete:`_evidence_panorama_artifact` 校验每个 `panorama_file` 真实存在
4. panorama_sync stage(条件触发):architect 评审跨 Feature 影响 + 起草 panorama-change-summary.md + 更新 sitemap.md

### 与老模式的对比

| 维度 | 老模式 | 新模式(v8.17) |
|---|---|---|
| Feature 内 preview/*.html | 必(static-html 介质) | **不存** |
| 全景 preview/*.html | 副本(panorama_sync 同步) | 唯一权威(ui_design 直接改) |
| 双副本不一致风险 | ⚠️ 必然(PTR-F052 实证) | ✅ 不存在 |
| Feature 局部决策痕迹 | UI.md + preview/ | UI.md(pages_changed[] 声明) |
| 评审视角分层 | ui_design 局部 + panorama_sync 全局(各评 1 次) | 不变(双 stage 保留) |
| 工作量(改一个 page) | 改 Feature 副本 + panorama_sync 时同步全景(2 处) | 直接改全景(1 处) |
| 跨 Feature 并行 | Feature 间无 merge 冲突(各自副本) | 多 Feature 改同一 panorama 文件可能 merge(项目 SOP 错峰) |

### 向后兼容(老 Feature)

- UI.md 无 `pages_changed[]` 字段 → fallback 老模式(`panorama_medium=static-html` 要求 Feature 内 `preview/*.html` ≥ 1)
- 老 Feature 不强迁 · 新 Feature 推荐新模式

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

🟢 **v8.17 推荐:全景为唯一权威**(详上 § 全景为唯一权威 · UI.md frontmatter 加 `pages_changed[]`):

- **`same-stack`**:在项目前端仓加 `/design/<page-id>` 路由 · 用项目自身组件 + MockDataProvider · UI.md 引用 design route URL · **不产** preview/*.html
- **`static-html`**:**直接编辑** `panorama_path/preview/<page.id>.html`(全景权威 · 唯一 source · worktree 内改 · merge 后同步全景)· UI.md `pages_changed[].panorama_file` 链到权威路径 · **Feature 内不存 preview/ 副本**

老模式(向后兼容 · 无 `pages_changed[]`):每 page.id 对应 Feature 内 `preview/<page.id>.html`(副本)· 静态 HTML + Tailwind CDN · 含可点击交互 —— 不推荐(PTR-F052 双副本不一致风险)

### 4. 判定 panorama 是否被本 Feature 改动(workspace 级 IA 影响?)
本 Feature UI 若动了 workspace 级 panorama(sitemap 节点 / overview / 设计 token)→ 在 §6 `ui_design-complete --panorama-changed=true` 显式标记 → 自动转 **panorama_sync** stage(workspace 级单独 stage · 收敛 sitemap 更新 + 跨 Feature reviewer 协调评审 · 详 [panorama-sync-stage.md](./panorama-sync-stage.md))。
不动 panorama → `--panorama-changed=false` · 直进 blueprint。

🔴 **本 stage 不直接改 sitemap.md** —— 改 sitemap / overview 是 panorama_sync stage 的产物(隔离审计 / 暂停点 / 跨 Feature 评审)。

### 5. ⏸️ 用户预览确认(R5 暂停点)
🔴 **`auto_mode=true` 时跳过此暂停点** —— 设计意图已落 UI.md / preview · auto 用户接受(详 [SKILL.md § auto_mode=true 时各暂停点行为](../SKILL.md))。

🔴 emit R5 标准 1/2/3(模板见 [SKILL.md § R5(b)](../SKILL.md)):
1. **确认 UI · 进入 blueprint** 💡 推荐 — `ui_design-complete` → 自动转 blueprint
2. **要改设计** — Designer 按你的反馈改 UI.md + preview
3. **其他指示**

📚 决策参考:`preview/<page>.html`

### 6. complete
```
state.py ui_design-complete --feature X --auto-commit Y \
  --artifacts <UI.md[,preview/]> \
  --panorama-changed {true|false}
```
- `--artifacts`:UI.md 必 · `static-html` 介质加 `preview/` · `same-stack` 介质仅 UI.md
- `--panorama-changed`:**必传** · true → 自动转 `panorama_sync` stage(workspace IA 同步 + 跨 Feature 评审)· false → 直进 blueprint

---

## 必读 cite 清单(P0-11 · 各 substep 动手前主对话输出)

| Substep | 必读 spec | 段 | cite 关键点 |
|---------|----------|----|------------|
| 1. 加载上下文 | `roles/designer.md` | § Telos + 创作要点 | UX 视角 |
| 2. Designer 起草 UI.md | `roles/designer.md` | § 创作要点 | frontmatter pages[] + body 4 段 |
| 3. 产出 panorama | `roles/designer.md` | § HTML 预览 / § Design Route | 按 `panorama_medium` 走 · same-stack 用 /design/* 路由 · static-html 产 preview/*.html · 含可交互 |
| 4. panorama 判定 | — | — | (无 cite 要求 · 涉变更交 panorama_sync stage) |
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

> 📋 **起草模板**(避免找历史 Feature 抄):
> - UI.md → `{SKILL_ROOT}/templates/ui.md`(含 panorama_medium frontmatter 示例)
> - preview/*.html(static-html 时)→ 无统一模板 · 按项目设计语言写

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
