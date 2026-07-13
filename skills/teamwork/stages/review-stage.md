# Review Stage

> 🧪 **四段结构试点**(v8.218 · 目标 / 硬规则 / 建议手段菜单 / Output Contract):目标 + 契约给足,**手段 AI 自选**(Execution Plan 声明选择与理由)· 降低强制规则比例。

---

## ① 目标(telos)

**拦住质量盲区**:实现「做坏了」但作者自己看不见(自评盲区是数学性的)。手段本质 = **独立视角采样**——多个不喂上下文的视角各自看一遍,盲点交叉暴露(历史实证:拦真问题 92/163)。同时**收敛**:review 是质量闸不是无限打磨(MINOR/NIT 永不构成再开一轮的理由)。

---

## ② 硬规则(白名单 · 每条一行 why · 违者 gate 拦或 review 无效)

1. **评审独立性**:每视角独立评、各自落 `REVIEW-{role}.md`、**不互喂 verdict / 不读他人报告**(why:防鼓掌效应——独立性没了,多视角 = 一个视角 × N 份)。评审角色按 `state.stage_review_roles.review`(prepare 按角色价值判据配 · 审计留痕);**做多少可调,做了就必须独立**。
2. **severity 定级纪律**:「可能有问题」不是 MAJOR——MAJOR 须给确定性实证(哪个输入/哪行/什么错误行为),拿不出 → MINOR(why:不收敛的根因就是无实证的高定级)。分级表:`BLOCKER`=AC 失败/数据损坏/安全;`MAJOR`=可实证复现的确定性 bug;`MINOR`=改进建议;`NIT`=风格。
3. **verdict 门槛**(review-complete 物化拦截):NEEDS_REVISION 须 ≥1 条 open BLOCKER/MAJOR 且 findings 机读台账非空;APPROVE 不得有 open BLOCKER/MAJOR(open MINOR/NIT = advisory 随行或转 deferred)。
4. **逐条裁决 · 举证对称**:每条 finding 走 **质疑 → 确认 → 裁决**(先假设不成立 · 回读真实代码核实 · 再定 confirmed/rejected/deferred);**confirmed 与 rejected 都必记实证**(why:盲采 = churn/误改,盲驳 = 白跑;「reviewer 说得对」不是采纳理由)。
5. **验证轮范围锁定**(Round 2+):只裁决上轮 open finding + 回归审查修复 diff · **禁全量重扫**(新 finding 仅限出自修复 diff、或 BLOCKER 级附「为何首轮未发现」);rejected 不得复提(除非新证据);同一代码点相邻轮方向相反(加固↔简化)= 钟摆 → 不修 · 升暂停点(why:全量重扫每轮随机采样出新 nit = 不收敛根因)。
6. **轮次预算**:超 `max_review_rounds`(默认 3)→ R5 升级暂停点用户裁决(1 仅修 BLOCKER/MAJOR 收口 💡 / 2 继续〔`review-retry --user-confirmed` 必须真有用户拍板 · yolo blanket 例外〕/ 3 按现状 APPROVE + deferred 留痕)。
7. **external 按 roster + 独立性协议**:roster 含 external → 跑 `state.py external-review --stage review`(先 `--preflight` 秒级验环境;同步慢 · 常 30s–3min · **别提前 kill**;超时/空输出 = FAIL 非放行;客观不可用已重试 → `--self-review-fallback` 显式降级 subagent 冷审 · frontmatter 标 `degraded` · 🔴 **绝不伪造/冒充/静默跳过**)。拟 APPROVE 前有过 fix → `--verify-fixes` 增量重验(物化校验)。
8. **REVIEW.md 是汇总不是替代**:三份视角产物独立留盘(缺 REVIEW-arch/REVIEW-qa → complete FAIL)。

---

## ③ 建议手段菜单(AI 按本 feature 自选 · Execution Plan 声明「选了什么 + 为何」· 不强制全用)

| 手段 | 何时值得 |
|---|---|
| **AC 逐条对照实现**(QA 经典) | 有结构化 AC 的 feature 默认首选 |
| **diff 走查 + 数据流追踪** | 改动集中/契约变更(顺 provider→consumer 追一遍) |
| **边界与异常路径审查**(空值/并发/超时/回滚) | 有状态/多步操作/外部依赖时 |
| **对抗复现**(按 finding 写最小复现或反例测试) | MAJOR 定级存疑时——复现即实证 · 复现不出降 MINOR |
| **简洁性 counter-lens**(Architect 独有:能否更简单/职责归错层/可删) | 方案偏重、external findings 偏「加校验」时(external 天然加 rigor · 需反向制衡) |
| **测试质量抽查**(测试是否真断言 · 假绿检测) | 测试全绿但 diff 大时 |
| **真机/预览截图核对** | UI feature(配合 dev §设计↔实际核对的产物) |
| **KNOWLEDGE/历史 bug 对照** | 项目有同类踩坑记录时 |
| **ultra review 摄入**(用户在本 session 跑 `/code-review ultra` → `state.py external-ingest --from session --input-file <转录>`)| 关键/高风险改动 · 用户在场愿投入 —— 产品化多智能体独立评审 · 摄入后照常走裁决管线(可代 external 第三视角)|

评审深度与手段组合是**判断不是清单**:小 diff 机械改 → AC 对照 + diff 走查即可;核心链路/新契约 → 叠加数据流 + 边界 + 对抗复现。

---

## ④ Output Contract(产物契约 · 机读)

### `REVIEW.md`(汇总层)
frontmatter:
```yaml
---
reviewers: [architect, qa, external]   # = state.stage_review_roles.review
verdict: NEEDS_REVISION | APPROVE
findings:
  - {id: F1, severity: MAJOR, status: open, title: "并发写入丢更新(store.py:88 无锁)", source: arch}
  - {id: F2, severity: MINOR, status: rejected, title: "…", source: qa}
---
```
- `id` = `F{n}` 跨轮稳定(修了改 status · 不删不换 id);`status` ∈ open/fixed/rejected/deferred;`source` ∈ arch/qa/external。
- body:§finding 汇总(逐条裁决依据)/ §修复建议 / §verdict。
- review-complete 快照合并进 `state.stage_contracts.review.findings_ledger[]`(跨轮单源 · 验证轮 brief 自动注入)。

### `REVIEW-arch.md` / `REVIEW-qa.md` / `external-cross-review/*.md`
各视角独立产物(external 由 `state.py external-review` 自动落 · 不手写;验证轮增量 = `review-<model>-fixverify.md`)。

### fix-retry 循环(stage 内 · 命令契约)
```
review-complete --verdict NEEDS_REVISION → RD 修+commit → review-fix --auto-commit <hash>
→ review-retry(超预算在此拦)→ 验证轮 → [有 fix 拟 APPROVE → external --verify-fixes]
→ review-complete --verdict APPROVE → 自动转 test
```
`rounds[]` + `findings_ledger` 结构由 state.py 维护(audit 单源)。发现 dev 设计根本错(非 finding 级)→ `reset-prev` 退 dev。

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py) · spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `REVIEW_SPEC`
- external 协议:[../standards/external-model-usage.md](../standards/external-model-usage.md)(§11 降级 · §12 裁决)
- 角色 telos:[../roles/architect.md](../roles/architect.md) / [../roles/qa.md](../roles/qa.md)
