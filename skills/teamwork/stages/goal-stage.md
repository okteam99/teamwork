# Goal Stage

> **telos**:产出**高质量业务目标 PRD** —— 调研先行(事实层)→ 起草 → **并行冷审**(隔离 subagent · QA 完备性 + Architect 简洁性 + PL 前提对抗 · 防鼓掌)→ 早问门(用户主权层)→ 整合修订 → 冷审循环收敛 → 用户确认(最终裁决)。

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

- 落 `{Feature}/PRD.md` · 🔴 **结构单源 = [templates/prd.md](../templates/prd.md)**(必填核:§背景 / §用户故事 / §交付预期 / §待决策项 / §验收标准 / §Out of Scope / **§开工前必须想清的**〔开放区 · 至少 1 实质或「无+理由」〕· 按需:流程图 / 埋点 / 消费方分析)· 起草前过模板 **§PM 起草规范 checklist**(产品目标 Why / AC 规范 / 影响范围 / PRD 不写什么 / 起草后自查 `pm_self_check`)
- frontmatter 必含 `acceptance_criteria` 数组 + `revision_history` 数组(可空 · 后续填)
- AC 写成 BDD(Given/When/Then)· 写在「**行为 / 价值**」高度(WHAT)· 不下沉实现机制;`§Out of Scope` 用足「非目标」主动收窄(防过度设计第一道闸)
- 🔴 **规模反压**:AC > 10 → §待决策项 必写「为什么不拆」或给拆分建议(回 planning 拆 BL / 拆子 Feature)—— 超大 PRD 的业务目标必然稀释
- §待决策项 只收**用户主权**问题(偏好 / 业务取舍 / 外部事实)· 🔴 事实类问题(答案在代码 / 文档 / 上游里)禁入 → 回 step 1 自答

🔴 **PRD 评审聚焦(高度对齐)**:PRD 评的是 **① 业务目标清晰**(为谁 · 解决什么 · 价值)+ **② 当前环境下可实现**(架构 / 技术约束内能落地)+ **③ 方案合理且恰当简洁**(无过度设计 · 责任在对的层)。

### 3. 并行冷审 Round 1(草稿写完即派 · 隔离 subagent · 防鼓掌)

🔴 PRD v0.1 落盘后,**并行派 3 个隔离 Agent 冷审**(Feature 流;敏捷需求 2 个〔QA+Architect〕)· 每个 subagent 只喂 `PRD + cite 文件 + KNOWLEDGE/GLOSSARY 摘录 + 上游规划摘要` · **不喂主对话起草心路**(防对自己推理的锚定 = 鼓掌效应主源 · v8.155 把 PL 的隔离 pattern 推广到全部 reviewer)。

| Agent | mandate | 找什么 |
|---|---|---|
| **QA** | 可测性 | 测试覆盖 / 边界场景 / AC 可测试性 / 空值与异常分支 |
| **Architect** | 可行 + 简洁 | 技术可行性 / 架构影响 / 性能安全 / **简洁性 counter-lens**(过度设计?职责焊错层?能更简单?)—— 🔴 唯一防过度设计的 lens(详 `roles/architect.md` Telos) |
| **PL** | 对抗质疑(不是审视) | 质疑六问:① 价值前提(为谁·不做会怎样 = 杀 feature 最便宜点)② 问题定义(真问题还是方案伪装的问题)③ 范围最小化(哪些 AC 砍掉不影响目标)④ 上游对齐(cite BL/WS/愿景行 · 或显式「无上游+理由」)⑤ 复活检查(KNOWLEDGE 已否方向换皮复活?)⑥ **既有行为变更**(PRD 是否改了某既有用户可感知默认行为〔原 A → 现 B〕? 若是 → 🔴 必须升级为显式 §待决策项 让用户拍板 · **不可**登记为「既有行为取舍/有意改变」叙述段蒙混 —— 那不是用户拍过板的)· 产 `PL-CHALLENGE-{n}`(category=premise-challenge)· 至少 1 实质质疑或显式「无+理由」 |

🔴 **为什么冷审 / 为什么并行**:同一个 AI 起草完转头审自己 = 带起草记忆脑补填缝 → 漏细微 gap(实证:in-context 的 arch/qa 只产 info-only 鼓掌 · 冷审的 external/PL 才抓到 high 契约 gap)。隔离 subagent 没那段记忆,只能照 PRD 字面查,抓得到。并行 = 3 个同时跑 · 不串行切帽子。

