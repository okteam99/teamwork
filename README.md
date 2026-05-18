# Teamwork

AI 从团队协作视角出发，通过**流程编排 + 角色视角切换 + 契约化 Stage + 机读状态机**，驱动从产品规划到交付的完整软件研发流程。

[English](./README-EN.md) · Version: **v7.3.10+P0-113**

---

## 设计前提

Teamwork 在两个维度上做匹配：

**按需匹配流程**：查代码、Bug、Feature 需要的协作深度完全不同。入口分诊（5 mode：query / execute / resume / status / discuss）意图匹配到合适流程 · 简单任务匹配简单流程 · 复杂需求走完整流程。

**按专业方向分配角色**：单角色覆盖多视角时会互相遮蔽——PM 的"用户想要"盖住 QA 的"边界情况"，架构师的"优雅"盖住 RD 的"交付期"。Teamwork 按专业分配：PM / 架构师 / QA / RD / Designer 各管一个维度（需求 / 架构 / 测试 / 实现 / UX），PMO 编排。每份产出从对应专业角度被检验 · 让盲区暴露给另一个视角。

你只需提需求 + 关键节点做决策。

### 多角色切换的工作机制

- **创建-批评循环**：PM 写 PRD → PL 从业务方向批评 → PM 修订，单角色单轮产出会跳过被自身视角遮蔽的盲区
- **注意力重分配**：切换角色 = 切换 checklist = 激活不同评价维度
- **强制重读**：角色切换迫使 AI 带着新问题重读同一份文档，发现的问题量级高于"再想想"
- **异质模型 Review**：评审环节引入异质模型角色独立 review（claude 作为主窗口时异质模型自动为 codex · 反之亦然），跨模型视角揭露同模型自评盲区

---

## 第一次用

### 安装

```bash
# 自动检测宿主环境（Claude Code / Codex CLI / Gemini CLI）
npx skills add okteam99/teamwork

# 或手动安装
bash skills/teamwork/install.sh
```

### 升级

```bash
npx skills update okteam99/teamwork
```

### 启动一个流程

```bash
# Feature（完整需求 → 设计 → 开发 → 测试 → 验收 → 交付）
/teamwork 实现用户登录功能

# 小改动（敏捷：≤5 文件、方案明确、无 UI/架构变更）
/teamwork 在用户列表增加导出 CSV 按钮

# 微调（Micro：零逻辑变更的文案 / 样式 / 资源替换）
/teamwork 把首页 logo 换成新的图片

# Bug 处理
/teamwork 登录页面在手机端返回 500 错误

# 问题排查（不产出代码，只定位根因）
/teamwork 最近 3 天生产环境 P95 延迟变高了，帮我看看

# Feature 规划（拆 ROADMAP，不产出代码）
/teamwork 规划电商推荐系统

# auto 模式（自动完成所有流程事项，直接推进到 MR 创建完成）
/teamwork auto 实现用户登录功能
```

### 你要做什么 vs AI 要做什么（产品迭代阶段）

| 阶段 | 你做的事 | AI 做的事 |
|------|----------|-----------|
| 起点 | 给一句话需求 | PMO 初步分析 + 识别流程类型 + 给完整步骤描述 |
| 确认流程 | 回 ok / 反馈 | 根据流程读取必要知识库文档 · 启动流程 |
| PRD | 等 / 纠偏 | PM 起草 PRD + 多角色并行评审 + 收敛 |
| 确认 PRD | 回 ok | — |
| 设计 | 等 | Designer 产出 UI + 同步全景 |
| 技术方案 | 等 | RD 起草 TECH + QA 起草 TC + 架构师 + 异质模型评审 |
| 开发 | 等 | RD 按 TDD 实现 + 单测 + 机器校验 |
| 审查 | 等 | 架构师 + QA + **异质模型（如 codex / claude）** 三视角独立 Review |
| 测试 | 等（启应用如需）| QA 集成测试 + API E2E 脚本化 |
| 验收 | 回 ok / 反馈 | PM 角度验收 + PMO 整理交付报告 + 自动 commit |
| **Ship Phase 1** | 点击 merge 按钮 | 创建好 MR/PR · 给出 MR 链接 → ⏸️ 等合并 |
| **Ship Phase 2** | 等 | 验证合并 + 收尾（state.json 终态 + 清理 worktree）→ ✅ |

