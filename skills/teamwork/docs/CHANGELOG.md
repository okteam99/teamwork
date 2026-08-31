# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.348 · 本地测试与 MR CI 同构性对照(实证 case)

> 用户看 case 问「测试流程是否需要约束、覆盖 CI 要检查的项目,避免问题遗漏到 CI 阶段」。
> case(aon-main DEV-F260830125314):TEST-REPORT 只记录 `cargo check -p aon-api-gateway`(只验编译),而 MR CI 跑 `cd services && cargo clippy --locked -- -D warnings` —— 一条 clippy 漏到 CI 才炸,MR 窗口期多烧一整轮。
> 🔴 **决定修法的关键细节**:那个 AI **试过** grep CI 配置,猜的是 `.gitlab-ci.yml .gitlab/ci/*.yml` → 返回空;真配置在 GitLab include 进来的 `infra/ci/api-gateway.yml`,于是空结果被当成「没有 CI」。**这不是偷懒,是不知道去哪儿找** —— 该由机器端清单(v8.323「数据算好别让人誊抄」),不是让每个 AI 自己猜路径。

### 变更
- **`state.py ci-commands --root <worktree>`**:扫本仓 CI 配置(GitLab 根 + `.gitlab/**` + include 常见位 `infra/ci/*` · GitHub `.github/workflows/*` · CircleCI / Azure),只取 `script`/`run` 块里的**门禁类**命令(编译/测试/静态检查),给 `文件:行 + 命令`。部署/发布类不收(不是本地该复现的);vendor/worktree 跳过。
- **test-stage 规则 2.9 + TEST-REPORT §2.5**:逐条标注 **本地已跑 / ⚠️ 跑不了(为什么)/ — 不适用**。
- 🔴 **刻意的边界:不要求本地跑 CI 全集**(有些 job 要 infra 凭据、有些太慢,强行复现是纯税)—— 要求的是**看过、并对每条给出处置**;🔴 **「跑不了」必须显式列出**,那就是「已知会在 CI 才发现」的清单,写出来风险才可见(零也显式)。
- **载体在消费时点**:test-start brief 自动带这条 + 「别自己猜 CI 配置路径」的 case 教训(v8.324「complete 会拒的必须 start 可见」同律)。
- **与 ship 侧分工写明**:本条是**防**(进 CI 前先对照),v8.345 的 CI 归因是**治**(真红了归因 · 自己引入的直接修)。

### 测试
`test_ci_parity_v8348.py` 13 条:GitLab include 布局(= 本 case 的形状)· GitHub `- run:` 列表项(初版正则漏了整段)· YAML 键不许当命令 · 部署类不收 · 给出文件:行 · 无 CI 配置给可写处置而非报错 · vendor/worktree 跳过 · CLI 双路径 · 三处载体 · **ship 侧归因不受影响**(防与治不重叠)。真仓库复验:aon-core 14 文件 / supersdk 15 文件,残留 YAML 前缀 0。全库 1607 绿。

## v8.347 · await-merge 后台化会自己退出(实证 case)

> 用户看 case 问「监控为什么自动退出了」。答案不是崩溃也不是超时,是**设计上的单轮上限**:默认 `18 轮 × 30s = 9 分钟`,用尽 emit `WAITING` 后 `sys.exit`(`emit_json` 每条都自带退出)。
> case(aon-core SVC-CORE-B260831064524):消费 AI **按 spec** 用 `nohup ... >> /tmp/` 后台启动 —— WAITING 里那句「AI 应自动重跑」进了没人读的文件,监控就此永久结束;人几分钟后才点合并,ship2 只能手动补跑。

### 变更
- **默认窗口按「等的是什么」定**:等人去平台点合并是**小时级**(框架自己的原始痛点数据是 132h 长尾),9 分钟差三个数量级 → `--max-checks` 默认 18 → **120(≈1h)**。
- **`--until-final`**:自己循环到**终态**才退(MERGED / CLOSED / CI 归因到自己),不受轮次上限约束 —— 后台跑正是这个模式该覆盖的用法,不再把续等义务甩给调用方。
- **后台化警告**:未开 `--until-final` 且 `stdout` 非 tty → WAITING 显式点出「你把我 nohup 了,但我不会自己续等」并给出口。前台跑不噪。
- **三处载体同步**(漏一处就复发):ship-stage spec 的投递次序、push emit 里给用户抄的命令行、用户卡片的「监控」行 —— 全部带上 `--until-final`。🔴 **根因其实在 spec**:它明确写着「先后台启动」,而命令从没说过自己必须在前台跑。

