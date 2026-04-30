# Triage Stage：用户输入承接 + 流程分流（流程级 Stage）

> 用户在 init-stage 完成后输入第一条需求消息时进入本 Stage。PMO 在此阶段做 KNOWLEDGE 扫描、ADR 扫描、外部模型探测、流程类型识别、流程步骤描述、暂停点决策。
>
> 🟢 **流程级 Stage**（v7.3.10+P0-26 新增）：
> - 触发频率：每次新需求一次（不是每 Feature；问题排查 / Micro / 敏捷需求 / Feature / Feature Planning / Bug 都走 triage 入口）
> - 状态归属：**幂等不持久化**——triage 不写 state.json，新对话重启时按用户原始消息重跑（结果应一致；外部模型探测可能因 CLI 安装变化而不同，预期行为）
> - 写操作禁令：本 Stage 触发红线 #10「写操作硬门禁」——未输出初步分析前禁止任何写
>
> 🔴 契约优先：本文件规范 Input / Process / Output 三契约。本 Stage 是 PMO 的**入口编排单元**。

---

## 本 Stage 职责

把"PMO 散落的初步分析"统一为契约化 Stage：
- 用户输入承接（红线 #4：所有用户输入由 PMO 先承接）
- KNOWLEDGE 扫描（v7.3.10+P0-22）
- ADR 索引扫描（v7.3.10+P0-21）
- 外部模型探测（v7.3.10+P0-24）
- 流程类型识别（六种之一，红线 #2）
- 跨 Feature 冲突检查 + 跨项目依赖识别（v7.3.10+P0-8）
- 流程完整步骤描述（红线 #15）
- 暂停点呈现（流程确认 + 外部模型评审决策点）

---

## Input Contract

### 必读输入

```
- 用户原始消息（自然语言 / `/teamwork ...` 命令参数）
- init-stage 已加载的项目空间状态（teamwork_space.md / 子项目清单 / 看板）
- 项目级 KNOWLEDGE.md（Gotcha / Convention / Architecture 三类）
- 已有 Feature 的 ADR 索引（如 docs/features/{Feature}/adrs/INDEX.md）
- 探测脚本输出（templates/detect-external-model.py JSON）
- Workspace 已有 Feature 状态扫描（识别可能的冲突）
```

### 进入条件

```
- init-stage 已完成（宿主检测、SKILL_ROOT 确定、CLAUDE.md 校验通过）
- 用户输入消息已收到
- 红线 #10 写操作硬门禁生效（任何写操作必须先经过本 Stage 的初步分析输出）
```

## 入口 Read 顺序（v7.3.10+P0-26 固定）

🔴 按以下顺序 Read，字节一致利于 prompt cache 命中。详见 [standards/prompt-cache.md](../standards/prompt-cache.md)。

```
Step 1: roles/pmo.md                            ← 角色层（L0 稳定）
Step 2: 无新模板                                 （checklist 在本 Stage spec 内）
Step 3: 项目级 KNOWLEDGE.md, teamwork_space.md  ← 项目层（L1 稳定）
        docs/features/*/adrs/INDEX.md           （如适用，L1）
Step 4: 用户原始消息                              ← 🔴 最后，动态入口（L3）
        + 探测脚本 stdout（detect-external-model.py）
```

🔴 R3 约束：本 Stage 不写 state.json（幂等设计），仅在用户确认流程后由后续 Feature 级 Stage 创建 Feature state.json 并写入字段。

---

## Process Contract

### Step 1: 用户输入承接（红线 #4）

PMO 必须**先**显式响应"我已收到你的输入"再做任何分析。禁止 AI 直接跳过承接动作进入分析。

### Step 2: KNOWLEDGE 扫描（v7.3.10+P0-22）

读取项目级 `KNOWLEDGE.md`，根据用户输入的关键词扫描三类（Gotcha / Convention / Architecture），输出「📚 相关项目事实」段：

**有命中时**（任一类 ≥1 条）：

```markdown
## 📚 相关项目事实（KNOWLEDGE 扫描）

- Gotcha 命中（X 条）：
  - {KNOWLEDGE.md 引用 + 简述}
- Convention 命中（Y 条）：
  - {同上}
- Architecture 命中（Z 条）：
  - {同上}
```

**无命中时**（v7.3.10+P0-30 渲染降级）：一行带过，不展开三类标题：

```markdown
📚 KNOWLEDGE 扫描：均无相关条目
```

🔴 **无命中也必须输出此行**（红线：扫描结果不可省略），但不需要展开 0 命中的子标题，避免视觉冗余。

### Step 3: ADR 索引扫描（v7.3.10+P0-21）

扫描已有 Feature 的 `adrs/INDEX.md`，识别与当前需求相关的历史决策：

**有命中时**：

```markdown
## 📜 相关 ADR（历史决策扫描）

- {ADR ID}：{标题}（{Feature 引用}）
- ...
```

**无命中时**（v7.3.10+P0-30 渲染降级）：

```markdown
📜 ADR 扫描：均无相关决策
```

### Step 4: 角色可用性扫描（v7.3.10+P0-38-A 修订）

🟢 **v7.3.10+P0-38-A 修订**：每次 Feature 启动时实时扫描（不在 init），反映运行时环境变化。

🟢 **v7.3.10+P0-30 跳过条件**：当 Step 5 流程类型识别为**问题排查**时，本 Step 整体跳过（问题排查不出代码、不需要角色可用性扫描）。

其他流程类型按以下规则扫描：

```
内部角色（固定可用）：
  ├── pl / rd / qa / designer / pmo / architect
  └── 始终加入 available_roles[]（不需要探测）

external 角色（按宿主异质性 + CLI 可用性探测）：
  ├── 调用 templates/detect-external-model.py
  ├── 解析 JSON 输出，识别异质 CLI（与主对话宿主异源）
  │   ├── 主对话 = claude → 找 codex-cli
  │   ├── 主对话 = codex  → 找 claude-cli
  │   └── 同源外部即使可用也不算（角色契约要求异质性）
  ├── 异质 CLI 可用 → available_roles[] 加 "external"
  │                  state.external_cross_review.model = "codex" 或 "claude"
  │                  state.external_cross_review.host_main_model = ...
  │                  state.external_cross_review.host_detection_at = <ISO 8601 UTC>
  │                  state.external_cross_review.available_external_clis = [...]
  └── 异质 CLI 不可用 → available_roles[] 不含 external
                       state.external_cross_review.model = null
                       state.concerns 加 INFO（不报警，仅信息）
```

