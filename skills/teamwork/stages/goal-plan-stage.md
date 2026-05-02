# Goal-Plan Stage：需求定义（PRD 起草 + 多角色并行评审 + PM 回应循环，v7.3.10+P0-34 5 子步骤）

> 在用户确认流程类型后进入本 Stage。产出一份经过产品对齐 + 技术评审的合格 PRD。
> 🔴 契约优先：本文件规范 Input / Process / Output 三契约。执行方式由 AI 在 Plan 模式自主规划（见 SKILL.md「AI Plan 模式规范」）。

---

## 本 Stage 职责

产出经过产品方向对齐 + 多视角技术评审的定稿 PRD，为后续 Stage 锁定需求边界。PRD 中的 AC 必须结构化以便与测试强绑定。

---

## 可配置点清单（v7.3.10+P0-55 新增 — Triage 预定义，Stage 入口默认采纳）

| 可配置点 | 默认值 | 控制字段 | 决策时机 |
|---------|-------|---------|---------|
| `review_roles[]` | 见推荐表（基于 Feature 类型）| `state.goal_plan_substeps_config.review_roles[]` | triage Step 8 给 hint，Stage 入口实例化决策 |
| 各角色 `execution` | subagent / main-conversation（按文件数 + 上下文累积价值）| `state.goal_plan_substeps_config.review_roles[].execution` | Stage 入口实例化 |
| `pl_prioritized` | true（含 PL 时）| `state.goal_plan_substeps_config.pl_prioritized` | Stage 入口（业务方向锁死前 PL 先于其他角色）|
| `round_loop.max_rounds` | 3 | `state.goal_plan_substeps_config.review_round_max` | 防无限评审循环 |
| 子步骤 4 触发条件 | NEEDS_REVISION 或 SHOULD-fix concern（v7.3.10+P0-51）| 触发条件（spec 内嵌）| Stage 内运行时 |
| `hint_overrides` | null | `state.goal_plan_substeps_config.hint_overrides` | Stage 入口实例化偏离 hint 时 |

🔴 不变内核（不可配置）：5 子步骤序列（PRD 起草 → PL-PM 讨论 → 联合评审 → PM 回应 → 用户最终确认）+ severity 三级（MUST-fix / SHOULD-fix / NICE-to-have）+ DEFER 收紧规则 + 业务方向锁死硬规则。

---

## Input Contract

### 必读文件（按顺序）

```
├── {SKILL_ROOT}/agents/README.md                    ← 通用规范
├── {SKILL_ROOT}/stages/goal-plan-stage.md                ← 本文件
├── {SKILL_ROOT}/roles/pm.md                         ← PM 角色 + PRD 技术评审规范
├── {SKILL_ROOT}/roles/product-lead.md               ← PL 角色（讨论用）
├── {SKILL_ROOT}/templates/prd.md                    ← PRD 模板（含 AC 结构化 frontmatter）
└── {SKILL_ROOT}/standards/common.md                 ← 通用开发规范

条件必读（v7.3.9+P0-13 新增）：
└── {SKILL_ROOT}/templates/external-cross-review.md
    🟡 仅当 "external" in state.goal_plan_substeps_config.review_roles[].role 时必读（v7.3.10+P0-38：external 升格为评审角色，启用条件改为 review_roles[] 含 external）
    🟢 关闭时跳过，节省启动 token

可选（存在则读取）：
├── docs/PROJECT.md                                  ← 产品总览
├── docs/KNOWLEDGE.md                                ← 项目知识库
├── docs/architecture/ARCHITECTURE.md                ← 架构文档（技术评审参考）
└── design/sitemap.md                                ← 全景设计（有 UI 时参考）
```

### Key Context（PMO 必须逐项判断，无则写 `-`）

- 历史决策锚点：上游 Stage / CHG 记录 / Goal-Plan Stage 纪要中的决策
- 本轮聚焦点：重派或修订场景必填
- 跨 Feature 约束：与其他进行中 Feature 的冲突/兼容
- 已识别风险：来自 KNOWLEDGE.md / 预检 / 历史 Bug
- 降级授权：PL 不可用时是否可由 PM 单独推进等
- 优先级 / 容忍度：进度优先 / 质量优先 / 平衡

### 前置依赖

- PMO 初步分析已输出且用户已确认流程类型
- state.json.current_stage == "goal_plan"
- 无其他阻塞项（blocking.pending_user_confirmations 为空）
- **环境配置（v7.3.10+P0-27 重构）**：triage-stage Step 7.5 已探测 + 用户已在 triage 暂停点确认 `state.environment_config = { worktree_mode, branch, merge_target, base, dirty_resolution }`
- **Worktree**：state.environment_config.worktree_mode 决定模式；Goal-Plan Stage 入口自动按配置创建（详见下方「Stage 入口环境准备」），PRD/discuss/评审等产物均落在该 worktree 分支，不污染 main / staging

---

## Stage 入口环境准备（v7.3.10+P0-27 重构，无暂停点）

> 🟢 **v7.3.10+P0-27 重构说明**：原 v7.3.9 的「Goal-Plan Stage 入口 Preflight」（4 项硬门禁 + 用户确认暂停点）已删除。决策前置到 [triage-stage Step 7.5 + Step 8](./triage-stage.md)（用户在 triage 暂停点一次性确认环境配置），执行后置到本段（自动执行，**无暂停点**）。Feature 典型暂停点从 4-5 个降到 3-4 个。
>
> 🔴 **本段不暂停**。所有决策已在 triage 完成；本段只按 `state.environment_config` 自动执行 git 操作。仅在异常情况下（base 不可达 / 分支冲突 / stash 失败）走异常分支降级或暂停。

### 输入

`state.environment_config`（triage-stage Step 9 已写入）：
- `worktree_mode`: auto / manual / off
- `branch`: feature/{Feature 全名}
- `merge_target`: staging / main / master
- `base`: origin/{merge_target}
- `dirty_resolution`: stash / commit / force / null（null 表示 triage 时工作区已干净）
- `workspace_status_at_triage`: clean / dirty

### 自动执行序列

```bash
# Step 1: 处理工作区状态（按 triage 决定的 dirty_resolution）
case state.environment_config.dirty_resolution in
  "stash")  git stash push -m "auto stash before {Feature 全名}" ;;
  "commit") git status --porcelain ;;  # 用户在 triage 后已自行 commit；验证已干净
  "force")  ;;  # 用户授权强制继续，未提交改动可能丢失（state.concerns 已记录授权时刻）
  null)     ;;  # triage 时工作区已干净
esac

# Step 2: Fetch base
git fetch origin {state.environment_config.merge_target}
git rev-parse --verify "origin/{state.environment_config.merge_target}"

# Step 3: 创建 worktree（如启用）
if state.environment_config.worktree_mode in ["auto", "manual"]:
    git worktree add {worktree.path} -b {state.environment_config.branch} "origin/{state.environment_config.merge_target}"

# Step 4: 切到 worktree（如启用）
cd {worktree.path}
```

🔴 **关键约束**：`git worktree add` 必须显式指定 base（`origin/{merge_target}`），不能依赖隐式 HEAD。锁定 base 防止 Feature 产物诞生后 Ship Stage MR diff 夹杂他人改动。

🟢 **P0-3 懒装依赖模型**：worktree 创建**不触发**依赖安装（`npm install` / `pip install` / `go mod download`）。纯文档 Stage（Plan / Blueprint / Review）可在空壳 worktree 上完成；依赖安装延迟到 Dev / Test Stage 入口按需执行。

