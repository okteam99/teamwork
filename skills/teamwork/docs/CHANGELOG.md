# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.275 · 暂停点投递位置红线 + migration 门目录级匹配 + 配方补 target_commit

> 实证 case(IOS-F005 会话三连):① ship1 卡片按模板写了、但贴在回合中段(随后又调 await-merge)—— 宿主不渲染回合中段文本,卡片被吞,用户被迫问「url 发下」:内容防了 · **投递位置没防**;② `OfflineOriginMigrationStore.swift` 类业务组件被 migration **子串**误伤触发 schema 门;③ degraded 外审配方产物缺 `target_commit` → 下轮 `--verify-fixes` 找不到上轮 FAIL。

### ① 投递位置(治整类 · 不只 ship1)
- SKILL R5(b) 新红线:暂停点 markdown / user_card 必须是**回合最后一条输出 · 其后零工具调用**;伴随的监控/标记类命令(pause-mark / await-merge)一律**先执行(后台/静默)再贴**。
- ship-stage §5 次序翻转:先后台启动 await-merge(30s 轮询不阻塞)→ 再把两段作为回合终文贴出;输出格式红线清单补第三条(必须是回合终文);卡片模板行改「已后台启动」。
- push emit `next_action_brief` 同步翻转(消费时点):①先启动 ②再贴 · 卡片后零工具调用 ·「次序不可倒」保留(现覆盖两层次序:监控先于卡 · 卡先于总结)。

### ② migration↔schema 门精确化
- 子串 `"migration" in f` → `_MIGRATION_PATH_RE`(目录级:`migrations/` `migration/` `migrate/` `alembic/`)—— 业务组件文件名含 Migration 不再误伤。

### ③ external-review degraded 配方
- frontmatter 必含清单补 `target_commit: <commit>` —— `--verify-fixes` 增量重验能锚到上轮。

### 验证
- 新增 test_ship_pause_delivery_v8275(5:业务组件不匹配 / DB 路径匹配〔含 Rails·Flyway·alembic〕/ hint 三关键词 / SKILL 投递位置 / 配方 target_commit)· pytest 938 passed。

## v8.274 · teamwork-space.md 骨架带 teamwork 安装地址

> 用户指令:space 文件要包含 teamwork 安装地址 —— 没装 teamwork 的协作者拿到项目、打开知识地图根,第一眼就能看到怎么装。头部引言加一行:🧰 本项目使用 [teamwork](https://github.com/okteam99/teamwork) AI 协作框架 —— 未安装的协作者:`npx skills add okteam99/teamwork`(装完 `/teamwork` 启动)。

### 改动
- bootstrap `maintain_teamwork_space` 精简骨架 + templates/teamwork-space.md 完整模板骨架块(两处生成源都带 · 新项目自动携带)。
- 存量项目:AI 维护 space 时按模板对齐即可补上(不加自动迁移 · space 变更需用户确认 R5)。

### 验证
- test_bootstrap +2(生成物含安装行 / 模板含安装行)· pytest 933 passed。

## v8.273 · 审核员只审内容 · 不重复跑测试脚本

> 用户指令:「审核员只需要审核内容,不需要重复跑测试脚本」。测试执行已有归属:dev(TDD)与 test stage(硬门 exit 0/差分 · 证据落盘)—— 评审员再跑一遍 = 双倍时延零新增证据。评审 = **静态审读**(diff / 代码 / 测试代码 / 实跑证据日志);疑点开 finding 由流水线实跑验证。

### 改动
- 覆盖方向「测试真跑」措辞消歧 ×3(hint 表 / brief 产物注 / review-stage 外审契约):测试真跑 = **读实跑证据/日志** · 非评审自己重跑 —— 这是最容易诱导重跑的一处措辞。
- review-stage 新规则 8:只审内容(Architect / QA / external / 验证轮全适用)。
- review brief(round 1)+ 验证轮 brief 各加纪律行(消费时点):验证轮裁决 fixed/not-fixed 依据 = 读修复 diff + 引用流水线证据。
- external prompt 模板本已拦(reviewer.md「跑测试 → out of scope」)· 本版补齐主审路与验证轮。

### 验证
- 新增 test_review_content_only_v8273(3)· pytest 931 passed。

## v8.272 · PRD 终确认暂停点回显 PRD 绝对路径

> 用户指令:「prd 确认的暂停点,回显一下 PRD 文件的绝对地址」。终确认导读再好也是摘要 —— 用户想核对全文时得自己找文件。导读**头部第一行回显 PRD 绝对路径**(格式 `PRD: /abs/.../PRD.md` · 🔴 绝对路径非相对 · worktree 内产物给 worktree 绝对路径),点开即达。

### 改动
- goal-stage ④ 终确认导读 spec 加头行回显要求;goal brief 步链「用户确认」步同步(消费时点);SKILL 暂停点清单 ② 标注。

### 验证
- brief 断言 ×1(fast/正常两态均携带)· pytest 928 passed。

## v8.271 · PRD 每条 AC 配大白话解释 · 机器校验逐条非空

> 用户指令:「PRD 模板优化,每一个 AC 都需要大白话解释一下」。BDD(Given/When/Then)是给 QA 绑 TC 的机器友好写法,但用户终确认时读起来费劲 —— §验收标准表加 **💬 大白话列**:每条 AC 一句人话(这条在验证什么 · 用户能感知到什么变化),与终确认导读「说人话」哲学同源,拍板者逐条看得懂。

### 改动
- templates/prd.md:AC 表加 💬 大白话列(含示例:「登录成功后 3 秒内能看到自己的头像和昵称」)· 表注/🧠 起草思考规范 AC 条/自查清单同步(写时即配 · 非写完补)。
- goal-complete 新 evidence `ac_plain_words`:解析 §验收标准表 —— 缺列 FAIL(提示照模板加列)· 逐行空/占位(`{...}`/`-`/`无`)FAIL 并列出 AC id;段缺失/无 AC 行不重复报(归 conformance/verify-ac)。
- goal-stage 规则 1 + goal brief 起草思考行同步。
- 机读块不动:大白话属人读单源(body 表)· 不进 TEAMWORK-MACHINE(id 一致原则照旧)。

### 验证
- 新增 test_ac_plain_v8271(5:填齐过 / 缺列 / 空+占位列 id / 无段放行 / 关键词不误判)· pytest 927 passed。
