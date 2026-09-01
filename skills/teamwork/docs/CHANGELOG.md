# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.349 · YOLO 两段式:待确认项攒在隔离分支(用户拍板)

> 用户拍板:「yolo 合入 staging 前需要有风险总结文档,每个 feature 合入时在 yolo 目标分支记一下待确认信息,留到 yolo 分支合入 target 分支时确认。yolo 必须先合入目标 yolo 分支,`yolo/` 开头的。」
> 事故背景(协议 v1.0 强制 header → 存量调用方全 400 → **线上请求归零**):AI **识别到了**风险(旧调用方会 400)、**写进了文档**(Bug 影响评估 + MR 风险清单),但**文档是终点** —— 没有任何通道能把「写下来的风险」变成「必须停的等待」;那条 Bug 走的正是 yolo,`diagnose` 方案确认被自动跳过。

### 变更
- **准入收紧**:yolo 的 `merge_target` 必须是 **`yolo/` 前缀的隔离分支**。v8.63 只挡了 main —— 但 **staging 也不行**(它常是生产前最后一站,事故正是从那儿出去的)。`init-feature` 与 `set-mode` **双入口同守**(否则「先普通启动再切 yolo」是现成的绕过口)。
- **① feature → `yolo/*`**(自动):`archive` 必填 `--yolo-risk`(风险总结/待确认项 · 无则写「无 · 一句为什么无」)+ 可选 `--yolo-breaking`,记一行进该分支的 `YOLO-PENDING.md`,**随归档 commit 原子合入**(留在本地 = 合过去的分支上没有它 = 等于没记)。
- **② `yolo/*` → 真 target**(**人工**):新命令 `state.py yolo-promote --root <checkout 了 yolo/* 的工作区>` 把攒下的**全部**待确认项摆出来(破坏性的**单独计数**、不淹在总数里)· 用户逐条过目后 `--confirm-all` 落痕再合。🔴 它**不代替用户点合并**,只保证「合之前摆到台面上过」。
- ❗ **可判问句**(填 `--yolo-breaking`):**今天能成功的请求 / 调用,明天会失败吗?**「不知道有没有这类调用方」= **当作会**(代价不对称:把没事当有事 = 多看一眼;把有事当没事 = 线上归零)。

### 设计要点
**隔离分支不是多一道墙,是待确认项的落脚处** —— 零 stop 不等于零确认,只是**把确认延后并批量化**。这保住了 yolo 的价值(无人值守跑完),又给「识别到的风险」补上了此前完全缺失的**升级通道**。

### 测试
`test_yolo_two_stage_v8349.py` 19 条:前缀判定(staging 被拒 · 不只是 main)· 双入口同守 · 主分支门仍在前(报错更具体)· 台账追加/幂等/表头回填/why 写在台账上 · promote 列出待确认且破坏性单独计数 · next_action 问三槽(现存调用方/灰度/回滚条件)+ 第 2 项恒「继续讨论」· confirm-all 可验 · **promote 不含 merge** · 台账随 archive commit · 门文案含可判问句与保守偏置 · spec 三载体 + 🔴 密度门。既有 9 条 yolo 用例按新约束更新(目标分支改 `yolo/*`)。全库 1626 绿。

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
