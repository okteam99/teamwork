# Teamwork

AI 从团队协作视角出发，通过**流程编排 + 角色视角切换 + 契约化 Stage + 机读状态机**，驱动从产品规划到交付的完整软件研发流程。

[English](./README-EN.md) · Version: **v8.360**（版本单源 = [SKILL.md](./skills/teamwork/SKILL.md) frontmatter）

---

## 我们在解决什么

**AI 在弱监督下写软件，有四个不可回避的本质风险** —— 它们是结构性的，不随模型变聪明而消失。Teamwork 的四根支柱各对应一个：

| 本质风险 | 为什么不可回避 | Teamwork 的应对 |
|---------|--------------|----------------|
| **意图偏差**（做错东西） | 信息不对称：用户没说的，AI 再聪明也不知道 | 暂停点 / 意图门（prepare 意图确认 · goal 深门 · 全景用户确认） |
| **质量盲区**（做坏东西） | 自评盲区是数学性的：同模型看不见自己的坑 | **隔离冷审 · 多路同清单 · 逐路模型错开**（独立采样 —— 不靠同一上下文里换个身份） |
| **状态漂移**（丢东西 / 乱东西） | context 有限是物理性的：长流程靠记忆必漂 | 机读状态机 + 产物物化校验 + worktree 隔离 |
| **知识流失**（重复犯错） | 每个 session 从零开始 | KNOWLEDGE 沉淀 + 跨项目审计回收（audit → harvest）反馈环 |

跨项目审计实证（截至 v8.191 · 163 条交付审计）：状态机零逃逸（bypass 0/163）· 评审拦真问题 92 例 · 暂停点真实收敛设计 32 例 · 近 20 个版本的改进全部由审计数据驱动。

## 设计前提

Teamwork 在两个维度上做匹配：

**按需匹配流程**：查代码、Bug、Feature 需要的协作深度完全不同。入口分诊（5 mode：query / execute / resume / status / discuss）意图匹配到合适流程 · 简单任务匹配简单流程 · 复杂需求走完整流程。

**按风险装配力度**：流程不是固定仪式，而是四个维度现拧——规格深度（要不要 PRD / TECH）· 证据门（有没有行为面）· 验证深度（自测够不够）· 评审力度（几路冷审 × 什么模型）。六个命名档位（micro / floor / tiny / lite / medium / full）只是起手点，选完还要逐维再拧一遍；每个 stage 边界都是**显式修订点**——出现装配时不知道的事实就改计划，加与减同价。

**独立性靠隔离，不靠身份**：起草与评审分开在**不同上下文**里做（隔离 subagent · 不喂起草心路），多路之间**逐路模型错开**。每个 stage 一份**统一冷审清单**，配几路就几路都过全清单——不按角色切分（切分留下的缝没人接）。年检实证：方向清单式冷审的产出是角色关注点式的 **2.1×**，采纳率 82.3%。

你只需提需求 + 关键节点做决策。

### 冷审为什么有效

- **隔离产生独立性**：起草完的 AI 审自己会脑补填缝。评审走**独立 subagent**、不喂起草心路，白板效应恰是要的东西——这比"在同一段对话里换个身份"强得多。
- **模型错开去相关**：多路冷审**逐路模型不同**（至少一路 ≠ 会话主模型）。同模型双路 = 盲区相关，两路一起瞎。
- **清单保覆盖，题目保对抗**：每 stage 一份清单，三段缺一即漏——⚔️ **对抗**（必须写成"我试图证明 X 不成立，结果是…"，不许打勾）· 🔍 **核对**（可以写"查过无发现"）· 💡 **清单外洞察**（清单没问但你认为该关注的）。💡 那一段是框架的自发现通道：历史上多数真缺口都不在当时的清单里。
- **模型按活分档**：照着清单核对 → 验证档；按既定方案写出来 → 执行档；要想出清单上没有的东西 → 深度档（PRD / TECH 起草与首轮冷审，不许降）。换个便宜模型产出不会更差的，就没有理由用贵的。

> 📎 早期版本靠"主对话切换角色身份"制造多视角。现在**起草侧仍分职能**（PM 写 PRD · RD 写 TECH · QA 写 TC · Designer 出图），但**评审侧不再按角色切分**——独立性来自隔离与模型差异，覆盖面来自清单。

---

