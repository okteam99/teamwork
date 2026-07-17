# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.262 · yolo 忽略 fast + PRD 送审前自检(评审关注点前置)

> 用户两令:①yolo 模式忽略 fast(不再互斥报错);②优化 PM 写产品文档的约束 —— 把要评审的点提前考虑进去 · 不要等评审有问题再改。

### ① yolo 忽略 fast(v8.261 互斥 → v8.262 静默覆盖)
- `--yolo` + localconfig `fast_mode: true` → **不报错** · fast 静默不生效(无人值守回全量评审安全网)· kickoff concerns 记 INFO 留痕(用户知情)。修复顺带抓到的缩进 bug:原实现 yolo 分支后 roster 仍被改成 fast 伪角色 —— 已归位 else 内。
- SKILL fast 节 / config.md / localconfig 注释 三处同步。

### ② PRD 送审前自检(评审关注点前置 · 治 Round 2+ 修订循环)
- 数据:goal 占 AI 自主 44% · 大头 = 修订循环;finding 采纳率 80-90% = **多数问题可预见** · 前置消掉最省。
- **templates/prd.md 新增 §送审前自检**(起草完 · 送冷审前 · 逐项打钩):PL 六问自问(答不出先补 · 别指望冷审替你想)/ **可实现**自查(依赖的接口字段真实存在 · 读过真实代码非假设)/ **可验证**自查(AC 可测 · 无「尽量/合理/优化」含糊词 · 边界异常有归宿)/ 高频 finding 预检(术语已定义 · AC 无矛盾)。
- goal-stage ③ 起草段 + goal brief 8 步链(起草 v0.1 → **送审前自检** → 冷审)消费点同步。

### 验证
- pytest 912 passed。

## v8.261 · fast mode 语义修正:留两端单路合并评审(PRD:PL+外审合一 · 代码:Architect+QA 合一)

> 用户改逻辑:fast 不再全拆 —— **留 PRD 评审**(把 external 和 PL 关注点合并)+ **留代码 review**(把架构师和 QA 关注点合并);blueprint 评审仍去。从「零评审」修正为「两端各一路合并评审」:质量关口保住需求侧与代码侧两个最值钱的位置 · 砍掉的是多路独立性与中段方案评审。

### 语义(v8.261 覆盖 v8.260)
- **roster = `{goal: [fast], review: [fast]}`**(「fast」= 合并伪角色 · 单隔离 agent 兼多帽):
  - **goal 单路合并冷审**:兼 PL(质疑六问 ≥1 实质)+ 外审(可实现/可验证 + AI 自主方向)· 产单份 PRD-REVIEW.md(`reviewers: [fast]` · `verdicts: {fast: ...}`)· **verdicts 全 APPROVE 门照拦**(v8.260 的 skip 撤销 · PRD-REVIEW 恢复必产必查);
  - **review 单路合并评审**:兼 Architect(实现↔设计一致性 · 简洁性 counter-lens)+ QA(测试真实性与覆盖 · 代码质量盲区)· REVIEW.md 单份 · **findings/severity/验证轮/轮次预算协议照跑** · 无 REVIEW-arch/-qa/external 独立产物(roster-aware 门自动放行);
  - **dev → review 恢复正常转移**(v8.260 的跳 review 撤销 · 三链图 test 边还原)。
- 不变:blueprint 评审去(TECH-REVIEW 不产不查 · `review_artifact` 标记保留)· 测试硬门/verify-ac/全部用户暂停点/worktree/ship 全链保留 · 与 yolo 互斥 · 默认关。
- 消费点:goal/blueprint/review 三 brief 的 fast 条件行(合并关注点清单写死)· SKILL fast 节 · config.md/localconfig 注释。

### 验证
- 测试改写至 v8.261 语义(+1:三 brief 合并 mandate 断言)· pytest **912 passed**。