### 异常分支（仅异常时走，常规情况不暂停）

| 异常 | 处理 |
|------|------|
| base 分支不可达（fetch 失败 / 远端配置错） | BLOCKED → state.concerns 加 WARN + ⏸️ 暂停（异常分支） |
| 分支名冲突（triage 时未发现，竞态） | state.concerns + ⏸️ 暂停（让用户决策：续用 / 改名 / 删除重建） |
| worktree add 失败 | 按 worktree 降级链（auto → manual → off），写 state.concerns + 不暂停（继续 off 模式） |
| stash 失败 | state.concerns + ⏸️ 暂停（让用户人工处理） |

🔴 **常规情况自动流转，不打断用户**。仅异常分支才暂停。

### state.json 写入

环境准备完成后写入：

```json
{
  "environment_config": {
    "...": "（triage 写入的字段保持不变）",
    "executed_at": "<ISO 8601 UTC>",
    "worktree_created": true,
    "concerns": []
  }
}
```

🟢 v7.3.10+P0-27 删除原 `state.stage_contracts.plan_preflight` 字段（preflight 概念整体废弃）。

---

## 入口 Read 顺序（v7.3.10+P0-23 固定）

🔴 按以下顺序 Read，字节一致利于 prompt cache 命中。详见 [standards/prompt-cache.md](../standards/prompt-cache.md)。

```
Step 1: roles/pm.md, roles/product-lead.md             ← 角色层（L0 稳定）
Step 2: templates/prd.md                               ← 模板层（L0 稳定）
        [条件] templates/external-cross-review.md          （仅 review_roles[] 含 external，v7.3.10+P0-38）
Step 3: 无（Goal-Plan Stage 是 Feature 起点，无既有 L2 产物）
Step 4: {Feature}/state.json                           ← 🔴 最后，动态入口（L3）
```

🔴 R3 约束：state.json 入口 Read 1 次 → 中段 0 读写 → 出口 Read 1 次 + Write 1 次；全 Stage ≤ 5 次（含豁免）。

---

## Process Contract（v7.3.10+P0-34 重构：5 子步骤 + 评审循环；+P0-38 加入口实例化）

> 🟢 **v7.3.10+P0-34 设计**：原"PM 起草 PRD → PL-PM 讨论 → 多视角技术评审 → 整合反馈 → 用户确认" 4 步混合结构，重构为**5 子步骤 + 评审-回应循环**：PL 升格为评审角色之一与 RD/Designer/QA/PMO 平级，所有评审角色统一走「多角色并行评审 → PM 回应循环 → 全员通过判定」模式（最多 3 轮，超限触发用户决策）。
>
> 🔴 子步骤 2/3/4 是循环单元（评审→回应→判定），最多 3 轮。
>
> 🆕 **v7.3.10+P0-38 加入口实例化 / +P0-38-A 修订**：goal_plan_substeps_config 不在 triage 决策（triage 仅给骨架 + execution_hints 软建议），由**Goal-Plan Stage 入口的 PMO 基于已有 PRD 草稿状态 + execution_hints + state.available_roles**实例化决策。

---

### 🆕 Goal-Plan Stage 入口实例化（v7.3.10+P0-48 引用统一规范）

> 🔴 **遵循 [standards/stage-instantiation.md](../standards/stage-instantiation.md) 通用流程**（4 步：read state hints → 决策 active_roles + execution + round_loop → 输出 5 行 Execution Plan → 默认通道 / 标准通道判定）。

**Goal-Plan Stage 特定参数**：

- 候选 `active_roles`：PL / RD / QA / Designer / PMO / external（具体决策见下方"评审组合智能推荐表"）
- `key_outputs`：PRD.md（含 acceptance_criteria[]）
- 子步骤序列：见下方 "5 子步骤序列"（PRD 起草 → PL-PM 讨论 → 多角色联合评审 → PM 回应循环 → 用户最终确认）

**特殊例外**：无（plan-stage 完全套用 standards/stage-instantiation.md 通用规范）

---

### 主对话输出 Tier 应用（v7.3.10+P0-54 升级）

> 🔴 **遵循 [standards/output-tiers.md](../standards/output-tiers.md) 通用 Tier 1/2/3 规范 + 4 类反模式禁令**（履职报告 / state.json 复述 / 决策菜单膨胀 / 工程性切片暂停）。

**Goal-Plan Stage 特定 Tier 应用**：

- **Tier 1（永远输出）**：5 行 Execution Plan / 子步骤 5 ⏸️ 用户最终确认 PRD / 评审循环 verdict 切换 / NEEDS_REVISION 升级 round
- **Tier 2（命中折叠）**：KNOWLEDGE / ADR 命中（仅 round 1 起草时）/ 跨 Feature 冲突告警 / external 评审 ADOPT/REJECT 摘要
- **Tier 3（不输出，走 state.json）**：goal_plan_substeps_config 详细字段 / review_roles[] 各角色 execution / pm_response 历史轮次 / artifact_root / 各 review 的 generated_at

📎 **判定标尺（如要重新触发回来）**：
- 完成度表：如果出现"用户拿到 PRD 后投诉某段缺失"→ 修 PMO 校验，不加表
- state.json 复述：如果出现"用户写 state.json 时不知当前配置"→ 改进 state.json 渲染，不主对话再述
- 工程性切片暂停：如果出现"评审跑完后 PRD 大返工率 >30%"→ 修 PM 起草规范，不加暂停

---

### 🧭 Goal-Plan Stage 评审组合智能推荐表（🔴 v7.3.10+P0-43 / +P0-48 唯一权威源）

> 🔴 **本表是 Goal-Plan Stage 评审组合决策的唯一权威源**（v7.3.10+P0-43 迁自 roles/pmo.md，v7.3.10+P0-48 加单源化标注）。
>
> - PMO 在 Goal-Plan Stage 入口实例化 + triage Step 8 生成 execution_hints 时**必须以本表为唯一依据**
> - roles/pmo.md 仅引用本表，不得复述决策规则
> - 二者不一致时**以本表为准**，发现 roles/pmo.md 残留决策规则 → 在 concerns 记录漂移 + 同 patch 删除

**两处使用场景**：

```
1. triage Step 8 生成 execution_hints（软建议）：
   PMO 基于本表给 Goal-Plan Stage 写实施建议（文本形式，含动词、模型、理由）
   → 写入 execution_plan_skeleton.stages[plan].execution_hints

2. Goal-Plan Stage 入口实例化（硬决策）：
   PMO 读 execution_hints + 上游 PRD 草稿状态，结合本表决策 active_roles + execution
   + pl_prioritized + round_loop → 写入 goal_plan_substeps_config

   triage 时 hint 是软建议；Stage 入口决策可采纳/调整/否决
   （否决时必须在 goal_plan_substeps_config.hint_overrides 写文本说明原因，cite hint 原文）
```

#### Step 1：Feature 类型识别

PMO 综合以下信号判定 Feature 类型：

| 信号 | 大 Feature | 中 Feature | 纯技术 refactor | 敏捷需求 | Bug 修复 |
|------|----------|----------|---------------|---------|---------|
| 文件数 | ≥10 | 5-10 | 不限 | ≤5 | 通常 ≤3 |
| 跨子项目 | ✅ 倾向 | 单 | 视情况 | 单 | 单 |
| 业务变更 | 新业务逻辑 | 小变更 | 无（仅技术 refactor） | 方案明确 | 缺陷修复 |
| UI 变更 | 含 UI | 视情况 | 无 | 一般无 | 一般无 |
| 关键词 | "新功能 / 业务" | "增强 / 调整" | "refactor / 重命名 / 删字段 / 迁移" | "增加 / 改进" | "修复 / Bug" |
| change_id 状态 | locked / 含本 Feature | 同 | 通常 locked | 不一定关联 | 通常无 |

