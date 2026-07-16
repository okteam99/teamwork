# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.245 · 排查升级暂停点:多候选逐一编号 + 斜杠并列即自由文本(治 ok 无从解析)

> 来源 case(问题排查 · codex 宿主):排查报告漂亮,收尾却 emit `⏸️ 请确认后续动作:Bugfix 流程 / 不处理代码(先修正 staging 配置)/ Feature 流程` —— 斜杠并列自由文本 · 无编号无 💡 推荐 → 用户回 `ok`(快捷词协议 = 选推荐项)无从解析 → AI 再问一轮 · 白耗两个来回。**模板其实早就存在**(SKILL Mode A/E 升级触发节 v8 早期就有 R5 格式),病根有二:①模板只有「进 X / 暂不升级」单流程形态 · case 是三候选动作 · 塞不进就退化成斜杠清单;②问题排查不进状态机 · 无机器 emit 可挂消费时刻提醒 · 长会话后凭记忆 emit 格式丢失。

### 改动(文本载体钉死 · 三处)
- **SKILL § Mode A/E 升级触发模板升级为多候选形态**:选项 1/2 = <按结论最可能的动作 · 具体化>💡 / <候选动作 B · 具体化>(不再绑死「进 X / 暂不升级」)· 新增三条规则:🔴 多候选动作**逐一编号**(斜杠并列 = 自由文本 · ok 无从解析 → 白问一轮)· 选项**具体化自排查结论**(「先修正 staging 配置(不改代码)」而非抽象流程名)· **💡 推荐必给**(排查者最有信息量 · 不给推荐 = 判断甩回用户 + ok 快捷词失灵)。
- **R5(b) 判定红线(全局)**:补「斜杠并列候选清单『A / B / C』同属自由文本」—— 不止排查 · 任何暂停点适用。
- **prepare.md 排查先行律**:升级暂停点行改为「候选动作逐一编号(R5 1/2/3 + 💡 推荐)」并显式点名反例(候选斜杠并列写进一行 = 自由文本)。

### 验证
- pytest 860 passed(纯文档 · 无行为变更)。
