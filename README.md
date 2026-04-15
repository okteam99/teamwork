# Teamwork

你的 AI 开发团队 — 一个 AI 以完整团队的方式工作，通过角色视角切换和 8 阶段质量门禁，一个人驱动从产品规划到交付的完整软件研发流程。

[English](./README-EN.md)

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

### 核心特性

- **Stage 化执行**：流程按 Stage 拆分（Plan / Blueprint / Panorama Design / UI Design / Dev / Review / Test / Browser E2E），PMO 按 stage 规范注入上下文并 dispatch
- **强阶段流转校验**：每次阶段变更必须引用 `rules/flow-transitions.md` 的原文 + 行号，禁止伪造证据
- **PMO 预检与硬门禁**：dispatch 前必须完成 L1/L2/L3 预检；PMO 未输出初步分析前禁止任何写操作
- **Product Lead 三模式**：引导（从零构建产品规划）、讨论（产品方向收敛 + CHG 变更记录）、执行（变更影响评估 + 级联）
- **变更级联规则**：三级影响（L1 功能级 / L2 业务模块级 / L3 方向级）+ 自下而上影响升级
- **多角色评审**：PRD / TC / 技术方案均由 PM、QA、RD、Designer 多视角审查
- **产品全景设计**：`design/sitemap.md` + `design/preview/overview.html` 作为产品 UI 的 Single Source of Truth
- **多子项目模式**：`teamwork_space.md` 统筹多个子项目，支持 business / midplatform 类型，跨项目依赖管理与中台消费方分析
- **Feature 状态追踪**：每个 Feature 目录下 `STATUS.md` 是状态 Single Source of Truth，PMO 每次流转自动更新
- **闭环验证红线**：RD/QA 声称"完成"必须附实际命令输出（测试/构建结果），禁止空口完成
- **暂停点强制**：关键节点 ⏸️ 必须等待用户确认，并且暂停时必须给出建议（💡）和理由（📝）
- **TDD 驱动**：先写测试再写代码，单元测试在 Dev Stage 内必须通过
- **状态恢复机制**：会话中断 / 新对话可通过 `CONTEXT-RECOVERY.md` 自动恢复到中断点

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

# 微调（资源/文案/配置）
/teamwork 把首页 logo 换成新的图片

# 查看当前状态 / 继续中断的流程
/teamwork status
/teamwork 继续

# 切换角色
/teamwork pm | designer | qa | rd | pmo

# 退出协作模式
/teamwork exit
```

> 注：Product Lead 由 PMO 自动调度，无需手动切换。

## 文件结构

```
teamwork/
├── skills/
│   └── teamwork/
│       ├── SKILL.md                  # 主入口：红线、文件索引、快速导航
│       ├── INIT.md                   # 🔴 每次启动必读（项目空间 + CLAUDE.md 校验）
│       ├── FLOWS.md                  # 流程规范：六种流程的选择与详细执行规则
│       ├── ROLES.md                  # 角色索引（→ roles/*.md）
│       ├── RULES.md                  # 核心规则：暂停、流转、变更、闭环验证
│       ├── REVIEWS.md                # 评审规范（PRD / TC / UI 还原验收）
│       ├── STANDARDS.md              # 编码规范索引
│       ├── STATUS-LINE.md            # 状态行格式 + 用户意图识别 + 阶段对照表
│       ├── TEMPLATES.md              # 文档模板索引
│       ├── CONTEXT-RECOVERY.md       # 新对话/中断恢复机制
│       ├── PRODUCT-OVERVIEW-INTEGRATION.md  # product-overview/ 与 PL 联动规则
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
│       │   ├── gate-checks.md        # PMO 预检（L1/L2/L3）
│       │   └── naming.md             # 命名规范
│       │
│       ├── stages/                   # Stage 规范（PMO dispatch 时加载）
│       │   ├── plan-stage.md         # PM/QA 计划 + 用例
│       │   ├── panorama-design-stage.md
│       │   ├── ui-design-stage.md
│       │   ├── blueprint-stage.md    # 技术方案 + 架构师评审
│       │   ├── dev-stage.md          # RD TDD 开发 + 自查
│       │   ├── review-stage.md       # 架构师 CR + Codex Review
│       │   ├── test-stage.md         # QA 代码审查 + 集成测试 + API E2E
│       │   └── browser-e2e-stage.md  # 浏览器 E2E（可选）
│       │
│       ├── agents/                   # 任务单元（被 stage 内部引用）
│       │   ├── README.md             # dispatch 通用约束
│       │   ├── rd-develop.md
│       │   ├── arch-code-review.md
│       │   ├── qa-code-review.md
│       │   ├── integration-test.md
│       │   └── api-e2e.md
│       │
│       ├── standards/                # 按技术栈拆分的开发规范
│       │   ├── common.md             # 通用：TDD / 架构 / 自查
│       │   ├── backend.md            # 后端：API、日志、数据库迁移
│       │   └── frontend.md           # 前端：测试分层、E2E、组件测试
│       │
│       └── templates/                # 文档模板
│           ├── prd.md / tc.md / tech.md / ui.md
│           ├── architecture.md / project.md / roadmap.md
│           ├── teamwork-space.md / config.md / dependency.md
│           ├── status.md / bug-report.md / knowledge.md / retro.md
│           ├── e2e-registry.md / pl-pm-feedback.md
│           └── README.md
│
├── README.md / README-EN.md
└── .gitignore
```

## Feature 流程概览（Stage 化）

```
PMO 分析 → 类型识别 + 跨 Feature 冲突检查 → ⏸️ 用户确认
  ↓
