# Teamwork 初始化流程

> 按需加载：仅在首次启动 `/teamwork` 或项目空间未初始化时读取。

## 初始化（首次调用时）

### Step 0: 加载项目空间定义 + 本地知识库

**Step 0-A: 检查 `teamwork_space.md` 文件**：
```
如果 teamwork_space.md 存在：
├── 读取文件内容
├── 加载子项目清单、职责、依赖关系
├── 后续 PMO 分析需求时参考此文件
└── 输出提示：「📦 已加载项目空间定义（X 个子项目）」

如果不存在：
├── 自动扫描项目结构（详见 templates/ 自动生成规则）
├── 扫描结果判断：
│   ├── 发现 ≥2 个子项目 → 生成 teamwork_space.md 草稿 → ⏸️ 必须暂停等用户确认后才能写入
│   ├── 发现 1 个子项目 → 提示用户确认，生成 teamwork_space.md（含该子项目）
│   └── 未发现子项目 → 询问用户定义项目名，生成 teamwork_space.md（作为单个子项目）
└── 🔴 禁止在用户确认前写入 teamwork_space.md！
```

**Step 0-A2: 检查 `.teamwork_localconfig.md`（多人协作配置）**：
```
如果 .teamwork_localconfig.md 存在：
├── 读取当前用户负责的子项目列表
├── scope = all → 用户负责所有子项目
├── scope = 指定子项目列表 → 用户只负责列出的子项目
├── 后续 PMO 分析需求时优先聚焦用户负责的子项目
└── 输出提示：「👤 当前负责模块：[子项目列表] / 全部」

如果不存在或为空：
├── ⏸️ 提示用户选择负责的子项目（可多选，或选择「全部」）
├── 用户选择后生成 .teamwork_localconfig.md
└── 🔴 此文件为本地配置，应加入 .gitignore，不提交到仓库
```

**Step 0-A3: 扫描外部依赖请求（用户负责的子项目）**：
```
🔴 scope = all 时跳过此步骤（自己负责所有模块，不存在跨人依赖）

scope = 指定子项目时，遍历用户负责的子项目，检查 {子项目路径}/docs/DEPENDENCY-REQUESTS.md：
├── 存在且有未解决请求（状态 ≠ ✅ 已完成）：
│   ├── 汇总所有待处理的外部依赖请求
│   ├── 按优先级排序（🔴 阻塞 > 🟡 影响进度 > 🟢 非紧急）
│   └── ⏸️ 提醒用户：
│       「📬 你负责的模块有 N 条外部依赖请求待处理：
│        [请求列表摘要]
│        建议优先处理阻塞级请求。是否先处理依赖请求，还是继续新需求？」
└── 不存在或无待处理请求 → 跳过
```

**Step 0-B: 加载本地知识库（如存在）**：
```
├── 读取全局 docs/KNOWLEDGE.md（如存在）
├── 读取各子项目 {子项目路径}/docs/KNOWLEDGE.md（如存在）
└── 输出提示：「📚 已加载知识库（全局 + X 个子项目）」
```

**Step 0-C: 加载/创建项目总览（PROJECT.md — 业务视角，给老板看）**：
```
遍历 teamwork_space.md 中的子项目清单
├── 对每个子项目检查 {子项目路径}/docs/PROJECT.md：
│   ├── 存在 → 读取并加载为该子项目上下文
│   └── 不存在 → 扫描子项目结构，自动生成基础版本
│       ├── 根据子项目代码推断：功能模块划分（用业务语言描述）
│       ├── 留空待补充：项目简介、核心业务流程、关键业务决策
│       ├── 🔴 不写技术栈、代码分层等技术细节（那些属于 ARCHITECTURE.md）
│       └── 写入 {子项目路径}/docs/PROJECT.md
├── 确保 teamwork_space.md 的子项目清单中包含各 PROJECT.md 链接
├── 对有 UI 的子项目（前端/客户端），检查 {子项目路径}/docs/design/sitemap.md：
│   ├── 存在 → 加载
│   └── 不存在 → 暂不创建（首次 Feature 涉及 UI 设计时由 Designer 创建）
└── 输出提示：「📋 已加载 N 个子项目总览（从 teamwork_space.md 进入全景）」
```

