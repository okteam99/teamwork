# Plan Stage：需求定义（PM 写 PRD + PL-PM 讨论 + 多角色技术评审）

> 在用户确认流程类型后进入本 Stage。产出一份经过产品对齐 + 技术评审的合格 PRD。
> 🔴 契约优先：本文件规范 Input / Process / Output 三契约。执行方式由 AI 在 Plan 模式自主规划（见 SKILL.md「AI Plan 模式规范」）。

---

## 本 Stage 职责

产出经过产品方向对齐 + 多视角技术评审的定稿 PRD，为后续 Stage 锁定需求边界。PRD 中的 AC 必须结构化以便与测试强绑定。

---

## Input Contract

### 必读文件（按顺序）

```
├── {SKILL_ROOT}/agents/README.md                    ← 通用规范
├── {SKILL_ROOT}/stages/plan-stage.md                ← 本文件
├── {SKILL_ROOT}/roles/pm.md                         ← PM 角色 + PRD 技术评审规范
├── {SKILL_ROOT}/roles/product-lead.md               ← PL 角色（讨论用）
├── {SKILL_ROOT}/templates/prd.md                    ← PRD 模板（含 AC 结构化 frontmatter）
├── {SKILL_ROOT}/templates/codex-cross-review.md     ← Codex 交叉评审规范（PRD 变体）
└── {SKILL_ROOT}/standards/common.md                 ← 通用开发规范

可选（存在则读取）：
├── docs/PROJECT.md                                  ← 产品总览
├── docs/KNOWLEDGE.md                                ← 项目知识库
├── docs/architecture/ARCHITECTURE.md                ← 架构文档（技术评审参考）
└── design/sitemap.md                                ← 全景设计（有 UI 时参考）
```

### Key Context（PMO 必须逐项判断，无则写 `-`）

- 历史决策锚点：上游 Stage / CHG 记录 / Plan Stage 纪要中的决策
- 本轮聚焦点：重派或修订场景必填
- 跨 Feature 约束：与其他进行中 Feature 的冲突/兼容
- 已识别风险：来自 KNOWLEDGE.md / 预检 / 历史 Bug
- 降级授权：PL 不可用时是否可由 PM 单独推进等
- 优先级 / 容忍度：进度优先 / 质量优先 / 平衡

### 前置依赖

- PMO 初步分析已输出且用户已确认流程类型
- state.json.current_stage == "plan"
- 无其他阻塞项（blocking.pending_user_confirmations 为空）
- **Preflight（v7.3.9 + P0 简化）**：PMO 已完成 Plan Stage 入口 preflight（worktree + 分支名 + base 分支 + 工作区干净 共 4 硬门禁），`state.json.stage_contracts.plan_preflight.output_satisfied == true`
- **Worktree（v7.3.8）**：worktree=auto 时 PMO 已在 preflight 阶段创建并切换，`state.json.worktree.{strategy, path, branch, base_branch}` 已写入；PRD/discuss/评审等产物均落在该 worktree 分支，不污染 main / staging

---

## Stage 入口 Preflight（v7.3.9 新增）

> 🔴 进入 Plan Stage 主流程之前，PMO 必须完成入口 preflight。这是 v7.3.9 新增的轻量前置检查，目的是在所有 Feature 产物诞生前锁定 git 环境，避免 Ship Stage 时才发现分支基线不对导致的大规模 rebase 灾难。

### 为什么加 preflight（v7.3.9 设计背景）

```
Feature 的全部产物（PRD / UI / TC / TECH / 代码 / 测试）都从 Plan Stage 开始累积。
如果 worktree 基于错误的 base 分支（例如基于陈旧 main 而非 origin/staging），
到 Ship Stage rebase onto staging 时会遇到大规模冲突——此时产物已成定局，
回退代价极高。Preflight 在 Plan Stage 入口锁定 base，防止后期灾难。
```

### 4 项硬门禁（P0 简化，从 v7.3.9 的 6 项精简）

