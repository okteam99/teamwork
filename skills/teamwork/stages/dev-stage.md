# Dev Stage

---

## 怎么做

### 1. 加载上下文(主对话 RD 身份)
读必读 artifact(brief 末尾给绝对路径):
- PRD.md(AC + 边界)
- TECH.md(技术方案 · Bug 流程跳过)
- 🔴 **flow_type=Bug**:读 `bugfix/BUG-*.md`(diagnose 阶段已产出并**经用户确认**的 §根因 + §修复方案)= 本阶段**权威输入** · 按确认的方案写 fix(详 [diagnose-stage.md](./diagnose-stage.md))
- TC.md(测试用例 · QA 起草)
- UI.md + preview/*.html(若 ui_design 完成)
- 🔴 `project-specs/DEV-RULES.md`(存在则**必读** · 本项目强制开发规范:分层 / 命名 / 错误处理 / 依赖方向 / 测试策略 / 风格)· 实现**须遵守**(不存在 → skip · 人维护 doc 可能未建)
- KNOWLEDGE.md(项目踩坑/事实)/ ARCHITECTURE.md(按需查)

### 1.5 组织实现(🧩 subagent 可选 · 按需并行 · 非必须)

多端 / 多模块 / 多独立文件的 dev(如 Android + iOS + JSSDK)· **可**派 subagent(`Agent` 工具)各做一块并行落地;主对话 RD 留**契约层 / 集成点**自己写(保对齐基准)+ 收口集成。

- ⚠️ **可选非默认**:单模块 / 强耦合 / 文件少的 dev 直接自己串行做 —— subagent 有 context 切换 + 协调 + 结果校验开销 · 滥用反碎片 + 拖慢。**判据:子任务相互独立且够大才值得拆**。
- 子 agent 写文件守 **worktree 内路径**(同 worktree 纪律 · 防污染主工作区);stage 流转 / commit / dev-complete 仍由**主对话**掌控(不外包整个 stage 跳流程)。

### 2. TDD 红绿循环(逐 AC / 逐 test)
1. **红**:照 TC.md 中下一个 test 写测试代码 → 跑测试看红
2. **绿**:写最小化实现 → 跑测试看绿
3. **重构**(可选):改进设计 / 命名 / 抽象 · 测试仍绿
4. **auto-commit**:每个绿点一个 commit(commit message 含 Feature ID)

### 3. UI 还原(仅 ui_design 已完成 · 按 panorama_medium 分支)
触发条件:`state.stage_contracts.ui_design.output_satisfied == true`

按 `UI.md` frontmatter `panorama_medium` 走:

- **`same-stack`** —— 分层对照(详 [ui-design-stage § 分层同构律](./ui-design-stage.md) · 旧「in-app /design 路由 diff」模型已废):
  - **Layer 1 基建**:实现**复用共享包**(packages/ui · theme · shell)· 🔴 不在真实 app 里复制/重写全景已用的基建(发现全景用了未共享的基建 → 先抽包/对齐)
  - **Layer 2 页面**:对齐**意图四要素**(布局结构 / 交互流 / 状态〔normal·empty·loading·error〕/ 字段映射 · 以 UI.md + 全景页为准)· 像素与代码组织自由 · **非字节还原**
  - 🔴 **设计↔实际 一致性核对(必做 · 非可选 · 治「设计稿和实际不一致」)**:起全景 dev server(preview.sh)+ 跑真实 app 目标路由 → **两边同开、browse 截图并排核对**意图四要素(布局结构 / 交互流 / 状态〔normal·empty·loading·error〕/ 字段映射)· 🔴 **逐要素给「一致 / 背离」结论**(不许「看一眼就过」· 截图存 `${TMPDIR:-/tmp}/teamwork/<feature_id>/screenshots/` · 非交付)· 核对的是**四要素不是像素**(像素自由 · 非字节还原)· 视觉回归工具(playwright screenshot diff)= 可选增强,**结构核对必做**。
  - 差异处置:四要素不一致 → 修实现;认为设计本身要改 → 🔴 不在 dev 顺手改 · 走 `--panorama-changed` / 回 ui_design(设计变更须重新对齐)· 🔴 **背离不许静默放过**(修掉 or 留 concerns · 这道核对就是「设计稿=实际效果」的落地闸)

### 3.5 共享基建变更 → 全景编译契约(条件必跑 · v8.134)

**触发**:本 feature diff 触及**全景的依赖**(preview-project workspace 依赖的共享包 · 如 packages/ui / theme / shell —— 读 preview-project `package.json` workspace 依赖与 diff 路径求交)。未触及 → 跳过本节。

**动作**(dev-complete 前 · worktree 内):
```bash
cd {子项目}/docs/design/preview-project && pnpm build   # 或项目等价 build/typecheck · exit 0 = 契约满足
```

**失败处置**:
- 基建 API 变更导致的**机械适配**(改全景页用法 · 不改设计语义)→ 本 feature 内顺手修(合法 · UI.md 变更记录 +1 行)
- 适配引发**视觉/交互变化** → 那是设计变更 · 走 `--panorama-changed=true` / panorama_sync(🔴 不可静默)
- 不想适配 → 收回破坏性基建改动 —— **改 API 者负责迁移所有消费者**(同 backend §五 Schema 影响分析的责任模型 · 全景是消费者之一)

**证据**:build exit 0 记入 dev 测试证据(同 §6 test evidence 模式)。⏳ 物化 TODO:dev-complete 条件 evidence(diff ∩ 共享包路径 → 要求 `--panorama-build-exit-code`)。
- **`static-html`** —— IA + 视觉层级 + Token 一致性校验(不强像素 · 介质差异不可调和):
  - 跑 `verify-panorama.py`(已 medium-aware · 同栈下自动 skip HTML 检查 · 不卡流程)
  - 对比实现 vs `UI.md` / `preview/*.html`
  - 差异处:preview 未覆盖 → TECH.md fallback;TECH 也未覆盖 → concerns + 主对话讨论
  - 🔴 **不要在 static-html 上死磕像素级 fidelity** —— 介质差异(系统字体 / CDN Tailwind / shadcn token 缺失)无法靠调 panorama 解决,治本是迁 same-stack(详 ui-design-stage.md § Panorama 介质类型)

### 4. 完工自查(🔴 实现完 · 在 `TECH.md` 末尾 §完工自查 **文档内逐项打 ✅**)
不只读清单 —— **在 TECH.md 的 §完工自查 段逐项打钩**(每项 ✅ 指向证据:测试名/文件/编译结果 · 不适用写 `N-A + 原因`)· review 据此核。该清单**对着本 TECH 的设计逐条**:
- 设计落地:现状基线前提仍成立 · §错误处理每条失败路径实现 · §依赖与影响**消费方都同步改**(`tsc -b`/编译零报错)· §数据结构跨层一致 · §数据库变更 migration 实跑 · §测试策略**集成/契约测试写了**(不只单测)
- 通用门:规范(DEV-RULES/common/backend/frontend)· 无回归(exit-code=0 · 红 base 走 `test-baseline` 差分)· build · linter · commit 含 Feature ID · 改动全在 changeset
- (UI feature)**设计↔实际一致性核对**(意图四要素 · §3)
- 🔴 **专防「设计了没实现」**。强门禁(test exit-code / verify-ac / external-review)仍是硬墙;本清单是**完整性自证**(soft · review 验 · 非橡皮图章)。

### 5. Bug fix 报告(flow_type=Bug 时 · 🔴 §现象/§根因/§修复方案 diagnose 已写并确认 · 不重写)
在 diagnose 已创建的 `bugfix/BUG-*.md` **追加** dev 产出:
- §回归测试(原 bug 不复发 + 周边无新错)+ §修复记录(按已确认的 §修复方案写 fix · 偏离方案要回 diagnose 复议)
- 🔴 **不重写 §根因/§修复方案**(那是 diagnose 经用户确认的产物)· 真发现根因判错 → `jump-to-stage --to diagnose` 复议

### 6. dev-complete(必传测试 evidence)
```
state.py dev-complete --feature <path> \
 --auto-commit <hash> \
 --artifacts <逗号分隔改动文件> \
 --test-stdout <log 文件路径 或 字符串> \
 --test-exit-code 0
```
state.py 校验:
- auto-commit 在 git history(`git cat-file -e`)
- artifacts 在 commit changeset 内
- test-stdout 非空
- test-exit-code = 0

---

## 必读 cite 清单(P0-11 · 各 substep 动手前主对话输出)

| Substep | 必读 spec | 段 | cite 关键点 |
|---------|----------|----|------------|
| 1. 加载上下文 | `project-specs/DEV-RULES.md`(若存在) | 全文 | 项目强制开发规范 · 实现须遵守(+ 读 PRD/TECH/TC) |
| 2. TDD 红绿循环 | `standards/tdd.md + roles/rd.md` | § Iron Law + § TDD | 先红 → 后绿 → refactor / 每绿点 commit |
| 3. UI 还原(若 ui_design 完成) | `roles/designer.md` | § UI 还原校验 | verify-panorama / preview 未覆盖 → TECH fallback |
| 4. 完工自查 | `TECH.md §完工自查` + `roles/rd.md` | § 自查规范 | 在 **TECH 文档内逐项打 ✅**(对着设计:现状基线/错误处理/依赖消费方/测试策略 + 通用门)· review 据此核 |
| 5. Bug fix 报告(flow_type=Bug) | `roles/rd.md` | § Bug 排查报告 | bugfix/BUG-*.md frontmatter 4 字段 |
| 6. dev-complete | — | — | (无) |


📎 **cite 纪律**(输出格式 / 强约束 / 为什么 cite)· 单源详 [../STAGES.md § 2 P0-11 cite 纪律](../STAGES.md)

## 质量基线

📎 **物化拦截**:`verify-panorama.py`(UI 还原差异校验 · ui_design 完成时必跑)

🔴 **worktree 写文件纪律**:worktree 模式下代码改动一律写 **worktree 内**(推荐绝对路径)· 相对路径会落主工作区污染其他并行 Feature · 详 [SKILL.md § worktree 纪律](../SKILL.md)。

**TDD SOP**(违反 → review NEEDS_REVISION):
- 严格红 → 绿 → refactor 顺序 · 每个 test 独立 commit(git log 可见 TDD 节奏)· 不"先实现后补测试"
- 每个绿点一个 commit · 一个 commit 一件事(便于 bisect)
- 测试失败必修 · skip 必含 reason + tracking issue(详 [test-stage 质量基线](./test-stage.md))

**TECH.md 模糊处 fallback 决策树**(不自行拍板 · 违反 → review 打回):
1. KNOWLEDGE.md(项目级约定) → 2. ARCHITECTURE.md(系统架构) → 3. standards/common.md(通用规范) → 4. 全无 → concerns INFO + 主对话找 architect

---

## Output Contract(产物形态参考)

> 📋 **起草模板**(避免找历史 Feature 抄):
> - 代码改动 → 无文档模板(纯实现 · 按 TECH.md 设计)
> - Bug fix 报告(`{Feature}/bugfix/BUG-XXX.md`)→ `{SKILL_ROOT}/templates/bug-report.md`(flow_type=Bug 时必用)

### 代码改动
- 源代码 + 测试代码一并 commit
- artifacts 列表用 `--artifacts` 传 · state.py 校验文件在 commit 内

### auto-commit(锚定证据)
- commit message 必含 Feature ID(如 `feat(login): add OAuth (PTR-F033)`)
- multiple commits 允许 · 但 `--auto-commit` 传 stage 最终 head commit

### test evidence
- `--test-stdout` 文件路径或 stdout 内容 · 非空
- `--test-exit-code 0` 必传 · 必 = 0

### Bug fix 报告(flow_type=Bug)
- `bugfix/BUG-*.md`(diagnose 已建 · 含 §根因/§修复方案)· dev **追加** §回归测试 + §修复记录(不重写根因/方案)

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `DEV_SPEC`
- TDD 权威:[../standards/tdd.md](../standards/tdd.md)
- 自查规范:[../standards/common.md](../standards/common.md)
- UI 还原工具:[../tools/verify-panorama.py](../tools/verify-panorama.py)
