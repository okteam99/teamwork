# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

