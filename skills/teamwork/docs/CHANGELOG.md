# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.366 · 读取分层 · 文档单一权威 · 评审不凑数(提效方案第 3 批)

> 起因:开工前要读的规则太多(prepare 前要先读三份规范);同一份测试设计在 TECH 与 TC 各写一遍;冷审「没发现」也必须写理由,单字「无」过不了门。

- **读取分层**:SKILL 新增「读取分层」表 —— 入口(每次)/ 当前阶段(进阶段时读 brief 点名的 stage doc)/ 参考(出问题时查)· 不需要读完整套流程才开工。
- **prepare 按需读**:§0 由「动手前必读三份」改为「最小路径 + 按需读」(conventions 仅偏离默认路径时读 · feature-planning §0 仅命中 §2.1 时读 · 反模式 / 错误处理 / 红线作参考)。
- **测试设计单一权威**:TECH §测试清单 不再复制 TC 用例表 · full 档权威 = TC.md · medium/lite 绑定在 PRD `test_refs`。
- **评审不凑数**:⚔️ 对抗 / 💡 清单外洞察「没有就写『无』」· 不再要求「无 + 理由」;💡 门禁接受显式「无」(占位符与留白仍拒)。SKILL 新增「评审先核验关键前提」。评审路数与模型错开**不变**(按方案:有对照数据前不放宽)。
- 测试口径同步:`test_derole_wiring_v8356` / `test_derole_unified_review_v8355` 原先锁定旧规则(单字「无」必拒 / 必须带理由),按本批决定改写。
- 验证:新增 `test_slim_reading_v8366.py` 6 例 · 全量通过。

## v8.365 · Bug 按风险分三档 · 复现证据机器核对(提效方案第 2 批)

> 起因:Bug 不论大小都固定走 diagnose → dev → review → test → pm_acceptance → ship,且 diagnose 必停等用户确认 —— 根因已经验证过的局部修复也要补一份完整 BUG 报告、再确认一次。

- **Bug 接入装配计划 · 只开三档**:`floor`(dev → ship)· `tiny`(dev → review〔external 单路〕→ ship)· `full`(原 diagnose 链 · 不变)。轻档链由 assembly_plan 推导(与 Feature 同一套 `derive_chain` · 不另立 Bug 专用图);其余 preset / `--dims` 对 Bug 拒绝。
- **轻档准入 = 机器证据**:新增 `state.py repro-record --cmd`(改代码前跑 · 命令必须失败才记录红);dev-complete 新增证据门 `bug_repro_red_then_green` —— 无红记录 / 红之后没有新 commit / 重跑仍失败 → 拒绝。不靠 agent 自述「根因已验证」。
- **升级**:新增 `state.py bug-escalate --evidence` —— 轻档 → full · 回 diagnose · repro / 阶段合同 / concerns 保留 · 原计划进 `plan_history`。
- **diagnose 确认改为按决策停**:修复改变预期行为 / 公开契约 / 有取舍 → 照旧停;只是恢复本该有的行为 → 写进 BUG 报告并告知 · 不停。
- 接线:引擎 `_resolve_flow_graph` / stage-start 链校验 / `reset-prev` / `jump-to-stage` 对 Bug 计划同口径推导;dev 准入对 Bug 轻档走计划判据;`prepare-check --flow-type Bug --preset floor|tiny` 预览对应链;ship 准入沿用「pm_acceptance 不在链上 → 验收在 ship1 MR」。
- 文档:prepare §2.3 Bug 定档 · FLOWS 三行 · dev-stage 复现证据节 · diagnose-stage 规则 5。
- 验证:新增 `test_bug_tiers_v8365.py` 12 例(真实临时 Git 仓库跑 init → dev-start → repro-record → 修复 commit → dev-complete → ship-start;升级回 diagnose;三档预览)· 全量通过。

## v8.364 · 清规则冲突 + 确认围绕决策(提效方案第 1 批)

> 起因:Teamwork 提效方案 —— 明确的任务被规则冲突与重复确认拖慢。本批只动「要不要停」与规则文字,不动流程链。

- **暂停必须写明要定的决定**:`pause-mark --decision` 必填,空 → 拒绝(说不出用户的回答会定下什么 = 不该停)· decision 随 `pause_log` 留痕。SKILL R5(b) 加确认默认行为表(已授权修复直接推进 / 有配置自动用 / 冲突与产品取舍才问)。
- **prepare 免停条件**(prepare §4.0):明确指令 + 无补的意图假设 + 4 项配置全取默认 / localconfig + 无异常 + 未触发 §2.1/§2.2 → 卡片照出、不停、直接执行。R-P1 / R-P2 同步。
- **缺产品规划不再拦执行任务**:cold-start gate 对 mode B 明确的 Feature/Bug 只提一句、不停;bare `/teamwork` / mode D / 规划类任务照旧停。
- **micro 准入失败不再一律 full**:按「超 micro 白名单怎么定档」在 floor / tiny / full 里选(原 §2.2 首句与定档段自相矛盾)。
- **起手档清单统一**:prepare 闭集写全 6 档;`prepare-check --preset` 接受全部档(原只认 full/tiny/micro,定 floor 时预览退回全链)。
- **定档单源按时刻划分**:prepare 起手 = prepare §2 · goal 调研后装配 = goal-stage 3.7 · FLOWS.md 只是视图(原 SKILL 同一处列了三个「权威」)。
- **floor 入场问句去绝对化**:「测试能完全证明它对」→「测试覆盖本次行为变化和已识别的关键风险」。
- 验证:新增 `test_decision_pause_v8364.py` 11 例(含真跑 pause-mark / prepare-check floor 预览)· 全量通过。

