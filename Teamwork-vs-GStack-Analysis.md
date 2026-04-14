# Teamwork vs GStack — AI Agent 团队协作框架深度对比分析

> 2026-04-13 | Teamwork Skill × GStack (garrytan/gstack)

---

## 1. 执行摘要

GStack 和 Teamwork 是两种截然不同的 AI Agent 开发框架。GStack 是 Y Combinator CEO Garry Tan 开源的 Claude Code 技能包（66K+ stars），把 23 个专项工具封装成独立的 slash command，面向单人开发者的快速迭代场景。Teamwork 是多角色协作框架，8 个专业角色组成流水线，面向复杂项目的全生命周期管理。

本报告从架构设计、流程控制、角色系统、质量门禁、安全机制、上下文管理等 12 个维度进行深度对比，并提出 8 项可落地的借鉴改进。

---

## 2. 定位与设计哲学

### 2.1 核心定位差异

| 维度 | GStack | Teamwork |
|------|--------|----------|
| 作者 | Garry Tan (YC CEO) | 团队内部 |
| 目标用户 | 单人开发者 / 创始人 | 团队协作项目 |
| 核心理念 | "钢铁侠战甲"——AI 增强个人 | "虚拟团队"——多角色协作流水线 |
| 设计范式 | 技能包模式（独立 skill） | 流程驱动模式（角色 + 阶段链） |
| 平台支持 | Claude Code / Codex / Gemini 等 7 种 | Claude Code |
| 文件规模 | ~23 个独立 SKILL.md | 48 个 .md 文件，~50K 词 |

### 2.2 设计哲学对比

**GStack 三大原则：**

- **Boil the Lake（做完整的事）**：100% 测试覆盖率、全部边界情况、完整错误路径。AI 让完整性的成本趋近于零——90% 到 100% 之间的 70 行 delta，用 AI 只需几秒。
- **Search Before Building（先搜索再构建）**：三层知识搜索——Layer 1 经典方案 → Layer 2 流行方案 → Layer 3 第一性原理。发现传统做法有误时记录"eureka moment"。
- **Iron Man Suit（钢铁侠模式）**：AI 生成，人类验证。即使 AI 有信心也不跳过验证。生成-验证循环。

**Teamwork 三大原则：**

- **流程即法律**：11 条不可违反的绝对红线。无论需求多简单，都必须走完整流程。"需求简单"不构成简化理由。
- **闭环验证**：每个阶段完成后 PMO 必须介入，输出摘要，判断是否继续。RD/QA 声称"已完成"必须附带实际命令输出。
- **暂停点强制等待**：27 类暂停条件，必须用户确认。模糊确认（≤5 字）触发复述规则。

---

## 3. 架构对比

### 3.1 整体架构

| 维度 | GStack | Teamwork |
|------|--------|----------|
| 组织方式 | 每个 skill 一个目录 + SKILL.md | 分层结构：核心文件 + agents/ + rules/ + templates/ + standards/ |
| 入口点 | 多入口（/qa, /ship, /review...） | 单入口（/teamwork） |
| 路由机制 | CLAUDE.md 自然语言匹配 → 自动激活 skill | PMO 初步分析 → 流程类型判断 → 角色调度 |
| 状态管理 | 跨会话持久化（~/.gstack/） | 文档驱动（STATUS.md + teamwork_space.md） |
| 执行引擎 | 单线程（主会话内） | Subagent 架构（PMO 主导，角色 Subagent 执行） |
| 浏览器能力 | Playwright daemon，100-200ms/命令 | 依赖外部 Browser E2E |
| 配置成本 | ~15 行路由规则写入 CLAUDE.md | 48 个文件的完整框架 |

### 3.2 技能路由 vs 角色调度

**GStack：意图 → 技能**

用户说"why is this broken"就自动激活 /investigate，说"ship it"就激活 /ship。每个 skill 内部封装了完整的人设 + 工具 + 约束，独立自管。路由规则只有 ~15 行，写在 CLAUDE.md 里。skill 之间无状态依赖。

```
用户意图 → CLAUDE.md 关键词匹配 → 激活对应 skill → skill 内部自管理
```

**Teamwork：需求 → 流程 → 角色**

两层路由。第一层：PMO 分析需求类型（Feature / Bug / 问题排查 / Feature Planning / 敏捷需求）。第二层：按流程定义的阶段链自动调度角色。PMO 是中央调度器，掌控所有流转。

```
用户需求 → PMO 初步分析 → 流程类型判断 → 阶段链 → 按阶段调度 Subagent
```

**优劣分析：**