🔴 **PMO 校验**：
- available_roles[] 必须 ≥ 6（内部 6 角色固定可用）
- external 是否在内取决于异质性匹配 + CLI 探测
- 探测脚本失败 → INFO + external 不在 available_roles，**不阻塞 triage**

#### 渲染输出

```markdown
🎭 角色可用性扫描
├── 内部角色：pl / rd / qa / designer / pmo / architect（6 个，固定可用）
└── external 角色：{✅ 可用（model={codex|claude}）/ ❌ 不可用}{失败时附 INFO 摘要}
```

📎 详见 [standards/external-model.md](../standards/external-model.md)（探测脚本规范）+ [roles/external-reviewer.md](../roles/external-reviewer.md)（角色契约）。

### Step 5: 流程类型识别（红线 #2）

根据用户输入 + 上述扫描结果，识别六种流程之一：

| 流程类型 | 识别信号 |
|---------|---------|
| **Feature 流程** | 完整需求、可能含 UI、改动 ≥5 文件或涉及架构 |
| **Feature Planning** | "规划"、"拆解"、"ROADMAP"、产品方向性话题 |
| **Bug 处理** | "Bug"、"报错"、"异常"、"线上问题"等明确缺陷措辞 |
| **问题排查** | "为什么"、"定位"、"分析下"、"检查下"、"看看"、"是否符合预期"等不含修复意图的核验 / 探究（v7.3.10+P0-30：扩展识别信号）|
| **敏捷需求** | 改动 ≤5 文件、无 UI/架构变更、方案明确 |
| **Micro** | 零逻辑变更（文案 / 样式 / 资源 / 配置常量 / 注释文档） |

🔴 不可识别为六种之外的类型；模糊场景下选最贴近的并在理由中说明。

### Step 6: 跨 Feature 冲突检查 + 跨项目依赖识别 + 变更归属检查（v7.3.10+P0-33 新增）

```
- 扫描已有进行中 Feature（state.current_stage != "completed"）
- 识别本需求与已有 Feature 的 ROADMAP 冲突 / 共享文件
- 跨项目依赖识别（v7.3.10+P0-8）：如本需求触及子项目 A 但依赖子项目 B 的接口/数据，必须显式列出
```

#### Step 6.5：变更归属检查（v7.3.10+P0-33 新增）

PMO 检查当前需求是否归属某个变更：

```
1. 扫描 product-overview/changes/*.md
2. 读每份变更文档的 frontmatter sub_features[] 字段
3. 判断当前 Feature 是否在某变更的 sub_features[] 中（按 ID / 范围匹配）
   - 匹配 → 当前 Feature 归属该变更
   - 不匹配 → 独立 Feature，不属于任何变更
4. 如归属变更 → 检查变更状态（frontmatter status 字段）
```

**归属变更时的处理矩阵**：

| 变更状态 | PMO 处理 |
|---------|---------|
| `discussion` | 🔴 硬阻塞：「本 Feature 归属变更 {change_id}（status=discussion 业务方向讨论中）。变更未完成规划前禁止启动子 Feature。请先与 PL 完成方向讨论 + 详细规划锁定（status=locked）。」 |
| `planning` | 🔴 硬阻塞：「本 Feature 归属变更 {change_id}（status=planning 详细规划中）。子 Feature 拆分 / 依赖 / 启动顺序未锁定前禁止启动。请先与 PM/RD 完成规划 + 用户锁定（status=locked）。」 |
| `locked` | 🟢 校验当前 Feature 是否在 launch_order 的下一个可启动节点：<br>- 是 → 通过，进入 Step 7<br>- 否（依赖未完成）→ 🔴 硬阻塞：「本 Feature 在 launch_order 中的依赖 {依赖 Feature ID} 未完成（当前状态 {状态}）。请先完成依赖 Feature。」 |
| `in-progress` | 🟢 同 `locked`，校验依赖 + launch_order |
| `completed` | 🟡 异常：变更已完成不应再启动子 Feature。提示用户：「变更 {change_id} 已 completed。如需新增子 Feature，请创建新变更或扩展本变更（须用户确认）」 |
| `abandoned` | 🟡 异常：「变更 {change_id} 已 abandoned。本 Feature 不应启动。」 |

#### 硬阻塞的逃生舱

```
🔴 阻塞时输出：
[阻塞理由 + 提示]

请选择：
1. ✅ 先去完成变更规划 / 完成依赖 Feature 💡（推荐）
2. 🔓 强制启动本 Feature（绕过变更状态检查）
3. 改成独立 Feature（脱离变更归属，但 launch_order 中保留占位符）
4. 其他指示

🔴 选项 2 强制启动须用户明确选择，state.concerns 加 WARN「用户绕过变更状态检查（变更 {change_id} 状态 {状态}），强制启动 Feature {当前 ID}」。
```

#### 当前 Feature 不归属任何变更时

直接通过本 Step，进入 Step 7。无需打扰。

### Step 7: 流程步骤描述（已合并到 Step 8 Feature 骨架，v7.3.10+P0-42 删除独立段）

> 🟢 **v7.3.10+P0-42 重构**：原 Step 7「流程步骤描述」段（P0-26 残留）已被 Step 8「Feature 骨架」段（P0-38-A 引入的 execution_plan_skeleton）取代——骨架段含每个 Stage 的 `goal / key_outputs / pause_points / execution_hints`，是流程步骤描述的超集。
>
> 本 Step 编号保留作为锚点（与 flow-transitions.md 引用对齐），实际输出合并到 Step 8 骨架段，不重复输出"流程步骤描述"独立段。
>
> 红线 #15（流程确认红线 - 必须给步骤描述）由 Step 8 骨架段承载：每个 Stage 的 goal + pause_points 即"做什么 + 暂停点"。

### Step 7.5: 环境配置预检（v7.3.10+P0-27 新增，仅 Feature / Bug / 敏捷需求 适用）

> 🔴 **这一步取代了原 v7.3.9 的「Goal-Plan Stage 入口 Preflight 暂停点」**（v7.3.10+P0-27 删除该独立暂停点）。
> 决策前置到 triage 暂停点，环境准备的执行后置到 Goal-Plan Stage 入口（自动执行，不暂停）。

PMO 探测当前 git 环境，输出「🛠 环境配置预检」段：

