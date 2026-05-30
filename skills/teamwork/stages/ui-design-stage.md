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

| medium | 适用 | 实现 | 优点 / 缺点 |
|---|---|---|---|
| `same-stack`(**推荐**) | 项目前端栈已定 | **独立 preview-project**:`{子项目}/docs/design/preview-project/`(同技术栈的独立前端项目 · 自带目标库 · 含 mock data)· `npm run build` → `{子项目}/docs/design/preview/*.html`(可视全景 · 必产) | ✅ 真实组件渲染保真 · **不污染真实工程** · **解「本 Feature 引入新库(如 antd 未装)」鸡蛋问题**(preview-project 独立装) ❌ 需搭独立项目 + 编译 |
| `static-html`(兜底) | 前端栈未定 / Designer-only / Greenfield POC | 手写 `{panorama_path}/preview/*.html`(CDN) | ✅ 零 build chain · designer 独立产出 ❌ 介质差异 → **不可能像素级仿 live**(系统字体 vs webfont · CDN 编译时机 · 语义 token 缺失 等)· **仅作 IA / 视觉层级 / Token 一致性参考** |

> 🔴 **v8.56 重定义 same-stack**(治本 CW-F002 case):旧 same-stack = 在**真实前端 app** 加 `/design/*` 路由 —— 污染真实工程 + 引入新库时鸡蛋问题。新 same-stack = **`{子项目}/docs/design/` 独立 preview-project 编译出静态全景**:
> ```
> {子项目}/docs/design/
>   ├─ UI.md              设计规范(token + 组件映射 + 页面 + AC 覆盖)· 也可在 feature_dir
>   ├─ preview-project/   独立前端项目(同技术栈 · 自带目标库 · src/Preview 渲染各页 + mock)· node_modules gitignore
>   └─ preview/           🔴 编译产物 *.html(可视全景 · 必产 · ui_design-complete 校验存在)
> ```
> `panorama_path = {子项目}/docs/design` · `pages_changed[].panorama_file → {子项目}/docs/design/preview/<page>.html`。
> 老 Feature(in-app /design 路由 / 无 preview)向后兼容不强迁 · 新 Feature 用本模型。

🔴 **硬规则**:
- 项目 `PROJECT.md` 声明了前端栈(`frontend_stack` 非空)→ panorama **必须 `same-stack`** · 用 `static-html` 即规范违规
- 「前端栈已定 + panorama 仍 `static-html`」= **dirty state** · 必须开 Feature 把 panorama 迁到 `same-stack` · 不可永久 hack(治本 PTR-F052 case · 4 轮调像素仍有差异 = 介质差异不可调和的实证)
- 🔴 **same-stack 必产可视全景**(v8.56):编译出 `{子项目}/docs/design/preview/*.html` · ui_design-complete **物化校验存在** · **不可只写 UI.md markdown 跳过可视全景**(治本 CW-F002:AI 拿"验证器只校验 UI.md 自查""same-stack 不要求 preview"当借口零可视产出 —— 最低物化闸 ≠ 免做交付物许可)
- `UI.md` frontmatter 缺 `panorama_medium` → verify-panorama / UI_DESIGN_SPEC 视作 `static-html`(向后兼容 · 但新建 Feature 必显式声明)

---

## 预览服务 hub(v8.57 · same-stack 编译产物必经)

> 🔴 same-stack 预览是编译出的 ES-module bundle · `file://` 因 CORS 不加载 module(browse 停 about:blank)· **必须 HTTP server**。各 session/并行 worktree/多终端各自 `python3 -m http.server` 会**抢端口冲突**。治本 = **单 hub**:全机一个常驻服务进程 · 各预览目录注册到共享 registry(`~/.teamwork/preview/`)· `http://127.0.0.1:<port>/<slug>/` 分发 · 后续 session 复用同 hub 不抢端口。