### 这条教训的形状
**载体缺口可以是运行姿态造成的** —— 不是措辞糊(v8.302 那族),而是同一句话在前台成立、在后台不成立;spec 让它后台跑,承诺就失去了接住它的东西。

### 测试
`test_await_until_final_v8347.py` 10 条:默认窗口小时级 + CLI 同步 · 非 tty 真跑一次拿 WAITING 并断言警告点出机制与出口 · 前台不噪 · until-final 忽略轮次上限且末轮照 sleep · **自续等不许变成永不退出**(三个终态仍在)· 三处载体同步 · why 记成「运行姿态」不是「措辞」。全库 1594 绿。

## v8.346 · 年检 P0 三修:数据推翻直觉(aon-core / supersdk / aib · 289 行台账)

> 用户:「结合 aon-core / supersdk / aib 做一次年检」。三项目全在 v8.344.1 · 台账 16 列 canonical · 样本 210/71/8。
> 面上数据:待用户占 wall-clock **61%**(AI 自主 18.6%)· 协调开销轮 **30%**(712/2373)· review/test >1 轮 **55%** · 起草可预防 **70.5%** · external 采纳率 **82.3%** · 暂停点「改」**20.6%**(不是橡皮图章)。

### 变更(三条 P0 全是用数据改框架自己的设计)
- **P0-1 降档砍错了路 → 单路默认 architect 改 external**:逐 stage 真 finding 产出 **ext > arch**(goal 275:178 · blueprint 76:57 · review 87:53 · 总量 1546:735 = **2.1×** · 采纳率 82.3%)。v8.341-343 把 tiny/lite/medium 的单路全配成 architect,理由「异质冷审边际收益压不过协调开销」是**推的、没有数据支撑** —— 砍掉的恰是产出最高的一路。改后 external 还天然满足「单路必错开模型」不变式。**路数不变**(仍单路),换的是留哪一路;full 双路不动。
- **P0-2 worktree 巡检挂到会跑的命令上**:v8.325 把「不覆盖存量 `worktree_cleanup=ask`」的补偿设计成「每 session 报告」,但 `prune_merged_worktrees` **只在 bootstrap 调** —— 而 v8.322 **刚刚**证明 bootstrap 在积灰项目上二十天不跑(同一条教训写在它前面一版,又踩了一遍)。实测:aon-core 14 个 worktree / **18G**;supersdk/aib 各 0。现挂到 `main-sync`(= feature 刚合并完、且在主工作区能看见全部 worktree 的那一刻),bootstrap 那条保留。
- **P0-3 复发防御清单接上写入端**:v8.278 把清单接到了**读取端**(dev brief 每次让 AI 先读),写入端从来没有动作 —— 可预防率常年 70.5%,而清单 aon-core **0 条** / aib **0 条** / supersdk 3 条。现在:`review-preventability` 在 preventable>0 时**出现成骨架**(v8.323「别让人誊抄」形状);`archive` 加 `defense-list` 验收门(v8.253「自由声明必有验收门」形状)· 例外走 `--no-defense-entry` 留痕。

### 一条自我修正
P0-2 初诊断是「框架默认改了、存量配置没迁」,据此写了 localconfig 缺省补齐 —— **查 git 后发现是错的**:v8.325 有意不覆盖存量 `ask`(代码注释写着)。已回滚该改动,按真根因(报告挂在不跑的命令上)重做。

### 测试
`test_annual_audit_v8346.py` 15 条:单路留高产那路 + **路数没被偷偷加回去** + full 不动 + 静态表与维度表同口径 + **判据带实测数字**(否则下一版又凭直觉改回去)· 巡检不炸收尾 + why 记住重复的错 + bootstrap 入口保留 · 骨架只在真有可预防时出 + 门只在 preventable>0 时响 + 例外留痕。既有 5 处 architect 锁按年检结论重锚。全库 1584 绿。

## v8.345 · CI 失败归因:自己引入的直接修(用户拍板)

