# v8.0 命令 Schema 完整定义

> 所有 state.py 命令的精确 schema。实现时按此契约 1:1 编码。
> 共 25 命令 · 按职责分组。

---

## A 类 · 初始化(3 命令)

### A1 · `init-feature`

**职责**:创建 Feature state.json,落 artifact_root 目录。

**沿用 v7 现有实现**(state.py:1562-1589)。schema_version 字段更新为 `v8.0`。

```
state.py init-feature 
  --feature <绝对/相对路径>      必传 · feature 目录,state.json 落此处
  --feature-id <id>             必传 · 如 DEV-F001-example
  --flow-type {Feature|Bug|Micro|敏捷需求|Feature Planning|问题排查}   必传 · R2 闭集
  --merge-target <branch>       必传 · 如 staging
  --branch <branch>             必传 · 如 feat/dev-f001
  --sub-project <id>            可选
  --initial-stage <stage>       可选 · 缺省按 flow_type 决定
  --worktree-mode {auto|manual|off}   默认 off
  --worktree-path <abs>         worktree-mode != off 时建议提供
  --auto-mode                   启用 AUTO_MODE
  --force                       覆盖现有 state.json
```

**输出**:state.json 初始化骨架 + 输出 `next_action_brief` = "跑 triage 或 prepare"。

---

### A2 · `triage`(替代旧 init_triage.py + triage-stage.md)

**职责**:session 入口 5 mode 分诊。

```
state.py triage
  --user-input <字符串>         必传 · 用户原始输入
  --host {claude-code|codex-cli|gemini-cli|unknown}   必传
  --skill-root <path>           必传 · SKILL_ROOT 绝对路径
  --skill-version <version>     必传 · 校验是否最新
```

**内部判定**:
1. mode A (query) / B (execute) / C (resume) / D (status) / E (discuss) 五选一
2. mode B → emit "next: prepare"
3. mode C → 查找 state.json + emit "next: 当前 stage 的 -start"
4. mode A/D/E → emit 直接执行的 brief(不进 stage 链)

**输出**:audit_line + mode 判定 + 下一步命令。

---

### A3 · `prepare`(替代旧 prepare-stage.md)

**职责**:mode B 重型准备。

```
state.py prepare
  --feature <path>              必传 · 由 init-feature 提供
  --user-input <字符串>         必传 · 原始需求描述
```

**内部判定**:
1. 校验宿主环境(CLAUDE.md / AGENTS.md / GEMINI.md 注入段)
2. 校验 SKILL_VERSION 一致
3. 扫描 KNOWLEDGE.md / ADR(silent read)
4. 流程类型识别 → 写 state.flow_type
5. 创建 state.json 骨架(若 init-feature 已创建则跳过)
6. 创建项目级文档空骨架(KNOWLEDGE.md / TROUBLESHOOTING.md / GLOSSARY.md 若不存在)
7. emit 流程步骤描述 + 暂停点等用户确认

**输出**:`PMO 初步分析` markdown + 暂停点。

---

## B 类 · Stage 流转(20 命令 · 10 stage × 2)

### B1 · `goal_plan-start` / `goal_plan-complete`

#### `goal_plan-start`

**入口前置**:
```yaml
prerequisites:
  - id: prepare_completed
    check: state.completed_stages contains "prepare"
    hint: "先跑 state.py prepare --feature <path> --user-input <...>"
  - id: feature_initialized
    check: state.feature_id != null AND state.flow_type != null
    hint: "先跑 state.py init-feature"
```

**transition**:`* → goal_plan`(任何 stage 都能进 goal_plan,重 PRD 时需 --allow-revision)。

