# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.345 · CI 失败归因:自己引入的直接修(用户拍板)

> 用户:「ship1 产出 MR 后监控合并的同时检查是否有 pipeline 失败,如果是自己引入的,直接修下。」
> v8.340 已经在查 CI,但停在**任何红都退出**去找修复口 —— base 本来就红时,这会把 AI 支去修它没弄坏的东西。这正是 dev/test 早已解掉的「base 即红」坑,那边用**差分基线**区分「新增回归」与「预存在失败」;本版把同一个形状搬到 CI 上。

### 变更
- **归因层**(`attribute_ci_failures` 纯函数 + `_base_branch_failing` 查 base 分支近期 CI):MR 失败项逐个对照 base —— base 同名 check 也红 → `pre_existing`;base 绿 → `self_introduced`。
- **归因决定动作**(本版实质):**自己引入 → 中断等待、直接修**(走 v8.339 的 MR 窗口期修复口 · **不问用户是否要修** —— 修自己弄坏的东西不是用户主权,是收尾的一部分);**base 预存在 → 不中断**,回显一行继续等合并(别去追别人的账)。
- 🔴 **查不到 base 归到「自己引入」是刻意的保守偏置**:代价不对称 —— 把别人的红当自己的 = 白看一眼;把自己的红当别人的 = 把坏的合进去。与 `test-baseline`「不在基线里就算新增回归」同口径,**不是**「查不到就放行」。
- 对照分支默认取 `state.merge_target`,`await-merge --base <branch>` 可覆盖;push emit 同步带归因(只有归因到自己才给修复口)。绿/pending 不查 base(不为没发生的事付一次网络往返)。

### 测试
`test_ci_attribution_v8345.py` 16 条:归因四象限 · 保守偏置有理由不是断言 · 默认动作是修且不问用户 · 升级边界(修不动才升级)· await-merge 只对自己的红中断 · push emit 归因 · 红时才查 base · spec 双分支 + 点名复用的形状。v8.340 三处锁按收窄后的语义重锚(「任何红退出」→「自己引入的才退出」· 实质「不傻等 CI 红」不变)。全库 1569 绿。

## v8.344 · 子代理禁问用户:问题回路收口主对话(用户拍板)

> case(Grok 宿主消费现场):写测试用例的子代理调宿主的 ask_user_question,把「登录回跳测试写在哪个文件」直接弹到用户屏幕 —— 纯实现细节,设计上永远不该到用户面前。用户拍板:「子代理/subagent 的问题由主对话自行处理,无需找用户确认,只有主对话判断需要用户确认的才交给用户确认」。
> 盘点:回路早就有(NEEDS_CONTEXT → 补上下文重派;stage brief「Substep 中间禁 AskUserQuestion」),但两个口没封:①暂停点纪律管的是**主对话**,子代理侧没有**对着工具名**的红线 —— 对没带全量 context 的执行路径,别处的规则等于不存在(「模式承诺 × 动作点载体」又一格);②派发 prompt 没要求带禁问句 —— 读过规则仍会漏,义务要寄生在必写载体上。

### 变更
- **agents/README §二 新红线(单源 · 对着工具名)**:子代理禁止调用任何「向用户提问/确认」类工具(`AskUserQuestion` / `ask_user_question` / 各宿主变体)—— 缺信息/拿不准 → 写进返回结果(`NEEDS_CONTEXT` + 缺什么)。**主对话二分**:实现细节(测试放哪 · 命名 · 用哪个函数)→ 自答后补上下文重派;真用户主权(偏好/业务取舍/外部事实 · 判据沿用早问门闸 2)→ 按 R5 编号选项 escalate。
- **派发载体寄生**:引擎 `DISPATCH_TIER_REMINDER` 加一行 —— 派发 prompt 必带禁问句,**与 Meta 首行声明同寄生一处**(不另立「记得写」的孤立义务)。
- **SKILL 一行 cite**(❌ 非 🔴 —— 密度门 count < 55 恰好顶满,按判例新增用 ❌)。
- 主对话侧既有纪律不动(两条规则互补不重叠:那条管主对话 substep,本条管子代理)。

### 测试
`test_subagent_no_user_question_v8344.py` 14 条:红线对着工具名锁(行为式表述糊得过、工具名糊不过)· NEEDS_CONTEXT 路由 · 拍板原文入规 · 主对话二分显式(否则红线只堵子代理,主对话原样转抛 = 问题换出口)· 派发载体寄生 + case 实证 · SKILL cite + 密度门 · 既有回路不动。全库 1553 绿。

## v8.343 · 装配维度矩阵 + 计划与显式修订点(用户拍板)

