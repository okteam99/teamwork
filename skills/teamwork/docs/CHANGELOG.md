# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.284 · 四段结构转正(解锁推广)+ 批次二 stage 减法

> 承 v8.283。审计挖到**推广卡死的根因**:`STAGES.md §3` 至今**必含**「怎么做 + 质量基线」两段 —— 已迁移四段结构的 dev/review/goal **反而不符合书面规范**,未迁移的 test/panorama_sync/pm_acceptance/diagnose **是在忠实遵守旧条款**,不是偷懒。v8.218 试点时写下「四段结构进 STAGES.md 定为标准」这一步没做,推广就此卡在 3/13 达六十余版。

### ① STAGES.md §3 四段结构转正
- 必含段改为:`① 目标(telos)` / `② 硬规则(白名单 · 每条一行 why)` / `③ 建议手段菜单(AI 自选 · 不强制 · 可省)` / `④ Output Contract` / `相关`。
- 明写 **②硬规则保留判据**(治结构风险不教干活):证据/验证 · 独立采样 · 用户主权 · 纯机械操作;**不该进②的**:怎么调研/怎么拆任务/怎么写代码(→③或交还模型)· 通用工程规范(→ `standards/` + 项目 `DEV-RULES.md`)。
- 明写**删「怎么做」与「质量基线」的理由**:前者是 HOW-to 教程「把强模型的地板变天花板」(v8.218 原话);后者把②的规则再复述一遍(实测未迁移文件因此把同一规则讲 2-3 遍)。**叙事在②一次 · 机器语法在④一次 · 没有第三处**。

### ② 批次二 stage 减法(门禁/暂停点一条未动)
- **ui-design 244 → 188**:🔴 21 行交互/视觉细则(hover/focus-visible/WCAG 4.5:1/触控 ≥44px/tabular-nums…)压成 **5 条判据** —— 原文自陈理由是「模型对交互体验缺天生判断力」,该前提已随模型能力失效;**v8.263 裁定的最后一处漏网环节化自检**(Designer 自查报告 A 段逐项过)改写法注;删「与老模式对比」论证表 / preview.sh 内部实现 / 工具面板 12 行设计品味论证与版本纠错史 / 纯目录式反模式清单 / 框架维护者 TODO;`roles/designer.md` 指针同步。
- **blueprint 120 → 98**:🐛 **修真实缺陷** —— §3 与 Output Contract 曾给 TECH.md **9 段 vs 5 段两份互相矛盾的清单**(「指针 + 复制被指向内容」的漂移实例);消除该模式(结构以模板为单源)· R5 三选项改引用式(与 ui-design 统一口径)· 删与 §4/SOP 重复的冷审与闭环条。
- **ship 235 → 221**:只砍旁白 —— 版本考古(旧两-MR 十二版沿革)· archive/ship-finalize 内部实现清单 · 投递次序**三处各说一遍**收敛为单源 · active_minutes 算法(同行已明写「不肉眼算」)· 已废弃配置墓碑 · 框架维护者 TODO。**门禁、命令序列、R5 暂停点、git add 红线一条未动**。

### ③ 兜底清单机制升级(v8.277 手段迭代)
- 原手段「blueprint 与 tech.md 两表同构」→ **单源 + 指针**(blueprint 改「照抄 TECH §兜底清单原样贴出 · 含 💬 大白话列」)。目的不变(暂停点贴出的表别丢列),但**只有一处定义才不会漂** —— 同一文件里刚实测到该模式的漂移(上述 9 段 vs 5 段)。测试同步为新不变式。

### 验证
- 新增 test_stage_slimming_v8284(12:四段结构转正 / 旧条款已废 / 判据成文 / 前端细则已删但判据保留 / 环节化已改写法 / 物化闸与主权暂停点保留 / blueprint 矛盾已修 / ship 门禁全在)· pytest **1002 passed**。

## v8.283 · 模板减法批次一 · 砍掉限制模型能力发挥的约束(prd/tech)

> 用户课题:随着模型越来越聪明,这些规则是否反而有负向影响?讨论后确立**按规则类型分衰减速率**的判据 —— 不衰减必保留:① 证据/验证(信任架构:模型越强、主张越有说服力,越需要证明而非被相信)② 独立采样(相关盲区是统计属性非智力属性)③ 用户主权(谁决定 ≠ 谁能干)④ 纯机械操作;随模型变强而衰减可砍:⑤ 手段规定(HOW-to)⑥ 能力上限 ⑦ 教学示例 ⑧ 重复 ⑨ 环节化自检。本版按判据做 prd.md / tech.md 的减法,**门禁与暂停点一条未动**。