```bash
# PMO 内部探测（只读，不写）
- 读 .teamwork_localconfig.md → worktree 模式（auto / manual / off）+ worktree_root_path + default_merge_target
- git rev-parse --abbrev-ref HEAD          → 当前分支
- git status --porcelain                   → 工作区是否干净
- git ls-files --others --exclude-standard → 未跟踪文件清单（如脏）
- 推断 base 候选：origin/{merge_target}
- 读 teamwork_space.md 子项目清单表 docs_root 列 → 计算 artifact_root
```

🔴 **v7.3.10+P0-41 硬规则（避免实战漏洞）**：

```
1. worktree 缺失硬默认 auto：
   ├── localconfig.worktree 字段缺失 / 注释掉 / 解析失败 → PMO 按 auto 处理
   ├── 🔴 禁止 PMO 自降级 off（"主工作区干净"等不是 off 理由）
   └── 仅当用户在 Step 8 决策点显式选 off 才允许 off

2. artifact_root 计算（路由权威，多子项目模式必做）：
   ├── 读 teamwork_space.md 子项目清单表 → 找 sub_project 对应行的 docs_root 列
   ├── artifact_root = {docs_root} + "/" + {Feature 全名}
   ├── 例：sub_project=FE → docs_root=app-frontend/docs/features → artifact_root=app-frontend/docs/features/F059-HomeShortcutKeySync
   ├── 🔴 禁止"沿用历史根 docs/features/"等理由偏离 docs_root 列
   └── teamwork_space.md docs_root 列缺失 / 不规范 → triage 阻断 + 提示用户先补全

3. 单子项目模式（无 teamwork_space.md）：
   ├── artifact_root = docs/features/{Feature 全名}
   └── state.sub_project = null
```

输出格式：

```markdown
## 🛠 环境配置预检

| 项 | 探测结果 | 计划行为 |
|----|---------|---------|
| worktree | mode={auto/manual/off}（P0-41 缺失硬默认 auto）, path=`{worktree_root_path}/{Feature 全名}`（P0-39 默认 `.worktree/`）| Goal-Plan Stage 入口创建 |
| 路由 | sub_project={abbr}, artifact_root={docs_root}/{Feature 全名}（P0-41 路由权威）| Stage 内 Write/Edit 前 PMO 必须校验路径前缀；teamwork_space.md docs_root 列缺失则阻断 |
| 分支 | HEAD={当前分支}, target={staging\|main\|master}, base=origin/{merge_target} | Goal-Plan Stage 入口 git checkout -b feature/{Feature 全名} origin/{merge_target} |
| 工作区 | {干净 \| 脏（N 个未提交文件）} | 干净自动继续；脏进入异常分支 |

🟢 探测结果正常 → triage 暂停点直接可继续
🔴 工作区脏 / 分支冲突 → triage 暂停点附决策选项（让用户选 stash / commit / 强制继续 / 取消）
```

🔴 **仅 Feature / Bug / 敏捷需求 流程触发本 Step**。Feature Planning 不出代码，问题排查不出代码，Micro 流程直接改主分支不需要 worktree——这三种流程跳过本 Step。

### Step 8: 暂停点呈现（**意图理解 + 流程承诺 双对齐** 一次性决策）

> 🟢 **v7.3.10+P0-30 分支**：当流程类型 == 问题排查 且**信号置信度足够**（用户措辞明确表达"核验 / 探究"且无修复意图）时，**跳过流程确认暂停点**，改为主动声明 + 直接执行。详见下方「问题排查快速通道」。
>
> 其他流程类型（Feature / Feature Planning / Bug / 敏捷需求 / Micro）走双对齐暂停。
>
> 🆕 **v7.3.10+P0-49 改造**：本 Step 输出从单一"流程承诺骨架"扩展为「意图理解段 + 流程承诺骨架」双产出，暂停点从单流程对齐改为双对齐（意图 + 流程一次性 ok）。意图段不落盘，存在于主对话上下文，下一阶段首次产出 commit 时自然落盘到对应人读资产（PRD 背景 / BUG-REPORT 顶部 / 排查记录顶部 / Feature Planning 章节草稿；Micro 流程意图段就一句话变更描述，不落盘）。

#### Step 8 意图理解段（v7.3.10+P0-49 新增 — 按流程类型分 schema）

PMO 在主对话渲染本段（**不落盘**），由用户在双对齐暂停点确认。schema 按流程类型分支：

```
[Feature / 敏捷需求 / Feature Planning]

📌 我对你这次需求的理解

Why now
{推断的因由：用户痛点 / 上游变更 / 业务诉求 / 之前 Feature 暴露的问题。
 一两句话；如有多个候选解读 → 列出来让用户拍板，不要替用户选}

Assumptions
- {假设 1：用户行为 / 技术 / 业务 / 上游可用性}
- {假设 2}
- {假设 3}
（每条用一句话；假设错了影响整个 Feature 的标"🔴 关键假设"）

Real unknowns（评审中讨论或现在拍板都行）
1. {真正不确定点 1：错了整个 Feature 重做的级别，不是 OQ 模板填空}
2. {真正不确定点 2}
3. {真正不确定点 3}
（数量 1-3 条，多了说明意图本身没想清楚 → 回去跟用户对齐）
```

```
[Bug]

📌 我对你这次需求的理解

症状
{用户报告的现象 + 何时何地出现}

复现路径
{1-N 步可复现的操作序列；如不可复现标"间歇性"+ 出现频率}

影响范围
{受影响用户群 / 受影响子项目 / 受影响业务功能 / 严重程度（P0-P3）}

期望行为
{修复后应该是什么样}
```

```
[问题排查]

📌 我对你这次需求的理解

症状
{用户描述的现象}

已知信息
{相关上下文：上游变更 / 最近发布 / 类似历史 case}

排查目标
{解释清楚什么 / 定位到什么粒度（确认是不是 bug / 找到根因 / 确定影响范围 / 等）}
```

```
[Micro]

📌 我对你这次需求的理解：{一句变更描述，如"把 Logo 图标 logo-v1.svg 换成 logo-v2.svg"}
（Micro 流程意图段就这一句，不需要 Why/Assumptions/Unknowns 结构化）
```

🔴 **意图段输出硬规则**：

