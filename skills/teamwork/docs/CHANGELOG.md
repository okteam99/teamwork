# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.240 · ship1 push user_card 防截断三重物化(治「AI 过滤 emit 丢卡片 · 用户看不到 MR 链接」)

> 实证 case(KA-PAGES-F260714041628 · aon-main):主对话习惯用 python key-filter 读 state.py emit,`ship-phase --action push` 的 `user_card` 字段被过滤丢弃 → AI 手写卡片把 MR URL 包进 markdown 加粗 → 用户「没看到链接」。v8.233 的纯 prose 防线(「先贴 user_card」)挡得住 head 截断、挡不住 key-filter —— 按「可枚举进脚本」物化。

### 改动
- **`_v8_ship.py` push emit 三重防御**:① `pmo_must_read` 置字段首位 + `user_card` 第二(survive head 截断);② 卡片同步**落盘** `<feature_dir>/SHIP-USER-CARD.md`(绝对路径 · untracked 随 worktree 消亡 · stdout 丢失时 `cat` 原样贴)+ emit `user_card_file`;③ `hint` 字段冗余同一指令(key-filter 惯选 verdict/hint —— 实证 case 的过滤器恰好选了 hint)。
- **ship-stage.md §5**:卡片段措辞升级为「原样用 + 禁 key-filter/截断 + 落盘兜底路径」。

### 验证
- 新增 `test_push_emit_user_card_materialized_v8240`(位置/落盘/hint/幂等 4 断言)· test_ship_safety 16 passed。

## v8.239 · WS 规划两道深度门:调研深度契约(ws-lint 抓占位)+ 拆解讨论暂停点(R5 必经)

> 用户观察:WS 规划调研浅 · 拆出的需求过散 —— **预期 WS 一定是「代码现状 × 用户深度讨论」的产物**。两病根:① Step 1 调研是软指令无深度证据契约;② 拆解本身没有用户讨论暂停点(用户只在收尾见成品 · 无法在拆解方向上纠偏)。

### 改动
- **调研深度契约**(Step 1 + 模板 + 机器抓):`features[].current_state` **必附来源文件路径**(浅调研拆出的 WS 必散);🔴 **ws-lint 新校验**:current_state **缺失**(条数 < features 数)或**仍是模板占位**(`<...>`/`...`)→ NONCONFORMANT(调研浅硬信号)。
- **Step 5.7 拆解讨论暂停点(R5 · 必经)**:拆解草案落 WS 文档**之前** emit 讨论稿(候选 BL + 每条边界理由 + current_state 摘要〔出自哪些实读文件〕+ 波次 + **粒度自检**)→ 用户就地讨论收敛(合并/砍/改边界)· 不落成品后返工;auto/yolo 按推荐 + WARN 留痕(同全景确认模式)。
- **粒度反压**(镜像 goal AC>10):BL > 8 或存在「无独立交付价值/纯机械半天活」的 BL → 草案必须给「为什么不合并」。
- planning-check checklist WS item 同步两道门。

### 验证
- ws-lint 深度校验测试 +3(占位抓/缺失抓/grounded 放行)· fixture 补 grounded current_state · pytest 838 passed。

## v8.238 · stage-start emit 附派发档位提醒(治「冷审全跑主对话模型 · 零声明」)

> 实证 case(KA-PAGES goal):三路冷审 subagent 全跑 Fable 5 · 零声明 —— QA(校验型)本应验证档。暴露 v8.230 裁定的盲区:**SKILL 全局规则在 session 早期读一次 · 派发那一刻 AI 实际消费的是 stage-start emit/brief** · goal 冷审恰是最高频派发点 · 那里什么都不提醒。

### 改动(不回退 v8.230 · 不复制规则回各 brief)
- **engine 单源常量 `DISPATCH_TIER_REMINDER`** 接进**每个 stage-start 成功 emit**(`dispatch_tier_reminder` 字段):一行提醒「派发声明 model+why · 校验型→验证档 · 判断型→不降档 · 未声明=unspecified」+ 指针 SKILL/agents README —— **工具生成 · 所有 stage 消费时点覆盖 · 文本单源一处**。

### 验证
- 常量+接线断言 +1 · pytest 835 passed。

## v8.237 · 升级检测缓存 TTL 24h → 8h(治缓存掩新版)

> 实证 case:发版节奏快(12 小时内 dev 推进 8 个 minor)· bootstrap 升级检测的 24h TTL 缓存命中 → 报 `up_to_date(from_cache)` · 实际已落后。用户拍板:TTL 改 8 小时。

### 改动
- `SKILL_UPDATE_CHECK_TTL_HOURS = 24 → 8`(失效条件不变:超 TTL / 无缓存 / 时钟回拨 / 本地版本或 channel 变 / `TEAMWORK_FORCE_UPDATE_CHECK=1` 强制实查)· 注释与测试措辞同步(测试逻辑用常量 · 零断言改)。

### 验证
- pytest 834 passed。

## v8.236 · dev brief 补并行提示(开工先问哪些模块可并行)+ 修 stale 措辞

> 用户问:dev brief 有提醒用 subagent/teammate/workflow 么?查实:**没有** —— 并行规则全在 SKILL 全局/agents/README(被动),而 dev 恰是并行红利最大的 stage(多端/多模块实现);顺带抓到 brief「详细步骤 6 步 + 注意事项 5 条」是 v8.218 四段重构前的 stale 旧话。

### 改动
- **dev brief +1 行**(stage 专属手段提示 · 指向全局不复制 · 不违 v8.230 单源判例):🧩 开工先问「哪些模块可并行」→ 多端/多模块各派 subagent/teammate(**ultracode → workflow 优先**)· 派发按 SKILL 🎚️ **声明 model + why** · 契约层/集成点留主对话 · 子 agent 只写 worktree 内路径。
- 必读行修正为四段结构措辞(6 步旧话清除)。

### 验证
- brief 冒烟 ✓ · pytest 834 passed。