## 第一次用

### 安装

```bash
# 自动检测宿主环境（Claude Code / Codex CLI / Gemini CLI）
npx skills add okteam99/teamwork
```

### 升级

```bash
npx skills update okteam99/teamwork
```

### 启动一个流程

```bash
# Feature（完整需求 → 设计 → 开发 → 测试 → 验收 → 交付）
/teamwork 实现用户登录功能

# 小改动（轻量 Feature · 装配自动缩到 tiny/lite 档）
/teamwork 在用户列表增加导出 CSV 按钮

# 微调（Micro：零逻辑变更的文案 / 样式 / 资源替换）
/teamwork 把首页 logo 换成新的图片

# Bug 处理
/teamwork 登录页面在手机端返回 500 错误

# 问题排查（不产出代码，只定位根因）
/teamwork 最近 3 天生产环境 P95 延迟变高了，帮我看看

# Feature 规划（拆 ROADMAP，不产出代码）
/teamwork 规划电商推荐系统
```

### 你要做什么 vs AI 要做什么（产品迭代阶段）

| 阶段 | 你做的事 | AI 做的事 |
|------|----------|-----------|
| 起点 | 给一句话需求 | PMO 初步分析 + 识别流程类型 + 给完整步骤描述 |
| 确认流程 | 回 ok / 反馈 | 根据流程读取必要知识库文档 · 启动流程 |
| PRD | 等 / 纠偏 | PM 起草 PRD + N 路隔离冷审（同一份清单）+ 收敛 |
| 确认 PRD | 回 ok | — |
| 设计 | 等 | Designer 产出 UI + 同步全景 |
| 技术方案 | 等 | RD 起草 TECH + QA 起草 TC + N 路隔离冷审（同一份清单） |
| 开发 | 等 | RD 按 TDD 实现 + 单测 + 机器校验 |
| 审查 | 等 | 架构师 + QA + **第三独立视角**（默认同模型隔离冷审 · 异质可选）三视角独立 Review |
| 测试 | 等（启应用如需）| QA 集成测试 + API E2E 脚本化 |
| 验收 | 回 ok / 反馈 | PM 角度验收 + PMO 整理交付报告 + 自动 commit |
| **Ship Phase 1** | 点击 merge 按钮 | 净化 + 知识沉淀（distill）+ 归档（随 feature MR 原子合入）+ 创建 MR/PR · user_card 置顶 MR 链接 + 📦 交付总结 → **await-merge 30s 轮询**（检测已合并自动进 Phase 2）|
| **Ship Phase 2** | 等 | 零内容清场：验证交付 + 清理 worktree + 主分支同步 → ✅ |

典型 Feature 暂停点数量：**3-5 个**。

### 你要做什么 vs AI 要做什么（产品方向规划）

从业务全景到具体 Feature 的拆解流程，PL（Product Lead）主导、PMO 编排、PM 承接落地。

| 阶段 | 你做的事 | AI 做的事 |
|------|----------|-----------|
| 起点 | 给一句话方向（如「做电商推荐系统」/「调整商业模式」） | PMO 识别为产品方向类输入 · 调度 PL |
| 业务全景 | 回答 PL 关键问题（用户 / 价值 / 场景） | PL 引导构建 product-overview（业务架构 + WS 拆解）|
| 确认业务全景 | 回 ok / 纠偏 | PL 落地 product-overview/ 文档 |
| 方向讨论 | 抛话题（增减业务线 / 商业模式调整） | PL 讨论模式：多视角分析 + 选项 + 推荐 |
| 拍板方向 | 选定方向 | PL 进入执行模式 · 判定变更级别（功能 / 业务模块 / 方向）|
| ROADMAP 拆解 | 等 / 纠偏 | PMO 调度拆 ROADMAP（业务线 → 模块 → Feature 列表）|
| 确认 ROADMAP | 回 ok | PMO 落地 ROADMAP.md + sitemap.md |
| 选 Feature 启动 | 指定下一个 Feature | PMO 转入 Feature 流程（进入「产品迭代阶段」表）|
| Feature 完成回流 | 等 | PMO 自动回写 ROADMAP 状态 + 更新 sitemap |

典型方向规划暂停点数量：**1-3 个**（业务全景确认 + 方向拍板 + ROADMAP 确认）。

---

## 5 mode 入口分诊

