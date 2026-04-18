# Teamwork

你的 AI 开发团队 — 一个 AI 以完整团队的方式工作，通过**角色视角切换 + 契约化 Stage + 机读状态机**，一个人驱动从产品规划到交付的完整软件研发流程。

[English](./README-EN.md) · Version: **v7.3.5**

## 概述

Teamwork 让一个 AI 以完整开发团队的方式工作。每个角色代表一个专业方向的关注点（PM 关注需求完整性、QA 关注测试覆盖、RD 关注实现质量、架构师关注技术合理性、Designer 关注用户体验），PMO 负责流程编排和信息流转。不是多个 AI 在开会——是确保每个产出物被从足够多的专业角度检验过。用户只需提出需求和在关键节点做决策。兼容 Claude Code / Codex CLI 等 AI 编程工具。

支持六种流程类型：

- **Feature 流程** — 完整的需求 → 设计 → 开发 → 测试 → 验收链路
- **Bug 处理流程** — 排查 → 判断 → 修复 → 验证 → 文档同步
- **问题排查流程** — 定位问题根因并由用户决定后续动作（不产出代码）
- **Feature Planning 流程** — 从产品目标拆解 ROADMAP（Wave 执行批次 + 依赖 + 并行度）
- **敏捷需求流程** — 小改动的精简链路（≤5 文件、无 UI/架构变更、方案明确）
- **Micro 流程** — 微调通道（零逻辑变更，资源/文案/样式/配置常量/注释文档）

补充说明：
- `Product Lead` 的引导/讨论/执行模式不是独立流程类型，而是 PMO 在六种标准流程之外使用的特殊路由模式。

### 设计哲学

软件工程的核心挑战不是写代码，而是从多个专业方向审视同一个东西。Teamwork 的每个角色代表一个专业方向的关注点（PM→需求完整性、QA→测试覆盖、RD→实现质量、架构师→技术合理性、Designer→用户体验、PL→产品方向），PMO 负责流程编排和信息流转。

多角色切换有效的底层机制：创建-批评循环（PM 写 PRD → PL 从业务方向批评 → PM 修订）、注意力重分配（切换角色 = 切换 checklist = 激活不同评价维度）、强制重读（角色切换迫使 AI 带着新问题重读同一份文档）。

### 核心特性（v7.3 系列）

#### 架构层

- **Stage 三契约化**（v7.3）：每个 Stage 文件统一为 **Input Contract / Process Contract / Output Contract** 三段式。规范**去哪儿**（产出契约），不规范**怎么走**（执行方式）。
- **AI Plan 模式**（v7.3，3 行核心）：每个 Stage 开始前 AI 在主对话输出 Execution Plan（Approach / Rationale / Role specs loaded / Estimated），执行方式由 AI 按规模/复杂度决定，不再硬绑定 Subagent。
- **AC↔Test 强绑定**（v7.3）：PRD.md 和 TC.md 头部 YAML frontmatter 机读化，`acceptance_criteria[].id` ↔ `tests[].covers_ac` 一一绑定。`python3 {SKILL_ROOT}/templates/verify-ac.py {Feature}` 自动校验覆盖完整性，消除"需求→代码"漂移。
- **state.json 机读状态机**（v7.3.2）：每个 Feature 目录下 `state.json` 是流转状态的**单一权威**，替代原 STATUS.md。包含 `current_stage / completed_stages / legal_next_stages / stage_contracts / planned_execution / executor_history`，compact 恢复单一锚点。
- **主对话产物协议**（v7.3 §六）：主对话直接执行任务（如 PRD 讨论、架构师 review、环境启动）时，产物必须按 YAML frontmatter 规范落盘，和 Subagent dispatch 协议形成完整闭环。

#### 流程层