典型 Feature 暂停点数量：**3-5 个**。

### 你要做什么 vs AI 要做什么（产品方向规划）

从业务全景到具体 Feature 的拆解流程，PL（Product Lead）主导、PMO 编排、PM 承接落地。

| 阶段 | 你做的事 | AI 做的事 |
|------|----------|-----------|
| 起点 | 给一句话方向（如「做电商推荐系统」/「调整商业模式」） | PMO 识别为产品方向类输入 · 调度 PL |
| 业务全景 | 回答 PL 关键问题（用户 / 价值 / 场景） | PL 引导构建 product-overview（业务架构 + 执行手册）|
| 确认业务全景 | 回 ok / 纠偏 | PL 落地 product-overview/ 文档 |
| 方向讨论 | 抛话题（增减业务线 / 商业模式调整） | PL 讨论模式：多视角分析 + 选项 + 推荐 |
| 拍板方向 | 选定方向 | PL 进入执行模式 · 判定变更级别（功能 / 业务模块 / 方向）|
| ROADMAP 拆解 | 等 / 纠偏 | PMO 调度拆 ROADMAP（业务线 → 模块 → Feature 列表）|
| 确认 ROADMAP | 回 ok | PMO 落地 ROADMAP.md + sitemap.md |
| 选 Feature 启动 | 指定下一个 Feature | PMO 转入 Feature 流程（进入「产品迭代阶段」表）|
| Feature 完成回流 | 等 | PMO 自动回写 ROADMAP 状态 + 更新 sitemap |

典型方向规划暂停点数量：**1-3 个**（业务全景确认 + 方向拍板 + ROADMAP 确认）。

---

## 5 mode 入口分诊（v7.3.10+P0-106 入口架构重构）

teamwork 入口是 **triage stage 的 5 mode 分诊** · 仅看用户输入决定走哪条最小路径：

| mode | 触发场景 | 行为 | 开销 |
|------|---------|------|------|
| **A · query** | 「看下 / 调研 / 解释 / why / 排查」+ 没推进动词 | 直接 grep / Read 答 + 跟进引导 · 不进 stage 链 | ~80 tokens |
| **B · execute** | 「实现 / 修复 / 创建 / 改」+ 明确动作 | 进 prepare-stage 重型准备 → 流程类型识别 → 业务 stage 链 | ~600-850 |
| **C · resume** | 「继续 F032 / ship F032」 | 找 state.json + jump 到 current_stage | ~300 |
| **D · status** | `/teamwork`（空命令）/「现在到哪了」 | 加载 Feature 看板 + 输出 | ~400 |
| **E · discuss** | 「我感觉 / 你怎么看 / X vs Y / 建议 / 哪种更合理」 | 综合视角讨论 + 选项 + 推荐 + 询问 → 用户拍板后升级 mode | ~150 |

**原则**：按需启动 · 为目标达成选择合适的流程。

## mode B 内部 5 种流程类型 — 该走哪条

| 流程 | 适用场景 | 产出 | 默认暂停点 |
|------|----------|------|-----------|
| **Feature** | 完整功能开发 | 代码 + 文档 + 测试 | 3-5 |
| **敏捷需求** | ≤5 文件 + 方案明确 + 无 UI/架构变更 | 代码 + 简化文档 + 测试 | 2-3 |
| **Micro** | 零逻辑变更（文案/样式/资源/配置常量/注释文档） | 代码（直改） | 2（确认 + 验收） |
| **Bug 处理** | 线上/本地缺陷 | 修复 + BUG 报告 + 回归测试 | 3-4 |
| **Feature Planning** | 从产品目标拆 ROADMAP | PROJECT.md + ROADMAP.md + sitemap.md | **1**（仅最终摘要确认）|

