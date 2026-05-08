# PMO 状态机维护详规范（PMO State Mgmt · v7.3.10+P0-96 抽出）

> 🔗 **角色契约见 [roles/pmo.md](./pmo.md)**（PMO 项目管理 + 调度协调）。本文件是 PMO 路径路由 + state.json 状态机维护 + 自下而上影响升级三大状态/数据职责的详细任务规范 · 是该任务的**权威源**。
>
> 本文件源流：原寄生在 roles/pmo.md 三段 → **v7.3.10+P0-96 抽出本文件**（pmo.md 1018 → ~775 向 ~500 cap 推进 · Wave 4 Phase 4）。
>
> 适用场景：
> - **§ 一 PMO 产物路径权威路由**（v7.3.10+P0-41）：sub_project 写到 state.json 时强制 artifact_root 路由
> - **§ 二 state.json 状态机维护**（v7.3.2 / +P0-23 / +P0-52）：流转前/进入 Stage 前/Stage 结束三时机 + R3 访问模式 + 增量更新
> - **§ 三 自下而上影响升级评估**：PM/RD 标记上游影响时 PMO 评估升级路径
>
> 🔗 相关单源：
> - [templates/feature-state.json](../templates/feature-state.json)（state.json 模板权威）
> - [standards/prompt-cache.md § 四](../standards/prompt-cache.md)（R3 访问模式硬规则）
> - [templates/state-patch.py](../templates/state-patch.py)（增量补丁脚本）
> - [RULES.md § state.json 维护硬规则](../RULES.md)（patch.py > Edit）
> - [templates/teamwork-space.md](../templates/teamwork-space.md)（docs_root 列权威源）

---

## 一、PMO 产物路径权威路由（v7.3.10+P0-41 新增）

> **触发场景**：实战 case 暴露 AI 把 sub_project=FE 的 Feature 文档写到根 `docs/features/` 而非 `app-frontend/docs/features/`——sub_project 字段写到 state.json 但路由没强制。

### 1.1 路由计算流程

```
triage Step 9 写 state.json 时计算 artifact_root：

1. Read teamwork_space.md「子项目清单」表
2. 找 sub_project 对应行的 docs_root 列
   例：sub_project=FE → docs_root=app-frontend/docs/features
3. artifact_root = {docs_root} + "/" + {Feature 全名}
   例：app-frontend/docs/features/F059-HomeShortcutKeySync
4. 写入 state.json.artifact_root
```

🔴 **路由权威硬规则**：

```
✅ 唯一权威：teamwork_space.md 子项目表 docs_root 列
   ├── PMO 不允许"沿用历史根 docs/features/"等理由偏离 docs_root 列
   ├── docs_root 列缺失 → triage 阻断 · 提示用户先补全
   └── 单子项目模式（无 teamwork_space.md）→ artifact_root = docs/features/{Feature 全名}

❌ 禁止反模式：
   ├── 把 sub_project=FE 写入 state.json 但产物落在根 docs/features/（路由失效）
   ├── 用"仓库历史功能在根 docs/features/"作为偏离理由
   └── PMO 在 Goal-Plan Stage 入口跳过 artifact_root 校验直接 Write PRD.md
```

### 1.2 历史 Feature 兼容处理（旧 Feature 在根 docs/features/）

```
v7.3.10+P0-41 之前的 Feature（在根 docs/features/）：
  - 状态：保留原位置不强制迁移（state.json.artifact_root 是历史快照）
  - 后续操作：在原 artifact_root（根 docs/features/...）下继续读写
  - 不阻塞新 Feature 走新 artifact_root（子项目 docs/features/）

新建 Feature：
  - 强制按 teamwork_space.md docs_root 列计算 artifact_root
  - 缺 docs_root 列 → 阻断 + 用户先补全
```

### 1.3 PMO 校验时机（与 RULES.md「写操作前路径硬门禁」配合）

