# PROCESS-LEDGER 模板(流程价值台账)

> 位置:`project-specs/PROCESS-LEDGER.md`(workspace 级 · 与 DEV-RULES / KNOWLEDGE 同级)。
> **telos**:一行一 feature 的流程仪式价值数据 · 给「该不该砍某环节」提供查表依据。消费方:流程审视场景 + 年检 kill criteria(详 [stages/ship-stage.md §16](../stages/ship-stage.md))。
> 🔴 区别 `docs/retros/`(业务/工程复盘 · 子项目级 · 知识层):本表只度量 **teamwork 流程本身**的环节价值 · 别混写。
> 写入时机:🔴 **ship1 archive 的规划 gate**(worktree 内 append · state.json / REVIEW.md 就在工作树 · 路径加进 `--planning-artifacts` 随 feature MR 原子合入;digest 在 ship2(ship-finalize)完成后 emit)。漏写兜底:`unzip -p features/_archive/<id>.zip <id>/state.json` 取数补行。🔴 单元格 ≤1 行 · 机器字段照实抄 · **不美化**(过场就写过场)。

---

# 流程价值台账

> 查询示例(年检 / 流程审视时算):external confirmed 率 = Σ采 / Σ总;某角色真 finding 率 = 该角色 finding 数 / feature 数;暂停点 all-default 率 = Σ默 / Σ(改+默);协调开销占比 = Σ开销轮 / Σ总轮;**新判例频次 = 含 `判例:` 前缀的行数 / 总行数**。
>
> 🔴 **率/频次类判据的分子分母必须同格或同表**(v8.298 立):否则该判据没有数据源、年检算不出来。
> 本表两处曾漏:① `角色真 finding` 只举了 review 侧(arch/qa/ext),**goal 侧的 `pl` 没进示例** ——
> 而 goal-stage 声明「PL-CHALLENGE 采纳率进台账 · 长期零采纳 = 过场信号」· 取不出就等于没这条判据;
> ② `反思摘要` 是自由文本,而 kill criteria 明确要「**连续数月无新判例** → 流程仪式砍半」—— 数不出来。
> 修法都不加列:**① 本列按 `<goal 侧> / <review 侧>` 两段写全角色**;**② 有流程新判例时,`反思摘要`
> 必须以 `判例:` 前缀开头**(可 grep 可数 · 无判例则照常写摘要)。

| Feature | flow | 实走 stages | 时长(总·AI自主·待用户) | review/test 轮 | external 总/采/驳 | 角色真 finding | 暂停点 改:默 | bypass/WARN | 反思摘要(≤1 行) | 各阶段耗时 | 用户邮箱 | 宿主 | 分诊校准(预测→实际) | 🛡️ 起草可预防性(可预防/总·缺考虑点) | ⏱️ 耗时归因(开销轮/总轮 · 详见流程复盘) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <ID> | <Feature / Feature·micro / Bug> | <goal→blueprint→dev→…→ship> | <2.4h·AI 88m·待 32m> | <1/1> | <3/1/2> | <pl:2 ext:1 / arch:1 qa:0 ext:1> | <1:2> | <0/0> | <external 拦 1 真问题 · ui_design 零 finding 过场> | <goal 20m(+等5m)·dev 40m·review 8m·pm_acceptance 30m> | <git user.email> | <claude-code/codex-cli/gemini-cli> | <explicit·goal→qa → diff 14 files·PRD 0 revision·review 1 轮> | <3/12 可预防·缺:并发时序> | <2/9 轮 · 详 apps/partner/docs/retros/SVC-F001-process.md> |