teamwork 入口是 PMO 主对话的 **5 mode 分诊** · 仅看用户输入决定走哪条最小路径：

| mode | 触发场景 | 行为 |
|------|---------|------|
| **A · query** | 「看下 / 调研 / 解释 / why / 排查」+ 没推进动词 | 直接 grep / Read 答 + 跟进引导 · 不进 stage 链 |
| **B · execute** | 「实现 / 修复 / 创建 / 改」+ 明确动作 | 进 prepare 子流程 → 流程类型识别 → 业务 stage 链 |
| **C · resume** | 「继续 F032 / ship F032」 | 找 state.json + jump 到 current_stage |
| **D · status** | `/teamwork`（空命令）/「现在到哪了」 | 加载 Feature 看板 + 输出 |
| **E · discuss** | 「我感觉 / 你怎么看 / X vs Y / 建议 / 哪种更合理」 | 综合视角讨论 + 选项 + 推荐 + 询问 → 用户拍板后升级 mode |

**原则**：按需启动 · 为目标达成选择合适的流程。

## 流程类型 — 该走哪条（闭集）

机器层：`flow_type ∈ {Feature, Bug}` + Feature 重量档 `preset ∈ {micro, floor, tiny, lite, medium, full}`（**六档 · 命名的维度组合**，不是六套流程）。轻重由**四维装配**承担，档位只是起手点——选完仍要逐维再拧。

| 流程 | 适用场景 | 产出 | 默认暂停点 |
|------|----------|------|-----------|
| **Feature · full** | 功能开发（默认） | 代码 + 文档 + 测试 | 3-5 |
| **Feature · floor** | 有行为面但测试能完全证明它对 · 不动契约面 — 评审全 0，验收在 MR diff | 代码 + 测试 | 1-2 |
| **Feature · tiny** | 测试证得了实现，但值得一双眼看 diff — 零文档 · review 单路 | 代码 + 测试 | 1-2 |
| **Feature · lite** | 有规格风险要 PRD，但方案空间小到不值得先写 TECH | 代码 + PRD + 测试 | 2-3 |
| **Feature · medium** | 方案空间值得先写 TECH，但没到要两路并行冷审 — goal/blueprint 各单路 | 代码 + PRD/TECH/TC + 测试 | 3-4 |
| **Feature · micro** | 零逻辑变更（文案/样式/资源/配置常量白名单 · ≤5 文件）— 跳过评审/测试，保留用户验收 + ship | 代码（直改） | 2（确认 + 验收） |
| **Bug** | 已识别的缺陷 — **先诊断**（根因 + 修复方案经用户确认后才动手修） | 修复 + BUG 报告 + 回归测试 | 3-4 |
| **Feature Planning** | 从产品目标拆 ROADMAP（不出代码 · R6 · 不进状态机） | WS + ROADMAP + 全景 | **1**（仅最终摘要确认）|
| **问题排查** | 仅定位根因，不产出代码（不进状态机 · 先排查法则） | 排查报告 + 后续 todo | 0-1 |

流程类型由 prepare 子流程在 mode B 入口自动识别（evidence-first 分诊），你只负责在暂停点确认。Feature / Bug 进状态机走 stage 链；Feature Planning / 问题排查不进状态机，由 PMO 主对话执行。

---

## 进阶使用

### 流程控制

```bash
# 查看当前状态（走到哪一步 / 下一步是什么 / 待决策点）
/teamwork status

# 恢复被中断的流程（新对话 / compact 后也能恢复，靠 state.json）
/teamwork 继续
```

暂停点选项都是编号化的（💡 推荐项标第一，最后一项始终是「其他指示」），**回复一个数字即可**，不用打字。支持多决策点组合（如 `1A 2B`）。全局快捷词：`ok` = 按推荐建议、`all default` = 全用默认值。

### 自动化档位：auto_mode / yolo

默认每个**用户决策**暂停点都停下等你确认。两个可选档位调高自动化:

- **`auto_mode`**：AI 代你完成 **stage 间流转** —— 只对「用户决策」类暂停点（如 PRD / UI 确认）代你接受 + 文档化（写 `concerns WARN` 留痕），**评审工作（N 路隔离冷审 · 逐路模型错开）照常真跑**。
- **`yolo`（v8.63 · 完全无人值守 · 🔴 高风险）**：`auto_mode` 超集，启动后**零 stop**（连 PM 验收 + MR 自动合）。`init-feature --yolo [<集成分支>]` 启用（自动 implies `auto_mode`）；中途切换用 `state.py set-mode --feature <F> --yolo [<分支>] --reason '...'`（走 audit，别 raw-write `state.json`）。

