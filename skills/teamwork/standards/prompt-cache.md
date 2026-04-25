# Prompt Cache 友好规则（v7.3.10+P0-23 新增）

> **定位**：teamwork 在 Claude Code / Codex 等宿主下跑时，宿主会做**隐式 prompt caching**（前缀命中则按 ~10% 价格 + ~5x 速度计费）。本规范约束 teamwork 自身如何组织 prompt 前缀，让宿主的自动 caching 命中率最大化。
>
> **不负责**：
> - 显式 `cache_control` 参数（宿主接管，skill 层不碰）
> - 跨 session 缓存持久化（宿主能力，非本规范）
> - Token 峰值优化（那是瘦身问题，不是命中率问题）
>
> **ROI 锚点**：按 Anthropic 公开数据，稳定前缀 ≥ 1024 token 且字节一致时，命中后 input token 按 10% 计费。teamwork 一个 Feature 典型输入 ≥ 50K token → 命中率从 20% → 80% 的改造收益 ≈ 成本下降 2-3 倍。
>
> **三条硬规则**：
> - 🔴 **R1 动态内容后置**：稳定层（L0/L1/L2）禁止注入任何易变字面值
> - 🔴 **R2 Stage 入口读取顺序固定化**：每个 Stage 入口按固定顺序 Read，禁止穿插
> - 🔴 **R3 state.json 访问次数上限**：每 Stage 入口 1R + 出口 1R + 1W，中段禁读写

---

## 一、prompt 分层模型

teamwork 的 prompt 按稳定性分四层：

| 层 | 内容 | 变化频率 | cache 策略 |
|----|------|---------|-----------|
| **L0 框架层** | SKILL.md / RULES.md / standards/ / roles/ / templates/ / stages/ / FLOWS.md | 跨 session 不变（仅 skill 升级时变） | 🟢 强制纯静态 |
| **L1 项目层** | CLAUDE.md / teamwork_space.md / PROJECT.md / ARCHITECTURE.md / KNOWLEDGE.md / ADR INDEX.md | 单 Feature 内不变 | 🟢 保持稳定 |
| **L2 Feature 层** | PRD / TC / TECH / 已产出的 review 文件 | 单 Stage 内不变 | 🟡 按 Stage 稳定 |
| **L3 动态层** | state.json / 用户消息 / tool call 结果 / 当前时间 / 状态摘要 | 每轮可能变 | 🔴 必须放在前缀**末尾** |

🔴 **核心原则**：L3 动态内容**绝对禁止**进入 L0/L1/L2 文件本体。任何层级混入动态内容 = 整条上游前缀失效。

---

## 二、R1 动态内容后置规则

### 2.1 禁止注入的动态值类型

以下字面值在 L0/L1/L2 文件本体中**绝对禁止**（仅允许以 `{占位符}` 形式说明）：

- **时间类**：今日日期 / 当前时间 / 时间戳 / "最后更新于 YYYY-MM-DD" / "自 YYYY 年以来..."
- **Git 类**：`git branch --show-current` 结果 / commit SHA / `git log` 输出
- **身份类**：当前用户姓名 / email / 机器名 / 路径上的用户目录
- **状态类**：当前 Feature 编号 / 当前 Stage / state.json 的任何字段取值
- **环境类**：CWD 绝对路径 / 当前工作目录的 `ls` 结果 / 环境变量值
- **会话类**：对话轮次编号 / 历史消息 ID / token 计数

### 2.2 正确表达方式

| 错误做法 | 正确做法 |
|---------|---------|
| "当前 Feature（F042-支付重构）的 PRD 必须..." | "当前 Feature（`{Feature 目录名}`）的 PRD 必须..." |
| "Skill 自 2026-04 起要求..." | "Skill 自 v7.3.10+P0-23 起要求..."（版本号稳定，日期不稳定）|
| "从 state.json 读取当前 Stage = blueprint 时..." | "从 state.json 读取 `{current_stage}` 字段，若值为 blueprint 时..."（占位符表述）|
| 示例段落："今天 2026-04-24，RD 执行..." | 示例段落："（示例日期 YYYY-MM-DD）RD 执行..."（明确是示例占位符）|

### 2.3 允许的动态内容承载位置

- ✅ **STATUS-LINE 输出**（单轮末尾，宿主渲染）
- ✅ **PMO 初步分析输出块**（单轮末尾，PMO 产出）
- ✅ **tool call 结果**（Read/Bash 输出，天然进入对话尾部）
- ✅ **Subagent dispatch.md 的 Input Files 段**（dispatch 内独立 session）

---

## 三、R2 Stage 入口读取顺序固定化

### 3.1 通用入口 Read 顺序（10 Stage 统一模板）

🔴 每个 Stage 启动时，PMO 必须按以下**固定顺序**执行 Read 操作，顺序不可颠倒：

```
Step 1: Read roles/{本 Stage 负责角色}.md           ← 角色层（相对稳定）
Step 2: Read templates/{本 Stage 需产出的模板}.md    ← 格式层（稳定）
Step 3: Read Feature 既有产物（L2 层，PRD/TC/TECH）  ← Feature 层（Stage 内稳定）
Step 4: Read state.json                             ← 🔴 必须最后，作为动态入口
                                                      此点之后前缀视为"稳定段结束"
```

### 3.2 每个 Stage 自己要补的清单

