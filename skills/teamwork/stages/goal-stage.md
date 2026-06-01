# Goal Stage

---

## 怎么做

### 1. PM 起草 PRD 初稿(主对话 PM 身份)
- 落 `{Feature}/PRD.md`
- frontmatter 必含 `acceptance_criteria` 数组 + `revision_history` 数组(可空 · 后续填)
- body 含 §需求背景 / §用户场景 / §AC / §边界与非目标
- AC 写成 BDD 风格(Given/When/Then) · 避免 "应该 / 可以 / 大概" 模糊措辞
- §Open Questions 写下未决项(**不向用户问** · 留给 review 评)

### 2. PL-PM 讨论(主对话角色切换)
- 切到 PL 视角 · 审视 PRD 业务方向
- PL finding 直接追加到 PRD 内对应 AC 后注释(不开新文件)

🔴 **PRD 评审聚焦(高度对齐)**:PRD 评的是 **① 业务目标清晰**(为谁 · 解决什么 · 价值)+ **② 当前环境下可实现**(架构 / 技术约束内能落地)+ **③ 方案合理且恰当简洁**(无过度设计 · 责任在对的层)。AC 写在「**行为 / 价值**」高度(WHAT)· **不下沉到实现机制细节**(字段解析 / 校验闸 / 内部数据结构 —— 那是 blueprint/dev 的事 · 且应保持最小)。`§边界与非目标` 用足「**非目标**」主动收窄(写清「**不做什么 / 不归我管什么**」= 防过度设计第一道闸)。

### 3. 多角色并行评审 → PRD-REVIEW.md
- **必含 5 角色**(state.stage_review_roles[goal] · _v8_stage_specs.py _evidence_reviewers_match 强制)· 缺角色 → goal-complete FAIL:
  - PM 视角:需求清晰度 / AC 完整性
  - QA 视角:测试覆盖性 / 边界场景 / AC 可测试性
  - Architect 视角:技术可行性 / 架构影响 / 性能安全 / **方案简洁性(是否过度设计 · 职责是否归错层 · 能否更简单达成业务目标)** —— 🔴 唯一的**简洁性 counter-lens**(详 `roles/architect.md` Telos)
  - PL 视角:业务方向 / 路线图对齐
  - External Reviewer:**跑** `state.py external-review --feature ... --stage goal`(v8.20+ 物化主路径 · host/model/profile 全自动 · 落 `external-cross-review/goal-<model>.md` · 详 standards §十一)
- 🔴 **external finding 须对照业务目标 + 简洁性取舍**:external review 天然「找缺口 → 加校验」· **每条**单看都合理 · 合起来却可能把方案做臃肿 / 把责任焊进错层。采纳「修真 bug / 真业务缺口」的 · 用 Architect 简洁性视角挡住「为 rigor 而 rigor」的复杂度(实证 SDK-F038:盲采 external 的显式校验 / 字段解析 → SDK 哑管道变复杂 · pm_acceptance 才被用户揪出回炉)。
- 落 `{Feature}/PRD-REVIEW.md` · frontmatter `reviewers: [pm, qa, architect, pl, external]` + `verdicts: {role: APPROVE|NEEDS_REVISION}`

### 4. PM 回应 + 修订 PRD
- 逐条响应 review finding
- 修订 PRD → draft-v0.2 / v0.3 ...
- PRD.frontmatter.revision_history 追新条目(版本号 + 修订理由)
- NEEDS_REVISION 时循环 · 直到全员 APPROVE

### 5. 全员通过判定
- 所有 reviewer verdict = APPROVE(或 SKIP)
- 若仍有 NEEDS_REVISION → 回 step 4

### 6. PM 决策 `--needs-ui`(complete 前必)
- 基于 PRD 内容判定是否需要独立 UI Design Stage
- 准备 `state.py goal-complete --needs-ui {true|false} ...`

### 7. ⏸️ 用户最终确认(R5 暂停点)
🔴 **`auto_mode=true` 时跳过此暂停点** —— PRD 已经多角色 review 内化 · auto 用户接受(详 [SKILL.md § auto_mode=true 时各暂停点行为](../SKILL.md))。

