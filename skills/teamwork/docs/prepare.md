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

🔴 **PMO 必先 Read 本 prepare.md(工具调用)再 emit 任何 prepare 内容** —— SKILL.md 只给"移交 prepare 子流程"指针 · 具体 emit 模板(🎯 意图确认 + ⚙️ 配置)/ 准入校验 / prepare-check 用法都在本文件。不读直接 emit = R5 违规(详 §0.5 #1)。

---

## 0.5 反模式黑名单

🔴 **AI 凭直觉 / 短回路跳步骤 · 大概率被用户叫停重做 · 不省 token · 反多消耗**。以下都是 R5 违规 · 列出供 PMO 自检:

| # | 违规 | 触发场景 | 治本 spec 位 |
|---|---|---|---|
| 1 | 漏 Read 本 prepare.md · 凭 SKILL.md「移交 prepare」概览就 emit | mode B 首次触发 prepare | § 0 必读 |
| 2 | 漏跑 `prepare-check` · 用 `ls` / `grep` 手算 next ID | 「目录看一眼就知道」 | § 1.5.4 |
| 3 | 跑 `prepare-check` 但漏 / 错 `--features-root`(没传子项目对应 docs_root)→ 拿主 tree 结果 → 错号 | monorepo 子项目场景(`apps/partner` 在 PTR namespace) | § 1.5.4 + conventions §1 |
| 4 | `prepare-check` 未叠加 worktree branch 上 in-flight Feature 占用的 ID → 撞号 | 并行 Feature 多 worktree 时 | § 1.5.4 |
| 5 | 关键词命中即推流程类型 · 漏 §2.2 准入**反向扫描**("加按钮"→ 敏捷需求 · 没扫"改 UI 结构"信号) | 用户原文含 UI 调整 / 加组件 / 改布局 / 改交互 | § 2.2 |
| 6 | 漏「🎯 我的理解」意图确认段 / 把意图埋到配置后 / 🧩 假设不摊开(只给干净 restatement)| 短回路("配置够了" · 或怕暴露假设) | § 4 |
| 7 | 现象类输入未排查直接定 Bug + emit prepare(「代码现状」填未验证猜测 · 命名/路由押在猜测上) | 用户只给现象(CI 失败/报错/挂了)· 无修复指令 | § 2 排查先行律 |

🔴 **AI 短回路 ≠ 用户授权**:用户给短指令("改下页面")**不等于** AI 可跳意图确认。指令越短 · AI 补的假设越多 · 越**该**摊开让用户校(短指令恰是误读高发区)· AI 无权省。

🔴 **PMO 自检顺序**(动手 emit 前过一遍 · 任一 ❌ 即重来):
1. ✅ 我读完本 prepare.md 全文了吗?
2. ✅ 我跑过 `prepare-check --features-root <子项目对应 docs_root> --flow-type <type>` 了吗?
3. ✅ 我手动 `git worktree list --porcelain | grep -oE '<PREFIX>-[FBM][0-9]+'` 叠加占用 ID 了吗?
4. ✅ 我反向扫过 §2.2 准入信号(UI / 架构 / 文件数)了吗?(关键词命中 ≠ 流程类型推完)
5. ✅ 我 emit 的「🎯 我的理解」在最前 + 🧩 假设摊开了吗?(§4.1 自检清单)

📎 **已物化的拦截**(工具层兜底 · 不依赖意志力):`init-feature` 门禁(本 session 未为该 prefix 跑过 prepare-check → FAIL with hint · 无 audit 不可 init-feature);`prepare-check --user-intent + --admission-judgment`(用户原文留痕 + AI 判断 JSON schema 校验 · recommended vs `--flow-type` MISMATCH → WARN · 不用 regex 关键词扫描:可枚举的进脚本、不可枚举的留 AI)。
📎 其余拦截待物化项属框架维护 backlog · 不在本运行时 spec 内跟踪(归框架仓 `docs/CHANGELOG.md` / `docs/RETRO-LEDGER.md`)。

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
- Planning **未 ship** 才入暂停点 ⚠️ 异常行(已 ship / N-A → 不显 · 全绿不噪)

无 Planning(直接 mode B execute)→ 跳此项。

### 1.5.2 · 检上游依赖(state.json blocking)

若 prepare 是从已有 Feature 衍生:
- 检上游 Feature 的 `state.blocking.pending_external_deps`
- **有待中依赖**才入暂停点 ⚠️ 异常行(全就绪 → 不显)

无上游 → 跳。

### 1.5.3 · 扫代码现状(可选 · 1 句话总结)

可选(高复杂度 Feature 推荐):
- grep 关键模块当前实现(如「<核心模块> 当前只支持 X 场景 / 关键分支硬编码」的一句话现状)
- 1 句话总结 · 喂「🎯 我的理解」的 📦 范围 / 🧩 假设(让用户据代码现实校启动方向)

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

prepare-check 输出 `reviewer_thinking_checklist` 4 个核心问题 · PMO 据此**设定实际评审角色 + stage 链**(结果进默认 · 暂停点「⚙️ 配置」段一行带过 · 不铺表):

| # | 问题 | 命中调整 |
|---|---|---|
| Q1 | 有产品方向影响?(业务目标 / 用户可见 / 商业模式 / 跨项目一致 / 变更级联 Level≥2) | **是**(常态)→ goal **留 pl** + goal §3 PL 质疑走 **subagent 隔离版**(详 goal-stage §3);仅纯内部技术重构 · 零产品面才去 pl · ⚠️『无 ROADMAP』**不是**去 pl 理由(ROADMAP=规划层 · 与 PRD 产品方向评审无关) |
| Q2 | 含 UI 改动? | 否 → ui_design 跳过 + browser_e2e 跳过 |
| Q3 | 跨 ≥3 module 触发点 / 调用方? | 是 → blueprint / review 强 external(异质模型查漏触发) |
| Q4 | 数据模型重构(删/改老字段 · 表结构变)? | 是 → blueprint 强 architect + 加 dba 评审 |

🔴 **pl 不是套路化删**:pl 默认保留(产品方向视角 · 防 Feature 偏离产品方向)· 去 pl 是**少数例外**(纯内部 / 技术重构 · 零产品面 · 零跨项目)· 必给该 Feature 特定理由 · 不得拿『无 ROADMAP』当通用借口(几乎所有执行层 Feature 都『无 ROADMAP』· 那是规划层的事)。

**不直接抄默认**:据本 Feature 实际(前后端先行 / 模块数 / 是否需 ui_design)给评审角色加减预估 · 不照搬 stage_chain_preview(后端先行→ui_design 可跳 · 跨多 module→blueprint 强 external)。

🔴 **Q1-Q4 思考的结果进默认 · 不在 prepare 暂停点铺成表**(信噪比):据 4 问设定实际 `stage_review_roles` + stage 链(如留 pl / 跳 ui_design / blueprint 加 external)· 暂停点「⚙️ 配置」段只用**一行**带过(`评审:各 stage 按 flow 默认 · 已据 Q1-Q4 设 · stage-start 再确认`)· 各 stage-start 时 state.py 会再 emit 本 stage 建议角色(prepare 重列 = 噪音)。用户想**全局**调评审强度 → 暂停点回一句即可。

---

> 🔴 v8.220:流程类型机器层 = Feature/Bug + `--preset full|lite|micro`(敏捷需求→lite · Micro→micro 自动映射)· 关键词命中「敏捷/micro」= 推荐对应 preset 而非独立类型。

## 1.5 明确度判定(clarity · v8.215 智能分诊 v1 · 证据先行)

🔴 **「看过再判」**:流程类型判定前先做 30 秒侦察(grep 候选改动面 / 查 KNOWLEDGE / 新依赖)· 填 `prepare-check` emit 的 `triage_evidence` 槽(**空着不给判**)· 据证据判 `clarity`:

- **explicit**(明确):用户给出明确方案 **或** 机械映射类(外化/重命名/迁移/升级)且无新业务行为。🔴 v8.216:clarity **仅记录**(`init-feature --clarity` → state · 台账/年检校准)· **评审配置由 AI 动态决策** —— 按 emit 的 `role_value_criteria` **逐 stage 逐角色**判「对本 feature 有没有值」(可去 pl 也可去 qa/architect/external · 每角色一行理由)→ `change-review-roles --reason` 配 roster(审计留痕 · gate 按 roster 自动放行)· review stage 从严(建议 ≥2 视角 · <2 需强理由)。
- **ambiguous**(模糊):一句话含方向词 / 多方案可选 → goal 深门(既有)。
- **normal**(默认):其余。

🔴 解耦「大」和「不确定」:改动面大 → Feature **骨架**(worktree/状态机/测试门);不确定性低 → **评审走轻档**。prepare 暂停点向用户显示判定(可一字改)。

## 2. Step 1 · 流程类型识别(6 闭集 · R2 红线)

PMO 按以下关键词表判定 user input 落入哪类流程:

| 关键词模式 | 流程类型 |
|----------|---------|
| 规划 / Feature Planning / feature planning / 更新 roadmap / 拆 roadmap / 路线图 / 全景 / 做电商 / 做 SaaS / 商业模式调整 | **Feature Planning** |
| 排查 / 查 log / 诊断 / why X 慢 / 调研 / 分析根因 · 🔴 以及一切**根因未定的现象类输入**(报错 / 挂了 / CI·编译失败 / 慢 · 无修复指令) | **问题排查**(排查先行律 · 见下) |
| 修复 / fix / 处理掉 X bug / 生产缺陷 · 🔴 仅当**缺陷已指认**(用户明确要求修复 · 或 现象+期望+大致位置已知) | **Bug** |
| 换 logo / 换图 / 改文案 / 改样式 / 改颜色 / 改配置常量 | **Feature · preset=micro** |
| 加按钮 / 加导出 / 加字段 / 列表加列 | **Feature · preset=lite** |
| 实现 / 开发 / 做功能 / 新建模块 | **Feature**(兜底)|

落入 6 闭集之一(R2 红线 · enum 强制)。

🔴 **排查先行律**(现象类输入不排查就定 Bug 的后果:「代码现状」填上未验证猜测 · 命名/前缀路由/worktree 全押在猜测上 · 真因若在别的子项目就全配错):
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

| flow_type(+preset) | branch 前缀 | worktree |
|----------|-----------|---------|
| Feature(full/lite/micro 全部)| `feature/` | 必(🔴 v8.220 统一 · `agile/`/`micro/` 前缀退役)|
| Bug | `fix/` | 必 |
| Feature Planning | — | 不进状态机 · 不走 prepare |
| 问题排查 | — | 不进状态机 · 不走 prepare |

**worktree path 默认** = `{worktree_root_path}/{Feature-ID}` ·
其中 `worktree_root_path` 解析顺序:
1. `state.json.environment_config.worktree_root_path`(已存在 Feature)
2. 项目根 `.teamwork_localconfig.json` 的 `worktree_root_path` 字段
3. 默认 `.worktree`(项目根子目录)

完整规范见 [docs/conventions.md § 9-11](./conventions.md)。

---

## 4. Step 3 · emit 暂停点(🎯 意图 + ⚙️ 配置 · 1 次完整 · 不分多轮)

PMO 复制给用户 · 🔴 **意图确认在最前** —— 它是用户 review 的**第一校准点**(AI 对意图理解偏 → 后面全偏)· 配置塌一段(均默认)· 异常才展开:

1. `# 🎯 我的理解`(意图确认 · **暴露补的假设** · 每次必出 · 在最前)
2. `# ⚙️ 配置`(flow + stage 链 + 4 项配置 + 评审一行 · 均默认可改)
3. `⚠️ 异常行`(仅上游未就绪 / ID 撞号 / Planning 未 ship 时出 · 全绿不显)

🔴 **信噪比**:执行 setup 领头会被 `ok` 盖章、把意图埋成一行 restatement → 误读搭便车溜过。意图提前 + **摊开「你没说、我替你补的假设」** = 用户一眼抓误读;评审表不在此展开(各 stage-start 会再 emit · prepare 重列 = 噪音)。

```markdown
⏸️ Prepare(回 `ok` 全默认 · 或纠正某项)

# 🎯 我的理解(先确认这个 · 下面配置可 default)
🗣️ 你说的:「<用户原话节选 · 源 --user-intent>」
🎯 理解:<要达成什么 · 1-2 句 · 要什么不写怎么做>
🧩 我补的假设〔仅「我假设你**想要** X」类意图解读 · 非平凡才列 · 否则写「请求明确 · 无补」〕:
   - <你没明说、我按 X 理解的点 · 错了请纠 · 源 admission-judgment.ai_rationale>
📦 范围:做 <Y> · 不做 <Z>
🔁 既有行为:<改「原 A → 现 B」· goal 将升级为待决策项 | 否 · 不动既有默认行为>

# ⚙️ 配置(均默认 · 改某项才说 · 回 `ok` 即全默认)
flow=<Feature> · 链=<goal→…→ship · 已反映 ui_design 跳过等> · ID=<PTR-F033> · merge_target=<staging> · wt=<.worktree/PTR-F033> · branch=<feature/ptr-f033>
评审:各 stage 按 flow 默认(已据 §1.5.4 Q1-Q4 设:如留 pl / 跳 ui_design / 加 external)· stage-start 再确认 · 高风险想**全局**加 external 现在说

⚠️ <上游依赖未就绪:… | ID 撞号:… | Planning 未 ship:…> ← 仅有问题才出此行 · 全绿删除
```

🔴 **意图段全是 prepare-check 已采数据**(非即兴):🗣️=`--user-intent` 原话 · 🎯🧩=`--admission-judgment.ai_rationale` 解读。🧩「补的假设」是抓误读**核心零件**(干净 restatement 会把假设藏起)· 无非平凡假设时显式写「请求明确 · 无补」(证明想过)。
🔴 **🧩 只列意图解读假设**(「我假设你**想要** X」· 用户域 · 用户能直接拍)· **禁抛未验证的代码/可行性猜测**(「我假设后端有 X 列」)—— 那归 §1.5.3「代码现状只写已验证事实」+ 反模式 #7:要么先验证再写,要么留给 goal 调研后的**深门**。prepare 在强制读代码**之前** · 此处抛代码猜测 = 让用户确认 AI 本该去查的事(误导 review)。
`ok` = 意图在最前的**知情**点头 · 非盲签。

flow_type → first_stage 映射:
- Feature / 敏捷需求 → `goal`
- Bug → `diagnose`(根因细查 + 修复方案 · 用户确认后才进 dev · 防修偏)
- Micro → `dev`
- Feature Planning / 问题排查 → 不进状态机 · prepare 在这两个流程上不调用

🔴 **必 1 次完整 emit · 不分多轮**(防 PMO 先建议 + 再"最终确认"的 2 轮交互浪费)。
🔴 **用户回 `ok`** · PMO 视作"按建议全部默认值" · 不再二次确认 · 立即执行 §5。

### 4.1 · emit 自检清单(PMO emit 前自查)

- [ ] § 🎯 我的理解(🗣️原话 + 🎯理解 + 🧩假设〔非平凡解读必摊开 · 否则「无补」〕+ 📦范围 + 🔁既有行为)· **在最前 = 第一校准点**
- [ ] § ⚙️ 配置(flow + stage 链 + ID + merge_target + wt + branch + 评审一行 · 均默认)
- [ ] ⚠️ 异常行(上游 / 撞号 / Planning · **仅有问题才出** · 全绿无此行 = 正常)

🔴 意图段缺 / 埋到配置后 / 🧩假设藏起不摊开 → 重 emit(误读会溜过)· 信噪比倒置违规。

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