**Step 0-C2: 加载/创建架构文档（ARCHITECTURE.md — 技术视角，给技术团队看）**：
```
遍历 teamwork_space.md 中的子项目清单
├── 对每个子项目检查 {子项目路径}/docs/architecture/ARCHITECTURE.md：
│   ├── 存在 → 读取并加载为该子项目技术上下文
│   └── 不存在 → 扫描子项目代码结构，自动生成基础版本（模板见 templates/architecture.md）
│       ├── 根据代码扫描推断：技术栈（语言、框架、数据库）
│       ├── 根据目录结构推断：分层架构、核心模块
│       ├── 生成架构图（Mermaid）
│       ├── 🔴 与 PROJECT.md 互补：ARCHITECTURE.md 写技术细节，PROJECT.md 写业务概览
│       └── 写入 {子项目路径}/docs/architecture/ARCHITECTURE.md
└── 输出提示：「🏗️ 已加载 N 个子项目架构文档（从 ARCHITECTURE.md 了解技术全景）」

⚠️ 初始化创建的 ARCHITECTURE.md 是基于代码扫描的基础版本：
├── 技术栈概览 → 从 package.json / go.mod / requirements.txt / Cargo.toml 等推断
├── 目录结构 → 从实际目录生成
├── 分层与职责 → 从目录命名推断（如 controllers/ services/ models/）
├── 核心模块说明 → 留空（首次 Code Review 时由架构师填充）
└── 后续由架构师在 Code Review 阶段持续更新和完善
```

**Step 0-C3: 加载/创建数据库 Schema 文档（database-schema.md）**：
```
遍历 teamwork_space.md 中的子项目清单
├── 对每个子项目，检测是否有数据库：
│   ├── 扫描信号（满足任一即判定有数据库）：
│   │   ├── 存在 migrations/ 或 db/migrate/ 目录
│   │   ├── 存在 ORM Model 定义文件（models/ entities/ schema/ 等目录）
│   │   ├── package.json / go.mod / Cargo.toml 等引用了数据库驱动（如 pg, mysql, sqlx, prisma, typeorm, gorm, sqlalchemy）
│   │   └── 存在 docker-compose 中的数据库服务定义
│   │
│   ├── 无数据库 → 跳过
│   └── 有数据库 → 检查 {子项目路径}/docs/architecture/database-schema.md：
│       ├── 存在 → 读取并加载
│       └── 不存在 → 扫描代码自动生成基础版本（模板见 templates/architecture.md）
│           ├── 扫描 ORM Model/Struct 定义 → 提取表名、字段、类型
│           ├── 扫描 migration 文件 → 提取建表语句、索引、约束
│           ├── 生成 ER 关系图（Mermaid erDiagram）
│           ├── 生成 Model/Struct 映射表（文件路径 + ORM 框架）
│           ├── 🔴 以代码为准：migration 文件和 ORM Model 是 schema 的真实来源
│           └── 写入 {子项目路径}/docs/architecture/database-schema.md
│
└── 输出提示：「🗄️ 已加载 N 个子项目数据库 Schema（M 个无数据库已跳过）」

⚠️ 初始化创建的 database-schema.md 是基于代码扫描的基础版本：
├── ER 关系图 → 从 Model 定义的外键/关联关系推断
├── 核心表说明 → 从 migration + Model 字段生成（字段、类型、索引）
├── Model/Struct 映射表 → grep 所有引用该表的 Model/Struct 及文件路径
├── SQL 查询引用点 → 留空（首次 Code Review 时由架构师填充）
└── 后续由架构师在 Code Review 阶段持续更新和完善
```

**Step 0-D: 扫描 Feature STATUS.md（生成 Feature 看板）**：
```
遍历所有 {子项目路径}/docs/features/*/STATUS.md：
├── 存在 → 读取当前阶段、当前角色、最后更新、阻塞状态
├── 不存在但目录有 PRD.md 等文件 → 根据文件存在情况推断阶段，创建 STATUS.md
├── 排除「当前阶段」为「✅ 已完成」的 Feature
├── 汇总为 Feature 看板输出（按最后更新时间降序）
└── 📋 Feature 状态看板
    | Feature | 当前阶段 | 当前角色 | 阻塞状态 | 最后更新 |
    |---------|----------|----------|----------|----------|
    | ... | ... | ... | ... | ... |

有进行中 Feature → 询问用户从哪里继续
无进行中 Feature → 等待新需求
```

**知识参考场景**：
```
├── PM 编写 PRD 时 → 参考「需求澄清」相关知识
├── Designer 设计时 → 参考「用户设计偏好」
├── QA 编写 TC 时 → 参考「测试重点」知识
├── RD 技术方案时 → 参考「技术决策」和「踩坑记录」
└── 所有角色 → 遵守「项目特定规则」
```

### Step 1: 自动注入 CLAUDE.md（实现会话级自动加载）

