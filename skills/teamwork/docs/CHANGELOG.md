# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.148 · ship2 后流程质量审计落安装目录 docs/audit/ · 框架跨项目搜集(补全反馈环消费侧)

> 用户(承前三轮诊断):ship2 后加一段 AI 静默逻辑 · 总结当前项目执行数据(做的好的/发现的问题/待优化的 + 实际数据)· 写到 skill 安装目录 docs/audit/ · 方便框架层面搜集流程质量。

### 背景:补的是反馈环缺失的「rollup 回收层」
- 前三轮查实:① ship2→框架的反馈通道只有意图无机制(jdp 漏掉真判例);② 「年检」被引用 7 次作消费方 · 0 次定义 procedure(幽灵);③ 项目级→框架的总结流程根本不存在。三者同一病根 = 反馈环只建了「写」· 「读/rollup」整个没规范。本版补 rollup 回收层第一块。
- 三处落点分工成文:PROCESS-LEDGER(项目侧 per-feature)· **docs/audit/(安装目录回收侧 · 跨项目)** · RETRO-LEDGER(框架仓 per-version)。安装目录 = 本机所有 consuming 项目共享回收点 · consuming 项目不自改 spec · 只投递 · 框架来 harvest。

### 改动(代码 + 测试 + 文档)
- **`_write_audit_record`(ship-finalize PASS 后调)**:落 `<安装目录>/docs/audit/<id>.md` —— **机器数据段工具确定性抽**(来源项目/flow/实走 stages/总时长〔stage_contracts 时间戳算〕/concerns/bypass · 喂 kill-criteria 不可幻觉)+ **三段判断占位**(做的好的/发现的问题/待优化的)由 **AI 静默补**(零暂停 · 改 audit_status: done)。`TEAMWORK_AUDIT_DIR` env 可 override(测试)· 写失败静默降级不阻塞 ship2 · 已填不覆盖(幂等)。
- 「发现的问题」段 = 框架级 bug/工具判例的**持久回收口**(取代 §16 旧易逝 digest 的「建议反馈 teamwork」行)。
- docs/audit/README.md(回收/harvest 说明)· .gitignore 只入库 README(运行时 <id>.md 是 transient 本机回收料 · 抗 update.py 覆盖:_overwrite_skill_files 不删 target 多余文件)。
- §16 三处落点表 + 时机成文;emit 增 audit_record + brief 静默补完指示。
- 测试 +2(审计草稿落 TEAMWORK_AUDIT_DIR 含机器数据+占位 / 已填不被重跑覆盖)。

### 验证
- pytest 3 failed / 527 passed(baseline 3 · 净 +2)· 真实产物 eyeball(时长/stages/concerns 确定性正确)。

## v8.147 · LEDGER 冲突升级机械自动解:三方对比纯增行判定 · union 进脚本(实战 case 驱动)

> 用户(截图 case:SVC-CORE-B260612051432 · aon 实战):v8.146 防线首战 —— PROCESS-LEDGER 三行追加冲突按 ③ 留给 AI · AI 的处置 = 删标记保双方行 · **零判断纯机械**。判定:该进脚本(v8.146 保守只解 INDEX · 实战证明 LEDGER 同样可枚举)。

### 设计:安全前提物化
- `_try_append_union_resolve`:三方对比 base(:1:)/ours(:2:)/theirs(:3:)· **双方相对 base 都是纯增行**(base 行序列为两侧保序子序列)才自动 union(theirs 全文为基 + 本侧增量去重后置)· 任一侧有删/改 → 拒动留 AI(PENDING 提示改为「台账类但非纯增行 · 人工合」)。
- 适用名单制(`PROCESS-LEDGER.md`)· 不做通用文件 union(代码文件双方尾部追加 union 可能语义错误)。
- sync 返回升级:status 统一 `auto_resolved` + `auto_resolved_files` 清单 · archive emit 的 `sync` 注明解了哪些文件(透明可审计)。

### 实战判读(截图 case · 防线首战全对)
- 重跑 archive = 冲突修复入口 ✓ · INDEX 静默处理 ✓ · LEDGER union 保双方行 ✓ · 只 add 冲突文件不碰 untracked 接力卡 ✓ —— AI 处置零瑕疵 · 但这步本可不存在 · 故升级。

### 验证
- 测试 +2(纯增行自动 union 双方行都在 / 非纯增行〔同行双改〕拒动 PENDING 留 AI)· pytest 3 failed / 525 passed(baseline 3 · 净 +2)。

