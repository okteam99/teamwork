# v8.0+P0-1 · 暂停点纪律物化(L2 substep 链)

> ⚠️ **归档文档(v8.0 重构期蓝图)**:本文件是 v7→v8 重构期的设计/规划文档 · 描述当时的**计划态**。v8 已稳定至 v8.45 · 现行权威以 [SKILL.md](../../SKILL.md) + tools/state.py 实际行为为准。文内可能引用已失效的 RULES.md/TRIAGE.md(并入 SKILL.md)/ 旧 stage 名 / 旧命令。暂停点纪律已并入 SKILL.md § R5(b) + § ok 作用域 · 本文为早期推导稿。不再维护。


> 治本 PTR-F033 实战 case · L2 substep 链内部 AI 自觉区漏洞。
> v8.0 把可枚举规则全部物化,但 brief 输出后 AI 在 substep 链内的行为是 state.py 看不见的盲区。

---

## 实战 case 复盘(PTR-F033 · Partner Credit Note Adjustment)

### 违规过程

```
state.py goal_plan-start --feature ... 
  ↓ emit brief 含 6 substep + ⏸️ Substep 6 用户最终确认

PM 起草 PRD v0.1                              ← substep 1 ✅
↓
切角色到 PL · 评审 PRD · 发现 3 个 issue       ← substep 2 ✅
↓
❌ AI 主动调 AskUserQuestion 问 5 个 Open Q  ← 违规 · 未授权暂停
↓
用户回答 4 个决策
↓
修订 PRD → draft-v0.2                         ← substep 4(早于 substep 3)
↓
准备跑多角色 review                            ← substep 3(晚于 substep 4)
```

### 违规根因(权重排序)

| 权重 | 原因 | 修复优先级 |
|------|------|----------|
| 40% | brief 列了 substep 链 + 末尾暂停点,但**没明文写"中间禁暂停"** · AI 把"至少 substep 6 暂停"理解成"至少这一次"而非"只有这一次" | ⭐⭐⭐ |
| 25% | CLAUDE.md 红线 R5 全局可见 ≠ 执行时可见 · AI 在 stage 内只看 brief 不回头扫 CLAUDE.md | ⭐⭐ |
| 15% | AI 训练偏好"早问免错" · 默认习惯需要显式压制 | ⭐⭐ |
| 10% | PRD 模板含 "Open Questions" 段 · AI 当成"自然要问用户" | ⭐ |
| 10% | 省 round-trip 合理化 · "顺手问掉"覆盖纪律 | - |

### state.py 当时看见了什么

```
state.py 视角:
  goal_plan-start  → emit brief
  ........(AI 在 substep 链内的行为不可观测)
  goal_plan-complete --auto-commit X
  ← state.py 只能从 artifact 状态间接推断"过程是否合规"
```

**核心问题**:state.py 在 stage-start emit 后到 stage-complete 接收前的窗口里,
AI 完全自治。可枚举规则物化只到了"命令调用层",没到"substep 链内层"。

---

## v8.0+P0-1 治本三层修复

### Layer A · brief 内联暂停点纪律(预防)

**改动**:`tools/_v8_engine.py`
- `StageSpec` 加 `authorized_pause_point: str` 字段
- `execute_stage_start` 自动 append `_render_pause_discipline(...)` 段到 brief 末尾
- 所有 11 个 stage 的 SPEC 都填了 `authorized_pause_point`

**效果**:每次 stage-start emit 的 brief 末尾自动出现:
```
🔴 暂停点纪律(CLAUDE.md R5 物化)

本 stage 唯一授权暂停:<具体描述>

⛔ Substep 链中间 0 用户暂停点 · 0 AskUserQuestion · 0 "请确认"
⛔ Open Questions / 待决策项 不是用户暂停点 · 是 PRD/Review 的评审项
⛔ "节省 round-trip" "顺手问掉" "5 个开放问题阻塞" 不构成插暂停理由
✅ 所有疑问写进 PRD/REVIEW 文档 · 由多角色 review 评 · 到授权暂停点一次性 escalate

反模式黑名单(命中 = process 违规):
  ❌ substep 链中间 AskUserQuestion
  ❌ Open Questions 直接抛给用户
  ❌ "我有 N 个细节想跟你确认"
  ❌ "先问几个问题再做"
```

AI 在执行那一刻就看到红线 · 不需要回头扫 CLAUDE.md。

### Layer B · state.py 间接 evidence(事后兜底)

