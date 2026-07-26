# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.292 · WS 拆解按交付内聚 · 不按评审面 · 默认合并

> 用户拍板:**WS 拆解都按交付内聚方向拆,不要按评审面拆,尽量不要拆太多 feature。**
> 审出的问题:原判据虽已写「主判据 = 交付内聚」,却在**同一行**把「评审 blast radius」列为合法拆分理由,并把它放进「保持独立的硬理由」清单 —— 那恰恰就是按评审面拆。

### 为什么按评审面拆是错的(写进判据)
横切出来的件**各自不能独立上线**(前端等后端 / 后端没人用),feature 数与跨件协调成本上升,**而评审总量并没变少**。内聚单元确实大到评审吃不消时,正解是:① 找**更小的内聚切片**(仍是端到端可交付的**纵切**),或 ② 接受多轮评审(review 收敛协议管这个:severity 门 / 验证轮 / 轮次预算)—— **不要**为了好评审把不能独立交付的东西拆开。

### 改动
- `docs/feature-planning.md` Step 5.7 边界判据重写:**交付内聚 = 唯一主判据** · 🔴 **默认合并 · 拆分是例外**(每一刀都要说得出「为什么这两件不能一起交付」,说不出就并回去)· 显式列反模式(代码在不同子项目 / 前后端分属 / 改动面大不好评审 **都不是理由**)。
- **保持独立的硬理由从四类收到三类**:外部依赖 gate(不绑架宿主交付)/ 交付节奏不同(上线时点本就分开)/ 管辖边界(不同团队拍板)—— **删掉 blast radius**。薄承接件默认并入宿主件 · 含金量悬殊 = 强合并信号(保留)。
- **粒度反压加严**:BL > 8 → **> 6**;触发条件加「按评审面横切」;默认姿态明写为合并。
- 同步 `templates/workstream.md`(拆分按交付内聚 · 不按子项目切、**不按评审面切**)+ `state.py` planning-check 清单。

### 机器守护(反压从文本变物化)
`ws-lint` 新增 `granularity_warnings`:features > 6 → WARN(**不 FAIL** —— 拆得对不对是判断题,机器只负责把问题摆到台面,不代用户拍板),warning 正文直接给出复核清单(逐件问「为什么不能一起交付」+ 反模式提醒 + 薄件合并信号)。

### 验证
- 新增 test_ws_granularity_v8292(8:交付内聚唯一主判据 / 评审面显式禁止 / blast radius 已移除 / 超大内聚单元有正解指引 / 模板与清单同步 / 7 件 WARN / 6 件不 WARN / **WARN 不是 FAIL**)· pytest **964 passed**。

## v8.291 · 跨厂商异质模型评审彻底退役 · 第三视角唯一形态 = 错开模型 subagent 冷审

> 用户拍板:**跨厂商异质评审太耗时,效率影响严重,彻底去掉,改为 subagent 不同模型冷审。**
> 实证支撑(台账):`codex exec` 挂死 98m 后杀掉重试 · OpenAI「Additional safety checks」慢路径(代码评审 prompt 天然命中)· 反复踩未登录 / MCP spawn 卡死 / ARG_MAX。而**同厂商模型错开**(会话 fable5 → 外审 opus)已拿到独立采样的主要收益 —— 上下文隔离 + 权重错开,零 CLI 成本。

