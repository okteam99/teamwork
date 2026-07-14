# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.240 · 拆解边界判据:交付内聚>子项目边界 + 含金量对照 + id 不重排纪律

> 来源 case(JCB 卡片 WS · v8.239 门生效前的存量拆解):7 件逐 feature 代码审计发现 4 件薄(S2/S3/S6 薄配套 · S7 半运营 · 「其余四件加起来的代码量可能不如 S5 一件」),但 v8.239 粒度反压零触发(7<8 · 每件流程上都「站得住」);用户亲自解禁「feature 也可以跨子项目」才合成 5;且落盘后合并触发**第三次编号重排 = 整卷重写防漏引用**。三个判据缺口,不加新暂停点。

### 改动(Step 5.7 判据升级 + 模板 + checklist 同步)
- **边界判据**:主判据 = **交付内聚**,**feature 可跨子项目**(`target` 只是 ROADMAP 归属 · 「代码在不同子项目」不是拆分理由,评审 blast radius 才是);**薄承接件默认并入宿主件**(只承接另一件产物/同 surface 严格串行/协调点可内化为里程碑),保持独立须给硬理由之一:外部依赖 gate / 交付节奏不同 / blast radius / 管辖边界(四类全部萃取自该 case 的真实裁决:S1+S2 并 · S6 gate 独 · S7 节奏独 · S3 blast radius 独)。
- **含金量对照**:讨论稿每条 BL 标「真新增工程量 vs 薄配套(承接/枚举/配置级)」——**含金量悬殊 = 强合并信号**(反压 BL>8 抓不住 7 件 4 薄这类)。
- **id 纪律**:草案期编号随便改;**落盘后合并/砍件不重排幸存 id**——被并件留一行遗迹(`S2 → 已并入 S1`)· 缺号不补。
- 模板顺手修:`flow_type` 注释还是 v8.222 合并前旧词表(feature/agile/bug/micro)→ 现闭集(Feature/Bug · micro 是 preset)。

### 验证
- 文档+模板+checklist 消费点三处同步 · ws-lint 不消费 target/flow_type 注释(纯文案安全)· pytest 839 passed。

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
