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

### 3. 多角色并行评审 → PRD-REVIEW.md
- QA 视角:测试覆盖性 / 边界场景 / AC 可测试性
- Architect 视角:技术可行性 / 架构影响 / 性能安全
- (可选)External Reviewer:异质模型 cross-review
- 落 `{Feature}/PRD-REVIEW.md` · frontmatter 含 `reviewers` + `verdicts: {role: APPROVE|NEEDS_REVISION}`

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

### 7. ⏸️ 用户最终确认
- 一次性 escalate 剩余开放问题给用户(若有)
- 用户回 ok 后跑 complete · state.py 按 --needs-ui 自动转移

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


**输出格式**(每个 substep 动手前必在主对话输出):
```
📖 cite:
- <spec> § <段>:"<引该段 1 句关键原文 · 证明真读>"
```

**强约束**(R5+P0-11 软约束 · 用户监督):
- 标 "—" 的 substep 无 cite 要求(状态机操作 / 用户暂停 / 已物化)
- 其余 substep **动手前必输出 cite 块** · 缺 cite 视为 process 违规(用户可叫停)
- cite 必含 § 段标题 + 至少 1 句原文(原文必真实存在于该 spec · 不可瞎编)
- AI 在 stage 内多次切角色 · 每次切换前重新 cite 该角色规范

**为什么 cite**:
- brief 列路径(P0-4)只解决"AI 找不到路径"· 不保证 AI 真读
- complete 时校验太晚(AI 已做完)
- substep 动手前 cite = 事前提醒 · 强制 AI 翻一眼 spec
- 物化死角(state.py 看不到 markdown Read 动作)· 软约束 + 用户监督兜底

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

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py) `execute_stage_start` / `execute_stage_complete`
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `GOAL_SPEC`
- 入口规范:[../TRIAGE.md](../TRIAGE.md)
- 治本反思:[../docs/v8-redesign/05-LESSONS-FROM-PTR-F033.md](../docs/v8-redesign/05-LESSONS-FROM-PTR-F033.md)