PM → PRD 初稿
  ↓
🤖 PL-PM 协同讨论（多轮收敛）→ PRD 定稿
  ↓
🤖 PRD 技术评审（PM / RD / Designer / QA / PMO 多视角）
  ↓
⏸️ 用户确认 PRD
  ↓
🔗 UI Design Stage（如有 UI）→ 同步产品全景设计
  ↓
⏸️ 用户确认设计
  ↓
🔗 Plan Stage（QA Test Plan + BDD Cases）
  ↓
🤖 TC 技术评审 → 无阻塞自动流转
  ↓
🔗 Blueprint Stage（RD 技术方案 → 架构师方案评审）
  ↓
⏸️ 用户确认技术方案（仅复杂方案）
  ↓
🔗 Dev Stage（RD TDD 开发 + 单元测试 + 自查，附实际测试输出）
  ↓
🔗 Review Stage（架构师 Code Review + Codex Review，并行）
  ↓
🔗 Test Stage（QA 代码审查 + 集成测试 + API E2E，附实际命令输出）
  ↓
🔗 Browser E2E Stage（如有 UI，可选）
  ↓
Designer → UI 还原验收（如有 UI，最多 3 轮）
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
  🔗 Panorama Design Stage（Designer 全景设计重建，有 UI 时）
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

## 设计哲学（绝对红线摘要）

完整红线见 [SKILL.md](./skills/teamwork/SKILL.md)，核心 13 条要点：

1. **PMO 不写代码**：分析/分发/总结，任何文件改动（即使一行）都必须 dispatch RD Subagent
2. **六种流程**：Feature / Bug / 问题排查 / Feature Planning / 敏捷需求 / Micro，禁止自创
3. **禁止擅自简化**：每种需求走对应级别的完整流程，「简单/小改/纯移植」不构成跳过理由
4. **PMO 统一承接**：所有用户输入由 PMO 先承接
5. **暂停点必须等确认**：包括 Micro 的用户确认和验收
6. **闭环验证**："完成"必须附实际命令输出
7. **暂停点必须给建议**：💡 建议 + 📝 理由，禁止只抛问题
8. **写操作硬门禁**：PMO 未输出初步分析前禁止任何 Edit/Write/Bash 写操作
9. **非暂停点禁止暂停**：自动流转节点 🚀 禁止插入询问，PMO 不得自创暂停点
10. **PMO 预检红线**：dispatch 前必须完成对应级别的预检（L1/L2/L3）

## License

MIT