🔴 **yolo 不是「简化 / 提速」，而是「加重审核」**：无人值守 = 没人在看 → 自动化评审是唯一安全网，必须保留 / 加重、**绝不削弱**。roster 内评审**全真跑 · 一个不少**（路数由装配定 · 每路都过全清单三段）· 第三视角 = **错开模型 subagent 隔离冷审**（唯一形态）· 🔴 **合入必须先进 `yolo/` 隔离分支**：每个 feature 合入时把待确认信息记在该分支，攒到 yolo 分支合入目标分支时一次性确认。

🔴 **硬门禁**：yolo 的 `merge_target` **必须非主分支**（main / master）—— 自动合入只进 `dev` / `staging` / `integration` 等集成分支，主分支提升仍由**人工 gate**。推荐给 yolo 一个专属集成分支（如 `--yolo yolo/feat-x`）隔离自动合入的代码。per-feature opt-in（不 sticky · 每次显式传）。

### 职能与评审

**流程职能**（起草侧 · 仍按专业分）：

- **PMO**（流程编排）：承接用户输入 → 识别流程 → 状态机维护 → 预检与暂停点
- **Product Lead (PL)**：产品方向。引导模式（从零构建 product-overview）/ 讨论模式（业务话题）/ 执行模式（变更级联 + Change Request lifecycle）
- **PM**：PRD + 结构化 AC + 最终验收
- **Designer**：UI 还原 + 全景（sitemap + preview）
- **RD**：TECH 起草 + 实现 + 自查
- **QA**：TC 起草（AC↔test 绑定）+ 集成测试 / API E2E

**评审侧不按角色切分**：每个 stage 一份统一冷审清单，配几路就几路**都过全清单**。roster 里的 `pl` / `external` / `architect` 是 **lane 标识**——只决定产物落在哪、是否跨会话隔离，**不决定查什么**。装配只拧**路数 × 模型**。

> 为什么改：按角色切分会留下缝——「这条算 PL 的还是 external 的」，没人接的项就漏了。年检实证方向清单式产出是角色关注点式的 2.1×。技术合理性 / 测试覆盖这些**视角仍在**，只是作为清单里的条目,不再是独立席位。

编排与 `state.py` 命令始终归 PMO 主对话；stage 内任务按需 dispatch subagent（上下文隔离 · 评审路必须隔离）。

### 跨宿主兼容

| 宿主 | 检测条件 | 指令文件 |
|------|----------|----------|
| Claude Code | .claude/ | CLAUDE.md |
| Codex CLI | .codex/ | AGENTS.md |
| Gemini CLI | .gemini/ | GEMINI.md |

session 启动时 `bootstrap.py` 做系统维护(骨架 / localconfig 自愈 / codex agent toml 部署 · 历史注入块与 legacy hooks 清理)。🔴 v8.211 起**不再注入**宿主指令文件(CLAUDE.md / AGENTS.md / GEMINI.md)—— 共享仓库里注入块会污染不用 teamwork 的用户;关键信息(PMO 定位 / worktree 纪律 / Subagent 授权)以 SKILL.md 为唯一载体 · bootstrap 自动清理历史注入块。

### 协作模型

**单人模式（默认）**：一个用户 + 一个 AI 会话操作整个项目。`.teamwork_localconfig.json` 的 scope 用于聚焦关注范围，而非并发控制。

**多人模式（实验性）**：多个用户各自用独立会话操作不同子项目。约束：每个子项目同一时刻只能有一个会话、不同用户必须负责不同子项目（scope 不重叠）、跨子项目需求由一个用户统一协调、不支持同一子项目并发开发。

### Worktree 策略

**默认 auto**。prepare 子流程为每个 Feature 创建隔离 worktree（`{worktree_root_path}/{Feature-ID}` · 默认 `worktree_root_path=.worktree`），Dev Stage 在 worktree 内开发，Ship Stage 第二段验证合并后清理。`init-feature` 物化校验 worktree 路径约定 + cwd。适合多个 Feature 并行 + 主分支保持稳定的场景。可在 `.teamwork_localconfig.json` 配置。

