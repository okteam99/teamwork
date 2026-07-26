# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.297 · 耗时归因与流程反思搬出台账 · 落独立流程复盘文档

> 用户:**耗时归因和阶段流程反思不该写到 PROCESS-LEDGER,因为写不下 —— 应该单独一个文档放到项目的复盘目录下,台账做引用。**

判断成立。台账**一行一 feature、单元格 ≤1 行**,而「这 318 分钟花在哪」恰恰是最值钱的那段;
v8.295 把归因塞进单元格是错的档位 —— 压缩掉的正是它的全部价值。

### 新增:`templates/process-retro.md` → `{子项目}/docs/retros/<feature-id>-process.md`

四段:**各阶段耗时表**(机器数据照抄 `ledger_timing.per_stage`)· **逐 stage 耗时归因**(本文件核心)·
**流程反思四问** · **起草可预防性**。写入时机 = ship1 archive 规划 gate(与台账行同时 · worktree 内)·
🔴 **路径加进 `--planning-artifacts` 随 feature MR 原子合入**(不进 git = 白写)。

划清了与同目录**业务复盘** `docs/retros/<feature-id>.md` 的边界:后者复盘需求演进与技术选型(知识层),
**本文件只复盘 teamwork 流程本身** —— 时间花在哪、哪个环节没产生价值。

给了「什么算协调开销」的**可判定判据**:**「这一轮产生了新的设计判断或新的实现吗?」** 没有 = 协调开销。
不给判据则每人一把尺,跨 feature 数据不可比。

### 顺带:原本「只 emit 不落盘」的 digest 四问,终于有家了

ship-stage §16 的 digest 明写「不落 feature 目录」—— **说完就蒸发**,年检什么也读不到。
现在四问同时写进复盘文档 §三,emit 只作当场回显。

### 台账列收窄为「可算比值 + 指针」

`⏱️ 耗时归因` 从 `协调开销 2/9 轮 · blueprint:<一长串归因> · 类型:…` 收成 **`2/9 轮 · 详 <复盘路径>`**。
两头都保住:年检**查表即得**占比趋势(不必逐个开文档),要细节再顺指针展开。
🔴 未动 schema 结构(只改列语义与表头文案)—— 删列/插列会让旧行错位。

### 这一版的门禁是上一版刚立的

v8.296 收尾时我补了一条**反向锁**:「`_v8_ship.py` 里新增 `ledger_*` emit 字段 → 必须同步进台账指令」。
本版新增 `ledger_process_retro_path` 时**当场被它拦下** —— 接完 ship-stage §16 才放行。
立门禁的那一轮就用上了,算是它自己的第一个实证。

### 测试

998 → **1005**。

---

## v8.296 · `docs/audit/` 整条退役 —— 数据追踪不了 · 后续以 retro 为准

> 用户:**docs/audit/ 这个逻辑可以去掉了,数据没办法追踪,后续以 retro 为准。**

### 为什么它追踪不了

运行时文件落 **`~/.teamwork/audit/`(机器本地 · git 不跟踪)** —— 跨机器 / 跨人**根本聚不起来**,
而它的 telos 恰恰是「框架层面**跨项目**搜集流程质量」。代码里也早就自陈「**审计只写不读**」
(`_v8_ship.py`)。框架仓 `docs/audit/` 目录里 22 个文件中**只有 README 进过 git**,
其余 21 个是 gitignore 的残留。

**它原本要办的事,已经被两处覆盖**(且两处都真的在 git 里):
- `project-specs/PROCESS-LEDGER.md` —— 一行一 feature · 机器字段 · **随 feature MR 原子合入** · 可查表算账
- `docs/RETRO-LEDGER.md` —— 框架侧一行一版 · 永久 · 年检直接读

### 删了什么

