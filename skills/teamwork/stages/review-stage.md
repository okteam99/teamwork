# Review Stage

---

## 收敛协议(总纲)

review 的目标是**收敛**,不是无限逼近完美。协议三根支柱(可枚举规则已进脚本 · review-complete / review-retry 物化拦截):

1. **severity 分级 + verdict 门槛**:只有 open 的 BLOCKER/MAJOR 才能打回;MINOR/NIT 永远不构成再开一轮的理由(= advisory)。
2. **验证轮(Round 2+ 范围锁定)**:第二轮起只裁决上轮 finding + 回归审查修复 diff · **禁全量重扫**(全量重审每轮随机采样出新 nit = 不收敛根因)。
3. **轮次预算**:`max_review_rounds`(localconfig · 默认 3)· 超预算 → 升级暂停点让用户裁决收口方式。

finding 全生命周期有机器台账(`REVIEW.md frontmatter findings` → `state.stage_contracts.review.findings_ledger`)· rejected 的 finding 不可复活。

---

## finding severity 分级

| 级别 | 定义 | 判据示例 |
|---|---|---|
| `BLOCKER` | AC 失败 / 数据损坏 / 安全漏洞 / 生产事故级 | 验收标准跑不通 · SQL 注入 · 丢数据路径 |
| `MAJOR` | 确定性 bug(可实证复现的错误行为) | 边界输入崩溃 · 状态机走错分支 · 竞态 |
| `MINOR` | 改进建议(现行为不错 · 有更好做法) | 可读性 · 更优 API 用法 · 潜在但未实证的隐患 |
| `NIT` | 风格 | 命名 · 注释措辞 · 格式 |

🔴 定级纪律:**「可能有问题」不是 MAJOR** —— MAJOR 须给确定性实证(哪个输入 · 哪行 · 什么错误行为)。拿不出实证 → MINOR。升级 MINOR → MAJOR 须补实证依据(写进 finding title/正文)。

---

## REVIEW.md frontmatter findings(机读台账 · schema)

```yaml
---
reviewers: [architect, qa, external]
verdict: NEEDS_REVISION
findings:
  - {id: F1, severity: MAJOR, status: open, title: "并发写入丢更新(store.py:88 无锁)", source: arch}
  - {id: F2, severity: MINOR, status: open, title: "错误信息可带字段名", source: qa}
  - {id: F3, severity: NIT, status: rejected, title: "变量名偏好", source: external}
---
```

- `id`:`F{n}` · 跨轮稳定(修了改 status · 不删条目 · 不换 id)
- `severity`:`BLOCKER|MAJOR|MINOR|NIT`(见上表)
- `status`:`open`(待处理)/ `fixed`(已修并验)/ `rejected`(裁决不修 · 带依据)/ `deferred`(转 PENDING 池)
- `source`:`arch|qa|external`
- block style(`- id: F1` + 缩进续行)亦可 · id 不得重复

review-complete 时快照合并进 `state.stage_contracts.review.findings_ledger[]`(按 id 合并 · 后轮状态覆盖前轮 · 保留 `round_opened`)—— 跨轮单源 · 验证轮 brief 自动注入。

## verdict 门槛(review-complete 物化拦截)

| verdict | 通过条件 | 不满足时 |
|---|---|---|
| `NEEDS_REVISION` | findings 里 ≥1 条 `status: open` 且 severity ∈ {BLOCKER, MAJOR} | FAIL:全部 open 为 MINOR/NIT → 改 APPROVE(advisory 随行)· 或为某条给出升级 MAJOR 的实证依据 |
| `NEEDS_REVISION` | findings 机读列表必须存在且非空 | FAIL:必须列出 finding 才能打回 |
| `APPROVE` | 不存在 open 的 BLOCKER/MAJOR | FAIL:先 fixed / rejected / deferred(带依据) |
| `APPROVE` | open 的 MINOR/NIT 允许(= advisory) | —— 应转 `deferred` 进 PENDING 池 · 或顺手修(不强制) |
| `APPROVE` | findings 缺失/空 = 干净通过 | —— |

---

## 怎么做(Round 1 · 全量评审)

### 1. 加载上下文
读 PRD.md / TC.md / TECH.md / 实际代码 diff(git diff HEAD~N)

### 2. Architect 视角 review → REVIEW-arch.md
技术合理性 / 性能 / 安全 / 架构一致性 + **方案简洁性(防过度设计)** · 主对话默认
🔴 Architect 是唯一**简洁性 counter-lens**(QA/external 都偏加 rigor):查「实现是否把不该管的复杂度焊进核心抽象 · 能否更简单 · 职责是否归错层(可删 / 可下沉正确 owner)」· external finding 别盲采(对照业务目标 + 简洁性取舍 · 详 `roles/architect.md` Telos)

