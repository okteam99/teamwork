# Panorama Sync Stage

> **workspace 级 panorama 评审 + 跨 Feature 协调** —— Feature 的 UI 改动影响全景 IA(sitemap / overview)时,architect 评审跨 Feature 影响 + 起草协调 summary。
>
> 条件 stage:`ui_design-complete --panorama-changed=true` 时自动进入;`false` 时跳过(直进 blueprint)。
> panorama 同步若埋成 ui_design 隐式动作 → 跨 Feature 影响 / 跨团队评审无显式暂停点 / 审计混在 Feature UI commit 里。

🟢 **全景为唯一权威**:`panorama_path/preview/<page>.html` 已在 ui_design 阶段直接改完(全景权威 · 不存 Feature 副本)· 本 stage **不再"同步副本到全景"** · 只做 sitemap.md 节点更新 + architect 评审 + 跨 Feature 协调 summary。

---

## 怎么做

### 1. 加载上下文(主对话 Designer / Architect / PMO 身份)
- 读 `UI.md`(本 Feature 的 pages_changed[] · IA 改动范围)· `PRD.md`(范围 / AC)
- 读 panorama 单源:`panorama_path/sitemap.md` + `panorama_path/preview/overview.html`(若存在)
- 读本 Feature 在 ui_design 已改的全景:`static-html` → `panorama_path/preview/<page>.html`;`same-stack`→ `panorama_path/preview-project/` 源(跑 preview.sh 看实时 dev server)
- 读 `teamwork-space.md § 子项目清单`(识别可能被本变更影响的其他子项目)

### 2. 更新 sitemap.md + 评审 panorama 文件改动
- **`sitemap.md`**:新增 / 移动 / 删除页面节点 · 保持层级清晰 · **mtime 必晚于本 stage `started_at`**(evidence_check 物化校验)
- **`panorama_path/preview/<page>.html`**(新模式):本 Feature 已在 ui_design 阶段直接改完 · 本 step 由 architect **review**(不重改 · 仅评)
- **`overview.html`**(若 panorama 是 `static-html` 介质 + 结构性改动):同步 DOM 变更
- 项目同栈 panorama(`same-stack`):评 preview-project 源(组件 / 路由 / mock)· 跑 preview.sh 看实时 dev server(不出静态 build)