| 位置 | 内容 |
|---|---|
| `_v8_ship.py` | `_write_audit_record`(86 行)+ `_capture_audit_sources`(27)+ `_audit_dir`(11)+ 调用点与 emit |
| `_v8_ship.py` | 🔴 **`--main-model` 死参数** —— 唯一消费者就是 audit record,help 还写着「写入 audit」= 在说谎 |
| `docs/audit/` | 整个目录(README + 21 个 gitignore 残留)· `.gitignore` 对应规则 |
| `update.py` | 对账豁免前缀收窄为 `("docs/retro/",)` |
| `ship-stage.md` | 「三处落点」→「两处落点」· ship2 的审计回收段删掉 |
| 测试 | `test_audit_sources_v8207.py` 整文件 + `test_ship_v8145_flow` 两例 + 残留 `TEAMWORK_AUDIT_DIR` env |

**保留**(同名不同物,别误伤):`_prepare_audit_path`(prepare-check 的 jsonl)是**活门禁** ——
主工作区 prepare → worktree init-feature 靠它对通,有真读者。

### 退役时发现的覆盖缺口(顺手补上)

`test_pause_mark_v8192` 里两个用例断言的是 audit 草稿渲染(user_email / AI-wait 三分 / host frontmatter),
删之前查了一下:这批数据的**活消费者** `ledger_timing`(→ PROCESS-LEDGER 四列)**零测试覆盖** ——
唯一的端到端保障挂在将死的那条线上。故不是删,是**改断言活路径**,并补一条「退役 audit 不能顺手砍掉台账数据源」。

> 教训进 RETRO:**退役一条链路前,先看它是不是别人唯一的测试宿主。**

### 反馈往哪走(替代口径)

框架级 bug / 工具判例 → 写进 PROCESS-LEDGER 行的「反思摘要」列(随 MR 进 git · 年检查得到);
真值得改框架的 → 开 issue 或在框架仓落 RETRO-LEDGER 行。**别再指望本机的审计文件被谁读到。**

### 测试

1001 → **996**(净减 5:删掉 7 条测已删机制的,补回 2 条测活路径的)。

---

## v8.295 · stage 耗时归因采集(补上「有数字没归因」那一环)

> 用户:**是否需要增加一个耗时复盘机制,每个阶段结束后总结耗时复盘,记录到固定文件夹 · 放到项目里进 git。**

### 结论:需要,但**不新建文件夹** —— 缺的是归因,不是载体

先盘已有的三层:`state.json.stage_contracts[stage]`(机器采 duration / await / **active_minutes** v8.276)
→ `project-specs/PROCESS-LEDGER.md`(一行一 feature · **已有「各阶段耗时」列** · 在项目里、进 git、
随 feature MR 原子合入)→ `docs/retros/`(业务/工程复盘)。

**缺的正是归因**:现有列只有**数字**(`blueprint 318m`),不回答「这 318 分钟花在哪」——
而 SVC-PLATFORM-F260726 复盘最值钱的恰恰是归因:blueprint 6 波往返里**波 5、6 是纯文档对齐、无设计价值**,
双档同步吃掉 ~35% 轮次 / ~25% token。

**不新建文件夹**:`docs/audit/` 是前车之鉴 —— 累了 22 个文件,代码自陈「**审计只写不读**」。
写了没人读的产物是纯成本。

**时机上用户是对的**:这类归因**只有 stage 结束时当场记得住**;ship 时回填要靠产物 mtime 反推
(那正是这次复盘干的苦活)。

### 机制(复用 v8.281 已跑通的形状:收敛后记录 → ship 聚合 → 年检分析)

```
state.py stage-cost --feature <path> --stage <goal|ui_design|blueprint|dev|review|test|browser_e2e> \
    --rounds <总轮次> --overhead-rounds <其中纯协调开销> \
    --kinds '双档同步;门禁重试' --note '最大的一笔开销是什么'
```

- 存 `state.json.stage_cost[]` → ship1 archive emit `ledger_stage_cost` → PROCESS-LEDGER **末尾新列**
  「⏱️ 耗时归因(协调开销轮/总轮·最大一笔)」(🔴 schema 演进纪律:只在末尾加列)
