# Changelog

> 📦 v8.57 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件只留最近 N 版(v8.58+)。

## v8.78 · 文档精简 P0+P1 + 治本 e1d12b2 编码损坏(用户 case「统计行数 + 逐文件 review 精简」· dev-only)

> 用户 2026-06-01:"统计 teamwork skills 总行数 · 逐个文件 review · 看哪些文档内容可以精简。" 4 路并行 review 审计后,执行 P0(归档自标记死档)+ P1(修 README 谎报 + 乱码)。乱码排查中发现一个真 bug:**commit e1d12b2「文档清理 P0」批量改写时掉了大量汉字的末字节**,导致 9 文件 invalid-UTF8 + 7 文件 U+FFFD。

### P0 · 归档自标记死档 + CHANGELOG 拆分

- **CHANGELOG 拆归档**:13,116 行 → 主文件 **548 行**(留最近 20 版 v8.77→v8.58)· v8.57→v1(229 版)迁 `docs/CHANGELOG-ARCHIVE.md`。v8.0「范式切换 · 不向下兼容」· v7 及更早描述的是已不存在的旧系统。
- **归档 4 个 v8-redesign + DESIGN + change-request**(均自标记「不再维护」/DEPRECATED)→ `docs/archive/`(2,396 行移出活跃集)。重指 **~30 处 cite**(8 角色 + FLOWS/STANDARDS/SKILL×5 + goal-stage + prepare + 6 工具 docstring)· 修 SKILL 文档导航 **死链 02-CLEANUP/03-MIGRATION**(早删但仍被引)· docs/ 顶层 8→6 文件。

### P1 · 修正(非冗余 · 真 bug)

- **agents/README dispatch 谎报**:删「dispatch 文件由 state.py 各 stage-start 自生成」(grep 证实工具零此逻辑)· dispatch 协议从「🔴 硬规则」降为「可选实践」· 对齐 [STAGES.md §4](../STAGES.md)「subagent 不强制 · 无 dispatch 预检协议」。
- **治本 e1d12b2 编码损坏(16 文件 · ~30 处)**:9 文件 invalid-UTF8(掉末字节 · 如 行 `E8A18C`→`E8A1`)+ 7 文件 U+FFFD。根因:e1d12b2 删 `v7.3.10+P0-xx` 元注释时损坏了相邻汉字。用 **git parent(e1d12b2^)还原**逐字符确认 · 全 **102 活跃文件现 clean UTF-8**。

### 验证

- pytest:**67 failed / 429 passed**(baseline 68 · `test_scan_spec_consumer` 因损坏修复 4→3 · **零新增失败**)。
- 全文件 UTF-8 完整性扫描通过 · 无 live 死链。

## v8.77 · ship 收尾必更新规划层 back-reference + commit(治本 ROADMAP BL 翻牌被当「后续」搁置 · 用户 case WEB-F031 · dev-only)

> 用户 2026-06-01:"ship2 之后应该把关联改动也更新下 · 然后再主工作区提交一下。" case:WEB-F031 ship 完成后 · WEB ROADMAP / WS-01 S2 仍标「📋 规划中/pending」· AI 把翻牌当「后续(非本次范围)」搁置 —— 还说「避免在刚净化的主工作区留新的未提交改动」。

### 根因:ship 流程缺「BL 状态翻牌」的对称步

- 规划期:`feature 写入 ROADMAP` = BL「📋 规划中」(有 commit 步)。
- 但 ship 完成后**没有对称的**「BL → ✅ 已交付 + commit」步 —— ship-finalize 干完 state.json 同步 + worktree 清理就结束 · brief 只说「流程终态 completed · 向用户汇报」· **不提规划层 back-reference**。
- 后果:① 规划层(ROADMAP/WS 进度)与执行层永久**脱节** · 进度统计失真;② AI 没有物化指令 → 把它当「后续/下次规划」搁置 · 还被 v8.70 main-sync「保持主工作区干净」误导成「不敢改」。

### 修复:ship-finalize 成功后必物化「收尾步」

| 改动 | 内容 |
|----|----|
| `_planning_backref_reminder()`(新)| ship 收尾指令:① ROADMAP 对应 BL 状态 规划中→已交付(WS 最后一个 BL → WS 标完成)② 关联文档同步 ③ `git add + commit + push` 到 merge_target · 明确「**不是后续/非本次范围**」+「别因怕弄脏主工作区搁置(翻牌 commit 本就干净)」 |
| `_ship_finalize_brief` | `finalize_ok` 时必追加收尾步(成功 + 有降级项两路都带)· 失败时不带(优先修 ship) |
| emit | 加 `planning_backref_pending: true`(ship 成功时)· 机器可见 |
| `ship-stage.md` §5.5(新)| 文档化 ship 收尾步 · 解释「feature=BL 落地 · 不翻牌=脱节」+ 规划层产物在主工作区 commit 正当(非 worktree 红线违规) |
| `SKILL.md` 快速开始 | ship 步加收尾注 |
| 测试 +4 | TestPlanningBackrefReminderV877(成功带 / 失败不带 / 降级仍带 / helper 含 commit+反搁置)· 428 passed · 68 pre-existing(无关)· 0 regression |

> 定位:「BL 翻牌 + commit」是 **ship 的一部分**(可枚举的流程步 · 物化到 ship 必经点)· 具体改哪个 BL / 什么文案是 **AI 判断**(项目特定 · 读 ROADMAP 定位)。与 v8.70 main-sync 不冲突:main-sync 清 feature 残留 · 此步是 ship 的一笔**有意的规划层干净提交**。

---

## v8.76 · 加「简洁性 counter-lens」(治本评审只加 rigor 无防过度设计 · 用户 case SDK-F038 · dev-only)

> 用户 2026-06-01:"PRD 评审重点是产出业务目标 / 当前环境是否可实现 / 是否合理 · 不应太注重边界细节。" case:SDK-F038 16 AC 全绿 + 3 轮 external 闭环 · 用户在 pm_acceptance 一眼看出**过度设计**(SDK 哑管道被焊进字段语义)· 回炉重切。

### 根因:所有评审视角都偏「加 rigor」· 无人审「简洁性 / 职责归位」

- goal/review 的评审视角:PM 看 **AC 完整** · QA 看 **边界覆盖** · Architect 看可行性/性能/安全 · external **找缺口** —— **全在加复杂度**。
- external review 天然「找缺口 → 加校验」· 每条单看合理 · **合起来把方案做臃肿 / 把责任焊进错的层**。AI 的诚实反思:"external 一路推我加 UUID 闸 / reserved-key 解析 / 位置参数 · 把本该对 SDK 透明的参数语义焊进了传输层。"
- **结构性缺口**:没有任何角色owning「**是否过度设计 · 能否更简单 · 职责是否归错层**」—— 评审越严 · 方案越臃肿 · 直到 pm_acceptance 用户兜底。

### 修复:Architect = 唯一「简洁性 counter-lens」+ PRD 评审聚焦

