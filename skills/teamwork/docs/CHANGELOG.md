# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.155 · goal 评审重构:草稿后并行派 3 个隔离 Agent 冷审 · 治锚定鼓掌 · PM 退整合者

> 用户(承数据分析线):goal 改成 PRD 草稿写完后 · 并行派 3 个 Agent 评审。

### 诊断闭环(多轮真实数据驱动)
- 读 aon/jdp/aifriend/TermPro 真实归档:in-context 的 arch/qa 在 goal 常产 **info-only 鼓掌**(SVC-F002:arch/qa 只 info 级背书解法)· 而隔离的 external/PL 抓到 high 契约 gap。根因 = **同一 AI 起草完审自己 = 带起草记忆脑补填缝 → 漏细微 gap**。框架早用 PL 的 subagent 隔离(v8.132)证明了机制,却把 arch/qa 留主对话靠「怀疑者视角防鼓掌」乐观假设(architect.md)—— 数据证伪。
- v8.149 拿掉 goal-external 的真实代价 = 丢「冷审安全网」;真修法不是加回 external · 是**把全部 reviewer 隔离冷审**。

### 改动(流程重构 · 代码 + 文档 + 测试)
- **goal §3+§5 合并为「并行冷审循环」**(9 步 → 8 步):草稿 v0.1 → **并行派 QA/Architect/PL 三个隔离 subagent 冷审**(只喂 PRD+cite+KB · 不喂起草心路)→ 早问门(**后移到冷审后** · 冷审视角更准识别用户决策)→ PM 整合修订 → **Round 2+ 验证模式**(喂上轮 finding+处置 · 核实 fix+找新)→ 全 APPROVE 收敛 · 3 轮不收敛升级用户。
- **PM 退出 reviewer**:`DEFAULT_REVIEW_ROLES[Feature,goal]` `[pm,qa,architect,pl]`→`[qa,architect,pl]`(敏捷 `[pm,qa,architect]`→`[qa,architect]`)· PM = 作者+整合者(审自己最锚定)· 不给 verdict · 门禁/模板 reviewers 同步去 pm。
- **architect.md 翻案**:goal 评审 `默认主对话`→`默认隔离 subagent`(评的是自己起草物 · 必隔离)· blueprint/review 评 RD 产物沿用主对话。qa.md 同加 goal 冷审默认。
- external opt-in 保留(契约型后端地基 feature 仍可加为第 4 冷审 · v8.149 安全阀 · 数据证明有用)。
- 测试:reviewers_match/pl_challenge 适配去 pm · simplicity-lens pin 更新(external opt-in)· 注释校正。

### 验证
- pytest 3 failed / 530 passed(baseline 3 · 零回归)· 8 步链 + cite 表 + brief + Output Contract 全对齐。

## v8.154 · disable_external_review 改 hard rename:撤 v8.153 旧名兼容(无项目使用 · 不留)

> 用户(承 v8.153):不用兼容。

### 改动(代码 + 模板 + 文档 + 测试)
- 撤掉 v8.153 加的旧名 OR 兼容:两 reader(state / _v8_stage_specs)+ bootstrap WARN reader **只读新名** `disable_external_review` · 旧名 `disable_heterogeneous_review` 废弃不再读取。
- 依据:核过无任何消费项目设旧名(只框架仓自己 · v8.153 已改新名)· 硬改无 silent break 风险 —— 同 v8.145「不留兼容期」路子。
- templates / standards 的「旧名仍兼容」注 → 改「v8.154 旧名已废弃」。
- 测试:v8.153 兼容测试反转为 hard-break 回归守护(单设旧名 true **不再生效** · 防有人误把 OR fallback 加回)。

### 验证
- pytest 3 failed / 530 passed(baseline 3 · 零回归)· 旧名非-docstring/非-守护引用清零。

## v8.153 · config 改名 disable_heterogeneous_review → disable_external_review(旧名 OR 兼容)

> 用户:`disable_heterogeneous_review` 这个配置名字改为 `disable_external_review`。

