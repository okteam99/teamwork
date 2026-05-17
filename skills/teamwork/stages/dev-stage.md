# Dev Stage

---

## 怎么做

### 1. 加载上下文(主对话 RD 身份)
读必读 artifact(brief 末尾给绝对路径):
- PRD.md(AC + 边界)
- TECH.md(技术方案 · Bug 流程跳过)
- TC.md(测试用例 · QA 起草)
- UI.md + preview/*.html(若 ui_design 完成)
- KNOWLEDGE.md / ARCHITECTURE.md(按需查)

### 2. TDD 红绿循环(逐 AC / 逐 test)
1. **红**:照 TC.md 中下一个 test 写测试代码 → 跑测试看红
2. **绿**:写最小化实现 → 跑测试看绿
3. **重构**(可选):改进设计 / 命名 / 抽象 · 测试仍绿
4. **auto-commit**:每个绿点一个 commit(commit message 含 Feature ID)

### 3. UI 还原(仅 ui_design 已完成)
触发条件:`state.stage_contracts.ui_design.output_satisfied == true`
- 跑 `verify-panorama.py` 或 `diff-html-vs-panorama.py`
- 对比实现 vs UI.md / preview/*.html
- 差异处:preview 未覆盖 → TECH.md fallback;TECH 也未覆盖 → concerns + 主对话讨论

### 4. 自查清单(实现完后跑)
- [ ] 规范符合(common.md / backend.md / frontend.md 对应)
- [ ] 跑已有测试无回归(`pytest` / `npm test` 等 · exit-code=0)
- [ ] build 通过(`make` / `npm run build` 等 · exit-code=0)
- [ ] linter pass(若项目有 · 如 `ruff` / `eslint`)
- [ ] commit message 含 Feature ID
- [ ] 改动文件全在 commit changeset 内

### 5. Bug fix 报告(flow_type=Bug 时)
落 `{Feature}/bugfix/BUG-XXX.md`:
- frontmatter:`bug_id` / `symptom` / `root_cause` / `fix_summary`
- body:§现象描述(重现步骤)/ §根因分析 / §修复方案 / §回归测试

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
| 1. 加载上下文 | — | — | (读 PRD/TECH/TC · 无 spec cite) |
| 2. TDD 红绿循环 | `standards/tdd.md + roles/rd.md` | § Iron Law + § TDD | 先红 → 后绿 → refactor / 每绿点 commit |
| 3. UI 还原(若 ui_design 完成) | `roles/designer.md` | § UI 还原校验 | verify-panorama / preview 未覆盖 → TECH fallback |
| 4. 代码自查清单 | `roles/rd.md + standards/common.md` | § 自查规范 | 规范 / 无回归 / build / linter |
| 5. Bug fix 报告(flow_type=Bug) | `roles/rd.md` | § Bug 排查报告 | bugfix/BUG-*.md frontmatter 4 字段 |
| 6. dev-complete | — | — | (无) |


📎 **cite 纪律**(输出格式 / 强约束 / 为什么 cite)· 单源详 [../STAGES.md § 2 P0-11 cite 纪律](../STAGES.md)

## 质量基线

📎 **物化拦截**:`verify-panorama.py`(UI 还原差异校验 · ui_design 完成时必跑)

**TDD SOP**(违反 → review NEEDS_REVISION):
- 严格红 → 绿 → refactor 顺序 · 每个 test 独立 commit(git log 可见 TDD 节奏)· 不"先实现后补测试"
- 每个绿点一个 commit · 一个 commit 一件事(便于 bisect)
- 测试失败必修 · skip 必含 reason + tracking issue(详 [test-stage 质量基线](./test-stage.md))

**TECH.md 模糊处 fallback 决策树**(不自行拍板 · 违反 → review 打回):
1. KNOWLEDGE.md(项目级约定) → 2. ARCHITECTURE.md(系统架构) → 3. standards/common.md(通用规范) → 4. 全无 → concerns INFO + 主对话找 architect

---

## Output Contract(产物形态参考)

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
- `{Feature}/bugfix/BUG-XXX.md` frontmatter 4 字段 + body 4 段

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `DEV_SPEC`
- TDD 权威:[../standards/tdd.md](../standards/tdd.md)
- 自查规范:[../standards/common.md](../standards/common.md)
- UI 还原工具:[../tools/verify-panorama.py](../tools/verify-panorama.py)