### 3. QA 视角 review → REVIEW-qa.md
AC 逐条对照实现 / 测试覆盖度 / 边界场景

### 4. External cross-review → external-cross-review/review-<model>.md
**跑** `state.py external-review --feature <path> --stage review`(host/model/profile 全自动 · 异质性硬约束物理墙 · 至少 1 份 · P0-154)。详 [standards/external-model-usage.md §十一](../standards/external-model-usage.md)。
🔴 **跑之前先 `--preflight`**(秒级):which + 微 probe 验**登录/网络/配额** E2E 通 · 失败此刻修环境(治「到 review 跑完 600s 才发现 CLI 未登录 → 降级折腾」)。超时/空跑本体已**自动重试一次**(1.5x timeout · emit `attempts`)· 长 review 项目 localconfig `external_review_timeout_sec` 可调基础超时。

🔴 **同步 · 慢 · 别提前 kill**:external-review **同步阻塞**跑(timeout 600s · claude 路径 = 纯 `claude -p <自包含 prompt>` 一次性生成 · 无工具 / 无 doc 模式 / 无 liveness 文件)· 真实评审常 **30s–3min**(模型并发 / 限流更久 · `claude -p` 会静默无输出)。**前台跑、耐心等满 600s · 不要中途 kill**。
- **真超时 / 空输出 = `verdict: FAIL`(门禁未达)· 不是放行**:🔴 **禁止**伪造 `tool_error` 文件、或把 external 自列进 REVIEW.md `reviewers` 当通过。按 FAIL 的 hint 串行重跑(并发会限流);**串行重跑仍超时/空输出**(限流/配额/网络等环境性原因)→ 归入下一条「异质客观不可用 · 已重试失败」走**显式降级**(合法继续路径 · 同时报因给用户留痕)。🔴 **不得**绕过 P0-154 —— 禁的是「伪造/冒充/静默跳过」· 不是降级协议本身。
- **异质客观不可用(未装/未登录/配额满/持续超时限流 · 已重试失败)→ 降级 subagent 自审(降级优先于移除)**:`state.py external-review ... --self-review-fallback --reason '<原因+重试证据>'` → **emit subagent 配方**(🔴 不再 exec CLI · PMO 起 `Agent` subagent 同模型自审 · harness 内跑)→ 写 `external-cross-review/<stage>-<model>-subagent-degraded.md`(frontmatter `heterogeneous:false degraded:true degraded_mode:subagent-fallback degraded_reason:'...'`)· **满足 P0-154**(降级 · 让你继续)· 非异质 · 同盲点。能修环境就重跑真异质;🔴 **绝不偷偷**用 subagent 冒充异质(必显式标 degraded)。详 [standards/external-model-usage.md §11.5](../standards/external-model-usage.md)。

