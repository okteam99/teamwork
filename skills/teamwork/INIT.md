# Teamwork 初始化流程

> 🔴 每次 `/teamwork` 启动时必须按顺序执行「启动必做」3 步。
> 「按需加载」由各角色在执行阶段自行加载，不在启动时执行。
> 「首次初始化」仅在 teamwork_space.md 不存在时执行。

---

## 启动必做（每次，按顺序执行）

### Step 1: 检测宿主环境 + 校验指令文件（🔴 最先做）

**Step 1.1: 检测宿主环境并设定 SKILL_ROOT**

```
检测当前 AI 工具：
├── 存在 Task 工具 + .claude/ 目录 → 宿主 = Claude Code
│   └── SKILL_ROOT = .claude/skills/teamwork
│   └── HOST_INSTRUCTION_FILE = CLAUDE.md
├── 存在 .codex/ 目录 或 codex 命令可用 → 宿主 = Codex CLI
│   └── SKILL_ROOT = .agents/skills/teamwork
│   └── HOST_INSTRUCTION_FILE = AGENTS.md
├── 存在 .gemini/ 目录 → 宿主 = Gemini CLI
│   └── SKILL_ROOT = .gemini/skills/teamwork（如支持）
│   └── HOST_INSTRUCTION_FILE = GEMINI.md
└── 均不匹配 → 宿主 = 通用
    └── SKILL_ROOT = 从 SKILL.md 所在目录推断
    └── HOST_INSTRUCTION_FILE = AGENTS.md（开放标准）

输出：「🔧 宿主环境：{宿主名} | SKILL_ROOT={路径}」
```

**Step 1.2: 校验宿主指令文件**

检查项目根目录的 `{HOST_INSTRUCTION_FILE}` 文件：
- 不存在 → 创建并写入下方内容
- 存在 → 读取 `## Teamwork 协作模式` 段落，对照下方模板校验内容完整性
  - 段落缺失 → 追加
  - 内容不符合预期（缺失/被篡改/旧版本）→ 替换为预期内容
  - 完整匹配 → 跳过

🔴 如果项目根同时存在多个指令文件（CLAUDE.md + AGENTS.md），则**每个文件都写入**相同内容，确保不同工具都能读到。

**写入内容**：
```markdown
## Teamwork AI 开发团队

本项目使用 Teamwork 流程框架：一个 AI 以完整团队方式工作，在不同阶段切换专业视角（PMO/PM/QA/RD/架构师等），通过质量门禁确保产出质量。
启动方式：`/teamwork [需求]` 或 `/teamwork 继续`。
详细规范见 skill 目录：`{SKILL_ROOT}/`，入口为 SKILL.md。
🔴 激活后必须先读取 INIT.md 完成初始化检查，再接收需求。

### 🔴 PMO 每次阶段变更必做（3 件事，缺一不可）

1. 输出 1 行校验：`📋 {A} → {B}（📖 {🚀/⏸️}，来源：flow-transitions.md L{行号} "{原文}"）`
   🔴 必须引用 flow-transitions.md 的实际行号+原文片段，禁止只写"查 ✅"。编造行号 = 伪造证据。
2. 🚀自动 → 直接执行，禁止询问 | ⏸️暂停 → 给建议+理由，等确认
3. 按顺序逐步走，禁止跳过/合并/自创步骤

### 🔴 绝对红线（13 条）

1. PMO 禁止写代码/改文件（即使只改一行也必须启 RD Subagent）
2. 流程只有六种：Feature / Bug / 问题排查 / Feature Planning / 敏捷需求 / Micro
3. 禁止擅自简化：每种需求走完整流程，用户明确说「跳过」才可豁免
4. 所有用户输入必须由 PMO 先承接
5. 暂停点必须等用户明确确认
6. 需求类型只能填规定的六种
7. 使用流程只能填规定的六种
8. Feature Planning 只产出文档，禁止产出代码
9. 闭环验证：声称"已完成"必须附带实际命令输出
10. 暂停点必须给建议（💡）和理由（📝）
11. PMO 未输出初步分析前禁止写操作
12. 非暂停点（🚀）禁止插入确认/询问
13. Subagent dispatch 前必须完成对应级别预检（L1/L2/L3）

### 工作原则

1. 不要假设用户清楚自己想要什么。动机或目标不清晰时，停下来讨论，不要带着猜测往前跑。
2. 目标清晰但路径不是最短的，直接说并建议更好的办法。
3. 遇到问题追根因，不打补丁。每个决策都要能回答"为什么"。
4. 输出说重点，砍掉一切不改变决策的信息。
```

### Step 2: 加载项目空间

