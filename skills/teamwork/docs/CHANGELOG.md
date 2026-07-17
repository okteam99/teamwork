# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.257 · DEV-RULES 三项制:API 契约 / 错误处理 / 其他约定(架构归 ARCHITECTURE · 命名风格测试归 standards)

> 用户拍板简化:架构已有 ARCHITECTURE.md · DEV-RULES 只留三项。原六段(架构分层/命名/错误处理/测试策略/代码风格/其他)与 ARCHITECTURE.md、standards/ 缺省存在职责重叠 —— 项目真正需要人来强制注册的就三类:**对外契约、失败语义、杂项强制特例**。

### 改动
- **templates/dev-rules.md**:骨架六段 → 三段。新增 **API 契约** 段(响应包络/错误码结构/分页/字段 casing/版本兼容 —— 存量风格 = 对外契约 · 沿用并在此注册 · standards 覆盖声明唯一注册处);**错误处理** 保留;**其他约定** 兜底(命名/风格/测试策略若有偏离 standards 缺省的强制特例注册在此)。
- **去向声明**:架构/分层/依赖方向 → `ARCHITECTURE.md`(workspace/{子项目})+ ADR(边界表加行);命名/风格/测试策略 → standards/ 缺省。
- **五处消费点词表同步**:SKILL 文档信息架构表 + 路由表 · blueprint-stage 必读行 · knowledge 边界表 · 模板自身定位句。

### 验证
- 纯模板/文档 · pytest 903 passed(bootstrap 只建空壳 · 存量项目 DEV-RULES 不受影响——已存在绝不改动的原则不变)。

## v8.256 · 效率三刀:验证轮降档 + TC∥TECH 起草并行 + goal 终确认投机窗

> 台账年检第二批(用户令「整个流程还有什么办法提升效率」)· 提五刀 · 用户拍板:①④+投机 TECH 做;**②(ship1 等合并窗启动下一 BL)不做——是否启动下一个 prepare 不确定 · 用户主权**;**③(auto 推荐)不做——不启 auto 的目的就是人工确认 PRD 与 DB 变更 · 等待是有意设计不是浪费**;⑤(波次推广)不做。

### ① 验证轮降档(goal/review Round 2+ → 验证档模型)
- 数据:goal 占 AI 自主 44%(大头=冷审修订循环 · finding 采纳率 80-90% 必有 Round 2+)· review 33% 到 3 轮;验证轮任务性质 = 校验型(核实 fix + 范围锁定内找新 · 对照清单)· 按档位规则本该验证档 · 但文档从未点名 → AI 默认继承重档。
- 落点:`_review_verify_round_brief`(Round 2+ 的消费时刻 emit)+ goal-stage ③ / review-stage 硬规则 5 / goal brief。首轮全量冷审不降档。预估砍 goal+review 循环成本 ~10-15% AI 自主时间。

### ④ TC ∥ TECH 起草并行(blueprint)
- TC 锚 PRD.AC · TECH 锚设计方案 · 相互独立 → **并行同发**(subagent 各一)· 完成后互查 `covers_ac` ↔ §测试策略。blueprint 中位 27m · 预估省近半。

### 🔮 goal 终确认投机窗(上一轮提议 · 本版落地)
- 时点纪律:**只在 emit 终确认暂停点后投机**(冷审收敛前 PRD 是活靶 · v1 时点必返工);数据:终确认「改:默」≈ 全默(变动率≈0)· goal 等待中位 26m ≈ blueprint 起草中位 27m(等待窗恰好藏下)。
- 行为:等待窗后台派 TECH 草稿 subagent(worktree 内草稿 · 🔴 不跑 state 命令);用户 ok → blueprint 接续;有改 → 差量更新;auto/yolo 不适用(无等待窗)。落点:goal-stage ④ 投机窗 + goal/blueprint brief + SKILL 等待窗条目补例。

### 拍板否决留档(防未来再被「优化」)
- ship1 等待窗启动下一 BL:❌ —— 启动 BL = 用户拍板事项(feature-planning 坑 5 同源);auto 推荐判据:❌ —— 中间等待点是**有意设计的确认闸**(PRD/DB 变更)· 非浪费。

### 验证
- 纯文本/brief · pytest 903 passed。预估三刀合计:中位 feature AI 自主 182m → ~150m · 墙钟 -15% 左右。