- **不落盘**：意图段仅在主对话渲染，不写入 state.json，不建独立 INTENT.md 文件
- **下一阶段继承**：进入 Goal-Plan Stage 子步骤 1（Feature/敏捷需求）/ Bug 流程 RD 起草 BUG-REPORT.md / 问题排查 RD 介入 / Feature Planning 写 Planning 产物时，意图段从主对话上下文**继承到对应人读资产文件**（PRD 背景段 / BUG-REPORT 顶部 / 排查记录顶部 / PROJECT.md 章节）。Micro 流程意图段就一句话不落盘
- **schema 按流程类型分支**：不允许跨流程混用（Feature 流程不写 Bug 的"症状/复现"，Bug 流程不写 Feature 的"Why now/Assumptions"）
- **PMO 草拟，不替用户决策**：Why now 有多种解读时列出来让用户选，不替选；Real unknowns 分"评审中讨论"和"用户已拍板"两个状态——拍板状态由用户在双对齐暂停时主动告知

🔴 **Step 8 硬约束（v7.3.10+P0-38-B 新增 / +P0-49 双对齐改造）**：

triage Step 8 暂停点的**唯一合法形态**是双对齐确认（意图 + 流程一次性 ok）：

```
⏸️ 双对齐

意图理解 + 流程承诺一次确认：

回 ok = 全部采纳推荐 → 写 state.json + 建任务目录 + 进入下一阶段
回数字 = 单点调整（如"骨架某 Stage 调整"或"unknowns 中我已拍板某项"）
回具体反馈 = 自由文本，PMO 解析意图修订或调整流程
回"切流程" / "改成 X" = 切换流程类型（如 Feature → 敏捷需求）
```

**双对齐的两个对齐维度**：

1. **意图对齐**：用户对 PMO 渲染的意图理解段（Why now / Assumptions / Real unknowns / 等按流程分形态）确认无偏差
2. **流程对齐**：用户对 PMO 起草的流程承诺骨架（Stage 链 / 评审角色组合 / execution_hints）确认采纳

回 `ok` 同时确认两件事；意图错了或流程错了都不能 ok（应给反馈或调整）。

**禁止的反模式（必须杜绝）**：

```
❌ 在 triage Step 8 输出 ≥2 个产品决策点（A/B/C 选项 × 多个问题）
   例：Q1 替换范围 / Q2 实现参数化 / Q3 复制内容 / Q4 反馈方式

   原因：Q1-Q4 是产品决策（业务方向 / 技术方案 / UX 细节），
        应在 Goal-Plan Stage 内部由 PM 起草 PRD 时承载（带不确定性进 Goal-Plan Stage 是合法的）。
        triage 只输出意图理解段（让用户确认 PMO 没偏）+ 流程承诺骨架（哪些 Stage / 评审组合），
        不替用户决策具体产品参数。

❌ 把流程确认 + 产品澄清问题混在同一暂停点
   例：在 Step 8 弹"Q1 业务方向 A/B/C / Q2 实现细节 a/b / Q3 流程类型"

   原因：意图段中 Real unknowns 列出来等评审讨论是合法的，但**不弹具体选项菜单**让用户在 triage 拍板。
        用户对意图段中 Real unknowns 的回应是"评审中讨论"或"我已拍板告诉你方向"，PMO 接收即可，不替用户列 A/B/C。
        流程跳步会让 Goal-Plan Stage 失去价值（产品决策应在 Goal-Plan Stage PRD 起草时讨论）。

❌ 把双对齐拆成两次单对齐暂停（先意图后流程，或先流程后意图）
   原因：决策疲劳。一次回复确认两件事 = 信息密度高 + 用户体验好。
        如果意图错了或流程错了，用户在同一回复给反馈 PMO 一次性修订。
```

🔴 **PMO 产品决策边界**（详见 [roles/pmo.md § 产品决策边界](../roles/pmo.md)）：
- triage Step 8 不得出现"业务方向选项"、"技术方案选项"、"UX 细节选项"
- 这些**应该带着不确定性**进 Goal-Plan Stage，PM 起草 PRD 时讨论 / 与 PL 评审时澄清
- triage 输出"📋 流程步骤描述"段时如发现**产品方向有多种解读**，应在 execution_hints 文本中说明（如"理由：业务方向有多种解读，Goal-Plan Stage 由 PM/PL 协商"），不出选项

🔴 **execution_plan_skeleton 输出契约**（v7.3.10+P0-38-A）：
- 必须输出每个 Stage 含 4 字段必填（stage / goal / key_outputs / pause_points）+ 1 可选（execution_hints）
- 仅"📋 流程步骤描述"段（旧格式）不算合规——必须以 execution_plan_skeleton 结构输出
- 缺字段视为流程违规，Stage 入口实例化无依据可读

#### Step 8 标准路径（Feature / Feature Planning / Bug / 敏捷需求 / Micro）

用户决策点（编号化，红线 #9 + #18）：

```
💡 建议: 走 {流程类型}
📝 理由: {简述}
1. {推荐流程} 💡
2. {备选流程，如适用}
3. 其他指示
```

#### Step 8 问题排查快速通道（v7.3.10+P0-30）

识别为问题排查时，PMO **不展示 4 选 1 流程确认暂停点**，改为：

```markdown
## 流程类型识别

└── 问题排查 ✅
    信号：{用户原句中的核验意图措辞，如"检查下…是否符合预期"}
    范畴：{涉及子项目 / 模块 / 单一资源}
    风险：极低（只读，不改任何文件）

🚀 直接进入问题排查执行（PMO 自主执行 grep / ls / git log / 配置核对等只读操作）
   默认范围：源码静态查 + 配置核对；不启动本地服务（如需本地实测须用户授权）

如需改流程，输入"切换流程"或具体指示（如"按 Micro 直接修复" / "改成敏捷需求做完整修复"）。
```

随后 PMO 直接执行排查 + 输出排查报告 + ⏸️ 用户决策（修 / 不修 / 升级流程）—— 整个问题排查流程**仅 1 个暂停点**（排查报告后的决策）。

**置信度判定**（PMO 自行决定是否走快速通道）：
- ✅ 走快速通道：用户措辞明确含"检查 / 排查 / 看看 / 为什么 / 分析下 / 是否符合预期 / 定位"等核验信号 + 无修复指令 + 范畴清晰
- ⚠️ 走标准 4 选 1：用户措辞模糊（"看下 favicon" 既可能是核验也可能是要修复）/ 范畴不清晰（"看看整个网站有什么问题"）/ 跨多子项目（需要用户先确认范围）

PMO 拿不准时**保守走标准 4 选 1**——默认安全，用户回 1 选问题排查仍然进入快速通道。

#### Step 8 用户打断机制（v7.3.10+P0-30）

