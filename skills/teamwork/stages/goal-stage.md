# Goal Stage

> 🧪 **四段结构**(试点 3/12):目标 / 硬规则白名单 / 建议手段菜单 / 产物契约 · 手段 AI 自选(Execution Plan 留痕)。

---

## ① 目标(telos)

**拦住意图偏差**:产出高质量业务目标 PRD——用户要的东西被如实结构化(AC 可测 · 范围收窄 · 未拍板的事不被 AI 悄悄拍板)。路径:调研先行(事实自答)→ 起草 → **隔离冷审**(独立采样防鼓掌)→ 早问门(用户主权)→ 修订收敛 → 用户最终确认。

---

## ② 硬规则(白名单 · 每条一行 why)

1. **PRD 结构单源 = [templates/prd.md](../templates/prd.md)**,三命门段机器校验(机读块 / AC / §开工前必须想清的)(why:canonical 到达率实测 2/11 · 抄旧 = 新机制失效)。AC 必 BDD、写行为/价值高度 · **每条配 💬 大白话**(一句人话说清这条在验证什么 · 给用户终确认拍板用 · goal-complete 逐条校验非空);`revision_history` 非空。
2. **冷审隔离**:评审派**隔离 subagent**,只喂 `PRD + cite 文件 + KNOWLEDGE/GLOSSARY 摘录 + 上游摘要`,**不喂主对话起草心路**(why:同一 AI 起草完审自己 = 带记忆脑补填缝,实证 in-context 只产鼓掌、冷审才抓到 high 契约 gap)。**派谁/派几个 = 按 `state.stage_review_roles.goal`**(prepare 按角色价值判据配 · `change-review-roles --reason` 审计;PM 永不自审——作者最锚定,退为整合者不给 verdict)。
3. **早问门三闸**(条件暂停 · R5):闸 1 每问必附已调研证据(没查完没资格问);闸 2 只问**用户主权**问题(偏好/业务取舍/外部事实)——**答案在代码/文档/上游里的事实类上抛 = R5 违规**,退回自答;闸 3 格式四件套(证据/为何自答不能/选项+影响/推荐)· ≤3 问 · 无过闸问题不暂停(why:用户时间是最贵资源 · 问题质量是入场券)。
3.7 🔗 **链装配(调研后 · 本节单源 · 用户拍板)**:装配 = **环节**(`ui_design` / `blueprint` / `browser_e2e` 进不进 —— canonical 链上仅此三段可选)+ **评审面**(各 stage roster / 外审方向 / 轮次)两维度 · 在**调研完成后**按实测复杂度定。🔴 **`blueprint` 跳 = lite 档**(用户拍板「lite 是不是可以被 full 装配出来」——**是**:lite 有 PRD、只是不产 TC/TECH,与 full 的差就是这一条边,故不立 preset、由本槽装配出来 · 好处是定档**零 re-init**:goal 调研完当场拧旋钮,不用回头重建 feature)。判据四轴:**改动方向**(加/改/删 —— 删除无新行为可做错)× **契约面**(API / 数据结构 / 存储 / 权限 / 状态流)× **影响面**(grep 实测触点数)× **验证成本**(MR diff 一眼可验 / 需运行链路)—— 🔴 **装配证据必填**(与 Bug 排查先行同律 · 定价不许建立在需求字面上)。**两拍生效**:① goal **自身**评审面(留/去 pl 等)调研后 **AI 自定**(`change-review-roles --reason "装配·<一句证据>"` 审计留痕 · **不问用户、但必回显**):派冷审**前**在主对话 emit **🎛️ 评审深度判断卡** —— 调研纪要(关键发现 · 含影响面/数据面实测)· goal 冷审 roster 与模型错开 · **是否需要额外评审**(+qa / +dba / 升异质 / 默认两路)· **逐项判断理由**(引四轴证据)· 下游装配预告一行;**回显后直接派发不停等**(用户想调回一句即可 · 与 ② 的「默认执行不阻塞」同律);② **下游**装配写进 PRD 终确认导读「🔗 链装配」节 · 🔴 **固定三槽 · 缺槽即漏 · 整卡 ≤6 行**(实证:形容词式要求下装配卡退化成「环节+影响面」两行 · **评审力度整维丢失**;槽位服务**减税可见** —— 评审减没减、减到几路,用户必须一眼可核 · 每槽一行理由一句 · 不是新表格):
   - **流程阶段**:`goal → [ui_design 进/跳] → [blueprint 进/跳] → dev → review → test → [browser_e2e 进/跳] → pm_acceptance → ship`(可选段标进/跳 + 一句理由 · 🔴 `blueprint 跳` = lite 档 · 判据是四轴的**验证成本**轴:方案空间小到不值得先写一份 TECH 再照着写 —— **不是**「工期紧」);
   - **评审力度**(逐评审 stage 一行 · **是否需要 × 几路 × 谁 × 理由**〔为什么这个力度〕):`blueprint:<N 路 · 角色 · 理由>` `review:<N 路 · 角色 · 理由>` · 收到零也显式写 `0 路 + 理由`(减税要减在明处);
   - **四轴证据**:方向 / 契约面 / 影响面实测 / 验证成本 各半句。
   **默认按此执行 · 用户不要求改就生效 · 不单独停等**(环节经 `goal-complete --needs-ui / --needs-blueprint / --needs-browser-e2e` 落 `execution_hints` · 下游 roster 经 change-review-roles 留痕)。装配判断表 —— 🔴 **加减两侧都要判**(实证:只有加法判据时,四轴全低的域名配置仍默认吃满 goal 双路 + blueprint 2 路 + review 2 路 = 六路评审 · 用户当场问「这么简单为什么那么多 review」):
   - **减法侧(四档 · 四轴越低档越轻 · 用户拍板)**:
     · **超低 = `preset=micro`** —— 纯文案 / 单行常量 · 无契约面 · 用户在 ship1 MR diff 上就能验完 → `execute → ship` 零门;
     · **低 =「直接做」形态 → `preset=tiny`(用户拍板原句:按理说直接开发,完成后架构师 review 一下,PM 验收盯 staging 部署就可以了)** —— 行为性但小(纯配置 / 删除 / 少量逻辑)· 无契约面 · **diff 可验(不需跑链路)** → `dev → review〔architect 单路〕 → pm_acceptance → ship` · **零文档**(规格 = dev brief 理解卡 · 无 PRD/TC)· PM 验收盯 staging 部署(await-merge 已自动带 CI)。🔴 tiny 无 goal 入口 —— 已在 goal 里才判出超低,说明 prepare 定档偏保守:`init-feature --force` 重定档合法(实证消费 AI 已走通),但**多数情况直接按低档装配继续走完更划算**(重定档要弃掉已产的 PRD);
     · **中低 = lite(装配形态 · 不是 preset · 零 re-init)** —— 有行为面但方案空间小(怎么做基本只有一种写法)· **需跑链路验证** → `goal〔PRD 极简 · 冷审 0 路缺省〕 → dev → review〔architect 单路〕 → test → pm_acceptance → ship`:`goal-complete --needs-blueprint false` 跳 blueprint(不产 TC/TECH/TECH-REVIEW)· **PRD 照要、终确认停等照停**(用户主权不因降档让渡)· AC↔测试绑定改由 **PRD 机读块 `acceptance_criteria[].test_refs`** 承载(dev 写完测试**回填真实引用** · test-complete 校验非空**且引用真实存在**);
     · **中**(缺省)→ full 链 + flow 默认 roster;**高**(命中任一加法触发)→ 加面。
     🔴 **tiny / lite 的分界 = 四轴的「验证成本」轴**:diff 一眼可验 → tiny(无 test stage)· 需跑链路才敢说对 → lite(保留 test)。**不是**按代码行数分。
     🔴 **降档不降独立性**:tiny/lite 的单路 architect **模型照错开**(≠会话主模型 · 单路不变式)—— 减的是路数,不是「换个人看」这件事本身;同模型自审 = 盲区相关,那一路等于没有。
     🔴 **一致性倒逼**:判断卡/装配卡的评审力度行,路数与四轴必须对得上 —— 四轴全低而某 stage ≥2 路 → 必须写一句「为什么不降」(写不出就降 · 实证:域名配置吃满六路评审 · 用户当场问「这么简单为什么那么多 review」);
   - **加法侧**:有产品方向影响 → goal 留 pl(仅纯内部技术重构去);无 UI 改动 → ui_design + browser_e2e 双跳;跨 ≥3 模块触发点 → blueprint/review 外审升异质或加独立 qa;数据模型重构(删改老字段 / 表结构变)→ blueprint 强 architect + 加 dba(why:prepare 只有需求文本没有代码现状 —— 在信息最少的时刻做信息最密的决策 = 结构性错判,实证「删 3 个按钮」被字面定价成九段全链;调研后定价 = Feature 与 Bug 统一成「先调研 · 再定价」)。
