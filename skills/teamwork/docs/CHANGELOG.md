# Changelog

> 📦 v8.98 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**保留最近 5 版**(每次发布:新增本版 → 若超过 5 版,把最旧的一版迁入归档)。

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

## v8.100 · UI 可视全景前移到规划层(拆 WS 前先出全景初步规划 · feature 边界对齐 UI 结构)

> 用户:UI 可视全景能否更早出 —— 放到 feature 阶段就晚了。确认链路:feature-planning 讨论需求规划逻辑 → 产出 UI 全景初步规划 → 据全景拆成最终 WS(1 个或多个)。

### 设计(全景出生点前移:per-Feature ui_design → 规划层 feature-planning)
- **拆 WS 之前先出全景初步**:涉 UI 的轮次,feature-planning 在拆 WS 前于 `{子项目}/docs/design/preview-project/` 出 design system + 关键页(🔴 **初步**:系统 + 代表页 · **非每页** · 防瀑布 · 跑 `preview.sh` 看)+ 同步 `sitemap.md`(IA 地图 · 🔴 只写层级/导航不写视觉)· 完成产生 git diff = **拆 WS 的输入**。非 UI 轮跳过(WS 标 `N-A`)。
- **WS 据全景拆 · 1..N 个**:feature-planning 输入=全景 diff + 业务目标 → 拆 **1 或多个 WS**(feature 边界对齐 UI 结构)· 每 WS 记 `ui_panorama: ✅/N-A` + `ui_panorama_pages`(覆盖页清单 · 替代模糊的"基于哪轮全景")· 涉 UI 必 ✅ 才转「规划完成」。
- **ui_design 改增量扩**:全景规划期已出生 · ui_design 阶段在已有全景上**增量补**本 Feature 的页与细节(源即权威)· 非从零搭;老项目/跳过规划路径 → 此处首次 seed(回退)。
- **三者分工厘清**:`sitemap.md`=IA 地图(文字 · 不写视觉)· `preview-project/`=视觉权威(可跑)· 单 Feature `UI.md`=本 feature 涉及的页(不重复全局)。

### 接线(8 文档/工具 · 一个 release)
- `docs/feature-planning.md`:§2 重排 Step —— 新 Step 5「🎨 UI 全景初步规划(条件)」插在拆 WS 之前 · 新 Step 6 显式「拆 WS(1..N)」· §1/§4 产物加 preview-project · 坑 4 改三者分工。
- `templates/workstream.md`:frontmatter 加 `ui_panorama` + `ui_panorama_pages` · 状态生命周期加「全景初规子门禁」(涉 UI 必 ✅ 才转规划完成)· 设计要点 +1。
- `stages/ui-design-stage.md`:§3 加「全景在规划期已出生 · ui_design 增量扩」框定 + same-stack 措辞「扩/搭」。
- `PRODUCT-OVERVIEW-INTEGRATION.md`:权威冷启动顺序 ×2 插入「(涉 UI)UI 全景初步规划」。
- `docs/conventions.md §13`:`design/` 加「首次 seed 在规划层」注 · `sitemap.md` 标「只写地图不写视觉」。
- `tools/state.py cmd_planning_check`:checklist +「🎨 全景UI初步规划」项 + WS 项加全景状态/页清单 + `planning_order` 加全景环。
- `roles/designer.md` + `roles/product-lead.md`:规划层参与/主导全景初规。
- `SKILL.md § 业务流程架构`:纵向链路图加「(涉 UI)UI 全景初步规划」一环 + 2 bullet。

### 验证
- 新增 `test_v8100_planning_check_panorama_before_ws`(全景在 WS 之前 + checklist 项 + WS 状态/页清单文案)· `planning_checklist` 5→6。
- pytest **3 failed / 500 passed**(baseline 3 = scan-spec 既有 · 零回归 · +1 测试)。

## v8.99 · DEV-RULES 模板去示例(只留段骨架 + 填写引导)

> 用户:DEV-RULES 模板不用给示例。

- `templates/dev-rules.md` 内嵌骨架各段(架构/分层 · 命名 · 错误处理 · 测试策略 · 代码风格 · 其他约定)删掉 `示例:…` 条目 · 只留 `## 段标题` + 一行 `>` 填写引导。人维护时空段直接填,不被示例干扰 / 误当真规则。
- doc-only · 无 code/测试影响(bootstrap scaffold 用本模板 · 测试用 fake 模板不依赖其内容)。
