# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.271 · PRD 每条 AC 配大白话解释 · 机器校验逐条非空

> 用户指令:「PRD 模板优化,每一个 AC 都需要大白话解释一下」。BDD(Given/When/Then)是给 QA 绑 TC 的机器友好写法,但用户终确认时读起来费劲 —— §验收标准表加 **💬 大白话列**:每条 AC 一句人话(这条在验证什么 · 用户能感知到什么变化),与终确认导读「说人话」哲学同源,拍板者逐条看得懂。

### 改动
- templates/prd.md:AC 表加 💬 大白话列(含示例:「登录成功后 3 秒内能看到自己的头像和昵称」)· 表注/🧠 起草思考规范 AC 条/自查清单同步(写时即配 · 非写完补)。
- goal-complete 新 evidence `ac_plain_words`:解析 §验收标准表 —— 缺列 FAIL(提示照模板加列)· 逐行空/占位(`{...}`/`-`/`无`)FAIL 并列出 AC id;段缺失/无 AC 行不重复报(归 conformance/verify-ac)。
- goal-stage 规则 1 + goal brief 起草思考行同步。
- 机读块不动:大白话属人读单源(body 表)· 不进 TEAMWORK-MACHINE(id 一致原则照旧)。

### 验证
- 新增 test_ac_plain_v8271(5:填齐过 / 缺列 / 空+占位列 id / 无段放行 / 关键词不误判)· pytest 927 passed。

## v8.270 · Bug 流 review 改单路评审 · 只留 external

> 用户指令:「bugfix 改为单路评审,只留 external」。Bug 流的质量重心在 diagnose(根因 + 修复方案经用户确认才许修)—— review 只需盯「fix 是否忠于已确认方案 + 是否引入新问题」,双路属重了。默认 roster `["architect","external"]` → `["external"]`:一路错开模型隔离冷审(≠会话主模型 · v8.269 单路不变式天然满足)。

### 改动
- `DEFAULT_REVIEW_ROLES` `("Bug","review")` → `["external"]`;Bug chain review 注同步。
- review brief 新增 🐛 `_bug` 条件行(flow_type=Bug 且非 fast):单路语义 + 覆盖必含**修复↔diagnose 方案一致性**(Architect 视角并入)+ REVIEW-arch 不产;fast 优先(fast 时 roster 已是 [fast])。
- 静态两路行标注 Feature 默认 · Bug 差异;review-complete `--artifacts` 注 ×2(Bug 单路 REVIEW.md 即可)。
- review-stage.md / FLOWS.md Bug 行同步;`change-review-roles` 可加回(审计留痕)。
- 协议不变:REVIEW.md findings 台账/severity 门/验证轮/轮次预算照跑 · cross_review_coverage 物化门照拦 · 门禁 roster-aware 自适应(REVIEW-arch 不再要求)。

### 验证
- test_bug_review_default 断言更新 + 新增 brief 条件测试(Bug 带注/fast 优先/Feature 不污染)· pytest 922 passed。

## v8.269 · 单路评审与会话主模型错开 · 补全错开不变式

> 用户指令:「单路评审要和主模型分开」。v8.268 只管了双路(外审路 ≠ 主审路),把 fast 单路标了「不适用」—— 但单路是仅有的独立采样,跑会话主模型 = 起草者自审(盲区全相关)。本版补全:**不变式 = 任何评审配置至少一路 ≠ 会话主模型** —— 双路 = 外审路错开;**单路(fast 合并 / roster 减到一路)= 该路必须错开**(如 fable5 会话 → 评审 opus)。

### 改动
- SKILL 🎚️ 单源:「fast 单路不适用」→ 单路同样错开 + 不变式表述(顺修 v8.268 括号瑕疵)。
- `DISPATCH_TIER_REMINDER`:错开条改双路/单路两分支(消费时点)。
- goal / review 两个 fast brief 串加 🎭 单路错开行(消费时点)。
- SKILL fast 节「留两端」行 + localconfig 模板注释 + config.md 同步。
- 边界不变:验证轮照 v8.256 降档(降档即错开)· 跨厂商异质 opt-in 天然错开 · degraded 诚实标注照旧。