```
🔴 穷举检查原则：判定"不存在"前必须检查所有合理位置，禁止只查一个路径就下结论。

检查 teamwork_space.md：
├── 搜索：{项目根}/teamwork_space.md → {项目根}/docs/teamwork_space.md
├── 找到 → 读取，加载子项目清单
├── 未找到 → 进入「首次初始化」流程（见下方）
└── 输出：「📦 已加载项目空间（X 个子项目）」

检查 .teamwork_localconfig.md（多人协作）：
├── 存在 → 读取 scope（all / 指定子项目列表）+ worktree 策略（off/auto/manual）
├── 不存在 → 默认 scope=all（单人模式），worktree=off，不提示不打断
└── 用户主动说"我只负责 XX" → 那时再创建 localconfig

检查 worktree 环境（worktree ≠ off 时）：
├── 执行 git worktree list → 检测当前是否在某个 Feature worktree 中
├── 在 worktree 中 → 记录当前 worktree 对应的 Feature 编号
├── 不在 worktree 中 → 正常（Dev Stage 前按策略创建）
└── git 不可用 → worktree 降级为 off，输出提示
```

### Step 3: 扫描进度 + 输出看板

```
扫描各子项目 docs/features/*/STATUS.md：
├── 读取当前阶段、当前角色、最后更新、阻塞状态
├── 排除「✅ 已完成」的 Feature
├── 不存在但目录有 PRD.md → 推断阶段，创建 STATUS.md
└── 汇总为 Feature 看板（按最后更新降序）

📋 Feature 状态看板
| 子项目 | Feature | 当前阶段 | 当前角色 | 最后更新 |
|--------|---------|----------|----------|----------|

🔴 有进行中 Feature → 必须给出优先级建议（💡 + 📝 理由），不能只列状态
无进行中 Feature → 等待新需求
```

---

## 按需加载（不在启动时执行，角色需要时加载）

| 文件 | 加载时机 | 加载者 |
|------|----------|--------|
| docs/KNOWLEDGE.md | 各角色执行时参考 | 当前角色 |
| docs/architecture/ARCHITECTURE.md | RD 技术方案 / 架构师 Review / Dev Stage | RD / 架构师 Subagent |
| docs/architecture/database-schema.md | RD 涉及 DB 变更时 | RD Subagent |
| docs/PROJECT.md | PM 编写 PRD / PL 讨论产品方向 | PM / PL |
| design/sitemap.md + overview.html | Designer 设计阶段 | Designer Subagent |
| docs/ROADMAP.md | Feature Planning / PMO 完成报告 | PM / PMO |
| DEPENDENCY-REQUESTS.md | scope ≠ all（多人协作）时扫描外部依赖 | PMO |

**按需加载规则**：
```
├── 各角色 Subagent 启动时，PMO 在 prompt 中注入所需文件（见 agents/README.md §四）
├── 主对话角色切换时，PMO 按需读取相关文件
├── 不存在的文件：记录但不阻塞，首次需要时由对应角色创建
│   ├── ARCHITECTURE.md 不存在 → Dev Stage 首次执行时扫描代码自动生成基础版
│   ├── database-schema.md 不存在 → RD 涉及 DB 时扫描 migration/Model 自动生成
│   ├── PROJECT.md 不存在 → PM 首次 Feature Planning 时创建
│   └── KNOWLEDGE.md 不存在 → 无历史知识，正常执行
└── 自动生成的文档为基础版本，后续由架构师在 Code Review 阶段持续完善
```

---

## 首次初始化（teamwork_space.md 不存在时）

### 创建项目空间

```
扫描项目结构：
├── ≥2 个子项目 → 生成 teamwork_space.md 草稿 → ⏸️ 用户确认后写入
├── 1 个子项目 → 提示确认，生成 teamwork_space.md
└── 未发现子项目 → 询问用户定义项目名
🔴 禁止在用户确认前写入 teamwork_space.md
```

### 创建基础目录

```bash
mkdir -p docs/decisions
mkdir -p {子项目路径}/docs/features
mkdir -p {子项目路径}/docs/architecture
```

### 项目扫描

```
自动识别：项目类型 / 技术栈 / 是否需要 UI / 子项目结构
```

### Codex CLI 检测

```
codex --version 可用 → codex_cli_available = true
不可用 → false（不影响其他流程，仅 Codex Code Review 跳过）
```

### 输出初始化报告

```
📋 Teamwork 初始化完成
================================
✅ CLAUDE.md 已校验
📦 项目空间：已加载（X 个子项目）
🤖 Codex CLI：✅ 可用 / ❌ 未安装

| 缩写 | 名称 | 技术栈 | 需要 UI |
|------|------|--------|---------|

请输入需求开始第一个功能。
```

### 已初始化项目恢复报告（teamwork_space.md 存在时替代初始化报告）

> Step 3 扫描完成后直接输出此报告。

```
📋 Teamwork 项目恢复
================================
📦 项目空间：{路径}（{X} 个子项目）

📋 进行中 Feature：
| 子项目 | Feature | 当前阶段 | 当前角色 | 最后更新 |
|--------|---------|----------|----------|----------|

💡 建议：{优先推进项 + 理由}

可选操作：
├── 📝 提交新需求
├── 🔄 继续进行中的 Feature
└── 📋 查看某子项目 ROADMAP
```