无论走快速通道还是标准 4 选 1，用户在 PMO 输出"直接进入问题排查执行"或排查执行过程中输入"切换流程" / "改成 X" / "不要排查" 等切换意图措辞时，PMO 立即停止当前执行，回到 Step 8 标准 4 选 1 让用户重选。

如有可用外部模型候选，**单独**给出外部评审决策点（v7.3.10+P0-28：三处独立 + 快捷选项）：

#### Feature 骨架决策（v7.3.10+P0-38 重构，取代原"外部模型决策" + "Plan 评审组合决策"两块）

> 🟢 **v7.3.10+P0-38 设计哲学**：triage 时上下文不足以决策每 Stage 的具体执行细节（PRD 还没写、代码还没出）。triage 仅输出**骨架**——哪些 Stage / 每 Stage 候选角色（来自 init.available_roles）/ 目标 / 关键产出 / 暂停点。具体决策（模型 / 串行并行 / 输入输出 / 评审循环参数）**延迟到各 Stage 入口**实例化（红线 #14 AI Plan 模式承担）。
>
> 取消的两块决策：
> - ❌ 独立"🌐 外部模型评审决策"段（external 升格为评审角色，由 execution_hints 文本承载）
> - ❌ "🧭 Goal-Plan Stage 评审组合决策"段（Goal-Plan Stage 入口实例化，不在 triage 决）

PMO 输出 execution_plan_skeleton（4 字段必填 + 1 可选字段：stage / goal / key_outputs / pause_points / execution_hints）+ 启动确认 3 选 1：

🔴 **卡片式输出模板硬规则（v7.3.10+P0-60 表格化）**：triage Step 8 主对话输出**必须套用下方卡片骨架**，不允许散文化展开。整个 Step 8 输出（意图段 + 骨架 + 暂停点）目标 ≤ 30 行。

🔴 **必含 5 段（缺一即流程违规）**：
1. 意图段（按流程类型 schema · ≤ 8 行 · Why now ≤ 2 行 / Assumptions ≤ 3 条 / Real unknowns ≤ 3 条 · Real unknowns 不进 state.json triage 写入清单 · 由各 Stage 入口角色起草时承接评审）
2. 流程承诺骨架表（# / Stage / 一句话目标 / 非默认 · 4 列 · Stage 数行）
3. 流程 meta 一行（流程类型 / Stage 总数 / 暂停点总数 / 预估耗时 / Feature ID）
4. 关键假设（仅当有"错了改路径"级假设时输出 · ≤ 2-3 条）
5. 双对齐 + 环境处理融合表（一表多用 · 选项行 + 含义列 + 推荐标 💡）

🔴 **必砍 7 段（违反 = 履职报告反模式）**：
1. ❌ 「Why now」单独成段（已在意图段 ≤ 2 行内承载，不再复述）
2. ❌ 「关键非默认决策」总结段（已在 Stage 表「非默认」列承载）
3. ❌ 「KNOWLEDGE 命中」详细段（一行摘要 + ID 落主对话；详细落 state.json `knowledge_hits[]`）
4. ❌ 「ADR 扫描」详细段（"无相关 / 见 INDEX"一行兜底；命中详情落 state.json `relevant_adrs[]`）
5. ❌ 「External 可用」详细段（init Stage 已写 state.available_roles · triage 不复述）
6. ❌ 「环境异常」单独成段（探测异常 → 直接进双对齐表的环境处理选项）
7. ❌ 各 Stage 多行展开（goal / key_outputs / pause_points / execution_hints 4 行 → 表格 1 行 · 详情查 stages/{stage}-stage.md Output Contract）

🔴 **execution_hints 在表内的承载方式**：
- 表内「非默认」列只写**一行**含核心点 + 简短理由（如 `💡 +codex (SSRF)` / `💡 跳 Designer (无视觉变更)`）
- 完整理由 + 详细 hint_text 落 state.json `execution_plan_skeleton.stages[].execution_hints` 字段（Tier 3）
- 默认配置不输出 — 只显示 `—`（破折号）

```markdown
📌 我对你这次需求的理解（不落盘 · 待你 ok）

🎯 意图：{一句话需求理解}

Why now：{1-2 行简短因由 · 用户未知信息才输出 · 已知则省略本行}
Assumptions：A1 {假设} / A2 {假设} / A3 {假设}（≤ 3 条 · 错了改路径的标 🔴）
Real unknowns：U1 {不确定项} / U2 {不确定项}（≤ 3 条 · 评审中讨论 / 由各 Stage 入口承接）

📋 流程：{流程类型} · {N} Stage · {M} 暂停点 · 预计 {X-Y} h
   Feature: {feature_id}-{feature_name}

| # | Stage          | 一句话目标                       | 非默认                       |
|---|----------------|--------------------------------|------------------------------|
| 1 | Plan           | PM 精简 PRD → ⏸️                | 💡 +PL/codex,跳 Designer    |
| 2 | UI Design      | Designer 设计 → ⏸️             | —（仅 requires_ui=true 出现）|
| 3 | Blueprint      | RD TECH + QA TC                | —                            |
| 4 | Dev            | TDD 实现                        | —                            |
| 5 | Review         | 三视角并行 → ⏸️ QUALITY        | 💡 +codex (SSRF)            |
| 6 | Test           | 集成 + API E2E                  | —                            |
| 7 | PM 验收        | 三选一 → ⏸️                    | —                            |
| 8 | Ship           | push+MR → ⏸️ 合并 finalize     | —                            |

🔑 关键假设（错了改路径）：仅当存在路径分叉假设时输出 · ≤ 2-3 条

⏸️ 双对齐 + 环境处理（一次回复确认）：

| 回   | 含义                                                          |
|------|---------------------------------------------------------------|
| ok    | 采纳全部推荐 + 环境选 1 💡（如"工作区脏 → commit + 创 worktree"）|
| ok 2  | 流程采纳 + 环境选 2（探测异常时存在）                          |
| ok 3  | 流程采纳 + 环境选 3（探测异常时存在）                          |
| ok 4  | 取消启动                                                      |
| 反馈  | 自由文本（如 "A1 选 A" / "Review 跳 codex" / "切换流程"）     |

📎 详情走 state.json：knowledge_hits / relevant_adrs / available_roles / Real unknowns 详细 / execution_hints 完整 / 环境配置详情

🔄 PMO | {feature_id} (待创建) | triage | ⏸️
```