> 拍板链:①「把流程、环节、评审力度 3 个维度拆开,交给 AI 组装,给 AI 强烈的提示有权利精简流程、降低评审力度、决定评审模型,必须做合理的权衡,不能过度保守」②「理论上拆出的力度最小可以直接 dev + ship」③「是否渐进式的流程更合理…或者至少可以修改」④「lite 之后是否需要一个 medium 档,goal 和 blueprint 只有一路冷审」⑤「然后给 AI custom 装配权限」。
> 关于「强提示防保守」:上一版的台账已经写死了结论 —— **权限不等于行为**,0 路评审在 v8.341 之前就合法,AI 照样吃满六路。所以本版把偏置写进**缺省值与可判问句**,不写进措辞强度。

### 变更
- **四维矩阵 + 一开关**:`D1 规格深度`(none/prd/prd_tech)· `D2 证据门`(开/关)· `D3 验证深度`(self/test/test_e2e)· `D4 评审力度`(逐评审点 路数×角色×模型)· 开关 `UI`(**事实判断不是力度**)。验收位置并进 D4:`pm_acceptance` 0 路 = 验收挪到 ship1 MR diff(不是取消,是换地方)。
- 🔴 **链由维度推导**(`derive_chain` / `derive_flow_graph`)—— 不再每档一张静态图。静态图降为**存量 state 回退**,且被「推导边 ⊆ 静态边」机器锁住。收益立刻兑现:medium 是本版实现**中途**加的,只加了一行。
- **六档 = 命名的默认元组 + 一句可判入场问句**(判**风险的种类**,不判改动大小):micro〔无行为面·测试无从写起〕· **floor(新)**〔测试能完全证明 · `dev → ship`〕· tiny〔值得一双眼看 diff〕· lite〔有规格风险要 PRD·方案空间小不写 TECH〕· **medium(新)**〔值得写 TECH·goal/blueprint 各单路〕· full。**档是起手点不是终点**。
- **floor 与 micro 的分界不是「更轻」而是「拿什么换轻」**:micro 拿掉证据门、准入靠白名单兜;floor 保留全部测试证据门(所以能接真逻辑改动),拿掉的是评审与独立验收口。
- 🎛️ **custom 装配**:`init-feature --dims '<JSON>'` 拧任意一维 · 组合连贯性机器校验(N/A ≠ 0 路等七条,不连贯直接拒)。
- 🔁 **计划 + 显式修订点**(取代纯渐进式):计划一次给全(用户看得见整体形状 · 抗棘轮),每个 `stage-complete` emit 带 `plan_checkpoint`(计划 · 剩余链 · **一句可判问句**「有没有出现装配时不知道的事实」)· `revise-plan --dim --to --evidence` 改 · **回显不停等** · ⚖️ **加与减同价**(只让「减」举证 = 保守偏置原样搬回来)· 🔴 **计划可改 · 历史不可改**(已走过的 stage 不许移出链 · dev 交了证据不许回溯关证据门)。修订记 delta + 方向 → **校准闭环的数据源**。
- **计划有了独立的家**:`state.assembly_plan`(此前散在 `execution_hints` 三个 boolean 里,与执行度量混住 → 无法整体渲染/比对/校准)。装配卡改为**从计划渲染**,不再手写(双手写载体必漂);goal 的三个 `--needs-*` 直接写 `dims`。
- 顺手修:守卫顺序 —— 「不可回溯」判定原在一致性校验之后,降维天然带出的不连贯会先报「组合不连贯」,把人支去修 roster 而真答案是「这段你已经走过了」(守卫写了却走不到 = 本框架反复复发的「规则立了没接线」)。

### 测试
`test_plan_dims_v8343.py` 35 条:六档链逐条 · ship 在任何组合都在 · 返工边不因降档消失 · 推导边 ⊆ 静态边 · state.py↔engine 两份实现逐档相等 · 七条连贯性 · 零路 vs N/A 可区分 · CLI 真跑六档 init + custom dims + 拒不连贯 · 修订双向同价 / roster 同步 / 孤儿剪枝报出 / 三类硬边界**各报各的理由** · 门与转移读计划 · `--needs-*` 写穿到 dims · 存量无 plan 回退。既有锁按新载体重锁(v8293 改锁「不许有自己的图」而非锁名字 · v8329/v8337/v8341/v8342)。全库 1539 绿。

## v8.342 · 四档流程回归:tiny 立档 · lite 由 full 装配出来(用户拍板)

> 拍板链:①「我们是否考虑加回多档流程」→ 加;②「tiny dev → review(单路 architect)→ pm_acceptance → ship / lite dev(TC 并行)→ 单路 architect → test → pm_acceptance → ship 这样合理么」;③「lite 是否也要有 PRD,不要 TC,要 verify-ac」;④「lite 是不是可以被 full 装配出来」→ **是**。
> 上一版把「直接做」形态拼成「micro + 手工附加轻门」——「附加」是形容词式承诺,没有载体就不会发生。本版给它正式档位。

