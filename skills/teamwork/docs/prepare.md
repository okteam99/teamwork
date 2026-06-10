# Prepare · 进状态机前的准备子流程

> **可重入子流程** · 任何"决定要走某流程"的 PMO 主对话点都走一次。
> 输入:用户意图(自然语言 / Feature Planning 中的 BL-NNN / 升级讨论收敛)
> 输出:`state.py init-feature` 命令的 5 项参数(flow_type + feature_id + worktree_path + branch + merge_target)

---

## 0. Must-read(PMO 进 prepare 前必读)

🔴 **必读 spec**(动手前主对话 cite 关键原文 · 详 [STAGES.md §2 P0-11 cite 纪律](../STAGES.md)):
- **[conventions.md §9-12](./conventions.md)** — worktree path 规范(`{worktree_root_path}/{Feature-ID}` · 默认 `.worktree/`)
- **`.teamwork_localconfig.json`** — 项目级 worktree_root_path 配置(读 `worktree_root_path` 字段 · 不存在用 `.worktree`)
- **[feature-planning.md §0](./feature-planning.md)** — 何时改走 Feature Planning(关键词 + 复杂度双触发)

🔴 **PMO 必先 Read 本 prepare.md(工具调用)再 emit 任何 prepare 内容** —— SKILL.md 只给"移交 prepare 子流程"指针 · 具体 5 段模板 / 准入校验 / prepare-check 用法都在本文件。不读直接 emit = R5 违规(详 §0.5 #1)。

---

## 0.5 反模式黑名单 + 物化拦截 TODO

🔴 **AI 凭直觉 / 短回路跳步骤 · 大概率被用户叫停重做 · 不省 token · 反多消耗**。以下都是 R5 违规 · 列出供 PMO 自检:

| # | 违规 | 触发场景 | 治本 spec 位 |
|---|---|---|---|
| 1 | 漏 Read 本 prepare.md · 凭 SKILL.md「移交 prepare」概览就 emit | mode B 首次触发 prepare | § 0 必读 |
| 2 | 漏跑 `prepare-check` · 用 `ls` / `grep` 手算 next ID | 「目录看一眼就知道」 | § 1.5.4 |
| 3 | 跑 `prepare-check` 但漏 / 错 `--features-root`(没传子项目对应 docs_root)→ 拿主 tree 结果 → 错号 | monorepo 子项目场景(`apps/partner` 在 PTR namespace) | § 1.5.4 + conventions §1 |
| 4 | `prepare-check` 未叠加 worktree branch 上 in-flight Feature 占用的 ID → 撞号 | 并行 Feature 多 worktree 时 | § 1.5.4 |
| 5 | 关键词命中即推流程类型 · 漏 §2.2 准入**反向扫描**("加按钮"→ 敏捷需求 · 没扫"改 UI 结构"信号) | 用户原文含 UI 调整 / 加组件 / 改布局 / 改交互 | § 2.2 |
| 6 | emit 简化版(只给 4 项配置 + 备选)· 漏「流程概览 / 评审角色 / 上下文 / Worktree」4 段 | 短回路认知偏差("4 项就够了") | § 4 |
| 7 | 现象类输入未排查直接定 Bug + emit prepare(「代码现状」填未验证猜测 · 命名/路由押在猜测上) | 用户只给现象(CI 失败/报错/挂了)· 无修复指令 | § 2 排查先行律 |

🔴 **AI 短回路 ≠ 用户授权**:用户给短指令("改下页面")**不等于** AI 可省略 5 段表。用户已通过本 prepare.md 决定承担 5 段的"重量" · AI 无权简化。

🔴 **PMO 自检顺序**(动手 emit 前过一遍 · 任一 ❌ 即重来):
1. ✅ 我读完本 prepare.md 全文了吗?
2. ✅ 我跑过 `prepare-check --features-root <子项目对应 docs_root> --flow-type <type>` 了吗?
3. ✅ 我手动 `git worktree list --porcelain | grep -oE '<PREFIX>-[FBM][0-9]+'` 叠加占用 ID 了吗?
4. ✅ 我反向扫过 §2.2 准入信号(UI / 架构 / 文件数)了吗?(关键词命中 ≠ 流程类型推完)
5. ✅ 我准备 emit 的 5 段(§4.1 自检清单)全有吗?

### 物化拦截 TODO(违规可枚举消除 · 工具未到位前靠 PMO 自觉 + 上面自检清单)

| TODO | 位置 | 治本机制 | 状态 |
|---|---|---|---|
| `init-feature` 加门禁 | `state.py` | 本 session 未为 prefix 跑过 prepare-check → FAIL with hint(无 audit 不可 init-feature) | ✅ 已物化 |
| `prepare-check` 内部合并 worktree ID | `state.py prepare-check` | 内部跑 `git worktree list --porcelain` 解析 ID · 与 `existing_ids` 取并集 · 输出统一 `next_available_id_stem` | ⏳ TODO |
| `prepare-check` 加 `--user-intent "<原文>"` + `--admission-judgment '<JSON>'` | `state.py prepare-check` | 接收用户原文(留痕)+ AI 读 §2.1/§2.2 后的判断(JSON 必含 sections_reviewed / matched_signals / recommended_flow_type / ai_rationale 4 字段)· 工具校验 JSON schema + consistency(recommended vs --flow-type)· MISMATCH → WARN(不 BLOCK · R0 兜底) · init-feature 读 audit 也 emit MISMATCH WARN | ✅ 已物化(用 AI judgment 替代 regex 关键词) |
| `prepare-check` 返回 `emit_template_markdown` | `state.py prepare-check` | 5 段填好的 markdown 字段 · AI 复制粘贴 emit · 漏段不可能(同 stage `next_action_brief` 模式) | ⏳ TODO |
| `prepare-check` 加 `--subproject <PREFIX>` | `state.py prepare-check` | 替代裸 `--features-root` · 内部读 teamwork-space.md docs_root · 传错 prefix → FAIL with hint | ⏳ TODO |

📎 物化策略说明:
- ✅ 已物化 2 条 · ⏳ TODO 3 条(渐进治本 · 优先治高频 case)
- 🔴 `prepare-check --admission-judgment` **不用 regex 关键词扫描** —— 用户洞察:关键词列表本身不可枚举完 · 语义不能简单 regex 匹配 · 改为 R0 拆分:**可枚举的进脚本(judgment JSON 必填 + schema 校验) · 不可枚举的留 AI(judgment 内容 · ai_rationale 由 AI 自由判)**
- 物化前 violation 全靠 PMO 自觉(case F001 证明不可靠)· 物化后违规由工具层直接拒绝 / 留 audit + WARN · 不依赖意志力

---

## 1. 触发场景

| 场景 | 何时走 |
|---|---|
| **新 session · mode B execute** | SKILL.md § Triage 入口规范 mode 分诊判 B → 进 prepare |
| **mode E discuss 升级 B** | 讨论收敛后 PMO 主动建议升级 → 进 prepare |
| **Feature Planning 完成后启 Feature** | PL 在 ROADMAP 拆完后 · 用户拍板某 BL → PMO 同 session 走 prepare 启动 Feature |
| **mode A/D 转 B**(罕见) | 用户从查看/状态切到执行 → 进 prepare |

**非触发场景**(prepare 不跑):
- mode A query / mode D status:不进状态机
- mode C resume:已有 state.json · 直接 jump
- Feature Planning 流程本身:由 PMO 主对话按 [docs/feature-planning.md](./feature-planning.md) 执行 · 不需 prepare(不进状态机)
- 问题排查流程:同上 · 不进状态机

---

## 1.5 Step 0 · 上下文准备

PMO 移交 prepare 后 · **必走以下 4 项准备**(emit 暂停点之前):

### 1.5.1 · 检 Planning ship 状态(若是 BL 启动 Feature)

若用户启动来自 ROADMAP 某 BL-NNN(Feature Planning 已完成):
- 读 ROADMAP.md 定位该 BL 行
- 检 Planning Feature 已 ship 的 commit hash(`git log --grep='<Planning Feature ID>'`)
- 输出"Planning ship 状态"行(给暂停点表格 · 用户看到 = 上游已 ready)

无 Planning(直接 mode B execute)→ 跳此项。

### 1.5.2 · 检上游依赖(state.json blocking)

若 prepare 是从已有 Feature 衍生:
- 检上游 Feature 的 `state.blocking.pending_external_deps`
- 列已就绪 / 待中(给暂停点表格)

无上游 → 跳。

### 1.5.3 · 扫代码现状(可选 · 1 句话总结)

可选(高复杂度 Feature 推荐):
- grep 关键模块当前实现(如 PTR-F041 = adapter.rs Impact-only 硬编码)
- 给暂停点表格 1 句话总结 · 让用户验证启动方向无误

低复杂度 / 用户已知 → 跳。

🔴 **「代码现状」只写已验证事实**:根因类判断必须来自排查先行 / 实证(读过真实代码与日志)· **未验证假设不得写入**(写进总览 = 误导用户 review · §2 排查先行律的反面教材)。

🔴 **路由前缀必判**(即便跳过上面的可选深挖):据**改动代码所在的子项目目录**定 artifact 前缀 + docs_root —— 查 `teamwork-space.md` 子项目清单(代码在 `apps/partner/` → 用 PTR 注册前缀 + docs_root · 在 `services/` → SVC-* · …)。**不可沿用上一个 Feature 的前缀**。错前缀 / 错路径 → `init-feature` 路由物化校验 FAIL(错前缀会落错位置)。

### 1.5.4 · ID 冲突预检 + stage 评审角色预览(强制)

```bash
state.py prepare-check --feature-id-prefix <PROJ> --flow-type <Feature|Bug|Micro|敏捷需求>
```

输出含:
- `next_available_id_stem` + `existing_ids` + `id_letter`(ID 冲突预检 · 字母 F/B/M 由 `--flow-type` 定 · 详 conventions.md §1)
- `stage_chain_preview`(stage × 评审角色预览 · 让 AI 在 prepare 阶段就看到各 stage 的建议评审角色)

🔴 `--flow-type` 必传:Bug → `PREFIX-B{NNN}` · Micro → `PREFIX-M{NNN}` · Feature/敏捷需求 → `PREFIX-F{NNN}`。漏传退回字母 F · Bug/Micro 会错号(漏传会错号)。

PMO 把数据填进暂停点表格:
- `next_available_id_stem` → artifact ID 推荐默认值
- `stage_chain_preview` → 渲染「📋 各 stage 评审角色」子表(详 §4 emit 模板)
- 🔴 `reviewer_thinking_checklist`→ **必基于 4 问思考 + 给出加减预估**(不直接抄 stage_chain_preview 默认)

🔴 **评审角色思考清单**(防 PMO 直接抄默认):

prepare-check 输出 `reviewer_thinking_checklist` 4 个核心问题 · PMO 在 emit prepare 暂停点的「建议评审角色」段时必基于此思考:

| # | 问题 | 命中调整 |
|---|---|---|
| Q1 | 有产品方向影响?(业务目标 / 用户可见 / 商业模式 / 跨项目一致 / 变更级联 Level≥2) | **是**(常态)→ goal **留 pl**;仅纯内部技术重构 · 零产品面才去 pl · ⚠️『无 ROADMAP』**不是**去 pl 理由(ROADMAP=规划层 · 与 PRD 产品方向评审无关) |
| Q2 | 含 UI 改动? | 否 → ui_design 跳过 + browser_e2e 跳过 |
| Q3 | 跨 ≥3 module 触发点 / 调用方? | 是 → blueprint / review 强 external(异质模型查漏触发) |
| Q4 | 数据模型重构(删/改老字段 · 表结构变)? | 是 → blueprint 强 architect + 加 dba 评审 |

🔴 **pl 不是套路化删**:pl 默认保留(产品方向视角 · 防 Feature 偏离产品方向)· 去 pl 是**少数例外**(纯内部 / 技术重构 · 零产品面 · 零跨项目)· 必给该 Feature 特定理由 · 不得拿『无 ROADMAP』当通用借口(几乎所有执行层 Feature 都『无 ROADMAP』· 那是规划层的事)。

**不直接抄默认**:据本 Feature 实际(前后端先行 / 模块数 / 是否需 ui_design)给评审角色加减预估 · 不照搬 stage_chain_preview(后端先行→ui_design 可跳 · 跨多 module→blueprint 强 external)。

🔴 emit prepare 暂停点 「建议评审角色」段格式(必含调整理由列):

```markdown
建议评审角色 🔴(基于 reviewer_thinking_checklist 思考 · 见调整理由)

| stage | 必/选 | 评审角色(调整后) | 调整理由(cite 4 问命中) |
|---|---|---|---|
| goal | 必 | pm, qa, architect, **pl**, external | Q1 有产品方向影响(如支付=商业模式 + 跨端一致)→ **留 pl**(默认 · 别拿无 ROADMAP 去) |
| ui_design | 跳过 | — | Q2 后端先行 · UI 留 PTR 子 Feature |
| blueprint | 必 | qa, architect, **external 🔴 强** | Q3 跨 5 module 触发点 · 异质模型查漏 |
| ... | ... | ... | ... |
```

---

## 2. Step 1 · 流程类型识别(6 闭集 · R2 红线)

PMO 按以下关键词表判定 user input 落入哪类流程:

| 关键词模式 | 流程类型 |
|----------|---------|
| 规划 / Feature Planning / feature planning / 更新 roadmap / 拆 roadmap / 路线图 / 全景 / 做电商 / 做 SaaS / 商业模式调整 | **Feature Planning** |
| 排查 / 查 log / 诊断 / why X 慢 / 调研 / 分析根因 · 🔴 以及一切**根因未定的现象类输入**(报错 / 挂了 / CI·编译失败 / 慢 · 无修复指令) | **问题排查**(排查先行律 · 见下) |
| 修复 / fix / 处理掉 X bug / 生产缺陷 · 🔴 仅当**缺陷已指认**(用户明确要求修复 · 或 现象+期望+大致位置已知) | **Bug** |
| 换 logo / 换图 / 改文案 / 改样式 / 改颜色 / 改配置常量 | **Micro** |
| 加按钮 / 加导出 / 加字段 / 列表加列 | **敏捷需求** |
| 实现 / 开发 / 做功能 / 新建模块 | **Feature**(兜底)|

落入 6 闭集之一(R2 红线 · enum 强制)。

🔴 **排查先行律**(治 case PTR-B260610102151:「ci 编译失败」被直接定 Bug · prepare「代码现状」填了未验证猜测〔i18next 类型推导〕· diagnose 才查出真因〔path 类型加宽 4 处漏改 2〕—— 命名/前缀路由/worktree 全押在猜测上 · 真因在别的子项目就全配错):
- **现象类输入**(报错 / 挂了 / CI 失败 / 慢)且 根因·影响面·归属 未定 → **不直接定 Bug · 不 emit prepare 总览** —— 先走问题排查(主对话 · 不进状态机 · 详 [FLOWS.md § 问题排查](../FLOWS.md))。
- 排查闭合 → 按 [SKILL.md § Mode A / E 升级触发](../SKILL.md) emit 升级暂停点:排查小结(**已验证**根因 / 影响面 / 修复性质)+ 建议流程(转 Bug / Micro / Feature / 不动 / revert 肇事 commit)→ **用户拍板后**才进 prepare。
- 转入 prepare 时:排查结论 = 「代码现状」内容(已验证事实 · 非假设)· Feature 命名 / 前缀路由据**真因所在子项目**定;后续 diagnose stage cite 排查结论**复核** · 不重查(详 [stages/diagnose-stage.md](../stages/diagnose-stage.md))。
- 边界:**Bug 直入仍合法** —— 用户明确指认缺陷并要求修复(现象+期望清楚 · 大致位置已知)→ 直接 Bug 流程 · 根因细查由 diagnose stage 承担。判别题不是「用户用了哪个词」· 是「**定流程所需的事实(根因/归属/规模)是否已知**」。

**触发场景为 "Feature Planning 启 Feature"** 时:flow_type 默认 `Feature`(因为是从 BL-NNN 启动具体功能 · BL 已经决定了"做什么")。

### 2.1 · 复杂度升级判据(覆盖关键词初判)

🔴 **关键词命中 Feature / 敏捷需求 / Micro 时 · PMO 必再扫以下复杂度信号** · 命中任一 → **强制升 Feature Planning**(覆盖关键词初判):

| 信号 | 例 | 不计入 |
|---|---|---|
| **跨独立部署服务**(≥2 个) | 独立 git repo / 独立 origin / 独立部署单元(后端服务 + 前端 + 管理后台) | mono-repo 内跨 apps(同 origin · 单部署单元) → 用"影响 ≥2 BL"判 |
| **数据模型重构** | 删/改老字段(影响存量) / 表结构变动 / 字段语义重定义 | 新增字段(无存量影响) |
| **老需求架构性废弃** | "X 不要了"/"统一为 Y"/"重构这套逻辑" / 整套机制语义替换 | 仅扩展(向后兼容) |
| **影响 ≥2 BL** | 一次需求拆成多个 Feature 协同(admin / backend / partner 各 1 BL) | 单 Feature 内多 commit |
| **方向级业务变更** | 新增/删除业务能力 / 商业模式调整 / 用户角色重新设计 | UI 文案微调 |

**为什么强制升级**:这些信号意味单 Feature 状态机承载不下 — 跨仓库要规划层 UI 全景初步规划(preview-project + sitemap)· 数据模型重构要 ROADMAP 多 Feature 协同 · 单 Feature 的 PRD/TC/TECH 写不下"3 仓库 + 老字段迁移 + 多 BL 拆解"。强行进 Feature → PMO 在主对话散述 Q1-Q4 决策树(违 R5 暂停点协议 · 写伪 PRD)。

**PMO 命中后必输出**(R5 标准 1/2/3 暂停点 · 不用自由文本):
```markdown
⏸️ 复杂度判据触发(prepare §2.1)· 你的需求触发以下复杂度信号:
- <信号 1>(具体:<例>)
- <信号 2>

请选择:

1. **进 Feature Planning 流程** 💡 推荐
   理由:跨仓库 / 数据模型重构 / 多 BL · 单 Feature 状态机承载不下
   动作:进 Feature Planning(涉 UI 先出全景初步规划 preview-project + sitemap)→ 拆 WS → ROADMAP 拆 BL-N → 每个 BL 后续启独立 Feature
2. **就一个 Feature**(确认范围未超 · 继续 mode B)
   理由:你确认信号是误判 / 范围实际收敛在单 Feature
   动作:继续 prepare · 按 Feature 流程走
3. **其他指示**
```

**反例**:
- 用户:"整体改下这里的逻辑 · source_type 不要了 · 统一为 api · adapter 改为账号可选功能"
- ❌ PMO 错:命中"整体改"→ Feature 兜底 → 主对话 emit Q1-Q4 决策树
- ✅ 正确:命中"跨 3 仓库 + 老字段废弃 + 数据模型重构"→ 升 Feature Planning →(涉 UI)全景初步规划 + 拆 WS + ROADMAP 拆 BL

### 2.2 · 敏捷需求 / Micro 准入校验(覆盖关键词初判)

🔴 **关键词命中「敏捷需求」或「Micro」时 · PMO 必验准入硬约束** · 任一不满足 → 升级(关键词只看字面 · 准入硬约束才是真流程边界):

**敏捷需求准入**(全满足才成立 · 否则升 **Feature**):

| 准入项 | 不满足的信号 |
|---|---|
| ≤5 文件改动 | 预估改动 >5 文件 |
| **无 UI 变更** | 改页面结构 / 加显示字段 / 加 UI 组件(预览/弹窗/图表)/ 改交互 |
| **无架构变更** | 新增模块 / 改接口契约 / **数据库数据结构变更**(新建/删除/修改 表、字段、索引、约束、migration) |
| 方案明确 | 用户需求有歧义 / 实现方式未定 |

**Micro 准入**(全满足才成立 · 否则升 **敏捷需求** 或 **Feature**):

| 准入项 | 不满足的信号 |
|---|---|
| 零逻辑变更 | 改动含任何条件 / 分支 / 数据流逻辑 |
| 改动类型在白名单 | 仅 文案 / 样式 / 资源 / 配置常量 / 注释 · 其它都不算 Micro |

**为什么校验**:关键词("加字段 / 列表加列")只看字面 · 无法区分"后端加字段(无 UI)"和"前端详情页加显示字段(UI 变更)"。命中关键词后 · PMO 必扫代码现状 + 需求范围 · 验准入。

**PMO 命中后必输出**(R5 标准 1/2/3 暂停点 · 不用自由文本):
```markdown
⏸️ 准入校验(prepare §2.2)· 关键词初判 <敏捷需求 / Micro> · 但触发以下准入不满足:
- <准入项>:<具体信号>

请选择:

1. **升级到 <Feature / 敏捷需求>** 💡 推荐
   理由:<准入项> 不满足 · 原流程 stage 链承载不下(如有 UI 变更但敏捷需求无 ui_design)
   动作:按 <Feature / 敏捷需求> 流程走;有 UI 变更的 Feature 在 goal-complete 标 `--needs-ui=true` 进 ui_design
2. **坚持 <原流程>**
   理由:你确认准入信号是误判
   动作:按 <原流程> 继续(⚠️ 跳过 ui_design / 完整 blueprint · 记流程例外)
3. **其他指示**
```

**反例**:
- 用户:"My Offers 详情页加 offerId label + 加 raw JSON 预览"
- ❌ PMO 错:命中"加字段"→ 敏捷需求(漏验准入)
- ✅ 正确:命中"加字段"→ 验准入 → "加 raw JSON 预览组件 + 改详情页信息结构" = UI 变更 → 升 Feature(goal-complete `--needs-ui=true`)

---

## 3. Step 2 · worktree 决策模板

PMO 按 flow_type 算 branch 前缀 + worktree path 建议:

| flow_type | branch 前缀 | worktree |
|----------|-----------|---------|
| Feature | `feature/` | 必 |
| 敏捷需求 | `agile/` | 必 |
| Bug | `fix/` | 必 |
| Micro | `micro/` | 必 |
| Feature Planning | — | 不进状态机 · 不走 prepare |
| 问题排查 | — | 不进状态机 · 不走 prepare |

**worktree path 默认** = `{worktree_root_path}/{Feature-ID}` ·
其中 `worktree_root_path` 解析顺序:
1. `state.json.environment_config.worktree_root_path`(已存在 Feature)
2. 项目根 `.teamwork_localconfig.json` 的 `worktree_root_path` 字段
3. 默认 `.worktree`(项目根子目录)

完整规范见 [docs/conventions.md § 9-11](./conventions.md)。

---

## 4. Step 3 · emit 完整表格(1 次完整 · 不分多轮)

PMO 复制给用户 · 🔴 **必含全 5 段**(漏任一段 = R5 暂停点违规 · 用户可叫停):

1. `# 流程概览`(流程目标 + flow_type + stage 链 + 理由)
2. `# 建议评审角色`(stage × 评审角色 × 建议理由表 · 数据从 `prepare-check --flow-type` 渲染)
3. `# 上下文准备(Step 0 已读)`(Planning ship / 上游依赖 / 代码现状 / ID 冲突)
4. `# Worktree 策略`(branch 前缀 + worktree_root_path + 推荐 path)
5. `# 4 项配置`(artifact ID + merge_target + worktree path + branch)

```markdown
⏸️ Prepare · 进入流程前总览(回 `ok` / `all default` 全用推荐 · 或修改某几项 + 确认)

# 流程概览
📋 **流程目标**:<1-2 句概述本次流程要达成什么 · 从用户原文/BL 描述提炼 · Feature/敏捷需求=需求目标(给谁 · 什么能力/价值)· Bug=解决目标(问题现象 → 期望修复后行为)· Micro=改动目标 · 写「要什么」不写「怎么做」>
📋 **流程类型**:<flow_type>(命中关键词 /<keyword>/)
📋 **stage 链**:<完整 stage 链 · 由 FLOW_BY_TYPE[flow_type] 渲染>
📋 **理由**:<识别理由 1 句>

# 建议评审角色 🔴(初步建议 · 各 stage 进入时可按方案复杂度调整)
> 数据从 `prepare-check --flow-type` 输出 `stage_chain_preview` 渲染 · **不可跳过**。

| stage | 必/选 | 建议评审角色 | 建议理由 |
|---|---|---|---|
| <stage> | <必跑/可选(若可选括号注触发条件)> | <reviewers 列表 / — (无 reviewer)> | <从 reason 字段渲染 · 1 句话为什么这些角色> |
| ...(每 stage 一行) | | | |

📎 reviewers="—" 表示 stage 无多角色评审(dev = RD 自写代码 + git commit / ship = PMO 编排 push+MR)。
📎 **初步建议 · 可调整**:
  - 各 stage-start 时 state.py 会再次输出本 stage 的「建议评审角色」段 · AI 按方案复杂度判定是否需调整
  - 简单方案可去 external · 高风险方案补 architect/external
  - **调整命令**:
    ```bash
    state.py change-review-roles --feature <path> --stage <stage> --roles 'a,b,c' --reason '<理由>'
    ```
    自动写 `stage_review_roles_adjustments` audit · 后续 stage-complete 校验按新值。

# 上下文准备(Step 0 已读)
- **Planning ship 状态**:<✅ <Planning Feature ID> · commit ... merge 到 staging | ⏭️ N/A>
- **上游依赖**:<✅ <list> | ⏭️ 无外部依赖>
- **当前代码现状**(可选):<1 句话总结 | ⏭️ 跳过>
- **ID 冲突扫描**:<已占 [<ids>] · 推荐 <next_available_id>>

# Worktree 策略
- **branch 前缀**:<feature/ | agile/ | fix/ | micro/>(由 flow_type 决定)
- **worktree_root_path**:<.worktree | ../<repo>-worktrees>(读 .teamwork_localconfig.json · 默认 .worktree)
- **推荐 path**:`{repo-root}/{worktree_root_path}/<Feature-ID>`

# 4 项配置(默认推荐 · 可改)
| # | 字段 | 推荐 | 理由 |
|---|---|---|---|
| 1 | **artifact ID** | <prepare-check `next_available_id_stem` · 字母 F/B/M 按 flow_type> | <冲突避让 + 业务命名> |
| 2 | **merge_target** | staging | <与项目历史 Feature 一致> |
| 3 | **worktree path** | <推荐 path 同上> | 默认 worktree_root_path |
| 4 | **branch** | <branch-prefix><Feature-ID-kebab-case> | 与 ID 一致 |

📎 **是否需要 UI Design Stage** 由 goal-complete 时 `--needs-ui` 决策 · prepare 入口不强制提前拍板。
```

flow_type → first_stage 映射:
- Feature / 敏捷需求 → `goal`
- Bug → `diagnose`(根因细查 + 修复方案 · 用户确认后才进 dev · 防修偏)
- Micro → `dev`
- Feature Planning / 问题排查 → 不进状态机 · prepare 在这两个流程上不调用

🔴 **必 1 次完整 emit · 不分多轮**(防 PMO 先建议 + 再"最终确认"的 2 轮交互浪费)。
🔴 **用户回 `ok`** · PMO 视作"按建议全部默认值" · 不再二次确认 · 立即执行 §5。

### 4.1 · emit 自检清单(PMO emit 前自查 5 段齐)

- [ ] § 流程概览(流程目标 + flow_type + stage 链 + 理由 · 目标 = 用户 review 第一校准点:AI 对目标理解偏 → 后面全偏)
- [ ] § 建议评审角色(prepare-check `stage_chain_preview` 表已渲染 · 不可漏)
- [ ] § 上下文准备(4 子项:Planning / 上游 / 代码 / ID 冲突)
- [ ] § Worktree 策略(branch 前缀 + worktree_root_path + 推荐 path)
- [ ] § 4 项配置(artifact ID + merge_target + worktree path + branch)

任一项缺 → 重 emit(用户不应被迫忽略漏段)。

---

## 5. Step 4 · 用户确认后 · PMO 显式执行

```bash
# 用户回(或 all default):
# 1. Feature ID: PTR-F033
# 2. merge_target: staging
# 3. worktree path: <repo>/.worktree/PTR-F033
# 4. branch: feature/PTR-F033

# PMO 跑(在主工作区 cwd · 不是 worktree):
git fetch origin
git worktree add -b feature/PTR-F033 <worktree-path> origin/staging
cd <worktree-path>

# 此刻 cwd 在 worktree 内 · 进状态机:
state.py init-feature \
 --feature docs/features/PTR-F033 \
 --feature-id PTR-F033 \
 --flow-type Feature \
 --merge-target staging \
 --branch feature/PTR-F033 \
 --worktree-mode auto \
 --worktree-path <worktree-path>
```

🔴 **Bug 流程先 diagnose**:Bug 首 stage = `diagnose`(不是 dev)。`diagnose-start` → 🔴 **深读代码做根因细查**(triage/prepare 读的代码往往不够细)→ 写 `bugfix/BUG-<bug-id>.md`(模板 `templates/bug-report.md` · frontmatter `bug_id/symptom/root_cause/fix_summary` + §现象/§根因/§修复方案)→ 🔴 **把修复方案给用户确认(R5)** → `diagnose-complete` → dev 才按确认的方案写 fix。治本「浅确认 → dev 一口气写报告+fix 修偏」。详 [stages/diagnose-stage.md](../stages/diagnose-stage.md)。

---

## 6. 与状态机的接口

prepare 完成 = init-feature 前置满足:
- ✅ flow_type / feature_id 已用户确认
- ✅ worktree 物理已创建(PMO 显式跑)
- ✅ cwd 在 worktree 内(PMO 显式 cd)
- ✅ branch / merge_target 已用户确认

**init-feature 拒绝条件**(状态机入口物化拦截):
- worktree_mode != off 但 cwd 不在 worktree → FAIL
- worktree_mode != off 但 worktree 物理不存在 → FAIL
- flow_type ∈ {Feature Planning, 问题排查} → reject(不进状态机)

**prepare 不做的事**:
- ❌ 不写 state.json(state.json 由 init-feature 创建)
- ❌ 不创建 worktree(由 PMO 显式跑)
- ❌ 不自动跑 git(防漏看用户确认)

---

## 7. 错误处理

### 7.1 · 流程类型识别错(关键词模糊)

PMO 识别不准 → 在暂停点列出"我猜是 X · 你确认是 Y/Z?"让用户拍板。

### 7.2 · 用户拒绝 worktree 默认值

部分用 default + 部分自定 → PMO 用混合值跑 git worktree add。
全否决 → 等用户给完整 4 项。

### 7.3 · git worktree add 失败

- branch 已存在 → `git worktree remove <path>` + `git branch -D <branch>`
- origin/base 不存在 → `git fetch origin`
- path 已存在但非 worktree → 删 path 或换 path

错误处理由 PMO 主导 · 不在 state.py 状态机里。

---

## 8. 红线

### R-P1 · 必经用户确认

prepare 输出暂停点后 · 必须等用户明确回 4 项配置(或 "all default")。
**不可** PMO 自己拍板 worktree path / branch / merge_target。

### R-P2 · 用户未确认前不进状态机

PMO 在用户未确认前 · **不可** cd / git worktree add / init-feature。
违规 = 主 tree 污染风险。

### R-P3 · 不可枚举判断留 PMO

意图总结 / 流程类型识别的不可枚举部分 → PMO 主对话判断(模糊时问用户)。
关键词表是辅助 · 不是强制 · PMO 可基于上下文覆盖默认。

---

## 9. 相关文档

- [SKILL.md § Triage 入口规范](../SKILL.md) — 5 mode 入口分诊(prepare 由 mode B / mode E 升级触发)
- [docs/feature-planning.md § 5](./feature-planning.md) — Feature Planning 完成后启 Feature 走 prepare
- [docs/conventions.md](./conventions.md) — Feature ID + worktree path 编号规范
- [SKILL.md](../SKILL.md) — 顶层叙事 + 项目级文档信息架构
- [SKILL.md § PMO 软约束 + 暂停点标准格式](../SKILL.md) — R5(b) PMO 必读