每个 stage spec 必须在顶部（Process Contract 之前）声明「入口 Read 清单」段，列出本 Stage 的具体文件：

```markdown
## 入口 Read 顺序（v7.3.10+P0-23 固定）

🔴 按以下顺序读，字节一致利于 prompt cache 命中：

1. `roles/{角色}.md`
2. `templates/{模板1}.md`, `templates/{模板2}.md`
3. `{Feature}/PRD.md`, `{Feature}/TC.md`（若本 Stage 依赖）
4. `{Feature}/state.json` ← 最后，动态入口
```

### 3.3 严格禁止

- 🔴 **禁止中段穿插 Read 新文件**：如果 Process Contract Step 5 突然需要 Read roles/qa.md，那就在入口 Read 清单里预先加入 qa.md；不预先加 = 前缀碎片化
- 🔴 **禁止按条件分支 Read**：分支条件在运行时才确定，会破坏前缀一致性。改做法：把所有可能分支的文件都预先加载，代码里再按条件使用
- 🟢 **允许的例外**：用户对话中追加需求时，PMO 按需 Read 用户指定的文件（那轮必然 cache miss，认了）

### 3.4 为什么 state.json 必须最后

- state.json 每 Stage 都会变（新 timestamp、新 executor_history）→ 前缀必然 miss
- 把它放在"稳定段"末尾 = 让前面所有 L0/L1/L2 文件都能被 cache 命中
- 把它放在前面 = 整条链一起 miss，改造白做

---

## 四、R3 state.json 访问次数上限

### 4.1 访问模式（硬约束）

每个 Stage 内 state.json 访问次数严格限制：

| 时机 | 操作 | 次数 | 说明 |
|------|------|------|------|
| **Stage 入口** | Read | 1 次 | 与 R2 通用入口顺序的 Step 4 对齐 |
| **Stage 中段** | Read / Write | **0 次** | 🔴 绝对禁止，违反 = 流程偏离 |
| **Stage 出口** | Read | 1 次 | 出口 Read 一次，对齐 Write 前的最新状态 |
| **Stage 出口** | Write | 1 次 | 决定状态流转、写入 executor_history |

### 4.2 豁免列表

以下场景允许突破"中段 0 次"上限，但必须满足条件：

| 豁免场景 | 允许操作 | 约束 |
|---------|---------|------|
| **内部评审修复循环**（Blueprint Stage TC/TECH 评审、Review Stage fix 循环） | 每轮修复结束时 1 次 Write | 🔴 至多 3 轮（对齐现有修复上限规则）|
| **Subagent dispatch 产出整合** | 整合每个 subagent 产出后 1 次 Write | 🔴 每次 dispatch 至多 1 次 |
| **用户显式追加需求导致 Stage 内部重走** | Read + Write 各 1 次 | 🔴 必须先走 PMO 分析 + 用户确认 |

### 4.3 反模式

| 反模式 | 正确做法 |
|-------|---------|
| 每个 Step 开头都 Read state.json 确认当前状态 | 🔴 入口 1 次 Read 后，中段状态在主对话上下文中保持；不重复 Read |
| 每写一个字段就 Write 一次 | 🔴 出口 1 次 Write 汇总全部变更 |
| "保险起见再 Read 一次 state.json" | 🔴 违反 R3；保险起见应该 review 上下文，而非重读 |
| 中段遇到不确定 → Read state.json 兜底 | 🔴 不确定 = 暂停点问用户，不是 Read 文件 |

### 4.4 量化上限

🔴 单个 Stage 完整执行过程 state.json 总访问次数 ≤ **5 次**（2 Read + 1 Write + 2 次豁免缓冲）
- 超过 5 次 = 流程偏离，记入 state.concerns
- 极端情况（复杂修复循环）≤ 8 次 = 需要在 concerns 明确记录理由

---

## 五、审计清单

teamwork skill 自查时检查以下项：

- [ ] `grep -E "今日|当前时间|YYYY-MM-DD" SKILL.md RULES.md INIT.md stages/ roles/ templates/` 返回空（除非是占位符说明）
- [ ] 每个 stage spec 顶部存在「入口 Read 顺序」段
- [ ] `roles/pmo.md` 含 state.json 访问次数上限约束
- [ ] Process Contract 里 state.json 操作只出现在 Step 1（入口）+ Step N（出口）
- [ ] 中段 Read/Write state.json 必有豁免场景标注

---

## 六、与其他规范的协作

- 🔗 [SKILL.md §红线](../SKILL.md#绝对红线) — 本规范不是红线，是性能硬规则，违反不触发红线机制但记入 concerns
- 🔗 [RULES.md](../RULES.md) — RULES 收录流程规则，本规范收录性能规则，两者互补
- 🔗 [standards/common.md](./common.md) — common 收录产出内容规范，本规范收录前缀组织规范
- 🔗 [INIT.md Step 1.2](../INIT.md) — INIT 的版本缓存机制（缓存"已校验状态"）与本规范（让 LLM prompt cache 命中）叠加使用，两套缓存层级互补

## 七、不在本规范覆盖的

- Anthropic API 的 `cache_control` 显式 breakpoint — 宿主接管，不触碰
- 跨 session 的持久化缓存 — 宿主能力
- Subagent dispatch 的 prompt 组装优化 — 见 `agents/README.md`（有独立优化路径）
- 模板瘦身 / 红线精简 / 索引压缩 — 属于 token 峰值优化，见各自规范
