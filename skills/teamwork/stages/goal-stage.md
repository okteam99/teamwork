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
4. **物化门禁**(goal-complete 拦):`prd_verdicts_all_pass`(verdicts 全 APPROVE/SKIP)· `pl_challenge_present`(roster 含 pl 时 PRD-REVIEW 必有 PL-CHALLENGE 段)· `external_coverage_present`(roster 含 external 时外审段必有 coverage 申报 · v8.243)· PRD-REVIEW mtime > PRD · `--needs-ui` × flow_type 校验。
5. **既有行为变更必升级**:PRD 改了用户可感知的既有默认行为(原 A → 现 B)→ 必入 §待决策项让用户拍板,**不可**写成「有意改变」叙述段蒙混(why:用户主权——没拍过板的不算拍板)。
6. **规模反压**:AC > 10 → §待决策项必写「为什么不拆」或给拆分建议(why:超大 PRD 的业务目标必然稀释)。
7. **收敛软上限**:连续 3 轮冷审不收敛 → 停止硬循环,升级用户「要不要回 planning 拆 BL / 收窄范围」(why:反复修不收敛 = 位置错了不是修得不够);⚡ **fast 上限 2 轮**(v8.267):第 2 轮末仍未收敛 → 不再循环 · 未收敛决策点直接列进终确认导读 🟡「你要拍板的」(A/B 选择题 + 倾向)抛用户拍板。
8. **auto_mode**:早问门与最终确认不暂停,按推荐继续 + `add-concern WARN` 留痕(why:委托要留审计)。

---

## ③ 建议手段菜单(AI 自选 · 不强制全用)

**起草前调研**(自答优先 · 也是早问门入场券)——按需选查:代码现状(grep+Read 核心文件)/ KNOWLEDGE(`Flagged Ambiguities` 防重复问 · `Preferences` 防问已答 · 已否方向防复活)/ GLOSSARY(术语实体)/ 上游规划(BL/WS/愿景/PENDING)。发现内化进 PRD,不单独成文。

**起草思考规范**(v8.262 · 写法非环节):写 PRD 时**就按冷审关注点思考**(不是写完再检查)—— 写背景/方案时 PL 六问过脑(价值前提/最小范围/既有行为);写每条 AC 时用可测判据(「尽量/合理/优化」落笔即换 · 边界/异常入 AC);涉依赖先读真实代码确认存在再写;术语当句定义。清单织在 [templates/prd.md 模板头「🧠 起草思考规范」](../templates/prd.md)。why:finding 采纳率 80-90% = 多数问题起草时可预见 · **按冷审标准写一遍比写完被打回改一遍省一整轮**(Round 2+ 是 goal 耗时大头)。

**冷审两路并行(v8.243 默认 roster = `[pl, external]`)**——⚡ 同发两个隔离 subagent · 互不喂对方产出 · 🎭 **两路模型错开**(v8.268:外审路 ≠ 主审路(如 fable5 会话 → 外审 opus));组合按 roster(prepare 判定 · `change-review-roles --reason` 可调):

| 路 | mandate | 找什么 |
|---|---|---|
| PL | 对抗质疑 | 质疑六问(价值前提 / 问题定义 / 范围最小化 / 上游对齐 / 复活检查 / 既有行为变更)· 产 `PL-CHALLENGE-{n}` · 至少 1 实质或「无+理由」· 详 [roles/product-lead.md](../roles/product-lead.md) |
| external(第三视角冷审 · 默认**错开模型** subagent〔≠主会话模型 · v8.268〕· 跨厂商异质 opt-in) | **覆盖方向制** | 🔴 **必覆盖**:**可实现**(技术可行 / 架构影响 / **简洁性 counter-lens**〔过度设计?职责焊错层?〕——唯一防过度设计 lens)· **可验证**(AC 可测试性 / 边界场景 / 空值异常分支)+ 🔴 **AI 自主方向 ≥1**(按 feature 特性自选:安全 / 性能 / 数据一致性 / 兼容 / 运维…)。每方向给 finding 或「查过无发现」· 段记 `coverage: [...]`(物化门 `external_coverage_present`) |
| qa / architect(默认并入外审覆盖方向) | 独立冷审(roster 加回时) | 复杂 feature(schema 即交付物 / 测试面大 / 架构决策重)→ `change-review-roles` 加回独立跑 · mandate = 上面覆盖方向的对应拆分 |