🔴 **意图段缩编硬规则（v7.3.10+P0-60 替代 P0-49 散文形态）**：
- Feature / 敏捷需求：`Why now / Assumptions / Real unknowns` 三行式（可省 Why now 当用户已知 · Assumptions ≤ 3 条 · Real unknowns ≤ 3 条 · 每条 ≤ 1 行）
- Bug：`症状 / 复现路径 / 影响范围 / 期望行为` 四行式（每行 ≤ 1 行）
- 问题排查：`症状 / 已知信息 / 排查目标` 三行式
- Micro：一行变更描述
- 整体意图段控制在 ≤ 8 行 · 越界 = 履职报告反模式

🔴 **骨架尾部一行硬约束（v7.3.10+P0-42 新增）**：
- 必含：Stage 总数 / 暂停点总数 / 预估耗时
- 不允许独立"骨架摘要"段（原段内容已机械可推算自骨架本身：Stage 数 = 数 stages 数组；暂停点数 = 数含 ⏸️ 的 stage；耗时 = 单独估算）
- 不允许在骨架后追加"BG 协调 ship"/"耗时数据来源"等额外提示段（这些是 PM 验收 / Stage 入口实例化的事，triage 不该越界）

🔴 **骨架字段契约（v7.3.10+P0-38-A）**：
- 必填：`stage` / `goal` / `key_outputs` / `pause_points`
- 可选：`execution_hints` (string | null)
  - **何时给 hint（有取舍时给）**：角色组合有取舍（Plan/UI Design/Blueprint/Review）/ 启用方式有特殊性（PL 优先 / external 用 codex）/ 跨 Stage 协调建议
  - **何时不给 hint（角色固定时不给）**：Dev/Test/PM 验收/Ship — 角色完全固定
  - **给 hint 必须含理由**："启用 X / 跳过 Y。理由：…"（不接受裸建议）
  - **动词约定**：评审 / 设计 / 实现 TDD / 测试 / 验收 / 净化+push+finalize
- goal / key_outputs / pause_points 必须来自 [stages/{stage}-stage.md](../stages/) 的 Output Contract（不允许 PMO 编造）

🔴 **Stage 入口对 hint 的硬约束**：
- execution_hints 存在 → 必读 + cite 原文 + 决策时参考
- 否决 hint → 必须在 *_substeps_config.hint_overrides 写文本说明原因
- execution_hints = null → 按 Stage spec 内置角色清单走标准流程

选项 2 进入二级决策：用户可调整某 Stage 的 execution_hints（如"Goal-Plan Stage 不要 external"）或剔除某 Stage（如"无 UI 变更，跳 ui_design"）。

📎 **与 *_substeps_config 的关系**：goal_plan_substeps_config / blueprint_substeps_config / review_substeps_config 是各 Stage **入口实例化**产物（不在 triage 决策），由 PMO 在该 Stage 入口基于已有上游产物 + execution_hints + 累积上下文决策具体 active_roles + execution + 评审循环参数 + hint_overrides（不一致时）。

#### 环境配置决策（v7.3.10+P0-27）

如 Step 7.5 探测显示**异常**（工作区脏 / 分支冲突），加环境配置决策点：

```
🛠 环境配置决策（探测发现 {异常类型}）：
1. 自动 stash 后继续 💡
2. 先 commit 当前工作区再继续
3. 强制继续（不推荐，未提交改动可能丢失）
4. 取消本次 Feature
```

如 Step 7.5 探测**正常**，环境配置不需要单独决策——按推荐配置自动应用。

### Step 9: 用户回数字 → 转入对应 Feature 级 Stage

```
用户确认骨架 → 创建 Feature 占位（首次写 state.json）：
  ├── state.flow_type = 用户选定流程
  ├── state.execution_plan_skeleton = {                    # v7.3.10+P0-38 新增
  │     version: 1,
  │     generated_at: <ISO 8601 UTC>,
  │     stages: [...]   # 用户确认的骨架（v7.3.10+P0-38-A：每个 Stage 含 goal / key_outputs / pause_points + 可选 execution_hints）
  │     amendments: []  # 各 Stage 入口的实例化 / 调整记录（追加写）
  │   }
  ├── state.external_cross_review = {                      # v7.3.10+P0-38 瘦身（删 *_enabled 三字段）
  │     model: "codex|claude|null",  # init Stage 已写
  │     host_main_model: "...",
  │     host_detection_at: "...",
  │     available_external_clis: [...],
  │     ... (其他元数据)
  │   }
  ├── state.preliminary_analysis_at = ISO 8601 UTC
  ├── state.environment_config = {     # v7.3.10+P0-27
  │     worktree_mode: "auto|manual|off",
  │     branch: "feature/F{编号}-{功能名}",
  │     merge_target: "staging",
  │     base: "origin/staging",
  │     workspace_status_at_triage: "clean|dirty",
  │     dirty_resolution: "stash|commit|force|null"
  │   }
  ├── state.change_id = "{change_id}|null"  # v7.3.10+P0-33
  └── state.current_stage = 该流程的第一个 Stage（如 Feature → "goal_plan"）

🔴 不在 triage 写的字段（v7.3.10+P0-38 重定位 / 延迟绑定）：
  ├── goal_plan_substeps_config       ← Goal-Plan Stage 入口实例化
  ├── blueprint_substeps_config  ← Blueprint Stage 入口实例化
  └── review_substeps_config     ← Review Stage 入口实例化

triage 仅写骨架（execution_plan_skeleton），不写各 Stage 的具体 substeps_config——这些字段由各 Stage 入口的 PMO 基于上游产物决策。

### 🔴 Step 9 state.json 写入硬清单（v7.3.10+P0-38-B 新增 / +P0-41 加 artifact_root）

triage Step 9 写 state.json 时，以下字段**必须全部包含**，缺一不可：

```
✅ 必含字段：
   ├── feature_id / sub_project / flow_type / current_stage / change_id      （基础元数据）
   ├── artifact_root                                                          （v7.3.10+P0-41 必含 / 路由权威）
   │   计算：teamwork_space.md 子项目表 docs_root 列 + Feature 全名
   │   例：app-frontend/docs/features/F059-HomeShortcutKeySync
   ├── available_roles[]                                                      （来自 Step 4 角色扫描）
   ├── execution_plan_skeleton.stages[]                                       （来自 Step 8 骨架决策）
   │   每个 Stage 含 stage / goal / key_outputs / pause_points + 可选 execution_hints
   ├── external_cross_review.{model, host_main_model, available_external_clis}  （来自 Step 4 元数据）
   ├── environment_config.{worktree_mode, branch, merge_target, base, workspace_status_at_triage}
   └── preliminary_analysis_at （ISO 8601 UTC）

