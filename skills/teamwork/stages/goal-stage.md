# Goal Stage

> **telos**:产出**高质量业务目标 PRD** —— 调研先行(事实层)→ 起草 → PL 对抗质疑(前提层)→ 早问门(用户主权层)→ 多角色评审(完备性层)→ 用户确认(最终裁决)· 五层各管一事不重叠。

---

## 怎么做

### 1. PM 现状调研(起草前 · 自答优先)

🔴 **四类必查** —— 全部是 AI 可自答的信息源 · 也是 §4 早问门的**入场券**(没查完没资格问用户):

- **代码现状**:grep 关键词 → Read 3-5 个核心文件(5-10 min · 只读不输出 · 流程详 [templates/prd.md § 起草前必读](../templates/prd.md))
- **KNOWLEDGE.md**:`Flagged Ambiguities`(历史已澄清歧义 · **防重复问**)· `Preferences`(用户已表达偏好 · **防问已答**)· `Out-of-Scope / 已否方向`(防复活)
- **GLOSSARY.md**:业务术语 / 实体关系(SKILL 路由表:PM 起草 PRD 前必读)
- **上游规划**:BL-NNN / WS / 愿景执行线 / PENDING + prepare「流程目标」行

产出:调研发现**内化**进 PRD(§背景 / AC 与代码现状契合)· 不单独成文;真未决且属**用户主权**的问题 → 暂记 §待决策项(§4 统一处理)。

### 2. PM 起草 PRD 初稿(主对话 PM 身份)

- 落 `{Feature}/PRD.md` · 🔴 **结构单源 = [templates/prd.md](../templates/prd.md)**(§背景 / §用户故事 / §交付预期 / §验收标准 / §Out of Scope / §待决策项 · 按需:流程图 / 埋点 / 消费方分析)· 起草前过模板 **§PM 起草规范 checklist**(产品目标 Why / AC 规范 / 影响范围 / PRD 不写什么 / 起草后自查 `pm_self_check`)
- frontmatter 必含 `acceptance_criteria` 数组 + `revision_history` 数组(可空 · 后续填)
- AC 写成 BDD(Given/When/Then)· 写在「**行为 / 价值**」高度(WHAT)· 不下沉实现机制;`§Out of Scope` 用足「非目标」主动收窄(防过度设计第一道闸)
- 🔴 **规模反压**:AC > 10 → §待决策项 必写「为什么不拆」或给拆分建议(回 planning 拆 BL / 拆子 Feature)—— 超大 PRD 的业务目标必然稀释
- §待决策项 只收**用户主权**问题(偏好 / 业务取舍 / 外部事实)· 🔴 事实类问题(答案在代码 / 文档 / 上游里)禁入 → 回 step 1 自答

🔴 **PRD 评审聚焦(高度对齐)**:PRD 评的是 **① 业务目标清晰**(为谁 · 解决什么 · 价值)+ **② 当前环境下可实现**(架构 / 技术约束内能落地)+ **③ 方案合理且恰当简洁**(无过度设计 · 责任在对的层)。

### 3. PL 对抗质疑(前提层 · 防 self-talk)

🔴 PL 不是「审视」是「**质疑**」—— 没有角色负责杀死不该做的 feature 时 · 评审只会把错的 PRD 打磨得更精致。**质疑五问**(每问对照 step 1 调研证据 · 不凭感觉):

| # | 质疑 | 杀伤点 |
|---|---|---|
| ① | 价值前提:为谁 · 不做会怎样 | 杀死 feature 最便宜的时点 |
| ② | 问题定义:真问题 · 还是方案伪装成的问题 | 防拿着锤子找钉子 |
| ③ | 范围最小化:哪些 AC 砍掉不影响目标 | 防镀金 |
| ④ | 上游对齐:cite BL / WS / 愿景行 · 或显式「无上游 · 独立判断 + 理由」 | 业务方向 grounding |
| ⑤ | 复活检查:KNOWLEDGE `Out-of-Scope / 已否方向` 记过此方向被否吗 | 防被否方向换皮复活 |

**执行强度**(按 prepare `reviewer_thinking_checklist` Q1):
- Q1 命中(产品方向影响 · 常态)→ 🔴 **subagent 隔离执行**:只喂 PRD + 上游规划摘要 + KNOWLEDGE 摘录 · **不喂主对话起草心路**(防对自己推理的锚定 = 鼓掌效应主源)
- Q1 未命中 → 轻版:主对话切 PL 身份 · 五问各 1 行结论
- 敏捷需求(goal 角色集无 pl)→ 整步免(门禁自动放行)

