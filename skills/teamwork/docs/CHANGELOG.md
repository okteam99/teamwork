# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.218 · 四段结构试点:review + dev stage 重构(目标/硬规则白名单/建议手段菜单/契约)

> 用户方向(第一性重审):保留 stage 划分 · 每 stage 给**目标**(QA=保障质量)+ 保**必须规则**(如异常必有 log)· 评审方式拆细为**建议** · 降低强制比例给模型发挥空间 —— 更好也更快。现状:12 stage 1666 行 · 🔴×139(全是红线 = 没有红线)。

### 改动(试点 2/12)
- **review-stage 235→77 行**:①目标(拦质量盲区 · 独立采样 92/163)②硬规则 8 条白名单(独立性/定级实证/verdict 门槛/裁决举证对称/范围锁定/轮次预算/external 协议/汇总不替代 · **每条带 why**)③手段菜单 8 项(AC 对照/diff 走查/边界审查/对抗复现/简洁性 counter-lens/测试质量抽查/截图核对/KNOWLEDGE 对照 · 各标「何时值得」· AI 自选 + Execution Plan 留痕)④契约(findings schema/fix-retry 命令链)。
- **dev-stage 149→63 行**:①目标(设计→可验证实现)②硬规则 7 条(DEV-RULES/worktree 路径/测试证据硬门/设计↔实际核对/全景编译契约/Bug 不重写根因/完工自查打钩)③手段菜单 6 项(🔴 **TDD 红绿从强制降为强烈建议默认** —— 测试证据仍是硬门 · 手段自由)④dev-complete 契约。
- 「怎么做」步骤教程整段删(目标+菜单+契约足够 · 步骤模型自推)。
- 安全网:v8.217 分诊校准回路对冲(放权后质量掉 → 台账显形 → 判据回收)。

### 验证
- 370→140 行 · pytest 819 passed(stage 散文与机器层零耦合实证)· 余 10 stage 待数据后推开。

## v8.217 · 智能分诊 v2:台账「分诊校准(预测→实际)」列 + 降级触发(持续分诊)

> 承 v8.215/216(维度化+动态 roster):v2 落学习回路的数据侧 —— 分诊判定要能被事后打分,判据才能随数据校准而非拍脑袋。

### 改动
- **archive emit 加 `triage_calibration` 束**:预测侧 = clarity + roster 调整摘要(审计已留);实际侧 = diff 文件数(git 确定性)+ goal 修订轮数(PRD 被打回?)+ review 轮数。
- **PROCESS-LEDGER 末尾加「分诊校准(预测→实际)」列**(末尾加列纪律 · ledger-migrate 单源自模板**自动升级**——本版测试实证:旧表 10 列 → 新 canonical 自动 14 列)· 年检算**分诊准确率**(explicit 判定却 PRD 常打回/review 高轮次 → 判据收紧)。
- **降级触发**(持续分诊 · 补反向):blueprint brief 推「TECH 复杂度=简单且零架构决策而 roster 仍重 → 提议降级(R5 → change-review-roles)」—— 升级触发已有(§2.1)· 分诊不是一次性的。

### 验证
- `_triage_calibration` 测试 +2 · migrate 测试改不写死列数(canonical 单源验证)· pytest 819 passed(预期)。

## v8.216 · 评审配置动态化:拆掉 clarity 硬编码 · AI 按「角色价值判据」逐角色配 roster

> 用户裁决(对 v8.215 的修正):`--clarity` 固定消费(跳 PL+跳 external)还是太规则化 —— 该**动态决策**,不一定去 PL,也可能去 QA / ARCH。机制其实早已存在:`stage_review_roles`(所有 gate 本就按它放行)+ `change-review-roles`(审计留痕)· v8.215 错在绕过它另立硬规则。

### 改动
- **删两处硬编码 clarity gate**(PL challenge / blueprint external)—— gate 回归纯 roster 路由:角色不在 `stage_review_roles[stage]` → 自动放行(既有逻辑)。
- **prepare-check emit 加 `role_value_criteria`**(给 AI 的判断框架 · 非规则):逐角色问「这个视角对本 feature 能拦住什么」—— pl=价值前提可质疑?qa=边界/可测性风险?architect=架构决策/跨模块?external=多触发点/同模型盲区?**每角色一行理由(有值留 · 无值去)**· review stage 从严(建议 ≥2 视角 · <2 需强理由)。
- **`triage_evidence.consumption` 改**:凭证据逐 stage 逐角色配 roster(`change-review-roles --reason` · 审计)· `--clarity` **仅记录**进 state(台账/年检校准 · 不触发硬编码行为)。
- goal / blueprint brief 推送同步(冷审派谁 = 按 roster · 非按 clarity 一刀切)。

### 验证
- 测试重写:clarity 单独**不再**跳过任何 gate ✓ · roster 去角色 → gate 放行 ✓(×4)· pytest 817 passed。

## v8.215 · 智能分诊 v1:clarity 维度(明确度)→ 评审强度比例化 + 分诊证据先行

> 实证 case(admin i18n):「**大而明确**」的需求走全重流程 —— 车道把「大」和「不确定」绑死(477 key/7 页 → Feature → goal 3 冷审 + PL 质疑 + blueprint external 全上 · 但需求零歧义)。智能分诊方向(用户确认):输出从「车道标签」走向「维度向量」· 证据先行 · 本版落 v1。

### 改动
- **prepare-check emit 加 `triage_evidence` 证据槽**(estimated_files/cross_repo/new_deps/has_ui/mechanical/clarity)——🔴「看过再判」:30 秒侦察后填 · **空着不给判**;prepare.md §1.5 判定标准(explicit=明确方案或机械映射类;ambiguous=方向词;normal=默认)。
- **`init-feature --clarity`**(explicit/normal/ambiguous · 默认 normal)→ `state.clarity`。
- **explicit 消费两处**(gate 自动放行 · 留痕):① goal **PL 对抗质疑跳过**(无产品歧义可质疑)+ brief 推「冷审 3→1(QA 边界)」;② **blueprint external 跳过**(架构师单审)。🔴 **review 三视角不动**(明确 ≠ 不会写错 · 拦真主力 92/163)。
- 解耦原则:改动面大 → Feature **骨架**照走;不确定性低 → **评审轻档**。预期 explicit 类膜时间 −30~40%。

### 验证
- `test_clarity_v8215` +4(PL 跳/PL 照拦/blueprint 跳/review 不受影响)· pytest 817 passed。

## v8.214 · 注入段/hooks 清理挪出 skip_maintain 版本门(每次 bootstrap 都清 · 治 merge 回流旧块)

> 用户问:升级后会清注入段么?答:**会**(升级 → 版本 marker 不匹配 → maintain 跑 → 清理触发 · E2E 实证)。但验证同时抓到真实边缘:清理挂在 `skip_maintain` 版本门内 —— **同版本内二跑不清**。实害:并行分支上旧版 bootstrap 注入过的 AGENTS.md 被 `git merge` 带回 · 同版本内永不清 · 要等下次升级。

### 改动
- **`maintain_host_injection` + `maintain_host_hooks` 挪出 skip_maintain**(每次 bootstrap 都跑 · 同 v8.91 localconfig backfill「无论 skip 与否」先例)—— 清理幂等且轻(字符串查找)· merge 回流的旧注入块/hook 当次 session 即被兜住。chmod/gitignore 仍在版本门内(真·一次性维护)。

### 验证
- 冒烟:同版本 skip 下 merge 回流块被清 ✓(CLAUDE.md 只剩用户内容 · hook 同清)· pytest 813 passed。