🔴 PMO 校验硬规则：
   ├── 任一字段缺失 → 视为流程违规，不允许进入下一 Stage
   ├── execution_plan_skeleton.stages 至少含 1 个 Stage
   ├── 每个 stages[] 元素必含 stage / goal / key_outputs / pause_points 4 字段（execution_hints 可为 null）
   └── available_roles 至少含内部 6 角色（pl/rd/qa/designer/pmo/architect）
```

**违规示例（实战 case 反模式）**：

```
❌ state.json 仅含 feature_id / sub_project / flow_type / current_stage 等基础元数据
   缺 execution_plan_skeleton / available_roles / external_cross_review

   后果：
   ├── Goal-Plan Stage 入口无 execution_hints 可读 → 入口实例化无依据
   ├── 各 Stage 入口校验 active_roles ⊆ available_roles 无据可查
   └── external 角色启用判断退化为 PMO "凭感觉"决策，违反"延迟绑定 + 上下文驱动"原则
```

完成 Triage Stage，转入 Feature 级 Stage 链（**Goal-Plan Stage 入口直接自动执行环境准备，无暂停点**）。
```

---

## Output Contract

### 必须产出（主对话输出，不落盘）

| 段 | 描述 |
|----|------|
| 用户输入承接确认 | 显式响应（红线 #4） |
| 「📚 相关项目事实」段 | KNOWLEDGE 扫描结果（无命中显式标注） |
| 「📜 相关 ADR」段 | 历史决策扫描（如适用） |
| 「🌐 外部模型探测」段 | 探测脚本渲染 |
| 「流程类型识别」段 | 六种之一 + 理由 |
| 「跨 Feature 冲突检查」/「跨项目依赖识别」段 | 如适用 |
| 「流程步骤描述」段 | 阶段链 + 每阶段做什么 + 暂停点 |
| 「🛠 环境配置预检」段 | 仅 Feature / Bug / 敏捷需求 适用；探测 git 状态 + 计划行为表（v7.3.10+P0-27 新增） |
| 暂停点选项（流程确认 + 外部模型评审 + 环境配置异常决策） | 编号化 + 「其他指示」 |

### 用户确认后写入（仅此时持久化）

`{Feature}/state.json`（首次创建）：

```json
{
  "feature_id": "F{编号}-{功能名}",
  "flow_type": "feature | feature-planning | bug | issue-investigation | agile | micro",
  "external_cross_review": {
    "enabled": true | false,
    "model": "codex | claude | null",
    "host_main_model": "...",
    "host_detection_at": "...",
    "available_external_clis": ["..."],
    "decided_at": "...",
    "decided_by": "user",
    "note": "..."
  },
  "preliminary_analysis_at": "<ISO 8601 UTC>",
  "current_stage": "{该流程的第一个 Feature 级 Stage}",
  ...
}
```

### 机器可校验条件

- [ ] 用户输入承接段存在（红线 #4）
- [ ] KNOWLEDGE 扫描段存在（无命中显式"无命中"）
- [ ] 流程类型 ∈ 六种枚举（红线 #2）
- [ ] 流程步骤描述段存在 + 阶段数 ≥ 该流程定义的最小阶段数（红线 #15）
- [ ] 外部模型探测脚本调用成功（或显式 WARN，标注降级）
- [ ] 暂停点选项编号化 + 含「其他指示」最后项（红线 #9 + #18）
- [ ] 写操作未发生（红线 #10：未输出初步分析前禁止任何写）

🔴 静默跳过任一段（特别是 KNOWLEDGE 扫描和流程步骤描述）违反闭环验证红线。

---

## AI Plan 模式指引