**产物**:PRD-REVIEW.md **`PL-CHALLENGE` 段**(finding id = `PL-CHALLENGE-{n}` · `category=premise-challenge`)· 🔴 至少 1 条实质质疑 **或** 显式「无实质质疑 + 理由」(goal-complete 物化校验 `pl_challenge_present`)。PM 逐条回应:接受 → 改 PRD / 反驳 → 留痕(先填 `pm_response.adversarial_self_check` 模拟对方最强论据再驳 · schema 详模板)/ 属用户主权 → 进 §待决策项(§4 问)。

### 4. ⏸️ goal-critical 早问门(条件暂停 · R5 · 三闸)

汇总 step 1-3 落进 §待决策项 的问题 · 过三闸后**一次性**问用户;**无过闸问题 → 跳过本步(不暂停)**:

- **闸 1 调研穷尽**:step 1 四类已查 · 每问必附「已调研证据」—— 没证据 = 没入场券
- **闸 2 用户主权判别**:答案 = 用户偏好 / 业务取舍 / AI 拿不到的外部事实 → 可问;答案在代码 / 文档 / 上游规划里(事实类)→ 退回自答 · 🔴 **上抛事实类 = R5 违规**
- **闸 3 格式四件套 + 上限**:每问必带 ① 已调研证据 ② 为何自答不能 ③ 选项 A/B + 各自对 AC / 范围的影响 ④ 推荐 + 理由;**≤3 问**(超过 = PRD 没想清楚 · 先收窄不是多问)· 全带推荐 → 用户可一个 `ok` 全收

🔴 **auto_mode=true**:不暂停 · 按推荐项继续 + 问题留 §待决策项 + `state.py add-concern --severity WARN --message "early-gate auto: <问题摘要+所选推荐>"` 留痕(同 blueprint §7.5 模式)。

**为什么在评审前**:5 角色无法替用户回答业务取向 · 错猜被全员 APPROVE 包装后到 step 9 才推翻 = 最贵返工点(v8.128 排查先行律的镜像:猜测被仪式包装后更难推翻)。

### 5. 多角色并行评审 → PRD-REVIEW.md

- **必含 `state.stage_review_roles[goal]` 全部角色**(默认 4:PM/QA/Architect/PL · v8.149 去 External · 经 `state.py change-review-roles` 调整后按新值校验 · `_evidence_reviewers_match` 强制)· 缺角色 → goal-complete FAIL:
  - PM 视角:需求清晰度 / AC 完整性(+ `pm_self_check` 落 frontmatter · 含 `code_context_read`)
  - QA 视角:测试覆盖性 / 边界场景 / AC 可测试性
  - Architect 视角:技术可行性 / 架构影响 / 性能安全 / **方案简洁性(是否过度设计 · 职责是否归错层 · 能否更简单达成业务目标)** —— 🔴 唯一的**简洁性 counter-lens**(详 `roles/architect.md` Telos)
  - PL 视角:业务方向 / 路线图对齐(cite 上游依据)+ **确认 §3 CHALLENGE 已解决 / 留痕**
- 🔴 **goal 不做 external 评审(v8.149)**:goal 是**业务目标对齐**(用户亲审 PRD)· external 天然「找缺口 → 加校验」· 每条单看都合理 · 合起来把方案做臃肿 / 责任焊错层 —— 在「定要做什么」阶段是噪音。**过度设计防线 = Architect 简洁性 counter-lens(内审)**;细节 / 边界 / 异质 cross-review 全部归 **blueprint**(技术方案阶段 · external 在那)。确需对某 PRD 上 external → `change-review-roles --stage goal --roles '...,external'` 显式 opt-in。
- 落 `{Feature}/PRD-REVIEW.md` · frontmatter `reviewers: [...]` + `verdicts: {role: APPROVE|NEEDS_REVISION|SKIP}` · Round 结构 / findings / `pm_response`(ADOPT|REJECT|DEFER + 对抗自查)schema 单源 = [templates/prd.md § PRD-REVIEW schema](../templates/prd.md)

### 6. PM 回应 + 修订 PRD

