# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.164 · PRD 模板三层 + 挑衅式开放区:必填核/按需/开放区显式 · 既有行为侦测提成主动挑衅

> 设计讨论结论(③④⑤+① 接力):模板该分「必填核(消费测试过)/ 按需 / 开放区」· 开放区给结构没问到的留逼判断的尖问题(非空白自由发挥)· 既有行为变更从待决策项里的被动 HTML 注释提成开放区的主动必答挑衅。

### 改动(prd.md 产物层 · 零代码)
- **③ 三层显式**:intro 改成「必填核(背景/用户故事/交付预期/待决策项/验收标准/Out of Scope)· 按需(流程图/埋点/消费方分析)· 开放区」· 消费测试定档(工具或下游真读 → 必填核)。
- **④ 挑衅式开放区**(`## 开工前必须想清的`):**可见**挑衅 4 问(🔁既有行为 / 🧱隐藏前提 / 🌊跨子系统涟漪 / ❓最不确定)· 「至少 1 实质 or 显式『无+理由』」· **人读 · 机器禁入**(无机读字段/不被 grep)· 冷审查是否过场。
- **⑤ 既有行为:被动注释 → 主动挑衅**:侦测(改了既有默认行为吗)提成开放区必答 🔁 · 后果(命中 → 必入待决策项让用户拍板)留刚性核(待决策项注释剥成「刚性后果」)。治 TermPro「8 轮打磨错前提」的结构成因。
- **① 残留接力**:必填核标「PRD 的脊 = prepare 已确认的意图(🎯/📦/🔁)· 起草不得偏离 · 冷审据此核对」· 防 goal 起草 re-drift(① 主体已被 v8.162/163 prepare 意图门吸收 · 不另建门)。
- goal-stage.md step 2 结构列表同步加 §开工前 + 修正段序对齐模板。

### 验证
- doc-only(模板)· prd.md 367→381(+开放区)· verify-ac 实测解析正常(开放区不碰机读)· pytest 3 failed(baseline)/ 545 passed。

## v8.163 · prepare 意图门 🧩 假设加硬约束:只列意图解读 · 禁抛未验证代码猜测