4. **物化门禁**(goal-complete 拦):`prd_verdicts_all_pass`(verdicts 全 APPROVE/SKIP)· `pl_challenge_present`(roster 含 pl 时 PRD-REVIEW 必有 PL-CHALLENGE 段)· `external_coverage_present`(roster 含 external 时外审段必有 coverage 申报)· PRD-REVIEW mtime > PRD · `--needs-ui` × flow_type 校验。
5. **既有行为变更必升级**:PRD 改了用户可感知的既有默认行为(原 A → 现 B)→ 必入 §待决策项让用户拍板,**不可**写成「有意改变」叙述段蒙混(why:用户主权——没拍过板的不算拍板)。
6. **规模反压**:AC > 10 → §待决策项必写「为什么不拆」或给拆分建议(why:超大 PRD 的业务目标必然稀释)。
6.5 🔴 **功能优先 · 复杂度守恒**(冷审 finding 准入 · 单源 [review-stage 规则 2.5](./review-stage.md)):PRD 冷审评「**要做的东西对不对**」—— 需求缺漏 / AC 矛盾 / 不可测 / 范围误解**必报**;不要求 PRD 为低概率场景增设兜底需求、不借冷审推流程门 / 测试门;「更简的需求形态达成同等业务价值」永远合法。
7. **收敛软上限**:连续 3 轮冷审不收敛 → 停止硬循环,升级用户「要不要回 planning 拆 BL / 收窄范围」(why:反复修不收敛 = 位置错了不是修得不够);⚡ **fast 上限 2 轮**:第 2 轮末仍未收敛 → 不再循环 · 未收敛决策点直接列进终确认导读 🟡「你要拍板的」(A/B 选择题 + 倾向)抛用户拍板。
8. 🎚️ **PRD 起草与冷审必用主模型 / 高级模型**(错开时也只在高档之间错 · **不许降到验证档**)(why:PRD 定义「做什么」· 它错了整条链都在做错的东西 —— 两份设计文档〔PRD/TECH〕决定全局质量上限;调研/整合/机械外化等可降档并行)。
9. **auto_mode**:早问门与最终确认不暂停,按推荐继续 + `add-concern WARN` 留痕(why:委托要留审计)。

