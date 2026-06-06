# Changelog

> 📦 v8.100 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**保留最近 5 版**(每次发布:新增本版 → 若超过 5 版,把最旧的一版迁入归档)。

## v8.105 · external review 消费侧规则:「信号 ≠ 判决」逐条裁决(治本 AI 盲采异质评审被误导)

> 用户(/loop):AI 对异质模型评审的内容倾向于相信,可能会被误导,是否需要优化规则。

### 诊断:规则有不对称 —— 合规侧重 · 消费侧空
- §十一 大力确保 review 真异质(反替身 / 文件名墙 / 反鼓掌);但**怎么消费 reviewer 说的**几乎无规则 —— 仅 review-stage 一行「Architect 别盲采」(范围窄)。
- 后果:AI 默认**相信**异质 review(语气笃定 + 当门禁跑)→ 被误导。但真异质 reviewer **没本项目上下文**(不懂 DEV-RULES / 不知 intentional 设计 / 会 hallucinate)→ 照单全收 = import 外部模型的误判。

### 改法(doc-only · 加消费侧规则)
- **`standards/external-model-usage.md` 新 §十二「消费侧:external review 是信号不是判决」**:
  - **裁决三态**(每条 finding 落其一 · 带依据):`confirmed`(核实真问题 → 修)/ `rejected`(false positive / 误解 intentional / 冲突 DEV-RULES → 不修 · 🔴 必记驳回依据)/ `deferred`(范围外 → PENDING)。
  - **两头都是反模式**:盲采(over-trust · 默认倾向 · import 误判/churn/regression)❌ · 盲驳(under-trust · 全 dismiss 让它过 · 异质 review 白跑)❌ · 裁决(带依据)✅ · **举证责任在主对话**。
  - **grounded 实际代码**:finding 是待核实断言 · 回读真实代码/AC/DEV-RULES 自己确认 · 不轻信 reviewer 转述 · 与 DEV-RULES 冲突 → DEV-RULES 优先 · 通用于代码/PRD/blueprint review。
- **`stages/review-stage.md` §5 汇合**:加「逐条裁决 external finding」段 + cite 表 row 5 指 §十二。

### 验证
- doc-only · pytest **3 failed / 500 passed**(baseline 3 = scan-spec 既有 · 零回归)。

## v8.104 · WS 规划完成给「执行顺序与并行建议」(波次 + 哪些可并行 · 作为 WS 文档一部分)

> 用户:workstream 规划完成后,需要给出并行执行建议,列出建议的执行顺序、哪些需求可并行,作为 WS 文档的一部分。

### 背景:WS 只有 flat launch_order · 不 surface 并行
- WS 此前仅 frontmatter `launch_order`(线性拓扑)+ per-feature `dependencies` · 不显式说「哪些可并行」。ROADMAP 模板早有 Wave/并行度,但那是 **per-子项目**;WS 才是**跨子项目**依赖全景所在 —— 并行编排该落 WS(用户判断正确)。

### 改动(doc-only · 仍是 PL 判断 · 不进 state.py 自动算)
- **`templates/workstream.md`**:
  - frontmatter 加 `execution_waves`(结构化:每 wave = 一组可并行 feature + `after` 前置)· `launch_order` 注明降级为线性回退。
  - body 加 **§执行顺序与并行建议**:波次表(可并行 feature / 前置 / 约束)+ 🔴 **DAG 之外的额外串行约束**(同改面防 merge 冲突 / 跨子项目 provider→consumer 方向 / 带宽 ≤3)+ 与 ROADMAP Wave 关系(WS=跨子项目权威 · ROADMAP=本地视图)。
  - 完成标准 +③、设计要点 +7:规划完成必给并行建议。
- **`docs/feature-planning.md` Step 6**:拆完 WS 必算波次 + 标额外串行约束。
- **`tools/state.py` planning-check**:WS checklist 项加「执行顺序与并行建议(波次)」。

### 为什么不进 state.py 自动算
- 波次的**逻辑层**可由 `dependencies` DAG 算,但**同改面 / 跨子项目方向 / 带宽**是 judgment(依赖字段不含)· 纯 DAG 自动算会误导 → 留 PL 判断(符合「不可枚举留 AI」)。

### 验证
- `test_v8100_planning_check_panorama_before_ws` 加断言(checklist 含「并行」)· pytest **3 failed / 500 passed**(baseline 3 = scan-spec 既有 · 零回归)。

## v8.103 · 外部 claude 评审 hermetic 化(`--bare` 跳宿主 MCP/hooks · 治本消费项目 dev-server MCP 卡死)

> 用户:异质 Blueprint review 跑 `state.py external-review` 卡住(写了 review_start.log liveness 后无 stdout · CPU 近 0 · 直到 timeout)· 裸 `claude -p 'OK'` 3 秒返回。卡住的原因是什么。

### 诊断:`--allowedTools` 激活工具栈 → 自动 spawn 消费项目 MCP → 卡死
- v8.85 起长 prompt 走 doc 模式:`claude -p <短句> --allowedTools Write Read`。`--allowedTools` 激活 claude **agentic 工具栈** → headless 下**自动发现并 spawn 消费项目的 `.mcp.json` MCP servers + `.claude/hooks/`**。
- 案例 aon 项目 `.mcp.json` 的 `aon-demo` = `npm run … dev`(长跑 dev/watch server · 永不返回 MCP 握手)→ MCP 子系统 block → 整个 `-p` 卡死至 600s timeout。liveness Write 先落(核心工具 · 快)→ 之后卡在 MCP = 正是观察到的"先写 liveness 再卡住"顺序。
- 裸 `claude -p 'OK'`(无 `--allowedTools`)不进工具栈 → 不载 MCP → 3 秒返回。**非代码 / 文档 / v8.102 问题**。

