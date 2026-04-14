# ARCHITECTURE 模板

> 受众：**技术团队（RD / 架构师）** — 代码级技术细节，技术栈选型、分层架构、模块依赖、接口规范。
> 业务层面的产品概览见 📎 PROJECT.md。

```markdown
# {项目名} 架构文档

> 技术层面的 Single Source of Truth。详细设计按领域拆分到子文档，本文件为全景索引。
> 业务层面的产品概览见 📎 PROJECT.md。

## 最后更新
{日期} - {更新内容简述}

## 一、技术栈概览

| 类别 | 选型 | 选型原因 |
|------|------|----------|
| 语言 | [如 TypeScript] | [原因] |
| 前端框架 | [如 React / Vue / Next.js] | [原因] |
| 后端框架 | [如 Express / NestJS / FastAPI] | [原因] |
| 数据库 | [如 PostgreSQL / MongoDB] | [原因] |
| 缓存 | [如 Redis] | [原因] |
| 基础设施 | [如 Docker / K8s / AWS] | [原因] |
| CI/CD | [如 GitHub Actions] | [原因] |

## 二、架构概述

### 2.1 架构图

\`\`\`mermaid
graph TD
    A[表现层] --> B[业务层]
    B --> C[数据层]
\`\`\`

### 2.2 目录结构
\`\`\`
src/
├── api/          # API 接口层
├── services/     # 业务服务层
├── models/       # 数据模型层
├── utils/        # 工具类
└── config/       # 配置文件
\`\`\`

## 三、分层与职责

### 3.1 表现层（Presentation Layer）
- 职责：
- 包含模块：
- 规范要求：

### 3.2 业务层（Business Layer）
- 职责：
- 包含模块：
- 规范要求：

### 3.3 数据层（Data Layer）
- 职责：
- 包含模块：
- 规范要求：

## 四、核心模块说明

### 4.1 {模块名}
- 职责：
- 对外接口：
- 依赖模块：
- 关键类/文件：
- 模块间依赖关系：

## 五、子文档索引

> 以下子文档包含各领域的详细设计。随项目演进按需创建，初期可不创建。

| 子文档 | 内容 | 创建时机 |
|--------|------|----------|
| 📎 [database-schema.md](./database-schema.md) | 数据库 schema 设计、ER 图、核心表说明、分库分表策略 | 有数据库设计时 |
| 📎 [api-design.md](./api-design.md) | API 总览、版本策略、核心接口清单、认证方案 | 有 API 设计时 |
| 📎 [deployment.md](./deployment.md) | 部署架构、环境拓扑、基础设施、CI/CD pipeline | 需要部署说明时 |

### 子文档管理规则

\`\`\`
📎 子文档由架构师在 Code Review 时按需创建和维护
├── 初始项目可以不创建，所有内容先写在本文件中
├── 当本文件某一领域内容超过 50 行时，拆分到对应子文档
├── 拆分后在本文件「子文档索引」中更新链接
└── 子文档与本文件保持相同的变更记录规范
\`\`\`

## 六、技术设计决策

> 🔴 **决策归属判断**：遇到设计决策时，按以下标准判断写在哪里。
>
> | 决策性质 | 归属 | 示例 |
> |----------|------|------|
> | 跨 Feature 的架构原则/设计标准 | 本表 + 子文档的「设计原则」章节 | JSONB 拍平标准、API 版本策略、缓存策略 |
> | 单个 Feature 的技术选型 | Feature 的 TECH.md「待决策」 | 用 WebSocket 还是 SSE |
> | 单个 Feature 的产品决策 | Feature 的 PRD「待决策项」 | 先做 A 还是先做 B |
> | 业务层面的战略决策 | PROJECT.md「关键业务决策」 | 为什么选这个商业模式 |
> | 开发中踩坑的经验 | KNOWLEDGE.md | 某库在某场景下会崩溃 |
>
> 📎 关键判断：**这个决策在下一个 Feature 中还需要遵守吗？** 是 → architecture；否 → PRD/TECH.md。

| 日期 | 决策 | 原因 | 影响范围 |
|------|------|------|----------|

> 业务层面的决策见 📎 PROJECT.md「关键业务决策」

## 七、变更记录

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|----------|--------|
\`\`\`

---

## database-schema.md 子文档

```markdown
# 数据库 Schema 设计