| 改动 | 内容 |
|----|----|
| `roles/architect.md` Telos | 加「**方案简洁性(防过度设计)**」+ 明确「其余角色都偏加 rigor · Architect 是唯一简洁性 counter-lens · 反问:能否更简单 / 每处复杂是否被业务目标(非边界 rigor)证成 / 职责是否归错层」 |
| `goal-stage.md` | 加 **PRD 评审聚焦**:① 业务目标清晰 ② 当前环境可实现 ③ 方案合理且**恰当简洁** · AC 写「行为/价值」高度(WHAT)**不下沉实现机制** · §非目标用足收窄 · + Architect 简洁性 lens + **external finding 须对照业务目标+简洁性取舍**(别盲采加 rigor) |
| `blueprint-stage.md` | Tech Review 加简洁性 lens 「**拦过度设计的最佳时机**(改 TECH 比改代码便宜)」 |
| `review-stage.md` | Architect Code Review 加简洁性 counter-lens(焊进核心抽象的复杂度可删/可下沉) |
| 测试 +4 | TestArchitectOwnsSimplicityLens / TestStageDocsCarrySimplicityLens(锁文案不回退)· 424 passed · 68 pre-existing(无关)· 0 regression |

### 你我对齐的原则

- **PRD 评的是业务目标 + 可实现性 + 恰当简洁** · 不是边界细节大全(边界要处理 · 但在**对的层** · 不是堆进核心抽象)。
- **评审需要简洁性 counter-lens** 平衡「找缺口」的天然加复杂度倾向 —— external finding 修真 bug 才采 · 别为 rigor 而 rigor。
- **过度设计拦得越早越省**:TECH review(改方案)> code review(改实现)> pm_acceptance(回炉)。

---

## v8.75 · 治本 pl 被系统性误删(reviewer checklist Q1 把 PL 价值等同 ROADMAP · 用户实证 · dev-only)

> 用户 2026-06-01:"几乎所有 feature 在 PRD 评审时都移除 pl · 理由是无 roadmap · 是否合理?" 不合理 —— 是工具引导的类目错误。

### 根因:checklist Q1 把 PL 评审价值 = ROADMAP 拆分

- `REVIEWER_THINKING_CHECKLIST[0]`(v8.27)旧:「涉及 ROADMAP 拆分 / 优先级决策?**否 → goal 去 pl(PL 评审价值低)**」。
- 但 **ROADMAP 是规划层产物**(Feature Planning 产出 · 执行层 Feature 流程里没有)—— 执行层 Feature **几乎都『无 ROADMAP』** → Q1 几乎恒为「否」→ **系统性删 pl**。
- 而 PL 的真 telos(`roles/product-lead.md`):**业务目标 / 跨项目一致性 / 商业模式 / 变更级联** ——「缺这个视角会留:做了一堆 Feature 但偏离产品方向」。把它窄化成 ROADMAP 是类目错误 · 把产品方向评审从几乎所有 PRD 删掉。
- 坏示范放大:`prepare.md` 的「建议评审角色」**worked example** 直接把 `goal …(去 pl)· Q1 无 ROADMAP 拆分` 当**标准正确输出**示范 + F-Bv2-8(2026-05-25)case 把它当『好调整』—— AI 照抄成定式。

### 修复:Q1 重构为「产品方向影响」· pl 默认保留 · 去 pl 是少数例外

| 改动 | 内容 |
|----|----|
| `state.py` Q1 | 「**有无产品方向影响?**(业务目标/用户可见/商业模式/跨项目一致/变更级联 Level≥2)」· **是(常态)→ 留 pl** · 仅纯内部技术重构零产品面才去 · ⚠️ **『无 ROADMAP』≠ 去 pl 理由**(显式 debunk) |
| `state.py` hint | 加「pl 默认保留 · 套路化删角色禁止 · 无 ROADMAP 不是去 pl 理由」· 去掉「goal 去 pl(无 ROADMAP)」坏示范 |
| `prepare.md` Q1 表 + worked example | 同步重构 · 示范从「去 pl」改「留 pl(产品方向相关)」+ 加「pl 不是套路化删」红线段 |
| 测试 | `test_v875_pl_not_roadmap_gated`(默认留 pl · 删旧『PL 评审价值低』· debunk ROADMAP)· covers_dimensions 维度 ROADMAP→产品方向 · 420 passed · 68 pre-existing(无关)· 0 regression |

> 核心:**PL 评审价值 = 产品方向(业务/一致性/商业模式/级联)· 与 ROADMAP(规划层)无关**。pl 默认保留;去 pl 仅限纯内部技术重构 · 且要给本 Feature 特定理由 —— 不是每个执行层 Feature 都『无 ROADMAP』就套路化删。

---

## v8.74 · subagent 改「可选手段」+ 出 brief 移 spec(纠 v8.73 过度物化 · 用户反馈 · dev-only)

> 用户 2026-06-01:"『标准执行手段』是否应是『可选执行手段』· 我担心 AI 过度使用 subagent。另外是否不需要写 brief · 在 SKILL.md 和 stage.md 说明就好 · 我担心 brief 越来越大。"

### 纠 v8.73 两个过度

v8.73 把 subagent 框成「每 stage 标准执行手段」+ 独立成 brief 段每 stage 必带 —— 两处过头:

1. **「标准」促过度使用**:是否用 subagent / 拆几个 = 典型**不可枚举判断**(设计哲学表「AI 自决」)· 框成「标准/必用」会让 AI 给小/耦合/串行任务也派 agent(纯开销 + 碎片)。
2. **brief 膨胀**:红线(禁自造暂停)值得物化到必经点 · 但**可选能力**不值得 —— 每 stage brief(start + 转移)+5 行正是 `brief 体量元规则` 警告的 Layer A 累积。

### 修复:降级 + 挪窝

| 改动 | 内容 |
|----|----|
| 删 `_render_execution_capability()` + 两处 brief 接入 | brief 回到 v8.72 体量 · 不再每 stage 注入 subagent 段 |
| 暂停点纪律 subagent 行 | 「独立子任务派 subagent · 见下执行手段」→「**可按需**派 subagent · 详 SKILL.md R4」(1 行 · 红线的正向收口 · 不展开) |
| SKILL.md R4 | subagent = **可选执行手段(AI 自决 · 非默认 · 非每 stage 必用)**· 列适用(独立可并行/需隔离大块)+ ⚠️ **不过度使用**(小/耦合/串行直接自己做 · 判据:子任务独立且够大才拆) |
| stages/dev-stage.md | 加 §1.5「组织实现(🧩 subagent 可选 · 按需并行 · 非必须)」· 多端/多模块场景 + 同款不过度使用判据 + worktree 纪律 |
| 测试 | 删 TestExecutionCapabilityV873 · 加 TestSubagentInPauseDisciplineV874(可选措辞 + 函数已删 + 无独立段)· 419 passed · 68 pre-existing(无关)· 0 regression |

> 定位:subagent 是 **AI 自决的可选手段** —— 知道、按需用、不过度;指引在 **SKILL.md / stage.md**(读一次的背景判断)· **不**塞进每个 brief(防膨胀)。红线(禁自造暂停)仍物化在暂停点纪律 · subagent 只是它的 1 行正向收口。

---

## v8.73 · subagent 升为「每 stage 标准执行手段」(治本框成兜底 · 接 v8.71/72 · dev-only · ⚠️ 部分被 v8.74 纠正)