---

## ③ 建议手段菜单(AI 自选 · 不强制全用)

**起草前深入调研**(自答优先 · 也是早问门入场券 · 用户拍板:预期是**深入**的调研,不是扫一眼)—— 四面**必过**(按 feature 相关性,查过的面各给一句发现 · 确不相关写「不涉」,不许静默跳):
① **代码现状**:核心触点 **grep 实测**(路由 / 实体 / API 的真实消费方与实现形态 —— 只读一个文件不算调研);② **数据面**(涉数据 / 统计 / 报表类必查):数据源 / 表 / 事件的真实 schema 与已有查询路径;③ **既有相似实现**:项目里最接近的功能长什么样(对齐存量形态 · 防重复造);④ **上游与规范**:BL/WS/PENDING · KNOWLEDGE(`Flagged Ambiguities` 防重复问 · 已否方向防复活)· GLOSSARY · DEV-RULES/ARCHITECTURE 相关节。
🎛️ **并行姿态(Orchestrator 同律)**:四面默认**多 subagent 并行采集**(每面/每束一路 · **验证档** · prompt 给「查什么 + 返回结构化发现」—— 调研采集在验证类白名单);**整合与判断留主对话**(深度档:交叉发现 · 提炼「最可能错在哪」· 出评审深度判断卡)—— 不新立「调研档」:采集 = 枚举检索、判断 = 深度,二分正好落既有档(单源 [agents/README §一](../agents/README.md))。
🔴 **深度判据一句话:查到能回答装配四轴(3.7)+ 能写出「这个 PRD 最可能错在哪」**—— 答不出 = 还没查完,不许起草。发现内化进 PRD,不单独成文;同时喂两张卡:3.7 装配证据 + 评审深度判断卡(见 3.7 ①)。

**起草思考规范**(写法非环节):写 PRD 时**就按冷审关注点思考**(不是写完再检查)—— 写背景/方案时 PL 六问过脑(价值前提/最小范围/既有行为);写每条 AC 时用可测判据(「尽量/合理/优化」落笔即换 · 边界/异常入 AC · 🔴 兜底 miss/坏输入分支必和命中分支一起落 AC);涉依赖先读真实代码确认存在再写(🔴 在当前 worktree/ship 目标分支读 · 不吃旧分支/记忆调研);术语当句定义。清单织在 [templates/prd.md 模板头「🧠 起草思考规范」](../templates/prd.md)。why:finding 采纳率 80-90% = 多数问题起草时可预见 · **按冷审标准写一遍比写完被打回改一遍省一整轮**(Round 2+ 是 goal 耗时大头)。