🟢 **老模式(无 `pages_changed[]` UI.md)兼容**:仍可在本 step 把 Feature 内 preview/*.html 副本同步到 panorama_path/preview/<page>.html(老路径)· 但新 Feature 推荐新模式(ui_design 直接改全景 · 本 stage 仅 review)。

### 3. 起草 `panorama-change-summary.md`(本 Feature 目录)+ 变更判级
frontmatter 必含 `reviewers` + `conclusion` + `change_level`(详 Output Contract)· body 列:
- **变更摘要**:本 Feature 改了 panorama 哪些节点 / 路径 / 组件
- **受影响 Features**:扫 `teamwork-space.md` + 各子项目 `ROADMAP.md` · 列可能受影响的 in-flight / planned Features
- **协调结论**:reviewers 跨 Feature 视角的评审 + 是否需要其他 Feature owner 联动(open question 留 INFO concerns)

🔴 **变更判级**(受影响 Features 扫描完成后判 · 依据逐条写进 §协调结论):
- **L1 · 节点内增量**:三判据**全**满足 —— ① sitemap 无节点增删移 / 无路由变化(只改既有节点的描述 / 状态列)② 无设计 token / 共享视觉基线变更 ③ 受影响 Features 扫描零命中
- **L2 · 结构变更**:任一判据不满足。拿不准 → 按 L2(宁可多停一次 · 不可漏协调)

### 4. ⏸️ 跨团队 reviewer 评审(条件 R5 暂停点 · 仅 L2 停)
🟢 **L1 不暂停** —— 暂停保护的两件事(IA 权威变更需多方评审 · 跨 Feature 影响需 owner 协调)在 L1 均不成立 · 事实已查明还停 = 只收获默认放行。PMO 三步:
1. `state.py add-concern --severity WARN --message "L1 auto-pass: panorama change scope=<节点/描述>, 判据=①无节点增删移 ②无 token 变更 ③冲突扫描零命中"` 留 audit
2. 输出零暂停 digest(≤3 行:变更一句话 + 判级三依据 + summary/diff 指针)· 用户看得见不被打断
3. 直接进 step 5 complete

🔴 **L2 必停**(`auto_mode=true` 时跳过 —— `panorama-change-summary.md` 已文档化 · auto 用户接受跨 Feature 影响 · PMO 必 `state.py add-concern --severity WARN --message "auto skip: panorama change scope=<节点/路径>, affected Features=<列表>"` 留 audit · 详 [SKILL.md § auto_mode=true 时各暂停点行为](../SKILL.md))。PMO emit R5 标准 1/2/3:

```markdown
⏸️ Panorama 结构变更(L2)需 reviewers 评审 + 跨 Feature owner 协调

请选择:
1. ✅ **评审通过 · 进 blueprint** 💡 推荐(reviewers 已签 + 无受影响 owner 异议)
   动作:`panorama_sync-complete` → 自动转 blueprint
2. ⚠️ **要改 panorama 设计**
   动作:Designer 改 sitemap / summary · 重跑 reviewer
3. ❌ **回退:不改 panorama · 退本 Feature UI**
   动作:用户选 `jump-to-stage --to ui_design --reason ...` 重做 UI(不改 IA)
```

📚 决策参考:`panorama-change-summary.md`(含 change_level 判据)/ `sitemap.md` diff / 受影响 Features 清单

### 5. complete
```
state.py panorama_sync-complete --feature <path> --auto-commit <hash> \
  --artifacts panorama-change-summary.md
```
state.py 校验:
- `sitemap.md` mtime > stage `started_at`(panorama 真被更新)
- `panorama-change-summary.md` 存在 + frontmatter 含 `reviewers` / `conclusion` / `change_level`
- 通过 → 自动转 `blueprint`

---

## 质量基线

📎 **物化拦截**:
- **`sitemap.md` mtime > stage `started_at`** —— 没真更新 panorama 就 complete · evidence_check FAIL
- **`panorama-change-summary.md` 必存** —— frontmatter `reviewers` + `conclusion` + `change_level` 缺一即 FAIL
- 跨 Feature 影响 owner 未协调 → reviewer 应在 summary 留 `WARN concerns`(本 stage 不强阻 · 但 audit 有迹)

🔴 **判级反模式**:结构变更(节点增删移 / token 改动 / 冲突命中)标 L1 逃暂停 = R5 违规同级。三判据依据必须逐条写进 summary §协调结论 · 可审计;PROCESS-LEDGER「暂停点 改:默」列统计 L1/L2 比例 · L1 被滥用回溯有迹。

🔴 **本 stage 不修代码** —— 只动 panorama 单源 + summary 文档。代码改动在后续 dev stage 做。

🔴 **冷启动豁免**:若项目 panorama 初次建立(panorama_path 未存在 sitemap.md)· 本 stage 退化为「建 panorama」· `sitemap.md` mtime 校验仍走(刚 touch 即 mtime > stage_started_at)。

---

## Output Contract(产物形态参考)

> 📋 **起草模板**(避免找历史 Feature 抄):
> - panorama-change-summary.md → 无独立模板 · 见下方 schema(reviewers + conclusion + change_level + 3 段 body)
> - panorama_path/sitemap.md → 项目级 sitemap · 无模板(按项目 IA 结构维护)
> - panorama_path/preview/overview.html(static-html 介质)→ 项目设计语言决定 · 无统一模板

### `panorama-change-summary.md`
- frontmatter:`reviewers: [pm, architect, ...]` · `conclusion: passed | needs-revision` · `change_level: L1 | L2`
- body:§变更摘要 / §受影响 Features / §协调结论(每段 ≥ 2 行 · `body_min_lines: 8` · 协调结论含 L1/L2 三判据逐条依据)

### `panorama_path/sitemap.md`
- mtime 晚于本 stage `started_at`
- 节点结构反映本 Feature 的 IA 改动

### (可选)`panorama_path/preview/overview.html`
- panorama 是 `static-html` 介质时同步;`same-stack` 介质看项目 design route 注册

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `PANORAMA_SYNC_SPEC`
- 上游:[ui-design-stage.md § Panorama 介质类型](./ui-design-stage.md) + `ui_design-complete --panorama-changed`
- 角色:[../roles/designer.md](../roles/designer.md) · [../roles/pm.md](../roles/pm.md)(跨 Feature 影响评估)
