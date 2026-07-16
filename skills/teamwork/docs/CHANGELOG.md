# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.250 · micro 流程重构:execute 零门禁自由执行 → ship(去 dev 门禁 + pm_acceptance)

> 用户拍板:micro 的病是「零逻辑改动却背全套 stage 门禁」。新 micro = **prepare → execute(自由执行 · 无规范限制)→ ship**。prepare 之后 AI 用它认为最合理的方式完成任务——自主决定用不用 subagent/teammate/workflow、自选模型、自决要不要跑测试,无任何框架规范限制,目标只有「完成任务」。然后 ship。

### 新 micro 链 = `execute → ship`(原 `dev → pm_acceptance → ship`)
- **新增 `execute` stage**(STAGE_SPECS 第 13 个 · allowed_flow_types=["Micro"]):零 prerequisites / 零 artifacts / 零 evidence 门 —— 唯一硬边界 2 条:① 代码写 worktree 内路径(并行隔离)② 不得超出 micro 准入白名单(超纲=误分诊·停·升 Feature)。brief 明写「自选 model/subagent/workflow/测试 · 无规范限制」。安全前置在准入白名单(prepare §2.2 卡死零逻辑),故执行阶段可无门禁。
- **去 pm_acceptance**:用户验收从 pm_acceptance 挪到 **ship1 的 MR diff review**(user_card + await-merge · 合并前看 diff)。`_check_pm_approved_ship` 加 micro 豁免(否则 ship-start 撞 pm_approved 前置)。micro 授权暂停点 3→2(prepare + ship1)。
- **去 dev**:micro 不再进 gated dev。`_dev_transition` 删死分支(Micro→pm_acceptance)· dev 一律 → review(去 micro 特例 · 防 v8.222 类死流程分支静默错误)。

### 改动面(两套流程图 + 初始 stage + 消费点)
- `_v8_stage_specs.py`:EXECUTE_SPEC + _execute_brief/_execute_transition + STAGE_SPECS 注册 + _check_pm_approved_ship micro 豁免 + _dev_transition 清死分支。
- `_v8_engine.py`:FLOW_STAGE_CHAIN["Micro"]=[execute,ship] + DEFAULT_REVIEW_ROLES 去 Micro/pm_acceptance 条目。
- `state.py`:MICRO_FLOW 转移图=execute→ship→completed + DEFAULT_INITIAL_STAGE["Micro"]=execute。
- 文档:新 stages/execute-stage.md · FLOWS/SKILL 流程表+暂停点清单+命令清单 · prepare §5 first_stage 映射 · STAGES.md 索引(+execute · 12→13)· README 双语计数。

### 验证
- 新测试 +10(链/转移图/初始 stage/execute spec 零门禁/transition→ship/brief 硬边界/pm 豁免仅 micro)· 旧断言 3 处更新(micro initial · no-pause 集 · dev-transition)· pytest **883 passed**。

## v8.249 · 纠 v8.247:cargo target 按 feature 共享(不按 stage 切)· 恢复 stage 间增量编译

> 台账年检(用户:AI 自主时间太久)顺出的根因之一:v8.247 scratch 约定写「按 stage 隔离 target 是正确设计 · 防多 worktree 并行争抢文件锁」—— **推理错**。并行争抢发生在**不同 feature 的不同 worktree** 之间,而 scratch 路径里的 `<feature_id>` 已把它们隔开;同一 feature 内 stage 严格串行(状态机一次一个)、从不并发构建 —— 再按 stage 把 target 切成 `<feature_id>/test-stage`、`<feature_id>/dev-target`,唯一效果是 **test 拿不到 dev 编好的 target,每 stage 冷编整棵依赖树**(Rust 冷编 5-20min vs 热增量 <1min)。这正是台账里 test 阶段占 AI 自主耗时 23% + blueprint/test 编译重极值的主浪费来源。

### 改动(纯约定纠正 · 零代码逻辑 · GC 不受影响)
- **standards/common.md §六**:build target 改**按 feature 共享**(`<feature_id>/target` · 串行 stage 全复用);显式标注 v8.247 推理错(锁隔离只需到 `<feature_id>` 粒度)+ 例外说明(单 stage 内派多并行 cargo 构建才临时 sub-split);`<用途>` 示例去掉误导的 `test-stage`/`main-target`(那是 target · 不该 per-stage)。
- **stages/test-stage.md**:CARGO_TARGET_DIR 提示同步 —— target = `<feature_id>/target`(别切 `/test-stage`)· 测试日志等无缓存价值的才 per-用途。
- 回收不变:GC(`_prune_feature_tmp` / `prune_teamwork_tmp`)作用在 `<feature_id>/` 整目录级,target 是其下一个子目录名 · 改名无影响。

### 验证
- 纯文档 · pytest 873 passed(无回归)· 退役词表回归网通过。

## v8.248 · 两个工具 bug 修复:ws-lint risks 误报 + ws-progress BL 撞号张冠李戴

> 用户在真实规划 session 报的两个 bug(没擅自改 skill · 用全局唯一编号绕开后回报):
> **①** ws-lint 的 v8.239 调研深度检查用 `^\s*-\s*id\s*:` 在**整个机读块**计数 feature —— `risks[]` 的 `- id: R1` 同写法(模板自带 risks 段)· 6 feature + 4 risk 误报「current_state 缺失(6/10)」——照模板写就必中(v8.239 我埋的)。
> **②** ws-progress 的 `by_bl.setdefault(r["bl"], ...)` 拿 BL 字符串当全局唯一键 · 但 conventions §4 明写「BL-NNN 各项目独立递增」—— 三子项目各有 BL-001 时先扫到的赢者通吃 · 且错的是标「勿手改」的自动生成块 · 每次刷新重新写错(更危险)。

