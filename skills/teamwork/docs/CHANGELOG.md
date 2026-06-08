# Changelog

> 📦 v8.106 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**保留最近 5 版**(每次发布:新增本版 → 若超过 5 版,把最旧的一版迁入归档)。

## v8.111 · Bug 流程 2 摩擦点修复:reviewer 名精确匹配过严 + test brief 对 Bug 撒谎

> 用户:看下我们的 bug 流程是否有问题(附真实 Bug feature 跑流程 transcript:`external-claude` 被拒 + `verify-ac.py` 撞 PRD 不存在)。诊断后选 A+B 都修。

### 诊断:状态机骨架健全 · 坏的是 1 个全局过严匹配 + 1 段对 Bug 撒谎的 brief
- Bug 链 `diagnose→dev→review→test→pm_acceptance→ship` 全接对 · 门禁对 Bug 安全(`ac_test_binding` 已 skip Bug)· 暴露的 2 点都是文案/匹配层 friction。

### 改动
- **Fix A · reviewers roll-call 容许「角色-限定」写法**(`_v8_stage_specs.py:_evidence_reviewers_match`):原精确集合差 `required - reviewer_set` 使 `external-claude ≠ external` 被拒 —— 逼用户把更有信息量的「标明异质模型」写法降级成裸 `external`。改为 token 命中 `角色名本身` 或 `角色-<限定>` 前缀即算覆盖(`external-claude` 满足 `external` · `external-` 边界防 `externalize` 误匹配)。异质性不由此 roll-call 保证(由 `_evidence_external_review_artifact` 校验 cross-review 产物 `review_model`)· 放宽安全 · **全流程生效**(非仅 Bug)。
- **Fix B · `_test_brief` 按 flow_type 分支**(`_v8_stage_specs.py` + `stages/test-stage.md`):原 brief 写死 Feature 视角 · 完成判定列「`verify-ac.py` 通过 / AC 全覆盖」—— 但 **Bug 无 PRD/TC** · 实证有 agent 照着去跑 `verify-ac.py` 撞「PRD 不存在」困惑数轮(**门禁其实对 Bug 自动 skip · 是 brief 在撒谎**)。Bug brief 改为「回归测试转绿 + 既有套件保持绿 · verify-ac/AC 全覆盖 N/A · 别去跑 verify-ac.py」· test-stage.md 加「🐛 Bug 流程分支」callout + §1/§5 内联 Bug 提示。

### 刻意不动(考量 C · 站得住)
- Bug 的 `test` 仍要 `e2e/*`(≥1)+ 双 exit-code 全绿 · review 需 `external` 异质评审 —— 对小 bug 偏重但能防 fix 引回归 · 可 `change-review-roles` 调 · 不在本轮改。

### 验证
- 新增 `TestV8111BugFlowFixes` 6 例(role-qualified 满足 / 裸 external 兼容 / 缺 external 仍 BLOCK / `externalize` 不误匹配 / Bug brief 无 verify-ac 假信号 / Feature brief 不回归)。
- pytest **3 failed / 509 passed**(baseline 3 = scan-spec 既有 · 零回归 · 509 = 503 + 6 新)。

## v8.110 · cosmetic 清理:删 vestigial `review_start.log` 读代码 + config.md 旧降级语义/版本标

> 用户:ok(清理上一轮列的 3 项 cosmetic)。

### 改动
- **vestigial 代码(`state.py`)**:删 `cmd_external_review` 里读/清 `review_start.log` 的 liveness 块 + rc!=0 hint 的 liveness 分支 + 两处 `liveness_confirmed_at` emit —— v8.106 纯 `claude -p`(无工具)已不写该文件 · `liveness_at` 恒 None(死代码)。FAIL hint 简化 + 指向 §11.5 subagent 降级。
- **`config.md`**:`disable_heterogeneous_review` 注释「exec 自审 / v8.88 self-review-fallback 落 self-review · 不满足门禁」→ 改 v8.108 subagent 降级语义(satisfies gate · `degraded_mode`)· 删 4 个 section-header 版本标(v8.79/82/89/90)+ 1 处 v8.80。
- **`test_state.py`** 旧 section 注释去 doc 模式/liveness 措辞。

### 刻意跳过(re-estimate · 风险 > 价值)
- **章节重编号**:`external-model-usage.md` §一→§十二 跳号(缺 §二/§十)**无害**(全部引用可解析)· renumber 会牵动 **15+ `§11.x` 跨文档引用**(含 state.py hints + 刚接好的 §11.5/§11.2 cites)· 易引入新 broken-ref → 不做。
- **`ui.md` v8.17/v8.58 版本标**:是**现行模型**的 provenance(panorama 唯一权威 / same-stack)· 非 stale content · code-fence 多 → 保留(避免 mangle)。

### 验证
- pytest **3 failed / 503 passed**(baseline 3 · 零回归)· liveness 残留引用 = 0(仅剩 bootstrap `.gitignore` 防御项 · 无害)。

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