### 改法(`state.py` · external review 必须 hermetic)
- `_build_claude_review_cmd` 两路都加 **`--bare`**(🔴 跳宿主项目 MCP/hooks/CLAUDE.md/skills 自动发现 · 直接消因);doc 模式再加 **`--permission-mode dontAsk`**(非白名单工具自动拒 · 不 abort 不挂)+ 白名单扩到 **`Read Grep Glob Write`**(读+导航 + 仅 liveness 写 · 仍不放 Bash/Edit)。
- 同步 PMO-facing `preview_cmd` 文案。flags 均在 claude CLI v2.1.162 验证存在。

### 验证
- `test_v885_short_prompt_inline` + `test_v885_long_prompt_doc_mode` 扩断言(`--bare` / `dontAsk` / `Grep`/`Glob` 在 · `Bash` 不在)· pytest **3 failed / 500 passed**(baseline 3 = scan-spec 既有 · 零回归)。
- 🔴 消费项目需 `tools/update.py` 拉本版才生效(aon 现 v8.101.1)· 临时绕过:删/注释消费项目 `.mcp.json` 的 dev-server MCP · 或手跑 `claude -p "$(cat <doc>)"`(无工具栈)。

## v8.102 · 异质评审 prompt 与 review_start.log liveness 调和(READ-ONLY carve-out 唯一允许写)

> 用户:异质模型评审 prompt 要求"不能写文件",但和 `review_start.log` 的 liveness 记录冲突,优化下。

### 诊断:claude doc 模式下 prompt 自相矛盾
- v8.85 起 claude doc 模式调用 · state.py argv 让 reviewer「先写 `review_start.log` 时间戳证明在工作」+ 授 `--allowedTools Write Read`(liveness:区分"模型没响应" vs "在跑但慢")。
- 但 reviewer 读到的 prompt(`claude-agents/reviewer.md`)STRICT CONSTRAINTS 写「不能写文件 · 改文件→Out of scope」—— **严格遵守的 reviewer 会拒写 liveness** → 信号永不出现 → state.py 误判"模型可能从未响应"。
- codex 路径无此问题:`sandbox_mode=read-only` 物理拦截 · 本就不写 liveness 文件。

### 改法(doc-only · 调和 prompt · 保留 liveness 机制 · 不动 state.py)
- `claude-agents/reviewer.md` STRICT CONSTRAINTS:`不能写文件` → `不改动代码库`(不改/不新建源码·文档·评审产物)+ 🟢 显式 carve-out「**唯一允许的写 = `review_start.log`**(liveness · 非评审产物 · 写完正常评审 · 除此不写)」· 评审记录明确「经 stdout 返回 · 不落文件」· out-of-scope 行加注「写 liveness 不算'评审之外'」。
- `standards/external-model-usage.md §一`:只读约束拆 codex(sandbox 物理拦截 · 无 liveness 文件)vs claude doc(唯一例外 `review_start.log` · `--allowedTools Write` 限范围 + 跑完清理)两路。
- **不动** codex prompt 头(§78-91):codex sandbox 真只读 · "Cannot write files" 正确。**不动** state.py:argv 早已指示写 liveness · 本次只让 prompt 与之一致。

### 验证
- pytest **3 failed / 500 passed**(baseline 3 = scan-spec 既有 · 零回归 · doc-only 无新测试)。

## v8.101 · 待规划需求池外置 → `product-overview/PENDING.md`(teamwork-space 瘦身 · 只留 1 行指针)

> 用户:teamwork-space.md 有点臃肿 · 尤其待规划需求(Backlog)部分 · 应拆出子文档单独管理 · 不占 teamwork-space 内容。

### 诊断:Backlog 是全景索引里唯一 append-heavy 的节
- teamwork-space 其余节都**结构静态**(子项目清单 / 架构全景 / 目录 · 仅 restructure 时变);待规划需求池每次跨 Feature 发现就 append 一行 · 即便「只留 active」也会撑大 · 违背它自己的「≤1 行 / 一眼看懂」。
- 决策(用户拍板):外置到 **`product-overview/PENDING.md`**(规划层 inbox · 用 PENDING 名对齐已有 `PENDING-NNN` id · 避开与 ROADMAP `BL-NNN` 撞名)· teamwork-space 只留 1 行指针。

### 改动(doc-only · state.py 从不碰此池 · 零 code/测试影响)
- **新 `templates/pending.md`**:实例化骨架 + 自描述规则头(ID `PENDING-NNN` / 只留 active 📝🔄 / 追加触发 / 转化即删 / ≤1 行)。
- `templates/teamwork-space.md`:§ 待规划需求池 整张表 → 1 行指针(→ `product-overview/PENDING.md`)。
- `docs/teamwork-space-guide.md §6`:收敛为「已外置」说明 + context 收益 + 指模板头。
- `SKILL.md`:① backlog-scan 触发改**按需读** `product-overview/PENDING.md`(不再 silent-read)· ② session 入口 silent-read 列表删「§ 待规划需求池」→ 移入「按需读」· ③ 追加机制 / §310 指针更新。
- `docs/conventions.md §13` + `PRODUCT-OVERVIEW-INTEGRATION.md` 目录树 + `bootstrap.py` 冷启动 hint:product-overview/ 内容加 `PENDING.md`。

### context 收益
- 待规划池**不再随每个 session 入口 silent-read 进 PMO 上下文** · 改为 mode A query 命中 backlog 关键词时按需读 · 池越长收益越大。

### 验证
- pytest **3 failed / 500 passed**(baseline 3 = scan-spec 既有 · 零回归 · doc-only 无新测试)。