🔴 emit R5 标准 1/2/3(模板见 [SKILL.md § R5(b)](../SKILL.md))· 一次性 escalate 剩余 Open Questions:
1. **确认 PRD · 进入下一 stage** 💡 推荐 — `goal-complete --needs-ui <true/false>` → 自动转 ui_design/blueprint
2. **还要改 PRD** — PM 按你的反馈修订 PRD · 重走多角色评审
3. **其他指示**

用户选 1 后跑 complete · state.py 按 `--needs-ui` 自动转移。

---

## 必读 cite 清单(P0-11 · 各 substep 动手前主对话输出)

| Substep | 必读 spec | 段 | cite 关键点 |
|---------|----------|----|------------|
| 1. PM 起草 PRD 初稿 | `roles/pm.md` | § 创作要点 | PRD 必含 AC + 边界 / Open Questions 不抛用户 |
| 2. PL-PM 讨论 | `roles/product-lead.md` | § 与 PM 协作 | 业务方向审视规则 |
| 3. 多角色并行评审 → PRD-REVIEW.md | `roles/qa.md + roles/architect.md` | § Review 规范 | QA 看测试覆盖性 / Architect 看技术可行 |
| 4. PM 回应 + 修订 PRD | `roles/pm.md` | § PRD 修订 | revision_history 必落 frontmatter |
| 5. 全员通过判定 | — | — | (无 cite 要求) |
| 6. PM 决策 --needs-ui | `stages/goal-stage.md` | § 特殊规则 1 | --needs-ui 决策 · 不传则 FAIL |
| 7. ⏸️ 用户最终确认 | — | — | (无 cite 要求) |


📎 **cite 纪律**(输出格式 / 强约束 / 为什么 cite)· 单源详 [../STAGES.md § 2 P0-11 cite 纪律](../STAGES.md)

## 质量基线

📎 **物化拦截**:
- `--needs-ui` × flow_type 校验(敏捷需求 / Feature Planning + `--needs-ui=true` → FAIL)
- P0-1 evidence_check:`PRD-REVIEW.md` mtime 必晚于 `PRD.md` + `PRD.frontmatter.revision_history` 数组非空

**PRD SOP**(违反 → review NEEDS_REVISION):
- AC 必 BDD 风格(Given X / When Y / Then Z)· 不写"应该流畅 / 用户友好"等不可测描述
- 每轮 NEEDS_REVISION 后修订 · 加 1 条 `revision_history` 记录(版本号 + 修订理由)
- substep 链中禁 AskUserQuestion · Open Questions 写进 `PRD.§Open Questions` · Substep 7 一次性 escalate

---

## Output Contract(产物形态参考)

> 📋 **起草模板**(避免找历史 Feature 抄):
> - PRD.md → `{SKILL_ROOT}/templates/prd.md`
> - PRD-REVIEW.md → 无独立模板 · 见下方 schema · 各 reviewer 自由分段

### `PRD.md`
- frontmatter:
 - `acceptance_criteria: [{id, description}]`(必)
 - `revision_history: [{version, date, changes}]`(必 · 至少 1 条)
- body:§需求 / §用户场景 / §AC(BDD)/ §边界 / §Open Questions(可空)

### `PRD-REVIEW.md`
- frontmatter:
 - `reviewers: [pm, qa, architect, ...]`
 - `verdicts: {role: APPROVE|NEEDS_REVISION|SKIP}`
- body ≥ 20 行 · 每 reviewer 单独段 · cite PRD 行号

### `external-cross-review/goal-<model>.md`(若启用)
- **跑** `state.py external-review --feature ... --stage goal`(v8.20+ 自动落产物 · 不要手写)· 详 [standards/external-model-usage.md §十一](../standards/external-model-usage.md)。

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py) `execute_stage_start` / `execute_stage_complete`
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `GOAL_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
- 治本反思:[../docs/v8-redesign/05-LESSONS-FROM-PTR-F033.md](../docs/v8-redesign/05-LESSONS-FROM-PTR-F033.md)
