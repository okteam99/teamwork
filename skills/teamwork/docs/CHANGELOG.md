# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.255 · DB 变更带目的 + 变更最小化四问(治「只写内容不写为什么 · 三张新表无人质询」)

> 用户看 DB 变更确认暂停点截图(表 = 表名|类型|内容|破坏性 · 三张新表)提两点:①每项变更要给**目的**——解决什么问题、为什么要这样变更;②设计方案时要**前移质询**——是否有更简单的、直接减少数据库变更的方案。溯源:截图表格正是 templates/tech.md「变更表清单」的列结构 —— 模板天生没有「为什么」列 · 项目照模板填自然就缺;v8.242 的暂停点明细虽有「用途」列 · 但项目直接抄 TECH 表 → 用途丢失。

### 改动(模板源头 + 设计前移 + 暂停点同构)
- **templates/tech.md §变更表清单**(源头):列升级 `表名|变更类型|变更内容|解决什么问题|为何非更简方案不可|破坏性`;表前置 🔴 **变更最小化四问**(①复用既有表/列〔加约束/局部索引〕②应用层/查询时计算 ③不入库〔缓存/TTL/内存〕④并入既有表 JSONB/扩展列 —— **全否才有资格入表**);「为何非更简」列 = 写否掉的最近一个更简方案 + 否的理由(写不出 → 该变更大概率不需要)。
- **blueprint-stage.md**:§数据模型标注行加「变更最小化先问 · 设计时前移不是确认时补 · DB 变更数是简洁性 counter-lens 重点审查对象」;§7.5 暂停点明细表列与 TECH 表**同构**(对象|变更|解决什么问题|为何非更简方案不可|破坏性)—— 用户拍板直接看动机。
- **specs blueprint brief**(消费时刻):TECH 结构行 + §7.5 提醒行同步(「只写内容不写为什么也不算变更点明细」)。

### 验证
- 纯模板/文档 · pytest 903 passed。

## v8.254 · 并行姿态两问补丁:阶段演进重问 + 等待窗口不闲置

> 来源 case(WS-19-S2 dev):开工时并行判断做对了(双线 = 耦合度允许的最大并行),但进入**集成测试子阶段**时把整包塞给单 agent · 主对话自己裸等 —— 用户问「为什么只有一个 Agent 在干活」· AI 被点破后当场自查出完美拆法(两个测试任务零文件重叠 · 可独立 TEST_PG_DB_NAME 隔离 · 完全可拆)+ 主对话该填的完工自查证据行(6/8 当场落钩)· 三线并行就位。病根:v8.225/236 的「开工先问哪些可并行」只在**开工时刻**问一次 —— 耦合度随子阶段变 · 开工时的最优拆分会过期;且「等待 agent」被当成合法闲置。

### 改动(三处姿态单源/消费点)
- **SKILL 全局姿态条目**(v8.225 段):两问补丁 —— ①「哪些可并行」**每进新子阶段重问**(实现→测试编写→修复)②派发后**等待窗口主对话不闲置**(干自己能干的:自查证据 / 再拆剩余工作)。
- **dev brief**(消费时刻):🧩 段同步两问(dev 是并行红利最大 stage · 最易犯)。
- **dev-stage.md ③**:新增「并行姿态两问」段 —— 含子任务独立判据(零文件重叠 + 可独立隔离 → 满足就再派)与 case 实证。

### 验证
- 纯文本(姿态规则)· pytest 903 passed。

## v8.253 · ship 翻牌验收门:state.bl 的 ROADMAP 行必须真翻完成态(治「漏翻 → 进度误报 0/N」)

> 来源 case(WS-19):S1 早已交付合入 staging · 但 ship 时**漏翻 ROADMAP 状态格** → ws-progress 一直误报 0/4 · ready_to_start 失灵 · 直到人工查账翻旧账才发现并手工订正。病根:`--planning-artifacts` 是**自由声明**(AI 说翻了就算翻了)· 机器从没验收过「声明的翻牌真的翻了」。

### 改动
- **`_check_bl_flipped`(archive 新门)**:`state.bl`(v8.196 机读绑定)已知 → worktree 内 ROADMAP 对应 BL 行状态格必须已翻**完成态**(复用 v8.252 状态桶:已完成/已交付/已上线 · 起始词匹配防「基本已完成」假翻;复用 `_ws_scan_ok` 防 .worktree 旧副本假翻)· 未翻 → PENDING(hint:worktree 内翻状态 + 填「对应 F编号」+ 计入 --planning-artifacts 重跑)。
- **`--no-planning-changes` 不豁免**:有 BL 关联 = 必有 ROADMAP 行可翻 · 矛盾同拦(同一门顺带治)。
- **例外通道**:`--bl-flip-exception '<理由>'`(部分交付等)· 记 `state.ship.bl_flip_exception` 审计留痕 · 不静默。
- 跳过条件(不误拦):state.bl 未设(ad-hoc)/ worktree 内无该 BL 行(行在其他仓/legacy)。
- ship-stage.md §archive 步骤表补 1.5 翻牌验收门。