### 拆除量(不是加开关 · 是整条路径连机械一起删)
| 层 | 删除 |
|---|---|
| `state.py cmd_external_review` | **770 → 85 行**:host→model 映射 / `which <cli>` / `--preflight` 登录探测 / CLI exec 与超时 / stdout 质量检查 / `--self-review-fallback` 降级 / `degraded`·`heterogeneous` 语义 / dry-run |
| 死 helper | `_preflight_external` · `_external_timeout_sec` · `_detect_cli_version` · `_check_external_review_quality` · `_read_disable_external_review` · `_localconfig_disable_external`(合计 ~140 行) |
| 命令参数 | `--host` / `--model` / `--codex-model` / `--preflight` / `--self-review-fallback` / `--reason` / `--dry-run` / `--accept-quality-warnings` / `--prompt-doc` 全去(留 `--feature --stage --commit --base --verify-fixes`) |
| 产物门禁 | `_evidence_external_review_artifact` **136 → 30 行**:异质性硬约束(文件名模型白名单 / review_model 字面比对 / degraded 语义 / host 比对)整套删 —— **没有可冒充的对象了** |
| 配置 | `disable_external_review` 退役(自愈默认表 / 三处 helper / 五处文档 · 存量配置被忽略) |
| 规范 | `standards/external-model-usage.md` **286 → 63 行**(跨厂商机械全删 · **裁决纪律 §12 原样存活** —— 它与模型无关且被 5 处引用) |
| profile | `codex-agents/`(3 个 toml)整目录退役 · `claude-agents/reviewer.md` 去 codex 对照段 · `update.py` 白名单同步 |
| 测试 | 退役 94 条测已删机械的用例(`TestExternalReviewCommand` 30 · `TestHostAutoDetect` 7 · `TestExternalReviewHeteroEnforcement` 14 · `test_external_mech_v8191` 整文件 …)· 换 20 条新契约用例 |

### 新契约(收敛为两条 + 一条不变式)
- ① **必须隔离 subagent**(`review_via: subagent`)—— 主对话热审 = 同上下文 = 零独立性;
- ② **必须照实申报模型**(`review_model` 非空)—— 供台账核「错开」是否真发生;
- 🔴 **yolo 不内化律存活**(v8.67):无人值守时额外要 **prompt doc**(实跑证据 · 由 `external-review` 落盘)—— 防 AI 直接手写产物自盖章。证据载体从「CLI 子进程日志」换代为「配方 doc」;`ultra-ingest` 产物豁免(provenance 是会话转录)。

### 🔺 顺带的门禁增强(拆除的副产品)
「fix 后 APPROVE 必须有 external 验证证据」原有 `disable_external_review=true` 豁免 —— 那个豁免**只因跨厂商 CLI 太贵才存在**。外审变成廉价 subagent 后**豁免取消**:这道门现在无条件生效。同理 legacy 全局日志路径 `~/.teamwork/external-review-logs` 一并退役(它还会污染测试隔离)。

### 验证
- 新增 test_cross_vendor_retired_v8291(9:机械已删 / 配置退役 / codex-agents 删除 / 命令不 exec / 新契约成文 / **yolo 不内化律存活** / 裁决纪律存活 / 全库无残留活配置 / 唯一形态成文)· pytest **956 passed**。

## v8.290 · 流程文档整体精简 + PRD/TECH 设计文档档位规则

> 用户原则:**保住底线规则,其余不限制模型发挥,精简没必要的 HOW**(示例:架构视角只需「架构要合理、防止未来维护成本过高」· 至于怎么设计 AI 自决)+ 新规则:**PRD、技术方案必须主模型或高级模型出设计或参与评审**,其余尽量主对话编排 subagent 并行。

### ① 新规则:设计文档档位(5 处消费时点)
- **PRD 与 TECH 必须主模型 / 高级模型出设计或参与评审** —— 与 v8.268/269 模型错开复合:**错开也只在高档之间错**(fable5↔opus)· **不许降到验证档**;其余环节(TC 对照 / 测试执行 / 机械外化)该降就降,**主对话编排 · subagent 并行**。
- 落 `DISPATCH_TIER_REMINDER`(每 stage-start 自动附带)+ goal/blueprint 两 brief + 两 stage ②硬规则白名单。
- why 写明:PRD 定义「做什么」错了整条链在做错的东西 · TECH 是全局质量上限方案错了下游全错 —— **两份设计文档定质量天花板**。