- **GStack 优势**：上手快、灵活、低认知负担。用户不需要理解流程，说自然语言就行。
- **GStack 劣势**：无法保证跨 skill 的状态一致性。/review 和 /qa 之间没有强制的执行顺序。
- **Teamwork 优势**：全流程可追溯，每个阶段的输入/输出严格定义，不会漏步骤。
- **Teamwork 劣势**：学习曲线陡。用户必须理解流程类型、角色分工、暂停点等概念。

---

## 4. 角色系统对比

### 4.1 角色覆盖范围

| 职能 | GStack | Teamwork |
|------|--------|----------|
| 产品规划 | /office-hours (CEO 视角) | Product Lead + PM |
| 架构设计 | /plan-eng-review (Eng Manager) | 架构师 (Tech Review + Code Review) |
| 代码开发 | 主会话直接写 | RD Subagent (TDD + 自查) |
| 代码审查 | /review (偏执狂 Staff Engineer) | 架构师 Code Review + QA 代码审查 |
| 测试 | /qa (浏览器自动化) | QA (Plan + Case + 集成测试 + E2E) |
| UI 设计 | /design-review + /design-consultation | Designer (UI 设计 + HTML 预览稿) |
| **发版** | **/ship (Release Engineer)** | **❌ 无对应角色** |
| 调试 | /investigate (自动冻结模块) | RD Bug 排查 + PMO 判断 |
| **复盘** | **/retro (团队周复盘)** | **❌ 无对应角色** |
| **安全审计** | **/cso (OWASP + STRIDE)** | **❌ 无对应角色** |
| 文档更新 | /document-release | PM 文档同步 (仅 Bug 流程) |
| **项目管理** | **❌ 无对应角色** | **PMO (全流程调度)** |
| **质量总结** | **❌ 无对应角色** | **QA Lead (质量总结)** |

### 4.2 角色深度分析

**GStack 的角色特点：**

- **人设鲜明**：每个 skill 有极其明确的人设。/review 是"偏执狂的 Staff Engineer"，专找 race condition、N+1 查询、信任边界违规。/office-hours 是 YC CEO 风格的产品审计，问 6 个刁钻问题。
- **发现分类明确**：/review 将发现分为 VALID & ACTIONABLE / VALID BUT ALREADY FIXED / FALSE POSITIVE / SUPPRESSED 四类，减少噪音。
- **对抗性思维**：强调"影子路径"（shadow path）——每个数据流必须追踪 4 条路径：happy path + nil 输入 + 空输入 + 上游错误 + 过期状态。

**Teamwork 的角色特点：**

- **职责边界清晰**：PMO 只做分析/分发/总结，禁止写代码。RD 不做流程判断。每个角色有严格的"可做/不可做"边界。
- **评审交叉**：PRD 评审由 RD + Designer + QA + PMO 四角色交叉评审，每个角色有明确的评审维度。TC 评审由 PM + RD + Designer 三角色评审。
- **Subagent 隔离**：每个角色在独立 Subagent 中执行，只加载自己需要的文件，上下文干净。

---

## 5. 质量门禁对比

### 5.1 测试策略

| 维度 | GStack | Teamwork |
|------|--------|----------|
| 测试理念 | 100% 覆盖率目标，"Boil the Lake" | 测试先行 (TDD)，后端 >80% 前端 >70% |
| 测试流程 | /qa 读 git diff → 识别影响页面 → 开浏览器测试 | QA Plan → Write Cases (BDD) → 集成测试 → API E2E → Browser E2E |
| 覆盖率门禁 | 发版时强制检查，低于标准需 override（最多 2 次） | RD 自查时检查，但非硬门禁 |
| 回归测试 | 每个 bug fix 自动生成回归测试 | QA 补充用例，但非自动化 |
| 浏览器测试 | Playwright daemon，100-200ms/命令，持久化会话 | 依赖外部 Browser E2E |

### 5.2 代码审查

| 维度 | GStack | Teamwork |
|------|--------|----------|
| 审查风格 | 对抗性"赏金猎人"模式 | 多角色交叉评审 |
| 审查维度 | Race condition / N+1 / 信任边界 / 安全漏洞 / 影子路径 | 架构合理性 / 规范遵守 / 性能 / 安全 / 验收标准覆盖 |
| 发现分类 | 4 类（VALID / FIXED / FALSE POSITIVE / SUPPRESSED） | 2 类（阻塞项 vs 建议项） |
| 安全审计 | /cso 专项 skill (OWASP Top 10 + STRIDE) | RD 自查的安全检查维度 |

### 5.3 发版流程

GStack 的 /ship 是一个完整的发版工程师：同步 main → 跑测试 → 覆盖率审计 → 更新 VERSION + CHANGELOG → 提交 → 推送 → 创建 PR。6 个工具调用完成。覆盖率低于标准时提供选项：A) 生成缺失测试（推荐）B) Override（最多 2 次，标注在 PR body 中）。