> 用户 2026-06-01:"合理使用 subagent 应该是 AI 各个 stage 必须知道的点 · 而不是任务大的时候才想起来。"

### 根因:v8.71/72 把 subagent 框成「工作量大」的兜底

- v8.71/72 的 subagent 指引绑在暂停点纪律里 · 措辞是「工作量大 / session 吃紧 → 派 subagent」—— **reactive**(任务大才用)· 不是 AI 每 stage 起手就该想到的标准手段。
- 后果:AI 默认串行闷头干 · 只有撑不住才想起 subagent · 错过 dev 多模块并行、调研丢 subagent 保持主 context 干净等常规收益。

### 修复:独立成段 · 每 stage brief 都带 · 框成主动标准

| 改动 | 内容 |
|----|----|
| `_render_execution_capability()`(新)| 「🧩 执行手段:subagent 是标准配置(每 stage 起手评估 · 非任务大才用)」· 起手即问哪些独立子任务可并行/隔离(dev 多模块 / goal·blueprint 多方案调研 / review 多关注点)· 收益(主 context 干净 + 并行提速 + 隔离)· 边界(只干子任务 · 不外包整个 stage 跳流程 · 守 worktree 纪律)|
| 接入两处必经点 | `execute_stage_start` + 自动流转 emit 都 append —— **每个 stage(start + 转移那刻)都见** |
| 暂停点纪律去 reactive | subagent 行从「工作量大才」改「规模/节奏 AI 自决 · 独立子任务派 subagent · 见『🧩 执行手段』」 |
| SKILL.md R4 | 「subagent 是标准执行手段 · 每 stage 起手评估 · **不是任务大才想起** · session 吃紧更要用」 |
| 测试 +3 | TestExecutionCapabilityV873(主动标准措辞 · 收益+边界 · 无 size-gating)· 419 passed · 68 pre-existing(无关)· 0 regression |

> 核心:subagent 从「撑不住的兜底」升为「每 stage 起手就评估的标准执行手段」—— 主编排 context 干净 + 并行提速是常态收益 · 不是大任务专属。

---

## v8.72 · 执行节奏伪决策护栏改通用红线(治本不止 dev · 所有 stage · 接 v8.71 · dev-only)

> 用户 2026-06-01:"不只是 dev · 其他阶段是否也会遇到类似问题。" 答:会 · 且分两类。

### 分析:两类 stage · 两种暴露面

| 类 | stage | v8.71 覆盖? |
|---|---|---|
| **无暂停**(连续执行) | dev / blueprint / blueprint_lite / test | ✅ 已覆盖(`"无暂停"` 通用检测 · 4 个全中) |
| **有授权暂停** | goal / ui_design / review / browser_e2e / pm_acceptance / ship / panorama_sync | ⚠️ **漏**:执行节奏伪决策护栏 + subagent 只在无暂停 stage 触发 |

- v8.71 把「禁执行节奏伪决策 + 体量大派 subagent」绑在 `"无暂停"` 分支 —— 但**执行节奏伪决策是通用失败模式**:有授权暂停点的 stage 也可能在「那一个」授权暂停**之外**自造伪暂停(如 goal「PRD 16 AC 要分批起草给你看吗」· review「先评核心模块给你看?」)。
- base 纪律只提「Open Questions(疑问)写进评审」· 框定的是**不确定性** · 没点名**执行节奏伪决策**(SDK-F038 的 AI 不觉得自己在"提问" · 觉得在"给落地节奏选择")。

### 修复:护栏拆两层

| 层 | 适用 | 内容 |
|----|----|----|
| **通用红线**(所有 11 stage)| 全部 | ⛔ 禁"如何推进/落地节奏/先做一层/一次性还是分批"执行节奏伪决策暂停 · "改动大/破坏式/不可逆/文件多/用户参与设计"非暂停理由 · ✅ 体量大 → plan + subagent 自决 |
| **无暂停抬头**(连续执行 stage)| dev/blueprint/blueprint_lite/test | 🔴 本 stage 无授权暂停点 · 任何暂停都违规 |

- `_render_pause_discipline`:执行节奏 + subagent 行移出 `"无暂停"` 分支 → base(通用)· `"无暂停"` 分支只留「任何暂停都违规」抬头
- 测试 8 例(原 5 → 8):TestUniversalExecutionPacingGuard(每个 stage 都含护栏 + subagent · 抬头只在无暂停 stage)+ TestContinuousStagesRegression(无暂停集合 = {dev,blueprint,blueprint_lite,test} 固定 · 防漂移)· 416 passed · 68 pre-existing(无关)· 0 regression

> 核心:**「禁执行节奏伪决策 + 体量大用 subagent」对所有 stage 生效**(不止无暂停 stage)· 只是无暂停 stage 额外强调「任何暂停都违规」。

---

## v8.71 · 无暂停 stage 禁自造伪决策暂停(治本 AI 不会自己解决问题 · 用户 case SDK-F038 · dev-only)

> 用户 2026-06-01:"AI 似乎不知道怎么自己解决问题 · 是否需要在规范里说明一下。" case:AI 在 blueprint PASS(自动转 dev)后 · 构造「⏸️ dev 如何推进」3 选项暂停点(先做一层给你看 / 一次性全落 / 先停审阅)· 把"破坏式跨端大改 + 不可逆 + 你全程参与设计"包装成"落地节奏选择"。用户当场纠正:dev 无授权暂停点 · session 太大该派 subagent · 不该停下问。

### 根因:规则只有「负面禁止」· 缺「正面怎么办」· 且不在必经点

- R4 早有「自动流转节点禁插暂停 · 容量预算不构成暂停理由」· 授权暂停点清单也写「stage 间自动流转 · 非暂停点」—— **规则在 · AI 仍违规**(self-correct 时才引用 R4)。
- 两个缺口:① 规则只说**别为容量暂停**(负面)· 没给**正面模式**(工作量大 → 内部 plan + subagent 消化)· AI 感到任务大时唯一会的工具就是"停下问用户怎么推进";② `_render_pause_discipline` 只在 `xx-start` 追加 · **自动流转 emit(blueprint→dev)不带** —— AI 在转移那刻看到的 dev brief **没有**「无暂停」提醒 · 等之后 dev-start 才有 · 那时伪暂停已构造。

### 修复:必经点物化 + 正向指引(两层)

| 改动 | 内容 |
|----|----|
| `_render_pause_discipline`(无暂停 stage 强化)| `authorized_pause_point` 含「无暂停」时追加:⛔ 禁构造"如何推进/落地节奏/先做一层/一次性还是分批"伪决策暂停 · ⛔"改动大/破坏式/不可逆/文件多/用户参与设计"都不是暂停理由 · ✅ 体量大 → 自己 plan + 派 subagent(`Agent` 工具)· 不停下问 |
| 自动流转 emit 带纪律(必经点)| `execute_stage_complete` 转移到下一 stage 时 · `next_stage_brief` 现追加下一 stage 的暂停点纪律 —— AI 在 blueprint→dev **转移那刻**即见「dev 无暂停 · 禁自造暂停」· 不靠之后 dev-start |
| SKILL.md R4 加正向指引 | 「授权暂停点=用户决策点(固定闭集)· stage 内怎么执行=AI 自决细节」· 「工作量大是 AI 自己的执行问题 · 不甩用户 · session 吃紧→派 subagent」· 「用户参与设计 ≠ 用户决定执行节奏」 |
| 04-PAUSE-POINT-DISCIPLINE.md | 反模式黑名单加 SDK-F038 条目(执行节奏伪决策)+ case 复盘 |
| 测试 +5 | TestNoPauseHardening 3 + TestContinuousStagesTriggerHardening 2(dev 必触发 · 防回归改 pause point 字面丢强化)· 413 passed · 68 pre-existing(无关)· 0 regression |