### 待规划需求池

跨 Feature/session 发现的"本次范围外但要做"事项，记入 `product-overview/PENDING.md`（已从 teamwork-space.md 外置 · 命中 backlog 查询才读）。用户问「还有什么待做 / pending / backlog」时 PMO 自动列出；转成 Feature/Bug 后即从池中移除，保持轻量。

### 产品规划体系

Teamwork 内置 **Product Lead (PL)** 角色维护产品规划文档：

```
product-overview/
├── {项目名}_业务架构与产品规划.md
├── workstream/                            # WS-NN.md · 规划单元（核心）
└── {项目名}_Product_Plan.md               # 可选
```

项目首次初始化时若 `product-overview/` 不存在，PMO 自动切换到 PL 引导模式。产品方向性话题（调整商业模式、增减业务线）PMO 会调度 PL 进入讨论模式。讨论结论需要落地时 PL 进入执行模式，按变更级别（Level 1 功能级 / Level 2 业务模块级 / Level 3 方向级）触发下游级联到 Feature Planning。

开发过程中如发现当前 Feature 与上游文档矛盾（如 ROADMAP 已有 Feature 冲突、产品架构需要调整），会触发**自下而上影响升级**：PMO 向上追溯影响层级直到找到需要变更的最高层文档，再由 PL 评估后向下级联。

---

## 核心保证（质量机制）

下列机制构成 Teamwork 的质量保证基础。每节描述机制本身和它针对的具体问题。

### 契约化产出

每个 Stage 文件统一为 **prerequisites（入口校验）/ artifacts（产物形态）/ evidence_checks（完成证据）** 契约。规范**去哪儿**（产出契约），不规范**怎么走**（执行方式由 AI 按规模/复杂度决定）。阶段产出物的形态被锁定，下游不会因为上一步"做得潦草"而推不动。

### 机器可校验 — AC↔Test 强绑定

PRD.md 和 TC.md 头部 YAML frontmatter 机读化，`acceptance_criteria[].id` ↔ `tests[].covers_ac` 一一绑定。`verify-ac.py` 脚本自动校验覆盖完整性，消除"需求→代码"漂移。

### 主对话产物协议

主对话直接执行任务（PRD 讨论、架构师 review、环境启动）时，产物**必须按 YAML frontmatter 规范落盘**。无论在哪个角色视角下产出，审计时一视同仁，不会因为"在主对话讨论的"就找不回去。

### 冷审清单（每 stage 一份 · N 路都过）

三段缺一即漏，机器门逐段校验：

- ⚔️ **对抗**：必须写成"我试图证明〈X 不成立〉，结果是…"——**不许打勾**。中性核对会把对抗项磨平（实证：角色一直在，"限制必要性"照样是盲区，因为它从没被写成题目）。
- 🔍 **核对**：可实现 / 可验证 / 测试真实性 / 代码质量盲区等，逐路申报 `coverage`，可以写"查过无发现"。
- 💡 **清单外洞察**：清单没问、但你认为该关注的（≥1 条或显式"无 + 为什么"）。**不为凑内容而写**。

产物是 **REVIEW.md 单份**（frontmatter 逐路列 `reviewers` / `review_models` / `coverage` / `outside_checklist_insight` + findings 机读台账），external lane 的冷审产物另落 `external-cross-review/*.md`。

🔁 **验证轮范围锁定**（Round 2+）：只核实上轮 finding 的处置 + 修订处的连带影响，**禁全量重扫**；新 finding 仅限出自修订处，或 BLOCKER 级并附"为何首轮未发现"。防的是多轮审查把边角挖成问题。

### fix-retry 循环

review / test 失败时在 stage 内 fix-retry（RD 修代码 → 重新评审/重跑），不切 stage，audit 留 `rounds[]` 完整循环记录。只在最终通过时才转下一 stage。

### ADR 决策记录

当讨论触发三问之一（Why / Options / Tradeoff），且有非平凡的决策发生时，自动落盘一份 ADR 到 `{子项目}/docs/adr/`（**唯一落点** · 不落 Feature 目录）。PMO 在 goal/blueprint 入口扫描相关 ADR 并注入上下文，避免老决策被忘记后重复讨论。

