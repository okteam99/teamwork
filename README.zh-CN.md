# Teamwork

多角色协作开发框架，为 Claude Code 提供完整的软件开发流程管理能力。

[English](./README.md)

## 概述

Teamwork 通过模拟 **PMO / PM / Designer / QA / RD / 资深架构师** 六种角色，在 Claude Code 中实现结构化的软件开发协作流程。

支持四种流程类型：

- **Feature 流程** — 完整的需求→设计→开发→测试→验收流程
- **Bug 处理流程** — 排查→判断→修复→验证→文档同步
- **问题排查流程** — 定位问题根因并建议后续处理方式
- **Feature Planning 流程** — 从产品目标拆解 Feature Backlog（优先级+依赖关系）

### 核心特性

- **7 个 Subagent 自动化阶段**：PRD 评审、TC 评审、UI 设计、架构师 TECH Review、TDD 开发+自查、架构师 Code Review、集成测试
- **多角色评审机制**：PRD 和 TC 均通过多视角 Subagent 自动评审
- **完整的暂停点控制**：关键决策节点等待用户确认
- **知识库积累**：每个功能完成后自动沉淀知识到 KNOWLEDGE.md
- **TDD 驱动开发**：先写测试再写代码，确保代码质量

## 安装

```bash
npx skills add okteam99/teamwork
```

## 使用

```bash
# 启动协作流程
/teamwork 实现用户登录功能

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
│       ├── SKILL.md              # 主入口 - 流程定义与状态管理
│       ├── ROLES.md              # 角色定义与职责
│       ├── RULES.md              # 核心规则（暂停、流转、Subagent）
│       ├── REVIEWS.md            # 评审流程规范
│       ├── STANDARDS.md          # 编码与文档标准
│       ├── TEMPLATES.md          # 文档模板（PRD/TC/TECH 等）
│       └── agents/               # Subagent 规范
│           ├── README.md             # 通用规范
│           ├── prd-review.md         # PRD 多角色评审
│           ├── tc-review.md          # TC 多角色评审
│           ├── ui-design.md          # Designer UI 设计
│           ├── arch-tech-review.md   # 架构师技术方案 Review
│           ├── rd-develop.md         # RD TDD 开发 + 自查
│           ├── arch-code-review.md   # 架构师 Code Review
│           └── integration-test.md   # QA 集成测试
├── README.md
├── README.zh-CN.md
└── .gitignore
```

## Feature 流程概览

```
PMO 分析 → 识别类型 → 切换角色
  ↓
PM → PRD
  ↓
🤖 PRD 多角色评审（Subagent）
  ↓
⏸️ 用户确认 PRD
  ↓
🤖 Designer → UI 设计（Subagent，如需 UI）
  ↓
⏸️ 用户确认设计
  ↓
QA → TC
  ↓
🤖 TC 多角色评审（Subagent）
  ↓
RD → 技术方案
  ↓
🤖 架构师 → TECH Review（Subagent）
  ↓
⏸️ 用户确认技术方案
  ↓
🤖 RD → TDD 开发 + 自查（Subagent）
  ↓
🤖 架构师 → Code Review（Subagent）
  ↓
Designer → UI 还原验收（如有 UI）
  ↓
QA → 代码审查
  ↓
QA → 集成测试前置检查 → 🤖 集成测试（Subagent）
  ↓
PM → 最终验收
  ↓
PMO → 完成报告 + 知识沉淀
```

## Feature Planning 流程概览

```
PMO 分析 → 识别为 Feature Planning
  ↓
PM → 澄清产品目标
  ↓
PM → 拆解 Feature 清单（P0/P1/P2）+ 依赖关系
  ↓
PM → 输出 BACKLOG.md
  ↓
⏸️ 用户确认 Backlog
  ↓
逐个 Feature 进入标准 Feature 流程
```

## License

MIT