流程类型由 prepare-stage 在 mode B 入口自动识别，你只负责在暂停点确认。

---

## 进阶使用

### 流程控制

```bash
# 查看当前状态（走到哪一步 / 下一步是什么 / 待决策点）
/teamwork status

# 恢复被中断的流程（新对话 / compact 后也能恢复，靠 state.json）
/teamwork 继续

# ⚡ auto 模式：一次性总开关，非关键暂停点自动流转（v7.3.10+P0-11）
/teamwork auto

# 切换角色（通常不需要手动切换，PMO 会自动调度）
/teamwork pm | designer | qa | rd | pmo

# 退出协作模式
/teamwork exit
```

暂停点选项都是编号化的（💡 推荐项标第一，最后一项始终是「其他指示」），**回复一个数字即可**，不用打字。支持多决策点组合（如 `1A 2B`）。

### 角色体系

- **PMO**（流程编排）：承接用户输入 → 识别流程 → 调度角色 → 状态机维护 → 预检与暂停点
- **Product Lead (PL)**：产品方向。引导模式（从零构建 product-overview）/ 讨论模式（业务话题）/ 执行模式（变更级联 + Change Request lifecycle）
- **PM**：PRD + 结构化 AC + 最终验收
- **Designer**：UI 还原 + 全景（sitemap + preview）
- **架构师**：Tech Review（Blueprint）+ Code Review（Review Stage）+ ARCHITECTURE.md 维护 + ADR 决策
- **QA**：TC（AC↔test 绑定）+ TC 技术评审（Blueprint）+ Code Review + 集成测试 / API E2E
- **RD**：TDD 实现 + 单测 + 自查 + Bug 排查报告
- **External Reviewer**：异质模型代码评审（gh / claude / codex CLI · 立场独立性硬约束）

### 跨宿主兼容

| 宿主 | 检测条件 | SKILL_ROOT | 指令文件 |
|------|----------|------------|----------|
| Claude Code | Task 工具 + .claude/ | .claude/skills/teamwork | CLAUDE.md |
| Codex CLI | .codex/ 或 .agents/ | .agents/skills/teamwork | AGENTS.md |
| Gemini CLI | .gemini/ | .gemini/skills/teamwork | GEMINI.md |
| 通用 | 均不匹配 | 从 SKILL.md 推断 | AGENTS.md |

执行方式也会自适应：Claude Code 用 Task dispatch Subagent，Codex CLI 用 agent toml spawn，不支持 Subagent 的宿主降级为主对话执行。

### 协作模型

**单人模式（默认）**：一个用户 + 一个 AI 会话操作整个项目。`.teamwork_localconfig.md` 的 scope 用于聚焦关注范围，而非并发控制。

**多人模式（实验性）**：多个用户各自用独立会话操作不同子项目。约束：每个子项目同一时刻只能有一个会话、不同用户必须负责不同子项目（scope 不重叠）、跨子项目需求由一个用户统一协调、不支持同一子项目并发开发。

### Worktree 策略

**默认 auto**（v7.3.10+P0-41 修订自原 P0-9 OFF 默认）。Goal-Plan Stage 入口自动按 `state.environment_config.worktree_mode` 创建隔离 worktree（`{worktree_root}/{Feature 全名}` · 默认 `worktree_root=.worktree`），Dev Stage 在 worktree 内开发，Ship Stage 第二段验证合并后清理。适合多个 Feature 并行 + 主分支保持稳定的场景。可在 `.teamwork_localconfig.md` 配置 `worktree_mode: off` 关闭。

### 产品规划体系

Teamwork 内置 **Product Lead (PL)** 角色维护产品规划文档：

```
product-overview/
├── {项目名}_业务架构与产品规划.md
├── {项目名}_执行手册.md
└── {项目名}_Product_Plan.md              # 可选
```