### KNOWLEDGE 4 类收敛

项目级 `project-specs/KNOWLEDGE.md`（AI 沉淀）分四类：**Gotchas**（踩坑）/ **已澄清歧义** / **用户偏好** / **已否方向**。每类有硬触发时机（如 debug 后写 Gotcha、澄清后记歧义），不靠自觉，同样的坑不会反复踩。分工边界：开发规矩归 `project-specs/DEV-RULES.md`（人维护）· 架构沉淀走 ADR / ARCHITECTURE · 复盘单独放 `retros/`。

### Ship Stage

**第一段（worktree 内 · 全交付）**：净化 commit → **知识沉淀 distill**（把「描述代码」的知识 graduate 到知识层 KNOWLEDGE / ADR / REG / ARCHITECTURE / database-schema）→ **归档**（feature 目录归档 + 规划翻牌 · 随 feature MR 单 commit 原子合入）→ push 分支 → CLI 创 MR → 输出 user_card（MR 链接置顶）+ 📦 交付总结 → **await-merge 30s 轮询**（全模式必跑 · 检测 MERGED 自动进第二段）。

**第二段（ship-finalize · 主工作区 · 零内容清场）**：verify-delivered 验证交付落地 → 删 worktree → 主分支 pull 同步 · state.json 标 completed。

MR/PR 由 PMO 用 `gh` / `glab` CLI 实际创建并给出真实链接 · CLI 不可用时按平台模板生成 URL 兜底 + 提示用户手动点击。

PM 验收暂停点 3 选 1：① 通过 + Ship（自动进 Ship Stage）② 通过但暂不 Ship ③ 不通过 + 修复派发。

### 项目排查工具集 TROUBLESHOOTING.md

teamwork mode A query / E · discuss 触及「排查 / 报错 / 查 log / 查环境」时 · PMO 自动 read `project-specs/TROUBLESHOOTING.md`：

- **路径固定**：`{项目}/project-specs/TROUBLESHOOTING.md`（bootstrap 自动建空骨架 · 项目根旧散放文件自动迁入）
- **teamwork 提供模板**：[templates/troubleshooting.md](./skills/teamwork/templates/troubleshooting.md)（4 段最小骨架：环境 / 查 log / 查数据缓存 / 常见报错 + 安全约束 + 维护）
- **内容用户 / AI 共同沉淀**：teamwork 不假设技术栈（K8s vs Docker vs Serverless）· 不规范具体命令
- 与 [KNOWLEDGE.md](./skills/teamwork/templates/knowledge.md) 互补：KNOWLEDGE = 踩坑注意点 · TROUBLESHOOTING = 操作步骤

### 外部模型只读评审

第三视角冷审在 teamwork 中**仅用于只读评审** · 不参与代码写权（红线 R1）：

- 评审路一律**独立 subagent 隔离冷审** · 逐路模型错开（至少一路 ≠ 会话主模型），独立采样揭露同模型自评盲区
- 评审产物是 markdown · 不改代码
- 📎 **跨厂商 CLI 异质（codex / gemini）已退役**：冷启动、安全审查慢路径、登录故障面严重拖慢流程，而同厂商错开已经拿到独立性收益

### Evidence-binding 物化拦截

事实型字段（mr_url / feature_head_commit / test_exit_code 等）必须有 evidence 支撑（command + stdout + exit_code）：

- **物化拦截层级 = state.json schema 完整性**：PMO 写 state.json 事实字段时不能凭印象（编造与真实命令格式不符 · 用户/PM 抽查识破）
- **状态字段 vs 事实字段**边界清晰：current_stage / phase / verdict 是状态字段（PMO 自判 · 无需 evidence）· stdout / mr_url 是事实字段（外部观察 · 必须 evidence）
- `state.json` 含 `_state_checksum` 自防护，跨宿主直写 state.json 会被物理拦截

### 状态恢复机制

`{Feature}/state.json` 是流转状态的**单一权威**。新对话 / compact / 会话退出重开，读 `state.json` 即可恢复，不依赖对话记忆。

### 闭环验证

RD/QA 声称"完成"必须附实际命令输出（测试/构建结果）；PMO 完成报告必须引用实际数据；禁止空口完成。所有降级路径（外部模型不可用、worktree 不可用等）必须输出结构化 WARN 日志，静默降级视为违反闭环验证红线。