### 验证
- test_model_stagger 新增 3(提醒单路分支 / fast 两 brief / 正常 brief 不受污染)· pytest 921 passed。

## v8.268 · 正常模式双路评审模型错开 · 外审路 ≠ 主审路

> 用户指令:「正常模式双路评审时模型要错开,例如 PRD 一路是 fable5,另一路应该是 opus」。同模型双路 = 盲区相关(系统性偏差两路同瞎)—— 两路并行冷审(goal:PL+外审 / blueprint·review:Architect+外审)**模型必须不同**:主审路继承会话主模型 · 外审路错开一档(fable5 会话 → 外审 opus;opus 会话 → fable5/sonnet)。零 CLI 成本拿到近异质(上下文与权重双错开);跨厂商异质 opt-in(codex/gemini)时天然错开;fast 单路不适用;验证轮照 v8.256 降档(降档本身即错开)。

### 消费时点(规则到场)
- `DISPATCH_TIER_REMINDER`(每 stage-start 附带)加错开条。
- goal / blueprint / review 三 brief 的两路派发行加 🎭 标记。
- `external-review` subagent 配方 next_action:起 subagent 时 model 参数用 ≠ 主会话的档(降级路同享)。
- SKILL 🎚️ dispatch 档位节 = 单源全文(why + 配对示例 + 边界)。

### 措辞升级(「同模型 subagent 冷审」→「错开模型」)
- SKILL yolo 节 ×3 · goal-stage 外审行 + 两路并行行 · blueprint-stage §6②/§3 产物注 · review-stage §7 · roles/external-reviewer · standards/external-model-usage(默认语义块 + 代价自知句:非跨厂商异质 · 强于同模型 · 仍弱于 codex 级)· config.md · yolo-preflight · bootstrap/state.py 各 INFO。
- 不变:异质性硬约束(同厂商仍非「异质」· degraded/heterogeneous:false 诚实标注照旧)· self-review exec 兜底(客观同模型 · 保持)。

### 验证
- 新增 test_model_stagger_v8268(3:提醒/三 brief/配方)· pytest 918 passed。

## v8.267 · fast 模式评审最多 2 轮 · 轮尽未收敛决策点抛用户

> 用户指令:「fast 模式评审最多 2 轮,无法收敛的决策点抛用户」。fast 的提速语义补上收敛端:单路合并评审(v8.261)管宽度,本版管深度 —— 首轮全量 + 1 验证轮共 2 轮,轮尽不再循环,把未收敛的决策点直接交用户拍板。

### 引擎(硬拦)
- `FAST_MAX_REVIEW_ROUNDS = 2`:`review-retry` 处 `state.fast_mode` → 预算 = min(localconfig `max_review_rounds`, 2)(显式配更小则从小)。
- 超预算 R5 暂停点:标题带「⚡ fast 模式封顶」标记 · 首行明示「以下即未收敛决策点 · 请你拍板」(open findings 按 severity 列全 + 1/2/3 · 逃生 `--user-confirmed --reason` 照旧)。

### 消费时点提醒(brief)
- goal 首轮 brief fast 串:冷审最多 2 轮 · 第 2 轮末未收敛 → 停止循环 · 决策点列进终确认导读 🟡「你要拍板的」(goal 无引擎轮门 · 复用既有终确认暂停点作为抛出通道)。
- review 首轮 brief fast 串:评审预算封顶 2 轮(引擎硬拦)。
- 验证轮 brief(fast 时):「⚡ 本轮即最后一轮」置顶提醒。

### 文档
- goal-stage 规则 7(收敛软上限 3 轮)补 fast 2 轮分支;review-stage 规则 6(轮次预算)补 fast 封顶;SKILL fast 节 + localconfig 模板注释 + config.md 同步。

### 验证
- 新增 3 测试(默认 3→封顶 2 拦 round 3 / localconfig=1 取更小 / 三处 brief 提醒 + 非 fast 无)· pytest 915 passed。