项目首次初始化时若 `product-overview/` 不存在，PMO 自动切换到 PL 引导模式。产品方向性话题（调整商业模式、增减业务线）PMO 会调度 PL 进入讨论模式。讨论结论需要落地时 PL 进入执行模式，按变更级别（Level 1 功能级 / Level 2 业务模块级 / Level 3 方向级）触发下游级联到 Feature Planning。

开发过程中如发现当前 Feature 与上游文档矛盾（如 ROADMAP 已有 Feature 冲突、产品架构需要调整），会触发**自下而上影响升级**：PMO 向上追溯影响层级直到找到需要变更的最高层文档，再由 PL 评估后向下级联。

---

## 核心保证（质量机制）

下列机制构成 Teamwork 的质量保证基础。每节描述机制本身和它针对的具体问题。

### 契约化产出

每个 Stage 文件统一为 **Input Contract / Process Contract / Output Contract** 三段式（v7.3）。规范**去哪儿**（产出契约），不规范**怎么走**（执行方式由 AI 按规模/复杂度决定，v7.3 AI Plan 模式）。阶段产出物的形态被锁定，下游不会因为上一步"做得潦草"而推不动。

### 机器可校验 — AC↔Test 强绑定

PRD.md 和 TC.md 头部 YAML frontmatter 机读化，`acceptance_criteria[].id` ↔ `tests[].covers_ac` 一一绑定。`verify-ac.py` 脚本自动校验覆盖完整性，消除"需求→代码"漂移。

### 主对话产物协议

主对话直接执行任务（PRD 讨论、架构师 review、环境启动）时，产物**必须按 YAML frontmatter 规范落盘**。和 Subagent dispatch 协议形成完整闭环——主对话产出和 Subagent 产出在审计时一视同仁，不会因为"在主对话讨论的"就找不回去。

### 多视角 Review

- **架构师**：默认主对话（保留项目架构累积上下文 + 怀疑者视角防鼓掌）
- **QA**：走 Subagent 保独立视角
- **Codex**：第三方交叉 review（opt-in，v7.3.10+P0-13 默认 OFF 控制成本）

三份产物**结构独立**（独立 generated_at / files_read / 不互相引用），可机读校验，避免"前一份 Review 已经说没问题了，后面就不仔细看"的鼓掌效应。

### ADR 决策记录（v7.3.10+P0-21）

当讨论触发三问之一（Why / Options / Tradeoff），且有非平凡的决策发生时，自动落盘一份 ADR 到 `{Feature}/adrs/`。PMO 在 Plan/Blueprint 入口扫描相关 ADR 并注入上下文，避免老决策被忘记后重复讨论。

### KNOWLEDGE 3 类收敛（v7.3.10+P0-22）

项目级 `KNOWLEDGE.md` 分三类：**Gotcha**（踩坑）/ **Convention**（规约）/ **Architecture**（架构片段）。每类有硬触发时机（如 debug 后写 Gotcha、Review 后写 Convention），不靠自觉，同样的坑不会反复踩。复盘从 KNOWLEDGE 剥离，单独放 `retros/`。

### Ship Stage

**第一段 push** → ⏸️ 用户在平台合并 → **第二段 finalize**（验证合并 + worktree 清理 + state.json 标 completed）。

MR/PR 由 PMO 用 `gh` / `glab` CLI 实际创建并给出真实链接 · CLI 不可用时按平台模板生成 URL 兜底 + 提示用户手动点击。

PM 验收暂停点 3 选 1：① 通过 + Ship（自动进 Ship Stage）② 通过但暂不 Ship（仅 push feature 分支归档）③ 不通过 + 修复派发。

### 项目排查工具集 TROUBLESHOOTING.md（v7.3.10+P0-109 / +P0-110）

teamwork mode A query / E · discuss 触及「排查 / 报错 / 查 log / 查环境」时 · PMO 自动 read 项目根 `TROUBLESHOOTING.md`：