> 🔴 v7.3.10+P0-47：原"PRD frontmatter `prd_variant`"信号已删除（PRD 模板合并为统一通用模板）。Feature 类型识别用上述其他信号（文件数 / 跨子项目 / 业务变更 / UI 变更 / 关键词 / change_id）综合判断。

#### Step 2：评审角色推荐表

| Feature 类型 | 评审角色组合 | external 角色（review_roles[] 含 external 与否）|
|------------|------------|-------------------------|
| **大 Feature** | pl + rd + designer（含 UI）+ qa + pmo | ✅ 推荐启用（异质视角补盲，价值高） |
| **中 Feature** | pl + rd + qa + pmo（含 UI 加 designer） | 不启用（内部多视角已够） |
| **纯技术 refactor** | rd + qa（pl/designer/pmo 跳） | 不启用（无业务歧义，refactor 类不需异质视角） |
| **敏捷需求** | rd + qa | 不启用 |
| **Bug 修复** | rd | 不启用 |

🔴 **PMO 视角触发条件**：中以上 Feature（包括大 / 中）默认启用；小 Feature / 敏捷 / Bug 跳过（PMO 视角主要看跨 Feature 影响 + 流程合规，对小 scope 价值低）。

🔴 **Designer 视角触发条件**（双保险）：
- PRD frontmatter `requires_ui: true` → 启用
- PMO 在用户消息中识别 UI 关键词（"页面 / 按钮 / 弹窗 / 表单 / 交互 / UI / UX"等）→ 启用
- 两条任一命中即启用

🆕 **PL 优先权（v7.3.10+P0-34-C）**：

如 review_roles[] 包含 `pl`，**PMO 默认 `pl_prioritized: true`**——PL 评审先于其他角色 dispatch（不并行）。设计意图：

- 避免技术评审挤压业务对齐：RD 在业务方向尚未对齐时给"技术接口"finding，PM 一边改技术一边改业务，焦点切碎
- 业务先于技术：PL 收敛 → PMO 写 PRD frontmatter `business_direction_locked: true` → 其他角色基于锁死后的 PRD 评审
- 防止业务方向回炉：其他评审角色发现实现层与已锁死方向矛盾才能 high 严重度上升

**PL 优先权关闭场景**（`pl_prioritized: false`，退化为全并行）：
- 业务方向已在 product-overview / change-request 阶段锁死（PRD frontmatter 已带 `business_direction_locked: true`）
- 纯技术 refactor（不含 PL 评审角色，不适用本规则）
- 用户在 triage Step 8 显式选"全 Subagent"且明确表示业务清晰

PMO 在 triage Step 8 推荐时如启用 PL 优先权，须 cite："`pl_prioritized: true`（业务方向先于技术评审锁死）"。

#### Step 3：执行方式推荐（subagent / main-conversation）

PMO 按以下信号决定每个角色的执行方式：

| 角色 | 倾向主对话 | 倾向 Subagent |
|------|-----------|--------------|
| **PMO** | 审计性视角 + 项目累积上下文价值高 | 大 Feature 跨子项目时为保独立性 |
| **PL** | 小 Feature 业务上下文已 in-context | 中以上 Feature 业务视角独立性优先 |
| **RD** | 小 Feature scope 简单 | 中以上 Feature 评审独立性优先（fresh context 防鼓掌效应） |
| **QA** | 几乎从不 | 永远 Subagent（QA 视角独立性是核心价值） |
| **Designer** | 仅小 UI 改动 | 含完整 UI 设计变更时 |

**执行方式信号**：
- Feature 文件数 < 5 → 主对话倾向
- Feature 文件数 ≥ 10 → Subagent 倾向
- 跨子项目 → Subagent 倾向（避免 cross-context 污染）
- 角色需要项目累积上下文（PMO / 架构师视角）→ 主对话倾向
- token 预算紧 → 主对话倾向（少一次 Subagent 启动开销）

🔴 **小 Feature 默认主对话硬约束（v7.3.10+P0-43）**：
- 文件数 ≤5 + 单子项目 + 无 UI → review_roles[].rd / pl 默认 main-conversation（QA 仍 subagent / external 仍 external-shell）
- PMO 不允许"出于独立性偏好"把小 Feature 的 RD/PL 默认 subagent（违反推荐表 + 增加无谓 dispatch 成本）
- 实战反例（INFRA-F019：DB rename + 3-4 文件 + 单子项目）：PMO 把 RD 设成 subagent 不符合本档默认，应该 main-conversation

#### Step 4：决策点呈现（triage Step 8）

```markdown
## 🧭 Goal-Plan Stage 评审组合决策（v7.3.10+P0-34）

PMO 智能推荐（Feature: {feature_id}，类型：{type}，理由：{1-2 句}）：
- 评审角色 + 执行方式：
  - rd: subagent（评审独立性）
  - qa: subagent（QA 视角独立性必须）
  - pmo: main-conversation（审计性 + 累积上下文）
  - pl: ⏭️ 跳过（理由：planning 已 locked，业务无新增价值）
  - designer: ⏭️ 跳过（理由：无 UI 变更）
- external 角色: review_roles[] 是否含 external（影响 Goal-Plan Stage 评审独立异质视角）

💡 1. 采用推荐组合 💡
   2. 全角色 + 全 Subagent（最大独立性，~+10 min token 成本）
   3. 全角色 + 全主对话（最快，~-5 min，但削弱独立性）
   4. 自定义（角色 + 执行方式独立选）
   5. 其他指示
```

#### Step 5：用户选择 → state.json 写入

triage Step 9 创建 Feature state.json 时写入 `goal_plan_substeps_config.review_roles[]`（详见 `templates/feature-state.json`）。

#### 评审循环 + 超 3 轮处理

每轮评审完成后判定 overall_verdict：
- 所有 verdict ∈ {PASS, PASS_WITH_CONCERNS} → 通过，进入子步骤 5（用户最终确认）
- 任一 NEEDS_REVISION 且 round < 3 → Round N+1（PM 整合反馈 + 修订 PRD + 重新启动评审）
- round == 3 仍 NEEDS_REVISION → ⏸️ 用户决策：
  ```
  ⏸️ Goal-Plan Stage 评审循环已 3 轮，仍未全员通过。

  💡 1. 强制通过当前 PRD（state.concerns 加 WARN）💡
     2. 继续 Round 4（无上限）
     3. 修改 scope（回到 PRD 初稿，重启评审）
     4. abort Feature（state.shipped = abandoned）
     5. 其他指示
  ```

#### 硬规则

- 🔴 PMO 在 triage-stage Step 8 必输出本段（不可省略）
- 🔴 评审角色组合 + 执行方式由 PMO 推荐 + 用户在暂停点确认（auto 模式按推荐执行 + 显式宣告，参 P0-11-A）
- 🔴 评审循环最多 3 轮，超限必触发用户决策（业务决策不可豁免）
- 🔴 用户最终确认（子步骤 5）永远必做（即使 auto 模式也保留，参 P0-11-A）
- 🔴 P0-43：小 Feature 默认 main-conversation（不许偏离推荐表）

---