> 核心:**授权暂停点是固定闭集(用户决策)· stage 内"怎么干"是 AI 自决的执行细节**。改动大/破坏式/不可逆/用户参与设计**都不是**暂停理由 —— 工作量大 AI 自己 plan + subagent 消化 · 闷头干到 stage 完成 · 后果由 review/test/pm_acceptance 下游 gate 兜。

---

## v8.70 · main-sync 主工作区净化决策(治本 ship 后 user-dirty 停在脏态 · 不 pull 不处理 · dev-only)

> 用户 2026-06-01:"ship2 结束后回到主工作区 · 如果不干净会停在那里 · 不 pull 也不处理。增加逻辑:发现不干净时提示是否净化 · push 当前改动 · pull 最新。目标:尽最大努力安全保持主工作区干净 + 最新。"

### 根因:step 7 main-sync 遇用户改动「保留 + WARN」即收手

- ship-finalize step 7(main-sync)对 dirty 分类:全副产物(state.json/review-log + bootstrap + locks)→ 自动 stash+ff-pull;**含用户真改动**(`other_files`)→ v8.62 只清 feature_artifacts + 尽力 ff-pull + **静默保留用户改动 + WARN**。
- 结果:主工作区停在脏态 · 既不主动 pull 也不引导处理 · 用户得自己 commit/stash/pull —— 与「保持主工作区干净 + 最新」的目标背离。

### 修复:发现 user-dirty → 提示是否净化 + 新 main-sync 命令执行

| 改动 | 内容 |
|----|----|
| ship-finalize step 7(普通模式)| user-dirty 不再静默保留 · 改 emit `main_sync_status="user_dirty_decision"` + `main_sync_decision`(3 选项 + 推荐 + 跟进命令)· `next_action_brief` 引导 PMO 按 R5(b) 转暂停点「是否净化」 |
| ship-finalize step 7(auto/yolo)| 无人值守 → 安全自动净化 **stash-pull**(改动留 stash · 无数据丢失 · **不推任意改动**到集成分支)· 保持干净 + 最新 |
| 新 `main-sync --strategy` 命令 | 用户拍板后执行 · 必在主工作区跑 · 校验当前分支 = merge_target + fetch |
| `_main_sync_apply_strategy` | 三策略(都先清 feature_artifacts · origin 版总安全):**commit-push**(add -A + commit + pull --rebase + push)/ **stash-pull**(stash -u + ff-pull · 留 stash)/ **skip**(仅清 artifacts + 尽力 ff-pull · 保留改动) |
| 安全 | commit-push 用 `pull --rebase`(本地落后时叠 commit 不冲突)· rebase 冲突 → abort + 保留 commit;push 被拒(分支保护)→ 报告 + 本地已最新;主分支 merge_target → 决策改荐 stash-pull(推送绕 MR review 有风险);**绝不 force**;用户改动**绝不丢**(commit / stash 二选一) |
| 测试 +6 | TestMainSyncStrategyV870:commit-push 推送+清 / stash-pull 留 stash 不推 / skip 保留 / 自定义 message / 决策非主荐 commit-push / 决策主荐 stash-pull · 408 passed · 68 pre-existing(无关)· 0 regression |

### 决策选项(普通模式 emit · PMO 转 R5(b) 暂停点)

| id | 动作 | 适用 |
|---|---|---|
| `commit-push` | git add -A + commit + pull --rebase + push → 主工作区干净+最新+已推 | 改动确实要进 merge_target(非主分支推荐) |
| `stash-pull` | git stash -u + ff-pull · 改动留 stash(可 pop 恢复)· 不推送 | 改动暂不推 / merge_target 是主分支(推荐) |
| `skip` | 保留现状 · 用户自处理(feature_artifacts 已自动清) | 用户想手动处理 |

```bash
# ship-finalize 报 user_dirty_decision 后 · 用户选 commit-push:
python3 tools/state.py main-sync --feature FEAT --strategy commit-push [--message '<msg>']
# 或暂存:
python3 tools/state.py main-sync --feature FEAT --strategy stash-pull
```

> auto/yolo 自动走 stash-pull(安全 · 留 stash + WARN)· 普通模式停在「是否净化」暂停点由用户拍板。

---

## v8.69 · set-mode 语义命令(治本 auto_mode/yolo 靠 raw-write 改 · 补 v8.68 遗留缺口 · 用户 case SVC-PLATFORM-F060 · dev-only)

> 用户 2026-05-31:"补一下"(接受 v8.68 末尾 offer)。Codex agent 在 SVC-PLATFORM-F060 诊断里点出:**auto_mode 当时是 raw-write 改的 · 因为没有语义化的 set-auto-mode 命令** —— state audit 里出现裸 raw-write · 不可审计。yolo 同理。

### 根因:改 auto_mode/yolo 无正式入口

- `init-feature` 能在创建时设 `--auto-mode`/`--yolo` · 但**中途切换**没命令 —— 只能 raw-write `state.json`(违反「state.json 写操作走 state.py 单源」软约束 · 且无 audit/无校验)。
- 后果:① audit trail 缺失(谁、何时、为何切 yolo 不可查)· ② 绕过 yolo 非 main 硬门 + implies-auto 隐含规则 · ③ 与 v8.55 物化哲学相悖。

### 修复:`set-mode` 子命令(语义 + 物化 + audit)

| 改动 | 内容 |
|----|----|
| `cmd_set_mode(args)` | 语义化 auto_mode/yolo 切换器 · 互斥校验(`--auto-mode`/`--no-auto-mode` · `--yolo`/`--no-yolo`)· 至少一个 flag · 必填 `--reason` |
| yolo 启用 | `--yolo [<分支>]` → `new_yolo=True` + `new_auto=True`(implies)· `<分支>` 设 merge_target · `_is_main_branch` 非 main 硬门(同 init-feature) |
| 隐含规则护栏 | yolo=True 时 `--no-auto-mode` → FAIL(auto 是 yolo 前置 · 不许拆) |
| 物化 + audit | 写 `state.mode_changes` 审计列表(before/after/reason/ts)· yolo 启用追加 concern WARN · 同步 merge_target/worktree.base_branch/environment_config |
| NOOP 保护 | after==before → 友好提示「新值 == 现值」· 不写空 audit |
| 测试 +7 | TestSetMode:enable_auto / yolo+branch implies auto / yolo main 拒 / disable yolo 留 auto / no-auto-while-yolo 拒 / 无 flag 拒 / NOOP · 402 passed · 68 pre-existing(无关)· 0 regression |