**next_action_brief**(PASS 时输出):
```markdown
## Goal-Plan Stage · 你要做什么

### Telos
PM 起草 PRD · PL-PM 讨论 · 多角色并行评审 · 收敛后用户确认。

### 必读 artifacts
1. {Feature}/teamwork-context.json (state.json snapshot · 自动生成)
2. PROJECT.md (产品全景) · 如存在
3. ROADMAP.md (Feature 优先级) · 如存在
4. KNOWLEDGE.md (项目级约定 + Gotcha)
5. GLOSSARY.md (业务术语) · 起草 PRD 前必读

### 子步骤
1. PM 起草 PRD 初稿 → {Feature}/PRD.md
2. PL-PM 讨论(角色切换 · 主对话)
3. 多角色并行评审(QA/architect 视角)
4. PM 回应 + 修订(NEEDS_REVISION 时循环)
5. 全员通过判定
6. ⏸️ 用户最终确认

### 必产物(goal_plan-complete 校验)
- {Feature}/PRD.md
  - YAML frontmatter 含 acceptance_criteria[].id (机读 AC)
  - body 含 §需求 / §用户场景 / §AC
- {Feature}/PRD-REVIEW.md
  - 含 QA review verdict + architect review verdict
- 至少 1 个 auto-commit hash
- (Feature Planning 流程) PROJECT.md / ROADMAP.md / sitemap.md 更新

### 完成方式
state.py goal_plan-complete --feature <path> --auto-commit <hash> 
                            --artifacts PRD.md,PRD-REVIEW.md
```

#### `goal_plan-complete`

**必产物校验**:
```yaml
artifacts:
  - path: PRD.md
    frontmatter_required: [acceptance_criteria]
    schema:
      acceptance_criteria: list[{id: str, description: str}]
  - path: PRD-REVIEW.md
    frontmatter_required: [reviewers, verdicts]
    body_min_lines: 20
evidence:
  - git_commit_exists: <auto-commit>
  - prd_md_in_commit: true
  - prd_review_md_in_commit: true
```

**自动副作用**:
- satisfy 三 gate
- enter-stage `legal_next`:
  - Feature 流程:有 UI 需求 → emit 暂停"选 ui_design 还是 blueprint"
  - Feature 流程:无 UI 需求 → 自动 enter blueprint
  - 敏捷需求:自动 enter blueprint_lite
  - Bug 流程:自动 enter dev
  - Planning:自动 enter completed(planning 流程只出文档)

---

### B2 · `ui_design-start` / `ui_design-complete`

#### `ui_design-start`

**入口前置**:
```yaml
prerequisites:
  - id: goal_plan_completed
    check: state.stage_contracts.goal_plan.output_satisfied == true
    hint: "先完成 goal_plan-complete"
  - id: prd_exists
    check: file {Feature}/PRD.md exists
    hint: "PRD.md 不存在 · 回 goal_plan stage 起草"
```

**next_action_brief**:
```markdown
## UI Design Stage

### Telos
Designer 产出 UI.md + HTML 预览稿 + sitemap 同步。

### 必读
- PRD.md(用户场景 + AC)
- sitemap.md(信息架构 · 如存在)
- KNOWLEDGE.md / GLOSSARY.md

### 子步骤
1. UI 设计稿(主对话或 Subagent · 按规模决定)
2. HTML 预览(preview/*.html)
3. sitemap 同步(全景 stage 触发条件 · 内部 silent)

### 必产物
- {Feature}/UI.md(YAML frontmatter 含 pages[].id)
- {Feature}/preview/*.html(每 page.id 对应一文件)
- sitemap.md 已同步(如适用)

### ⏸️ 暂停点
- 完成后给用户预览 URL · 等确认

### 完成方式
state.py ui_design-complete --feature <path> --auto-commit <hash>
                            --artifacts UI.md,preview/*.html
```

#### `ui_design-complete`

**必产物校验**:
```yaml
artifacts:
  - path: UI.md
    frontmatter_required: [pages]
  - path: preview/
    glob: "*.html"
    min_files: 1
    each_page_has_html: true  # UI.md pages[].id 全部有对应 .html
evidence:
  - git_commit_exists: <auto-commit>
  - all_html_in_commit: true
```

**自动副作用**:
- satisfy 三 gate
- 自动 enter blueprint

---