> 🔴 **schema 演进纪律(v8.210)= 只在末尾加列** —— 新列一律追加到表**最右**(旧 feature 行天然是**有效前缀** · 新列它们为空 = 该 feature 早于该指标 · 诚实)· **永不在中间插列**(否则旧行错位、年检读错列)。**旧项目台账迁移 = 仅换表头一行**(旧数据行不动):append 前跑 `state.py ledger-migrate --feature <path>`(幂等 · header 已最新则 no-op)。
> 🔴 **🛡️ 起草可预防性(v8.281)**:各评审收敛后跑 `state.py review-preventability --stage <goal|blueprint|review> --preventable N --total M --missing '缺的考虑点'` 记录 · ship 聚合成「可预防/总·缺考虑点」照抄本列(数据源 = ship1 archive emit 的 `ledger_authoring_preventability`)。**用途**:年检看「缺的考虑点」跨 feature 复发 → 补 PRD/TECH 起草考虑点(PL六问/TECH自查/复发清单);判据同 v8.278(findings 82% 真·砍轮=漏 bug·真杠杆=起草挡掉可预防子集)。非门禁 · 没记录留空(有效前缀)。
> 🔴 **⏱️ 耗时归因(v8.295 · v8.297 收窄)**:本列**只放可查表算账的比值 + 指针** ——
> `<开销轮>/<总轮> 轮 · 详 <流程复盘文档相对路径>`(数据源 = ship1 archive emit 的 `ledger_stage_cost`)。
> 🔴 **归因叙述不写这里**:一行一 feature、单元格 ≤1 行,压不下「这 318 分钟花在哪」——
> 而归因恰恰是最值钱的部分。叙述归 **`{子项目}/docs/retros/<feature-id>-process.md`**
> (模板 [process-retro.md](./process-retro.md) · 与台账行同时在 ship1 规划 gate 写 · 随 feature MR 原子合入)。
> 采集:各 stage 收敛后跑 `state.py stage-cost --stage <…> --rounds N --overhead-rounds M --kinds '…' --note '…'`
> (stage-complete emit 会带提示 · 非门禁 · 零开销也要记 —— 「这次没开销」与「没记录」是两回事)。
> **用途**:年检看**协调开销占比**跨 feature 趋势(查表即得 · 不必开文档)+ 展开读归因定位复发的开销类型;
> 🔴 也是**验证提效改动是否真起效的唯一手段**(v8.294 的收敛期归一 / TC 边界 / 投机窗准入都声称能砍这块)。
> 🔴 **时长三分(v8.208)**:`总` = 墙钟(init→archive · 不含 MR 等待)· `AI自主` = 扣掉所有人工等待后 AI 真跑的时长(Σ 工作 stage〔duration − stage 内 pause-mark 暂停〕)· `待用户` = 全部人工等待(stage 内暂停 + pm_acceptance 等纯等待 stage 墙钟)。**数据源 = ship1 archive emit 的 `ledger_timing`**(确定性 · 照抄不肉眼算)· `各阶段耗时`同源(`per_stage`)。
> 🔴 **角色真 finding**:按 `<goal 侧> / <review 侧>` 两段写全 —— goal 侧含 `pl`(PL-CHALLENGE 采纳)与 `ext`,review 侧含 `arch`/`qa`/`ext`。🔴 **零也要写**(`qa:0`)—— 「零 finding」与「没这个角色」是两回事,而「某角色长期零真 finding → 评审矩阵收缩」正是靠它。
> 🔴 **反思摘要**:一行。**有流程新判例时以 `判例:` 前缀开头**(年检数「连续数月无新判例」靠 grep 这个前缀)· 完整反思归 `docs/retros/<id>-process.md` §三。
> 🔴 **用户邮箱** = `git config user.email`(archive emit `ledger_timing.user_email`)· 供年检按人/团队分析流程健康度。
> 🔴 **分诊校准(v8.217/231)** = archive emit `triage_calibration` 照抄(预测:clarity+roster 调整;实际:diff 文件数/goal 修订轮/review 轮;**dispatch_models 分布** —— `unspecified` 占比高 = dispatch 没分档 · 年检验档位建议采纳率)· 年检算**分诊准确率**(explicit 判定却 PRD 常打回/review 高轮次 → 判据收紧)。
> 🔴 **宿主(v8.209)** = AI 宿主类型 `claude-code` / `codex-cli` / `gemini-cli`(archive emit `ledger_timing.host` = `state.host`)· 供年检**按宿主对比流程质量**(如 external 采纳率 / 过场率 / AI 自主时长在 claude vs codex 上的差异)。