### 变更
- **四档、三 preset**:`preset ∈ {full, tiny, micro}`。判据 = **preset 只给「不立就走不通链」的档**(micro 跳 review/test · tiny 无 goal/blueprint 入口);lite 与 full 只差「跳 blueprint」一条边 → FEATURE_FLOW 加 `goal→dev` / `ui_design→dev` 直边 + 装配旋钮,**不加图**。多一张转移图 = 多一处要同步的口径(legacy `lite`/`blueprint_lite` 正是这么烂掉的:三份 flow-key 实现对同一输入解析出两张不同的图)。
- **tiny(新 preset)**:`dev → review〔architect 单路〕 → pm_acceptance → ship` · 零文档(规格 = dev brief **理解卡**,brief 要求开工前回显一遍)· 无 test stage(判据 = 四轴的**验证成本**轴:diff 可验)。与 micro 的分界 = 有没有独立验收口(micro 在 MR diff 上验)。
- **lite(装配形态 · 零 re-init)**:`goal-complete --needs-blueprint false` → 跳 blueprint,不产 TC/TECH/TECH-REVIEW。**PRD 照要、终确认停等照停**(降的是文档与路数,不是拍板权)。dev 前置从「blueprint 完成」回落到「goal 完成」,不是无条件放行。
- **绑定载体换而不撤**:lite 无 TC → AC↔测试绑定改走 PRD 机读块 `acceptance_criteria[].test_refs`,`verify-ac.py --mode test-refs` 校验**非空 + 引用真实存在**(文件存在 · 带 `::用例名` 的名字要在文件里出现)。顺带堵住 TC 模式老坑:TC 点名的函数全仓不存在,覆盖率照样 21/21 全绿。
- **降档不降独立性**:tiny/lite 的单路 architect 仍须错开模型(单路不变式)—— 减的是路数,不是「换个人看」这件事本身。
- **装配环节第三旋钮**:装配卡流程阶段槽从「ui_design / browser_e2e」扩到三段可选,`blueprint 进/跳` 入槽;goal 3.7 减法侧分级表改四档(超低→micro · 低→tiny · 中低→lite · 中/高→full)。
- **prepare 接线**:§2.2 超 micro 白名单 → 推荐 tiny(选项 2 = 继续讨论,守 v8.338);`prepare-check --preset` 让链预览按档出 —— 原实现 `flow_type in FLOW_STAGE_CHAIN` 短路,preset 永远读不到,定了轻档也预览全链(用户看到的链才是他感知到的重量)。
- 顺手修:`build_stage_chain_preview` 用 raw flow_type 查 roster 矩阵恒 miss(键是内部名)· Micro 无 roster 条目才一直没暴露,Tiny 有条目会直接把 architect/pm 吃掉。

### 测试
`test_flow_tiers_v8342.py` 34 条:三 preset/四档不变式 · lite 不许有自己的图 · tiny 四道会死锁的门 · 三实现 flow-key 一致 · lite 旋钮只认显式 false · PRD/test 门不因降档松开 · test-refs 五种情形(含「点名不存在的用例」)· 门不休眠(lite 下换口径而非 skip)· prepare-check 按档预览 · spec 载体。既有锁按新载体重锁:v8329(三旋钮)· v8336(锁退役不锁出边条数)· v8341(四档 + 降档不降独立性)· engine_fixes(goal→dev 已合法 · 非法样本改用 test→dev)。全库 1504 绿。

## v8.341 · 评审力度减法侧分级 +「直接做」形态正名(用户拍板)

> case(jolichatbox 域名配置):v8.334-337 链条全部正常工作(深调研/判断卡/跳 ui·browser),但四轴全低的配置改动仍默认吃满六路评审 —— 用户当场问「这么简单的需求为什么还要那么多 review」,消费 AI 中途 re-init 切 micro 落地开 MR(自评:「按全链启动了 —— 这是错配」)。
> 用户拍板目标形态:**按理说直接开发,完成后架构师 review 一下,PM 验收盯 staging 部署就可以了。**

### 变更
- **3.7 装配判断表补减法侧(加减两侧都要判)**:**超低**(纯配置/删除/文案级 · 无契约面 · diff/断言可验)→ 建议改走 `preset=micro`(同 feature re-init 合法 · 消费实证)+ **micro 附加轻门**(execute 完成后单路 architect diff 冷审〔subagent 错开 · 只拦 BLOCKER〕· PM 验收 = MR diff + 合并后盯 staging〔await-merge 自动带 CI〕);**低**(行为性但小)→ goal `[fast]` 单路合并 · blueprint 0 路 · **review `[architect]` 单路(用户形态)**;中 = 缺省;高 = 加法触发。
- **一致性倒逼**:判断卡/装配卡评审力度行,路数与四轴对不上必须写「为什么不降」(写不出就降)。
- **prepare §2.2「坚持 micro」正名**:行为性小改动亦合法(留痕)+ 附轻门建议 —— 消费 AI 的逃生路径转正。goal brief 同步。

### 测试
`test_review_intensity_tiers_v8341.py` 9 条:超低档 = 用户拍板句 / 低档逐 stage 缺省 / 判据机械 / 一致性倒逼 / 单路仍错开 / prepare 正名 / brief。全库全绿。