### Goal-Plan Stage 子步骤序列（v7.3.10+P0-44 重构：5 步精简版）

> 🟢 **v7.3.10+P0-44 重构原则**：把"事后多角色独立评审"前置为"事前 PM 起草规范" + "PL-PM 业务讨论" + "QA+RD+Designer 主对话联合评审 ∥ external 并行"。降低 dispatch 数 + 减少评审循环，预估典型 Feature 耗时减半。

| 子步骤 | 名称 | 启用条件 | 暂停点 | 产物 |
|--------|------|---------|-------|------|
| 1 | PM 按起草规范写 PRD | ✅ 永远必做 | 🚀 自动 | `PRD.md`（draft + 含产品/AC 视角）|
| 2 | PL-PM 讨论（业务方向锁死） | 🟡 **条件启用**（`pl ∈ review_roles[]`）| 🚀 自动 | `PRD-REVIEW.md.reviews[].pl_rounds[]`（v7.3.10+P0-51 单源化，删 discuss/ 文件）+ `PRD.md` frontmatter `business_direction_locked: true` |
| 3 | 联合评审（QA + RD + Designer? + external?）∥ external 并行 | ✅ 永远必做（active_roles 由入口实例化决策）| 🚀 自动 | `PRD-REVIEW.md`（reviews[] = qa, rd, designer?, external?）|
| 4 | PM 回应 + 修订 PRD | 🟡 仅当评审有 NEEDS_REVISION 或 ≥1 个 SHOULD-fix concern 时触发（v7.3.10+P0-51 扩展）| 🚀 自动（超 3 轮 ⏸️）| `PRD.md`（修订）+ `PRD-REVIEW.md`（pm_response + adversarial_self_check）|
| 5 | 用户最终确认 | ✅ 永远必做 | ⏸️ 用户确认 | 用户回 ok / 反馈（v7.3.10+P0-49-A 二选一姿态）|

🔴 **暂停点分类（v7.3.10+P0-51 清晰化）**：
- **核心暂停点（理想路径）**：仅 1 个（子步骤 5）
- **异常暂停点**：(a) 评审循环超 3 轮 → 用户决策升级 / (b) PL-PM 讨论分歧锁死失败 → 用户拍板业务方向 / (c) Stage 入口实例化严重偏差（standards/stage-instantiation.md）→ 5 选 1
- 异常暂停**不算工程性切片**——业务方向锁定失败 / 评审循环不收敛是真实异常分支，不是预防性切片暂停

📎 **子步骤 2 启用条件说明（v7.3.10+P0-51 改造）**：
- `pl ∈ review_roles[]` → 子步骤 2 启用，PL-PM 讨论锁死业务方向后进子步骤 3
- `pl ∉ review_roles[]` → 子步骤 2 跳过，子步骤 1 起草完直接进子步骤 3 联合评审
- 典型不启用 PL 的 Feature：Bug 修复 / 纯技术 refactor / 敏捷需求（业务方向已在 product-overview 锁定）

---

### 子步骤 1：PM 按起草规范写 PRD（v7.3.10+P0-49 改造：背景段从 triage 上下文继承，主体段 elaborate）

**意图段继承（v7.3.10+P0-49 新增）**：

triage 阶段的"📌 我对你这次需求的理解"段（Why now / Assumptions / Real unknowns）已经过用户双对齐确认 + 在主对话上下文内。PM 起草 PRD 时**直接把这三件继承到 PRD 背景段**（用户故事段之上），不重新理解、不重新跟用户对齐。

```
PRD.md 背景段（继承 triage 意图）
├── Why now：直接抄 triage 意图段
├── Assumptions：直接抄 triage 意图段
├── Real unknowns：抄 triage + 子步骤 2-4 评审中可能演进
│   └── 用户已拍板的 unknown → 标"已决"+ 决议结果（triage 双对齐时已收的"我已拍板"信号）
│   └── 评审中讨论的 unknown → 进 OQ list
└── 上游 KNOWLEDGE / ADR 链接（如适用）

PRD.md 主体（PM elaborate）
├── 用户故事 / 使用方故事（按需必填，参 templates/prd.md）
├── 验收标准（AC list，从 triage 粗 AC 种子扩到完整 list）
├── 影响范围 + 跨子项目依赖 + 业务风险
└── UI 用户故事（如 requires_ui=true）
```

🔴 **意图段继承的边界**：

- **不重新跟用户对齐意图**：意图层在 triage 已锁，PM 起草时直接落到 PRD；如果 PM 起草过程中发现 triage 意图理解有遗漏 / 偏差 → 标记 concerns，子步骤 2 PL-PM 讨论或子步骤 3 评审中处理（不弹中间暂停跟用户重新对齐意图）
- **不弹"PRD v0/v1"中间暂停**：PRD 背景段从 triage 继承意图后**直接 elaborate 主体一次性出**，子步骤 1 是单次产出（不拆 v0/v1 两步）
- **意图段在 PRD 中可演进**：评审循环中可能修订 Why now / 加 Assumptions / 减 Real unknowns —— 这是 PRD 评审正常输出，不破坏 triage 意图锁。git diff PRD.md first commit vs final commit 看意图段如何从 triage 原始理解演化到最终规格

📎 **替代了什么**（v7.3.10+P0-49 减负）：

- 删除原"PM 起草前先做意图理解"隐式职责（已转移到 triage）
- 删除原 PRD 背景段"从 0 起草"工作量（背景段直接从 triage 继承，PM 工作量减半）
- 删除子步骤 1 内部任何"PRD v0 → 用户意图对齐 → PRD v1"暂停（之前讨论的中间方案已废弃）

---

PM 按 `roles/pm.md` + `templates/prd.md` 起草 PRD 初稿。

#### 🔴 PM 起草规范 checklist（v7.3.10+P0-51 单源化）

> **PM 起草规范权威源**：[templates/prd.md § PM 起草规范 checklist](../templates/prd.md)（含通用 checklist + UI 用户故事维度 + PRD 不写什么边界 + 起草后自查）。本文件不复述 checklist 全文，避免主对话重复述 3 遍（起草时 + 自查时 + PRD-REVIEW pm_self_check）。

🔴 **PM 起草核心约束**（cite templates/prd.md 简版）：
- 起草前 grep 关键词 + Read 3-5 个相关核心模块（5-10 min · 只读不输出 brief · v7.3.10+P0-73 新增）
- PRD 仅回答"做什么 + 为什么"（产品/业务视角）
- 技术/测试/视觉细节 → TECH.md / TC.md / UI Design Stage（v7.3.10+P0-46 边界）
- 起草后自查 → 写 `PRD-REVIEW.md.reviews[role=pm].pm_self_check = {checklist_passed: bool, code_context_read: bool, failed_items: [...], notes: "..."}`，不复述 checklist 全文

---

### 子步骤 2：PL-PM 讨论（业务方向锁死，v7.3.10+P0-51 条件启用 + 单源化）

> 🟡 **启用条件（v7.3.10+P0-51 改造）**：仅当 `pl ∈ state.goal_plan_substeps_config.review_roles[]` 时启用本子步骤；不含 PL 的 Feature（Bug 修复 / 纯技术 refactor / 敏捷需求）跳过本子步骤，子步骤 1 完成后直接进子步骤 3。