## v8.363 · 计时口径 v2:先把统计做对,再改流程(提效方案第 0 批)

> 起因:Teamwork 提效方案评审 —— 要验证「明确任务少走手续」是否真提效,得先有可比基线;而现有统计有三处失真,流程改动与口径修正同批上会让效果无法归因。本版**只改统计,流程规则一律不动**。

- **总时长起点**:`_feature_duration_h` 原来只从最早 stage 起算,漏掉 bootstrap/分诊/prepare。v2 起点取 `prepare_check_at`(init-feature 从 prepare-check audit 记录取)/ `created_at` 中最早者。
- **启动准备耗时单列**:`ledger_timing.startup_min` = 可观测起点 → 首个 stage 开始(prepare-check 之前不可观测 · 是下界)。
- **pm_acceptance 不再整段算等待**:v8.361 起 AC 全过不停,原口径把验收工作算成「等用户」;v2 下按普通 stage 计,真停时 pause-mark 打点进 `await_minutes`。
- **暂停次数机器计数**:`close_open_pause` 每次闭合落一条 `pause_log`(stage/label/minutes)· `ledger_timing.pause_count`。
- **新旧不混比**:init-feature 写 `timing_basis: "v2"`;存量 state 无此字段 → 全部按旧口径算(结果不变)· 台账「时长」格 v2 行追加 `·启 Nm·停 N` 段即口径标记 · `ledger_timing.timing_basis` 显式标注。
- 未做(留待后续批次按需补):首次有效产出时间、合并后 14 天遗漏缺陷追踪、未归档任务统计。
- 验证:新增 `test_timing_basis_v8363.py` 14 例(含真跑 prepare-check → init-feature)· 全量通过。

## v8.362 · 归档后 MR 修复通道 + CI 归因修正(实证 GPT-F261014120919-Offer-Plugin)

> 起因:ship1 归档后 MR CI 红,修一行 tsconfig —— 被迫重走 dev→review→test→browser_e2e→pm_acceptance→ship,test / browser_e2e 各 bypass 一次;同时 await-merge 把本分支新增 `proxy.ts` 导致的 TS2307 连判 8 次「base 预存在」,监控不报警。

- **P0 · 归档后报告门不再逼 bypass**:`ship.phase ∈ {archived, pushed}` 时 TEST-REPORT / BROWSER-TEST-REPORT 跳过「在 commit 内」检查(需求目录已 `git rm --cached` 出分支 · 永远满足不了)· 文件存在照查 · concerns 记 INFO(设计内豁免)。实证:本单 bypass 2 次。
- **P0 · MR 修复轻量通道**:回炉目标 dev、相对上次 push 代码改动 ≤3 文件且 ≤30 行 → dev-complete 直达 ship 重录 push(验收早已发生);超出照走完整链 · 重录即关闭通道并回到 completed · dev brief 要求测试证据跑 CI 失败的那条命令。原「bypass_log 区分豁免/逃生」不再需要(这类 bypass 不再发生)。实证:一行修复走完 7 个 stage。
- **P0 · CI 归因**:GitLab `_mr_ci_status` 原来 `failing` 恒为空 → 归因无 job 名 → 每次落进「预存在」分支(与「未知按自己引入」的设计相反)。改为 API 取失败 job 名(取不到记 `pipeline`)· base 只看 merge_target **最新一条** pipeline · 失败 job 名命中本分支 `git diff origin/<base>...HEAD` 改动目录 → 直接判本 feature 引入 · 依据逐条打日志 · 两边都空时不判预存在。实证:`fe-ember-official-site-build` 连判 8 次。
- **P1 · ci-commands 跟 GitLab `include: local`**(递归 · 支持 glob)。实证:返回 0 条,CI 对照只能人工。
- **P1 · test-baseline 不越界写主工作区**:worktree 里没有 project-specs 时 `--add` 返回 PENDING,`--target worktree` 写副本 / `--target main --user-confirmed` 写主工作区 · 读取取各份并集。实证:写到了主工作区未跟踪文件。
- **P1 · 复发防御清单门禁**:project-specs 在主工作区未跟踪时给两个落点的绝对路径,主工作区那份有条目也算通过。实证:只能 `--no-defense-entry` 跳过。
- **P1 · 文档**:dev 中途追加范围 → `jump-to-stage --to blueprint`(reason 记停掉 / 待重派的 lane)· 未新增命令(已有能力);blueprint 确认卡对类型/枚举/provider 类字段问「取值集合固定还是会增长」(只问取值集合,不问「将来要不要做 X」)。实证:登录 provider 可扩展性在 dev 中途才追加。
- 验证:新增 `test_post_archive_mr_fix_v8362.py` 16 例(真实临时 Git 仓库跑「归档后修 1 行 → 不 bypass 重录 push」全流程)· 全量通过。