**产物**:3 份 finding 汇进 `{Feature}/PRD-REVIEW.md` Round 1 · frontmatter `reviewers: [qa, architect, pl]`(v8.155 **去 pm**:作者审自己最锚定 · PM 退为**整合者** · 不给 verdict)+ `verdicts: {role: APPROVE|NEEDS_REVISION|SKIP}` · Round 结构 / findings / `pm_response` schema 单源 = [templates/prd.md § PRD-REVIEW schema](../templates/prd.md)。

🔴 **external opt-in**:契约型后端地基 feature(schema 即交付物)可 `change-review-roles --stage goal --roles 'qa,architect,pl,external'` 加异质 Agent 为第 4 冷审(v8.149 保留安全阀 · 数据证明对这类 feature 有用)· 默认不含。

### 4. ⏸️ goal-critical 早问门(冷审后 · 条件暂停 · R5 · 三闸)

Round 1 冷审跑完 · PM(主对话 · 整合者)汇总 `起草时 §待决策项 + 冷审 surface 的用户主权问题` · 过三闸后**一次性**问用户;**无过闸问题 → 跳过(不暂停)**:

- **闸 1 调研穷尽**:每问必附「已调研证据」—— 没证据 = 没入场券
- **闸 2 用户主权判别**:答案 = 用户偏好 / 业务取舍 / AI 拿不到的外部事实 → 可问;答案在代码 / 文档 / 上游里(事实类)→ 退回自答 · 🔴 **上抛事实类 = R5 违规**
- **闸 3 格式四件套 + 上限**:每问带 ① 已调研证据 ② 为何自答不能 ③ 选项 A/B + 各自对 AC/范围的影响 ④ 推荐 + 理由;**≤3 问** · 全带推荐 → 用户一个 `ok` 全收

🔴 **auto_mode=true**:不暂停 · 按推荐继续 + `state.py add-concern --severity WARN --message "early-gate auto: <问题摘要+所选推荐>"` 留痕。

🔴 **为什么冷审后**(v8.155 调整 · 原在评审前):冷审视角比主对话先验更能识别哪些是**真**用户决策(主对话起草时易把自己拍的当定论)· 合并「起草时 + 冷审」两处问题源一次问 · 比旧「评审前问」更准 · 且避免冷审空转在用户主权项上(冷审已先跑 · 问题已浮出)。

### 5. PM 整合 + 回应 + 修订 → PRD v(N+1)

- PM 收 3 份冷审 finding · 逐条响应(`pm_response.action` = ADOPT / REJECT / DEFER · DEFER 仅限 `business-decision` 类)
- 🔴 **默认姿态=质疑 · 不盲目认同**:`adversarial_self_check` 双向 —— **ADOPT 前**先质疑 finding 不成立的最强反方(过度设计/错层/false positive)再回读代码确认它真成立才采纳;**REJECT 前**先 steelman finding 再驳。**两个方向都给实证**(采纳给「为何确为真+为何这样改对」· 驳回给「为何不是问题」)·「冷审说得对」与「我觉得没事」都不是理由(详 [standards/external-model-usage.md §12](../standards/external-model-usage.md))。盲采 = 最常踩反模式。
- 修订 PRD → v0.2 / v0.3 ... · `revision_history` 追条目(版本号 + 修订理由)

### 6. 冷审循环判定(Round 2+ 验证模式 · 收敛 = 全 APPROVE)

- 🔴 **Round 2+ 重新派冷 Agent**(不复用上轮 subagent · 保持冷)· **验证模式**:喂 `修订后 PRD + 上轮各自 finding + PM 处置(ADOPT 改了啥/REJECT 理由)` · 任务 = 核实 fix 真站得住 + 找新(对抗性 verify · 防重复提已解决的)
- 任一 verdict = **NEEDS_REVISION** → 回 §5 再修再审;**全 APPROVE/SKIP** → 出循环
- 🔴 物化门禁:`prd_verdicts_all_pass`(verdicts 全 APPROVE/SKIP · 词表只认 APPROVE|NEEDS_REVISION|SKIP)+ `pl_challenge_present`(角色含 pl 时 PRD-REVIEW 必有 PL-CHALLENGE 段)
- 🔴 **收敛软上限**:连续 **3 轮**不收敛 → 不再硬循环 · 升级用户「PRD 可能根本没想清楚 · 要不要回 planning 拆 BL / 收窄范围」(防死循环 churn · 镜像 v8.128 排查先行:反复修不收敛 = 该换位置不是再修)