### B3 · `panorama_design-start` / `panorama_design-complete`

**仅 Feature Planning 流程触发**。

#### `panorama_design-start`

**入口前置**:
```yaml
prerequisites:
  - id: flow_type_is_planning
    check: state.flow_type == "Feature Planning"
    hint: "panorama_design 仅 Feature Planning 流程触发 · 当前 flow_type={state.flow_type}"
```

#### `panorama_design-complete`

**必产物**:
- PROJECT.md(产品全景 · 业务架构 + 执行手册)
- ROADMAP.md(Feature 列表)
- sitemap.md(信息架构)

**自动副作用**:enter completed(planning 不产生代码)。

---

### B4 · `blueprint-start` / `blueprint-complete`

#### `blueprint-start`

**入口前置**:
```yaml
prerequisites:
  - id: goal_plan_completed
    check: state.stage_contracts.goal_plan.output_satisfied == true
  - id: prd_exists
    check: file {Feature}/PRD.md exists
```

**next_action_brief**:
```markdown
## Blueprint Stage

### Telos
QA 起草 TC(测试用例 BDD)· RD 起草 TECH(技术方案)· 架构师 review · External 交叉评审。

### 必读
- PRD.md(权威需求)
- TECH 起草前必读:架构 ARCHITECTURE.md / 数据库 schema(如存在)
- TC 起草前必读:测试规约 standards/tdd.md(精简版)

### 子步骤
1. QA 起草 TC.md
2. RD 起草 TECH.md
3. 架构师 Tech Review(主对话 · 保留架构上下文)
4. QA TC Review(可选 · 复杂时启用)
5. External 交叉评审(blueprint-complete 必检 artifact 存在)
6. PM 回应循环(NEEDS_REVISION 时)

### 必产物
- {Feature}/TC.md(frontmatter.tests[].covers_ac 与 PRD.AC 一一绑定)
- {Feature}/TECH.md
- {Feature}/TECH-REVIEW.md(架构师 verdict)
- {Feature}/TC-REVIEW.md(如启用)
- {artifact_root}/external-cross-review/*.md(External 评审)

### 完成方式
state.py blueprint-complete --feature <path> --auto-commit <hash>
                            --artifacts TC.md,TECH.md,TECH-REVIEW.md,external-cross-review/*.md
```

#### `blueprint-complete`

**必产物校验**:
```yaml
artifacts:
  - path: TC.md
    frontmatter_required: [tests]
    schema:
      tests: list[{id: str, covers_ac: str, description: str}]
  - path: TECH.md
  - path: TECH-REVIEW.md
    frontmatter_required: [reviewer, verdict]
  - glob: external-cross-review/*.md
    min_files: 1     # External 评审至少 1 份 (v7.3.10+P0-154)
evidence:
  - git_commit_exists: <auto-commit>
  - all_artifacts_in_commit: true
ac_test_binding:
  - script: templates/verify-ac.py
    args: [--prd PRD.md, --tc TC.md]
    expect_exit: 0
```

**自动副作用**:enter dev。

---

### B5 · `blueprint_lite-start` / `blueprint_lite-complete`

**仅敏捷需求流程触发**(精简版 blueprint · 砍 TECH.md / 砍 architect review)。

#### `blueprint_lite-start`

**入口前置**:
```yaml
prerequisites:
  - id: flow_type_is_agile
    check: state.flow_type == "敏捷需求"
  - id: goal_plan_completed
    check: state.stage_contracts.goal_plan.output_satisfied == true
```

#### `blueprint_lite-complete`

**必产物**(精简版):
- TC.md(可选简化版 · 至少 1 个 test 覆盖每 AC)
- 不要求 TECH.md / TECH-REVIEW.md / External

**自动副作用**:enter dev。

---

### B6 · `dev-start` / `dev-complete`

#### `dev-start`