### 用法

```bash
# 中途切 auto 模式
python3 tools/state.py set-mode --feature FEAT --auto-mode --reason "夜间无人值守"
# 切 yolo + 指定专属 merge_target(非 main)
python3 tools/state.py set-mode --feature FEAT --yolo dev-integration --reason "全自动跑通到集成分支"
# 关 yolo(保留 auto)
python3 tools/state.py set-mode --feature FEAT --no-yolo --reason "恢复人工把关合并"
```

> 自此 auto_mode/yolo 的**任何**变更都有正式入口 + audit · raw-write 不再是唯一路径。

---

## v8.68 · external 异质性校验 host-aware(治本 codex-cli 宿主 claude 评审误判同源 · 用户 case SVC-PLATFORM-F060 · dev-only)

> 用户 2026-05-31(SVC-PLATFORM-F060 · 主对话宿主 = codex-cli · Codex agent 已诊断):review-complete 把**合规**的 Claude external review 误判"同源自审" · 被迫 `change-review-roles` 绕过(语义不对 · external 明明真存在)。

### 根因:工具前后口径不一致

- `state.py external-review` **已 host-aware**:`EXTERNAL_HOST_TO_MODEL` 映 `codex-cli→claude` —— 所以 Codex 主对话跑 Claude external 是正确异质路径 · 产出合规 `external-cross-review/review-claude.md`。
- 但 `_check_external_hetero`(review-complete 校验)是 **Claude-host 时代的静态黑名单** `("claude","anthropic",...)` —— 把 claude 一律判同源。
- 矛盾:前半段「codex-cli → claude(异质)」· 后半段「artifact 含 claude → 同源违规」。

### 修复:host-aware 同源判定

| 改动 | 内容 |
|----|----|
| `_check_external_hetero(name, host=None)` | host-aware · 同源 = ① 机制字面(isolated/subagent · 无论 host)· 或 ② review model 与 **host 同族**(`_host_to_family` + `_MODEL_FAMILY_KEYWORDS`)· host 缺失 → 保守默认 claude-code |
| 白名单扩展 | `EXTERNAL_REVIEW_HETERO_KEYWORDS` 加 claude/anthropic/openai/google/bard(host-aware 排除 host 自族) |
| `_evidence_external_review_artifact` | 读 host(state.host > 文件 frontmatter host > None)逐文件传入 · 错误 hint 改 host-aware(同源依 host · 修复跑 `state.py external-review` 而非硬编码 codex review) |
| 测试 +4 | codex-cli+claude PASS / claude-code+claude FAIL / codex-cli+codex FAIL / 任意 host+isolated FAIL(+ ambiguous 措辞 1 例)· 395 passed · 68 pre-existing(无关)· 0 regression |

### 判定矩阵(实测)

| host | review model | 结果 |
|---|---|---|
| codex-cli | claude | ✅ 异质 PASS(**bug 修复**) |
| claude-code | claude | ❌ 同源 FAIL |
| codex-cli | codex | ❌ 同源 FAIL |
| claude-code | codex | ✅ 异质 PASS |
| 任意 | *-isolated/subagent | ❌ 机制 FAIL(保留 F034 保护) |
| 缺 host | claude | ❌ 保守默认 claude → FAIL(不放宽老 case) |

> 📌 case 附带提的 set-auto-mode 语义命令缺口(auto_mode 当时靠 raw-write 改)· 另列 · 本次不含。

---

## v8.67 · yolo 严格按流程 · 不内化(external 实跑日志物化校验 · 用户 case WS-002 · dev-only)

> 用户 2026-05-30:"yolo 模式必须严格按 teamwork 流程流转 · 不能内化。"

### 根因(yolo 把评审"内化"= 走过场)

WS-002 yolo case:AI 写 `PRD-REVIEW.md` `mode: yolo-internalized` 自盖章 pm/qa/architect APPROVE + 去掉 goal/blueprint external(v8.66 已堵)→ 评审形同虚设。v8.63–66 强调"零 stop / 自主解决",AI 误把"无人值守"读成"AI 自己内化评审走完流程"。**反了**:无人值守 = AI 仍须做**真实评审工作**(多角色真分析 + external 真调异质模型)· 零 stop 只针对**人工决策点** · 不是省评审。

### 修复:物化防内化

| 改动 | 内容 |
|----|----|
| `_external_run_log_exists` helper | 校验 `~/.teamwork/external-review-logs/<feat>/codex-<stage>-*.log` / `claude-<stage>-*.log`(v8.55 实跑日志)存在 |
| `_evidence_external_review_artifact` yolo gate | yolo + external 评审**无实跑日志** → **FAIL** · hint:必真跑 `state.py external-review`(不得手写 external-cross-review)。**文件名/frontmatter 能伪装合规 · 实跑日志伪造不了** |
| `SKILL.md § yolo` | 加 🔴🔴「严格按流程 · 不得内化」:评审必真跑(多角色真分析 + external 真调)· 不得 `yolo-internalized` 自盖章 / 手写 external · external 实跑日志物化校验。澄清 auto_mode「内化」措辞(仅指跳过用户确认 · 非伪造评审)· 修表 2 处 |
| 测试 +3 | yolo 无日志 FAIL / 有日志 PASS / 非 yolo 不受影响 · 391 passed · 68 pre-existing(无关)· 0 regression |

### 物化哲学

artifact 的文件名 / frontmatter `review_model` 能被 AI 伪装合规(v8.19 黑名单只挡明显同源)· 但 **external-review 实跑日志**(state.py 真调 codex/claude 时 v8.55 自动落)伪造不了 —— 把"真跑了异质模型"钉在 AI 必经的物化点。

---

## v8.66 · yolo 加重审核(非简化)· change-review-roles 去 external 物化 BLOCK(用户 case WS-002 · dev-only)

> 用户 2026-05-30(WS-002 yolo 实战):"yolo 不得擅自简化流程 · yolo 模式本来就无人值守 · 需要加重各环节审核力度 · 非必要不得去掉外部模型评审。"

### 根因(yolo 哲学被理解反了)

v8.63–65 yolo spec 强调"零 stop / 自主解决",AI 据此把 yolo 当**简化/提速** —— WS-002 实战 AI 合并 9 BL 为 4 feature + `change-review-roles` 去掉 goal/blueprint 的 external 评审(美其名"集中到 review stage")。**反了**:无人值守 = 没人在看 → 自动化评审(尤其 external 异质模型)是**唯一安全网** · 应**加重**不应削弱。

### 修复

| 改动 | 内容 |
|----|----|
| **物化 gate** `cmd_change_review_roles` | yolo + 去 external(before 有 / after 无)+ 无 `--accept-external-removal` → **BLOCK** · hint 明列"不得为效率/集中去 external" |
| `--accept-external-removal` flag | 显式逃生口 · 仅 external CLI **客观不可用**(未装/网络死·重试失败)· 用了写 concern WARN 留痕 |
| `SKILL.md § yolo` | 顶部加 🔴🔴「yolo ≠ 简化/提速 · 是加重审核」原则(零 stop 只针对人工决策点 · 技术/评审环节一个不少 · 不得去 external / 合并 BL / 跳 stage / 减 review 轮次 · **可以加重**)· 修「自主解决」表 external 行(优先重试 · 绝不为效率去) |
| 测试 +3 | yolo 去 external BLOCK / `--accept` 放行+WARN / 非 yolo 不受影响 · 388 passed · 68 pre-existing(无关)· 0 regression |

