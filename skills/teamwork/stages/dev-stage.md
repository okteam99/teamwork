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

- **`same-stack`** —— 真渲染 diff(项目自身 `/design/<page-id>` 路由 vs live 实现 · 同栈像素级 fidelity 由构造保证):
  - 跑项目自有 visual regression(storybook diff / playwright screenshot / chromatic 等)· teamwork 尚未提供统一同栈 diff 工具(后续 Feature)
  - 差异 → 修代码 或 修 design route + mock data
- **`static-html`** —— IA + 视觉层级 + Token 一致性校验(不强像素 · 介质差异不可调和):
  - 跑 `verify-panorama.py`(已 medium-aware · 同栈下自动 skip HTML 检查 · 不卡流程)或 `diff-html-vs-panorama.py`
  - 对比实现 vs `UI.md` / `preview/*.html`
  - 差异处:preview 未覆盖 → TECH.md fallback;TECH 也未覆盖 → concerns + 主对话讨论
  - 🔴 **不要在 static-html 上死磕像素级 fidelity** —— 介质差异(系统字体 / CDN Tailwind / shadcn token 缺失)无法靠调 panorama 解决,治本是迁 same-stack(详 ui-design-stage.md § Panorama 介质类型)

### 4. 自查清单(实现完后跑)
- [ ] 规范符合(common.md / backend.md / frontend.md 对应)
- [ ] 跑已有测试无回归(`pytest` / `npm test` 等 · exit-code=0)
- [ ] build 通过(`make` / `npm run build` 等 · exit-code=0)
- [ ] linter pass(若项目有 · 如 `ruff` / `eslint`)
- [ ] commit message 含 Feature ID
- [ ] 改动文件全在 commit changeset 内

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
| 4. 代码自查清单 | `roles/rd.md + standards/common.md` | § 自查规范 | 规范 / 无回归 / build / linter |
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
