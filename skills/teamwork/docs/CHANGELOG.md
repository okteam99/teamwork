# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.325 · merged worktree 巡检 + 构建世界纪律(P1-4)

> aon-core `.worktree/` 23G:14 个注册 worktree 里 13 个分支已 merge(18G 纯垃圾 · 最老 31 天)+ 1 孤儿目录;supersdk 5 个僵尸壳被 `ws-progress` 递归扫成双份(9→18)。
> 根因与 141GB scratch 同款:回收挂在 ship2,session 常死在 ship1 push 后 → ship2 永不跑;且 `worktree_cleanup` 配置键**没有任何代码消费者**(安慰剂配置 —— 「ask」从没人被问过)。

### 变更
- **`bootstrap.prune_merged_worktrees`**(挂 session bootstrap · 每 session 会跑到的地方):worktree 根下逐目录巡检 —— 僵尸壳(不在 `git worktree list` · 树里只有 .DS_Store)任何模式都删;注册 worktree 已 merge 进 merge_target 且干净(untracked 仅接力卡 `docs/features/**` · `-uall` 逐文件豁免)→ 按 `worktree_cleanup` 处置;未 merge / 有真实未提交内容**永不动**(报告);孤儿有内容只报告;收尾 `git worktree prune`。体量 `du -sk` 限时 3s(同 scratch 的耗时纪律)。
- **`worktree_cleanup` 转正为真开关**:`auto`(**新默认** · merged+干净即删 + branch -d)/ `ask`(不删 · 每 session bootstrap 逐个报告 —— ask 终于真的在问)/ `keep`(只计数)。存量项目显式写的 `ask` 不被覆盖(backfill 只补缺失键 · 用户主权)。
- **构建世界纪律收编**(conventions §12.45):worktree 只隔离 git 树不隔离构建世界 —— 依赖目录 / `.pth` editable / 构建缓存与 TMPDIR / 测试数据库 / dev server 端口五面纪律表(消费项目六条独立 KNOWLEDGE 同根教训收编为框架职责)。

### 测试
`test_worktree_prune_v8325.py` 13 条:auto 删+删分支 / 接力卡 untracked 不挡(-uall 修折叠)/ 真残留只报 / 未 merge 不动 / ask·keep 语义 / 僵尸壳任何模式清 / 孤儿只报 / 默认翻转+模板同步 / 非法值回退 ask / wiring / 构建世界表。全库全绿。

## v8.324 · 格式门禁前置化:complete 契约 spec 同源预告 + 解析器放宽一档(P0-3)

> 两项目耗时归因 26-28% 轮次 = 纯协调开销,归因高度同质:「格式门禁重试 · spec 字段名未预读」「dev-complete 的 test-runner 门在 dev-start 没预告 · complete 时才拒」;aon-core 复盘:外审产物 YAML **单空格缩进**列表被解析为空 `files_read` → CAPABILITY_BLOCKED 误报 —— 一个缩进空格换一轮返工。

### 变更(两刀)
- **start brief 自动附「⛔ complete 时机器校验」块**(`_render_complete_contract`):从 artifacts / evidence_checks 的**同一份 spec 对象**渲染(产物路径 · glob 最少数 · frontmatter 必含字段 · body 行数 · 须在 changeset · fast 豁免标记 · 每条 evidence 点名+描述)—— 门禁改了预告自动跟,手写 brief 漂移不再可能漏预告(11/12 个 stage 有契约块 · 无门禁 stage 渲染为空)。
- **`parse_frontmatter` 列表缩进兼容 1-4 空格**(原只认两空格):格式门禁的解析器必须比它拦的格式宽一档;5+ 空格 = 嵌套结构,行式解析不装懂,保持忽略。

### 测试
`test_gate_preannounce_v8324.py` 10 条:单空格伤亡原型 / 2-4 空格 / 深缩进仍忽略 / key:value 不受扰 / GOAL·BROWSER_E2E 契约块 / 反向锁「有门禁必有预告块」/ 源码顺序锁 / dev test-runner 门 start 可见。全库全绿。

## v8.323 · 台账自动落行:archive 直接写行(P0-2)

> aon-core 复盘原话:「emit 提供了已算好的 `ledger_timing`/`ledger_stage_cost`,台账行仍需人工 append —— 若 archive 能直接落行,可再省一轮。」
> supersdk 实证:47% 归档 feature 台账无行(最近 8 次 ship 漏 3 次)· 判例「精确 timing 仅在 archive 后 emit · 需归档后补提交」(时序矛盾)。

### 变更
- **archive 自动落行**:`_compose_ledger_row`(机器格确定性取数 = 此前让 AI「照抄」的同源字段:实走 stages / 时长三分 / 各阶段耗时 / bypass·WARN 计数 / 宿主 / 邮箱 / 分诊校准 / 可预防性 / 耗时归因)+ `_append_ledger_row`(无台账按模板建表 · 有则先跑 v8.322 迁移〔表头+旧行补宽〕· 按 feature_id 幂等 · 插表尾)· 行随归档 commit **原子合入**(timing 此刻已在手 —— 时序矛盾一并治)。
- **判断格走参数**:`--ledger-reflection`(反思摘要 · **必填 gate** `pending_step: ledger-row`)+ `--ledger-rounds / --ledger-external / --ledger-findings / --ledger-pauses`(缺省 `—` = 诚实留空 · emit `defaulted_cells` 点名)。单元格净化(竖线→全角 · 换行压平)· 列宽对齐模板单源(模板加列自动补 —)。
- **emit**:+`ledger_row`(status/row/defaulted_cells);`ledger_*` 旧字段保留(透明校验 + 旧消费方兼容)。台账失败不拦归档(status:error 可手补)。
- **brief/spec 改口**:push brief 不再教「先 ledger-migrate 再手工 append」;ship-stage §3.5/§16、process-ledger 模板同步(顺带修正模板残留的「旧数据行不动」旧语义 → v8.322 补宽语义)。
- 两条设计锁按新设计更新:v8295 emit 字段注册表 +ledger_row;v8301 migrate-before-append 时序锁从「brief 文案」改锁「_append_ledger_row 源码顺序」。

