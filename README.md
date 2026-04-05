# Teamwork

AI Agent 团队协作开发框架 — 8 个专业 AI Agent 组成虚拟开发团队，一个人驱动从产品规划到交付的完整软件研发流程。

[English](./README-EN.md)

## 概述

Teamwork 将 Claude Code 变成一支完整的 AI 开发团队：**PMO / Product Lead / PM / Designer / QA / QA Lead / RD / 架构师** 八个专业 Agent 各司其职，像真实团队一样协作，用户只需提出需求和做关键决策。

支持四种流程类型：

- **Feature 流程** — 完整的需求→设计→开发→测试→验收流程
- **Bug 处理流程** — 排查→判断→修复→验证→文档同步
- **问题排查流程** — 定位问题根因并建议后续处理方式
- **Feature Planning 流程** — 从产品目标拆解 ROADMAP（Wave 执行批次 + 依赖关系 + 并行度）

### 核心特性

- **11 个 Subagent 自动化阶段**：PL-PM 协同讨论、PRD 评审、TC 评审、UI 设计、架构师 TECH Review、TDD 开发+自查、架构师 Code Review、QA 代码审查、集成测试、E2E 端到端验收、QA Lead 质量总结
- **PL-PM Teams 讨论**：PM 输出 PRD 初稿后，PL 与 PM 通过多轮 Agent 交替讨论收敛定稿，再进入评审
- **Product Lead 角色**：三种模式 — 引导模式（从零构建产品规划）、讨论模式（产品方向讨论 + CHG 变更记录）、执行模式（变更级联评估）
- **多角色评审机制**：PRD 和 TC 均通过多视角 Subagent 自动评审
- **产品全景设计**：design/sitemap.md + design/preview/overview.html 作为产品 UI 的 Single Source of Truth
- **变更级联规则**：三级影响评估（L1 功能级 / L2 业务模块级 / L3 方向级）+ 自下而上影响升级
- **多子项目模式**：teamwork_space.md 统筹多个子项目，支持 business / midplatform 两种子项目类型，跨项目需求追踪与依赖管理
- **中台子项目支持**：midplatform 类型子项目自动触发消费方分析、兼容性评审等增强流程
- **Feature 状态追踪**：每个 Feature 目录下的 STATUS.md 作为状态 Single Source of Truth，PMO 每次阶段流转自动更新
- **完整的暂停点控制**：关键决策节点等待用户确认
- **知识库积累**：每个功能完成后自动沉淀知识到 KNOWLEDGE.md
- **TDD 驱动开发**：先写测试再写代码，确保代码质量
- **状态恢复机制**：会话中断后可通过文档状态自动恢复到中断点

## 安装

```bash
npx skills add okteam99/teamwork
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

# 查看当前状态
/teamwork pmo

# 退出协作模式
/teamwork exit
```

## 文件结构

```
teamwork/
├── skills/
│   └── teamwork/
│       ├── SKILL.md              # 主入口 — 流程定义、状态管理、绝对红线
│       ├── ROLES.md              # 角色定义（PMO/PL/PM/Designer/QA/RD/Architect）
│       ├── RULES.md              # 核心规则（暂停、流转、Subagent、变更处理）
│       ├── REVIEWS.md            # 评审流程规范（PRD/TC/UI 验收）
│       ├── STANDARDS.md          # 编码规范索引
│       ├── TEMPLATES.md          # 文档模板（PRD/TC/TECH/ROADMAP 等）
│       ├── agents/               # Subagent 规范
│       │   ├── README.md             # 通用规范
│       │   ├── pl-pm-discuss.md      # PL-PM 协同讨论（Teams 模式）
│       │   ├── prd-review.md         # PRD 多角色评审
│       │   ├── tc-review.md          # TC 多角色评审
│       │   ├── ui-design.md          # Designer UI 设计（增量模式 + 全景重建模式）
│       │   ├── arch-tech-review.md   # 架构师技术方案 Review
│       │   ├── rd-develop.md         # RD TDD 开发 + 自查
│       │   ├── arch-code-review.md   # 架构师 Code Review + 架构文档更新
│       │   ├── qa-code-review.md     # QA 代码审查（读代码 + TC 逐条验证）
│       │   └── integration-test.md   # QA 集成测试
│       └── standards/            # 按技术栈拆分的编码规范
│           ├── common.md             # 通用：TDD 检查清单、架构规范、自查规范
│           ├── backend.md            # 后端：TDD、API、日志、数据库迁移
│           └── frontend.md           # 前端：测试分层、E2E、组件测试
├── README.md                     # 中文文档（默认）
├── README-EN.md                  # 英文文档
└── .gitignore
```

## Feature 流程概览

```
PMO 分析 → 识别类型 → 切换角色
  ↓
PM → PRD 初稿
  ↓
🤖 PL-PM Teams 讨论（Subagent：PL 审查 + PM 回应，多轮收敛）→ PRD 定稿
  ↓
🤖 PRD 多角色评审（Subagent：RD / Designer / QA / PMO 四个视角）
  ↓
⏸️ 用户确认 PRD
  ↓
🤖 Designer → UI 设计（Subagent，如需 UI）+ 同步产品全景设计
  ↓
⏸️ 用户确认设计
  ↓
QA → TC（BDD/Gherkin 格式）
  ↓
🤖 TC 多角色评审（Subagent：PM / RD / Designer 视角）
  ↓
RD → 技术方案
  ↓
🤖 架构师 → TECH Review（Subagent）
  ↓
⏸️ 用户确认技术方案（仅复杂方案）
  ↓
🤖 RD → TDD 开发 + 自查（Subagent）
  ↓
🤖 架构师 → Code Review + 架构文档更新（Subagent）
  ↓
Designer → UI 还原验收（如有 UI，最多 3 轮）
  ↓
🤖 QA → 代码审查（Subagent：读代码 + TC 逐条验证）
  ↓
QA → 集成测试前置检查 → 🤖 集成测试（Subagent）
  ↓
PM → 最终验收
  ↓
PMO → 完成报告（知识库 + 技术债 + Schema/API + PROJECT.md + 全景设计同步）
```

## Feature Planning 流程概览

```
PMO 分析 → 识别为 Feature Planning → 判断范围
  ↓
📁 子项目级：
  PM → 与用户讨论产品方向
    ↓
  🤖 Designer → 全景设计重建（Subagent，有 UI 时）
    ↓
  ⏸️ 用户确认全景设计
    ↓
  PM → 更新 PROJECT.md
    ↓
  PM → 拆解 ROADMAP.md（Wave 执行批次 + 并行度）
    ↓
  ⏸️ 用户确认 ROADMAP
    ↓
  逐个 Feature 进入标准 Feature 流程

🌐 工作区级：
  PM → 与用户讨论整体架构
    ↓
  PM → 更新 teamwork_space.md
    ↓
  ⏸️ 用户确认工作区架构
    ↓
  对每个受影响的子项目 → 执行子项目级 Planning
    ↓
  PMO → 收尾更新 teamwork_space.md
    ↓
  ⏸️ 用户最终确认
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

## License

MIT
