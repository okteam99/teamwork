# Goal Stage

> 🧪 **四段结构**(v8.219 试点 3/12):目标 / 硬规则白名单 / 建议手段菜单 / 产物契约 · 手段 AI 自选(Execution Plan 留痕)。

---

## ① 目标(telos)

**拦住意图偏差**:产出高质量业务目标 PRD——用户要的东西被如实结构化(AC 可测 · 范围收窄 · 未拍板的事不被 AI 悄悄拍板)。路径:调研先行(事实自答)→ 起草 → **隔离冷审**(独立采样防鼓掌)→ 早问门(用户主权)→ 修订收敛 → 用户最终确认。

---

## ② 硬规则(白名单 · 每条一行 why)

1. **PRD 结构单源 = [templates/prd.md](../templates/prd.md)**,三命门段机器校验(机读块 / AC / §开工前必须想清的 · v8.201)(why:canonical 到达率实测 2/11 · 抄旧 = 新机制失效)。AC 必 BDD、写行为/价值高度;`revision_history` 非空。
2. **冷审隔离**:评审派**隔离 subagent**,只喂 `PRD + cite 文件 + KNOWLEDGE/GLOSSARY 摘录 + 上游摘要`,**不喂主对话起草心路**(why:同一 AI 起草完审自己 = 带记忆脑补填缝,实证 in-context 只产鼓掌、冷审才抓到 high 契约 gap)。**派谁/派几个 = 按 `state.stage_review_roles.goal`**(prepare 按角色价值判据配 · `change-review-roles --reason` 审计;PM 永不自审——作者最锚定,退为整合者不给 verdict)。
3. **早问门三闸**(条件暂停 · R5):闸 1 每问必附已调研证据(没查完没资格问);闸 2 只问**用户主权**问题(偏好/业务取舍/外部事实)——**答案在代码/文档/上游里的事实类上抛 = R5 违规**,退回自答;闸 3 格式四件套(证据/为何自答不能/选项+影响/推荐)· ≤3 问 · 无过闸问题不暂停(why:用户时间是最贵资源 · 问题质量是入场券)。
4. **物化门禁**(goal-complete 拦):`prd_verdicts_all_pass`(verdicts 全 APPROVE/SKIP)· `pl_challenge_present`(roster 含 pl 时 PRD-REVIEW 必有 PL-CHALLENGE 段)· PRD-REVIEW mtime > PRD · `--needs-ui` × flow_type 校验。
5. **既有行为变更必升级**:PRD 改了用户可感知的既有默认行为(原 A → 现 B)→ 必入 §待决策项让用户拍板,**不可**写成「有意改变」叙述段蒙混(why:用户主权——没拍过板的不算拍板)。
6. **规模反压**:AC > 10 → §待决策项必写「为什么不拆」或给拆分建议(why:超大 PRD 的业务目标必然稀释)。
7. **收敛软上限**:连续 3 轮冷审不收敛 → 停止硬循环,升级用户「要不要回 planning 拆 BL / 收窄范围」(why:反复修不收敛 = 位置错了不是修得不够)。
8. **auto_mode**:早问门与最终确认不暂停,按推荐继续 + `add-concern WARN` 留痕(why:委托要留审计)。

---

## ③ 建议手段菜单(AI 自选 · 不强制全用)

**起草前调研**(自答优先 · 也是早问门入场券)——按需选查:代码现状(grep+Read 核心文件)/ KNOWLEDGE(`Flagged Ambiguities` 防重复问 · `Preferences` 防问已答 · 已否方向防复活)/ GLOSSARY(术语实体)/ 上游规划(BL/WS/愿景/PENDING)。发现内化进 PRD,不单独成文。

**冷审各角色找什么**(mandate 参考 · **按 roster 派**,组合由 prepare 判定):

| 角色 | mandate | 找什么 |
|---|---|---|
| QA | 可测性 | 测试覆盖 / 边界场景 / AC 可测试性 / 空值异常分支 |
| Architect | 可行 + 简洁 | 技术可行性 / 架构影响 / **简洁性 counter-lens**(过度设计?职责焊错层?)——唯一防过度设计的 lens |
| PL | 对抗质疑 | 质疑六问(价值前提 / 问题定义 / 范围最小化 / 上游对齐 / 复活检查 / 既有行为变更)· 产 `PL-CHALLENGE-{n}` · 至少 1 实质或「无+理由」· 详 [roles/product-lead.md](../roles/product-lead.md) |
| external(opt-in) | 异质盲区 | 契约型后端地基 feature(schema 即交付物)值得加第 4 冷审 |

**修订与收敛**:PM 逐条响应(ADOPT/REJECT/DEFER)· `adversarial_self_check` 双向——ADOPT 前先质疑 finding 不成立、REJECT 前先 steelman,**两个方向都给实证**(「冷审说得对」「我觉得没事」都不是理由);Round 2+ 重新派**冷** Agent 走验证模式(喂修订 PRD + 上轮 finding + 处置,核实 fix + 找新,防重复提已解决)。

**评审聚焦三问**:业务目标清晰?当前环境可实现?方案恰当简洁?

---

## ④ Output Contract(产物契约)

### `PRD.md`
frontmatter `acceptance_criteria[] + revision_history[]`(均必);body 按 templates/prd.md(§背景/§用户故事/§交付预期/§验收标准/§Out of Scope/§待决策项〔只收用户主权问题〕/§开工前必须想清的)。

### `PRD-REVIEW.md`
frontmatter `reviewers`(= stage_review_roles.goal)+ `verdicts: {role: APPROVE|NEEDS_REVISION|SKIP}`;body 每冷审 Agent 单独段 · cite PRD 行号 · PL 段 = PL-CHALLENGE 段 · 标 `execution: subagent`。schema 单源 = templates/prd.md § PRD-REVIEW schema。external opt-in 时产 `external-cross-review/goal-<model>.md`(跑 `state.py external-review` · 不手写)。

### ⏸️ 用户最终确认(R5 · 「重点 review 指引」导读先行)
确认前 emit 导读——**首节分两层**:🟡 **你要拍板的**(REJECT/DEFER/升级项 · **每条写成 A/B 选择题 + 我的倾向** · 说人话 · finding id 挪括号)/ ✅ **已处理**(ADOPT 压成主题保 substance · 不逐条 spell 码);余节 ≤2 行:核心取舍/范围收窄/影响面/修订轨迹/残留风险——**全部照实抄落盘产物 · 空节写「无」**(why:导读给没读过 PRD 的人;决策与 ADOPT 平铺等权 = 决策被淹)。然后 R5 标准 1/2/3(1=confirm+`goal-complete --needs-ui <bool>` 💡 / 2=按反馈修订重审 / 3=其他)· 剩余 §待决策项一次性 escalate(早问门问过的不重复)。

**过场观测**:PL-CHALLENGE 采纳率 / 早问门「改:默」进 PROCESS-LEDGER——长期零采纳 = 过场信号,收紧判据。

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py) · spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `GOAL_SPEC`
- 裁决纪律:[../standards/external-model-usage.md](../standards/external-model-usage.md) §12 · 角色 telos:[../roles/](../roles/)
