# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。

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