### ② 文档精简(判据:证据/独立采样/主权/机械/逆默认 = 底线保留 · HOW-to/示例/重复/考古/铺陈 = 砍)
| 文档 | 行数 | 🔴 |
|---|---|---|
| SKILL.md | 754 → **544**(-28%) | 74 → **43** |
| docs/prepare.md | 412 → **365** | 33 → 26 |
| docs/feature-planning.md | 294 → **287** | 43 → 39 |
- **行 205 的 3173 字符怪物拆成 9 条**(最长 391)· v8.268 双路 + v8.269 单路合并成一条「**评审模型必错开(独立采样不变式)**」。
- 砍:v7/v8 范式对比图 · 45 处版本沿革标注 · 错误处理协议 ASCII 流程图(与 bypass 节同一件事)· 文档清单与路由速查两表合并(零文档丢失)· 31 处重复标红降级 · prepare「怎么侦察」的具体清单(**要不要侦察是底线 · 怎么侦察留给模型**)· feature-planning 里 IA 镜像律/分层同构律的展开(改指 ui-design 权威处)。
- `roles/architect.md` telos 改为用户示例形态:**底线「架构要合理——别让未来的维护成本过高」+ 显式「至于架构怎么设计 AI 自决」**;`roles/rd.md` 同款。其余 6 个 role telos 本就是「说视角 + 缺了会留什么问题」,未动。
- `docs/conventions.md` **如实不砍**:288 行几乎全是 ID/命名约定与路径/状态机接口(判据④ 模型不可能知道)。

### ③ 顺带抓到三个真问题
- 🐛 **SKILL 指向 `blueprint § 7.5`** —— 该章节已随 v8.284 四段结构重构消失 → 改指 `§④`。
- 🐛 **命令清单已漂**:自称「≈55 命令」,52 个真实子命令里 **11 个从未出现在 SKILL.md**(整个 micro 流程 `execute-start/complete` · `review-preventability` · `ws-lint` / `ws-progress` / `test-baseline` / `ledger-migrate` …)。文档自称「权威 = `state.py --help`」却抄了份过时副本 —— **又是「指针 + 复制」**。改分类概览(A 状态机入口 / B stage 流转 / C 维护与数据)+ 权威指针,保住 11 个 routing 级语义特殊命令。
- 🐛 **`UI-RULES.md` 从未进 SKILL 路由表**(既有缺口 · 非本次砍掉):它是 ui_design 必读 + bootstrap 七件骨架之一,用户问「设计规范在哪」路由不到 → 补入(连同 `test-baseline.md`)。

### 验证
- 新增 test_flow_doc_slimming_v8290(9:无超长行 / 🔴 密度 / 命令清单是指针非副本 / routing 级命令仍在 / 底线全在 / 断链已修 / role telos 底线+自决 / **project-specs 清单跨文件同步守护**〔SKILL 路由表 ↔ conventions §13 · 把 v8.259 的人工七点清单换成机器检查〕)· pytest **1041 passed**。

## v8.289 · REVIEW-<role>.md 退役 · 改为 REVIEW.md 内每角色 coverage 申报

> 用户:重新 review 流程,看哪些过程文档没必要写。用同一把尺子(**有没有真读者**)过完全部产物 —— 其余都有真消费方(PRD/TC/TECH 被 dev 照做 + verify-ac 机器读 · REVIEW.md findings 台账 70 处消费 · TEST-REPORT 是 pm_acceptance 逐条核对 AC 的实证来源 · verdicts 被门禁解析 · screenshots 是用户验收证据),**只有 `REVIEW-<role>.md` 是纯仪式**。(`docs/audit/<id>.md` 用户指示暂不动。)

