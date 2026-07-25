# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.281 · 起草可预防性台账列 · 评审后记录 → ship 聚合 → 年检完善 teamwork

> 用户:每次评审后记录「为什么审出这么多 + 起草考虑点该不该补」,同步到台账供后续分析完善 teamwork。这是 v8.278 dev shift-left 的诊断层 —— 把「起草考虑点缺不缺」从猜变成数据。活体验证(aon-core Postback 会话):PRD 两路冷审 11 findings,该 session 手动归因出 4 条起草考虑点缺口(在旧分支 grounding / 未 trace 真实运行时路径 / 结算路径下游未枚举 / 兜底 miss 分支未落 AC)—— 正是本列要系统化采集的。

### 机制(非门禁 · 纯数据采集)
- 新命令 `state.py review-preventability --stage <goal|blueprint|review> --preventable N --total M --missing '缺的考虑点(分号分隔)'`:评审收敛后记录 findings 可预防率 + 缺哪条起草考虑点 → 追加 `state.authoring_preventability`。
- ship 聚合 `_authoring_preventability_summary`(跨评审求和 + 缺项去重)→ emit `ledger_authoring_preventability` → PROCESS-LEDGER 新列「🛡️ 起草可预防性(可预防/总·缺考虑点)」(rightmost · append-only schema · ledger-migrate 自动加列)。
- review harvest(v8.278 rule 8)+ 验证轮 brief + ship §16 台账口径接线;判据同 v8.278/279(findings 82% 真·砍轮=漏 bug·真杠杆=起草挡掉可预防子集)。
- **消费方 = 年检**:跨 feature 看「缺的考虑点」复发 → 补 PRD/TECH 起草考虑点(反复缺=真缺口补框架)· 全 emergent = 别动(避 v8.266 一刀切)。没记录列留空(有效前缀 · 非门禁)。

### 验证
- 新增 test_authoring_preventability_v8281(6:聚合去重/记录追加/非门禁/表头分隔一致)· pytest 976 passed。

## v8.280 · 修 micro 状态机 preset-blind 死门(execute 链走不通)

> 实证 case(aifriends 4 行合规 bump 走 micro):init-feature preset=micro 建出 `flow_type="Feature" + preset="micro" + current_stage="execute"`,但 **execute-start 直接 FAIL** —— 用户被迫手动跳过状态机做完 micro 实质。根因:engine 通用 gate **用 raw `state.flow_type="Feature"`** 比 `EXECUTE_SPEC.allowed_flow_types=["Micro"]`(legacy 内部键)→ 恒 FAIL;且图查 `flow_by_type.get("Feature")` 拿 **full 图**(即便过①·execute→ship 转移错路由)。`resolve_flow_graph`/`internal_flow_key` 在 state.py 有,但 engine 的 `execute_stage_start/complete` 从没用 —— 现有 micro 测试只断言 spec 常量、**从没真跑 gate** → 漏网整整一版。

### 修复(engine gate preset-aware)
- 新增 `_internal_flow_key(state)` + `_resolve_flow_graph(state, flow_by_type)`(与 state.py resolve_flow_graph/internal_flow_key、specs _flow_key 严格同口径 · engine 不能 import state.py〔循环〕故本地实现)。
- `execute_stage_start` 三处:① allowed_flow_types 门用 `_internal_flow_key`(Feature·micro → "Micro" 匹配)· ② 转移图用 `_resolve_flow_graph`(micro 拿 Micro 图非 full)· 未知 flow_type/preset 仍显式 FAIL(保「已知流程表」措辞)。
- `execute_stage_complete` 转移同修(execute→ship 正确路由)。
- 正常 Feature·full / Bug 行为不变(`_internal_flow_key` 对它们恒等映射)。

### 测试补口
- 新增 test_micro_gate_v8280(6:resolver 单测 micro/full/bug/legacy + `_resolve_flow_graph` micro 拿对图 + **真跑 init micro → execute-start 过门** e2e)—— 补上「只断言常量、从没跑 gate」的集成盲区。
- pytest 970 passed。