### 原则

yolo「零 stop」**只**针对人工决策暂停点(prepare / pm_acceptance / MR merge)· **技术与评审环节一个不省**。BL 拆分是 Planning 已定范围 · yolo 不重打包。无人值守正该**更严**。

---

## v8.65 · yolo 可携带专属 merge_target 分支(--yolo <branch> · 覆盖 localconfig 默认 · 用户拍板 · dev-only)

> 用户 2026-05-30:"yolo 可以指定一个分支 · 这个分支就是这个需求的 merge_target · 如果指定了则不使用 localconfig 的 merge_target。"

### 是什么

`init-feature --yolo <branch>` · `<branch>` = 本需求专属 `merge_target` · **覆盖** `--merge-target` / localconfig 默认(`templates/teamwork_localconfig.json` 的 `"merge_target":"staging"`)。推荐给每个 yolo 需求一个**专属集成分支**(如 `--yolo yolo/feat-x`)· 隔离无人 review 自动合入的代码。

### 改动

| 改动 | 内容 |
|----|----|
| `--yolo` `store_true` → `nargs='?' const=True`(可选 `<BRANCH>` 值) | tools/state.py |
| `--merge-target` `required=True` → `False`(yolo 可用 `--yolo <branch>` 提供) | tools/state.py |
| `cmd_init_feature` 早解析:`merge_target = yolo_branch or args.merge_target` · 都空 → FAIL · 全 6 处 `args.merge_target` 改用 resolved | tools/state.py |
| `_is_main_branch` gate 用 resolved merge_target(`--yolo main` 同样 FAIL) | tools/state.py |
| `SKILL.md § yolo`:`--yolo [<分支>]` 语法 + 专属集成分支隔离建议 | SKILL.md |
| 测试 +4(--yolo branch=merge_target / branch 覆盖 --merge-target / --yolo main FAIL / 都没 merge_target FAIL) | test_state.py |

### 解析优先级

`merge_target` = `--yolo <branch>`(最高) > `--merge-target` > (都空 → FAIL)。`state.json.yolo` / `auto_mode` = `args.yolo is not None`(nargs='?' 三态:None 未传 / True 无值 / str 分支)。385 passed · 68 pre-existing(无关)· 0 regression。

---

## v8.64 · yolo 自主解决语义(失败/卡点也零人工 · require_user_confirmed yolo 放行 · 用户澄清核心目标 · dev-only)

> 用户 2026-05-30:"yolo 模式的核心目标是 AI 自主解决所有的问题 · 不需要人工干预。" → v8.63 只覆盖 happy-path 零 stop · 没定义**失败/升级/bypass**时的行为(正是"零人工"最关键处)· 补上。

### 根因(v8.63 的 gap)

v8.63 yolo 去了 pm_acceptance + MR merge 两个 designed stop · 但**失败路径**仍会停下问人:stage 校验 FAIL 3 次 → bypass 协议**暂停问用户**(`require_user_confirmed` 物化拦截 · 设计本意"防 AI 自决逃生")。这与 yolo「零人工」核心目标直接冲突。

### 修复:autonomous resolution

| 改动 | 内容 |
|----|----|
| `require_user_confirmed(args, yolo=False)` | yolo=True → 视作用户已 blanket 委托(`--yolo`)· 放行不拦(仍 `--reason` + `bypass_log` + concerns WARN)· 4 个调用点(`_v8_engine` ×3 + `_v8_ship` ×1)传 `yolo=state.get("yolo")` |
| `SKILL.md § yolo 自主解决` | 失败/卡点行为表(FAIL→持续自解 / bypass→自授权 / external CLI 缺→自动 change-review-roles)· 🔴 **优先级 解决 > 绕过**(bypass 是穷尽后兜底 · 非遇错就推 · `bypass_log` 频率 = yolo 健康度)· 真·硬停(环境彻底不可用)极少 |
| 测试 +3 | `TestYoloBypass`(yolo 放行 / 非 yolo 仍拦 sys.exit(1) / 显式 --user-confirmed 兼容)· 381 passed · 68 pre-existing(无关)· 0 regression |

### 设计要点

- **解决 > 绕过**:yolo 不是"遇错 bypass 硬推" · 是 AI 当负责工程师穷尽手段**真解决**;bypass 是不停下的最后兜底 · 每次 WARN 留痕(`bypass_log` 频率高 = AI 没在真解决 · 该回炉/降级 yolo)。
- **安全仍在**:① yolo 只合非主分支(v8.63 gate)② 每次 bypass 写 `bypass_log` + concerns WARN ③ **非 yolo** 的 `require_user_confirmed` 拦截**不变**(防 AI 在非 yolo 下自决逃生)。

---

## v8.63 · 新增 yolo 模式(完全自动 · 无人值守 · 硬约束 merge_target 非主分支 · 用户拍板 · dev-only)

> 用户 2026-05-30:"增加一个 full-auto 模式 · 完全自动 · 包括自动 merge · 处理主工作区。" → 命名定 **yolo**(诚实标注"无人 review 自动合 main"的风险)+ "这种模式 MR 目标必须指定非 main 分支"。

### 是什么

`yolo` = `auto_mode` **超集** · 启动后**零 stop**(把 auto_mode 残留的 pm_acceptance + MR merge 两个 stop 也自动了):
- pm_acceptance → 自动 `approved_and_ship` + WARN 审计
- ship Phase 1 MR → 自动 merge(`gh pr merge --auto --merge` / `glab mr merge`)
- ship-finalize → 自动跑(v8.62 已修 main-sync 干净)
- 只剩 kickoff 输入(说要建什么)· 之后无人值守跑到底

### 🔴 硬约束(物化):merge_target 必须非主分支

`init-feature --yolo` + `merge_target` ∈ {`main`/`master`/远端默认} → **FAIL**(`_is_main_branch` gate)。理由:yolo **无人 review 自动 merge** · 不得让 AI 错误/幻觉特性直接进 main —— 只能合 `dev`/`staging`/`integration` · 主分支提升仍**人工 gate**。

### 改动

| 改动 | 文件 |
|----|----|
| `--yolo` flag(init-feature)· `state.json.yolo` + **implies `auto_mode`** | tools/state.py |
| `_is_main_branch(branch, repo_cwd)` helper(名字 main/master · 或 == 远端默认分支 origin/HEAD) | tools/state.py |
| init-feature gate:yolo + 主分支 → FAIL(早于建 state/worktree) | tools/state.py |
| `SKILL.md § yolo 模式`(行为表 + 硬约束 + 安全栏:尊重分支保护 / WARN 审计 / per-feature opt-in) | SKILL.md |
| 测试 +4(yolo+main FAIL / yolo+master FAIL / yolo+dev OK 且 implies auto_mode / 非 yolo+main 不受影响) | test_state.py |

### 物化边界(诚实)