- **非门禁 · 纯采集**(不记不拦 ship · 台账列留空 = 有效前缀)· 零开销也要记(`--overhead-rounds 0`)——
  「这次没开销」和「没记录」是两回事,年检要分得开
- 物化护栏:`--overhead-rounds > --rounds` → FAIL

**提示放在 complete emit,不写进各 stage 文档** —— 机器在**正确的时刻**提醒(带本 stage 实际耗时 +
可直接跑的命令 + 「趁现在记」的时效说明),不靠文档记忆。且**只在有多轮往返成本的 7 个 stage 提**
(ship / pm_acceptance / panorama_sync / diagnose / execute 不提)。

### 🔴 为什么这不是又一道「环节化自检」

v8.283 的规则衰减分类学把「环节化自检」判为**会衰减、可砍**的那类。这条不同:
- 它**不让 AI 自查做得好不好** —— 采的是 **AI 自己算不出、事后也复原不了的事实**
- 它是**验证提效改动是否起效的唯一手段**:v8.294 的收敛期归一 / TC 职责边界 / 投机窗准入
  **都声称能砍这块协调开销**,没有这列数据就无法证伪

### 顺带修好一处既有不一致

新加的 schema 门禁(表头 / 分隔行 / 示例行列数必须一致)当场抓到:**v8.281 加「🛡️ 起草可预防性」列时
没补示例行的对应格** —— 示例行比表头少一格已经存在一版。已补齐。

### 测试

988 → **1001**。

---

## v8.294 · 复盘驱动:localconfig 在 worktree 里读不到(真 bug)· rival 设计强制 · TC 职责边界

> 来源:matrixpower SVC-PLATFORM-F260726(三级算力体系 + 锚定链定价 · 计费热路径 + 破坏性迁移)
> 的评审耗时复盘。逐条对着现行代码核过 —— 其中 R4(external 门禁词汇表)**已由 v8.291+293 修掉**
> (case 跑的是 v8.287.1),R5 是反面确认(5 条 high 全实锤 · 不因耗时降档)。

### 一、🔴 R3 是真 bug,且比复盘诊断的宽 5 倍

复盘报「fast_mode 静默失效,疑似 init-feature 快照链路问题」。实际根因更深:

`.teamwork_localconfig.json` 是**本地配置、不入 git**(bootstrap 自动 gitignore),因此**只存在于主工作树**。
而**五份独立实现**都是「从 feature_dir 向上找 · 遇 `.git` 停」—— linked worktree 的根有 `.git`
(**文件**形式)却没有配置 → 全部静默回退默认值。**teamwork 默认 `worktree: auto`**,
等于这五项配置在真实 feature 上**从来没生效过**:

| 读取者 | 配置项 | 起于 |
|---|---|---|
| `state.py _read_fast_mode` | `fast_mode` | v8.260 |
| `state.py _read_id_strategy` | `id_strategy` | v8.79 |
| `_v8_engine._idle_threshold_minutes` | `idle_threshold_minutes` | v8.276 |
| `_v8_engine._localconfig_max_review_rounds` | `max_review_rounds` | — |
| `_v8_ship._read_archive_on_ship` | `archive_on_ship` | v8.82 |

讽刺的是 `state.py` 里另有一段**正确**实现(`git worktree list --porcelain` 取主树再读 config)——
代码自己知道该怎么做,那五处没用它。**不是漂移,是五份副本生下来就都是错的。**

**修**:抽 `_v8_engine.load_localconfig()` 唯一解析器 —— 遇 `.git` **目录**才停(主仓根),
遇 `.git` **文件**(linked worktree)就解析 gitdir **跳到主工作树继续找**。纯文本解析不起 subprocess
(git 卡了不该让配置读取跟着不可用)。五处调用点全换,并加门禁锁「只准剩一份实现」。