### prd.md 393 → 325 行(-68)
- 🔴 **砍能力封顶**(判据⑥ · 最锋利的一处):`❌ Read 5+ 个文件 / 1000+ 行`、`时间预算:5-10 min`、`不超过 10 min` —— 这是**直接给调研深度设天花板**,且与 v8.282 刚加的「在 ship 目标分支读真代码」**自相矛盾**(那个 aon-core Postback case 翻车根因恰恰是 grounding 不够深)。改为「读多深 / 怎么找 / 读几个文件由 AI 按本 feature 判断」。
- 砍 Step1-4 调研流程(判据⑤ 43 行 → 12 行):目标(把真实代码现状内化)+ 边界(只读不输出 / 不写技术细节 / code_context_read 痕迹)保留,HOW 交还模型。
- 砍三个完整 mermaid 示例(判据⑦ · 保留「什么时候必须画图」的触发判据 —— 那是判断)。
- 砍通用 checklist 的 AC 块(判据⑧ · 与 §验收标准表 + goal-complete 机器校验 100% 重复)。
- 「起草后必做自查」→「PM 自查字段(机读 · 非环节)」(判据⑨ · v8.263 已裁定「不是加自检环节,是写的时候就这样想」· 这是幸存的同类物;PRD-REVIEW 消费的机读字段保留)。
- 压缩 adversarial_self_check 的两个 worked example(规则本身属判据① 原样保留)。

### tech.md 277 → 238 行(-39)
- 砍填充示例(判据⑦):字段表 4 行(RFC 5322 等)· 跨层映射示例 · 错误处理表 4 行(压成「至少想过这几类」)· 文件树 · mermaid 时序图。
- 砍 TDD 粒度表 + ❌✅ 示例(判据⑤ · dev-stage v8.218 早把 TDD 从强制降为「强烈建议」,tech.md 没跟上)· 保留粒度原则一句。
- 完工自查去掉与机器门 100% 重复的两项(判据⑧ · test exit-code / commit changeset 已由 dev-complete 物化校验)。

### 一条未动(判据 ①②③④ 点名保留)
兜底 ROI 清单 · 现状基线 + decisive 前提核验 · 变更最小化四问的产出要求 · Schema 影响分析 · FK 决策 · 不静默吞异常 · 完工自查(review 真读它 = 产物契约非自检仪式)· 机读块 / verify-ac / AC 大白话机器校验 · 既有行为变更必入待决策项 · 「模板是地板不是天花板」。

### 验证
- 新增 test_template_slimming_v8283(12:封顶不得回归 / HOW-to 不得回归 / grounding 目标仍在 / 证据契约仍在 / 用户主权仍在 / 教学示例已清 / 核心契约仍在)· pytest 991 passed。

## v8.282 · PRD 起草思考规范补 2 条普适缺口(Postback case 归因)

> aon-core Postback 会话:PRD 两路冷审 11 findings,归因出 4 条起草考虑点缺口。按 v8.281 纪律筛(普适→补框架 · 情境/项目→进台账/KNOWLEDGE):① 在 ship 目标分支 grounding 和 ④ 兜底 miss 分支落 AC 是**普适 PRD 写作陷阱**(任何项目都会犯 · 单个锋利 case 足以过门),补进框架;② trace 运行时路径(情境)进台账观察、③ 结算下游枚举(项目特定)进 aon-core KNOWLEDGE,不动框架。

### 补入 prd.md 🧠 起草思考规范(+ goal-stage 镜像 + goal brief 同步)
- **① 依赖读真实代码 → 精确化**:「在**当前 worktree(ship 目标分支)**读,不吃跨分支/记忆的旧调研」—— 实证:PRD 基于 fix 分支旧调研写、staging 领先 233 commits → 状态码 404→422、rejected 桶去向全错(EXT-2/EXT-4)。
- **④ 兜底 line 加**:「**未命中/坏输入分支必须和命中分支一起落 AC**」—— 只写 happy path、miss 是大概率真实分支却漏进 AC = 冷审必打(EXT-2/PL-4)· 接 v8.279 兜底高发区。
- 不补:② trace 运行时(situational · 台账观察)· ③ 结算下游枚举(aon-core 项目 KNOWLEDGE)。

### 验证
- test_authoring_preventability +3(gap1 ship 分支 / gap4 miss AC / brief 双带)· pytest 979 passed。