> 用户:「ship1 产出 MR 后监控合并的同时检查是否有 pipeline 失败,如果是自己引入的,直接修下。」
> v8.340 已经在查 CI,但停在**任何红都退出**去找修复口 —— base 本来就红时,这会把 AI 支去修它没弄坏的东西。这正是 dev/test 早已解掉的「base 即红」坑,那边用**差分基线**区分「新增回归」与「预存在失败」;本版把同一个形状搬到 CI 上。

### 变更
- **归因层**(`attribute_ci_failures` 纯函数 + `_base_branch_failing` 查 base 分支近期 CI):MR 失败项逐个对照 base —— base 同名 check 也红 → `pre_existing`;base 绿 → `self_introduced`。
- **归因决定动作**(本版实质):**自己引入 → 中断等待、直接修**(走 v8.339 的 MR 窗口期修复口 · **不问用户是否要修** —— 修自己弄坏的东西不是用户主权,是收尾的一部分);**base 预存在 → 不中断**,回显一行继续等合并(别去追别人的账)。
- 🔴 **查不到 base 归到「自己引入」是刻意的保守偏置**:代价不对称 —— 把别人的红当自己的 = 白看一眼;把自己的红当别人的 = 把坏的合进去。与 `test-baseline`「不在基线里就算新增回归」同口径,**不是**「查不到就放行」。
- 对照分支默认取 `state.merge_target`,`await-merge --base <branch>` 可覆盖;push emit 同步带归因(只有归因到自己才给修复口)。绿/pending 不查 base(不为没发生的事付一次网络往返)。

### 测试
`test_ci_attribution_v8345.py` 16 条:归因四象限 · 保守偏置有理由不是断言 · 默认动作是修且不问用户 · 升级边界(修不动才升级)· await-merge 只对自己的红中断 · push emit 归因 · 红时才查 base · spec 双分支 + 点名复用的形状。v8.340 三处锁按收窄后的语义重锚(「任何红退出」→「自己引入的才退出」· 实质「不傻等 CI 红」不变)。全库 1569 绿。

## v8.344 · 子代理禁问用户:问题回路收口主对话(用户拍板)

> case(Grok 宿主消费现场):写测试用例的子代理调宿主的 ask_user_question,把「登录回跳测试写在哪个文件」直接弹到用户屏幕 —— 纯实现细节,设计上永远不该到用户面前。用户拍板:「子代理/subagent 的问题由主对话自行处理,无需找用户确认,只有主对话判断需要用户确认的才交给用户确认」。
> 盘点:回路早就有(NEEDS_CONTEXT → 补上下文重派;stage brief「Substep 中间禁 AskUserQuestion」),但两个口没封:①暂停点纪律管的是**主对话**,子代理侧没有**对着工具名**的红线 —— 对没带全量 context 的执行路径,别处的规则等于不存在(「模式承诺 × 动作点载体」又一格);②派发 prompt 没要求带禁问句 —— 读过规则仍会漏,义务要寄生在必写载体上。

### 变更
- **agents/README §二 新红线(单源 · 对着工具名)**:子代理禁止调用任何「向用户提问/确认」类工具(`AskUserQuestion` / `ask_user_question` / 各宿主变体)—— 缺信息/拿不准 → 写进返回结果(`NEEDS_CONTEXT` + 缺什么)。**主对话二分**:实现细节(测试放哪 · 命名 · 用哪个函数)→ 自答后补上下文重派;真用户主权(偏好/业务取舍/外部事实 · 判据沿用早问门闸 2)→ 按 R5 编号选项 escalate。
- **派发载体寄生**:引擎 `DISPATCH_TIER_REMINDER` 加一行 —— 派发 prompt 必带禁问句,**与 Meta 首行声明同寄生一处**(不另立「记得写」的孤立义务)。
- **SKILL 一行 cite**(❌ 非 🔴 —— 密度门 count < 55 恰好顶满,按判例新增用 ❌)。
- 主对话侧既有纪律不动(两条规则互补不重叠:那条管主对话 substep,本条管子代理)。

### 测试
`test_subagent_no_user_question_v8344.py` 14 条:红线对着工具名锁(行为式表述糊得过、工具名糊不过)· NEEDS_CONTEXT 路由 · 拍板原文入规 · 主对话二分显式(否则红线只堵子代理,主对话原样转抛 = 问题换出口)· 派发载体寄生 + case 实证 · SKILL cite + 密度门 · 既有回路不动。全库 1553 绿。
