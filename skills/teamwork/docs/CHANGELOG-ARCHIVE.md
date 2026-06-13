# Changelog Archive

> 📦 **定期清空**:本文件只暂存从 [CHANGELOG.md](./CHANGELOG.md) keep-5 轮转出的条目 · 膨胀时整体清空 —— 完整历史 = **git 提交历史**(永不丢 · `git log` / `git show` 按需追溯)· 工作区不热存。
> 上次清空:**v8.127**(2026-06-10 · 清除 v8.121 → v1 全部 293 条 · 约 13.9k 行)。

---

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

## v8.143 · 发版交付边界:止于 push dev · 砍本机 rsync · 消费项目统一走 update.py(channel=dev)

> 用户:rsync 去掉 · 本地其他项目走 dev 版本升级 · 你只负责将修改提交到 dev。

### 诊断
- 发版例程里的 `rsync → ~/.agents/skills/teamwork` 是 session 习惯(仓内零成文)· 效果 = 本机消费项目被静默推到未过 main 发布门的版本:无升级提示(本地恒新于线上)· 无确认 · 无 update.py 的 backup · 回滚要手动。用户在 codex session 撞见「静默最新」后拍板砍掉。

### 改动(doc-only)
- **CHANGELOG 头部加「交付止于 push dev」规则**(发版 session 必读处 · 防未来 session 凭惯性恢复 rsync):发版不碰本机安装副本 · 框架仓工作区 ≠ 交付渠道。
- **本机消费项目与其他机器同路**:bootstrap 升级提示(v8.142 起带变更描述)→ 用户确认 → `update.py` tarball 覆盖(自带 backup)。本机项目在各自 `.teamwork_localconfig.json` 配 `"update_channel": "dev"`(项目侧动作 · 不在本仓)。
- 链路已验通:update.py 自 v8.41 去 git 化(tarball 下载覆盖)· 对非 git 安装副本可用;当前安装副本 v8.142.1 == dev tip · 下一版起提示自然出现。

### 验证
- doc-only · pytest 3 failed / 549 passed(零回归)。

## v8.142 · 升级提示带变更描述:线上 CHANGELOG 标题行进暂停点 · keep-5 断档加 git 历史注

> 用户:更新提示出现时 · 需要带一下更新描述。

### 诊断
- 升级暂停点只报版本号 + 「去 GitHub 看 CHANGELOG」指针 —— 用户在暂停点上无法判断「这次升级对我有什么」· 决策要出门。发版纪律里每版标题行本就是一行蒸馏摘要 · 现成可用。

### 改动
- **`_fetch_changelog_titles`**(bootstrap.py):outdated 时拉线上 `docs/CHANGELOG.md`(channel 同 SKILL.md · env `TEAMWORK_SKILL_CHANGELOG_URL` 测试覆盖)· 抽「本地版本之后」各版 `## vX.Y · 标题` 行(新→旧 · 扫到 ≤ 本地即停)· prompt 加「本次升级包含」清单(cap 8 · 超出加共 N 版注)。
- **keep-5 断档识别**:扫完未遇到 ≤ 本地的条目 = 落后超出线上留存范围 → 加「(线上 CHANGELOG 仅存最近 5 版 · 更早变更见 git 历史)」注。
- **best-effort**:拉取/解析失败返 None · prompt 降级回原指针 · 绝不阻塞 bootstrap;up_to_date 路径零额外网络(只在 outdated 才拉)。emit 增机器可读 `changelog_titles`。
- 测试 +4(标题进 prompt 且 ≤ 本地不列 / 拉取失败降级 / keep-5 断档注 / up_to_date 不拉)· setUp 把 changelog env 指向受控 file://(防既有测试外呼真 GitHub)。

### 验证
- pytest 3 failed / 549 passed(baseline 3 · 净 +4)。

## v8.141 · claude -p MCP 隔离:--strict-mcp-config 零 spawn · v8.106 归因翻案(裸跑也拉项目 MCP)

> 用户:claude -p 是否支持 --allowedTools · 重点解决 MCP 卡死。答:支持(CLI 2.1.173 实测)· 卡死真因不是 --allowedTools。

### 实测(本地四组对照 · marker 文件法 · 毒 MCP 项目)
| 案 | flags | 项目 MCP 真 spawn | 结果 |
|---|---|---|---|
| C1 | 裸 `claude -p` | **True** | 5.4s OK |
| C2 | `--allowedTools Read` | **True** | 4.2s OK |
| C3 | `--strict-mcp-config` | **False** | 4.8s OK |
| C4 | strict + `--allowedTools Read` | **False** | 7.4s OK |

### 诊断:v8.106 归因翻案
- **裸 `claude -p` 也每轮 spawn 消费项目 .mcp.json 全部 server**(C1)—— 现行外部评审一直在拉火药库 · 只是 CLI 2.1.173 连接不阻塞所以侥幸不卡;卡死与 `--allowedTools` 无关(C2 同 spawn)· 真正变量 = 项目 MCP 被 spawn + CLI 版本连接行为(2.1.15x 阻塞 → 当年卡死)。
- 评审 prompt 自包含零工具 · 本就不该碰项目 MCP —— 修法是**隔离整类**而不是赌 CLI 版本。

### 改动(代码 + 测试 + 文档)
- **`_build_claude_review_cmd` 固定加 `--strict-mcp-config`**(不传 --mcp-config = 零 MCP spawn · 不碰登录上下文 · 无 --bare 认证回归)· 生产 argv 形态在毒项目实测 3.9s rc=0 零 spawn。
- 测试:2 处 cmd pin 更新 + 新 1(strict 必在 + --mcp-config 必不在 · 缺一不可)。
- standards 新 §11.7(对照表 + 翻案记录)· §一 claude 路径行 + state.py 两处 docstring 同步修正因果。
- **解锁备忘**:strict 隔离下 `--allowedTools Read` 实测安全(C4)· 未来 ARG_MAX 卡长 prompt 可走「短 prompt + reviewer 自己 Read + strict」· 当前保持零工具 inline。

### 验证
- pytest 3 failed / 545 passed(baseline 3 · 净 +1)。

## v8.140 · 评审「开始声明」可行化:RUNNING 心跳(harness)+ 首行 REVIEW-ACK 自证(模型)

> 用户(承 v8.139):能否在 prompt 注入 · 让评审模型开始运行时在同名 .log 声明开始 + 时间戳。

### 裁定:直写 .log 不可行 · 拆成两个可行层
- **模型写不了文件**:claude -p 零工具(v8.106 故意拔 —— --allowedTools 激活 agentic 栈 → 拉消费项目 MCP → 卡死 · 恢复工具 = 复活该 bug 类);codex 沙箱不保证可写。且「开始时」恰是模型还没起来的窗口(认证/排队/网络)· 谁都报不了。
- 诉求拆解:① 运行中活性(还活着么)→ **harness 心跳**;② 模型亲口确认「处理的是本轮」→ **输出首行回显**(prompt 注入 · 可行)。