### 四条证据
1. 门禁 `_evidence_review_role_artifacts` 只查**文件存在**(`.exists()`)· 不解析任何内容;
2. 角色归属**早已在 REVIEW.md** —— findings 台账每条带 `source: arch|qa|external`;
3. **实测就是写两遍**:aifriend `REVIEW-arch 37 行 / REVIEW.md 38 行` · aon-core `55 / 63`;
4. 内容形态是**确认性叙述**(「实现对齐 TECH」「架构一致」「无回归风险」…),不是 finding。

### 但保住了它的真价值
光秃秃 `APPROVE` + 零 finding,与「根本没评审」在产物上**无法区分** —— 这个防橡皮图章的性质不能丢。改用 external 早在用的 **coverage 申报**形式:REVIEW.md 内每个 roster 主审角色**一行**申报查过的方向(有问题列 finding · 无则「查过无发现」)。成本从 40 行降到 1 行,性质不变。

### 改动
- 门禁换代:`review_role_artifacts`(文件存在)→ `review_role_coverage`(REVIEW.md 内申报)· **roster-aware 语义原样保留**(移出的角色不查)· legacy state 无 roster 时跳过(不对存量加严)。
- REVIEW.md frontmatter schema 加 `coverage:` 段示例;review-stage ②规则 8 + Output Contract 改写。
- 全链清理:review brief 结果段与 complete 命令 `--artifacts REVIEW.md`(去 REVIEW-arch)· engine 产物模板表 / 归档文件名表 / complete 命令模板 / roster 注释 · fast 与 Bug brief 措辞 · SKILL fast 节 · templates/README。
- 常量正名 `_REVIEW_ROLE_ARTIFACTS`(role→文件名映射)→ `_REVIEW_MAIN_ROLES`(角色集)。

### 验证
- v8.241 的 4 条 roster-aware 测试改写为新机制 6 条(roster 移出不查 / 缺申报 FAIL / 申报形式宽松 / legacy 跳过 / 空 roster / **Bug 流 external-only 无需主审申报**)· pytest **1028 passed**。

## v8.288 · tdd.md 退役(三条规则已在白名单 · 留着就是第二份副本)

> 用户:「如果 TDD 只有三行,是否不用单独一个文件了」。核实后确认——**比预想的更该删**:v8.287 留下的三条结果规则里,**两条与 HARD-RULES 逐字重复**(每个 TC 有对应实现 / 测试必须真断言),第三条(≥3 次失败升级)也在。tdd.md 已经退化成我们一路在消灭的「指针 + 复制」第二份副本。

### 退役
- 删 `standards/tdd.md`(42 行)· 吸收其唯一独有内容:「结果由谁保证」表 → 压成 HARD-RULES #8 下的一行(AC 覆盖 → `verify-ac.py` · 真跑真绿 → `--test-exit-code 0` + `--test-stdout` 非空 + 差分基线 · 没作弊 → test-stage ②不走捷径 + 外审测试真实性)。
- **10 处入链改指 HARD-RULES**:STANDARDS.md 路由表 + 三条子项目加载链 · backend/frontend 的「TDD 流程唯一权威源」头注与 Subagent 加载指引 · common.md · dev-stage §相关 · blueprint ③菜单 · tech.md · 2 处测试。
- `standards/` 从 6 件 → 5 件:HARD-RULES(50 · 必读)+ common(354)+ backend(551)+ frontend(90)+ external-model-usage(286)+ scripts-policy(232)。

### 顺带:通用断链守护(治本)
- 新增 `test_all_standards_links_resolve`:全库扫 `standards/*.md` 引用,**指向不存在的文件即红**。
- 实证驱动:v8.285 删 stage heading 造成 6 处 cite 失效(靠 agent 报出才发现)· v8.287 退役 tdd.md 需手改 10 处入链 —— 这类操作该被自动拦,不靠人肉 grep。
- 另加 `test_tdd_md_retired`:退役前**必须确保三条规则已在白名单**(防「删了文件规则也跟着没了」)。

### 验证
- pytest **1026 passed**(+2)。