> 🔴 **P0 简化说明**：v7.3.9 原设计为"3 硬门 + 3 软提示"。P0 审计后发现：
> - 原软提示 "工作区干净" 实际是硬条件（worktree 会继承脏状态，事后代价大）→ **升级为硬门禁**
> - 原软提示 "merge_target 解析路径清晰" 当 localconfig 无分歧时无需交互 → **自动接受，仅冲突时才问**
> - 原软提示 "Feature 编号 + 命名合规" 可从 Feature 名自动派生 → **自动派生，不再暂停询问**
>
> 简化后 = **4 硬门禁 + 0 软提示**。暂停次数从"至多 3 次"降到"最多 1 次（仅真冲突时）"。

**🔴 4 项硬门禁（不通过必须阻塞或暂停）：**

```
1. worktree 策略明确（off / auto / manual）且 state.json.worktree 无残留
   └── 上一 Feature 的 worktree 字段未清理 → ⏸️ 提示用户沿用 / 清理

2. 分支名与既有 feature 分支无冲突（分支名自动从 Feature 全名派生）
   └── 派生规则：feature/{Feature 全名}（由 PMO 自动生成，无需用户确认命名）
   └── git branch --list "feature/{Feature 全名}" 非空 → ⏸️ 追问（续用 / 改名 / 删除重建）

3. base 分支明确且可达（origin/{merge_target}）
   └── merge_target 自动解析：state.json.merge_target > localconfig > 默认 staging
       （此级联无分歧时不暂停；state.json 与 localconfig 冲突才暂停）
   └── git rev-parse --verify origin/{merge_target} 失败 → BLOCKED（远端未 fetch / 配置错）
   └── 本地 origin/{merge_target} 已过时 → 自动 git fetch（不暂停）

4. 工作区干净（git status --porcelain 为空）🆕 P0 升级为硬门禁
   └── 非空 → ⏸️ 暂停，让用户确认：
       ├── 暂存改动（git stash）再进入 Plan Stage
       ├── 先 commit 归入当前分支再进入
       └── 放弃改动（git restore）
   └── 理由：worktree 会继承工作区状态，脏 worktree 在 Feature 产物诞生后难以清理
```

**自动派生 / 接受的项（不再暂停询问）：**

```
- Feature 分支名：从 Feature 全名派生 feature/{全名}，PMO 直接使用
- merge_target：按级联读取，无分歧时静默接受，暂停点仅展示结果
- Feature 编号 + 命名：PMO 初步分析阶段已完成，preflight 不重复问
```

### Preflight 命令序列（auto 模式）

```bash
# 硬门禁 1：state.json 残留检查（由 PMO 读 state.json 实现）

# 硬门禁 2：分支名冲突检查
git branch --list "feature/{Feature 全名}"
git worktree list | grep "feature/{Feature 全名}"

# 硬门禁 3：base 分支可达性
git fetch origin {merge_target}
git rev-parse --verify "origin/{merge_target}"

# 软提示 4：工作区状态
git status --porcelain

# 通过后创建 worktree（显式指定 base，v7.3.9 关键改动）
git worktree add ../feature-{Feature 全名} -b feature/{Feature 全名} "origin/{merge_target}"
cd ../feature-{Feature 全名}
```

🔴 **v7.3.9 关键差异**（对比 v7.3.8）：`git worktree add` 必须显式指定 base（`origin/{merge_target}`），不能依赖隐式 HEAD。

🟢 **P0 懒装依赖模型**：worktree 创建**不触发**依赖安装（`npm install` / `pip install` / `go mod download`）。纯文档 Stage（Plan / Blueprint / Review）可在空壳 worktree 上完成；依赖安装延迟到真正需要执行代码的 Stage 入口（Dev / Test），由各 Stage preflight 检测并按需执行。Plan Stage 进入时 worktree 开销 ~1-2s，无 npm/pip 等待。

### Preflight 暂停点模板