- **路径固定**：项目根 `TROUBLESHOOTING.md`（teamwork 不查 docs/ · 类比 teamwork_space.md 处理）
- **teamwork 提供模板**：[templates/troubleshooting.md](./skills/teamwork/templates/troubleshooting.md)（4 段最小骨架：环境 / 查 log / 查数据缓存 / 常见报错 + 安全约束 + 维护 · 共 ~50 行）
- **内容用户维护**：teamwork 不假设技术栈（K8s vs Docker vs Serverless）· 不规范具体命令
- **不存在时**：PMO 一句话提示用户从模板创建（不强推 / 不阻塞 · 用通用方法继续排查）
- 与 [KNOWLEDGE.md](./skills/teamwork/templates/knowledge.md) 互补：KNOWLEDGE = 踩坑注意点 · TROUBLESHOOTING = 操作步骤

### Codex CLI 合规使用（v7.3.10+P0-104 OpenAI ToS 合规）

外部模型 codex / claude / gemini 在 teamwork 中**仅用于只读评审** · 不参与代码写权：

- 5 个非评审 codex profile（rd-developer / tester / planner / designer / e2e-runner）标 deprecated（teamwork 主流程不再 dispatch · 仍保留兼容手动 ad-hoc）
- 全部 codex profile sandbox_mode = read-only（不再 full sandbox）+ 删除 service_tier=fast + 删除 hooks.json（持久化触发信号）
- 评审 profile（reviewer / blueprint-reviewer / prd-reviewer）developer_instructions 加 STRICT CONSTRAINTS 头：READ-ONLY · markdown only · "Out of scope" 拒绝模板
- 申诉模板见 [standards/external-model-usage.md § 十](./skills/teamwork/standards/external-model-usage.md)

### Evidence-binding 物理拦截（v7.3.10+P0-101 / +P0-112 层级修正）

事实型字段（available_external_clis / mr_url / feature_pushed_at / tests_passed / pm_self_check.code_context_read 等）必须含 evidence binding（command + stdout + exit_code + timestamp）：

- **物理拦截层级 = state.json schema 完整性**（不在主对话 verbatim · v7.3.10+P0-112 修正自原 P0-101）
- **主对话只输出精炼结论**（如 "🌐 External 探测：codex ✅ / claude ⏭️ / gemini ❌"）· 与 silent execution 协同
- 拦截力等价：PMO 写 state.json stdout 字段时不能凭印象（编造与真实命令格式不符 · 用户/PM 抽查识破）
- **状态字段 vs 事实字段**边界清晰：current_stage / phase / verdict 是状态字段（PMO 自判 · 无需 evidence）· stdout / mr_url 是事实字段（外部观察 · 必须 evidence）

详见 [standards/evidence-binding.md](./skills/teamwork/standards/evidence-binding.md)。

### 状态恢复机制

`{Feature}/state.json` 是流转状态的**单一权威**（v7.3.2 替代 STATUS.md）。新对话 / compact / 会话退出重开，读 `state.json` 即可恢复，不依赖对话记忆。

### 闭环验证

RD/QA 声称"完成"必须附实际命令输出（测试/构建结果）；PMO 完成报告必须引用实际数据；禁止空口完成。所有降级路径（Subagent 失败、Codex 不可用、worktree 不可用）必须输出结构化 WARN 日志，静默降级视为违反闭环验证红线。

### Prompt Cache 友好（v7.3.10+P0-23）

按 4 层模型组织文档（L0 框架 / L1 项目 / L2 Feature / L3 动态），稳定层和动态层严格分离，Stage 入口 Read 顺序固定，state.json 访问次数受限，减少 AI 在跨 Stage / 跨 Feature 时的重复思考——同样的 Feature 工作流，下一次推进的成本和延迟都明显更低（典型 Feature 场景 ≈ ↓60-70%）。

### 绝对红线（8 条 R1-R8 · v7.3.10+P0-103 归并 + 层级化）

红线从原 16 条归并为 **R1-R8 · 8 条核心**，引入**三层级化**（L1 核心红线 / L2 专项规范 / L3 工具层）+ **生命周期管理元规则**（每 P0 patch 必走"路径 A 归并 / 路径 B 降级 / 路径 C 新增"三选一审视 · 防止再膨胀）。