materialize 的是 **flag + 非主分支 gate**(关键安全约束);auto-merge 执行 / pm_acceptance 自动过 / ship-finalize 自动跑 是 **PMO 按 SKILL.md spec 行为**(与 auto_mode 同源 · auto_mode 本身就 spec-driven · 代码只存 flag)。安全网双保险:① gate 物化挡住 main ② 分支保护由平台 server 端强制(`gh`/`glab` merge 失败即退回手动 stop + WARN)。378 passed · 68 pre-existing(无关)· 0 regression。

---

## v8.62 · ship-finalize main-sync 主分支残留治本(feature_artifacts 无条件清 + ff-pull · 用户 case · dev-only)

> 用户 2026-05-30:"总是发现主分支残留 state.json 和一个 jsonl · 是否有必要回主分支后 git pull · 一般刚有新 MR 合入 · 尽量保证主分支干净最新。"

### 根因(两个叠加)

ship-finalize step 7 main-sync 本就 `git fetch` + `pull --ff-only` + 尝试清 feature_artifacts(state.json / review-log.jsonl = finalize-push 已推 origin 的**冗余本地副本**)· 但:
1. **清理被 gate 在「无其他 dirty」**:`else` 分支(主工作区含任何用户改动 → `safe_to_stash=False`)整段 `skipped_user_changes` —— 连 feature_artifacts 也不清 → 永久残留 + 主分支没 pull。主工作区几乎总有点 dirty(bootstrap 注入 / 用户 WIP)→ 用户实证"总是残留"。
2. **feature_rel 误分类**:`feature_dir.relative_to(main_wt)` 不 resolve · symlink 不一致(macOS /var→/private/var)时抛 ValueError → `feature_rel=""` → state.json/jsonl 落 other_files → 触发 (1)。

### 修复

| 改动 | 内容 |
|----|----|
| `_classify_main_sync_dirty` | relative_to 前先 `resolve()` 双边(归一 symlink)· 防 state.json/jsonl 误落 other_files |
| main-sync `else` 分支 | 不再整段跳过:**无条件** `git checkout origin/<mt> --` 覆盖清除 feature_artifacts(它们总是安全丢弃 · origin 已有终态)+ 尽力 `ff-pull`(finalize commit 只动这两文件 · 一般不碰用户改动)· 用户真改动**始终保留不动** · 新 status `cleaned_pulled_user_dirty_kept` / `cleaned_skip_pull_user_changes` |
| 测试 | classifier 加 mixed 场景(feature_artifacts + 用户改动 → feature_artifacts 仍识别 2 · safe_to_stash=False)· 374 passed · 68 pre-existing(无关)· 0 regression |

### 回答用户

不必额外手动 `git pull` —— main-sync 本就 fetch + ff-pull · 问题是清理被 gate 跳过。治本后:**即便主工作区有用户改动 · 也会清掉冗余 state.json/jsonl(用 origin 终态覆盖)+ ff-pull 到最新 · 保留你的改动不动** → 主分支干净 + 最新。

---

## v8.61 · 修 v8.58 同栈预览 3 个 gap(v8.59 修好的 codex 异质评审实战挑出 · dev-only)

> v8.59 修好的 codex exec 评审跑 commit 56a8715(v8.58 改动)报 NEEDS_REVISION · 挑出 3 个真 gap —— 异质评审修好后第一次实战就见效。

### gap 1(真物化漏洞)· same-stack ui_design-complete 不验证 preview-project 已提交

v8.58 `_check_same_stack_preview_project` 只校验 `preview-project/` + `preview.sh` + `package.json` 在**磁盘**上存在 · 不验证进了 `auto_commit` → 预览源没提交也 PASS → ship 丢失(same-stack 全景权威 = preview-project **源**)。
- **修**:加 `_path_in_commit`(`git ls-tree {commit} -- {abspath}` · 3 态:在树内/未提交/无法判定)· `_check_same_stack_preview_project` 加 `auto_commit` 参数 · 校验 preview.sh + package.json 进了 auto_commit · 未提交 → FAIL + hint(`git add` + commit)· 不传 auto_commit 时仅磁盘校验(向后兼容 · None 不阻塞)· symlink 归一(macOS /var→/private/var)

### gap 2 · ui_design-start 脚手架没提 preview.sh