```
⏸️ Plan Stage 入口 Preflight 确认

📋 Preflight 结果（4 硬门禁）
├── Feature: {编号}-{功能名}（自动派生，无需确认）
├── 合并目标（merge_target）: {staging}（自动解析：{state.json | localconfig | 默认}，无分歧）
├── Worktree 策略: {auto | manual | off}（门禁 1）
├── 分支名: feature/{全名}（自动派生；本地 {✅ 可用 / ⚠️ 已存在}）（门禁 2）
├── Base 分支: origin/{merge_target}（{✅ 可达 / ❌ 需 fetch}）（门禁 3）
├── 工作区干净: {✅ 干净 / ⚠️ 有未提交改动}（门禁 4，P0 升级为硬门禁）
└── 🔴 硬门禁: {全部通过 / 第 N 项未通过}

💡 建议: {具体建议，如"所有检查通过，请确认创建 worktree"或"先处理未提交改动再启动 Plan Stage"}
📝 理由: {说明为什么这么建议}

请选择：
1. ✅ 确认启动 Plan Stage（采用当前 preflight 配置）
2. 🔧 修改配置（改分支名 / 切换 worktree 策略 / 改 merge_target）
3. ⏸️ 暂停处理 git 环境（fetch / 清理未提交改动 / 切换分支）后重跑 preflight
4. 其他指示
```

### state.json.stage_contracts.plan_preflight 写入

```json
{
  "plan_preflight": {
    "input_satisfied": true,
    "process_satisfied": true,
    "output_satisfied": true,
    "checks": {
      "worktree_resolved": true,
      "branch_name_confirmed": true,
      "base_branch_verified": "origin/staging",
      "clean_tree": true,
      "existing_branch_collision": false,
      "merge_target_resolved": "staging",
      "_note": "P0 简化后仅 4 项硬门禁：worktree_resolved / branch_name_confirmed / base_branch_verified / clean_tree。existing_branch_collision 和 merge_target_resolved 保留为信息性字段，不作为独立门禁。"
    },
    "started_at": "...",
    "completed_at": "...",
    "duration_minutes": 4
  }
}
```

### 失败处理

| 场景 | 处理 |
|------|------|
| base 分支不可达 | BLOCKED → ⏸️ 用户 fetch 后重跑 |
| 分支名已存在 | ⏸️ 用户选择：续用 / 改名 / 删除重建 |
| worktree add 失败 | 按既有 worktree 降级链（auto → manual → off），输出 WARN 到 concerns |
| 工作区不干净 | 🔴 硬门禁 4（P0 升级，原软提示）→ ⏸️ 暂停：stash / commit / restore 三选一后重跑 |

---

## Process Contract

### 必做动作