| 子命令 | 作用 |
|---|---|
| `preview.py serve --feature {feat_dir}` | 解析 feature 预览目录(UI.md `pages_changed[].panorama_file` / `feature/preview`)· 注册 + 确保 hub 起 · 返 `url`/`page_urls` |
| `preview.py serve --dir {子项目}/docs/design/preview` | 显式指定编译产物目录(same-stack 推荐) |
| `preview.py list` | hub 状态 + 全部已注册预览 + URL(跨 session 找别人的预览稿) |
| `preview.py stop --all` | 停 hub(registry 保留 · 下次 serve 自动重启) |
| `preview.py stop --slug X` / `--prune` | 注销单个 / 清 dir 已删的 stale 条目 |

🔴 **注意**:① same-stack build 必 `base:'./'`(相对资产路径)· 否则 `/<slug>/` 前缀下 `/assets/*` 绝对路径 404 · ② hub detached 常驻(终端关了仍活)· ③ 仅 `127.0.0.1`(本机) · 不对外。

---

## 怎么做

### 1. 加载上下文
读 PRD.md(用户场景)· sitemap.md(信息架构)· KNOWLEDGE.md(项目级 UI 规范)· `PROJECT.md § 技术栈`(决定 panorama_medium)

### 2. Designer 起草 UI.md
frontmatter `pages: [{id, title}]` + `panorama_medium: same-stack|static-html` 必 · body §页面列表 / §交互流 / §视觉规范 / §字段映射(对应 PRD.AC)

### 3. 产出 panorama(按 `panorama_medium` 分支)

🟢 **v8.17 推荐:全景为唯一权威**(详上 § 全景为唯一权威 · UI.md frontmatter 加 `pages_changed[]`):

- **`same-stack`**(v8.56):在 `{子项目}/docs/design/preview-project/` 搭**同栈独立项目**(自带目标库 + mock data · `src/Preview` 渲染各 page)· `npm run build` → `{子项目}/docs/design/preview/<page>.html`(可视全景 · **必产** · 🔴 build 配**相对资产路径** vite `base:'./'` · 否则 hub `/<slug>/` 前缀下 `/assets/*` 绝对路径 404)· UI.md `pages_changed[].panorama_file` 链到 `docs/design/preview/<page>.html` · 本 Feature **引入新库**时 preview-project 独立装该库(解鸡蛋问题)· 🔴 **验证渲染:`python3 {SKILL_ROOT}/tools/preview.py serve --dir {子项目}/docs/design/preview`(v8.57 单 hub · 自动起服务 + 不抢端口 + 跨 session/worktree 可访问)→ 拿返回的 `url` → browse 截图**(`file://` 因 CORS 不加载 ES module · 不要手动 `python3 -m http.server`〔并行 worktree/多终端会端口冲突〕· 治本 CW-F002 误判"渲染正常")
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

📚 决策参考:
- **`static-html`**:直接 browse `preview/<page>.html`(纯 HTML · `file://` 可开)
- **`same-stack`**(v8.57):`python3 {SKILL_ROOT}/tools/preview.py serve --feature {feature_dir}` → 把返回的 `url`(及 `page_urls`)给用户 browse · 单 hub 自动起服务 · 跨 session/worktree 同一端口不冲突 · `preview.py list` 看全部已注册预览

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
- **`same-stack`**(v8.56 物化):**要求** `{子项目}/docs/design/preview/*.html`(preview-project 编译产物)存在 —— ui_design-complete 校验(`pages_changed[].panorama_file` 真实存在 · 或 `panorama_path/preview/*.html` ≥ 1)· 🔴 **不再「不要求 preview · return True」**(那是 CW-F002 cut-corner 的缝)· UI.md 自查 + frontmatter 仍校验
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
- **`same-stack`**(v8.56):`{子项目}/docs/design/preview-project/`(同栈独立项目 · node_modules gitignore)+ **编译产物** `{子项目}/docs/design/preview/*.html`(必产 · 校验存在)· UI.md `pages_changed[]` 链到 `preview/<page>.html`

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `UI_DESIGN_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