- 逐条响应 review finding(`pm_response.action` = ADOPT / REJECT / DEFER · DEFER 仅限 `business-decision` 类)· 🔴 **默认姿态=质疑 · 不盲目认同**:`adversarial_self_check` 方向对称 —— **ADOPT 前**先质疑 finding 不成立的最强反方(过度设计/错层/false positive)再回读代码确认它真成立才采纳;**REJECT 前**先 steelman finding 再驳。盲采(「reviewer 说得对」式无核实采纳)= 最常踩反模式 · 详 [standards/external-model-usage.md §12](../standards/external-model-usage.md)
- 修订 PRD → draft-v0.2 / v0.3 ... · `revision_history` 追新条目(版本号 + 修订理由)
- NEEDS_REVISION 时循环 · 直到全员 APPROVE

### 7. 全员通过判定(🔴 已物化)

- 所有 reviewer verdict = **APPROVE(或 SKIP)** · 仍有 NEEDS_REVISION → 回 step 6
- 🔴 v8.132 起 goal-complete 物化校验 `prd_verdicts_all_pass`(词表只认 `APPROVE | NEEDS_REVISION | SKIP` · 旧 PASS 系词表不通过)—— 此前「全员通过」是纸面纪律 · 全 NEEDS_REVISION 也能 complete

### 8. PM 决策 `--needs-ui`(complete 前必)

- 基于 PRD 内容判定是否需要独立 UI Design Stage
- 准备 `state.py goal-complete --needs-ui {true|false} ...`

### 9. ⏸️ 用户最终确认(R5 暂停点 · 带重点 review 指引)

🔴 **`auto_mode=true` 时跳过此暂停点** —— PRD 已经多角色 review 内化 · auto 用户接受(详 [SKILL.md § auto_mode=true 时各暂停点行为](../SKILL.md))。

🔴 **请求确认前先 emit「重点 review 指引」**(v8.137 · 用户重点 review 的导读 · 镜像 v8.120 流程目标的校准定位):固定 6 节 · 每节 ≤2 行 · 🔴 **全部照实抄自既有落盘产物 · 不即兴总结不美化** · 空节显式写「无」(证明查过 · 不可省节):

```
📌 重点 review 指引(导读 · 不替代 PRD)
- 替你做的判断:<被 REJECT/DEFER 的 PL finding:谁提 · 驳/缓一句理由(源:pm_response)| 无>
- 核心取舍:<评审中有争议、已裁决的点 · cite finding/PL-CHALLENGE id(源:PRD-REVIEW)| 无>
- 范围收窄:<Out of Scope 中用户可能预期在内的项(源:§Out of Scope)| 无显著>
- 影响面:<跨服务/跨模块清单(源:PM 自查·影响范围)>
- 修订轨迹:<v0.1→v0.N 实质变化 1-2 句 · 哪轮评审驱动(源:revision_history + ADOPT findings)>
- 残留风险/假设:<未完全解决项 + §待决策项剩余(将在下方选项一次性 escalate)| 无>
```

🔴 **「替你做的判断」放第一节**:REJECT/DEFER 是 AI 判断替代用户判断之处 · 用户抽查此节性价比最高。六节来源全部是已落盘结构化数据(`findings[].pm_response` / `PL-CHALLENGE` / `revision_history` / `§Out of Scope` / PM 自查 / `§待决策项`)—— 脱离产物自由发挥 = 违规(同 PROCESS-LEDGER「照实抄」纪律)。

🔴 emit R5 标准 1/2/3(模板见 [SKILL.md § R5(b)](../SKILL.md))· 一次性 escalate 剩余 §待决策项(§4 早问门已问过的**不重复问**):
1. **确认 PRD · 进入下一 stage** 💡 推荐 — `goal-complete --needs-ui <true/false>` → 自动转 ui_design/blueprint
2. **还要改 PRD** — PM 按你的反馈修订 PRD · 重走多角色评审
3. **其他指示**

用户选 1 后跑 complete · state.py 按 `--needs-ui` 自动转移。

---

## 必读 cite 清单(P0-11 · 各 substep 动手前主对话输出)