## v8.146 · ship1 冲突防线:archive 前置 sync 自动合 · INDEX 冲突机械自动解 · 代码冲突留 AI

> 用户(承 v8.145):ship1 在 MR 创建后大概率会冲突 · 是否有必要增加检测冲突环节 · 自动评估处理。判定:有必要 —— v8.145 设计时把该 trade-off 低估为「可能」· 实为「并行 ship 窗口重叠时必然」(INDEX/LEDGER 是 every-feature 同位追加)。

### 设计(按框架哲学拆:可枚举进脚本 · 不可枚举留 AI)
- 解决场所 = worktree(到 ship2 前一直活着 · 正是 v8.145「内容性工作在可控环境」的合法位置)。
- 同步用 **merge 不 rebase**(分支已推 · MR 已开 · 不破 review 历史)。

### 改动(代码 + 测试 + 文档)
- **`_sync_feature_branch`(内置于 archive · 首跑+幂等重跑共用)**:fetch + behind 检测 → 落后自动 `merge origin/<mt>` —— ① 干净则无感(MR 开出来即可合 · INDEX 基于合并后状态生成);② **INDEX.md 冲突机械自动解**(确定性再生成:origin 侧为基 + 重放本 feature 行 · 追加表语义明确);③ 其余冲突(代码/规划文件)→ emit `PENDING merge-conflict` + 文件清单(LEDGER 类提示 union)· AI 在 worktree 评估处理 → `git add`/`git commit` → 重跑 archive。
- **重跑 archive = MR 窗口期冲突修复入口**:平台报冲突 → 回 worktree 重跑(自动 sync + 机械解)→ `git push` → MR 自动更新;⏸️ ship1 暂停点加「平台报冲突」选项;emit 增 `sync` 字段(同步动作透明)。
- fetch 失败降级(冲突防线降级不阻塞归档 · WARN);未完成 merge 检测(MERGE_HEAD)→ 先收尾再重跑。
- 测试 +3(前置 sync 无感合 / INDEX 冲突自动解双方行都在 / 代码冲突 PENDING→解→重跑通过)· ship-stage.md §3 冲突防线成文。

### 验证
- pytest 3 failed / 523 passed(baseline 3 · 净 +3)。

## v8.145 · ship 架构重构:ship1 全交付(worktree 内 · 终点 = MR 提交)· ship2 零内容清场 · 砍双 MR 链路

> 用户拍板:单个 ship 的终点就是提 MR · 收尾更新状态不属于本次 ship。ship1 全交付 feature 内容(文档总结/压缩 zip 全在 worktree 内)· 完成后提示用户合并 MR 即结束;ship2 回主工作区删 worktree · 净化(脏内容提交 · 影响大给方案由用户决策)· pull · push。**ship2 不修改任何内容**。三项确认:INDEX.md 保留 / 副产物自动 commit / 不留兼容期。

### 架构裁定(为什么对)
- 旧链路十二个版本(v8.16/31/32/33/70/80/82/87/93/113/130/144)反复修同一条尾巴 —— 根因 = 在**不可控的主工作区**(脏树/分叉/并行 feature/保护分支)做**内容性工作**(归档/翻牌/状态)。新原则:内容全部发生在可控环境(worktree · 自己的分支)随 feature MR **原子合入**;主工作区只清理。
- **单 MR**:归档 zip + 规划翻牌 + 终态 state.json 全进 feature MR · 不再有 ship-finalize/<id> 第二分支 + 第二个 MR。**MR diff 反而更干净**:过程目录在分支历史「加了又删」对 merge_target 净零 · diff 只剩代码 + zip + INDEX 行 + 翻牌行。
- **翻牌语义更对**:随 MR 原子生效 —— MR 不合 ROADMAP 不显示已交付 · revert 同退(旧模型有 merge 后时间窗)。
- **主工作区从未物化过程目录**:v8.82 purge / v8.87 残留清除 / v8.144 staged-D 终态 那批债结构性消失。