### 改动(代码 + 测试 + 文档)
- **RUNNING 心跳行**(`_run_streamed_to_log` 增 heartbeat 线程 · 默认 60s · 0 关):报已等待秒数 + 已收字节 —— claude -p 完成前 stdout 0 chars 属正常 · pid 行到 END 行之间原本仍是盲窗 · 心跳让 tail -f 分清「生成中」vs「卡死」。
- **首行 ACK 自证**(`_ack_block` 注入 + `_review_ack_status` 验证):generated 路径 prompt 尾注入输出契约「第一行必须 `REVIEW-ACK <prompt-doc stem>`」(stem 自带 stage/model/UTC ts)· 头 200 字符回显即 verified(emit `review_ack`)· 缺失 → `ack_missing` **WARN 不 BLOCK**(遵从概率性 · 不可枚举);两引擎先拼后落 doc(审计=输入不分叉)· `--prompt-doc` override 原样执行不注入不验。无 liveness 作用(print 模式整体到达)· 价值 = 输出 ↔ 本轮 prompt **对应性绑定**(v8.136 防 stale 从输入侧门禁补到输出侧自证 · 回显进结果文件与 .log 留档)。
- 测试 +4(心跳盲窗 0 字节/0 关/ACK 块契约/验证三态 + codex 测试加 ACK 断言)· standards §11.6 补两层。

### 验证
- pytest 3 failed / 544 passed(baseline 3 · 净 +4)。

## v8.139 · 外部评审过程实时落盘:prompt-doc 同名 .log · START 行 harness 写 · 黑盒窗口可观测

> 用户:触发外部评审后完全黑盒 · 提议过程输出写同名 log · 第一行由评审模型自报已开始 + 时间戳。裁定:同名配对 ✅ · 首行改 **harness 写**(模型自报不可行也不可靠)。

### 诊断:v8.55 日志三缺陷 = 黑盒根源
- **跑完才写**:`_log_external_run` 在 subprocess.run 返回(或超时)后落盘 —— 运行中窗口(最长整个 timeout)磁盘零痕迹 · 黑盒恰是这段。
- **藏 ~/.teamwork + 独立时间戳命名**:与 feature 内 prompt-doc 不同目录不同名 · 无法配对 · 用户不知其存在。
- **stderr 死因等验尸**:鉴权失败/codex 升级提示/限流都在 stderr 早期出现 · 却要等超时后才可见;超时还返空 stdout(丢已收部分)。
- **首行模型自报不可行**:`claude -p` print 模式输出整体到达 · 模型「已开始」行不可能先到;挂死/认证失败时恰恰零输出;且把流程关切注入评审 prompt(遵从概率性)。时间戳可枚举 → 归脚本(框架哲学)。

### 改动(代码 + 测试 + 文档)
- **`_run_streamed_to_log` 取代 `_log_external_run`**:Popen + 双 reader 线程实时落盘 —— 发起即写 `[UTC] START` 行(harness 时间戳)→ `pid=` 行 → stdout 原样 + stderr 逐行 `[stderr] ` 前缀(死因秒级可见 · mtime=心跳)→ `END · rc · 耗时 · 字节`;超时写 `TIMEOUT` 行 + **保留已收部分输出**(rc=124);重跑 append 叠加不覆盖;日志 OSError 静默降级绝不阻塞评审。
- **同名配对律**:log = prompt-doc `.with_suffix(".log")` · 审计三件套同目录成组(输入 .md / 过程 .log / 结果 external-cross-review/)。**codex 路径补齐审计=输入**(prompt 落唯一命名 doc · 执行仍 argv inline · 对齐 v8.136 claude 路径)。
- **透出**:发起时 stderr 打印 log 路径(tail -f 可观察 · 不污染 stdout JSON)· emit 增 `process_log`(成功/失败都有 · 失败 hint 第一条改「查过程日志」)· prompt_doc 字段放开到两引擎。
- 测试:改 2(mock 执行器)删 2(v8.55 旧日志)新 6(首行 START 序/超时保留部分输出/append 叠加/无 log 照跑/两引擎配对)· standards/external-model-usage.md 新 §11.6。

### 验证
- pytest 3 failed / 540 passed(baseline 3 · 净 +4)。

## v8.138 · panorama_sync 变更判级:L1 节点内增量不暂停(WARN 留痕)· L2 结构变更才停

> 用户(case:PTR-F260611065743 panorama_sync):全景修改的暂停点是否有必要 —— sitemap 仅描述行更新 · AI 推荐理由自证「IA 不变 · 未发现跨 Feature 冲突」· 用户按 1 纯放行。

### 诊断:暂停粒度与触发粒度错配 · 「纯过场」活标本
- 暂停保护两件事:IA 权威变更需多方评审 · 跨 Feature 影响需 owner 协调。case 两条件均不成立且 stage 内已查明(冲突扫描零命中 + 无节点增删)—— 事实已知还停 = 上抛已知事实(v8.128/v8.132 同款判别:停不停看事实已知度)· 收获只有默认放行。PROCESS-LEDGER「暂停点 改:默」kill criteria 的第一个判例(改:默 = 0:1)。
- 根因:`--panorama-changed=true` 判据是「panorama 文件动没动」(文件级 · sitemap 描述列更新也必走本 stage —— ui_design 不许直改 sitemap);暂停语义是「结构变更/跨 Feature 冲突」(语义级)。**stage 该进 · 暂停不该一律停**。

### 改动
- **变更判级**(substep 3 · 受影响 Features 扫描后判 · 依据逐条写进 §协调结论):**L1 节点内增量** = 三判据全满足(① 无节点增删移/路由变化 ② 无设计 token/共享视觉基线变更 ③ 受影响 Features 零命中);**L2 结构变更** = 任一不满足 · 拿不准按 L2。
- **L1 不暂停(任何模式)**:add-concern WARN 留痕(复用 auto-skip 语式)+ 零暂停 digest(≤3 行:变更/判据/产物指针)+ 直接 complete;**L2 必停**照旧(auto_mode 跳过规则不变)。
- **物化**:summary frontmatter 必含 `change_level: L1|L2`(缺即 FAIL —— 判级决定停不停 · 级别必须留痕);`authorized_pause_point` 改条件式。深校验(L1 时 sitemap diff 真无节点增删)不可枚举(sitemap 格式各项目异)→ AI 判 + 声明审计 + LEDGER L1/L2 比例兜底。
- **判级反模式成文**:结构变更标 L1 逃暂停 = R5 违规同级;ui-design-stage 触发处加期望管理(`true` ≠ 必暂停 · 不必预判影响大小)。