**可见性**(复盘第二诉求 —— 静默回退是双输:用户既没拿到速度、也不知道为什么慢):
init-feature kickoff 回显三态且各自说明来源 —— `on(来源 localconfig)` /
`off(localconfig 为 true 但被 yolo 覆盖)` / `off(localconfig 未开)`。

### 二、rival 设计强制(复盘 §二 · 本轮最高价值的沉淀)

复盘问「为什么没先想到把标记打在 accounts 上」——「内部运营账户」被设计成 singleton 指针表 +
独立审计表(2 张新表),用户一句话 → 6 新表变 4 新表 + 2 列。

它自己诊断到了根因:**简洁性 checklist 是验证式的**(作者给的理由成立吗),四问确实跑了,
但**参照物由作者的叙事给定**(「能否并入 `monetization_config`」—— 一个冻结面,当然不能),
**没人问「这个设定的自然归属实体是谁」**。盲区只有**生成式**才破。

落 Architect 简洁性 lens + **blueprint 运行时 brief**(只改 stage doc 到不了 AI):
评审**新增结构**(新表/新模块/新抽象/新服务)必须**自己先生成 ≥1 个替代形态**
(并入宿主实体加列 / 现算不存 / 复用既有 / 根本不做)再裁决 ——
🔴 **「赢了作者列举的被否方案」不构成通过条件**。附:「全局唯一 / singleton 语义」**不等于**需要单独一张表。

### 三、TC 的职责边界(治 R1 的一半)· 不合并 TC/TECH

复盘算出双文档同步吃掉 blueprint **~35% 轮次 / ~25% token**,提议合并两文档。核过之后不合并 ——
拆开看同步的**内容**:表数 27→33→31、错误码命名回填、过期注、存储改选连锁,而
**TC 模板里根本没有表数/表清单/存储断言这些槽位**,是起草时自己加进去的。
即:**一半是 TC 越界**(划界直接**消除**),一半是真耦合(合并只是把跨 agent 往返变成同 agent 内往返)。
合并会让越界变得「合法」,把消除降级成缓解;而 `verify-ac.py` 这道 AC→测试的唯一机器门锚在
TC frontmatter,合并要重做 schema。

**新增 `templates/tc.md § TC 的职责边界`**(格式单源 · blueprint ④ / qa.md / rd.md 指过来):
- **telos**:把每条 AC 变成可执行、可判定的验收判据 —— 回答「怎么证明它满足了」,不回答「怎么做出来」
- 🔴 **一句话判据:换实现就要改的内容,不属于 TC** —— 假设 TECH 换实现方式,这条用例还成立吗?
  还成立 = 验行为归 TC;要跟着改 = 持实现形态归 TECH
- **关注**:AC↔用例绑定 / 可观测行为 / **边界与异常路径**(QA 核心价值)/ 测试层级与优先级
- **不关注**:表结构与表数 / 模块划分与选型 / 存储形态 / 性能实现手段(但性能**指标**若是 AC 则必须验)
- 🔴 **契约值的分寸**:断言到的错误码/状态码/字段名**必须写具体**(不具体就不叫断言);
  但**维护一份清单**(全部错误码、新表数量)= 复述 TECH,必删。**TC 从不需要知道有几张表。**

### 四、角色的两种用法(ROLES.md 新增判据)· 治 R1 的另一半

**同一个词在起草期和评审期不是一回事**:

| | 起草期 | 评审期 |
|---|---|---|
| 角色是 | **分工标签**(同一个 AI 切帽子) | **独立采样点**(不同上下文 / 不同模型) |
| 能否合并 | 🟢 能 —— 省跨 agent 冷启动往返 | 🔴 不能 —— 多视角退化成「一个视角 × N 份」 |
| 依据 | 产物有机器门兜底(verify-ac / build / 测试硬门) | v8.155 实证:in-context architect 在 goal 只产鼓掌 · 被冷审的 external/PL 反超 |

