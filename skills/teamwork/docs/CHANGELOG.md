# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.327 · archive preflight:反向引用扫描 + retro path 物理校验(P1-6)

> aon-core G-TEST-003:测试 `include_str!` 引用 feature 目录下 fixture · archive 按设计删目录 → 整个测试二进制编不出来 · cargo check **红 11 天**(交付完成之日 = 编译失败之日)。
> supersdk:根级模块 sub_project="SDK" 被拼成不存在的 `SDK/docs/retros` · path mapper 在同一仓造出三种矛盾落点 + 幽灵 `CA/` 目录进 git。

### 变更
- **反向引用 preflight**(archive gate 链新增 · bl-flip 之后):`git grep -F "features/<id>"`(排除 feature 目录自身与 `*_archive*`)扫 tracked 引用 —— 命中 → `PENDING archive-backref` 列文件清单 + 处置(代码引用搬出 fixture / 文档死链改指 zip 或 F-id);确属可接受 → `--archive-ref-exception '<一句>'`(记 `state.ship` 审计 · 不静默)。`_archive/<id>.zip` 形态字符串不误伤(归档后引用本就该指 zip)。
- **retro path 物理校验**:`_process_retro_path` 拼 sub_project 前核目录存在(给了 repo_root 时)—— 不存在回退根级 `docs/retros/`(不造幽灵目录);archive emit 与台账拼行两处调用点带 repo_root。

### 测试
`test_archive_preflight_v8327.py` 9 条:tracked 引用拦 + 清单 / 例外放行 + 审计留痕 / 无引用干净过 / zip 字符串不误伤 / retro path 四态(存在前缀 · 缺失回退 · 无 root 旧行为 · 无 sub 根级)/ spec 载体。v8.323 拼行测试按物理校验新行为更新。全库全绿。

## v8.326 · 评审模型错开机器门(P1-5)

> supersdk CA case:双路冷审实测同为 opus-5(主审路未继承会话模型)= 盲区相关 —— 补派错开模型盲审**当场查出 2 条 BLOCKER**(无重新部署入口 / 拉取凭据链整条缺失,两条前两路都在核「按 TECH 实现没有」故均错过)。SKILL「评审模型必错开」是纯规则:外审 `review_model` 只申报不比对,主审路根本不申报 —— 规则存在 ≠ 规则执行(又一格)。

### 变更
- **主审产物申报**:PRD-REVIEW / TECH-REVIEW / REVIEW frontmatter 新增 `review_models`(列表形态 `- <role>: <实际模型>` —— 适配行式解析 · v8.324 缩进放宽后申报不构成新格式税)。
- **`review_models_staggered` evidence check**(goal / blueprint / review 三处注册):主审 `review_models` × 外审 `review_model` 合并比对(ultra-ingest 不参与 —— 模型不由框架派发)—— **≥2 路申报且全同 → complete 拒**(hint 给处置:任选一路换模型重跑;确属例外走既有 bypass 协议留痕,不发明新旗);<2 可比对(存量未申报 / 单路)→ skip,hint 教新产物申报格式。大小写不敏感比对。
- start 预告零成本:v8.324 契约块从 spec 同源渲染,本门自动出现在三个 stage 的 start brief。

### 测试
`test_review_model_stagger_v8326.py` 11 条:同模型拒(原案复刻)/ 错开过 / 大小写 / 存量 skip+教学 hint / 单路 skip / ultra-ingest 除外 / 双外审同模型拒 / 单空格申报可解析 / 三处注册 / start 预告自动带 / 三 stage 文档契约。全库全绿。

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
