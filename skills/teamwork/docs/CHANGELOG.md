# Changelog

> 📦 v8.103 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**保留最近 5 版**(每次发布:新增本版 → 若超过 5 版,把最旧的一版迁入归档)。

## v8.108 · 外部评审降级策略统一改 subagent(不 exec · 降级而不是去掉 · 满足门禁)

> 用户:降级策略统一改用 subagent · 不用 exec 了(exec 在这出过很多次问题:认证 / --bare / 卡死 / 登录)· 降级而不是去掉。

### 诊断:两条降级路径都 exec CLI 自审 → 反复踩坑
- `--self-review-fallback`(v8.88)+ `disable_heterogeneous_review`(v8.90)都 **exec 宿主自身模型 CLI** 自审 → 子进程 CLI 反复出认证 / `--bare` / MCP 卡死 / "Not logged in" / stdin 问题。
- 且 `--self-review-fallback` 落 `self-review/` 不满足门禁 → 用户被迫「去掉 external」(change-review-roles)· 与「降级而不是去掉」相悖。

### 改法:降级 = subagent(harness 内 · 不 exec)· 满足门禁
- **`state.py`**:self_fallback / het_disabled 两路 **不再 exec** · 改 emit `verdict: SUBAGENT_FALLBACK` 配方(state.py 是脚本起不了 `Agent`)→ PMO 起 `Agent` subagent(isolated context · 宿主自身模型 · 同 auth · 无子进程 CLI 问题)产出降级评审 → 写 `external-cross-review/<stage>-<model>-subagent-degraded.md`。exec 只留给**真异质主路径**。
- **门禁** `_evidence_external_review_artifact`:接受 honest-degrade(`degraded:true heterogeneous:false degraded_mode:subagent-fallback`)→ 满足 P0-154(降级 · 让你继续)。🔴 **无** degraded marker 的 subagent 文件仍落黑名单 BLOCK(防 F034 伪装)· `config-disabled` marker 仍须 `het_disabled` 为真。
- **降级优先于移除**:which-cli 不在的 FAIL hint 改三选一 —— ① 降级(subagent · 推荐)② 装异质 CLI ③ 移除(最后手段)。
- **specs**:standards §11.5(降级=subagent · 不 exec)+ §11.1 两注(self-review-fallback / disable_het 改 subagent)+ review-stage §4。

### 验证
- 更新 3 测(self-review-fallback / config-disabled → SUBAGENT_FALLBACK recipe · which-cli hint)+ 新 2 测(honest subagent-degrade 放行〔即便未 opt-out + 含 claude 文件名〕· bare subagent 仍 BLOCK)· pytest **3 failed / 503 passed**(baseline 3 = scan-spec · 零回归 · +2 测试)。

## v8.107 · Bug 流程加 `diagnose` 阶段(根因细查 + 修复方案确认 · 用户确认后才进 dev · 治本 fix 修偏)

> 用户(case INFRA-B260606100214):Bug 流程 prepare → ok → dev 一口气写 BUG 报告 + fix + commit · prepare 时读的代码不够细 → 易修偏。需在 dev 前加根因细查 + 修复方案确认(用户确认后才进 dev)。

### 诊断:Bug 流程缺「计划确认」闸
- Feature 有 goal(PRD)+ blueprint(TECH)在 dev 前确认「what + how」;Bug **直入 dev**,根因/方案是 dev 里(写 fix 时)顺手写的 → 无独立确认闸 → 修偏。
- 根因细查需**深读代码**:triage/prepare 读的代码只够判流程类型 + 给大致方向 · 不够细。