### 7. PM 决策 `--needs-ui`(complete 前必)

- 基于 PRD 内容判定是否需要独立 UI Design Stage
- 准备 `state.py goal-complete --needs-ui {true|false} ...`

### 8. ⏸️ 用户最终确认(R5 暂停点 · 带重点 review 指引)

🔴 **`auto_mode=true` 时跳过此暂停点** —— PRD 已经多角色 review 内化 · auto 用户接受(详 [SKILL.md § auto_mode=true 时各暂停点行为](../SKILL.md))。

🔴 **请求确认前先 emit「重点 review 指引」**(v8.137 · 用户重点 review 的导读 · 镜像 v8.120 流程目标的校准定位):**首节分两层**(🟡 你要拍板的〔写成选择题〕/ ✅ 已处理〔备查·压主题〕)· 余 5 节 ≤2 行 · 🔴 **照实抄落盘产物 · 不美化** · 🔴 **说人话**:CR/PL/AC/R/Q/v 等代码 id 挪进括号当 ref · **不当正文**(导读要让没读过 PRD 的人也看得懂)· 空节显式写「无」:

```
📌 重点 review 指引(导读 · 不替代 PRD)
- 🟡 **你要拍板的**(REJECT / DEFER / 升级给你 = AI 替你判断 or 升级给你 · **每条写成选择题** · 无则「无 · 全 ADOPT」):
  · **<一句话背景 · 通俗>** —— A) <选项> / B) <选项> · 我倾向 **<X>**(<一句理由>)〔<finding/PL id>〕
  · 🔎 **抽查改判**:<我把 reviewer 的 X 驳回了 · 理由一句> —— 看站不站得住〔REJECT id〕
- ✅ **已处理**(ADOPT · 备查可跳 · **压成主题 · 不逐个 spell CR/id 码 · 但保留 substance**):
  · 冷审:<抓到的主题一句>(QA/Arch 共 N 条)· external N 轮:<主题一句>(共 M 条)
- 核心取舍:<评审中有争议、已裁决的点 · cite finding/PL-CHALLENGE id(源:PRD-REVIEW)| 无>
- 范围收窄:<Out of Scope 中用户可能预期在内的项(源:§Out of Scope)| 无显著>
- 影响面:<跨服务/跨模块清单(源:PM 自查·影响范围)>
- 修订轨迹:<v0.1→v0.N 实质变化 1-2 句 · 哪轮评审驱动(源:revision_history + ADOPT findings)>
- 残留风险/假设:<未完全解决项 + §待决策项剩余(将在下方选项一次性 escalate)| 无>
```

🔴 **按可操作性分层 · 决策写成选择题**(实证 aon auth case · 旧「冷审逐条全列」把 13 条 external ADOPT 和 4 条用户决策平铺等权 → 决策被淹 + 代码当正文逼用户回翻 PRD):第一节拆 **🟡 你要拍板的**(REJECT/DEFER/升级 = AI 替你判断/升级 · 抽查 ROI 最高 · **每条 A/B 选择 + 倾向 · 说人话**)+ **✅ 已处理**(ADOPT · 抽查 ROI 低 · **压成主题保 substance · 不逐个 spell 码**;要细节去 PRD-REVIEW)。🔴 **compact ≠ collapse**:压主题保留了「抓到什么」(substance)· 禁的仍是 v8.167 那种藏掉 substance 的「全部 ADOPT」。六节来源全部已落盘结构化数据 —— 脱离产物自由发挥 = 违规(同 PROCESS-LEDGER「照实抄」纪律)。

🔴 emit R5 标准 1/2/3(模板见 [SKILL.md § R5(b)](../SKILL.md))· 一次性 escalate 剩余 §待决策项(§4 早问门已问过的**不重复问**):
1. **确认 PRD · 进入下一 stage** 💡 推荐 — `goal-complete --needs-ui <true/false>` → 自动转 ui_design/blueprint
2. **还要改 PRD** — PM 按你的反馈修订 PRD · 重走并行冷审
3. **其他指示**