> 📎 ARCHITECTURE.md 子文档，存放于 \`docs/architecture/\` 目录，由架构师全阶段维护。ARCHITECTURE.md 描述整体架构设计，本文档专注数据库表结构、ORM 映射登记及 SQL 引用点追踪。

## 最后更新
{日期} - {更新内容简述}

## 设计原则

> 🔴 跨 Feature 长期有效的 DB 设计标准写在这里，不要埋在单个 Feature 的 PRD 或 TECH.md 中。
> 各 Feature 的 TECH.md 应引用本节标准（\`📎 详见 database-schema.md 设计原则\`），而非重新定义。

### {原则名称}（示例：JSONB + 拍平列策略）

{原则描述 + 判断标准}

> 📎 每个新增原则需记录到 ARCHITECTURE.md「技术设计决策」表中（决策日期 + 原因 + 影响范围）。

## ER 关系图

\`\`\`mermaid
erDiagram
    USERS ||--o{ ORDERS : places
    ORDERS ||--|{ ORDER_ITEMS : contains
    PRODUCTS ||--o{ ORDER_ITEMS : "ordered in"
\`\`\`

## 核心表说明

### {表名}
- 用途：
- 核心字段：

| 字段 | 类型 | 说明 | 索引 |
|------|------|------|------|

- 关联关系：

**Model/Struct 映射**（🔴 架构师维护，schema 变更时必须同步更新）：

| Model/Struct | 所在子项目 | 文件路径 | ORM 框架 | 说明 |
|-------------|-----------|---------|---------|------|
| PlanRow | BE | src/models/plan.rs | sqlx FromRow | 主 Model |
| PlanRow | ADM | src/repo/plan.rs | sqlx FromRow | 跨子项目引用 |

> 📎 此表记录所有引用该表的 Model/Struct 及其位置。当 migration 变更该表时，RD 必须逐行检查此表中列出的所有 Model 和对应 SQL 查询是否同步更新。
> 架构师 Code Review 时对照此表验证变更完整性。

**SQL 查询引用点**（涉及跨子项目引用时必填）：

| SQL 引用 | 所在子项目 | 文件路径 | 查询类型 | 说明 |
|----------|-----------|---------|---------|------|
| find_active_plan | ADM | src/repo.rs:L42 | SELECT | query_as PlanRow |
| extend_plan | ADM | src/repo.rs:L78 | RETURNING | query_as PlanRow |

> 📎 此表记录引用该表 Struct 的关键 SQL 查询。当表增删列时，这些 SQL 的列列表必须同步修改（缺列 → ORM 反序列化报错 → 500）。

## 分库分表策略（如有）

| 维度 | 策略 | 说明 |
|------|------|------|

## 变更记录

| 日期 | 版本 | 变更内容 | 影响子项目 | 变更人 |
|------|------|----------|-----------|--------|
\`\`\`

---

## api-design.md 子文档（可选）

```markdown
# API 设计总览

> 隶属于 📎 [ARCHITECTURE.md](./ARCHITECTURE.md)，API 层面的详细设计。

## 最后更新
{日期} - {更新内容简述}

## 版本策略

\`\`\`
当前活跃版本：v1
版本路径格式：/api/v{N}/...
\`\`\`

## 版本清单

| 版本 | 状态 | 说明 |
|------|------|------|
| v1 | ✅ 活跃 | 当前版本 |

## 核心接口清单

### {模块名}

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| POST | /api/v1/auth/login | 用户登录 | v1 |

## 认证方案

- 认证方式：
- Token 格式：
- 刷新机制：

## 变更记录

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|----------|--------|
\`\`\`

---

## deployment.md 子文档（可选）

```markdown
# 部署架构

> 隶属于 📎 [ARCHITECTURE.md](./ARCHITECTURE.md)，部署和基础设施的详细设计。

## 最后更新
{日期} - {更新内容简述}

## 环境拓扑

| 环境 | 用途 | 地址 | 说明 |
|------|------|------|------|
| dev | 开发联调 | | |
| staging | 预发布验证 | | |
| production | 线上环境 | | |

## 部署架构图

\`\`\`mermaid
graph LR
    CDN --> LB[负载均衡]
    LB --> APP1[应用节点 1]
    LB --> APP2[应用节点 2]
    APP1 --> DB[(数据库)]
    APP2 --> DB
    APP1 --> CACHE[(缓存)]
    APP2 --> CACHE
\`\`\`

## CI/CD Pipeline

\`\`\`
代码提交 → 自动测试 → 构建镜像 → 部署到 staging → 人工验证 → 部署到 production
\`\`\`

## 变更记录

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|----------|--------|
\`\`\`