**入口前置**:
```yaml
prerequisites:
  - id: blueprint_or_lite_completed
    check: |
      state.stage_contracts.blueprint.output_satisfied == true OR
      state.stage_contracts.blueprint_lite.output_satisfied == true OR
      state.flow_type IN ("Bug", "Micro")  # Bug/Micro 直入 dev
    hint: "先完成 blueprint 或 blueprint_lite"
  - id: prd_or_bug_report_exists
    check: |
      file {Feature}/PRD.md exists OR
      file {Feature}/bugfix/BUG-*.md exists
    hint: "PRD.md 不存在(Feature)或 BUG-REPORT.md 不存在(Bug)"
  - id: ui_artifact_if_needed
    check: |
      state.stage_contracts.ui_design.output_satisfied != true OR
      file {Feature}/UI.md exists
    hint: "ui_design 已完成但 UI.md 缺失 · 异常 · 跑 ui_design-complete 重新校验"
```

**next_action_brief**:
```markdown
## Dev Stage

### Telos
按 TECH.md 实现代码 · TDD 红绿循环 · 单测全绿 · auto-commit · 自查通过。

### 必读
1. {Feature}/PRD.md          - 需求与 AC
2. {Feature}/TECH.md         - 技术方案(Bug 流程跳过)
3. {Feature}/TC.md           - 测试用例(QA 已起草)
4. {Feature}/UI.md + preview/*.html   - 如 ui_design 已完成 · UI 还原依据
5. KNOWLEDGE.md             - 项目级 Gotcha / Convention
6. ARCHITECTURE.md          - 系统架构(如涉及架构改动)

### 必跑工具(从 .teamwork_localconfig.md 读)
- 项目 build 命令
- 项目 test 命令
- linter / formatter

### TDD 循环
1. 写测试(红)
2. 实现代码(绿)
3. 重构(refactor)
4. auto-commit

### 必产物
- 代码改动 + 测试代码(一并 commit)
- 至少 1 次 auto-commit
- 测试全绿(test exit code = 0)
- 自查通过(roles/rd.md 自查清单编码到 dev-complete)

### UI 还原(如 ui_design 已完成)
- 必跑 verify-panorama.py 或 diff-html-vs-panorama.py
- preview 未覆盖的交互状态以 TECH.md 为准
- TECH 也未覆盖 → 加 concerns INFO

### 暂停点
- 无(dev stage 全自动)

### 完成方式
state.py dev-complete --feature <path> --auto-commit <hash>
                      --artifacts <src/*.py,tests/*.py>
                      --test-stdout <test-output.log>
                      --test-exit-code 0
```

#### `dev-complete`

**额外必传参数**:
```
--test-stdout <文件路径或字符串>   测试运行 stdout
--test-exit-code <int>             必须 = 0
```

**必产物校验**:
```yaml
artifacts:
  - paths_in_commit: true     # --artifacts 列出的全在 commit changeset 内
evidence:
  - git_commit_exists: <auto-commit>
  - test_exit_code: 0
  - test_stdout_non_empty: true
  - rd_self_check_passed: true  # 自查清单(规范符合 + 跑测试无回归)
```

**自动副作用**:enter review。

---

### B7 · `review-start` / `review-complete`

#### `review-start`

**入口前置**:
```yaml
prerequisites:
  - id: dev_completed
    check: state.stage_contracts.dev.output_satisfied == true
  - id: dev_test_passed
    check: state.stage_contracts.dev.evidence.test_exit_code == 0
    hint: "dev 测试未通过 · 回 dev stage 修"
```

