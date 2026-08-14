# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.320 · browser-e2e 可重放契约:关键路径必留脚本 · Playwright 默认首选

> 用户(7-29):Browser E2E 是否可以约定优先使用 playwright?→ 拍板「约定产物:关键路径必须留可重放脚本」。
> **该拍板当时未落地**(对话随后转向,无任何载体接住)。今日用户重提:目前 browser-e2e 测试用什么有规范么,预期优先使用 playwright —— 两条一起补。

### 问题(改前现状)
- 工具菜单写「Playwright / Puppeteer / Selenium · 按项目栈选」—— 无默认,临场自选。
- 产物契约只收 `screenshots/*.png` + 报告 —— **截图是一次性证据**:代码一改,旧截图证明不了新代码;AI 用 playwright MCP 手点也算「用了 Playwright」,工具名约束不了可重放性。

### 变更(三载体 + 运行时 brief)
- **stage ② 硬规则 6**:关键路径必留可重放脚本 —— 判据「**这条 browser 验证在交付后还需要重跑吗(回归 / CI)?**」需要 → 脚本进 repo + TC 注册(生命周期 **L2** · 进 L1 仍走 `ci_reason` 门);只看一眼 → 截图即可(探索落 scratch)。
- **stage ③ 菜单**:Playwright(默认首选 · 用户拍板)· 已有 Puppeteer / Selenium / Cypress 基建则**复用**(一致性优先,不逼迁移)。
- **stage ④ 产物契约**:+可重放脚本行(落项目 e2e 目录 · TC `tests[]` level: fe-e2e)。**不设机器门** ——「关键与否」是判断题,载体承载。
- **报告模板**:frontmatter 新增 `replay_entry` 必填槽(关键路径写一条可直接跑的重放命令 / 探索性一次性填 `n/a` —— 空着 = 没想过要不要重放);`browser_automation` 注释改为默认首选口径。
- **tc.md 执行方式二分**:`browser-script`(可重放 · Playwright 优先)/ `browser`(AI 手点 · 仅探索性/一次性,降级理由写在选项旁)。
- **运行时 brief 同步**(`_browser_e2e_brief`):结果区 +replay_entry 与可重放脚本行 ·「注意事项 5 条」→ 6 条(动作点载体不同步 = 模式承诺未物化,已两例的老病)。

### 测试
`test_browser_e2e_replay_v8320.py` 14 条:判据措辞 / L2+ci_reason 衔接 / 手点反例入 why / 探索性出口 / 菜单默认+复用 / replay_entry 槽位含 n/a / tc 二分 / brief 同步 / artifacts 仍 2 项 evidence_checks 空(锁「不设机器门」设计边界)/ 触改文件零版本标。全库 1271 collected 全绿。

## v8.319 · scratch 根迁入 worktree:随 worktree 生一起死

> 用户:`/tmp/teamwork` 的内容能放到 worktree 下面么,随着 worktree 就一起清理了?
> 追问 ①「push 清理走脚本么」②「清理耗时么」→ 三问都在本版物化。

### 拍板前实测清掉的最大未知

`git worktree remove` **不被 ignored 构建产物拦**(实测:ignored 文件在场 remove 直接整树删);
tree-hash 指纹用 `git diff HEAD`,ignored 不进 diff → 不受影响;
worknode 额外收益:worktree 在**绑定卷**,scratch 不再堆容器**可写层**(141GB 实证环境的元凶)。

### 新形态

```
worktree 模式(缺省): <worktree>/.teamwork-scratch/<用途>   ← bootstrap 自动 gitignore「.teamwork-scratch*」
worktree=off / legacy: ${TMPDIR:-/tmp}/teamwork/<feature_id>/<用途>
```

**回收三通道重排**:① ship1 push 成功即清(双根)② **worktree 生命周期主兜底** ——
finalize / close 删 worktree = scratch 必然随之消亡(不存在「清了 worktree 忘了 scratch」的错位);
ship2 tmp-cleanup 转存量旧根幂等兜底 ③ TTL:旧根整目录 + 各 worktree 的 `.teamwork-scratch*`
子目录(🔴 只删 scratch 子目录**绝不动 worktree 本体**〔可能藏未提交工作〕—— 子目录永远可安全删)。

### 三个插问的物化

- **走脚本**:清理在 `ship-phase --action push` 处理器内(与 push 记录同一条命令 · emit `scratch_cleanup`);
- **耗时**:原实现同步 rmtree + 全树统计 = **双遍历分钟级会拖住 push** → 改**同盘 rename(O(1) ·
  原路径立即消失)+ detached `rm -rf` 后台真删**,push 毫秒级返回;体量 `du` 限时 3s 大树跳过;
  后台删夭折的 `*-trash-*` 残骸由下次清理 glob + TTL 双兜底;
- **通配 `.teamwork-scratch*`** 让 gitignore / 清理 / TTL 三方天然覆盖 rename 残骸。

### 落点

工具:`_prune_feature_tmp` 双根重写 + push/close 传 worktree 路径 · bootstrap gitignore 新 entry +
TTL 第二根扫描。spec 九处同口径(common §六 / HARD-RULES 10+17 / conventions §12.5 / SKILL /
ui-design 6 / test-stage 9 / ship-stage §4 / dev-stage 8 / tc.md L3)。
自己的版本标门当场抓了新文里手滑的一处「v8.306」—— 门在工作。