> 🟢 **v7.3.10+P0-44 恢复 v7.3.x 模式 + P0-51 单源化**：原 P0-34 把 PL 升格为评审角色（独立 finding），实战中 PL 视角的对抗深度需要"多轮对话"才能挖掘出来。本次回归 v7.3.x 多轮讨论模式：PL 提 finding → PM 回应 → PL 反驳 → 收敛或显式分歧。**v7.3.10+P0-51 单源化**：删 discuss/PL-FEEDBACK-R{N}.md / discuss/PM-RESPONSE-R{N}.md 双源文件，所有讨论轮次集中写到 `PRD-REVIEW.md.reviews[].pl_rounds[]` 数组（schema 见 templates/prd.md）。

#### 流程

```
Round 1：
  ├── PL 读 PRD + product-overview + change-request（如有）+ KNOWLEDGE
  ├── PL 输出 finding 段（业务方向 / 流程完整性 / 中台子项目通用性）→ 写 PRD-REVIEW.md.reviews[role=pl].pl_rounds[1].pl_feedback
  └── PM 回应（含 ADOPT/REJECT/DEFER + adversarial_self_check）→ 写 .pl_rounds[1].pm_response

Round 2（PL 仍有反驳）：
  ├── PL 读 PRD（修订）+ R1 历史 → 输出反驳 / 质询 → 写 .pl_rounds[2].pl_feedback
  └── PM 二次回应 → 写 .pl_rounds[2].pm_response

Round 3（同上，硬上限）

收敛判定（写 .pl_rounds[N].verdict）：
  ├── verdict=CONVERGED（PL 满意）
  │   → 业务方向锁死：写 PRD frontmatter `business_direction_locked: true` + 时间戳
  │   → 进入子步骤 3
  ├── verdict=DISAGREEMENT（业务方向有分歧）
  │   → 写 PRD「业务方向锁定」段含分歧记录 + 上升给用户决策（异常暂停点）
  │   → ⏸️ 用户拍板分歧（异常暂停点）
  └── 3 轮未收敛 → ⏸️ 用户决策（force-converge / continue-round-4 / modify-scope / abort）
```

#### 产物（v7.3.10+P0-51 单源化到 PRD-REVIEW.md）

所有 PL-PM 讨论轮次集中写到 `PRD-REVIEW.md.reviews[role=pl].pl_rounds[]` 数组：

```yaml
reviews:
  - role: pl
    pl_rounds:                   # v7.3.10+P0-51 新增：多轮讨论日志
      - round: 1
        pl_feedback: "..."        # PL 反馈文本（业务方向 / 流程完整性 / 中台通用性）
        pm_response:              # PM 回应
          adopt: ["..."]
          reject: ["..."]
          defer:
            - item: "..."
              category: business-decision
              category_explanation: "..."
          adversarial_self_check: "..."
        verdict: null              # null（继续讨论）/ CONVERGED / DISAGREEMENT
      - round: 2
        ...
    final_verdict: CONVERGED      # 最终收敛状态
    final_verdict_at: "2026-04-29T..."
```

🔴 **v7.3.10+P0-51 单源化**：撤销 P0-43 废止 / P0-44 恢复 discuss/ 文件双源。所有讨论日志单源在 PRD-REVIEW.md.reviews[].pl_rounds[]，**不再建 discuss/ 子目录**。理由：双源（discuss/ + PRD-REVIEW）会导致 PL 意见维护两份，改 PRD 时漂移风险高。

#### 业务方向锁死硬规则（保留 P0-34-C 价值）

- 🔴 PL 声明 CONVERGED 后才能进入子步骤 3
- 🔴 业务方向锁死后写 PRD frontmatter `business_direction_locked: true`（v7.3.10+P0-48：时刻由 state.json 单一记录，PRD frontmatter 不重复）
- 🔴 子步骤 3 评审角色基于已锁死 PRD 评审，禁止回炉业务方向

---

### 子步骤 3：QA+RD+Designer(可选) 主对话联合评审 ∥ external 并行

> 🟢 **v7.3.10+P0-44 重构**：取消 P0-34/P0-43 的"多角色独立 subagent 评审"模式。改为：
> - QA / RD / Designer 在 PMO 主对话内连续身份切换（节省 subagent dispatch 冷启动税）
> - external 后台 shell 并行（保留异质独立视角）

> 🔴 **v7.3.10+P0-46 评审 scope = PRD 范围**：本子步骤评审的是 PRD（review_scope = "prd"），仅审产品视角。技术实现 / 测试用例细节在 Blueprint Stage 评审（review_scope = "blueprint"）。

#### 🔴 评审 scope = PRD 范围（v7.3.10+P0-46 新增）

**RD 评审 PRD 时关注点**（产品视角，不是技术实现细节）：
```
✅ 该审：
  ├── PRD 中是否有技术不可行的 AC（如"100ms 延迟"但调用第三方 API 平均 500ms）
  ├── PRD 中是否有业务方向上的技术风险（如新业务方向需要重构现有架构）
  ├── 跨子项目依赖标注是否完整（业务层面，不是接口层面）
  └── PRD 描述的功能行为是否与既有系统冲突（如复用既有功能 / 已有 ADR）

❌ 不审（移到 Blueprint Stage TECH 评审）：
  ├── 接口 schema 设计 / 数据模型设计
  ├── 异常处理实现细节（重试 / 降级 / 兜底）
  ├── 性能实现方案
  └── 复用既有库 / 模式
```

**QA 评审 PRD 时关注点**（产品视角，不是测试用例细节）：
```
✅ 该审：
  ├── AC 是否清晰可测试（QA 能从中转化为测试用例 = AC 描述足够清晰）
  ├── 边界场景的业务行为是否完整（用户感知的异常 / 错误处理）
  ├── AC 之间是否有矛盾或重叠
  └── 验收方法是否合理（如"用户能登录"应明确"登录后能看到 X / Y / Z"）

❌ 不审（移到 Blueprint Stage TC 评审）：
  ├── 具体测试用例规划
  ├── 集成测试规划 / 性能测试规划 / ROLLBACK 测试
  └── 测试数据设计
```

**Designer 评审 PRD 时关注点**（产品视角，不是视觉细节）：
```
✅ 该审：
  ├── PRD 的用户故事是否完整（normal / empty / loading / error 状态）
  ├── 涉及页面 / 组件清单是否覆盖
  └── 交互改动描述是否清晰

❌ 不审（移到 UI Design Stage Designer）：
  ├── 视觉风格约束 / token 设计
  ├── 全景同步细节
  └── 具体视觉规范
```

PM 起草规范已让 PRD 质量大幅提升（产品视角 checklist 覆盖），子步骤 3 联合评审仅审 PRD 范围的边界 finding。

#### 调度顺序（PMO 主对话身份切换）

```
1. PMO → QA 切换（cite roles/qa.md + standards/testing.md）
   └── 输出 QA finding（测试覆盖 / 边界场景 / 测试可行性 / 集成测试需求）
   └── 写到 PRD-REVIEW.md.reviews[].qa

2. PMO → RD 切换（cite roles/rd.md + standards/{frontend|backend}.md）
   └── 输出 RD finding（技术可行性 / 接口设计 / 数据模型 / 异常处理）
   └── 写到 PRD-REVIEW.md.reviews[].rd

3. 🟡 PMO → Designer 切换（仅 requires_ui=true 或 UI 关键词命中）
   └── cite roles/designer.md + design/sitemap.md（如有）
   └── 输出 Designer finding（视觉一致性 / 交互 / 全景同步 / 状态流完整性）
   └── 写到 PRD-REVIEW.md.reviews[].designer

并行：external 评审（review_roles[] 含 external 时）
   ├── PMO 在调度 QA 之前用 background bash 启动 external CLI shell
   ├── codex CLI / claude CLI 评审 PRD
   ├── PMO 主对话同时做 QA→RD→Designer 评审（不阻塞）
   └── external 完成后写 external-cross-review/prd-{model}.md
       PMO 收集到 PRD-REVIEW.md.reviews[].external 段
```