### Prompt Cache 友好

按 4 层模型组织文档（L0 框架 / L1 项目 / L2 Feature / L3 动态），稳定层和动态层严格分离，Stage 入口 Read 顺序固定，state.json 访问次数受限，减少 AI 在跨 Stage / 跨 Feature 时的重复思考——同样的 Feature 工作流，下一次推进的成本和延迟都明显更低。

### 绝对红线（9 条 R1-R9）

teamwork 的 9 条核心红线，其中 8 条由 `state.py` 状态机物化校验（可枚举规则进脚本），1 条（R3 PMO 统一承接）是 PMO 主对话内的软规则。

| 红线 | 内容（一句话）|
|------|----------|
| **R1** 代码写权归 RD | 代码 / 测试 / 构建配置由 RD 角色执行；外部模型仅只读评审 |
| **R2** 流程类型闭集 | `{Feature, Bug}` + preset `{micro, floor, tiny, lite, medium, full}` + 不进状态机的 Feature Planning / 问题排查 · 禁止自创变体 |
| **R3** PMO 统一承接 | 所有用户输入由 PMO 先承接 · 禁止其他角色直接响应 |
| **R4** 流程边界 | 不简化（不擅自跳过阶段）/ 不膨胀（自动流转节点禁止插入暂停）/ 必给步骤描述 |
| **R5** 暂停点协议 | 必等用户确认 + 必给 💡 推荐 + 编号化（单决策 1/2/3 · 多决策 1A 2B）|
| **R6** Feature Planning 只出文档 | 不出代码 · 不自启 Feature 流程 |
| **R7** 证据闭环 | 声称完成必附 commit + 实测输出；事实字段 evidence-binding |
| **R8** 写操作硬门禁链 | prepare 完成前拒绝 stage-start · Ship Phase 1 CLI-first |
| **R9** session bootstrap | 入口必跑 bootstrap.py + PMO 按 5 mode 分诊 |

完整红线条文见 [SKILL.md](./skills/teamwork/SKILL.md)（现行权威）。

---

## 文档导航

| 文件 | 作用 |
|------|------|
| [SKILL.md](./skills/teamwork/SKILL.md) | 主入口：设计哲学 + 命令清单 + Triage 入口规范 + 9 红线 + 项目级文档架构 |
| [FLOWS.md](./skills/teamwork/FLOWS.md) | 流程闭集 telos（Feature/Bug × preset + 2 个不进状态机）与适用场景 |
| [STAGES.md](./skills/teamwork/STAGES.md) | 11 stage 索引 + 通用 cite 纪律 |
| [ROLES.md](./skills/teamwork/ROLES.md) | 角色索引（→ roles/*.md） |
| [STANDARDS.md](./skills/teamwork/STANDARDS.md) | 技术规范索引（→ standards/*.md） |
| [TEMPLATES.md](./skills/teamwork/TEMPLATES.md) | 文档模板索引 |
| [docs/prepare.md](./skills/teamwork/docs/prepare.md) | mode B → 进状态机前的准备子流程 |
| [docs/feature-planning.md](./skills/teamwork/docs/feature-planning.md) | Feature Planning 流程指南（不进状态机） |
| [docs/conventions.md](./skills/teamwork/docs/conventions.md) | Feature ID + worktree path 命名规范 |
| [stages/*.md](./skills/teamwork/stages/) | 各 stage Telos + Output Contract |
| [roles/*.md](./skills/teamwork/roles/) | 角色 telos + 创作要点 |
| [standards/*.md](./skills/teamwork/standards/) | 技术规范（common / backend / frontend / tdd 等） |
| [tools/state.py](./skills/teamwork/tools/state.py) | 唯一编排器入口 |
| [docs/CHANGELOG.md](./skills/teamwork/docs/CHANGELOG.md) | 最近 5 版变更（更早历史走 git 提交历史） |

详细目录结构见 [skills/teamwork/](./skills/teamwork/)。

---

## 版本

当前 **v8.360**（版本单源 = [SKILL.md](./skills/teamwork/SKILL.md) frontmatter）。变更记录见 [docs/CHANGELOG.md](./skills/teamwork/docs/CHANGELOG.md)（最近 5 版）· 更早历史走 git 提交历史（CHANGELOG-ARCHIVE **定期清空**）。

---

## License

MIT