落地:blueprint/dev 的 **RD 与 QA 起草期合一**;blueprint ③ 改为
**「起草期并行 · 收敛期归一」** —— 复核后的修订由**同一 agent 顺序改两档**,
纯机械同步项**主编排直接 Edit 不派 agent**。评审席位照 roster 隔离冷审,不受影响。

### 五、R2 投机窗准入

投机窗原有**时点**纪律(只在终确认后)但无**开放决策数**条件。补:
§待决策项里**影响表结构/模块形态**的开放项 **≤1** 才投机;>1 或含结构分叉 → 等终确认再起草。
why:「终确认改:默 ≈ 全默」的统计前提**只在单决策上成立** —— 多个结构性开放项时草稿必须押某一组合,
用户改选任意一项都触发差量重写(实证:两项结构性改选 → 一整轮重写 · 该轮 token ~1.3× 初稿 = **投机变净亏**)。

### 测试

970 → **988**。

---

## v8.293 · 全库冗余清理:死岛 · 退役残留 · 敏捷需求 legacy 整条删除(净 −1600 行)

> 用户:**逐个文件整体 review 下,看下哪些冗余需要清理或者删掉。**
> 判据三条:**还有没有消费者** / **是否与现行规则矛盾** / **同一教义是否写了多遍**。

### 一、死岛 —— v8.291 只砍了入口,没砍被调链(−680 行)

| 位置 | 内容 |
|---|---|
| `state.py` | `_run_codex_review` / `_run_claude_review` / `_build_codex_prompt` / `_run_streamed_to_log` / `_build_claude_review_cmd` / `_detect_host` + `EXTERNAL_HOST_TO_MODEL` / `REVIEW-ACK` 协议 / `_prompt_doc_stale_reason`(`--prompt-doc` 参数早已删)/ `_FINDING_POSTURE_HINT` —— **586 行** |
| `state.py` | `scaffold-review-prompt` **整命令**(零文档引用 · 用途已被 external-review 自写 prompt-doc 取代) |
| `_v8_stage_specs.py` | `_check_external_hetero` + 4 个专属常量 —— **63 行** |

🔴 其中一颗雷:`EXTERNAL_REVIEW_SAME_CONTEXT_BLOCKED` 把 `"subagent"` 列为**必 BLOCK** 的同源字面 —— 而 v8.291 后 subagent 恰是**唯一合法形态**。谁把这 checker 重新接上,拦的就是唯一支持的路径。

`EXTERNAL_STAGE_TO_PROFILE` 三层嵌套 dict 折叠为两个常量:`codex-agents/` 已删,三个 stage 的 claude profile 本就全是同一个 `reviewer.md`。

### 二、退役声明贴在头上、正文一字未改(3 处)

- 🔴 **`review-stage.md` 硬规则 1** 仍要求「各自落 `REVIEW-{role}.md`」,而同一份白名单的**规则 8** 写着「v8.289 已取代该文件」—— **两条硬规则直接打架,漏在最高权重位置**。顺带修:编号出现两个 8。
- `roles/external-reviewer.md` 头部有 v8.291 退役声明,正文四条照旧写着「claude 主时调 codex」「OpenAI ToS 合规」「文件名必含 codex/gemini 字面」→ 整篇重写。
- `disable_external_review` 仍是 `teamwork_localconfig.json` 的活配置 + `config.md` 一整节 —— 能活一版是因为 v8.291 的退役扫描测试 **glob 只扫 `*.md`/`*.py`,漏了 `.json`**(已补)。

### 三、「敏捷需求」/ `lite` / `blueprint_lite` 整条 legacy 删除(−400 行)

删的理由**不是「没人用」**,是 audit 查出 **三份 flow-key 实现对同一输入解析出不同的转移图**:
`state.py` → `Feature+full`(无 blueprint_lite 的图)· `_v8_engine.py` → `Feature+lite`(含 blueprint_lite),
**而 engine 的注释还声称与 state.py「严格同口径」**。三份实现无一被测到该输入。