### 验证
- pytest 3 failed / 536 passed(baseline 3 · 净 +2:change_level 物化 pin + 条件暂停 pin)。

## v8.137 · goal 确认前置「重点 review 指引」:六节照实抄导读 · 替你做的判断放第一节

> 用户:PRD 在 AI 评审后直接交用户确认 · 希望请求确认前最后输出值得关注和了解的点 · 方便重点 review。

### 诊断:出口缺导读(v8.120 流程目标的对偶)
- 入口已有「流程目标」校准「要做什么」;出口(substep 9)用户面对的是全员 APPROVE 的成品 PRD · 没有导读告诉他**哪里值得抽查** —— 尤其 AI 在评审循环里替用户做过的判断(REJECT/DEFER 的 finding)完全不可见。

### 改动(doc-only)
- **goal-stage substep 9 加「重点 review 指引」**(请求确认前 emit · 固定 6 节 · 每节 ≤2 行):① **替你做的判断**(REJECT/DEFER 的 finding · AI 判断替代用户判断之处 · 抽查性价比最高 · 放第一节)② 核心取舍(争议已裁决 · cite id)③ 范围收窄(Out of Scope 中用户可能预期在内的)④ 影响面 ⑤ 修订轨迹(哪轮评审驱动)⑥ 残留风险/假设。
- **反即兴约束**:六节全部照实抄自已落盘结构化产物(pm_response / PL-CHALLENGE / revision_history / Out of Scope / PM 自查 / §待决策项)· 空节显式写「无」不可省 · 反模式成文(复述全文 / 营销式总结 /「经多轮评审已完善」/ 无产物出处)。

### 验证
- doc-only · pytest 3 failed / 534 passed(零回归)。

## v8.136 · claude -p 链路三修:prompt-doc 每轮唯一命名(审计=输入)· 模板提取治双嵌 PRD · 显式 doc staleness 门禁

> 用户(case:PTR-F260611065743 三轮 external review):claude -p 总是出现各种问题 · 整体 review → 裁定保留 doc 优先 · 每轮 doc 名唯一 · 传入 doc 路径。

### 诊断:结构性事故链(手工修复不可能根治)
- **固定名缓存中毒**:round 1 走 inline fallback 后把 prompt 写进固定名 `goal-claude.md` 作「审计副本」(v8.106 保留);round 2 的 `if prompt_doc.exists(): 优先读` 把它当 v8.44 人工 doc 消费 → 评审 stale PRD v0.1;AI 手工删 doc → round 3 又写回 → round 4 必复发。审计产物成了无失效机制的缓存。
- **模板整文件替换双嵌 PRD**:fallback 拿 claude-agents/reviewer.md **整文件**(文档+模板混合体)做全局 replace —— 尾部「占位符说明」表里的 `{file_list}` 示例格也被灌入完整 PRD → prompt 含模板元说明 + codex 对照表 + **双份 PRD**(~400 行垃圾 · 加重长 prompt 卡)。
- v8.44「scaffold + 人工填 summary」推荐路径零使用记录 · 每轮都 fallback + WARN · 形同虚设。

### 改动(代码 + 测试)
- **每轮唯一 prompt-doc(用户方案 · 优于直接废 doc)**:`_new_prompt_doc_path` = `<stage>-<model>-<UTC时间戳>.md` —— 默认路径每轮**现生成**(模板 Prompt 主体提取 + inline 当前文件 → 写新 doc → 用它执行)· **审计 = 输入零分叉** · 旧轮留档不复用 · 随 feature 归档。
- **显式 `--prompt-doc` 保留优先** + **staleness 门禁**(`_prompt_doc_stale_reason`:doc mtime 必须新于全部待评审文件 · stale → FAIL with hint)。
- **模板提取**(`_extract_prompt_body`):只取「## Prompt 主体」fenced block 内文本做替换(占位符表/对照表永不进 prompt · `{file_list}` 替换点唯一)· claude 路径 + subagent 降级路径同享。
- scaffold-review-prompt 改唯一命名(覆盖冲突消失 · `--force` 降 no-op 兼容)· subagent 降级 doc 同步时间戳命名。
- 测试:改 3(路径唯一性 / scaffold 两轮两 doc 且首份不被动)+ 新 3(提取排除模板文档+替换点唯一 / 无标记回退兼容 / staleness 门禁三态)· test_state 196 全过。

### 验证
- pytest 3 failed / 534 passed(baseline 3 · 净 +2 · 零回归)· grep `_default_prompt_doc_path` 残留 = 0。

## v8.135 · 注入块加「Subagent 默认授权」:满足宿主工具契约的长期授权 · 授权管能不能 · R4 判据管该不该

> 用户(case:codex-cli 跑 teamwork goal external review):注入逻辑增加 subagent 使用声明 —— 用户明确授权在 Teamwork 流程中默认使用 subagent(PRD/Blueprint/Review cross-review · 并行探索 · 互不重叠实现子任务)· 无需每次另行确认。

### 诊断:宿主工具契约与 teamwork 流程的缝隙
- Codex 的 spawn_agent 契约要求 "user explicitly asks";teamwork 流程(external review / 多角色评审 / PL 隔离质疑 / 并行实现)预设用 subagent —— 每次等口头授权会卡住流程(尤其无人值守 auto/yolo)。授权的合法落点 = 宿主指令文件(工具契约读取处)= 注入块。
- 两个措辞修正:注入块三宿主共用(不能写死「Codex」→ 通用宿主表述);约束不复述 SKILL 已有纪律(防双源 · 只给指针)。

### 改动(doc-only)
- **host-instruction-injection.md 注入块新增「Subagent 默认授权(Teamwork 流程)」段**:用户明确授权(三宿主通用)在 Teamwork 流程中默认使用 subagent · 无需每次另行确认;适用枚举(各阶段 cross-review/多角色评审 · PL 对抗质疑隔离执行 · 并行探索 · 互不重叠 write scope 实现子任务 · 验证/测试 sidecar);约束仅指针(R4 判据 · worktree 内写路径 · 流转不外包 · 主对话整合)。
- 本仓 CLAUDE.md 实例同步(gitignored · 下次 bootstrap sync-drift 也会按模板刷新);consuming 项目在各自下次 bootstrap 自动获得。
- **SKILL.md R4 subagent 条款加授权指针**:授权已长期化 —— 解决「能不能用」;R4 判据(独立且够大)仍管「该不该用」· 防授权被读成「滥用许可」。

### 验证
- doc-only · pytest 3 failed / 532 passed(零回归)· 注入模板/CLAUDE 实例/SKILL R4 三处口径一致。

