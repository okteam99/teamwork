# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.318 · scratch 清理前移 ship1:治 worknode 141GB 堆积

> 实证(worknode · Docker-in-Docker):`/tmp/teamwork` 独占 **141GB**,单 feature
> SRUN-F260810160028 达 **78GB**。用户:feature 结束时是否有清理临时文件?
> 追加拍板:**按理 ship1 阶段就应该清。**

### 回答:设计上有,但两条通道在 worknode 形态下都够不着

| 既有通道 | 为什么没救到这个 case |
|---|---|
| ship2 `tmp-cleanup`(verify-delivered 后整树删) | **session 常在 ship1 交 MR 后结束/换机** —— ship2 根本不在积灰的那台机器上跑 |
| bootstrap TTL 7 天兜底 | **时间判据救不了空间问题** —— 7 天窗 × 78GB/feature,窗内即可打满磁盘 |

### 修(用户拍板:ship1 即清)

- **push 成功即清**(主时点):`ship-phase --action push` 记录成功后,工具顺手删
  `${TMPDIR:-/tmp}/teamwork/<feature_id>/` 整树 · emit `scratch_cleanup`(含 pruned_bytes)。
  依据:此刻测试/构建证据已入 state.json,scratch 无对账价值;**MR 窗口期撞冲突回炉需
  冷编 = 接受的代价**(磁盘占用 > 增量缓存)。
- **放弃即清**:`close-unmerged --abandon` 同步清(不会再回炉);暂时关闭(可重开)**保留**
  增量缓存(重跑 archive→push 免冷编 · TTL 兜底)。
- **ship2 `tmp-cleanup` 转幂等兜底**(ship1 漏清 / legacy in-flight)· bootstrap TTL 继续扫历史孤儿。
- 回收口径从「双通道」改「三通道」(common §六 · ship-stage §4 同步)。

### case 里另一个值得留意的点(不动 · 记录)

141GB 含多个 feature 目录 —— 除主时点缺失外,单 feature 78GB 说明该项目构建产物本身巨大;
in-flight feature 的 scratch 是**有意保留**的(串行 stage 复用增量编译),本版不加大小门 ——
若后续 in-flight 单体也失控,再议按体量 WARN(观察项)。

## v8.317 · 复杂度信号 1 收窄:部署单元 → git 仓库(三载体统一)

> 实证(matrixpower · Published-Model-Discovery):前后端联动小改(platform-api 目录规则 +
> Console 表单必填)触发复杂度门,推荐先做 Feature Planning —— 用户选 2 纠正后问:
> **复杂门禁是怎么判断的?**

### 机制回答 + 门自己的问题

判定链:关键词初判 → §2.1 五信号扫描 → 命中任一强制 emit 升级暂停点(模板固定推荐 Planning)
→ 用户可选 2 收敛单 feature(门是「必须问」不是「必须拆」)。本 case 命中信号 1。

但查下来是**三载体两口径,权威那份恰好过宽**:判定权威 prepare §2.1 写「跨独立**部署服务**」
(例子含「独立部署单元:后端 + 前端 + 管理后台」),而 planning-check emit 与 feature-planning §0
写的是「跨**仓库**联动」。AI 跟了权威载体 → monorepo 里两个独立部署的服务也命中。

**部署拓扑不影响一个 feature 装不装得下** —— 真正的承载边界是 git 仓库:worktree 是仓库级、
MR 是仓库级,同 repo 全栈改动一个 worktree 一个 MR 原子交付(本 case 用户选 2 后实际发生的事,
且 AI 正确按「业务交付宿主」定了 CONSOLE 前缀)。旧口径下 monorepo **每次前后端联动都多付一轮 1/2 选择**。

### 修(用户拍板:收窄为跨 git 仓库 · 三处统一)

- 信号 1 = **跨独立 git 仓库(≥2 repo/origin)** —— 一个 worktree / 一个 MR 装不下,单 Feature
  状态机**真**承载不了;🔴 **同 repo 内跨子项目 / 多独立部署单元不计入**(一个 worktree 原子交付 ·
  照样一个 feature · 交付宿主定前缀)。
- 两个接盘点名:规模由「影响 ≥2 BL」信号兜 · 部署协调由 WS「跨子项目方向(provider 先于 consumer)」串行约束管。
- 五处统一口径(prepare §2.1 / SKILL 警觉锚点 / feature-planning §0 / state.py 两处 emit)· 旧口径清零(测试锁)。
- 暂停点模板推荐写死 Planning **保留**(用户选):收窄后真命中的基本是跨仓库大变更,写死反而合理。

### 顺带回答:判信号时有调研现状吗?

**有,强制**:§1.7「看过再判」—— 流程类型判定前必做 30 秒侦察,证据填 `prepare-check` 的
`triage_evidence` 槽(**空着不给判** · 机器校验);§1.5.3 可选深挖。本 case 里 AI 真做了
(读了表单组件、grep 校验逻辑,暂停点里「已核实的变更点」甚至发现「可选」只是 AntD 必填标记
未声明的视觉问题)—— 调研质量没问题,问题只在信号口径。

## v8.316 · WS 总览加「大白话目标」列 · 「子项目」改「涉及子项目」

> 用户(附 WS-11 截图):ws 文档模版改下,拆出的 feature 加一个大白话目标列;子项目改为涉及子项目。
> 截图实证:总览表「功能」列是技术短语(「SuperRun 数据库连接注入」)—— 扫一眼看不出
> 每条 feature 做完后**谁能干什么**;「子项目」单数列名与 v8.314「可跨子项目」语义已不符。

### 先做了一次概念合并(单名防漂)

v8.314 昨天刚立的「交付物」槽(这条单独上线后谁得到什么)与本次要的「大白话目标」是
**同一个概念** —— 一个概念两个名字必漂(五维/六维双副本是现行判例)。全链统一为**大白话目标**:

```
拆解讨论稿必答槽 ──→ WS frontmatter features[].goal_plain ──→ ws-progress 总览表「大白话目标」列
     (Step 5.7)              (机读 · 模板注释带判据)              (名册驱动直出 · 空显「—」)
```

四处同名 · 判据不变(写不出可感知目标 = 横切件并回宿主 ·「后端接口就绪」不算)· 旧名清零(测试锁)。

### 改动

- `_parse_ws_features` 认 `goal_plain` 键(存量 WS 无该字段 → 缺省空 · 不炸);
- ws-progress 总览表:表头 `| feature | BL | 涉及子项目 | 功能 | 大白话目标 | 状态 | 当前阶段 | F |` ·
  名册命中与未匹配两路都透传 · 孤儿/回退路容缺显「—」;
- workstream 模板:frontmatter 加 `goal_plain` 字段(注释带判据)· body 每-feature 节行改同名;
- feature-planning Step 5.7 讨论稿槽 + PLANNING_CHECKLIST 条目同步单名,并点名落点
  `features[].goal_plain`(讨论产出与落盘字段有名字链路 · 不靠意会)。

空着显「—」即可见 —— 载体承载,不配门(同 v8.312/315 姿态)。
