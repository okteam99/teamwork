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
APPROVE → 自动进 test · NEEDS_REVISION → ⏸️ 用户选回 dev 还是接受

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

## 注意事项

### 坑 1 · 三视角互相 cite(鼓掌效应)
Architect cite QA verdict → 三视角变一视角。
 **对策**:每视角独立 review · 各自落 REVIEW-{role}.md · 不互相参考

### 坑 2 · NEEDS_REVISION 绕过 dev 直接接受
问题被 PMO/用户合理化掉 · 隐藏 bug 进 test。
 **对策**:NEEDS_REVISION 默认回 dev 修 · 接受需用户明示 + concerns WARN 记录原因

### 坑 3 · External cross-review 漏
`external-cross-review/*.md` 为空 → P0-154 物化 FAIL。
 **对策**:必跑异质模型一次 · 即使 finding 少也要落 markdown

### 坑 4 · verdict APPROVE 隐藏 advisory finding
把"建议改进"标 APPROVE 不写 · review 失去价值。
 **对策**:APPROVE 可附 advisory(non-blocking)finding · 显式落 REVIEW.md · 留 audit

### 坑 5 · QA 只看 happy path 不查边界
PRD.AC 边界场景测试漏。
 **对策**:QA 必逐条 AC 对照 · 显式列"边界场景测试" finding

---

## Output Contract(产物形态参考)

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
- 入口规范:[../TRIAGE.md](../TRIAGE.md)