用户选 1 后跑 complete · state.py 按 `--needs-ui` 自动转移。

---

## 必读 cite 清单(P0-11 · 各 substep 动手前主对话输出)

| Substep | 必读 spec | 段 | cite 关键点 |
|---------|----------|----|------------|
| 1. PM 现状调研 | `templates/prd.md` + `KNOWLEDGE.md` + `GLOSSARY.md` | § 起草前必读 + FA/Pref/OoS | 四类自答 · 早问门入场券 |
| 2. PM 起草 PRD v0.1 | `roles/pm.md` + `templates/prd.md` | § 创作要点 + § PM 起草规范 checklist | 结构单源 · AC BDD · 规模反压 AC>10 |
| 3. 并行冷审 Round 1 | `roles/qa.md + roles/architect.md + roles/product-lead.md` + `templates/prd.md` | § 创作要点 + § PRD-REVIEW schema | 🔴 隔离 subagent 冷审(不喂起草心路)· QA 可测 / Architect 简洁 counter-lens / PL 质疑六问(含 ⑥ 既有行为变更 · 至少 1 实质或「无+理由」) |
| 4. ⏸️ 早问门(冷审后) | 本文件 §4 | 三闸 | 只问用户主权 · 带证据/选项/推荐 · ≤3 |
| 5. PM 整合 + 回应 + 修订 | `roles/pm.md` + `templates/prd.md` + `standards/external-model-usage.md §12` | § PRD 修订 + pm_response schema | 默认姿态=质疑 · 双向举证 · 对抗自查后再裁决 · revision_history 必落 |
| 6. 冷审循环判定 | — | — | (已物化 · verdicts 全 APPROVE/SKIP · Round 2+ 验证模式 · 3 轮不收敛升级) |
| 7. PM 决策 --needs-ui | `stages/goal-stage.md` | § 特殊规则 | --needs-ui 不传则 FAIL |
| 8. ⏸️ 用户最终确认 | — | — | (无 cite 要求) |

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
- substep 链中禁 AskUserQuestion · 用户主权问题统一走 §4 早问门(三闸)· 剩余在 Substep 8 一次性 escalate
- 🔴 早问门反模式:未调研先问(闸 1)/ 问事实类(闸 2)/ 无选项无推荐(闸 3)—— 都是 R5 违规
- 🔴 重点 review 指引反模式(Substep 8):复述 PRD 全文 / 营销式总结 / **决策与 ADOPT 平铺等权**(决策被淹 · 必拆「🟡 你要拍板 / ✅ 已处理」两层)/ **代码 id 当正文**(CR-1/PL-2/R-8/AC-12 逼用户回翻 PRD · 必说人话 + id 挪括号)/ **决策没写成选择题**(埋 prose 末尾 · 必 A/B + 倾向)/ **collapse 藏 substance**(「全部 ADOPT」不给主题)/ 省略空节 / 内容无产物出处 —— 导读是给**没读过 PRD 的人**看的、不是宣传。

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
 - `reviewers: [qa, architect, pl]`(按 stage_review_roles[goal] · v8.155 去 pm〔整合者〕· v8.149 默认无 external)
 - `verdicts: {role: APPROVE|NEEDS_REVISION|SKIP}`(🔴 全 APPROVE/SKIP 才可 complete)
- body ≥ 20 行 · 每冷审 Agent(qa/architect/pl)单独段 · cite PRD 行号 · **PL 段 = PL-CHALLENGE 段**(`PL-CHALLENGE-{n}`)· 每段标 `execution: subagent`(冷审)

### `external-cross-review/goal-<model>.md`(v8.149 默认不产 · 仅 opt-in 时)
- goal 默认无 external(细节归 blueprint)· 仅 `change-review-roles --stage goal --roles '...,external'` 显式启用时才 **跑** `state.py external-review --feature ... --stage goal`(自动落产物)· 详 [standards/external-model-usage.md §十一](../standards/external-model-usage.md)。

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py) `execute_stage_start` / `execute_stage_complete`
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `GOAL_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
