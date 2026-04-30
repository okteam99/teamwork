# teamwork_space.md 模板

> 位置：项目根目录 `teamwork_space.md`
> 🔴 **任何变更（创建/修改/删除）必须暂停等待用户确认！**
>
> 🔴 **本文件是 teamwork_space.md 的唯一格式权威源（v7.3.10+P0-58）**。每个表格紧邻的 quote block 是该表的硬规则；PM/PMO/PL 起草时按本模板硬规则填，不另立约定。
>
> 🔴 **核心简化原则**：teamwork_space.md 是**全景索引**，不是事件日志 / 进度看板 / 评审记录。**任一表格的任一单元格都应 ≤ 1 行**；详情一律外迁到对应文档（changes/{id}.md / Feature 自己的 state.json + PRD / PROJECT.md / ADR）。这能让 teamwork_space.md 永远保持"一眼看懂全景"，避免演化到几百行难以维护。

```markdown
# Teamwork Space

> 本文件是多子项目模式的全景入口，定义子项目结构、依赖关系，并链接到各子项目详情。
> 🔴 本文件的任何变更都需要用户明确确认后才能生效。

---

## 产品规划引用（有 product-overview/ 时）

> teamwork_space.md 的上游输入。状态同步自 product-overview 文档头部的规划状态表。
> 只有 ✅ 已确认 的文档内容才会驱动 teamwork_space.md 的子项目规划。

| 文档 | 路径 | 规划状态 |
|------|------|----------|
| 业务架构与产品规划 | 📎 [\`product-overview/{项目名}_业务架构与产品规划.md\`](product-overview/) | 📝 草稿 / 🔄 讨论中 / ✅ 已确认 |
| 执行手册 | 📎 [\`product-overview/{项目名}_执行手册.md\`](product-overview/) | 📝 草稿 / 🔄 讨论中 / ✅ 已确认 |

> 无 product-overview/ 的项目可省略此章节。
> 规划状态含义：📝 初创未讨论 → 🔄 有活跃议题讨论中 → ✅ 用户确认可作为执行依据

---

## 规划状态

| 字段 | 值 |
|------|---|
| 状态 | ✅ 正常 |
| 当前阶段 | 初始化 / 架构规划中 / 开发中 |
| 最近规划 | - |
| 受影响子项目 | - |

> 状态值：✅ 正常 / 📝 规划中 / ⏸️ 架构待确认 / 🔄 子项目 Planning 中 / ✅ 已完成
> 当前阶段：初始化（仅引用 product-overview）→ 架构规划中（定义子项目）→ 开发中（正常运转）
>
> 🔴 **硬规则（v7.3.10+P0-58）**：每个槽位值 **≤ 1 行**。"最近规划"/"最近更新"只写「日期 + 一句话事件 + 链 changes/{id}.md 或 Feature 路径」；多事件累积时**只保留最近一次**，旧事件移到对应 changes/{id}.md 的「变更日志」段。

---

## 执行线概览（有 product-overview/ 时）

> 执行线是业务价值视角的「要做什么」，从执行手册中提取。
> 执行线不反向绑定具体子项目或 Feature 编号——映射关系由子项目侧维护。

| 执行线 | 使命 | 当前阶段 | 关键里程碑 |
|--------|------|----------|-----------|
| Line 1 · XXX | [从执行手册提取] | Phase 0 | [里程碑摘要] |
| Line 2 · YYY | [从执行手册提取] | Phase 0 | [里程碑摘要] |

> 🔴 执行线表中不出现子项目缩写或 Feature 编号。子项目与执行线的映射关系在下方「子项目清单」中维护。
>
> 🔴 **硬规则（v7.3.10+P0-58）**：「使命」/「关键里程碑」列各 **≤ 1 行**，原文取自执行手册（不复述背景 / 不加事件级补充）。

---

## 项目架构全景

> 初始化时由 PL 阶段 2.5 子项目拆分方案产出，PMO 阶段 3 填入。
> 后续 Workspace Planning 时由 PM 更新。

（Mermaid 子项目拓扑 + 依赖关系图）

---

## 项目目录结构

> PMO 在子项目拆分确认后生成此 tree 图，反映项目根下的物理目录布局。
> 每个目录附职责说明，帮助新成员快速理解项目组织方式。
> 🔴 子项目目录直接放在项目根下，不嵌套 \`packages/\` 等中间目录。

\`\`\`
项目根/
├── teamwork_space.md          # 本文件 — 全景入口（架构图 + 子项目链接 + 跨项目追踪）
├── product-overview/          # 产品规划文档（业务架构、执行手册）— 有 product-overview 时
├── external/                  # 🔴 三方/外部资源文档（接入指南、API 参考、SDK 文档，按服务名分子目录）
│   └── README.md              #   目录说明 + 三方资源总览索引
├── docs/                      # 全局文档（跨子项目共用）
│   ├── ROADMAP.md             #   产品规划 Feature Roadmap
│   ├── KNOWLEDGE.md           #   全局知识库（跨子项目经验沉淀）
│   ├── RESOURCES.md           #   全局资源配置（连接串/Key 等，与 external/ 互补）
│   └── decisions/             #   全局技术/产品决策记录（DEC-xxx）
│
├── {子项目A}/                  # business 子项目 — 负责：{职责}。不负责：{边界}
│   ├── docs/                  #   子项目文档（PROJECT.md + features/ + architecture/）
│   └── src/                   #   子项目源码（内部按技术职能分层）
│
└── {子项目B}/                  # business 子项目 — 负责：{职责}。不负责：{边界}
    ├── docs/
    └── src/
\`\`\`

> 📎 各子项目内部目录结构详见 templates/project.md「目录结构」章节。
> PMO 生成时将 \`{子项目X}\` 替换为实际目录名和职责，与下方「子项目清单」表保持一致。

---

## 子项目清单

> 初始化时由 PMO 阶段 3 从 PL 子项目拆分方案填入。
> 「承接执行线」列维护子项目与执行线的映射关系（执行线侧不反向记录）。

| 缩写 | 名称 | 类型 | 职责范围 | docs_root | 承接执行线 | 技术栈 | 需要 UI | 消费方 | 完成度 | 项目详情 |
|------|------|------|----------|-----------|-----------|--------|---------|--------|--------|----------|
| AUTH | 认证服务 | business | 负责：用户认证、权限管理、Token 签发。不负责：业务权限校验（由各业务子项目自行判断） | auth/docs/features | Line 1 | | 否 | - | 0/0 | [链接] |
| WEB | 前端应用 | business | 负责：终端用户界面、交互逻辑、前端路由。不负责：业务规则计算（调用后端 API） | web/docs/features | Line 1, Line 2 | | 是 | - | 0/0 | [链接] |
| PAY | 支付中台 | midplatform | 负责：支付渠道对接、支付状态管理、对账。不负责：订单业务逻辑（由消费方处理） | pay/docs/features | Line 1 | | 否 | AUTH, WEB | 0/0 | [链接] |

> **类型说明**：\`business\`（默认）= 服务终端用户的业务子项目；\`midplatform\` = 服务内部消费方（其他子项目）的中台子项目。
> **职责范围**：用「负责：XX。不负责：YY」格式明确边界。PMO 路由需求时依据此列判断该派发到哪个子项目。职责有交叉时在此列标注「与 XX 共同负责 YY」。
>
> 🔴 **docs_root（v7.3.10+P0-41 新增，必填，路由权威）**：
> - 子项目的 Feature 文档根目录（相对项目根的路径）
> - 标准格式：`{子项目目录}/docs/features`（如 `auth/docs/features`、`web/docs/features`）
> - PMO 在 triage Step 9 计算 `state.artifact_root = {docs_root}/{Feature 全名}`，所有 Feature 产物必须落在此根下
> - 🔴 **路由权威**：PMO 不允许"沿用历史根 docs/features/"等理由偏离 docs_root 列；老 Feature 在根目录的兼容处理见 [roles/pmo.md § 产物路径权威路由](../roles/pmo.md)
> - 缺失 → triage 阻断（流程违规），用户必须先在 teamwork_space.md 补全
>
> **消费方**：仅 midplatform 类型填写，列出依赖本子项目能力的其他子项目缩写。business 类型填 \`-\`。
> **完成度**：格式 \`已完成数/总数\`，基于该子项目 ROADMAP.md 中的 Feature 统计。PMO 在每个 Feature 完成时同步更新此列。无 ROADMAP 时填 \`0/0\`。
>
> 🔴 **硬规则（v7.3.10+P0-58）**：表内**任一单元格 ≤ 1 行**。"当前状态"等可选列只写「最近一次状态结论 + 链 PROJECT.md / ROADMAP.md」，**不复述 Feature 进度详情 / 不堆事件历史**（详情找子项目自己的 PROJECT.md + ROADMAP.md）。

---

## 跨项目变更与历史（v7.3.10+P0-59 单源化指针段）

> 🟢 **本文件不再维护变更类表格**（v7.3.10+P0-59 简化）。teamwork_space.md 的定位是**项目结构静态描述**，不是事件日志 / 状态看板 / 评审记录。
>
> **变更 / 阻塞 / 历史的单源**：
> - 🔴 **活跃变更**（含状态 / 简介 / 影响子项目 / 子 Feature / 推进顺序 / 联调依赖 / 锁定决策）→ [`product-overview/changes/`](./product-overview/changes/) 目录下每个 `{change_id}.md` 自己的 frontmatter + 「变更日志」段（schema 见 [templates/change-request.md](~/.claude/skills/teamwork/templates/change-request.md)）
> - 🔴 **当前阻塞** → 对应 `changes/{change_id}.md` 的「风险与缓解」段 / 或单 Feature 的 `state.concerns`
> - 🔴 **Feature 级事件**（Stage 流转 / Ship / 评审 finding）→ 各 Feature 自己的 `state.json` + `review-log.jsonl` + git log
> - 🔴 **跨变更回溯查询**：`ls product-overview/changes/*.md` / `grep -l "status: locked" product-overview/changes/*.md`
>
> **Feature → 变更反查**：Feature `state.json` 通过 `change_id` 字段反向引用所属变更。
>
> 🔴 **核心硬约束（保留）**：变更状态 != `locked` 时禁止启动归属本变更的子 Feature，PMO 在 triage 时硬阻塞（保留"用户明确说强制启动"逃生舱）。校验由 PMO 直接读 `changes/{change_id}.md` frontmatter 完成，不再读本文件中的任何索引表。
\`\`\`

---

## teamwork_space.md 生命周期

\`\`\`
teamwork_space.md 随项目演进经历三个阶段：

阶段 1 · 初始化（首次启动 teamwork 时自动创建）
├── 触发：PMO 首次承接需求，发现无 teamwork_space.md
├── 内容：根据有无 product-overview/ 或代码目录自动生成
├── 结果：⏸️ 用户确认后进入阶段 2

阶段 2 · 架构规划（逐个子项目 Planning 或首个 CHG 执行时）
├── 触发：用户确认开始子项目 Planning / 执行 CHG
├── PM 在 Workspace Planning 中更新子项目清单、架构全景、各子项目 ROADMAP
├── 结果：⏸️ 用户确认后进入阶段 3

阶段 3 · 开发期（正常运转）
├── 子项目清单 + 项目架构全景 + 项目目录结构按结构变更同步更新（v7.3.10+P0-59）
├── 变更 / 阻塞 / 事件历史一律落 product-overview/changes/{id}.md 或 Feature state.json，本文件不再维护此类表格
└── 自上而下 / 自下而上双向更新
\`\`\`