## v8.134 · 分层同构律:基建层共享包完全一致 · 页面层意图权威(四要素)· 共享基建改动须验全景编译

> 用户四轮推演(承 v8.133):镜像方式是否最合理 → mock 态全景提案 → 规划层不可纯文档(需最终视觉稿)→ 裁定分层同构 + 补「共享基建改动后 dev 结束须保证全景编译通过」。

### 推演与裁定(完整决策链留底)
- **v8.133 全量镜像律推到逻辑终点 = 双源死结**:一个「除数据层外处处必须相同」的镜像就是真实 app 本身 · 维护两份必须一样的代码正是框架反复消灭的反模式;且全貌要求意味着每次 ship 都要回灌镜像(spec 无此环节 · 权威必倒置)。
- **mock 态全景方案**(全景=真实 app mock 态 · 设计 worktree 内 mock-first)解了零翻译 · 但撞规划期约束(规划层需多方对齐的最终视觉稿 · 文字/草图不够 · 而规划期出真实 app 代码破 R6/worktree 纪律)+ 丢「多 future 合并浏览」能力 → 不采纳。
- **用户的第三条路**:同构承诺按「能否由结构保证」分层 —— 全镜像和废镜像都是错的。
- 顺带实锤:dev-stage §3 same-stack 还原段仍写「项目自身 /design/<page-id> 路由 diff」= 已废 in-app 旧模型残留。

### 改动(doc-only)
- **ui-design-stage 分层同构律**(替代数据层唯一差异律 · IA 镜像律保留):**Layer 1 基建层完全一致**(shell/架构/栈版本/组件库/主题 · ① 共享包优先〔monorepo workspace 包 · 两端依赖同一份代码 · 一致性由单源结构保证 · 零镜像维护〕② 不可抽包才版本锁定镜像+记豁免)· **Layer 2 业务页面层意图权威**(四要素:布局结构/交互流/状态/字段映射 = UI.md 既有段落 · 实现「重点参考」= 四要素必须对齐 · 像素/代码组织自由)· **权威时效**(设计权威至该页 ship 止 · 此后代码即真相 · 反模式:拿停更全景纠正已演化页面)。
- **下游编译契约(dev-stage 新 §3.5)**:共享基建两个消费者(真实 app + 全景)· feature diff 触及全景依赖的共享包 → dev-complete 前 worktree 内跑 preview-project build(exit 0)· 失败处置三分:机械适配顺手修(+UI.md 记录)/ 引发视觉变化走 --panorama-changed / 收回破坏性改动(改 API 者迁移所有消费者 · 同 Schema 影响分析责任模型)· 证据进 dev test evidence · ⏳ 物化 TODO(--panorama-build-exit-code 条件 evidence)· 自查清单 +1 项。
- **dev-stage §3 same-stack 还原重写**:废 in-app 路由 diff 残留 → 分层对照(L1 复用共享包不重写 · L2 四要素对齐非字节还原 · 设计变更不在 dev 顺手改)。
- **联动**:templates/ui.md(意图四要素 + 权威时效注)· designer(分层同构)· feature-planning Step 5(seed 基建层优先共享包)· 质量基线反模式更新(分层版)。

### 验证
- doc-only · pytest 3 failed / 532 passed(零回归)· 分层同构律/四要素/§3.5 五文件 grep 一致 · in-app 路由残留清零。

## v8.133 · same-stack 全景两律:IA 镜像(真实路由 + 首页设计稿)+ 数据层唯一差异 · 预览给页面直达 URL

> 用户(case:jdp console ingest-info-entry):same-stack 时预期设计稿与实现完全一致 · 区别只在数据层(mock);预览应给页面真实 path URL(如 :62706/xxxpath)· 不是把设计页顶在 / 上;/ 应是真实首页设计稿。相关 stage 描述是否有问题。

### 诊断:有问题 —— spec 亲手教 AI 给根 URL · 「全景」缺 IA 镜像这一半
- ui-design-stage § 预览写明「抓 PREVIEW_URL= 那行给用户 browse」(根 URL);preview.sh 模板注释同款;全文无「路由镜像 / 页面挂真实 path / `/` = 首页」任何要求 —— case 里 AI「未引入 react-router-dom(单页渲染不需要路由 · 有意省略)」是**照章办事** · 把设计页顶在 / 也合规。
- 「同技术栈」只字面要求栈名 · 未定义镜像范围:case 第一轮反馈(pnpm/antd 版本 / main.tsx 入口结构漂移)全靠用户人工抓 —— spec 缺「与真实实现差异只允许在数据层」的总律。
- sitemap.md 本就含路由(designer role:「IA 地图:层级/导航/路由」)—— IA 镜像意图在规划侧存在 · 但从未绑定到 preview-project。

### 改动(doc + 模板注释)
- **ui-design-stage 立两律**(same-stack 模型区):🔴 **IA 镜像律** —— preview-project 路由结构 = 真实 app(与 sitemap 一致)· 本次设计页挂真实 `route_path` · `/` = 真实首页设计稿 · router 属栈镜像必含(「单页不需要路由」= 漂移反模式);🔴 **数据层唯一差异律** —— 框架/版本/包管理器/入口结构/路由/组件库全镜像 · 差异只允许 mock 数据层 · 其他漂移修复或 UI.md 记显式豁免。
- **预览地址约定**:PMO 给用户的 URL = `PREVIEW_URL` + `pages_changed[].route_path`(页面直达)· 注明 `/` = 首页 · 多页给直达清单 · 把设计页渲染在 `/` 顶掉首页 = 违规。§5 暂停点决策参考 / preview.sh 模板注释 ×2 同步。
- **frontmatter 加 `route_path`**(same-stack 必填 · ui-design-stage 示例 + templates/ui.md):`panorama_file` 降级 static-html 必 / same-stack 可选。
- **联动**:roles/designer.md 镜像两律 + 直达 URL · feature-planning Step 5(全景 seed 即按真实路由组织 · router 必含)· 质量基线加 IA 镜像反模式行。
- ⏳ 物化 TODO:same-stack 时 route_path 必填校验(parse_frontmatter 不支持嵌套 list-of-dict · 需 raw 扫描 · 渐进)。

### 验证
- doc-only(+模板注释)· pytest 3 failed / 532 passed(零回归)· IA 镜像律/数据层唯一差异律/route_path 五文件 grep 一致(ui-design-stage / ui.md / preview.sh / designer / feature-planning)。

## v8.122 · MD review P1:frontend.md 瘦身 1684→166(guide 外迁)+ TDD 单源收敛 + 降级路径划清 + 数字宣称校验物化

> 用户:继续 P1(承 v8.121 全量 MD review 顺延项)。