**检查项目根目录的 `CLAUDE.md` 文件**：
- 如果不存在 → 创建并写入 Teamwork 规则
- 如果存在但无 `<!-- teamwork-rules-v` 版本标记 → 追加 Teamwork 规则
- 如果已有版本标记但版本号 < 当前版本（v5） → 替换整个 `## Teamwork 协作模式` 段落
- 如果版本号 = 当前版本 → 跳过

**写入内容**：
```markdown
<!-- teamwork-rules-v5 -->
## Teamwork 协作模式

本项目使用 Teamwork 多角色协作流程。

### 🔴 流程合规红线（详见 SKILL.md）
1. PMO 不写代码  2. 五种流程  3. 禁止擅自简化  4. PMO 先承接  5. 暂停点必须停
6. 阶段流转必须校验  7. 需求类型五选一  8. 流程五选一  9. 闭环验证  10. 暂停必给建议
📎 完整红线定义见 SKILL.md §红线，此处为速查索引。

### 自动激活条件（满足任一）
- 用户输入 `/teamwork [需求]` 或 `/teamwork 继续`
- 检测到 `docs/features/` 下有进行中的功能（状态非「已完成」）
- 用户回复与当前进行中的功能相关

### 激活后行为
1. 加载 skill 规范（SKILL.md + 按需加载 RULES.md / TEMPLATES 等）
2. 遵循多角色流程（PMO → PL/PM → Designer → QA → RD → Architect）
3. 每次回复末尾包含状态行
4. 直到用户输入 `/teamwork exit` 或功能完成才退出

### ⚠️ 重要提示
上方红线是**硬约束**，即使未加载完整 skill 规范也必须遵守。
**完整的多角色协作规范请通过 `/teamwork` 命令加载**。

### Hooks 自动化
本项目配置了 Claude Code hooks（hooks/hooks.json）：
- **SessionStart**：自动扫描 STATUS.md，恢复进行中 Feature 的上下文
- **PreCompact**：context 压缩前自动提醒保存状态到 STATUS.md
- **PostCompact**：context 压缩后自动注入恢复指令
- **Stop**：🔴 每轮回复后读取 STATUS.md 流转约束段，注入到下一轮上下文

### 新对话恢复
SessionStart hook 会自动检测进行中的 Feature 并注入上下文。
```

### Step 2: 创建基础目录

**创建目录**（teamwork_space.md 已确认后）：
```bash
# 全局目录
mkdir -p docs/decisions

# 各子项目目录（根据 teamwork_space.md 中的路径）
mkdir -p {子项目路径}/docs/features
mkdir -p {子项目路径}/docs/architecture
```

### Step 3: 项目扫描

扫描项目，自动识别：
- 项目类型（Web/Mobile/Server/全栈）
- 技术栈（语言、框架）
- 是否需要 UI
- 现有架构文档
- **子项目结构（如果 Step 0-A 扫描到多子项目）**

### Step 3.5: Codex CLI 环境检测

```
检查 Codex CLI 是否已安装：
├── 方式：检查 `codex --version` 命令是否可用
├── ✅ 命令可用 → codex_cli_available = true
├── ❌ 命令不可用 → codex_cli_available = false
└── 结果记入初始化报告

💡 未安装时建议：
安装 Codex CLI，并确认 `codex --version` 可执行
```

### Step 4: 输出初始化报告

**初始化完成报告**：
```
📋 Teamwork 初始化完成
================================

✅ CLAUDE.md 已更新（自动加载规则已注入）
✅ 基础目录已创建
📦 项目空间：已加载（X 个子项目）
👤 当前负责模块：[子项目列表] / 全部
🏗️ 架构文档：已加载 / 已自动生成基础版本
🗄️ 数据库 Schema：已加载 / 已自动生成 / 无数据库
📚 本地知识库：已加载 / 无历史知识
🤖 Codex CLI：✅ 可用 → QA 代码审查 + 集成测试默认使用 Codex CLI 执行
   / ❌ 未安装 → 遇到默认引擎为 Codex 的阶段时，由用户选择「安装后继续」或「本次改用 Claude」

子项目列表：
| 缩写 | 名称 | 技术栈 | 需要 UI | 我负责 |
|------|------|--------|---------|--------|
| AUTH | auth-service | Go + Gin | 否 | ✅ |
| WEB | web-app | React + TS | 是 | ✅ |
| ADMIN | admin-panel | React + TS | 是 | — |

📬 外部依赖请求（如有）：
├── [🔴 阻塞] WEB 请求你的 AUTH 模块提供 SSO 回调接口
└── [🟢 非紧急] ADMIN 请求你的 AUTH 模块开放角色查询 API

知识库摘要（如有）：
├── 全局：[跨项目经验]
├── AUTH：[子项目经验]
└── WEB：[子项目经验]

请输入需求开始第一个功能。
```

---
