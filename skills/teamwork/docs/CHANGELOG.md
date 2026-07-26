# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.287 · TDD 手段规定整体撤除 · 只管结果(怎么测 AI 自觉)

> 用户:「TDD 是否不用写到规范里了,加一句确保每个 TC 用例都有对应实现即可」+「至于怎么做 TDD AI 自觉」。TDD 是**手段**,正是判据⑤(衰减类)的典型 —— 模型早已内建。框架该管的是**结果**,而结果已有机器门与评审兜着,所以撤手段不开洞。

### 撤除(手段规定)
- `standards/tdd.md` **93 → 42 行**:删 Iron Law(无失败测试不写实现)· RED-GREEN-REFACTOR · 自检清单 · 反模式 · **「跳过 TDD 须用户同意」的例外机制**(TDD 不再强制,例外机制自然失去意义)。
- dev ③菜单:「TDD 红绿循环 = 强烈建议的默认」→「**测试节奏 AI 自定**」(TDD 红绿 / 先骨架后补边界 / test-after 自选)。
- tech.md `## TDD 开发计划` → `## 测试与实现计划` · 节奏「AI 自定」;dev brief 目标行、`FLOW_STAGE_CHAIN` dev 描述、`roles/rd.md` telos、STANDARDS.md 路由表同步。

### 保留(结果规则 · 三条)
1. 🔴 **每个 TC 用例必须有对应实现** —— AC↔TC 由 `verify-ac.py` 管,**TC↔实现这一跳没有机器门**,靠本条(TC 写了没实现 = 需求链最后一米断掉,而「测试全绿」会盖住它)。
2. 🔴 **测试必须真断言 · 禁 mock 被测组件自身内部方法**(防假绿)——*模型默认倾向:为了让测试过,把正要验的那段 mock 掉。恒绿空壳测试比没测试更危险(门禁/评审/验收同时失效)。*
3. 🔴 **同一处失败修复 ≥3 次 → 停下升级**(这条**不是 TDD 规则**,是排障纪律 —— 模型默认会一直试)。
- HARD-RULES §一 的两条 TDD 方法论换成上述①②(③本就在)· tdd.md 补「结果由谁保证」表(verify-ac / test-exit-code + 差分基线 / 不走捷径 + 外审测试真实性 / TECH §测试策略)。

### 为什么撤手段不开洞(核实过)
假绿是唯一真风险,而它有三道结果侧防线:test-stage ②「不为凑 exit-code=0 走捷径」(skip 必含 reason · 不标 xfail)· review 外审**必覆盖**「测试真实性与覆盖」· review ③菜单「测试质量抽查(是否真断言 · 假绿检测)」。本版再加白名单第 ⑦ 条兜底。

### 验证
- 两处旧断言(锁 TDD 措辞)更新为新状态:白名单断言改结果规则 · v8.283 的「强烈建议的默认」改为**断言其不存在** + 断言「AI 自定 / 每个 TC 有对应实现」。pytest **1024 passed**。

## v8.286 · standards 硬规则白名单 + 读取路径接通(工程规范并集 · 项目优先)

> 承 v8.285。用户设计:**AI 读「框架工程规范 + 项目 DEV-RULES」的并集,冲突以项目为准**。落地时**没有新建 `dev-rules-teamwork.md`** —— `standards/` 本就是框架级那层(DEV-RULES 模板早写明分工),再造一个会成**第三个家**(v8.284 刚实测过「指针+复制」的漂移)。真问题是**读取路径不对称**:项目 DEV-RULES 是必读、框架 standards 不是,所以框架自己的规范只能被复制进模板才到得了模型(实测同一条日志规则曾活在三处)。

### ① `standards/HARD-RULES.md`(47 行 · 唯一必读)
- **收录判据 = 与模型默认行为的距离**(只收两类):**逆默认**(模型会做反的 —— 它越强越笃定,越需要明确逆着写)· **不可知**(框架/项目约定 = 信息不是规范)。**模型默认就会的一律不收**(REST/SOLID/TDD 步骤/mermaid/WCAG 细则)—— 收了就是注意力税。
- 逆默认 9 条:默认避免 FK(项目可覆盖)· 降级/fallback 必打 WARN(缺失阻塞 CR)· 三方异常必 ERROR · 不静默吞异常 · **两个 adapter 才抽象**(模型默认提前抽象)· 安全/兜底必过 ROI · NEVER refactor while RED / 禁 horizontal slicing / 禁 mock 自身内部方法 · TDD Iron Law(例外须用户同意)· ≥3 次失败即升级。
- 不可知 7 条:scratch 根与 feature_id 纪律 · `[DEBUG-…]` 前缀 + ship 前 grep · 测试脚本两层结构 · 结构化日志必填字段 · 统一响应格式与状态码 · 迁移命名优先级链 · Build 硬门。
- 分册(common/backend/frontend/tdd/external/scripts-policy)降为**按需查**,不要求通读。