| Substep | 必读 spec | 段 | cite 关键点 |
|---------|----------|----|------------|
| 1. PM 现状调研 | `templates/prd.md` + `KNOWLEDGE.md` + `GLOSSARY.md` | § 起草前必读 + FA/Pref/OoS | 四类自答 · 早问门入场券 |
| 2. PM 起草 PRD 初稿 | `roles/pm.md` + `templates/prd.md` | § 创作要点 + § PM 起草规范 checklist | 结构单源 · AC BDD · 规模反压 AC>10 |
| 3. PL 对抗质疑 | `roles/product-lead.md` | § 创作要点(质疑五问) | 至少 1 条实质质疑 · Q1 命中走 subagent 隔离 |
| 4. ⏸️ 早问门 | 本文件 §4 | 三闸 | 只问用户主权 · 带证据/选项/推荐 · ≤3 |
| 5. 多角色并行评审 | `roles/qa.md + roles/architect.md` + `templates/prd.md` | § Review 规范 + § PRD-REVIEW schema | QA 看可测试性 / Architect 看可行+简洁 |
| 6. PM 回应 + 修订 | `roles/pm.md` + `templates/prd.md` | § PRD 修订 + pm_response schema | 对抗自查后再 REJECT · revision_history 必落 |
| 7. 全员通过判定 | — | — | (已物化 · verdicts 全 APPROVE/SKIP) |
| 8. PM 决策 --needs-ui | `stages/goal-stage.md` | § 特殊规则 | --needs-ui 不传则 FAIL |
| 9. ⏸️ 用户最终确认 | — | — | (无 cite 要求) |

📎 **cite 纪律**(输出格式 / 强约束 / 为什么 cite)· 单源详 [../STAGES.md § 2 P0-11 cite 纪律](../STAGES.md)

## 质量基线

📎 **物化拦截**:
- `--needs-ui` × flow_type 校验(敏捷需求 / Feature Planning + `--needs-ui=true` → FAIL)
- P0-1 evidence_check:`PRD-REVIEW.md` mtime 必晚于 `PRD.md` + `PRD.frontmatter.revision_history` 数组非空
- v8.132 `prd_verdicts_all_pass`:verdicts 全 APPROVE/SKIP 才 complete
- v8.132 `pl_challenge_present`:角色含 pl 时 PRD-REVIEW 必含 PL-CHALLENGE 段

**PRD SOP**(违反 → review NEEDS_REVISION):
- AC 必 BDD 风格(Given X / When Y / Then Z)· 不写"应该流畅 / 用户友好"等不可测描述
- 每轮 NEEDS_REVISION 后修订 · 加 1 条 `revision_history` 记录(版本号 + 修订理由)
- substep 链中禁 AskUserQuestion · 用户主权问题统一走 §4 早问门(三闸)· 剩余在 Substep 9 一次性 escalate
- 🔴 早问门反模式:未调研先问(闸 1)/ 问事实类(闸 2)/ 无选项无推荐(闸 3)—— 都是 R5 违规
- 🔴 重点 review 指引反模式(Substep 9):复述 PRD 全文 / 营销式总结(「本 PRD 经多轮评审已完善」)/ 省略空节 / 内容无产物出处 —— 指引是导读不是宣传 · 六节照实抄 · 空节写「无」

**对抗有效性观测**(防仪式化):PL-CHALLENGE 采纳率 / 早问门「改:默」由 [PROCESS-LEDGER](../templates/process-ledger.md) 列观测 —— PM 长期零采纳 CHALLENGE = 过场信号 · 用户从不改早问门推荐 = 问多了收紧闸 2。

---

## Output Contract(产物形态参考)

> 📋 **起草模板**(避免找历史 Feature 抄):
> - PRD.md → `{SKILL_ROOT}/templates/prd.md`(结构 + § PM 起草规范 checklist 单源)
> - PRD-REVIEW.md → 同文件 § PRD-REVIEW schema(Round 结构 · findings · pm_response · 机读 frontmatter)

### `PRD.md`
- frontmatter:
 - `acceptance_criteria: [{id, description}]`(必)
 - `revision_history: [{version, date, changes}]`(必 · 至少 1 条)
- body:按 templates/prd.md(§背景 / §用户故事 / §交付预期 / §验收标准〔BDD〕/ §Out of Scope / §待决策项)

### `PRD-REVIEW.md`
- frontmatter:
 - `reviewers: [pm, qa, architect, pl]`(按 stage_review_roles[goal] · v8.149 默认无 external)
 - `verdicts: {role: APPROVE|NEEDS_REVISION|SKIP}`(🔴 全 APPROVE/SKIP 才可 complete)
- body ≥ 20 行 · 每 reviewer 单独段 · cite PRD 行号 · **PL 段 = PL-CHALLENGE 段**(`PL-CHALLENGE-{n}`)

### `external-cross-review/goal-<model>.md`(v8.149 默认不产 · 仅 opt-in 时)
- goal 默认无 external(细节归 blueprint)· 仅 `change-review-roles --stage goal --roles '...,external'` 显式启用时才 **跑** `state.py external-review --feature ... --stage goal`(自动落产物)· 详 [standards/external-model-usage.md §十一](../standards/external-model-usage.md)。

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py) `execute_stage_start` / `execute_stage_complete`
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `GOAL_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