```
1. triage Step 9 写 state.json 前：计算 artifact_root + 校验 docs_root 列存在
2. Goal-Plan Stage 入口实例化后 / 子步骤 1 开始前：第一次 Write 前校验路径前缀
3. 每次 Edit/Write Tool 调用前：repeat 校验（防中途路径漂移）
4. 每次 Stage 切换时：再次校验
```

🔴 PMO 校验失败时输出格式（标准化）：

```
❌ 写操作硬门禁拦截

文件路径：{intended_path}
预期前缀：{state.artifact_root}（来自 teamwork_space.md docs_root + Feature 全名）
当前 pwd：{pwd}
预期 pwd：{state.worktree.path}（worktree_mode = {mode}）

违规原因：{路径不在 artifact_root 下 / pwd 不在 worktree.path}
正确做法：
  ├── 切到 worktree：cd {state.worktree.path}
  └── 写到正确路径：{state.artifact_root}/{filename}

记录：state.concerns 加 BLOCK 条目；流程暂停等用户决策。
```

📎 与 P0-38-B Step 9 state.json 写入硬清单的关系：Step 9 保证 state.json 含 artifact_root；本规则在每次 Write/Edit 时校验文件路径与字段一致性。

---

## 二、state.json 状态机维护规范（v7.3.2）

> 🔴 **PMO 是 state.json 的唯一维护者**。所有流转状态变更必须反映到 state.json。
>
> 模板见 [templates/feature-state.json](../templates/feature-state.json)。
>
> 位置：`{子项目}/docs/features/{功能目录}/state.json`（与 PRD/TC/TECH 同目录）
>
> 🟢 v7.3.2：state.json 替代 STATUS.md 成为 Feature 目录唯一状态文件。STATUS.md 已废弃。

### 2.1 流转前必做（每次阶段变更都要做）

```
1. Read {Feature}/state.json
2. 校验：target_stage ∈ legal_next_stages ？
   ├── 是 → 继续
   └── 否 → 🔴 阻塞 · 输出原因："目标阶段 {X} 不在合法下一步 {legal_next_stages} 中"
3. 校验：stage_contracts[current_stage] 三项（input/process/output）全 satisfied ？
   ├── 是 → 继续
   └── 否 → 🔴 阻塞 · 输出未满足的契约项
4. 校验：blocking.pending_user_confirmations 为空？
   ├── 是 → 继续
   └── 否 → 🔴 必须先处理 pending 项
```

### 2.2 进入 Stage 前必做

