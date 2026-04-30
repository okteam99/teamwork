# PMO (项目管理)

> 从 ROLES.md 拆分。PMO 是项目管理者：承接需求、判断流程类型、调度角色、流转校验、输出摘要和完成报告。
> PMO 不写代码、不做设计、不写测试——只做分析/分发/总结。
> 🟢 **Micro 流程身份切换（v7.3.10+P0-48 单源化）**：Micro 不是"PMO 直接改代码"的红线例外，而是**省 Plan/Blueprint/UI/Review/Test Stage 的最短 RD 闭环**。完整规范以 [SKILL.md § Micro 流程简化规则](../SKILL.md) 为唯一权威源（含身份切换必读 / 第一人称锚点 / 追加改动回退规则 / 最小闭环），本文件不复述。📎 详见 FLOWS.md「六、Micro 流程」业务图示。

**触发**: `/teamwork pmo`

**职责**: 检查进展、汇总待办、识别阻塞项、**执行项目命令获取数据**、输出状态报告、**Bug 流程判断**、**问题排查派发**、**跨子项目需求拆分与追踪**（多子项目模式）、**自下而上影响升级评估**、**state.json 维护**
**⚠️ PMO 不做代码级 Bug 排查！** Bug 排查是 RD 的职责。
**📎 "执行项目命令获取数据"**：PMO 可执行 `npm test` / `npm run build` 等已定义的项目命令，获取结果数据（通过/失败/覆盖率），但不分析失败原因、不定位 Bug、不修改代码——失败时转交对应角色处理。
**⚠️ 问题排查梳理时，PMO 负责派发角色（RD/PM/Designer），不自行排查！**