1. **PM 起草 PRD 初稿**（按 `roles/pm.md` + `templates/prd.md`）
   - 🔴 **格式基准锚定（v7.3.9+P0-7 硬规则）**：
     - 起草前必须 Read `templates/prd.md` + `templates/feature-state.json` 为格式唯一真相源
     - 🔴 禁止说"先参考最近一份 PRD / state.json 格式"——违反 P0-7 红线
     - peer Feature 仅作内容参考（AC 写法、消费方分析套路），格式回 templates/ 对齐
     - 详见 [TEMPLATES.md § 格式权威红线](../TEMPLATES.md#-格式权威红线v739p0-7-新增)
   - 🔴 **跨项目依赖前置（v7.3.9+P0-8 硬规则）**：
     - PM 起草过程中若发现需要"调用 / 访问 / 接入 / 对接 ... 其他子项目的能力"
     - **立即**通知 PMO 走 [roles/pmo.md § 跨项目依赖识别](../roles/pmo.md#-跨项目依赖识别pmo-专属v739p0-8-新增) 场景 A 流程
     - 🔴 PMO 先 Read `templates/dependency.md` → 在**上游子项目** `{upstream}/docs/DEPENDENCY-REQUESTS.md` 追加 DEP-N 条目（而非等 PRD 写完再补、而非在当前 Feature 目录自创 DEPS.md）
     - PRD 正文引用 DEP 编号作为 AC / 前置条件
     - state.json.blocking.pending_external_deps 登记 DEP 编号
   - 必须包含「交付预期」section（用户视角的变化 + 验证方式）
   - AC 结构化（按 templates/prd.md 的 YAML frontmatter）
   - 不允许 TBD / 待补充

2. **PL-PM 讨论**（产品方向对齐）
   - 最多 3 轮讨论
   - 达成共识 → PM 按共识更新 PRD
   - 有分歧 → 记录分歧项，标记为待用户决策

3. **多视角技术评审**（RD / Designer / QA / PMO / Codex）
   - 按 `roles/pm.md`「PRD 技术评审规范」执行 RD/Designer/QA/PMO 四个内部视角
   - **内部评审先行**：PMO 完成上述 4 视角 + 自身内部审视（pmo-internal-review.md，≥3 条实质 finding）**之后**才可 dispatch Codex
   - 产出 PRD-REVIEW.md（4 个内部视角汇总）
   - **Codex 交叉评审**：按 `templates/codex-cross-review.md` 调用 `codex-agents/prd-reviewer.toml`，产出 `{Feature}/prd-codex-review.md`（YAML frontmatter：perspective=external-codex、files_read、findings[]）
   - 汇总问题 + 建议

4. **整合 Codex 反馈 + PRD 定稿**
   - PMO 对 prd-codex-review.md 的每条 finding 分类：`ADOPT` / `REJECT` / `DEFER`（理由记入 PRD-REVIEW.md 尾部的「Codex 交叉评审整合」section）
   - 🔴 严禁"全盘接受"或"全盘忽略"——必须逐条推理
   - PM 按整合结论（4 内部视角 + 已 ADOPT 的 Codex finding）更新 PRD
   - 标记状态为「待用户确认」

### 过程硬规则

- 🔴 **角色规范必读且 cite**：切换到每个视角（PM/PL/RD/Designer/QA/PMO）前，必须先 Read 对应 `roles/{id}.md`，并在产出前 cite 该角色的关键要点（"📖 本视角遵循：roles/pm.md §Y 的 X 项约束"）
- 🔴 **PL-PM 讨论独立性**：PL 和 PM 各自表达观点，不能一方主导
- 🔴 **技术评审完整性**：必须覆盖 RD / Designer（如有 UI）/ QA / PMO 四个内部视角 + Codex 交叉评审一个外部视角
- 🔴 **Codex 独立性**：dispatch prd-reviewer 时 prompt 不得暗示结论；Codex 产出的 `files_read` 不得包含 PRD-REVIEW.md / discuss/* / pmo-internal-review.md（违反 = 重 dispatch）
- 🔴 **防外包思考**：PMO 必须先产出自身内部评审（≥3 条实质 finding）才能 dispatch Codex；Codex 返回后 PMO 逐条分类（ADOPT/REJECT/DEFER）不得无差别采纳
- 🔴 **Codex 降级处理**：Codex CLI 不可用时按 `agents/README.md §三` 三选一（修复 / 🟢 AI 自主规划等效独立审查 / skip+记入 concerns），不可静默跳过
- 🔴 **PRD 质量下限**：不能留 TBD / 待补充；验收标准必须量化可验证
- 🔴 **讨论轮次控制**：PL-PM 最多 3 轮，超出则记录分歧返回
- 🔴 **AC 结构化**：每条 AC 必须有 id / description / priority 字段（test_refs 在 Blueprint Stage 填入）
- 🔴 **Stage 完成前 git 干净** → 统一遵循 [rules/gate-checks.md § Stage 完成前 git 干净](../rules/gate-checks.md#-stage-完成前-git-干净v739-硬规则p0-集中化)（本 Stage commit message：`F{编号}: Plan Stage - {简述}`；典型产物：PRD / PRD-REVIEW / discuss 文档）

### 多视角独立性要求

- PL 和 PM 的讨论纪要必须分开记录（`discuss/PL-FEEDBACK-R{N}.md` 和 `PM-RESPONSE-R{N}.md`）
- 多视角技术评审的每个视角独立输出评审意见（不互相引用）
- Codex 交叉评审独立性通过产物结构强制：prd-codex-review.md 的 YAML frontmatter 必须声明 `perspective: external-codex` + `files_read`，且 `files_read` 不得包含任何内部评审产物（用 `grep -E "PRD-REVIEW|discuss/|pmo-internal" prd-codex-review.md` 应为空）

---

## Output Contract

### 必须产出的文件

| 文件路径 | 格式 | 必需字段 |
|---------|------|---------|
| `{Feature}/PRD.md` | Markdown + YAML frontmatter | `feature_id`, `acceptance_criteria[]` (id, description, priority), 交付预期, 影响范围 |
| `{Feature}/PRD-REVIEW.md` | Markdown | 4 个内部视角的评审意见（RD/Designer/QA/PMO）+ 汇总问题清单 + 尾部「Codex 交叉评审整合」section（逐条 ADOPT/REJECT/DEFER） |
| `{Feature}/pmo-internal-review.md` | Markdown | PMO 自身视角评审（≥3 条实质 finding，Codex dispatch 的前置条件）|
| `{Feature}/prd-codex-review.md` | Markdown + YAML frontmatter | `perspective: external-codex`, `target: prd`, `generated_at`, `files_read[]`, `findings[]`（含 C1-C6 checklist 分类）, `findings_summary` |
| `{Feature}/discuss/PL-FEEDBACK-R{N}.md` | Markdown | PL 视角反馈（每轮一个文件） |
| `{Feature}/discuss/PM-RESPONSE-R{N}.md` | Markdown | PM 对 PL 反馈的回应 |

### 机器可校验条件

- [ ] PRD.md frontmatter 可 YAML 解析（`yq '.feature_id' PRD.md` 成功）
- [ ] `acceptance_criteria[]` 至少 1 条，每条有 id/description/priority
- [ ] 无 TBD / 待补充 / TODO（`grep -iE "TBD|待补充|TODO" PRD.md` 为空）
- [ ] 多视角评审 4 个内部视角都有意见（或显式标注"无意见"+ 理由）
- [ ] pmo-internal-review.md 存在且含 ≥3 条 finding（Codex dispatch 前置）
- [ ] prd-codex-review.md frontmatter 可解析且 `perspective == "external-codex"`
- [ ] prd-codex-review.md 的 `files_read` 不包含 PRD-REVIEW / discuss/ / pmo-internal-review（`grep -E "PRD-REVIEW\|discuss/\|pmo-internal" prd-codex-review.md` 为空）
- [ ] PRD-REVIEW.md 尾部「Codex 交叉评审整合」section 对每条 finding 均有 ADOPT/REJECT/DEFER 标记 + 理由
- [ ] Codex 降级场景：若 Codex 未执行，state.json.concerns 或 PRD-REVIEW.md 需显式记录 skip_reason

### Done 判据

- 所有产出文件存在且通过格式校验
- PL-PM 讨论已达成共识或记录分歧
- 多视角评审已完成且无 🔴 阻塞问题
- `state.json.stage_contracts.plan.output_satisfied = true`

### 返回状态

| 状态 | 条件 | 后续 |
|------|------|------|
| ✅ DONE | 产出完整 + 评审通过 + 无分歧 | PMO ⏸️ 用户确认 PRD |
| ⚠️ DONE_WITH_CONCERNS | PRD 定稿但有 PL-PM 分歧 / 评审建议 | PMO ⏸️ 用户逐项决策 |
| 💥 FAILED | 需求不清晰无法产出 | 返回错误 + 部分产出 |

---

## AI Plan 模式指引

📎 Execution Plan 4 行格式（含 Estimated）→ [SKILL.md「AI Plan 模式规范」](../SKILL.md#-ai-plan-模式规范v73-新增)。默认 approach → [agents/README.md §一](../agents/README.md#一执行方式参考默认推荐--判断原则)。

本 Stage 默认 `main-conversation`（多视角 prompt 切换 + 用户讨论）。典型偏离：需求极清晰、无用户介入 → `subagent`。

**Expected duration baseline（v7.3.3）**：20-40 min（主对话 / 含 PL-PM 讨论）；需求清晰走 Subagent 一次闭环可降至 15-20 min。AI 在 Execution Plan 的 `Estimated` 字段按本 Feature 规模（预期 AC 数、讨论复杂度）校准。

---

## Worktree 集成（PMO 执行，v7.3.8 从 Dev Stage 前移至此）

```
触发时机：用户确认流程类型 → 进入 Plan Stage 之前（flow-transitions.md 第 11 行）

worktree 策略（从 .teamwork_localconfig.md 读取）：
├── off → 跳过，Plan 产物落在当前分支
├── manual → PMO 提醒用户创建后再继续
└── auto → PMO 自动创建 + 切换 + 记录 state.json

auto 模式命令（v7.3.9：显式指定 base 避免后期 rebase 灾难）：
  git fetch origin {merge_target}
  git worktree add ../feature-{Feature 全名} -b feature/{Feature 全名} origin/{merge_target}
  cd ../feature-{Feature 全名}

state.json 写入：
  "worktree": {
    "strategy": "auto",
    "path": "../feature-{Feature 全名}",
    "branch": "feature/{Feature 全名}",
    "base_branch": "origin/{merge_target}",
    "created_at": "{ISO 8601}"
  }

为什么在 Plan Stage 入口而不是 Dev Stage 入口（v7.3.8 修订）：
├── PRD.md / discuss/ / PRD-REVIEW.md / pmo-internal-review.md / prd-codex-review.md
│   都是 Plan Stage 产物——落在 feature 分支而不是 main，语义更干净
├── 用户拒绝 PRD → git worktree remove 一键回退，main 零污染
├── Codex 交叉评审读的是独立 worktree 的 PRD，不受 main 并发修改干扰
└── UI Design / Blueprint 阶段产物（UI.md / TC.md / TECH.md）同 worktree 延续

降级链（每档降级输出 WARN 到 state.json.concerns）：
├── auto 失败（git 不可用 / worktree add 错误 / 磁盘不足）→ 降 manual
├── manual 用户 2 次未响应 → 降 off
└── off → 所有阶段在当前工作区执行，跨 Feature 约束回退为人工注意力
```

---

## 执行报告模板（Output Contract 的输出呈现）

```
📋 Plan Stage 执行报告（F{编号}-{功能名}）
================================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / FAILED}
├── 执行方式：{主对话 / Subagent / 混合}（来自 Execution Plan）
├── PL-PM 讨论：{R1 收敛 / R2 收敛 / 有分歧}
├── 内部技术评审：{通过 / 有建议已纳入 / 有问题}（RD/Designer/QA/PMO）
├── Codex 交叉评审：{DONE / DONE_WITH_CONCERNS / SKIPPED / FAILED}（ADOPT: N / REJECT: M / DEFER: K）
└── PRD 验收标准数：{N} 条（AC 结构化已校验）

## PL-PM 讨论纪要
├── 讨论轮次：{1-3}
├── 共识项：{N} 条
├── 分歧项：{M} 条（待用户决策）
└── PRD 修改：{已纳入的修改摘要}

## 技术评审报告
{按 PRD-REVIEW.md 格式，含尾部 Codex 整合章}

## Codex 交叉评审摘要
├── Codex 状态：{DONE / SKIPPED + 原因}
├── Findings 总数：{N}（C1:{?} C2:{?} C3:{?} C4:{?} C5:{?} C6:{?}）
├── ADOPT: {a} 条（已并入 PRD）
├── REJECT: {b} 条（理由见 PRD-REVIEW.md 尾部）
└── DEFER: {c} 条（写入 state.json.concerns 或下一 Stage Key Context）

## 产出文件
├── 📁 PRD.md（定稿，AC 结构化）
├── 📁 PRD-REVIEW.md（评审记录 + Codex 整合）
├── 📁 pmo-internal-review.md（PMO 自审）
├── 📁 prd-codex-review.md（外部视角）
└── 📁 discuss/PL-FEEDBACK-R{N}.md + PM-RESPONSE-R{N}.md

## Output Contract 校验
├── YAML frontmatter：✅ 可解析
├── AC 数量：{N}（≥1）
├── 无 TBD/TODO：✅
├── 4 内部视角评审：✅ 全覆盖
├── Codex 独立性（files_read grep）：✅
└── Codex findings 分类完整：✅
```