**修订与收敛**:PM 逐条响应(ADOPT/REJECT/DEFER)· `adversarial_self_check` 双向——ADOPT 前先质疑 finding 不成立、REJECT 前先 steelman,**两个方向都给实证**(「冷审说得对」「我觉得没事」都不是理由);Round 2+ 重新派**冷** Agent 走验证模式(喂修订 PRD + 上轮 finding + 处置,核实 fix + 找新,防重复提已解决)· 🎚️ **验证轮派发用验证档模型**(v8.256 · 校验型任务 · 首轮全量冷审不降档)。

**评审聚焦三问**:业务目标清晰?当前环境可实现?方案恰当简洁?

---

## ④ Output Contract(产物契约)

### `PRD.md`
frontmatter `acceptance_criteria[] + revision_history[]`(均必);body 按 templates/prd.md(§背景/§用户故事/§交付预期/§验收标准/§Out of Scope/§待决策项〔只收用户主权问题〕/§开工前必须想清的)。

### `PRD-REVIEW.md`
frontmatter `reviewers`(= stage_review_roles.goal · v8.243 默认 `[pl, external]`)+ `verdicts: {role: APPROVE|NEEDS_REVISION|SKIP}`;body 每冷审 Agent 单独段 · cite PRD 行号 · PL 段 = PL-CHALLENGE 段 · external 段 = 覆盖方向制(记 `coverage: [...]` · 按方向分小节)· 标 `execution: subagent`。schema 单源 = templates/prd.md § PRD-REVIEW schema。异质 opt-in(localconfig `false`)时外审改跑 `state.py external-review` 产 `external-cross-review/goal-<model>.md`(不手写)· PRD-REVIEW external 段引其结论。

### ⏸️ 用户最终确认(R5 · 「重点 review 指引」导读先行)

🔮 **投机窗**(v8.256 · 等待窗不闲置的 goal 特化):emit 终确认暂停点后 · **后台派 TECH 草稿 subagent**(读 PRD 终稿候选 · 产物 = worktree 内 TECH.md 草稿 · 🔴 不跑任何 state 命令)——数据支撑:终确认「改:默」台账 ≈ 全默(PRD 此刻变动率≈0 · 冷审已收敛)· goal 等待中位 26m ≈ blueprint 起草中位 27m(等待窗恰好藏下)。用户 `ok` → blueprint-start 后草稿直接接续(TC 起草与冷审照跑);用户有改 → 草稿差量更新。auto/yolo 不适用(确认点 skip · 无等待窗)。🔴 时点纪律:**只在终确认暂停点后投机**(冷审收敛前 PRD 是活靶 · finding 采纳率 80-90% · v1 时点投机必返工)。
确认前 emit 导读——**首节分两层**:🟡 **你要拍板的**(REJECT/DEFER/升级项 · **每条写成 A/B 选择题 + 我的倾向** · 说人话 · finding id 挪括号)/ ✅ **已处理**(ADOPT 压成主题保 substance · 不逐条 spell 码);余节 ≤2 行:核心取舍/范围收窄/影响面/🛡️ 兜底策略(PRD 层降级体验类 · 逐项一句「保护什么+成本」· v8.265 不许默默做 · 无则「无」)/修订轨迹/残留风险——**全部照实抄落盘产物 · 空节写「无」**(why:导读给没读过 PRD 的人;决策与 ADOPT 平铺等权 = 决策被淹)。然后 R5 标准 1/2/3(1=confirm+`goal-complete --needs-ui <bool>` 💡 / 2=按反馈修订重审 / 3=其他)· 剩余 §待决策项一次性 escalate(早问门问过的不重复)。

**过场观测**:PL-CHALLENGE 采纳率 / 早问门「改:默」进 PROCESS-LEDGER——长期零采纳 = 过场信号,收紧判据。

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py) · spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `GOAL_SPEC`
- 裁决纪律:[../standards/external-model-usage.md](../standards/external-model-usage.md) §12 · 角色 telos:[../roles/](../roles/)