### 5. 汇合 → REVIEW.md(🔴 汇总层 · 不是合并:arch/qa/external 三份产物都要独立留盘)
REVIEW.md 是 REVIEW-arch.md + REVIEW-qa.md + external-cross-review/*.md **之上**的汇总 · **不替代**它们(三份独立产物是 P0 门禁硬要求 · 原因:多视角独立性 SOP · 各视角各自落盘防鼓掌效应 · 详 §质量基线)。🔴 别把三视角揉进一个 REVIEW.md + `reviewers:[…]` list 就交差 —— review-complete 会因缺 REVIEW-arch.md/REVIEW-qa.md FAIL。

🔴 **逐条裁决 finding(信号 ≠ 判决)**:异质 review 是独立视角采样盲点 · 但**没完整上下文**(可能 false positive / 不懂 DEV-RULES / hallucinate)· **默认倾向是相信它 —— 正是要纠的偏**。🔴 **固定思考顺序:① 质疑**(先假设 finding 不成立:false positive / 过度设计 / 错层 / reviewer 没看全上下文)**→ ② 确认**(回读真实代码 / AC / DEV-RULES 核实质疑成不成立)**→ ③ 裁决** → **confirmed(修)/ rejected(不修)/ deferred(→ PENDING)** · 带依据落 REVIEW.md。**两头都错**:盲采(reviewer 说啥改啥 · 🔴 最常踩 ·「reviewer 说得对」不是采纳理由)= import 误判 / churn / regression;盲驳(全 dismiss 让它过)= 异质 review 白跑。🔴 **举证责任对称**:**confirmed 与 rejected 都必记实证** —— 采纳给「为何确为真 + 为何这样改对」· 驳回给「为何不是问题」· 都指真实代码/规约/目标 · 不是"我觉得"/"reviewer 说的"。详 [standards/external-model-usage.md §十二](../standards/external-model-usage.md)。

裁决结果落 frontmatter `findings`(机读 · 定 severity + status)· body §finding / §修复建议 / §verdict。

### 6. complete --verdict
`state.py review-complete --verdict {APPROVE|NEEDS_REVISION}`(受 §verdict 门槛拦截)。
APPROVE → 自动进 test · NEEDS_REVISION → 留 review-stage · 走 fix-retry 循环(见 §fix-retry)

---

## 验证轮(Round 2+ · 范围锁定)

review-retry 开新轮后 · brief 自动切换为验证轮模板(注入上轮 findings 台账)。**验证轮不是重新评审 · 是验证收敛**:

**本轮只做两件事**:
1. **逐条裁决上轮 open finding**:fixed / not-fixed(REVIEW.md findings 更新 status · 带依据)
2. **回归审查修复 diff**(上轮已评 commit..HEAD):只看修复本身引入的新问题

**🔴 范围锁定规则**:
- **禁全量重扫**。新 finding 仅两种合法来源:(a)出自修复 diff;(b)BLOCKER 级且附「为何首轮未发现」说明。其他新发现(重扫全库翻出的 MINOR/NIT)→ 不入本轮 findings · 直接进 PENDING 池。
- **rejected 的 finding 不得复提**(台账 status=rejected 即已裁决 · 除非新证据 —— 新证据须写明比上轮多知道了什么)。
- **钟摆检测**:同一代码点相邻轮次出现方向相反的 finding(上轮要求加固 ↔ 本轮要求简化)→ **不修** · 升暂停点让用户裁决取向(钟摆 = reviewer 采样噪音 · 修它只会摆回去)。

**external 频率(全流程)**:
- Round 1:全量 external(§4)
- 中间验证轮:可不跑 external(arch/qa 裁决即可)
- **拟 APPROVE 前**:本 stage 有过 fix → 跑一次 `state.py external-review --feature <path> --stage review --verify-fixes`(增量 · 只评上轮已评 commit..HEAD 修复 diff · 上轮 findings 自动注入逐条给 fixed/not-fixed)。review-complete 物化校验此证据(external-review-prompts/review-*.log mtime > 最后 fix_at)· `disable_external_review=true` 项目自动跳过。锚点失效(rebase)→ 自动 FAIL 提示退回全量。

---

## fix-retry 循环(stage 内 · 减回退切 stage 噪音)

review-stage 含 **stage 内 fix-retry 循环** · NEEDS_REVISION 不切 stage:

```
Round N: review-complete --verdict NEEDS_REVISION (写 rounds[-1].verdict + findings 台账合并)
  ↓ (current_stage 仍是 review · contract.evidence.verdict=NEEDS_REVISION)
RD 修代码 + commit (在 worktree 内)
  ↓
review-fix --auto-commit <hash> [--addresses-findings F1,F2]
  ↓ (写 rounds[-1].fix_commit + fix_at)
review-retry   ← 超 max_review_rounds 在此拦(见 §轮次预算)
  ↓ (rounds 加 round N+1 · 重置 contract gates · 清 evidence.verdict · brief 切验证轮)
验证轮:逐条裁决上轮 open finding + 回归审查修复 diff(禁全量重扫 · 见 §验证轮)
  ↓ 拟 APPROVE 前(有 fix)→ external-review --verify-fixes
review-complete --verdict APPROVE | NEEDS_REVISION(受 severity 门槛拦截)
  ↓ APPROVE → 自动转 test
```

**rounds[] 结构**(audit · 反映完整循环 · 含收敛计数):
```json
"stage_contracts.review.rounds": [
  {"round": 1, "verdict": "NEEDS_REVISION", "review_commit": "C1",
   "fix_commit": "C2", "fix_at": "...", "addresses_findings": ["F1"],
   "new_findings_count": 2, "carried_open_count": 0},
  {"round": 2, "verdict": "APPROVE", "review_commit": "C3",
   "fix_commit": null, "completed_at": "...",
   "new_findings_count": 0, "carried_open_count": 1}
]
```

**findings_ledger**(跨轮台账 · review-complete 自动合并):
```json
"stage_contracts.review.findings_ledger": [
  {"id": "F1", "severity": "MAJOR", "status": "fixed", "title": "...",
   "source": "arch", "round_opened": 1, "last_updated_round": 2},
  {"id": "F2", "severity": "MINOR", "status": "deferred", "title": "...",
   "source": "qa", "round_opened": 1}
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
| `review-complete --verdict NEEDS_REVISION` | 出本轮 verdict(须 ≥1 open BLOCKER/MAJOR) | 评审已落 REVIEW.md(含 findings)/REVIEW-arch.md/REVIEW-qa.md |
| `review-fix --auto-commit <hash>` | 记录 fix commit | rounds[-1].verdict=NEEDS_REVISION + rounds[-1].fix_commit=null |
| `review-retry` | 开新一轮(验证轮) | rounds[-1].fix_commit 已记录 · 且未超 max_review_rounds |
| `review-retry --user-confirmed --reason '<用户拍板>'` | 超预算逃生 · 放行超预算轮次 + concerns WARN 留痕 | 用户在升级暂停点选「继续完整修复」 |
| `review-complete --verdict APPROVE` | 终结 review-stage(无 open BLOCKER/MAJOR · 有 fix 则须 verify-fixes 证据) | 任意轮 |

## 轮次预算与升级暂停点

`max_review_rounds`(`.teamwork_localconfig.json` · 默认 3)。review-retry 即将开启 round > 预算 → FAIL 并 emit R5 升级暂停点(工具生成 · 原样给用户):

```
⏸️ review 已 N 轮未收敛(超过 max_review_rounds=3)· 剩余 open finding:
[按 severity 分组列 id+title]
请选择:
1. 仅修 BLOCKER/MAJOR 后收口 💡 推荐(动作:MINOR/NIT 全部 deferred → PENDING 池 · 修完走验证轮 APPROVE)
2. 继续完整修复(动作:review-retry --user-confirmed --reason '<用户拍板>' 开新一轮)
3. 按现状 APPROVE(动作:open 项全部 deferred + concerns WARN 留痕)
```

- 选 2 的逃生命令由 AI 代跑 · 但 `--user-confirmed` **必须真有用户拍板**(审计发现 AI 自加 = 红线违规;yolo = blanket 委托例外 · reason 仍必填)
- 每次超预算放行自动写 concerns WARN(audit 单源)

---

**与 dev-stage 的关系**:
- review-stage **只读 dev 的最终 commit**(进 stage 时)+ 后续每轮 fix commit
- dev-stage contract 不变(已 completed_stages)· 不重新走 dev-start/dev-complete
- 如果发现 dev 设计根本错(不是 finding 级 fix 能解决)· 用户用 `state.py reset-prev` 退到 dev 重做

---

## 质量基线

📎 **物化拦截**:P0-154(`external-cross-review/*.md` 非空 · 跨模型异质 review 必跑一次)+ severity 门槛 + findings 台账 + 轮次预算(本文档 §收敛协议 · review-complete / review-retry 强制)

**多视角独立性 SOP**(违反 → review 失去价值):
- 每视角独立 review · 各自落 `REVIEW-{role}.md` · 不互相 cite verdict(避免鼓掌效应)
- APPROVE 可附 advisory(non-blocking)finding · 显式落 `REVIEW.md` findings(status open 的 MINOR/NIT 即 advisory)留 audit · 不隐藏

**QA 边界 SOP**:必逐条 AC 对照 · 显式列"边界场景测试" finding · 不只看 happy path

**NEEDS_REVISION 处理**:stage 内 fix-retry(RD 修 · 不切 stage · R5 + fix-retry 规范);带 open BLOCKER/MAJOR 收口(全部转 deferred 按现状 APPROVE)需用户在升级暂停点明示 + concerns WARN 记录原因

---

## Output Contract(产物形态参考)

> 📋 **起草模板**(避免找历史 Feature 抄):
> - REVIEW.md / REVIEW-arch.md / REVIEW-qa.md → 无独立模板 · 见下方 schema 与 §findings schema · 各 reviewer 按视角分段
> - external-cross-review/*.md → 跑 `state.py external-review --feature ... --stage review`(自动落产物 · 不要手写 · 详 standards §十一)

### `REVIEW.md`
frontmatter `reviewers + verdict + findings(机读台账 · 见 §findings schema)` · body §finding 汇总(逐条裁决依据)/ §修复建议 / §verdict

### `REVIEW-arch.md`
架构师视角 · 技术 / 性能 / 安全 / 简洁性

### `REVIEW-qa.md`
QA 视角 · AC 对照 / 测试覆盖 / 边界

### `external-cross-review/*.md`
异质模型 · 至少 1 份(验证轮增量产物 `review-<model>-fixverify.md` 由 --verify-fixes 自动落)

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `REVIEW_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