| 红线 | 内容（一句话）|
|------|----------|
| **R1** 代码写权归 RD | 代码 / 测试 / 构建配置由 RD 角色执行（含 Ship Stage finalize 例外）+ **外部模型仅只读评审**（v7.3.10+P0-104 OpenAI ToS 合规）|
| **R2** 流程类型闭集 | 5 种流程：Feature / Bug / Micro / 敏捷需求 / Feature Planning · 禁止自创变体 |
| **R3** PMO 统一承接 | 所有用户输入由 PMO 先承接 · 禁止其他角色直接响应 |
| **R4** 流程边界 | (a) 不简化（不擅自跳过流程阶段）(b) 不膨胀（自动流转节点禁止插入暂停 · 含容量焦虑暂停黑名单 v7.3.10+P0-102）(c) 必给步骤描述 |
| **R5** 暂停点协议 | 必等用户确认 + 必给 💡 建议 + 编号化（单决策 1/2/3 · 多决策 1A 2B）|
| **R6** Feature Planning 只出文档 | 不出代码 · 不自启 Feature 流程 |
| **R7** 证据闭环 | (a) 实测输出（声称完成必附命令 stdout）(b) 声明即承诺（Stage 入口 Execution Plan + Cite spec）(c) 事实字段 evidence-binding（v7.3.10+P0-101 / +P0-112 物理拦截层级 = state.json schema · 主对话精炼结论）|
| **R8** 写操作硬门禁链 | (a) 流程入口门禁（PMO 未输出初步分析前禁止写）(b) Subagent dispatch 预检（c) Ship Phase 1 CLI-first 门禁（v7.3.10+P0-113 trip-wire 破除 git push hint URL trap）|

完整红线条文 + L2/L3 sub-file 索引见 [SKILL.md](./skills/teamwork/SKILL.md) 顶部。

---

## 文档导航