### ② 读取路径接通(这才是原来缺的)
- blueprint ②1 + dev ②1 改为:**工程规范 = `standards/HARD-RULES.md`(必读)+ 项目 `DEV-RULES.md` 的并集 · 🔴 冲突以项目为准**。
- `templates/dev-rules.md` 边界表同步(项目侧视角:冲突以本文件为准)。
- **删最后一处同源副本**:tech.md 的日志规则正文 → 改指白名单(该规则原散在 standards + 模板两处)。

### ③ standards 深度精简 1290 → 1135(累计 1773 → 1135 · **-36%**)
- backend 655 → 551:日志级别表与 JSON 示例(模型默认就会)· API 响应示例 · FK 理由 10 行压成 2 行(**逆默认规则的 why 必须留** —— 否则模型会反驳或"修正"它,只是不必铺开)。
- tdd 127 → 93:RED-GREEN-REFACTOR 5 步教程删,只留框架强调的两点(红要真红 / 一绿点一 commit)。
- frontend 154 → 90:测试规范流程教程删,留项目约定的阈值与清单(覆盖率 / 分层 / 必测场景)。
- WCAG 细则与 ui-design 刚砍的 rubric 同类,但 frontend 那份含「禁 div onClick / 禁 aria-hidden 键盘陷阱」等**逆默认**项,保留原样。

### 验证
- 新增 test_hard_rules_v8286(9:白名单够短可必读 / 并集与优先级成文 / 收录判据成文 / 逆默认 6 条在 / 框架约定 5 条在 / blueprint+dev 读取路径已接 / dev-rules 模板同步 / 模板副本已改指针 / 分册总量)· pytest **1024 passed**。

## v8.285 · 四段结构推广完成(11/13)+ standards 减法

> 承 v8.284 解锁。**批次三**:除两个记录在案的例外,全部 stage 迁到四段结构。**standards 减法**:按「与模型默认行为的距离」判据砍 —— 模型默认就会的(零价值·纯税)砍、模型不可能知道的(信息)留、**模型默认会做反的(最高价值·模型越强越需要)** 一条不动。

### 批次三 · 四段结构推广(3/13 → 11/13)
| stage | 行数 | ②硬规则 |
|---|---|---|
| test | 179 → **112**(-37%) | 9 条 |
| panorama-sync | 112 → **73**(-35%) | 5 条 |
| pm-acceptance | 107 → **77**(-28%) | 4 条 |
| ui-design | 188 → **175** | 8 条(补回被漏的分层同构律领域模型) |
| blueprint | 98 → **83** | 9 条 |
| browser-e2e | 65 → **55** | 5 条 |
| diagnose | 67 → **65** | 7 条(③整段省略 · 原文本就没水分) |
| execute | 38 → **42** | ②③ 归位(原写反:②=自主/③=边界) |

- **记录在案的例外**(STAGES.md §3 明写 · 测试守护「不许有沉默的例外」):`ship-stage.md`(主体是命令序列 + 物化门禁的**操作手册**,四段治的是 HOW-to 教程不是必要操作次序)· `blueprint-lite-stage.md`(v8.223 已废弃)。
- **顺带修断链**:删 heading 导致 6 处 `§ 测试体系` / `§ SOP` / `§ 怎么做` cite 失效(test-report / browser-test-report / e2e-registry / specs brief)· 全部改指四段段名;`test-baseline --add` 的 `--test-id` + `--reason` 必填在旧文档漏写,补齐与 CLI 一致。

### standards 减法 1773 → 1290(-27%)
- **common.md 767 → 354**:🔴 砍 **RD 自查规范 + 报告模板 216 行** —— 全库**零机器消费者**(grep 无任何工具校验它)、零文档引用、与 `tech.md §完工自查`(review 真读)职能重复。**但抢救两条真规则**:Build 必跑通才进 Code Review(证据类硬门)+ worktree lazy-install 缺 build 工具链(真踩坑)。另压缩 §二代码架构规范(SOLID/分层教科书)· §四D QA 检查项(与 verify-ac + review 覆盖方向重叠)· §五 mermaid 语法。
- **backend.md 725 → 655**:TDD 手艺单源 `tdd.md`(它本就声明整段吸收)· 集成测试报告模板压成字段清单。
- **对照组保留**(判据:模型默认会做反的 = 最高价值):`默认避免 FK`(模型训练默认「加 FK 保证引用完整性」· 本框架明确逆着走)· 降级/兜底必打 WARN 日志 · 统一响应格式与状态码表 · 测试脚本两层结构 · scratch 路径约定 · **Designer 自查**(有 `verify-panorama.py` 物理校验 → 判据①保留,与被砍的 RD 自查形成对照)。
- 全部入链锚点验过不断链(prd.md→§五 · verify-panorama→§四B · ship/conventions→§六)。

### 验证
- 新增 test_standards_slimming_v8285(13:RD 自查已删 / 抢救规则仍在 / Designer 自查保留 / 逆默认规则保留 / 锚点不断链 / **四段结构推广守护:全 stage 合规 + 例外必须写进标准**)· v8.284 两处**措辞脆断言**改实质导向。pytest **1015 passed**。