**next_action_brief**:
```markdown
## Review Stage

### Telos
三视角独立评审:架构师 + QA + External(异质模型 codex/claude/gemini)。

### 必读(每视角独立)
- 架构师视角:TECH.md + ARCHITECTURE.md + 实际代码 diff
- QA 视角:PRD.AC + TC.md + 实际测试代码
- External 视角:全 artifact + 代码 diff

### 子步骤(并行)
1. 架构师 review → {Feature}/REVIEW-arch.md
2. QA review → {Feature}/REVIEW-qa.md
3. External review → {artifact_root}/external-cross-review/*.md
4. 汇合 → {Feature}/REVIEW.md(总结 + 处理建议)

### QUALITY_ISSUE 处理
- review.verdict = APPROVE → 继续
- review.verdict = NEEDS_REVISION → ⏸️ 暂停 · 用户选回 dev 还是接受

### 必产物
- {Feature}/REVIEW.md(总结 · verdict)
- {Feature}/REVIEW-arch.md
- {Feature}/REVIEW-qa.md
- {artifact_root}/external-cross-review/{review_id}.md

### 完成方式
state.py review-complete --feature <path> --auto-commit <hash>
                         --artifacts REVIEW.md,REVIEW-arch.md,REVIEW-qa.md
                         --verdict APPROVE|NEEDS_REVISION
```

#### `review-complete`

**额外必传**:
```
--verdict {APPROVE|NEEDS_REVISION}
--external-review-files <逗号分隔>   外部评审 markdown 文件清单
```

**必产物校验**:
```yaml
artifacts:
  - path: REVIEW.md
    frontmatter_required: [reviewers, verdict]
  - path: REVIEW-arch.md
  - path: REVIEW-qa.md
  - glob: external-cross-review/*.md
    min_files: 1
evidence:
  - all_review_perspectives_present: [architect, qa, external]
  - external_review_artifact_exists: true   # v7.3.10+P0-154 物化
```

**自动副作用**:
- verdict = APPROVE → enter test(legal_next 唯一)
- verdict = NEEDS_REVISION → emit 暂停"选回 dev 还是接受 + ship" · 不自动转移

---

### B8 · `test-start` / `test-complete`

#### `test-start`

**入口前置**:
```yaml
prerequisites:
  - id: review_approved
    check: state.stage_contracts.review.evidence.verdict == "APPROVE"
```

**next_action_brief**:
```markdown
## Test Stage

### Telos
QA 集成测试 + API E2E 脚本化。

### 必读
- PRD.AC + TC.md(测试用例)
- TECH.md(API 接口定义)

### 子步骤
1. 集成测试运行(项目 test 命令)
2. API E2E 脚本(QA 起草 + 跑)
3. 测试报告产出

### 必产物
- {Feature}/TEST-REPORT.md
- {Feature}/e2e/*.py(或语言对应文件)
- AC ↔ Test 全覆盖(verify-ac.py 通过)

### 完成方式
state.py test-complete --feature <path> --auto-commit <hash>
                       --artifacts TEST-REPORT.md,e2e/*
                       --integration-test-exit-code 0
                       --e2e-test-exit-code 0
```

#### `test-complete`

**额外必传**:
```
--integration-test-exit-code <int>   必须 = 0
--e2e-test-exit-code <int>           必须 = 0
```

**必产物校验**:
```yaml
artifacts:
  - path: TEST-REPORT.md
  - glob: e2e/*
    min_files: 1
evidence:
  - integration_exit_code: 0
  - e2e_exit_code: 0
ac_test_binding:
  - script: templates/verify-ac.py
    expect_exit: 0
```

**自动副作用**:
- 用户标记 browser_e2e 需要 → emit 暂停"启用 browser_e2e 还是跳到 pm_acceptance"
- 默认 → enter pm_acceptance

---

### B9 · `browser_e2e-start` / `browser_e2e-complete`

**仅显式启用时触发**(可选 stage)。

#### `browser_e2e-start`

**入口前置**:
```yaml
prerequisites:
  - id: test_completed
    check: state.stage_contracts.test.output_satisfied == true
```

#### `browser_e2e-complete`