### 修复
- **① features 段限定计数**:`- id:`/`current_state:` 只在 `features:` 段内统计(切片到下一个顶层键)—— risks/execution_waves 等列表不再串味;防矫枉过正:真缺失仍抓(0/1 测试锁定)。
- **② BL 撞号三级判别**(`_pick_bl_row` · 可单测):同号多候选时 ①target 缩写经 teamwork-space registry(`_parse_workspace_registry` 复用)映射 docs_root · 候选 ROADMAP 在其树下 → 命中;②行「对应 F编号」前缀 == target;③目录名 ci == target;④单候选/全不中兜底首个(不比旧行为差)。ready_to_start(v8.196)同一消费点一并修。

### 验证
- 新测试 +6(risks 不计入 · 真缺失仍抓 · registry 判别胜扫描序 · f_id 前缀回退 · 无 target 保旧 · 单候选直通)· pytest **873 passed**。

## v8.247 · scratch 回收三件套:约定固化 + ship2 tmp-cleanup + bootstrap TTL 兜底(治 48GB 磁盘打满)

> 来源:另一 session 的完整提案(用户递交 · 基于真实事故)—— CI mac 磁盘 100% 打满(可用 51MB),下钻定位到 `/tmp/teamwork` 48GB 全是可无损重建的 cargo target(单 feature bl031 散落 7 目录 26GB · 躺了数月)。三条根因:①`/tmp/teamwork` 是事实约定但框架从未定义管理(agent 即兴命名 `bl031-*` · 无主命名空间「有人写没人收」)②ship2 只清 git worktree 不清 /tmp ③容器 /tmp 非 tmpfs 且无任何兜底回收。同类先例 = external-review-logs 膨胀 300MB(已治)—— 本版是同一模式在 160 倍量级上的复用,且提案给出关键设计差异:**cargo target 必须按目录整体删**(fingerprint 一致性 · 不能照抄 review-logs 的按文件删)。

### 改动(三处对应三根因)
- **A 约定固化**(standards/common.md 新 §六 + test-stage/conventions §12.5 消费点互链):临时产物统一 `${TMPDIR:-/tmp}/teamwork/<feature_id>/<用途>` —— 🔴 完整 feature_id(禁 `bl031` 类简称 · 实证即兴命名使按 ID 回收全落空)· 🔴 禁 scratch 根之外(实证 `/tmp/<项目名>-*` 泄漏 6GB)· 与截图约定同根;按 stage 隔离 target 是正确设计(防并行 cargo 锁争抢)只补回收。
- **B ship2 即时回收**(_v8_ship):`SHIP_FINALIZE_STEPS` 增 `tmp-cleanup`(worktree-remove 之后 · main-sync 之前)—— `_prune_feature_tmp()` 在 verify-delivered 通过后整树删 `<scratch>/<feature_id>/`(内容已上岸零对账价值)· 幂等(缺目录 n_a)· 失败不阻塞(warning)· emit 带 `tmp_cleanup.pruned_bytes`。
- **C bootstrap TTL 兜底**:`prune_teamwork_tmp()`(TTL 7 天 · 深度 2 mtime 判活跃〔cargo `.cargo-lock` 每次构建更新 · 全树 rglob 15GB target 会拖慢启动〕· 🔴 按目录整体删)—— 捞回放弃的 feature / 历史即兴命名孤儿 / 约定推行前存量;与 review-logs pruner 并列跑(git 守卫之前 · 与项目无关)· audit JSON 两处带 `teamwork_tmp_prune`。
- 参数取舍:TTL 7 天(review logs 45 天 —— 后者小且有对账价值 · cargo target 巨大且可重建);root 统一 `${TMPDIR:-/tmp}` 口径(比提案的硬编码 /tmp 多覆盖 macOS · 与 §12.5 一致)· `TEAMWORK_TMP_ROOT` env 测试注入。
- 已知局限照提案明示:scratch 根之外仍会泄漏(靠 A 约束)· 存量即兴命名靠 C 的 mtime 捞。

### 验证
- 新测试 +6(TTL 过期删/活跃留/浅层 mtime 防误删/缺根 n_a/ship 整树删含字节数/幂等 + 步骤时序断言)· pytest **867 passed**。

## v8.246 · 自动流转防歇脚:complete emit 机械附带「非暂停点 · 立即继续」提醒

> 来源 case:test→browser_e2e **自动流转**后 · AI 汇报完状态即结束回合(把回合边界当暂停点)· 用户被迫问「为什么暂停了」· AI 自己复盘用词与 SKILL R4 原文一致(「回合边界不构成暂停理由」)—— 规则早在 · 流转时刻无提醒 = 读过 ≠ 在场(与 v8.238 档位提醒同构的消费时点问题)。

### 改动
- **engine `AUTO_TRANSITION_CONTINUE_REMINDER`**:每次 auto-transition 的 stage-complete emit 附 `continue_reminder` 字段——「自动流转 · 非暂停点:本回合**立即继续执行 <next> stage**(汇报/总结完不停 · 回合边界/容量预算/让用户看进度都不是暂停理由 · R4)· 合法停点仅授权暂停点清单 · auto/yolo 同理」;fix-retry 未流转(transitioned_to=None)不附。
- SKILL R4「不膨胀」条款补实证与机器提醒说明。

### 验证
- 测试 +1(流转 emit 含 continue_reminder · 含下一 stage 名/非暂停点/回合边界关键词)· pytest **861 passed**。
