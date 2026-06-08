# Changelog

> 📦 v8.104 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**保留最近 5 版**(每次发布:新增本版 → 若超过 5 版,把最旧的一版迁入归档)。

## v8.109 · 跨文档一致性 sweep(清理 + 4-agent 审计修 v8.100–108 遗留的 conflict/stale/broken-ref)

> 用户:清理(SKILL 命令计数 + reviewer.md liveness carve-out)· 并整体 review 各 md 文件看语义冲突 / 冗余 / 缺失。

### 清理(2 项)
- `SKILL.md` 命令清单:`10 stage × 2` → `11`(补 diagnose-start/complete 条目)。
- `claude-agents/reviewer.md`:删 v8.102 liveness carve-out(`review_start.log`)—— v8.106 已删 doc 模式 / Write 工具 · 该 carve-out 已 moot;READ-ONLY 改「不写任何文件 · 经 stdout 返回」· stdin→argv。

### 审计(4 并行 agent 扫 SKILL/planning · stages · standards/roles · templates)→ 修 conflict/stale/broken-ref
- **v8.107 diagnose 接线漏修**:`dev-stage.md`(§1 加 Bug 读 diagnose 的 BUG 报告为输入 · §5/Output 改「dev 追加 §回归测试/§修复记录 · 不重写根因/方案」)· `FLOWS.md` Bug 链补 diagnose · `bug-report.md` `current_stage` enum 换 v8 BUG_FLOW(删 defunct triage 枚举)+ body 段对齐(根因/方案=diagnose · §回归测试=dev · 删复杂度评估/PMO 流程判断)· `roles/rd.md` + `SKILL.md` 授权暂停点 Bug 行加 diagnose。
- **v8.106/108 external-review 接线漏修**:`external-model-usage.md §一`(claude 路径删 doc 模式/liveness/--allowedTools → 纯 claude -p)· §11.2 加 honest-degrade 黑名单例外 · §11.4 修 broken ref `7.x→11.x` + subagent 反模式区分伪装 vs §11.5 诚实降级 · §11.3 决策树降级优先 · `review-stage.md §4` 删 liveness bullet。
- **v8.100/101/104 planning 接线**:`prepare.md` 死术语 `panorama-design`→「UI 全景初步规划」(3 处)· `feature-planning.md`「只产 3 文档」→ WS+preview-project · `PRODUCT-OVERVIEW`/`roadmap.md` launch_order→execution_waves + WS/ROADMAP 波次权威关系。
- **broken-ref / stale**:`workstream.md`/`workstream-readme.md`「§ 进度统计」→「§ 规划状态」· `external-reviewer.md` `{review_id}.md`→`<stage>-<model>.md`(合 §11.2)+ host-aware 异质 · `templates/README.md` knowledge「3 类含 Conventions」→ 4 类(Conventions 已迁 DEV-RULES)+ 补 pending/dev-rules 行 · `agents/README.md §三` 加「权威已迁 §11」指针。
- **去版本标**(违 v8.98 spec 写作约定):清掉近期加到 SKILL/prepare/feature-planning/teamwork-space-guide 的 `(v8.10x)` inline 标。

### 验证
- 残留 grep(panorama-design / 旧 liveness / § 进度统计 section-ref)= 0 · doc-only · pytest **3 failed / 503 passed**(baseline 3 = scan-spec · 零回归)。
- 余(cosmetic · 不阻塞):external-model-usage §二/§十 编号跳号 · ui.md/config.md 旧版本标 · state.py vestigial `review_start.log` 读(无害)。

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