**冷审两路并行(默认 roster = `[pl, external]`)**——⚡ 同发两个隔离 subagent · 互不喂对方产出 · 🎭 **两路模型错开**(外审路 ≠ 主审路(如 fable5 会话 → 外审 opus));组合按 roster(prepare 判定 · `change-review-roles --reason` 可调):

| 路 | mandate | 找什么 |
|---|---|---|
| PL | 对抗质疑 | 质疑六问(价值前提 / 问题定义 / 范围最小化 / 上游对齐 / 复活检查 / 既有行为变更)· 产 `PL-CHALLENGE-{n}` · 至少 1 实质或「无+理由」· 详 [roles/product-lead.md](../roles/product-lead.md) |
| external(第三视角冷审 · 默认**错开模型** subagent〔≠主会话模型〕· 跨厂商异质 opt-in) | **覆盖方向制** | 🔴 **必覆盖**:**可实现**(技术可行 / 架构影响 / **简洁性 counter-lens**〔过度设计?职责焊错层? · 🛡️ **安全加固/兜底降级 finding 尤其过 ROI**——最难驳的过度设计高发区〕——唯一防过度设计 lens)· **可验证**(AC 可测试性 / 边界场景 / 空值异常分支)+ 🔴 **AI 自主方向 ≥1**(按 feature 特性自选:安全 / 性能 / 数据一致性 / 兼容 / 运维…)。每方向给 finding 或「查过无发现」· 段记 `coverage: [...]`(物化门 `external_coverage_present`) |
| qa / architect(默认并入外审覆盖方向) | 独立冷审(roster 加回时) | 复杂 feature(schema 即交付物 / 测试面大 / 架构决策重)→ `change-review-roles` 加回独立跑 · mandate = 上面覆盖方向的对应拆分 |

**修订与收敛**:PM 逐条响应(ADOPT/REJECT/DEFER)· `adversarial_self_check` 双向——ADOPT 前先质疑 finding 不成立、REJECT 前先 steelman,**两个方向都给实证**(「冷审说得对」「我觉得没事」都不是理由);Round 2+ 重新派**冷** Agent 走验证模式(喂修订 PRD + 上轮 finding + 处置,核实 fix + 找新,防重复提已解决)· 🎚️ **验证轮派发用验证档模型**(校验型任务 · 首轮全量冷审不降档)。

**评审聚焦三问**:业务目标清晰?当前环境可实现?方案恰当简洁?

---

## ④ Output Contract(产物契约)

### `PRD.md`
frontmatter `acceptance_criteria[] + revision_history[]`(均必);body 按 templates/prd.md(§背景/§用户故事/§交付预期/§验收标准/§Out of Scope/§待决策项〔只收用户主权问题〕/§开工前必须想清的)。

### `PRD-REVIEW.md`
frontmatter `reviewers`(= stage_review_roles.goal · 默认 `[pl, external]`)+ `verdicts: {role: APPROVE|NEEDS_REVISION|SKIP}` + 🔴 `review_models`(列表 `- <role>: <实际模型>` · 照实申报 —— 与外审 `review_model` 机器比对错开〔`review_models_staggered`〕· 各路全同模型 = 盲区相关 → complete 拒 · <2 申报存量 skip);body 每冷审 Agent 单独段 · cite PRD 行号 · PL 段 = PL-CHALLENGE 段 · external 段 = 覆盖方向制(记 `coverage: [...]` · 按方向分小节)· 标 `execution: subagent`。schema 单源 = templates/prd.md § PRD-REVIEW schema。异质 opt-in(localconfig `false`)时外审改跑 `state.py external-review` 产 `external-cross-review/goal-<model>.md`(不手写)· PRD-REVIEW external 段引其结论。

### ⏸️ 用户最终确认(R5 · 「重点 review 指引」导读先行)