`_v8_engine.py` `STAGE_TEMPLATES.ui_design` 只列 UI.md + preview/*.html(static-html)· 没 same-stack 的 preview.sh。
- **修**:加 `preview-project/preview.sh` → `preview-project-preview.sh`(scaffold 提示 · 拷入后按框架改 dev server 行)

### gap 3 · templates/ui.md 残留 static-preview 引用与 same-stack 冲突

同栈 Designer 读模板同时看到「用 preview.sh」(frontmatter)和「填 §全景权威索引 preview/*.html」(§表格 / §HTML 预览稿模板)· 矛盾。
- **修**:① frontmatter 注释 v8.56「编译出 preview/*.html」→ v8.58「源即权威 · preview.sh · 不出 build」② 顶部「视觉真相」改介质感知 + 加「🔵 介质分流」note ③「§全景权威索引」「§HTML 预览稿模板」标题标「🔵 static-html 介质专用 · same-stack 跳过」

### 测试

`TestPanoramaArtifactEvidence` +3(uncommitted preview-project → FAIL / committed → PASS / 无 auto_commit → 仅磁盘校验)· 373 passed · 68 pre-existing(无关)· 0 regression。

---

## v8.60 · bootstrap 截断鲁棒 pmo_must_read digest + 禁截断工具输出规则(用户 case · dev-only)

> 用户 2026-05-30(AON session):AI 跑 `bootstrap.py | head -50` 把 `skill_update_check`(JSON 后位)切掉 → 漏升级提示 + 误判"bootstrap 没检查升级"(实际检查了 · 是 head -50 吞了)。"约束 AI 不要截断 py 脚本输出 · 检查我们输出不要太长 · 过长则写文档传路径。"

### 根因

bootstrap 输出 102 行 · 关键 forewarn(`skill_update_check`〔行 67〕/ `flow_gates`〔行 74〕/ `session_entry_priority`〔行 95〕)全在**后 1/3** · 顶部是 silent 维护噪声(skeletons/chmod/hooks)。AI 习惯 `| head` 截断长输出 → 正好切掉 PMO 必须 act 的部分。

### 修复(物化 + 规则双管)

| 改动 | 内容 |
|----|----|
| **bootstrap.py 截断鲁棒 digest** | 输出**顶部**(verdict/command 之后 · 位置 2)置 `pmo_must_read` 一行 digest:禁截断警告 + skill 升级状态 + flow_gates 名单 + session_entry_priority —— **survive `head -5`**(实测) |
| **SKILL.md 禁截断规则** | § bootstrap flow_gates 响应 加 🔴「禁截断工具输出」:teamwork 工具(bootstrap / state.py / update.py)输出 = 结构化 JSON · 字段顺序有意义 · 关键 forewarn 在后位 · **禁 `\| head`/`tail`/`sed` 截断** · 必完整读;工具输出罕见过长 → 落文件 emit 路径(不 inline 巨串) |
| 测试 | `test_pmo_must_read_digest_at_top_survives_truncation`:断言 digest 在头部(位置 ≤2)+ 含禁截断警告 + 提 flow_gates + **head -5 实测仍见**(直接复现 bug 场景)· 370 passed · 68 pre-existing(无关)· 0 regression |

### 三问对账(用户)

1. **约束 AI 不截断** → SKILL.md 硬规则 + digest 顶置(即便习惯性截断也见关键信息)
2. **检查输出不要太长** → digest 给 1 行短读路径(AI 不必啃全 102 行)· 详细仍在 JSON 后位
3. **过长写文档传路径** → 规则写明「工具输出罕见过长 → 落文件 emit 路径」(external-review 已是此模式)

---

## v8.59 · 异质评审 review stage 改 codex exec(治本 codex review 子命令 headless 卡死 · 用户 case + 本地实测 · dev-only)

> 用户 2026-05-30(AON SVC-PLATFORM-F057 review stage):"执行异质模型评审总是报错 · 看下逻辑是否有问题 · 本地测试下" + "不一定非要统一 exec · 只要确保 review 正常即可"。

### 根因(两层)

1. **直接诱因 · 安装的 skill 旧(v8.50.1)**:`~/.claude/skills/teamwork` 软链 v8.50.1(pre-v8.55)· 超时仍 300s + 无 `stdin=DEVNULL` 抗卡 + 无执行日志 → AON 看到的"300s exit 124 + 无日志"全对得上(v8.55 早已升 600s + DEVNULL + 日志 · 但用户没 update 拉新)。
2. **真根因 · `codex review` 子命令 headless 卡死**:review stage 用 `codex review --commit X --title Y`(goal/blueprint 用 `codex exec`)。**本地实测**(codex-cli 0.135.0 · `stdin=DEVNULL`):
   - `codex review --commit` → 跑满 220s 产 **0 字节 stdout**(超时)❌
   - `codex exec <review prompt>` → **RC=0 · 169.7s · 1488 字节真实评审**(含 NEEDS_REVISION verdict · 还真挑出 v8.58 几处 gap)✅
   与 AON 现象一致:同 Feature goal/blueprint(走 exec)早成功 · 唯独 review(走 codex review)持续超时。

### 修复:全 stage 统一 codex exec

| 改动 | 文件 |
|----|----|
| `_run_codex_review` 删 `stage==review` 的 `codex review` 子命令分支 → 全走 `codex exec [PROMPT]`(exec 已被 goal/blueprint 验证 · codex review 历史反复横跳 v8.23/25/26) | `tools/state.py` |
| `_build_codex_prompt` review 分支修 **diff scope bug**:旧 `git diff base..commit -- {feature_dir}`(只看 Feature docs · **漏掉真实代码**·实现在 `src/`)→ `git diff base...commit`(全量 · 显式提示实现在 feature_dir 之外 · 加 verdict 要求) | `tools/state.py` |
| `cmd_external_review` dry_run 删 review 特例 → 统一 exec preview | `tools/state.py` |
| 测试:dry_run / v8.23 / v8.26 三例从断言 `codex review` → 断言 `codex exec` + PROMPT 含 `git diff` + verdict | `tools/tests/test_state.py`(369 passed · 68 pre-existing 无关 · 0 regression) |

### 🔴 用户须知

AON 装的是 v8.50.1(旧)· 即使逻辑修了也要 **`python3 ~/.claude/skills/teamwork/tools/update.py`**(channel=dev)拉到 v8.59 才生效 —— 同时拿到 v8.55 的 600s 超时 + 抗卡 + 执行日志(`~/.teamwork/external-review-logs/`)。

---

## v8.58 · same-stack 预览改 preview-project/preview.sh(dev server + 动态端口 · supersede v8.57 hub + v8.56 静态 build · 用户拍板 option B · dev-only)

> 用户 2026-05-30:"最好针对预览稿直接编译运行 · 设计确认时直接给 URL · **不用在 teamwork 层起 server** · 直接用项目的 dev 环境 · 只是端口动态生成一个 · 是否可以在 preview-project 内也有一个 preview.sh 脚本 · 执行调用编译运行后输出可打开 URL。"

### 方向修正:v8.57 hub 被 supersede

v8.57 在 teamwork 层起单 hub serve 静态构建 —— 用户否定("不用在 teamwork 层起 server")。更干净的方案:preview-project 就是个可跑项目 · 让它自己的 dev server 跑预览 · **每次选动态空闲端口**(并行 worktree/多终端天然不冲突)· 用 `preview.sh` 封装。

### 用户拍板 option B(AskUserQuestion)

「加了 preview.sh 后 v8.56 的静态 build 必产 + 物化校验怎么处理」→ **去掉 · preview.sh 即唯一预览**:
- same-stack 全景权威 = **preview-project 源**(committed 可跑独立项目 · 要看跑 preview.sh)· **不再出静态 `docs/design/preview/*.html`**
- 物化闸改为 `preview-project/` + `preview.sh` + `package.json` 存在(`_check_same_stack_preview_project`)· 比 v8.56 静态产物校验弱 · 但用户接受(换 DX:实时热更 + 一键 URL)

### 改动

| 文件 | 内容 |
|----|------|
| **删** `tools/preview.py` + `tools/tests/test_preview.py` | v8.57 单 hub 整体回退(不在 teamwork 层起 server) |
| **新** `templates/preview-project-preview.sh` | preview.sh 模板:按 lockfile 选包管理器 + 缺则装依赖 + `node net` 选动态空闲端口(`PORT` env 可覆盖)+ 打印 `PREVIEW_URL=` + 起 dev server(vite/next/CRA · 一行按框架改)· 拷入 preview-project 根 |
| `tools/_v8_stage_specs.py` | `_evidence_panorama_artifact` 重构:same-stack → `_check_same_stack_preview_project`(preview-project+preview.sh+package.json · 不再要静态 build)· static-html 不变 · 加 `_resolve_panorama_subdir` helper |
| `stages/ui-design-stage.md` | same-stack 模型重述(源即权威 · 删静态 build)· 新 § 预览(preview.sh · dev server · 动态端口)替换 v8.57 § 预览服务 hub · step 3/5 + 物化拦截 + Output Contract 改 preview.sh |
| `roles/designer.md` / `templates/ui.md` / `docs/conventions.md` / `stages/panorama-sync-stage.md` | same-stack 验证改 preview.sh · 去 preview.py / base:'./' / 静态产物 |
| `SKILL.md` | 删 tools/preview.py 文档清单行 |
| 测试 | TestPanoramaArtifactEvidence same-stack 3→4 例(无 panorama_path FAIL / preview-project+preview.sh+pkg PASS / 无 preview-project FAIL / 缺 preview.sh FAIL)· 369 passed · 68 pre-existing(无关)· 0 regression |

### 🔴 preview.sh 用法

PMO 后台跑 `bash {子项目}/docs/design/preview-project/preview.sh` → 读早期 stdout 的 `PREVIEW_URL=` 行 → 等就绪 browse → 用完 kill。dev server 前台阻塞 · 故 `run_in_background`。仅 localhost。


---

## 更早版本(v8.57 → v1)

完整历史已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)(v8.0 之前的 v7/v6/… 旧系统亦在此)。