### 改法:新 `diagnose` stage(Bug 专属 · 插在 dev 前)
- **新 Bug 链**:`diagnose → dev → review → test → pm_acceptance → ship`(Bug 首 stage 改 diagnose)。
- **diagnose 产出**:`bugfix/BUG-*.md` 的 §现象/§根因/§修复方案(frontmatter `root_cause` + `fix_summary` 非空)· 🔴 深读代码挖真因 · **不写 fix 码**。
- **R5 用户确认闸**:diagnose-complete 前必停 · 把修复方案给用户确认 · ok 才 → dev。dev 按**已确认方案**写 fix + §回归测试。
- **dev 准入**:Bug 现要求 `diagnose` output_satisfied(不再直入)· Micro 仍直入。

### 接线(状态机 + spec + 文档)
- `state.py`:LEGAL_STAGES + `BUG_FLOW`(diagnose→dev)+ `DEFAULT_INITIAL_STAGE[Bug]=diagnose` + init brief。
- `_v8_stage_specs.py`:`DIAGNOSE_SPEC`(flow=Bug 准入 · evidence=BUG 报告根因/方案非空 · R5 暂停点 · auto→dev)+ 注册 + dev 准入门禁改(Bug 需 diagnose 完成)。
- `_v8_engine.py`:`FLOW_STAGE_CHAIN[Bug]` + stage→spec-doc 映射。
- 新 `stages/diagnose-stage.md`(深读方法 + 根因实证 + 方案要素 + 用户确认协议)· `templates/bug-report.md` + `docs/prepare.md` 加 diagnose/dev 分工。

### 验证
- 更新 `test_init_feature_bug_defaults_to_diagnose`(Bug 首 stage = diagnose)+ 新 `test_v8107_bug_dev_requires_diagnose`(dev 准入要 diagnose · Micro 仍直入)· pytest **3 failed / 501 passed**(baseline 3 = scan-spec · 零回归 · +1 测试)。
- 🔴 顺延:外部评审降级策略统一改 subagent(原计划 v8.107 · 改为后续版本)。

## v8.106 · 外部 claude 评审回退纯 `claude -p`(删 --bare/--allowedTools/doc 模式 · 治本 --bare 砸登录)

> 用户(case PTR-F260606):state.py 预期只用 `claude -p`。case:`claude --bare -p` 报 "Not logged in" 而裸 `claude -p` 正常。

### 诊断:v8.103 的 `--bare` 砸了登录上下文
- v8.85 起长 prompt 走 doc 模式(短 argv + `--allowedTools` 让 reviewer 自己 Read)· v8.103 加 `--bare`(想跳消费项目 MCP 防卡死)。
- 但 `--bare`(minimal mode)**也跳了 claude 的登录/认证上下文** → `claude --bare -p` = "Not logged in"(裸 `claude -p` 已登录)。v8.103 想用 `--bare` 救 MCP-hang · 反而砸了认证 —— 比病更重。

### 改法(用户拍板「只用 claude -p」)
- `_build_claude_review_cmd`:**只用 `["claude","-p",<full inline prompt>,"--output-format","text"]`**(cwd=None)· 删 doc 模式短引用 + `--allowedTools` + `--bare` + `--permission-mode` + liveness。
- prompt **自包含**(goal/blueprint 已 inline 待评审文件内容 · `_gather_review_files_for_claude`)· reviewer 无需工具 / 文件系统访问 · 一次性纯文本生成 —— 一并消除 MCP-hang(无工具栈)+ 认证回归(无 `--bare`)。
- 仍写 prompt_doc(审计 + 可复跑 · 不 clobber PMO 预写)· 删死常量 `CLAUDE_REVIEW_ARGV_LIMIT`。

### 验证
- 重写 `test_v885_short_prompt_inline` + 新 `test_v8106_long_prompt_still_inline`(长短都 inline · 无 `--bare`/工具 · doc 仍写盘)· pytest **3 failed / 500 passed**(baseline 3 · 零回归)。
- 🔴 下一步(v8.107):降级策略统一改 **subagent**(不用 exec)· 实现「降级而不是去掉」(用户已确认设计:subagent 自审满足门禁 + WARN · 显式带 reason)。

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