📎 Execution Plan 3 行格式 → [SKILL.md](../SKILL.md#-ai-plan-模式规范v73-新增)。

本 Stage 默认 `main-conversation`（PMO 主对话执行）。**不需要** dispatch Subagent ——triage 是 PMO 自身的流程入口职责。

特殊场景：
- KNOWLEDGE.md 超大（>2000 行）→ PMO 仍主对话执行，可分段 Read（按需加载相关章节）
- 探测脚本失败 → 主对话 WARN + 默认禁用外部模型评审，不阻塞 triage
- 用户消息极简（如 `/teamwork status`）→ 跳过 triage，直接进入恢复流程

---

## 失败 / 异常处理

| 异常 | 处理 |
|------|------|
| 探测脚本调用失败（python3 不可用 / 脚本路径错） | WARN + 跳过外部模型评审决策点（默认 OFF） + 在 triage 输出标注降级 |
| KNOWLEDGE.md 不存在 | 跳过 KNOWLEDGE 扫描段（输出"项目尚未建立 KNOWLEDGE.md"），不阻塞 |
| 用户消息无法识别为六种流程之一 | PMO 主动反问澄清（最多 1 轮），仍不能识别 → 默认走 Feature 流程并显式标注"按 Feature 流程处理，如有偏差请回退" |
| 跨 Feature 冲突 | 显式列出冲突项，让用户在暂停点决策（修当前 / 先修冲突的 / 等冲突 Feature 完成） |

---

## 与其他 Stage / 文件的关系

| 文件 | 关系 |
|------|------|
| [stages/init-stage.md](./init-stage.md) | 上游 Stage（会话级），triage 进入前必完成 |
| [roles/pmo.md](../roles/pmo.md) | PMO 角色规范，本 Stage 是 PMO 工作单元 |
| [FLOWS.md](../FLOWS.md) | 流程总览，原"PMO 初步分析输出格式"段已迁移到本文件 |
| [RULES.md](../RULES.md) 红线 #4 / #10 / #15 | 本 Stage 是这三条红线的契约化承载 |
| [standards/external-model.md](../standards/external-model.md) | Step 4 探测脚本调用规范 |
| [standards/prompt-cache.md](../standards/prompt-cache.md) | Step 1-4 Read 顺序遵守 R2 规则 |
| [templates/detect-external-model.py](../templates/detect-external-model.py) | Step 4 直接调用 |

---

## 执行报告模板（主对话输出，不落盘）

🟢 **v7.3.10+P0-49-A 输出哲学：决策呈现，不是履职报告**

triage 输出的核心是给用户**决策依据**，不是 PMO 履职汇报。规则：

```
✅ 用户必看（Tier 1，永远输出）：
  ├── 意图理解段（Why now / Assumptions / Real unknowns 等按流程分形态）
  ├── 流程承诺骨架（启用 Stage + 关键非默认决策）
  └── ⏸️ 双对齐暂停点

🟡 命中 / 异常才输出（Tier 2，默认折叠）：
  ├── KNOWLEDGE 命中（仅在 Gotcha/Convention 命中时一行摘要 + 详情可查 state.json）
  ├── ADR 命中（仅在历史决策与本 Feature 相关时输出）
  ├── 跨 Feature 冲突 / 跨项目依赖（仅在有冲突 / 依赖告警时输出）
  └── 环境异常（仅在工作区脏 / path 偏离规范时一行摘要）

❌ 默认不输出（Tier 3，全部走 state.json）：
  ├── 角色可用性扫描（无异常时不输出；异常如 external 不可用时一行说明）
  ├── 流程类型识别（除非 PMO 不确定，否则识别结果直接体现在 Feature 骨架顶部，不立独立段）
  ├── worktree mode / path / artifact_root 详细复述（state.json 已存，主对话不复述）
  ├── 探测脚本输出原文（state.json 已存）
  └── "无变更归属" / "无 ADR" 等空段（不存在就不输出）
```

🔴 **关键反模式**（必须杜绝）：

```
❌ 履职报告体感（"我做了 N 件事"列表式）：
   PMO 把扫了 KNOWLEDGE / 扫了 ADR / 扫了角色 / 识别了流程 / 查了冲突 / 探测了环境 全部立段。
   即使没命中也立"无 ADR" / "无冲突" 段。
   用户最关心的意图段被推到第 7 段。
   → 用户认知负担 = 9 段平铺，没法快速找到决策点。

❌ state.json 复述表（违反 P0-48 红线）：
   把 worktree mode / path / sub_project / artifact_root 等机读字段以"维度: ... 值: ... 计划行为: ..."
   表格形态在主对话渲染。
   → state.json 已存，主对话再述 = padding。

❌ 5 选 1 决策菜单（违反 P0-49 双对齐姿态）：
   把"ok / 反馈"二选一退化为"1. 意图反馈 / 2. 调整骨架 / 3. 拍板 unknown / 4. 切流程 / 5. 其他"。
   用户必须先选编号才能反馈。
   → 决策疲劳。"反馈"应该是自由文本入口，PMO 解析时分类，不让用户先选。
```

---

### 标准输出形态（v7.3.10+P0-49-A）

```
📋 我对你需求的理解（不落盘 · 待你 ok）

Why now
{1-3 句话：核心因由 + 时间约束（如 24h 观测期）+ 上游/下游关联}

Assumptions
- {🔴 关键假设 1：错了 Feature 重做的级别}
- {🔴 关键假设 2}
- {假设 3：影响一般的}
（关键假设标 🔴；普通假设不标。总数 2-4 条，不全部列）

Real unknowns（评审讨论 / 现在拍板都行）
1. {真正不确定点 1}
2. {真正不确定点 2}
3. {真正不确定点 3}
（数量 1-3 条；多了说明意图本身没想清楚，回去跟用户对齐）

📋 流程承诺骨架（{流程类型} · {N} Stage · {跳过的 Stage 注明} · {M} 暂停点 · 预计 {X-Y} min/h）

Stage 1 Plan        {一句话目标}
                    💡 {仅非默认决策} 启用 X / 跳过 Y。理由：{cite 关键信号}

Stage 2 Blueprint   {一句话目标}
                    💡 {仅非默认决策，如 触发 ADR / 启用 external} 理由：{cite 信号}

Stage 3 Dev         {一句话目标}（默认推荐 → 一行带过，不展开）
Stage 4 Review      💡 {仅非默认决策，如 启用 external} 理由：{cite 信号}
Stage 5 Test        {一句话目标}（默认 → 一行带过；如 24h 时窗约束才标 💡）
Stage 6 PM 验收     {一句话目标}（标准 → 一行带过）
Stage 7 Ship        💡 {仅非默认约束，如 24h 时窗 / 协调 ship 时间窗} 理由：{cite 信号}

[折叠区 · 命中 / 异常才输出]

📚 KNOWLEDGE {N+M} 命中（一行摘要：{最关键 1 条 + N 条详情可查 state.json}）
📜 ADR {N} 命中（一行摘要：{命中 ADR 编号 + 一句话相关性}）
⚠️ 跨 Feature 冲突告警：{一行说明 + 处理路径见 Real unknown #N}
🛠 环境异常：{一行说明，如 "worktree path 偏离规范 + CLAUDE.md 脏文件 → worktree 隔离规避"}

[决策点]

⏸️ 双对齐

回 ok = 全部采纳推荐 → 写 state.json + 建任务目录 + 进入下一阶段
回反馈 = 自由文本（如 "意图段 Assumption 错了"/"#3 选 b"/"骨架跳过 X Stage"/"切流程改成敏捷需求"/...）
PMO 解析反馈类型：意图偏差 / 骨架调整 / unknown 拍板 / 切流程，按需修订后重新呈现。
```

---

🔴 **输出形态硬约束（v7.3.10+P0-49-A）**：

- **意图段必须最前**：用户最关心的"PMO 懂没懂我"是触发拍板的核心，物理位置在 Tier 2/3 任何履职报告之前
- **Tier 2 段默认折叠**：KNOWLEDGE / ADR / 跨 Feature 冲突 / 环境异常 仅在命中或异常时输出一行摘要，详情可查 state.json
- **Tier 3 段不输出**：角色可用性扫描结果 / 流程类型独立识别段 / worktree path 等机读字段，绝对不在主对话渲染（state.json 是真相源）
- **Feature 骨架默认 Stage 一行带过**：Dev / PM 验收 / 默认配置的 Stage 单行不展开理由；仅 💡 非默认决策行展开 cite 关键信号
- **双对齐回到二选一姿态**：ok 或自由反馈，禁止 1/2/3/4/5 编号菜单（菜单 = 用户先选编号才能反馈 = 决策疲劳）

🔴 **保留的硬约束**（来自 P0-38-A / P0-42 / P0-49）：

- 不允许独立"流程步骤描述"段（已合并到 Feature 骨架，P0-42）
- 不允许独立"外部模型评审决策"段（已并入骨架的 execution_hints，P0-38）
- 不允许追加"BG 协调 ship 提示"等越界段（PM 验收的事 / Stage 入口实例化的事，P0-42）
- 不允许把"双对齐"拆成两次单对齐暂停（P0-49）
- 不允许在 triage 列产品决策选项（业务方向 / 技术方案 / UX 细节，P0-38-B / P0-49）