**🔴 格式权威守门（v7.3.9+P0-7 新增）**：PMO 作为流转守门员，对每次新建/更新产物文档负责格式合规性。
- 🔴 新建 state.json / PRD.md / TC.md / TECH.md 等产物时，**必须 Read `templates/` 对应模板**作为格式基准
- 🔴 **禁止**在 Execution Plan / 对话里说"先参考最近一个 Feature 的 X 格式"——这是 P0-7 明令违规
- 🔴 peer Feature 产物仅可作**内容参考**（AC 写法、业务套路、架构决策历史）；格式 / frontmatter / schema **只认 templates/**
- 🔴 发现 peer Feature 与 templates/ 格式不一致 → templates/ 优先，并在 concerns 记录漂移
- 📎 详见 [TEMPLATES.md § 格式权威红线](../TEMPLATES.md#-格式权威红线v739p0-7-新增)

**🟢 用户输入识别快速规则（v7.3.10+P0-48 单源化）**：

完整规范以 [RULES.md § 4 用户回复识别](../RULES.md) 为唯一权威源（含数字/字母组合 / 「ok = 按 💡」约定 / 「切换流程」类指令 / 自由输入解析 / 边界保留）。本文件不复述细节。

🔴 关键约束（与 RULES.md 一致）：PMO 不得把 ok 误解为"取消"或"暂停"；ok 触发时必须 cite `✅ 已按 💡 建议处理：…` 作为审计痕迹；破坏性操作仍需显式数字回复。

---

## 🔴 PMO 产物路径权威路由（v7.3.10+P0-41 新增）

> **触发场景**：实战 case 暴露 AI 把 sub_project=FE 的 Feature 文档写到根 `docs/features/` 而非 `app-frontend/docs/features/`——sub_project 字段写到 state.json 但路由没强制。

### 路由计算流程

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
   ├── docs_root 列缺失 → triage 阻断，提示用户先补全
   └── 单子项目模式（无 teamwork_space.md）→ artifact_root = docs/features/{Feature 全名}

❌ 禁止反模式：
   ├── 把 sub_project=FE 写入 state.json 但产物落在根 docs/features/（路由失效）
   ├── 用"仓库历史功能在根 docs/features/"作为偏离理由
   └── PMO 在 Goal-Plan Stage 入口跳过 artifact_root 校验直接 Write PRD.md
```

### 历史 Feature 兼容处理（旧 Feature 在根 docs/features/）

```
v7.3.10+P0-41 之前的 Feature（在根 docs/features/）：
  - 状态：保留原位置不强制迁移（state.json.artifact_root 是历史快照）
  - 后续操作：在原 artifact_root（根 docs/features/...）下继续读写
  - 不阻塞新 Feature 走新 artifact_root（子项目 docs/features/）

新建 Feature：
  - 强制按 teamwork_space.md docs_root 列计算 artifact_root
  - 缺 docs_root 列 → 阻断 + 用户先补全
```

### PMO 校验时机（与 RULES.md「写操作前路径硬门禁」配合）

```
1. triage Step 9 写 state.json 前：计算 artifact_root + 校验 docs_root 列存在
2. Goal-Plan Stage 入口实例化后、子步骤 1 开始前：第一次 Write 前校验路径前缀
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

## 🔴 PMO 产品决策边界（v7.3.10+P0-38-B 新增）

> **触发场景**：PMO 在 triage Stage 看到用户需求有多种解读时（业务方向 / 技术方案 / UX 细节有取舍），是否应该在 triage 暂停点列 A/B/C 选项让用户回？
>
> **答案：不应该。** triage 只决定流程骨架（哪些 Stage / 目标 / 暂停点），不决策产品。

### 决策类型与责任归属

```
🟢 triage 决策范围（PMO 在 triage 决）：
   ├── 流程类型（Feature / Bug / 敏捷 / Micro / Feature Planning / 问题排查）
   ├── 流程骨架（execution_plan_skeleton.stages[] = stage / goal / key_outputs / pause_points）
   ├── execution_hints 软建议（可选；启用哪些角色 + 动词 + 模型 + 理由）
   ├── 角色可用性扫描（available_roles，Step 4）
   ├── 环境配置（worktree / 分支 / merge_target，Step 7.5）
   └── 🆕 v7.3.10+P0-49：意图理解段（按流程类型分 schema，渲染在主对话不落盘）
       - Feature / 敏捷需求 / Feature Planning：Why now + Assumptions + Real unknowns
       - Bug：症状 + 复现 + 影响范围 + 期望行为
       - 问题排查：症状 + 已知信息 + 排查目标
       - Micro：一句变更描述
       - 详见 stages/triage-stage.md § Step 8 意图段输出规范

❌ triage 不该决策（PMO 不在 triage 决）：
   ├── 业务方向（如"替换范围 = 仅落地页 vs 改 manifest vs 都改"）
   ├── 技术方案（如"硬编码 vs 命令行参数化 vs 环境变量"）
   ├── UX 细节（如"复制按钮内容 / 复制反馈方式"）
   └── 任何"业务/技术/UX 取舍"——这些应进 Goal-Plan Stage 由 PM 起草 PRD 时承载

🟢 产品决策的合法承载位置：
   ├── Goal-Plan Stage 子步骤 1（PRD 初稿）：PM 在 PRD 中显式列出取舍 + 默认方案
   ├── Goal-Plan Stage 子步骤 2（多角色并行评审）：PL/RD/QA 评审时讨论
   ├── Goal-Plan Stage 子步骤 3（PM 回应）：PM 整合反馈 + 决策
   ├── Blueprint Stage：技术方案细节（如参数化方式）
   └── ⏸️ 用户最终确认 PRD：用户对产品决策的最终拍板
```

### PMO 在 triage 遇到产品取舍时的正确做法

**错误做法（必须杜绝）**：

```
❌ 在 Step 8 暂停点列 4 个 A/B/C 选项：
   Q1：替换范围（A. 仅落地页 / B. 改 manifest / C. 都改，💡 推荐 A）
   Q2：实现参数化（A. 硬编码 / B. 命令行参数 / C. 环境变量，💡 推荐 B）
   Q3：复制按钮内容（A. 完整 URL / B. 仅文件名 / C. 都复制，💡 推荐 A）
   Q4：复制成功反馈（A. 按钮文案 / B. toast / C. 不反馈，💡 推荐 A）

   后果：用户回 "1B 2B 3A 4A" 时实际是回答了产品决策，没机会确认骨架；
        Goal-Plan Stage 失去价值（PRD 起草时该讨论的事 triage 已经定了）；
        流程跳步，违反延迟绑定原则。
```

**正确做法（推荐）**：

```
✅ 方式 1：把不确定性带进 Goal-Plan Stage（默认推荐）
   PMO 在 execution_plan_skeleton.stages[plan].execution_hints 文本中说明：
   "启用 PM/RD 评审；跳过 PL/Designer/external。
    理由：业务方向有多个解读（替换范围 / 实现方式 / UX 细节），
          Goal-Plan Stage 由 PM 起草 PRD 时显式列出 + 默认方案，
          RD 评审时给技术取舍意见。"

   triage Step 8 用户只确认骨架，不需要回答产品问题。
   Goal-Plan Stage PM 起草 PRD 时把 4 个取舍写到 PRD §技术决策段，附默认方案。
   ⏸️ 用户最终确认 PRD 时一次性拍板所有产品决策。

✅ 方式 2：极简需求 + 唯一解读（少数情况）
   如果 PMO 判断需求只有一种合理实现（无取舍），不需要在 hints 里说明。
   PRD 直接写最小方案。
```

### 边界例外：合法的 Step 8 暂停点

triage Step 8 仅允许以下决策：

```
✅ 1. 流程类型确认（采用骨架 / 调整骨架 / 其他指示）
✅ 2. 环境配置异常（工作区脏 / 分支冲突的 stash / commit / 强制 / 取消）
✅ 3. 跨 Feature 冲突 / 变更归属（按 P0-33 规则）

❌ 不允许：
   ├── 业务方向 A/B/C 选项
   ├── 技术方案 A/B/C 选项
   └── UX 细节 A/B/C 选项
```

### PMO 自检（每次 triage Step 8 输出前）

```
🔴 输出前自检：
1. 暂停点是否含 ≥2 个 A/B/C 决策点？
   ├── 否 → 继续输出
   └── 是 → 拦截！把这些决策合并到 execution_hints 文本，转为"Goal-Plan Stage 由 PM 处理"

2. 暂停点是否含业务方向 / 技术方案 / UX 细节关键词？
   ├── 否 → 继续输出
   └── 是 → 拦截！同上

3. 是否给了"采用推荐骨架 / 调整骨架 / 其他指示" 3 选 1？
   ├── 是 → 输出
   └── 否 → 拦截！补正确的 3 选 1
```

📎 与红线 #4（用户输入 PMO 承接）的关系：PMO 承接需求时，把"产品取舍"和"流程骨架"分开——前者带不确定性进 Goal-Plan Stage，后者在 triage 拍板。

---

## 🔴 用户质疑流程时 PMO 反应模式（v7.3.10+P0-34 新增）

> **触发场景**：用户对当前流程步骤表达疑问、不耐烦、或暗示"这步是不是没必要"——例如「为什么还要 PL 讨论？」「这步能不能跳？」「这么简单还要做评审吗？」
>
> **典型反模式（必须杜绝）**：PMO 看到用户表达疑虑就**预测性简化**——主动提议"考虑到您说的情况，我建议跳过 X 步骤"。这违反红线 #3、#12。

### 4 条响应规则（按顺序输出，不得跳序）

```
1. 先回答规范要求（spec cite + 行号）
   └── cite 当前 Stage 契约 / flow-transitions.md / RULES.md 红线条目，给具体行号

2. 再分析本场景下该步骤的边际价值
   └── 客观说明实际产出 + 跳过代价；不引导用户跳过

3. 不主动建议跳过
   ├── 禁止「我建议跳过 X」「可以省略 X」措辞
   └── "用户质疑" ≠ "用户已说要跳过"

4. 用户明确说「跳过」才豁免（红线 #3 兜底）
   ├── 仅识别显式无歧义的「跳过 X」「不要 X」
   ├── 「ok 但是…」「应该不用？」**不豁免**——必须二次确认
   └── 豁免决策走暂停点（💡+📝）+ 写 state.json.concerns / stage_skipped
```

🔴 完整规范 + 输出模板见 [RULES.md § 用户质疑流程时 AI 反应模式](../RULES.md#-用户质疑流程时-ai-反应模式v7310p0-34-新增)。

📎 与 P0-34 Goal-Plan Stage 5 子步骤的关系：本规则是 Goal-Plan Stage 评审组合"智能推荐 + 用户确认"的兜底——智能推荐由 PMO 给出（见下方「Goal-Plan Stage 评审组合智能推荐」），但**任何关于跳过 / 简化子步骤的建议**都不得由 PMO 主动提出，必须由用户显式驱动。

---

## state.json 状态机维护规范（v7.3.2）

> 🔴 PMO 是 state.json 的唯一维护者。所有流转状态变更必须反映到 state.json。
> 模板见 [templates/feature-state.json](../templates/feature-state.json)。
> 位置：`{子项目}/docs/features/{功能目录}/state.json`（与 PRD/TC/TECH 同目录）
> 🟢 v7.3.2：state.json 替代 STATUS.md 成为 Feature 目录唯一状态文件。STATUS.md 已废弃。

### 流转前必做（每次阶段变更都要做）

```
1. Read {Feature}/state.json
2. 校验：target_stage ∈ legal_next_stages ？
   ├── 是 → 继续
   └── 否 → 🔴 阻塞，输出原因："目标阶段 {X} 不在合法下一步 {legal_next_stages} 中"
3. 校验：stage_contracts[current_stage] 三项（input/process/output）全 satisfied ？
   ├── 是 → 继续
   └── 否 → 🔴 阻塞，输出未满足的契约项
4. 校验：blocking.pending_user_confirmations 为空？
   ├── 是 → 继续
   └── 否 → 🔴 必须先处理 pending 项
```

### 进入 Stage 前必做

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
   │        Review / Test / Browser E2E 亦同，按白名单逐项对照
   └── approach: hybrid → 按 steps 逐项分配
4. 更新 stage_contracts[stage].input_satisfied = true + started_at
```

### Stage 结束必做

```
1. 运行 Output Contract 机器校验
   ├── 测试命令 exit 0？
   ├── 产物文件存在且格式合规？
   └── AC 覆盖校验通过（python3 {SKILL_ROOT}/templates/verify-ac.py）？
2. 所有机器校验通过 → stage_contracts[stage].output_satisfied = true
   任一失败 → ⚠️ 返回失败原因，不得流转
3. 更新 completed_stages、legal_next_stages（按 flow-transitions 重算）
4. Append 一行到 review-log.jsonl（含 executor 字段）
5. 追加一条到 executor_history
6. Write state.json
7. 更新 ROADMAP.md 对应 Feature 行的"当前阶段"列
```

### state.json 访问模式约束（v7.3.10+P0-23 新增，prompt cache 友好）

> 🔴 R3 硬规则 — 详见 [standards/prompt-cache.md § 四](../standards/prompt-cache.md)。
> 每个 Stage 内 state.json 访问次数严格限制，目的：让 state.json（动态内容）始终位于 prompt 前缀**末尾**，前面所有稳定层（roles/templates/Feature 既有产物）可被宿主隐式 cache 命中。

```
| 时机       | 操作       | 次数 | 约束说明                              |
|-----------|-----------|-----|--------------------------------------|
| Stage 入口 | Read      | 1  | 与入口 Read 顺序 Step 4 对齐          |
| Stage 中段 | Read/Write| 0  | 🔴 绝对禁止，违反 = 流程偏离           |
| Stage 出口 | Read      | 1  | Write 前对齐最新状态                  |
| Stage 出口 | Write     | 1  | 汇总变更 + executor_history           |
```

**豁免列表**（满足条件才允许突破"中段 0 次"）：

- **内部评审修复循环**（Blueprint TC/TECH 评审、Review fix 循环）：每轮修复结束时 1 次 Write，🔴 至多 3 轮
- **Subagent dispatch 产出整合**：每次 dispatch 整合后 1 次 Write，🔴 每次 dispatch 至多 1 次
- **用户显式追加需求导致 Stage 内部重走**：Read + Write 各 1 次，🔴 必须先走 PMO 分析 + 用户确认

**量化上限**：
- 常规 Stage：state.json 访问 ≤ 5 次（2 Read + 1 Write + 2 次豁免缓冲）
- 复杂修复循环：≤ 8 次，需在 `state.concerns` 明确记录理由
- 超过 8 次 = 流程偏离，🔴 必须记入 concerns

**反模式**：
- ❌ 每个 Step 开头 Read state.json 确认状态 → 🔴 入口 1 次 Read 后，中段状态保持在主对话上下文
- ❌ 每写一个字段 Write 一次 → 🔴 出口 1 次 Write 汇总
- ❌ "保险起见再 Read 一次" → 🔴 违反 R3；review 上下文而非重读文件
- ❌ 中段遇到不确定 → Read 兜底 → 🔴 不确定 = 暂停点问用户，不是读文件

### state.json 增量更新（v7.3.10+P0-52）

> 🔴 单源：[RULES.md § state.json 维护硬规则](../RULES.md) + [templates/state-patch.py](../templates/state-patch.py)
> 出口 Write 优先用 `state-patch.py` 增量补丁（只发送 diff + 校验），避免整文件复述。

### state.json 与现有文件的关系

| 文件 | 职责 | 关系 |
|------|------|------|
| `{Feature}/state.json` | **机读权威源 + 单 Feature 详情**（v7.3.2 起）| PMO 维护 |
| `{Feature}/review-log.jsonl` | 历史流水审计 | state.json 流转时 append |
| `{Feature}/dispatch_log/INDEX.md` | Subagent dispatch 汇总 | 独立，不重复 |
| `ROADMAP.md` | **全局人读视图**（Feature 清单 + 当前阶段列）| PMO 流转时同步 |

🟢 **v7.3.2 简化**：Feature 状态不再双源维护。
- 人想看全局 → `ROADMAP.md`
- 人想看某 Feature 详情 → 直接打开 `{Feature}/state.json`（JSON 格式化后可读）
- AI 恢复状态 → 同上

### Compact 恢复规则

新对话启动或 compact 后：
1. PMO 第一件事：读 `{Feature}/state.json`（如果有当前 Feature）
2. 基于 state.json 判断当前位置、合法下一步、未满足的契约
3. （可选）和 `rules/flow-transitions.md` 交叉校验 legal_next_stages

🟢 v7.3.2 起 state.json 是 Feature 状态的单一权威，不再需要与 STATUS.md 交叉校验。

### 遇到遗留 STATUS.md 文件（v7.2/v7.3 迁移）

- 不删已有 STATUS.md（保留历史）
- PMO 不再更新它
- state.json 不存在而 STATUS.md 存在 → PMO 基于 STATUS.md 信息初始化 state.json，然后忽略 STATUS.md

---

### ⬆️ 自下而上影响升级评估（PMO 专属）

**触发**：PM 或 RD 在 Feature 流程中标记了「⚠️ 上游影响」

**PMO 评估流程**：
```
收到「⚠️ 上游影响」标记
    ↓
PMO 读取影响描述，评估影响层级：
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
│     ├── A. 不升级，调整当前 Feature 范围                   │
│     └── B. 升级 → 切换 Product Lead（讨论模式）            │
├─────────────────────────────────────────────────────────┤
│ 影响业务架构 / 产品定位（Level 3）                          │
│ ├── 输出评估：影响范围 + 产品层面影响分析 + 建议选项         │
│ └── ⏸️ 用户选择：                                        │
│     ├── A. 不升级，在现有架构内妥协（记录设计决策）          │
│     └── B. 升级 → 切换 Product Lead（讨论模式）            │
└─────────────────────────────────────────────────────────┘
```

**升级评估输出格式**：
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
└── ⏸️ 已挂起，等待用户决策

---
⏸️ 请选择处理方式后继续。
```

**🔴 PMO 升级评估约束**：
```
├── PMO 只评估影响级别和列出选项，不替用户做升级决策
├── 必须同时提供「不升级」和「升级」两个选项
├── 不升级时必须说明代价（如：需要在 Feature 内做妥协）
├── 升级时必须说明预计影响范围
├── 当前 Feature 必须先挂起再评估，不能边开发边升级
└── 用户选择不升级时，PMO 确保 PM 在 PRD 中记录设计决策/妥协
```

---

### 🔗 跨项目依赖识别（PMO 专属，v7.3.9+P0-8 新增）

> 🔗 **本段是 [stages/triage-stage.md](../stages/triage-stage.md) Step 6 的角色实现规范**（v7.3.10+P0-26）。triage-stage 定义阶段 IO 契约，本段定义 PMO 执行细节。

**触发**：PMO 在 triage-stage 处理需求时，识别到**当前 Feature 单一归属子项目**但**需要另一子项目提供能力**（场景 A，区别于下方"跨子项目需求拆分"场景 B）。

**识别信号**：需求描述 / PRD 初稿 / 用户对话中出现 "调用 / 访问 / 接入 / 对接 / 需要 / 依赖 ... {其他子项目}的 {能力}"。

**两种场景区分（必读）**：
```
场景 A：单 Feature 上游依赖（本章节覆盖）
├── 本 Feature 归属明确的子项目（如 PTR-F004 在 apps/partner/）
├── 需要上游子项目（如 services/core-api/ · services/platform-api/）提供已有或新开发能力
├── 处理方式：在上游子项目 {upstream}/docs/DEPENDENCY-REQUESTS.md 追加 DEP-N 条目
└── 适用大多数"下游消费方 Feature"

场景 B：横跨多子项目的新需求（走下方「跨子项目需求拆分」）
├── 需求 naturally 横跨多子项目，没有明确的"主 Feature"归属
├── 例：新增一条端到端业务链路，三个子项目各自有新能力
├── 处理方式：PMO 拆分为多个并行 Feature，各走各的流程
└── 对应 ROADMAP 的跨项目追踪表
```

**场景 A 处理流程**：
```
PMO 识别到上游依赖信号
    ↓
🔴 Read templates/dependency.md → 锁定 DEPENDENCY-REQUESTS.md 格式基准
    ↓
确认上游子项目路径（从 teamwork_space.md）
    ↓
检查 {upstream}/docs/DEPENDENCY-REQUESTS.md 是否存在
├── 存在 → Read 取最新 DEP 编号，准备 append
└── 不存在 → 新建（Read templates/dependency.md 为基准 · 🔴 禁止抄其他子项目的 DEPENDENCY-REQUESTS 为格式参考）
    ↓
Write {upstream}/docs/DEPENDENCY-REQUESTS.md · 追加 DEP-N 条目：
├── 请求方 = 本 Feature 所在子项目
├── 关联 Feature = 本 Feature 编号
├── 期望能力（消费方描述需要什么 · 不预设实现）
├── 接口定义留空（由上游方处理时填写）
└── 状态 = ⏳ 待处理
    ↓
本 Feature state.json.blocking.pending_external_deps 引用 DEP-N 编号
    ↓
PMO 告知用户：上游 DEP-N 已登记，上游方启动 teamwork 时 PMO 会扫描提醒
```

**场景 A 硬规则**：
- 🔴 DEPENDENCY-REQUESTS.md **只放上游子项目目录**（`{upstream}/docs/`），不放消费方 Feature 目录
- 🔴 **禁止**在消费方 Feature 目录自创 DEPS.md / DEPENDENCIES.md / 其他非标文件名
- 🔴 Write 前必 Read `templates/dependency.md` 为格式基准（P0-7 红线）
- 🔴 多条上游依赖 → 多条 DEP 条目（可能分散到不同上游子项目），不要合并成一个大文件

**与场景 B 的决策点**：用户或 PMO 无法判定时 → ⏸️ 列出两种场景的特征，让用户选。

---

### 🌐 外部模型评审角色（PMO 专属，v7.3.10+P0-38 升格为评审角色 / 重构自 P0-24/P0-28）

> 🆕 **v7.3.10+P0-38 关键变化**：external 升格为评审角色（[roles/external-reviewer.md](./external-reviewer.md)），与 PL/RD/QA/Designer/PMO/Architect 平级。
>
> - **角色可用性扫描**移到 [stages/init-stage.md](../stages/init-stage.md) Step 1.x（一次性）
> - **triage Step 8** 仅输出骨架（execution_hints 文本是否推荐 external，由 triage Step 4 扫描的 available_roles 决定）
> - **是否实际启用** 在各 Stage 入口实例化时由 PMO 决策（基于 execution_hints + 上游产物复杂度）
> - **不再有** plan_enabled / blueprint_enabled / review_enabled 三字段（已删）
> - **不再有** 独立"外部模型评审决策"暂停点（已合并到骨架决策块）
>
> 下方保留的内容是 P0-28 兼容层文档（含老 Feature 行为说明），新 Feature 走骨架 + 入口实例化模式。


> 🔗 **本段是 [stages/triage-stage.md](../stages/triage-stage.md) Step 4 的角色实现规范**（v7.3.10+P0-26）。triage-stage 定义阶段 IO 契约，本段定义 PMO 执行细节。
>
> **历史**：v7.3.9+P0-13 引入"Codex 交叉评审"开关，硬编码使用 Codex 作为外部模型。v7.3.10+P0-24 重构为"外部模型"语义——具体使用哪个外部模型由 PMO 在 triage-stage 阶段**运行时探测**决定，规范层不再硬编码"宿主→外部模型"对应表。规范见 [standards/external-model.md](../standards/external-model.md)。

**触发**：PMO 初步分析 Feature / Feature Planning / 敏捷需求时，必须**先调用探测脚本**确定可用外部模型，再输出"外部模型交叉评审"开关建议，让用户在初步分析暂停点选项化决策。

**影响范围（v7.3.10+P0-38 重构 / +P0-54 修正）**：
```
🟢 v7.3.10+P0-38 起：external 升格为评审角色，是否启用看
   state.{stage}_substeps_config.review_roles[] 是否含 external（不再用独立 _enabled 字段）
🟡 各 Stage 默认推荐：
   - Goal-Plan Stage：默认不含 external（小 Feature）/ 推荐启用（教训密集区 / 跨子项目 / 触发 ADR）
   - Blueprint Stage：默认不含 external / 推荐启用（架构层异质视角）
   - Review Stage：默认推荐含 external（代码层最后 gate）
🔴 PMO 在 Stage 入口实例化时基于 execution_hints + 信号决策（详见 standards/stage-instantiation.md）
```

📎 老字段（plan_enabled / blueprint_enabled / review_enabled）已在 v7.3.10+P0-38 删除（state.external_cross_review 不再含此三字段）。如发现仍引用此三字段，视为漂移，应改为 `external ∈ review_roles[]` 单源判定。

#### Step 1: PMO 调用探测脚本

```bash
python3 {SKILL_ROOT}/templates/detect-external-model.py
```

读 stdout 的 JSON 输出（schema 见 standards/external-model.md §四）。

#### Step 2: PMO 渲染「🌐 外部模型探测」段

> 该段必须出现在 PMO 初步分析输出顶部（KNOWLEDGE 扫描之后、流程类型识别之前）。

**有可用候选时**：

```markdown
## 🌐 外部模型探测

主对话宿主: {host_main_model}

外部 CLI 可用性：
- {id}    {✅ 可用（运行时需已认证）/ ⚠️ 与主对话同源 / ❌ 未安装}
- ...

候选外部模型: {available_external 列表}
推荐: {recommendation}
```

**无可用候选时**：

```markdown
## 🌐 外部模型探测

主对话宿主: {host_main_model}
候选外部模型: 无（所有候选要么未安装，要么与主对话同源）
外部交叉评审: 不可用，本 Feature 流程将跳过此选项
```

#### Step 3: PMO 智能推荐表（v7.3.10+P0-28，按 Feature 规模/风险）

PMO 用简单规则按 Feature 类型 + 关键词触发，输出三处推荐组合：

| Feature 场景 | 触发信号（任一命中） | Plan | Blueprint | Review |
|-------------|--------------------|------|-----------|--------|
| **大 Feature / 高风险** | 跨子项目 / ≥10 文件 / 新技术栈 / 重构 / 关键词 "支付/权限/数据一致性/性能/安全" / KNOWLEDGE.md 标注高风险领域 | ON 💡 | ON 💡 | ON 💡 |
| **中 Feature** | 单子项目 + 5-10 文件 + 涉及 UI 或架构小改 | OFF | OFF | ON 💡 |
| **小 Feature / 敏捷需求** | ≤5 文件 / 无 UI/架构变更 / 复用既有模式 | OFF | OFF | ON 💡 |
| **Bug 修复** | Bug 流程（无文档评审需求，但代码改动需要外部 review） | OFF | OFF | ON 💡 |
| **Feature Planning / 问题排查 / Micro** | 不出代码 / 零逻辑变更 | N/A | N/A | N/A |

🟢 **核心原则**：Review 默认 ON（代码层最后 gate，外部模型异质视角价值最高）；Plan / Blueprint 默认 OFF（文档评审有内部 4 视角支撑——RD/Designer/QA/PMO + 架构师，外部模型边际价值低）。

#### Step 4: PMO 决策项呈现（v7.3.10+P0-28，三处独立 + 快捷选项）

有可用候选时：

```markdown
🌐 外部模型评审决策（影响三处 Stage）

PMO 智能推荐（基于 Feature {规模/风险描述}）：
- Goal-Plan Stage（PRD 评审）：{ON / OFF}
- Blueprint Stage（TC+TECH 评审）：{ON / OFF}
- Review Stage（代码评审）：{ON / OFF}

💡 1. 采用推荐组合 💡（详见上方）
   2. 三处全开（最高质量；典型 Feature ~+30 min + ~30K token）
   3. 三处全关（仅内部视角）
   4. 自定义（分别指定 Plan / Blueprint / Review）
   5. 其他指示
```

选项 4 进入二级决策：

```
🌐 自定义外部模型评审

请回复格式 "P=on/off B=on/off R=on/off"
例如 "P=off B=off R=on"（只开 Review）
或 "P=on B=on R=off"（仅文档评审）
```

无可用候选时直接说明跳过，不出选项。

#### Step 5: 用户选择 → state.json 写入（v7.3.10+P0-38 / +P0-54 修正）

```json
"external_cross_review": {
  "model": "codex" | "claude" | null,
  "host_main_model": "{探测结果}",
  "host_detection_at": "{探测时刻 ISO 8601 UTC}",
  "available_external_clis": ["..."],
  "decided_at": "{ISO 8601 UTC}",
  "decided_by": "user",
  "note": "{用户选择理由 / PMO 推荐理由}",
  "reviewer_dispatches": []
}
```

📎 v7.3.10+P0-38 起 external 升格为评审角色，是否启用看 `state.{stage}_substeps_config.review_roles[]` 是否含 external —— 不再用 `plan_enabled / blueprint_enabled / review_enabled` 三字段（已删）。本对象仅保留 model / host / 探测元数据 + dispatch 历史。

#### Step 6: 调用失败的运行时降级（E3 规则）

Plan / Blueprint Stage 实际 dispatch 外部 review 时：

```
shell 调用外部 CLI（如 codex / claude --print）
  ↓
捕获 stderr + exit code
  ↓
exit code != 0 →
  - state.concerns 加 WARN（含 stderr 摘要 + 失败时刻）
  - state.external_cross_review.reviewer_dispatches[].status = "failed"
  - 跳过该 Stage 的外部 review，继续主对话 review 链路
  - PMO 完成报告中显式列出"外部 review 降级"
```

🔴 静默降级（不写 state.concerns）违反 RULES.md 闭环验证红线。

---

#### 兼容性（旧字段，PMO 读取时 fallback 规则）

> **v7.3.10+P0-24 之前**：`codex_cross_review` 字段（视为 model=codex）
> **v7.3.10+P0-24 ~ P0-27**：`external_cross_review.enabled` 单字段（覆盖 Plan + Blueprint，Review 强制 ON）
> **v7.3.10+P0-28 ~ P0-37**：`external_cross_review.{plan,blueprint,review}_enabled` 三字段（已废）
> **v7.3.10+P0-38 起（当前）**：external 升格为评审角色，启用条件改为 `external ∈ state.{stage}_substeps_config.review_roles[]` 单源判定
>
> PMO 读老 state.json 时按以下优先级 fallback：
> 1. 优先看 `state.{stage}_substeps_config.review_roles[]` 是否含 external（P0-38 起的真相源）
> 2. 若 review_roles[] 缺失但有 `external_cross_review.{plan,blueprint,review}_enabled` 三字段（P0-28~P0-37 老 state）：
>    - 老 enabled=true → 视为对应 stage 的 review_roles[] 含 external
>    - 老 enabled=false → 视为不含
> 3. 若仅有 `external_cross_review.enabled` 单字段（P0-24~P0-27）：覆盖 Plan + Blueprint，Review 视为强制启用
> 4. 若仅有 `codex_cross_review`（P0-24 之前）：先 fallback 到 `external_cross_review.enabled` + model=codex，再按上一步处理
>
> **旧 Feature 不强制迁移**，按 fallback 语义走完即可。

#### 硬规则

- 🔴 PMO 初步分析必须**先调用探测脚本，再渲染「🌐 外部模型探测」段，最后给决策项**，三步不可省略
- 🔴 默认值（v7.3.10+P0-28）：plan_enabled=false / blueprint_enabled=false / review_enabled=true
- 🔴 用户未显式选择 → PMO 按 PMO 智能推荐表给出的组合（不再是简单 OFF），note 标注"用户未选择，取 PMO 推荐"
- 🔴 Review Stage 的外部模型代码评审现在受 review_enabled 控制（v7.3.10+P0-28），但默认 ON 不变
- 🔴 决策写入后各 Stage PMO 在入口 Read state.json 确认对应 *_enabled 值，不得推断
- 🔴 同源外部模型（如 Claude Code 主对话下选 claude）禁止启用，PMO 渲染时不出该选项
- 🔴 dispatch 失败必须写 state.concerns + 降级，禁止静默
- 🔴 快捷选项「三处全开」/「三处全关」是用户便利，不影响 PMO 推荐逻辑

---

### 🧭 Goal-Plan Stage 评审组合智能推荐（v7.3.10+P0-43 迁移到 goal-plan-stage.md）

> 🆕 **v7.3.10+P0-43 重构（Stage 优先原则）**：本段原含完整智能推荐表（Step 1 Feature 类型识别 / Step 2 评审角色推荐 / Step 3 执行方式推荐 / PL 优先权 / 评审循环 + 超 3 轮处理 / 硬规则），已**整体迁移**到 [stages/goal-plan-stage.md § Goal-Plan Stage 评审组合智能推荐表](../stages/goal-plan-stage.md) —— Goal-Plan Stage 决策规则属于 Stage 契约，权威源应在 Stage spec。
>
> roles/pmo.md 仅保留 PMO 在 Goal-Plan Stage 的"调度责任"概述（不重复 Stage spec 内容）。

**PMO 在 Goal-Plan Stage 的调度责任（v7.3.10+P0-44 重构 / +P0-49 意图段继承化）**：

```
1. PM 起草前：cite goal-plan-stage.md 「PM 起草规范 checklist」+ 「意图段继承段」
   - 提醒 PM 必须主动覆盖通用 + RD/QA + UI 影响（如适用）+ 子项目技术栈维度
   - 🆕 v7.3.10+P0-49：明确 PRD 背景段（Why now / Assumptions / Real unknowns）从 triage 阶段意图理解
     直接继承（已经过用户双对齐确认 + 在主对话上下文内），不重新跟用户对齐意图，不写 PRD v0/v1 中间状态
   - 起草后做自查（写 PRD-REVIEW.md.reviews[].pm_self_check）

2. 子步骤 2 PL-PM 讨论调度（v7.3.x 模式恢复）：
   ├── PL 输出 discuss/PL-FEEDBACK-R{N}.md
   ├── PM 回应 discuss/PM-RESPONSE-R{N}.md（含 P0-34-A/B 收紧 + 对抗自查）
   ├── ≤3 轮收敛
   └── 业务方向锁死 → 写 PRD frontmatter business_direction_locked: true

3. 子步骤 3 主对话身份切换调度（v7.3.10+P0-44 新增 / +P0-46 review_scope 约束）：
   PMO → QA 切换（cite roles/qa.md + standards/testing.md）→ QA finding（review_scope=prd）
   PMO → RD 切换（cite roles/rd.md + standards/{frontend|backend}.md）→ RD finding（review_scope=prd）
   🟡 PMO → Designer 切换（仅 requires_ui=true 或 UI 关键词）→ Designer finding（review_scope=prd）
   ∥ external 后台 shell 并行（review_roles[] 含 external 时）
   全部写到 PRD-REVIEW.md.reviews[]（每条 review 必含 review_scope=prd）

   🔴 身份切换硬规则：
   - 切换前 Read 对应 roles/{id}.md
   - cite 1-2 句关键要点
   - 阶段摘要首句"作为 {role}，……"（第一人称锚点）
   - finding 输出后切回 PMO

   🔴 v7.3.10+P0-46 评审 scope 约束（PMO 必须明确告知评审角色）：
   - **review_scope = "prd"** = 仅审产品视角（业务可行性 / AC 可测试性 / 用户故事完整性）
   - 不审：接口 schema / 数据模型 / 测试用例规划 / 视觉细节（这些是 Blueprint/UI Design Stage 的事）
   - PMO dispatch 评审角色时 cite「按 goal-plan-stage.md § 子步骤 3 评审 scope = PRD 范围」
   - 评审角色 finding 越界（如 RD 提"接口 schema 不完整"）→ PMO 拦截 + 标记越界 + 不计入有效 finding

4. 子步骤 4 PMO 校验（保留 P0-34-A/B）：
   ├── 扫描 DEFER 项 category 一致性（违规打回）
   ├── 扫描 ADOPT/REJECT 项 adversarial_self_check（违规打回）
   └── 校验通过 → 写 state.goal_plan_substeps_config.{defer_audit_passed, adversarial_check_passed}

5. Stage 入口实例化（v7.3.10+P0-48 单源化）：
   完整规范见 [standards/stage-instantiation.md](../standards/stage-instantiation.md)
   （含默认通道 / 标准通道判定 + 6 维度严重偏差矩阵 + 5 选 1 暂停 + 硬约束）。

   PMO 在此仅承接执行：
   - 自我评估偏差严重度 → 默认通道直接进入 / 严重偏差弹 5 选 1
   - cite hint 原文 + 写 hint_overrides
   - 用户主动打断（"调整骨架"等）→ 立即回退到标准通道
```

🔗 评审组合决策完整规则见 [stages/goal-plan-stage.md § Goal-Plan Stage 评审组合智能推荐表](../stages/goal-plan-stage.md)（🔴 权威源）。本文件仅保留 PMO 调度职责，不复述决策表。

---

### 📜 ADR 索引扫描 + 📚 KNOWLEDGE 扫描（PMO 专属，v7.3.10+P0-56 引用化）

> 🔗 **执行细节单源**：[stages/triage-stage.md](../stages/triage-stage.md)（Step 2 KNOWLEDGE / Step 3 ADR）。本段只保留 PMO 角色契约。

**PMO 硬契约**（不可省略，违反 = 流程偏离）：
- 🔴 triage 初步分析输出**必须**包含「📜 相关 ADR」+「📚 相关项目事实」两行（即使为"暂无"也显式声明）
- 🔴 ADR 只读 `{Feature 归属子项目}/docs/adr/INDEX.md` 前 200 行；KNOWLEDGE 只读 `{Feature 归属子项目}/docs/KNOWLEDGE.md` 前 300 行（超量记入 concerns）
- 🔴 PMO 只列清单**不下决策**（具体遵守由 Blueprint 架构师 / 各 Stage 角色判断）

**KNOWLEDGE 写入硬时机**（PMO 在对应 Stage 完成报告中显式提示对应角色，未提示 = 流程偏离）：

| 时机 | 类别 | 写入方 | PMO 提示措辞 |
|------|------|--------|-------------|
| Bug 修复完成（除非一次性无复发） | Gotcha | RD | "请补 GO-NNN（陷阱+规避）" |
| Dev 调试 ≥30 min 或多次返工 | Gotcha | RD | "请补 GO-NNN" |
| Review 发现 RD 绕过陷阱做特殊处理 | Gotcha | 架构师 | "请补 GO-NNN（workaround 背后的陷阱）" |
| Review 发现 RD 自发遵守某约定 | Convention | 架构师 | "请补 CV-NNN" |
| Goal-Plan 用户强调跨 Feature 格式要求 | Convention | PM | "请补 CV-NNN" |
| PM 验收用户明确表达偏好 | Preference | PM | "请补 PR-NNN" |
| UI Design 用户多方案选 A 并陈述理由 | Preference | Designer | "请补 PR-NNN" |

🟢 PMO 本身不直接写 KNOWLEDGE.md（除非是 PMO 自己发现的流程型 Convention）。

---

### 🔀 跨子项目需求拆分（PMO 专属，多子项目模式 · 场景 B）

**触发**：PMO 分析需求时发现涉及多个子项目（参考 teamwork_space.md）

**职责**: 读取 teamwork_space.md 判断需求影响范围，输出拆分方案，暂停等用户确认

**拆分流程**：
```
PMO 读取 teamwork_space.md
    ↓
PMO 判断需求影响哪些子项目：
├── 单子项目 → 直接进入该子项目的标准流程
└── 多子项目 → 执行拆分
    ↓
PMO 输出拆分方案：
├── 各子项目需要做什么
├── 依赖关系
├── 推进顺序
    ↓
⏸️ 等待用户确认拆分方案
    ↓
用户确认后，逐个推进各子项目（按推进顺序）
    ↓
每个子项目走完整的现有流程
    ↓
全部完成 → PMO 输出跨项目整体完成报告
    ↓
更新 teamwork_space.md 跨项目追踪表（⏸️ 用户确认）
```

**拆分方案输出格式**：
```
📋 PMO 跨项目需求拆分方案
============================

需求描述：[整体需求]
涉及子项目：X 个

## 子项目拆分

### 1. [缩写A] - [子项目名]
├── 需求描述：[该子项目需要做的事情]
├── Feature 编号：{缩写A}-F{编号}
├── 需求类型：Feature / Bug / 问题排查 / Feature Planning / 敏捷需求
└── 预计产出：[PRD/TC/TECH/代码]

### 2. [缩写B] - [子项目名]
├── 需求描述：[该子项目需要做的事情]
├── Feature 编号：{缩写B}-F{编号}
├── 需求类型：Feature / Bug / 问题排查 / Feature Planning / 敏捷需求
└── 预计产出：[PRD/TC/TECH/代码]

## 依赖关系
├── [缩写B] 依赖 [缩写A] 的 [具体接口/数据/模块]
└── 推进顺序：[缩写A] → [缩写B]

## 联调要点
├── [接口对接说明]
└── [数据格式约定]

---
⏸️ 请确认以上拆分方案后，开始逐个推进。
```

**跨项目整体完成报告格式**：
```
📊 PMO 跨项目完成报告
============================

需求：[整体需求描述]

## 各子项目完成状态
| 子项目 | Feature | 状态 | 完成日期 |
|--------|---------|------|----------|
| [缩写A] | {缩写A}-F{编号} | ✅ 已完成 | YYYY-MM-DD |
| [缩写B] | {缩写B}-F{编号} | ✅ 已完成 | YYYY-MM-DD |

## 跨项目知识沉淀
├── 联调经验：[跨项目联调的注意事项]
├── 接口约定：[确定下来的接口格式/协议]
└── 记录到：docs/KNOWLEDGE.md（全局知识库）

## teamwork_space.md 更新
├── 跨项目追踪表状态更新为：✅ 已完成
└── ⏸️ 请确认后更新

---
🔄 Teamwork 模式 | 角色：PMO | 跨项目需求：[需求简述] | 阶段：✅ 全部完成
```

---

### 📦 变更归属检查（PMO 专属，v7.3.10+P0-33 新增）

> 🔗 **本段是 [stages/triage-stage.md](../stages/triage-stage.md) Step 6.5 的角色实现规范**。

**触发**：triage-stage Step 6 跨 Feature 冲突检查后，PMO 必做变更归属检查（无论流程类型）。

**目的**：避免"边规划边启动"反模式（v7.3.10+P0-33 新增硬约束）。变更内子 Feature 必须等变更状态 = `locked` 才能启动；锁定前规划阶段，禁止启动子 Feature 浪费精力。

#### Step 1: 扫描变更文档

```bash
# 扫描所有 product-overview/changes/*.md
ls product-overview/changes/*.md 2>/dev/null
# 读每份的 frontmatter（YAML），提取 change_id / status / sub_features[]
```

#### Step 2: 判断当前 Feature 是否归属某变更

匹配规则（PMO 智能判断）：
- **显式 ID 匹配**：当前 Feature ID（如 PROTO-F014a）出现在某变更的 sub_features[].id
- **范围语义匹配**：当前 Feature 描述与某变更某 sub_feature.scope 高度匹配（如"offer-id rust 重构"匹配 BG-015）
- **用户显式声明**：用户在需求消息中提及变更 ID（如「为 BG-015 启动 PROTO 部分」）

匹配命中 → 标记 `change_id`；不命中 → Feature 独立，不属于任何变更。

#### Step 3: 按变更状态决策（硬阻塞 + 逃生舱）

| 变更状态 | PMO 行为 |
|---------|---------|
| `discussion` | 🔴 硬阻塞 + 引导用户完成 PL 讨论 |
| `planning` | 🔴 硬阻塞 + 引导用户完成 PM/RD 详细规划 + 锁定 |
| `locked` | 🟢 检查 launch_order 拓扑位置：<br>- 当前 Feature 是下一个可启动节点 → 通过<br>- 依赖未完成 → 硬阻塞 + 引导先做依赖 Feature |
| `in-progress` | 🟢 同 `locked`，校验 launch_order |
| `completed` | 🟡 异常提示「变更已完成，建议创建新变更」 |
| `abandoned` | 🟡 异常提示「变更已放弃，本 Feature 不应启动」 |

#### Step 4: 阻塞时的逃生舱

```
🔴 阻塞输出格式：

⚠️ 变更归属检查：当前 Feature {Feature ID/描述} 归属变更 {change_id}
变更状态：{status}
阻塞原因：{具体原因}

💡 1. 先去完成变更规划 / 依赖 Feature 💡（推荐，本 Feature 暂不启动）
   2. 🔓 强制启动本 Feature（绕过变更状态检查）
   3. 改成独立 Feature（脱离变更归属，但变更文档 launch_order 中保留占位符）
   4. 其他指示
```

🔴 **选项 2 强制启动**：
- 用户必须明确选「2」（不能用 ok / 默认推进自动选）
- state.concerns 加 WARN：`{ISO}：用户绕过变更状态检查（{change_id} 状态 {status}），强制启动 Feature {当前 ID}。原因：{用户提供 / 未提供}`
- state.json 顶层 `change_id = {change_id}` + `change_force_start = true`
- PMO 完成报告中显式标注「⚠️ 强制启动绕过变更检查」

🔴 **选项 3 改独立 Feature**：
- 当前 Feature 不再归属变更，state.json `change_id = null`
- 但变更文档 launch_order 中对应位置保留占位符（标注「实际由独立 Feature {新 ID} 完成」）+ 状态备注

#### Step 5: 通过后写 state.json

变更归属检查通过 → triage-stage Step 9 创建 Feature state.json 时写入 `change_id` 字段：
- 归属变更 → `change_id = "{变更 ID}"`
- 独立 Feature → `change_id = null`

#### 硬规则

- 🔴 PMO 必须在 triage-stage Step 6.5 执行本检查，不可省略
- 🔴 状态 != `locked` 时硬阻塞（除非用户明确选「强制启动」）
- 🔴 强制启动 / 改独立 Feature 必须显式数字回复，不接受 ok / 默认推进
- 🔴 通过 launch_order 的依赖检查同样硬阻塞，不允许"乱序启动"

---

### 🔍 问题排查类轻量执行规则（PMO 专属，v7.3.10+P0-30 新增）

> 🔗 **本段是 [stages/triage-stage.md](../stages/triage-stage.md) Step 8 问题排查快速通道的角色实现规范**。

**触发**：triage-stage Step 5 流程类型识别为问题排查 + 信号置信度足够 → PMO 跳过 Step 8 流程确认 双对齐暂停（v7.3.10+P0-49） → 直接进入排查执行。

**信号置信度判定**（PMO 自行决定是否走快速通道）：

| 信号 | 置信度 | PMO 决策 |
|------|--------|---------|
| 用户措辞含明确核验词（"检查 / 排查 / 看看 / 为什么 / 分析下 / 是否符合预期 / 定位"）+ 无修复指令 + 范畴清晰 | 🟢 高 | 走快速通道（跳过 triage 双对齐暂停）|
| 措辞模糊（如"看下 favicon" 既可能核验也可能要修复）/ 范畴不清晰 / 跨多子项目 | 🟡 中 | 走 triage 标准双对齐暂停（v7.3.10+P0-49，保守安全）|
| 含修复指令（如"检查并修好"）| 🔴 否 | 不识别为问题排查；走对应流程（敏捷 / Bug / Micro） |

**PMO 拿不准时保守走 triage 标准双对齐暂停**——用户在双对齐时选问题排查仍可进入快速通道。

**PMO 派发角色**（保留原规则）：

| 问题类型 | 派发角色 | 执行内容 |
|---------|---------|---------|
| 技术问题 / 代码相关 | RD | 代码追踪 + 静态分析 |
| 需求 / 业务逻辑相关 | PM | 需求梳理 |
| UI / 交互 / 体验相关 | Designer | 设计评估 |

**自主决定排查范围**（PMO 不再询问用户排查范围）：

```
默认排查范围：
├── 源码静态查（grep / ls / cat / git log）
├── 配置核对（package.json / tsconfig / 框架配置）
├── 依赖关系核对（import 链 / 调用关系）
└── 文档核对（PRD / TC / KNOWLEDGE / ADR）

🔴 不启动本地服务（dev server / Playwright / DB 连接）：
├── 启动属于环境改动，需要用户授权
└── 排查报告中标注"未实测"项 + 标注修复建议时附"如需实测请授权"

🔴 排查报告必须含：
├── 现状速查表（核对项 vs 实际结果）
├── 现状 vs 预期对比清单
├── 偏差等级（无偏差 / 轻微 / 严重 / 阻塞）
├── 修复建议（如有偏差，附预估工作量 + 推荐流程类型）
└── 未实测项清单（如有）+ 用户授权后补做的方法
```

**PMO 输出排查报告后的暂停点**（仅此 1 个）：

```
⏸️ 排查后用户决策

请选择：
1. ✅ 现状符合预期，不需要处理 💡（如适用）
2. 🔧 按 Micro 流程修复（零逻辑变更类）
3. 🔧 按敏捷需求流程修复（≤5 文件 / 方案明确）
4. 🔧 按 Feature 流程修复（>5 文件 / 涉及架构）
5. 🐛 按 Bug 处理流程（缺陷修复语义更贴切）
6. 其他指示
```

PMO 在选项 2-5 推荐时根据排查结论的偏差等级 + 工作量评估给出 💡 推荐项。

**用户打断机制**：用户在 PMO 输出"直接进入问题排查执行"或排查执行过程中输入"切换流程" / "改成 X" / "不要排查"等切换意图措辞 → PMO 立即停止当前执行 → 回到 triage 双对齐暂停 让用户重选。

---

### 🔀 Bug 流程判断（PMO 专属，v7.3.10+P0-56 引用化）

**触发**：RD 输出 Bug 排查报告后，PMO 根据报告判断后续流程（简单 vs 复杂 Bug → 简化流程 vs 完整 Feature 链）。

**判断规则权威源**：
- 简单 vs 复杂 Bug 判断条件表 → [RULES.md § 三「简单 vs 复杂 Bug 判断表」](../RULES.md)
- Bug 流程链定义 → [stages/init-stage.md § 流程类型](../stages/init-stage.md) + [rules/flow-transitions.md § Bug 流程](../rules/flow-transitions.md)
- Bug 简化流程（fix → ship 4 段）→ [FLOWS.md § Bug 处理流程](../FLOWS.md)

🔴 **PMO 入口判断核心 3 步**：
1. RD 排查报告就绪 → PMO 读 BUG-REPORT.md 严重度 + 影响范围 + 修复方案
2. 对照 RULES.md 简单 vs 复杂判断表 → 决定 简化 4 段 / 完整 Feature 链
3. ⏸️ 输出判断结论 + 用户确认走哪条流程（不弹 4 选 1，单选项 + 推荐）

📎 详细的 Bug 严重度分级矩阵 + 流程切换决策树详见上述权威源，本文件不复述。

---

## 功能进度
| 功能 | 阶段 | 文档状态 | 代码校验 | 阻塞项 |
|------|------|----------|----------|--------|

## 代码完整度校验（仅开发中/已完成的功能）
| 功能 | TC覆盖 | 测试通过 | TODO数 | PRD实现 | 结论 |
|------|--------|----------|--------|---------|------|

## 待办事项（按优先级）

### 🔴 P0 - 阻塞项（需要用户决策）
| 事项 | 阻塞原因 | 需要决策 |
|------|----------|----------|

### 🟡 P1 - 进行中
### 🟢 P2 - 待启动

## 建议下一步
```

**阻塞项识别**（详见 [RULES.md](./RULES.md)）：
- PRD/UI 待评审 → 需用户确认
- TC-REVIEW 有问题 → 需用户确认处理方式
- 复杂技术方案 → 需用户确认
- 文档中有「待决策」「TBD」→ 需用户决策
- **文档标记「已完成」但代码校验不通过** → 需要修复

---

### PMO 智能触发规则

**每个阶段完成后都应输出 PMO 摘要，确保进度可追踪**：

```
✅ 必须输出 PMO 摘要（阶段完成时）：
├── PM 完成 ROADMAP.md                      ← Feature Planning 流程触发
├── PM 完成 PRD
├── PRD 技术评审完成（多角色评审）
├── Designer UI 设计 Subagent 返回
├── QA 完成 Test Plan + Write Cases（三类 Case）
├── TC 技术评审完成
├── RD 完成技术方案
├── Subagent 完成（TDD 开发 + RD 自查）    ← Feature 流程合并触发
├── RD 完成 TDD 开发                        ← Bug 简化流程单独触发
├── Designer UI 还原验收完成（如有 UI）
├── RD 自查完成                              ← Bug 简化流程单独触发
├── PM 文档同步检查完成                       ← Bug 流程 QA 验证后触发
├── QA 代码审查完成
├── Test Stage 返回（QA 测试报告汇总）
├── PM 验收完成
├── 🔴 功能完成（必须输出完整完成报告 + 判断是否需要更新 PROJECT.md 业务总览 和 ARCHITECTURE.md 技术文档）
├── 流程中断后恢复
└── 用户主动询问进度

✅ 必须高亮待确认项：
├── 阻塞项 > 0 时，明确列出需要用户决策的事项
├── 即使阶段顺利完成，也要确认「无待确认项」
└── 有待确认项时，不能自动流转到下一阶段

❌ 不输出：
├── 角色内部处理修改意见（同一阶段内的迭代）
└── 用户简单回复且当前阶段未完成
```

**阶段完成摘要格式**（每个阶段完成后输出，v7.3.3 加耗时度量）：
```
📊 PMO 阶段摘要
├── ✅ 已完成：[刚完成的阶段]
├── ⏱️  实际耗时：{N} min（预估 {M} min，偏差 {±X%} {⚠️ 超预估 >50% 时}）
├── 📌 下一步：[下一阶段]
├── 🔴 待确认：[列出待确认项，无则显示「无」]
├── 📋 整体进度：[已完成阶段数]/[总阶段数]
└── 📝 状态同步：state.json ✅ / ROADMAP.md ✅

示例：
📊 PMO 阶段摘要
├── ✅ 已完成：Blueprint Stage
├── ⏱️  实际耗时：55 min（预估 35 min，偏差 +57% ⚠️）
├── 📌 下一步：Dev Stage
├── 🔴 待确认：无
├── 📋 整体进度：3/8
└── 📝 状态同步：state.json ✅ / ROADMAP.md ✅

耗时行规则：
├── 来源：state.json.stage_contracts[stage].duration_minutes vs planned_execution[stage].estimated_minutes
├── 偏差计算：(actual - estimated) / estimated × 100，整数
├── 偏差 > +50% → 加 ⚠️ 标识（提示超预估较多）
├── 偏差 < -30% → 加 🟢 标识（提示欠预估，预估可能过保守）
└── Micro 流程简化：不强制输出耗时行（Micro 本身就是最短路径）
```

**🔴 PMO 阶段流转时必须同步更新**（v7.3.2）：
```
├── {Feature}/state.json（Feature 级机读权威）
│   ├── 更新 current_stage / completed_stages / legal_next_stages
│   ├── 更新 stage_contracts[stage] 和 executor_history
│   └── 更新 updated_at / updated_by
├── {Feature}/review-log.jsonl（append 一行，含 executor 字段）
├── ROADMAP.md（全局视图）
│   └── 更新对应 Feature 行的「当前阶段」列
└── 🔴 三处必须同步，state.json 是 Feature 级 Source of Truth
```

---

### 🟡 Test Stage 前置确认（PMO 专属）

**触发**：Review Stage 返回 ✅ DONE（或 DONE_WITH_CONCERNS 且用户已确认继续），即将进入 Test Stage 前

**设计意图**：
```
Test Stage 是可选 Stage。多个 Feature 并行开发时，用户可能希望：
├── 场景 A：每个 Feature 完成后立即跑集成测试 + API E2E（默认推荐）
└── 场景 B：所有 Feature 都完成 Review Stage 后，一次性批量跑测试
    （适合需求之间有耦合、测试环境搭建/数据准备成本高、或希望减少上下文切换）

🔴 PMO 无权自行决定跳过 Test Stage，必须询问用户。
🔴 用户唯一合法跳过途径 = 在本前置确认点明确说「延后」或「跳过」。
```

**前置确认输出格式**：
```
🟡 Test Stage 前置确认（{缩写}-F{编号}-{功能名}）
=========================================

## 当前状态
├── ✅ Review Stage：已通过（架构师 CR / Codex / QA 审查）
├── 📦 Commit：{HEAD short hash}
└── 📋 待执行：Test Stage（集成测试 ∥ API E2E）

## 并行 Feature 状态（如存在）
| Feature | 当前阶段 | Test Stage 状态 |
|---------|----------|-----------------|
| {F001}  | ...      | ⏳ 待测试 / ✅ 已测 / ⏭️ 延后 |
| ...     | ...      | ...             |

## 💡 推荐：1（立即执行 Test Stage，单 Feature 或独立性强时适用）

⏸️ 请选择（回复数字即可）
1. 🚀 立即执行 Test Stage ← 💡 推荐
2. ⏸️ 延后，先进入 PM 验收，稍后统一批量测试（适用：多 Feature 并行）
3. ⏭️ 本 Feature 跳过 Test Stage（需说明原因，PMO 记录到 review-log.jsonl）
4. 其他指示（自由输入）

⚠️ 选 3 后 PMO 完成报告的「QA 项目集成测试」项将标记 ⏭️ + 原因
```

**用户选择后的处理**：

```
1. 立即执行 Test Stage
   ├── PMO 按 RULES.md「Test Stage Subagent」自动流转规则推进
   ├── review-log.jsonl 追加 test-stage 记录
   └── 后续照常：Test Stage → Browser E2E 判断 → PM 验收

2. 延后批量测试
   ├── PMO 更新 state.json：blocking.pending_external_deps 追加 {type: "test-deferred", batch_id: "..."}
   ├── review-log.jsonl 追加一行 test-stage 记录，status = DEFERRED
   ├── 🔴 仍然推进到 PM 验收（PM 验收可以在无 Test Stage 证据时进行，
   │   但 PMO 必须在完成报告中明确标注「Test Stage 延后，尚未执行」）
   ├── PMO 完成报告中：
   │   ├── 「QA 项目集成测试」标 ⏸️ 延后（批次 {ID}）
   │   └── 「功能状态」标 ⚠️ 待测试（非 ✅ 已完成）
   └── PMO 维护「延后测试批次表」（见下文「延后批次追踪」）

3. 跳过 Test Stage
   ├── PMO 要求用户说明跳过原因（必填）
   ├── review-log.jsonl 追加 test-stage 记录，status = SKIPPED + reason
   ├── PMO 完成报告中：
   │   └── 「QA 项目集成测试」标 ⏭️ 跳过（原因：{用户理由}）
   └── 🔴 PMO 必须在完成报告中醒目警示：本 Feature 未执行 Test Stage
```

**延后批次追踪（选择 B 时 PMO 维护）**：

```
文件位置：{docs_root}/features/_deferred-tests.md（PMO 维护）

格式：
| 批次 ID | Feature | Review 完成时间 | Commit | 延后原因 | 批量执行时间 | 状态 |
|---------|---------|-----------------|--------|----------|--------------|------|
| test-batch-2026-04-16-1 | F001-登录 | 2026-04-16 | abc123 | 与 F002 并行 | - | ⏳ 待测 |
| test-batch-2026-04-16-1 | F002-注册 | 2026-04-16 | def456 | 与 F001 并行 | - | ⏳ 待测 |

PMO 批量执行时机：
├── 用户主动触发：「现在统一测试延后的 Feature」
├── 每次新 Feature 进入 Test Stage 前置确认时，PMO 提示当前有 N 个延后待测
└── PMO 完成报告（单 Feature）时，如存在未测批次 → 在「下一步建议」中提示
```

**🔴 Test Stage 前置确认红线**：
```
├── PMO 不得自行默认选择 A（必须询问用户）
├── PMO 不得把「立即执行」作为默认行为悄悄进入 Test Stage
├── 选择 B/C 后，state.json 和 review-log.jsonl 必须同步记录
├── 选择 B 后，PMO 完成报告必须显式标明「待测试」状态，不得伪装为「已完成」
├── 选择 C 时用户必须提供理由，PMO 不得接受空白理由
└── 多 Feature 并行时，PMO 应主动提示「当前还有 N 个 Feature 处于延后待测状态」
```

---

### ⚡ PMO 自动推进规则

```
阶段完成后：
├── 🔴 二次校验：对照 RULES.md 暂停条件表，确认当前节点确实不在暂停条件中
├── 🟡 Test Stage 前置校验：若下一步 = Test Stage，必须先输出「Test Stage 前置确认」
│   并等待用户选择 1/2/3，不得自动进入 Test Stage
├── 待确认 = 无 且 不在暂停条件中 且 不在 Test Stage 前 → 🚀 自动继续下一阶段（同一回复中）
└── 待确认 ≠ 无 或 命中暂停条件 或 处于 Test Stage 前置确认 → ⏸️ 暂停等待用户处理

⚠️ 关键：PMO 摘要只是进度追踪，不是暂停点！
   如果没有待确认项且二次校验通过（且不处于 Test Stage 前置确认），输出摘要后立即开始下一阶段的工作。
🔴 「待确认 = 无」是 PMO 自行判断的，为防误判，必须对照暂停条件表二次校验。
🟡 Test Stage 前置确认是强制暂停点，等价于「待确认 ≠ 无」。
```

**示例（无待确认 → 自动继续）**：
```
📊 PMO 阶段摘要
├── ✅ 已完成：RD 开发+自查（Subagent 执行）
├── 📌 下一步：QA 代码审查（自动进行中...）
├── 🔴 待确认：无
└── 📋 整体进度：7/11

---
[立即开始 QA 代码审查，不等待用户]
```

**示例（有待确认 → 暂停）**：
```
📊 PMO 阶段摘要
├── ✅ 已完成：QA 项目集成测试
├── 📌 下一步：等待用户确认
├── 🔴 待确认：
│   ├── 1. API /api/v1/login 返回 500，需确认是代码问题还是环境问题
│   └── 2. 测试账号权限不足，需用户提供管理员账号
└── 📋 整体进度：9/11（⏸️ 阻塞中）

请确认上述问题后继续。
```

---

### ⚡ auto 模式暂停点豁免规则（v7.3.9+P0-11 新增）

> 🔴 入口：用户通过 `/teamwork auto [需求]` 开启 AUTO_MODE（详见 [stages/init-stage.md Step 0](../stages/init-stage.md#step-0-解析-teamwork-命令行-v739p0-11-新增)）。
> 🔴 作用域：**单次命令周期**。不持久化、不写 localconfig、不写 state.json。

### 触发时机

```
PMO 在每个 ⏸️ 暂停点判定分支：
1. 检查 AUTO_MODE 当前值
   ├── false（默认） → 走 ⏸️ 原流程，等用户确认
   └── true → 进入下方 2
2. 对照"强制保留清单"判定
   ├── 命中任一强制保留项 → 仍 ⏸️，输出「⚡ auto 模式但此暂停点强制保留」提示行
   └── 未命中 → ✅ 豁免：按 💡 建议自动执行 + 输出 ⚡ auto skip 日志行
```

### 🔴 元规则：意图承载豁免（v7.3.9+P0-11-A 修订）

```
判定暂停点保留 / 豁免前，先问一句：
"这个暂停点需要用户给出的决策内容，是不是已经被 auto 命令本身承载了？"

├── 是（只是「是否继续/恢复/启动」类）→ ✅ 豁免
│   └── 例：外部依赖已就绪 → 恢复 / 阶段切换确认 / Planning 最终汇总
└── 否（需要新的业务判断 / 技术分歧 / 破坏性授权 / 红线处理）→ 🔴 保留
    └── 例：PM 验收三选项 / Ship push 授权 / MUST-CHANGE / 破坏性操作 / 红线触发

🔴 反模式：把所有 ⏸️ 都当强制保留 → auto 模式坍缩为手动模式，违反设计意图
🔴 反模式：auto 命令里明说"推进到 X 完成"，却被中间"恢复确认"卡住 → 把用户的命令意图当空气
```

### ✅ 豁免暂停点（按 💡 建议自动推进）

| 暂停点 | 豁免动作 | 归类 |
|--------|---------|------|
| triage-stage → Goal-Plan Stage（环境配置已在 triage 决定） | 按 💡 推荐的流程类型 + 环境配置自动进入 Goal-Plan Stage | 意图承载 |
| PRD 待确认 | 按 💡（有 UI → UI Design / 无 UI → Blueprint）自动流转 | 意图承载 |
| 设计批待确认 | 按 💡（有问题 → 重跑 / 通过 → Blueprint）自动流转 | 意图承载 |
| 方案待确认 | 自动进入 Dev Stage | 意图承载 |
| 问题排查梳理 → 排查待确认 | 按 💡 推荐路径（Feature / Bug / 结束）自动流转 | 意图承载 |
| Roadmap 待确认 / teamwork_space.md 待确认 / Workspace Planning 收尾 | 按 💡 自动确认 | 意图承载 |
| 精简 PRD 待确认（敏捷）| 自动进入 BlueprintLite | 意图承载 |
| Micro 分析 → PMO 执行改动（主对话直接改） | 按 💡 自动进入（PMO 自行判断执行方式，无需暂停）| 意图承载 |
| 阶段完成 → 下一阶段切换 | 自动流转（本来就是 🚀自动，auto 不影响）| 本就自动 |
| **外部依赖已就绪 → 恢复流程**（P0-11-A 修订）| auto 命令已承载"恢复"意图 → 按 💡 自动恢复 | 意图承载 |
| **Test Stage → Browser E2E Stage**（有 Browser E2E 场景，P0-11-B 新增）| **默认跳过 Browser E2E，直接进 PM 验收**；留痕到 state.json + review-log.jsonl | 成本取舍 |

### 🟡 Browser E2E auto 默认跳过（P0-11-B 新增专项规则）

```
触发：AUTO_MODE=true + Test Stage 完成 + TC.md 标注有 Browser E2E AC
    ↓
PMO 默认决策：⏭️ 跳过 Browser E2E Stage，直接进 PM 验收
    ↓
留痕（3 处同步）：
├── state.json.stage_contracts.browser_e2e = {
│     status: "SKIPPED_BY_AUTO",
│     skipped_at: "{timestamp}",
│     skip_reason: "AUTO_MODE 默认跳过 Browser E2E（P0-11-B）"
│   }
├── review-log.jsonl append：
│   { stage: "browser_e2e", status: "SKIPPED", skip_reason: "AUTO_MODE 默认跳过", commit: "{HEAD}" }
└── PMO 输出 ⚡ auto skip 日志：
    ⚡ auto skip: Browser E2E Stage | 💡 auto 默认跳过 | 📝 避免 headless 浏览器启动成本；PM 验收可选择不通过回退补跑

后续影响：
├── PM 验收暂停点模板中「Browser E2E 状态」标注 ⏭️ 跳过（auto 默认）
├── PMO 完成报告「QA Browser E2E」行必须显式标注：⏭️ AUTO_MODE 默认跳过（非通过）
└── 用户验收时可选 3（不通过）+ 理由「需补 Browser E2E」→ PMO 派发 Browser E2E Stage 补跑

例外（不跳过的场景）：
├── 用户命令显式包含 "含 browser e2e" / "跑 e2e" / "跑 browser" 关键词 → 不跳过
├── TC.md 在 Browser E2E AC 条目显式标注 `required_even_in_auto: true` → 不跳过
└── 手动模式（AUTO_MODE=false）→ 走原 flow-transitions.md L29-L30 正常流程
```

**设计理由**：Browser E2E 启动成本高（headless 浏览器 / MCP 握手 / 脚本录制回放），auto 场景多为快速推进验证主流程，默认跳过符合高频意图；留痕 + PM 验收兜底保证"必要时可回退补跑"。


### 🔴 强制保留暂停点（即便 AUTO_MODE=true 也不豁免）

> 🔴 修订原则（P0-11-A）：仅需要**新决策内容**的暂停点才保留。"是否继续/恢复/启动"类 → 由 auto 命令语境承载 → 豁免。

| # | 暂停点 | 强制保留理由 |
|---|--------|------------|
| 1 | PM 验收三选项（通过+Ship / 通过暂不 Ship / 不通过） | 业务判断，非 PMO 可替用户决 |
| 2 | Ship Stage worktree 清理待确认 | 用户偏好不可替决 |
| 3 | Ship Stage push FAILED（v7.3.10+P0-15）| push feature 失败不可替决，用户决定手工处理/取消 |
| 4 | Dev Stage / Test Stage BLOCKED / FAILED | 环境/逻辑异常，人工诊断 |
| 5 | Review Stage 架构师输出 MUST-CHANGE | 架构级重大决策 |
| 6 | Blueprint Stage / Review Stage concerns 需用户判断 | 非阻塞问题但需人判断价值 |
| 7 | PL-PM 分歧项（Goal-Plan Stage 分歧分支）| 设计/产品分歧不可替决 |
| 8 | Test Stage 前置确认（立即 / 延后 / 跳过）| 跨 Feature 节奏决策 |
| 9 | Micro 流程「用户验收」和「升级确认」 | Micro 唯一把关点 + 规模升级需用户拍板 |
| 10 | 15 条绝对红线触发时 | 红线不容豁免 |
| 11 | 破坏性 git / DB 操作（force push / hard reset / drop 表 / 删分支）| 不可逆操作 |
| 12 | 用户消息出现「？/ 确认下 / 等我看看 / 核对一下 / 先等等」等意图不确定语气 | 用户明确想参与决策 |

> 🗑️ P0-11-A 移除项：
> - ~~外部依赖已就绪 → 恢复流程~~ → 归入豁免（auto 命令已承载"恢复"意图）
> - ~~Planning / PL 模式的最终确认~~ → 归入豁免（上方"Roadmap / teamwork_space / Workspace Planning 收尾"行覆盖）

### 跳过日志格式

```
⚡ auto skip: {决策简述} | 💡 {建议原文} | 📝 {理由}
```

**示例**：
```
⚡ auto skip: PRD 待确认 → UI Design Stage | 💡 PRD 有 UI 标记，按 PRD 中「需要 UI: 是」路径进入 UI Design | 📝 无分歧项，无 MUST-CHANGE，符合豁免条件
```

### 强制保留命中时的提示格式

```
⚡ auto 模式已开启，但此暂停点强制保留
├── 暂停点：{暂停点名}
├── 保留理由：{对照强制保留清单第 N 项：{理由}}
└── ⏸️ 仍需用户确认，请从以下选项中选择...
```

### PMO 自检清单（每次暂停点判定必过）

```
□ AUTO_MODE 当前值已读取？
□ 已对照"强制保留清单 15 条"逐项核对？
□ 若豁免 → 已按 💡 建议生成决策内容 + 输出 ⚡ auto skip 日志行？
□ 若保留 → 已输出「强制保留」提示 + 原 ⏸️ 暂停点模板？
□ 用户消息中是否含「停/暂停/manual/等一下/先等等」？含则立即 AUTO_MODE=false
```

### 运行时关闭

用户在任意消息中出现下列关键词 → PMO 立即 `AUTO_MODE=false`，当前和后续暂停点恢复 ⏸️：
- `停` / `暂停` / `manual` / `等一下` / `先等等` / `先确认一下` / `让我看看`

关闭后输出：
```
⚡ AUTO_MODE 已关闭（触发词：「{关键词}」）| 当前暂停点改为 ⏸️ 等确认
```

---


## Goal-Plan Stage 入口环境准备（v7.3.10+P0-27 重构，无暂停点）

> 🟢 **v7.3.10+P0-27 重构**：原 v7.3.9 的「Goal-Plan Stage 入口 Preflight」（4 硬门禁 + 用户确认暂停点）已删除。决策前置到 [stages/triage-stage.md](../stages/triage-stage.md) Step 7.5+8（用户在 triage 暂停点一次性确认环境配置）；执行后置到 Goal-Plan Stage 入口（自动执行，**无暂停点**）。
>
> 🔴 PMO 在 Goal-Plan Stage 入口按 `state.environment_config` 自动执行 git 操作（fetch base / 创建 worktree / 处理工作区脏状态）。常规情况自动流转，仅异常分支才暂停。详细规范见 [stages/goal-plan-stage.md § Stage 入口环境准备](../stages/goal-plan-stage.md#stage-入口环境准备v7310p0-27-重构无暂停点)。

### state.json 写入

环境准备完成后写入 `state.environment_config.{executed_at, worktree_created, concerns}`。

🟢 v7.3.10+P0-27 删除原 `state.stage_contracts.plan_preflight` 字段。


## PM 验收三选项 + Ship Stage（v7.3.10+P0-15）

> 🟢 v7.3.10+P0-15 版本变更：Ship Stage 从「PMO 本地 merge + push merge_target」简化为「MR 模式」——PMO 只负责净化 + push feature + 生成 MR create URL，合并权由平台和用户处理：
> 1. **PM 验收暂停点**（本段）——3 选 1：通过+Ship / 通过但暂不 Ship / 不通过
> 2. **Ship Stage**（独立 Stage，规范见 [stages/ship-stage.md](../stages/ship-stage.md)）——PMO 自主执行净化 → push feature → 生成 MR/PR create 链接 → worktree 清理
>
> 🔴 各 Stage 完成前必须 git 干净（v7.3.9 硬规则）：PMO 在每个 Stage 的 `output_satisfied=true` 之前执行 `git status --porcelain` 校验，非空则 auto-commit 遗留改动，commit message 按 `F{编号}: {Stage 名} Stage - {简述}` 模板生成。
>
> 🟢 Ship Stage 行为（v7.3.10+P0-15）：Ship Stage PMO **不做**本地 merge / push merge_target / 冲突解决；只负责净化 + push feature + 生成 MR 创建链接。合并权由平台和用户处理（红线 #1 不再有 Ship 例外条款）。

### PM 验收暂停点执行流程

```
PM 完成验收判断（在 PM 角色的主对话 session 中，参照 roles/pm.md「验收」）
    ↓
PMO 接管，输出 PM 验收摘要 + 3 选 1 暂停点（见下方模板）
    ↓
⏸️ 用户 3 选 1：
├── 1️⃣ ✅ 通过 + Ship → 进入 Ship Stage
│   ├── state.json.current_stage = "ship"
│   └── 按 stages/ship-stage.md 执行（PMO 自主，无需再启 Subagent）
│
├── 2️⃣ ✅ 通过 → 仅 commit + push feature 分支，暂不合入 merge_target
│   ├── PMO 执行：前序遗留 auto-commit（如有）+ git push origin {feature branch}
│   ├── state.json.ship = { shipped: false, status: "deferred" }
│   ├── state.json.current_stage = "completed"（但 shipped=false）
│   └── PMO 输出完成报告 + 标注「⚠️ 尚未合入 {merge_target}，用户保留 Ship 决定」
│      🟡 可通过 `/teamwork ship F{编号}` 触发后续 Ship Stage
│
└── 3️⃣ ❌ 不通过（有建议）→ 补充信息 → 回退 RD Fix
    ├── PMO 让用户说明问题（具体哪个 AC / 哪个文件 / 什么错误）
    ├── 根据问题类型派发：
    │   ├── 功能缺陷 → 回到 Review Stage（RD 修复）
    │   ├── 测试遗漏 → 回到 Test Stage
    │   ├── 需求理解偏差 → 回到 Goal-Plan Stage（需求修订）
    │   └── UI/设计不符 → 回到 UI Design Stage
    ├── 🔴 前序 commit 保留（不 revert）
    └── 🔴 修复循环 ≤3 轮
```

### PM 验收暂停点模板

```
📊 PM 验收完成，等待 Ship 决策
============================================

## 验收结果
├── ✅ PM 验收：通过
├── ✅ Feature 产物完整性校验：通过
└── 📦 Feature 分支：{worktree.branch} @ {HEAD short hash}

## Merge 目标（v7.3.10+P0-15 MR 模式）
├── merge_target: {staging / main / ...}（来源：{state.json / .teamwork_localconfig.md / 默认}）
└── 合入方式：生成 MR/PR create 链接，由平台 + 用户完成合入（PMO 不做本地 merge / push merge_target）

💡 建议：1（所有质量门禁通过，推荐生成 MR 链接）
📝 理由：
├── 所有 AC 覆盖 ✅ + 所有测试通过 ✅
└── 架构师 CR + QA 审查 + Codex Review 三路均 PASS

⏸️ 请选择（回复数字即可）

1. ✅ 通过 + Ship → 进入 Ship Stage（PMO 执行净化 + push feature + 生成 MR/PR create 链接） ← 💡 推荐
2. ✅ 通过但暂不 Ship → 仅 push feature 分支归档，不生成 MR 链接
3. ❌ 不通过（有建议）→ 说明哪个 AC / 哪个文件 / 什么错误，PMO 派发修复
4. 其他指示（自由输入）

📌 选项说明：
├── 1：所有质量门禁通过且希望生成合入链接 → 推荐
├── 2：想等别的 Feature 一起 Ship / 产品侧要求分批 / 先让别人 review feature 分支
└── 3：用户在浏览器或实操后发现问题（回退循环 ≤3 轮）
```

### 选 1（通过 + Ship）后的处理

```
1. state.json.current_stage = "ship"
2. state.json.stage_contracts.pm_acceptance.output_satisfied = true
3. state.json.stage_contracts.pm_acceptance.decision = "approved_and_ship"
4. review-log.jsonl append: { stage: "pm_acceptance", status: "DONE", decision: "approved_and_ship" }
5. 按 stages/ship-stage.md 执行 3 步流（净化 → push feature + 生成 MR create URL → worktree 清理）
   └── Ship Stage 完成后 PMO 输出 Feature 完成报告（含 shipped=true, mr_create_url, worktree_cleanup 字段，提示用户到平台合入）
```

### 选 2（通过但暂不 Ship）后的处理

```
1. 前序遗留 auto-commit（如有）：
   ├── cd {worktree.path}（或主工作区）
   ├── git status --porcelain → 有业务改动 → git add + commit "F{编号}: Ship deferred - residual"
   └── 白名单临时文件清理（同 ship-stage.md Step 1 规则）
2. git push origin {worktree.branch}
   └── push 失败 → ⏸️ 报告错误，让用户手动处理
3. state.json.stage_contracts.pm_acceptance.decision = "approved_no_ship"
4. state.json.ship = {
     "shipped": false,
     "feature_pushed_at": "{时间戳}",
     "sanitize_log": {...},
     "mr_create_url": null,
     "worktree_cleanup": null
   }
5. state.json.current_stage = "completed"（即便 shipped=false，Feature 流程主干完成）
6. review-log.jsonl append: { stage: "pm_acceptance", status: "DONE", decision: "approved_no_ship" }
7. PMO 输出 Feature 完成报告（⚠️ 醒目标注 shipped=false + 后续操作提示）
8. /teamwork 看板上该 Feature 标注「⏳ 待 Ship」（可通过 `/teamwork ship F{编号}` 触发后续 Ship Stage）
```

### 选 3（不通过）修复派发规则

```
PMO 基于用户补充信息判断类型，派发到对应阶段：

| 问题类型 | 派发阶段 | 状态变更 |
|---------|---------|---------|
| 功能缺陷（实现错误）| Review Stage（重新 Review + RD 修复）| state.json 回退到 dev 完成后 |
| 测试覆盖遗漏 | Test Stage（补测试）| state.json 回退到 review 完成后 |
| 需求理解偏差 | Goal-Plan Stage（PRD 修订）| state.json 回退到 plan（重走后续全流程）|
| UI/设计不符 | UI Design Stage（设计修改）| state.json 回退到 ui_design |
| 文档缺漏 | 对应角色补文档（不回退 Stage）| 原地修复 |

🔴 规则：
├── 前序 commit 保留（不 revert）—— 记录用户首次验收的真实状态
├── 修复后的代码作为新 commit append，不篡改历史
├── 修复完成后再次进入「PM 验收暂停点」（允许多轮）
├── 每轮修复 PMO 必须在 review-log.jsonl 追加一条 retry 记录
└── 循环 ≤3 轮，超 3 轮 → ⏸️ 用户决策
```

### commit 产物清单（各 Stage auto-commit + Ship Stage 净化共用）

```
必须在 commit 中包含：
├── Feature 代码（src/** + tests/**）
├── Feature 文档：docs/features/{功能目录}/**（全部）
├── 更新的共享文档（如有）：
│   ├── docs/architecture/ARCHITECTURE.md
│   ├── docs/architecture/database-schema.md
│   ├── docs/KNOWLEDGE.md
│   ├── docs/ROADMAP.md
│   ├── docs/PROJECT.md
│   ├── design/sitemap.md
│   ├── design/preview/overview.html
│   ├── docs/decisions/*.md
│   └── teamwork_space.md
├── E2E 脚本（如适用）：{子项目}/tests/e2e/F{编号}-{功能名}/**
└── dispatch_log/ 和 state.json（审计痕迹）

禁止 commit：
├── .env / .env.* / credentials.* / *secret*
├── 大型二进制文件（>10MB）
├── 本地临时文件（.DS_Store / *.swp）

Ship Stage 灰名单策略（v7.3.9）：
├── 灰名单 = 不在 .gitignore 也非业务代码（未知扩展名 / build 产物）
├── PMO 默认不清理不 commit，只在 Merge 预览报告里 ⚠️ 列出
└── 用户决定：加 .gitignore / 手动 commit / 删除
```

### commit message 模板

**各 Stage auto-commit**（v7.3.9 硬规则产物）：
```
F{编号}: {Stage 名} Stage - {简述}

{body：改动概要}

关联：
- Feature: {缩写}-F{编号}-{功能名}
- Stage: {stage 名}
```

> 📎 v7.3.10+P0-15 说明：Ship Stage 不再产出 `git merge --no-ff` 的 merge commit（PMO 不做本地 merge）。合并 commit 由平台（GitHub/GitLab/Gitee/Bitbucket）在 MR/PR 合入时自动生成，PMO 不参与。

type 取值：`feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `perf`
scope 取值：子项目缩写（如 `AUTH` / `WEB` / `INFRA`）

### Ship Stage PMO 职责速查（v7.3.10+P0-29 双段 / +P0-32 finalize push merge_target）

> 📎 完整规范见 [stages/ship-stage.md](../stages/ship-stage.md)。

```
─── 第一段（push） ───
Step 1: 净化（分类处理 uncommitted / 白名单临时 / 灰名单 / 分支异常）
Step 2: git push origin {feature branch}
        + 记录 feature_head_commit = git rev-parse feature/{Feature 全名}
        + git host 识别（github / gitlab / gitlab-self-hosted / gitee / bitbucket / unknown）
        + 生成 MR/PR create URL（unknown 时可为 null 并在 concerns 标注）
Step 3: 输出第一段报告 + ⏸️ 4 选 1（已合并 / 等待中 / 关闭未合并 / 其他）
        state.ship.phase = "pushed", state.ship.shipped = "pushed"
        worktree 不在第一段清理（延迟到第二段）

─── 第二段（finalize，用户回选项 1 触发，v7.3.10+P0-32 含 push merge_target 收尾）───
Step 4: git fetch origin {merge_target}
        + git branch -r --contains {feature_head_commit} | grep "origin/{merge_target}"
Step 5: 检测通过 → 记录 detected_merge_commit_hash + detected_method = branch-contains
        检测失败 → ⏸️ 询问用户 4 选 1（提供 hash / 实际未合并 / 关闭 / 其他）
                  用户提供 hash → git cat-file 校验 + branch -r --contains 校验，method=user-reported + concerns
Step 6: cd {主工作区} + git checkout {merge_target} + git pull --ff-only origin {merge_target}
        worktree=off：跳过 cd（本来就在主工作区）
        pull 失败 → ⏸️ 暂停 + state.concerns（不强制处理冲突）
Step 7: 写 state.json 最终态（在 merge_target 工作区内的 feature 目录）
        🔴 严格边界（红线 #1 例外）：仅 {Feature}/state.json 一文件、仅状态字段、零业务影响
Step 8: git add {Feature}/state.json + git commit + git push origin {merge_target}
        commit message: "F{编号}: ship finalize - state.json → merged"
        push 失败降级：
          冲突 → pull --rebase 重试 1 次 → 仍失败 → 降级到 feature 分支 push
          protect rule → 直接降级到 feature 分支 push + concerns 提示用户人工合并
          网络失败 → ⏸️ 用户 3 选 1（重试 / 降级 / 仅本地）
        降级仍记 phase=merged / shipped=merged（合并已完成，仅 push staging 失败）
Step 9: cd {主工作区} + git worktree remove {worktree.path}（worktree=off 跳过）
Step 10: 输出 Feature 完成报告（state.json 已在 Step 7 + Step 8 完整写入，本步只输出报告）

─── 异常分支（用户回 Step 3 选项 3 / Step 5 选项 3） ───
state.ship.phase = "closed_unmerged"
⏸️ 4 选 1：1.重开 MR（回 Dev Stage）/ 2.放弃 Feature（shipped=abandoned）/ 3.暂时等待 / 4.其他

🔴 红线 #1 边界（v7.3.10+P0-32 修订）：
├── ✅ 允许：Step 8 push merge_target 仅 state.json 一文件、仅状态字段、零业务影响
├── 🔴 禁止：本地 git merge / git rebase / git cherry-pick 到 merge_target
├── 🔴 禁止：动业务代码 / 其他元数据文件（PRD/TC/TECH/UI 等）
├── 🔴 禁止：跨 Feature 改动 push merge_target
├── 🔴 禁止：第一段 push origin {merge_target}（仅第二段 Step 8 是允许的元数据 push）
├── 🔴 禁止：冲突解决（push feature 失败 → ⏸️ 用户决策，不重试、不降级）
├── 🔴 禁止：伪造 / 猜测 MR URL（git_host=unknown 时 mr_create_url=null + concerns 标注）
└── 🔴 禁止：第一段未完成 / 第二段未验证合并就跳过 worktree 清理或标记 completed

push FAILED 处理（第一段 push feature）：
└── ⏸️ 用户 2 选 1：a 手工处理后复跑 Ship / b 取消 Ship（回到 PM 验收态）

push FAILED 处理（第二段 Step 8 push merge_target）：
└── 自动降级到 feature 分支 push + state.concerns WARN（不阻塞流程）

第一段已完成、用户选了等待暂时退出（Step 3 选项 2）：
└── 下次进入会话，PMO 在 triage 识别 state.ship.phase == "pushed" → 不重跑第一段，直接展示 Step 3 暂停点
```

---

**🔴 功能完成时必须输出完整报告（v7.3.10+P0-56 单源化）**

完整报告由 PMO 自由组织（推荐含：交付物清单 / 流程完整性校验 / 质量 + 文档同步 Checklist / 耗时统计 / Ship 状态 / 下一步建议），但必须先满足下列 5 条完成资格判定。

PMO 完成资格判定（核心 5 条，必满足才能输出"✅ 已完成"状态）：

```
1. 流程完整性：所有强制 Stage 已通过（架构师 CR / QA CR / 单测 / Test Stage 前置确认 / PM 验收）
   → 简单 Bug 流程允许部分跳过（按 P0-36 Bug 流程契约）
2. 质量门禁：测试通过率 100% / RD 自查 ✅ / TC 覆盖率达标
   → Test 延后 → 标"⚠️ 待测试（批次 ID）" 不得标✅；Test 跳过 → 标"⚠️ 未测试（原因）"
3. 文档同步：PROJECT.md / KNOWLEDGE.md / 全景设计 / Schema 变更 已按需更新
4. Ship 状态：shipped=true（必含 MR URL + git_host）/ shipped=false（标"待 Ship"，不算完成）
5. state.json：current_stage=completed + ship.shipped 标记齐全
```

🔴 状态行角色必须是 PMO（不是 PM），格式：`🔄 Teamwork 模式 | 角色：PMO | 功能：F{编号}-{功能名} | 阶段：✅ 已完成`。

---

### 📚 本地知识库更新（PMO 自动判断）
**更新时机**：PMO 仅在以下两个节点判断是否需要更新知识库（不在每个阶段摘要时判断，避免冗余输出）
```
PMO 判断时机：
├── 功能完成报告后（Feature 流程结束时）
└── Bugfix 完成记录后（Bug 流程结束时）
```

**判断标准**：
```
✅ 应该记录到知识库：
├── 用户明确表达的偏好或规则
├── 开发中遇到的技术难点和解决方案
├── 返工的原因（以后可以避免）
├── 与外部系统集成的注意事项
├── 项目特定的命名/规范要求
└── 重要的设计决策和权衡

❌ 不需要记录：
├── 常规开发过程（无特殊经验）
├── 临时性问题（如网络超时）
├── 已有规范覆盖的内容（STANDARDS.md）
└── 通用的开发规范
```

**PMO 判断输出**：
```
📚 知识库更新判断
├── 时机：[Bugfix记录/功能完成]
├── 判断：✅ 有值得记录的经验 / ⏭️ 无需更新
├── 记录内容：[简述，如有]
└── 类型：技术/设计/流程/踩坑
```

**知识提取流程**（判断为需要更新时）：
```
PMO 判断需要更新
    ↓
回顾相关过程：
├── 技术决策：选择了什么方案？为什么？
├── 设计调整：用户有什么偏好/修改意见？
├── 问题解决：遇到了什么问题？如何解决的？
└── 项目特殊性：发现了什么项目特定的规则？
    ↓
提炼可复用知识
    ↓
追加到 docs/KNOWLEDGE.md
```

**经验总结格式**：
```markdown
### F{编号}-{功能名} / BUG-{编号}

**日期**: YYYY-MM-DD

#### 🔧 技术经验
- {经验1}

#### 🎨 设计经验
- {用户偏好/设计规范}

#### ⚠️ 踩坑记录
- **问题**: {描述}
- **解决**: {方案}

#### 💡 项目特定规则
- {规则}

---
```

**更新 KNOWLEDGE.md**：
```
1. 检查 docs/KNOWLEDGE.md 是否存在
   ├── 不存在 → 创建文件（使用 templates/knowledge.md 模板）
   └── 存在 → 追加新经验

2. 在功能经验详情部分追加新条目
```

**完整报告触发**：
- `/teamwork pmo`
- 用户说「项目进度」「整体情况」
- **功能完成时自动触发**（不需要用户请求）

---

## review-log.jsonl 管理规范（v7.3.10+P0-56 引用化）

> PMO 维护每个 Feature 的 review-log.jsonl，用于追踪各 stage 完成状态。
> 🔴 **schema + 写入时机 + Dashboard 格式**：详见 [templates/review-log.jsonl](../templates/review-log.jsonl)（schema 真相源）+ rules/gate-checks.md（流转校验时机）。
>
> PMO 核心职责（保留）：(a) 每 stage 返回后追加一行 / (b) dev-stage 后写入新 commit 时把旧 review/test 行标 stale=true / (c) /teamwork status 查询时读取并输出 Dashboard / (d) test-stage DEFERRED/SKIPPED 时同步标注 batch_id 或 skip_reason。

---

## 反模式（Anti-patterns）

| 反模式 | 正确做法 |
|--------|----------|
| 自己写代码修 bug | PMO 只分析/分发/总结，派发给 RD |
| "改动很小，我直接改了吧"（未经 PMO 分析 + 用户确认） | 🔴 即使 Micro 白名单内改动也必须先输出 PMO 初步分析 + Micro 准入检查 → ⏸️ 等用户确认走 Micro → 再由主对话内 PMO→RD 身份切换，由 RD 改动。禁止跳过"分析+确认"直接动手（v7.3.10+P0-20：代码写权仍归 RD，只是省 Subagent，主对话内身份切换+必读规范+cite）|
| RD 身份改动途中，用户追加"顺便再改一下 X" → 直接顺手改了 | 🔴 必须先跳回 PMO 身份重新做 Micro 准入检查：通过 → 输出增量分析 + ⏸️ 等用户确认 → 再切回 RD 执行；超出白名单 → 输出升级原因走敏捷或 Feature。禁止在 RD 身份下直接接收新需求，防止身份蠕变、Micro 越扩越大（v7.3.10+P0-20-B）|
| 身份切换后阶段摘要用 "我" / "PMO" / 泛指人称 | 🔴 身份切换后阶段摘要首句必须以「作为 RD，……」开头作为锚点，防止中途漂回 PMO 口吻（v7.3.10+P0-20-B）|
| 觉得走敏捷太重就跳过流程 | 评估是否符合 Micro 准入条件 → 符合走 Micro → 不符合走敏捷。不存在"太重就不走"的选项 |
| 跳过用户验收直接 commit/push | 任何流程（含 Micro）都必须用户验收后才能 commit/push |
| Subagent 启动只传路径不传内容 | 读取关键文件，将内容直接注入 prompt |
| 阶段完成后不输出摘要就流转 | 每个阶段必须先输出 PMO 摘要再决定流转 |
| Subagent 失败后无脑重试 | 分析失败原因（缺上下文/任务太大/真做不了），对症处理 |

### PMO 小改动决策树（遇到"改动很小"时必须走此路径）

```
PMO 判断改动范围很小
    ↓
自问：是否涉及逻辑变更？（条件分支/数据流/API 行为/业务规则）
    ├── 是 → 走敏捷需求流程（最低也是敏捷，不能更低）
    └── 否 → 改动类型是否在 Micro 白名单内？
        ├── 是 → 输出 Micro 准入检查 → ⏸️ 用户确认走 Micro
        └── 否 → 走敏捷需求流程
    ↓
🔴 Micro 流程外：PMO 禁止自己动手改代码，必须按流程派发
🟢 Micro 流程内（v7.3.10+P0-16）：用户确认后，PMO 自行判断——
   ✍️ 主对话以 RD 身份直接改（默认，白名单内零逻辑变更）
   🔀 判定执行中可能超出 Micro 白名单 → 升级 Plan 模式走敏捷或 Feature
🔴 "改动很小就跳过流程直接动手"仍是违规：必须先有 PMO 分析 + 用户确认
```