```
1. AI 在主对话输出 Execution Plan 块（3 行核心：Approach / Rationale / Role specs loaded）
2. PMO 写入 state.json.planned_execution[stage]
3. 启动对应执行路径：
   ├── approach: main-conversation → 主对话执行（走主对话产物协议 §六）
   ├── approach: subagent → 生成 dispatch 文件 → dispatch Subagent
   │    └── 🔴 Feature 产物白名单硬校验（v7.3.9+P0-12 新增）
   │        PMO 生成 dispatch 前必须按 `templates/dispatch.md § Feature 产物强制白名单` 逐项判断：
   │        Dev Stage + `state.stage_contracts.ui_design.output_satisfied==true`
   │        → Input files 必须显式包含 `{Feature}/UI.md` + `{Feature}/preview/*.html`
   │        → 缺项 → **PMO 自拒重生**（不得发出）
   │        Review / Test / Browser E2E 亦同 · 按白名单逐项对照
   └── approach: hybrid → 按 steps 逐项分配
4. 更新 stage_contracts[stage].input_satisfied = true + started_at
```

### 2.3 Stage 结束必做

```
1. 运行 Output Contract 机器校验
   ├── 测试命令 exit 0？
   ├── 产物文件存在且格式合规？
   └── AC 覆盖校验通过（python3 {SKILL_ROOT}/templates/verify-ac.py）？
1.5. 🔴 事实字段 evidence-binding 完整性校验（v7.3.10+P0-101 新增 · SKILL.md 红线 R7）
   ├── 校验本 Stage 写入的事实字段是否含 evidence binding 子对象
   ├── 失败任一 = 流程违规 · 阻断 Stage 出口（不得 Write · 不得流转）
   ├── 详见下方 § 2.4「事实字段 evidence-binding 出口校验」
   └── 自检清单：available_external_clis / mr_url / feature_pushed_at / tests_passed / pm_self_check.code_context_read
2. 所有机器校验通过 → stage_contracts[stage].output_satisfied = true
   任一失败 → ⚠️ 返回失败原因 · 不得流转
3. 更新 completed_stages、legal_next_stages（按 flow-transitions 重算）
4. Append 一行到 review-log.jsonl（含 executor 字段）
5. 追加一条到 executor_history
6. Write state.json
7. 更新 ROADMAP.md 对应 Feature 行的"当前阶段"列
```

### 2.4 state.json 访问模式约束（v7.3.10+P0-23 新增 · prompt cache 友好）

> 🔴 **R3 硬规则** — 详见 [standards/prompt-cache.md § 四](../standards/prompt-cache.md)。
> 每个 Stage 内 state.json 访问次数严格限制 · 目的：让 state.json（动态内容）始终位于 prompt 前缀**末尾** · 前面所有稳定层（roles/templates/Feature 既有产物）可被宿主隐式 cache 命中。

| 时机 | 操作 | 次数 | 约束说明 |
|------|------|-----|---------|
| Stage 入口 | Read | 1 | 与入口 Read 顺序 Step 4 对齐 |
| Stage 中段 | Read/Write | 0 | 🔴 绝对禁止 · 违反 = 流程偏离 |
| Stage 出口 | Read | 1 | Write 前对齐最新状态 |
| Stage 出口 | Write | 1 | 汇总变更 + executor_history |

**豁免列表**（满足条件才允许突破"中段 0 次"）：

- **内部评审修复循环**（Blueprint TC/TECH 评审 / Review fix 循环）：每轮修复结束时 1 次 Write · 🔴 至多 3 轮
- **Subagent dispatch 产出整合**：每次 dispatch 整合后 1 次 Write · 🔴 每次 dispatch 至多 1 次
- **用户显式追加需求导致 Stage 内部重走**：Read + Write 各 1 次 · 🔴 必须先走 PMO 分析 + 用户确认

**量化上限**：
- 常规 Stage：state.json 访问 ≤ 5 次（2 Read + 1 Write + 2 次豁免缓冲）
- 复杂修复循环：≤ 8 次 · 需在 `state.concerns` 明确记录理由
- 超过 8 次 = 流程偏离 · 🔴 必须记入 concerns

**反模式**：
- ❌ 每个 Step 开头 Read state.json 确认状态 → 🔴 入口 1 次 Read 后 · 中段状态保持在主对话上下文
- ❌ 每写一个字段 Write 一次 → 🔴 出口 1 次 Write 汇总
- ❌ "保险起见再 Read 一次" → 🔴 违反 R3；review 上下文而非重读文件
- ❌ 中段遇到不确定 → Read 兜底 → 🔴 不确定 = 暂停点问用户 · 不是读文件

#### 事实字段 evidence-binding 出口校验（v7.3.10+P0-101 新增 · SKILL.md 红线 R7）

> 🔴 **触发**：Stage 出口 Read 之后、Write 之前，PMO 必须执行本校验。失败 = 流程违规 = 阻断 Stage 出口。
> 🔴 **目的**：物理拦截"凭印象生成事实字段"反模式（详见 SKILL.md 红线 R7 实战触发 case）。

**事实字段范围**（来自外部观察 · 含否定 / 空集 / 不可用 / 不存在 / 0 命中等声明）：

| 字段路径 | evidence schema | 必填条件 |
|---------|----------------|---------|
| `external_cross_review.available_external_clis` | `detection_evidence = { command, stdout, exit_code, detected_at }` | Triage Step 4 探测后必填 |
| `ship.feature_pushed_at` / `ship.merge_target_pushed_at` | `*_push_evidence = { command, stdout, exit_code, pushed_at }` | Ship Stage push 后必填 |
| `ship.mr_url` + `ship.mr_creation_method` | `mr_creation_evidence = { method, command/url, stdout 或 user_visited_url, created_at }` | Ship Stage MR 创建后必填 |
| `tests_passed` / 各阶段测试断言 | 命令 stdout 原文 + exit code（落 review-log.jsonl） | 任何"已通过"声明必填 |
| `pm_self_check.code_context_read` | 实际读取证据（grep 历史 ToolUse 可验） | PM 验收输出 self-check 必填 |

**校验步骤**（PMO 在 Stage 出口 Read state.json 之后执行）：

```
for field in 本 Stage 写入的事实字段:
    if field 在事实字段范围:
        if field._evidence 缺失 OR field._evidence.stdout 为空 OR command 字段缺失:
            → 🔴 阻断 Stage 出口
            → 主对话输出违规告警："字段 {path} 缺 evidence binding · 请补 bash 实测 + 写入 state.json stdout 字段（v7.3.10+P0-112：物理拦截层级 = state.json · 不要求主对话 verbatim）"
            → 不得执行 § 2.3 Step 6 Write
            → 状态保持当前 Stage · 等待补证据后重走出口
```

**违规处置**：

- **PMO 自检发现**：立即在主对话告警 + 列出缺 evidence 的字段清单 + 给出补救命令模板（bash 实测 + 写入 state.json stdout 字段 · v7.3.10+P0-112）· 不得 Write · 不得流转
- **用户/外部反馈发现**（事后）：作为 Bug 流程处理（PMO 起 Bug · 走 fix→ship 简化流程 · evidence 补全后回写）

**反模式**（v7.3.10+P0-101 实战触发 case）：

- ❌ `available_external_clis: []` 但无 `detection_evidence` → 物理拦截：贴 `command -v codex` 完整 stdout + exit code
- ❌ `mr_url: "https://..."` 但无 `mr_creation_evidence` → 必填 method（cli/url-fallback）+ 实际命令或访问 URL
- ❌ `feature_pushed_at: "2026-05-05T..."` 但无 push stdout → 必填 `git push` 命令的 stdout（含 remote ref 行）
- ❌ "我看了一下没有" / "印象中应该是" → 🔴 这些是状态字段思维 · 事实字段必须 bash 实测后贴原文

**与状态字段的边界**：

- **状态字段**（PMO 自判状态机 · 不在本红线范围）：current_stage / phase / verdict / completed_stages / legal_next_stages / output_satisfied
- **事实字段**（来自外部观察 · 必须 evidence binding）：见上表
- 区分原则：能由外部命令验证真伪的 = 事实字段 · PMO 内部状态机推导的 = 状态字段

### 2.5 state.json 增量更新（v7.3.10+P0-52）

> 🔴 **单源**：[RULES.md § state.json 维护硬规则](../RULES.md) + [templates/state-patch.py](../templates/state-patch.py)
>
> 出口 Write 优先用 `state-patch.py` 增量补丁（只发送 diff + 校验）· 避免整文件复述。

### 2.6 state.json 与现有文件的关系

| 文件 | 职责 | 关系 |
|------|------|------|
| `{Feature}/state.json` | **机读权威源 + 单 Feature 详情**（v7.3.2 起）| PMO 维护 |
| `{Feature}/review-log.jsonl` | 历史流水审计 | state.json 流转时 append |
| `{Feature}/dispatch_log/INDEX.md` | Subagent dispatch 汇总 | 独立 · 不重复 |
| `ROADMAP.md` | **全局人读视图**（Feature 清单 + 当前阶段列）| PMO 流转时同步 |

🟢 **v7.3.2 简化**：Feature 状态不再双源维护。

- 人想看全局 → `ROADMAP.md`
- 人想看某 Feature 详情 → 直接打开 `{Feature}/state.json`（JSON 格式化后可读）
- AI 恢复状态 → 同上

### 2.7 Compact 恢复规则

新对话启动或 compact 后：

1. PMO 第一件事：读 `{Feature}/state.json`（如果有当前 Feature）
2. 基于 state.json 判断当前位置 / 合法下一步 / 未满足的契约
3. （可选）和 `rules/flow-transitions.md` 交叉校验 legal_next_stages

🟢 v7.3.2 起 state.json 是 Feature 状态的单一权威 · 不再需要与 STATUS.md 交叉校验。

### 2.8 遇到遗留 STATUS.md 文件（v7.2/v7.3 迁移）

- 不删已有 STATUS.md（保留历史）
- PMO 不再更新它
- state.json 不存在而 STATUS.md 存在 → PMO 基于 STATUS.md 信息初始化 state.json · 然后忽略 STATUS.md

---

## 三、自下而上影响升级评估

**触发**：PM 或 RD 在 Feature 流程中标记了「⚠️ 上游影响」

### 3.1 PMO 评估流程

```
收到「⚠️ 上游影响」标记
    ↓
PMO 读取影响描述 · 评估影响层级：
    ↓
┌─────────────────────────────────────────────────────────┐
│ 仅影响 ROADMAP（同子项目内）                              │
│ ├── 输出评估：影响范围 + 建议选项                          │
│ └── ⏸️ 用户选择：                                        │
│     ├── A. 调整当前 Feature 范围（在现有框架内完成）        │
│     └── B. 启动子项目级 Feature Planning                  │
├─────────────────────────────────────────────────────────┤
│ 影响 teamwork_space（跨子项目依赖）                        │
│ ├── 输出评估：影响范围 + 涉及子项目 + 建议选项              │
│ └── ⏸️ 用户选择：                                        │
│     ├── A. 仅调整依赖关系（更新 teamwork_space.md）        │
│     └── B. 升级为 Workspace Planning                      │
├─────────────────────────────────────────────────────────┤
│ 影响执行手册（Level 2）                                    │
│ ├── 输出评估：影响范围 + 受影响执行线 + 建议选项             │
│ └── ⏸️ 用户选择：                                        │
│     ├── A. 不升级 · 调整当前 Feature 范围                  │
│     └── B. 升级 → 切换 Product Lead（讨论模式）            │
├─────────────────────────────────────────────────────────┤
│ 影响业务架构 / 产品定位（Level 3）                          │
│ ├── 输出评估：影响范围 + 产品层面影响分析 + 建议选项         │
│ └── ⏸️ 用户选择：                                        │
│     ├── A. 不升级 · 在现有架构内妥协（记录设计决策）         │
│     └── B. 升级 → 切换 Product Lead（讨论模式）            │
└─────────────────────────────────────────────────────────┘
```

### 3.2 升级评估输出格式

```
📋 PMO 上游影响评估
====================

## 来源
├── 触发角色：PM / RD
├── 当前 Feature：[子项目缩写]-F{编号}-[功能名]
├── 触发阶段：[PRD 编写 / 技术方案 / 开发中]
└── 原始标记：[引用 PM/RD 的上游影响描述]

## 影响评估
├── 影响层级：ROADMAP / teamwork_space / 执行手册(L2) / 业务架构(L3)
├── 影响描述：[PMO 评估后的完整影响分析]
└── 受影响范围：[具体子项目/执行线/文档]

## 选项
├── A. [不升级方案描述 + 代价说明]
└── B. [升级方案描述 + 预计影响范围]

## 当前 Feature 状态
└── ⏸️ 已挂起 · 等待用户决策

---
⏸️ 请选择处理方式后继续。
```

### 3.3 PMO 升级评估约束

```
├── PMO 只评估影响级别和列出选项 · 不替用户做升级决策
├── 必须同时提供「不升级」和「升级」两个选项
├── 不升级时必须说明代价（如：需要在 Feature 内做妥协）
├── 升级时必须说明预计影响范围
├── 当前 Feature 必须先挂起再评估 · 不能边开发边升级
└── 用户选择不升级时 · PMO 确保 PM 在 PRD 中记录设计决策/妥协
```