### 改动(代码 + 模板 + 文档 + 测试)
- **config key 全量改名** `disable_heterogeneous_review` → `disable_external_review`(更贴语义:禁的是 external 评审角色 · 不是「异质」jargon):两个 reader(`_read_disable_external_review` / `_localconfig_disable_external`)· bootstrap 默认 + 自愈 + 启动 WARN · templates(localconfig.json / config.md)· standards §11/§十二 · 内部 var `het_disabled → ext_disabled`。
- 🔴 **旧名 OR 兼容(不 silent break)**:reader 读「新名 is True **or** 旧名 is True」—— 防 bootstrap additive 自愈把新名补默认 false 顶翻已有旧 true(healer 只补不覆盖 · 老项目旧 key 仍生效)。
- 行为口径顺带校正:reader/template/doc 旧注释还写「exec 自审」· 实际 v8.108 起是 **subagent 降级配方**(emit SUBAGENT_FALLBACK · 非 exec)· 一并改正。
- `checks.heterogeneous_review`(bootstrap emit check 名)语义仍准(报异质评审健康度)· 留;warning 文案已用新 key。
- 测试:reader/默认/降级三处改新名 + 新增旧名兼容测试(旧 true+新 false → 仍禁用)。

### 验证
- pytest 3 failed / 530 passed(baseline 3 · 净 +1 兼容测试)· 残留扫描:非测试/非兼容引用清零。

## v8.152 · posture hint 两个方向都摆明实证:REJECT 也点名给理由(修 v8.151 自身不对称)

> 用户:REJECT 也要给理由。

### 诊断:v8.151 hint 矫枉过正 · 又写歪了对称
- v8.150 治的是「ADOPT 欠防」· v8.151 把姿态推进 brief 时**只把「ADOPT 也要给实证」摆明**· REJECT 的举证只剩抽象一句「举证责任对称」—— 讽刺地犯了 v8.150 要治的同款不对称(具体摆明的只有一侧)。doc 侧(§12.1 表 / pm_response schema)本就两侧都全 · 是 brief 字面歪了。

### 改动(代码 + 测试)
- **`_FINDING_POSTURE_HINT` + `_review_brief` 姿态行**:从「ADOPT 也要给实证」改为「**两个方向都必给实证**」并各自点名 —— ADOPT 给「为何确为真+为何这样改对」· REJECT 给「为何不是问题(指真实代码/规约/目标)」·「reviewer 说得对」与「我觉得没事」都不是理由。
- 测试断言更新(校验两侧都摆明 · 非只抽象「对称」)。

### 验证
- pytest 3 failed / 529 passed(baseline 3 · 零回归)。

## v8.151 · finding 质疑姿态进 brief:消费时点主动推 · 防 v8.150 spec 只被动躺 doc

> 用户(承 v8.150):相关的 brief 是否要有对应的提示。

### 诊断:spec 被动 · brief 主动 —— 防线得在决策那一刻到场
- v8.150 把「先质疑→确认→采纳 · 举证对称」写进了 §12 / schema / stage doc · 但这些是**被动 spec**(AI 要主动去读才生效)。而 findings 刚产出、即将被消费的那一刻,state.py 主动推的是 `next_action_brief` —— 它当时只说「整合 finding 到 REVIEW.md → complete」· 零质疑姿态。光改 doc 不改 brief = 防线在文档里、决策在别处(框架「可枚举/主动告知」哲学的要害)。

### 改动(代码 + 测试)
- **`_FINDING_POSTURE_HINT` 常量**:① 先质疑(过度设计/错层/false positive/没看全)→ ② 回读真实代码/AC/DEV-RULES 确认 → ③ 才 ADOPT/REJECT · **ADOPT 也要给实证** ·「reviewer 说得对」不是采纳理由 · 举证责任对称。
- **接进 external-review 成功 emit 的 next_hint**(default + degraded 两分支)—— 每个 stage(goal/blueprint/review)external finding 消费的必经处 · 一处覆盖三阶段。
- **`_review_brief` 加姿态行**(review stage start 即带)。
- 测试 +2(posture hint 关键 token / review brief 含姿态)。

### 验证
- pytest 3 failed / 529 passed(baseline 3 · 净 +2)。