### 验证
- 新测试 +6(无 bl skip / 行缺 skip / 未翻拦 / 已交付别名算翻〔v8.252 复用〕/ .worktree 旧副本不算翻 / 「基本已完成」不算翻)· pytest **903 passed**。

## v8.252 · ws-progress 健壮性两修:状态词表漂移 + .worktree 扫描污染

> 两个实战 bug(并行 session 修 · 本版一并发):
> **① 状态词表漂移**:项目 ROADMAP 混用「✅ 已交付」「已上线」被判「待开始」→ 进度假 0/N + `ready_to_start` 失灵(该起的 feature 起不来)。且词表外写法被静默吞,漂移无人发现。
> **② `.worktree` 未排除**:ws-progress/ws-lint 全仓 rglob 扫到并行 feature worktree 内的**旧基线副本** → 「算旧写旧」+ 把进度自动块**写进别人的 worktree**(工具污染他人工作区 · verdict 却 OK)。

### 改动
- **状态桶归一**(`_ws_status_bucket`):完成态收别名 `已完成/已交付/已上线`;剥前导 emoji 后按**起始词**匹配(防「基本已完成，待测试」子串误判完成);词表外 → 归「待开始」+ **标不可识别**(不静默吞)。
- **unrecognized 警告 surface**:`_render_ws_progress` 返回 `(block, unrecognized)`,总览顶部 emit `⚠️ 状态词不在词表(按待开始计 · 词表见 roadmap.md)` —— 漂移当场可见。
- **扫描排除单源**(`_ws_scan_ok` + `_WS_SCAN_SKIP`):显式目录名 + **任何隐藏目录段**(`.worktree` 及自定义 worktree 根都兜住)· WS/ROADMAP rglob 全走它。
- **正本判定 + 多候选 surface**(`_find_ws_file` 返回最优候选 + 全部候选):排序 product-overview 优先 → 段数少 → 字典序;多候选时列清单(治 rglob 无序取首把进度写错副本)。
- roadmap.md 模板状态词表同步(别名 + 起始位置规则 + unrecognized_status 警告说明)。

### 验证
- 新测试 `test_ws_scan_vocab.py`(worktree 污染 / scan_ok 排除 / find_ws_file 正本+候选 / 别名计完成 / 子串不误判 / bucket 单测)+ test_ws_progress_v8174 更新 · pytest 897 passed。

## v8.251 · release-gated 裁决:拆开「代码门」vs「发版门」(治 review 磨不可闭合的 BLOCKER)

> 来源 case(aon-core Canonical-Offer):review 卡在物理上不可能本地关闭的 BLOCKER 上反复磨轮(round 4→5),用户被迫手动介入 4 次才把「真需发版」的 F-002 和「本地可 mock」的 F-004 拆开。病根:review 收敛协议把两种完全不同的「未闭合」混为一谈——代码缺陷 vs 发版证据。**review 只该 gate 代码完整性(本地/CI 能修的);发版证据(soak/rollout/prod-smoke)是独立发版门,不卡 APPROVE 但必须追踪到发版。**

### 改动(判据 + schema + carry-forward · 全做)
- **① release-gated 裁决**(review-stage.md 硬规则 3.5):证据物理上必须 post-deploy 的 BLOCKER/MAJOR → `status: deferred` + `deferred_reason: "release-gated · 欠<证据>"`,别磨轮,它是发版义务不是 review 阻塞。
- **② 双向护栏**(把 case 的分界线写成判据):**只有真部署/真墙钟/真生产平台能产的才算 release-gated**(真实 rollout/rollback · 24h/72h/7d soak · 不可 mock 的生产平台);**能 mock/fake/注入时钟复现的不算**(F-004 的 WireMock、soak 注入 clock 缩时)= 本地必须做完才 APPROVE,不许借 defer 逃。物化护栏:`deferred` 的 BLOCKER/MAJOR **必须写 deferred_reason**(空 defer → complete FAIL · 防扫地毯下 · hint 直接教 WireMock 反例)。
- **③ carry-forward**(release_gated_deferrals 抽取器):`deferred(release-gated)` 带结构化「欠什么证据」→ **pm_acceptance brief** 列「🚚 发版后待补证据 N 项」(用户验收知情)+ **ship1 user_card** 列同款(合并前看到)· 真追踪不消失。
- schema:findings 加 `deferred_reason` 字段(parse_review_findings 保留)。

### 效果
case 能自主收敛:F-002 识别 release-gated → deferred + 记义务(carry 到 pm/ship);F-004 识别本地可 mock → 空 defer 被物化门拦 → AI 自己写 WireMock → APPROVE。**零用户往返。**

### 验证
- 新测试 +7(空 defer 拦 · MINOR 不强制 · release-gated 放行 · open 仍拦 · 抽取剥前缀 · pm brief 含/不含)· 旧断言 1 处(findings +deferred_reason)· pytest 897 passed。
