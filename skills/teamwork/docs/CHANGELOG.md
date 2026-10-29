# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.361 · 年检提效:砍掉价值不高的环节(用户拍板「都做」)

> 数据源:aon-core `PROCESS-LEDGER.md`(2026-08-16 后 128 个 Feature)+ 174 份流程复盘。AI 自主中位 115m、等用户中位 136m(等待占墙钟 ~70%)· **~30% 轮次是协调开销**(781/2564)· 暂停点 71% 按默认放行 · 台账 `rejected_with_feedback` 0 次。外审采纳率 goal 7/7、blueprint 24/24 —— **评审环节保留**,砍的是框架自己制造的开销与重复停等。

- **门禁纯开销**:删 goal `prd_review_after_prd`(mtime 顺序门 · 每改 PRD 都得连带碰 PRD-REVIEW · 10 份复盘记过);`must_be_in_commit` 放宽为「本 stage 内已提交且与 auto-commit 一致」也算入账(TEST-REPORT 与代码分两次提交不再被逼重提 · 未提交改动 / 上一轮旧报告仍拦)。
- **测试证据指纹只算代码**:流程目录(feature 目录 / `docs/features` / `docs/retros` / `project-specs`)下的文档类文件不进指纹 → 提交 TEST-REPORT / 改 PRD 不再让证据作废重跑(76 份复盘提到重跑);feature 目录里的 `e2e/*.py` 照算。新增 `state.py tree-hash` 单源取指纹(配方不再手抄 python 片段);旧口径指纹兼容放行。
- **验收拍板并入 ship1**:AC 全过 → pm_acceptance 不停,验收结论进 ship1 MR 卡片「✅ 验收」段,**点合并 = 验收通过并发布**;要改回「要改 <问题>」(MR 窗口期放行口加 `goal` / `ui_design`)。AC 没过 / 有阻塞 / 有产品取舍 → 照旧停三选项。
- **流程复盘文档按需写**:仅协调开销 ≥30% / 有 bypass / review ≥3 轮 / MR 窗口期回炉 / 反思摘要是「判例:」时写;ship brief 直接告诉本单写不写 · 台账行照落。
- **medium 档不产 TC.md**:测试设计归 TECH §测试策略 · AC↔测试绑定走 `PRD.acceptance_criteria[].test_refs`(与 lite 同载体 · test 阶段校验);引擎 `StageArtifactSpec.skip_if`。
- 同期已推 dev 的小改(v8.360.5–.8):功能生效闸先问触发条件能否从源头消除 · PRD 终确认待决策项逐项讨论 · 守卫清单「只在绕过时变」必给触发路径证据。
- 验证:新增 `test_annual_cut_v8361.py` 20 例(真实临时 Git 仓库验指纹与入账判定);全量 **1840 passed, 2 subtests passed**。

## v8.360.4 · 修复评审证据归属、流程修订与合并后清场

- 修正规划收尾的选项编号与执行分支，选 2 仅继续讨论；统一独立冷审的执行规范。
- 外审结果按阶段筛选，新派发绑定请求 ID 与被审 commit；修复后必须有覆盖最后 fix commit 的实际结果，prompt 不再充当完成证据。
- `revise-plan` 同步执行位置、合法下一阶段与评审配置；自定义维度的阶段准入与文档要求按实际计划判定。
- `await-merge --feature` 检测合并后在主工作区实际调用 `ship-finalize`，保留失败、脏文件保护和待决策结果。
- 验证：新增 20 个回归用例；全量 **1812 passed, 2 subtests passed**；真实临时 Git 仓库验证 worktree 删除与主工作区同步。