**必产物**:
- 截图证据(screenshots/*.png)
- 浏览器测试报告

**自动副作用**:enter pm_acceptance。

---

### B10 · `pm_acceptance-start` / `pm_acceptance-complete`

#### `pm_acceptance-start`

**入口前置**:
```yaml
prerequisites:
  - id: test_completed
    check: state.stage_contracts.test.output_satisfied == true
```

**next_action_brief**:
```markdown
## PM Acceptance Stage

### Telos
PM 站在用户视角验收 + 给出三选项决策。

### 必读
- PRD.AC(逐条对照实现)
- TEST-REPORT.md
- 截图(如 browser_e2e 启用)

### ⏸️ 三选项暂停点
1. approved_and_ship       通过 + 自动进 ship
2. approved_no_ship        通过但暂不 ship(只 push feature 分支归档)
3. rejected_with_feedback  不通过 + 回 dev 修复

### 完成方式
state.py pm_acceptance-complete --feature <path> --auto-commit <hash>
                                --decision {approved_and_ship|approved_no_ship|rejected_with_feedback}
                                --note "<说明>"
```

#### `pm_acceptance-complete`

**额外必传**:
```
--decision {approved_and_ship|approved_no_ship|rejected_with_feedback}
--note <字符串>     (rejected 时必填)
```

**自动副作用**:
- approved_and_ship → enter ship
- approved_no_ship → enter completed(只 push 不 merge)
- rejected_with_feedback → emit 暂停"回 dev 还是放弃 Feature"

---

### B11 · `ship-start` / `ship-phase` / `ship-complete`

Ship Stage 内部多动作 · 三命令组合。

#### `ship-start`

**入口前置**:
```yaml
prerequisites:
  - id: pm_approved_and_ship
    check: state.stage_contracts.pm_acceptance.evidence.decision == "approved_and_ship"
    hint: "PM 决策非 approved_and_ship · 不进 ship · pm_acceptance-complete --decision 重选"
  - id: cwd_main_worktree
    check: cwd in main worktree (not linked)
    hint: "cd 到主工作区 · 不是 linked worktree(治本 P0-156)"
```

**自动副作用**:无(等待 ship-phase 推进)。

**next_action_brief**:
```markdown
## Ship Stage

### Telos
push feature → CLI 创建 MR → 等用户合并 → 验证 + 清理。

### Phase 1(连续动作)
1. ship-phase --action sanitize         净化 commit 记录(检查 residual)
2. ship-phase --action push             push feature 分支
3. ship-phase --action create-mr        CLI 优先(gh/glab)创 MR · 否则 URL 兜底

### ⏸️ Phase 1 → Phase 2 间断
- 输出 MR URL · 等用户在平台点 merge

### Phase 2
4. ship-phase --action confirm-merged   验证合入(git log origin/{merge_target})
5. ship-phase --action cleanup          删 worktree + 分支

### 异常路径
- ship-phase --action close-unmerged   MR 被关闭 / 用户放弃

### 完成方式
state.py ship-complete --feature <path>
   (无需 --auto-commit · 各 phase 已记录 commit)
```

#### `ship-phase`

```
state.py ship-phase
  --feature <path>                必传
  --action {sanitize|push|create-mr|confirm-merged|cleanup|close-unmerged}   必传
  
  # action=sanitize
  --residual-commits <JSON>       可选 · [{commit,files,reason}]
  --cleaned-files <逗号分隔>      可选
  
  # action=push
  --feature-head-commit <hash>    push 时必传
  --git-host {github|gitlab|gitlab-self-hosted|gitee|bitbucket|unknown}   必传
  --feature-pushed-at <ISO8601>   可选 · 默认 now
  
  # action=create-mr
  --mr-creation-method {cli-gh|cli-glab|url-fallback|unknown-platform}   必传
  --mr-url <url>                  cli-* 时必传
  --mr-create-url <url>           url-fallback 时必传
  
  # action=confirm-merged
  --merge-commit-hash <hash>      必传
  --merge-detection-method {branch-contains|user-reported}   必传
  --mr-merged-at <ISO8601>        可选
  --merge-target-pushed-at <ISO8601>   可选 · finalize-push 成功时
  --merge-target-push-failed      可选 · finalize-push 失败时
  --failed-reason {conflict|protect-rule|network|other}   失败时必传
  
  # action=cleanup
  --status {cleaned|deferred|n_a}   必传
  
  # action=close-unmerged
  --abandon                       彻底放弃 → shipped=abandoned
  --reason <字符串>               可选 INFO
```

**内部状态机**(沿用 v7 P0-156 物理拦截):
- linked worktree 拦截
- phase 转移合法性校验
- destructive op 前置 evidence

#### `ship-complete`

**入口前置**:
```yaml
prerequisites:
  - id: ship_phase_merged
    check: state.ship.phase == "merged"
  - id: cleanup_done
    check: state.ship.worktree_cleanup IN ("cleaned", "n_a")
```

**自动副作用**:
- satisfy 三 gate(ship-* phase 完成即满足 · v8 桥接)
- enter completed

---

### B12 · 终态 `completed`

无 -start / -complete 命令。由前一 stage 的 -complete 自动转移到 completed,即 Feature 流程结束。

---

## C 类 · 维护 / 逃生(5 命令)

### C1 · `recover`

沿用 v7。state.json 被外部改后重新认证 checksum + 写 concerns WARN。

### C2 · `snapshot`

沿用 v7。--tier {core|stage|full}。

### C3 · `validate`

沿用 v7,**强化**:跑全 schema + 状态机 + evidence-binding 全量校验。

### C4 · `raw-read` / `raw-write`

沿用 v7 逃生舱。必带 --reason 入 concerns WARN。

### C5 · `migrate-v7-to-v8`(新增 · 一次性迁移)

```
state.py migrate-v7-to-v8 --feature <path>
```

读 v7 state.json → 转换字段 → 写 schema_version=v8.0。

---

## 命令总数对照

| 类别 | v7 | v8 |
|------|-----|-----|
| 初始化 | 1(init-feature) | 3(init-feature / triage / prepare) |
| 状态流转 | 3 通用 + 5 ship | 20(10 stage × 2)+ 3 ship 子命令 |
| 维护 | 5 | 5 + 1 migrate |
| **总** | **18** | **~32** |

数量增,但每个命令语义专一,无歧义。

---

## 命令调用顺序示例(完整 Feature 流程)

```bash
# Day 0
state.py init-feature --feature docs/features/DEV-F001 ...
state.py triage --user-input "实现 X 功能" ...
state.py prepare --feature docs/features/DEV-F001 ...

# Goal-Plan
state.py goal_plan-start --feature ...
# AI 完成 PRD / Review
state.py goal_plan-complete --feature ... --auto-commit abc1

# (UI Design - 可选)
state.py ui_design-start --feature ...
state.py ui_design-complete --feature ... --auto-commit abc2

# Blueprint
state.py blueprint-start --feature ...
state.py blueprint-complete --feature ... --auto-commit abc3

# Dev
state.py dev-start --feature ...
state.py dev-complete --feature ... --auto-commit abc4 --test-exit-code 0

# Review
state.py review-start --feature ...
state.py review-complete --feature ... --auto-commit abc5 --verdict APPROVE

# Test
state.py test-start --feature ...
state.py test-complete --feature ... --auto-commit abc6 --integration-test-exit-code 0 --e2e-test-exit-code 0

# PM Acceptance
state.py pm_acceptance-start --feature ...
# 用户选 approved_and_ship
state.py pm_acceptance-complete --feature ... --decision approved_and_ship

# Ship Phase 1
state.py ship-start --feature ...
state.py ship-phase --action sanitize --feature ...
state.py ship-phase --action push --feature ... --feature-head-commit abc6 --git-host gitlab
state.py ship-phase --action create-mr --feature ... --mr-creation-method cli-glab --mr-url https://...
# ⏸️ 等用户合并

# Ship Phase 2
state.py ship-phase --action confirm-merged --feature ... --merge-commit-hash xyz --merge-detection-method branch-contains
state.py ship-phase --action cleanup --feature ... --status cleaned
state.py ship-complete --feature ...
# ✅ Feature 完成
```

**全程 AI 不需要 read 任何 SKILL.md / stages/*.md / roles/*.md** — 跑命令 + 读 stdout 即可。
