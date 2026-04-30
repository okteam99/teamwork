# Teamwork

AI 以完整团队的方式工作，通过**角色视角切换 + 契约化 Stage + 机读状态机**，驱动从产品规划到交付的完整软件研发流程。

[English](./README-EN.md) · Version: **v7.3.10+P0-60**

---

## 设计前提

软件工程包含多个专业方向的并行关注点：需求完整性、架构合理性、测试覆盖、实现质量、用户体验，各自有自己的盲区。一个人同时覆盖 PM / 架构师 / QA / RD / Designer 五个专业视角时，视角之间会互相遮蔽——PM 的"用户想要"会盖住 QA 的"边界情况"，架构师的"优雅"会盖住 RD 的"交付期"。结果常见的有：需求漏项、架构飘移、测试覆盖不全、验收靠感觉。

Teamwork 按专业方向分配角色：PM→需求完整性 / 架构师→技术合理性 / QA→测试覆盖 / RD→实现质量 / Designer→用户体验，PMO 负责流程编排和信息流转。每份产出物从对应的专业角度被检验。

你只需提出需求和在关键节点做决策。兼容 Claude Code / Codex CLI / Gemini CLI 等 AI 编程工具。

### 多角色切换的工作机制

- **创建-批评循环**：PM 写 PRD → PL 从业务方向批评 → PM 修订，单角色单轮产出会跳过被自身视角遮蔽的盲区
- **注意力重分配**：切换角色 = 切换 checklist = 激活不同评价维度
- **强制重读**：角色切换迫使 AI 带着新问题重读同一份文档，发现的问题量级高于"再想想"

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
```

### 你要做什么 vs AI 要做什么

| 阶段 | 你做的事 | AI 做的事 |
|------|----------|-----------|
| 起点 | 给一句话需求 | PMO 初步分析 + 识别流程类型 + 给完整步骤描述 |
| 确认流程 | 回复数字 1/2/3 确认流程 | — |
| PRD | 对关键问题给答复（通常 3-5 个） | PM 起草 PRD + PL 从业务方向批评 |
| 确认 PRD | 回复数字 | — |
| 设计 | 审一眼 UI + 全景 | Designer 产出 UI + 同步全景 |
| 技术方案 | 审一眼方案 | RD 起草 TECH + QA 起草 TC + 架构师评审 |
| 开发 | 等 | RD 按 TDD 实现 + 单测 + 机器校验 |
| 审查 | 等 | 架构师 + QA + Codex 三视角独立 Review |
| 测试 | 启应用（如需） | 集成测试 + API E2E 脚本化 |
| 验收 | PM 角度验收 + 决定 push 方式 | PMO 整理交付报告 + 自动 commit |

典型 Feature 暂停点数量：**3-5 个**。

---

## 六种流程 — 该走哪条

| 流程 | 适用场景 | 产出 | 默认暂停点 |
|------|----------|------|-----------|
| **Feature** | 完整功能开发 | 代码 + 文档 + 测试 | 3-5 |
| **敏捷需求** | ≤5 文件 + 方案明确 + 无 UI/架构变更 | 代码 + 简化文档 + 测试 | 2-3 |
| **Micro** | 零逻辑变更（文案/样式/资源/配置常量/注释文档） | 代码（直改） | 2（确认 + 验收） |
| **Bug 处理** | 线上/本地缺陷 | 修复 + BUG 报告 + 回归测试 | 3-4 |
| **问题排查** | 不确定问题出在哪，需先定位 | 定位报告（不产出代码） | 1-2 |
| **Feature Planning** | 从产品目标拆 ROADMAP | PROJECT.md + ROADMAP.md + product-overview | 3-5 |

流程类型由 PMO 在初步分析时自动识别，你只负责在暂停点确认。

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

暂停点选项都是编号化的（💡 推荐项标第一，最后一项始终是「其他指示」），**回复一个数字即可**，不用打字。支持多决策点组合（如 `1A 2B`，v7.3.6+）。

### 角色体系（简介）

- **PMO**（流程编排）：承接用户输入 → 识别流程 → 调度角色 → 状态机维护 → 预检与暂停点
- **Product Lead (PL)**：产品方向。引导模式（从零构建 product-overview）/ 讨论模式（业务话题）/ 执行模式（变更级联）
- **PM**：PRD + 结构化 AC + 最终验收
- **Designer**：UI 还原 + 全景（sitemap + preview）
- **架构师（主对话）**：技术方案评审 + Code Review，保留项目架构累积上下文
- **QA**：TC（AC↔test 绑定） + 集成测试 + Code Review
- **RD**：TDD 实现 + 单测 + worktree 集成

> PL 由 PMO 自动调度，不用手动切换。

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

默认 OFF（v7.3.10+P0-9 决策）。开启后（在 `.teamwork_localconfig.md` 配置）Goal-Plan Stage 入口为 Feature 创建隔离的 worktree，Dev Stage 在 worktree 内开发，Ship Stage 合并回主分支。适合多个 Feature 并行开发 + 主分支保持稳定的场景。

### 产品规划体系（可选）

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

### Ship Stage MR 模式（v7.3.10+P0-15）

PM 验收通过 → PMO 自动本地 commit（结构化 message 含 AC 覆盖 / Review 状态 / 耗时摘要）→ ⏸️ 用户回复数字：

1. ✅ push（自动）
2. ✅ 开 MR / PR（自动生成描述）
3. ✅ 仅本地 commit（用户保留 push 决定）
4. ❌ 不通过，修复

PMO **禁止自动 push**，保留用户对远程推送的完全控制。

### 状态恢复机制

`{Feature}/state.json` 是流转状态的**单一权威**（v7.3.2 替代 STATUS.md）。新对话 / compact / 会话退出重开，读 `state.json` 即可恢复，不依赖对话记忆。

### 闭环验证

RD/QA 声称"完成"必须附实际命令输出（测试/构建结果）；PMO 完成报告必须引用实际数据；禁止空口完成。所有降级路径（Subagent 失败、Codex 不可用、worktree 不可用）必须输出结构化 WARN 日志，静默降级视为违反闭环验证红线。

### Prompt Cache 友好（v7.3.10+P0-23）

按 4 层模型组织文档（L0 框架 / L1 项目 / L2 Feature / L3 动态），稳定层和动态层严格分离，Stage 入口 Read 顺序固定，state.json 访问次数受限，减少 AI 在跨 Stage / 跨 Feature 时的重复思考——同样的 Feature 工作流，下一次推进的成本和延迟都明显更低（典型 Feature 场景 ≈ ↓60-70%）。

### 绝对红线（15 条）

完整红线清单见 [SKILL.md](./skills/teamwork/SKILL.md) 开头。README 不重复列，避免双源维护。核心思路：**PMO 写操作边界 / 流程不可跳过 / 暂停点必达 / 闭环验证 / Execution Plan / Preflight 必达**。

---

## 文档导航

| 文件 | 作用 |
|------|------|
| [SKILL.md](./skills/teamwork/SKILL.md) | 主入口：15 条红线、AI Plan 模式、文件索引 |
| [INIT.md](./skills/teamwork/INIT.md) | 每次启动必读：宿主检测、项目空间、看板 |
| [FLOWS.md](./skills/teamwork/FLOWS.md) | 六种流程的选择与详细执行规则 |
| [ROLES.md](./skills/teamwork/ROLES.md) | 角色索引（→ roles/*.md） |
| [RULES.md](./skills/teamwork/RULES.md) | 核心规则：暂停 / 流转 / 变更 / 闭环验证 |
| [REVIEWS.md](./skills/teamwork/REVIEWS.md) | 评审规范（PRD / TC / UI 还原验收） |
| [STANDARDS.md](./skills/teamwork/STANDARDS.md) | 编码规范索引（含 prompt-cache.md） |
| [STATUS-LINE.md](./skills/teamwork/STATUS-LINE.md) | 状态行格式 + 意图识别 |
| [TEMPLATES.md](./skills/teamwork/TEMPLATES.md) | 文档模板索引 |
| [CONTEXT-RECOVERY.md](./skills/teamwork/CONTEXT-RECOVERY.md) | 新对话 / 中断恢复机制 |
| [docs/CHANGELOG.md](./skills/teamwork/docs/CHANGELOG.md) | 完整版本变更记录 |

详细目录结构见 [skills/teamwork/](./skills/teamwork/)。

---

## 版本历史

**v7.3.10 + P0 系列**（当前 P0-60，累计 60+ 补丁，仅列里程碑）：
- **P0-60** triage Step 8 卡片式输出（必含 5 段 / 必砍 7 段 / 实战输出 -74%）
- **P0-58~59** teamwork_space.md 单源化（变更类 3 张表全砍 → changes/{id}.md 是变更唯一权威源）
- **P0-54** 主对话输出 Tier 1/2/3 规范单源（决策呈现 vs 履职报告 · standards/output-tiers.md）
- **P0-53** Plan Stage → Goal-Plan Stage 改名（与 Blueprint 对仗 · 避免 PDCA 泛 plan 混淆）
- **P0-49** 双对齐暂停（triage 意图理解 + 流程承诺一次确认）
- **P0-48** 框架元规则（加 1 删 1 / "重新触发回来"标尺 / 防累积膨胀）
- **P0-44** Goal-Plan Stage 5 子步骤（PM 起草 → PL-PM 讨论 → 多角色并行评审 → PM 回应 → 最终确认）
- **P0-38** Stage 入口实例化（triage 仅给骨架 + execution_hints / 具体决策延迟到各 Stage 入口）
- **P0-33** 跨子项目变更管理（changes/{change_id}.md 模板 + status=locked 才能启动子 Feature）
- **P0-26** triage Stage 前置（流程编排独立 Stage / 6 流程类型分诊 / KNOWLEDGE/ADR 扫描）
- **P0-23** Prompt Cache 友好改造（动态内容后置 + 入口 Read 顺序固定 + state.json ≤5 次/Stage）
- **P0-22** KNOWLEDGE.md 3 类收敛（Gotcha / Convention / Preference 硬触发）
- **P0-21** 混合 ADR 体系（3 问触发器 + PMO 索引扫描）
- **P0-20** 红线 #1 重构（职责正交化 + Micro 升格为独立流程）
- **P0-15** Ship Stage MR 模式重构（push / MR / 仅本地 3 选 1）
- **P0-11** ⚡ auto 模式（一次性总开关 · 非关键暂停点自动流转）
- **P0-9** worktree 默认 OFF
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