| 文件 | 作用 |
|------|------|
| [SKILL.md](./skills/teamwork/SKILL.md) | 主入口：8 条红线 R1-R8、项目级文档信息架构、AI Plan 模式 |
| [stages/triage-stage.md](./skills/teamwork/stages/triage-stage.md) | teamwork 真正入口（v7.3.10+P0-106）：5 mode 分诊 |
| [stages/prepare-stage.md](./skills/teamwork/stages/prepare-stage.md) | mode B 重型准备（v7.3.10+P0-106）：宿主检测 + KNOWLEDGE/ADR + 流程类型识别 + state.json 创建 |
| [FLOWS.md](./skills/teamwork/FLOWS.md) | 5 种流程类型的选择与详细执行规则 |
| [ROLES.md](./skills/teamwork/ROLES.md) | 角色索引（→ roles/*.md） |
| [RULES.md](./skills/teamwork/RULES.md) | 核心规则：暂停 / 流转 / 变更 / 闭环验证 |
| [REVIEWS.md](./skills/teamwork/REVIEWS.md) | 评审规范（PRD / TC / UI 还原验收） |
| [STANDARDS.md](./skills/teamwork/STANDARDS.md) | 编码规范索引（含 prompt-cache / output-tiers / discussion-mode / evidence-binding / external-model-usage / stage-instantiation）|
| [standards/discussion-mode.md](./skills/teamwork/standards/discussion-mode.md) | E · discuss 详规范（v7.3.10+P0-106）：触发规则 / 知识地图 / 与 PL 讨论 / Feature Planning 边界 |
| [standards/evidence-binding.md](./skills/teamwork/standards/evidence-binding.md) | 事实字段证据绑定（v7.3.10+P0-101 / +P0-112）：state.json schema 物理拦截 |
| [standards/external-model-usage.md](./skills/teamwork/standards/external-model-usage.md) | 外部模型 OpenAI ToS 合规（v7.3.10+P0-104）：codex 只读评审 + 申诉模板 |
| [templates/troubleshooting.md](./skills/teamwork/templates/troubleshooting.md) | 项目排查工具集模板（v7.3.10+P0-109/+P0-110）：4 段最小骨架 |
| [STATUS-LINE.md](./skills/teamwork/STATUS-LINE.md) | 状态行格式 + 意图识别 |
| [TEMPLATES.md](./skills/teamwork/TEMPLATES.md) | 文档模板索引 |
| [CONTEXT-RECOVERY.md](./skills/teamwork/CONTEXT-RECOVERY.md) | 新对话 / 中断恢复机制 |
| [docs/CHANGELOG.md](./skills/teamwork/docs/CHANGELOG.md) | 完整版本变更记录 |

详细目录结构见 [skills/teamwork/](./skills/teamwork/)。

---

## 版本历史

**v7.3.10 + P0 系列**（当前 **P0-113** · 仅列里程碑）：

🌟 **入口架构终极重构（P0-106 ~ P0-110 · 6 patch 收官）**：
- **P0-110** troubleshooting 模板砍重 367→50 行（4 段最小骨架 · 不假设技术栈）
- **P0-109** 项目排查工具集 TROUBLESHOOTING.md 引入（路径固定项目根 · teamwork 不规范内容）
- **P0-108** Feature Planning 流程精简（4 暂停 → 1 暂停 · 讨论部分迁 E · discuss）
- **P0-107** init-stage.md 物理删除 + 全框架 22 处引用迁移
- **P0-106** 5 mode 入口分诊（A query / B execute / C resume / D status / E discuss）+ prepare-stage 新建 + 项目级文档信息架构 + E · discuss 模式

🛡️ **设计哲学修正（P0-101 ~ P0-105 + P0-112）**：
- **P0-113** Ship Phase 1 CLI-first 双层防御（状态机字面 + R8(c) trip-wire 破除 git push hint URL trap）
- **P0-112** evidence-binding 物理拦截层级修正（state.json schema 层 · 主对话精炼结论 · 主对话减重）
- **P0-105** init/stage 入口 silent execution 强化（隐式承接 + stage 入口标题禁令）
- **P0-104** codex 调用 OpenAI ToS 合规（5 profile read-only + 删 service_tier=fast + 删 hooks.json + 申诉模板）
- **P0-103** 红线归并 16 → 8（R1-R8 + 三层级化 L1/L2/L3 + 生命周期管理元规则防再膨胀）
- **P0-102** 容量焦虑暂停反模式（措辞黑名单破除"为下回合留预算"伪暂停）
- **P0-101** 事实字段 evidence-binding（detection_evidence schema · 状态字段 vs 事实字段边界）

🌟 **P0-100** README 同步收齐技术债（P0-60 → P0-100 · 反映 Wave 1-4 + 各项体感改进）

**评审规范分层规范化项目（4 Wave · 完整收官）**：
- **P0-99** Ship Stage CLI 优先创建 MR（gh / glab 实际创建 · URL 兜底 · 失败诊断不静默降级）
- **P0-98** Silent execution 硬规则（框架仪式 / Step 头 / 思考链播报禁止 · 主对话仅 3 类输出）
- **P0-93~97 Wave 4** pmo.md 重点瘦身：1814 → 477 行（净删 1337 行 / 74% 减重 + 6 PMO sub-file）
- **P0-87~92 Wave 3** 6 role 4 段重构 + sub-file 化（架构师 / QA / RD / PM / Designer / PL / External）
- **P0-86 Wave 2** 架构师独立 peer-level role（与 RD 平级 · 不再寄生 RD 文件）
- **P0-85 Wave 1** 评审规范分层基础设施（review-verdict + review-scope 双单源 · 反模式 / Tier 1-2-3 规范）

**核心体感改进**：
- **P0-81** Pull/Push 模式根本改造（轻型意图静默直接 grep · 跳过框架仪式）
- **P0-78** ADR 触发判定 + 业务术语漂移升级（KNOWLEDGE.md Glossary）
- **P0-68** QA Code Review Step 4.5 PRD AC 直接对账（实证 F059 教训 · 埋点/日志/监控类 AC）
- **P0-60** triage Step 8 卡片式输出（必含 5 段 / 必砍 7 段 / 实战输出 -74%）
- **P0-58~59** teamwork_space.md 单源化（变更类 3 张表全砍 → changes/{id}.md 是变更唯一权威源）
- **P0-54** 主对话输出 Tier 1/2/3 规范单源（决策呈现 vs 履职报告）
- **P0-53** Plan Stage → Goal-Plan Stage 改名（与 Blueprint 对仗）
- **P0-49** 双对齐暂停（triage 意图理解 + 流程承诺一次确认）
- **P0-48** 框架元规则（加 1 删 1 / "重新触发回来"标尺 / 防累积膨胀）
- **P0-44** Goal-Plan Stage 5 子步骤（PM 起草 → PL-PM 讨论 → 多角色并行评审 → PM 回应 → 最终确认）
- **P0-41** Worktree 默认 auto + artifact_root 路径权威路由（teamwork_space.md docs_root 列）
- **P0-38** Stage 入口实例化 + External Reviewer 升格评审角色（triage 仅给骨架）
- **P0-36** Bug 流程 Ship 缩简分支（fix → ship 4 段）
- **P0-33** 跨子项目变更管理（changes/{change_id}.md 模板 + status=locked 才能启动子 Feature）
- **P0-32** Ship Stage finalize push merge_target（双段 + 仅 state.json 一文件 · 红线 #1 例外）
- **P0-29** Ship Stage 双段流程（push / finalize）
- **P0-26** triage Stage 前置（流程编排独立 Stage / 6 流程类型分诊 / KNOWLEDGE/ADR 扫描）
- **P0-23** Prompt Cache 友好改造（动态内容后置 + 入口 Read 顺序固定 + state.json ≤5 次/Stage）
- **P0-22** KNOWLEDGE.md 3 类收敛（Gotcha / Convention / Architecture 硬触发）
- **P0-21** 混合 ADR 体系（3 问触发器 + PMO 索引扫描）
- **P0-20** 红线 #1 重构（职责正交化 + Micro 升格为独立流程）
- **P0-15** Ship Stage MR 模式重构（push / MR / 仅本地 3 选 1）
- **P0-11** ⚡ auto 模式（一次性总开关 · HITL/AFK 暂停点二分 v7.3.10+P0-76）
- **P0-3** 懒装依赖模型（Goal-Plan → Dev → Test 逐阶段校验）

**v7.3.9**：PM 验收三选项 + Ship Stage + 每阶段 auto-commit + Goal-Plan Stage 入口 Preflight（P0-27 后已迁入 triage Step 7.5）
**v7.3.8**：Worktree 创建时机前移至 Goal-Plan Stage 入口
**v7.3.7**：PRD/Blueprint Codex 交叉评审 + Progress Log 实时轮询
**v7.3.6**：多决策点支持（数字决策点 + 字母选项 `1A 2B`）
**v7.3.5**：暂停点选项编号化（回复数字即可）
**v7.3.4**：暂停点压缩（UI+全景合并、验收+commit+push 合并 3 选 1）
**v7.3.3**：Stage 耗时度量闭环（duration / variance / retry / user_wait）
**v7.3.2**：STATUS.md 废弃，state.json 成为 Feature 目录唯一状态文件
**v7.3.1**：Execution Plan 3 行核心
**v7.3**：Stage 三契约化 + AI Plan 模式 + AC↔test 绑定 + 主对话产物协议 + state.json
**v7.2**：Dispatch 文件协议 + API E2E 脚本化 + Progress 可见性 + Key Context
**v7.1 及更早**：多角色评审、多子项目模式、变更级联、闭环验证等基础架构

完整变更记录见 [skills/teamwork/docs/CHANGELOG.md](./skills/teamwork/docs/CHANGELOG.md)。

---

## License

MIT