- **六种流程**（Feature / Bug / 问题排查 / Feature Planning / 敏捷 / Micro）：通过 PMO 初步分析自动识别，每种都有明确的准入条件、步骤描述、完成标准。
- **Micro 真轻量**（v7.3，红线 #1 Micro 例外）：PMO 可直接改代码（白名单内零逻辑变更），**无需 Subagent、无需 Execution Plan、无需 dispatch 文件**，仅保留"分析→用户确认→执行→验收"最小闭环。
- **暂停点压缩**（v7.3.4）：
  - UI Design + Panorama Design 合并为一个「设计批」暂停点（Designer 一次产出 UI + 全景增量同步）
  - PM 验收 + commit + push 合并为一个暂停点（PMO 自动本地 commit，用户 3 选 1 决定 push）
  - 典型 Feature 暂停点从 6-8 个降至 4-5 个
- **暂停点编号化**（v7.3.5）：所有可选项以 `1/2/3...` 编号列出，推荐项标 💡 列第一，最后一项始终是「其他指示」，用户回复一个数字即可（而非打字）。
- **流程步骤描述**（v7.3）：PMO 初步分析必须给出流程的**完整步骤描述**（阶段链 + 每阶段做什么 + 暂停点），用户基于步骤而非流程名确认。

#### 执行层

