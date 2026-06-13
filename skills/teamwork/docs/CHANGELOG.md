# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.150 · review finding 处理对称化:先质疑→确认→采纳/驳 · 举证责任对称 · 治本盲采

> 用户:AI 对 review 结果的处理过程应该是先质疑、再确认、再采纳、给出采纳理由的思考过程 · 不能盲目认同。

### 诊断:举证责任不对称 → ADOPT 成无摩擦默认 = 盲采温床
- 框架有裁决三态(confirmed/rejected/deferred)+ adversarial_self_check + 12.2 点名「盲采是默认倾向」—— 但**防线不对称**:rejected「必记驳回依据」是硬的,ADOPT 的 rationale 只要填「改了什么」· adversarial_self_check 的示例/措辞全是 REJECT 方向(steelman finding 再驳)。结果:reject 有摩擦、adopt 无摩擦 → 盲采(reviewer 说啥改啥)恰是阻力最小路径,虽被点名却没设防。

### 改动(doc-only · 对称化既有机制 · 非加新仪式)
- **§12 头部加「固定思考顺序」**:① 质疑(先假设 finding 不成立:false positive/过度设计/错层/没看全)→ ② 确认(回读真实代码/AC/DEV-RULES)→ ③ 裁决+给理由。🔴 **举证责任对称**:confirmed 与 rejected 同责 —— 采纳也要给「为何确为真+为何这样改对」实证 ·「reviewer 说得对」不是理由。
- **§12.1 confirmed 判据**:加「先质疑」前置 + 处置加「记采纳依据(与 rejected 对称)」;§12.2 盲采标「最常踩」+「没经①②的 ADOPT = 盲采」。
- **pm_response.adversarial_self_check schema(prd.md)**:改方向对称 —— ADOPT 方向写「finding 不成立的最强反方→回读确认不成立→采纳」(给 ADOPT 示例);rationale 要求 ADOPT 含「质疑→确认链」三步,不接受无核实采纳。
- **review-stage.md / goal-stage.md substep 6 / roles/pm.md** 三处引用同步对称化(默认姿态=质疑)。

### 验证
- doc-only · pytest 3 failed / 527 passed(零回归)· 无测试 pin §12 措辞。

## v8.149 · goal 阶段去 external 评审:业务对齐阶段不做技术细节挑刺 · 细节/边界归 blueprint

> 用户:goal 阶段的外部评审去掉 —— 总会挑出细节和过度设计;这阶段目的是对齐业务目标(用户会看 PRD)· 细节和边界在技术方案阶段定就行。

### 判断:对的工具 · 错的阶段(非「external 没用」)
- external 整体 82% 采纳(实测数据)· 是框架 MVP —— 但**采纳率高 ≠ 每个阶段都该有**。goal 产物是业务对齐的 PRD、用户亲审;external 天然「找缺口 → 加校验」· 在「定要做什么」阶段把技术细节/边界审进来 = 噪音 + 过度设计提前涌入。external 留在 blueprint(技术方案)+ review(代码)· 那里技术挑刺正当其位。
- **框架早知道病只贴了创可贴**:goal-stage.md 原有「🔴 external finding 须对照简洁性取舍 · 每条单看合理 · 合起来把方案做臃肿」—— 承认了过度设计,却只让 AI 自己筛。v8.149 移除病因(不在此阶段做),而非继续筛。

### 改动(代码 1 处 + 文档)
- **`DEFAULT_REVIEW_ROLES[("Feature","goal")]`**:`[pm,qa,architect,pl,external]` → `[pm,qa,architect,pl]`(唯一硬接线处)。verdicts 门禁通用(谁在查谁 · 不硬要 external)· pl_challenge 独立 → 拆得干净。
- **能力保留**:`EXTERNAL_STAGE_TO_PROFILE` 仍含 goal · 确需对某 PRD 上 external → `change-review-roles --stage goal --roles '...,external'` 显式 opt-in(降默认不删能力)。
- **goal 过度设计防线 = Architect 简洁性 counter-lens(内审)**:external 走后这条内审 lens 成为 goal 唯一简洁性把关 · 文档强化。
- 文档对齐:goal-stage.md(默认 5→4 · 删 External Reviewer bullet · 新「goal 不做 external」段 · 重点 review 指引去 external)· prd.md 模板(reviewers/verdicts 示例)· prepare.md 角色表 · FLOW_STAGE_CHAIN hint。测试 1 处 pin 更新(simplicity-lens v8.76)。
- 🔴 敏捷需求 goal 本就无 external(不变)· Feature Planning goal/planning 的 external **未动**(不同 flow · 跨 feature 粒度 · 待用户单独定夺)。

### 验证
- pytest 3 failed / 527 passed(baseline 3 · 零回归)· build_default_stage_review_roles('Feature')['goal'] 验证去 external · blueprint external 保留。