用户拍板:不选边,整条删。lite 档 v8.223 已退役,其链本就是 Feature 链的 `needs-ui=false` 剖面(纯冗余)。
删:`AGILE_FLOW` / `FLOW_BY_TYPE["Feature:lite"]` / `BLUEPRINT_LITE_SPEC` / `DEFAULT_REVIEW_ROLES` 5 条 / `STAGE_CHAIN_PREVIEW` 一支 / `stages/blueprint-lite-stage.md`。**stage 数 13 → 12**。
新增门禁:三份实现对同一 state 必须给出一致的内部键与转移图。

### 四、孤儿模板(用户逐个拍板)

- **`templates/architecture.md` 351 → 192 行**:产物 `{子项目}/docs/architecture/ARCHITECTURE.md` 是活的(SKILL 路由 + engine 读 + ship 门),模板却零消费者 —— 是**路由缺口**不是死文件。补 SKILL/architect 指针;**藏在里面的 68 行迁移起号纪律上提到 `standards/backend.md §五`**(那里才是权威);删 86 行 api-design/deployment 示例子模板;去掉「超 50 行必拆」的能力上限规则。
- **`templates/e2e-registry.md` 241 行整个退役**:全库零入口 —— 没有任何文档说 REG case 长什么样 / 放哪 / 怎么建,却只有 ship distill 在要求逐项申报。连 `DISTILL_KEYS` 的 `reg` 槽位一起删(6 项 → 5 项)。

### 五、模板层去重与矛盾(−330 行)

- 🔴 **`ui.md` 段落契约矛盾**(真 bug):模板明令「视觉描述一律归 HTML 预览产物 · **不在本文复述**」,而 `ui-design-stage.md` / `roles/designer.md` 要求 body 必含 §页面列表/§交互流/§视觉规范/§字段映射 —— **模板里没有这四段**。Designer 照哪边写都违反另一边。按「templates/ = 格式唯一真相源」改 stage 与 role。
- **`config.md` §localconfig −116 行**:是 JSON 模板 `_comment_*` 的逐字第二副本,且用 ` ```markdown ` 围栏把它描述成带 `## 负责人` 标题的 **markdown 文件**(真实文件是 JSON)—— 副本必漂,这次漂到了介质。改指针;第三份(`bootstrap.py` 的 DEFAULT dict,原靠一句「🔴 两处都加」的自觉)换成**物化对齐门**。
- 三份「起草要点」段自陈「v8.199 cite 仪式已废」却仍在逐条复述对应 stage 的硬规则 → 整删。
- `tc.md`:三个孤儿段(标「代码审查时填写」但 review 的产物契约是 REVIEW.md · 从不读)+ Gherkin 语法速查(HARD-RULES 判据:模型默认就会的一律不收)+ 一个 `standards` 里根本不存在的「后端覆盖率 > 80%」阈值。
- `adr-index.md` 66 行里「PMO 读本索引」写了 4 遍;`knowledge.md` 300 行上限与文档边界表各写两遍;`pm-note.md §3` 是 pm-acceptance-stage 暂停点脚本的逐字副本(PM-NOTE 是**已决策后的记录**)。
- ADR 落点权威分裂(`SKILL.md` 指 Feature 目录 vs `adr.md`/`architect.md` 定「`{子项目}/docs/adr/` 唯一落点」)—— 同 v8.205 sitemap case 复发,已归一。
- `preflight` 旧机制名 → `triage`(5 处);`tech.md` 实现步骤表的 TDD 红绿词表(与同节「节奏 AI 自定」自相矛盾)。

### 测试

962 → **970**(+8 类:死物不复活 / 退役声明与正文一致 / § 引用可解析 / 三份 flow-key 一致 / localconfig 单源 / ui 契约 / **markdown 围栏平衡**)。
最后一条是自伤实证:按 `## 标题` 切段时切掉了 `adr-index.md` 的围栏闭合 —— 切文档一律回来验围栏。

---