- **Dispatch 文件协议**：每次 Subagent dispatch 生成 `{Feature}/dispatch_log/{NNN}-{subagent}.md`，文件即入参即审计记录；主对话 ↔ Subagent 交接结构化；并行/重派/降级全可追溯。
- **Key Context 6 类**：每次 dispatch 必填 6 类关键点（历史决策、本轮聚焦、跨 Feature 约束、已识别风险、降级授权、优先级），无则写 `-`（证明已判断）。
- **多视角 Review**（架构师 / QA / Codex 三路独立）：架构师默认主对话（保留项目架构累积上下文 + 怀疑者视角防鼓掌）；QA / Codex 走 Subagent 保独立视角；三份产物结构独立（独立 generated_at / files_read / 不互相引用，可机读校验）。
- **API E2E 脚本化**：Subagent 生成可重跑的 Python 脚本（`tests/e2e/F{编号}/api-e2e.py`），而非一次性 curl；4 类断言覆盖（status / body / DB / 副作用）；脚本 commit 作为 Feature 交付物。
- **耗时度量闭环**（v7.3.3）：每个 Stage 自动记录 `started_at / duration_minutes / estimated_minutes / variance_pct / dispatches_count / retry_count / user_wait_seconds`；Feature 完成报告自动聚合耗时统计表；retros/*.md 支持跨 Feature 趋势分析。
- **自动 commit，用户决 push**（v7.3.4）：PM 验收通过 → PMO 自动本地 commit（结构化 message 含 AC 覆盖 + Review 状态 + 耗时摘要）→ ⏸️ 用户 3 选 1（push / 仅本地 / 不通过修复）。PMO **禁止自动 push**，保留用户对远程推送的完全控制。

#### 质量保障

- **闭环验证红线**：RD/QA 声称"完成"必须附实际命令输出（测试/构建结果）；PMO 完成报告必须引用实际数据；禁止空口完成。
- **降级兜底 WARN 日志**：所有降级路径（Subagent 失败、Codex 不可用、宿主不支持 TodoWrite、worktree 不可用等）必须输出结构化 WARN 日志，静默降级视为违反闭环验证红线。
- **PMO 预检 L1/L2/L3**：dispatch 任何 Subagent 前必须完成对应级别预检，预检未通过不得 dispatch。
- **产品全景保护**（v7.3.4）：全景（`design/sitemap.md` + `design/preview/overview.html`）是已确认的**产品 + 业务逻辑真相**，Feature 流程默认**增量合并**，禁止重写；任何修改必须在 sitemap 加标红注释 + 执行报告列 diff；涉及结构性变更（删页面/重构导航）→ 建议改走 Feature Planning 流程。
- **TDD 驱动 + 机器校验**：推荐测试先行（弱约束）；单元测试、Typecheck、Lint 作为 Dev Stage Output Contract 硬门禁。
- **状态恢复机制**：新对话/compact 后读 `{Feature}/state.json` 即可恢复，不依赖对话记忆。

## 跨宿主兼容

Teamwork 通过 `{SKILL_ROOT}` 变量和宿主环境自动检测，兼容多种 AI 编程工具：

| 宿主 | 检测条件 | SKILL_ROOT | 指令文件 |
|------|----------|------------|----------|
| Claude Code | Task 工具 + .claude/ 目录 | .claude/skills/teamwork | CLAUDE.md |
| Codex CLI | .codex/ 或 .agents/ 目录 | .agents/skills/teamwork | AGENTS.md |
| Gemini CLI | .gemini/ 目录 | .gemini/skills/teamwork | GEMINI.md |
| 通用 | 均不匹配 | 从 SKILL.md 推断 | AGENTS.md |

执行方式也会根据宿主自适应：Claude Code 使用 Task 工具 dispatch Subagent，Codex CLI 使用 agent toml spawn，不支持 Subagent 的宿主降级为主对话执行（PMO 按 AI Plan 模式决定）。

## 协作模型

### 单人模式（默认）
一个用户 + 一个 Claude 会话操作整个项目。`.teamwork_localconfig.md` 的 scope 用于聚焦关注范围，而非并发控制。

### 多人模式（实验性）
多个用户各自使用独立 Claude 会话操作不同子项目。

约束条件：
- 每个子项目同一时刻只能有一个会话在操作
- 不同用户必须负责不同的子项目（scope 不重叠）
- 跨子项目需求由一个用户统一协调
- 不支持同一子项目的并发开发

## 安装

```bash
# 自动检测宿主环境（Claude Code / Codex CLI）
npx skills add okteam99/teamwork

# 或手动安装
bash skills/teamwork/install.sh
```

## 升级

```bash
npx skills update okteam99/teamwork
```

## 使用

```bash
# 启动 Feature 流程
/teamwork 实现用户登录功能

# 启动 Feature Planning
/teamwork 规划电商推荐系统

# 报告 Bug
/teamwork 登录页面在手机端返回 500 错误

# 小改动（敏捷需求：≤5 文件、方案明确）
/teamwork 在用户列表增加导出 CSV 按钮

# 微调（Micro：零逻辑变更，PMO 可直接改）
/teamwork 把首页 logo 换成新的图片

# 查看当前状态 / 继续中断的流程
/teamwork status
/teamwork 继续

# 切换角色
/teamwork pm | designer | qa | rd | pmo

# 退出协作模式
/teamwork exit
```

> 注：Product Lead 由 PMO 自动调度，无需手动切换。流程类型由 PMO 自动识别，无需手动指定。

## 文件结构

```
teamwork/
├── skills/
│   └── teamwork/
│       ├── SKILL.md                  # 主入口：红线、AI Plan 模式、文件索引
│       ├── INIT.md                   # 🔴 每次启动必读（宿主检测 + 项目空间 + 看板）
│       ├── FLOWS.md                  # 流程规范：六种流程的选择与详细执行规则
│       ├── ROLES.md                  # 角色索引（→ roles/*.md）
│       ├── RULES.md                  # 核心规则：暂停、流转、变更、闭环验证
│       ├── REVIEWS.md                # 评审规范（PRD / TC / UI 还原验收）
│       ├── STANDARDS.md              # 编码规范索引
│       ├── STATUS-LINE.md            # 状态行格式 + 用户意图识别 + 阶段对照表
│       ├── TEMPLATES.md              # 文档模板索引
│       ├── CONTEXT-RECOVERY.md       # 新对话/中断恢复机制
│       ├── PRODUCT-OVERVIEW-INTEGRATION.md  # product-overview/ 与 PL 联动规则
│       ├── install.sh                # 一键安装脚本（自动检测宿主环境）
│       │
│       ├── roles/                    # 角色完整定义（按需加载）
│       │   ├── pmo.md
│       │   ├── product-lead.md
│       │   ├── pm.md
│       │   ├── designer.md
│       │   ├── qa.md
│       │   └── rd.md                 # RD + 架构师（方案评审 + Code Review）
│       │
│       ├── rules/                    # 拆分的核心规则
│       │   ├── flow-transitions.md   # 🔴 阶段转移表（校验唯一权威源）
│       │   ├── gate-checks.md        # PMO 预检 + state.json 同步规则
│       │   └── naming.md             # 命名规范
│       │
│       ├── stages/                   # Stage 规范（三契约结构）
│       │   ├── plan-stage.md         # PM PRD + PL-PM 讨论 + 多角色技术评审
│       │   ├── ui-design-stage.md    # Feature UI + 全景增量同步（v7.3.4 合并）
│       │   ├── panorama-design-stage.md  # 全景重建模式（仅 Feature Planning 使用）
│       │   ├── blueprint-stage.md    # QA TC + RD TECH + 架构师方案评审
│       │   ├── blueprint-lite-stage.md  # 敏捷需求专用轻量蓝图
│       │   ├── dev-stage.md          # RD TDD 开发 + 单测 + worktree 集成
│       │   ├── review-stage.md       # 三视角独立审查（架构师 / QA / Codex）
│       │   ├── test-stage.md         # 环境准备 + 集成测试 + API E2E 脚本化
│       │   └── browser-e2e-stage.md  # 浏览器 E2E（半自动，可选）
│       │
│       ├── agents/                   # 任务单元 + 协议
│       │   ├── README.md             # 执行方式参考 + Dispatch 协议 §四 + 主对话产物协议 §六
│       │   ├── rd-develop.md
│       │   ├── arch-code-review.md
│       │   ├── qa-code-review.md
│       │   ├── integration-test.md
│       │   └── api-e2e.md            # API E2E 脚本化规范
│       │
│       ├── codex-agents/             # Codex CLI 自定义 agent 定义
│       │   ├── README.md
│       │   ├── rd-developer.toml / reviewer.toml / tester.toml
│       │   ├── planner.toml / designer.toml / e2e-runner.toml
│       │   └── hooks.json
│       │
│       ├── standards/                # 按技术栈拆分的开发规范
│       │   ├── common.md             # 通用：TDD / 架构 / 自查 / WARN 日志
│       │   ├── backend.md            # 后端：API、日志、数据库迁移
│       │   └── frontend.md           # 前端：测试分层、E2E、组件测试
│       │
│       └── templates/                # 文档模板
│           ├── prd.md                # 含 YAML frontmatter acceptance_criteria[]
│           ├── tc.md                 # 含 YAML frontmatter tests[].covers_ac
│           ├── tech.md / ui.md
│           ├── architecture.md / project.md / roadmap.md
│           ├── teamwork-space.md / config.md / dependency.md
│           ├── feature-state.json    # Feature 状态机（v7.3.2 替代 status.md）
│           ├── verify-ac.py          # AC↔test 覆盖校验标准实现
│           ├── bug-report.md / knowledge.md / retro.md
│           ├── e2e-registry.md / pl-pm-feedback.md
│           ├── review-log.jsonl / dispatch.md
│           └── README.md
│
├── README.md / README-EN.md
└── .gitignore
```

## Feature 流程概览（v7.3 契约化 + v7.3.4 暂停点压缩）

```
PMO 初步分析（类型识别 + 流程步骤描述 + 跨 Feature 冲突检查）
  ↓
⏸️ 用户确认走什么流程（基于步骤描述，回复数字 1/2/3）
  ↓
🔗 Plan Stage（PM PRD + PL-PM 讨论 + 多视角技术评审）
  ↓
⏸️ 用户确认 PRD（回复数字）
  ↓
🔗 UI Design Stage（如有 UI，v7.3.4 合并全景增量）
  Designer 一次产出：Feature UI + HTML 预览 + 全景增量同步（🟡 谨慎修改全景）
  ↓
⏸️ 用户确认「设计批」（UI + 全景一起审，一个暂停点）
  ↓
🔗 Blueprint Stage（QA TC + RD TECH + 架构师方案评审；AC↔test 绑定）
  ↓
⏸️ 用户确认技术方案
  ↓
📋 PMO L2 预检 → 🔗 Dev Stage（AI Plan 决定主对话/Subagent；TDD + 单测 + 机器校验）
  ↓ 🚀 自动
🔗 Review Stage（架构师 主对话 + QA/Codex Subagent 并行，三份产物结构独立）
  ↓ 🚀 自动
🟡 Test Stage 前置确认（回复数字：1 立即 / 2 延后 / 3 跳过）
  ↓
🔗 Test Stage（环境主对话 + 集成测试 + API E2E 脚本化）
  ↓
Browser E2E（如需，回复数字决定）
  ↓
🔗 PM 验收 + commit + push（v7.3.4 合并暂停点）
  PM 完成验收 → PMO 自动本地 commit（结构化 message）
  ⏸️ 用户回复数字：
    1. ✅ 通过 → 自动 commit + push
    2. ✅ 通过 → 仅本地 commit（用户保留 push 决定）
    3. ❌ 不通过 → 补充信息，回到对应阶段修复
    4. 其他指示
  ↓
PMO 完成报告（交付物 + 流程完整性 + 文档同步 + ⏱️ 耗时统计 + 📦 Commit & Push 状态）
```

典型 Feature 暂停点：**3-5 个**（流程确认 / PRD / 设计批 / 方案 / 验收+commit+push）。

## 敏捷需求流程概览

```
PMO 分析 → 识别为敏捷需求（≤5 文件、无 UI/架构变更、方案明确）→ ⏸️ 用户确认
  ↓
PM → 简化 PRD（核心需求 + 结构化 AC）→ ⏸️ 用户确认
  ↓
🔗 BlueprintLite Stage（QA 简化 TC + RD 实现计划，主对话执行，无评审）
  ↓
🔗 Dev Stage → Review Stage → Test Stage（与 Feature 相同）
  ↓
PM 验收 + commit + push（回复数字 1/2/3/4）→ PMO 完成报告
```

## Micro 流程概览（v7.3 真轻量）

```
PMO 分析 + 准入条件检查 + 流程步骤描述
  ↓
⏸️ 用户确认走 Micro（回复数字 1/2/3/4）
  ↓
PMO 直接改代码（🟢 无需 Subagent、无需 Execution Plan、无需 dispatch）
  ↓
⏸️ 用户验收（手测/目视）
  ↓
PMO 完成报告（含 Micro 事后审计）
```

准入条件：零逻辑变更 + 改动类型在白名单内（资源替换 / 文案 / 样式 / 配置常量 / 注释文档）。

## Feature Planning 流程概览

```
PMO 分析 → 识别为 Feature Planning → 判断范围
  ↓
📁 子项目级：
  PM → 与用户讨论产品方向 → ⏸️ 用户确认
    ↓
  🔗 Panorama Design Stage（全景重建模式，如有 UI）→ ⏸️ 用户确认全景
    ↓
  PM → 更新 PROJECT.md → 拆解 ROADMAP.md（Wave + 依赖 + 并行度）
    ↓
  ⏸️ 用户确认 ROADMAP → 逐个 Feature 进入标准 Feature 流程

🌐 工作区级：
  PM → 讨论整体架构 → 更新 teamwork_space.md → ⏸️ 用户确认
    ↓
  对每个受影响的子项目 → 执行子项目级 Planning
    ↓
  PMO → 收尾更新 teamwork_space.md → ⏸️ 用户最终确认
```

## 产品规划与 Product Lead

Teamwork 内置产品规划体系，由 **Product Lead (PL)** 角色负责维护。当项目需要产品层面的规划和决策时，PMO 会自动调度 PL。

### 产品规划文档

```
product-overview/
├── {项目名}_业务架构与产品规划.md    # 产品定位、业务流程、收入模型、功能规划
├── {项目名}_执行手册.md              # 执行线、里程碑、验收标准
└── {项目名}_Product_Plan.md          # 可选 · 外部产品计划
```

产品规划文档是 Feature Planning 的上游输入，也是变更级联的顶层依据。

### Product Lead 三种工作模式

**引导模式**：项目首次初始化时，如果 `product-overview/` 不存在，PMO 自动切换到 PL 引导模式。PL 通过结构化问答引导用户从零构建产品规划文档（业务架构 → 执行手册 → 项目初始化）。

**讨论模式**：当用户提出产品方向性话题（如调整商业模式、增减业务线），PMO 识别后调度 PL 进入讨论模式。PL 与用户讨论达成共识后，将结论写入 product-overview 文档，并生成 CHG 变更记录。

**执行模式**：当讨论结论需要落地时，PL 产出变更影响评估报告，评估影响范围和级别，用户确认后触发下游级联：

```
Product Lead 评估 → 变更级别判断
  ├── Level 1（功能级）→ 直接进入 Feature Planning
  ├── Level 2（业务模块级）→ 更新 product-overview → 子项目级 Feature Planning
  └── Level 3（方向级）→ 更新 product-overview → 工作区级 Feature Planning
```

### 变更级联与自下而上影响升级

开发过程中如果发现当前 Feature 与上游文档存在矛盾（如 ROADMAP 中已有 Feature 冲突、产品架构需要调整），PM/RD 会触发 **自下而上影响升级**，由 PMO 向上追溯影响层级直到找到需要变更的最高层文档，再由 PL 评估后向下级联。

## 绝对红线（15 条要点，完整见 [SKILL.md](./skills/teamwork/SKILL.md)）

1. **PMO 写操作边界**：非 Micro 流程下影响运行时的改动 → 必须按流程执行；Micro 流程 PMO 可直接改（白名单内零逻辑）；纯文档 PMO 可直接改需标注
2. **六种流程**：Feature / Bug / 问题排查 / Feature Planning / 敏捷需求 / Micro，禁止自创
3. **禁止擅自简化**：每种需求走对应级别完整流程，"简单/小改/纯移植"不构成跳过理由
4. **PMO 统一承接**：所有用户输入由 PMO 先承接
5. **暂停点必须等确认**：包括 Micro 的用户确认和验收
6. **需求类型/使用流程**枚举受限（6 种）
7. **Feature Planning 只产出文档**，禁止产出代码
8. **闭环验证**："完成"必须附实际命令输出
9. **暂停点必须给建议 + 编号化选项**（v7.3.5）：💡 建议 + 📝 理由 + 1/2/3 编号 + 最后项"其他指示"
10. **写操作硬门禁**：PMO 未输出初步分析前禁止任何写操作
11. **非暂停点禁止暂停**：自动流转节点 🚀 禁止插入询问
12. **PMO 预检红线**：dispatch 前必须完成对应级别的预检（L1/L2/L3）
13. **Subagent dispatch 前预检必达**
14. **AI Plan 模式红线**（v7.3）：每个 Stage 开始前必须输出 Execution Plan 3 行核心；Plan 写入 state.json.planned_execution
15. **流程确认红线**（v7.3）：PMO 必须给出流程完整步骤描述，用户基于步骤确认

## 版本历史

- **v7.3.5**：暂停点选项编号化（用户回数字即可）
- **v7.3.4**：暂停点压缩（UI+全景合并、验收+commit+push 合并 3 选 1）
- **v7.3.3**：Stage 耗时度量闭环（duration / variance / retry / user_wait）
- **v7.3.2**：STATUS.md 废弃，state.json 成为 Feature 目录唯一状态文件
- **v7.3.1**：规则对齐与仪式精简（Execution Plan 3 行核心）
- **v7.3**：Stage 三契约化 + AI Plan 模式 + AC↔test 绑定 + 主对话产物协议 + state.json
- **v7.2**：Dispatch 文件协议 + API E2E 脚本化 + Progress 可见性 + Key Context
- **v7.1 及更早**：多角色评审、多子项目模式、变更级联、闭环验证等基础架构

完整变更记录见 [skills/teamwork/docs/CHANGELOG.md](./skills/teamwork/docs/CHANGELOG.md)。

## License

MIT