#### Designer 触发条件（双保险 + v7.3.10+P0-51 中途补启用）

✅ 任一命中即启用 Designer 评审：

- PRD frontmatter `requires_ui: true` → 启用
- PMO 在用户消息或 PRD 内容中识别 UI 关键词（"页面 / 按钮 / 弹窗 / 表单 / 交互 / UI / UX / 设计 / 样式 / 布局" 等）→ 启用

🆕 **中途补启用机制（v7.3.10+P0-51 新增）**：

triage 阶段或 Plan 入口实例化未启用 Designer，但 PM 起草过程中发现需要 UI（triage 漏识别 / PRD elaborate 后才暴露 UI 触点）：

- PM 在 PRD frontmatter 标 `requires_ui: true` + 在 concerns 段写"UI 触点：…"
- PMO 在子步骤 3 评审 dispatch 前检测 PRD frontmatter `requires_ui: true` 且 `designer ∉ active_roles[]` → 触发"补启用"：
  - 写 `state.goal_plan_substeps_config.hint_overrides += "+designer (中途补启用，PM 起草发现 UI 触点)"`
  - 加 `designer` 到 active_roles
  - 主对话一行说明"补启用 Designer：PM 起草发现 UI 触点，自动加入子步骤 3 评审"（不弹暂停，自动决策属轻微偏差）
- 不命中 → Designer 视角折叠到 PM 起草规范的"UI 影响"维度（PM 写 PRD 时主动确认）

📎 设计意图：Designer 启用决策**前置在 triage / Plan 入口最准**，但实战中 PM 起草细化 PRD 时可能暴露 triage 漏识别的 UI 触点。补启用机制 = 不让 Designer 决策过早锁死，保留 PM 起草中调整的灵活性。

#### 主对话身份切换硬规则（保留 P0-20-B 第一人称锚点）

- 🔴 切换前必须 Read 对应 `roles/{id}.md`（QA / RD / Designer）
- 🔴 cite 1-2 句关键要点（证明真实读，非凭记忆换名头）
- 🔴 阶段摘要首句以「作为 QA / RD / Designer，……」开头（身份锚点）
- 🔴 输出 finding 后切回 PMO（"作为 PMO，整合……"）

#### external 并行实施（v7.3.10+P0-44 新增）

```bash
# PMO 在子步骤 3 入口启动 external（伪代码）：
if "external" in goal_plan_substeps_config.review_roles[].role:
    # 后台启动 external CLI（不阻塞主对话）
    bash run_in_background=true \
      "codex --profile prd-reviewer ... > external-cross-review/prd-codex.md 2> stderr.log"

    # PMO 主对话立即开始 QA → RD → Designer 切换评审
    # external 与 QA+RD+Designer 真并行

    # QA+RD+Designer 完成后，PMO 等待 external 完成（如未完成）
    # 整合 finding
```

🔴 external 异质性硬约束（保留 P0-38 / P0-38-A）：
- host_main_model = claude → external CLI 必须是 codex（异质）
- host_main_model = codex → external CLI 必须是 claude（异质）
- 同源 → external 不在 review_roles[] 里

---

### 子步骤 4：PM 回应 + 修订 PRD（保留 P0-34-A/B 对抗自查 + DEFER 收紧 + v7.3.10+P0-51 SHOULD-fix 触发）

#### 触发条件（v7.3.10+P0-51 扩展）

子步骤 4 启用条件 ANY：

- 任一 review verdict == NEEDS_REVISION（强制响应）
- 任一 review 含 ≥1 个 `severity: SHOULD-fix` concern（即使 verdict == PASS_WITH_CONCERNS，也必须响应）
- PASS / PASS_WITH_CONCERNS 但 concerns 全是 `severity: NICE-to-have` → **不触发 PM 回应**，子步骤 4 跳过，直接进子步骤 5（concerns 仍记录在 PRD-REVIEW，由用户在子步骤 5 决定是否采纳）

📎 **severity 分级**（PRD-REVIEW.md.reviews[].findings[].severity）：
- `MUST-fix` → 等同 NEEDS_REVISION（review verdict 必须 NEEDS_REVISION）
- `SHOULD-fix` → review verdict = PASS_WITH_CONCERNS，但 PM 必须响应（v7.3.10+P0-51 扩展）
- `NICE-to-have` → review verdict = PASS_WITH_CONCERNS / PASS，PM 响应可选

PM 整合 PRD-REVIEW.md.reviews[] 所有视角的 finding（QA / RD / Designer? / external?），对每条触发响应的 finding 给 pm_response：

#### 响应规则（保留 P0-34-A）

```
foreach finding in PRD-REVIEW.md.reviews[].findings WHERE severity ∈ {MUST-fix, SHOULD-fix}:
  pm_response.action ∈ {ADOPT, REJECT, DEFER}

  ADOPT → 修订 PRD.md + 写 pm_rationale "已修订：{改了什么 + PRD §X.Y 段落引用}"
  REJECT → 不改 PRD + 写 pm_rationale "反方论据为何不成立 + 替代方案"
  DEFER → 仅允许 category=business-decision；其他类别禁止（P0-34-A 收紧）
```

#### 对抗自查（保留 P0-34-B）

```
每条 ADOPT/REJECT 必含 adversarial_self_check 段（≥2 句反方论据模拟）：
  站在 finding 提出方视角写最强反驳论据，再写最终 response
```

#### PMO 校验（子步骤 4 完成后）

- 扫描所有 DEFER 项的 category 一致性 → 违规打回 PM 重做（P0-34-A）
- 扫描所有 ADOPT/REJECT 项的 adversarial_self_check 字段（≥2 句具体内容）→ 违规打回（P0-34-B）
- 校验通过 → 写 state.goal_plan_substeps_config.{defer_audit_passed, adversarial_check_passed}

---

### 子步骤 5：用户最终确认 PRD（⏸️ 核心暂停点，理想路径下唯一暂停点）

#### 用户审视

```
PRD.md（终稿，business_direction_locked=true）
PRD-REVIEW.md（含 reviews[] 全部 + PM 回应）
PMO 摘要（评审循环纪要 + finding 汇总 + 关键决策）
```

#### 决策选项

```
⏸️ Goal-Plan Stage 用户最终确认

请选择：
1. ✅ PRD 通过 → 进入 Blueprint Stage 💡
2. PRD 修改 → 列出修改点（AC / scope / 决策项）
3. 重启评审循环（如对评审结论有异议）
4. 其他指示
```

用户回 1 → state.current_stage = "blueprint"（如 requires_ui=true → ui_design）→ 转入下一 Stage。

---

### 过程硬规则（v7.3.10+P0-44 修订）