🔮 **投机窗**(等待窗不闲置的 goal 特化):emit 终确认暂停点后 · **后台派 TECH 草稿 subagent**(读 PRD 终稿候选 · 产物 = worktree 内 TECH.md 草稿 · 🔴 不跑任何 state 命令)——数据支撑:终确认「改:默」台账 ≈ 全默(PRD 此刻变动率≈0 · 冷审已收敛)· goal 等待中位 26m ≈ blueprint 起草中位 27m(等待窗恰好藏下)。用户 `ok` → blueprint-start 后草稿直接接续(TC 起草与冷审照跑);用户有改 → 草稿差量更新。auto/yolo 不适用(确认点 skip · 无等待窗)。🔴 时点纪律:**只在终确认暂停点后投机**(冷审收敛前 PRD 是活靶 · finding 采纳率 80-90% · v1 时点投机必返工)。
🔴 **准入纪律**:PRD §待决策项里**影响表结构 / 模块形态**的开放项 **≤1** 才投机;**>1 或含结构分叉 → 不投机**,等终确认再起草。why:「终确认改:默 ≈ 全默」这个统计前提**只在单决策上成立** —— 多个结构性开放项时,投机草稿必须押某一组合(D1-A/D2-A/…),用户改选任意一项都触发差量重写。实证 SVC-PLATFORM-F260726:两项结构性改选(D1-B/D2-C)→ 一整轮重写 · 该轮 agent token 是初稿的 ~1.3 倍 —— **投机反而变成净亏**。
确认前 emit 导读——📄 **头部第一行回显 PRD 绝对路径**(格式 `PRD: /abs/.../PRD.md` · 让用户直接点开全文核对 · 🔴 绝对路径非相对 · worktree 内产物给 worktree 绝对路径);**首节分两层**:🟡 **你要拍板的**(REJECT/DEFER/升级项 · **每条写成 A/B 选择题 + 我的倾向** · 说人话 · finding id 挪括号)/ ✅ **已处理**(ADOPT 压成主题保 substance · 不逐条 spell 码);余节 ≤2 行:核心取舍/范围收窄/影响面/🔗 **链装配**(🔴 按 3.7 ② **固定三槽 ≤6 行**:流程阶段全链标进/跳 / 评审力度逐 stage「是否×几路×谁×理由」〔零也显式〕/ 四轴证据 · **默认按此执行 · 不要求改就生效** · 想调回一句即可)/🛡️ 兜底策略(PRD 层降级体验类 · 逐项一句「保护什么+成本」· 不许默默做 · 无则「无」)/修订轨迹/残留风险——**全部照实抄落盘产物 · 空节写「无」**(why:导读给没读过 PRD 的人;决策与 ADOPT 平铺等权 = 决策被淹)。然后 R5 标准 1/2/3(1=confirm+`goal-complete --needs-ui <bool> [--needs-blueprint <bool>]` 💡〔装配卡把 blueprint 标「跳」就传 `false` = lite 档 · 标「进」不传即可〕 / **2=继续讨论**〔恒定第 2 项 · 目标与方向 · 想法/疑虑直接说 —— 聊清楚再修订或确认〕/ 3=其他)· 剩余 §待决策项一次性 escalate(早问门问过的不重复)· 🔴 **逐条带「💡 建议 + 一句理由」**(同 §你要拍板的 —— 推荐不了就写明是缺信息/纯偏好/等上游 · **不许只列选项**)。

🔴 **拍板项每条固定四槽**(「你要拍板的」与 §待决策项 escalate 同用 · 实证 CA-F260810:四条 D 项只写「建议 A——<术语压缩>」,B 选项从头到尾没出现,用户被迫追问「大白话解释下 · 上下文是什么」):
- 🎬 **场景**:什么时候会遇到 · 影响谁(一句大白话 —— 导读给没读过 PRD 的人,术语自由的读者拍不了板);
- ❓ **要定什么**:说人话 · 不用术语缩写;
- **选项 A / B / …**:🔴 **每个选项的内容与后果各一句都必须写出** —— 只写推荐项、再让用户「可回 D1=B」而 B 是什么从没出现 = **假选择题**(选项集没到达,用户只能追问或盲从);
- 💡 **建议 + 理由**(既有要求)。

**过场观测**:PL-CHALLENGE 采纳率 → 台账「角色真 finding」列的 **goal 侧 `pl:` 段**(零也要写 `pl:0`)· 早问门「改:默」→「暂停点 改:默」列 —— 长期零采纳 = 过场信号,收紧判据。

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py) · spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `GOAL_SPEC`
- 裁决纪律:[../standards/external-model-usage.md](../standards/external-model-usage.md) §二 · 角色 telos:[../roles/](../roles/)
