# Review Stage

---

## 怎么做

### 1. 加载上下文
读 PRD.md / TC.md / TECH.md / 实际代码 diff(git diff HEAD~N)

### 2. Architect 视角 review → REVIEW-arch.md
技术合理性 / 性能 / 安全 / 架构一致性 + **方案简洁性(防过度设计)** · 主对话默认
🔴 Architect 是唯一**简洁性 counter-lens**(QA/external 都偏加 rigor):查「实现是否把不该管的复杂度焊进核心抽象 · 能否更简单 · 职责是否归错层(可删 / 可下沉正确 owner)」· external finding 别盲采(对照业务目标 + 简洁性取舍 · 详 `roles/architect.md` Telos)

### 3. QA 视角 review → REVIEW-qa.md
AC 逐条对照实现 / 测试覆盖度 / 边界场景

### 4. External cross-review → external-cross-review/review-<model>.md
**跑** `state.py external-review --feature <path> --stage review`(host/model/profile 全自动 · 异质性硬约束物理墙 · 至少 1 份 · P0-154)。详 [standards/external-model-usage.md §十一](../standards/external-model-usage.md)。

🔴 **同步 · 慢 · 别提前 kill**:external-review **同步阻塞**跑(timeout 600s · claude 路径 = 纯 `claude -p <自包含 prompt>` 一次性生成 · 无工具 / 无 doc 模式 / 无 liveness 文件)· 真实评审常 **30s–3min**(模型并发 / 限流更久 · `claude -p` 会静默无输出)。**前台跑、耐心等满 600s · 不要中途 kill**。
- **真超时 / 空输出 = `verdict: FAIL`(门禁未达)· 不是放行**:🔴 **禁止**伪造 `tool_error` 文件、或把 external 自列进 REVIEW.md `reviewers` 当通过。按 FAIL 的 hint 串行重跑(并发会限流);**串行重跑仍超时/空输出**(限流/配额/网络等环境性原因)→ 归入下一条「异质客观不可用 · 已重试失败」走**显式降级**(合法继续路径 · 同时报因给用户留痕)。🔴 **不得**绕过 P0-154 —— 禁的是「伪造/冒充/静默跳过」· 不是降级协议本身。
- **异质客观不可用(未装/未登录/配额满/持续超时限流 · 已重试失败)→ 降级 subagent 自审(v8.108 · 降级优先于移除)**:`state.py external-review ... --self-review-fallback --reason '<原因+重试证据>'` → **emit subagent 配方**(🔴 不再 exec CLI · PMO 起 `Agent` subagent 同模型自审 · harness 内跑 · 治本 exec 反复出认证/卡死)→ 写 `external-cross-review/<stage>-<model>-subagent-degraded.md`(frontmatter `heterogeneous:false degraded:true degraded_mode:subagent-fallback degraded_reason:'...'`)· **满足 P0-154**(降级 · 让你继续)· 非异质 · 同盲点。能修环境就重跑真异质;🔴 **绝不偷偷**用 subagent 冒充异质(必显式标 degraded)。详 [standards/external-model-usage.md §11.5](../standards/external-model-usage.md)。

### 5. 汇合 → REVIEW.md(🔴 汇总层 · 不是合并:arch/qa/external 三份产物都要独立留盘)
REVIEW.md 是 REVIEW-arch.md + REVIEW-qa.md + external-cross-review/*.md **之上**的汇总 · **不替代**它们(三份独立产物是 P0 门禁硬要求 · 原因:多视角独立性 SOP · 各视角各自落盘防鼓掌效应 · 详 §质量基线)。🔴 别把三视角揉进一个 REVIEW.md + `reviewers:[…]` list 就交差 —— review-complete 会因缺 REVIEW-arch.md/REVIEW-qa.md FAIL。

🔴 **逐条裁决 external finding(信号 ≠ 判决)**:异质 review 是独立视角采样盲点 · 但**没完整上下文**(可能 false positive / 不懂 DEV-RULES / hallucinate)· **默认倾向是相信它 —— 正是要纠的偏**。每条 external finding **回读真实代码 / AC / DEV-RULES 独立核实** → 归 **confirmed(修)/ rejected(不修 · 🔴 必记驳回依据)/ deferred(→ PENDING)** · 带依据落 REVIEW.md。**两头都错**:盲采 = import 误判 / churn / regression;盲驳(全 dismiss 让它过)= 异质 review 白跑。**举证责任在主对话**(rejected 必给实证 · 不是"我觉得没事")· 详 [standards/external-model-usage.md §十二](../standards/external-model-usage.md)。

frontmatter `reviewers + verdict: APPROVE|NEEDS_REVISION` · body §finding / §修复建议 / §verdict

### 6. complete --verdict
APPROVE → 自动进 test · NEEDS_REVISION → 留 review-stage · 走 fix-retry 循环(见 §fix-retry)

---

## fix-retry 循环(stage 内 · 减回退切 stage 噪音)

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

**为什么 stage 内循环**:
- stage 间循环(NEEDS_REVISION → 自动转 dev)= stage 切换 4 次/轮 · audit 噪音
- stage 内循环 = 1 次 stage 切换/Feature(只在最终 APPROVE 时切 test)
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
| 2. Architect 视角 review → REVIEW-arch.md | `roles/architect.md` | § Code Review | 技术合理性 / 性能 / 安全 / 架构 / **简洁性(防过度设计 · 唯一 counter-lens)** |
| 3. QA 视角 review → REVIEW-qa.md | `roles/qa.md` | § Code Review | AC 逐条对照 / 测试覆盖 / 边界场景 |
| 4. External cross-review | `roles/external-reviewer.md` | § Cross-review 协议 | 异质模型独立 review |
| 5. 汇合 → REVIEW.md | `standards/external-model-usage.md` | §十二 | 逐条裁决 external finding:confirmed / rejected(必记依据)/ deferred · **信号≠判决 · 不盲采不盲驳** |
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
> - external-cross-review/*.md → 跑 `state.py external-review --feature ... --stage review`(自动落产物 · 不要手写 · 详 standards §十一)

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