- 🔴 **PM 起草规范 checklist 必读必填**（v7.3.10+P0-44 新增）：起草前必读本段 + standards/{相关}.md，起草后必做自查
- 🔴 **角色规范必读且 cite**：PMO 主对话身份切换前，必须先 Read 对应 `roles/{id}.md`，并 cite 关键要点 + 第一人称锚句开头
- 🔴 **多视角独立性**：主对话身份切换模式靠 cite + 锚句自律；外部模型评审 fresh shell 物理隔离
- 🔴 **PM 回应完整性**：每条 NEEDS_REVISION finding 必须有 pm_response（ADOPT/REJECT/DEFER + rationale + adversarial_self_check）
- 🔴 **DEFER 严格收紧（P0-34-A）**：仅允许 category=business-decision；技术/业务一致性/UX/质量类禁止 DEFER
- 🔴 **评审循环上限**：最多 3 轮，超限必触发用户决策
- 🔴 **PRD 质量下限**：不能留 TBD / 待补充；验收标准必须量化可验证；AC 结构化
- 🔴 **PL-PM 讨论收敛 / 业务方向锁死**：进入子步骤 3 前 business_direction_locked 必须为 true
- 🔴 **Stage 完成前 git 干净** → 统一遵循 [rules/gate-checks.md](../rules/gate-checks.md)

### 多视角独立性要求