**改动**:`tools/_v8_stage_specs.py`
- 新增通用 evidence helpers:
  - `_evidence_review_after_primary(primary, review)` — review_artifact mtime > primary_artifact mtime
  - `_evidence_revision_history_present(artifact, min_revisions)` — frontmatter 含 revision_history
- 注入到 `GOAL_PLAN_SPEC.evidence_checks`:
  - `prd_review_after_prd` — PRD-REVIEW.md mtime > PRD.md mtime
  - `prd_revision_history` — PRD.md frontmatter 含 revision_history

**效果**:goal_plan-complete 时 state.py 校验:
- PRD-REVIEW mtime <= PRD mtime → FAIL + hint "substep 链可能被压缩 · 重做 review"
- PRD.md 缺 revision_history → FAIL + hint "添加 revision_history 字段"

**实证拦截**(从测试场景):
```json
"failed_evidence": [
  {
    "name": "prd_review_after_prd",
    "error": "PRD-REVIEW.md mtime <= PRD.md mtime · review 未在 PRD 落盘后发生 · substep 链可能被压缩 · 重做 review"
  },
  {
    "name": "prd_revision_history",
    "error": "PRD.md frontmatter 缺 `revision_history` 字段 · 无法证明 review 收敛过"
  }
]
```

### Layer C · 其他 stage 复制(后续 P0-2)

PRD/Review 模式可扩展到其他 stage:
- `BLUEPRINT_SPEC`:TC-REVIEW / TECH-REVIEW mtime > TC.md / TECH.md mtime
- `REVIEW_SPEC`:REVIEW.md mtime > 代码 commit mtime
- 全 stage 的 artifact 都可加 `revision_history` 校验

留待 v8.0+P0-2 推广。

---

## 设计哲学:三层物化模型

```
┌─────────────────────────────────────────────────────────────┐
│ L0 · 状态机层(stage 之间)                                  │
│      物化:legal_next_stages enum / 非法转移立即 FAIL        │
│      可见性:state.py 每次命令调用时校验                     │
├─────────────────────────────────────────────────────────────┤
│ L1 · 命令调用层(stage start/complete)                      │
│      物化:prerequisites + artifacts + evidence_checks        │
│      可见性:state.py 在命令边界校验                         │
├─────────────────────────────────────────────────────────────┤
│ L2 · substep 链内层(brief 输出到 stage-complete 之间)      │
│      物化方式:                                              │
│      - A 预防:brief 内联纪律(让 AI 实时看见)              │
│      - B 兜底:间接 evidence(事后从 artifact 状态推断)     │
│      可见性:state.py 看不见过程 · 只能从结果推断           │
└─────────────────────────────────────────────────────────────┘
```

L2 是 v8 最棘手的层 — state.py 不在场。修复策略只能是:
- **预防**(让 AI 在做决策那一刻看到规则)
- **事后兜底**(从间接证据反推过程是否合规)

不能"实时拦截"(那需要 state.py 介入 AI 的每一次 token 输出 · 不现实)。

---

## 防再次出现的反模式

这次违规暴露了一个常见 AI 行为模式:
> AI 倾向"早问免错" + 倾向"压缩 round-trip" + 倾向"合理化省事"

未来设计新 stage 或新 substep 时,**默认假设 AI 会插用户暂停点**,然后通过:
1. brief 明文反模式黑名单
2. state.py 间接 evidence
3. 必要时 PRD/Review frontmatter 强制 revision_history

来物化。

---

## 元规则总结

```
v8 凡新增 substep 链都必须同时定义:
  ✅ authorized_pause_point 字段(brief 自动 append 纪律)
  ✅ 至少一个间接 evidence check(事后兜底)
  ✅ 可选 frontmatter revision_history 强证据
```

这是 v8.0+P0-1 落地后的元规则,未来 stage 扩展都必须遵循。

---

## 相关

- 设计宪法:[00-MANIFESTO.md](./00-MANIFESTO.md)
- 命令 schema:[01-COMMAND-SCHEMA.md](./01-COMMAND-SCHEMA.md)
- 引擎代码:[../../tools/_v8_engine.py](../../tools/_v8_engine.py) `_render_pause_discipline()` + `StageSpec.authorized_pause_point`
- evidence helpers:[../../tools/_v8_stage_specs.py](../../tools/_v8_stage_specs.py) `_evidence_review_after_primary()` + `_evidence_revision_history_present()`
