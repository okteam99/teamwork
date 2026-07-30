# Panorama Sync Stage

> 🧭 四段结构· 条件 stage:`ui_design-complete --panorama-changed=true` 时自动进入;`false` 时跳过(直进 blueprint)。

---

## ① 目标(telos)

**workspace 级 panorama 评审 + 跨 Feature 协调**:Feature 的 UI 改动涉及全景 IA(sitemap / overview)时,确认 IA 变更被评审、跨 Feature 影响被识别并协调。🟢 全景 `panorama_path/preview/<page>.html` 已在 ui_design 阶段由 Designer 直接改完(全景唯一权威 · 不存 Feature 副本),本 stage 不重复"同步副本",只做 sitemap.md 节点更新 + architect 评审 + 起草跨 Feature 协调 summary,并按结构变更程度决定是否需要 reviewer / 用户介入。拦的风险:panorama 同步若埋成 ui_design 隐式动作,跨 Feature 影响与跨团队评审就没有显式暂停点,审计会混进 Feature UI commit 里。

---

## ② 硬规则(白名单 · 每条一行 why)

1. **变更判级 L1/L2**(判据逐条写进 summary §协调结论 · 可审计):**L1**(节点内增量)须三判据**全**满足——① sitemap 无节点增删移 / 无路由变化 ② 无设计 token / 共享视觉基线变更 ③ 受影响 Features 扫描零命中;任一不满足,或**拿不准 → 一律按 L2**(why:结构变更〔节点增删移 / token 改动 / 冲突命中〕被误标 L1 逃暂停,后果与 R5 违规同级——宁可多停一次,不可漏协调)。
2. **L1 放行也要留痕 · L2 必停 R5**:L1 判定后仍须 `add-concern --severity WARN` 记三判据依据 + 输出零暂停 digest 才能 complete;L2 必须 emit R5 暂停点等 reviewers / 跨 Feature owner 表态,🔴 `auto_mode=true` 时可跳过但 PMO 必须 `add-concern --severity WARN` 记 `auto skip: panorama change scope=..., affected Features=...` 留痕(详 [SKILL.md § auto_mode=true 时各暂停点行为](../SKILL.md))(why:L1 已查明零跨 Feature 影响,再停只收获默认放行;L2 是 IA 权威变更,委托跳过也要 audit 可查)。
3. **`sitemap.md` 必须真更新**(panorama_sync-complete 物化校验:mtime > 本 stage `started_at`)(why:防止 panorama 单源没被实际编辑就上报完成——mtime 是唯一能核实"确实碰过文件"的机器信号)。🟢 冷启动(项目尚无 sitemap.md)时本 stage 退化为「建 panorama」,新建文件 touch 即自动满足 mtime 校验,不构成跳过更新的借口。
4. **`panorama-change-summary.md` frontmatter 三字段必填**:`reviewers` / `conclusion` / `change_level`(缺一 complete FAIL)(why:summary 是跨 Feature 协调的审计单源——缺字段 = 协调结论无法追溯谁评的、评没评、级别对不对)。
5. **本 stage 不改代码**(只动 panorama 单源 `sitemap.md` + `panorama-change-summary.md`;代码改动留 dev stage)(why:代码变更须过 dev 的测试证据硬门——本 stage 顺手改代码 = 绕过证据闸)。

---

## ④ Output Contract(产物契约 · 机读)

### 上下文入口(读什么)
`UI.md`(本 Feature `pages_changed[]`)· `PRD.md`(范围 / AC)· panorama 单源:`panorama_path/sitemap.md` + `panorama_path/preview/overview.html`(若存在)· 本 Feature 已在 ui_design 改完的全景(按 `panorama_medium`:`static-html` → `panorama_path/preview/<page>.html`;`same-stack` → `preview-project/` 源,跑 preview.sh 看实时 dev server)· `teamwork-space.md § 子项目清单`(识别可能受影响的其他子项目)。
🟢 老模式兼容(Feature 的 UI.md 无 `pages_changed[]`):仍需手动把 Feature 内 `preview/*.html` 副本同步到 `panorama_path/preview/<page>.html`(老路径);新 Feature 走新模式,本 stage 只 review 不重改。

### `panorama-change-summary.md`
- frontmatter:`reviewers: [pm, architect, ...]` · `conclusion: passed | needs-revision` · `change_level: L1 | L2`
- body(每段 ≥2 行 · `body_min_lines: 8`):§变更摘要(改了哪些节点 / 路径 / 组件)/ §受影响 Features(扫 `teamwork-space.md` + 各子项目 `ROADMAP.md` 列可能受影响的 in-flight / planned Features)/ §协调结论(reviewers 跨 Feature 视角评审 + L1/L2 三判据逐条依据 + 是否需要其他 owner 联动,open question 留 INFO concerns)

### `panorama_path/sitemap.md`
mtime 晚于本 stage `started_at` · 节点结构反映本 Feature 的 IA 改动

### (可选)`panorama_path/preview/overview.html`
panorama 是 `static-html` 介质时同步结构性改动;`same-stack` 介质看项目 design route 注册

### L1 · 自动放行留痕
```
state.py add-concern --severity WARN --message "L1 auto-pass: panorama change scope=<节点/描述>, 判据=①无节点增删移 ②无 token 变更 ③冲突扫描零命中"
```
随后输出零暂停 digest(≤3 行:变更一句话 + 判级三依据 + summary/diff 指针)· 用户看得见不被打断 · 直接进 complete。

### L2 · ⏸️ R5 暂停点(reviewers + 跨 Feature owner 协调)
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
`auto_mode=true` 时可跳过本暂停(仍须先满足②规则 2 的留痕义务)。📚 决策参考:`panorama-change-summary.md`(含 change_level 判据)/ `sitemap.md` diff / 受影响 Features 清单。

### complete
```
state.py panorama_sync-complete --feature <path> --auto-commit <hash> \
  --artifacts panorama-change-summary.md
```
state.py 校验:`sitemap.md` mtime > stage `started_at` · `panorama-change-summary.md` 存在 + frontmatter 含 `reviewers` / `conclusion` / `change_level` · 通过 → 自动转 `blueprint`。

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `PANORAMA_SYNC_SPEC`
- 上游:[ui-design-stage.md § Panorama 介质类型](./ui-design-stage.md) + `ui_design-complete --panorama-changed`
- 角色:[../roles/designer.md](../roles/designer.md) · [../roles/pm.md](../roles/pm.md)(跨 Feature 影响评估)