- QA / RD / Designer 主对话评审：cite roles/{id}.md + 第一人称锚句 + 不引用其他视角已做判断（自律保证）
- external 评审：fresh shell 物理隔离 + frontmatter `files_read` 不得包含 PRD-REVIEW.md / discuss/* / pmo-internal-review.md
- PL-PM 讨论：discuss/* 文件独立产出，不引用 PRD-REVIEW.md（讨论先于评审）

---

## Output Contract

### 必须产出的文件

| 文件路径 | 条件 | 格式 | 必需字段 |
|---------|------|------|---------|
| `{Feature}/PRD.md` | 🔴 必需 | Markdown + YAML frontmatter | `feature_id`, `acceptance_criteria[]` (id, description, priority), 交付预期, 影响范围 |
| `{Feature}/PRD-REVIEW.md` | 🔴 必需 | Markdown | 内部视角的评审意见（按 review_roles[] 角色组合）+ 汇总问题清单；review_roles[] 含 external 时追加尾部「外部模型交叉评审整合」section（逐条 ADOPT/REJECT/DEFER），不含 external 时写"external 评审角色未启用" |
| `{Feature}/pmo-internal-review.md` | 🟡 仅 Codex 开启时必需 | Markdown | PMO 自身视角评审（≥3 条实质 finding，Codex dispatch 的前置条件）|
| `{Feature}/external-cross-review/prd-{model}.md` | 🟡 仅 Codex 开启时必需 | Markdown + YAML frontmatter | `perspective: external-codex`, `target: prd`, `generated_at`, `files_read[]`, `findings[]`（含 C1-C6 checklist 分类）, `findings_summary` |
| `{Feature}/discuss/PL-FEEDBACK-R{N}.md` | ❌ v7.3.10+P0-43 废止 | — | 旧 v7.3.x「PL-PM Teams 讨论」遗留契约。P0-34 后 PL 升格为评审角色，finding 应统一在 `PRD-REVIEW.md` frontmatter `reviews[].pl.findings[]`，PM 回应统一在 `reviews[].findings[].pm_response`。**禁止产出本文件**（避免 PRD-REVIEW.md / discuss 双重产物） |
| `{Feature}/discuss/PM-RESPONSE-R{N}.md` | ❌ v7.3.10+P0-43 废止 | — | 同上 |

> 🟡 external 条件说明（v7.3.10+P0-38）：`"external" in goal_plan_substeps_config.review_roles[].role` 时 pmo-internal-review.md + external-cross-review/prd-{model}.md 为必需产物；不含 external 时两份文件不产出，PRD-REVIEW.md 尾部声明"external 评审角色未启用"即可。

### 机器可校验条件

- [ ] PRD.md frontmatter 可 YAML 解析（`yq '.feature_id' PRD.md` 成功）
- [ ] `acceptance_criteria[]` 至少 1 条，每条有 id/description/priority
- [ ] 无 TBD / 待补充 / TODO（`grep -iE "TBD|待补充|TODO" PRD.md` 为空）
- [ ] 多视角评审 4 个内部视角都有意见（或显式标注"无意见"+ 理由）
- 🟡 以下校验仅当 `"external" in state.goal_plan_substeps_config.review_roles[].role` 时生效（v7.3.10+P0-38）：
  - [ ] pmo-internal-review.md 存在且含 ≥3 条 finding（Codex dispatch 前置）
  - [ ] external-cross-review/prd-{model}.md frontmatter 可解析且 `perspective == "external-codex"`
  - [ ] external-cross-review/prd-{model}.md 的 `files_read` 不包含 PRD-REVIEW / discuss/ / pmo-internal-review（`grep -E "PRD-REVIEW\|discuss/\|pmo-internal" external-cross-review/prd-{model}.md` 为空）
  - [ ] PRD-REVIEW.md 尾部「外部模型交叉评审整合」section 对每条 finding 均有 ADOPT/REJECT/DEFER 标记 + 理由
  - [ ] Codex 降级场景：若 Codex 未执行，state.json.concerns 或 PRD-REVIEW.md 需显式记录 skip_reason
- 🟢 若 `external ∉ state.goal_plan_substeps_config.review_roles[]`（v7.3.10+P0-51 改 `state.external_cross_review.plan_enabled == false` 为 review_roles 单源判定）：
  - [ ] PRD-REVIEW.md 尾部显式声明"外部模型评审未启用（external ∉ review_roles）"，不产出 pmo-internal-review.md / external-cross-review/prd-{model}.md

### Done 判据（v7.3.10+P0-34 重构）

- 所有产出文件存在且通过格式校验
- PRD-REVIEW.md `overall_verdict ∈ {PASS, PASS_WITH_CONCERNS}`（所有 review_roles 均通过）
- 评审轮次 `review_round <= 3`（超出走用户决策，记录到 `review_round_overflow_decision`）
- PM 已对每条 finding 给出 ADOPT / REJECT / DEFER 响应（`pm_response` 完整）
- `state.json.stage_contracts.goal_plan.output_satisfied = true`

### 返回状态

| 状态 | 条件 | 后续 |
|------|------|------|
| ✅ DONE | 产出完整 + 全员 PASS + PM 响应完整 | PMO ⏸️ 用户最终确认 PRD |
| ⚠️ DONE_WITH_CONCERNS | 全员通过但有 PASS_WITH_CONCERNS / DEFER 项 | PMO ⏸️ 用户逐项决策 |
| 🔁 ROUND_OVERFLOW | 评审循环超出 3 轮 | PMO ⏸️ 4 选 1（force-pass / continue-round-4 / modify-scope / abort）|
| 💥 FAILED | 需求不清晰无法产出 | 返回错误 + 部分产出 |

---

## AI Plan 模式指引

📎 Execution Plan 4 行格式（含 Estimated）→ [SKILL.md「AI Plan 模式规范」](../SKILL.md#-ai-plan-模式规范v73-新增)。默认 approach → [agents/README.md §一 执行方式与模型](../agents/README.md)。

本 Stage 默认 `main-conversation`（多视角 prompt 切换 + 用户讨论）。典型偏离：需求极清晰、无用户介入 → `subagent`。

**Expected duration baseline（v7.3.10+P0-34）**：30-60 min（主对话 / 含多角色并行评审 + PM 回应循环）；评审组合精简 + 需求清晰单轮通过可降至 20-30 min；评审循环触达 Round 3 上限可达 90 min+。AI 在 Execution Plan 的 `Estimated` 字段按本 Feature 规模（预期 AC 数、评审角色数、复杂度）校准。

---

## Worktree 集成（PMO 执行，v7.3.8 从 Dev Stage 前移至此）

```
触发时机：用户确认流程类型 → 进入 Goal-Plan Stage 之前（flow-transitions.md 第 11 行）

worktree 策略（从 .teamwork_localconfig.md 读取）：
├── off → 跳过，Plan 产物落在当前分支
├── manual → PMO 提醒用户创建后再继续
└── auto → PMO 自动创建 + 切换 + 记录 state.json

worktree 路径解析（v7.3.10+P0-39 / +P0-42 硬规则强化）：
  1. 读 .teamwork_localconfig.md 的 worktree_root_path（默认 .worktree）
  2. 实际路径拼接：{worktree_root_path}/{Feature 全名}
     示例：.worktree + AUTH-F042-email-login → .worktree/AUTH-F042-email-login
  3. 路径合法性校验（创建前）：
     ├── 根目录不能是已 commit 的 git 工作目录（除 .gitignore 包含目录）
     ├── 父目录必须存在或可创建
     └── 拼接后路径不能与现有文件冲突
  4. 校验失败 → state.concerns 加 BLOCK + ⏸️ 用户决策（改路径 / 改 manual / 改 off）

🔴 **v7.3.10+P0-42 硬规则强化（基于实战 case 反例）**：

```
❌ 禁止偏离 P0-39 默认路径：
   ├── 禁止用项目历史 / 团队约定的路径（如 .claude/worktrees/）
   ├── 禁止子目录加 feature- 前缀（worktree path 仅用 {Feature 全名}，不加任何前缀）
   ├── 禁止"上次也是这么用的"作为偏离理由
   └── 唯一合法的路径来源：localconfig.worktree_root_path 字段（缺失则硬默认 .worktree）

✅ 合法路径示例：
   localconfig.worktree_root_path = .worktree（默认 / 缺失硬默认）
     → worktree path = .worktree/AUTH-F042-email-login

   localconfig.worktree_root_path = ../.repo-worktrees（用户自定义）
     → worktree path = ../.repo-worktrees/AUTH-F042-email-login

❌ 实战反例（INFRA-F019 case）：
   PMO 用了 .claude/worktrees/feature-INFRA-F019-conversions-offer-id-rename
              ↑ 项目历史约定（旧）        ↑ 多了 feature- 前缀（违反 P0-39 模板）
   正确：.worktree/INFRA-F019-conversions-offer-id-rename
   修复：localconfig 没配 worktree_root_path 时硬默认 .worktree（不允许沿用项目历史）
```

🔴 **PMO 校验**：进入 Goal-Plan Stage 入口创建 worktree 前，必须 cite localconfig.worktree_root_path 字段或确认硬默认值（.worktree），违反则视为流程违规。

auto 模式命令（v7.3.10+P0-39 默认路径变更：{worktree_root_path}/{Feature 全名}，默认 .worktree/）：
  git fetch origin {merge_target}
  git worktree add {worktree_root_path}/{Feature 全名} -b feature/{Feature 全名} origin/{merge_target}
  cd {worktree_root_path}/{Feature 全名}

state.json 写入：
  "worktree": {
    "strategy": "auto",
    "path": "{worktree_root_path}/{Feature 全名}",
    "root_path": "{worktree_root_path 配置值，如 .worktree}",
    "branch": "feature/{Feature 全名}",
    "base_branch": "origin/{merge_target}",
    "created_at": "{ISO 8601}"
  }

为什么在 Goal-Plan Stage 入口而不是 Dev Stage 入口（v7.3.8 修订）：
├── PRD.md / discuss/ / PRD-REVIEW.md / pmo-internal-review.md / external-cross-review/prd-{model}.md
│   都是 Goal-Plan Stage 产物——落在 feature 分支而不是 main，语义更干净
├── 用户拒绝 PRD → git worktree remove 一键回退，main 零污染
├── 外部模型交叉评审读的是独立 worktree 的 PRD，不受 main 并发修改干扰
└── UI Design / Blueprint 阶段产物（UI.md / TC.md / TECH.md）同 worktree 延续

降级链（每档降级输出 WARN 到 state.json.concerns）：
├── auto 失败（git 不可用 / worktree add 错误 / 磁盘不足）→ 降 manual
├── manual 用户 2 次未响应 → 降 off
└── off → 所有阶段在当前工作区执行，跨 Feature 约束回退为人工注意力
```

---

## 执行报告模板（Output Contract 的输出呈现）

```
📋 Goal-Plan Stage 执行报告（F{编号}-{功能名}）
================================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / ROUND_OVERFLOW / FAILED}
├── 执行方式：{主对话 / Subagent / 混合}（来自 Execution Plan + state.goal_plan_substeps_config）
├── 评审角色：{review_roles[].role 列表，例：PL, RD, QA}（各 execution: subagent / main-conversation）
├── 评审轮次：Round {1/2/3} 收敛（v7.3.10+P0-34，≤3 轮）
├── 各角色 verdict：PL={PASS/PASS_WITH_CONCERNS/NEEDS_REVISION} / RD=… / QA=… / Designer=… / PMO=…
├── PM 响应分布：ADOPT × N / REJECT × M / DEFER × K
├── 外部模型交叉评审：{ENABLED → DONE / DONE_WITH_CONCERNS / SKIPPED / FAILED | DISABLED（external ∉ review_roles[]）}
└── PRD 验收标准数：{N} 条（AC 结构化已校验）

## 评审循环纪要（v7.3.10+P0-34）
├── Round 1：{各角色 verdict + finding 数 + PM 响应分布}
├── Round 2（如有）：{同上，重点列 carry-over finding}
├── Round 3（如有）：{同上 + 是否触发 ROUND_OVERFLOW 用户决策}
└── 最终 overall_verdict：{PASS / PASS_WITH_CONCERNS}（来自 PRD-REVIEW.md frontmatter）

## 技术评审报告
{按 PRD-REVIEW.md 格式，含尾部 Codex 整合章}

## 外部模型交叉评审摘要（🟡 仅当 external ∈ state.goal_plan_substeps_config.review_roles[] 时输出本节）
├── Codex 状态：{DONE / SKIPPED + 原因 / DISABLED}
├── Findings 总数：{N}（C1:{?} C2:{?} C3:{?} C4:{?} C5:{?} C6:{?}）
├── ADOPT: {a} 条（已并入 PRD）
├── REJECT: {b} 条（理由见 PRD-REVIEW.md 尾部）
└── DEFER: {c} 条（写入 state.json.concerns 或下一 Stage Key Context）

## 产出文件
├── 📁 PRD.md（定稿，AC 结构化 + business_direction_locked frontmatter）
├── 📁 PRD-REVIEW.md（评审记录，含所有评审角色 reviews[].* 段；review_roles[] 含 external 时含整合章）
├── 🟡 pmo-internal-review.md（PMO 自审，仅 review_roles[] 含 external 时产出）
└── 🟡 external-cross-review/prd-{model}.md（外部视角，仅 review_roles[] 含 external 时产出）
（v7.3.10+P0-43：discuss/PL-FEEDBACK-R{N}.md / PM-RESPONSE-R{N}.md 已废止，禁止产出）

## Output Contract 校验
├── YAML frontmatter：✅ 可解析
├── AC 数量：{N}（≥1）
├── 无 TBD/TODO：✅
├── 4 内部视角评审：✅ 全覆盖
└── Codex 校验：{ENABLED → 独立性 grep ✅ + findings 分类 ✅ | DISABLED → PRD-REVIEW 尾部声明已关闭 ✅}
```