### 改动(代码 −979 行 · 测试 · 文档)
- **ship-phase 新 action `archive`**(ship1 终幕 · tool-executed):规划翻牌 gate(--planning-artifacts/--no-planning-changes · v8.93 前移)→ 终态 state.json(current_stage=completed · 墓碑进 zip · 宣称与落地随 MR 原子可见)→ zip + INDEX(--archive-desc ≤200 门禁保留)→ `git rm --cached` 过程目录(**工作树保留 = ship2 接力卡**)→ 单 commit。幂等;push 门禁改 archived → pushed。
- **ship-finalize 重定义为 ship2**(零内容):verify-delivered(zip 在 origin · 抗 squash · 未合 PENDING 绝不删 worktree)→ worktree-remove(+fetch --prune)→ main-sync(**副产物注入块/锁自动 commit** · 用户真改动决策面板 · pull --rebase/--ff-only 对症 · push 被拒提示)→ stash 盘点 + digest 指引。幂等:接力卡消亡 → origin 全树搜 zip → noop。
- **删除(不留兼容期)**:confirm-merged/cleanup 子动作 · state-sync · finalize-deliver 双 MR 链路 · 零 checkout plumbing(_stage_archive_commit/_finalize_push_plumbing)· v8.82 purge · v8.87 强清 · §12 state.json 直推例外 · archive_on_ship 配置(残留忽略 + WARN)。
- **main-sync 去 feature 依赖**(接力卡可已消亡):--feature 可选 · --merge-target 三级推导;决策面板命令串同步。
- 测试:新 test_ship_v8145_flow.py(13 测:archive gate/归档形态/翻牌原子/幂等/ship2 全周期/副产物自动 commit/决策面板/featureless main-sync)· 删旧链路 ~37 测 · ship 存量套件适配;SHIP_SPEC/SKILL/ship-stage.md/模板 全面改写。
- PROCESS-LEDGER 采写时机:planning-backref(主工作区)→ **archive 规划 gate(worktree 内)** · 数据源就在工作树。

### 验证
- pytest 3 failed / 520 passed(baseline 3 · 旧链路测试删除后净 −29 · 新流程 13 测全绿)。

## v8.144 · ship-finalize 收尾终态治理:pop 结果必查 · pull 失败对症判别 · 残留清除即补 pull · stash 盘点

> 用户(case:SVC-PLATFORM-B260611083636 收尾 transcript):看下收尾动作是否有问题 · 是否需要优化。终态正确(双 MR merged · 归档落位)· 但尾段甩给 AI ~20 条 git 手术 · 其中两处是框架自造的债。

### 诊断(代码对照 + git 沙箱实测)
- **pop 结果被无视**:step 7 stash→pull→pop 链 · pull 失败分支不查 pop.returncode · 宣称「stash 已 pop」—— 实证里 pop 没成 · bootstrap 注入块改动埋在 auto-stash · AI 误以为丢失**手工重写** = 与 stash 双份地雷。
- **「分叉 · 需手动 rebase」一刀切误导**:任何 pull 失败都喊分叉。沙箱实测(E2):staged 删除(本地删 vs origin 同删)+ 无关 M 文件**不阻塞** ff-pull —— 实际仅落后 · 一条 `git pull --ff-only` 即愈 · AI 却被引上 reset/stash/pull 手术路径。
- **v8.87「下次 pull 自愈」只对一半**:残留清除用 git rm 留 staged 删除等下次 pull —— 前提成立(实测)但「下次」不该留给人:PASS 终态停在 behind + staged D。
- **teamwork 自动 stash 跨 feature 堆积**(实证 3 个跨 2 feature)无人盘点;收尾分支零 checkout 仅存远端 · emit 不说 · AI 烧 4 条命令重发现;remote-tracking 残影要手动 prune。

### 改动(代码 + 测试)
- **`_behind_ahead` + `_pull_failure_remedy`**:rev-list --left-right 判别「仅落后(给 pull · 不喊 rebase)」vs「真分叉(才给 rebase)」· clean 路径 / v8.32 stash 路径 / v8.87 补 pull 三处接入。
- **pop 必查**:pull 失败分支区分 pop 成败 —— 失败 → `pull_failed_stash_stuck` + 「改动埋在 stash『名』· 先 pop 勿手工重写」;两处 pop 失败文案都带 stash 名。
- **v8.87 残留清除后立即补 ff-pull**(E1/E2 背书)→ 成功即 `purged_pulled` 干净+最新 · PASS 不再留 behind+staged D 终态。
- **stash 盘点**:emit `teamwork_stashes` + 处置指引(show -p 核对 → pop/drop · 勿堆积);deliver_pending 注明「分支仅存远端 · 本地查不到属正常」;delivered 清理后自动 `fetch --prune`。
- 测试:新 test_ship_main_sync_v8144.py(8 测 · 含 staged-D ff-pull 地面真相固化 · 防 git 行为回退静默失真)· ship 既有 55 测零回归。

### 验证
- pytest 3 failed / 557 passed(baseline 3 · 净 +8)。

