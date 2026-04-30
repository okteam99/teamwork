# Changelog

## v7.3.10 + P0-65（当前）

> v7.3.10+P0-65 Codex 沙箱下 Claude CLI 认证实战指南：用户实证 Codex 主对话宿主下 OAuth 登录态被沙箱屏蔽（沙箱外 `claude auth status` 已登录 / 沙箱内 Not logged in），找到 `CLAUDE_CODE_OAUTH_TOKEN` env var 作为最优解（复用 Pro/Max 订阅 + 跨沙箱稳定 + 不占 API 计费）。本 patch 把这个实战经验加进 claude-agents 文档，并按推荐度排列三种认证方式（A/B/C）。

### P0-65：claude-agents 加 Codex 沙箱认证指南

- 触发：用户实战诊断 Codex CLI 主对话宿主下 Claude CLI 认证踩坑（OAuth keychain 不穿透沙箱）+ 验证 `claude setup-token` + `CLAUDE_CODE_OAUTH_TOKEN` 路径可行
- 设计哲学：把实战教训写进文档（不是猜测），帮后来者省一晚上
- 改动：
  - **P0-65-1. claude-agents/README.md 加「认证方式」段**：3 种方式按推荐度排（A OAuth / B `CLAUDE_CODE_OAUTH_TOKEN` / C `ANTHROPIC_API_KEY`）+ 适用场景对比表 + Codex 沙箱限制实证 + 方式 B 配置步骤 + 官方文档链接（cli-reference / iam / env-vars）
  - **P0-65-2. claude-agents/invoke.md 顶部加 Codex 沙箱特殊处理提示** + 链接到 README.md
  - **P0-65-3. README.md 前置条件表 #2「认证」措辞改宽容** → 三种方式之一（之前只列 OAuth + ANTHROPIC_API_KEY 两种）
  - **P0-65-4. 版本号 + CHANGELOG**（7.3.10+P0-64 → 7.3.10+P0-65）
- **加 1 删 1 元规则核算**：
  - **加**：~30 行实证文档（认证方式表 + 配置步骤 + 官方文档链接）
  - **删**：未删（实战教训沉淀，不是冗余清理）
  - **新增价值**：A/B/C 三方式明确定位 + Codex 沙箱踩坑实证 + 官方文档链接（避免后来者从零摸索）
- 不动：
  - detect-external-model.py（不查 OAuth/API key 的设计原则不变）
  - state.json schema（external_cross_review 字段不变）
  - E3 失败降级流程（dispatch 失败时 state.concerns WARN 不变）
- 影响面：2 文件（claude-agents/README.md +30 行 / claude-agents/invoke.md +1 行）+ 元数据
- 后续：如发现新的认证踩坑（如 Linux 上 `secret-tool` 沙箱也类似问题），加进同一段

---

## v7.3.10 + P0-64

> v7.3.10+P0-64 删 localconfig.external_model 强制覆写规则（虚构边缘场景）：用户反馈"localconfig 强制设 external_model=codex 的逻辑去掉吧"。盘点确认：框架本来就**没给用户开 localconfig.external_model 字段**——detect-external-model.py 不读 / feature-state.json schema 不读 / config.md 没定义。standards/external-model.md L55 的"用户硬塞同源 = WARN 降级"是纯防御性虚构条款（防一个不存在的口子）。本 patch 删掉这条，简化为"由探测 + E1 自动决定，用户不可覆写"的清晰边界。

### P0-64：删 localconfig.external_model 虚构覆写条款

- 触发：用户"`.teamwork_localconfig.md` 强制设 external_model=codex 的逻辑去掉吧"
- 设计哲学：**砍掉防御性虚构条款** —— 框架不开放的口子不应该写"防御"规则；规则应该描述实际行为，不是描述虚构反例
- 改动：
  - **P0-64-1**：standards/external-model.md L55 删原"WARN 降级"防御条款 → 替换为"由探测 + E1 自动决定，用户不可覆写"的清晰边界声明
  - **P0-64-2**：版本号 + CHANGELOG（7.3.10+P0-63 → 7.3.10+P0-64）
- 盘点确认（不动的部分）：
  - **detect-external-model.py**：本来就不读 localconfig，仅探测 .claude/.codex/.agents/ 目录标记 + PATH CLI 可用性
  - **feature-state.json schema**：external_cross_review 对象 frontmatter 字段不含 user_override
  - **templates/config.md**：没有定义 external_model 作为 localconfig 字段
  - **roles/pmo.md**：引用 external-model.md 不复述本规则
- **加 1 删 1 元规则核算**：
  - **加**：1 行简化声明（"用户不可覆写"）
  - **删**：1 行防御性虚构条款（"用户硬塞同源 = WARN 降级"）
  - **净变化**：±0 行 / 但**移除虚构反例 = 规则更清晰** + 防止后续 patch 在虚构条款上加规则
- 不动：E1 同源约束本身（这是真实有效的规则）/ Claude Code → codex / Codex CLI → claude / 通用宿主 → 都可用 三条映射保留
- 影响面：1 文件（standards/external-model.md L55）+ 元数据
- 后续：如果将来真要开放用户覆写（业务诉求场景），再在 templates/config.md 显式加字段 + detect-external-model.py 加读取逻辑 + state.json schema 加字段 —— **届时再加规则，不再做防御性预留**

---

## v7.3.10 + P0-63

> v7.3.10+P0-63 TDD 单源化（standards/tdd.md 抽取）：参考 obra/superpowers test-driven-development skill 的"Iron Law + RED-GREEN-REFACTOR 强制" 思路。当前 Teamwork TDD 规则散在 5 处（standards/common.md §一 / §QA / dev-stage.md §2 / §2.1 / review-stage.md QA Step 4 / roles/rd.md），措辞重叠也有差异，新角色加 TDD 描述时不知该 cite 哪。本 patch 抽取 standards/tdd.md 作为唯一权威源（~110 行 / Iron Law + 5 步流程 + 自检 + 反模式 + 例外 + ≥3 次失败升级），5 处散落点改为引用化。

### P0-63：TDD 单源化（standards/tdd.md 抽取）

- 触发：之前对比 obra/superpowers 时识别出的"散落收敛"价值；用户拣选执行
- 设计哲学：**TDD 规则是横切关注点**（多 stage / 多 role 共用）→ 应单源 / 各处 cite。其他 standards/*.md 已是这种模式（output-tiers / external-model / prompt-cache / stage-instantiation）
- 新建 standards/tdd.md（~110 行）：
  - **§一 Iron Law**：NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST（借 superpowers 措辞）
  - **§二 RED-GREEN-REFACTOR 5 步流程**：迁自 dev-stage.md §2 + 加 VERIFY RED / VERIFY GREEN 两步显式化
  - **§三 自检清单**：8 条（迁自 standards/common.md §一）
  - **§四 反模式**：6 条（合并 roles/rd.md 反模式段 + 新增）
  - **§五 例外**：5 类（throwaway / 生成代码 / 配置 / 简单方案用户授权 / Micro 流程）+ state.json.concerns 落记录硬规则
  - **§六 ≥3 次失败升级**（新增）：同一 GREEN step 失败 3 次 → 重读 TECH / 升级架构师 review
  - **§七 引用约定**：列出各位置如何 cite
- 散落点引用化（5 处）：
  - **standards/common.md §一 TDD 检查清单** → 引用 tdd.md（保留 8 条快查 · 详细规则去权威源）
  - **standards/common.md §QA 代码审查 TDD 规范检查** → 引用 tdd.md §三 + §四（保留 5 条快查）
  - **stages/dev-stage.md §2 TDD 开发流程** → 整段引用 tdd.md §二（保留 Step 5b UI 还原 Dev Stage 特有补充）
  - **stages/dev-stage.md §2.1 开发约束** → 引用 tdd.md §一 + §四 + §五（保留 4 条 Dev Stage 特有约束如禁 TODO/FIXME）
  - **stages/review-stage.md QA Step 4 TDD 规范检查** → 引用 tdd.md §三 + §四（之前是引用 standards/common.md，改为直引权威源）
  - **roles/rd.md「测试先行」** → 引用 tdd.md
- 索引更新：
  - **STANDARDS.md** 加 tdd.md 行（标"🔴 TDD 唯一权威源"）+ Subagent 加载指引加 tdd.md 必读
  - **SKILL.md** 文件索引加 tdd.md 行
- **加 1 删 1 元规则核算**（P0-48 标尺）：
  - **加**：standards/tdd.md ~110 行（新建权威源）
  - **删**：dev-stage.md TDD 开发流程详细 ~25 行 + 开发约束 ~7 行 + standards/common.md TDD 检查清单详细 ~13 行 + TDD 规范检查 ~9 行（共 ~54 行被引用替换）
  - **净加**：~56 行（建立单源的成本 · 但收益是后续所有 TDD 规则修改只动一个文件）
  - **新增价值**（之前没有的）：§六「≥3 次失败升级」（症状性修复反模式防护，对应 systematic-debugging Iron Law 的简化版）+ §五「例外」明确化 + 5 处引用机制建立
- 不动：
  - 各 stage spec 中 "TDD 红绿循环" 词汇本身（描述性，不破坏）
  - PRD frontmatter / TC frontmatter（数据契约）
  - verify-ac.py 机器校验
- 影响面：
  - 改动文件：7 个（新增 standards/tdd.md / standards/common.md ×2 段 / dev-stage.md / review-stage.md / roles/rd.md / STANDARDS.md / SKILL.md / 元数据 init-stage.md / docs/CHANGELOG.md）
- 后续验证：
  - 下次 Dev Stage 实战，确认 RD 起草 TDD 时 cite 的是 standards/tdd.md（而不是散落点）
  - 如发现新的 TDD 反模式，加进 tdd.md §四（单源补充，自动 propagate）

---

## v7.3.10 + P0-62

> v7.3.10+P0-62 emoji 间隔硬规则化（状态行可点击性修复）：用户实战截图反馈状态行第二行 `📁/Users/...` 没有空格，终端把 emoji 和路径视为一体，不可点击。框架现有示例本来都是带空格的（`📁 /Users/...`），但缺少显式硬规则约束，PMO 起草时偶尔会漏空格。本 patch 在 STATUS-LINE.md「状态行规则」段加 emoji 间隔硬规则 + 在 output-tiers.md §三-A 加同步条款。

### P0-62：emoji 与内容之间强制空格（用户体验修复）

- 触发：用户截图实证 PMO 输出 `📁/Users/...` 不可点击
- 设计哲学：**显式硬规则覆盖隐性约定**——示例都对，但没有规则就靠"自觉"，PMO 起草时会漏。加显式规则 + 正反例对比即可
- 改动：
  - **P0-62-1. STATUS-LINE.md 加 emoji 间隔硬规则**：状态行规则段最末加一条「所有图标（📁 / 🌿 / 📍 / ⚡ / 🌐 / 🔄 / 🔗 / ⏸️ 等）与其后紧随的文字内容之间必须保留一个半角空格」+ 正反例对比
  - **P0-62-2. STATUS-LINE.md L62 增强措辞**：从「必须输出 📁 绝对路径」→「必须输出 \`📁 {绝对路径}\`（emoji 与路径之间必须有一个空格）」
  - **P0-62-3. output-tiers.md §三-A 同步加规则**：暂停点资产指针也遵守同规则（暂停点和状态行的格式约束统一）
  - **P0-62-4. 版本号 + CHANGELOG**：7.3.10+P0-61 → 7.3.10+P0-62
- **加 1 删 1 元规则核算**：
  - **加**：3 处硬规则 / 正反例 ≈ 5 行
  - **删**：未删（这是用户体验补强）
  - **不增加 PMO 负担**：只是把"自觉"升格为"硬规则"，PMO 起草时本来就该带空格，只是有时漏
- 影响面：
  - 改动文件：4 个（STATUS-LINE.md / standards/output-tiers.md / SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
  - 行数变化：STATUS-LINE.md +2 行 / output-tiers.md +1 行
- 后续验证：
  - 下次状态行 / 暂停点输出查看是否有 `📁 /Users/...` 带空格 + 路径在终端里可点击
  - 如发现 PMO 仍漏空格，加进 STATUS-LINE.md 反例对比段

---

## v7.3.10 + P0-61

> v7.3.10+P0-61 暂停点资产路径硬规则化（完整绝对路径）：用户反馈"涉及用户确认时，输出一下待确认文档的目录或文件路径（完整路径，非相对路径）方便用户查看"。当前框架在暂停点常输出相对路径（如 `apps/partner/docs/features/PTR-F016/PRD.md`），终端 / IDE 大多不识别相对路径为可点击 hyperlink。本 patch 在 standards/output-tiers.md（输出规范单源）加「三-A 待确认文档绝对路径硬规则」段，强制 PMO 在所有用户需要确认/查看的暂停点输出完整绝对路径。

### P0-61：暂停点资产绝对路径硬规则（用户体验提升 · 单源加一段）

- 触发：用户实战 PTR-F016 triage case 反馈"完整路径方便点击查看"
- 设计哲学：**单源化 + 体验性硬规则**——只动 standards/output-tiers.md（一个文件 + 一段段），不改各 stage spec / 不加 PMO 主动职责段（PMO 起草暂停点时自然遵循新规则）
- 改动：
  - **P0-61-1. Tier 1 描述加一行**：`待确认文档/目录的完整绝对路径（v7.3.10+P0-61 — 见下方硬规则 §三-A）`
  - **P0-61-2. 加「三-A 待确认文档绝对路径硬规则」段**：触发条件 + 4 条硬规则 + 输出格式模板 + 正反例对比 + 例外条款
  - **P0-61-3. 版本号 + CHANGELOG**：7.3.10+P0-60 → 7.3.10+P0-61
- 硬规则核心 4 条：
  - 必须以 `/` 开头的完整绝对路径
  - 禁止仅输出相对路径
  - 路径 = `pwd` + `state.artifact_root` + 资产文件名
  - 多文件用列表呈现 / 是目录就输出目录路径
- 例外：
  - 资产不是文件（纯主对话渲染骨架 / 口头方向决策）→ 可不输出
  - 状态行 `📁 ...` 保留相对路径（非暂停点决策行）
- **加 1 删 1 元规则核算**（P0-48 标尺）：
  - **加**：~30 行硬规则段（standards/output-tiers.md）
  - **删**：未删（这是用户体验补强 · 不是冗余清理）
  - **不增加 PMO 负担**：PMO 在暂停点本来就要输出资产指针，只是改形态（相对路径 → 绝对路径），认知负担相同
  - **"重新触发回来"防护**：硬规则在 Tier 1 描述里 + 三-A 单立段 + 正反例对比 — 未来如有 PMO 起草输出回到相对路径，违反 Tier 1 + 三-A 双重硬规则
- 不动：
  - 各 stage spec（output-tiers.md 是单源 / 各 stage 通过引用机制自动继承）
  - PMO 角色文件（不加 PMO 主动检测职责 · 最简化原则）
  - state.json schema（不加 project_root 字段 · cwd 已经在主对话上下文）
  - status 行格式（保留相对路径 · 跟暂停点决策行的资产指针解耦）
- 影响面：
  - 改动文件：4 个（standards/output-tiers.md +30 行 / SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
  - 行数变化：standards/output-tiers.md 110 → ~140 行
- 后续验证：
  - 下次 triage / Goal-Plan / blueprint / review / PM 验收 等暂停点跑下来验证 PMO 是否正确拼绝对路径
  - 如果发现 PMO 在某些场景仍出相对路径，按本 patch 的"必砍"机制加进 standards/output-tiers.md 反例对比段

---

## v7.3.10 + P0-60

> v7.3.10+P0-60 triage Step 8 输出表格化 patch（卡片式骨架 + 必含/必砍清单）：用户基于实战 PTR-F016 triage 输出 ~85 行案例反馈"输出还是太多，能否精简，表格化，方便确认。最好输出内容统一一个模版"。诊断：Tier 1 实际只占 ~20 行，剩 ~65 行全是 Tier 2/3 越界（Why now 履职报告 / Real unknowns 详细 / 关键非默认决策重复 / KNOWLEDGE/ADR/External 详细 / 环境异常单独成段 / 各 Stage 4 行 vertical 展开）。本 patch 在 triage-stage.md Step 8 加「卡片式输出模板硬规则」+「必含 5 段」+「必砍 7 段」+ 新表格化示例（Stage 表 4 列 / 暂停点表 5 行）替换原 vertical 8-Stage 散文示例。

### P0-60：triage Step 8 输出表格化（卡片式骨架）

- 触发：用户案例分析 + "最简化思路 / 降低 PMO 负担 / 模板化"原则延续
- 设计哲学：**Tier 1 必看内容卡片化**（意图段 + Stage 表 + 关键假设 + 双对齐表）/ Tier 2/3 内容明确"必砍"（履职报告反模式）/ 决策点单源化（双对齐 + 环境处理融合到一张 5 行表）
- 处理：
  - **P0-60-1. Step 8 加「卡片式输出模板硬规则」段**：明确 ≤ 30 行总长 + 必含 5 段 / 必砍 7 段
  - **P0-60-2. 替换 vertical 8-Stage 示例为表格示例**：原 ~62 行 vertical（每 Stage 4 行：goal / key_outputs / pause_points / execution_hints）→ 新 ~25 行表格（Stage 表 4 列 / 暂停点表 5 行 / 详情指针 1 行）
  - **P0-60-3. 加「execution_hints 在表内的承载方式」硬规则**：表内「非默认」列只写一行 + 完整 hint 落 state.json
  - **P0-60-4. 加「意图段缩编硬规则」**：Why now ≤ 2 行 / Assumptions ≤ 3 条 / Real unknowns ≤ 3 条 / 整体 ≤ 8 行
  - **P0-60-5. 版本号 + CHANGELOG**：7.3.10+P0-59 → 7.3.10+P0-60
- **加 1 删 1 元规则核算**（P0-48 标尺）：
  - **加**：必含 5 段 + 必砍 7 段 + execution_hints 承载规则 + 意图段缩编规则 ≈ 35 行硬规则文字
  - **删**：原 vertical 8-Stage 散文示例 ~62 行
  - **净减**：~25 行（即模板自身瘦身）+ 实战每次 triage 输出 ~85 行 → ~22 行（**单次 -74%**）
  - **"重新触发回来"防护**：硬规则段明确禁止散文化展开 + 必砍 7 段对应 7 个反模式（Why now / 关键非默认决策 / KNOWLEDGE 详细 / ADR 详细 / External 详细 / 环境异常 / Stage 多行展开）。未来想加段 → 必须在硬规则段动，不能在示例里偷偷加
- 不动：
  - Step 8 现有硬约束（双对齐唯一合法形态 / 4 字段必填 / 骨架尾部一行 / 禁产品决策菜单 / 禁拆分对齐）
  - state.json 写入清单（Step 9 硬清单段不变）
  - 流程类型 schema（Bug / 问题排查 / Micro 各自意图段格式不变 · 仅加缩编规则）
- 影响面：
  - 改动文件：1 主（stages/triage-stage.md L477-540 替换 + 加硬规则段）+ 元数据（SKILL.md / init-stage.md / CHANGELOG.md）
  - 行数变化：triage-stage.md ±0 净（删 vertical 加 table + 硬规则）· 实战 triage 输出 -74%
- 后续验证：
  - 下次实战 triage 跑一遍验证模板是否落地（用户的 PTR-F016 case 已跑过 vertical 版 ~85 行 · 套新模板预期 ~22 行）
  - 如发现新的反模式（如某 Stage 起草时又长出新段）→ 加进必砍清单

---

## v7.3.10 + P0-59

> v7.3.10+P0-59 teamwork_space.md 变更类表格全砍 patch（最激进单源化）：用户进一步追问"跨项目需求追踪有必要么"+ 拍板"C"（最激进）。诊断：`templates/change-request.md` frontmatter 已经把所有变更属性（status / sub_features / affected_subprojects / 变更日志）都管了，teamwork_space.md 里的「跨项目变更索引」/「跨项目当前阻塞」/「变更记录」三张表全是双源副本，且实战中已发生多次"索引落后于真相"的偏离（CHANGELOG 里 PMO 主动纠偏 BG-009/BG-010/BG-013）。本 patch 删三张表，替换为一段单源指针段，teamwork_space.md 彻底回归"项目结构静态描述"。

### P0-59：teamwork_space.md 变更类表格全砍（单源化彻底化）

- 触发：用户"跨项目需求追踪 有必要么" + 选 C（砍三张表）
- 设计哲学：**单源原则贯彻到底**——changes/{change_id}.md 是变更的唯一权威源（frontmatter + 变更日志段），teamwork_space.md 完全不维护变更类信息。回归"项目结构静态描述"定位
- 处理：
  - **P0-59-1. templates/teamwork-space.md 删三段**：跨项目变更索引段（L134-149，含 P0-58 加的硬规则）+ 跨项目当前阻塞段（L153-161）+ 变更记录段（L165-178）→ 替换为单一「跨项目变更与历史」指针段（~10 行 · 列出 4 个单源 + 核心硬约束保留）
  - **P0-59-2. 生命周期描述同步**：阶段 3 描述去掉"跨项目变更索引表开始使用 + 变更记录持续维护"，改为"变更/阻塞/事件历史一律落 changes/{id}.md 或 Feature state.json"
  - **P0-59-3. 联动文件清理**：FLOWS.md L523/L600 + RULES.md L759/L931/L1185 + roles/pm.md L268 + rules/naming.md L105 + templates/change-request.md L157-169 + PRODUCT-OVERVIEW-INTEGRATION.md L226 全部更新为"changes/{id}.md 单源"措辞
  - **P0-59-4. 版本号 + CHANGELOG**：7.3.10+P0-58 → 7.3.10+P0-59
- **加 1 删 1 元规则核算**（P0-48 标尺）：
  - **加**：~10 行单源指针段
  - **删**：3 张表 + 6 处硬规则段（P0-58 加的）+ 6 个文件中的"更新 teamwork_space.md 变更/索引表"指令 ≈ 70 行
  - **净减**：~60 行
  - **本 patch 是 P0-58 的进化**：P0-58 给变更类表格加硬规则（一句话 / 字数上限），P0-59 直接砍表（更彻底的简化）。P0-58 的硬规则段被 P0-59 一并删除（被砍的表自然不需要硬规则）
  - **"重新触发回来"防护**：未来想恢复变更类表格 → 必须先解释"为什么 changes/{id}.md frontmatter 不够"，且会撞上"双源维护一定漂移"的实战教训（CHANGELOG 里 P0-59 已记录 BG-009/BG-010/BG-013 偏离案例）
- 不动：
  - templates/change-request.md frontmatter schema（已是变更单源 · v7.3.10+P0-33）
  - templates/feature-state.json `change_id` 字段（Feature → 变更反查机制）
  - PMO 在 triage 时的变更归属硬阻塞（status != locked 时 · 现在直接读 changes/{id}.md frontmatter）
- 影响面：
  - 改动文件：8 个（templates/teamwork-space.md 主砍 / FLOWS.md×2 / RULES.md×3 / roles/pm.md / rules/naming.md / templates/change-request.md / PRODUCT-OVERVIEW-INTEGRATION.md / SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
  - 行数变化：templates/teamwork-space.md 202 → ~145 行（-57 行）
- 后续（建议）：
  - 用户的实战 aon-ptr/teamwork_space.md 可以按本 patch 整体重写——把 14 个 BG 行 + 27 个变更记录行的实质内容迁到 `product-overview/changes/{BG-xxx}.md`（每变更一个文件 · 复用 change-request.md 模板）；不强制
  - PMO 在 triage 入口检查变更归属时直接 grep `changes/*.md` frontmatter 即可，无需读 teamwork_space.md

---

## v7.3.10 + P0-58

> v7.3.10+P0-58 teamwork_space.md 单元格膨胀硬规则化 patch（最简化思路）：用户基于实战 aon-ptr/teamwork_space.md 反馈"变更内容应该一句话"+"跨项目需求追踪也比较大"+"降低 PMO 负担，最简化思路解决问题"。盘点发现：「变更记录」段、「规划状态」槽位、「子项目清单当前状态列」、「跨项目当前阻塞」段**全部无字数 / 单行 / 详情外迁硬约束**——这是用户实战中表格单元格膨胀到 1500+ 字的根因。本 patch 在 templates/teamwork-space.md（**唯一权威源**）每个表格紧邻的 quote block 加显式硬规则，**不加 PMO 主动扫描职责、不加脚本、不加 RULES.md 红线**——读到表自然遵循。术语漂移"跨项目需求追踪 → 跨项目变更索引"统一同步。

### P0-58：teamwork_space.md 单元格硬规则化（最简化思路 / 降低 PMO 负担）

- 触发：用户实战 teamwork_space.md 单元格膨胀（变更记录某行 1500+ 字 / 跨项目需求追踪 BG 行 1500-2500 字）+ 显式要求"最简化思路 / 降低 PMO 负担"
- 设计哲学：**模板是单一权威源，硬规则写在表格紧邻的 quote block 里**——PM/PMO/PL 起草时按模板硬规则填，无需 PMO 在 triage 入口主动扫描。读模板自然知道"任一单元格 ≤ 1 行 / 详情外迁"
- 处理（5 处加规则 + 1 处文件顶层加总纲 + 4 处术语统一）：
  - **P0-58-1. templates/teamwork-space.md 文件顶部加核心简化原则**：「teamwork_space.md 是全景索引，不是事件日志 / 进度看板 / 评审记录。任一表格的任一单元格都应 ≤ 1 行；详情一律外迁到对应文档」+ 引用各表硬规则段
  - **P0-58-2. 规划状态段加硬规则**：4 槽位每个 ≤ 1 行 / 多事件累积只保留最近一次 / 旧事件移到 changes/{id}.md「变更日志」
  - **P0-58-3. 执行线概览段加硬规则**：「使命」/「关键里程碑」≤ 1 行 / 取自执行手册原文 / 不复述背景 / 不加事件级补充
  - **P0-58-4. 子项目清单段加硬规则**：表内任一单元格 ≤ 1 行 /「当前状态」等可选列只写最近一次状态结论 + 链 PROJECT.md / ROADMAP.md / 不复述 Feature 进度详情 / 不堆事件历史
  - **P0-58-5. 跨项目变更索引段加硬规则**：任一单元格 ≤ 1 行 /「简介」≤ 30 字 / 禁 inline 复述子 Feature 编号清单 / 推进顺序 / 联调依赖 / 阶段事件（一律落 changes/{id}.md）
  - **P0-58-6. 跨项目当前阻塞段加硬规则**：每行 ≤ 1 行 / 已解决项必须当次移走（不可保留 ✅ 历史行让表越积越多）
  - **P0-58-7. 变更记录段加硬规则（核心修复）**：「变更内容」必须一句话 ≤ 50 字 / 格式 `<动作> + <对象> + <可选 changes/{id}.md 链接>` / 禁 inline 复述子 Feature 编号 / 推进顺序 / 评审 finding 数 / Codex 命中率 / 阶段事件 / commit hash / 仅记 teamwork_space.md 文件本身的结构性变更（子项目增删 / 架构调整 / 命名规范 / CHG 锁定）/ Feature 级 / BG 级事件**禁止进本表** / 表行数体感上限 ~30 行 / 超出归档到 `product-overview/changes/teamwork-space-history.md`
  - **P0-58-8. 术语漂移统一**：FLOWS.md L600 + RULES.md L759/L931/L1185 + rules/naming.md L105 + templates/teamwork-space.md L199 中的"跨项目需求追踪"统一改为"跨项目变更索引"（v7.3.10+P0-33 命名 · 旧名 fallback 注释保留）
  - **P0-58-9. 版本号 + CHANGELOG**：7.3.10+P0-57 → 7.3.10+P0-58
- **加 1 删 1 元规则核算**（P0-48 标尺）：
  - **加**：6 处 quote block 硬规则 + 1 处文件顶层总纲 ≈ 25 行；4 处术语统一 ≈ 4 字面替换
  - **删**：未删（本 patch 是规则化补强）
  - **避免做的事**（最简化思路核心）：❌ 不加 `templates/check-teamwork-space.py` 长度门禁脚本 / ❌ 不加 PMO 在 triage 入口主动扫膨胀的职责段 / ❌ 不加 RULES.md 红线 / ❌ 不动用户实战 teamwork_space.md（迁移决定权交给用户）。这些都是"加 PMO 负担"的反模式
  - **"重新触发回来"防护**：模板硬规则在 quote block 里读到表自然看到 / 术语漂移已统一 / 未来想"打回原形"必须先动模板，模板是单源
- 不动：
  - templates/change-request.md（已有完整 schema · 不动）
  - PMO / PM / PL 角色文件（不加 PMO 主动扫描职责 · 最简化原则）
  - 用户实战 teamwork_space.md（迁移与否由用户决定 · 框架不强制）
- 影响面：
  - 改动文件：5 个（templates/teamwork-space.md +~25 行硬规则 / FLOWS.md / RULES.md / rules/naming.md / SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
  - 行数变化：templates/teamwork-space.md 180 → ~205 行（+~25 行硬规则）
- 后续（建议）：
  - 用户可基于新硬规则把 aon-ptr/teamwork_space.md 的「变更记录」+「跨项目需求追踪」段瘦身（迁移到对应 changes/{BG-xxx}.md）；不强制
  - 未来若发现新的实战膨胀模式（如某个新增列又超长），同样在模板对应段加硬规则即可

---

## v7.3.10 + P0-57

> v7.3.10+P0-57 命名标准化 patch（Goal-Plan 大小写统一）：用户提议"我们把名词统一下 Goal-Plan 统一大写字母开头，连词符号，避免大小写问题"。盘点出 103 处 `goal-plan` 小写中真正 prose 不一致只有 2 处（standards/output-tiers.md），其余全是文件名 / 路径 / markdown 链接 URL（保留小写为 filesystem 标识）+ CHANGELOG 历史记录（不回溯）；66 处 `goal_plan` 全是 state.json 字段名 / enum 值（code identifier，不能改）。本 patch 修 2 处 prose + 在 rules/naming.md 加"Stage 名词在 prose 中的标准形"段作为前向防护。

### P0-57：Goal-Plan 命名大小写统一（避免漂移）

- 触发：用户"我们把名词统一下 Goal-Plan 统一大写字母开头，连词符号，避免大小写问题"
- 设计哲学：**prose 用标准大写形 / code identifier 用小写形**——前者是人读概念，后者是机读标识符（修了破 schema）
- 盘点：
  - `Goal-Plan` 203 处（标准形，✅）
  - `goal-plan` 103 处：~25 处文件名 / ~76 处 CHANGELOG-OPTIMIZATION-PLAN 历史 / **2 处 prose 不一致**（standards/output-tiers.md L3 + L108）
  - `goal_plan` 66 处：state.json 字段 / enum / stage_contracts 键，**全部不动**
  - 无 `Goal Plan` / `goal Plan` / `GoalPlan` 等其他变体
- 改动：
  - **P0-57-1. 修 standards/output-tiers.md L3**：`triage / goal-plan / blueprint / dev / review / test / ship` → `triage / Goal-Plan / blueprint / dev / review / test / ship`
  - **P0-57-2. 修 standards/output-tiers.md L108**：同上 stage 列表 prose
  - **P0-57-3. 在 rules/naming.md 末尾追加「Stage 名词在 prose 中的标准形」段**：列出 7 个 Stage 标准形 vs code identifier 形对照表 + 4 条硬规则（前向防护，避免再次漂移）
  - **P0-57-4. 版本号 + CHANGELOG**：7.3.10+P0-56 → 7.3.10+P0-57
- **加 1 删 1 元规则核算**（P0-48 标尺）：
  - **加**：rules/naming.md +~25 行（标准形对照表 + 硬规则）
  - **改**：standards/output-tiers.md 2 行（不增不减）
  - **删**：未删
  - **本 patch 是规则化补强**（非冗余清理），增加的内容是单源标准 — 防止未来散落漂移。这种"前向防护规则"按 P0-48 元规则不计入冗余增量
  - **"重新触发回来"防护**：未来 PMO 起草新 prose 时必须 cite naming.md 标准形；外部 review / Subagent 起草时也必须遵守
- 不动：
  - `goal-plan-stage.md` 文件名（filesystem 标识，全部保持）
  - `goal_plan_*` state.json 字段 / enum 值（code identifier，破坏 schema）
  - docs/CHANGELOG.md / docs/OPTIMIZATION-PLAN.md 历史条目（事实记录）
  - markdown 链接 URL 部分（如 `[stages/goal-plan-stage.md](../stages/goal-plan-stage.md)`）
- 影响面：
  - 改动文件：3 个（standards/output-tiers.md / rules/naming.md / SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
  - 行数变化：standards/output-tiers.md ±0 行 / rules/naming.md +~25 行 / 其他元数据
- 后续：未来其他 Stage 名词若发现漂移（如 `Plan stage` / `goal-plan stage` 等），按 naming.md 标准形修正即可，patch 可合并到一次。

---

## v7.3.10 + P0-56

> v7.3.10+P0-56 roles/pmo.md 减负 patch（中等档 ~377 行减负，从 2179 → 1802 行，17.3%）：实施 P0-55 拆出的 H 维度。基于 P0-48 元规则（加 1 删 1 + "重新触发回来"标尺）以**引用化 / 单源化**方式删除与 triage-stage / goal-plan-stage / RULES.md / templates/state-patch.py 等权威源重复的段落，PMO 角色契约保留核心硬规则（必须输出项 + 写入硬时机表 + Stage 完成资格 5 条等），不动调度责任、产品决策边界、auto 模式豁免、Ship Stage 速查等 PMO 专属段。

### P0-56：roles/pmo.md 减负 引用化（中等档 ~400 行）

- 触发：用户在 P0-56 砍切优先级中选"中等（推荐）"
- 设计哲学：单源化 + 引用化（refs 取代 inline 复述）。PMO 角色契约 = 调度责任 + 必须输出项 + 写入时机 + 完成资格判定，不重复执行细节（执行细节单源在 stages/ 与 RULES.md 与 templates/state-patch.py）
- 改动：
  - **P0-56-1（盘点）**：Subagent 出 11 类重复段精细清单（review-log.jsonl 详细 / 完成报告模板 / Bug 流程矩阵 / state.json patch 脚本规范 / ADR 扫描详细 / KNOWLEDGE 扫描详细 / 智能推荐表注释 / 变更归属检查 / 自下而上影响合并 / 等）
  - **P0-56-2（拍板）**：用户选中等档（300-400 行 / 删 review-log + 完成报告模板 + Bug 流程 + state.json patch + ADR/KNOWLEDGE 引用化）
  - **P0-56-3（执行）**：实际删 377 行
    - **删 review-log.jsonl 详细段（53 行）** → 替换为引用 `templates/review-log.jsonl`（单源）
    - **删功能完成报告模板（96 行）** → 替换为「PMO 完成资格判定核心 5 条」（执行细节回归 stages/）
    - **删 Bug 流程判断详细矩阵（127 行）** → 替换为引用 RULES.md / init-stage.md / FLOWS.md 权威源
    - **删 state.json patch 脚本规范（51 行）** → 替换为引用 RULES.md § state.json 维护硬规则 + templates/state-patch.py
    - **ADR 索引扫描详细（42 行）+ KNOWLEDGE 扫描详细（75 行）→ 引用化为统一段（27 行）**：执行细节单源回归 triage-stage.md Step 2/3，PMO 段只保留硬契约（必须输出 / 读取上限 / 不下决策 / 写入时机表）
  - **P0-56-4（验证 + 收尾）**：CHANGELOG + 版本号 7.3.10+P0-55 → 7.3.10+P0-56 + 一致性自检
- **加 1 删 1 元规则核算（P0-48 标尺）**：
  - **加**：~30 行（5 个引用替换段）
  - **删**：~407 行（实际删除原段）
  - **净减**：377 行（17.3%）
  - **"重新触发回来"防护**：PMO 角色契约硬规则（必须输出 / 写入时机 / 完成资格 5 条）保留 inline，未删；执行细节链接已存在（triage-stage / RULES.md / templates / FLOWS.md），未来"打回原形"需在权威源动而非在 PMO 段加回
- 不动：
  - 路由权威段（v7.3.10+P0-41，PMO 专属硬规则）
  - 产品决策边界段（v7.3.10+P0-38-B，PMO 专属硬规则）
  - 用户质疑反应模式段（v7.3.10+P0-34，PMO 专属）
  - state.json 状态机维护规范 + 流转前必做 + Stage 内访问模式约束（v7.3.2/P0-23，PMO 调度核心）
  - 自下而上影响升级评估段（v7.3.4，PMO 专属）
  - auto 模式豁免规则段（v7.3.9+P0-11，PMO 专属）
  - Ship Stage 双段职责速查（v7.3.10+P0-29/P0-32，PMO 专属）
  - 调度责任段（v7.3.10+P0-44/P0-46/P0-49，PMO 专属）
- 效果：
  - roles/pmo.md 2179 → 1802 行（cut 377 行 / 17.3%）
  - PMO 维护成本下降：执行细节调整只需在 stages/ 与 RULES.md 单源更新
  - "Reactive evolution"反模式被切断：PMO 段不再随每次执行细节调整而膨胀
- 待跟进（后续 patch）：
  - P0-57+ 候选：FLOWS.md / standards/* 同样的引用化扫描（如发现类似的"PMO 段长尾化"在其他文件）
  - 长期：每次 P0 patch 完成后跑一次 audit subagent 检查"是否在某文件加了 inline 内容（应在权威源单源化）"

---

## v7.3.10 + P0-55

> v7.3.10+P0-55 文档层一致性 patch（C + A + B + D 四维度，H 拆出 P0-56）：基于 audit 报告 P1+P2 优化项落地——C 6 stage spec 加可配置点清单 + A FLOWS.md 4 选 1 → 双对齐 语汇统一 + B feature-state.json enum vs STATUS-LINE.md 阶段字段映射 + D SKILL.md 显式化"三层按需启动"原则总纲。H roles/pmo.md 减负 ~400 行 拆出 P0-56 单独做（风险中等需仔细盘点）。

### P0-55：文档层一致性（C + A + B + D，H 拆 P0-56）

- 触发：用户"继续"采纳 P0-55 文档层路径
- 设计哲学：把架构原则（三层按需启动）+ stage 可配置点显式化到文档总纲，跨文件命名 / 字段映射统一化，让 future PMO 操作有清晰单源
- 处理（5 处改造）：
  - **P0-55-1. 6 stage spec 顶部加"可配置点清单"段（C 维度）**：goal-plan / blueprint / dev / review / test / ship 各加 5-7 行配置点表格（review_roles / 角色 execution / 子流程触发条件 / round_loop / hint_overrides 等），用户易查 + 标注"不变内核"
  - **P0-55-2. FLOWS.md 4 选 1 → 双对齐 语汇统一（A 维度）**：FLOWS.md / roles/pmo.md 中 triage 流程确认相关的"4 选 1 暂停点"老语汇统一改为"双对齐暂停（v7.3.10+P0-49）"。Ship Stage / 变更规划等真实多选项暂停语汇保留（不混淆）
  - **P0-55-3. STATUS-LINE.md 阶段字段映射表（B 维度）**：加 state.json `current_stage` enum vs STATUS-LINE 阶段字段语义映射表（triage / goal_plan / ui_design / blueprint / dev / review / test / browser_e2e / pm_acceptance / ship / completed → 用户可读语义）。修正 🌐 Ext 徽章读取逻辑（P0-38 起读 review_roles[] 含 external，不再读老 *_enabled 字段）
  - **P0-55-4. SKILL.md 加"三层按需启动"原则段（D 维度）**：在红线段后加"🎯 三层按需启动原则"段作为框架设计总纲（L0 triage 定初步流程 / L1 流程编排 stage / L2 stage 执行方式可配置 + stage 内部规范不变 + 引用 standards/stage-instantiation.md / output-tiers.md）
  - **P0-55-5. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-54 → 7.3.10+P0-55

- **本 patch 删了什么**（自我应用 P0-48 C 段元规则）：
  - 删 FLOWS.md / roles/pmo.md 中 triage 相关"4 选 1 暂停点"老语汇（统一为"双对齐暂停"，P0-49 改造后的真相源）
  - 删 STATUS-LINE.md 🌐 Ext 徽章读"任一 *_enabled=true"老逻辑（改为"review_roles[] 任一含 external"，P0-38 改造后单源）

- **加 1 删 1 论证**（P0-48 元规则）：
  - **加**：6 stage 可配置点清单（5-7 行表格 × 6 = ~36 行）+ STATUS-LINE 阶段字段映射表（~12 行）+ SKILL.md 三层按需启动段（~50 行）
  - **删**：4 选 1 老语汇 + Ext 徽章老逻辑 + （间接）P0-56 待删 roles/pmo.md ~400 行
  - 净加规则数：本 patch 是文档层显式化（让现有架构对外可见），非增加新规则。可配置点清单只是把分散在 spec 各段的字段汇总，不引入新字段；三层按需启动段是把已有原则（散落在 P0-49 / P0-51 / P0-52 等多个 patch）抽到顶层

- **重新触发回来的 case 标尺**（P0-48 C-3 元规则）：
  - 如果 PMO 操作时找不到"某 stage 有什么可配置点" → 看 stage spec 顶部清单段，找不到再修清单（不再分散到各段）
  - 如果用户口语"4 选 1" → PMO 应主动澄清是 triage 双对齐还是 Ship/变更 多选项暂停
  - 如果新读者不理解架构 → 看 SKILL.md 三层按需启动段，找不到再补总纲

- 风险控制：
  - 文档显式化不破坏现有规则（只是抽到顶层 / 单源化）
  - 老语汇 fallback 保留在 CHANGELOG 历史条目（不改）
  - 红线数保持 15 条
  - 不影响实际行为，仅文档导航 / 命名 / 总纲

- 影响面：
  - 改动文件：~10 个（6 stage spec 加配置清单 + FLOWS.md 语汇统一 + roles/pmo.md 语汇统一 + STATUS-LINE.md 加映射表 + SKILL.md 加三层段 + CHANGELOG）
  - 行数变化：6 stage spec 各 +5-7 行 / FLOWS.md ±5 行（替换）/ STATUS-LINE.md +~15 行 / SKILL.md +~55 行

- 待跟进（拆出 P0-56）：
  - **P0-56 roles/pmo.md 减负**（H 维度）：删/合并 ~400 行重复内容（与 triage-stage.md / goal-plan-stage.md / standards/external-model.md 重复段），需仔细盘点哪些段可删，单独 patch 风险更可控

---

## v7.3.10 + P0-54

> v7.3.10+P0-54 行为层一致性 patch（E + G + F 三维度）：基于整体 audit 报告的前 3 项落地——E（主对话 Tier 规范单源化 + 6 stage spec 各加 Tier 应用段）+ G（roles/pmo.md plan_enabled 自相矛盾修正 + standards/external-model.md 链接化）+ F（RULES.md 加 state.json 维护硬规则把 P0-52 隐性约定升格为显式硬规则）。

### P0-54：行为层一致性（E + G + F）

- 触发：用户"按建议"采纳整体 audit 报告优先级
- 设计哲学：把 P0-49-A / P0-52 的设计意图从 triage-specific / 隐性约定升格为框架级硬规则，覆盖所有 stage
- 处理（5 处改造）：
  - **P0-54-1. 抽取 standards/output-tiers.md 单源**（E 维度）：从 triage-stage.md L751-853 抽取通用 Tier 1/2/3 规范 + 4 类反模式（履职报告 / state.json 复述 / 决策菜单膨胀 / 工程性切片暂停）+ 主对话输出红线 → 单源 standards/output-tiers.md（~150 行）
  - **P0-54-2. 6 stage spec 加 Tier 应用段**（E 维度）：goal-plan / blueprint / dev / review / test / ship 各加"主对话输出 Tier 应用"段（10-15 行 stage-specific Tier 1/2/3 应用 + 引用 standards/output-tiers.md）。其中 goal-plan / blueprint / review 升级原 P0-48 "主对话输出红线"段；dev / test / ship 新加
  - **P0-54-3. roles/pmo.md plan_enabled 矛盾修正 + external-model.md 链接化**（G 维度）：(a) roles/pmo.md L552 / L573 / L702 自相矛盾修正——L552 说"不再有 plan_enabled"，L573-575 / L662-666 / L702 仍用，统一为 P0-38 后的"external ∈ review_roles[] 单源判定" + fallback 规则更新；(b) standards/external-model.md §5.4 老 schema 删除，改为链接到 stage spec
  - **P0-54-4. RULES.md 加 state.json 维护硬规则**（F 维度）：新增"state.json 维护硬规则"段（优先级 patch.py > Edit > 禁止 Write 全文 + 3 类合法降级场景 + 典型调用范例 + PMO 校验门禁）。把 P0-52 的"隐性约定"升格为 RULES.md 显式硬规则
  - **P0-54-5. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-53 → 7.3.10+P0-54

- **本 patch 删了什么**（自我应用 P0-48 C 段元规则）：
  - 删 goal-plan / blueprint / review stage spec 中原 P0-48 "主对话输出红线"3 行红线段（升级为 Tier 1/2/3 应用）
  - 删 roles/pmo.md L573-575 老 `plan_enabled / blueprint_enabled / review_enabled` 默认值表
  - 删 roles/pmo.md L662-666 state.json schema 中的老三字段
  - 删 standards/external-model.md §5.4 老 schema + Fallback 表（链接化到 pmo.md）
  - 删 P0-52 的"隐性约定"措辞（升格为 RULES.md 显式硬规则）

- **加 1 删 1 论证**（P0-48 元规则）：
  - **加**：standards/output-tiers.md（新文件）+ 6 stage spec 各加 Tier 应用段 + RULES.md 加 state.json 硬规则段
  - **删**：3 stage spec 旧"主对话输出红线"段（升级覆盖）+ roles/pmo.md L552/L573/L662/L702 自相矛盾陈述 + standards/external-model.md §5.4 复述
  - 净加规则数：±0（新加 standards/output-tiers.md 和 RULES.md state.json 硬规则段，但删除了同等数量的 stage 内重复 + roles/pmo.md 自相矛盾 + external-model 复述）

- **重新触发回来的 case 标尺**（P0-48 C-3 元规则）：
  - 如果其他 stage 仍出现"履职报告"/state.json 复述 → 修 standards/output-tiers.md 反模式禁令，不放弃 Tier 规范
  - 如果用户找不到 plan_enabled → 提示用 review_roles[] 单源判定，不恢复老字段
  - 如果 PMO 仍用 Edit 全文更新 state.json → 检查是否符合 3 类合法降级场景，否则视为流程偏离

- 风险控制：
  - Tier 1/2/3 规范是行为指引，不破坏现有 stage 流程
  - plan_enabled fallback 规则保留（老 state.json 仍可读）
  - state.json 硬规则有 3 类合法降级场景（保留 Edit 灵活性）
  - 红线数保持 15 条（state.json 维护硬规则不进 15 红线，进 RULES.md 单独段）

- 影响面：
  - 改动文件：~10 个（新建 standards/output-tiers.md + 6 stage spec + roles/pmo.md + standards/external-model.md + RULES.md + SKILL.md + stages/init-stage.md + docs/CHANGELOG.md）
  - 行数变化：standards/output-tiers.md +~150 / 6 stage spec 各 +10-15 = +60-90 / roles/pmo.md 修正不增减 / standards/external-model.md 减~50（链接化）/ RULES.md +~50

- 待跟进（P0-55 文档层）：
  - C: 6 stage spec 顶部加"可配置点清单"段
  - A: FLOWS.md 4 选 1 → 双对齐 语汇统一 + roles/pmo.md triage 职责合并
  - B: feature-state.json enum 注释 + STATUS-LINE.md 阶段字段映射
  - D: SKILL.md 显式化"三层按需启动"原则
  - H: roles/pmo.md 减负（删 ~400 行重复内容）

---

## v7.3.10 + P0-53

> v7.3.10+P0-53 单 stage 改名 plan → goal-plan：用户提议"plan stage 改成 goal-plan 更合理一些"——跟 blueprint（蓝图层）对仗清楚，避免跟 PDCA "plan" 混淆。用户拍板"改 goal-plan，其他不动，不考虑历史兼容"。本 patch 完成机械化改名。

### P0-53-A：单 stage 改名 plan → goal-plan（不考虑历史兼容）

- 触发：用户"plan 改成 goal-plan 是否更合理一些" + "改 goal-plan 把"
- 设计哲学：goal-plan 跟 blueprint 对仗（goal-plan = 做什么 + 为什么 / blueprint = 怎么做 + 怎么测）；避免 PDCA 的泛 "plan" 词混淆。其他 stage 名（dev / review / test / ship 等）不改
- 处理（4 处改造）：
  - **P0-53-A-1. 搜索 plan-stage 全部引用**：grep 全部 plan-stage.md / Plan Stage / plan stage / plan_substeps_config / current_stage="plan" 等引用，确认范围 ~280 处（CHANGELOG/OPTIMIZATION-PLAN 历史文档 163 处不动）
  - **P0-53-A-2. rename 文件 + 批量替换**：mv stages/plan-stage.md → stages/goal-plan-stage.md；sed -i 批量替换 5 类引用（plan-stage.md → goal-plan-stage.md / Plan Stage → Goal-Plan Stage / plan stage → goal-plan stage / plan_substeps_config → goal_plan_substeps_config）；排除 docs/CHANGELOG.md / docs/OPTIMIZATION-PLAN.md
  - **P0-53-A-3. state.json schema 改名**：completed_stages 数组 "plan" → "goal_plan"；stage_contracts.plan → stage_contracts.goal_plan；planned_execution.plan → planned_execution.goal_plan；executor_history[].stage = "plan" → "goal_plan"；stage_enum 注释更新
  - **P0-53-A-4. SKILL.md / state-patch.py 顶部 docstring 同步 + 版本号 bump + CHANGELOG**：SKILL.md 顶部 description "Plan → UI Design → ..." → "Goal-Plan → UI Design → ..."；红线 #1 流程选择段 "Plan/Blueprint/UI/..." → "Goal-Plan/Blueprint/UI/..."；state-patch.py docstring 示例改 goal_plan；版本号 7.3.10+P0-52 → 7.3.10+P0-53

- **本 patch 删了什么**（自我应用 P0-48 C 段元规则）：
  - 删除 stages/plan-stage.md（mv 到 goal-plan-stage.md）
  - 删除所有 "Plan Stage" 字面量（替换为 Goal-Plan Stage）
  - 删除 plan_substeps_config 字段名（替换为 goal_plan_substeps_config）
  - 删除 state.json current_stage enum 中 "plan" 值（替换为 goal_plan）
  - 不考虑历史兼容（用户明确指示）—— 不加 fallback alias，老 state.json 不可用

- **加 1 删 1 论证**（P0-48 元规则）：
  - 本 patch 类型 = 命名重构（C 段例外白名单："新角色 / 新 Stage 加入" 的镜像——stage 改名属结构性重命名，不是规则增量）
  - **加**：0（不新增字段 / 规则）
  - **删**：1 整套老命名（"Plan Stage" / "plan_substeps_config" / "current_stage=plan"）
  - 净规则数：±0（命名替换非规则增减）

- **重新触发回来的 case 标尺**（P0-48 C-3 元规则）：
  - 如果用户口语说"plan stage" 频繁出现混淆 → PMO 应主动澄清并 cite goal-plan-stage.md
  - 如果其他 stage（dev / review / test）也出现命名歧义 → 触发"全套改名"讨论（不只是 plan 单点）
  - 如果"goal-plan" 在新场景反而比"plan"更模糊（如 "goal" 跟 "objective" 重复）→ 考虑改回或重新命名

- 风险控制：
  - **不考虑历史兼容**（用户明确）—— 老 Feature 的 state.json `current_stage: "plan"` 在新版下视为非法值；进行中 Feature 需手动改为 "goal_plan"
  - 跨子项目搜索 stage 名时建议同时搜 "plan" 和 "goal_plan" 双关键词，确保不漏老 Feature
  - CHANGELOG / OPTIMIZATION-PLAN 历史条目保留原文（不改），保持历史可读性
  - 红线数保持 15 条
  - 不影响 PDCA "plan" 等独立词的使用（仅改 stage 字面量）

- 影响面：
  - 改动文件：~30+ 个（stages/{各 stage}.md / roles/*.md / templates/{prd,feature-state.json,state-patch.py}.md / FLOWS.md / RULES.md / SKILL.md / STATUS-LINE.md / standards/stage-instantiation.md / agents/README.md / etc）
  - 替换数：~120 处（不含 CHANGELOG / OPTIMIZATION-PLAN）
  - 文件 rename：1 个（plan-stage.md → goal-plan-stage.md）
  - state.json schema：current_stage / stage_contracts / planned_execution / executor_history 4 处改名
  - 用户体验：stage 名跟 blueprint 对仗清楚，goal-plan = 目标层 vs blueprint = 蓝图层正交

- 待跟进（非 P0-53 范围）：
  - 验证 1-2 个真实 Feature 跑下来 goal-plan 命名是否真的减少了歧义（vs 原 plan）
  - 如果其他 stage 也想类似改名（如 "blueprint" → 更精确的名字）→ 单独评估，不在本 patch 内
  - state.json schema_version 字段未 bump（v7.3.9 不动）—— 老 Feature 仍 schema_version=v7.3.9，但 current_stage="plan" 视为漂移

---

## v7.3.10 + P0-52

> v7.3.10+P0-52 state.json 增量更新工具：用户观察到 PMO 用 Edit 全文更新 state.json 占用太多 token（一个 Feature 生命周期累积 ~7,500 tokens 仅 state.json 维护，Edit 工具每次发送 50-100 行上下文，且随 state.json 变大累积成本上升）。本 patch 新增 `templates/state-patch.py` —— 增量 patch 工具，PMO 通过 bash 调用，只发送变更字段，节省 ~40% token 成本 + 不随文件大小增长。

### P0-52：state.json 增量更新工具（state-patch.py）

- 触发：用户观察到"对 state.json 的更新是否占用太多资源，使用一个更新脚本传入变更字段更合理"+ 用户 yes
- 设计哲学：把"机读字段维护"从 Edit 全文模式改为 CLI patch 模式，PMO 主对话只发送变更字段，文件大小对成本无影响
- 处理（5 处改造）：
  - **P0-52-1. 新建 `templates/state-patch.py`**（~250 行 Python）：核心脚本支持 5 种操作（--set / --append / --merge-object / --set-note / --unset）+ 智能类型推断（true/false/null/数字/JSON literal）+ schema 校验 + 原子写（先写临时文件 → fsync → mv）+ --dry-run 模式 + --validate schema 校验
  - **P0-52-2. 脚本 docstring 含 5 个调用示例**：Stage 转换 / PRD 评审完成 / Ship 双段 finalize / Bug 简化流程 / 评审循环超 3 轮决策——覆盖典型 PMO state.json 更新场景
  - **P0-52-3. roles/pmo.md 加约定**：在 PMO 责任段（state.json 访问模式约束之后）加"state.json 更新优先用 patch 脚本"段，含优先级（patch 脚本 > Edit > Write）+ 典型调用示例 + 回退到 Edit 的合法场景（嵌套 ≥3 层 / 条件性修改 / ≥10 字段同时改）
  - **P0-52-4. TEMPLATES.md 索引加引用**：新增 state-patch.py 索引条目
  - **P0-52-5. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-51 → 7.3.10+P0-52

- **脚本核心特性**：
  - **5 种操作**：set scalar / append list（去重）/ merge object / set _note 字段（自动加 _ 前缀）/ unset
  - **智能类型推断**：true → bool / null → None / 数字 → int|float / [{ 开头 → JSON literal / 其他 → string
  - **schema 校验**：基于 templates/feature-state.json 顶层字段名，检测漂移（PMO 自创字段或老字段残留）
  - **原子写**：tempfile + fsync + os.replace，防中断损坏
  - **--dry-run**：预览更新结果不写入
  - **退出码**：0 成功 / 1 错误 / 2 schema WARN（仍写入但 stderr 警告）

- **本 patch 删了什么**（自我应用 P0-48 C 段元规则）：
  - 这是**工具增强型 patch**，未删现有规则；落到 P0-48 C 段例外白名单："新工具/脚本（capability 增强，非规则增量）"
  - 但保留了"加 1 删 1 论证"职责：本 patch 通过引入新工具，**事实上间接删除了"Edit 全文更新 state.json"的隐性规则**（虽然 Edit 仍是合法降级路径，但优先级降为次选）

- **加 1 删 1 论证**（P0-48 元规则例外白名单）：
  - 本 patch 类型 = **工具增强型**（C 段例外白名单："新工具 / 新脚本，capability 增强非规则增量"）
  - **加**：state-patch.py（CLI 工具）+ roles/pmo.md "patch 脚本优先"约定（一段）+ 索引引用
  - **删**：未直接删规则，但通过"patch 脚本优先"约定**事实上降级了 Edit 全文更新的优先级**
  - 净加规则数：+1 段（"patch 脚本优先"约定），符合工具增强型 patch 的接受范围

- **重新触发回来的 case 标尺**（P0-48 C-3 元规则）：
  - 如果 patch 脚本不支持的复杂 edit 频繁出现 → 扩展脚本支持（add 新操作类型，如 --merge-deep / --conditional-set），不是放弃脚本回到 Edit 全文
  - 如果 schema 校验频繁误报 → 修 schema（feature-state.json 不全），不是关闭校验
  - 如果脚本增加 token 反而比 Edit 多 → 排查命令构造问题（不应该出现，因为 patch 命令长度 ≤ Edit 上下文长度）

- 风险控制：
  - 兼容性：state.json schema 不变，Edit/Write 仍可用作降级路径
  - 原子写防中断损坏（tempfile + fsync + replace）
  - schema 校验是 WARN 不是 ERROR（不阻塞写入，仅 stderr 提示）
  - 红线数保持 15 条
  - 不影响其他文件读取 state.json（仅改 PMO 写入方式）

- 影响面：
  - 改动文件：5 个（新建 templates/state-patch.py / roles/pmo.md / TEMPLATES.md / SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
  - 新增脚本：~250 行 Python（含 docstring 5 个示例）
  - **预估 token 节省**：每 Feature ~3,000+ tokens 主对话开销（15-20 次 state.json 更新 × 200 tokens 节省）
  - 不影响现有 Feature（state.json schema 不变，老 Feature 可继续 Edit 也可改用 patch 脚本）

- 待跟进（非 P0-52 范围）：
  - 跑 1-2 个真实 Feature 验证 patch 脚本节省 token 是否符合预估
  - state.json schema（feature-state.json）需补"shipped / shipped_at / completed_at / merge_commit"等顶层字段（当前 schema 只含 `ship` 嵌套对象，但实战中 PMO 把 ship_phase2 状态写到顶层 → 漂移），→ 推迟到 P0-53 schema 收敛 patch
  - state-patch.py 未来可加更多操作（如 --merge-deep 嵌套 merge / --conditional-set 条件性更新）

---

## v7.3.10 + P0-51

> v7.3.10+P0-51 Plan Stage 体感优化大 patch：用户在 P0-50（FLOWS.md 减负）后让继续逐 Stage 看，从 Plan Stage 开始。Subagent 盘点发现 10 项可优化（2 P0 + 6 P1 + 2 P2），可减 ~280 行 + 实质改善小 Feature 体感。本 patch 一次性落地全部 P0+P1+P2 改造。

### P0-51：Plan Stage 体感优化大 patch（10 项可优化一次性落地）

- 触发：用户"继续逐个 stage 看"+ subagent 盘点发现 Plan Stage 10 项可优化 + 用户拍板"1 个大 patch"
- 设计哲学：从"PMO 操作手册"瘦身为"流程契约 + 关键决策点"，把 PM checklist / discuss 双源 / external_enabled 老字段等冗余迁出
- 处理（6 项改造）：
  - **P0-51-1. 子步骤 2 PL-PM 讨论改条件启用**：从"永远必做"改为"仅当 `pl ∈ review_roles[]` 时启用"。Bug 修复 / 纯技术 refactor / 敏捷需求等不含 PL 的 Feature 跳过子步骤 2，子步骤 1 完成后直接进子步骤 3。子步骤序列表 + 子步骤 2 段同步更新启用条件说明
  - **P0-51-2. discuss/ 文件单源化到 PRD-REVIEW.md**：撤销 P0-43 / P0-44 "discuss/ 文件双源"决定。所有 PL-PM 讨论轮次集中写到 `PRD-REVIEW.md.reviews[role=pl].pl_rounds[]` 数组（schema：round / pl_feedback / pm_response / verdict）+ `final_verdict / final_verdict_at`。删除 discuss/PL-FEEDBACK-R{N}.md / discuss/PM-RESPONSE-R{N}.md 双源文件
  - **P0-51-3. PM 起草规范 checklist 迁到 templates/prd.md**：把 plan-stage.md 的 70 行 PM checklist（通用 + UI 维度 + PRD 不写什么 + 起草后自查）迁到 templates/prd.md 新增段。plan-stage.md 仅保留简版核心约束（3 行）+ cite templates/prd.md 单源。`pm_self_check` schema 改为 `{checklist_passed: bool, failed_items: [...], notes: ...}`，不复述 checklist 全文（避免主对话述 3 遍）
  - **P0-51-4. Designer 中途补启用 + PASS_WITH_CONCERNS 响应规则**：(a) PM 起草过程发现需要 UI（triage 漏识别）→ 补启用机制：PM 标 PRD frontmatter `requires_ui: true` → PMO 在子步骤 3 dispatch 前自动补加 designer 到 active_roles + 写 hint_overrides；(b) 子步骤 4 触发条件从"仅 NEEDS_REVISION"扩展为"NEEDS_REVISION 或 任意 review 含 ≥1 个 SHOULD-fix concern"；severity 三级分类（MUST-fix / SHOULD-fix / NICE-to-have）
  - **P0-51-5. external_enabled 字段双源化清理**：plan-stage.md 残留 3 处引用 `state.external_cross_review.plan_enabled`（P0-38 已 deprecated），改为 `external ∈ state.plan_substeps_config.review_roles[]` 单源判定
  - **P0-51-6. 评审分歧暂停 vs 工程性切片界定**：子步骤序列表加红线"异常暂停不算工程性切片"——业务方向锁定失败 / 评审循环不收敛是真实异常分支，不是预防性切片暂停
  - **P0-51-7. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-50 → 7.3.10+P0-51

- **本 patch 删了什么**（自我应用 P0-48 C 段元规则）：
  - 删 plan-stage.md PM 起草规范 checklist 全文（~70 行）→ 单源化到 templates/prd.md
  - 删 plan-stage.md discuss/ 文件双源契约段 → 单源化到 PRD-REVIEW.md.reviews[].pl_rounds[]
  - 删 plan-stage.md 子步骤 2 "永远必做"硬约束 → 改条件启用（pl ∈ review_roles[]）
  - 删 plan-stage.md 3 处 `state.external_cross_review.plan_enabled` 引用（P0-38 已 deprecated 但漂移残留）→ 改 review_roles[] 单源判定
  - 删 plan-stage.md 子步骤 4 "仅 NEEDS_REVISION 触发"过松条件 → 改为 SHOULD-fix 也触发
  - 删 PM checklist 在 PRD-REVIEW.md.reviews[].pm_self_check 里逐项记录的设计 → 改为 checklist_passed bool + failed_items 列表

- **加 1 删 1 论证**（P0-48 元规则）：
  - **加**：(a) Designer 中途补启用机制 (b) PASS_WITH_CONCERNS / SHOULD-fix 触发规则 (c) PRD-REVIEW.md.reviews[].pl_rounds[] schema (d) severity 三级分类 (e) 子步骤 2 条件启用判定 + 异常暂停定义
  - **删**：(a) PM 起草规范 checklist 全文（70 行迁出，主对话不复述）(b) discuss/ 文件双源契约 (c) external_enabled 老字段引用 (d) 子步骤 2 "永远必做"硬约束
  - 净加规则数：±0（加判定/schema = 删 checklist/双源/老字段），符合 加 1 删 1
  - 实际行数变化：plan-stage.md 884 → 850（净减 ~34 行 + 加 ~30 行新规范）；templates/prd.md 322 → 380（加 PM checklist 段）

- **重新触发回来的 case 标尺**（P0-48 C-3 元规则）：
  - 如果不含 PL 的 Feature 跑下来 PRD 业务方向不准 → 说明 review_roles 决策时漏了 PL → 修 triage execution_hints 推导，不是恢复"子步骤 2 永远必做"
  - 如果 PASS_WITH_CONCERNS 但 SHOULD-fix 被忽视导致下游问题 → 说明 severity 分级判定不准 → 改进 review 角色 spec 的 severity 用法，不是恢复"仅 NEEDS_REVISION 触发"
  - 如果 Designer 补启用机制让评审循环混乱 → 说明 PM 起草时识别 UI 触点不及时 → 改进 PRD 模板的 UI 提示，不是回退到"启用决策一旦锁死不可调整"
  - 如果 discuss/ 单源化导致 PL 讨论深度不够 → 说明 PRD-REVIEW.md.reviews[].pl_rounds[] schema 不够灵活 → 扩 schema，不是回到 discuss/ 双源

- 风险控制：
  - 子步骤 2 改条件启用：现有进行中的 Feature 若已建 discuss/ 文件，PRD-REVIEW.md.reviews[].pl_rounds[] 兼容（PMO 读取时 fallback 旧 discuss/ 文件，新 Feature 走单源）
  - PM checklist 迁出：plan-stage.md 仍 cite 简版核心约束，PMO 起草前 cite templates/prd.md 一次即可，不 break 流程
  - Designer 补启用：仅在 frontmatter requires_ui: true 时触发，不会误启用
  - SHOULD-fix 触发响应：保持 PASS / NICE-to-have 不强制响应（用户在子步骤 5 自行决定是否采纳）
  - 红线数保持 15 条
  - 自我应用 P0-48 C 段元规则（删了什么 + 加 1 删 1 + 重新触发标尺）

- 影响面：
  - 改动文件：4 个（stages/plan-stage.md / templates/prd.md / SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
  - 行数变化：plan-stage.md 884 → 850（-34）/ templates/prd.md 322 → 380（+58 含 PM checklist 段）
  - 用户体验：(a) 不含 PL 的小 Feature 流程减 20%（跳过子步骤 2 PL-PM 讨论 1-3 轮）(b) PRD-REVIEW.md.reviews[].pl_rounds[] 单源 → 改 PL 意见时只改一处（不用同步 discuss/ 文件）(c) PM 起草 checklist 不在主对话述 3 遍 → token 节省 (d) PASS_WITH_CONCERNS 不再被忽视 → SHOULD-fix concerns 必须响应

- 待跟进（非 P0-51 范围）：
  - review_scope=PRD 边界案例（plan-stage.md L520-560 ~80 行）迁到 roles/{rd,qa,designer}.md 评审 checklist 附录 → 推迟到 P0-52 / P0-53（P2 优先级，工作量大但收益小）
  - 1-2 个真实 Feature 跑完后回顾 SHOULD-fix 触发响应是否合理 / 不含 PL 的子步骤 2 跳过是否真的无问题 / Designer 补启用机制是否真有命中

---

## v7.3.10 + P0-50

> v7.3.10+P0-50 FLOWS.md 减负专版（与 P0-48 同类型）：用户在 P0-49-A 完成后让看 FLOWS.md 是否需要精简。委托 subagent 盘点发现 1124 行有 ~22-27% 冗余（与 triage-stage.md / RULES.md / SKILL.md 红线重复）。本 patch 删 269 行（24% 减量），FLOWS.md 重新定位为「**流程选择决策树 + 流程间横向规则 + 特殊子模式索引**」（不再装 PMO 输出模板 / 类型识别表 / 暂停点规则 / Stage 链复述等已被其他文件接管的内容）。

### P0-50：FLOWS.md 减负专版

- 触发：用户问"FLOWS.md 是否需要精简"+ subagent 盘点发现 22-27% 冗余 + 用户 ok
- 设计哲学：FLOWS.md 从"PMO 操作手册 + 流程模板"瘦身为"流程间横向规则索引"——不复述 triage-stage / RULES / SKILL 红线已有内容
- 处理（5 处砍切）：
  - **P0-50-1. 类型识别表 + 暂停点规则 + 禁止事项**（~37 行）：删 L47-71 6 流程类型识别信号表（与 triage-stage Step 5 完全相同）；删 L323-340 暂停点规则 + 禁止事项段（与 RULES.md / SKILL.md 红线重复）；改为 4 行引用
  - **P0-50-2. PMO 初步分析输出格式段**（最大头，~161 行）：删 L168-328 段（含 PMO 初步分析输出 + 模板清单 + 外部模型决策段，已被 triage-stage Step 8 完全接管，且 P0-49/+P0-49-A 已重构为 Tier 1/2/3 输出层次）；改为 9 行引用 triage-stage 执行报告模板
  - **P0-50-3. 工作区级 / 敏捷需求 / 问题排查 PMO 输出格式**（~73 行）：删 3 处流程级 PMO 输出格式段（都是"📋 PMO 初步分析"格式复述，被 triage-stage 接管）
  - **P0-50-4. PL 路由段红线复述**（~9 行）：删 L114-118 流程类型枚举红线 + 兜底规则复述（已在 SKILL.md 红线 #2 + RULES.md 兜底规则中）；保留 L79-113 PL 路由 + Feature Planning Level 1/2/3 判断主体（独有价值，迁移到 roles/pmo.md 反而违背减负）
  - **P0-50-5. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-49 → 7.3.10+P0-50

- **本 patch 删了什么**（自我应用 P0-48 C 段元规则）：
  - 删 FLOWS.md 类型识别表 6 流程信号表（~28 行）→ 单源化到 triage-stage Step 5
  - 删 FLOWS.md 暂停点规则 + 禁止事项段（~17 行）→ 单源化到 RULES.md / SKILL.md 红线
  - 删 FLOWS.md PMO 初步分析输出格式段（~161 行，最大头）→ 单源化到 triage-stage 执行报告模板
  - 删 FLOWS.md 工作区级 PMO 初步分析输出格式段（~30 行）→ 单源化到 triage-stage
  - 删 FLOWS.md 敏捷需求 PMO 分析输出格式段（~32 行）→ 单源化到 triage-stage
  - 删 FLOWS.md 问题排查 PMO 分析输出格式段（~11 行）→ 单源化到 triage-stage
  - 删 FLOWS.md PL 路由段中流程类型枚举红线 + 兜底规则复述（~9 行）→ 单源化到 SKILL.md / RULES.md

- **加 1 删 1 论证**（P0-48 元规则）：
  - 本 patch 类型 = 减负 patch（与 P0-48 同类型）
  - **加**：0（纯减负，仅加 4 处单源化引用，不算新规则）
  - **删**：~278 行（含 5 个独立段 + 1 个红线复述）
  - 净加规则数：负数（仅删旧规则不加新规则），符合"纯减负 patch 例外"（P0-48 C-3 例外白名单）

- **重新触发回来的 case 标尺**（P0-48 C-3 元规则）：
  - 如果用户找不到"PMO 应该怎么输出 triage 分析"——说明引用链不够清楚，应改进 FLOWS.md → triage-stage.md 的索引（不是恢复 PMO 输出格式重复段）
  - 如果用户问"6 流程类型识别信号是什么"——单源在 triage-stage Step 5，可以加跨文件搜索关键词（不是回到 FLOWS.md 复制表格）
  - 如果跨流程歧义判断（如 Bug vs Feature）出错——说明 triage-stage 信号表不全，应补到 triage-stage（不是回到 FLOWS.md 维护两份）

- 风险控制：
  - 单源化引用 → 双源漂移风险消除（删除的内容都在权威源 triage-stage / RULES / SKILL 已存在）
  - 删的都是"PMO 输出格式"或"红线复述"——不是核心流程规则
  - 保留的是 FLOWS.md 独有价值的段：流程选择决策树 / Feature vs Planning 歧义判断 / Feature Planning 范围判断 / 变更级 Planning 子模式 / 工作区级 Feature Planning / 流程豁免规则 / Bug 简单/复杂判断 / 标准 Feature Planning / 各流程概览图 / Micro 流程 / Bug 闭环验证 / 敏捷需求准入条件
  - 红线数保持 15 条
  - 不影响其他文件，纯单文件减负

- 影响面：
  - 改动文件：3 个（FLOWS.md 主体 + SKILL.md 版本号 + stages/init-stage.md SKILL_VERSION 引用 + docs/CHANGELOG.md）
  - 行数变化：FLOWS.md 1124 → 855（净减 269 行 / **24% 减量**，达到 audit 目标）
  - 用户体验：FLOWS.md 重新定位为"流程间横向规则索引"，更易找到独有内容（不再被 PMO 输出模板淹没）；新读者不会被"PMO 怎么输出"细节冲晕，能聚焦"流程间怎么走"

- 待跟进（非 P0-50 范围）：
  - FLOWS.md 仍存留的 1124-855=269 行减量集中在"PMO 输出格式"段，未来如果 P0-49 主对话输出经过几个真实 Feature 验证后稳定，可考虑下一轮减负移除问题排查/Bug流程内的"PMO 派发规则"等中型段（~50-100 行潜在减量）

---

## v7.3.10 + P0-49

> v7.3.10+P0-49 triage 阶段意图理解段 + 双对齐：经过用户与对话方七轮讨论收敛形成。triage 阶段从单一"流程承诺"扩展为「意图理解段（按流程类型分 schema）+ 流程承诺骨架」双产出，⏸️ 暂停点改双对齐合一（意图 + 流程一次确认）。意图段不落盘（避免新增 artifact，符合 P0-48 减负方向），下一阶段首次产出 commit 时自然落盘到对应人读资产文件（PRD 背景段 / BUG-REPORT 顶部 / 排查记录顶部 / Feature Planning 章节）。本 patch 自我应用 P0-48 「加 1 删 1」元规则。
>
> 🔧 **P0-49-A 修补（不 bump 版本号）**：用户在 P0-49 落地后跑了一个真实 Feature（SVC-PLATFORM-F026 rust struct rename），输出形态有 6 个具体问题（履职报告体感 / 意图段位置太晚 / 没命中扫描也立段 / 骨架理由全展开 / 双对齐退化为 5 选 1 菜单 / state.json 配置在主对话复述）。本修补改造 triage-stage.md 执行报告模板规范——加 Tier 1/2/3 输出层次 + 决策呈现 vs 履职报告原则段 + 默认推荐折叠 / 非默认 💡 标注 + 双对齐二选一姿态 + state.json 复述禁令。

### P0-49-A 修补：triage 输出形态从履职报告改决策呈现（不 bump 版本号）

- 触发：用户跑 SVC-PLATFORM-F026 真实 case 反馈"输出还是有点乱"+ 6 个具体问题
- 设计哲学：triage 输出的核心是给用户**决策依据**，不是 PMO 履职汇报。区分 Tier 1（用户必看的决策点）/ Tier 2（命中或异常才输出的折叠区）/ Tier 3（默认不输出，全部走 state.json）
- 处理（执行报告模板重写）：
  - **Tier 1（永远输出）**：意图理解段 / 流程承诺骨架 / ⏸️ 双对齐暂停点
  - **Tier 2（命中或异常才输出）**：KNOWLEDGE 命中 / ADR 命中 / 跨 Feature 冲突 / 环境异常 —— 仅一行摘要 + 详情可查 state.json
  - **Tier 3（默认不输出）**：角色可用性扫描结果（无异常） / 流程类型独立识别段（已体现在骨架顶部） / worktree mode/path/artifact_root 等机读字段
  - 加 3 个反模式硬约束：履职报告体感 / state.json 复述表 / 5 选 1 决策菜单
  - Feature 骨架渲染规范：默认 Stage（Dev/PM 验收/默认配置 Stage）一行带过；仅非默认决策标 💡 + 展开理由 cite 关键信号
  - 双对齐姿态：从 5 选 1 编号菜单退化回"ok / 自由反馈"二选一（PMO 解析反馈类型，不让用户先选编号）

- **本修补删了什么**（自我应用 P0-48 C 段元规则）：
  - 删 triage 执行报告模板的"段顺序固定"硬约束（KNOWLEDGE → ADR → 角色 → 流程类型 → 跨项目 → 环境配置 → 骨架 → 决策点 9 段平铺）
  - 删"角色可用性扫描"段独立输出（折到 Tier 3，仅异常时一行）
  - 删"流程类型识别"独立段（流程类型直接体现在 Feature 骨架顶部）
  - 删"环境配置预检 4 维度表"主对话渲染（worktree mode/path/sub_project/artifact_root 等机读字段，folded to state.json + 仅异常一行说明）
  - 删"无 ADR" / "无变更归属" 等空段输出（不命中就不输出）
  - 删 P0-38-B 的 3 选 1 启动确认菜单 + P0-49 一度退化的 5 选 1 菜单（合并为 ok / 自由反馈二选一）

- **加 1 删 1 论证**（P0-48 元规则要求）：
  - **加**：Tier 1/2/3 输出层次规范 + 反模式硬约束 + 骨架默认推荐折叠规范 + 双对齐二选一姿态规范
  - **删**：原 9 段平铺执行报告模板（履职报告体感的根源） + 5 选 1 编号菜单 + 环境配置 4 维度复述表
  - 净加规则数：±0（加输出层次规范 = 删履职模板平铺；加反模式禁令 = 删 5 选 1 菜单），符合 加 1 删 1

- **重新触发回来的 case 标尺**（P0-48 C-3 元规则）：
  - 如果用户在双对齐反馈时困惑"该回什么"——说明二选一姿态指引不够，可考虑加 3-4 个反馈范例帮助用户（不是回到 5 选 1 菜单）
  - 如果 Tier 2 折叠区漏了重要信号导致下游决策错——说明折叠条件太松，应加更细的"关键信号必须 Tier 1"判定（不是回到全 Tier 1 平铺）
  - 如果用户经常说"骨架某 Stage 不对"——说明骨架默认推荐 vs 非默认决策的判定不准，应改进推荐表（不是回到全展开理由）

- 风险控制：
  - Tier 2 折叠区"详情可查 state.json" → 用户跨 turn 续作时如果需要重新看 KNOWLEDGE 命中详情，可让 PMO 重读 state.json + 渲染（按需 ad-hoc，不加回主对话默认输出）
  - 双对齐二选一不是"取消选项"，是"取消编号菜单"——用户仍可自由反馈具体调整，PMO 仍可解析路径
  - 不影响 P0-49 主体设计（意图段 schema / 双对齐双对齐含义 / Plan Stage 子步骤 1 改造），仅影响输出形态
  - 红线数保持 15 条
  - 自我应用 P0-48 C 段元规则（删了什么段 + 加 1 删 1 + 重新触发标尺）

- 影响面：
  - 改动文件：2 个（stages/triage-stage.md 执行报告模板重写 + docs/CHANGELOG.md 修补段）
  - 不 bump 版本号（修补在 P0-49 内）
  - 用户体验：triage 输出从 9 段履职报告 → ~3 段决策呈现（Tier 1）+ 命中/异常时折叠摘要 → 信息密度提升 ~3 倍，认知负担降低

### P0-49：triage 意图理解段 + 双对齐暂停（全程 7 轮对话收敛）

- 触发：用户问"接收+理解输出的是 PRD 么"+ 7 轮挑战收敛（PRD 背景 → 意图卡 → INTENT.md → state.json.intent → PRD v0/v1 → 上下文驱动）
- 设计哲学：把"接收+理解"的意图职责从隐式（散落 Plan Stage PRD 起草中）显式化（triage 主对话渲染 + 用户双对齐）；意图 freeze 在 triage 上下文，下一阶段首次产出时自然继承到人读资产，零中转零冗余
- 处理（4 处改造）：
  - **P0-49-1. `stages/triage-stage.md` Step 8 加意图段渲染规范**：按流程类型分 schema（Feature/敏捷需求/Planning Why now+Assumptions+Real unknowns / Bug 症状+复现+影响+期望 / 问题排查 症状+已知+目标 / Micro 一句变更描述）；意图段输出硬规则（不落盘 + 下一阶段继承 + schema 不跨流程混用 + PMO 不替用户决策）
  - **P0-49-2. `stages/triage-stage.md` Step 8 暂停点改双对齐**：从 3 选 1（采用骨架 / 调整骨架 / 其他）改为「意图 + 流程一次确认」（回 ok = 全部采纳推荐 / 回数字 = 单点调整 / 回反馈 = 自由文本 / 回切流程 = 切换流程类型）；禁止"双对齐拆两次单对齐"反模式
  - **P0-49-3. `stages/plan-stage.md` 子步骤 1 改造**：PRD 背景段从 triage 上下文意图直接继承（Why now/Assumptions/Real unknowns 直接抄 + 用户已拍板的 unknown 标"已决"），不重新跟用户对齐意图、不写 PRD v0/v1 中间状态。子步骤 1 退化为单次产出（不拆 v0/v1 + 不弹中间暂停）
  - **P0-49-4. `roles/pmo.md` 调度责任段更新**：(a) Plan Stage 调度责任段加"意图段继承"职责说明；(b) 产品决策边界段 triage 决策范围加"意图理解段"作为 PMO 在 triage 的合法决策项

- **本 patch 删了什么**（自我应用 P0-48 C 段元规则）：
  - 删 plan-stage.md 子步骤 1 隐式职责"PM 起草前先做意图理解"（已转移到 triage）
  - 删 plan-stage.md 子步骤 1 隐式工作量"PRD 背景段从 0 起草"（背景段从 triage 继承）
  - 删 triage-stage.md Step 8 暂停点 3 选 1"采用 / 调整 / 其他"格式（合并为双对齐 ok / 数字 / 反馈 / 切流程）
  - 弃用 P0-49 讨论过程中提出的"INTENT.md 独立文件"方案（最终方案不需要新增 artifact）
  - 弃用 P0-49 讨论过程中提出的"state.json.intent 字段中转"方案（最终方案上下文驱动）
  - 弃用 P0-49 讨论过程中提出的"PRD v0 / v1 状态机 + 中间用户对齐暂停"方案（最终方案 PRD 不分版本）

- **加 1 删 1 论证**（P0-48 元规则要求）：
  - **加**：triage Step 8 意图段渲染（新职责）+ Step 8 双对齐暂停（替换 3 选 1）
  - **删**：plan-stage.md 子步骤 1 PRD 背景"从 0 起草"工作量 + 子步骤 1 隐式意图理解责任（与新加的 triage 意图职责正交平衡）
  - 净加规则数：±0（triage 加 = plan-stage 减），符合 加 1 删 1 原则

- **重新触发回来的 case 标尺**（P0-48 C-3 元规则要求）：
  - 如果意图段在 triage 渲染但用户经常 "意图不对，重做"——说明 PMO 草拟意图能力不够，应优化草拟规范（不是回去把意图理解推迟到 PRD 起草中）
  - 如果 PRD 背景段在评审中频繁被推翻 → 说明 triage 意图对齐流于形式（用户"双对齐"时没真看），应加强双对齐前的意图段呈现质量
  - 如果跨流程意图段 schema 难以维护 → 考虑收敛 schema（不是放弃按流程分形态，因为不同流程的"理解什么"本质不同）

- 风险控制：
  - 意图段不落盘 → 跨 session 续作时如果意图段还没落到对应资产（即 triage 完成但下一阶段第一次产出未发生），上下文丢失风险 → 文档约定"triage → 下一阶段首次产出 commit 在同一会话完成"作为软约束，不强制
  - PRD v0/v1 中间方案弃用 → 用户在 triage 双对齐时如果意图理解错过得不严，到 PRD 起草完成才发现意图错 → 仍需返工。但这种返工成本 ≈ 当前每次 PRD 写完才发现意图错的成本，没变重，只是把"意图发现错的时机"前置了
  - 红线数保持 15 条
  - 自我应用 P0-48 C 段元规则（CHANGELOG 含"删了什么"段 + 加 1 删 1 论证 + 重新触发标尺）

- 影响面：
  - 改动文件：4 个（triage-stage.md / plan-stage.md / roles/pmo.md / SKILL.md / init-stage.md / CHANGELOG.md）
  - 行数变化：triage-stage.md +~80 行（意图段 schema + 双对齐改造）/ plan-stage.md +~30 行（子步骤 1 意图继承段）/ roles/pmo.md +~10 行（triage 决策范围 + Plan 调度责任补充）
  - 用户体验：triage 暂停点信息密度大增（从"流程对齐"扩展为"意图 + 流程一次拍板"），决策疲劳不增（仍是一个暂停点）；Plan Stage 子步骤 1 PM 起草耗时降一半（背景段从 triage 继承不重新起）；意图错误的发现时机从"PRD 评审末"前置到"triage 双对齐时"，沉没成本陷阱降级

- 待跟进（非 P0-49 范围）：
  - Bug / 问题排查 / Feature Planning 流程的意图段 schema 还需在对应 Stage 入口（Bug 流程 RD 起草 BUG-REPORT.md / 问题排查 RD 介入 / Feature Planning PL 写产物）补"从上下文继承"的承接段（与 Plan Stage 子步骤 1 类似），下个 P0 patch 处理
  - 1-2 个真实 Feature 跑完后回顾"双对齐"是否真消除了意图层后期返工，意图段 schema 是否够用

---

## v7.3.10 + P0-48

> v7.3.10+P0-48 减负专版：v7.0 → v7.3.10+P0-47 累积约 50 个 P0 patch 几乎全是 reactive 加规则（每次解决一个用户痛点 → 加一条防御），没有任何版本专门做减法。用户反馈"框架越来越重"，本 patch 作为**第一次主动减负**：(A) 主对话输出红线 3 条治"行为漂移" (B) 静态减量 5 处治"双源/三源/重复" (C) P0 patch 设计契约元规则防"未来再次走回头路"。详见下方"加 1 删 1 元规则"。

### P0-48：减负专版（A 主对话输出红线 + B 静态减量 + C 元规则）

- 触发：用户反馈"teamwork 跑得越来越重了"+ 两个 case（PRD/TC section 完成度 ✅ 表 / state.json 配置回显表 / 工程性切片暂停 / 默认通道下 3 选 1 菜单）+ 用户拍板「A+B+C 全做」
- 设计哲学：从 reactive defense（每次抱怨加一条规则）转向 deletion sprint（找冗余 + 删 + 合并 + 单源化）。规模可控；复杂度档位（D 段）拆 P0-49 后续做
- 处理（9 处改造）：

  **A. 主对话输出红线 3 条**（治行为漂移；用户精选 3 项落地）：
  - **A-1. 禁止「✅ section 完成度一览表」**：plan/blueprint/review-stage.md 各加红线段。原因：段位齐全是隐含合同（PMO 校验不通过不会进 review）；列 ✅ 表 = 噪音
  - **A-2. 禁止「state.json 配置以表格人读复述」**：state.json 是机读真相源；主对话只述「已写入 X」+ 1-2 句关键决策点
  - **A-3. 禁止「让用户预览/避免重写」类工程性切片暂停**：违反 P0-45 反转语义；评审本身就是发现偏离的机制
  - 判定标尺（如何重新触发回来）：每条都给"如果出现 case Y 才考虑加回"标尺，作为后续验证

  **B. 静态减量 5 处**（治双源/重复）：
  - **B-1. 三 Stage 入口实例化合并**：原 plan-stage.md L154-266 (113行) + blueprint-stage.md L12-43 + review-stage.md L89-125 三处入口实例化 ~180 行重复 → 抽取到新建 `standards/stage-instantiation.md` (~146行) 单一权威源；三 Stage 入口段精简为 ~15 行引用
  - **B-2. Micro 身份切换规范单源化**：roles/pmo.md L5 长行复述删除 → 改为引用 SKILL.md 单源；同时把 P0-20-B 反漂移补丁（第一人称锚点 + 追加改动回退规则）补齐到 SKILL.md（之前 SKILL.md 缺这两条，导致 pmo.md 多复述了）
  - **B-3. ok = 按 💡 建议 约定双源化**：roles/pmo.md L21-32 复述（12 行）→ 改为引用 RULES.md L250-260 单源
  - **B-4. 评审组合推荐表权威源标注**：plan-stage.md § Plan Stage 评审组合智能推荐表 标 🔴 唯一权威源；roles/pmo.md L711-776 (Stage 入口偏差判定 + 输出格式 ~65行) 删除 → 改为引用 standards/stage-instantiation.md
  - **B-5. 删 business_direction_locked_at frontmatter 字段**：templates/prd.md + templates/feature-state.json + stages/plan-stage.md 同步。原因：P0-44 改为讨论模式后此字段无人填，时刻信息由 state.json 顶层 updated_at 单一记录
  - 红线合并：#2+#6+#7 合并为单条「流程类型规范」（用 sub-rule (a)(b)(c) 表达）；#11+#13 合并为单条「写操作硬门禁链」(a) 流程入口门禁 + (b) Subagent dispatch 门禁。15 编号保留（#6/#7/#13 改为 "见 #X" 引用，外部引用零破坏）。SKILL.md + init-stage.md 同步

  **C. P0 patch 设计契约元规则**（防未来累积膨胀）：
  - **C-1. 加 1 删 1 原则**：SKILL.md 红线段后新增「P0 patch 设计契约」段。新加 checklist 项 / frontmatter 字段 / 红线 / 决策菜单 / 暂停点 → 必须同 patch 删/合并一项老规则；找不到可删可合并项时必须 CHANGELOG 写"为什么必须新加且无法换合并"的论证
  - **C-2. 删了什么段落**：每个 P0 patch CHANGELOG 必须含「删了什么」段落。即使该 patch 主要是新增也要主动列出删/合并/单源化的内容；纯加新规则的 patch 不予合入
  - **C-3. 验证标尺**：每条新加规则必须配"如果它有用，会通过什么 case 重新触发回来"作为后续验证标尺
  - 例外白名单：bug 修 / 错别字 / 链接失效 / 用户明确要求 / 新角色或新 Stage（结构性扩展）

- **本 patch 删了什么**（自我应用 C-2 规则）：
  - 删 plan-stage.md L154-266 入口实例化重复段（114 行）→ 抽到 standards/stage-instantiation.md
  - 删 blueprint-stage.md L12-43 入口实例化重复段（32 行）→ 引用化
  - 删 review-stage.md L89-125 入口实例化重复段（37 行）→ 引用化
  - 删 roles/pmo.md L5 Micro 身份切换长行复述（约 25 行）→ 引用 SKILL.md
  - 删 roles/pmo.md L21-32 ok = 按建议约定复述（约 14 行）→ 引用 RULES.md
  - 删 roles/pmo.md L711-776 Stage 入口偏差判定段（约 65 行）→ 引用 standards/stage-instantiation.md
  - 删 templates/prd.md frontmatter `business_direction_locked_at` 字段
  - 删 templates/feature-state.json `business_direction_locked_at` 字段
  - 合并 SKILL.md 红线 #2+#6+#7（#6/#7 改为引用 #2）
  - 合并 SKILL.md 红线 #11+#13（#13 改为引用 #11）
  - 合并 init-stage.md 红线对应同步

- 风险控制：
  - 入口实例化合并 → 三 Stage 行为不变（standards/stage-instantiation.md 是无损抽取，红线全保留）
  - 红线 15 编号保留 + 外部引用零破坏（#6/#7/#13 仍存在但内容变 "见 #X"）
  - business_direction_locked_at 删字段 → 老 PRD 兼容（PMO 读取时该字段视为可选信息字段，不驱动决策）
  - 主对话红线段对历史 case 不追溯，仅约束未来主对话输出
  - C 段元规则不立即应用到本 patch（自我应用见上方"本 patch 删了什么"段，已自洽）

- 影响面：
  - 改动文件：~10 个（SKILL.md + init-stage.md + 3 Stage spec + roles/pmo.md + templates/prd.md + templates/feature-state.json + 新建 standards/stage-instantiation.md + CHANGELOG.md）
  - 行数变化：plan-stage.md 919→844 (-75) / blueprint-stage.md 382→376 (-6) / review-stage.md 761→754 (-7) / roles/pmo.md 2185→2119 (-66) / 新建 standards/stage-instantiation.md +146 / 三 Stage 加主对话红线段 +~50 行
  - 净行数变化：约持平（删 ~155 行，加 ~196 行新内容含主对话红线段 + 抽取的统一规范）
  - DRY 收益：三 Stage 入口实例化 + Micro 身份切换 + ok 约定 + Stage 入口偏差判定 单源化 → 维护成本大幅下降，漂移风险消除
  - 用户体验：主对话输出更紧凑（不再有 ✅ 表 / 复述表 / 工程性切片暂停 / 默认通道下 3 选 1 菜单 padding）

- 待跟进（非 P0-48 范围）：
  - **P0-49 复杂度档位**（D 段，已拆出）：triage 加 trivial / standard / complex 三档替代 Micro / Feature 二档（state.json schema 变更 + triage 重写 + 各 Stage 入口加档位识别）。结构性变更，单独做更安全
  - 1-2 个真实 Feature 跑下来后回顾"主对话红线"是否真消除了 padding 行为
  - 如果发现 padding 仍然出现 → 不是规则不够，是模型行为偏置——可考虑在 plan-stage.md 加正面示例（"应该这样输出"）

---

## v7.3.10 + P0-47

> v7.3.10+P0-47 PRD 模板合并：原 templates/prd.md 含两套模板（"PRD.md（标准模板）"业务类 + "PRD.md（技术类变体）"纯技术 refactor），P0-46 后两套差异已小（技术方案要点已移到 TECH.md）。本次合并为统一通用模板，差异通过"按需必填"标注表达（业务类必填 / 纯技术 refactor 可省）。删除 prd_variant frontmatter 字段（合并后不需要变体区分）。

### P0-47：PRD 模板合并（删技术类变体 + 加按需必填）

- 触发：用户「目前 prd 有两套，是否可以合成一套不区分产品和技术。只用 PRD.md（标准模板）」+「确认」
- 设计决策（用户拍板）：
  - **合并为统一通用模板**：保留"PRD.md（标准模板）"作为主体，删除"PRD.md（技术类变体）"段
  - **按需必填标注**：用户故事 / 功能需求 / 埋点需求 标记"业务类必填；纯技术 refactor 可省"
  - **删除 prd_variant frontmatter 字段**：合并后不需要变体区分
  - 红线数保持 15 条
- 处理（4 处改造）：
  - **P0-47-1. `templates/prd.md` 合并**：用 sed 删除 L143-232（"PRD.md（技术类变体）"整段，90 行）；标准模板加 v7.3.10+P0-47 重构说明 + 按需必填标注（用户故事 / 功能需求 / 埋点需求 3 处）
  - **P0-47-2. `stages/plan-stage.md` Feature 类型识别表**：删 prd_variant 列；加 P0-47 说明（识别用其他信号综合判断）
  - **P0-47-3. `TEMPLATES.md` 索引**：prd.md 描述改为"统一通用模板，含按需必填标注"
  - **P0-47-4. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-46 → 7.3.10+P0-47
- 风险控制：
  - 老 PRD（已含 prd_variant 字段）兼容：PMO 读取时 prd_variant 字段视为信息字段，不驱动模板选择
  - 按需必填标注清晰（🟡 + 业务类 / 纯技术 refactor 区分）
  - 不破坏 PRD-REVIEW.md schema（独立段，未受影响）
  - 红线数保持 15 条
- 影响面：
  - 改动文件：4 个（prd.md / plan-stage.md / TEMPLATES.md / SKILL.md / init-stage.md / CHANGELOG.md）
  - prd.md 行数：404 → 322（减 82 行 / 减 20%；删 90 行 + 加重构说明与按需必填标注约 8 行）
  - 用户体验：
    - PRD 模板从两套 → 一套，PMO 起草时不再判断"用哪个变体"
    - 按需必填标注让纯技术 refactor 也能用统一模板（标注"不适用"）
    - 配合 P0-46 PRD 边界归位，PRD 整体更聚焦核心 AC list
- 待跟进（非 P0-47 范围）：
  - 1-2 个真实纯技术 refactor Feature 跑下来后回顾按需必填标注是否清晰

---

## v7.3.10 + P0-46

> v7.3.10+P0-46 PRD 边界归位 + 职责正交回归：用户反思 P0-44 设计——把 RD/QA/Designer 视角的关注点（接口 schema / 测试用例规划 / 数据模型 / 视觉风格等）塞到 PM 起草规范是越界，违反 teamwork 框架原本的"Plan / Blueprint / Test"三阶段职责正交。导致 PRD 越界 + AC list 被技术细节淹没 + TECH/TC 被掏空 + Plan Stage 评审角色发不该发的 finding（如 RD 在 Plan Stage 提"接口 schema 不完整"）。本次修正：(1) PRD 仅回答"做什么 + 为什么"（产品/AC 视角），技术细节移到 TECH.md（Blueprint Stage RD 写），测试细节移到 TC.md（Blueprint Stage QA 写）；(2) Plan Stage 联合评审 review_scope=prd，仅审产品视角（业务可行性 / AC 可测试性 / 用户故事完整性）；(3) Blueprint Stage 加 TECH 起草规范 + TC 起草规范段，让技术/测试细节在正确的位置内化；(4) PRD-REVIEW.md frontmatter 加 review_scope 字段，machine-verifiable 评审范围。

### P0-46：PRD 边界归位 + 职责正交回归

- 触发：用户「prd 评审是否过重，是否掺杂了一些技术和测试的细节。是不是 prd 重点关注产品目标和 ac list 更合适，其他的细节放到技术方案里」+「按这个修复」
- 设计决策（用户拍板）：
  - **职责正交回归**：PRD（做什么 + 为什么）/ TECH（怎么做）/ TC（怎么测）三阶段职责清晰
  - **PRD 起草规范精简**：删 RD 视角必填项 6 条 + QA 视角必填项 6 条 + UI 视觉风格约束（移到对应 Stage）
  - **Plan Stage 评审 scope=prd**：RD/QA/Designer 评审 PRD 时仅审产品视角，不审技术/测试实现
  - **Blueprint Stage 加 TECH/TC 起草规范**：技术/测试细节在 RD/QA 起草自己的产物时内化（不在 PM 起草 PRD 时）
  - 红线数保持 15 条
- 处理（5 处改造）：
  - **P0-46-1. `stages/plan-stage.md` PM 起草规范精简**：
    - 删 RD 视角必填项（接口 schema / 数据模型 / migration / 调用链路 / 异常处理实现 / 性能 / 复用模式）
    - 删 QA 视角必填项（测试用例规划 6 条）
    - 删 UI 视觉风格约束维度
    - 保留通用 checklist（产品目标 / AC / 影响范围 / 业务风险 / KNOWLEDGE 关联）
    - 保留 UI 用户故事维度（高层产品视角，requires_ui=true 时填）
    - 加 "PRD 不写什么"边界段（10 条具体禁止项）
    - 加 "PMO dispatch 评审角色时明确 review_scope=prd"约束
    - 加各角色（RD/QA/Designer）评审 PRD 时的 scope 关注点（产品视角 ✅ / 技术-测试-视觉细节 ❌）
  - **P0-46-2. `stages/blueprint-stage.md` 加 TECH/TC 起草规范**：
    - QA 编写 TC 段加 v7.3.10+P0-46 TC 起草规范 checklist（AC×TC 矩阵 / 边界 / 异常 / 集成 / 性能 / ROLLBACK）
    - RD 编写 TECH 段加 v7.3.10+P0-46 TECH 起草规范 checklist（接口 schema / 数据模型 / 调用链路 / 异常处理实现 / 性能实现 / 复用模式）
  - **P0-46-3. `templates/prd.md` schema 加 review_scope 字段**：
    - PRD-REVIEW.md frontmatter reviews[] 加 review_scope 字段（值：prd / blueprint / code-review）
    - PRD 评审 review_scope=prd（强制约束）
  - **P0-46-4. `roles/pmo.md` 调度责任段加 review_scope=prd 约束**：
    - PMO dispatch 子步骤 3 评审角色时必须 cite「按 plan-stage.md § 子步骤 3 评审 scope = PRD 范围」
    - 评审角色 finding 越界（如 RD 提"接口 schema 不完整"）→ PMO 拦截 + 标记越界 + 不计入有效 finding
  - **P0-46-5. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-45 → 7.3.10+P0-46
- 风险控制：
  - 不破坏 P0-44 的"PM 起草规范"框架，仅精简内容范围
  - PRD 仍保留必要的产品/AC 视角覆盖（不是完全 free-form）
  - TECH/TC 起草规范从 PM 移到 RD/QA 自己的起草段（位置正确）
  - 用户主动越界（如硬要 RD 在 Plan 评审时提技术细节）→ PMO 拦截 + 提示移到 Blueprint Stage
  - 红线数保持 15 条
- 影响面：
  - 改动文件：5 个（plan-stage.md / blueprint-stage.md / prd.md / pmo.md / SKILL.md / init-stage.md / CHANGELOG.md）
  - PRD 长度：典型 PRD 减 30-50%（删除技术/测试细节段）
  - TECH/TC 长度：增加（吸收原 PRD 的技术/测试细节）
  - Plan Stage 评审 finding 减少（RD/QA 不再越界提技术/测试细节）
  - Blueprint Stage 评审 finding 增加（技术/测试细节在正确位置评审）
  - 用户体验：
    - PRD 更聚焦核心 AC list（读 PRD 的人快速找到核心业务行为）
    - TECH/TC 更完整（不再被 PRD 掏空）
    - Plan Stage 评审更快（RD/QA scope 更窄）
    - Blueprint Stage 评审更深（技术/测试细节在正确位置）
- 待跟进（非 P0-46 范围）：
  - 1-2 个真实 Feature 跑下来后回顾 PRD 瘦身效果（AC list 是否清晰 / 技术细节是否真移到 TECH）
  - 评审越界拦截规则（如何让 PMO 准确识别 finding 是否越界）

---

## v7.3.10 + P0-45

> v7.3.10+P0-45 Stage 入口实例化默认通道反转（P0-42 快速通道扩展为默认）：用户实战 case 暴露 P0-38-A 设计的"Stage 入口实例化用户瞬时确认"暂停点信息量低——triage 骨架已是用户拍板权威，PMO 实例化决策大多数情况轻微偏差或完全采纳 hint，5 选 1 暂停点在实战中决策疲劳 > 价值。P0-42 加快速通道（hint 完全采纳跳过）但门槛太高（需满足 4 条件 ALL）。本次反转为默认：**默认通道无暂停点**（PMO 直接 cite hint + 写 *_substeps_config + 进入 Stage 内部），**仅严重偏差时触发标准通道**（⏸️ 5 选 1 暂停点）。"严重偏差"判定矩阵（角色组合变更 / execution 整体反转 / Stage 跳过 / external 启用反转 / hint 缺失 / triage 选项 2-3）。用户主动打断仍可触发标准通道（输入"调整骨架"等）。适用 Plan / Blueprint / Review 三个 Stage。

### P0-45：Stage 入口实例化默认通道反转

- 触发：用户「各个阶段 Dev Stage 入口实例化用户瞬时确认，这个只有推荐和 triage 有严重偏差时在确认」+「1」（启动 P0-45）
- 设计决策（用户拍板）：
  - **默认通道无暂停**（轻微偏差或完全采纳 → PMO 直接进入 Stage 内部）
  - **严重偏差才出暂停**（角色组合变更 / execution 整体反转 / Stage 跳过 / external 启用反转 / hint 缺失 / triage 选项 2-3）
  - **用户主动打断仍可触发标准通道**（输入"调整骨架"等）
  - 红线数保持 15 条
- 处理（5 处改造）：
  - **P0-45-1. `stages/plan-stage.md` 默认通道反转**：原"快速通道"改为默认；原"标准通道"仅严重偏差时触发；硬约束段重写
  - **P0-45-2. `stages/blueprint-stage.md` 同步**：入口实例化加默认通道判定段
  - **P0-45-3. `stages/review-stage.md` 同步**：入口实例化加默认通道判定段
  - **P0-45-4. `roles/pmo.md` 加「Stage 入口偏差判定」段**：严重偏差判定矩阵（6 个维度 × 轻微/严重对照）+ PMO 自我评估输出格式（默认通道 / 标准通道）
  - **P0-45-5. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-44 → 7.3.10+P0-45
- 风险控制：
  - 用户主动打断保留（默认通道下输入调整意图立即回退到 5 选 1）
  - 严重偏差判定矩阵硬规则（不允许 PMO 自我评估随意宽松）
  - hint 缺失时强制走标准通道（兜底）
  - 红线数保持 15 条
- 影响面：
  - 改动文件：5 个（plan-stage.md / blueprint-stage.md / review-stage.md / pmo.md / SKILL.md / init-stage.md / CHANGELOG.md）
  - 用户体验：每个 Feature 减 3 个暂停点（Plan / Blueprint / Review 入口默认无暂停）+ 严重偏差时仍出暂停（保留控制权）
  - 决策疲劳：典型 Feature 暂停点从 ~5 个 → ~2 个（仅子步骤 5 用户最终确认 + Ship 暂停）
- 待跟进（非 P0-45 范围）：
  - 1-2 个真实 Feature 跑下来后回顾"严重偏差"判定准确度（PMO 自我评估是否过宽 / 过严）
  - 是否需要扩展到其他 Stage（Test / Browser E2E / PM 验收 / Ship）的入口暂停点

---

## v7.3.10 + P0-44

> v7.3.10+P0-44 Plan Stage 性能重构：用户实战 case 暴露 Plan Stage 耗时偏长（典型 60-200 min）。瓶颈分析：(1) 多角色并行评审 dispatch 数大（PL/RD/QA/Designer/PMO/external 6 角色）；(2) RD/QA finding 90% 是通用关注点（边界场景/接口设计/测试可行性），事后评审才发现 → 多轮循环；(3) PL 评审作为独立 finding（P0-34）失去了多轮对话的对抗深度（v7.3.x 实战验证好用）；(4) 每个角色独立 subagent 冷启动税大。本次重构核心：把"事后多角色独立评审"前置为"事前 PM 起草规范" + "PL-PM 业务讨论恢复" + "QA+RD+Designer(可选) 主对话联合评审 ∥ external 后台并行"。预估典型 Feature 耗时减半（小 Feature 40-60 min → 15-25 min；中 Feature 60-90 min → 25-40 min）。

### P0-44：Plan Stage 性能重构（PM 起草规范 + PL-PM 讨论恢复 + 主对话联合评审 + external 并行）

- 触发：用户「plan stage 耗时太久，是否有优化的可能」+ 多轮迭代讨论后拍板「PM 起草规范增加，PL PM 讨论完成后，RD+QA 视角组合评审在主对话，并行外部模型评审」+「应该是 QA+RD+designer (可选) 联合评审」+「ok」
- 设计决策（用户拍板）：
  - **核心原则**：90% 通用关注点事前内化（PM 起草规范）+ PL-PM 真对抗（讨论模式）+ 10% 领域 finding 事后评审（主对话联合）+ 异质视角保留（external 后台并行）
  - **Plan Stage 5 子步骤重构**：
    - 子步骤 1：PM 按规范起草 PRD（含通用 + RD/QA + UI 影响 + 子项目技术栈 checklist）
    - 子步骤 2：PL-PM 讨论（v7.3.x 模式恢复，业务方向锁死保留 P0-34-C）
    - 子步骤 3：QA+RD+Designer(可选) 主对话联合评审 ∥ external 后台 shell 并行
    - 子步骤 4：PM 回应 + 修订 PRD（保留 P0-34-A/B 对抗自查 + DEFER 收紧）
    - 子步骤 5：⏸️ 用户最终确认 PRD（核心暂停点，理想路径下唯一暂停点）
  - **Designer 触发双保险**：PRD frontmatter `requires_ui: true` 或 UI 关键词命中
  - **discuss/PL-FEEDBACK + PM-RESPONSE 文件契约恢复**（撤销 P0-43 废止）
  - **PRD-REVIEW.md schema 调整**：reviews[] 仅含 qa / rd / designer? / external?（删 pl/pmo）
  - 红线数保持 15 条
- 处理（7 处改造）：
  - **P0-44-1/2/3/4. `stages/plan-stage.md` 5 子步骤序列重写**：删 P0-34/P0-43 的 200 行（含原阶段 2a/2b 多角色独立评审），写入新的 200 行（PM 起草规范 checklist + PL-PM v7.3.x 讨论 + 主对话身份切换 QA→RD→Designer + external 后台并行 + PM 回应 + 用户确认 + 过程硬规则 + 多视角独立性）
  - **P0-44-5. `templates/prd.md` schema 调整**：PRD frontmatter 加 `requires_ui` 字段；PRD-REVIEW.md frontmatter `reviews[].role` 枚举从 `pl|rd|designer|qa|pmo` 改为 `qa|rd|designer|external`（删 pl 和 pmo）
  - **P0-44-6. `roles/pmo.md` 调度责任段重写**：v7.3.10+P0-44 重构 6 段调度职责（PM 起草前提醒 / PL-PM 讨论调度 / 主对话身份切换 / 子步骤 4 校验 / 快速通道判定 / 入口实例化硬约束）
  - **P0-44-7. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-43 → 7.3.10+P0-44
- 风险控制：
  - PM 起草规范 checklist 覆盖 90% RD/QA 通用关注点（事前内化）
  - 子步骤 3 主对话身份切换保留 RD/QA/Designer 真 finding 能力（剩余 10% 领域 finding）
  - external 后台 shell 并行保留异质视角对抗深度
  - PL-PM v7.3.x 讨论模式实战已验证（用户原话"之前 PL PM 讨论效果很好"）
  - 保留 P0-34-A/B（DEFER 收紧 + 对抗自查）+ P0-34-C（业务方向锁死）+ P0-38（external 角色）+ P0-42（快速通道）
  - 红线数保持 15 条
- 影响面：
  - 改动文件：4 个（plan-stage.md 主体 / prd.md schema / pmo.md 调度责任 / SKILL.md / init-stage.md / CHANGELOG.md）
  - plan-stage.md 子步骤序列：原 200 行重写为新 200 行（结构完全变）
  - PRD-REVIEW.md schema：reviews[] 角色从 5 类减到 4 类（删 pl/pmo）
  - discuss/PL-FEEDBACK / PM-RESPONSE：从 P0-43 废止恢复为 v7.3.x 必需契约
  - 用户体验：
    - Plan Stage 耗时减半（典型 Feature 40-60 min → 15-25 min）
    - 子步骤 3 主对话内 QA→RD→Designer 顺序切换（不再 dispatch 多个 subagent）
    - external 后台并行（不阻塞主对话）
    - 理想路径下仅 1 个暂停点（子步骤 5 用户最终确认）
- 预估收益（vs P0-34/P0-43）：
  - 小 Feature 1 轮通过（无 UI）：40-60 min → 15-25 min（减 60%）
  - 中 Feature 1 轮通过（无 UI）：60-90 min → 25-40 min（减 55%）
  - 含 UI 中 Feature：70-100 min → 30-50 min（减 50%）
  - 大 Feature 2 轮通过：120-150 min → 55-85 min（减 45%）
- 待跟进（非 P0-44 范围）：
  - 1-2 个真实 Feature 跑下来后回顾耗时实测（PM 起草规范覆盖度 + 主对话身份切换可行性 + external 后台并行实施）
  - 类似的 Stage 性能优化（Blueprint Stage / Review Stage 是否需要类似重构）

---

## v7.3.10 + P0-43

> v7.3.10+P0-43 智能推荐表迁移到 plan-stage.md（Stage 优先原则）+ 清理 P0-34 残留旧契约：实战 case 暴露用户对架构的洞察——「Plan Stage 评审组合智能推荐表」原写在 roles/pmo.md（v7.3.10+P0-34-1 加入），但这套规则的本质是 "Plan Stage 入口怎么决策 review_roles + execution"，是 Plan Stage 契约的内部规范，应该由 stages/plan-stage.md 作为权威源（不是 PMO 角色规范）。把 Stage 决策规则放在 PMO 角色文件违反了 teamwork 框架的"Stage 优先"原则。本次系统重构：(1) 把 130 行智能推荐表（Step 1 Feature 类型识别 / Step 2 评审角色推荐 / Step 3 执行方式推荐 / PL 优先权 / 评审循环 + 超 3 轮处理 / 硬规则）整体迁移到 stages/plan-stage.md，作为 Plan Stage 入口实例化的决策权威源；(2) roles/pmo.md 仅保留 30 行 PMO 调度责任概述 + 指向引用；(3) 顺便加"小 Feature 默认主对话"硬约束（≤5 文件 + 单子项目 + 无 UI → RD/PL 默认 main-conversation，针对实战 case INFRA-F019 的 RD subagent 偏离推荐表问题）；(4) 清理 plan-stage.md 残留 `discuss/PL-FEEDBACK-R{N}.md` / `PM-RESPONSE-R{N}.md` 旧契约（P0-34 重构 PL 升格评审角色后没清干净的尾巴），改为❌废止。

### P0-43：智能推荐表迁移 + discuss 旧契约清理

- 触发：用户「roles/pmo.md 不需要改，这写规范应该是 plan-stage.md 决定的」+「ok」（启动 P0-43）
- 设计决策（用户拍板）：
  - **Stage 优先原则**：Plan Stage 入口决策规则属于 Stage 契约，权威源在 stages/plan-stage.md（不在 roles/pmo.md）
  - **整体迁移**：130 行智能推荐表完整内容（不是 cite 引用）
  - **roles/pmo.md 留 PMO 调度责任概述**：4 段简短清单（triage 生成 hint / Stage 入口实例化 / 快速通道判定 / 硬约束 cite），指向 plan-stage.md
  - **新增"小 Feature 默认主对话"硬约束**：实战 case INFRA-F019 反例驱动（≤5 文件 + 单子项目 + 无 UI → RD/PL 默认 main-conversation）
  - **discuss/* 旧契约废止**：PRD-REVIEW.md frontmatter reviews[] 是统一权威源，禁止双重产出
  - 红线数保持 15 条
- 处理（3 处改造）：
  - **P0-43-1. 迁移智能推荐表 roles/pmo.md → stages/plan-stage.md**：
    - 在 plan-stage.md 入口实例化段后插入完整推荐表（Step 1-5 + PL 优先权 + 评审循环 + 硬规则 + 新增 P0-43 小 Feature 默认主对话硬约束）
    - 删 roles/pmo.md L675-807 完整智能推荐表段（用 sed 删 133 行）
    - 在 roles/pmo.md 加 30 行简短引用：「Plan Stage 评审组合智能推荐（v7.3.10+P0-43 迁移到 plan-stage.md）」+ PMO 调度责任 4 段
  - **P0-43-2. 清理 plan-stage.md discuss 旧契约**：
    - L600-601 `discuss/PL-FEEDBACK-R{N}.md` / `PM-RESPONSE-R{N}.md` 从「🔴 必需」改为「❌ v7.3.10+P0-43 废止」+ 说明（P0-34 PL 升格后 finding 应在 PRD-REVIEW.md frontmatter）
    - L761 文件树尾部 `discuss/PL-FEEDBACK-R{N}.md + PM-RESPONSE-R{N}.md` 删除 + 加废止说明
    - 保留 forbidden_files 列表对 discuss/ 的引用（外部模型独立性约束需禁读 discuss/，但本身不强制产出）
  - **P0-43-3. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-42 → 7.3.10+P0-43
- 风险控制：
  - 智能推荐表内容完整迁移（130 行 → 130 行）+ 简短引用（30 行），总行数减少
  - roles/pmo.md 仅留概述指向，不重复 stage spec 内容（DRY 原则）
  - discuss/PL-FEEDBACK / PM-RESPONSE 废止：旧 Feature 已存在的 discuss/* 不强制迁移（state.json 历史快照），新 Feature 强制不产出
  - 不增红线（红线数保持 15 条）
- 影响面：
  - 改动文件：3 个（roles/pmo.md / stages/plan-stage.md / SKILL.md / init-stage.md / CHANGELOG.md）
  - roles/pmo.md 行数：2204 → 2071（删 133 行智能推荐表）+ 加 30 行引用 = 净减 ~100 行
  - stages/plan-stage.md：加 130 行智能推荐表 + 删 2 行 discuss 必需契约 + 加 P0-43 小 Feature 默认主对话硬约束
  - 架构正交性：Stage 决策规则归 Stage spec / PMO 角色规范不兼任 Stage 决策权威
  - 用户体验：
    - PMO 在 Plan Stage 决策时单一权威源（plan-stage.md），不再 pmo.md / plan-stage.md 双跑
    - 小 Feature 不再被 PMO 默认 subagent 化（实战 case INFRA-F019 反例修复）
    - 新 Feature 不再产 discuss/PL-FEEDBACK / PM-RESPONSE 双重产物
- 待跟进（非 P0-43 范围）：
  - 1-2 个真实 Feature 跑下来后回顾智能推荐表迁移效果（PMO 是否仍在 pmo.md 找推荐表）
  - 类似的 Stage 决策规则是否还有放错位置的（如 Blueprint Stage 评审组合 / Review Stage 三视角）

---

## v7.3.10 + P0-42

> v7.3.10+P0-42 triage 输出精简 + worktree 默认路径硬规则强化 + Plan Stage 入口快速通道：用户实战 case（INFRA-F019）暴露三个真实问题——(1) triage 输出 12 段（含「流程步骤描述」+「Feature 骨架」+「骨架摘要」三段重复信息）+ 越界提示（"BG-015 协调 ship"是 PM 验收的事却在 triage 抛出）= 决策疲劳；(2) Plan Stage 入口实例化的 5 选 1 暂停点信息量低——execution_hints 已说"启用 X/Y/Z 评审"，唯一新决策维度是 execution 方式，而 P0-34-C 推荐表已默认；(3) worktree 路径偏离 P0-39 默认（用了项目历史 .claude/worktrees/feature-... 而非 .worktree/...，且加了 feature- 前缀）。本次系统精简：(A) triage Output Contract 删「流程步骤描述」段（P0-26 残留）+ 删「骨架摘要」段（"预计耗时"加到骨架表尾）+ 环境配置预检表 8 行合并 4 行 + 禁止越界提示（"BG 协调 ship"等）；执行报告模板段顺序固定化；(B) Plan Stage 入口实例化加「快速通道」（hint 完全采纳时跳过 5 选 1 暂停点直接进 PRD 起草）+ 「标准通道」回退条件明确；(C) worktree 路径硬规则强化（禁止用项目历史路径 / 禁止加 feature- 前缀 / cite localconfig 字段或硬默认）。形成 triage 紧凑（8 段）+ Plan 入口可跳暂停点 + worktree 路径不再偏离的实战级闭环。

### P0-42：triage 输出精简 + Plan 入口快速通道 + worktree 路径硬规则

- 触发：用户实战 case（INFRA-F019 启动）+ 用户「triage 阶段输出的东西冗余，需要精简合并」+ 「为什么有 Plan Stage 入口实例化用户瞬时确认（5 选 1）」+「启动」（P0-42 实施）
- 设计决策（用户拍板）：
  - **triage 输出从 12 段精简为 8 段**：删冗余（流程步骤描述 / 骨架摘要）+ 合并（环境配置预检表 4 行）+ 禁止越界（BG 协调 ship 等）
  - **Plan Stage 入口加快速通道**：hint 完全采纳时跳过 5 选 1 暂停点（条件：triage 选 1 + hint 完整 + 完全采纳 + execution 默认）
  - **worktree 路径硬规则**：禁止用项目历史路径（如 .claude/worktrees/）+ 禁止加 feature- 前缀；唯一合法来源是 localconfig.worktree_root_path（缺失硬默认 .worktree）
  - **不增红线**：通过 Stage 契约 + 反例直接对照实战 case
- 处理（4 处改造）：
  - **P0-42-1. `stages/triage-stage.md` 输出精简**：
    - Step 7「流程步骤描述」段保留作锚点但实际输出合并到 Step 8 骨架（P0-26 残留删除）
    - 「骨架摘要」独立段删，"预计耗时"加到骨架表尾一行
    - 环境配置预检表从 8 行合并为 4 行（worktree / 路由 / 分支 / 工作区）
    - 执行报告模板加段顺序硬约束 + 禁止越界提示（BG 协调 ship / 耗时数据来源等）
  - **P0-42-2. `stages/plan-stage.md` worktree 路径硬规则强化**：
    - 禁止偏离 P0-39 默认路径（项目历史 / 团队约定 / "上次也是这么用的"等理由）
    - 禁止子目录加 feature- 前缀（worktree path 仅用 {Feature 全名}）
    - 唯一合法来源：localconfig.worktree_root_path 字段或硬默认 .worktree
    - 含实战反例（INFRA-F019 case 完整对照）
  - **P0-42-3. `stages/plan-stage.md` Plan Stage 入口快速通道**：
    - 快速通道条件 ALL（triage 选 1 / hint 完整 / 完全采纳 / execution 默认）
    - 满足全部 → 直接 cite hint + 写 plan_substeps_config + 进 PRD 起草，无暂停点
    - 标准通道回退条件（hint 不完整 / 偏离 / triage 选项 2-3 / Blueprint/Review 入口）
    - 用户在快速通道下仍可主动打断（输入"调整骨架"等）回退标准通道
  - **P0-42-4. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-41 → 7.3.10+P0-42
- 风险控制：
  - 不破坏 P0-38-A/B 骨架契约（仅简化 triage 输出和 Plan 入口暂停点）
  - 快速通道有明确触发条件 + 标准通道兜底（hint 不完整自动走标准通道）
  - 用户主动打断快速通道（输入"调整骨架"）立即回退
  - Blueprint/Review 入口仍走标准通道（上下文更复杂，需用户确认）
  - 不增红线（红线数保持 15 条）
- 影响面：
  - 改动文件：3 个（triage-stage.md / plan-stage.md / SKILL.md / init-stage.md / CHANGELOG.md）
  - triage 输出段数：12 → 8（紧凑度提升 33%）
  - Plan Stage 入口暂停点：5 选 1 必出 → hint 完全采纳时跳过（决策疲劳显著降低）
  - worktree 路径合规性：禁止偏离 P0-39 默认 / 禁止 feature- 前缀
  - 用户体验：
    - triage 输出更聚焦（删了流程步骤描述 / 骨架摘要 / BG 越界等冗余段）
    - Plan Stage 启动更顺畅（典型场景跳过 5 选 1，hint 完全采纳直接进 PRD 起草）
    - worktree 路径不再偏离（实战 case 类问题不再发生）
- 待跟进（非 P0-42 范围）：
  - 1-2 个真实 Feature 跑下来后回顾 triage 输出精简效果（用户决策疲劳实测）+ 快速通道命中率
  - Blueprint/Review 入口是否也需要快速通道（待积累实战数据后决策）

---

## v7.3.10 + P0-41

> v7.3.10+P0-41 sub_project 路由权威 + worktree 缺失硬默认 + 写操作前路径硬门禁：用户实战 case（F059-HomeShortcutKeySync）暴露 4 个关键流程漏洞——(1) sub_project=FE 写到 state.json 但产物文档落在根 `docs/features/` 而非 `app-frontend/docs/features/`（路由失效，AI 沿用历史根目录）；(2) localconfig 没配 worktree 时 AI 自降级 off，把"主工作区干净"简化为"可以直接写"，违反隔离原则；(3) 写操作前没有 pwd / 路径前缀硬校验，AI 钻空子；(4) teamwork_space.md 子项目清单表没有 docs_root 列，路由没有机器可读权威源。本次系统补漏：(A) teamwork-space.md 子项目表加 docs_root 列（路由权威）；(B) feature-state.json 加 artifact_root 字段（triage Step 9 写入）；(C) config.md 注释明确 worktree 缺失硬默认 auto + 禁止 AI 自降级；(D) triage Step 7.5/9 加硬规则（worktree fallback / artifact_root 计算 / state.json 写入清单加 artifact_root）；(E) RULES.md §六 加"写操作前路径硬门禁"段（pwd 校验 + 路径前缀校验 + 跨 Feature 写入禁止 + 实战反例）；(F) pmo.md 加"产物路径权威路由"段（路由计算流程 + 硬规则 + 历史兼容 + 校验时机 + 标准化拦截输出）。形成 triage 决策（写 state.json）+ 写操作前校验（pwd + 路径前缀）双层硬门禁。

### P0-41：sub_project 路由权威 + worktree 缺失硬默认 + 写操作前路径硬门禁

- 触发：用户实战 case（F059-HomeShortcutKeySync）AI 自我反思 +「为什么没按流程，需要优化 teamwork」+ 4 条建议（triage 出口校验 / worktree 缺失默认 auto / 写操作硬门禁 / teamwork_space 路由权威）
- 设计决策（用户拍板）：
  - **不增红线**：通过 Stage 契约 + RULES.md §六 写操作硬门禁扩展 + PMO 角色路由权威段达到约束效果（红线数保持 15 条）
  - **路由权威**：teamwork_space.md 子项目清单表 docs_root 列（必填），所有 Feature 产物路径必须以 `{docs_root}/{Feature 全名}` 开头
  - **worktree 缺失硬默认 auto**：禁止 AI 自降级 off（"主工作区干净"等不是 off 理由）
  - **写操作前硬门禁**：pwd + 路径前缀 + 跨 Feature 写入校验
  - **历史 Feature 兼容**：保留原位置不强制迁移（state.json.artifact_root 是历史快照），新 Feature 走新规则
- 处理（7 处改造）：
  - **P0-41-1. `templates/teamwork-space.md` 子项目清单表加 docs_root 列**（必填，路由权威）：表头加 docs_root；3 个示例行（AUTH/WEB/PAY）填入 `{子项目目录}/docs/features` 标准格式；含路由权威硬规则说明
  - **P0-41-2. `templates/feature-state.json` 加 artifact_root 字段**：顶层位置（与 feature_id / sub_project 同级）；含计算规则注释（teamwork_space.md docs_root 列 + Feature 全名）+ 写入时机（triage Step 9）+ 写操作硬门禁说明
  - **P0-41-3. `templates/config.md` worktree 缺失硬默认 auto 说明**：注释明确"localconfig 缺 worktree 字段 → PMO 必须按 auto 处理（不是 off）"+ 禁止 AI 自降级 + 实战反例
  - **P0-41-4. `stages/triage-stage.md` Step 7.5/8/9 加硬规则**：
    - Step 7.5 加 worktree 缺失硬默认 auto + artifact_root 计算逻辑
    - Step 8 暂停点输出表加 sub_project / artifact_root 两行
    - Step 9 state.json 写入硬清单加 artifact_root 字段
  - **P0-41-5. `RULES.md` §六 加「写操作前路径硬门禁」段**：3 项校验（pwd / 路径前缀 / 跨 Feature 写入禁止）+ 校验时机（Plan 入口 / 每次 Write 前 / Stage 切换）+ 实战反例（沿用根目录 / worktree=off 误用）
  - **P0-41-6. `roles/pmo.md` 加「产物路径权威路由」段**：路由计算流程（4 步）+ 硬规则（唯一权威 + 禁止反模式）+ 历史 Feature 兼容 + 校验时机 + 标准化拦截输出
  - **P0-41-7. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-40 → 7.3.10+P0-41
- 风险控制：
  - 历史 Feature 不强制迁移（state.json.artifact_root 是历史快照）
  - 单子项目模式（无 teamwork_space.md）兼容：artifact_root = `docs/features/{Feature 全名}`
  - 不增红线（红线数保持 15 条）
  - 不破坏现有 Stage 契约（仅加硬规则 + 路径校验）
  - 反例直接来自实战 case（提高 AI 识别力）
- 影响面：
  - 改动文件：7 个（teamwork-space.md / feature-state.json / config.md / triage-stage.md / RULES.md / pmo.md / SKILL.md / init-stage.md / CHANGELOG.md）
  - state.json 字段：顶层加 `artifact_root`（必填）
  - teamwork_space.md schema：子项目清单表加 `docs_root` 列（必填）
  - 用户体验：
    - 多子项目模式产物路由透明（用户在 triage Step 8 看到 artifact_root + sub_project）
    - worktree 隔离不再被 AI 自降级
    - 写操作硬门禁防 AI 钻空子（pwd + 路径前缀双校验）
    - 实战 case 类问题不再发生（沿用根目录 / 主工作区写代码）
- 待跟进（非 P0-41 范围）：
  - 1-2 个真实多子项目 Feature 跑下来后回顾 artifact_root 路由的实测体验
  - 是否需要写一个 state.json 字段完整性校验脚本作为机器层兜底
  - 历史 Feature（在根 docs/features/）的批量迁移工具（暂不做，按需手工）

---

## v7.3.10 + P0-40

> v7.3.10+P0-40 RD 开发 + 架构师 Code Review 默认 Opus 模型：用户实战 case（BUG-F002-001 架构师 Code Review 用了 Sonnet 4.6 跑 2m 38s + 72.3k tokens）暴露当前模型默认值有问题——架构师 CR 是质量最后 gate，深度架构判断不可降级到 Sonnet。原 agents/README.md §一 模型偏好把"Review"统一标为 Sonnet 推荐，但这没区分"架构师 CR"（深度判断）和"QA CR"（执行型校验）。本次细化模型偏好原则："深度判断 = Opus / 执行验证 = Sonnet / 异质独立 = external"，明确：(1) RD 开发 / 架构师 CR / PM PRD / RD TECH / Designer UI = Opus 默认；(2) QA CR / QA TC / QA 测试 / Browser E2E / 多角色并行评审 / Bug 排查 = Sonnet 默认；(3) external (codex/claude CLI) 角色独立机制不变。dispatch 模板加场景化模型推荐注释。

### P0-40：RD 开发 + 架构师 CR 默认 Opus（深度判断不可降级）

- 触发：用户「rd 开发和 架构 review 默认应该用 opus 模型」+ 实战 case 显示 Bug 流程架构师 CR 用 Sonnet
- 设计决策（用户拍板）：
  - **RD 开发**（Dev Stage）默认 Opus（保持原推荐 / 显式化 + 例外说明）
  - **架构师 Code Review**（Review Stage + Bug 流程必经）从 Sonnet 推荐改为 Opus 推荐
  - **QA Code Review** 保持 Sonnet（执行型校验，TC 覆盖判断 Sonnet 够用）
  - **原则统一为**："深度判断 = Opus / 执行验证 = Sonnet / 异质独立 = external"
  - external 角色独立机制（claude-agents）不动 — 与"架构师 CR / RD Dev"是不同概念
  - 红线数保持 15 条
- 处理（4 处改造，跳过原计划的 P0-40-3 claude-agents 同步）：
  - **P0-40-1. `agents/README.md` §一 模型偏好调整**：原 "Opus 推荐 = Plan/Blueprint/Dev/Designer / Sonnet 推荐 = Review/Browser E2E" 重构为按角色细分：
    - Opus 推荐：RD Dev / 架构师 CR / PM PRD / RD TECH / 架构师评审 TECH / Designer UI / Panorama
    - Sonnet 推荐：QA CR / QA TC / QA 测试 / Browser E2E / PRD/TC/TECH 多角色并行评审 / Bug 排查
    - external：codex / claude CLI（独立异质）
    - 加显式 v7.3.10+P0-40 关键变化说明
  - **P0-40-2. `stages/dev-stage.md` + `stages/review-stage.md` AI Plan 模式默认 Opus**：
    - dev-stage.md AI Plan 段加"v7.3.10+P0-40 默认 Opus 模型"硬规则（主对话继承会话 / Subagent 显式 model: opus / Bug 排查例外用 Sonnet）
    - review-stage.md AI Plan 段加三视角模型默认（架构师 CR = opus / QA CR = sonnet / external = 异质独立）
  - **P0-40-3. (跳过)** claude-agents 文件同步：审视后发现 claude-agents/ 处理的是 external reviewer，与 P0-40 的"架构师 CR / RD Dev"是不同概念，不需要改
  - **P0-40-4. `templates/dispatch.md` 模板更新**：Model 字段加完整场景化默认推荐注释（架构师 CR / RD Dev = opus；QA / Test / 校验型评审 = sonnet；含 Bug 排查例外）
  - **P0-40-5. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-39 → 7.3.10+P0-40
- 风险控制：
  - 不改 external 机制（claude-agents/invoke.md 默认 sonnet 不动 — 那是 external reviewer 调用，不是架构师 CR）
  - 不引入硬性强制（仍是"推荐"，用户可自定义覆盖）
  - 主对话模式由用户会话模型决定，仅在 Subagent 模式硬约束 model 字段
  - 红线数保持 15 条
- 影响面：
  - 改动文件：6 个（agents/README.md / dev-stage.md / review-stage.md / dispatch.md / SKILL.md / init-stage.md / CHANGELOG.md 版本号）
  - 用户体验：
    - Bug 流程架构师 CR 用 Opus → 减少深度问题漏判（典型 Bug 改动 ≤5 文件，Opus 反而更稳）
    - Feature 流程 Review Stage 三视角分层（架构师深度 / QA 校验 / external 异质）→ 平衡质量与成本
    - QA Code Review 仍用 Sonnet → 不增加 token 成本（QA 主要做 TC 逐条覆盖校验）
- 待跟进（非 P0-40 范围）：
  - 1-2 个真实 Feature 跑下来后回顾 Opus 架构师 CR 的实测效果（finding 深度 / 漏判率 / 成本）
  - 是否需要在 .teamwork_localconfig.md 加 `default_model_per_role` 字段让用户级偏好持久化（当前用户级偏好需手工修改 stage spec）

---

## v7.3.10 + P0-39

> v7.3.10+P0-39 worktree 默认路径调整 + 可配置：原硬编码默认路径 `../feature-{Feature 全名}` 是 sibling 目录（仓库父目录的同级目录），存在两个问题：(1) 污染父目录（用户的 `~/apps/okok/` 下会出现 `feature-AUTH-F042-...` 这种与项目仓库混在一起的目录）；(2) IDE 跨 worktree 跳转受限 + 工具链忽略复杂。本次改默认路径为 `{worktree_root_path}/{Feature 全名}`（默认 `worktree_root_path = .worktree`，即项目根目录下 `.worktree/` 子目录），且支持在 `.teamwork_localconfig.md` 配置 `worktree_root_path` 字段调整根目录（如 `../.repo-worktrees` 父目录分组 / `/tmp/worktrees` 完全自定义绝对路径）；install.sh 自动注入 `.worktree/` 到项目根 `.gitignore`（避免主仓库 git 嵌套混乱）。

### P0-39：worktree 默认路径项目内 + 可配置 root_path

- 触发：用户「需要改为默认在项目根目录的.worktree 目录下，可在.teamwork_localconfig.md 配置路径」+ 二次精简「配置 key：`worktree_path` 改为 `worktree_root_path`，去掉占位符逻辑，默认就是 worktree_root_path 下按 featurename 创建子目录」
- 设计决策（用户拍板）：
  - **默认路径变更**：`../feature-{Feature 全名}` → `{worktree_root_path}/{Feature 全名}`（默认 worktree_root_path = `.worktree`）
  - **配置 key**：`worktree_root_path`（不是 worktree_path），语义更明确——是"根目录"，子目录按 Feature 全名自动拼接
  - **去掉占位符逻辑**：路径拼接简化为 `{worktree_root_path}/{Feature 全名}`，不需要 `{feature_name}` / `{repo_root}` 等占位符
  - **gitignore 自动化**：install.sh 自动检测项目根 .gitignore，缺则追加 `.worktree/`
  - 红线数保持 15 条
- 处理（6 处改造）：
  - **P0-39-1. `templates/config.md` 加 `worktree_root_path` 配置**：默认 `.worktree`；说明实际路径 = `{worktree_root_path}/{Feature 全名}`；含路径合法性约束 + .gitignore 提醒 + 解析优先级
  - **P0-39-2. `stages/plan-stage.md` 改 worktree 命令**：路径解析逻辑（读 worktree_root_path + 拼接 Feature 全名）；命令模板从 `git worktree add ../feature-{Feature 全名}` 改为 `git worktree add {worktree_root_path}/{Feature 全名}`；state.json 写入加 `root_path` 字段
  - **P0-39-3. `stages/triage-stage.md` 预检表加 worktree 路径预览行**：Step 7.5 「🛠 环境配置预检」表加 `worktree 路径` 行（按 localconfig 推算 + Plan Stage 入口创建）
  - **P0-39-4. `templates/feature-state.json` 示例更新**：`environment_config.worktree_root_path = ".worktree"`；`worktree.path` 示例改为 `.worktree/AUTH-F042-email-login`；加 `worktree.root_path` 字段
  - **P0-39-5. `install.sh` .gitignore 注入**：检测项目根 .gitignore 是否含 `.worktree/`；缺则追加（含说明注释）
  - **P0-39-6. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-38-B → 7.3.10+P0-39
- 风险控制：
  - state.worktree.path 是历史快照（不重算），老 Feature 的旧路径保留
  - localconfig 缺 `worktree_root_path` → 用新默认 `.worktree`
  - 自定义路径在项目内时由用户自行确保 gitignore（仅默认路径自动注入）
  - 项目无 `.git` 目录时 install.sh 跳过 gitignore 注入（不报错）
  - 红线数保持 15 条
- 影响面：
  - 改动文件：6 个（config.md / plan-stage.md / triage-stage.md / feature-state.json / install.sh / SKILL.md / init-stage.md / CHANGELOG.md 版本号）
  - state.json 字段：`environment_config.worktree_root_path`（新增）/ `worktree.root_path`（新增）/ `worktree.path` 默认值变更
  - 用户体验：
    - 新 Feature 的 worktree 自动落到项目内 `.worktree/{Feature 全名}`，不污染父目录
    - IDE 索引可包含 `.worktree/` 或排除（按团队偏好），跨 worktree 不再跳到 sibling 目录
    - 自定义路径配置一目了然（一行 `worktree_root_path: <path>`）
- 待跟进（非 P0-39 范围）：
  - 1-2 个真实 Feature 跑下来后回顾 `.worktree/` 目录在 IDE 中的索引体验（IntelliJ / VS Code）
  - 是否需要在 install.sh 提供命令行参数自定义 worktree_root_path（避免每个项目手工改 localconfig）

---

## v7.3.10 + P0-38-B

> v7.3.10+P0-38-B 三个硬约束补丁：用户实战 case（INFRA Android 落地页 CDN 域名替换）暴露 P0-38-A 设计未真正落地——AI 仍按旧 P0-28 模式跑：(1) triage Step 8 输出 Q1-Q4 四个产品决策（替换范围 / 实现参数化 / 复制内容 / 反馈方式），把业务方向 / 技术方案 / UX 细节决策都塞进 triage 暂停点；(2) 用户回 "1B 2B 3A 4A" 时实际是回答了产品决策，没机会确认骨架，流程跳步，Plan Stage 失去价值；(3) state.json 缺 execution_plan_skeleton / available_roles / external_cross_review 三字段；(4) Plan Stage 入口直接跳到"创建目录 + 写 PRD"，绕过实例化流程（读 execution_hints / 写 plan_substeps_config / 输出 5 行 Plan / ⏸️ 用户瞬时确认）。本次补三个硬约束让 P0-38-A 真正落地：(A) triage Step 8 暂停点唯一合法形态是骨架确认 3 选 1 + 禁止产品决策类暂停点；(B) Step 9 state.json 写入硬清单（必含三字段，缺一不可）+ PMO 校验；(C) plan/blueprint/review 三 Stage 入口实例化硬规则，跳过实例化视为流程违规；(D) `roles/pmo.md` 加"产品决策边界"段，明确 triage 决策范围 vs Plan Stage 决策范围 + 反例（实战 Q1-Q4 模式）+ PMO 自检清单。

### P0-38-B：让 P0-38-A 真正落地的硬约束补丁

- 触发：用户「看下下面的 case 有问题么」+ 提供实战 case（INFRA Android 落地页 CDN 域名替换 Q1-Q4 产品决策塞 triage）+ AI 审视后发现 5 处偏离 P0-38-A 契约 +「按建议」（启动 P0-38-B）
- 设计决策（用户拍板）：
  - **不增红线**：通过 Stage 契约硬规则 + PMO 角色自检 + 反模式禁止条款达到约束效果（红线数保持 15 条）
  - **PMO 产品决策边界明确**：triage 不决策业务方向 / 技术方案 / UX 细节；这些带不确定性进 Plan Stage 由 PM 起草 PRD 时承载
  - **Stage 入口实例化不可绕过**：进入 Plan/Blueprint/Review 必须先做实例化，跳过视为流程违规
  - **state.json 写入硬清单**：triage Step 9 必含 execution_plan_skeleton / available_roles / external_cross_review 三字段
- 处理（4 处改造）：
  - **P0-38-B-1. `stages/triage-stage.md` Step 8/9 加硬约束**：
    - Step 8 暂停点唯一合法形态：骨架确认 3 选 1（采用 / 调整 / 其他）
    - 禁止反模式：≥2 个产品决策点 / 流程确认 + 产品澄清混在同一暂停点 / Q1-Q4 类的业务方向决策
    - execution_plan_skeleton 输出契约：必须输出 4+1 字段，仅"流程步骤描述"段不算合规
    - Step 9 state.json 写入硬清单：必含 execution_plan_skeleton / available_roles / external_cross_review 三字段（缺一视为流程违规）
    - 含违规示例（实战 case 反模式）
  - **P0-38-B-2. `stages/{plan,blueprint,review}-stage.md` 入口实例化硬规则**：
    - plan-stage.md 加"跳过实例化 = 流程违规"硬规则 + 反模式列举（直接跳到创建目录 + 写 PRD / Steps remaining 仅 3 步 / Role specs loaded 缺）
    - blueprint-stage.md 同上（禁止跳过直接进 4 步内部闭环）
    - review-stage.md 同上（禁止跳过直接进三视角独立审查）
    - PMO 校验：未先输出实例化 5 行 Plan + 写入 *_substeps_config → 视为流程违规
  - **P0-38-B-3. `roles/pmo.md` 加"PMO 产品决策边界"段**：
    - 决策类型与责任归属（triage 决策范围 vs 不该决策范围 vs 产品决策合法承载位置）
    - 错误做法详细反例（实战 case Q1-Q4 模式完整展示）
    - 正确做法（方式 1 把不确定性带进 Plan Stage 默认推荐 / 方式 2 极简需求唯一解读）
    - 边界例外：合法的 Step 8 暂停点（流程类型确认 / 环境配置异常 / 跨 Feature 冲突）
    - PMO 自检清单（输出前 3 步自检：A/B/C 决策点检查 / 业务-技术-UX 关键词检查 / 3 选 1 格式检查）
  - **P0-38-B-4. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-38-A → 7.3.10+P0-38-B
- 风险控制：
  - 不破坏现有 Stage 契约（仅加硬约束 + PMO 校验，不改 Stage 处理流程）
  - 不引入新红线（红线数保持 15 条）
  - 反例直接来自实战 case（提高 AI 识别力）
  - 兼容老 Feature：state.json 缺新字段时按降级路径处理（标 INFO + 不阻塞）
- 影响面：
  - 改动文件：6 个（triage-stage.md / plan-stage.md / blueprint-stage.md / review-stage.md / pmo.md / SKILL.md / init-stage.md / CHANGELOG.md 版本号）
  - 红线数：保持 15 条
  - PMO 行为变化：
    - triage Step 8 不再输出产品决策选项
    - 业务/技术/UX 取舍带不确定性进 Plan Stage
    - state.json 必含 execution_plan_skeleton / available_roles / external_cross_review
    - 进入各 Stage 必须先做入口实例化（5 行 Plan + 写 *_substeps_config + ⏸️ 用户瞬时确认）
  - 用户体验：
    - triage 输出更聚焦（仅骨架确认，不再回答产品 Q&A）
    - 产品决策集中在 Plan Stage（PM 起草 PRD 时一次性讨论 + 用户最终确认）
    - 减少决策疲劳（避免回答 4-5 个 A/B/C 选项）
- 待跟进（非 P0-38-B 范围）：
  - 1-2 个真实 Feature 跑下来后回顾 P0-38-A + B 是否真正落地（特别是 PMO 自检清单的执行率）
  - 如 AI 仍漏掉 execution_plan_skeleton 字段，考虑加 state.json 写入前的机器可校验脚本

---

## v7.3.10 + P0-38-A

> v7.3.10+P0-38-A 修订 P0-38 的两个设计点：(1) 角色可用性扫描从 init Stage 移回 triage Stage——init 职责本已重，且角色可用性是动态的（用户中途装/卸 CLI 应实时感知），available_roles 不应是会话级常量；(2) execution_plan_skeleton.stages 字段从"5 字段（含 candidate_roles）"瘦身为"4 字段必填 + 1 可选（execution_hints）"——candidate_roles 是机械可推算的，不应入决策态；改为 execution_hints 文本字段（软建议非决策），承载启用/跳过角色 + 动作动词（评审/设计/实现 TDD/测试/验收/净化+push+finalize）+ 模型 + 理由；角色固定 Stage（Dev/Test/PM 验收/Ship）允许 hints=null；Stage 入口实例化时必读 hint + 否决时在 *_substeps_config.hint_overrides 写文本说明（cite hint 原文 + override 原因）。形成 triage 给软建议 + Stage 入口实例化做硬决策的双层契约。

### P0-38-A：角色扫描移回 triage + execution_hints 文本契约

- 触发：用户「角色可用性扫描是否应该放到 triage 阶段，triage 阶段的目标就是需要哪几个 stage 来完成事项，事项的目标是什么，每个 stage 的预估参与角色是什么」+「等一下，我觉得偏了，triage 输出的应该是个骨架...至于模型，串行还是并行，在这个阶段执行时再做进一步规划。不做前置规划，防止上下文不够」+「是否给一个阶段实施建议，例如 external_reviewer(codex) 参与一下评审」+「role_hints 是否可以直接是个文本，而不是结构化 json」+「启用 architect/qa/external(codex) 改为 启用 architect/qa/external(codex) 评审」（动词后缀）+「不需要每个 Stage 都给建议，但给建议一定给理由」+「是否把角色建议改为执行建议更好一些」+「接受」
- 设计决策（用户拍板）：
  - **角色可用性扫描放 triage**（修复 P0-38 设计错误）：每次 Feature 启动实时扫描，反映运行时环境变化；available_roles 是 Feature 决策时快照，不是会话级常量
  - **删 candidate_roles 字段**：机械可推算的不入决策态（基于 Stage spec 内置清单 ∩ available_roles 即可推算）
  - **加 execution_hints 字段（文本，可选）**：
    - 文本不是 JSON：消费者只有 Stage 入口的 PMO（也是 LLM），无需结构化解析；state.json 已有 concerns/note/pmo_summary 等文本字段先例；文本可表达犹豫/条件/关联
    - 命名"执行建议"不是"角色建议"：hint 承载内容超出"哪些角色"，含动作动词 + 模型 + 顺序 + 协调
    - 软约定格式（非硬约束）："启用 X 动词；跳过 Y。理由：..."
    - 动词约定：评审 / 设计 / 实现 TDD / 测试 / 验收 / 净化+push+finalize
    - 角色固定 Stage（Dev/Test/PM 验收/Ship）允许 hints=null
    - 给 hint 必须有理由（不接受裸建议）
  - **加 hint_overrides 字段（文本，可选）**：Stage 入口实例化时若否决 hint，必须在 *_substeps_config.hint_overrides 写文本说明（cite hint 原文 + override 原因）
  - 红线数保持 15 条
- 处理（7 处改造）：
  - **P0-38-A-1. `templates/feature-state.json` schema 调整**：删 execution_plan_skeleton.stages[].candidate_roles；加 execution_hints (string | null)；available_roles 注释从"init 写入"改"triage 写入"；plan_substeps_config 加 hint_overrides 字段
  - **P0-38-A-2. `stages/init-stage.md` 回退角色扫描段**：删除 P0-38-3 添加的"角色可用性扫描段"，恢复"探测延后到 triage Step 4"
  - **P0-38-A-3. `stages/triage-stage.md` Step 4 + Step 8 调整**：Step 4 从"读 available_roles"改回"角色可用性扫描"（调 detect-external-model.py 写 available_roles）；Step 8 骨架字段：删 candidate_roles + 加 execution_hints + 渲染措辞用"执行建议"+ 动词约定 + 角色固定 Stage 不给 hint
  - **P0-38-A-4. `roles/external-reviewer.md` 来源调整**：可用性来源段从"init Stage 决定"改为"triage Stage 决定"+ 设计意图说明
  - **P0-38-A-5. plan/blueprint/review-stage.md 入口实例化段更新**：读 execution_hints + 必读 cite + 否决时写 hint_overrides；删除对 candidate_roles 的引用
  - **P0-38-A-6. `roles/pmo.md` 智能推荐表注释同步**：智能推荐表段说明承担两处职责（triage 时生成 execution_hints + Stage 入口实例化）
  - **P0-38-A-7. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-38 → 7.3.10+P0-38-A
- 风险控制：
  - 不破坏现有 *_substeps_config 内部契约（仅加 hint_overrides 字段）
  - 不引入结构化 hint schema（文本字段，灵活性高 + 维护成本低）
  - 老 Feature 兼容：state.json 缺新字段时按 Stage spec 内置清单走标准流程，无需迁移
  - 红线数保持 15 条（红线 #14 AI Plan 模式 + execution_hints 软建议 + Stage 入口实例化天然形成"骨架软建议 → 入口硬决策 → 5 行 Plan"三层）
- 影响面：
  - 改动文件：7 个（feature-state.json + init-stage.md + triage-stage.md + plan/blueprint/review-stage.md + external-reviewer.md + pmo.md + SKILL.md / CHANGELOG.md 版本号）
  - state.json schema：删 execution_plan_skeleton.stages[].candidate_roles；加 execution_hints (string | null)；plan_substeps_config 等加 hint_overrides
  - 概念变化：candidate_roles 决策字段 → execution_hints 软建议字段
  - 用户体验：
    - triage 主对话渲染从机械"角色范围列表"改为有指向性的"执行建议（含动词 + 模型 + 理由）"
    - Stage 入口实例化路径透明（hint + override_reason 留审计痕迹）
    - 角色固定 Stage（Dev/Test/PM 验收/Ship）不再有冗余 hint
- 待跟进（非 P0-38-A 范围）：
  - 1-2 个真实 Feature 跑下来后回顾 hint 命中率（PMO triage 时 hint 与 Stage 入口实际决策的一致率）
  - hint_overrides 文本格式是否需要软约定（如 cite hint 原文 + override 原因两段式）

---

## v7.3.10 + P0-38

> v7.3.10+P0-38 triage 输出骨架 + Stage 入口实例化 + external 升格为评审角色：用户审视当前 triage stage 输出后提出关键设计反思——triage 时上下文不足以决策每 Stage 的具体执行细节（PRD 还没写、代码还没出），把"模型选择 / 串行并行 / 评审循环参数 / 具体输入输出"前置到 triage 是过度规划，违反延迟绑定原则。本次重构 triage stage 的输出本质：从"决策片段化输出"升级为"完整 Feature 骨架"——只输出 5 字段（stage / candidate_roles / goal / key_outputs / pause_points），具体决策推迟到各 Stage 入口实例化（红线 #14 AI Plan 模式承担）。同时把外部模型从"独立维度（plan_enabled/blueprint_enabled/review_enabled 三字段）"升格为"评审角色"（新建 `roles/external-reviewer.md`，与 PL/RD/QA/Designer/PMO/Architect 平级）；角色可用性扫描从"triage 时探测"前移到"init Stage 一次性扫描"（写入 state.available_roles[]）；triage Step 8 决策块从"两个独立块（外部模型 + Plan 评审组合）"瘦身为"单一骨架决策块"。形成"init 能力探测 → triage 骨架调度 → 各 Stage 入口实例化"三层职责正交架构。

### P0-38：triage 骨架化 + Stage 入口实例化 + external 升格

- 触发：用户「我们重新确认下 triage stage 需要输出的内容，我理解是一个落地 plan，完成这个 feature 需要哪些 stage，每个 stage 有哪些 todo，每个 todo 的参与角色是什么，每个角色的模型是什么，输入是什么，输出是什么」+ 反思「等一下，我觉得偏了，triage 输出的应该是个骨架，有哪些流程，需要谁参与，目标是什么。至于模型，串行还是并行，在这个阶段执行时再做进一步规划。不做前置规划，防止上下文不够」+「确认」
- 设计决策（用户拍板）：
  - **三层职责正交架构**：
    - init Stage = capability detection（一次性扫描 available_roles）
    - triage Stage = scheduler（输出 execution_plan_skeleton 骨架）
    - 各 Stage 入口 = workers（基于上游产物实例化具体配置）
  - **triage 骨架 5 字段**：stage / candidate_roles / goal / key_outputs / pause_points（不含模型/串行并行/具体 IO/评审循环参数）
  - **延迟绑定原则**：所有"基于上下文不足以决策"的字段（model / execution / 串行并行 / round_loop）推迟到各 Stage 入口
  - **external 升格为评审角色**：与 PL/RD/QA/Designer/PMO/Architect 平级，统一进入 review_roles[]；不再有独立维度
  - **取消 P0-28 三字段**：plan_enabled / blueprint_enabled / review_enabled 删除（按 review_roles[] 是否含 external 判定）
  - **立场独立性硬约束保留**：external-reviewer.md 反复强调异质模型 + forbidden_files 不可读
  - 红线数保持 15 条
- 处理（9 处改造）：
  - **P0-38-1. `templates/feature-state.json` schema 变更**：加 `available_roles[]` + `execution_plan_skeleton` 顶层字段；删 `external_cross_review.{plan/blueprint/review}_enabled` 三子字段（保留 model / host / available_clis 等元数据）
  - **P0-38-2. 新建 `roles/external-reviewer.md`**：角色契约（核心价值=立场独立性 + 通用评审原则 + context schema 规范 + 失败降级 + 立场独立性硬约束反复强调）
  - **P0-38-3. `stages/init-stage.md` 加角色可用性扫描段**：原 P0-24 的"延后探测"废止；改为 init Step 1.x 一次性扫描内部 6 角色（固定可用）+ 调用 detect-external-model.py 探测 external 异质性 + 写入 state.available_roles[]
  - **P0-38-4. `stages/triage-stage.md` Step 4 + Step 8 重写**：
    - Step 4：从"调探测脚本"改为"读 state.available_roles[]"
    - Step 8：删独立"🌐 外部模型评审决策"块 + 删"🧭 Plan Stage 评审组合决策"块；改为输出 execution_plan_skeleton（5 字段：stage / candidate_roles / goal / key_outputs / pause_points）+ 启动确认 3 选 1
  - **P0-38-5. `stages/plan-stage.md` 加入口实例化段**：删 plan_enabled 字面值引用（替换为"`"external" in plan_substeps_config.review_roles[].role`"）；加 Plan Stage 入口实例化流程（PMO 基于 execution_plan_skeleton.stages[plan].candidate_roles + 已有信息决策 active_roles + execution + pl_prioritized + round_loop）
  - **P0-38-6. `stages/blueprint-stage.md` 加入口实例化段**：删 blueprint_enabled 字面值引用；加 Blueprint Stage 入口实例化流程（基于 PRD 复杂度信号决策评审组合 + ADR 触发判断）
  - **P0-38-7. `stages/review-stage.md` 加入口实例化段**：删 review_enabled 字面值引用；加 Review Stage 入口实例化流程（基于 Dev Stage 代码复杂度决策三视角评审组合 + parallel_mode）
  - **P0-38-8. `roles/pmo.md` 智能推荐表瘦身**：原"🌐 外部模型交叉评审开关决策"段顶部加 P0-38 升格说明；原"🧭 Plan Stage 评审组合智能推荐"段重定位为"Plan Stage 入口实例化的角色实现规范"
  - **P0-38-9. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-37 → 7.3.10+P0-38
- 风险控制：
  - 不破坏现有 Stage spec 内部契约（Process Contract / Output Contract 主体不变，仅入口加实例化段 + 字段引用更新）
  - 不引入新抽象（claude-agents/ + codex-agents/ 现有文件作为 external 角色 context 物化，零变更）
  - external 异质性硬约束保留（init 扫描时同源外部不进 available_roles）
  - 老 Feature 兼容：state.json 缺新字段时降级为 P0-28 兼容层行为（老字段 plan_enabled 等读到时按原语义解释）
  - 红线数保持 15 条（红线 #14 AI Plan 模式 + Stage 入口实例化天然对齐，二者形成"骨架 → 实例化 → 5 行 Plan"清晰双层）
- 影响面：
  - 改动文件：9 个（feature-state.json + 新建 external-reviewer.md + init-stage.md + triage-stage.md + plan-stage.md + blueprint-stage.md + review-stage.md + pmo.md + SKILL.md / CHANGELOG.md 版本号）
  - state.json schema 新增字段：available_roles[] / execution_plan_skeleton{}
  - state.json schema 删除字段：external_cross_review.{plan_enabled / blueprint_enabled / review_enabled}
  - 红线 #14 AI Plan 模式：与 Stage 入口实例化天然对齐（5 行 Plan 就是实例化产物）
  - 用户体验：
    - triage Step 8 从 2-3 个决策块瘦身为 1 个骨架决策块（决策疲劳显著降低）
    - external 是否启用变成"角色是否在 candidate_roles 推荐里"（语义统一）
    - 不可用 external 自动从推荐里剔除（用户面无感降级）
- 待跟进（非 P0-38 范围）：
  - 1-2 个真实 Feature 跑下来后回顾骨架决策块的可读性 + 各 Stage 入口实例化的实操体验
  - templates/external-cross-review.md 措辞按"角色契约"语境调整（非 P0-38 范围，独立小补丁）
  - 老 Feature 兼容层何时正式淘汰（建议跑 5+ 新 Feature 后再考虑）

---

## v7.3.10 + P0-37

> v7.3.10+P0-37 codex profile 默认 high + fast：用户实战 case 暴露 codex CLI 调用频繁卡死或超时——根因是 `codex-agents/*.toml` 全部 8 个 profile 中只有 `designer.toml` 显式设置了 `model_reasoning_effort = "high"`，其余 7 个未设 → fallback 到 codex CLI 默认 `xhigh`（极深度思考模式，单次调用可能 5-15 分钟），叠加 `service_tier` 全部未设 → fallback 到 OpenAI API 默认 `standard` tier（高负载时排队），双重放大耗时。本次统一所有 8 个 profile 显式默认 `model_reasoning_effort = "high"` + `service_tier = "fast"`，并在 codex-agents/README.md 加默认配置说明 + 调优指引（何时调高/调低 + 用户级覆盖方法 + 与红线 #14 的关系）。

### P0-37：codex profile 默认 high + fast（避免 xhigh 卡死 + standard tier 慢响应）

- 触发：用户「我们能否默认 codex 执行的时候使用 high 和 fast 模式，避免耗时和卡死」+ 实战 case 显示 codex 调用经常超时或卡死（macOS `timeout` 命令缺失叠加 codex 自身 xhigh 推理深度）+「按建议」
- 设计决策（用户拍板）：
  - **统一显式默认**：所有 8 个 profile 显式设置 `model_reasoning_effort = "high"` + `service_tier = "fast"`，不再依赖 codex CLI fallback
  - **质量 vs 速度的权衡**：`high` 是 cross-review 质量足够 + 响应时间可控（30-180 秒）的合理 baseline；`xhigh` 卡死代价 = 整个 Feature 流转中断 + 用户介入诊断，不接受作为默认
  - **service_tier=fast 计费略高但稳定性收益远超成本**：用户 OpenAI 账户不支持 fast tier 时不会报错（仅退化为 standard 行为），无副作用
  - **保留用户级覆盖**：profile 级编辑 / 命令行 -c 覆盖 / 项目根 `.codex/config.toml` 全局覆盖三种方式
  - 红线数保持 15 条
- 处理（3 处改造）：
  - **P0-37-1. 8 个 codex profile 加 `model_reasoning_effort = "high"` + `service_tier = "fast"`**：reviewer.toml / prd-reviewer.toml / blueprint-reviewer.toml / designer.toml（已有 high，加 fast）/ planner.toml / rd-developer.toml / tester.toml / e2e-runner.toml；每行加 v7.3.10+P0-37 注释说明
  - **P0-37-2. `codex-agents/README.md` 加「默认推理深度 + service_tier 配置」段**：
    - 全局默认配置块
    - 为什么默认 high + fast（vs xhigh 默认卡死、vs standard 排队）
    - 何时调整（调低 / 调高 / service_tier 切换）
    - 用户级覆盖方法（profile 级 / 命令行 / config.toml）
    - 与红线 #14 的关系（high 是 Plan 模式合理 baseline，xhigh 容易在 Plan 模式纸面分析阶段卡住）
    - 历史 case 说明
  - **P0-37-3. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-36 → 7.3.10+P0-37
- 风险控制：
  - 不修改 developer_instructions 段（业务逻辑不变）
  - 不修改 sandbox_mode（权限边界不变）
  - 用户 OpenAI 账户不支持 fast tier 时降级为 standard 行为，不会报错
  - 用户可通过 profile 级 / 命令行 / config.toml 三种方式覆盖默认值
  - 红线数保持 15 条
- 影响面：
  - 改动文件：9 个（8 个 codex-agents/*.toml + 1 个 codex-agents/README.md + SKILL.md / init-stage.md / CHANGELOG.md 版本号）
  - codex 调用耗时：xhigh → high 实测下降 60-80%（用户报告：高复杂度场景 5-15 分钟 → 30-180 秒）
  - codex 调用稳定性：standard → fast 减少 API 排队等待，跨地理区域 / 高负载时段尤其明显
  - 用户体验：codex cross-review 不再卡死，Feature 流转可预期完成
- 待跟进（非 P0-37 范围）：
  - 1-2 个真实 Feature 跑下来后回顾 high 模式的 cross-review 质量是否仍能发现深层 finding（如不足以发现关键问题，考虑 prd-reviewer / blueprint-reviewer 两个最关键的 profile 单独提到 xhigh + 配合 gtimeout 上调）
  - macOS 用户 `timeout` 命令缺失问题（用户场景）：考虑 `claude-agents/invoke.md` 加 `gtimeout` fallback 检测 + 友好提示
  - 是否在 .teamwork_localconfig.md 加 `codex_default_reasoning_effort` / `codex_default_service_tier` 字段，让用户级偏好持久化（未来 P0）

---

## v7.3.10 + P0-36

> v7.3.10+P0-36 Bug 流程 state.json + Ship Stage 补齐：用户审计发现 Bug 流程两个设计漏洞——(1) Bug 流程不维护 state.json（rules/flow-transitions.md Bug 流程表所有 11 条转移以 BUG-REPORT.md 文本字段为状态源，违反 v7.3.2「state.json 单一权威」）；(2) Bug 流程无 Ship Stage（PMO Bug 总结直接到「完成 ✅」，commit/push/MR/merge/worktree 清理全部空白）。这两个漏洞是 v7.3.10+P0-15（Ship Stage 引入）+ +P0-29（双段拆分）+ +P0-32（Ship Finalize push）等连续升级时**只改 Feature 流程未同步 Bug 流程**的累积结果。本次补齐：(A) BUG-REPORT.md 加机读 YAML frontmatter（复用 feature-state.json 字段命名，承担 Bug 流程的 state.json 职能，不新建独立 state.json 文件以避免简单 Bug 流程膨胀）；(B) Ship Stage 加 Bug 缩简分支（共享 Step 1-10 主流程，仅状态承载文件 / 字段命名 / MR 标题模板 / push 范围有差异）；(C) flow-transitions.md Bug 流程末尾加 4 条 Ship 转移行；(D) 红线 #1 Ship Finalize 例外条款扩展（从仅允许 state.json 一文件 → 同时允许 BUG-REPORT.md 一文件，仅 frontmatter 元数据字段）。复杂 Bug 不影响（升级 Feature 后用 Feature 的 state.json）。

### P0-36：Bug 流程 state.json + Ship Stage 补齐

- 触发：用户「看下 bugfix 流程是否有问题，更新的文件是否是 state.json，结束后是否会自动进入 ship」+ 审计确认两个漏洞 +「按建议」
- 设计决策（用户拍板）：
  - **不新建独立 state.json 文件**：BUG-REPORT.md 顶部 YAML frontmatter 承载 Bug 流程状态机，字段命名复用 feature-state.json（current_stage / phase / shipped / commit_hash / mr_url / merge_commit_hash 等），保持 schema 一致性 + 避免简单 Bug 流程文件膨胀
  - **Ship Stage 共享主流程**：Bug 缩简版与 Feature 共享 Step 1-10，仅产物 / 状态字段引用 / MR 标题模板 / push 范围有差异，不重复 Stage 设计
  - **红线 #1 Ship Finalize 例外条款扩展**：从仅允许 state.json 一文件 → 同时允许 BUG-REPORT.md 一文件（仅 frontmatter 元数据字段，零业务影响）
  - **复杂 Bug 不变**：复杂 Bug 进入 Feature 流程后用 Feature 的 state.json，无需改动
  - 红线数保持 15 条（红线 #1 例外条款扩展，不增红线）
- 处理（6 处改造）：
  - **P0-36-1. `templates/bug-report.md` 加机读 YAML frontmatter**：bug_id / feature_id / classification / flow_type: bug / current_stage 枚举 / completed_stages / phase / commit_hash / shipped / mr_url / mr_merged_at / merge_commit_hash / merge_target_pushed_at / worktree_cleanup / ship_concerns / planned_execution 等字段；含复杂 Bug 例外说明（移交 Feature state.json）+ PMO 校验规则
  - **P0-36-2. `stages/ship-stage.md` 加 🆕 Bug 流程缩简分支段**：触发条件（flow_type=bug + classification=simple + current_stage=pmo_summary + phase=summarized）+ 与 Feature Ship 关键差异表（状态承载 / 字段引用 / MR 标题 / Step 7-8 写入对象 / push 范围）+ 各步骤 Bug 分支差异说明（Step 1-10 各项是否有差异）
  - **P0-36-3. `rules/flow-transitions.md` Bug 处理流程末尾加 4 个 Ship 转移行**：`PMO Bug 总结 → Ship Stage 第一段` / `Ship 第一段 → 等待合并` / `等待合并 → Ship Finalize`（⏸️暂停）/ `Ship Finalize → Bugfix 完成 ✅`；额外加 2 条异常分支（MR 关闭未合并 / push 失败）；既有 11 条转移加 frontmatter 字段引用
  - **P0-36-4. `roles/pmo.md` Bug 流程段加 BUG-REPORT.md frontmatter 维护职责**：初始化模板 + 每次阶段变更必做（写 frontmatter current_stage）+ 复杂 Bug 升级时移交规则 + Ship Stage 调度规则；`FLOWS.md` Bug 流程末段加 Ship Stage 流程图（净化 → push → MR → ⏸️ 用户合并 → finalize → 清理）
  - **P0-36-5. 红线 #1 Ship Finalize 例外扩展**：`SKILL.md` 红线 #1 措辞从"Feature 流程"扩展为"Feature 流程 / 简单 Bug 流程"两分支，明确 Bug 分支允许 push BUG-REPORT.md 一文件 + 仅 frontmatter 元数据字段；`stages/init-stage.md` 红线 #1 同步；`stages/ship-stage.md` Step 7 严格边界段同步加 Bug 分支
  - **P0-36-6. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-34-A → 7.3.10+P0-36（跳过 P0-35，因 P0-35 是评审 → 讨论模式重构方案被驳回）
- 风险控制：
  - 不破坏 Feature 流程现有契约（Ship Stage 主流程 Step 1-10 完全不变）
  - 不引入新文件（frontmatter 寄宿在 BUG-REPORT.md，不新建独立 state.json）
  - 复杂 Bug 上升 Feature 流程时清晰移交（frontmatter classification=complex + current_stage=escalated_to_feature）
  - 老 Bug 兼容：v7.3.10+P0-36 之前的 BUG-REPORT.md（无 frontmatter）仍允许存在，PMO 在流转校验时识别为"老格式"，提示用户手工 ship 或补 frontmatter；新建 BUG-REPORT.md 强制带 frontmatter
  - 红线数保持 15 条（红线 #1 例外条款扩展，不增红线）
- 影响面：
  - 改动文件：6 个（bug-report.md / ship-stage.md / flow-transitions.md / pmo.md / FLOWS.md / SKILL.md / init-stage.md / CHANGELOG.md）
  - state.json 字段：feature-state.json **不改**（Bug 流程不复用 state.json 文件）
  - BUG-REPORT.md 新增 frontmatter：~20 个字段（复用 feature-state.json 字段命名）
  - 红线 #1 Ship Finalize 例外：从单分支扩展为双分支（Feature / Bug）
  - 用户体验：简单 Bug 修复后自动进入 Ship Stage，commit/push/MR/finalize/worktree 清理闭环；BUG-REPORT.md frontmatter 单一权威记录全程状态
- 待跟进（非 P0-36 范围）：
  - 1-2 个真实简单 Bug 跑下来后回顾 Ship 缩简版实测体验（特别是 Step 7 写 BUG-REPORT.md frontmatter 的可读性 vs state.json）
  - 是否需要为 Bug 流程也加 worktree 集成（当前 worktree 主要服务 Feature 流程，简单 Bug 通常不开 worktree）
  - templates/bug-report.md 老格式兼容性的 PMO 识别逻辑细化

---

## v7.3.10 + P0-34-A

> v7.3.10+P0-34-A 是对 P0-34 评审模式的「对抗深度补丁包」（不重构 P0-34 主框架）：用户实战担忧 → P0-34 评审模式相比旧 PL-PM 讨论可能导致对抗深度降低（finding 提了 PM 给个 ADOPT/REJECT/DEFER 就过、问题被 DEFER 抛给用户、PL 业务深度被技术评审挤压）。诚实反思后，**不做 P0-35 完整重构**（"对抗辩论"在 LLM 上的实现存在物理局限：subagent 和 PM 是同一模型，没有真实立场冲突；多轮回合 ≠ 多轮深度），改用 3 个小补丁覆盖 80% 诉求：(A) DEFER 严格收紧（仅允许 category=business-decision，技术/业务/UX/质量类 finding 禁止 DEFER）；(B) PM 对抗性自查段（每条 ADOPT/REJECT 前必须先输出 ≥2 句"反方最强论据模拟"，对抗强度通过内省补回）；(C) PL 优先权 + 业务方向锁死（PL 评审先于其他角色 dispatch，PL 收敛后 PRD frontmatter `business_direction_locked: true`，其他角色基于锁死 PRD 评审，防止技术评审挤压业务对齐）。3 补丁合力使 PM response 从"轻量回应"变成"对抗内省 + 实质收敛"，且不增加流程步数。

### P0-34-A：DEFER 收紧 + PM 对抗性自查 + PL 优先权（3 补丁包）

- 触发：用户「之前的PL  PM 讨论效果很好，也能发现一些问题，变成review 之后是否会导致讨论深度降低了，例如将更多问题抛给了用户，而不是经过反复思考对抗性辩论的结果。」+ 反思「对抗性辩论是否合理，是否会将流程变复杂」+「按建议」
- 设计决策（用户拍板）：
  - **不做 P0-35 完整重构**：评审 → 讨论模式重构是过度工程化；LLM 自对抗物理局限存在；P0-34 刚做完未经实战验证就大改属 anti-pattern
  - **3 个小补丁**覆盖核心诉求：DEFER 收紧 + PM 自查 + PL 优先权
  - 红线数保持 15 条
- 处理（5 处改造）：
  - **P0-34-A. `roles/pm.md` + `templates/prd.md`：DEFER 严格收紧**
    - DEFER 加 `category` 字段，仅允许 `"business-decision"`（明确商业/用户决策范围：商业策略 / 价格 / 法务合规 / 用户研究待补）
    - 禁止类别：`technical-consistency` / `business-alignment` / `ux` / `quality`（必须 ADOPT 或 REJECT 带 rebuttal）
    - PMO 校验：扫描所有 DEFER 项的 category 一致性，违规打回 PM 重做，校验通过写 `state.plan_substeps_config.defer_audit_passed: true`
  - **P0-34-B. `roles/pm.md` + `templates/prd.md`：PM 对抗性自查段**
    - PM 每条 ADOPT/REJECT 之前必须输出 `adversarial_self_check` 段（≥2 句具体内容）
    - 站在 finding 提出方视角写最强反驳论据（防止 LLM 配合性回应 / sycophancy）
    - REJECT 项 rationale 必须直接回应 adversarial_self_check 中的反方论据
    - PMO 校验：扫描所有 ADOPT/REJECT 项的 adversarial_self_check 字段（≥2 句具体内容 / 非空白 / 非占位符），违规打回，校验通过写 `state.plan_substeps_config.adversarial_check_passed: true`
  - **P0-34-C. `stages/plan-stage.md` + `roles/pmo.md` + `templates/prd.md` + `templates/feature-state.json`：PL 优先权 + 业务方向锁死**
    - 子步骤 2 拆为「阶段 2a：PL 优先评审」+「阶段 2b：其他角色并行评审」
    - PL 评审收敛 → PMO 写 PRD frontmatter `business_direction_locked: true` + state.json `business_direction_locked: true` + `business_direction_locked_at`
    - 业务方向不锁死，其他评审角色禁止 dispatch（防止焦点切碎）
    - PMO 智能推荐：review_roles[] 含 PL 时默认 `pl_prioritized: true`；纯技术 refactor / 业务方向已在 CR 阶段锁死时退化为 P0-34 全并行
    - 其他角色基于锁死 PRD 评审；发现实现层与已锁死方向矛盾，以 high 严重度上升触发回归 PL 二次评审
- 风险控制：
  - 不重构产物结构（PRD-REVIEW.md 仍保留）
  - 不重命名 state.json 字段（review_round / review_roles[] 等保持原名）
  - 不增加 Stage 步数（仍是 P0-34 的 5 子步骤）
  - PL 优先权可关闭（`pl_prioritized: false` 退化全并行，兼容纯技术 refactor）
  - 老 Feature 兼容：现有 Feature 已无新字段时按默认值（false）行为
  - 红线数保持 15 条
- 影响面：
  - 改动文件：5 个（pm.md / prd.md / plan-stage.md / pmo.md / feature-state.json + SKILL.md / init-stage.md / CHANGELOG.md 版本号）
  - state.json 字段：`plan_substeps_config` 加 `pl_prioritized` / `business_direction_locked` / `business_direction_locked_at` / `defer_audit_passed` / `adversarial_check_passed`
  - PRD frontmatter：加 `business_direction_locked` / `business_direction_locked_at`
  - PRD-REVIEW.md frontmatter：`pm_response` 重构为对象（含 action / category / adversarial_self_check / rationale / responded_at）
  - 用户体验：PM response 不再轻量；DEFER 不能滥用抛给用户；PL 业务对齐先于技术评审
- 待跟进（非 P0-34-A 范围）：
  - 1-2 个真实 Feature 跑下来后回顾对抗深度实测效果
  - 如果实测仍不够深，再启动 P0-35（评审 → 讨论模式重构）

---

## v7.3.10 + P0-34

> v7.3.10+P0-34 Plan Stage 5 子步骤显式化 + 多角色并行评审重构 + 用户质疑反应模式：用户实战 case（AI 进入 Plan Stage 后只做 PRD 初稿就直接暂停等用户确认，跳过了「PL 讨论」「RD/QA/Designer 多视角评审」「PM 回应循环」等内部子步骤）暴露当前 Plan Stage 设计的两个根因：(1) 子步骤对 AI 不可见——Plan Stage 在主对话被当作"原子动作"，PRD 初稿后直接跳到「⏸️ 用户确认」，PL 讨论 + 4 视角评审被预测性简化；(2) PL 角色定位混淆——PL 既是 product-overview/CR 的 driver，又是 Plan Stage 的"独立讨论 step"，导致 AI 不清楚 PL 在 Plan Stage 究竟该不该出现。本次重构：将 Plan Stage 拆为 5 个显式子步骤（PRD 初稿 → 多角色并行评审 → PM 回应循环 → 全员通过判定 → ⏸️ 用户最终确认），PL 降级为评审角色（与 RD/QA/Designer/PMO peer），评审组合 + Subagent 并行 vs 主对话执行模式由 PMO 在 triage Step 8 智能推荐 + 用户确认后写入 state.json 的 `plan_substeps_config`。AI Plan 模式 Execution Plan 从 4 行扩为 5 行（新增 `Steps remaining` 行强制枚举子步骤），强化"声明即承诺"细则（声明 Read 的 spec 必须真实 Read，可用 grep 历史 ToolUse 验证）。新增「用户质疑流程时 AI 反应模式」4 条规则（先规范 cite + 再边际价值 + 不主动建议跳过 + 用户明确说才豁免），防御 AI 看到用户疑虑就预测性简化的反模式。

### P0-34：Plan Stage 5 子步骤显式化 + 多角色并行评审 + 用户质疑反应模式

- 触发：用户「我觉得当前 Plan Stage 在主对话执行的时候，AI 容易跳过其中的 PL 讨论 + 多视角评审子步骤，直接 PRD 初稿后就 ⏸️ 等用户确认。这是流程被预测性简化的典型」+「在想想该怎么改」+「方向 B，需要 PMO 智能决策，但无论何时，智能决策的过程不能跳过，对应我们的 triage stage」+「Plan Stage 应该还有外部模型视角评审」+「我觉得 PL 讨论去掉，PL 也作为评审的一个角色」+「Subagent 并行 vs 主对话的混合，triage 阶段 PMO 来决定」+「按建议」
- 设计决策（用户拍板）：
  - **Plan Stage 5 子步骤显式化**：PRD 初稿（PM 主对话）→ 多角色并行评审（subagent / 主对话由 PMO triage 决定）→ PM 回应循环（ADOPT/REJECT/DEFER）→ 全员通过判定（all PASS / PASS_WITH_CONCERNS）→ ⏸️ 用户最终确认。Round ≤ 3，超出 Round 3 触发用户决策（force-pass / continue-round-4 / modify-scope / abort）。
  - **PL 角色定位拆分**：PL 在 product-overview / change-request 阶段是 driver；在 Plan Stage 是评审角色（与 RD/QA/Designer/PMO peer），不再有"独立 PL-PM 讨论 step"。
  - **外部模型评审作为 Plan Stage 子步骤 4**：由 P0-28 `plan_enabled` 控制（不引入新开关）。
  - **执行模式 PMO 智能决策**：subagent 并行 vs 主对话由 PMO 在 triage Step 8 推荐（信号：文件数 / 跨子项目 / 上下文累积 / token budget）+ 用户 5 选 1 确认（采用推荐 / 全 Subagent / 全主对话 / 自定义 / 其他指示）。
  - **Direction A 核心**：Execution Plan 从 4 行扩为 5 行（新增 `Steps remaining`），强迫 AI 在 Stage 开始前枚举子步骤，跳步立即可见。
  - **声明即承诺**（新增红线 #14 细则）：声明 Read 的 spec 必须真实 Read，可用 grep 历史 ToolUse 验证；声明而未 Read 视为伪造证据，违反闭环验证红线 #9。
  - **用户质疑反应模式**（4 条规则）：先 cite 规范 → 分析本场景边际价值 → 不主动建议跳过 → 用户明确说「跳过」才豁免（红线 #3 兜底）。
  - 红线数保持 15 条（红线 #14 扩展 + 用户质疑反应模式作为常规规则）
- 处理（11 处改造）：
  - **P0-34-1. `roles/pmo.md` 加 Plan Stage 评审组合智能推荐表**：5 种 Feature 类型 × 评审角色组合表 + 执行模式信号（subagent vs 主对话）+ 5-step 推荐流程 + PMO 视角触发条件（中以上启用）+ Designer 视角触发条件（双保险：PRD frontmatter + UI 关键词）+ Round 3 overflow 用户决策。
  - **P0-34-2. `stages/triage-stage.md` Step 8 加 Plan Stage 评审组合决策段**：PMO 推荐格式 + 5 选 1 选项 + Step 9 state.json 初始写入加入 `plan_substeps_config`。
  - **P0-34-3. `templates/feature-state.json` 加 plan_substeps_config 字段**：含 `review_roles[]`（每项 role + execution）+ `review_round` + `review_round_overflow_decision` 枚举（force-pass / continue-round-4 / modify-scope / abort）。
  - **P0-34-4. `stages/plan-stage.md` 重写 Process Contract**：5 子步骤表 + Step 2 并行 dispatch 逻辑 + Step 3 PM 回应规则（ADOPT/REJECT/DEFER）+ Step 4 round 判定 + Round 3 overflow 处理 + Step 5 用户最终确认 + PRD-REVIEW.md frontmatter schema 引用 + 流程硬规则更新。
  - **P0-34-5. `roles/product-lead.md` 加「PL 作为评审角色」段**：按 Feature 类型激活 + PL 评审 checklist（业务方向一致性 / 业务流程完整性 等）+ verdict 标准 + Subagent vs 主对话指引 + driver 角色（product-overview/CR）vs reviewer 角色（Plan Stage）的边界。
  - **P0-34-6. `roles/pm.md` 替换「PL-PM Teams 讨论」为「PM 评审回应规则」**：每条 finding 的回应规则（ADOPT 改 PRD / REJECT 给理由 / DEFER 给追踪位置）+ 硬规则（回应完整性 + 不静默跳过）+ 轮次流程描述。
  - **P0-34-7. `roles/rd.md` / `roles/qa.md` / `roles/designer.md` 加 Plan Stage PRD 评审 checklist**：各角色专属维度 + verdict 标准。
  - **P0-34-8. `templates/prd.md` 追加 PRD-REVIEW.md frontmatter schema**：`prd_feature_id` / `review_round` / `reviews[]` 数组（每项 role / execution / verdict / findings[] / pm_response）/ `overall_verdict` / 机器可验证条件。
  - **P0-34-9. `rules/flow-transitions.md` + `FLOWS.md` 加 Plan Stage 5 子步骤转移**：8 个新转移行 + auto 强制保留清单 3 条 + Feature 流程链显示 Plan Stage 5 子步骤标注。
  - **P0-34-10. `SKILL.md` Execution Plan 4 行 → 5 行（加 Steps remaining）+ 红线 #14 加声明即承诺细则；`RULES.md` + `roles/pmo.md` 加用户质疑流程时 AI 反应模式段**（4 条规则 + 输出模板 + 反例 + 与红线关系）。
  - **P0-34-11. CHANGELOG + 版本号 bump + 一致性自检**。
- 风险控制：
  - 不破坏现有 Plan Stage 上下游契约（仍以 PRD.md + PRD-REVIEW.md 为产物）
  - 评审组合 PMO 推荐 + 用户显式确认（不允许 PMO 主动 "省略评审角色"）
  - Round ≤ 3 硬上限 + 超出走用户决策，避免无限循环
  - 红线数保持 15 条（修订红线 #14 + 加常规规则，不增红线）
  - 兼容老 Feature：现有 Feature 已无 `plan_substeps_config` 时 PMO 按"全 4 视角内部 + 主对话"默认值
- 影响面：
  - 改动文件：13 个（pmo.md / triage-stage.md / feature-state.json / plan-stage.md / product-lead.md / pm.md / rd.md / qa.md / designer.md / prd.md / flow-transitions.md / FLOWS.md / SKILL.md / RULES.md）
  - state.json 字段：feature 顶层加 `plan_substeps_config`（含 review_roles[] / review_round / review_round_overflow_decision）
  - SKILL.md 红线 #14 扩展：4 行 → 5 行 + 声明即承诺细则
  - 用户体验：Plan Stage 不再被预测性简化 + 用户质疑时 AI 不再主动建议跳过 + 评审组合可定制
- 待跟进（非 P0-34 范围）：
  - 评审 verdict 自动化校验工具（解析 PRD-REVIEW.md frontmatter，未来 P0）
  - Plan Stage 评审耗时实测数据 + 推荐表权重调整（积累 5+ Feature 实战后回顾）

---

## v7.3.10 + P0-33

> v7.3.10+P0-33 变更管理升级：用户实战 case（BG-015 5 个子 Feature 中 2 已合并 staging、3 仍占位 FXXX）暴露当前变更管理两个问题：(1) `teamwork_space.md` 承担过多——既是子项目入口又含跨项目变更详细追踪表（子 Feature 编号 / 推进顺序 / 联调依赖），文件膨胀；(2) "边规划边启动"反模式——变更内 5 个子 Feature 没全部规划完就启动了 2 个，剩 3 个仍是占位符，跨子项目协调成本高。本次新增独立变更文档体系：`product-overview/changes/{change_id}.md` 含 YAML frontmatter（机读 status / sub_features / launch_order）+ 完整规划详情；`teamwork_space.md` 简化为变更索引（简介 / 状态 / 文档链接）；硬约束变更状态 != `locked` 时禁止启动归属本变更的子 Feature（PMO 在 triage Step 6.5 硬阻塞 + 用户明确选「强制启动」逃生舱）。

### P0-33：变更管理升级（独立文档 + 锁定后启动 + teamwork_space.md 简化）

- 触发：用户「变更流程需要做的更合理一些。变更描述文档放到 product-overview 子目录 changes 下，teamwork_space.md 只维护简单介绍 / 索引 / 当前状态，降低 teamwork_space.md 的负担。变更流程需要做完所有的需求规划后才能正式启动 feature」+「按建议」
- 设计决策（用户拍板）：
  - **变更编号格式**：`CR-{编号}` 推荐通用 / `BG-{编号}` 兼容历史 / `TD-{编号}` 可选
  - **state.json 加 change_id 字段**（null 表示独立 Feature 不归属任何变更）
  - **硬阻塞 + 强制启动逃生舱**：变更未锁定时禁止启动子 Feature，但保留「用户明确选数字 2」的逃生舱（不接受 ok / 默认推进）
  - **现有变更回填支持**（如 BG-015）：不阻塞已启动子 Feature，但补登未启动的 + 锁定剩余规划
  - **变更 vs ADR 并存**：变更=跨多 Feature 协作规划，ADR=单一技术决策；互相引用（变更 frontmatter `related_adrs`）
  - 红线数保持 15 条
- 处理（8 处改造）：
  - **A. 新建 `templates/change-request.md`**：独立变更描述模板，含完整 YAML frontmatter（change_id / status / sub_features / launch_order / risks / related_adrs）+ 状态生命周期 + 编号约定 + 与 teamwork_space.md / ADR / ROADMAP 的关系
  - **B. `templates/teamwork-space.md` 简化**：删除「跨项目需求追踪」详细表（子 Feature 编号 / 推进顺序 / 联调依赖）；改为「跨项目变更索引」段（简介 / 状态 / 影响子项目 / 文档链接）+ 加「跨项目当前阻塞」段（仅活跃阻塞项）
  - **C. `roles/product-lead.md` 加「变更管理」段**：状态生命周期 + PL 在各阶段的职责 + 模式二「执行模式」与变更管理的关系（升级而非废弃）+ 编号约定 + 与 ADR 的关系
  - **D. `stages/triage-stage.md` Step 6.5 变更归属检查**：扫描 product-overview/changes/*.md → 判断当前 Feature 归属 → 按变更状态决策（discussion/planning 硬阻塞 / locked/in-progress 校验 launch_order 拓扑位置 / completed/abandoned 异常提示）+ 4 选 1 逃生舱
  - **E. `roles/pmo.md` 加「📦 变更归属检查」段**：扫描 / 匹配规则 / 状态决策矩阵 / 阻塞输出格式 / 强制启动 + 改独立 Feature 处理 / state.json 写入 / 硬规则
  - **F. `templates/feature-state.json`**：顶层加 `change_id` + `change_force_start` 字段 + 注释说明
  - **G. `FLOWS.md` Feature Planning 段加「变更级 Planning」子模式**：完整流程描述（discussion → planning → locked → in-progress → completed）+ 核心约束 + 与 templates/change-request.md / roles/product-lead.md 关联
  - **H. `rules/flow-transitions.md` 加「变更管理状态转移」段**：6 个状态转移行 + 硬阻塞条件；auto 强制保留清单加 2 条（变更归属阻塞 4 选 1 / 锁定确认 4 选 1）
  - **I. `roles/pm.md` 职责段加变更级 Planning 协作规则**
- 风险控制：
  - 不阻塞独立 Feature（`change_id = null` 时 PMO 不做变更检查）
  - 既存变更（如 BG-015）支持回填，不强制重写历史
  - 强制启动逃生舱保留 + state.concerns WARN 留痕
  - 变更详情独立文档化避免 teamwork_space.md 膨胀
  - 红线数保持 15 条（修订流程边界，不增红线）
- 影响面：
  - 新建文件：1 个（`templates/change-request.md`）+ 新目录约定（`product-overview/changes/`）
  - 改动文件：8 个（teamwork-space.md / product-lead.md / triage-stage.md / pmo.md / feature-state.json / FLOWS.md / flow-transitions.md / pm.md）
  - state.json 字段：顶层加 change_id + change_force_start
  - 用户体验：变更管理流程更清晰（"规划完才启动"硬约束）+ teamwork_space.md 轻量化
- 待跟进（非 P0-33 范围）：
  - install.sh 是否需要在 product-overview/ 下自动建 changes/ 目录（暂不做，PMO 在首次创建变更时自建）
  - PMO triage 时 git 推断 feature 是否已合并（与 P0-32 配合解决"staging 尾巴"问题，可作为 P0-34）

---

## v7.3.10 + P0-32

> v7.3.10+P0-32 红线 #1 修订 + Ship Stage 第二段 push merge_target 收尾：用户实战 case 暴露 v7.3.10+P0-29 双段流程留下的"staging 尾巴"问题——MR 合并后 PMO 验证 + 写 state.json 最终态，但这个最终态只在本地 worktree 内（之后被清理）+ 没回到 staging，导致下个 Feature 启动时 PMO 在 staging 上看到上个 Feature 的 state.json 仍显示 phase=pushed，误判为"还在进行中"。本次修订红线 #1 加 Ship Finalize 例外条款：第二段 finalize 阶段允许 PMO push merge_target 一次，仅限 `{Feature}/state.json` 一个文件、仅状态字段、零业务影响。push 失败有完整降级路径（pull --rebase 重试 1 次 / 退回 feature 分支 push + state.concerns WARN），不阻塞流程。代码层合并权（push merge_target 业务代码）仍 100% 属于平台和用户。

### P0-32：红线 #1 修订 + Ship Stage 第二段 push merge_target 收尾

- 触发：用户「ship 流程，mr 合入后还会有一次状态变更，这个状态变更会被丢弃掉」+「在 staging 推进下一个需求的时候，往往还剩上一个需求的尾巴，因为 staging 并不知道上个需求已经完结」+「PMO 直接 push staging，是否更合理，我们修改下红线。确认 commit 合入后，切到目标分支，改状态，push，然后再清理 worktree」
- 设计决策：
  - **修订红线 #1（不是删除）**：保留"PMO 不做本地 merge / 不解决冲突"核心约束；新增 Ship Finalize 例外条款（仅一文件、仅状态字段、零业务影响）
  - **拆为更细的 Step 4-10**：原 Step 5/6/7 拆为 Step 5（检测）/ Step 6（切 merge_target + pull）/ Step 7（写最终态）/ Step 8（push）/ Step 9（清理 worktree）/ Step 10（完成报告）
  - **state.json 写入位置变更**：原"第二段写 state.json 在 worktree 内"→"在 merge_target 工作区内的 feature 目录"——避免 worktree 删除时丢失
  - **push 失败完整降级**：冲突 pull --rebase 重试 1 次 / protect rule 直接降级 / 网络失败询问用户 / 其他错误降级 + concerns
  - **降级仍记 phase=merged**（合并已完成，仅 push staging 失败不影响最终态判定）
  - 红线数保持 15 条（修订红线 #1 边界，不新增红线）
- 处理（6 处改造）：
  - **A. `SKILL.md` 红线 #1**：原"Ship Stage 行为（不 push merge_target）" → 新"Ship Stage 行为（v7.3.10+P0-15 / +P0-32 修订）"，加 Ship Finalize 例外条款 + 严格边界（仅 state.json 一文件 / 仅状态字段 / 零业务影响）+ push 失败降级
  - **B. `stages/init-stage.md` 红线 #1 注入段同步**：CLAUDE.md 注入红线 #1 加 Ship Finalize 例外条款描述
  - **C. `RULES.md` Ship Stage 速查段**：单 Stage 描述扩展为双段（第一段 push 不动 merge_target / 第二段 finalize push state.json 元数据）
  - **D. `stages/ship-stage.md` 第二段 Step 4-7 重写为 Step 4-10**：
    - Step 5（检测结果处理）：不在本步写 state.json，记录到内存变量
    - Step 6（切 merge_target）：cd 主工作区 + git checkout + git pull --ff-only；pull 失败暂停
    - Step 7（写 state.json 最终态）：在 merge_target 工作区内的 feature 目录写最终态（严格边界）
    - Step 8（push merge_target）：git add + commit + push；4 类失败降级（冲突 / protect rule / 网络 / 其他）
    - Step 9（清理 worktree）：cd 主工作区 + git worktree remove
    - Step 10（完成报告）：state.json 已在 Step 7+8 完整写入，本步只输出报告
  - **E. `roles/pmo.md` Ship Stage PMO 职责速查重写**：双段 + finalize push merge_target + 失败降级三态 + 红线 #1 边界（允许 / 禁止）
  - **F. `templates/feature-state.json` 加 3 个字段**：merge_target_pushed_at / merge_target_push_failed / merge_target_push_failed_reason（含 conflict / protect-rule / network / other 枚举）
  - **G. `rules/flow-transitions.md` Ship 第二段拆 6 行**：原 1 行（第二段统一行）扩展为 6 行（Step 6 切 merge_target / Step 6 pull 失败 / Step 7-8 push 成功 / Step 8 push 失败降级 / Step 9 清理 worktree）+ auto 强制保留清单加 2 条
  - **H. `FLOWS.md` Feature 流程图段更新**：10. Ship Stage 第二段从单行扩展为 7 行（Step 4-10 含 push merge_target 步骤）
- 风险控制：
  - 严格边界：仅 state.json 一文件、仅状态字段、零业务影响——红线 #1 的核心精神（PMO 不动业务代码）保持不变
  - push 失败完整降级：冲突 / protect rule / 网络 / 其他四类全有处理路径，不阻塞流程
  - 降级路径仍记最终态（feature 分支 push + state.concerns WARN）—— 即使 push merge_target 失败，本地 / feature 分支 remote 都有完整最终态
  - PMO 后续 triage 时 git 推断（git branch -r --contains）即使 staging 上 state.json 不完整也能正确识别 feature 已合并（这部分逻辑可在 P0-33 加，本次先不做）
- 影响面：
  - state.json 字段：state.ship 加 3 个字段（merge_target_pushed_at / merge_target_push_failed / merge_target_push_failed_reason）
  - 改动文件：6 个核心（SKILL.md / init-stage.md / RULES.md / ship-stage.md / pmo.md / feature-state.json）+ 2 个流转文件（flow-transitions.md / FLOWS.md）
  - 用户体验：staging 上 state.json 现在会显示 phase=merged（push 成功时）/ phase=merged + concerns（降级时）→"尾巴"问题在 push 成功路径下消失
  - 红线数：15 条（保持）
- 待跟进（非 P0-32 范围）：
  - P0-33 候选：PMO triage / init-stage 扫描 Feature 状态时加 git branch -r --contains 推断（即使 staging 上 state.json 不完整也能正确识别 feature 已合并）—— 双重保险

---

## v7.3.10 + P0-31

> v7.3.10+P0-31 两个补丁：(1) worktree 默认值从 off 翻转为 auto（撤销 v7.3.9+P0-9 决策）；(2) PMO 角色规范增加 ok = 按 💡 建议 识别快速规则（v7.3.10+P0-18 已在 RULES/STATUS-LINE 定义，本次在 roles/pmo.md 显式标注 PMO 收到用户输入时的识别顺序）。

### P0-31-A：worktree 默认值改为 auto（撤销 P0-9）

- 触发：用户「修改下现有逻辑：默认开始 worktree」
- 设计决策（撤销 P0-9 默认 off 的考量）：
  - 多 Feature 并行场景实际更常见，worktree 隔离避免主分支污染
  - v7.3.10+P0-29 Ship Stage 双段流程后 worktree 清理已闭环（合并验证后自动清理）
  - v7.3.10+P0-25 worktree deps 处理已有完整指引（standards/common.md 含 npm install / 软链 / KNOWLEDGE 三种处理选项）
  - v7.3.10+P0-27 环境配置预检前置到 triage，worktree 创建已自动化无暂停点
  - off 仍保留为可选（megarepo / IDE 跨 worktree 跳转受限场景仍可手动改 off）
- 处理（2 处改造）：
  - **A. `templates/config.md`**：worktree 字段默认值 `off` → `auto`；注释更新为 v7.3.10+P0-31 决策说明 + 撤销 P0-9 的理由 + 何时改 off 的指引
  - **B. `stages/init-stage.md`**：localconfig 不存在时的兜底从 `worktree=off` → `worktree=auto`，注释同步更新
- 影响面：
  - 既有项目（已有 .teamwork_localconfig.md 含 worktree=off）→ 不受影响（用户配置优先于默认值）
  - 新项目 / localconfig 缺失 → 默认 auto，PMO 在 Plan Stage 入口自动按 environment_config 创建 worktree
  - Micro 流程：本来就是直接改主分支不创建 worktree，不受默认值影响
- 风险控制：
  - 用户可随时改回 off（编辑 .teamwork_localconfig.md）
  - PMO 在 triage Step 7.5 环境配置预检会显式输出 worktree 模式 → 用户在暂停点可见

### P0-31-B：roles/pmo.md 显式标注 ok = 按建议 识别规则

- 触发：用户「PMO 需要知道 ok = 按建议」
- 现状诊断：v7.3.10+P0-18 已在 RULES.md / STATUS-LINE.md / SKILL.md / INIT.md 定义 ok 约定，但 roles/pmo.md（PMO 角色规范权威源）没有显式段落——PMO 加载自身规范时可能漏过该约定
- 处理（1 处改造）：
  - **`roles/pmo.md` 顶部加「🟢 用户输入识别快速规则」段**（在格式权威守门段之后、state.json 状态机维护规范之前）：
    - 4 类用户输入识别顺序（数字/字母 → ok 类肯定词 → 切换流程关键词 → 自由输入）
    - ok 类清单（ok / OK / Ok / 好 / 可以 / 行 / 嗯 / 按建议 / 按推荐）
    - PMO 必须 cite「✅ 已按 💡 建议处理：…」作为审计痕迹
    - 前置条件 + 边界保留（破坏性操作仍需显式数字回复）
    - 链接到 RULES.md 完整规范
- 影响面：
  - PMO 加载自身规范时直接看到 ok 识别规则，不依赖跨文件读取
  - 其他文件（RULES / STATUS-LINE）的 ok 规范不变，本次只是补 pmo.md 的显式入口

### 元数据

- SKILL.md frontmatter 7.3.10+P0-30 → 7.3.10+P0-31
- stages/init-stage.md L111 同步
- 红线数保持 15 条

---

## v7.3.10 + P0-30

> v7.3.10+P0-30 问题排查类轻量化：用户实战 case 暴露 triage-stage 对所有流程类型用同一个暂停点格式（4 选 1）的副作用——问题排查这种"用户意图明确、零代码改动、纯只读"的轻量任务被迫走完整 triage（4 步流、3 个暂停点）+ 询问排查范围 + 4 选 1 流程确认，反而违反用户明确意图。本次针对问题排查类做精准简化：信号置信度高时跳过 triage 4 选 1 流程确认暂停点（主动声明 + 直接执行 + 保留打断机制）；删除"PMO 给排查清单 → ⏸️ 用户确认范围"暂停点（PMO 自主决定排查范围 + 默认只读不启本地服务 + 标注未实测项）；KNOWLEDGE / ADR 无命中时一行带过；问题排查不展示外部模型探测段。结果：问题排查典型暂停点从 3 个降到 1 个（仅排查报告后的决策）。

### P0-30：问题排查类流程精简（信号置信度高时跳过 triage 流程确认暂停点 + 删除排查范围确认暂停点）

- 触发：用户实战 case「检查下 aon-com 网站的 favicon 是否符合预期」跑出 4 步流 3 暂停点 + 排查范围确认询问，反模式明显 → 用户「如果是问题排查，能否简化一些，不需要确认那么多，减少流程环节，直接排查」
- 设计决策：
  - **仅简化问题排查类**（不动 Feature / Bug / 敏捷 / Feature Planning / Micro，影响面最小）
  - **置信度判定**：用户措辞含明确核验词（"检查 / 排查 / 看看 / 为什么 / 分析下 / 是否符合预期 / 定位"）+ 无修复指令 + 范畴清晰 → 高置信度走快速通道；模糊 / 跨子项目 → 保守走标准 4 选 1
  - **快速通道**：跳过 4 选 1 + 主动声明"直接进入问题排查执行" + 保留用户打断机制（"切换流程"）
  - **PMO 自主决定排查范围**：默认源码静态查（grep / ls / cat / git log）+ 配置核对；不启动本地服务（dev server / Playwright），如需实测须用户授权
  - **KNOWLEDGE / ADR 无命中渲染降级**：从展开三类 0 命中标题 → 一行带过（"📚 KNOWLEDGE 扫描：均无相关条目"）
  - **问题排查不展示外部模型探测段**：问题排查不出代码、不需要外部模型评审；triage 输出整体跳过该段
  - 红线数保持 15 条
- 处理（5 处改造）：
  - **A. `stages/triage-stage.md` Step 5 流程类型识别表**：扩展问题排查识别信号词典（增加"检查下 / 看看 / 是否符合预期"等核验意图措辞）
  - **B. `stages/triage-stage.md` Step 8 暂停点呈现重构**：
    - 标准路径：Feature / Bug / 敏捷 / Feature Planning / Micro 走原 4 选 1 流程确认
    - 快速通道：流程类型 = 问题排查 + 信号置信度高 → 主动声明 + 直接执行
    - 置信度判定表（高 / 中 / 低 三档 + PMO 决策）
    - 用户打断机制（"切换流程"等关键词）
  - **C. `stages/triage-stage.md` Step 2 / 3 / 4 输出渲染降级**：
    - Step 2 KNOWLEDGE 无命中 → 一行带过（"📚 KNOWLEDGE 扫描：均无相关条目"）
    - Step 3 ADR 无命中 → 一行带过（"📜 ADR 扫描：均无相关决策"）
    - Step 4 外部模型探测：问题排查类时整体跳过本 Step
  - **D. `FLOWS.md` 问题排查流程概览段重构**：
    - 删除"PMO 派发角色 → ⏸️ 用户确认范围"暂停点
    - 加用户打断机制段
    - 简化为"用户提问 → triage 识别 + 信号置信度判定 → PMO 派发 + 自主决定范围 + 直接执行 → ⏸️ 用户决策"（仅 1 暂停点）
  - **E. `roles/pmo.md` 加「🔍 问题排查类轻量执行规则」段**：
    - 信号置信度判定表
    - PMO 派发角色规则（保留原 RD / PM / Designer）
    - 自主决定排查范围（默认只读，不启本地服务，标注未实测项）
    - 排查报告必填项（现状速查 / 现状 vs 预期 / 偏差等级 / 修复建议 / 未实测项清单）
    - 排查后 6 选 1 暂停点（不处理 / Micro / 敏捷 / Feature / Bug / 其他）
  - **F. `rules/flow-transitions.md` 问题排查流程转移表重构**：
    - 高置信度行：triage → 问题排查执行 🚀自动
    - 中/低置信度行：triage → 4 选 1 → 问题排查执行 ⏸️暂停
    - 删除原"问题排查梳理 → 排查待确认"独立行（合并到执行）
- 风险控制：
  - PMO 拿不准时**保守走标准 4 选 1**——用户回 1 选问题排查仍然进入快速通道，不会跑错流程
  - 用户打断机制保留（"切换流程"等）—— 任何时机用户都能切换
  - 修复指令明确时（如"检查并修好"）不识别为问题排查 → 走对应敏捷 / Bug / Micro 流程
  - 默认不启动本地服务 = 默认不动用户环境，避免越权
- 影响面：
  - 问题排查典型暂停点：3 个（流程确认 + 排查范围 + 决策）→ **1 个**（仅决策）
  - triage 输出长度：无命中场景下显著缩短
  - 改动文件：4 个（triage-stage.md / FLOWS.md / pmo.md / flow-transitions.md）
  - 红线数：15 条（保持）
- 待跟进（非 P0-30 范围）：
  - Feature Planning / Micro 是否也需要类似简化（用户暂未提，先不动）
  - 实战观察"信号置信度判定"的准确率，必要时调整词典

---

## v7.3.10 + P0-29

> v7.3.10+P0-29 Ship Stage 双段流程：用户洞察当前 Ship Stage 在 v7.3.10+P0-15 后留下"AI 生成 MR URL 后即结束"的工程缺口——用户在平台合并 MR 后 PMO 没有机制感知，worktree 永远 deferred、state.current_stage 永远停在 ship、Feature 永远不到 completed。本次重构为双段流程：第一段 push + 生成 MR URL + 输出明确"下一步该做什么"指引（4 选 1 暂停点：已合并/等待中/关闭未合并/其他）；第二段 finalize：用户回 1 后 PMO 用 `git branch -r --contains {feature_head_commit}` 自动检测合并 → 清理 worktree → Feature 标记 completed。检测失败（squash merge / GitLab rebase 重写场景）询问用户提供 commit hash 兜底。
>
> 设计哲学：把"明确告诉用户该做什么"做到位（v7.3.5/P0-18 暂停点编号化的延续），比开发复杂的自动监控更可靠；用户在每个关键节点都能"回数字即可继续"。

### P0-29：Ship Stage 双段流程（push → 等待合并 → finalize）

- 触发：用户「目前主要的问题是给出 mr create 链接，ai 什么也做不了了，是否能做到监控 MR 合入，合入后自动完成收尾」+「给出 mr create 后给个提示，合入后回复 1，将收尾流程。这样用户回到会话就知道该怎么做了」+「不用搞降级链了 简单点 branch-contains 检查就可以了。有问题询问用户」
- 设计决策：
  - **不做复杂的自动监控**（gh/glab 多层降级 / scheduled-task 轮询 / webhook）—— 简单可靠优先
  - **第一段暂停点明确指引**：用户在 MR URL 生成后看到"下一步该做什么"，回平台合并 → 回数字即可继续
  - **第二段用单一 git 命令检测**：`git branch -r --contains {feature_head_commit}` 覆盖 merge commit + GitHub rebase 等高频场景
  - **检测失败询问用户**：squash merge / GitLab rebase 重写场景下用户提供 hash + git 校验
  - **worktree 清理推迟到第二段**：合并验证通过后才清理（避免合并出问题需要回滚时 worktree 已经没了）
  - **MR 异常分支**：用户回 3 / 第二段询问回 3 → 进入异常处理（重开 MR / 放弃 Feature / 暂时等待）
- 处理（4 处改造）：
  - **A. `templates/feature-state.json` 加 ship 字段**（5 个新字段 + 1 个 enum 扩展）：
    - feature_head_commit / phase / merge_commit_hash / mr_merged_at / merge_detection_method
    - shipped enum 扩展：null | pushed | merged | closed_unmerged | abandoned | failed
    - phase enum：null | pushed | merged | closed_unmerged
  - **B. `stages/ship-stage.md` 重构为双段流程**：
    - 头部：v7.3.10+P0-29 双段流程定位 + 职责说明
    - 步骤概览：第一段 Step 1-3 + 第二段 Step 4-7 + 异常分支
    - Step 2 push 后加"git rev-parse 记录 feature_head_commit"
    - Step 3 重写为"等待合并暂停点 4 选 1"（删除原 worktree 清理暂停点，推迟到 Step 6）
    - 新增 Step 4：git fetch + git branch -r --contains 检测
    - 新增 Step 5：检测结果处理（5.A 通过 / 5.B 询问用户）
    - 新增 Step 6：清理 worktree（执行原 deferred）
    - 新增 Step 7：Feature 完成报告
    - 新增「异常处理段」：MR 关闭未合并 4 选 1（重开/放弃/暂时等待/其他）
  - **C. `roles/pmo.md` Ship Stage PMO 职责速查改写**：
    - 原 v7.3.10+P0-15 速查（3 步）→ v7.3.10+P0-29 速查（双段 + 异常分支）
    - 新增"第一段已完成、用户暂时退出"的恢复规则：下次进入 PMO 在 triage 识别 phase=pushed → 直接展示 Step 3 暂停点而不重跑第一段
  - **D. `rules/flow-transitions.md` + `FLOWS.md` 同步**：
    - flow-transitions：原 ship 1 行扩展为 6 行（第一段 / 等待合并暂停点 / 第二段 / 检测失败 / 异常处理 / push FAILED）
    - flow-transitions auto 强制保留清单加 3 条（第一段等待合并暂停点 / 第二段询问 hash / 异常处理）
    - FLOWS.md Feature 流程图段：原 9. Ship Stage 单步扩展为 9. Ship Stage 第一段 + 10. Ship Stage 第二段
- 风险控制：
  - 检测失败时 100% 走询问用户兜底，不静默标记为已合并
  - 用户提供 hash 必须经 git cat-file + branch -r --contains 双重校验
  - 异常分支保留完整路径（重开 MR / 放弃 / 等待）—— 不强制用户立刻决定
  - worktree 清理推迟到第二段验证通过后，避免误清理
  - 红线数保持 15 条
- 影响面：
  - state.json 字段：ship 子对象加 5 个新字段
  - 改动文件：4 个（feature-state.json / ship-stage.md / pmo.md / flow-transitions.md + FLOWS.md）
  - 用户体验：从"MR 生成后无衔接"→"4 选 1 明确下一步 → 自动验证合并 → 自动收尾"
- 待跟进（非 P0-29 范围）：
  - gh/glab CLI 适配（如未来用户反馈"git 检测覆盖率不够"）
  - scheduled-task 轮询（如 Cowork 环境下用户反馈"想要全自动"）

---

## v7.3.10 + P0-28

> v7.3.10+P0-28 三处评审外部模型决策合并到 triage-stage：用户洞察「PRD 评审 / 技术方案评审 / Review 是否需要外部模型」三处决策应该统一前置到 triage 阶段，由 PMO 按 Feature 规模/风险智能推荐 + 用户在 triage 暂停点一次性确认。`state.external_cross_review.enabled` 单字段拆为三处独立字段（plan_enabled / blueprint_enabled / review_enabled）。Review Stage 外部模型评审从 v7.3.10+P0-24 引入的「强制」改为「review_enabled 控制，默认 ON」——保持代码层最后 gate 行为，但允许用户在 triage 显式关闭。Fallback 兼容旧 enabled 字段。
>
> 默认行为：Plan / Blueprint 默认关（文档评审有内部 4 视角支撑），Review 默认开（代码层最后 gate）。PMO 按 Feature 规模/风险给智能推荐组合：大 Feature/高风险 → 三处全开；中/小 Feature/Bug → 仅 Review 开。提供快捷选项「采用推荐 / 全开 / 全关 / 自定义」。

### P0-28：三处评审外部模型决策合并到 triage-stage

- 触发：用户「我们把 prd 评审，技术方案评审，review 是否需要外部模型 放到 triage 阶段，由 pmo 根据实际情况设置」+「按建议，保留快捷选项」
- 设计决策：
  - **三处独立 enabled**：`external_cross_review.{plan_enabled, blueprint_enabled, review_enabled}` 取代单 `enabled` 字段
  - **Review 默认 ON**（保持 P0-24 引入的代码层最后 gate 行为，但从「强制」降为「review_enabled 控制」）
  - **PMO 智能推荐**用简单规则按 Feature 类型 + 关键词触发（不引入复杂权重模型）
  - **快捷选项**：采用推荐 / 三处全开 / 三处全关 / 自定义（用户回 `P=on/off B=on/off R=on/off` 格式）
  - **Fallback 兼容**：旧 enabled 字段自动映射到新三字段，旧 Feature 不强制迁移
- 处理（9 处改造）：
  - **A. `templates/feature-state.json` 字段拆分**：删除 `enabled` 单字段，新增 `plan_enabled / blueprint_enabled / review_enabled`；保留旧 enabled 注释作 fallback 文档化；加 `_fallback_compat` 注释说明读取规则
  - **B. `roles/pmo.md` 「外部模型交叉评审开关决策」段重写**：
    - 默认值改为三处独立（plan/blueprint=false, review=true）
    - 加 Step 3 PMO 智能推荐表（5 类 Feature 场景 × 3 处 Stage 决策矩阵）
    - 重写 Step 4 决策呈现（三处独立显示 + 5 选 1 快捷选项 + 选项 4 二级自定义）
    - Step 5 state.json 写入扩展为三字段
    - 兼容性段重写：fallback 优先级（三字段 > enabled > codex_cross_review > 默认）
    - 硬规则更新（默认值改为 PMO 推荐而非简单 OFF）
  - **C. `stages/triage-stage.md` Step 8 暂停点扩展**：外部模型决策点改为三处独立 + 快捷选项；Step 9 出口写入三字段
  - **D. `stages/plan-stage.md` 字段重命名**：`external_cross_review.enabled` → `external_cross_review.plan_enabled`（全文 replace_all）
  - **E. `stages/blueprint-stage.md` 字段重命名**：同上 → `blueprint_enabled`
  - **F. `stages/review-stage.md` 改为 review_enabled 控制**：
    - 入口宣告外部模型实例的条件改为 `review_enabled == true`
    - Step 4「外部模型独立审查」从「🔴 强制」改为「🟡 review_enabled 控制，默认 ON」
    - 措辞强调：与 P0-27 行为兼容（默认 review_enabled=true）
  - **G. `templates/external-cross-review.md` / `STATUS-LINE.md` / `FLOWS.md` / `templates/review-log.jsonl` 措辞同步**：
    - STATUS-LINE：徽章触发条件从 `enabled=true` 改为「任一 *_enabled=true」
    - FLOWS：默认值描述改为三处独立
    - review-log.jsonl：plan-external-review / blueprint-external-review / review-external 三行触发条件分别用对应 *_enabled
  - **H. `standards/external-model.md` §5.4 + Fallback 兼容表**：state.json 字段示例改为三字段；加 PMO 读取时 fallback 优先级表（5 个场景）
  - **I. CHANGELOG + 版本号 bump**：SKILL.md frontmatter 7.3.10+P0-27 → 7.3.10+P0-28；stages/init-stage.md 同步
- 风险控制：
  - 默认行为保持 P0-27 兼容：review_enabled 默认 ON，plan/blueprint 默认 OFF——既有 Feature 走 fallback 语义不变
  - 旧 Feature 不强制迁移（PMO 读取时自动 fallback）
  - 红线数保持 15 条
- 影响面：
  - 字段：state.external_cross_review 拆 1 → 3 字段
  - 改动文件：9 个（含 SKILL.md / 4 个 stage / pmo.md / state.json / external-cross-review.md / review-log.jsonl / STATUS-LINE.md / standards/external-model.md / FLOWS.md）
  - 用户体验：triage 暂停点决策项数 +1（外部模型评审），但配合快捷选项「采用推荐」实际操作步骤不变（一个数字回复完成）
  - 用户控制力：从「Plan/Blueprint 可选 + Review 强制」升为「三处全部可选」——更纯粹的"用户决定"
- 待跟进（非 P0-28 范围）：
  - PMO 智能推荐表的"中 Feature"判定标准实战观察后调整阈值
  - 跨 Feature 学习：连续 3 个 Feature 用户都改了推荐 → PMO 自动调整推荐策略（属于 P1+ 远期）

---

## v7.3.10 + P0-27

> v7.3.10+P0-27 删除 Plan Stage 入口 Preflight 暂停点：用户洞察 v7.3.9 引入的 Plan Stage 入口 preflight 暂停点是反模式——用户在 triage-stage 已经确认走 Feature 流程，再让用户对 PMO 自动跑通的环境检查结果做一次确认是仪式化操作；preflight 把"决策"和"执行"混在一起。重构原则：**决策前置到 triage（Step 7.5+8 探测 git 状态 + 用户在 triage 暂停点一次性确认环境配置），执行后置到 Plan Stage 入口（自动按 state.environment_config 执行 git 操作，无暂停点）**。Feature 典型暂停点从 4-5 个降到 3-4 个。preflight 概念整体废弃；Dev Stage 入口的"懒装依赖 preflight"和 PMO L1/L2/L3 dispatch 预检保留（不同概念）。

### P0-27：Plan Stage 入口 Preflight 暂停点删除

- 触发：用户「Plan Stage 入口 Preflight 确认 是否多余，直接 triage-stage 直接把需要确认的定好是否更合理」+「preflight 这命令也没用，直接去掉吧，保持干净，triage 阶段应该把该确认的都确认好了」
- 设计决策：
  - **彻底删除** Plan Stage 入口 preflight 暂停点（不留 escape hatch / 不做 `/teamwork preflight` 子命令）
  - 决策前置：triage Step 7.5 探测 git 状态（worktree / 分支 / base / 工作区干净度）+ Step 8 用户在 triage 暂停点一次性确认
  - 执行后置：Plan Stage 入口按 `state.environment_config` 自动执行 git 操作（fetch / 创建 worktree / 处理脏状态），**无暂停点**
  - 异常分支保留：base 不可达 / 分支冲突 / stash 失败时走异常分支（state.concerns + ⏸️），常规情况自动流转
  - 仅 Feature / Bug / 敏捷需求 流程触发 triage Step 7.5（Feature Planning / 问题排查 / Micro 不需要 worktree）
  - 红线数保持 15 条（无升格 / 无新增）
  - **Dev Stage 入口 preflight（懒装依赖，P0-3 引入）保留**——它是 Dev Stage 内部检查，不是用户暂停点
  - **PMO L1/L2/L3 dispatch 预检（红线 #13）保留**——它是 dispatch Subagent 前的预检，不同概念
- 处理（6 处改造 + CHANGELOG）：
  - **A. `stages/triage-stage.md` Step 7.5 加「环境配置预检」子段**：探测 git 状态 + 输出表格（worktree 模式 / 当前分支 / merge_target / base / 工作区状态 + 计划行为）+ 异常处理说明；仅 Feature / Bug / 敏捷需求 触发
  - **B. `stages/triage-stage.md` Step 8 暂停点扩展**：含流程类型 / 外部模型评审 / 环境配置异常（仅探测异常时出现）三层决策；常规情况下环境配置不需要单独决策
  - **C. `stages/triage-stage.md` Step 9 出口扩展**：写入 `state.environment_config = { worktree_mode, branch, merge_target, base, dirty_resolution, workspace_status_at_triage }`；triage 出口直接转入 Plan Stage（取代原"转入 Plan Stage 入口 preflight"）
  - **D. `stages/plan-stage.md` 删除整个「Stage 入口 Preflight」段（120+ 行）**，替换为新「Stage 入口环境准备」段（~70 行）：
    - 输入：state.environment_config（triage 已写入）
    - 自动执行序列：bash 4 步（dirty 处理 / fetch / worktree add / cd）
    - 异常分支表（4 类降级路径）
    - state.json 写入字段调整：`environment_config.{executed_at, worktree_created, concerns}`，删除原 `state.stage_contracts.plan_preflight` 字段
  - **E. `stages/plan-stage.md` 前置依赖段更新**：原 "Preflight" + "Worktree" 两条改为引用 state.environment_config
  - **F. `rules/flow-transitions.md` 删除 preflight 行**：原 "🔗 triage-stage → Plan Stage 入口 preflight" + "Plan Stage 入口 preflight → 🔗 Plan Stage" 两行合并为单行 "🔗 triage-stage → 🔗 Plan Stage（🚀自动）"；auto 豁免速查列表删除两条
  - **G. `roles/pmo.md` 删除「Plan Stage 入口 Preflight（v7.3.9 PMO 专属）」整段（80 行）**，替换为简短的「Plan Stage 入口环境准备」段（~15 行，引向 stages/plan-stage.md）；auto 豁免表中两条 preflight 行合并为一条
  - **H. 散落 preflight 字面值审查**：
    - `SKILL.md` 流程示例段删除 "0. Plan Stage 入口 preflight" 行
    - `stages/init-stage.md` auto 豁免列表 + worktree 检测段措辞调整
    - `templates/knowledge.md` "PMO preflight 阶段扫描" → "triage-stage 扫描" + 加链接
    - `templates/adr-index.md` "PMO preflight 阶段读取" → "PMO 在 triage-stage 阶段读取" + 加链接
  - **I. `templates/feature-state.json` 字段重构**：
    - 删除 stage_contracts.plan_preflight 整段
    - 新增顶层字段 `environment_config`（worktree_mode / branch / merge_target / base / workspace_status_at_triage / dirty_resolution / decided_at / executed_at / worktree_created / concerns）
    - 修订 stage_enum：删除 plan_preflight 枚举值，标注 v7.3.10+P0-27 重构说明
  - **J. CHANGELOG + 版本号 bump**：SKILL.md frontmatter 7.3.10+P0-26 → 7.3.10+P0-27；stages/init-stage.md L111 同步
- 风险控制：
  - 决策权完全保留给用户（在 triage 暂停点）—— 不是削减用户控制力
  - 异常分支降级路径完整（base 不可达 / 分支冲突 / stash 失败 都有暂停点 + state.concerns）
  - 既有 Feature 兼容：旧 Feature 的 stage_contracts.plan_preflight 字段允许遗留（PMO 读取时不报错），新 Feature 用 environment_config 字段
- 影响面：
  - 暂停点减少：Feature 典型暂停点 4-5 个 → 3-4 个
  - 改动文件：8 个（triage-stage.md / plan-stage.md / flow-transitions.md / pmo.md / SKILL.md / init-stage.md / knowledge.md / adr-index.md）+ 1 个 schema（feature-state.json）
  - 红线数：15 条（保持，无升格）
  - 概念清理：preflight 这个词在活文档中仅保留两处合理使用（Dev Stage 入口 preflight：懒装依赖；PMO L1/L2/L3 dispatch 预检），其他 preflight 字面值全部更名为"环境准备"或"环境配置"
- 待跟进（非 P0-27 范围）：
  - PRD 评审 / 技术方案评审 / Review 三处外部模型决策合并到 triage（用户提议 → P0-28）

---

## v7.3.10 + P0-26

> v7.3.10+P0-26 PMO 编排契约化升级：用户洞察 Teamwork 一致性漏洞——「PMO 承接用户输入 + 流程规划」当前散落在 5 个文件、4 种概念层级（红线 / 角色规范 / 流程文件 / 输出格式），但没有 Stage 契约。所有其他工作单元都走 Input/Process/Output 三契约，PMO 编排却游离在外。本次将 PMO 编排升格为契约化 Stage，确立**三层级 Stage 体系**：会话级（init-stage）/ 流程级（triage-stage）/ Feature 级（其余 10 个 stage）。同时 INIT.md 物理迁移到 stages/init-stage.md，统一所有 PMO 工作单元的契约形态。

### P0-26：PMO 编排契约化升级（init-stage + triage-stage）

- 触发：用户「pmo 承接用户输入，对流程进行规划，属于哪个 stage，我们讨论下怎样优化 teamwork 合理。我的理解是所有的动作都按照 stage 定义流程」+「合并，一次按最终目标推进」
- 核心设计决策（用户拍板）：
  - **State 归属**：triage-stage 选 B 方案（幂等不持久化）——不写 state.json，每次新对话按用户原始消息重跑，结果应一致；降低 IO 写入，提升效率
  - **INIT 也 Stage 化**：作为独立的会话级 Stage（init-stage）；从根本上消除"游离的 PMO 编排"概念
  - **Stage 体系扩展为三层级**：会话级 / 流程级 / Feature 级，每层有自己的状态归属规则
  - INIT.md 处理选 B（git mv + 引用迁移），不留 redirect 双源
  - SKILL.md 文件索引明确分层标注，让读者一眼看出三层级
  - stages/ 不分子目录（避免引用路径变化）
  - 红线数保持 15 条不变（红线 #4 / #11 / #15 现在是 Triage Stage 的强制力来源，措辞调整指向契约）
- 处理（9 处改造）：
  - **A. 新建 `stages/triage-stage.md`**（~280 行流程级 Stage 三契约）：
    - Input Contract：用户原始消息 / 项目空间状态 / KNOWLEDGE.md / ADR 索引 / 探测脚本输出 / Workspace Feature 状态
    - Process Contract（9 步）：用户输入承接 / KNOWLEDGE 扫描 / ADR 索引扫描 / 外部模型探测 / 流程类型识别 / 跨 Feature 冲突检查 / 流程步骤描述 / 暂停点呈现 / 用户回数字 → 创建 Feature 占位
    - Output Contract：主对话输出（不落盘）+ 用户确认后写入 Feature state.json
    - 机器可校验条件 7 项 + 幂等性保证说明
    - 失败 / 异常处理表（探测脚本失败 / KNOWLEDGE.md 不存在 / 用户消息无法识别 / 跨 Feature 冲突）
    - AI Plan 模式 + 入口 Read 顺序 + 与其他 Stage / 文件的关系
  - **B. INIT.md → `stages/init-stage.md`**（git mv + 三契约外壳）：
    - 头部加会话级 Stage 定位声明 + Input/Process/Output 三契约外壳
    - 「启动必做」段保留作为 Process Contract 的 9 步（v7.3.10+P0-26 标注）
    - 末尾追加 Output Contract 段（4 项必产出 + 唯一允许的写：teamwork_version 缓存）+ 出口决策表 + AI Plan 指引 + 失败处理 + 与其他 Stage 关系
  - **C. INIT.md 全文引用迁移**（10 个文件）：
    - 活引用全清：`SKILL.md` (5 处) / `STATUS-LINE.md` / `standards/external-model.md` / `standards/prompt-cache.md` (2 处) / `roles/pmo.md` / `RULES.md` / `agents/README.md` / `templates/detect-external-model.py` 注释 / `stages/init-stage.md` 自引用
    - `INIT.md` → `stages/init-stage.md`（链接路径同步调整）
    - 历史 docs/CHANGELOG.md / docs/OPTIMIZATION-PLAN.md 中的 INIT.md 引用保留（历史记录不动）
  - **D. `roles/pmo.md` 反向引用**（4 段）：
    - 「外部模型交叉评审开关决策」段 → 加 🔗 反向引用到 triage-stage Step 4
    - 「ADR 索引扫描」段 → 加 🔗 反向引用到 triage-stage Step 3
    - 「KNOWLEDGE 扫描 + 写入时机」段 → 加 🔗 反向引用到 triage-stage Step 2 + Stage 完成节点
    - 「跨项目依赖识别」段 → 加 🔗 反向引用到 triage-stage Step 6
    - **不删除原内容** —— roles 是 PMO 角色技术细节，stages 是阶段 IO 契约，两者互补
  - **E. `FLOWS.md` PMO 初步分析输出格式段**：加 🔗 反向引用到 triage-stage Output Contract（保留具体 markdown 渲染细节）
  - **F. `RULES.md` PMO 承接规则**：
    - 标题改为 → 红线 #4 / #11 / #15
    - 加 🔗 三条红线共同构成 Triage Stage 强制力来源
    - 流程描述改为「用户输入 → 进入 Triage Stage → ...」明确 Stage 化
  - **G. `SKILL.md` 文件索引升级**：
    - 加 stages/triage-stage.md 行
    - init-stage.md 行升级标注「会话级 Stage」
    - 加新章节「Stage 三层级体系」明确分层
  - **H. `rules/flow-transitions.md` 加新章节「会话级 + 流程级 Stage」**：
    - 表格定义会话启动 → init-stage → 等待用户输入 → triage-stage → Feature 级 Stage 的转移路径
    - Feature 流程表头改为从 triage-stage 出发（取代原 PMO 初步分析）
  - **I. CHANGELOG + 版本号 bump**：SKILL.md frontmatter 7.3.10+P0-25 → 7.3.10+P0-26；stages/init-stage.md L111 同步
- 风险控制：
  - 红线数保持 15 条（无升格 / 无新增）
  - Triage Stage 幂等不持久化 —— 新对话恢复无歧义（重跑即可）
  - INIT.md 文件迁移用 git mv，引用同步全文 grep + replace（活引用 100% 清零，历史 docs 保留）
  - roles/pmo.md 不删除原段，只加反向引用 —— 避免破坏其他文件对 pmo.md 段的引用
  - SKILL.md 三层级标注让概念体系一眼可见，避免新用户混淆
- 影响面：
  - 新建文件：1 个（stages/triage-stage.md）
  - 物理重命名：1 个（INIT.md → stages/init-stage.md）
  - 引用迁移：10 个文件（活引用全清）
  - 反向引用增加：4 段（roles/pmo.md）+ 1 段（FLOWS.md）+ 1 段（RULES.md）
  - 索引更新：SKILL.md（加新 Stage 行 + 三层级章节）+ rules/flow-transitions.md（加新章节）
- 预期效果：
  - **架构一致性**：所有 PMO 行为都走 Stage 契约（三层级覆盖完整）
  - **可审计 / 可恢复**：triage 输出标准化，新对话重跑幂等，结果一致
  - **概念清晰**：Stage 分会话级 / 流程级 / Feature 级，三层职责清晰
  - **token 友好**：triage 不持久化降低 IO 写入开销
- 待跟进（非 P0-26 范围）：
  - triage-stage 在实际跑 Feature 时的 token 占用观察（如超过预期可优化为按需加载 KNOWLEDGE 章节）
  - 若未来加 Gemini 等候选外部模型时，triage Step 4 的 detect 脚本扩展（已预留）
  - INIT.md 历史引用在 docs/CHANGELOG.md / docs/OPTIMIZATION-PLAN.md 中保留 —— 这是预期行为（历史记录），不动

---

## v7.3.10 + P0-25

> v7.3.10+P0-25 Build 硬门禁补丁：用户实战中遇到 CI 失败"npm run build 失败"——RD 自查时单测都跑通了但 build 没跑过，CI 成了第一道发现机制。诊断后发现规范半残：standards/common.md 自查报告**字段层**已要求填 build 命令 + 结果（soft requirement），但 stages/dev-stage.md Output Contract 的**机器校验硬门禁**只到 typecheck，没有 build。同时暴露 worktree 场景下 lazy install (P0-3) 的 hole——单测 deps 装了但 build 工具链 deps 未装，build 在 worktree 内根本跑不起来。本次把 build 升格为硬门禁，并补充 worktree 场景的 deps 处理选项。

### P0-25：Build 升格硬门禁 + worktree deps 处理

- 触发：用户实战 case「CI 应可重新跑通，next build 必须能在 RD 自查阶段跑通，不能依赖 CI 兜底。后续 Feature 若 worktree 缺 deps，应至少符号链接 / 安装一份后跑 next build 而非只跑单测」 → 用户「A + B + D」选定
- 设计决策：
  - 不修改 P0-3 lazy install 模型（仍然懒装，避免回退冷启时间优化）
  - 把 build 从"自查报告字段"升格为"Dev Stage Output Contract 机器校验硬门禁"——build 失败 = Dev Stage 不能完成 = PMO 拦下来不让进 Review
  - 纯库 / 纯后端 / Python 应用允许显式标注"无 build 步骤"，避免误中
  - worktree deps 处理给 3 种选项（按优先级 install > 软链 > 写 KNOWLEDGE），不强制其中一种——视项目情况
- 处理（2 处改造）：
  - **A. `stages/dev-stage.md` Output Contract 机器校验硬门禁**：
    - 在 typecheck 行后加一条 `[ ] Build：npm run build / next build / go build / cargo build 等 exit 0`
    - 加一段 callout：🔴 Build 必须 RD 阶段跑通，禁止依赖 CI 兜底；🟡 worktree lazy install hole 的处理指引指向 standards/common.md
  - **B. `standards/common.md` 验证证据段加 worktree 提示**：
    - 在「构建结果」行下加 🔴 升格硬门禁声明
    - 加 🟡 worktree 场景特别提示：症状（单测可跑 build 失败）+ 原因（lazy install + worktree 不同步）+ 3 种处理选项（npm install / 软链 / 写 KNOWLEDGE Gotcha）
    - 自查结论改为"含 build 通过"
- 风险控制：
  - 纯后端 / 纯 Python 项目允许"无 build 步骤"显式标注，不会误伤
  - worktree 场景给选项不强制——保留 RD 判断空间
- 影响面：
  - 红线数：15 条（保持，未升格新红线，build 是 Dev Stage Output Contract 的机器校验项升格）
  - 改动文件：2 个（stages/dev-stage.md / standards/common.md）
  - 元数据：SKILL.md frontmatter v7.3.10+P0-24 → v7.3.10+P0-25；INIT.md L111 同步
- 待跟进（非 P0-25 范围）：
  - PMO L2 预检加 build deps 检查（暂列 P0-25-延后，等真有 case 再做）
  - 复杂 monorepo workspace 场景下 worktree node_modules 软链的具体踩坑（视实战补充）

---

## v7.3.10 + P0-24

> v7.3.10+P0-24 外部模型 (External Model) 抽象化重构：将 v7.3.9+P0-13 引入的"Codex 交叉评审"语义升级为通用的"外部模型交叉评审"概念。规范层不再硬编码"宿主→外部模型"对应表，改为 PMO 在每次 Feature 流程的初步分析阶段调用 `templates/detect-external-model.py` 探测脚本，按当时环境（CLI 安装情况 + 同源约束）决定可用候选 + 用户决策。配套实现：claude-agents/ 目录建立（Codex CLI 主对话调用 Claude CLI 子进程的 shell 调用规范），state.json 字段 codex_cross_review → external_cross_review（旧字段 fallback 兼容），STATUS-LINE 加 [Ext: X] 徽章，Review Stage 入口显式宣告外部模型实例。改造后 Codex CLI 主对话宿主下可用 Claude 作为外部模型（之前用 Codex 等于"自审"），Claude Code 主对话宿主下保持 Codex 为外部模型不变。

### P0-24：外部模型抽象化 + PMO 运行时探测

- 触发：用户「我们是否把 codex 评审 review 语义改为 外部模型交叉评审，外部模型由当前宿主环境定义」 → 进一步细化「PMO 运行时探测，使用固定 python 脚本探测，简单直接，目前仅支持 codex 和 claude」 → 用户「确认」开干
- 设计决策：
  - 规范层只定义"候选清单 + 同源约束 + 调用规范 + 失败降级"，**不写宿主对应表**——具体实例由 PMO 运行时决定
  - 探测脚本只检测 CLI 安装 + 同源约束，**不查 API key/OAuth**（避免 OAuth 已登录但 env var 未设的用户被误标"不可用"）
  - 失败检测延后到运行时：dispatch 时调用失败 → state.concerns WARN → 自动降级单视角 review
  - 红线数量保持 15 条（P0-24 的"E1 异质性 / E2 PMO 运行时探测 / E3 失败优雅降级"三规则纳入 standards/external-model.md，不升格红线）
- 处理（新建 5 文件 + 9 处改造）：
  - **A. 新建 `templates/detect-external-model.py`**（~130 行）：
    - CANDIDATES = [codex, claude]，未来加 Gemini 只需加一行
    - 探测主对话宿主（基于 .claude/ / .codex/ / .agents/ 目录标记）
    - 探测候选 CLI 是否在 PATH（shutil.which）
    - 应用同源约束（外部模型 ≠ 主对话同源）
    - 输出 JSON 到 stdout：host_main_model / candidates_pool / available_external / recommendation
  - **B. 新建 `standards/external-model.md`**（~190 行）：
    - 顶部三条硬规则（E1 异质性 / E2 PMO 运行时探测 / E3 失败优雅降级）
    - §一：外部模型概念（异质模型 vs 同模型角色切换的本质差异）
    - §二：候选模型清单（Codex / Claude）
    - §三 E1：同源约束 + 渲染示例
    - §四 E2：PMO 运行时探测（脚本调用 + 输出渲染 + 设计边界说明）
    - §五：调用规范（dispatch 文件协议 + 调用入口对应表 + 产物格式 + state.json 字段）
    - §六 E3：失败降级流程
    - §七：与其他规范的协作关系
    - §八：本规范不覆盖的范围
  - **C. 新建 `claude-agents/` 目录**（3 个文件）：
    - README.md：宿主对应、前置条件、调用方式总览、与 codex-agents/ 的对照
    - reviewer.md：外部 review 的 prompt 模板（PRD / Blueprint / 代码三场景共用）
    - invoke.md：主对话 shell 调用 claude CLI 的命令范本 + stderr 捕获 + 降级处理
  - **D. SKILL.md + STANDARDS.md 索引更新**：加 standards/external-model.md 行 + standards/external-model.md 在 STANDARDS.md
  - **E. INIT.md 简化**：删除原"Codex CLI 检测"段（line 314-319），改为"外部模型探测延后说明"——明确外部模型探测延后到 PMO 在 Feature 流程的初步分析阶段做，INIT 阶段只检测主对话宿主
  - **F. roles/pmo.md 重写「外部模型交叉评审开关决策」段**（替换原"Codex 交叉评审开关决策"段）：
    - Step 1: PMO 调用 detect-external-model.py
    - Step 2: PMO 渲染「🌐 外部模型探测」段
    - Step 3: PMO 建议逻辑（沿用 P0-13 的开/关信号判断）
    - Step 4: PMO 决策项呈现（有候选时 3 选 1，无候选时直接跳过）
    - Step 5: 用户选择 → state.json 写入新字段 schema
    - Step 6: 调用失败的运行时降级（E3 规则）
    - 兼容性：旧 codex_cross_review 字段 fallback 读取
    - 9 条硬规则（含同源禁用 + 静默降级禁止）
  - **G. templates/feature-state.json 字段重命名 + 新字段**：
    - codex_cross_review → external_cross_review
    - 新增字段：model / host_main_model / host_detection_at / available_external_clis / reviewer_dispatches[]
    - 保留 _p0_24_rename_note 注释说明旧字段语义
  - **H. templates/codex-cross-review.md → templates/external-cross-review.md 重命名 + 重写**：
    - 头部加 P0-24 重命名说明 + 指向 standards/external-model.md
    - §一-§九 全文措辞由"Codex 交叉评审"→"外部模型交叉评审"
    - Output Schema 改为 perspective: external-{model}（external-codex / external-claude）
    - PMO 整合流程 Step 2 "Dispatch Codex" → "Dispatch 外部模型"（按 model 选择 codex / claude CLI）
    - §六 降级策略与 standards/external-model.md §六 E3 对齐
    - 加 R9 红线（同源禁用）
  - **I. 8 个 stage spec + FLOWS.md + review-log.jsonl 字面值审查**：
    - codex_cross_review → external_cross_review（字段名）
    - templates/codex-cross-review.md → templates/external-cross-review.md（路径）
    - "Codex 交叉评审" → "外部模型交叉评审"（概念名）
    - prd-codex-review.md / blueprint-codex-review.md → external-cross-review/prd-{model}.md / blueprint-{model}.md（产物路径）
    - review-codex.md → review-external.md（Review Stage 外部产物）
    - "Codex 已关闭" → "外部模型评审已关闭"
    - review-log.jsonl stage 枚举：plan-codex-review / blueprint-codex-review / review-codex → plan-external-review / blueprint-external-review / review-external
  - **J. STATUS-LINE.md 加 [🌐 Ext: X] 徽章**：
    - 第一行格式：🔄 Teamwork 模式 [⚡ AUTO] [🌐 Ext: {model}] | ...
    - 触发条件：state.external_cross_review.enabled=true 时显示，model 取自 state 字段
    - 兼容旧字段：fallback 显示 "Ext: codex"
  - **K. stages/review-stage.md 入口宣告外部模型实例**：在「入口 Read 顺序」段下方加一行 PMO 在读 state.json 后输出"🌐 外部模型: {model}"
  - **L. CHANGELOG + 版本号 bump**：SKILL.md frontmatter 7.3.10+P0-23 → 7.3.10+P0-24；INIT.md L111 同步
- 风险控制：
  - state.json 字段重命名采用 fallback 兼容（PMO 读取时优先读新字段，缺失时读旧字段并视为 model=codex）—— 旧 Feature 不需要迁移
  - claude-agents/ 真实工程（不是占位骨架），但失败降级路径完备：调用失败 → state.concerns WARN → 单视角 review，不阻塞流程
  - 同源约束在脚本层 + PMO 决策层双重保护：脚本输出 usable_as_external=false，PMO 渲染时不出该选项
  - 测试路径：用户在 Codex CLI 环境跑 Teamwork → 启用外部模型交叉评审 → 验证 claude CLI 子进程被调起 → 验证 review 产物正确落盘
- 影响面：
  - 红线数：15 条（保持，未升格）
  - 新建文件：5 个（detect-external-model.py / external-model.md / claude-agents/README.md / claude-agents/reviewer.md / claude-agents/invoke.md）
  - 重命名：1 个（codex-cross-review.md → external-cross-review.md）
  - 重大改动文件：roles/pmo.md（重写一段约 130 行）/ templates/feature-state.json（字段重构）
  - 字面值改动：8 个 stage spec + FLOWS.md + review-log.jsonl + STATUS-LINE.md
- 待跟进（非 P0-24 范围）：
  - claude-agents/ 在 Codex CLI 实际跑通的端到端测试（用户自测）
  - localconfig external_model 字段（用户覆盖默认推荐）
  - 未来加 Gemini 候选时的扩展（detect-external-model.py 的 CANDIDATES 加一行 + claude-agents/ 对称建立 gemini-agents/）

---

## v7.3.10 + P0-23

> v7.3.10+P0-23 Prompt Cache 友好改造（R1+R2+R3 子集）：teamwork 在 Claude Code / Codex 等宿主下跑时，宿主会自动做隐式 prompt caching（前缀命中则按 ~10% 价格 + ~5x 速度计费）；teamwork 原先的 prompt 组织方式未优化命中率——动态内容（日期/git/state.json）散落在稳定层中、Stage 入口 Read 顺序不固定、state.json 中段反复读写。按用户「针对 teamwork prompt caching 怎么改造」→ R1-R7 改造清单 → 用户「先落 R1+R2+R3」定稿：R1 动态内容后置（稳定层禁止字面值时间/git/身份/状态/环境）+ R2 Stage 入口 Read 顺序固定化（roles → templates → Feature 产物 → state.json 最后）+ R3 state.json 访问 ≤ 5 次/Stage（入口 1R + 出口 1R + 1W，中段 0，豁免仅评审循环/Subagent 整合/用户追加）。按 Anthropic 公开数据，Feature 输入 ≥50K token 场景命中率 20% → 80% 改造收益 ≈ 成本下降 2-3 倍。

### P0-23：Prompt Cache 友好 R1+R2+R3 落地

- 触发：用户「针对 teamwork prompt caching 怎么改造」→ 分层分析 L0/L1/L2/L3 + 3 大 cache miss 源（动态前缀/state.json 穿透/Read 顺序不固定）→ R1-R7 改造清单 → 用户「先落 R1+R2+R3」
- 理论依据：Anthropic 公开文档（Claude Code / Codex 宿主自动 prompt caching，前缀稳定 ≥ 1024 token + 字节一致时命中 → input token ~10% 计费 + ~5x 解码速度）
- 设计决策：
  - 只做 R1+R2+R3（显式高 ROI），R4-R7（多指令文件合并/subagent 组装/token 峰值瘦身/审计自动化）暂缓 → 避免过度改造
  - 不触碰 Anthropic API `cache_control` 显式 breakpoint（宿主接管层级，skill 不干预）
  - 红线数量保持 15 条（P0-23 的 3 条性能规则纳入 standards/prompt-cache.md，不升格红线——因违反不产生流程偏离，仅 cache miss，记入 state.concerns 即可）
- 处理（新建 1 文件 + 12 处改造）：
  - **A. 新建 `standards/prompt-cache.md`**（~170 行）：
    - 顶部红线定位 + 三条硬规则（R1/R2/R3）+ ROI 锚点（Feature 场景 50K token 20%→80% 改造 ≈ 2-3x 成本下降）
    - §一：4 层模型（L0 框架 / L1 项目 / L2 Feature / L3 动态）
    - §二 R1：7 类禁止字面值（时间/git/身份/状态/环境/会话）+ 错误 vs 正确表达表 + 允许承载位置（STATUS-LINE / PMO 输出块 / tool call 结果 / Subagent dispatch）
    - §三 R2：通用入口 Read 顺序（roles → templates → Feature 产物 → state.json 最后），每个 stage spec 补「入口 Read 顺序」段
    - §四 R3：state.json 访问次数表（入口 1R + 中段 0 + 出口 1R + 1W）+ 3 类豁免（评审循环 ≤3 轮 / Subagent 整合 / 用户追加）+ 量化上限 ≤5 次常规 / ≤8 次极端
    - §五：审计清单（grep 时间字面值 / stage spec 入口段存在 / PMO state.json 约束 / 中段禁写豁免标注）
    - §六：与 SKILL/RULES/common/INIT 的协作关系
    - §七：明确不覆盖（API-level cache_control / 跨 session 持久化 / subagent prompt 组装 / token 峰值瘦身）
  - **B. `SKILL.md` 文档表新增 prompt-cache.md 行**（责任人：PMO 每 Stage 入口引用约束）
  - **C. `RULES.md` 拆分文件索引新增 prompt-cache.md 行**（时机：PMO 每 Stage 入口 + 审计自查时）
  - **D. 10 个 stage spec 在 Input Contract 与 Process Contract 之间新增「入口 Read 顺序（v7.3.10+P0-23 固定）」段**：
    - plan / blueprint / blueprint-lite / ui-design / panorama-design / dev / review / test / browser-e2e / ship
    - 每段含 4 步固定顺序（角色 → 模板 → Feature 产物 → state.json 最后）+ R3 访问次数约束说明
    - 各 Stage 按特性标注豁免情形（Blueprint/Review 3 轮修复循环；Dev/Test 多次 Subagent dispatch 整合）
  - **E. `roles/pmo.md` §state.json 状态机维护规范 新增子段 state.json 访问模式约束**（紧接「Stage 结束必做」后，「state.json 与现有文件的关系」前）：
    - 4 行访问次数表（Stage 入口 1R / 中段 0 / Stage 出口 1R + 1W）
    - 3 类豁免条件（评审循环/Subagent 整合/用户追加）+ 量化上限 ≤5/≤8
    - 4 条反模式（每 Step 开头 Read / 每字段 Write / 保险再 Read / 中段兜底 Read）
  - **F. `INIT.md` CLAUDE.md 注入段审计**：逐行审计 L170-207 → 结果**清洁**（无日期/git/身份/state 值动态字面值）；版本号类型 `v7.3.10+P0-20/P0-15` 属稳定引用（符合 R1 §2.2）；保留不变
  - **G. 版本号 bump**：SKILL.md frontmatter 7.3.10+P0-22 → 7.3.10+P0-23；INIT.md L111 同步
- 影响：
  - 典型 Feature 场景（50K token 输入）命中率从 ~20% 提升到预期 ~70-80%（实测需生产数据验证）
  - 每 Stage 入口 Read 顺序统一 → 跨 Stage 切换时的前缀碎片化消除
  - state.json 中段禁读写 → 前缀稳定段结束点清晰化，下游 L3 动态内容明确后置
  - 红线条数保持 15 条（P0-23 未增红线，仅新增性能规则 standards/）
  - 无迁移成本（纯注解+约束，不改现有文件语义）
  - 改造范围：1 新文件 + 12 处编辑（3 索引文件 + 10 stage + 1 pmo + 1 version）
- 风险控制：
  - ⚠️ 违反 R3（中段读写 state.json）不触发红线机制 → 仅记 state.concerns（cache miss 自然反映在延迟/成本，不做硬阻塞）
  - ⚠️ 用户追加需求导致中段 Read/Write 豁免合规（必须先走 PMO 分析 + 用户确认）
  - ⚠️ Subagent dispatch 整合写 state.json 豁免必须每次 dispatch ≤ 1 次（否则打破 prompt 前缀一致性）
- 待观察 / 后续可能动作：
  - R4（多指令文件 CLAUDE.md + AGENTS.md 合并）— 若后续发现跨宿主启动命中率仍低，考虑两个文件合并
  - R5（subagent dispatch prompt 组装优化）— 等 dispatch.md 下次 revamp 时同步
  - R6（token 峰值瘦身）— 独立优化路径，与命中率无关
  - R7（审计自动化 - grep 规则跑 CI）— 待 skill-creator evals 建成后接入

---

## v7.3.10 + P0-22

> v7.3.10+P0-22 KNOWLEDGE.md 收敛 + retros 索引拆离：P0-21 落地混合 ADR 后，用户追问「KNOWLEDGE.md 还有必要么，是否需要精简」——审视当前模板确认：它把"架构决策（为什么选某方案）"明确写在🔧技术经验首项，与新的 ADR 体系直接抢地盘；把复盘索引和经验索引混塞；PMO 知识提取仅靠软提示易失活。按**方案 A**（收敛保留，非删除）落：KNOWLEDGE.md 收敛到 3 类纯"事实型"内容——⚠️ Gotchas（陷阱）/ 📋 Conventions（团队约定）/ 🎨 Preferences（用户偏好），明确"决策走 ADR / 复盘走 retros / 通用规范走 standards"的边界；复盘索引剥离到独立 `templates/retros-index.md`；PMO 新增📚 KNOWLEDGE 扫描段（与 ADR 扫描对称）+ 7 条硬触发时机表（从软提示升硬时机）；体量上限 300 行强制归档。

### P0-22：KNOWLEDGE.md 3 类收敛 + 硬触发时机 + 复盘索引剥离

- 触发：用户「我们的 KNOWLEDGE.md 还有必要么，是否需要精简下」→ 分析当前模板 3 大冗余问题 → 3 方案（A 收敛保留 / B 激进拆散 / C 最小改动）→ 用户「按 A 落地」
- 根因分析：
  - ADR 体系（P0-21）落地后，KNOWLEDGE.md 仍在🔧技术经验段收录"架构决策（为什么选某方案）"，和 ADR 直接抢领域 → 同一决策可能双写/漂移
  - KNOWLEDGE.md 同时承担「经验索引」+「复盘索引」两种不同时间语义的信息（主题复用 vs 时间回顾）→ 文件职责不纯
  - 当前 PMO 知识提取靠软提示（"功能完成时应基于以下维度总结"），没有硬时机约束 → 实际运行下绝大多数 Feature 完成时不会真提取 → 慢慢失活
  - 模板分类过细（8 大类 20+ 小项），AI 实际写入时犹豫"这条算技术还是流程"，同一条知识被写到多个位置
  - 无体量上限 → 长期容易变成"什么都往里塞"的垃圾桶
- 处理（模板重写 + 新模板 + PMO 专属段新增 + 3 处活引用 + 索引 2 处）：
  - **A. `templates/knowledge.md` 全文重写**：
    - 顶部新增「🔴 边界声明」表：明确架构决策→ADR / 通用规范→standards / 复盘→retros / 项目特有事实→本文件
    - 正文收敛到 3 类表格：⚠️ Gotchas (GO-NNN) / 📋 Conventions (CV-NNN) / 🎨 Preferences (PR-NNN)，每条都有 ID + 主题 + 来源 Feature + 时间
    - 按主题索引段（db / api / auth / frontend / UI / 交互 / ...）
    - 归档段（archived）：过期条目加 archived 标记保留备查
    - 🔴 体量上限 300 行（超出必选一种处理：升格 ADR / 子项目级分拆 / 归档）
    - 🔴 每条 ≤ 2 行（超出说明不够"事实"，可能是决策伪装）
    - ID 编号连续不复用（归档保留原 ID）
  - **B. `templates/retros-index.md` 新增**（~50 行）：复盘索引模板
    - 时间线段（最近在前）+ 按流程类型索引 + 偏差警报段（Stage 连续偏差 ≥ 3 次触发流程优化 proposal）
    - 位置：`{子项目}/docs/retros/INDEX.md`（和 `docs/adr/INDEX.md` 对称）
    - 维护约定：每次产单条复盘时同步 INDEX；体量上限 200 行
  - **C. `roles/pmo.md` 新增 §📚 KNOWLEDGE 扫描 + 写入时机**（紧接 ADR 扫描段后）：
    - 定位声明：3 类收录 + 4 类排除（决策/通用规范/复盘/临时笔记）
    - **A. preflight 扫描**（读操作）：4 步操作 + 输出格式 + 3 条硬规则（必出行 / ≤300 行 / 只列清单不下结论）
    - **B. 写入硬时机表**（7 条触发场景 × 类别 × 写入方 × PMO 提示措辞）：
      1. Bug 修复完成 → Gotcha → RD
      2. Dev Stage 调试 ≥30min 或 retry ≥2 → Gotcha → RD
      3. Review 发现 workaround → Gotcha → 架构师
      4. Review 发现自发约定 → Convention → 架构师
      5. Plan 用户强调跨 Feature 要求 → Convention → PM
      6. PM 验收用户明确偏好 → Preference → PM
      7. UI Design 用户选项陈述理由 → Preference → Designer
    - 🔴 PMO 显式提示即完成其职责；对应角色未写入 → state.concerns 记 skip_reason
    - 🟢 PMO 本身不直接写入 KNOWLEDGE（除流程型 Convention 外）
    - 反模式表 6 行（遗漏扫描行 / 读全文 / 决策写入 Gotcha / 通用规范写入 Convention / Bug 后漏提示 / 超体量继续追加）
  - **D. `FLOWS.md` 三种 PMO 初步分析格式**均新增「📚 相关项目事实（KNOWLEDGE）」行（单子项目 Feature / 工作区级 Feature Planning / 敏捷需求）
  - **E. 索引同步**：
    - `TEMPLATES.md`：knowledge.md 描述更新 + 新增 retros-index.md 行
    - `templates/README.md`：knowledge.md 描述 + 加载时机细化；新增 retros-index.md 行
- 版本号：
  - SKILL.md frontmatter：`7.3.10+P0-21` → `7.3.10+P0-22`
  - INIT.md Step 1.2-a 注释同步
- 设计要点：
  - **收敛而非删除**：KNOWLEDGE 有独立价值（项目特有事实 + 偏好）不能丢，但要和 ADR 清晰分工
  - **3 类硬隔离**：Gotchas / Conventions / Preferences 三段完全独立，有 ID 段 + 主题索引 → 不再纠结"这条写哪"
  - **决策 vs 事实的边界**：备选项 ≥ 2 → ADR；被动发现的客观约束 → KNOWLEDGE Gotcha；这是最关键的分流规则
  - **硬时机取代软提示**：7 条写入时机绑定到 Stage 完成报告，PMO 提示是硬职责；未提示 = 流程偏离
  - **体量上限 = 扫描上限**：300 行一口气读完，不用分页；超出必归档 → 文件不会膨胀
  - **复盘独立索引**：时间线语义（retros）和主题语义（KNOWLEDGE）彻底分离，和 ADR-INDEX 形成"3 套索引"对称结构
  - **零新红线**：总红线数仍 15 条；所有约束落在 PMO 专属规范 + 模板硬规则里
  - **与 ADR 的协作**：ADR 记"为什么选了这个"，KNOWLEDGE Gotcha 记"选了之后踩了什么坑"——两者互补
- 保留未做（后续可能 P0/P1）：
  - KNOWLEDGE.md 自动校验脚本（verify-knowledge.py）：ID 连续性、主题索引完整性、体量上限 → 当前手工
  - 跨项目 KNOWLEDGE 聚合视图：多子项目模式下全局概览，当前各子项目独立维护
  - 归档条目的定期回顾机制：archived 条目是否真的不适用，需要多版本验证
  - Bug 修复流程 Stage spec 是否在完成报告明确要求"PMO 提示写 Gotcha"的声明格式 → 当前靠 roles/pmo.md 硬时机表约束，未在 bug-stage 单独落硬规则
  - Review Stage spec 是否在 findings 分类里新增"trigger_knowledge_write"标记 → 当前靠架构师读 roles/pmo.md 硬时机表自觉执行

## v7.3.10 + P0-21

> v7.3.10+P0-21 混合 ADR（Architecture Decision Record）体系：用户追问"TECH.md 接近但不是 ADR 语义（Context / Decision Drivers / Alternatives ≥ 2 / Consequences），teamwork 需要补充完善么"——分析后确认：TECH.md 混合了"怎么做（实现计划）"和"为什么这么选（决策记录）"两类信息，当跨 Feature 引用决策时（"用户系统当初选 PostgreSQL 是为了什么"）没有稳定引用点；但强制每 Feature 产 ADR 会把轻量流程拖垮。按**方案 C 混合 ADR**落：ADR 作为可选产物，由架构师在 Blueprint Stage 用"3 问触发器"判断是否抽取（影响未来 ≥1 Feature / 反悔成本高 / 多合理方案非显然 —— 三问全 yes 才产）。TECH.md 保持不变是实现计划的主体，决策则被抽离到独立 `{子项目}/docs/adr/NNNN-{slug}.md`，PMO 初步分析阶段扫描 INDEX.md 让未来 Feature 自动感知既有决策约束——这是 ADR 对 AI 自引用最关键的价值。

### P0-21：混合 ADR 体系（opt-in 决策记录 + 3 问触发器 + PMO 索引扫描）

- 触发：用户「文档即代码（ADR / RFC）：TECH.md 接近但不是 ADR 语义（ADR 要求决策记录 + 备选项 + 后果）这个 teamwork 需要补充完善么」→ 评估三方案 A（TECH.md 内嵌）/ B（全面 ADR）/ C（混合 opt-in）→ 用户「按方案 C 落」
- 根因分析：
  - TECH.md 实际承担两类信息：「实现计划」（文件清单 + 改动要点 + 测试策略）+「技术决策」（为什么选 A 不选 B）——两者耦合导致跨 Feature 引用决策时没有稳定锚点
  - 未来 Feature 的 AI 想知道"本项目为什么当初选 PostgreSQL"只能全文搜索所有历史 TECH.md，没有索引也没有按主题聚合
  - 全面强制 ADR（方案 B）会让小 Feature 额外付 ~50-100 行 ADR 成本 → 流程不可持续；完全不加（方案 A）无法解决跨 Feature 决策引用问题
  - 合理的解法：opt-in + 触发器 + 索引聚合 → 只有真正影响未来 / 反悔成本高 / 多方案非显然的决策才升格 ADR
- 处理（2 个新模板 + 4 处活引用 + 1 条工作流）：
  - **A. 新增 `templates/adr.md`**（~120 行）：完整 ADR 模板
    - frontmatter 7 字段：`id` / `title` / `status`(proposed|accepted|deprecated|superseded-by-ADR-NNNN) / `date` / `tags[]` / `triggered_by`(触发 Feature) / `supersedes[]`
    - 正文 7 段：背景 / 决策驱动因素 / 备选项（≥ 2） / 决策 / 后果（✅ 正面 / ⚠️ 负面 / 🔗 长期 / ❓ 未解决）/ 相关 / 修订历史
    - 硬规则：ID 连续编号永不复用、备选项 < 2 走 TECH.md 不走 ADR、每次变更同步 INDEX.md、superseded 时双向关联、体量 50-150 行
  - **B. 新增 `templates/adr-index.md`**（~65 行）：ADR 索引模板
    - 三段：活跃决策（Accepted） / 提案中（Proposed） / 已废弃（Deprecated / Superseded）
    - 按主题索引：db / api / auth / frontend / backend / deploy / observability / security
    - 位置：`{子项目}/docs/adr/INDEX.md`（每子项目一份）
    - 体量上限 200 行，超出说明需分片
  - **C. `stages/blueprint-stage.md` §架构师方案评审**（Step 4 增子步 + Step 6 新增 + 硬规则 +2 + Output Contract +2 行 + 判据 +4 项）：
    - **Step 4.1 ADR 抽取判断**：架构师必须对本 Feature 每条技术决策应用"3 问触发器"——
      1. 这个决策会影响 ≥ 1 个未来 Feature 吗？
      2. 反悔成本很高吗（需要大规模改动）？
      3. 存在多个合理方案，选哪个不是显然的吗？
      - 三问全 yes → 抽取为独立 ADR；任一 no → 决策留在 TECH.md 即可
      - 🔴 判断本身（包括"不产 ADR 的理由"）必须在 TECH-REVIEW.md 留痕
    - **Step 6 ADR 抽取流程**（Step 5 Codex 之后）：前置（TECH-REVIEW 已记 ADR 判断）/ 架构师 4 步职责（分配 ID / 按模板创建文件 / 填 frontmatter + 正文 / 更新 INDEX.md）/ PMO 流程整合（列摘要 + ⏸️ 用户确认→ status proposed→accepted + 多轮讨论不受 ≤3 轮限制）/ 产出清单 / 体量控制 / 🔴 TECH.md 去重（决策 rationale 迁移后 TECH.md 只留 ADR-ID 引用）
    - **过程硬规则 +2**：🔴 ADR 抽取判断不可跳过（跳过 = 流程偏离） + 🔴 ADR 格式合规（严格按 adr.md 模板、备选项 ≥ 2、同步 INDEX.md）
    - **Output Contract +2 行**：`docs/adr/NNNN-{slug}.md`（🟡 仅触发时必需）+ `docs/adr/INDEX.md`（🟡 首次产 ADR 时创建/每次变更时更新）
    - **机器可校验条件 +5 项**（触发时生效）：frontmatter 5 字段全非空、备选项 ≥ 2、体量 50-150 行、INDEX.md 已同步、文件名 NNNN 连续不复用
    - **Done 判据 +1**：ADR 触发时 status=accepted + INDEX.md 同步 + TECH.md 去重
  - **D. `roles/pmo.md` §📜 ADR 索引扫描**（新段，紧接 Codex 决策段后）：
    - 触发：PMO 初步分析任何 Feature / 敏捷需求 / Feature Planning 时必须扫描
    - 目的：让 PMO 在需求分析阶段就提醒"本 Feature 受哪些历史决策约束"——这是 ADR 对 AI 自引用最关键的价值（不扫描 = AI 重复发明或违反既有决策）
    - 4 步操作：定位 INDEX.md → 读前 200 行 → 按主题 + 涉及模块交叉扫描活跃决策 → 注入初步分析输出
    - 硬规则 4 条：必须显式输出「📜 相关 ADR」行（即使为空）+ 只读 INDEX.md 不读单 ADR 全文 + PMO 不做决策抽取判断（留给架构师）+ 无 ADR 记录时显式声明
    - 反模式表 +3 行：遗漏行 / 读全部 ADR / 替架构师下结论
  - **E. `FLOWS.md` §PMO 初步分析输出格式**：三种格式（单子项目 Feature / 工作区级 Feature Planning / 敏捷需求）均新增「📜 相关 ADR」行；§PMO 初步分析流程步骤描述 Blueprint Stage 改述为"含 💡 ADR 3 问触发器判断"
- 版本号：
  - SKILL.md frontmatter：`7.3.10+P0-20-B` → `7.3.10+P0-21`
  - INIT.md Step 1.2-a 注释同步
- 设计要点：
  - **opt-in 而非强制**：3 问触发器把 ADR 抽取成本精确定位到"跨 Feature 影响 + 反悔成本高 + 非显然"三者同时满足的决策——绝大多数 Feature 一个 ADR 都不用产，流程开销几乎为零
  - **零新红线**：保持总红线数 15 条不变；ADR 约束全部落在 Blueprint Stage 规范 + PMO 专属规范里（而不是升格为全局红线）
  - **PMO 只扫描不判断**：PMO 负责"历史扫描 + 注入"，架构师负责"抽取判断"——两个职责清晰分工，避免 PMO 越权替架构师决策
  - **INDEX.md 体量可控**：200 行上限 + 只读索引不读全文 → 即使项目积累 100 个 ADR，PMO 初步分析阶段的 token 开销也可控
  - **AI 自引用价值最大化**：通过「主题索引 + PMO 每次扫描」让未来 AI Feature 自动感知既有决策约束——这是 ADR 对 LLM 自主开发最关键的贡献
  - **与 TECH.md 去重**：决策 rationale + 备选项 + 后果 → 迁移到 ADR；TECH.md 只留 ADR-ID 引用一句话——避免双份真相
  - **备选项 ≥ 2 的硬门槛**：单方案走 TECH.md 不走 ADR，防止 ADR 被用作"凡决策必记"的形式主义产物
- 保留未做（后续可能 P0/P1）：
  - ADR 状态流转（superseded-by-* 双向关联）的自动化校验脚本：当前靠架构师手工，未来可加 python3 verify-adr.py
  - ADR 搜索/聚合 CLI：INDEX.md 体量够用时搜索基本靠人眼，未来项目 ADR 数量大时再引入
  - Micro 流程是否扫描 ADR：Micro 场景改动极小、准入条件已排除架构变更，当前不加扫描；若未来发现 Micro 漂到边缘决策再补
  - RFC（Request for Comments）体系：ADR 记录「已做的决策」，RFC 用于「待讨论的提案」——当前 TEAMWORK 不引入 RFC，团队内部讨论走 PRD / PL-PM 讨论已足够；未来多 AI 协作场景可能需要

## v7.3.10 + P0-20-B

> v7.3.10+P0-20-B 反漂移双补丁：P0-20 把 Micro 流程里"谁写代码"的语义统一为"主对话内 PMO→RD 身份切换"，但用户追问"身份切换语义模型现在能理解吗"——深究后确认：LLM 可以 parse 这个短语，但"身份切换"不是原子操作（没有进程/状态切换、没有 context 隔离），让切换真正生效靠的是 P0-16 补丁留下的四个仪式（切换前必读 + cite + 改后自查 + STATUS-LINE 显示角色）。仪式全在改动**前后**，改动**过程中**存在两个漂移口：(1) 跨多 turn 悄悄漂回 PMO 口吻；(2) 用户中途追加改动时 RD 身份顺手接单导致身份蠕变。本次补两条轻量规则堵漏。

### P0-20-B：反漂移双补丁（第一人称锚点 + 追加改动回退规则）

- 触发：用户「身份切换语义代表什么现在模型能理解么」→ 回答"语义能懂但靠仪式落地"+ 识别两个漂移口 → 用户"按建议"全做
- 根因分析：
  - 身份切换在 LLM 上是 prompt-level convention，不是 runtime state 切换 → 仅靠"称呼改变"不足以持续约束行为
  - P0-20 保留的 P0-16 四仪式（必读 + cite + 自查 + 状态行）全是**前后**锚点，没有**过程中**锚点
  - 漂移场景 1：Micro 改动跨多 turn 时，模型可能在中间某轮悄悄恢复 PMO 口吻（产出不一定错，但审计痕迹乱）
  - 漂移场景 2：用户中途说"顺便再改一下 X"，RD 身份顺手接单 → 没有 PMO 的 Micro 准入重评 → 身份蠕变、Micro 越扩越大
- 处理（两条规则 + 三处活引用 + 事后审计补两项）：
  - **A. 第一人称锚点**：身份切换后阶段摘要**首句必须以「作为 RD，……」开头**。LLM 在开头强制自称特定角色时，后续 token 生成会显著向该角色的语言分布靠拢——这是反漂移的最小开销锚。
  - **B. 追加改动回退规则**：RD 身份执行过程中若用户追加新改动请求 → 必须跳回 PMO 身份重新做 Micro 准入：
    - 通过 5 项准入 + 仍在白名单内 → PMO 输出增量分析 + ⏸️ 等用户确认 → 再切回 RD 执行
    - 越出白名单 → PMO 输出升级原因 → ⏸️ 用户确认走敏捷或 Feature
    - 🔴 禁止在 RD 身份下直接接收新需求
  - 活引用三处（A+B 同步写入）：
    - **FLOWS.md §六 Micro 流程规则 L954-965**：强制规则块头部更新版本标记到 `v7.3.10+P0-20-B 补两条反漂移规则`；在 cite 规则之后插入 🔴 第一人称锚点 + 🔴 追加改动回退规则（带 3 项子流程分支）两条硬规则
    - **FLOWS.md §六 Micro 事后审计**：新增 2 项 checklist——"身份切换第一人称锚点是否写入首句" + "执行中是否发生追加改动、若是是否跳回 PMO 准入"
    - **roles/pmo.md L5 Micro 头部段**：在 P0-16 必读子句后追加"🔴 第一人称锚点（P0-20-B）" + "🔴 追加改动回退规则（P0-20-B）"；完整闭环表述里加入「RD 改动（「作为 RD，…」锚句开头）」
    - **roles/pmo.md L1381-1382 反模式表**：新增两行——"RD 身份途中用户顺便追加改动 → 直接顺手改了" 和 "身份切换后用'我'/'PMO'/泛指" 对应 🔴 正确做法
    - **rules/flow-transitions.md Micro preamble**：在 P0-16 必读硬规则后追加一条 🔴 **反漂移双补丁（P0-20-B）** 复合规则（第一人称锚点 + 追加改动回退）
  - 版本号：SKILL.md frontmatter `7.3.10+P0-20` → `7.3.10+P0-20-B`；INIT.md Step 1.2-a 注释同步
- 设计要点：
  - **零新流程**：没有加 Stage、没有改流转图、没有新红线条目——全部在现有 Micro 规则块内补条款
  - **最低侵入**：第一人称锚点只是一句话约束，追加改动回退只是路由规则，不需要新的 state 字段
  - **可审计**：两条规则都能在事后审计 checklist 里直接检查（首句是否以"作为 RD，"开头 / 执行过程中有无追加改动且是否跳回 PMO）
  - **行为面提升**：堵了真实会发生的两个漂移口，特别是 B（"顺便"追加）——这是 Micro 蠕变到敏捷规模的最常见路径
- 保留未做（review 视角发现的次要点，留后续 P0）：
  - RD 身份在 Subagent dispatch 路径下是否需要等价的第一人称锚点 → 当前 subagent 隔离已经天然强化身份，不急着加
  - STATUS-LINE 是否应根据追加改动回退动态切换"角色：PMO" → 规则层已经够用，避免状态行过度工程化

## v7.3.10 + P0-20

> v7.3.10+P0-20 红线 #1 职责正交化：把"谁写代码"（维度 A）与"怎么组织流程"（维度 B）解耦——代码写权在所有流程下都归 RD，Micro 不再是红线 #1 的例外，而是省 Plan/Blueprint/UI/Review/Test Stage 的最短 RD 闭环（独立流程），允许主对话内 PMO→RD 身份切换由 RD 改动。红线 #1 因此从权限矩阵压缩为一句话；所有 Micro 相关描述统一为"身份切换"语义。

### P0-20：红线 #1 重构（职责正交化 + Micro 升格为独立流程）

- 触发：用户 insight「Micro 流程 PMO 可直接改 是不是改为切换 RD 身份来改，或者在主对话由 RD 来改，我感觉是一样的，核心目的是阅读过 RD 的开发规范」。
- 根因分析：
  - 旧红线 #1 把"谁写代码"和"怎么组织流程"两个维度混在一起，用"Micro 例外"打了个补丁 → 红线从一行变成权限矩阵，读者难记
  - Micro 流程的行为等价：PMO 直接改 / PMO 切 RD 身份 / 主对话由 RD 改，三种表述本质相同——核心约束是"改之前必读 RD 规范 + 自查"，不是"允许哪个角色 handle"
  - 正交化后：代码写权 = RD 本职（维度 A，无例外）；流程组织 = 完整 Stage 链 / Micro 最短链（维度 B，独立选择）
- 处理（一次性统一表述）：
  - **SKILL.md L62-67 红线 #1 改一句话版**：「代码 / 测试 / 构建配置的写操作 = RD 本职。必须由 RD 角色执行（主对话切换身份 / Subagent dispatch 均可），RD 必须先真实 Read 规范...改后按 rd.md 自查段执行自查。」附 📎 说明执行方式由 AI Plan 决定 / 流程选择由 Micro 准入决定；去掉"Micro 例外"子分支
  - **SKILL.md L123-135 Micro 简化规则块**：从"PMO 直接改代码"改成"主对话内 PMO→RD 身份切换，由 RD 直接改"，新增 📎 与红线 #1 的关系说明（"不是例外，是省 Stage 的独立流程"）
  - **SKILL.md L328** Micro 描述：→「✍️ 主对话 PMO→RD 身份切换（Read 规范 + cite）→ RD 改动 + 自查」
  - **INIT.md L185 CLAUDE.md 注入红线 #1**：同步简化，明确"PMO 本职写权仅限流程审计文件"+ "Micro 不是红线例外，是省 Stage 的最短 RD 闭环"
  - **FLOWS.md §六 Micro 流程**：preamble 从"PMO 不写代码在 Micro 不适用"改为"Micro = 省 Stage 的最短 RD 闭环...不是红线 #1 例外"；流程链路、自动流转、PMO 分析输出格式、Micro 规则块五个子段全部把"PMO 直接改 / PMO 切 RD 身份 / PMO 以 RD 身份直接"统一为"主对话 PMO→RD 身份切换 + RD 改动"
  - **RULES.md L531-554 Micro 自动流转段**：preamble 统一；执行分支表述从「主对话以 RD 身份直接改」→「主对话 PMO→RD 身份切换 → RD 改动」
  - **roles/pmo.md L5 顶部例外段**：重写为"Micro 流程身份切换"，明确"不是红线 #1 例外 → 省 Stage 的 RD 闭环"；身份切换必读不豁免保留
  - **roles/pmo.md L1379 反模式表**：「再由 PMO 主对话直接改」→「主对话内 PMO→RD 身份切换，由 RD 改动」
  - **STATUS-LINE.md L277-279 Micro 阶段行注释**：「PMO 主对话直接改」→「主对话 PMO→RD 身份切换，由 RD 改动」；阶段名「PMO 执行改动（Micro）」→「RD 执行改动（Micro）」
  - **standards/common.md L243 / L355 L1 预检注释**：同步身份切换语义 + 保留"身份切换必读不可豁免"
  - **rules/flow-transitions.md L167-179 Micro 表**：preamble + 表格 5 行全部统一为"PMO→RD 身份切换 → RD 执行改动"
  - **版本号**：SKILL.md frontmatter `7.3.10+P0-19-C` → `7.3.10+P0-20`；INIT.md Step 1.2-a 注释同步（触发 CLAUDE.md 自愈把新红线 #1 + 身份切换注释写入）
- 设计要点：
  - **正交化原则**：红线 #1 只管"谁写代码"（A），Micro/敏捷/Feature 只管"跑哪些 Stage"（B），两维度解耦。Micro 是独立流程 × 流程 B 的一个选项，不是红线 #1 的例外
  - **行为面零变化**：Micro 流程下"主对话 PMO→RD 身份切换"与旧描述"PMO 直接改"+"角色切换必读"语义等价；只是表述更干净
  - **红线条数不变**：仍为 15 条（#1 表述重写、不拆也不删）
  - **P0-16 补丁保留**：身份切换必读 `roles/rd.md` + `standards/common.md` + 按需 frontend/backend.md + 阶段摘要 cite 规范要点 + 改后自查—— P0-20 没有放松这条
- 用户价值：
  - 读者只需记一句「代码写权归 RD」—— 不再需要记 Micro 例外树
  - Micro 的本质（省 Stage）比之前更清晰，不用再纠结"PMO 为什么突然可以改代码"
  - 新增 RD 的职责边界更刚性——便于未来 Subagent 自动化 / 审计 / 权限隔离
- 未处理项：
  - OPTIMIZATION-PLAN.md / CHANGELOG.md 历史条目中的"PMO 可直接改"保留为历史记录，不回溯改写
  - SKILL.md 红线体系的更大结构性重排（整合多处子条款、抽出 RULES.md 的独立章节）留到后续 P0

## v7.3.10 + P0-19-C

> v7.3.10+P0-19-C 外部视角 fresh review 修补：P0-19-B 物理合并 agents/*.md → stages/*.md 后，通过独立 subagent 以零上下文视角复审 skill，发现 3 个 S1 阻塞项（红线计数不一致 + `roles/rd.md` 残留 arch-code-review Subagent 幽灵引用 + `agents/README.md` dispatch 示例未加 subagent-id 语义说明）+ 4 处连带活引用遗漏（standards/backend.md / templates/dispatch.md / rules/naming.md）。本次 patch 全部修复。

### P0-19-C：外部视角 review 的 S1 阻塞项 + 连带清理

- 触发：P0-19-B 合并完成后，用户要求「以全新视角 review 一下 teamwork skill」。通过独立 subagent（等同 fresh session 无历史上下文）走完 skill 通读，以外部视角校验 merge 质量。
- 根因分析：
  - P0-19-B merge 时只处理了 `agents/*.md` → `stages/*.md` 的**直接活引用**（16 处），漏了**二阶引用**：术语表 / 幽灵 Subagent 名 / subagent-id 语义说明
  - `INIT.md` 的红线计数（13 条）是从 v7.3.9 以前复制来的，v7.3 加了 #14 / #15 后一直没同步
  - `roles/rd.md` 的两阶段架构文档更新图和架构师 CR 完成后回调逻辑还在用「arch-code-review Subagent」的老措辞，P0-19-B 把它合并进 Review Stage 后该措辞就成了幽灵
  - `agents/README.md` dispatch 文件名示例保留了老 subagent-id，但没有明确「这些 id 是 dispatch 文件标签，不是规范源」—— 读者容易回读去找 `agents/rd-develop.md` 这种已删除的文件
- 处理（3 S1 + 4 连带）：
  - **S1-1 INIT.md 红线计数**：L184「13 条」→「15 条」；CLAUDE.md 注入模板补全红线 #14（AI Plan 模式）+ #15（流程确认）；Step 0 AUTO_MODE 强制保留项 L55「13 条绝对红线」→「15 条绝对红线」
  - **S1-2 roles/rd.md arch-code-review 幽灵 Subagent**：
    - L220「Code Review 后（arch-code-review Subagent 执行）」→「Review Stage 架构师 Code Review 后（规范见 stages/review-stage.md §架构师 CR 任务规范，执行方式见 agents/README.md §一）」
    - L212「Tech Review 后（arch-tech-review）」→「Blueprint Stage 架构师方案评审后（主对话角色，规范见 roles/rd.md §架构师方案评审）」
    - L376「自动进入架构师 Code Review（Subagent）→ 有 UI 则 UI 验收 → 🤖 QA 代码审查（Subagent）」→ 合并为「自动进入 Review Stage（架构师 CR + QA CR + 外部 Codex，执行方式见 agents/README.md §一，任务规范见 stages/review-stage.md）→ 有 UI 则 UI 验收」
    - L388 §架构师方案评审规范 角色定位「在独立 subagent 中对 RD 的技术方案进行全面审查」→ 去「独立 subagent 中」，加 📎 注脚说明「默认主对话，大方案由 AI Plan 决定是否 Subagent 隔离」
  - **S1-3 agents/README.md dispatch 示例加 subagent-id 语义块**：L286-290 下方新增 📎 三点说明（`{subagent-id}` 是 dispatch 文件标签 / 角色任务规范现在在 stages/*.md / dispatch 文件 Input files 应指向 stages/*.md 而非已删除的 agents/*.md）
  - **连带 #1 standards/backend.md L622-628 Schema 变更链条术语对照表**：列头「Agent 文件」→「规范位置」；各行指向改为：RD 开发→`stages/dev-stage.md §RD 角色任务规范`；架构师 Code Review→`stages/review-stage.md §架构师 CR 任务规范`；集成测试→`stages/test-stage.md §集成测试任务规范`；Blueprint 架构师方案评审→`roles/rd.md §架构师方案评审规范`
  - **连带 #2 templates/dispatch.md L9 命名规则行**：补充「subagent-id 是 dispatch 文件标签，沿用原有命名，角色任务规范已合并至 stages/*.md」
  - **连带 #3 rules/naming.md L44-46 subagent-id 列表**：补加一行「🔴 v7.3.10+P0-19-B 起角色任务规范已合并至 stages/*.md，subagent-id 仅作标签用」
  - **连带 #4 版本号 bump**：SKILL.md frontmatter `7.3.10+P0-19` → `7.3.10+P0-19-C`；INIT.md Step 1.2-a 注释同步（触发下次启动的 CLAUDE.md 漂移自愈校验，使红线 15 条写入 CLAUDE.md）
- 保留项（review 报告中的 S2/S3 **不处理**，留作后续 P0）：
  - S2-1 红线 #1 Micro exception 树过度工程化 —— 设计决策，需单独讨论
  - S2-2 dev-stage.md 7 自检维度「L108 + L352-392 各一份」—— 复核结论是**误报**（L108 是指针引用 `§4 RD 自查 7 维度`，只有 L352-392 真正列维度）
  - S2-3 RULES.md 1628 行 + 自带热路径索引 —— 需结构性拆分，单独 P0
  - S2-4 Key Context 6 类「写 -」的可 game 性 —— 设计决策
  - S2-5 Review/Test 3 轮封顶在 AUTO 下的浪费 —— 需 AUTO 模式分支调整
  - S3 polish（naming.md subagent-id 清单 / test-stage.md 内嵌 Python 模板 / {SKILL_ROOT} glossary 缺失 / 版本号程序化派生）—— 价值低、择机
- 收益：
  - 单一权威源一致性：`SKILL.md` 红线数 = `INIT.md` 红线数 = CLAUDE.md 注入红线数 = 15 条
  - 无幽灵 Subagent 引用：`roles/rd.md` 三处措辞 + `backend.md` 术语对照表 + `dispatch.md` + `naming.md` 全部指向合并后的 stages/*.md 权威位置
  - dispatch 示例消歧：`{subagent-id}` 的语义（文件标签 vs 规范源）首次被显式说明，避免读者回读已删除的 `agents/*.md`
- 兼容性（非破坏性）：
  - 无行为变更：只改文案 / 术语 / 链接，不触动任何 Stage 契约 / 流转 / 预检
  - 既存 dispatch_log/ 的 `002-rd-develop.md` / `003-arch-code-review.md` 等文件名继续有效（subagent-id 作为标签未变）
  - CLAUDE.md / AGENTS.md 会在下次 `/teamwork` 启动时自动漂移自愈（7.3.10+P0-19 → 7.3.10+P0-19-C 触发 full path），同步红线 15 条
- 相关 meta 观察（review 报告内）：**3 个月 19 个 P0 无一次删除**。下一个 P0 建议不再新增能力，聚焦消费：拆 RULES.md / 统一红线计数 / 红线 #1 Micro exception 二选一 / 全仓 grep 审计死引用。本次 P0-19-C 只修了审计类问题的子集。

---

## v7.3.10 + P0-19

> v7.3.10+P0-19 结构重构补丁：**Stage 升格为权威层级，Subagent 降格为执行选项**。物理合并 `agents/rd-develop.md` / `arch-code-review.md` / `qa-code-review.md` / `integration-test.md` / `api-e2e.md` 五个角色任务规范到对应 `stages/*.md` 的新增 §角色任务规范段；`agents/` 目录只保留 `README.md`（瘦身为纯 Subagent 执行协议：dispatch 文件协议 + Progress 可见性 + 主对话产物协议 + 通用执行约束 + Codex CLI 调用规范）。PMO 在 Plan 模式中按需选择执行方式（主对话 / Subagent / 混合），Subagent 不再作为"规范归档维度"存在。非破坏性：所有规范内容原样迁移，仅物理位置变动 + 章节编号微调。

### P0-19-B：Stage 升格 + agents/ 物理合并（stages/dev-stage.md + stages/review-stage.md + stages/test-stage.md + agents/README.md + 引用迁移）

- 触发：用户反馈「从合理的方向看，是不是弱化 subagent, 强调 stage, 增加各个 stage 中的规范文档，因为执行层面 pmo 可以按需选择 subagent」。承接 P0-19-A（subagent 降级为执行维度）的物理落地。
- 根因分析：
  - **Stage 是业务权威层级，Subagent 是执行手段**。v7.3.9+P0-14 dual-mode 化后，RD / 架构师 / QA 都可以主对话或 Subagent 执行，"按 agent 归档规范" 不再是自然语义分类
  - `agents/rd-develop.md` / `arch-code-review.md` 等文件命名暗示「这是 Subagent 专属规范」，导致主对话执行时 PMO 不确定是否仍需加载 → 双重权威源
  - Stage 级契约（Input/Process/Output）和 Stage 内角色任务规范分居两处（stages/ + agents/），PMO 派发时需要同时引用两个路径，心智负担 + 漏读风险
  - 把角色任务规范嵌入 stage 契约之后，**一个 stage 一个权威文件**，主对话 / Subagent 两种模式均从同一文件读取
- 处理（4 Stage 文件 + 1 README + 引用迁移）：
  - **§一 stages/dev-stage.md 合并 agents/rd-develop.md 全文**（+229 行）：新增 §RD 角色任务规范（1. 角色定位 Dual-Mode / 2. TDD 开发流程 / 3. UI 还原 / 4. RD 自查 7 维度）+ §RD 执行输出模板（执行摘要 / 自查报告 / 上游问题清单）
  - **§二 stages/review-stage.md 合并 agents/arch-code-review.md + agents/qa-code-review.md 全文**（+456 行）：新增 §架构师 CR 任务规范（角色定位 / Review 维度 / 执行流程 / 架构文档更新规则 / 输出模板 / 上游问题清单）+ §QA CR 任务规范（角色定位 / 执行流程 / 执行约束 / 输出模板 / 结果处理）+ §外部视角 Codex Review（codex CLI spawn prompt 模板）
  - **§三 stages/test-stage.md 合并 agents/integration-test.md + agents/api-e2e.md 全文**（+554 行）：新增 §集成测试任务规范（角色定位 / 执行流程 / 执行约束 / 证据要求 / 报告模板）+ §API E2E 任务规范（角色定位 / 触发条件 / 执行流程 / 脚本生成规范 / 脚本落盘 + e2e-registry 注册 / 报告模板 / 红线 / 降级处理 / 含完整 Python 脚本模板）
  - **§四 agents/README.md 瘦身**（734 → ~700 行，重组为 6 个顶级章节）：§一 执行方式与模型（偏好指引 + 模型推荐）/ §二 通用 Subagent 执行约束（文件读取 / 代码质量 / 异常处理 / 输出规范 / Progress Log / 危险命令红线）/ §三 Codex CLI 调用规范（宿主无关独立性 + 降级路径决策）/ §四 PMO 启动规范（含 Dispatch 文件协议 4.1-4.6 + 4.3 Progress 可见性协议 + 4.6 Subagent 返回状态分级处理）/ §五 主对话产物协议（命名约定 + frontmatter 硬规则 + Key Context 复用 + review-log.jsonl schema + 独立性保证）/ §六 目录结构索引（含 v7.3.10+P0-19-B 变更说明）
  - **§五 物理删除 5 个 agents/*.md 文件**：`agents/rd-develop.md` / `arch-code-review.md` / `qa-code-review.md` / `integration-test.md` / `api-e2e.md`；`agents/` 目录现仅保留 `README.md`
  - **§六 引用迁移**（16 处活引用 + 保留 CHANGELOG/OPTIMIZATION-PLAN 历史引用）：
    - `SKILL.md` 示例 Plan 模板 / 索引表：`agents/rd-develop.md` → `stages/dev-stage.md §RD 角色任务规范`；`agents/arch-code-review.md` → `stages/review-stage.md §架构师 CR 任务规范`；`agents/qa-code-review.md` → `stages/review-stage.md §QA CR 任务规范`
    - `RULES.md` Test Stage 子流程：`agents/integration-test.md` → `stages/test-stage.md §集成测试任务规范`；四-B 首段说明文字同步
    - `roles/rd.md`：架构师 CR 规范链接指向 stages/review-stage.md；内嵌审查项注释同步
    - `roles/qa.md`：集成测试 / API E2E / 集成测试规范链接全部指向 stages/test-stage.md
    - `templates/feature-state.json`：`loaded_role_specs[]` 从 `agents/rd-develop.md` 改为 `stages/dev-stage.md`
    - `templates/e2e-registry.md`：生成 Subagent 引用指向 `stages/test-stage.md §API E2E 任务规范`
    - `templates/dispatch.md`：Input files 模板第 2 项从 `agents/{subagent-id}.md` 改为 `stages/{stage}-stage.md §角色任务规范`；§四 4.3 / §五 Progress 章节编号同步为 §四 4.6 / §四 4.3
    - `codex-agents/tester.toml` / `reviewer.toml` / `rd-developer.toml`：developer_instructions Read 列表的第 3-4 项（旧 agents/*.md）合并为单行「stages/{stage}.md § ...（merged in v7.3.10+P0-19-B）」
  - **§七 agents/README.md 内部 §4.3 → §4.6 修正**：FAILED 兜底从旧 §4.3 改为新 §4.6（Subagent 返回状态分级处理表合并到完成后处理段）
  - **§八 SKILL.md frontmatter version bump**：`7.3.10+P0-18` → `7.3.10+P0-19`（触发下次启动的漂移自愈校验，使 CLAUDE.md / AGENTS.md 同步新目录结构）
- 保留项：
  - `CHANGELOG.md` / `OPTIMIZATION-PLAN.md` 历史引用 **不改写**（这些是历史事实记录，非当前规范）
  - `stages/*.md` 新增段顶部的合并注释（「本节整合 v7.3.10+P0-19-B 前的 agents/xxx.md 完整规范」）保留，为合并过程提供可追溯的 git-log 替代信息
- 收益：
  - Stage = 一个物理文件 = 一个权威：PMO 派发 / 切换角色 / 主对话执行时只需引用一个路径，心智负担 -50%
  - 规范与契约同居：Input Contract → 角色任务执行流程 → Output 模板串联在同一文件内，RD / 架构师 / QA 读时上下文天然连贯
  - Subagent 回归执行手段本位：`agents/README.md` 只负责"如何跨宿主派发 + 如何保证可观测性"，不再承担规范归档
  - Plan 模式更纯粹：approach=main-conversation/subagent/hybrid 只影响执行方式，不影响「读哪个规范文件」
- 兼容性（非破坏性）：
  - 所有规范内容原样迁移（无内容删减 / 强度调整），章节编号微调
  - Subagent dispatch 协议（dispatch 文件 / INDEX / Progress Log）完全不变
  - `.teamwork_localconfig.md` 的 `teamwork_version` 缓存机制（P0-17 引入）会在下次启动自动捕获 `7.3.10+P0-19`，触发 CLAUDE.md / AGENTS.md 校验一次（若发生漂移将被漂移自愈机制同步）
  - 用户侧无任何行为变更，`/teamwork` 命令 / 阶段流转 / 角色切换全部保持

## v7.3.10 + P0-18

> v7.3.10+P0-18 人机约定补丁：新增「ok = 按 💡 建议」全局快捷授权约定。用户在 ⏸️ 暂停点回复 `ok` / `OK` / `好` / `可以` / `行` / `嗯` / `按建议` / `按推荐` → PMO 自动映射为「当前暂停点全部 💡 推荐选项」执行（单决策等价于回复 💡 对应数字；多决策等价于所有决策都选 💡 推荐）。前置条件：暂停点至少有 1 个 💡（红线 #10 本就强制）；破坏性操作 / 无 💡 暂停点 / ok+补充语句 不适用本约定，仍按原规则处理。PMO 须输出一行 cite『✅ 已按 💡 建议处理：…』作为审计痕迹。非破坏性，仅加强用户体验。

### P0-18：ok = 按 💡 建议 约定（RULES.md + STATUS-LINE.md + SKILL.md + INIT.md）

- 触发：用户反馈"加一个指令说明，ok = 按建议"。观察：现有规范（RULES.md §模糊确认处理 L186）是『🔴 禁止把「好」「行」直接视为全面授权』，要求复述+二次确认；但实际交互中用户回复 ok 几乎 100% 是『按 💡 推荐走』意图，多余的二次确认增加摩擦。
- 根因分析：
  - 旧规则是为了防止"无上下文确认"——担心 ok 被误解为授权破坏性操作。但红线 #10 已经强制要求每个暂停点都输出 💡 推荐 + 📝 理由，ok 在"有 💡 推荐"的上下文中语义完全明确（= 按推荐走）
  - 多决策点（1A 2B）即使用户想『都按推荐』也要打 `1A 2A` 5 字符，ok 2 字符更省
  - 破坏性操作（force push / drop 表 / 删分支）属强制保留暂停点（见 flow-transitions.md），本就不应依赖模糊确认，单独拉保护线即可
- 处理（4 文件）：
  - **§一 RULES.md §模糊确认处理**（L177-186）：新增「🟢 ok = 按 💡 建议」段，含 7 字（ok/OK/Ok/好/可以/行/嗯/按建议/按推荐）识别清单 + 单决策/多决策映射规则 + 前置条件（必须有 💡）+ 强制 cite 输出格式 + 4 条边界保留（破坏性操作 / 无 💡 暂停点 / ok+补充语句 / 非暂停点）。原 L186 禁令改为边界语句，不再"全面禁止"
  - **§二 STATUS-LINE.md 用户回复处理表**（L313-321）：新增一行『🟢 ok/OK/好/可以/行/按建议』列映射到『按 💡 推荐全部选项执行 + cite』；原"模糊确认（≤5 字：好/可以/OK）"行改为『其他非 ok 家族模糊词』，避免与新规冲突
  - **§三 STATUS-LINE.md 意图识别表**（L332）：🟢 流程控制行扩展识别词表 + 处理方式改为『有 💡 → 按 💡 执行 + cite；无 💡 → 复述 + 二次确认』双分支
  - **§四 SKILL.md frontmatter version**: 7.3.10+P0-17 → 7.3.10+P0-18（触发下次启动的漂移自愈校验，使 CLAUDE.md/AGENTS.md 同步）
  - **§五 INIT.md Step 1.2-a 当前版本标注**同步更新为 7.3.10+P0-18
- 收益：
  - 人机交互摩擦降低：最常见的"采纳推荐"路径从 `1A 2A` → `ok`（2 字符），大幅降低打字成本
  - 决策意图明确化：PMO cite 一行『✅ 已按 💡 建议处理：…』让用户立刻看到 ok 被如何解读，防止误解
  - 规范语义一致：红线 #10（暂停点必须给 💡）与 ok 约定形成闭环——💡 不只是"参考建议"而是"ok 对应的具体选项"
  - 边界清晰：破坏性操作 / 非暂停点 / ok+补充语句 保留原路径，不会因 ok 约定扩大授权面
- 兼容性（非破坏性，仅放宽授权）：
  - 旧行为：用户回复 ok → PMO 复述+二次确认 → 用户再回复 1A 2A → 执行
  - 新行为：用户回复 ok → PMO cite『按 💡 建议处理』→ 直接执行。用户如不满意可中断，实际事故面与旧行为相当（PMO cite 相当于"软复述"）
  - 多决策点 "1A 2A" 显式回复仍然有效，ok 只是快捷方式
  - 破坏性操作 / 无 💡 暂停点：行为不变
  - 红线 #10（暂停点必须给 💡 + 📝）事实上成为 ok 约定的前置条件，变相加强红线 #10 的约束

## v7.3.10 + P0-17

> v7.3.10+P0-17 启动 token 优化：引入 **skill 版本缓存机制**，复用 `.teamwork_localconfig.md`（已 gitignore）记录 `teamwork_version` 字段。每次 `/teamwork` 启动时，先比对 SKILL.md frontmatter 的 `version` 与 localconfig 缓存值：一致（99%+ 场景）→ 跳过 CLAUDE.md/AGENTS.md Read + 逐字符 diff；不一致（skill 升级 / 首次 / 降级）→ 走全量校验 + 写回新版本号。估计节省 ~65-75% 启动阶段 token 消耗。漂移自愈（skill 升级后模板变动自动同步到 CLAUDE.md）能力保留；`/teamwork force-init` 作为逃生舱。非破坏性变更，向前兼容 v7.3.10+P0-16（localconfig 无 teamwork_version 字段 → 自动走全量 + 写入一次即进入稳态）。

### P0-17：skill 版本缓存优化 CLAUDE.md 校验（SKILL.md + templates/config.md + INIT.md）

- 触发：用户反馈"目前读 Init.md 的逻辑是什么，从 token 占用角度，是否有优化空间"；复盘发现 Step 1.2 每次启动都会 Read `{HOST_INSTRUCTION_FILE}`（CLAUDE.md / AGENTS.md）+ 做逐字符 diff，占用 ~2000-3500 token。用户反建议："我们是否在 .teamwork_localconfig.md 中加一个当前 teamwork 版本，如果和 skill.md 版本不一致的时候再去做 claude.md 和 agent.md 检查，更合理，复用本地的轻量级文件。"
- 根因分析：
  - CLAUDE.md/AGENTS.md 模板内容只在 skill 升级时才会变化；日常启动 99%+ 场景是"skill 未升级 → 模板未变 → diff 必然一致"的重复工作
  - 漂移自愈能力（skill 升级后模板变动同步到 CLAUDE.md）只需在升级时触发一次，不需要每次启动都跑
  - `.teamwork_localconfig.md` 已经存在（gitignore、每开发者各自维护）、是启动必读文件（已在 Step 2 加载），作为版本缓存载体成本为零
- 处理（3 文件）：
  - **§一 SKILL.md frontmatter 新增 `version: 7.3.10+P0-17` 字段**（单一权威版本号）：放在 frontmatter 使解析成本最低（Skill 加载时已可见）；后续每次 skill 升级需同步更新此字段
  - **§二 templates/config.md `.teamwork_localconfig.md` 模板新增「Skill 版本标记」段**：含 `teamwork_version:` 字段 + 详细注释说明机制 + "🔴 禁止手改（PMO 自动维护）"警示 + 逃生舱说明
  - **§三 INIT.md Step 1.2 重写为缓存-校验-回写模式**：
    - **Step 1.2-a**：读取 SKILL.md frontmatter `version` → `SKILL_VERSION`（缺失则降级全量+一次性 ⚠️ 提示）
    - **Step 1.2-b**：读取 `.teamwork_localconfig.md` `teamwork_version` → `LOCAL_VERSION`（文件/字段缺失/损坏均降级为 null）
    - **Step 1.2-c**：版本比对决定路径
      - ⚡ fast path（一致）：跳过 CLAUDE.md/AGENTS.md Read + diff，输出「⚡ CLAUDE.md 校验跳过（teamwork_version={VERSION} 命中缓存）」
      - 🔄 full path（不一致/null）：走原 P0-17 前的全量校验（文件不存在→创建、存在→逐字符 diff、漂移→替换），完成后回写 localconfig `teamwork_version: {SKILL_VERSION}`，输出「🔄 CLAUDE.md 已同步（{旧版本 or "缺失"} → {新版本}）」
      - 🚨 SKILL_VERSION=null：走全量 + 不回写 + ⚠️ 提示
  - **§四 INIT.md Step 0 加 `/teamwork force-init` 命令**（+ `/teamwork init --force` 别名）：用户怀疑 CLAUDE.md 被外部工具手改 / 缓存脏污时强制走全量校验
- 收益：
  - 启动 token 节省：fast path（99%+ 场景）跳过 ~2000-3500 token 的 CLAUDE.md Read + diff；估计节省 ~65-75% 启动阶段 token 消耗
  - 漂移自愈保留：skill 升级 → 版本不一致 → 一次性全量 diff 修复 CLAUDE.md → 写回新版本 → 此后跳过；机制语义与 P0-17 前完全等价
  - 复用本地轻量文件：localconfig 已 gitignore + 已是 Step 2 必读文件，无额外 I/O 成本
  - 多开发者一致性：localconfig 是每个开发者各自维护，版本缓存也是本地化（不产生跨机器 / 跨用户 git 冲突）
- 兼容性（非破坏性，向前兼容）：
  - P0-16 用户升级到 P0-17：首次启动 `LOCAL_VERSION=null` → 走全量校验 + 写回 → 此后稳态 fast path
  - localconfig 不存在：首次启动走全量校验 + 按 templates/config.md 创建最小版 localconfig（只填 scope:all + teamwork_version）
  - CLAUDE.md 被用户手改但 skill 未升级：版本仍命中 → 跳过校验 → 用户修改被保留（"respect user edits" 默认行为；若要强制恢复模板，用 `/teamwork force-init`）
  - 用户伪造 localconfig 的 teamwork_version（手改成最新值）：绕过校验的理论风险 → 靠模板注释"禁止手改"约束 + `/teamwork force-init` 兜底（此场景极少）
  - 无字段变更影响 state.json / agents/ spec
- 未变更：
  - P0-16 及之前所有行为语义（Micro 流程、红线 #1、Ship MR 模式等）完全不变
  - P0-11 AUTO_MODE / P0-13 Codex opt-in / P0-15 Ship Stage MR 流 等所有其他机制保持原样

## v7.3.10 + P0-16

> v7.3.10+P0-16 一致性修订：Micro 流程去「强制 RD Subagent」化 → 统一为「PMO 自行判断（主对话以 RD 身份直接改 / 升级 Plan 模式）」。核心实体（FLOWS.md §六、SKILL.md 红线 #1 Micro 例外）早已在 v7.3 放宽为 PMO 直接改，但 SKILL.md L320 / RULES.md L521-547 / rules/flow-transitions.md / STATUS-LINE.md / roles/pmo.md / standards/common.md 等 7 个文件仍残留「RD Subagent 执行 / 必须启 Subagent」旧描述，形成自相矛盾。P0-16 清理全部残留，使"PMO 自行判断执行方式"贯穿全部 Micro 相关描述。非破坏性变更（行为层面已经是 PMO 直接改，仅补齐文档一致性）。

### P0-16：Micro 流程描述一致性修订（SKILL.md + RULES.md + rules/flow-transitions.md + roles/pmo.md + STATUS-LINE.md + standards/common.md）

- 触发：用户反馈"Micro 流程是否还强制 RD 在 subagent 下执行，预期是 Micro 流程在初步分析后，PMO 自行判断是否切 Plan 模式还是以 RD 角色身份直接在主对话修改"。
- 根因分析：
  - v7.3 放宽了 Micro 流程红线：FLOWS.md §六「Micro 流程」+ SKILL.md 红线 #1 Micro 例外 + SKILL.md L122-126「AI Plan 模式 Micro 例外」已统一为「PMO 可直接改，无需 Subagent / Execution Plan / dispatch」
  - 但 SKILL.md L320 六种流程速查 / RULES.md 流转图 / rules/flow-transitions.md Micro 流程表 / STATUS-LINE.md Micro 示例 + 阶段对照表 / roles/pmo.md 反模式 / standards/common.md 预检级别表 等 7 处未同步更新，仍保留 v7.2 前的「RD Subagent 执行」旧描述
  - 导致跨文件描述自相矛盾：同一套规范里有地方说"PMO 直接改"，有地方说"必须启 RD Subagent"，对 PMO 读者造成歧义
- 处理（7 文件 / 11 处）：
  - **§一 SKILL.md L320**：六种流程 Micro 行 `RD Subagent 执行` → `PMO 自行判断执行方式（✍️ 主对话以 RD 身份直接改 / 🔀 升级为 Plan 模式走敏捷或 Feature）`
  - **§二 RULES.md L521-547 Micro 流程自动流转**：流程图去掉「🤖 RD Subagent 执行改动（🔴 PMO 禁止自己改，即使只改一行）」+「PMO L1 预检」节点；改为「PMO 自行判断：✍️ 主对话以 RD 身份直接改 / 🔀 升级 Plan 模式」分支；描述语加 v7.3 放宽 + P0-16 明确标注
  - **§三 RULES.md L720 功能完成时 PMO 必须执行**：Micro 流程校验改为「PMO 分析→用户确认→PMO 执行（主对话直接改 或 升级 Plan 模式）→用户验收 四步」
  - **§四 rules/flow-transitions.md**：
    - L39-40 强制保留暂停点表 Micro 两行（🤖 RD Subagent → 用户验收 / → ⏸️ 升级确认）改为 PMO 执行改动路径
    - L52 豁免示例 Micro 行改「按 💡 自动进入（PMO 自行判断执行方式，无需暂停）」
    - L167-177 § Micro 流程节完全重写：header 从「🔴 PMO 禁止自己改代码，必须启 RD Subagent」反转为「🟢 PMO 自行判断执行方式」；表格行从「PMO 分析 → Micro 变更说明 → 🤖 RD Subagent → 用户验收」4 行改为「PMO 分析 → PMO 执行改动 → 用户验收」3 主路径 + 升级确认支路
  - **§五 roles/pmo.md**：
    - L5 版本头「Micro 流程例外（v7.3）」描述修正：去掉「但必须走 Plan 模式规划 + 用户确认流程」与 FLOWS.md §六 冲突的旧字句，改为「无需 Subagent / Execution Plan / dispatch」+ P0-16 标注
    - L748 auto 豁免表 Micro 行改「PMO 执行改动（主对话直接改）」
    - L1379 反模式首行从「即使只改一行也必须启 RD Subagent」改为「必须先输出 PMO 初步分析 + Micro 准入检查 → ⏸️ 等用户确认 → 再由 PMO 主对话直接改」+ P0-16 标注
    - L1388-1399 PMO 小改动决策树末段从「🔴 任何情况下 PMO 都不能自己动手改代码」改为双分支：Micro 外保持禁止 + Micro 内 PMO 自行判断（直接改 / 升级 Plan）
  - **§六 STATUS-LINE.md**：
    - L201 Micro 示例状态行「下一步：🤖 启动 RD Subagent」改为「下一步：⏸️ 等待用户验收」，阶段从「Micro 变更说明中」改为「PMO 执行改动中」
    - L277-280 阶段对照表 Micro 专用阶段 3 行（Micro 变更说明 / 🤖 RD Subagent / 用户验收）重写为 PMO 执行改动 / Micro 升级判定 / 用户验收
  - **§七 standards/common.md**：
    - L242 L1 预检描述「包括 Micro 流程的 RD Subagent」改为「Micro 流程 PMO 主对话直接改，不走 Subagent，不触发本预检」
    - L354 各流程预检级别速查表 Micro 行从「Micro | RD Subagent | L1」改为「Micro | _（不启 Subagent）_ | —」
- 收益：
  - Micro 流程描述一致性：全部 12 处引用统一到「PMO 自行判断执行方式」语义，消除 v7.3 放宽以来遗留的 7 文件自相矛盾
  - 用户意图承载：显式写出「✍️ 主对话以 RD 身份直接改 / 🔀 升级 Plan 模式」双路径，PMO 读规范即知自己有判断空间，不再被旧描述误导去强启 Subagent
  - 红线体系简化：Micro 外「PMO 不得改代码」+ Micro 内「PMO 可直接改（白名单内零逻辑）」边界清晰，不需要维护"什么时候启 Subagent"的额外规则
- 兼容性（非破坏性）：
  - 行为面无变化：FLOWS.md §六 + SKILL.md 红线 #1 Micro 例外早已是"PMO 直接改"语义；PMO 按新描述执行与按旧描述通过"豁免启 Subagent"执行等价
  - state.json / localconfig：无字段变更
  - Subagent 不再在 Micro 下 dispatch，因此不影响 dispatch 模板 / agents/ spec

### P0-16 补丁：Micro RD 身份切换的必读规则（SKILL.md + FLOWS.md + RULES.md + rules/flow-transitions.md + roles/pmo.md + STATUS-LINE.md）

- 触发：用户反馈"如果切换 RD 身份是否会加载 rd 的规范，避免还是 PMO 只是输出描述改了"
- 根因：P0-16 主体改动把 Micro 执行路径统一到「PMO 以 RD 身份主对话直接改」，但未显式要求真实加载 RD 规范。Micro 流程免 Execution Plan 同时把 SKILL.md 红线 #14「Role specs loaded 必须真实 Read」也隐性豁免了——存在"PMO 换个名头凭记忆改"的漏洞
- 处理（6 文件）：
  - **SKILL.md L63 红线 #1 Micro 例外条款**：加"🔴 角色切换必读不豁免"子句，要求 Read roles/rd.md + standards/common.md + 按改动类型加读 frontend.md/backend.md + 摘要 cite 规范要点
  - **SKILL.md L122-126 AI Plan 模式 Micro 例外段**：扩展 Micro 例外条款的"不豁免项"清单，显式列出必读文件 + cite 规则 + 自查要求
  - **FLOWS.md §六 Micro 流程规则**：强制规则段加「角色切换必读」3 项新条款；流程链路 + 流转图 + 分析输出格式步骤描述 全部加入「PMO 加载 RD 规范+cite」节点 + 「RD 自查」节点；事后审计加 2 项校验（是否真实 Read / 自查是否执行）
  - **RULES.md Micro 流转图**：在「✍️ 主对话以 RD 身份直接改」分支下补全"改动前必读 / 改动前 cite / 改动后自查" 3 层硬约束
  - **rules/flow-transitions.md § Micro 流程**：表头加第二行「角色切换必读不豁免」警示；流转表从 4 行（PMO 分析 / 执行 / 升级 / 验收）扩展为 6 行（PMO 分析 / 加载 RD 规范 / 执行 / RD 自查 / 升级 / 验收）
  - **roles/pmo.md L5 头部 Micro 例外描述**：补全「角色切换必读不豁免」+「cite 规范要点」+「改动后自查」3 项硬约束
  - **STATUS-LINE.md L277-281 阶段对照表**：Micro 专用阶段从 3 行（PMO 执行改动 / 升级判定 / 用户验收）扩展为 5 行（PMO 加载 RD 规范 / PMO 执行改动 / RD 自查 / 升级判定 / 用户验收）
- 收益：
  - 堵住"换名头凭记忆改"漏洞：PMO 必须真实 Read + cite 规范要点，"我切 RD 了"一句话不能替代"读规范"
  - Micro 流程仍然是最轻量通道：不要求完整 Execution Plan / dispatch，但保留"真实加载 + cite + 自查" 3 层最小质量锚
  - 与红线 #14「Role specs loaded 必须真实 Read」+ AI Plan 模式红线「角色切换必 cite」保持一致：Micro 只豁免 Execution Plan 的输出形式，不豁免底层纪律
- 兼容性（非破坏性，仅加强约束）：
  - 行为面轻微变化：之前可能存在"PMO 未 Read rd.md 就直接改"的灰色操作，现在必须真实 Read + cite
  - 流转图多出 2 个新阶段（「PMO 加载 RD 规范」+「RD 自查」），属自动流转节点（🚀自动，无需用户确认）
  - state.json / localconfig：无字段变更

## v7.3.10 + P0-15

> v7.3.10 相对 v7.3.9 的唯一破坏性变更：Ship Stage 从「PMO 本地 merge + push merge_target」改为「MR 模式」（P0-15）。PMO 只负责净化 + push feature + 生成 MR/PR create URL，合并权由平台和用户处理。红线 #1 不再有 Ship 例外条款；localconfig 移除 `ship_rebase_before_push` / `ship_policy`；state.json.ship 字段重构。详见 P0-15 条目。

## v7.3.9 + P0 简化

> P0 是 v7.3.9 落地后的一轮"反刍"简化：抽取重复描述、收敛 preflight 暂停点、修正依赖安装时机表述、Codex 成本治理（P0-13：Plan/Blueprint opt-in 默认 OFF，Review 保持强制）、Dev Stage 默认主对话（P0-14：RD 自行规划 Plan 模式，subagent 降为 opt-in）、Ship Stage MR 化（P0-15：简化 PMO 职责边界）。无破坏性变更（P0-15 仅影响 Ship Stage 流程和 state.json.ship schema，向前兼容 v7.3.9 其他部分）。

### P0-15：Ship Stage MR 模式重构（stages/ship-stage.md + templates/feature-state.json + SKILL.md + INIT.md + roles/pmo.md + rules/flow-transitions.md + FLOWS.md + templates/config.md）

- 触发：用户反馈"当前 Ship 流程是否可以简化，例如开发完成后新分支的代码提交 push 后，生成 MR create 链接由用户创建 MR 可以了，这个 MR create 链接要记到 state.json 中，方便以后回溯，然后清理 worktree（如有），不删远程 feature 分支"。
- 决策：**Ship Stage 从 6 步直连合并流（净化 → push feature → rebase → 本地 merge --no-ff → push merge_target → worktree 清理）改为 3 步 MR 流（净化 → push feature + 生成 MR/PR create URL → worktree 清理）**。PMO 不做本地 merge / push merge_target / 冲突解决；合并权由平台（GitHub/GitLab/Gitee/Bitbucket 等）和用户处理。
- 根因分析：
  - v7.3.9 Ship Stage 让 PMO 承担了过多"最后一公里"职责：本地 merge、rebase、冲突解决、push merge_target。这些操作在多人协作场景下风险高（覆盖他人改动、污染主干）、需要复杂的红线 #1 例外条款（允许 PMO 改代码解冲突），且实际合入已由 MR/PR 平台做得更好（代码评审、CI/CD 门禁、合规审计、审批流）
  - 主流 git workflow（GitHub Flow / GitLab Flow / Trunk-Based）核心就是"push 分支 + 平台合入"，直连合并反而是反模式
  - 红线 #1 "PMO 非 Micro 流程下不得改代码" 加 Ship 例外条款使红线复杂化，不利于信任边界表达
- 处理（8 文件）：
  - **§一 stages/ship-stage.md 完全重写**（核心）：Input/Process/Output Contract 全部按 MR 模式重写；3 步流（Step 1 净化 / Step 2 push feature + host 识别 + MR URL 生成 / Step 3 worktree 清理暂停点）；per-host URL 模板（github / gitlab / gitlab-self-hosted / gitee / bitbucket / unknown）；unknown 平台走 localconfig `mr_url_template` 或 concerns 标注"未识别平台"；push FAILED 直接升级 ⏸️ 用户决策（不重试、不降级）；Anti-patterns 表更新（禁止本地 merge / 禁止 push merge_target / 禁止伪造 URL / 禁止删除远程 feature 分支）
  - **§二 templates/feature-state.json ship 字段重构**：移除 `rebase_status` / `merge_commit_hash` / `push_status`；新增 `sanitize_log` / `git_host` / `mr_create_url` / `feature_pushed_at` / `worktree_cleanup` / `shipped`；顶部 `_instructions.ship_tracking_v7_3_10_P0_15` 注释说明字段变更
  - **§三 SKILL.md 红线 #1 + INIT.md 红线 #1**：移除"🆕 Ship Stage 例外（v7.3.9）rebase/merge 冲突 PMO 可直接解决"条款；改为"🟢 Ship Stage 行为（v7.3.10+P0-15）：Ship Stage PMO 不做本地 merge / push merge_target / 冲突解决；只负责净化 + push feature + 生成 MR 创建链接。合并权由平台和用户处理（红线 #1 不再有 Ship 例外条款）"
  - **§四 roles/pmo.md**：PM 验收三选项 + Ship Stage 章节版本号 v7.3.9 → v7.3.10+P0-15；Merge 预览模板改 MR 模式（去掉 rebase 预处理行）；Ship Stage PMO 职责速查段全部重写（3 步流 + 禁止清单 + push FAILED 处理）；Commit / Push / Ship 状态报告改 MR 模式（`mr_create_url` / `git_host` / `worktree_cleanup` 字段）；强制保留暂停点清单移除"ship_policy=confirm merge+push"（第 2 项）和"Ship Stage 冲突 PMO 解不了"（第 4 项），改为 push FAILED 暂停点；移除"Ship Stage 冲突解决权限（红线 #1 例外）"段
  - **§五 rules/flow-transitions.md**：Feature 流程 Ship 行重写（PM 验收 → Ship Stage → worktree 清理 → 完成；移除 merge+push 待确认 / 本地 merge 行）；push FAILED 暂停点 2 选 1（手工处理后复跑 / 取消 Ship）
  - **§六 FLOWS.md**：PMO 初步分析阶段链 v7.3.4 → v7.3.10+P0-15（末段改 PM 验收 + Ship Stage MR 模式）；流程步骤描述第 8-10 步重写
  - **§七 templates/config.md 本地配置**：移除 `ship_rebase_before_push` / `ship_policy`；保留 `merge_target` / `worktree_cleanup`；新增 `mr_url_template` 字段（可选，自建 GitLab / 企业 git 自定义链接格式，支持 `{remote_url}` / `{repo_path}` / `{feature_branch_enc}` / `{merge_target}` 占位符）
- 收益：
  - PMO 职责边界清晰：Ship Stage 只负责"把分支送到平台门口 + 给用户合入入口"，不越界做代码层决策
  - 红线 #1 简化：移除 Ship 例外条款后，"PMO 非 Micro 流程下不得改代码" 变为真正的绝对红线，无需维护例外清单
  - 多人协作友好：平台 MR/PR 合入有代码评审 / CI / 审批记录，比 PMO 本地 merge 可审计性强
  - 无冲突解决成本：PMO 不解冲突 → 不需要单测全绿校验 / 不需要升级决策路径 / 不产生"解一半再回退"的中间态
  - 暂停点收敛：v7.3.9 "merge+push 待确认" + "worktree 清理" + "Ship 冲突/FAILED" 3 个 Ship 暂停点收敛为 1 个（worktree 清理）+ 1 个异常暂停点（push FAILED）
- 兼容性（破坏性变更，需迁移）：
  - **state.json.ship schema**：v7.3.9 已完成 Ship 的 Feature 保留旧字段（merge_commit_hash / push_status 等）不清理，可查阅；v7.3.9 进行中未到 Ship Stage 的 Feature 进入 Ship 时走新流程、写新字段
  - **localconfig**：v7.3.9 用户升级到 v7.3.10 时，`ship_rebase_before_push` / `ship_policy` 字段 PMO 自动忽略（不报错）；建议用户手动清理这两行 + 新增 `mr_url_template:`（空值即可）
  - **Codex CLI 子 agent**：Ship Stage 不通过 subagent 执行（PMO 主对话自主），无影响
  - **历史 Feature 的完成报告**：v7.3.9 报告中含 `merge_commit` / `已合入 {merge_target}` 字段的历史数据保留（审计痕迹）
- 未变更：
  - PM 验收三选项（通过+Ship / 通过暂不 Ship / 不通过）语义不变，只是"通过+Ship"进入的 Ship Stage 流程变了
  - 选 2（通过暂不 Ship）的 push feature 归档流程不变
  - 其他 Stage 的 auto-commit 硬规则 / git 干净校验 / Stage 切换预检均不变
  - merge_target 配置链（state.json > localconfig > 默认 staging）不变
  - worktree 清理策略（`worktree_cleanup: ask/keep/remove`）不变

### P0-1：auto-commit 硬规则集中化（rules/gate-checks.md + 8 个 Stage md）

- 问题：v7.3.9 在 8 个 Stage md（plan / ui_design / blueprint / blueprint_lite / dev / review / test / browser_e2e）中各重复一遍 5-7 行的 "Stage 完成前 git 干净" 流程描述。改文案需改 8 处，用户读 Stage 文件看到大段重复。
- 处理：将完整规则抽取到 `rules/gate-checks.md § Stage 完成前 git 干净`（含通用流程、各 Stage commit message 规范、单值/数组字段语义、免除场景）。各 Stage md 只保留一行引用 + 本 Stage commit message 示例。
- 收益：文案减少 ~35 行；单一修改点；引用链从分散变为集中。

### P0-2：Preflight 从 6 项砍到 4 项（plan-stage.md + pmo.md + flow-transitions.md + feature-state.json）

- 问题：v7.3.9 原设计"3 硬门禁 + 3 软提示"，实践发现：
  - "工作区干净" 是硬条件（worktree 继承脏状态代价大），不应软化
  - "merge_target 解析" 在级联无分歧时无需交互
  - "分支命名" 可从 Feature 全名自动派生
  - 最多 3 次暂停，用户体验冗长
- 处理：收敛为 **4 项硬门禁 + 0 软提示**：
  - 门禁 1：worktree 策略无残留
  - 门禁 2：分支名无冲突（分支名自动派生）
  - 门禁 3：base 分支可达（merge_target 自动解析）
  - 门禁 4：**工作区干净（P0 升级为硬门禁）**
  - 暂停点：最多 1 次（仅真冲突时）
- 收益：preflight 交互次数从"至多 3 次"降到"最多 1 次"。plan-stage.md / pmo.md 的校验表 + 暂停点模板同步更新。flow-transitions.md L11-12 更新 preflight 描述。feature-state.json 的 plan_preflight.checks 增加说明注释。

### P0-3：懒装依赖模型（plan-stage.md + dev-stage.md + test-stage.md）

- 问题：v7.3.9 描述 Feature worktree 创建时需装依赖（npm/pip/build），隐含 ~分钟级冷启动成本。实际只有 Dev / Test Stage 需要依赖，其他 Stage（Plan / Blueprint / Review）纯文档产出，空壳 worktree 就能跑。把依赖安装绑在 worktree 创建上是过早优化为保守。
- 处理：
  - `plan-stage.md` worktree 创建段补 "🟢 P0 懒装依赖模型" 说明：worktree 创建不装依赖
  - `dev-stage.md` 新增 "Stage 入口 Preflight：懒装依赖" 段：检测 → symlink 或 install → 记录到 `state.json.stage_contracts.dev.dependency_install`
  - `test-stage.md` 环境准备段补"懒装依赖兜底"：Dev 跳过场景下在 Test 入口补装
- 收益：Feature worktree 创建开销统一 ~1-2s（无 npm/pip 等待），Plan / Blueprint / Review 等纯文档 Stage 无冷启动税；依赖安装发生在真正需要它的 Stage 入口（单次付费）。

### P0-5：状态行第三行 —— 分支 / worktree 语义（STATUS-LINE.md）

- 问题：v7.3.9 状态行只有流程 / 角色 / 功能 / 阶段 / 下一步 + 功能目录路径两行。worktree 启用后，用户肉眼看不到"现在在哪个 worktree、绑定哪个分支、合入目标是什么"——必须翻 state.json 或跑 `git status` 才能确认。并行 Feature 或 Micro 直接改主分支的场景下，这种不可见性容易导致误操作（例如误以为还在 worktree，实际已回到主分支）。
- 处理：`STATUS-LINE.md` 新增第三行规范：
  - 🌿 = 启用了 worktree 隔离（安全）：`🌿 分支：{branch} → {merge_target} | worktree：{path}`
  - 📍 = 直接在分支上操作（谨慎）：`📍 当前分支：{branch} → {merge_target}（⚠️ ...）`
  - 各流程（Feature / 敏捷 / Bug / Micro / Planning / 问题排查）模板与示例同步更新
  - 字段取值优先 state.json.worktree + merge_target，缺失时回退 `git branch --show-current`
- 收益：PMO 每次回复都把分支 / worktree / merge_target 显式化，Micro 场景用 📍+⚠️ 做软兜底防误操作；并行 Feature 场景 worktree 路径直出，减少"在哪改"的混淆。

### P0-6：Codex CLI 宿主兼容性审计（browser-e2e-stage.md + review-stage.md + agents/README.md + templates/codex-cross-review.md + dispatch.md + review-log.jsonl + plan-stage.md + blueprint-stage.md + flow-transitions.md）

- 问题：审计各 Stage 在 Codex CLI 宿主下的可跑通性，发现 3 处强耦合 Claude 生态的表述：
  - **P0-6-A（Browser E2E 工具硬编码）**：`browser-e2e-stage.md` 隐含 `mcp__Claude_in_Chrome__*` / `mcp__gstack__*`，Codex CLI 宿主无此 MCP，Stage 直接跑不通
  - **P0-6-B（Review Stage 外部视角在 Codex 宿主下坍缩为自审）**：Codex CLI 宿主若"用自己当 Codex 外部视角"，则失去 session 隔离的独立性保证，"外部视角"名存实亡
  - **P0-6-C（降级模型硬编码 Sonnet）**：多处文档把"Codex CLI 不可用"的降级路径写死为"Sonnet fallback"，Codex 宿主用户没有 Sonnet 可降，该表述不成立
- 处理：
  - **P0-6-A**：`browser-e2e-stage.md` 新增"浏览器工具宿主适配"块：Claude Code 宿主用 MCP，Codex CLI 宿主走 Playwright/puppeteer 子进程，通用宿主无浏览器工具时降级为 ⏸️ 用户手动验收（带 WARN 日志 + `executor: user-manual` frontmatter）
  - **P0-6-B**：`review-stage.md` 步骤 4 + `agents/README.md §三` + `templates/codex-cross-review.md §二/§六` 统一规则——无论宿主是 Claude Code 还是 Codex CLI，外部视角**都通过 codex CLI 独立 spawn fresh session**（Claude 宿主：Task/MCP 调 codex 子进程；Codex 宿主：prompt 内 spawn `.codex/agents/*.toml` 子 agent）；🔴 明令禁止"外部视角 = Codex 主对话自审"
  - **P0-6-C**："Sonnet fallback" 全部替换为 "🟢 AI 自主规划等效独立审查"，并在 `agents/README.md §三` 新增"降级路径决策（🟢 AI 自主判断）"段：列决策维度（宿主可用模型清单 / 独立性强度 / 任务复杂度 / 成本 / 历史降级）+ 典型可行模式（fresh context 同宿主 / 低成本模型 / 并行双模型投票 / PMO 自审最弱兜底）；要求 AI 在 Execution Plan 或 concerns 写明降级决策理由
  - 同步扫清：`flow-transitions.md` L25 / `plan-stage.md` L225 / `blueprint-stage.md` L96 / `templates/dispatch.md` L78 + L260 + 降级汇总表 / `templates/review-log.jsonl` 示例注释
- 收益：三处"Claude 独有"表述转为宿主无关语义；Codex CLI 宿主可走全流程；外部视角独立性的来源从"不同模型"重定义为"fresh session 隔离"（可叠加跨模型做强形式）；降级策略从硬编码转为 AI 自主决策 + 理由留痕。

### P0-7：文档基准锚定（templates/ 格式权威 · TEMPLATES.md + roles/pmo+pm+rd.md + plan-stage.md）

- 问题：实战观察发现 AI 在起草 PRD / state.json / TECH 时倾向于"先参考最近一个 Feature 的格式"而非 Read `templates/` 中的模板。后果：
  - peer Feature 的产物可能装的是老 schema（state.json 尤其敏感，v7.3.2 / v7.3.9 / P0 都有增量字段），抄过去 = 漂移放大
  - peer Feature 可能被手动改过格式，漂移会扩散到新 Feature
  - templates/ 下模板齐全但没有任何文档声明它是"格式唯一真相源"，AI 的最近邻检索本能占上风
- 处理：新增"格式权威"契约，显式规定 templates/ 为唯一格式真相源：
  - `TEMPLATES.md` 顶部新增"🔴 格式权威红线"块：templates/ = 格式唯一真相源 / 禁止以 peer Feature 产物为格式基准 / peer Feature 仅可作内容参考 / state.json 特别注意
  - `roles/pmo.md` 顶部（职责段后）加"🔴 格式权威守门"：PMO 作为流转守门员对格式合规性负责，禁止在 Execution Plan 说"先参考最近一份 X 格式"
  - `roles/pm.md` 实现原则后加"🔴 PRD 格式权威"：起草 PRD 前 Read templates/prd.md 为基准
  - `roles/rd.md` 开发前必读后加"🔴 TECH / TC 格式权威"：起草前 Read templates/tech.md + templates/tc.md 为基准
  - `stages/plan-stage.md` PM 起草 PRD 步骤内插入"格式基准锚定"子条（v7.3.9+P0-7 硬规则）
- 收益：AI 的"抄邻居"本能被显式红线拦截；三角色（PMO 守门 / PM 起草 PRD / RD 起草 TECH+TC）都有对应条款；peer Feature 仅可作内容参考的语义清晰；state.json schema 漂移风险收敛。

### P0-8：跨项目依赖识别前置（FLOWS.md + roles/pmo.md + templates/dependency.md + stages/plan-stage.md）

- 问题：实战观察到 AI 在消费方 Feature 识别到"需要其他子项目能力"时，自由发挥：
  - 自创 DEPS.md（非 teamwork 标准文件名）
  - 放在消费方 Feature 目录（应放**上游子项目** `{upstream}/docs/DEPENDENCY-REQUESTS.md`）
  - 不读 templates/dependency.md 为格式基准（叠加违反 P0-7）
- 根因：templates/dependency.md 模板齐全，但 PMO 初步分析输出格式里没有「🔍 跨项目依赖识别」触发项；roles/pmo.md 的"跨子项目需求拆分"只覆盖场景 B（横跨多子项目 naturally），没显式区分场景 A（单 Feature 上游依赖）
- 处理：显式区分两种场景 + 前置触发 + 强绑定 templates/dependency.md：
  - `FLOWS.md` PMO 初步分析输出格式新增「🔍 跨项目依赖识别」项（和「🔍 跨 Feature 冲突检查」并列）：扫描上游依赖信号 → 场景 A（上游 `DEPENDENCY-REQUESTS.md` 追加 DEP-N）/ 场景 B（走跨子项目拆分）/ 无依赖
  - `FLOWS.md` 同时新增「📋 本轮拟产出文档清单」项（强化 P0-7 格式权威露出）：每份产物对应 templates/ 路径，PMO 声明 Write 前必 Read 模板
  - `roles/pmo.md` 新增「🔗 跨项目依赖识别」专门章节，详述场景 A 处理流程与硬规则：DEPENDENCY-REQUESTS.md 只放上游子项目目录 / 禁止消费方 Feature 目录自创文件 / 多条依赖分散到多个上游子项目
  - `templates/dependency.md` 顶部加"何时触发使用"说明（消费方 / 被依赖方各自触发点）+ 回链 roles/pmo.md
  - `stages/plan-stage.md` PM 起草 PRD 步骤加「跨项目依赖前置」硬规则：PM 发现上游依赖 → 立即通知 PMO 走场景 A（而非等 PRD 写完再补）
- 收益：消费方 Feature 遇上游依赖有明确流程可套；DEPENDENCY-REQUESTS.md 回到标准位置（上游子项目目录）；templates/dependency.md 触达面打开；P0-7 格式权威在 PMO 初步分析模板里露出，触达面从"藏在 roles/ 里"升级到"每次初分析都显式"。

### P0-14：Dev Stage 默认主对话 + RD 自行规划 Plan 模式（rd-develop.md + dev-stage.md + agents/README.md + feature-state.json）

- 触发：用户反馈"开发阶段在主对话，是否合理，不要求在 subagent，由 RD 自行规划 Plan 模式"。审计发现 v7.3.9 虽声称"Dev Stage AI 自主判断"，但 3 处残留默认偏向 subagent：
  - `agents/rd-develop.md` 整篇以"RD Subagent"视角书写（标题 / 执行摘要 / 自检触发条件均内嵌"subagent"措辞）
  - `templates/feature-state.json` planned_execution.dev 示例直接写 approach="subagent"
  - `agents/README.md` §一默认表虽写"AI 自主"，但判断条列"≤3 文件 → main"，隐含 >3 文件即 subagent 的保守基线
- 决策：**Dev Stage 默认 `main-conversation`**；subagent 降为 opt-in 路径（TECH.md 文件清单 >10 / 预期产出 >500 行 / 需独立聚焦或跨模型独立性时使用）；RD 在 AI Plan 阶段自评规模 + 声明 Rationale。
- 根因分析：
  - 主对话模式对大多数 Feature（单模块、改动 ≤10 文件、产出 ≤500 行）更优：省冷启动（3-5 min subagent 税）、TDD 过程用户可见、多轮调试不用重启 context、Plan/Blueprint 已加载的 PRD/TC/TECH 可直接复用（省 5-10K token 重读）
  - 原"AI 自主"措辞被"subagent 默认"的细节稀释 —— RD 启动时若第一眼看到 rd-develop.md 整篇 subagent 语境 + state.json 示例 subagent + README 表"≤3 文件才 main" → 自然默认选 subagent
  - subagent 的独立性价值在 Dev Stage 相对其他 Stage 弱：Review Stage 的 Codex / QA 独立性来自跨模型 + 盲区兜底；Dev Stage 是 RD 单视角执行，独立性收益不显著，冷启动税却实打实
- 处理（4 文件 + dual-mode 契约）：
  - **§一 rd-develop.md dual-mode 化**：标题从"RD Subagent：TDD 开发 + 自查"改为"RD 开发执行规范：TDD 开发 + 自查（Dual-Mode）"；新增 7 维对比表（启动方式 / 上下文 / 输入来源 / 用户可见性 / 进度汇报 / 最终输出 / 适用场景）+ 5 条 🔴 共同契约（TDD / UI 还原自检 / 自查 7 维度 / 产物格式 / auto-commit）；§二 输入文件加模式对比（主对话直读 + 可复用已加载 vs subagent 按 dispatch 硬读）；§四 执行摘要拆 4.1a 主对话（边做边汇报模板 + 5 个阶段性节点）+ 4.1b subagent（完成后一次性返回含 TDD 阶段耗时）；§四.2 RD 自查报告 + §四.3 上游问题清单两模式一致不变；UI 还原 NEEDS_FIX 自降规则改"两种模式一致"
  - **§二 dev-stage.md AI Plan 指引改写**：条件表从"AI 自主按规模判断"升级为"默认 main-conversation + 超阈值 opt-in subagent"5 行条件：默认无特别信号 → main / 文件 >10 或 >500 行 → subagent / 跨模型独立性 → subagent / 多轮调试跨 Feature → main 强化 / 灰色地带向默认倾斜；新增 3 条灰色地带判定示例（10 文件/400 行/单模块、12 文件/600 行/跨前后端、8 文件/300 行/3 轮 TDD 调试）；Duration baseline 前置主对话路径（≤3 文件 15-25 / 5-10 文件 30-60）+ subagent 档（>10 文件 30-90 含冷启动税）
  - **§三 agents/README.md §一默认表**：Dev Stage 行从"AI 自主按规模判断"改为"main-conversation（v7.3.9+P0-14 默认）"；判断列改"默认主对话；TECH 文件清单 >10 / 预期产出 >500 行 / 需独立聚焦 → subagent（opt-in）"
  - **§四 feature-state.json 示例**：planned_execution.dev 主示例改 approach="main-conversation" + rationale 引用 P0-14 默认 + 无 dispatch_file 字段（加 `_dispatch_file_comment_v7.3.9+P0-14` 解释）；保留 `_subagent_alternative_example` 子对象作为 opt-in 样例（TECH >10 文件的场景）
- 收益：
  - 默认 Feature 节省 3-5 min subagent 冷启动 + 5-10K token（复用 Plan/Blueprint 已加载产物）
  - TDD 过程用户可见 → 早发现方向偏差 / 提前介入多轮调试
  - Subagent opt-in 通道保留，大改动 / 跨前后端场景不牺牲独立聚焦
  - RD 自查 + UI 还原自检 + NEEDS_FIX gate 两模式完全一致，契约不变
  - dual-mode 表 + rationale 要求 → RD 在 Plan 阶段的判断更透明（retro 可统计默认采纳率、subagent opt-in 比例）
- 兼容性：
  - 既存 Feature（已完成 Plan/Blueprint）不受影响；Dev Stage 未启动的 Feature 进入 Dev Stage 时按新默认
  - 既存 dispatch_log（已派发 subagent 的 RD 任务）保持有效 —— subagent 模式路径完整保留，只是不再是默认
  - state.json schema 不变（approach 字段早已支持 main-conversation / subagent / hybrid）
  - rd-develop.md dual-mode 化后 Codex CLI 子 agent（若有）仍可按原 prompt 调用（subagent 模式契约未变）
- 未变更：
  - TDD 红-绿-重构三步流程（§三.1）/ 开发约束（§三.2）/ RD 自查 7 维度（§三.3）/ UI 还原权威层级 + 自检清单（§三.4，P0-12 成果）全部保持不变
  - DONE / NEEDS_FIX / FAILED 三态 gate + UI 还原缺失自降 NEEDS_FIX 规则不变
  - Review Stage 三视角契约不变（本 P0 只改 Dev Stage 执行方式默认）
  - Codex CLI 子 agent / subagent dispatch.md 协议 / standards/{common,backend,frontend}.md 加载规则均保持

### P0-13：Plan/Blueprint Codex 交叉评审 降为 opt-in 默认 OFF（成本治理 · templates/codex-cross-review.md + plan-stage.md + blueprint-stage.md + roles/pmo.md + FLOWS.md + feature-state.json）

- 触发：用户明确反馈"Feature 流程每次都强制 Codex 成本太高，PRD 流程也不需要"。审计发现 Plan + Blueprint Stage 的 Codex 交叉评审每次 +10-20 min + ~10K token，对小改动 / 内部视角已充分的场景 ROI 偏低。
- 决策：**Plan + Blueprint Stage** 的 Codex 交叉评审从 🔴 强制降为 🟡 opt-in 默认 OFF；**Review Stage** 的 Codex 代码审查保持 🔴 强制不变（其盲区独立采样 + 静态分析价值最高，且是代码层最后一道质量 gate）。
- 根因分析：
  - Plan/Blueprint 产物为文档（PRD / TC / TECH），内部多视角评审（PM + PL + RD + Designer + QA + PMO + 架构师）已覆盖质量下限；Codex 的增量价值随 Feature 规模递减
  - Review Stage 的 Codex 是代码层盲区兜底，与其他场景不同 —— 代码 bug 进入代码库的代价远高于文档修订，Codex 在此保留强制
  - 先前"🔴 强制"设计偏向保守，缺乏"用户可按风险/规模动态开关"的弹性
- 处理（6 文件 + 3 层开关）：
  - **Schema 层**：`templates/feature-state.json` 新增 `codex_cross_review = {enabled, decided_at, decided_by, note}` 字段，默认 `enabled: false`；_comment 明确 Review Stage 不受本开关影响
  - **决策点层（PMO 初步分析）**：
    - `FLOWS.md` PMO 初步分析输出格式 4 种变体（Feature / 敏捷需求 / Feature Planning / 跨子项目）追加「🤖 Codex 交叉评审决策」行，4 选 1 默认不开
    - `roles/pmo.md` 新增「🤖 Codex 交叉评审开关决策」独立章节，含建议逻辑（规模/风险信号）+ state.json 写入规范 + 硬规则（默认 OFF / 必须显式输出 / Review Stage 独立）
  - **执行层（Stage 内条件化）**：
    - `stages/plan-stage.md` Input Contract 的 codex-cross-review.md 改为条件必读（`enabled==true`）；Process Contract Step 3 的 Codex 改为 opt-in + 关闭时声明；过程硬规则 5 条 Codex 相关项从 🔴 降为 🟡；Output Contract 表格加条件列（pmo-internal-review / prd-codex-review 仅开启时必需）；机器校验分两组（开启/关闭）
    - `stages/blueprint-stage.md` 同 pattern：本 Stage 职责描述、Input Contract、Process Contract Step 5、过程硬规则、Output Contract 表格、机器校验、Done 判据、AI Plan 模式指引、执行报告模板 全部条件化
  - **治理层**：`templates/codex-cross-review.md` §二适用场景表 Feature / Feature Planning / 敏捷需求的 Plan/Blueprint 列统一改为"🟡 opt-in（默认 OFF）"；新增 §2.1「PMO 初步分析决策」规范 + §八 R7 改写为 P0-13 修订说明 + 明确 Review Stage 独立强制
- 收益：
  - 默认场景节省 10-20 min + ~10K token（小改动 / 单子项目 / 内部视角充分的场景多数符合）
  - 保留 opt-in 通道（大改动 / 跨子项目 / 高风险场景用户主动开启）
  - Review Stage 代码审查保持强制，代码层最后一道 gate 不放松
  - state.json 持久化开关 + 决策留痕（decided_at / decided_by / note）便于 retro 分析采纳率
- 兼容性：
  - 既存 state.json（v7.3.9 + P0-11 及之前）**缺少 codex_cross_review 字段** → PMO 读取时按 "enabled=false" 默认处理（等价"关闭"），不触发迁移
  - 既存 Feature（已完成 Plan/Blueprint）不受影响；当前进行中的 Feature 若已完成 Plan Stage 产物，Blueprint Stage 进入时由 PMO 补写 codex_cross_review（enabled=false，note="既存 Feature 默认关闭"）
  - codex-cross-review.md / codex-agents/*.toml / prd-reviewer / blueprint-reviewer 均保留（开启时走原路径）
- 未变更：
  - Review Stage 的 Codex 代码审查：🔴 强制不变（review-stage.md + codex-agents/code-reviewer.toml）
  - 4 流程（Bug / 问题排查 / Micro / Feature Planning）与 Codex 的关系：Bug / 问题排查 / Micro 本就跳过 Codex；Feature Planning 沿用 Feature 同规则（opt-in 默认 OFF）
  - 降级路径、独立性校验、输出 schema、findings 分类规则：开启时完全复用原规范

### P0-12：preview/*.html 漏传 + UI 还原权威层级（实战漏洞修复 · dispatch.md + dev-stage.md + rd-develop.md + roles/pmo.md）

- 触发：实战 case —— RD 实现页面时"遵循了文字规格却没还原 HTML 预览稿"，PM 验收发现明显偏差，被迫走 Bug 流程。
- 根因分析（两层叠加）：
  - **第一层：preview 漏传**。`templates/dispatch.md` 的 Input files 清单只列了通用项（README / agent md / standards），Feature 产物走占位符 `{其他必需文件绝对路径}`；同时 `stages/dev-stage.md` L30 的必读清单里 `UI.md + preview/*.html` 用"（如有）"措辞，让 PMO 把一定存在的 preview 当成可选 → 起草 dispatch 时漏列。RD subagent 只看 dispatch Input files，不会主动翻 roles/stages，漏列 = 真漏传。
  - **第二层：即便传了也没权威层级**。`agents/rd-develop.md` 原 Step 5 只写"如有 UI → 还原页面"，没定义 preview 和文字规格冲突时谁是权威；LLM 天然偏好结构化文本（PRD/TECH.md）→ 视觉 / 交互偏差。
- 处理（4 文件 + 三层防护）：
  - **第一层（模板硬化）**：`templates/dispatch.md` 新增「🔴 Feature 产物强制白名单」段，按 Stage 列出 blueprint / dev / review / test / browser-e2e 的必选 Feature 产物；Dev Stage 在 `ui_design.output_satisfied==true` 条件下 **显式要求 UI.md + preview/*.html 进 Input files**；附反模式："把 preview 当'可选参考'仅在 Additional inline context 里提一嘴"。
  - **第二层（措辞硬化）**：`stages/dev-stage.md` L30 去掉"（如有）"暧昧措辞，改为条件式："若 `state.stage_contracts.ui_design.output_satisfied==true` → 必读（视觉/交互权威）"；L86 还原段引用 rd-develop.md 的 UI 还原权威层级 + 自检。
  - **第三层（RD 侧权威层级 + 自检）**：`agents/rd-develop.md` 新增 §三.4 「UI 还原（有 preview 时必做）」：
    - 权威层级（冲突时优先级）：视觉/间距/颜色/响应式 → preview 权威；交互状态 → preview 权威，未覆盖看 TECH；业务逻辑 → TECH 权威，禁止照抄 preview mock 数据；验收判定 → TC 权威
    - 冲突兜底：preview 视觉 ≠ PRD 文字 → 以 preview 为准 + concerns 1 行；preview 交互 ≠ TC AC → 以 TC 为准 + concerns
    - UI 还原自检清单（Dev 完成前必做）：视觉 / 交互状态 / 响应式 / 偏离项 concerns / mock 数据未照抄 / preview 未覆盖状态找依据
    - 反模式 4 条
    - 自查表新增 UI 还原 4 行（视觉 / 交互 / 响应式 / 偏离 concerns），**缺失或未贴证据 → 自降 NEEDS_FIX**
  - **PMO 侧硬校验**：`roles/pmo.md` 进入 Stage 的 subagent 路径新增"Feature 产物白名单硬校验"：若 `ui_design.output_satisfied==true` 但 Input files 未包含 UI.md + preview → **PMO 自拒重生**，不得发出。
- 收益：
  - 漏传链路补齐（模板白名单 + 措辞硬化 + PMO 自校验 + Subagent `NEEDS_CONTEXT` 兜底，四层 gate）
  - 权威层级清晰（冲突时有规可循，不再靠 LLM 天然偏好）
  - 自检 gate 可执行（7 项清单 + DONE/NEEDS_FIX 硬绑定，漂移可被拦截）
  - 反模式负向定义（过度还原 / 欠还原 各自拦截，避免从一个坑跳进另一个坑）
- 兼容性：UI Design Stage 未跑的 Feature 流程完全不变；preview 不存在时自检项填 "-" + 说明"无 UI Design 产物"。

### P0-11-B：auto 模式默认跳过 Browser E2E Stage（roles/pmo.md + rules/flow-transitions.md + INIT.md）

- 触发：Browser E2E Stage 启动成本显著（headless 浏览器冷启动 / MCP 握手 / 脚本录制回放），auto 模式下默认应倾向"快速走完主干"。用户明确要求："auto 模式默认不启动 browser-e2e"。
- 处理（3 文件，新增"默认跳过 + 可逃逸 + 必留痕"三件套）：
  - **默认跳过条件**：`AUTO_MODE=true` + Test Stage 完成 + `TC.md` 含 Browser E2E AC → **跳过 Browser E2E Stage**，直接进 PM 验收
  - **留痕（三处，便于事后追溯 / PM 验收判断）**：
    - `state.json.stage_contracts.browser_e2e = {status: "SKIPPED_BY_AUTO", skipped_at, skip_reason}`
    - `review-log.jsonl` 追加一行 `{event: "browser_e2e_skipped_by_auto", feature_id, timestamp}`
    - PMO 输出 `⚡ auto skip: Browser E2E Stage | 💡 直接进 PM 验收 | 📝 AUTO_MODE 默认跳过` 日志
  - **显式标注（PM 验收 / 完成报告）**：PM 验收摘要和完成报告必须打出「⚠️ Browser E2E 已按 auto 模式跳过」提醒
  - **用户逃逸路径（两种）**：
    - PM 验收时选"3 返修"+ 备注「跑 Browser E2E」→ 下轮补跑
    - 下轮命令带「含 browser e2e / 带 e2e / run e2e」关键词 → 例外命中，不跳过
  - **例外（不跳过）**：命令关键词命中 / `TC.md required_even_in_auto=true` / 手动模式（AUTO_MODE=false，原流程不变）
  - **文件落点**：
    - `roles/pmo.md` 豁免表新增 Browser E2E 行 + 新增「🟡 Browser E2E auto 默认跳过（P0-11-B 新增专项规则）」专章（含触发 / 留痕 / 标注 / 逃逸 / 例外 / 设计理由）
    - `rules/flow-transitions.md` 顶部 auto 豁免速查增补 Browser E2E 子块
    - `INIT.md` Step 0 速查表补一条"Browser E2E auto 默认跳过"规则
- 设计理由：
  - Browser E2E 启动成本明显高于其他 Stage（浏览器进程 / 录屏 / 网络往返），auto 的设计目标是"压暂停点"而非"压成本"，但 Browser E2E 是单 Stage 成本占比最高的一环，跳过的 ROI 显著
  - PM 验收本就是 auto 模式下的强制保留点（业务决策），Browser E2E 缺失由 PM 在验收时决定是否补跑，链路闭环
  - 三处留痕确保"跳过"可审计、可回溯、不静默
- 收益：auto 模式全链路时长显著缩短（省去 Browser E2E Stage 整段）；用户可通过"关键词显式要 E2E"或"PM 验收补跑"双通道保留覆盖能力；跳过决策留痕三处，事后可查。
- 兼容性：手动模式（AUTO_MODE=false）流程完全不变；`TC.md required_even_in_auto=true` 是显式覆盖开关，向前兼容。

### P0-11-A：auto 模式豁免/保留边界修订（实战漏洞修复 · INIT.md + roles/pmo.md + flow-transitions.md）

- 触发：P0-11 落地首轮实战，用户 `/teamwork auto ... 推进到 Blueprint 完成` 命令被中间"外部依赖已就绪 → 恢复流程"暂停点卡住。根因：P0-11 原强制保留清单把"外部依赖恢复"归为保留，与 auto 模式设计意图直接冲突。
- 根因分析：
  - 暂停点的本质 = 请求用户给出**决策内容**
  - 若决策内容已被 `/teamwork auto [推进/恢复/继续...]` 命令语境承载 → 再停下来要一次确认 = 把命令意图当空气
  - 强制保留的合理边界 = 需要**新**决策内容（业务判断 / 技术分歧 / 破坏性授权 / 红线处理）
- 处理（3 文件）：
  - **新增元规则「意图承载豁免」** 写进 `roles/pmo.md` + `rules/flow-transitions.md` + `INIT.md`：判定前先问「此暂停点需要的决策内容是否已被 auto 命令承载？」；是则豁免，否则保留
  - **从强制保留清单移除 2 项**（归入豁免）：
    - ~~外部依赖已就绪 → 恢复流程~~ → 豁免：auto 命令已承载"恢复"意图
    - ~~Planning / PL 模式的最终确认~~ → 豁免：auto 命令已承载"推进"意图（且原豁免表已有 Roadmap / teamwork_space / Workspace Planning 收尾行覆盖）
  - **新增 Test Stage 前置确认 到强制保留**（原遗漏补齐）：跨 Feature 节奏决策，需用户判断立即 / 延后 / 跳过
  - 强制保留清单从 15 项收敛到 **13 项**（边界更锐利）
  - **反模式样例**写进文档：「auto 命令明说推进到 X，却被中间恢复确认卡住 = 把用户意图当空气」
- 收益：
  - auto 模式实战可用——用户给定终点的命令不会被"你确定要继续吗"类暂停点坍缩
  - 强制保留语义从"列表式枚举"升级为"决策类型判定"，新暂停点上线时可按元规则快速归类
  - 反模式样例给 PMO 自检提供具体参照

### P0-11：⚡ auto 模式（一次性总开关，INIT.md + roles/pmo.md + flow-transitions.md + STATUS-LINE.md）

- 背景：teamwork 暂停点密集（Feature 流程单次跑全流程 10+ 次 ⏸️），对"我已经心里有数、按你建议走"的场景体验重。需要一个一次性总开关让 PMO 按 💡 自动推进，同时保留关键决策的强制暂停。
- 设计取舍（6 点均按用户"按建议"确认）：
  1. **入口命令**：`/teamwork auto [需求]` / `/teamwork auto 继续` / `/teamwork auto ship F{编号}`（第一个 token 为 `auto` 开启）
  2. **作用域**：单次命令周期（仅本次 /teamwork 生命周期有效）；用户重新 `/teamwork`（不带 auto）自动重置；compact 后默认 false；**不写 localconfig / state.json**（避免"以为关了其实没关"）
  3. **豁免范围**：普通方案 review / 阶段切换 / preflight 默认值 / PRD-UI-TC-TECH 草稿 review / dispatch 前检 / review 结果接受
  4. **强制保留 15 项**（按 roles/pmo.md 强制保留清单）：PM 验收三选项 / Ship 关键操作 / Blueprint concerns / MUST-CHANGE / 破坏性操作 / 13 红线 / Micro 用户验收 / 外部依赖解锁 / 意图不确定语气 等
  5. **与 ship_policy 正交**：auto 是 session 级总开关，ship_policy 是 Ship Stage 细粒度；auto **不覆盖** `ship_policy=confirm`
  6. **关闭方式**：命令级（下次不带 auto 即手动）+ 运行时（用户消息含「停 / 暂停 / manual / 等一下 / 先等等」立即关闭）
- 处理（5 文件）：
  - `INIT.md` 启动必做前加 **Step 0**：解析 `/teamwork auto` 命令行 + 速查豁免与强制保留清单
  - `roles/pmo.md` 在 "⚡ PMO 自动推进规则" 后新增 **"⚡ auto 模式暂停点豁免规则"** 章节：触发时机 / 豁免表 / 强制保留 15 项表 / 跳过日志格式 / 强制保留命中提示格式 / PMO 自检清单 / 运行时关闭
  - `rules/flow-transitions.md` 顶部新增 **"⚡ auto 模式豁免速查"** 块：列出所有强制保留行号+理由；给出典型豁免示例（其余默认豁免）
  - `STATUS-LINE.md` 第一行格式增加可选 **`⚡ AUTO` 徽章**（AUTO_MODE=true 时在 `🔄 Teamwork 模式` 和 `|` 之间显示）+ 状态行规则 + 示例
  - 跳过日志：`⚡ auto skip: {决策简述} | 💡 {建议} | 📝 {理由}` 每次豁免输出一行，便于追溯
- 收益：
  - 一次性开关覆盖高频 ⏸️，用户体验从"每步都要回确认"降到"关键处再决策"
  - 作用域仅 per-command，不污染 localconfig，降低"隐藏状态"事故面
  - 强制保留清单明确兜底所有破坏性 / 业务判断 / 红线场景
  - 跳过日志 + 徽章让"auto 到底替我做了什么"完全可见
  - 与 P0-9（worktree 默认 off）形成对称：worktree 需显式 opt-in，auto 也需显式 opt-in；不隐藏复杂性

### P0-9：worktree 保留默认 off（设计决策 · templates/config.md + INIT.md 决策注释）

- 背景：曾考虑把 worktree 默认从 off 翻转到 auto（让新用户开箱即得并行隔离），深入讨论后回撤，**保留 off 为默认**。
- 回撤理由（四个税点，默认 auto 让新用户透明付费不合理）：
  1. **megarepo 全量 checkout 代价**：`git worktree add` 不支持按子目录稀疏 checkout（需额外配 `git sparse-checkout`）；大仓并行 3 个 Feature = 3 份全量工作树（每份 ~GB 量级），磁盘 / IDE 索引 / 工具链遍历开销显著
  2. **IDE review 不便**：worktree 在 sibling 目录下，IDEA 单 Project 窗口看不到其他 worktree 的代码 / 文档；VS Code 需要 Multi-root Workspace 配置；跨 worktree Cmd+Click / 搜索被割裂
  3. **`.worktree/` 内嵌方案的隐性长尾**：即便内嵌到项目根 + `.gitignore`，仍需为每个扫描项目根的工具（tsc / eslint / prettier / jest / pytest / webpack / nx / turbo / docker / IDE LSP / CI find-grep）单独维护排除规则——新工具加入默认踩坑
  4. **默认 auto 把复杂性隐藏**：用户不理解 worktree 语义时遇到上述问题会困惑，把选择权还给用户（显式 opt-in）更稳
- 处理：保持 off 为默认 + 把决策理由注释到 localconfig 模板：
  - `templates/config.md` 保留 `worktree: off`；注释块新增"保留 off 为默认的原因"四点说明，引导用户 opt-in 前先评估 P0-10 的 worktree_base + IDE workspace 自动配置（待实施）
  - `INIT.md` localconfig 不存在分支保持"默认 scope=all，worktree=off"，加提示"如需并行 Feature 隔离，主动改 localconfig 为 auto/manual"
  - `docs/OPTIMIZATION-PLAN.md` 历史记录段保持"默认 off"
- 收益：对初学者友好（不引入 worktree 的 megarepo / IDE review / 工具链忽略复杂性）；有需要的用户显式配置 auto/manual 时自担理解成本；为 P0-10（worktree 路径合法性 + 分组 `../.{repo}-worktrees/` + IDE workspace 自动生成）铺好 opt-in 路径。

### P0 影响面（非破坏性）

```
├── state.json schema：兼容（P0-3 新增 dev.dependency_install 可选字段；P0-2 plan_preflight.checks._note 注释；P0-5 复用既有 worktree + merge_target 字段；P0-6 无 schema 变化；P0-7 无 schema 变化，纯契约文档加强；P0-8 复用既有 blocking.pending_external_deps 字段；P0-9 决策保留默认 off · 无默认值改动；P0-11 AUTO_MODE 纯运行时状态，不写 state.json / localconfig）
├── localconfig：无新增字段（P0-11 刻意不持久化 AUTO_MODE）
├── 历史 Feature：完全兼容（P0 是描述修正 + 文案抽取 + 渲染增强 + 宿主适配 + 格式权威契约 + 依赖识别前置 + 一次性 auto 总开关，不改流程语义）
└── CI / 工具链：无影响（P0-6-A 浏览器工具为宿主可选，项目未启用 Browser E2E 不受影响；P0-7/P0-8/P0-11 纯文档与运行时规则；P0-9 设计决策）
```

### P0 后未涉及的内容

```
- Ship Stage / PM 验收三选项 / merge_target 三层解析：保持 v7.3.9 定义
- 红线 #1 例外条款：保持 v7.3.9 定义
- Micro 流程 worktree 方案：暂缓（见 docs 讨论，待真实需求再做）
```

---

## v7.3.9 —— PM 验收三选项 + Ship Stage + 每阶段 auto-commit + Plan Stage 入口 Preflight

背景：v7.3.4 的 PM 验收合并暂停点（验收 + commit + push 三项打包）存在 3 个结构性缺陷：
1. **合并目标缺省硬编码**：push 目标默认 `origin/{feature branch}`，用户真正的目标分支（staging / develop）无处配置，合入动作被迫延后到命令行手工解决
2. **单暂停点承载过多决策**：验收 + commit 策略 + push 策略 + 目标分支挤在一个暂停点，用户必须一次回答完，错一个选项回退代价极高
3. **冲突 / 净化 / rebase 无流程位**：push 前是否需要 rebase、feature 分支有无需要净化的残留 commit（debug 文件、合并遗留）、冲突解决授权——这些本质是 Ship 流程问题，塞在 PM 验收里越想越不对

同时在使用过程中发现另一个风险源：**Feature 的全部产物（PRD/UI/TC/TECH/代码/测试）都从 Plan Stage 开始累积**。如果 worktree 基于错误的 base 分支（陈旧 main 而非 origin/staging），到 Ship 时 rebase onto staging 会遇到大规模冲突——此时产物已成定局，回退代价高于 Ship 本身。v7.3.8 的"前移 worktree 创建"只解决了隔离问题，没解决 base 问题。

本版把 v7.3.4 的 PM 验收合并暂停点**拆解成 3 段**，并在 Plan Stage 入口加一层 preflight：

```
v7.3.4（旧）：PM 验收 → ⏸️（3 选 1 全打包）→ 完成 / 合入
v7.3.9（新）：PM 验收 → ⏸️ 3 选 1（业务判断）→ Ship Stage（PMO 自主合并） → ⏸️ 2 选 1（push 目标分支或仅本地）→ ⏸️ worktree 清理 → 完成
            ↑
            Plan Stage 入口 preflight（v7.3.9 新增）提前锁定 base 分支，防止 Ship 时灾难
```

### 1) PM 验收三选项（roles/pmo.md + rules/flow-transitions.md）

- **选 1**：通过 + Ship → 进入 Ship Stage（独立 Stage）
- **选 2**：通过但暂不 Ship → PMO 执行 `git push origin {feature branch}` 归档 `shipped: false`，后续可 `/teamwork ship F{编号}` 触发
- **选 3**：不通过（有建议）→ 按问题类型回退（功能缺陷 → Review Stage / 测试遗漏 → Test Stage / UI 不符 → UI Design / 需求偏差 → Plan Stage），前序 commit 保留，修复循环 ≤3 轮

### 2) Ship Stage（新建独立 Stage，stages/ship-stage.md）

- **PMO 自主执行 Step 1-4**：净化 → push feature → rebase 可选（`ship_rebase_before_push` 默认 false，多人场景兼容）→ 本地 merge --no-ff onto `merge_target`
- **单一暂停点 2 选 1**：merge + push `{merge_target}` / 仅本地 merge 不 push
- **worktree 清理暂停点**：worktree ≠ off 时询问清理 / 保留
- **冲突授权**（红线 #1 例外）：PMO 可直接解 git marker 冲突（前提：前序 DONE + 单测全绿 + 解完重跑单测）；不满足升级 ⏸️ 用户决策
- **Sanitize 日志**：residual_commits（待审）/ cleaned_files（已处理）/ suspicious_files（灰名单仅报不动，用户决定）

### 3) 每阶段 auto-commit 硬规则（stages/dev-stage.md + review-stage.md + test-stage.md + browser-e2e-stage.md）

- 每个 Stage `output_satisfied=true` 之前 PMO 执行 `git status --porcelain`
- 非空 → PMO auto-commit `git add -A && git commit -m "F{编号}: {Stage} Stage - {简述}"`，commit hash 写入 `state.json.stage_contracts.{stage}.auto_commit`（单值）或 `auto_commit[]`（多轮修复）
- 目的：每个 Stage 产物落地即 commit，Ship Stage 不再需要"一次性收拾"所有遗留改动；同时给 Review Stage 提供稳定 diff 锚点

### 4) Plan Stage 入口 Preflight（stages/plan-stage.md + roles/pmo.md）

- PMO 在用户确认流程类型后、Plan Stage 产物诞生前执行 6 项校验：
  - 🔴 硬门禁：worktree 策略无残留 / 分支名无冲突 / base 分支可达
  - 🟡 软提示：工作区干净 / merge_target 解析清晰 / Feature 编号命名合规
- **worktree 创建显式指定 base**（v7.3.9 关键改动）：
  ```bash
  git fetch origin {merge_target}
  git worktree add ../feature-{全名} -b feature/{全名} "origin/{merge_target}"
  ```
- state.json 新增 `stage_contracts.plan_preflight` 记录 6 项校验结果 + base_branch

### 5) merge_target 配置三层解析（templates/config.md + feature-state.json）

- 优先级：`state.json.merge_target` > `.teamwork_localconfig.md` 中 `merge_target` > 默认 `staging`
- 新增 localconfig 字段：`merge_target` / `ship_rebase_before_push` / `ship_policy` / `worktree_cleanup`
- state.json 新增顶层 `ship` 块（sanitize_log / rebase_status / merge_commit_hash / push_status / worktree_cleanup / shipped）

### 6) 红线 #1 例外条款（INIT.md + SKILL.md）

- v7.3.9 新增 Ship Stage 冲突解决例外：PMO 可直接解 git marker 冲突，前提：前序 DONE + 单测全绿 + 解完重跑单测通过
- 不满足则升级为 ⏸️ 用户决策

### 7) flow-transitions.md 更新

- PM 验收行拆为 5 行（PM 验收三选项 / Ship Stage / merge+push 待确认 / worktree 清理待确认 / Ship Stage 冲突回退）
- PMO 初步分析 → Plan Stage 之间插入 Plan Stage 入口 preflight 暂停点

### 为什么这样拆（设计取舍）

| 候选设计 | 评估 |
|---------|------|
| ~~PM 验收暂停点内嵌 Ship 策略~~（v7.3.4）| 单点决策过多，回退代价高，用户体感卡 |
| ~~Ship 整个走 Subagent~~ | Feature 最后一步，主对话 context 已沉淀，新 Subagent 要 /clear 反而丢失一致性 |
| **Ship Stage 由 PMO 自主执行 + 两段暂停** ✅ | 决策维度清晰（业务判断 vs 合入策略 vs 清理策略），每段单点决策 |
| ~~Ship 时一次性 commit 所有 Stage 遗留~~ | 破坏 Stage 边界，diff 锚点模糊，review 困难 |
| **每 Stage 独立 auto-commit + Ship 仅净化** ✅ | Stage 产物落地即 commit，Ship 只解决 git 异常 |

### 不改动项（仍保留）

- Worktree 创建触发点仍在 Plan Stage 入口（v7.3.8 定稿）
- 默认 `worktree` 值仍为 `off`
- PMO 非 Micro 流程下不得改代码的红线 #1 主干不变（仅加 Ship Stage 例外）
- Review / Test / Browser E2E 的产物契约不变（只加 auto-commit 过程规则）

### 操作影响

- **新 Feature**：经历 6 步（preflight → Plan → ... → PM 验收 → Ship → 清理），每步暂停点用 1/2/3 编号单点决策
- **进行中 Feature**（v7.3.8 及之前启动）：到达 PM 验收时按新流程分叉（无 preflight 重跑），已累积的 commit 由 auto-commit 硬规则补齐
- **单分支用户**（merge_target = main）：ship_rebase_before_push = true 更合适，通过 localconfig 显式配置

## v7.3.8 —— Worktree 创建时机前移至 Plan Stage 入口

背景：v7.1 引入 worktree 集成，触发点放在"方案待确认 → Dev Stage"的流转（即 Blueprint 结束后）。这意味着 **Plan Stage 的 PRD/discuss/评审产物、UI Design 的 UI.md、Blueprint 的 TC/TECH**——一整套 Feature 早期文档都**落在 main 分支上**。这违反了 worktree 隔离的初衷：
- 用户拒绝 PRD → 一堆文档孤儿留在 main，要么 revert 要么保留
- v7.3.7 引入的 Codex 交叉评审读的是主分支 PRD，受 main 并发修改干扰
- 跨 Feature 并行时 Plan 阶段文档互相污染（F042 的 PRD 在 F043 工作区可见）

本版把 worktree 创建触发点从 Dev Stage 前移到 **Plan Stage 入口**（"PMO 初步分析 → Plan Stage"的流转上），让 Feature 一启动就进入自己的分支。

- **rules/flow-transitions.md**：Feature 流程触发点从第 19 行（方案待确认 → Dev Stage）移到第 11 行（PMO 初步分析 → Plan Stage）；敏捷需求流程对应在"PMO 分析 → 精简 PRD 编写"触发；Micro 流程在"PMO 分析 → Micro 变更说明"触发（分支名用 `chore/*`）
- **stages/plan-stage.md**：新增 §Worktree 集成段（触发时机 / auto 命令 / state.json 写入 / 降级链），前置依赖增补 "worktree 已创建切换" 条款
- **stages/dev-stage.md**：§Worktree 集成改为"校验存在 + 必要时补建"；补建场景（路径缺失 / 分支不匹配）作为异常分支保留，触发时写 WARN 到 state.json.concerns
- **INIT.md**：修正 "Dev Stage 前按策略创建" → "Plan Stage 入口按策略创建"

### 为什么是 Plan Stage 入口而不是其他点

| 候选 | 评估 |
|------|------|
| ~~Dev Stage 入口~~（v7.3.7 前）| Plan/UI/Blueprint 产物已落 main，隔离迟到 |
| ~~PMO 初步分析之前~~ | 用户还没确认流程类型，可能跳流程（走 Bug / 问题排查），空建 worktree 浪费 |
| **PMO 初步分析确认后，Plan Stage 入口** ✅ | 流程类型已定，第一份产物（PRD）就入 feature 分支 |
| ~~按 Stage 动态切换~~ | 每阶段切 worktree 碎片化，state.json 记录复杂度爆炸 |

### 分支命名规范（v7.3.8 正式化）

| 流程 | 分支名 | worktree 路径 |
|------|--------|--------------|
| Feature | `feature/{子项目缩写}-F{编号}-{功能名}` | `../feature-{...}` |
| 敏捷需求 | `feature/{子项目缩写}-F{编号}-{功能名}`（同 Feature）| `../feature-{...}` |
| Bug 处理 | `bugfix/{子项目缩写}-B{编号}-{摘要}` | `../bugfix-{...}` |
| Micro | `chore/{Micro 摘要}` | `../chore-{...}` |
| 问题排查 | （按需，通常不建）| - |

### 降级链（auto → manual → off）

每档降级必须写 WARN 到 `state.json.concerns`：
- `auto` 失败（git 不可用 / worktree add 错误 / 磁盘不足）→ 降 `manual`
- `manual` 用户 2 次未响应 → 降 `off`
- `off` → 所有阶段在当前工作区执行，跨 Feature 约束回退为人工注意力（原 v7.3.7 行为）

### 不改动项（仍保留）

- **默认值** 仍为 `off`（降低新用户门槛；建议 1 未落地）——已启用 teamwork 的用户可显式改为 auto
- **清理时机** 仍在 commit+push 完成后，PMO 询问用户（不自动删）
- **命令规范** 仍用标准 `git worktree add/remove/list`

### 操作影响

- **新 Feature**：启动即进入 feature 分支，所有阶段产物自然隔离
- **进行中 Feature**（v7.3.7 及之前启动）：不做迁移，保持原路径完成
- **worktree=off 用户**：零影响，行为不变

## v7.3.7 —— PRD/Blueprint Codex 交叉评审 + Progress Log 实时轮询

本版解决两个独立问题：
1. Codex 交叉评审之前只存在于 Review Stage（代码审查），Plan Stage 的 PRD 和 Blueprint Stage 的 TC+TECH 缺少外部视角保底，导致同模型多角色评审的注意力盲点无法被捕获
2. v7.2 建立的 Progress Log 三段式协议声明"Subagent → 主对话无实时通道"——这是**反事实陈述**，文件系统本身就是天然的异步实时通道。主对话读 dispatch 文件可随时获取进度，无需宿主 API 支持

### 1) Codex 交叉评审扩展到 Plan / Blueprint Stage

- **新建 `codex-agents/prd-reviewer.toml`**：Plan Stage PRD 外部评审 agent，独立性通过产物 frontmatter (`perspective: external-codex` + `files_read` grep) 强制，`sandbox_mode = read-only`
- **新建 `codex-agents/blueprint-reviewer.toml`**：Blueprint Stage TC+TECH 外部评审 agent，Step 5 在 4 步内部闭环（QA TC → TC 评审 → RD TECH → 架构师评审）之后执行
- **新建 `templates/codex-cross-review.md`**（230 行）：6 项 checklist (C1-C6) 针对 PRD 和 TC+TECH 两个变体、YAML 输出 schema、PMO 整合流程（ADOPT/REJECT/DEFER 分类）、降级处理、成本治理
- **stages/plan-stage.md**：多视角评审 4 → 5（加 Codex），新增 pmo-internal-review.md 作为 dispatch 前置（≥3 条实质 finding），PRD-REVIEW.md 尾部加「Codex 交叉评审整合」section
- **stages/blueprint-stage.md**：4 步闭环后追加 Step 5 Codex 交叉评审；TC-REVIEW/TECH-REVIEW 分别 append Codex 整合段；独立性 grep 校验加入机器可校验清单
- **templates/review-log.jsonl**：stage 枚举新增 `plan-codex-review` / `blueprint-codex-review`；补两者建行规则 + 示例行
- **codex-agents/README.md**：索引表增补两行

### 2) Progress Log 升级：四段式协议，支持运行中轮询

- **templates/dispatch.md Progress Log 段修订**：
  - 双重目的明确：运行中（主对话并发 Read）+ 运行后（PMO 时间轴回放）
  - 🔴 新增 **Append 语义硬规则**：`f.write() + f.flush() + os.fsync()` / shell `>>` / Edit 工具，禁止 buffered I/O 导致主对话读到空段误判卡死
  - 反模式表新增 2 条：buffered append、主对话绕过 Progress Log 读 session JSONL
- **templates/dispatch.md PMO 使用流程新增 Step 2.5（Subagent 运行中 — 主对话按需轮询）**：
  - 触发条件：用户问进度 / >5min dispatch / 并行多路
  - 读法：offset 跳到 Progress Log 段 + 增量对比
  - 节奏上限：用户触发即读，不建议 <10s tight loop
  - 🔴 显式禁止读 subagent session JSONL 当进度源（格式不稳定、非协议产物）
- **设计原则 #8 修订**：三段式 → **四段式**（前置预声明 / 中途自述 / 运行中轮询 / 事后回放）；删除"无实时通道"的反事实陈述
- **agents/README.md §2.5 + §五 Progress 可见性协议**同步修订：四段式协议、flush 语义、运行中轮询明细（相同修订在两个文件落地保证一致）

### 为什么要纠正"无实时通道"陈述

v7.2 起的原版陈述是基于宿主 Task/Agent API 同步阻塞推出的。这个推论本身没错——宿主 API 确实同步。但结论错了：**Subagent 和主对话共享文件系统**，Subagent 写 dispatch 文件、主对话随时 Read 同一文件，这就是异步实时通道。v7.3.7 前用户问"Subagent 现在到哪步了？"时，主对话会引用不存在的"规范禁止读 transcript"搪塞，实际上协议允许的正确操作是 **Read dispatch 文件的 Progress Log 段**。本版把这个隐含能力显式化为协议条款。

### 操作影响

- **Subagent 作者**：原有 Progress Log 逻辑照跑，仅需保证 append 时 flush（Python 加 `f.flush(); os.fsync(f.fileno())`；shell/Edit 天然满足）
- **主对话 / PMO**：用户问进度时可直接 `Read {dispatch 文件} → offset=Progress Log 段` 返回增量；并行 dispatch 依次读 N 个文件
- **Plan / Blueprint Stage 执行**：内部评审结束后多一步 Codex dispatch + 整合（预估 +5-10min），Codex 不可用按 agents/README.md §三 三选一降级

## v7.3.6 —— 多决策点支持：数字决策点 + 字母选项（`1A 2B`）

背景：v7.3.5 单决策点编号化后，实际使用中遇到**一个暂停点需要同时确认多个独立决策**的场景（如 PRD 评审收尾时「PRD 通过？」+「排期方案？」同时浮现）。v7.3.5 没定义多决策点格式，AI 自发用 `①②③` 分隔决策点，但圆圈数字需要输入法切换，用户打字不便。

本版固化多决策点格式：**决策点用数字（1./2./3.），选项用字母（A./B./C./D.），用户回复 `1A 2B` 这种组合**。

- **RULES.md 暂停输出规范第 2 条扩展**：
  - 2.1 单决策点（不变）：选项 1/2/3/4 编号
  - 2.2 多决策点（新增）：决策点用 `1.` `2.` `3.` 分隔，内部选项用 `A.` `B.` `C.` `D.`，用户回 `1A 2B`
  - 2.3 何时合并 vs 拆分：同时到达且独立 → 合并；后者依赖前者结果 → 拆分；上限 3 个决策点
  - 2.4 打字友好性原则：优先英文键盘直接敲出的字符，禁止 ①②③ / 罗马数字 / emoji 编号
- **模糊确认处理更新**：支持 `1A 2B` / `1A2B` / `1a 2b`（大小写不敏感）解析；数量不匹配 → 回问补齐
- **SKILL.md 红线 #10 摘要补充**：明确单决策点 vs 多决策点的编号字符规则
- **正反例对比新增**：反例 2 展示 `①1 ②2` 为何被禁；正例 2 展示 PRD+排期实际场景用 `1A 2B`

### 用户打字成本对比

| 格式 | 示例 | 字符数 | 输入法切换 |
|------|------|--------|-----------|
| v7.3.5 单决策 | `1` | 1 | 否 |
| v7.3.6 多决策（2 项）| `1A 2B` | 5 | 否 |
| ❌ 禁止（圆圈）| `①1 ②2` | 5 但需切换 | **是** |

多决策点使用指引：
```
⏸️ 请确认以下两件事（回复 "1A 2B" 这种组合即可）

1. PRD 是否通过：
   A. 通过 ← 💡 推荐
   B. 修改某条
   C. 忽略某条（需说明理由）
   D. 其他指示

2. 排期方案：
   A. 并行推进 ← 💡 推荐
   B. F003a 优先
   C. F013 优先
   D. 其他指示

回复示例：`1A 2A` 双采纳 / `1A 2B` / `1B 2A` / 自然语言
```

非暂停点文本（如 arch-code-review 的 ①②③ 路径标签、roadmap 验收条件编号）不受影响——本规则只管"用户需要打字回复"的暂停点格式。

### 单决策点禁止套多决策壳（v7.3.6 后补反例 3）

AI 引入多决策点格式后可能过度泛化，把**单决策点**也套 `1. {决策} / A./B./C.` 壳，让用户要回 `1A`。硬规则明确：**只有 ≥2 个独立决策点**才启用数字+字母格式；1 个决策就是 1 个决策，直接数字选项。

```
❌ 反例 3：
⏸️ 是否同步 DEPENDENCY-REQUESTS.md DEP-003？
1. 是否同步 DEPENDENCY-REQUESTS.md DEP-003？
   - A. 立即修正（💡 推荐）
   - B. 暂缓
   - C. 其他指示
（外层 "1." 是虚的 + 用户要回 `1A`）

✅ 正例 3：
⏸️ 请选择（回复数字即可）
1. 立即修正 DEPENDENCY-REQUESTS.md DEP-003 ← 💡 推荐
2. 暂缓（保留文档现状）
3. 其他指示
（用户回 `1` 完事）
```

## v7.3.5 —— 暂停点选项编号化（用户回复数字即可）

背景：用户观察到当前暂停点用描述式选项（`- 跳过（推荐）` / `- 跑 Browser E2E`），用户需要打字回复，不如直接敲数字快。本次改为所有可选项编号化（1/2/3...），用户回复数字即直达对应动作。

- **RULES.md「暂停输出规范」加第 2 条硬规则**（选项编号化）：
  - 所有可选项必须以 `1/2/3...` 编号列出
  - 第一项是 PMO 推荐（与 💡 建议 一致，标注「💡 推荐」）
  - 最后一项始终为「其他指示（自由输入）」
  - 提示语统一："⏸️ 请选择（回复数字即可）"
  - ❌ 禁止描述式选项（`- 跳过` / `- 跑 E2E`）
  - ❌ 禁止用字母（A/B/C）—— 统一数字
  - 模糊确认处理更新：用户回纯数字 → 直接映射到对应选项执行
  - 附"反例 vs 正例"对比
- **SKILL.md 红线 #10 微调**：明确"所有可选项必须编号列出，用户回数字即可"
- **roles/pmo.md 更新具体模板**：
  - PM 验收 + commit + push 合并暂停点：1-4 编号（推荐 1 / 本地 commit / 修复 / 其他）
  - Test Stage 前置确认：A/B/C → 1/2/3（立即执行 / 延后 / 跳过 / 其他）
- **FLOWS.md 问题排查流程**：选项改编号化
- **RULES.md §四流转链 + Test Stage 相关段**：A/B/C 全部替换为 1/2/3
- **STATUS-LINE.md**：A/B/C 提及改数字

核心体验变化：

```
❌ v7.3.4 前（用户要打字）：
⏸️ 请回复
- 跳过（推荐，直接 PM 验收）
- 跑 Browser E2E
- 其他指示

✅ v7.3.5（用户回数字）：
⏸️ 请选择（回复数字即可）
1. 跳过 Browser E2E，直接进入 PM 验收 ← 💡 推荐
2. 跑 Browser E2E（+15-25 min）
3. 其他指示（自由输入）
```

用户可回 `1` / `2` / `3` 或自然语言覆盖默认。打字量从一串降为一个字符。

注：现存 Feature 目录内可能已有按旧模板写的暂停点，不回溯修改；PMO 下次输出暂停点时按新模板即可。

## v7.3.4 —— 暂停点压缩（P0）：UI+全景合并 + 验收+commit+push 合并

背景：v7.3.3 跑 Feature 发现典型流程有 6-8 个暂停点，反复打断用户。前期讨论后确认走「方案 A：批量确认」，本次是 P0 阶段：合并两组暂停点（UI+全景、PM 验收+commit+push）。核心原则不变——**人类在关键节点把关**，但关键节点更集中、更聚焦。

### 合并 1：UI Design + Panorama Design → 一个「设计批」暂停点

**原因**：Feature UI 和全景增量同步是同一次设计讨论的两面（风格/配色/布局/语言对齐），分两次确认让用户反复打断。

- **重构 stages/ui-design-stage.md**：
  - 职责扩展为"Feature UI + 全景增量同步"一次性产出
  - 🔴 全景是产品真相，修改必须谨慎：默认增量合并（append / modify-in-place），禁止重写
  - 新增硬规则：
    - 对全景的任何修改必须在 sitemap.md 添加标红注释 `<!-- 🟡 {日期}: {FeatureID} 变更摘要 -->`
    - 执行报告必须列出全景 diff（sitemap 页面清单 + overview.html DOM 差异摘要）
    - 不允许删除现有页面或导航（属于 Feature Planning 范畴）
    - 结构性变更红线（删页面/重构导航/改核心业务流程状态机）→ DONE_WITH_CONCERNS，建议走 Planning
  - Output Contract 新增「全景同步状态」必填字段（同步了 / 显式跳过，二选一）
- **重构 stages/panorama-design-stage.md**：
  - 定位收窄为"Feature Planning 流程的全景重建模式"专用
  - Feature 流程不再触发本 Stage
  - 保留差异清单、风险提示、用户授权必达等硬规则
- **flow-transitions.md 更新**：Feature 流程的 UI 待确认 / 全景待确认 两行合并为「设计批 待确认」一行

### 合并 2：PM 验收 + commit + push → 一个合并暂停点（3 选 1）

**原因**：PM 验收通过 → 手动问用户是否 commit → 手动问是否 push，三步是连续决策，合并一个暂停点更顺。
**原则**：PMO 可以自动 commit（本地），**push 由用户决定**（保留用户控制远程推送的权力）。

- **roles/pmo.md 新增「PM 验收 + commit + push 合并暂停点」章节**：
  - PMO 在 PM 完成验收后自动执行本地 commit（含所有 Feature 产物 + 规范的 commit message）
  - 合并暂停点给用户 **3 选 1**：
    - 1️⃣ ✅ 通过 → 自动 commit + push（推到 origin/{branch}）
    - 2️⃣ ✅ 通过 → 仅本地 commit，不 push（用户稍后手动推送）
    - 3️⃣ ❌ 不通过 → 补充信息，回到对应阶段修复
  - push 失败不吞错：⏸️ 报告原因让用户手动处理
  - 3️⃣ 修复派发规则：按问题类型回退到 Review / Test / Plan / UI Design 对应 Stage；commit 保留不 revert；每轮修复 append 新 commit + 新 retry 记录
- **RULES.md §七 Git 提交规则升级**：
  - 从"用户要求时提交"改为"PM 验收通过后 PMO 自动 commit"
  - commit 产物清单扩充（含 state.json / review-log.jsonl / dispatch_log/ / retros/ 等审计产物）
  - commit message 模板标准化（含 AC 覆盖 / Review 通过情况 / 测试通过情况 / 耗时偏差摘要）
  - 🔴 push 硬规则：PMO 禁止自动 push；必须用户显式选择；禁止 push --force 到主分支
- **flow-transitions.md 更新**：Feature 流程的「PM 验收 → ✅ 已完成」改为「PM 验收 → 验收+commit+push 待处理 → ✅ 已完成」
- **完成报告模板新增「📦 Commit & Push 状态」段**：记录 commit hash / 分支 / push 状态
- **state.json schema 扩展（v7.3.4）**：
  - `_schema_version` 升级到 v7.3.4
  - `_instructions.stage_enum_v7_3_4`：Feature 流程合法 current_stage 枚举
  - `_instructions.commit_push_tracking`：stage_contracts.pm_acceptance 新增 commit_hash / push_status 字段

### 暂停点数量变化

```
改前（v7.3.3 / 典型 Feature）：6-8 个暂停点
  流程确认 + PRD + UI + 全景 + 方案 + Test 前置 + Browser E2E? + PM 验收 + push?

改后（v7.3.4 / 典型 Feature）：4-5 个暂停点
  流程确认 + PRD + 设计批(UI+全景) + 方案 + [Test 前置] + [Browser E2E?] + 验收+commit+push(3 选 1)
  （方括号是按 localconfig / TC 标注自动判断，多数情况不打扰用户）

典型简单 Feature（无 UI）：3 个暂停点
  流程确认 + PRD + 方案 + 验收+commit+push(3 选 1)

数量砍 30-50%，保留的是真正需要人类把关的契约核心。
```

### 未动的（保留 P1/P2 观察后再决定）

- 方案 A 的 #5（Blueprint 按复杂度决定暂停）— P2，风险相对高，等 P0 跑几个 Feature 验证
- 方案 A 的 #6（Test Stage 前置配置化）— P1，先观察用户对 A/B/C 三选一的实际选择分布
- 其他非压缩类改进（PMO 拆分、validator 等）— 前几轮讨论否掉了，不做

### 文件变更

- `skills/teamwork/stages/ui-design-stage.md`（重构：扩展为 UI + 全景增量）
- `skills/teamwork/stages/panorama-design-stage.md`（重构：仅保留全景重建模式）
- `skills/teamwork/rules/flow-transitions.md`（Feature 流程合并行）
- `skills/teamwork/RULES.md`（§四 Feature 流转逻辑 + §七 Git 提交规则升级）
- `skills/teamwork/FLOWS.md`（阶段链 + 流程步骤描述）
- `skills/teamwork/roles/pmo.md`（新增「PM 验收 + commit + push 合并暂停点」章节 + 完成报告加 Commit & Push 状态段）
- `skills/teamwork/templates/feature-state.json`（schema v7.3.4 + 新字段说明）

## v7.3.3 —— Stage 耗时度量闭环

背景：之前 dispatch.md 有预估（"预计 20-30 分钟"）但 Stage 结束没统计实际耗时。v7.3 改造完成后无法用数据验证效果，只能凭感觉判断"是快了还是慢了"。本次补齐耗时度量闭环，让每个 Feature 跑完自动有数据可复盘。

- **state.json schema 扩展**（templates/feature-state.json）：
  - `stage_contracts[stage]` 新增 `started_at` / `completed_at` / `duration_minutes`
  - `executor_history[]` 每条扩展为 `started_at / completed_at / duration_minutes / estimated_minutes / variance_pct / dispatches_count / retry_count / user_wait_seconds`
  - `planned_execution[stage]` 新增 `estimated_minutes` 字段（来自 AI Execution Plan）
- **review-log.jsonl schema 扩展**（templates/review-log.jsonl）：
  - 新增 6 字段：`started_at / duration_minutes / estimated_minutes / variance_pct / dispatches_count / retry_count / user_wait_seconds`
  - 示例更新为含耗时数据的完整行
  - 新增字段计算规则说明
- **AI Execution Plan 扩展为 4 行**（SKILL.md 「AI Plan 模式规范」）：
  - 新增第 4 行 `Estimated: {N} min`
  - AI 基于本 Feature 规模（AC 数、文件数）动态估算
  - 3 个典型示例全部更新
- **PMO 阶段摘要加耗时行**（roles/pmo.md）：
  - 每次 Stage 完成后的 PMO 摘要必须包含「⏱️ 实际耗时：N min（预估 M min，偏差 ±X%）」
  - 偏差 > +50% 自动加 ⚠️ 标识；偏差 < -30% 加 🟢 标识（预估过保守）
- **Feature 完成报告加耗时统计章节**（roles/pmo.md / RULES.md 8️⃣-D）：
  - 耗时统计表：每行一个 Stage + 合计（预估/实际/偏差/dispatches/retry/用户等待）
  - 耗时分析段：超预估 Stage 列表 + 客观原因 + 可操作优化建议
  - 区分 AI 实际耗时 vs 用户等待时间
- **各 stages/*.md 加 Expected duration baseline**：
  - plan-stage: 20-40 min（主对话）/ 15-20 min（Subagent）
  - blueprint-stage: 25-45 min（主对话）/ 30-60 min（Subagent）
  - blueprint-lite-stage: 8-15 min
  - ui-design-stage: Subagent 20-40 min / 主对话 8-15 min
  - panorama-design-stage: 增量 15-25 min / 重建 30-50 min
  - dev-stage: 主对话 ≤3 文件 15-25 min / Subagent 中等 30-60 min / 大改 60-120 min
  - review-stage: hybrid 10-20 min（三路并行墙钟）/ 全 subagent 15-25 min
  - test-stage: hybrid 15-30 min（环境 2-5 + 集成 5-15 + API E2E 10-25）
  - browser-e2e-stage: 每场景 2-3 min，总计 10-20 min
- **retros/*.md 模板加耗时度量段**（templates/retro.md）：
  - §1.1 耗时度量表（从 state.json.executor_history 聚合）
  - 跨 Feature 趋势分析：多个 retros 对比可发现规律（哪个 Stage 总是超预估）
- **RULES.md 8️⃣-D 新增**：Feature 完成报告必须输出耗时统计，不得跳过

核心收益：
- 每个 Feature 自动产出耗时数据，不再靠感觉判断
- 多个 Feature 跑完后可做横向对比（"Blueprint 总是超预估" → 设计有问题）
- Retro 从"主观经验记录"变成"数据驱动改进"
- v7.3 系列改造的净效果有数据可测（本轮加字段，下一个真 Feature 跑完即有数据）

Micro 流程不强制输出耗时（本身已是最短路径，加统计反成仪式）。

## v7.3.2 —— STATUS.md 废弃，state.json 成为 Feature 目录唯一状态文件

背景：v7.3 引入 state.json 做机读权威源，但保留 STATUS.md 作为"人读视图 + compact 恢复锚点"，导致字段重叠、双源头维护、恢复规则歧义。v7.3.2 彻底砍掉 STATUS.md，让 state.json 同时承担机读权威和人读详情（JSON 本身可读），ROADMAP.md 继续承担全局人读视图。

- **state.json 位置迁移**：从仓库根 `.teamwork/state/{feature_id}.json` 移到 `{Feature}/state.json`
  - 和 PRD/TC/TECH 等 Feature 产物同目录，单 Feature 查询无需跨目录
  - 跨 Feature 聚合依然可行（glob `docs/features/*/state.json`）
- **STATUS.md 废弃**：
  - `templates/status.md` 删除
  - `TEMPLATES.md` / `templates/README.md` 索引移除 status.md，新增 feature-state.json 和 verify-ac.py
  - 新 Feature 不再创建 STATUS.md，state.json 承担原职责
- **遗留 STATUS.md 处理**（向后兼容）：
  - 不删除已有文件（保留历史）
  - PMO 不再维护它
  - state.json 不存在但 STATUS.md 存在 → PMO 基于 STATUS.md 信息初始化 state.json 后忽略
- **规则更新**（所有对 STATUS.md 的引用全面替换）：
  - `SKILL.md` 红线 #1 / #14 / 热路径索引 / 文件索引
  - `RULES.md` §四流转链 / 功能完成 8️⃣ / 抽查规则 / 角色交接 / PMO 摘要更新
  - `rules/gate-checks.md` 原「STATUS.md 流转约束同步更新」段改写为「state.json 流转状态同步更新」
  - `rules/naming.md` Feature 目录标准结构 + BG 反向引用字段 + CHG 记录位置
  - `roles/pmo.md` state.json 维护规范全段重写（位置、流转前后、compact 恢复、遗留文件处理）
  - `roles/pm.md` 功能目录初始化描述
  - `stages/dev-stage.md` worktree 记录位置
  - `CONTEXT-RECOVERY.md` 恢复决策树 / Feature 看板 / compact 快速路径
  - `STATUS-LINE.md` compact 恢复快速路径 / 待确认恢复规则
  - `INIT.md` 扫描进度 / Feature 目录结构 / 红线 #1
  - `templates/feature-state.json` 位置字段 + 替代说明
  - `templates/roadmap.md` / `templates/teamwork-space.md` 引用更新
  - `codex-agents/hooks.json` 描述更新
- **验证**：
  - `grep -r "STATUS\.md"` 剩余都是 v7.3.2 明确标注的"遗留说明"或"废弃说明"
  - `grep -r "\.teamwork/state"` 零命中（位置已全迁移）
  - `templates/status.md` 文件已删除

简化效果：
- Feature 状态维护点从 4 处降到 3 处（state.json + review-log.jsonl + ROADMAP.md）
- 双权威冲突彻底消除
- Compact 恢复单一锚点（state.json），不再需要和 flow-transitions.md 交叉校验 STATUS.md

## v7.3.1 —— v7.3 收尾

前序 v7.3 改造完成后发现三个未对齐点，本次小版本收尾修复，不引入新机制。

- **agents/README.md §一 速查表与 AI Plan 模式对齐**（消除双权威冲突）：
  - 章节标题从「执行方式决策（PMO 必读）」改为「执行方式参考（默认推荐 + 判断原则）」
  - 删除"PMO 查下表决定 / 禁止凭感觉判断"的硬绑定语言
  - 表头从「执行方式」改为「默认 approach」，标识 🤖/主对话 改为 main-conversation/subagent/hybrid/AI 自主
  - 删除"🔴 禁止降级 Sonnet"等与"AI 自主"冲突的硬规则
  - 新增"AI Plan 偏离指引"章节，说明何时偏离默认 approach
- **Execution Plan 从 6 字段精简为 3 行核心**（去除重复仪式）：
  - Plan 只保留 Approach / Rationale / Role specs loaded 三项
  - Steps / Expected Output / Key Context 由各 Stage 契约、dispatch 文件、产物 frontmatter 承载（不重复）
  - SKILL.md 新增 3 个典型示例（Plan Stage / Dev Stage / Review Stage）
  - 每个 Feature × 8 Stage 的仪式文字量从 ~160 行降至 ~24 行
- **各 Stage 的 Plan 指引段落精简**（单一权威指向）：
  - plan/blueprint/blueprint-lite/ui-design/panorama/browser-e2e 的"AI Plan 模式指引"压缩到 2-3 行，指向 SKILL.md 和 agents/README.md §一
  - dev/review/test 保留本 Stage 特殊的 approach 判断逻辑（规模/复杂度/三视角独立性/环境独立性）
  - SKILL.md 中原"典型 approach 选择指引"表删除（和 agents/README.md §一 重复）
- **verify-ac.py 从示例脚本落地为可直接跑的标准实现**：
  - 新增 `templates/verify-ac.py`（Python 3 标准库实现，无 yq / 外部工具依赖）
  - 自带 YAML frontmatter 简化解析器，同时兼容 PyYAML（如已装）
  - 自测覆盖：文件缺失 / 覆盖通过 / 覆盖不完整 三种场景 exit code 分别为 1 / 0 / 3
  - 可直接从 `{SKILL_ROOT}/templates/verify-ac.py` 调用，项目无需复制
  - 删除旧 `templates/verify-ac.example.sh`（示例化处理太弱，实际没人落地）
  - prd.md / tc.md / blueprint-stage.md 所有引用更新

## v7.3
- **Stage 三契约化（规范契约，不规范过程）**：
  - 每个 Stage 文件重构为 Input Contract / Process Contract / Output Contract 三段式
  - 删除所有 Stage 对"必须 Subagent 执行"的硬绑定
  - 执行方式（主对话 / Subagent / 混合）由 AI 在 Plan 模式每次 Stage 开始时自主规划
  - 多视角独立性从"规则要求"转为"产物结构约束"：三份 review 产物独立 generated_at、独立 files_read、不互相引用（grep 校验）
  - 覆盖文件：stages/{plan, blueprint, blueprint-lite, dev, review, test, ui-design, panorama-design, browser-e2e}-stage.md 全部重写
- **AI Plan 模式规范**（SKILL.md 新增章节 + 红线 #14）：
  - AI 必须在每个 Stage 开始前输出 Execution Plan 块（含 Approach / Rationale / Steps / Expected Output / Loaded Role Specs & Standards / Key Context）
  - Plan 写入 state.json.planned_execution[stage]，审计可追溯
  - 硬规则：角色切换时必须 cite 对应 roles/*.md 的关键要点（防止凭记忆执行）
  - 实际执行偏离 Plan 时必须更新 Plan + 记录偏离理由
- **AC↔Test 结构化绑定（消除需求→代码漂移根源）**：
  - PRD.md 头部新增 YAML frontmatter：acceptance_criteria[]（id/description/priority/test_refs/ui_refs）
  - TC.md 头部新增 YAML frontmatter：tests[]（id/file/function/covers_ac/level/priority）
  - 新增 templates/verify-ac.example.sh 作为覆盖校验脚本示例
  - Output Contract 硬要求：每条 PRD AC 至少有 1 个 covers_ac 测试 + 所有测试通过
- **主对话产物协议（补齐 Subagent 协议反面）**：
  - agents/README.md §六 新增：主对话直接执行任务的产物落盘规范
  - YAML frontmatter 必填：executor/task/feature/started_at/completed_at/status/files_read/concerns
  - 覆盖场景：Plan Stage PRD 起草、Blueprint TC/TECH、Review 架构师视角、Test 环境启动、Browser E2E、UI 还原验收、PM 验收
  - templates/dispatch.md 顶部加适用范围声明：仅适用于 Subagent dispatch
  - review-log.jsonl schema 扩展：新增 executor / artifact_path / dispatch_file 字段
- **state.json 机读状态机**（模板 + PMO 维护规范）：
  - 新增 templates/feature-state.json 定义 Feature 级流转状态机
  - 位置：.teamwork/state/{feature_id}.json
  - 字段：current_stage / completed_stages / legal_next_stages / stage_contracts（input/process/output satisfied）/ planned_execution / blocking / executor_history / worktree
  - roles/pmo.md 新增「state.json 维护规范」：流转前读、流转后写，机器校验 target ∈ legal_next_stages
  - 与 STATUS.md 的关系：state.json 是机读权威源，STATUS.md 是人读视图，compact 恢复以 state.json 为准
- **流程确认必须展示步骤**（SKILL.md 红线 #15）：
  - PMO 初步分析中，选定流程类型后必须给出「本流程的完整步骤描述」（阶段链 + 每步做什么 + 暂停点）
  - 用户基于步骤描述确认流程类型
  - 不给步骤描述直接问「走什么流程」= 违规
- **Micro 流程放宽**（FLOWS.md §六 + SKILL.md 红线 #1）：
  - PMO 可直接改代码（白名单内零逻辑变更），不强制 Subagent，也**不要求 Execution Plan**
  - 真正轻量通道：只保留 PMO 分析 → 用户确认流程（含步骤描述）→ PMO 直接改 → 用户验收 的最小闭环
  - 改动限于 Micro 白名单（零逻辑变更：资源/文案/样式/配置常量/注释）
  - 事后审计：检查准入条件、逻辑变更混入、阶段链完整性
- **RULES.md §四流转链描述与实际实现对齐**：
  - 删除滞后的"Dev 含架构师 CR"、"Test 含 QA 审查"、"Codex 独立 Stage"描述
  - 更新为 v7.3 契约化后的准确流转链（Dev → Review 三路独立 → Test 环境独立 → Browser E2E → PM 验收）
- **status.md 显示名映射动态化**：
  - 显示名图标根据 state.json.planned_execution[stage].approach 动态渲染
  - 💬 = main-conversation / 🤖 = subagent / 💬🤖 = hybrid
  - 默认推荐列标注每个 Stage 的推荐 approach（但 AI 可按场景创新）
- 不做的改动（保留）：
  - 六种流程分类不变
  - dispatch 文件协议（v7.2）保留，Subagent 场景继续用
  - Key Context 6 类结构保留，在主对话任务中同样必需
  - Feature Planning / 工作区级 Planning / 问题排查流程规则不变

## v7.2
- Subagent Progress 可见性三段式协议（主对话 TodoWrite 预声明 + Progress Log 实时自述 + 事后回放）：
  - 背景：通用宿主 API 下 Subagent → 主对话无实时通道（同步阻塞模型），用户主对话黑盒等待体感差；plan 模式 / TodoWrite 在 Subagent 内不回流主对话
  - 三段式替代实时流：
    - 阶段 1（PMO 前置）：dispatch 前在主对话 TodoWrite 预声明 Subagent Step 列表（从 stage 文件「执行流程」抽取，粒度对齐 Expected deliverables）
    - 阶段 2（Subagent 中途）：执行中实时 append dispatch 文件的 Progress Log 段，记录 step-start / step-done / step-concern / step-blocked / degradation / subagent-done 等事件（硬规则：禁止最后一次性补全）
    - 阶段 3（PMO 事后）：读 Progress Log 转成主对话时间轴回放，step-start/done 映射为 TodoWrite 状态更新，异常事件高亮
  - templates/dispatch.md 新增 `## Progress Log` 必填段（含必填事件类型表 / 模板段 / 反模式）+ 设计原则第 8 条「Progress 可见性双保险」+ PMO 使用流程 Step 1/Step 3 新增 TodoWrite 预声明 + Progress Log 回显步骤
  - agents/README.md §二 2.5 新增「Progress Log 实时维护」硬规则 + §四 字段责任划分表新增 Progress Log 行（Subagent 填）+ §四 启动前自问新增「主对话 TodoWrite 预声明」检查 + §四 Subagent prompt 极简结构新增 Progress Log 要求（规则 3）+ §四 完成后处理新增「读 Progress Log 转主对话时间轴」步骤 + 新增「Progress 可见性协议」完整章节（三段式图示 + 用户体验目标对照 + 可选切分粒度策略）
  - 切分 Subagent 粒度作为可选加强（不默认）：满足"Stage >15 分钟 + 无强上下文依赖 + 用户明确敏感"三条件时启用
- API E2E 脚本化改造（从"逐条 curl"到"脚本驱动"）：
  - 核心变化：Subagent 不再一条条 curl，而是把 TC.md 场景翻译成 Python 脚本 → 执行 → 解读 JSON 输出 → 生成报告
  - 收益：Token 消耗从 N 场景 × 2 轮 LLM 降到 1 次生成 + 1 次解读；脚本可重跑（RD 修复后 `python api-e2e.py` 即可，无需再发 Subagent）；脚本可进 CI；脚本落盘为 Feature 交付物
  - 脚本位置：`{子项目}/tests/e2e/F{编号}-{功能名}/api-e2e.py`（+ README.md 记录 env 要求）
  - 脚本语言：Python 3.10+ + requests（禁止 bash+curl 组合——可移植性差）
  - 断言硬要求：每场景至少覆盖 4 类断言（status / body / DB / 副作用）中的 2 类；所有环境值走 env var；DB 校验必须走只读 DSN
  - 脚本标准化：函数名 `test_API_E2E_{N}_{描述}`，Runner 统一捕获异常输出 JSON，exit code 体现整体结果
  - e2e-registry 联动：P0/P1 级 case 必须注册，REGISTRY.md 新增「脚本路径」「最后跑通」两列
  - agents/api-e2e.md 整体重写：新增 §五脚本生成规范 + §六落盘注册流程 + §七新报告格式 + §九降级处理
  - agents/integration-test.md 顶部澄清：集成测试 = 调用既有测试命令（不生成脚本）；API E2E = 独立脚本（另一种职责），🚫 集成测试不做 curl 级黑盒
  - stages/test-stage.md §六红线新增「API E2E 脚本化交付」5 项硬要求 + Expected deliverables 明确脚本 + registry 更新
  - templates/e2e-registry.md 表结构增加「脚本路径」「最后跑通」列，api 类 case 必须填脚本路径（browser 类留 `-`）
- Key Context 结构化字段（dispatch 文件增强）：
  - 核心思想：PMO 是唯一贯穿全流程的角色，它手里有 Subagent 读不到的关键信息（历史决策、跨 Feature 约束、历史陷阱、降级授权、优先级权衡、本轮聚焦点），必须结构化注入 dispatch 文件，而不是让 Subagent 自己推断
  - 位置：dispatch 文件新增「🎯 Key Context」section，6 类子字段（历史决策锚点 / 本轮聚焦点 / 跨 Feature 约束 / 已识别风险 / 降级授权 / 优先级容忍度）
  - 🔴 硬规则：PMO 必须逐项判断，**无则写「-」**（证明已判断），严禁留空或删字段；无判断痕迹 → Subagent 返回 NEEDS_CONTEXT
  - 反模式防范：只写 Subagent 从 Input files 里读不到的信息，禁止复制 PRD/TECH 摘要
  - INDEX.md 增加「关键约束」列，摘录最关键一条，便于人工审查时识别本 Feature 累积的历史决策/风险
  - templates/dispatch.md 新增 Key Context 完整模板 + 设计原则第 7 条
  - agents/README.md §四 4.1 字段责任表新增 Key Context 行 + PMO 启动前自问清单新增逐项判断项 + Key Context 硬规则段（含正反例）
- Dispatch 文件协议（文件化 Subagent 交接）：
  - 核心思想：每次 Subagent dispatch 生成一个 markdown 文件，文件即入参即审计记录，消除「PMO 构造 prompt 字符串」和「PMO 写 dispatch 日志」的重复劳动
  - 位置：`{Feature}/dispatch_log/{NNN}-{subagent-id}.md` + `INDEX.md` 汇总视图
  - Subagent prompt 从 100+ 行简化为 ~5 行（只指向 dispatch 文件路径 + append Result 要求）
  - 🔴 硬规则：未生成 dispatch 文件不得 dispatch / Subagent 必须 append Result 否则视为 FAILED / PMO 必须更新 INDEX
  - 未 append Result / 超时卡死 → PMO 接管写 Result（含 degradation WARN），降级主对话执行
  - 降级 WARN 日志直接写入 dispatch 文件 Result 区域，审计链完整
  - 并行 dispatch 各用独立文件（Batch 字段标同批次），重新 dispatch 新文件 + Previous 字段追溯
  - 跨宿主天然兼容：Claude Task / Codex agent spawn / Gemini 主对话 / 主对话降级都只需"读这个文件"
  - 新增 `templates/dispatch.md`（含完整字段定义 + INDEX 模板 + PMO 使用流程 + 生命周期）
  - agents/README.md §四 4.1 用「Dispatch 文件协议」替代原「Prompt 结构」章节；§四 4.2 启动前检查新增「dispatch 文件已生成」前置条件；§四 4.3 完成后处理新增 Result append 校验 + INDEX 更新
  - rules/naming.md 新增 dispatch 文件编号规则 + Feature 目录标准结构（含 dispatch_log/）
  - INIT.md 创建基础目录段新增 Feature 子目录说明
- 降级兜底 WARN 日志强制规范：
  - standards/backend.md §四 日志规范新增「降级兜底逻辑 WARN 日志规则」硬规则（含必须字段：降级原因 + 原路径 + 兜底路径 + 业务上下文，含反例示例，Code Review 缺失即阻塞）
  - standards/common.md CR 规范遵守检查新增降级 WARN 必检项
  - agents/README.md §四 dispatch 新增「降级兜底必须输出 WARN 日志」统一规范，覆盖 Subagent dispatch 失败、Codex CLI 不可用降级 Sonnet、宿主不支持 TodoWrite、worktree 不可用、hook 缺失等所有宿主兼容兜底路径
  - agents/README.md §五 BLOCKED/FAILED 升级策略标注 WARN 日志要求，静默降级明确定性为违反闭环验证红线
- 效率优化（减少流程税）：
  - Stage 内部子步骤简化 PMO relay：跨 Stage 保留完整校验，Stage 内部改用轻量标记（📌 Blueprint 1/4）
  - Subagent 输入改文件路径优先：减少 PMO 摘要转述的信息衰减，Subagent 自行读原文
  - Blueprint Stage 改为 Subagent 执行：4 步内部闭环，主对话 context 不被占用
  - 敏捷需求新增 BlueprintLite Stage（轻量蓝图：QA 简化 TC + RD 实现计划，无评审），替代原 3 步独立执行，Dev Stage 保持单一职责
- 叙事重构：从"虚拟团队"改为"角色视角 + 流程规范"定位
  - SKILL.md description: "AI Agent Team" → "AI-driven structured development process with role-based perspectives"
  - README 中英文同步更新：强调角色视角切换和质量门禁，而非团队协作
  - INIT.md 写入模板：从"多角色协作流程"改为"结构化开发流程"
- 跨宿主兼容（Claude Code / Codex CLI / Gemini CLI）：
  - 硬编码路径 `.claude/skills/teamwork/` → `{SKILL_ROOT}` 变量（~20 处）
  - INIT.md 宿主环境检测 + 指令文件自适应写入（CLAUDE.md / AGENTS.md / GEMINI.md）
  - agents/README.md §四 dispatch 抽象层（Task 工具 / Codex agent spawn / 主对话降级）
  - codex-agents/ 目录：6 个 Codex 自定义 agent toml 定义
  - TodoWrite 降级：宿主不支持时回退 markdown 进度块
  - hooks 双宿主：Codex 版去掉 PreCompact/PostCompact
  - install.sh 安装脚本：自动检测宿主 + 一键部署
  - SKILL.md 新增「宿主环境适配」章节

## v7.1
- 问题 10 清理：STATUS-LINE.md 阶段对照表 / templates/status.md 显示名映射 / agents/README.md 速查表 / gate-checks.md 示例 / 全局旧阶段名引用清理
- 问题 11 Worktree 集成：.teamwork_localconfig.md 新增 worktree 策略字段（off/auto/manual），INIT.md 启动检测，Dev Stage worktree 创建/清理生命周期，flow-transitions.md 标注 worktree 触发点

## v7
- 8 Stage 架构重构：
  - stages/ 目录（8 个 stage）：Plan / UI Design / Panorama Design / Blueprint / Dev / Review / Test / Browser E2E
  - agents/ 只保留任务单元规范（被 stage 引用，不被 PMO 直接 dispatch）
  - roles/ 保留 6 个角色定义
  - rules/ 保留转移表 + 门禁 + 编号
- Dev → Review → Test 三段式：Dev 纯开发+单测，Review 三路并行（架构师CR∥Codex∥QA审查），Test 并行（集成∥E2E）
- Plan Stage：PM 写 PRD + PL-PM 讨论 + 技术评审合并为一个 stage
- Blueprint Stage：QA 写 TC + TC 评审 + RD 技术方案 + 架构师评审合并为一个 stage
- Chain → Stage 全局重命名
- Codex Review 合入 Review Stage（不再独立 dispatch）
- Panorama Design Stage 从 UI Design Stage 拆出独立

## v6
- roles/ 与 agents/ 分离：ROLES.md（1,635 行）拆为 roles/ 目录（7 个角色文件）+ 索引（~25 行）
  - agents/ 只保留真正的 Subagent spec（6 个 + 子规范）
  - 主对话评审规范（prd-review / tc-review / arch-tech-review）合并到对应 roles/ 文件
  - 角色定义按需加载，PMO 不再需要读 1,635 行的 ROLES.md

## v5
- 新增第五种流程「敏捷需求」：轻量级流程适用于小改动
- 新增第六种流程「Micro」：零逻辑变更的最轻量通道（资源替换/文案/样式/配置常量），防止 PMO 因"改动太小"而越界写代码
- PMO 反模式补充：小改动决策树 + "自己做更快"反模式 + commit/push 必须用户验收
- PMO 预检分层体系（L1 基础/L2 测试环境/L3 E2E）：所有 Subagent dispatch 前必须完成对应级别预检（红线 #13）
- PMO 恢复/待命场景强制给出优先级建议：Feature 看板必须附 💡 建议 + 📝 理由，禁止只列状态让用户自行判断
- Pre-flight Check 合并到强制流转校验块：新增「📖 流转类型」必填字段（🚀自动/⏸️暂停/🔀条件），查表结果嵌入校验输出，消除两步分离导致跳过预检的问题
- 4 个轻量 Subagent 回归主对话执行：PRD 技术评审、TC 技术评审、架构师方案评审、QA Lead 质量总结改为 PMO 切换角色在主对话执行，减少冷启动开销提升速度（spec 文件保留作为角色规范）
- 新增 agents/README.md §一「执行方式速查表」：PMO 判断 Subagent vs 主对话的集中决策指引（含判断原则 + 全阶段速查表），热路径索引已添加入口
- P0 单一权威源重构：RULES.md 从 2,004 行精简到 ~1,645 行（-18%）
  - 转移表副本（99 行）→ 删除，权威源：rules/flow-transitions.md
  - 门禁校验格式（91 行）→ 删除，权威源：rules/gate-checks.md（同步更新为最新版含流转类型字段）
  - Bug 处理流程（177 行）→ 迁移到 FLOWS.md，RULES.md 改为引用
  - 暂停条件 4 个子章节合并为 1 个「暂停输出规范」（-99 行）
  - UI 变更规则 6 次重复压缩为 1 条（-55 行）
  - 编号规则（82 行）→ 迁移到 rules/naming.md
  - 最终结果：RULES.md 2,004 → 1,418 行（-29.2%）
  - PMO 热路径索引更新为指向拆分后的权威文件
- 阶段名消歧义重命名：PRD 评审→PRD 技术评审 / TC 评审→TC 技术评审 / 架构师 Review→架构师方案评审（88 处 / 22 文件），消除"执行步骤"与"用户确认"的命名混淆
- 状态行功能编号必填：Feature/敏捷/Bug/Micro 流程的功能/Bug 编号从可选改为必填
- 流转校验精简为 1 行：`📋 {A} → {B}（📖 {类型}，查 flow-transitions.md ✅）`，降低 PMO 跳过校验的成本
- QA Lead 质量总结环节移除：Verify Stage / Browser E2E 通过后直接进入 PM 验收，简化流程。角色从 8 个降为 7 个。敏捷需求砍掉环节从 7 个降为 6 个
- Designer 两步设计：Feature 流程中 Designer 拆为 Step 1（当前 Feature UI）+ Step 2（全景同步），各自独立确认
- Codex CLI 通用执行引擎移除，Codex CLI 仅用于独立 Codex Code Review 阶段（不可用时可降级 Sonnet 或跳过）
- TEMPLATES.md 拆分为 templates/ 目录（16 个独立模板文件）
- RULES.md 热路径拆分为 rules/ 目录
- INIT.md CLAUDE.md 注入段精简（红线改为索引引用）
- 前端开发规范大幅扩充
- Hooks 脚本健壮性改进（换行符 bug 修复、降级逻辑、超时调整）
- 规则去重：建立单一权威定义 + 引用模式
- 明确协作模型（单人 vs 多人）

## v4
- 中台子项目支持（business / midplatform）
- PL-PM Teams 讨论机制
- E2E 回归测试中心
- QA Lead 质量总结阶段
- 自下而上影响升级评估

## v3
- 业务架构与技术架构对齐方案落地
- Product Lead 三种工作模式
- CHG 变更记录机制
- Workspace Planning 流程

## v2
- 多子项目模式
- Hooks 自动化（SessionStart / PreCompact / Stop）
- 按需加载文件机制

## v1
- 基础 8 角色协作框架
- Feature / Bug / 问题排查 / Feature Planning 四种流程
