# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.266 · 修正 v8.265:兜底不是「默认不做」· 是逐项算 ROI

> 用户修正:「不是默认不做,需要考虑 ROI」。v8.265 把判据写成了先验偏向(默认不做 / 重点砍除对象)—— 正解是**中性算账**:每个兜底逐项算 保护场景的真实概率×后果 vs 实现维护成本,**ROI 立得住 → 做;立不住 → 砍**。两个方向都不许偷懒:AI 天然偏加兜底(别不算账就加),但高概率×高代价的兜底是正收益(别一刀全砍)。

### 改动(纯措辞纠偏 · 透出机制不变)
- prd.md 思考规范:「默认不做」→「按 ROI 取舍(立得住做 · 立不住砍)」。
- tech.md:判据条改「兜底按 ROI 取舍 · 两个方向都别偷懒」;清单表列「为何值得」→「ROI 结论(vs 实现维护成本)」;清单引导「确需保留」→「ROI 立得住而保留」。
- blueprint §4 lens:「兜底是重点砍除对象」→「兜底按 ROI 审 · 两个方向都要实证」(对齐既有裁决举证对称原则);§7.5 触发条与暂停点兜底块同步 ROI 措辞。
- specs brief TECH 结构行同步。
- 不变:兜底清单落盘单源 · §7.5 双触发透出 · 用户拍板 · auto skip+WARN。

### 验证
- 纯措辞 · pytest 912 passed。

## v8.265 · 兜底纪律:默认不做(复杂度×收益)· 确需的在暂停点透出拍板

> 用户令:产品方案和技术方案要考虑复杂度和收益 · **不要做没必要的降级兜底和安全兜底**;确需的兜底策略必须**在暂停点明确提出来**(不许默默做)。AI 天然偏加兜底(重试/降级/防御层)—— 每层兜底都是复杂度,且历来藏在方案正文里从不被拍板。

### 改动(写法 + 判据 + 暂停点透出 三层)
- **写法**(v8.263 形态 · 起草时思考):prd.md 🧠 起草思考规范 +1 条 —— 涉降级/兜底体验默认不做 · 确需的是**产品决策** · 列 §待决策项或终确认导读;tech.md 简洁性自查 +1 条 —— 每个 fallback/degradation/重试熔断/防御层过「真实概率×后果 vs 实现维护成本」· 写不出必要性 → 删。
- **判据落盘**:tech.md 新 **🛡️ 兜底清单**表(兜底|保护什么失败场景|概率×后果|为何值得)· 无则写「无兜底」—— 透出的单源。
- **暂停点透出**:blueprint **§7.5 扩展为双触发**(v8.265):DB 数据结构变更 **或 兜底清单非空** → R5 方案要素确认暂停点(两类命中一次给全 · 兜底块照抄 TECH 清单);goal 终确认导读余节 + 🛡️ 兜底策略行(PRD 层降级体验 · 无则「无」)。auto 模式同款 skip+WARN(消息含 兜底 摘要)。
- **评审侧**:blueprint §4 Architect 简洁性 counter-lens 点名「兜底是重点砍除对象」。
- 消费点:specs blueprint brief(§7.5 双触发 + TECH 结构行含兜底清单)· SKILL 授权暂停点清单 ④ + auto 表 blueprint 行改「方案要素确认(DB 变更/兜底)」。

### 验证
- 纯模板/文档 · pytest 912 passed。

## v8.264 · localconfig 两修:fast_mode 入自愈默认表 + 「可提交」文档漂移纠正

> 用户问「.teamwork_localconfig.json 什么时候创建」· 答题时撞出两个实质问题:①v8.260 加 fast_mode 时漏了 `LOCALCONFIG_CONFIG_DEFAULTS`(:708 明写「新增字段两处都加」)—— **存量项目的自愈永远不会补出这个新选项 · 用户看不到**;②conventions §13 说该文件「可提交」· 但 bootstrap 实际把它加 .gitignore(`_bootstrap` 段含 host/maintain 时间等机器态)—— 文档与机器行为相反。

### 改动
- **bootstrap `LOCALCONFIG_CONFIG_DEFAULTS` + `fast_mode: False`**:存量项目下次 session 自愈即补出字段(带注释 · additive 不覆盖已有值)。
- **conventions §13 纠正**:`.teamwork_localconfig.json` = **本机级 · bootstrap 自动 gitignore** · 团队共享档位靠各机自配(非 git 共享)。

### 验证
- pytest 912 passed。

## v8.263 · 修正 v8.262:起草思考规范是「写法」不是「环节」

> 用户修正:「不是加自检环节,是写 PRD 的时候按这个规范去思考」。v8.262 把评审关注点做成了**写完后过的自检清单段**(§送审前自检 · 逐项打钩)—— 形态错了:那是又加一道仪式;用户要的是**起草时的思考方式**,关注点织进写的动作里。

### 改动
- **prd.md**:删 §送审前自检 整段;模板头新增 **🧠 起草思考规范**(写的时候就这样想 · 非写完检查):写背景/方案时 PL 六问过脑(写不顺的地方就是冷审会打的地方)· 写每条 AC 时用可测判据(「尽量/合理/优化」**落笔即换**)· 涉依赖先读真实代码确认存在再写 · 术语当句定义;AC 表注释就地强化(写时即用可测判据)。
- **goal-stage ③**:「送审前自检」段改写为「起草思考规范(写法非环节)」;**goal brief**:撤独立自检步 · 思考规范并进「起草 v0.1」步内注。

### 验证
- 纯模板/文档 · pytest 912 passed。