> 承 v8.162 · 用户追问「prepare 前会读代码查事实么」暴露的洞:prepare 在强制读代码**之前**(§1.5.3 代码现状可选 · 强制深调研在 goal step-1)· 故 🧩 暴露的假设只能基于用户的话 · 若 AI 在此抛**猜的代码事实**(「我假设后端有 X 列」)= 让用户确认 AI 本该去查的事(正是 §1.5.3「代码现状只写已验证事实」+ 反模式 #7 已防的洞 · v8.162 的 🧩 措辞没把这纪律带进去)。

### 改动(prepare.md §4 · 一句硬约束)
- **🧩 只列「我假设你想要 X」类意图解读假设**(用户域 · 用户能直接拍)· **禁抛未验证代码/可行性猜测**(留给 goal 调研后的深门 · 或先验证再写)。
- 把浅/深意图门分工说干净:prepare 🧩 = 「我假设你**想要**什么」(意图 · 读代码前 · 用户拍)· goal 深门 = 「我读代码**发现**了什么、它怎么重塑意图」(现实 · 调研后 · 如 CPS-F003 后端 GAP)。

### 验证
- doc-only(prepare.md · 模板 🧩 行 + footnote 各一句)· pytest 3 failed(baseline)/ 545 passed(零碰)。

## v8.162 · prepare 暂停点信噪比反转:意图确认提到最前(暴露补的假设)· 执行 setup 塌一行

> 设计讨论结论:意图 fidelity(我们有没有理解对你要什么)只能由用户校验(用户是自己意图的唯一 oracle)· 而 prepare/triage 是规划→执行的那层膜 —— 这个唯一不可转移的校验该锁在前门。旧 prepare 暂停点领头是执行 setup(被 `ok` 盖章)· 把意图埋成一行 restatement → 误读搭便车溜过(实证 TermPro 前提盲:8 轮打磨错前提)。

### 改动(prepare.md 暂停点重排 · 同一处编辑解两个诉求)
- **意图确认提到最前**(`# 🎯 我的理解`):🗣️ 用户原话 + 🎯 理解 + **🧩 我补的假设**(摊开「你没说、我替你补的」= 抓误读核心零件 · 干净 restatement 会把假设藏起)+ 📦 范围 + 🔁 既有行为。**数据全是 prepare-check 已采的**(`--user-intent` + `--admission-judgment.ai_rationale`)· 只是从「目标概述」reframe 成「暴露假设的确认」。
- **执行 setup 塌一行**:旧 5 段(流程概览/评审角色表/上下文/Worktree/4 项配置)· 派生值多、用户盖章 → 配置一段 + 评审一行(各 stage-start 会再 emit · prepare 重列 = 噪音)+ 上下文**仅异常出**(上游未就绪/撞号/Planning 未 ship · 全绿不显)。
- **风险分级**:请求一清二楚 → 🧩 写「无补」秒过;含糊/大范围/改既有行为 → 摊假设让用户校(短指令恰是误读高发区)。
- 配套改自身护栏:§0.5 反模式 #6 / 自检 #5 / §4.1 自检 / §1.5 喂数据引用 / state.py `reviewer_thinking_hint`(评审思考结果进默认 · 不铺表)· prepare.md 459→417。

### 边界 + 验证
- 这是**浅意图门**(prepare · 调研前 · 拦粗误读)· **深意图**(goal 调研后才浮出的形状)是 goal 侧后续。
- doc + 1 hint 字符串(测试断言的 pl 默认保留/不要直接抄/F-Bv2-8 全保留)· pytest 3 failed(baseline)/ 545 passed。

## v8.161 · review 外审评本 feature 增量 diff:进 dev 冻结 base 锚 · 治跨 feature 串味 + 超时

> harvest docs/audit/(aifriend 20 条)最高频框架信号:external review 评 `merge_target...HEAD` · 在长 WS / stacked 分支(yolo/ws02)随 deliverable 累积 → ① 跨 feature 串味(B014/B017 实测:一次涌 5 个跨子系统 finding · 本 bug 只占 1 · in/out scope 全靠 AI 自决无工具)② 600s 超时(B016/B017:base...head 全量随 deliverable 增长)。

### 改动(治本:diff base 从「不前进的 merge_target」改「本 feature 的 pre-dev 锚」)
- **进 dev 冻结 base 锚**:`maybe_freeze_review_base`(_v8_engine.py)· stage-complete 进 dev 那刻把 pre-dev HEAD(完成 stage=blueprint/diagnose/blueprint_lite 的 commit)冻进 `state.review_base_commit` · 它在 commit graph 上是 dev HEAD 祖先 → `base...HEAD` **天然排除 prior features**(拓扑无关)。仅首次进 dev 设 · review→dev 回退不覆盖。
- **review 外审默认用增量锚**(state.py)· `base = --base > review_base_commit(仅 review stage · 且校验是目标 commit 祖先)> merge_target(兜底)`。`_is_ancestor`(git merge-base --is-ancestor)失效→透明兜底既有行为 · **绝不因锚点失效而 BLOCK**。
- **审计可见**:emit 加 `base_source`(--base / review_base_commit / merge_target)· prompt 措辞兼容 commit 锚 · `--base` help + init schema 显式化。
- goal/blueprint 评文档不评 diff · 锚逻辑只在 review stage 生效。

### 验证
- 新增 `test_review_base_commit_v8161.py` +11(冻结 4 / 祖先校验 3 / dry-run 解析 4)· pytest 3 failed(baseline)/ 545 passed。

## v8.160 · 全模板瘦身:剥贴在活规则上的版本号 + 删「已移除字段/撤销旧决策/上线计划」考古

> 用户(承 v8.159):查看其他模板是否有 prd.md 同类问题(过时/历史背景)。

### 改动(10 模板 · 同 v8.159 律:剥死历史留 why)
- **剥版本号前缀**(贴在仍有效规则上 · 规则留、`vX.Y` 去):`bug-report`(v8.107×2 / v7.3)· `tc`(v7.3 契约化×2)· `external-cross-review`(v8.19/20/21)· `ui`(v8.17×4 / v8.58 option B×3 / v8.134)· `config`(v7.3.8)· `roadmap`(v8.49)· `必读 cite(P0-11)`×3(browser-test/pm-note/test-report)。
- **删决策/迁移考古块**:`config`「撤销 默认 off 决策」4 bullet(留「改 off 的合理理由」=何时选 off 的 why)+「已移除字段 ship_rebase/ship_policy」+ disable_external_review「改名自…旧名已废弃」(v8.154 已硬改名无兼容)· `external-cross-review`「字段重命名重构」note +「十、启用路线 Week 1-2」上线计划(早物化)· `ui`「旧模板…段已删除」改写为 live 规则。
- **保留 why / live 行为**(不误伤):ui「治本双副本不一致 / 介质 drift」· config archive_on_ship「残留被忽略+WARN」(代码仍读)· 老模式向前兼容 note。
- **假阳性不碰**:host-injection `teamwork-pointer v8.2`(sync-drift.py 解析的功能 marker)· ADR/e2e/workstream「废弃」状态枚举(live 数据模型)· tech 迁移策略段 · config P0-154(live 约束追溯)。

### 验证
- doc-only(模板)· 10 文件 −18 行 · pytest 3 failed(baseline)/ 534 passed(零回归)。

