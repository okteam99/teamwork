# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.260 · fast mode:去掉所有评审环节(localconfig 配置 · 默认关 · 与 yolo 互斥)

> 用户点单:增加 fast mode · 去掉所有评审环节 · 默认关 · `.teamwork_localconfig.json` 配置开启。

### 语义
- **开关**:`fast_mode: true`(缺省/false = 关)· init-feature 时**快照进 `state.fast_mode`**(中途改配置不影响 in-flight feature)。
- **去掉**:goal 冷审(PL 质疑/外审 · 不产 PRD-REVIEW.md)· blueprint 评审(Architect 主审/外审 · 不产 TECH-REVIEW.md)· **整个 review stage**(dev 直进 test)。
- **保留**:测试证据硬门(exit 0/差分)· verify-ac · 全部用户暂停点(prepare/PRD 确认/DB 确认/pm_acceptance/ship1)· worktree 纪律 · ship 全链。
- 🔴 **与 yolo 互斥**(init-feature 硬拦):yolo 无人值守的唯一安全网 = 自动化评审 · fast 恰好拆掉它 —— 有人值守下 fast 才安全;与 auto_mode 正交可叠。

### 实现
- **state.py**:`_read_fast_mode`(默认 False · 显式 true 才开)· init-feature 快照 + roster 全清空(roster-aware 门自动放行 · adjustments 审计留痕)+ yolo 互斥拦;三链图 dev 边 +`test`(fast 转移合法)。
- **engine**:`StageArtifactSpec.review_artifact` 标记 + complete 校验循环 fast 跳过(PRD-REVIEW/TECH-REVIEW 标记)。
- **specs**:`_dev_transition` fast→test · `_check_review_approved`(test 前置)fast 放行 · `_evidence_prd_verdicts_all_pass` fast skip · goal/blueprint brief 条件提示行(⚡ fast_mode 生效 · 去了什么留了什么)。
- **配置面**:localconfig 模板 + config.md 文档段(含警示:质量安全网自拆 · 原型/个人适用)· SKILL 模式区新 fast 节(auto/yolo 并列)。

### 验证
- 新测试 +8(读取三态 / dev 跳 review / 图边合法 / test 前置放行 / PRD verdicts skip / 产物标记正反)· pytest **911 passed**。

## v8.259 · RELEASE-GUIDE 入图:DEV-RULES 协作区互链 + teamwork-space 知识入口登记

> 用户点单收尾:①DEV-RULES 关联发版规范 ②teamwork-space 目录加该文档。零死角律要求磁盘上的知识节点必在地图有指针 —— v8.258 建了文件 · 本版把它接进知识图谱。

### 改动
- **templates/dev-rules.md 协作区**:+`RELEASE-GUIDE.md` 互链(「本文件管怎么写码 · 它管怎么发版」)。
- **templates/teamwork-space.md 知识入口**:project-specs 行「内含」列更新 —— +RELEASE-GUIDE(发版)· 顺带纠旧清单(去已废 RESOURCES · 补 UI-RULES/PROCESS-LEDGER · 标注清单单源 conventions §13)。

### 验证
- 纯模板 · pytest 903 passed。

## v8.258 · RELEASE-GUIDE.md:版本发布规范(用户点单 · 默认 staging→main MR + URL 置顶 + 提醒合入)

> 用户拍板新增:RELEASE-GUIDE.md 作为版本发布规范 · 默认内容 = 发布到线上流程:创建 staging → main 的 MR/PR 后给出 URL · 提醒用户合入。填补的空档:「发布/上线」此前无任何流程覆盖(ship 只管 feature → 集成分支;集成 → 生产无人管)。

### 改动
- **templates/release-guide.md**(新):默认五步流程 —— ①核对 staging(列本次上线清单给用户过目)②创建 staging→main MR/PR(CLI-first)③🔴 URL 置顶独立行原样贴(同 ship1 user_card 纪律)④🔴 提醒用户合入(AI 不代点 · 可轮询监控)⑤发布后义务(核对各 feature REVIEW 的 release-gated 待补证据〔v8.251〕逐项补跑)。+ 环境分支段 / 项目特有步骤段(人维护)。
- **边界声明**:本文件管「集成分支 → 生产」;单 feature 交付(feature → 集成)归 ship stage · 别混。人维护原则同 DEV-RULES(bootstrap 无则建 · 已存在绝不改 —— 但模板自带可用默认 · 非空壳)。
- **bootstrap 骨架**:skeletons 六件 → **七件**(+RELEASE-GUIDE.md)。
- **消费点**:SKILL 信息架构表 + 路由表(「发布/上线/发版 → RELEASE-GUIDE.md · PMO 必读照办 · 合入归用户」)· conventions §13 · templates/README 索引。

### 验证
- 骨架测试 fixture +release-guide · pytest 903 passed。