Teamwork 没有对应的发版角色。流程结束于 PM 验收，之后的 git 操作、CI/CD、PR 创建不在框架范围内。

---

## 6. 安全机制对比

| 机制 | GStack | Teamwork |
|------|--------|----------|
| 模块冻结 | /freeze 锁定编辑范围；/investigate 自动冻结 | 无对应机制（仅 Subagent prompt 口头警告） |
| 危险命令拦截 | /careful 拦截 rm -rf、DROP TABLE、force-push | 无对应机制 |
| 写操作控制 | 无全局写门禁 | 红线 #11：PMO 未输出初步分析前禁止写操作 |
| 流程强制 | 无强制顺序，用户自决定 | Pre-flight Check + 流转表强制校验 |
| 暂停点 | 无强制暂停 | 27 类暂停条件，必须用户确认 |
| 模糊确认防护 | 无 | ≤5 字回复触发复述规则 |
| 编辑范围限制 | /freeze 可手动限定目录 | Subagent 输入时指定子项目路径 |
| 综合安全模式 | /guard = /careful + /freeze | 红线 + Pre-flight Check + 暂停点 |

**核心差异**：GStack 的安全是"工具型"的——提供专项工具（/freeze, /careful, /guard）让用户按需启用。Teamwork 的安全是"流程型"的——安全规则嵌入在流程每个环节，不依赖用户主动启用。

---

## 7. 上下文管理对比

| 维度 | GStack | Teamwork |
|------|--------|----------|
| 跨会话持久化 | ~/.gstack/ 目录 + 算法 | STATUS.md + teamwork_space.md 文档 |
| 恢复机制 | /checkpoint 保存 + 恢复 | CONTEXT-RECOVERY.md 决策树 + Feature 看板 |
| 学习积累 | learnings.jsonl 持久化 | KNOWLEDGE.md 项目知识库 |
| 会话状态 | 浏览器状态持久化（cookies/tabs） | Compact 恢复快速路径 |
| 遗忘风险 | 低（skill 独立，上下文小） | 中（长流程多轮累积，但 Subagent 缓解） |
| 遥测分析 | ~/.gstack/analytics/skill-usage.jsonl | 无 |

---

## 8. 综合评分

以下评分基于各自目标场景的实现完整度，满分 5 星。

| 维度 | GStack | Teamwork | 说明 |
|------|--------|----------|------|
| 上手难度 | ★★★★☆ | ★★☆☆☆ | GStack 15 行路由 vs Teamwork 48 文件体系 |
| 流程完整性 | ★★★☆☆ | ★★★★★ | Teamwork 每个阶段都有明确的输入/输出/校验 |
| 角色覆盖广度 | ★★★★★ | ★★★★☆ | GStack 有 ship/retro/cso，Teamwork 缺少 |
| 质量门禁强度 | ★★★☆☆ | ★★★★☆ | Teamwork 暂停点 + 红线更严格 |
| 安全防护 | ★★★★☆ | ★★★★☆ | GStack 工具型，Teamwork 流程型，各有侧重 |
| 浏览器能力 | ★★★★★ | ★★☆☆☆ | GStack 核心竞争力 |
| 上下文管理 | ★★★★☆ | ★★★★☆ | 各有所长，GStack 跨会话，Teamwork 文档驱动 |
| 可扩展性 | ★★★★★ | ★★★☆☆ | GStack 加个目录就行，Teamwork 需改多文件 |
| 复杂项目适用性 | ★★☆☆☆ | ★★★★★ | Teamwork 的多子项目/跨项目能力远超 GStack |
| Token 性价比 | ★★★★★ | ★★★☆☆ | GStack skill 独立→用完释放；Teamwork 全流程耗调 |
| 团队协作 | ★★☆☆☆ | ★★★★★ | Teamwork 专为多角色协作设计 |
| 开发标准化 | ★★★☆☆ | ★★★★★ | Teamwork 有 standards/ 完整开发规范 |

---

## 9. 可借鉴的具体改进

### 改进 1：危险命令拦截（🔴 紧急）

**来源**：GStack 的 /careful 命令拦截

**问题**：RD Subagent 可能执行 rm -rf、DROP TABLE、force-push 等破坏性命令，当前没有拦截机制。

**方案**：在 agents/README.md 通用约束中增加"危险操作红线"：禁止 Subagent 执行 rm -rf、force-push、DROP/TRUNCATE 等破坏性命令。发现这类需求时上报 PMO，由用户决定。

**优先级**：★★★★★ 紧急

---

### 改进 2：模块冻结机制（⭐ 高）

**来源**：GStack 的 /freeze + /investigate auto-freeze

**问题**：RD Subagent 开发时可能修改子项目外的文件，导致回归问题。当前只在 Subagent prompt 中口头警告，无硬约束。

