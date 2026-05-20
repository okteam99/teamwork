# Panorama Sync Stage

> **workspace 级 panorama 同步** —— Feature 的 UI 改动影响全景 IA(sitemap / overview / 设计 token)时,把改动**显式收敛**到 panorama 单源,并跨 Feature 协调评审。
>
> 条件 stage:`ui_design-complete --panorama-changed=true` 时自动进入;`false` 时跳过(直进 blueprint)。
> 治本 case:历史把 panorama 同步埋成 ui_design step 4(隐式动作)· 跨 Feature 影响 / 跨团队评审无显式暂停点 / 审计混在 Feature UI commit 里。

---

## 怎么做

### 1. 加载上下文(主对话 Designer / PMO 身份)
- 读 `UI.md`(本 Feature 的 IA 改动)· `PRD.md`(范围 / AC)
- 读 panorama 单源:`panorama_path/sitemap.md` + `panorama_path/preview/overview.html`(若存在)
- 读 `teamwork-space.md § 子项目清单`(识别可能被本变更影响的其他子项目)

### 2. 更新 panorama 单源
- `sitemap.md`:新增 / 移动 / 删除页面节点 · 保持层级清晰
- `overview.html`(若 panorama 是 `static-html` 介质):同步 DOM 变更
- 项目同栈 panorama(`same-stack`)· 更新 design route 注册表 / 导航组件 fixture
- **mtime 必晚于本 stage `started_at`** —— evidence_check 物化校验

### 3. 起草 `panorama-change-summary.md`(本 Feature 目录)
frontmatter 必含 `reviewers` + `conclusion`(详 Output Contract)· body 列:
- **变更摘要**:本 Feature 改了 panorama 哪些节点 / 路径 / 组件
- **受影响 Features**:扫 `teamwork-space.md` + 各子项目 `ROADMAP.md` · 列可能受影响的 in-flight / planned Features
- **协调结论**:reviewers 跨 Feature 视角的评审 + 是否需要其他 Feature owner 联动(open question 留 INFO concerns)

### 4. ⏸️ 跨团队 reviewer 评审(R5 暂停点)
🔴 **`auto_mode=true` 时跳过此暂停点** —— `panorama-change-summary.md` 已文档化 · auto 用户接受跨 Feature 影响 · PMO 必 `state.py add-concern --severity WARN --message "auto skip: panorama change scope=<节点/路径>, affected Features=<列表>"` 留 audit(详 [SKILL.md § auto_mode=true 时各暂停点行为](../SKILL.md))。

🔴 PMO emit R5 标准 1/2/3:

```markdown
⏸️ Panorama 改动需 reviewers 评审 + 跨 Feature owner 协调

请选择:
1. ✅ **评审通过 · 进 blueprint** 💡 推荐(reviewers 已签 + 无受影响 owner 异议)
   动作:`panorama_sync-complete` → 自动转 blueprint
2. ⚠️ **要改 panorama 设计**
   动作:Designer 改 sitemap / summary · 重跑 reviewer
3. ❌ **回退:不改 panorama · 退本 Feature UI**
   动作:用户选 `jump-to-stage --to ui_design --reason ...` 重做 UI(不改 IA)
```

📚 决策参考:`panorama-change-summary.md` / `sitemap.md` diff / 受影响 Features 清单

### 5. complete
```
state.py panorama_sync-complete --feature <path> --auto-commit <hash> \
  --artifacts panorama-change-summary.md
```
state.py 校验:
- `sitemap.md` mtime > stage `started_at`(panorama 真被更新)
- `panorama-change-summary.md` 存在 + frontmatter 含 `reviewers` / `conclusion`
- 通过 → 自动转 `blueprint`

---

## 必读 cite 清单(P0-11)

| Substep | 必读 spec | 段 | cite 关键点 |
|---|---|---|---|
| 1. 加载上下文 | — | — | (读 UI/PRD/panorama · 无 spec cite) |
| 2. 更新 panorama 单源 | `roles/designer.md` | § panorama 同步 | sitemap 节点变更 + mtime 物化 |
| 3. 起草 summary | `roles/designer.md` + `roles/pm.md` | § 跨 Feature 影响评估 | reviewers / 受影响 Features / 协调结论 |
| 4. ⏸️ reviewer 评审 | — | — | (R5 暂停点) |
| 5. complete | — | — | (无) |

📎 **cite 纪律**详 [../STAGES.md § 2 P0-11 cite 纪律](../STAGES.md)。

## 质量基线

📎 **物化拦截**:
- **`sitemap.md` mtime > stage `started_at`** —— 没真更新 panorama 就 complete · evidence_check FAIL
- **`panorama-change-summary.md` 必存** —— frontmatter `reviewers` + `conclusion` 缺一即 FAIL
- 跨 Feature 影响 owner 未协调 → reviewer 应在 summary 留 `WARN concerns`(本 stage 不强阻 · 但 audit 有迹)

🔴 **本 stage 不修代码** —— 只动 panorama 单源 + summary 文档。代码改动在后续 dev stage 做。

🔴 **冷启动豁免**:若项目 panorama 初次建立(panorama_path 未存在 sitemap.md)· 本 stage 退化为「建 panorama」· `sitemap.md` mtime 校验仍走(刚 touch 即 mtime > stage_started_at)。

---

## Output Contract(产物形态参考)

### `panorama-change-summary.md`
- frontmatter:`reviewers: [pm, architect, ...]` · `conclusion: passed | needs-revision`
- body:§变更摘要 / §受影响 Features / §协调结论(每段 ≥ 2 行 · `body_min_lines: 8`)

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
