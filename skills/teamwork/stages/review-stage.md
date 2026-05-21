# Review Stage

---

## 怎么做

### 1. 加载上下文
读 PRD.md / TC.md / TECH.md / 实际代码 diff(git diff HEAD~N)

### 2. Architect 视角 review → REVIEW-arch.md
技术合理性 / 性能 / 安全 / 架构一致性 · 主对话默认

### 3. QA 视角 review → REVIEW-qa.md
AC 逐条对照实现 / 测试覆盖度 / 边界场景

### 4. External cross-review → external-cross-review/*.md
异质模型独立 review · 至少 1 份(P0-154)

### 5. 汇合 → REVIEW.md
frontmatter `reviewers + verdict: APPROVE|NEEDS_REVISION` · body §finding / §修复建议 / §verdict

### 6. complete --verdict
APPROVE → 自动进 test · NEEDS_REVISION → 留 review-stage · 走 fix-retry 循环(见 §fix-retry)

---

## fix-retry 循环(stage 内 · 治本回退切 stage 噪音 · v8.9)

review-stage 含 **stage 内 fix-retry 循环** · NEEDS_REVISION 不切 stage:

```
Round N: review-complete --verdict NEEDS_REVISION (写 rounds[-1].verdict)
  ↓ (current_stage 仍是 review · contract.evidence.verdict=NEEDS_REVISION)
RD 修代码 + commit (在 worktree 内)
  ↓
review-fix --auto-commit <hash> [--addresses-findings F1,F2]
  ↓ (写 rounds[-1].fix_commit + fix_at)
review-retry
  ↓ (rounds 加 round N+1 · 重置 contract gates · 清 evidence.verdict)
重新做评审(architect/qa/external)
  ↓
review-complete --verdict APPROVE | NEEDS_REVISION
  ↓ APPROVE → 自动转 test
```

**rounds[] 结构**(audit · 反映完整循环):
```json
"stage_contracts.review.rounds": [
  {"round": 1, "verdict": "NEEDS_REVISION", "review_commit": "C1",
   "fix_commit": "C2", "fix_at": "...", "addresses_findings": ["F1"]},
  {"round": 2, "verdict": "NEEDS_REVISION", "review_commit": "C3",
   "fix_commit": "C4", "fix_at": "...", "addresses_findings": ["F2","F3"]},
  {"round": 3, "verdict": "APPROVE", "review_commit": "C5",
   "fix_commit": null, "completed_at": "..."}
]
```

**为什么 stage 内循环**(v8.8 → v8.9 设计演进):
- v8.8 试 stage 间循环(review NEEDS_REVISION → 自动转 dev)· stage 切换 4 次/轮 · audit 噪音
- v8.9 改 stage 内循环 · 1 次 stage 切换/Feature(只在最终 APPROVE 时切 test)
- R1 红线不变:fix 由 RD 角色跑(review-fix 命令 · 角色仍是 RD · 只是物理 stage 在 review)
- 镜像 GitHub PR 工作流(review → push → 重审)· 业界标准

**命令清单**:
| 命令 | 用途 | 前置 |
|---|---|---|
| `review-complete --verdict NEEDS_REVISION` | 出本轮 verdict | 评审已落 REVIEW.md/REVIEW-arch.md/REVIEW-qa.md |
| `review-fix --auto-commit <hash>` | 记录 fix commit | rounds[-1].verdict=NEEDS_REVISION + rounds[-1].fix_commit=null |
| `review-retry` | 开新一轮 review | rounds[-1].fix_commit 已记录 |
| `review-complete --verdict APPROVE` | 终结 review-stage | 任意轮 verdict 通过 |

**与 dev-stage 的关系**:
- review-stage **只读 dev 的最终 commit**(进 stage 时)+ 后续每轮 fix commit
- dev-stage contract 不变(已 completed_stages)· 不重新走 dev-start/dev-complete
- 如果发现 dev 设计根本错(不是 finding 级 fix 能解决)· 用户用 `state.py reset-prev` 退到 dev 重做

---

## 必读 cite 清单(P0-11 · 各 substep 动手前主对话输出)

| Substep | 必读 spec | 段 | cite 关键点 |
|---------|----------|----|------------|
| 1. 加载上下文 | — | — | (读 PRD/TC/TECH + 实际代码 diff) |
| 2. Architect 视角 review → REVIEW-arch.md | `roles/architect.md` | § Code Review | 技术合理性 / 性能 / 安全 / 架构 |
| 3. QA 视角 review → REVIEW-qa.md | `roles/qa.md` | § Code Review | AC 逐条对照 / 测试覆盖 / 边界场景 |
| 4. External cross-review | `roles/external-reviewer.md` | § Cross-review 协议 | 异质模型独立 review |
| 5. 汇合 → REVIEW.md | — | — | (整合 · 无 spec cite) |
| 6. complete --verdict | — | — | (无) |


📎 **cite 纪律**(输出格式 / 强约束 / 为什么 cite)· 单源详 [../STAGES.md § 2 P0-11 cite 纪律](../STAGES.md)

## 质量基线

📎 **物化拦截**:P0-154(`external-cross-review/*.md` 非空 · 跨模型异质 review 必跑一次)

**多视角独立性 SOP**(违反 → review 失去价值):
- 每视角独立 review · 各自落 `REVIEW-{role}.md` · 不互相 cite verdict(避免鼓掌效应)
- APPROVE 可附 advisory(non-blocking)finding · 显式落 `REVIEW.md` 留 audit · 不隐藏

**QA 边界 SOP**:必逐条 AC 对照 · 显式列"边界场景测试" finding · 不只看 happy path

**NEEDS_REVISION 处理**:默认回 dev 修(in-stage fix-retry · R5 + fix-retry 规范)· 接受需用户明示 + concerns WARN 记录原因

---

## Output Contract(产物形态参考)

> 📋 **起草模板**(避免找历史 Feature 抄):
> - REVIEW.md / REVIEW-arch.md / REVIEW-qa.md → 无独立模板 · 见下方 schema · 各 reviewer 按视角分段
> - external-cross-review/*.md → `{SKILL_ROOT}/templates/external-cross-review.md` § 4 Output Schema(代码评审场景)

### `REVIEW.md`
frontmatter `reviewers + verdict` · §finding 汇总 / §修复建议 / §verdict

### `REVIEW-arch.md`
架构师视角 · 技术 / 性能 / 安全

### `REVIEW-qa.md`
QA 视角 · AC 对照 / 测试覆盖 / 边界

### `external-cross-review/*.md`
异质模型 · 至少 1 份

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `REVIEW_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