### 诊断
- frontend.md 1684 行 · §二–§七 为教程式内容(选型对比/配置/示例)与 standards「must/must-not」定位不符 · subagent 默认加载即超载;且全文示例代码曾在一次历史格式清理中丢失全部**空括号 `()`**(`jest.fn()`→`jest.fn` · `() =>`→` =>`)· 文末悬空 ``` 破栅栏。
- §一「前端 TDD 流程」是 tdd.md(自称唯一权威源)的**未注册 fork**:4 步 vs 5 步(缺 VERIFY RED)· 示例腐坏 · tdd.md §七 引用约定表无 frontend.md 行。
- e1d12b2 清 v7 残留的同次事故还留 **7 处全角「Ｔ」脏标题**(tdd.md ×2 / adr.md ×3 / prd.md / common.md · v8.121 只修到 frontend/backend 标题 2 处)。
- review-stage「真超时重试失败 → 报因给用户」vs「异质不可用已重试失败 → 降级」边界未划清:持续限流超时归哪条两可 · AI 会在停报与降级间摇摆。
- v8.121 类数字宣称漂移(stage 数/版本徽章/gate 名)无物化校验 · 只靠人工 grep。

### 改动
- **frontend.md 瘦身 1684 → 166 行**:§二–§七 原文(决策树+示例)整体外迁新 `standards/frontend-guide.md`(按需查阅 · 不默认加载 · 头部声明历史损坏:箭头参数括号已批量修复 35 处 · 其余空调用括号待逐例修)· frontend.md 各节改硬规则 bullets +「📎 示例 → guide §N」指针 · 修文末破栅栏 · STANDARDS.md 注册 guide + 加载规则注明按需。
- **TDD 单源收敛**:删 frontend.md「前端 TDD 流程」fork(腐坏示例直接删 · 不外迁)· 改 1 段 cite tdd.md(§二 5 步 + §三 自检 · 前端差异仅 vitest 命令 + 组件测试先行)· tdd.md §七 引用约定表补 frontend.md 行。
- **脏字符清零(7 处)**:tdd.md「horizontal slicing（借鉴 mattpocock/skills tdd）」「NEVER refactor while RED（借鉴同上）」· adr.md 三条门槛 / 7 类列表 / 极简模板 · prd.md「Out of Scope（借鉴 …to-prd）」· common.md「调试日志规范（借鉴 …diagnose）」。
- **降级路径划清**:review-stage —— 串行重跑**仍**超时/空输出(环境性)→ 归入「异质客观不可用」走**显式降级**(合法继续 · 报因留痕);🔴 P0-154 禁的是「伪造/冒充/静默跳过」· 不是降级协议本身。客观不可用枚举两处同步补「持续超时·限流(串行重跑仍失败)」(review-stage + external-model-usage §11.5)。
- **数字宣称校验物化**:新 `tools/tests/test_spec_claims.py` 4 测 —— STAGES.md 索引 == STAGE_SPECS 全集 ·「N stage」宣称 == len(STAGE_SPECS) · README 徽章 major.minor == SKILL frontmatter(patch 不比 → auto-bump 免疫 · README 缺失〔安装副本〕skip)· 现行 md 的 cold_start_* gate 名必存在于 bootstrap/state 源码。负验证:regex 实测命中 5 处 stage 宣称 + 4 处徽章(非空匹配白过)。
- **bump 脚本(P1 项裁定不改)**:auto-bump 只动 patch 段 · 徽章语义 = major.minor → patch bump 不产生漂移;真实漂移向量 = **人工 minor bump 忘改 README** → 由上述 pytest 拦截(发版必跑)· 改 bump 脚本属误靶。

### 验证
- pytest **3 failed / 523 passed**(baseline 3 = scan-spec 既有 · +4 新校验全过 · 零回归)· 全仓现行 md/py「Ｔ」= 0 · frontend.md 1684 → 166 行 · guide 1554 行(§二–§七 原文零丢失 + 35 处箭头修复)。

### 顺延
- frontend-guide.md 示例**空调用括号**逐例修复(`jest.fn;` 类 · 已头部声明)· scan-spec-consumer 3 个 baseline failed 测试治理。

## v8.123 · 裁定删除 frontend-guide.md:通用教程不入库 · 知识归模型 · 规则已全在骨架

> 用户(承 v8.122):frontend-guide.md 是否有必要 · 或是否需要精简 → 委托裁定(「你觉得怎么处理合理」)。

### 裁定:删除(非精简 · 非保留)
- **消费者是 AI RD · 内容零增量**:1554 行中 90% 为代码栅栏(452 行通用决策树 + ~950 行示例)· 全是 Testing Library / MSW / Zustand / TanStack Query / WCAG / Vite / GH Actions 通用用法 = 模型训练数据常识;AI 需要示例时自生成的比腐坏样例(仍残 ~20 处空调用括号)质量高。
- **规范零丢失**:数值门禁 / 禁项 / 选型默认已 100% 在 frontend.md 骨架(v8.122 提炼)。
- **框架哲学对齐**:v8.114 三层律 teamwork 不 own 知识内容(防腐烂反向误导)· 通用教程无归属层 —— 项目特异归各项目 `DEV-RULES.md`(用户主权)· 通用知识归模型本身。精简成决策树版只把负资产变小 · 不解决归属。
- **可逆**:原文完整在 git 历史(v8.122 commit 8a76a43)。

### 改动
- 删 `standards/frontend-guide.md` · frontend.md 去 7 处 guide 指针 + 头部加「实施示例/选型教程不入库」哲学行(防未来被加回)· STANDARDS.md 去注册行 + 加载规则还原。
- 撤销 v8.122 顺延项「guide 示例空调用括号逐例修复」(随删除作废)。

### 验证
- grep 全仓 frontend-guide 引用 = 0(CHANGELOG 历史除外)· pytest 3 failed / 523 passed(baseline 3 · 含 4 项 spec 宣称校验 · 零回归)。

## v8.124 · backend.md 同款体检:TDD fork 收敛 + 通用示例删除 + Date.now 腐坏修复(规范主体保留)

> 用户(承 v8.123):后端规范也看下。

### 体检结论:与 frontend 病情不同 · 主体是真规范 · 不大砍
- 781 行中 §三 响应契约 / §四 日志门禁(承载契约字段的 ✅/❌ 对照示例)/ §五 迁移+FK 策略(单源)/ §六 版本管理 / §二 集成测试报告模板+失败处理 都挂着 teamwork stage/角色语义 → 保留。
- 病灶三处:§一「开发流程(Red-Green-Refactor)」是 tdd.md 的**未注册 3 步 fork**(缺 VERIFY RED/GREEN · 与 frontend 同款漂移);§二 两段通用 python 验证示例(检查项树已承载规则 · 示例还带 `.json[` 腐坏);§四 示例 **`Date.now` ×3 丢空括号**(同 e1d12b2 事故 · 此前扫描正则未覆盖 `now`)。

### 改动
- §一 fork → 1 段 cite tdd.md(后端差异仅 pytest / npm test / go test 命令)· tdd.md §七 引用约定表补 backend.md 行 · 保留覆盖率 >80% + 测试命名规范。
- §二 删两段通用 python 示例(检查项树保留)。
- §四 修 `Date.now()` ×3。
- 头部加载指引补 tdd.md + 「通用教程不入库」哲学行(注明边界:保留的 ✅/❌ 示例仅限**承载契约/门禁字段**的对照 · 区别 frontend 教程类全删)。
- 全仓腐坏复扫(`Date.now`/`.json[`/`jest.fn`/`Math.random` 缺括号):仅 backend.md 7 处 · 本版全清。

### 验证
- pytest 3 failed / 523 passed(baseline 3 · 零回归)· backend.md 781 → 719 行 · 全仓空括号腐坏 grep = 0。

## v8.125 · standards 优先级成文:DEV-RULES 为主 · teamwork 默认为缺省 · §三 API 规范挂优先级链

> 用户(承 v8.124):服务端 API 接口规范是否需要优先以 DEV-RULES.md 为主 · 没有再降级成现有规范。

### 诊断:对 —— §三 无优先级链 · 且覆盖注册处两套口径(错档)
- §三 API 规范写成绝对条款(「统一响应格式」「必须遵守」)· 既有项目自有 envelope / camelCase 时直接冲突(违用户主权);v8.119 已为 §五 迁移命名定过「① DEV-RULES → ② 默认」模式 · §三 没挂。
- backend.md 注册处不一致:§四 日志 / §五 FK(×2)/ §六 版本策略的覆盖条款写「以 KNOWLEDGE.md 为准」(4 处)· 而 dev-rules.md 模板边界表明文「强制开发规矩 → DEV-RULES.md;踩坑/客观约束(AI 沉淀)→ KNOWLEDGE.md」—— 格式/策略类覆盖被错档进 KNOWLEDGE。
- STANDARDS.md 无全局优先级声明 · tdd.md §二 Step 3 也只提 KNOWLEDGE。

### 改动
- **STANDARDS.md 加全局优先级**(根治):项目/子项目 DEV-RULES.md(用户主权 · 人维护)> standards 默认 —— standards 是「未规定时的缺省」不是法律;存量对外契约一致性优先 · 沿用时**提示用户**固化进 DEV-RULES(AI 不代写 · 模板红线);兼容既有 KNOWLEDGE 声明 · 新增覆盖一律 DEV-RULES。
- **backend.md §三 挂优先级链**:① DEV-RULES API 约定 → ② 存量服务已有一致接口风格 → 沿用(对外契约 · 同服务一致性 = 正确性 · 新接口不得自创风格)+ 提示用户固化 → ③ 全新/无约定 → teamwork 默认。📎 注明与 §五 migration「不读邻居」的区别:迁移文件名 = 内部惯例(坏样板不传染);API 响应结构 = 对外契约(消费方依赖)→ 存量在 ② 合法沿用。
- **覆盖注册处统一 DEV-RULES**(4 处 · 全部兼容既有 KNOWLEDGE 声明):§四 日志格式 / §五 FK 覆盖条款 + ✅ 条件行 / §六 版本策略。
- tdd.md §二 Step 3:「遵循 KNOWLEDGE.md 项目特定规则」→「遵循 DEV-RULES.md(强制规矩)+ KNOWLEDGE.md(项目事实/坑)」。

### 验证
- pytest 3 failed / 523 passed(baseline 3 · 零回归)· grep:standards 内「以 KNOWLEDGE.md 为准」独立口径 = 0(全部改为 DEV-RULES 主 + KNOWLEDGE 兼容)。

## v8.126 · 覆盖注册处收口单源:DEV-RULES 有则为准 · 没有按当前默认 · 去 KNOWLEDGE 兼容层

> 用户(承 v8.125):「KNOWLEDGE.md 声明为准」改为 DEV-RULES 口径 · 没有则按照当前规范。

### 裁定:覆盖声明唯一注册处 = DEV-RULES.md · 两级链(有声明为准 / 无声明按默认)
- v8.125 为平滑迁移留了「兼容既有 KNOWLEDGE.md 声明」层 · 用户裁定不要兼容层:单一注册处更干净 · KNOWLEDGE 回归纯「项目事实/踩坑」定位(dev-rules 模板边界表)。

### 改动(6 处去兼容)
- STANDARDS.md 全局优先级:兼容句 → 「覆盖声明唯一注册处 = DEV-RULES.md(未声明 → 按 standards 当前默认);KNOWLEDGE.md 不作为规范覆盖注册处 · 既有覆盖声明应迁入 DEV-RULES」。
- backend.md §四 日志 / §五 FK 覆盖条款 + ✅ 条件行 / §六 版本策略:去「兼容既有 KNOWLEDGE 声明」· 统一为「DEV-RULES 声明后以其为准;未声明按本节默认」。
- templates/tech.md FK 决策行示例:「KNOWLEDGE.md L{行号} 已覆盖默认」→「DEV-RULES.md L{行号}」。
- 不动(KNOWLEDGE 正确用途):common.md Gotcha 沉淀 / tdd.md「DEV-RULES(规矩)+ KNOWLEDGE(事实/坑)」分档 / backend §五 撞守卫后记 DEV-RULES/KNOWLEDGE(记坑)。

### 验证
- grep standards+templates+roles:「兼容…KNOWLEDGE」「或既有 KNOWLEDGE」「以 KNOWLEDGE.md 为准」= 0 · pytest 3 failed / 523 passed(零回归)。

## v8.127 · 仓库减重 55%:删 docs/archive + CHANGELOG-ARCHIVE 清空立「定期清空」制(历史归 git)

> 用户(承 v8.126 体量分析):docs/archive 都删掉 · CHANGELOG-ARCHIVE 清空一版内容 · 定期清空 · 其他先不动。

### 裁定
- 冻结历史的「冷库」职责由 **git 提交历史**承担(永不丢 · git log/show 可溯)· 工作区不再热存 16.3k 行不被读的内容(占仓库 55% · 每次装机同步)。

### 改动
- 删 `docs/archive/`(v8-redesign 00-MANIFESTO / 01-COMMAND-SCHEMA / 04-PAUSE-POINT / 05-LESSONS + DESIGN + change-request · 2,396 行)。
- `CHANGELOG-ARCHIVE.md` 13,867 行(v8.121 → v1 全部 293 条)清空 → 政策 stub · CHANGELOG.md 头部立规:keep-5 轮转 → 归档暂存 → **定期清空**。
- 重指/清理悬空引用 **34 处**:README×2(顺带修 :332 残留「最近 1 版」→「最近 5 版」)· SKILL×4(含路由表归档行删除)· FLOWS / STANDARDS / prepare / goal-stage 各 1 · roles ×8「设计宪法」指针 · 工具 docstring/注释 ×11(state / engine / ship / stage_specs / update)。
- `_v8_engine._render_pause_discipline` 渲染串「📖 详细」改指 **SKILL.md § R5(b)**(现行权威 · 原 04-PAUSE-POINT-DISCIPLINE 已清理)· 同步 `test_pause_discipline_v871` 断言(04 文件名 → R5(b))。

### 验证
- grep 现行 md/py:docs/archive / 00-MANIFESTO / 01-COMMAND-SCHEMA / 04-PAUSE / 05-LESSONS 实体引用 = 0 · pytest 3 failed / 523 passed(零回归 · 含改断言后的 pause 测试)· 仓库 md 总量 29,821 → 13,552 行。

## v8.128 · 排查先行律:根因未定的现象类输入先问题排查再定流程(治「猜测进 prepare 总览」)

> 用户(case:consuming 项目「ci 编译失败」):应该先诊断再给流程。

### 诊断:关键词路由跟「用户措辞」不跟「事实已知度」· prepare 总览写进未验证猜测
- 现行表「报错/挂了/500」直接 → Bug;「排查/查 log」才 → 问题排查 —— 现象类输入(ci 编译失败)被直接定 Bug · emit prepare:「代码现状」填了未验证假设(i18next 类型推导)· diagnose 才查出真因(ff326a74 path 类型加宽 · 4 调用点漏改 2)—— **命名/前缀路由/worktree 全押在猜测上**(真因在别的子项目就全配错)· 用户 review 被误导(中途反问「你排查到原因了么」)。
- diagnose-stage 自述「triage/prepare 读码只够判流程类型」—— 现象类场景连流程类型都判不可靠。

### 改动
- **prepare.md §2 立排查先行律**:现象类输入(报错/挂了/CI 失败/慢 · 无修复指令)且根因·影响面·归属未定 → 不定 Bug · 不 emit prepare —— 先问题排查(主对话 · 不进状态机)→ 排查闭合走 SKILL「Mode A/E 升级触发」暂停点(已验证根因 + 影响面 + 建议流程:转 Bug / Micro / Feature / 不动 / revert)→ 用户拍板 → prepare(排查结论 = 「代码现状」· 命名/路由据真因所在子项目)。**Bug 直入边界**:缺陷已指认(明确要求修复 · 现象+期望+位置已知)。判别题 = 「定流程所需事实是否已知」· 非「用户用了哪个词」。
- **关键词表两处收窄**(prepare §2 + FLOWS 识别列表):问题排查行接收现象类输入 · Bug 行加「仅当缺陷已指认」。
- prepare §0.5 反模式 +#7(现象输入未排查直接定 Bug + 总览填猜测)· §1.5.3「代码现状」加硬规则:**只写已验证事实 · 假设不得写入**。
- FLOWS 问题排查:用户选项补「转 Micro / revert 肇事 commit」+ 排查先行律;diagnose-stage 加**双入口**(②问题排查转入 → cite 结论复核不重查 · 重点落 BUG 报告 + 方案 R5 确认)。

### 验证
- doc-only · 关键词表两处口径一致(grep 复核)· pytest 3 failed / 523 passed(零回归)。

## v8.129 · 流程价值反思:ship2 后输出台账行 + digest(给仪式攒「该不该活着」的数据)

> 用户(承「teamwork 是否该存在」复盘):我们是否需要增加一个流程价值反思流程 · 在 ship2 后输出 → ok。

### 诊断:框架只有负反馈回路(出事 → 判例 → 加规则)· 没有正/零反馈(这环节这次拦没拦住东西)
- 规则只增不减(v8.0 以来 120+ 版首次系统性减法发生在 v8.121-127)· 仪式价值靠信念:多角色评审 self-talk 嫌疑 / 暂停点 all-default 率 / external confirmed 率全部无数据 · 「该不该砍」永远是辩论不是查表。
- 风险:反思流程自己变成新仪式 → 设计三条反仪式约束。

### 改动(doc-only · v1)
- **ship-stage.md §16**:ship-finalize 完成后 PMO 输出两层 —— ① 台账行 append 到 workspace `project-specs/PROCESS-LEDGER.md`(机器字段为主:实走 stages/时长/rounds/external 总采驳/角色真 finding/暂停点 改:默/bypass · AI 判断仅 2 格 · 照实抄不美化)② digest ≤10 行固定 4 问(拦住真问题?/纯过场?/流程新判例?/成本异常?)。
- **三条反仪式约束**:🔴 零新增暂停点(纯情报 · auto/yolo 照常)· 机器字段为主防 self-talk · 消费方指名(流程审视场景 + 年检 kill criteria:无新判例→仪式砍半 · external confirmed≈0→异质降可选 · 角色长期零真 finding→评审矩阵收缩)。
- **与既有 retros 划界**:`docs/retros/` = 业务/工程复盘(子项目级 · 知识层);PROCESS-LEDGER = 流程仪式价值度量(workspace 级)· 🔴 别混写(spec/模板双侧声明)。
- **豁免**:Micro 只记台账行不出 digest(最轻通道不加仪式)。
- 新 `templates/process-ledger.md` · 注册三处:templates/README 表 · conventions §13 project-specs 清单 · SKILL 路由表。
- ⏳ 物化 TODO(v2):ship-finalize 自动抽机器字段 emit ledger_row(AI 只补判断格)。

### 验证
- doc-only · pytest 3 failed / 523 passed(零回归)· 注册三处 + spec/模板分工声明 grep 一致。

## v8.130 · 台账采集时机修正:ship2 归档删目录后取数断粮 → 两段式(planning-backref 采写 · finalize 后 emit)

> 用户(承 v8.129):ship2 之后相关的产物都压缩了 · 你还能找到统计信息么。

### 诊断:对 —— v8.129 v1 设计两个缺陷被一问暴露
- **取数断粮**:§16 原定「finalize 完成后输出」· 但 §15 归档已把 state.json / REVIEW.md zip 进 `_archive/<id>.zip` 并删原目录 —— 数据没丢(zip 自描述 · `unzip -p` 可取)但取数高摩擦 · AI 大概率跳过或凭记忆填(违「照实抄」)。
- **写入无载体**:finalize 后 merge_target 全程只经 MR · 此时 append 台账行 = 脏文件无合入载体。

### 改动(doc-only)
- **§16 改两段式**:① 采集 + 写台账行 = ship2 step 5 `planning-backref` 暂停点(state.json/REVIEW.md 尚在磁盘 · 取数零成本)· 台账文件加进 `--planning-artifacts` 随**同一收尾 MR** 合入(`_resolve_planning_artifacts` 只校验「存在+仓内」· 已核代码)② digest = finalize 全部完成后 emit(从已写行渲染 · 时长口径 = init → ship2 暂存 · 表内统一)。
- **兜底成文**:漏写 → `unzip -p features/_archive/<id>.zip <id>/state.json` 不落盘取数 · 补行随下次任意 MR。
- v2 物化 TODO 同步:ship-finalize 在 planning-backref 暂停点 emit ledger_row 草稿(漏写不可能)。
- 同步措辞 4 处:templates/process-ledger.md 写入时机 · conventions §13 · SKILL 路由表 · templates/README。

### 验证
- doc-only · `--planning-artifacts` 路径校验已读码核实(存在+仓内即可)· pytest 3 failed / 523 passed(零回归)。

## v8.131 · 框架自省台账 RETRO-LEDGER:发版三件套 · 框架反思归框架仓(永久层)

> 用户:是否每次流程完善后写一段 teamwork 的问题/优化点/有用的地方/反思 · 记到 teamwork skill 子目录 —— 全项目总结汇一起 · 框架自身的东西不适合放项目目录。

### 诊断:框架自省无持久层 · 正反馈无归档处
- 框架反思散落 chat(session 结束即丢)与 CHANGELOG(keep-5 轮转 + 归档定期清空 · **故意易逝**);「有用的地方」(正反馈)更是哪都没记 → 年检只剩坏消息可查。PROCESS-LEDGER(v8.129)是项目侧的 · 框架侧缺对偶。

### 改动(doc-only)
- 新 `docs/RETRO-LEDGER.md`(框架自省台账):一行一版 · 6 列(版本/来源 case/问题/优化点/**有用的地方**/反思)· 单元格 ≤1 行 · 不复述 CHANGELOG · **永久**(超 ~500 行年检主题化压缩 · 原文 git 可溯)。
- **三层分工成文**:CHANGELOG = 单版细节(易逝)· PROCESS-LEDGER = 项目侧环节价值 · RETRO-LEDGER = 框架侧自省蒸馏(永久)。
- **发版三件套**(CHANGELOG 头部立约 · 同 commit):CHANGELOG entry + RETRO-LEDGER 1 行 + 版本 bump。
- **消费方指名**:年检/存在性审视直接读表;框架改进 session 动手前读最近 10 行(防重复踩坑)。
- **回填种子**:本 session v8.120→v8.130 共 11 行 + v8.131 自身 = 12 行。

### 验证
- doc-only · pytest 3 failed / 523 passed(零回归)。

## v8.132 · goal stage 质量改造:调研前置 + PL 对抗质疑 + 三闸早问门 + 全员通过物化(产高质量业务目标 PRD)

> 用户:review goal stage 逻辑是否合理(目的:产高质量业务目标 PRD)→ 追问早问门会否纵容上抛/有无调研前置 → 追问对抗性讨论(PL 质疑)→ 确认。

### 诊断(review 实锤)
- **结构 4 弱点**:业务目标事实输入薄 · 校准点全在最后(锚定:全员 APPROVE 包装后 step 7 才见用户 · v8.128 镜像);PL「审视」非「质疑」· 无人负责杀前提(同上下文切帽子 = 鼓掌效应);external@goal 无业务上下文(留台账裁决);AC 规模无反压。
- **漂移/死门禁 6 实锤**:goal-complete **不校验 verdicts**(全 NEEDS_REVISION 也能过 ·「全员通过」纸面纪律);authorized_pause_point「Substep 6」vs 文档 7 步(编号错位);`_check_prepare_completed` 死门禁(恒真 · hint 引用 P0-12 已删命令);PRD-REVIEW 模板内嵌旧 4 角色叙述段(RD/Designer/PMO)+ Round schema「删 pl/pmo · architect 不参与 prd」与现行 5 角色三方矛盾 · 顶层 reviewers/verdicts 字段缺失(machine schema 不满足代码门禁!)· PASS 系词表漂移;章节名两套(§需求背景/§用户场景/§边界 vs 模板 §背景/§用户故事/§Out of Scope);模板「PM 起草规范 checklist(单源化)」含起草前必读代码现状 · 但 cite 清单不路由 = writer-only。

### 改动
- **代码物化(+2 门禁 · −1 死门禁)**:`prd_verdicts_all_pass`(verdicts 全 APPROVE/SKIP · frontmatter 原文块级解析兼容行内{}与缩进 map · 旧 PASS 词表判 FAIL 强制 canon)· `pl_challenge_present`(角色含 pl 时 PRD-REVIEW 必含 PL-CHALLENGE · 敏捷需求无 pl 自动放行)· 删 prepare_completed 死门禁 · pause point 改「Substep 9 + 条件:Substep 4 早问门」· brief 同步 9 步。**+9 测试**(行内/缩进/SKIP/旧词表拒/缺失/无 pl 放行)。
- **goal-stage.md 重写为 9 步五层防线**:调研先行(事实层 · 四类:代码现状/KNOWLEDGE FA·Pref·OoS/GLOSSARY/上游规划 = 早问门入场券)→ 起草(模板单源 + AC>10 规模反压)→ **PL 对抗质疑**(前提层 · 质疑五问:价值前提/问题定义/范围最小化/上游对齐 cite/复活检查 · Q1 命中 subagent 隔离不喂起草心路 · PL-CHALLENGE-{n} 产物)→ **三闸早问门**(用户主权层 · 条件暂停:调研穷尽/主权判别〔上抛事实类=R5 违规〕/格式四件套+≤3+全带推荐 · auto 不停转 §待决策项+WARN)→ 多角色评审(完备性层)→ 用户确认(裁决层)。
- **模板对齐(464→388)**:删旧 4 角色叙述段 · role 枚举对齐现行 5 角色 · 顶层 reviewers+verdicts 补齐(满足代码门禁)· 词表统一 APPROVE|NEEDS_REVISION|SKIP · category +premise-challenge · 调研四类入 checklist ·「子步骤 3 RD 评审」×3 → substep 5 多角色。
- **联动**:roles/pm.md(调研/早问门/对抗自查)· roles/product-lead.md(质疑五问职责)· prepare Q1 命中后果 +「PL 质疑 subagent 隔离版」· 对抗有效性观测进 PROCESS-LEDGER(PL-CHALLENGE 采纳率 · 早问门 改:默)。

### 验证
- pytest 3 failed / 532 passed(baseline 3 · +9 新全过 · 零回归)· 模板旧口径 grep 清零(PASS 词表/旧角色段/删 pl 注释/子步骤旧编号)。