**方案**：在 agents/README.md 的 Subagent 启动规范中增加"编辑范围红线"——PMO 启动 Subagent 时注入允许编辑的目录白名单，Subagent 禁止写入白名单之外的文件。

**优先级**：★★★★☆ 高

---

### 改进 3：影子路径检查（⭐ 高）

**来源**：GStack /review 的对抗性思维

**问题**：架构师 Code Review 和 QA 代码审查缺少影子路径检查维度。可能遗漏 nil 输入、空输入、上游错误、过期状态等边界情况。

**方案**：在 agents/arch-code-review.md 和 agents/qa-code-review.md 中增加"影子路径审查"维度：每个数据流必须追踪 nil/空/上游错误/过期状态四条路径。

**优先级**：★★★★☆ 高

---

### 改进 4：覆盖率硬门禁（⭐ 高）

**来源**：GStack /ship 的覆盖率审计

**问题**：RD 自查时检查覆盖率，但不是硬门禁。覆盖率 60% 也能通过。

**方案**：在 rules/gate-checks.md 中增加覆盖率门禁：后端 < 80% 或前端 < 70% 时 QA 代码审查不通过，需补充测试。可申请 override 但需用户确认。

**优先级**：★★★★☆ 高

---

### 改进 5：发版流程（⭐ 中）

**来源**：GStack 的 /ship 一键发版

**问题**：Teamwork 流程结束于 PM 验收，之后的 git commit / PR / CI 不在框架范围内。

**方案**：在 PM 验收通过后增加可选的"RD 发版"阶段：同步主分支 → 跑测试 → 更新 CHANGELOG → 提交 → 创建 PR。作为流程的可选收尾步骤。

**优先级**：★★★☆☆ 中

---

### 改进 6：复盘机制（⭐ 中）

**来源**：GStack 的 /retro 团队复盘

**问题**：Teamwork 没有复盘阶段。流程中的问题（角色违规、流程卡顿、多次回退）没有系统性记录和分析。

**方案**：PM 验收通过后，增加可选的 PMO 复盘阶段：流程耗时分析、回退次数统计、红线违规记录、改进建议，写入 KNOWLEDGE.md。

**优先级**：★★★☆☆ 中

---

### 改进 7：发现分类体系（⭐ 中）

**来源**：GStack /review 的 4 类发现分类

**问题**：当前架构师 Code Review 和 QA 代码审查只分"通过/不通过"，缺少细粒度分类。

**方案**：引入 4 类分类：✅ VALID & ACTIONABLE / ✅ VALID BUT ALREADY FIXED / ❌ FALSE POSITIVE / ⏸️ SUPPRESSED，减少审查噪音。

**优先级**：★★★☆☆ 中

---

### 改进 8：架构师搜索优先原则（⭐ 中）

**来源**：GStack 的 Search Before Building 三层原则

**问题**：架构师技术方案缺少强制的"先搜索再设计"约束，可能重复造轮子。

**方案**：在 agents/arch-tech-review.md 中增加"方案搜索"必要步骤：技术方案开头必须包含"现有方案调研"段落，记录已评估的方案和选择理由。

**优先级**：★★★☆☆ 中

---

## 10. 结论

GStack 和 Teamwork 是两种互补的设计哲学，而非竞争关系。

**GStack 的核心优势**：上手极快（15 行路由规则）、浏览器自动化是核心竞争力（Playwright daemon 架构精妙）、/ship 一键发版开发体验极佳、安全工具 (/freeze, /careful, /guard) 设计精细、可扩展性强（加个目录就是一个新 skill）。

**Teamwork 的核心优势**：流程完整性无人能及（每个阶段都有明确的输入/输出/校验）、多角色交叉评审保证质量（PRD 四角色评审、TC 三角色评审）、红线 + Pre-flight Check + 暂停点三层安全体系、多子项目/跨项目管理能力远超 GStack、Subagent 架构的上下文隔离设计精巧。

**核心建议**：Teamwork 应该借鉴 GStack 的"工具型安全"和"开发体验"优势，将其融入已有的流程体系。优先落地的 3 项改进：**危险命令拦截（紧急）**、**模块冻结（高）**、**影子路径检查（高）**。这 3 项改动小、收益大，且不破坏现有架构。

---

*Sources: [GStack GitHub](https://github.com/garrytan/gstack) · [GStack ARCHITECTURE.md](https://github.com/garrytan/gstack/blob/main/ARCHITECTURE.md) · [GStack Skills Docs](https://github.com/garrytan/gstack/blob/main/docs/skills.md) · [Augment Code Analysis](https://www.augmentcode.com/learn/garry-tan-gstack-claude-code) · [Codex Blog](https://codex.danielvaughan.com/2026/03/30/gstack-garry-tan-production-skills-toolkit/)*