### 测试
`test_ledger_autorow_v8323.py` 9 条(列宽单源 / 机器格 / 净化 / 幂等 / 建表 / 旧 schema 先迁 / gate / 行入 HEAD / 重跑不重复);既有 ship 测试 48 条经 `_archive` helper 注入默认反思全绿。

## v8.322 · 升级传导:版本漂移入口自愈(P0-1)

> aon-core × supersdk 实证分析拍板「按建议」的第一件。
> supersdk 画像:skill 全局副本静默升 37 版 · per-project bootstrap 20 天没跑 ·
> `last_update_check_result` 还在说 up_to_date · 台账 61% 旧列宽(aon-core 50%)·
> gitignore 注入水位停在三十版前 ——「提示用户去跑 bootstrap」被实证不发生。

### 治法(与 scratch 清理同构:挂在积灰机器自己天天跑的命令上)
- **state.py 入口自愈**(`main()` 前 best-effort · 绝不拦正事 · 输出走 stderr 不污染 stdout JSON 契约):marker 版本 ≠ 当前 skill 版本 → 就地跑零风险幂等迁移集 —— ①台账 schema 迁移 ②gitignore 条目重放 ③marker 记录(`_bootstrap.state_migrate{at,from,to,actions}` · 不冒充 full bootstrap 的 `skill_version`)。chmod / hooks / host 注入 / 升级 R5 检测仍归 session bootstrap(重量级或需用户决策 · 不越权)。不接管:无 localconfig / 无 `_bootstrap` marker(首铺归 bootstrap)/ skill 在项目仓内(框架仓自身守卫)。
- **台账迁移升级为「表头 + 旧行补列宽」**(`_v8_engine.migrate_process_ledger` 单源 · state.py `ledger-migrate` 与 bootstrap maintain 双通道共用):立制时「旧行是有效前缀不动」被两项目实证打破(按列索引解析静默错位 · 年检读错列)—— 改为**内容前缀逐字不动 · 末尾补 `—` 到表头宽**(`—` = 早于该指标)· 只补不裁(超宽/断行不动)。
- **state.json schema 版本**:`_schema_version`(int · schema 真变才 +1)写路径盖戳(engine `save_state` + state.py `atomic_write` 双写点)· 读路径只拦「来自未来」(混合宿主/多机下新 skill 写的 state 不被旧逻辑静默丢字段)· 缺失/更低 = 旧数据兼容读。
- `locate_localconfig`(返回路径)从 `load_localconfig` 拆出单源共用。

### 测试
`test_version_drift_heal_v8322.py` 16 条(自愈全路径 / 不接管三场景 / 只补不裁 / 入口 stderr + stdout 纯 JSON / schema 戳与未来拦截);`test_ledger_migrate_v8210.py` 按新设计更新(旧行「逐字不动」→「前缀不动 + 补宽」);`test_authoring_preventability_v8281.py` 指向 engine 单源。全库全绿。

## v8.321 · browser_e2e 档位承载:验证档 subagent 写进动作点

> 用户:是 subagent 验证档模型执行这个阶段么?
> 答案在全局白名单里是「是」—— 但 browser_e2e 自己的 stage 硬规则与运行时 brief **零承载**。

### 问题
档位约束(e2e ∈ 验证类白名单 → 一律降验证档 · 例外须用户授权)只活在 SKILL 全局规则与 agents/README 档位表;对照 goal/blueprint(🎚️ 不许降档)、review(🎚️ 验证轮用验证档)、test(subagent 并行判据),唯独 browser_e2e 这个白名单成员在自己的执行入口一行没写 —— 执行到该 stage 的 AI 若 context 没带全局白名单,默认继承会话主模型自己手点(常费而不自知)。「模式承诺 × 动作点载体」对账表第三格(fast/yolo 之后)。

### 变更(两载体)
- **stage ② 硬规则 7**(🎚️):默认派验证档 subagent 执行 —— 主对话模型是用户主权不可切,**降档只有派 subagent 显式传 model 一条路**(prompt 首行 `Meta: tier=验证 · model=… · 理由=…`);例外 🔴 不许 AI 自决 · 开 R5 请用户授权(典型:首份可重放脚本要逆向真进程启动配方 = 探索+调试占主体 —— 与硬规则 6 的可重放契约衔接);宿主不支持 subagent → 主对话串行 + `⚠️ WARN [degradation-fallback]`。判据单源仍在 agents/README §一,本行是指针复述。
- **运行时 brief 同步**:+🎚️ 档位行(Meta 申报格式 + R5 例外)·「注意事项 6 条」→ 7 条。

### 测试
`test_browser_e2e_tier_v8321.py` 9 条:降档唯一路径 / Meta 申报格式 / R5 例外含首份脚本典型 / 降级 WARN / 指针指单源 / agents/README 白名单仍含 e2e(单源锚 · 漂了先在这响)/ brief 三断言。全库全绿。
