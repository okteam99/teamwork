# Ship Stage：双段流程 - push feature → 等待合并 → finalize 收尾

> PM 验收通过且用户选择「通过 + Ship」后进入本 Stage。
>
> **不变内核**：
> - **第一段（push）**：净化 → push feature → CLI 优先创建 MR/URL 兜底 → ⏸️ 暂停等用户在平台合并
> - **第二段（finalize）**：用户回报合并完成 → `git branch -r --contains` 验证 → 切 merge_target → 写 state.json 最终态 → 清理 worktree → completed
> - **契约红线**：PMO 不动 merge_target（红线 R1 例外仅 state.json/BUG-REPORT.md 一文件）、不做本地 merge、不删 feature 分支。合并动作由用户在平台 UI 上完成。
>
> 版本演进详见 CHANGELOG（P0-15 取消 direct-merge / P0-29 改双段 / P0-32 红线 R1 例外 / P0-36 Bug 分支 / P0-74 Micro 分支 / P0-99 CLI 优先 / P0-115 暂停点渲染契约）。

---

## 本 Stage 职责

- **第一段（push）**：净化遗留 git 问题 → push feature 到 remote 并记录 `feature_head_commit` → 识别 git host → CLI 优先创建 MR/URL 兜底 → ⏸️ 暂停等合并。完成后 `state.ship.phase = "pushed"`，`state.current_stage` 仍为 `ship`。
- **第二段（finalize）**：`git branch -r --contains` 验证合并 → 切 merge_target → 写 state.json 最终态 → 清理 worktree → 输出完成报告，标记 `current_stage=completed` / `ship.shipped=merged` / `ship.phase=merged`。
- **不产生 merge commit**（合并由平台处理）；**不删 feature 分支**（由平台 auto-delete-on-merge 或团队手动清理）。

---

## 可配置点清单

| 可配置点 | 默认值 | 控制字段 | 决策时机 |
|---------|-------|---------|---------|
| `merge_target` | staging（localconfig 配置）| `state.environment_config.merge_target` | triage Step 7.5 探测决策 |
| `git_host` | 自动识别（GitHub / GitLab / Gitee / Bitbucket / 未知）| `state.ship.git_host` | 第一段 push 时识别 |
| `mr_url` / `mr_create_url` | v7.3.10+P0-99：CLI 优先（gh/glab）实际创建 → mr_url；CLI 不可用 → URL 兜底 mr_create_url | `state.ship.mr_url` / `state.ship.mr_create_url` | 第一段 push 末段 |
| `mr_creation_method` | enum: `cli-gh` / `cli-glab` / `url-fallback` / `unknown-platform`（v7.3.10+P0-99）| `state.ship.mr_creation_method` | 第一段 push 末段 |
| `worktree_cleanup` | cleaned / deferred / n_a（按 worktree mode 决策）| `state.ship.worktree_cleanup` | 第二段 finalize |
| Bug 简化分支（v7.3.10+P0-36）| 仅 Bug 流程触发 | spec 内嵌 | 流程类型判断 |
| `merge_target` push 边界 | 第二段 finalize 仅允许 state.json / BUG-REPORT.md 一文件（红线 R1 例外）| spec 内嵌硬规则 | 第二段 finalize |

🔴 不变内核：双段流程（第一段 push + 第二段 finalize）+ PMO 不做 merge / 不解决冲突 + push 失败降级（pull --rebase 重试 1 次）+ MR URL 生成。

---

## 🔴 state.json 写操作入口（v7.3.10+P0-125 新增 · 单源走 tools/state.py）

> Ship Stage 涉及 ship.* 字段 ~25 个 + 状态机 phase: null → pushed → {merged | closed_unmerged} · 历史上 PMO 直接编辑 JSON 多次出错（拼字段名 / 跳 phase / 缺 evidence / 红线 R1 边界破）。本节起所有 state.json 写操作走 `skills/teamwork/tools/state.py`，spec 描述「写什么」，脚本管「怎么写 + 校验」。
>
> 🔴 **硬门禁**：
> - 禁止用 Edit / jq / sed 直接改 state.json · 违者 = 流程违规
> - 唯一逃生舱：`state.py raw-write`（自动追加 `concerns` WARN）· 仅 migration / debug 使用
> - 治本 P0-124 拦截：`ship-cleanup --status cleaned` 在 phase ≠ merged 时被脚本物理拒绝（exit 1 BLOCKED · 不靠 PMO 自觉）
> - 治本 P0-156 拦截（v7.3.10+P0-156 新增）：`ship-confirm-merged` + `ship-cleanup` 在 **linked worktree** 直接 FAIL（exit 2）· 强制 cd 到 merge_target 主工作区再跑（cite Step 6）· 旁路 `TEAMWORK_BYPASS_MAIN_WORKTREE=1` · 治本 ADMIN-F013 case：agent 在 feature worktree 跑 ship-confirm-merged → state.json 写到 worktree → `git worktree remove --force` 时丢失 → 后续 ship-cleanup 找不到 state.json → 状态更新永久丢失.

### 子命令 ↔ Step 映射

| Step | state.py 子命令 | 触发时机 |
|------|---------------|---------|
| Step 1 | `ship-sanitize --residual-commits ... --cleaned-files ... --suspicious-files ...` | 净化结束 · 写 sanitize_log |
| Step 2 末 | `ship-push --feature-head-commit H --git-host G --mr-creation-method M --mr-url U \| --mr-create-url U` | feature 已 push · MR/PR 已创建 / 兜底 URL 已生成 · 写 phase=pushed |
| Step 3 暂停 | （不写 · phase=pushed 已在 Step 2 末写入）| — |
| Step 4-5 验证后 | （不写 · 用 in-memory 变量传到 Step 7）| — |
| Step 7-8 | `ship-confirm-merged --merge-commit-hash H --merge-detection-method M [--merge-target-pushed-at \| --merge-target-push-failed --failed-reason]` | 合并验证 + finalize push 一并写入 phase=merged |
| Step 9 | `ship-cleanup --status {cleaned\|deferred\|n_a}` | worktree 处置（cleaned 必须 phase=merged · 治本 P0-124）|
| 异常段 | `ship-closed [--abandon] [--reason ...]` | MR 关闭未合并 / 用户放弃 |
| 全 Stage 出口 | `complete-stage --stage ship` → `enter-stage --stage completed` | 三 gate 满足 + 转 completed |

### 调用约定

- 入参用语义化命令行（不暴露 dotted path）· enum 通过 argparse `choices` 提前拦截
- stdout = JSON `{verdict, updated_fields, cited_fields, next_actions, warnings}` · PMO 只把这块引入对话 · 不再 cite 原文 410 行
- 失败 exit 1（业务校验）/ 2（参数）/ 3（状态机非法）· stderr 含 hint · PMO 按 hint 自纠
- evidence 字段（feature_head_commit / merge_commit_hash 等）由 PMO 在 Bash 取 git stdout 后作命令行入参传入 · 脚本不调 git

---

## Input Contract

### 必读文件

```
├── {SKILL_ROOT}/stages/ship-stage.md（本文件）
├── {SKILL_ROOT}/roles/pmo.md（PMO 角色契约）
├── {SKILL_ROOT}/roles/pmo-pm-acceptance-ship.md（PMO PM 验收 + Ship Stage 详规范 · v7.3.10+P0-93 抽出）
├── {Feature}/state.json（读 worktree.path / worktree.branch / ship.merge_target）
├── 项目根 .teamwork_localconfig.md（读 merge_target / mr_url_template / worktree_cleanup）
└── 项目根 .gitignore（净化判断白名单/灰名单时参考）
```

### Key Context

- merge_target 来源层级：state.json.ship.merge_target > .teamwork_localconfig.md.merge_target > 默认 `staging`
- git host 识别来源：`git remote get-url origin` → 按 URL pattern 匹配平台
- 未知平台兜底：localconfig `mr_url_template` 提供自定义 URL 模板；均无则输出 feature 分支 URL + 提示用户手动创建 MR

### 前置依赖

- `state.json.current_stage == "pm_acceptance"`
- PM 验收已在主对话完成（PM 输出验收结论）
- 用户在 PM 验收暂停点选了「1. 通过 + Ship」
- `state.json.stage_contracts.pm_acceptance.output_satisfied == true`

---

## 入口 Read 顺序（v7.3.10+P0-23 固定）

🔴 按以下顺序 Read，字节一致利于 prompt cache 命中。详见 [standards/prompt-cache.md](../standards/prompt-cache.md)。

```
Step 1: roles/pmo.md + roles/pmo-pm-acceptance-ship.md  ← 角色层（L0 稳定 · v7.3.10+P0-93 sub-file）
Step 2: 无产出新模板                                    （本 Stage 仅 push + 生成 MR URL）
Step 3: 项目根 .teamwork_localconfig.md, .gitignore   ← 项目层（L1 稳定）
Step 4: {Feature}/state.json                           ← 🔴 最后，动态入口（L3）
```

🔴 R3 约束：state.json 入口 Read 1 次 → 中段 0 读写 → 出口 Read 1 次 + Write 1 次；全 Stage ≤ 5 次（含豁免）。

---

## Process Contract

### 主对话输出 Tier 应用（v7.3.10+P0-54 新增）

> 🔴 **遵循 [standards/output-tiers.md](../standards/output-tiers.md) 通用 Tier 1/2/3 规范 + 4 类反模式禁令**。

**Ship Stage 特定 Tier 应用**：

- **Tier 1（永远输出）**：第一段 5 行 Execution Plan / 净化 + push verdict / MR URL 生成 / ⏸️ 用户合并 MR 暂停 / 第二段 finalize 验证 verdict（merge_commit / branch -r --contains 校验）/ ship 完成声明
- **Tier 2（命中折叠）**：sanitize_log 异常摘要（仅有可疑文件时）/ push 失败降级路径（仅触发时）/ Bug 简化分支特例（仅 Bug 流程）
- **Tier 3（不输出，走 state.json）**：ship 字段详细（git_host / mr_create_url / feature_pushed_at / worktree_cleanup 等机读字段）/ merge_evidence 完整 git 命令输出 / 主流程异常 audit trail 详细

---

### 步骤概览（双段）

```
─── 第一段（push） ───
Step 1: 净化（git status 分析 + 分类处理）
    ↓
Step 2: push feature 分支 + 记录 feature_head_commit + 识别 git host + 生成 MR create URL
    ↓
Step 3: 输出第一段报告 + ⏸️ 4 选 1 暂停点（已合并 / 等待中 / 关闭未合并 / 其他）
        state.ship.phase = "pushed"

─── 第二段（finalize，用户回选项 1 触发） ───
Step 4: git fetch origin {merge_target} + git branch -r --contains {feature_head_commit} 检测
    ↓
Step 5: 检测通过 → 进入 Step 6
        检测失败 → ⏸️ 询问用户提供 merge commit hash + state.concerns 标注
    ↓
Step 6: 切到 merge_target 主工作区（v7.3.10+P0-32）
        cd {主工作区} + git checkout {merge_target} + git pull --ff-only origin {merge_target}
    ↓
Step 7: 写 state.json 最终态（在 merge_target 工作区内的 feature 目录，v7.3.10+P0-32）
        state.current_stage = "completed"
        state.ship.{phase, shipped, merge_commit_hash, mr_merged_at, merge_detection_method, completed_at, worktree_cleanup}
    ↓
Step 8: commit + push 到 merge_target（v7.3.10+P0-32 红线 R1 例外，仅 state.json 一文件）
        push 失败降级：pull --rebase 重试 1 次 → 仍失败 → 退回 feature 分支 push + state.concerns WARN
    ↓
Step 9: 清理 worktree（执行第一段延迟的 worktree 清理）
    ↓
Step 10: 输出 Feature 完成报告
```

异常分支：
- 用户回 Step 3 选项 3（MR 关闭未合并）→ 进入「异常处理」段
- Step 5 用户回报"未合并"或"放弃"→ 进入「异常处理」段

---

### 🆕 Bug 流程缩简分支（v7.3.10+P0-36 新增）

> 简单 Bug 流程也产生代码改动，必须 push + MR + 合并 + 清理才能正确闭环。本节定义 Bug 流程进入 Ship Stage 时的分支差异（与 Feature 流程共享主流程，仅产物 / 状态字段 / 校验项不同）。

#### 触发条件

```
Bug 流程进入 Ship Stage 的前置条件（v7.3.10+P0-36）：
├── BUG-REPORT.md frontmatter `flow_type: bug` 且 `classification: simple`
├── BUG-REPORT.md frontmatter `current_stage: pmo_summary`（PMO 已完成 Bug 总结）
├── BUG-REPORT.md frontmatter `phase: summarized`
└── PMO 输出 Bugfix 记录后自动流转（参考 rules/flow-transitions.md Bug 流程末尾的 Ship 转移）
```

🔴 **复杂 Bug 不走本分支**：复杂 Bug 升级为 Feature 流程后，state.json 是 Feature 的，按 Feature Ship Stage 执行（无差异）。

#### 与 Feature Ship 的关键差异

| 维度 | Feature Ship | Bug Ship 缩简版 |
|------|-------------|----------------|
| 状态承载 | `{Feature}/state.json` | `{Feature}/bugfix/BUG-{id}-*.md` 的 frontmatter |
| 状态字段引用 | `state.ship.{phase/shipped/merge_commit_hash/...}` | BUG-REPORT.md frontmatter `{phase/shipped/merge_commit_hash/...}` |
| MR 标题 | `{type}({scope}): {summary}` | `[Bug] {简述} (BUG-{编号})` |
| MR 描述 | 完整 AC 覆盖 / Review / 测试报告 | 根因分析 / 修复方案 / QA 验证（来自 BUG-REPORT.md） |
| Step 7 写状态 | 写 state.json | 写 BUG-REPORT.md frontmatter（同字段命名） |
| Step 8 push 内容 | 仅 `{Feature}/state.json` 一文件 | 仅 `{Feature}/bugfix/BUG-{id}-*.md` 一文件（红线 R1 Ship Finalize 例外扩展，v7.3.10+P0-36） |
| Worktree 清理 | feature worktree | 同上（Bug 也用 worktree） |
| 完成报告 | Feature 完整 Stage 摘要 | Bug 修复摘要（QA 验证 / 文件 / commit / merge_commit）|

#### Bug 分支差异步骤（仅列差异；Step 1/4/5/6/9 与 Feature 一致）

```
Step 2（push feature）：
  - feature 分支由 RD Bug 修复阶段创建（命名 bugfix/BUG-{id}）
  - push 后记录到 BUG-REPORT.md frontmatter `feature_head_commit`（不是 state.json）

Step 3（第一段报告 + ⏸️）：
  - MR URL 标题用 `[Bug] {简述} (BUG-{编号})`
  - MR description 来源：BUG-REPORT.md 的"问题描述 + 根因 + 修复方案 + QA 验证"段
  - phase 字段：BUG-REPORT.md frontmatter `phase = "shipping"`（不是 state.ship.phase）

Step 7（写最终态）：
  - 写入对象：BUG-REPORT.md frontmatter（不是 state.json）
  - 字段：current_stage="completed" / phase="shipped" / shipped="merged" /
         merge_commit_hash / mr_merged_at / completed_at / worktree_cleanup

Step 8（push merge_target）：
  - 🔴 红线 R1 例外扩展：Bug 流程允许 push merge_target，仅限 BUG-REPORT.md 一文件、
    仅元数据字段（frontmatter shipped / merge_commit_hash / completed_at 等）、零业务影响
  - 业务代码（src/ 等）已在 MR 合并时入 merge_target，不重复 push
  - push 失败降级：与 Feature 一致（pull --rebase 重试 1 次 → 退回 feature 分支 push + frontmatter ship_concerns WARN）

Step 10（完成报告）：
  - 报告对象：Bug 修复
  - 内容：根因 / 修复方案 / 影响 / QA 验证 / commit / merge_commit / 流程（简化流程 / 完整流程）
  - 同时输出 PMO Bugfix 记录（FLOWS.md 既有格式）
```

#### Bug 流程的入口前置依赖（v7.3.10+P0-36）

```
- BUG-REPORT.md frontmatter `flow_type: bug` 且 `classification: simple`
- BUG-REPORT.md frontmatter `current_stage: pmo_summary`
- BUG-REPORT.md frontmatter `phase: summarized`
- PMO 已输出 Bugfix 记录到 BUG-REPORT.md「修复记录」段
```

📎 **本分支不改主流程结构**——Step 1-10 全部沿用，仅状态承载文件 / 字段命名 / MR 标题模板 / push 范围有差异。PMO 在 Stage 入口按 `flow_type` 分支选择正确的状态承载文件即可。

📌 **state.py 调用**（Bug 流程 · v7.3.10+P0-125）：

```bash
# Step 2 push 后落 phase=pushed
python3 {SKILL_ROOT}/tools/state.py bug-frontmatter --feature {Feature} --bug-id BUG-{id} \
  --set phase=pushed --set feature_head_commit=$HEAD_COMMIT \
  --set mr_url=https://... --set git_host=github --validate-ship

# Step 7 写最终态（合并已确认）
python3 {SKILL_ROOT}/tools/state.py bug-frontmatter --feature {Feature} --bug-id BUG-{id} \
  --set phase=merged --set shipped=merged \
  --set merge_commit_hash=$HASH --set mr_merged_at=$ISO \
  --set merge_detection_method=branch-contains \
  --set worktree_cleanup=cleaned --set current_stage=completed --validate-ship
```

`--validate-ship` 启用与 ship 同形态状态机镜像（治本 P0-124 在 Bug 路径同步生效：phase=merged 必带 merge_commit_hash + mr_merged_at）。

---

### 🆕 Micro 流程缩简分支（v7.3.10+P0-74 新增）

> Micro 流程的省略**只在前端 5 个 Stage**（Plan / Blueprint / UI / Review / Test）—— 但代码仍要发布。实证（2026-04-30）：Micro 走完用户验收后只有「本地已修改未 commit / 未 push」，用户被迫追问"没 ship 么"才意识到代码没落库。本节定义 Micro 流程进入 Ship Stage 时的分支差异（与 Feature / Bug 共享 Step 1-10 主流程，仅状态承载 / MR 标题 / 第二段元数据范围有差异）。

#### 触发条件

```
Micro 流程进入 Ship Stage 的前置条件（v7.3.10+P0-74）：
├── 流程类型 = Micro（PMO 在 triage / Micro 准入条件已确认）
├── Micro 用户验收已通过（FLOWS.md Micro 链路：用户验收 → ✅ 完成 之间）
└── PMO 输出 Micro 完成报告（事后审计 + 自查摘要）后自动流转到 Ship Stage 第一段
```

🔴 **Micro 升级到敏捷 / Feature 后不走本分支**：升级后 state.json 是 Feature 的，按 Feature Ship Stage 执行（无差异）。

#### 与 Feature / Bug Ship 的关键差异

| 维度 | Feature Ship | Bug Ship 缩简版 | Micro Ship 缩简版（v7.3.10+P0-74） |
|------|-------------|----------------|----------------------------------|
| 状态承载 | `{Feature}/state.json` | BUG-REPORT.md frontmatter | **主对话 + commit hash**（无 state.json · 无元数据文件） |
| 状态字段引用 | `state.ship.{phase/shipped/...}` | BUG-REPORT.md frontmatter `{phase/shipped/...}` | **主对话内 phase 字符串描述**（不写盘） |
| commit message | `F{编号}: Ship Stage - {简述}` | `BUG-{id}: Ship Stage - {简述}` | `micro: {简述}` |
| MR 标题 | `{type}({scope}): {summary}` | `[Bug] {简述} (BUG-{id})` | `micro: {简述}` |
| MR 描述 | 完整 AC 覆盖 / Review / 测试报告 | 根因分析 / 修复方案 / QA 验证 | **变更清单（PMO 已有）+ RD 自查摘要 + 验证结果**（主对话内来源） |
| Step 7 写状态 | 写 state.json | 写 BUG-REPORT.md frontmatter | **不写元数据**（仅完成报告含 commit hash + merge_commit_hash） |
| Step 8 push 内容 | state.json 一文件 | BUG-REPORT.md 一文件 | **跳过**（无元数据可 push · 红线 R1 不需扩展） |
| Worktree 清理 | feature worktree | bugfix worktree | **通常无 worktree**（Micro 默认 worktree=off / 用 chore/* 分支直接在主仓） |
| 完成报告 | Feature 完整 Stage 摘要 | Bug 修复摘要 | Micro 改动摘要 + commit hash + 已合入 origin/{merge_target} 证据 |

#### Micro 分支差异步骤（仅列差异；Step 1/4/5/6 与 Feature 一致）

```
Step 2（push feature）：
  - feature 分支在 Micro 准入时由 PMO 创建（命名 chore/{micro_id}-{简述}），或直接在当前分支
  - push 后记录到主对话内（不写 state.json）：commit_hash / pushed_at（仅口头）

Step 3（第一段报告 + ⏸️）：
  - MR URL 标题用 `micro: {简述}`
  - MR description 来源（来自主对话）：变更清单（PMO 初步分析时已列）/ RD 自查摘要（规范符合 + 回归通过）/ 验证结果（build / 单测 / 目视确认）
  - phase 字段：主对话内表述 "shipping"（不写盘）

Step 4-5（合并检测，补充）：
  - 用 `git merge-base --is-ancestor {commit_hash} origin/{merge_target}` 检查（替代 branch -r --contains）
    ├── exit 0 → 已合入 ✅ → 进 Step 10
    └── exit 1 → 未合入 → 主对话 concerns + 告知用户 + 不进 ✅ 完成

📌 **state.py 调用**（v7.3.10+P0-125 · Micro 唯一脚本入口）：

```bash
# verdict=PASS → 已合入；verdict=BLOCKED → 未合入；FAIL → git fetch 缺失或 commit 错
python3 {SKILL_ROOT}/tools/state.py micro-validate \
  --commit {commit_hash} --merge-target {staging|main} --cwd {主工作区}
```

stdout 含 `evidence.command + exit_code + checked_at`，可作为 Micro 事后审计的物证（治本 P0-101 evidence-binding 镜像）。

Step 7（写最终态）：
  - 🔴 **跳过**：Micro 无 state.json / 无 BUG-REPORT.md，无元数据载体
  - phase 状态在主对话完成报告内表述（"shipped" / "merged"）

Step 8（push merge_target）：
  - 🔴 **跳过**：无元数据文件可 push，红线 R1 例外不需要扩展第三类
  - 业务代码已在 MR 合并时入 merge_target

Step 9（清理 worktree）：
  - Micro 默认 worktree=off → 跳过；若用了 chore worktree（极少见）→ 与 Feature 一致清理

Step 10（完成报告）：
  - 必含：变更文件清单 / commit hash / merge_commit_hash / 已合入 origin/{merge_target} 证据 / RD 自查摘要 / Micro 事后审计
  - **不输出** state.json 字段（无）
```

#### Micro Ship 完成报告模板（v7.3.10+P0-74）

```markdown
✅ Micro 需求完成

**改动**：
- {文件}：{摘要}（commit: {commit_hash}）

**发布证据**：
- MR URL：{mr_url}（已合 ✅）
- merge_commit_hash：{merge_commit_hash}
- 已合入 origin/{merge_target}（验证：git merge-base --is-ancestor）

**RD 自查**：
- 规范符合 ✅ / 已有测试无回归 ✅ / Micro 事后审计 ✅
```

#### Micro 流程的入口前置依赖（v7.3.10+P0-74）

```
- 流程类型 = Micro（PMO 已在 triage 完成 Micro 准入条件 5 项检查）
- 用户验收已通过（FLOWS.md Micro 链路 ✅ 验收）
- 当前主对话仍在 PMO 角色（RD 身份切换已恢复）
- worktree=off 时直接当前分支 / worktree=auto 时 chore worktree 已创建
```

📎 **本分支不改主流程结构**——Step 1-10 全部沿用，仅 Step 7 / Step 8 跳过（无元数据载体）/ MR 标题模板 / Step 9 通常跳过有差异。PMO 在 Stage 入口按 `flow_type` 分支选择即可。

---

### Step 1：净化（"解决 git 提交的非预期问题"）

切到 feature worktree 内执行 `git status --porcelain`，按以下分类处理：

| 分类 | 识别规则 | PMO 动作 | state.json 记录 |
|------|---------|---------|----------------|
| 业务改动未 commit | `*.py` / `*.ts` / `*.go` / `src/**` / `tests/**` 等修改 | `git add {files} && git commit -m "F{编号}: Ship Stage - residual changes ({简述})"` + ⚠️ 警告 | `ship.sanitize_log.residual_commits[]` + `concerns[]` 加一条 "前序 Stage 有漏 commit" |
| 白名单临时文件 | `.DS_Store` / `*.pyc` / `__pycache__/**` / `*.log` / `.vscode/` / `.idea/` | 直接清理（`git clean -f`，仅针对白名单） | `ship.sanitize_log.cleaned_files[]` |
| 灰名单文件 | 不在 .gitignore 且不属于业务代码（未知扩展名 / build 产物 / 调试文件） | **不清理也不 commit，在报告里列出让用户决定** | `ship.sanitize_log.suspicious_files[]` |
| detached HEAD / 分支异常 | `git symbolic-ref HEAD` 失败 / 分支名不符 | 🔴 FAIL，暂停点要求用户介入 | `ship.status = "BLOCKED"` |

白名单默认清单（PMO 严格遵守，不扩展）：

```
.DS_Store
Thumbs.db
*.pyc
*.pyo
__pycache__/
*.log
.vscode/
.idea/
*.swp
*.swo
.pytest_cache/
node_modules/  # 仅当项目 .gitignore 已包含时
```

🔴 **灰名单默认策略 = A（报告但不动，用户决定）**：PMO 不得自行 commit 或删除灰名单文件。在完成报告里以 ⚠️ 列出，由用户后续决定处理。

📌 **state.py 调用**（净化结束 · 落库 sanitize_log · 自动 warn residual_commits/suspicious_files 非空）：

```bash
python3 {SKILL_ROOT}/tools/state.py ship-sanitize --feature {artifact_root} \
  --residual-commits '[{"commit":"...","files":["..."],"reason":"..."}]' \
  --cleaned-files .DS_Store,__pycache__/m.pyc \
  --suspicious-files '[{"path":"...","reason":"..."}]'
```

三个参数都可选 · 缺省 = 该列表为空数组。

### Step 2：push feature 分支 + 创建 MR/PR（v7.3.10+P0-99：CLI 优先 + URL 兜底）

#### 2.1 push feature

```bash
cd {worktree.path}
git push -u origin {worktree.branch}
```

失败处理：
- push 被拒（远端有新 commit，多人协作场景）→ 🔴 FAIL，提示用户「feature 分支远端有他人 commit，请手动 `git pull --rebase origin {worktree.branch}` 后重试 Ship Stage」
- 网络失败 → 重试 2 次，仍失败 → 🔴 FAIL

🟢 **为什么不做 rebase 辅助**（v7.3.10+P0-15 决策）：Teamwork Feature 分支本就应该独占，远端有他人 commit 属于异常场景，由用户手工 resolve 更安全。AI 代做 rebase 可能误覆盖他人工作。

#### 2.2 识别 git host

```bash
git remote get-url origin
```

按以下规则解析 `{host, owner, repo}`：

| URL 模式 | host |
|---------|------|
| `https://github.com/{owner}/{repo}.git` 或 `git@github.com:{owner}/{repo}.git` | `github` |
| `https://gitlab.com/{owner}/{repo}.git` 或 `git@gitlab.com:...` | `gitlab` |
| `https://{自建域名}/{owner}/{repo}.git`（localconfig 标注了 self_hosted_gitlab）| `gitlab-self-hosted` |
| `https://gitee.com/{owner}/{repo}.git` | `gitee` |
| `https://bitbucket.org/{owner}/{repo}.git` | `bitbucket` |
| 其他 | `unknown` |

#### 2.3 创建 MR/PR — CLI 优先 + URL 兜底（v7.3.10+P0-99 重构）

> 🟢 **设计意图**：用户实战反馈 "希望直接拿到已创建的 MR URL · 不要让我再点 create 链接"。
>
> 优先级：**Tier 1 CLI 实际创建 → Tier 2 URL 兜底链接**。CLI 失败时 PMO **诊断 + 提示用户处理环境** · 用户决定重试或走 URL 兜底 · PMO 不静默降级。

##### 2.3.1 Tier 1：CLI 优先创建（gh / glab）

按 git host 选择 CLI：

| host | CLI | 命令模板 |
|------|-----|---------|
| github | `gh` | `gh pr create --base {merge_target} --head {feature_branch} --fill --body-file {Feature}/PR-BODY.md`（无 PR-BODY 时 `--fill`）|
| gitlab / gitlab-self-hosted | `glab` | `glab mr create --target-branch {merge_target} --source-branch {feature_branch} --fill`（gitlab-self-hosted 需 `glab auth login --hostname {self_hosted_domain}` 已配置）|
| gitee / bitbucket / unknown | （无标准 CLI tier）| 直接走 § 2.3.2 URL 兜底 |

🔴 **CLI 执行流程**（PMO 严格遵守）：

```
1. command -v {gh|glab}         # 检测 CLI 是否在 PATH
   ├── 不存在 → 跳到 § 2.3.2 URL 兜底 + state.concerns INFO「{cli} 未安装 · 走 URL 兜底」+ 在第一段报告"环境建议"段提示用户安装
   └── 存在 → 继续

2. {cli} auth status            # 检测 CLI 是否已登录
   ├── 未登录 / token 过期 → 提示用户：
   │   「⚠️ {cli} 未登录或 token 过期。请运行：
   │      gh auth login                              （github）
   │      glab auth login --hostname {host}          （gitlab）
   │    完成后回复"重试"PMO 重新创建 MR/PR；
   │    或回复"用 URL 兜底"PMO 跳过 CLI 直接给创建链接」
   │   ⏸️ 用户决策（重试 / URL 兜底 / 取消 Ship）
   └── 已登录 → 继续

3. 执行 {cli} 创建命令
   ├── 成功 → CLI 输出 MR/PR URL（如 https://github.com/owner/repo/pull/123）
   │   ├── 解析 stdout 拿真实 URL
   │   ├── 写 state.ship.mr_url = {真实 URL}
   │   ├── 写 state.ship.mr_creation_method = "cli-gh" / "cli-glab"
   │   ├── 第一段报告显示 "✅ MR/PR 已创建" + URL
   │   └── 跳过 § 2.3.2 URL 兜底
   │
   └── 失败 → PMO 诊断 stderr 分类：
       ├── auth 失败（401 / unauthorized / login）→ 同 Step 2 prompt 用户 login + 重试
       ├── 已存在同分支 MR（"already exists" / 422）→ 用 {cli} pr/mr list 查找现有 MR URL · 复用作 mr_url
       ├── target_branch 不存在（404 base / target not found）→ 提示用户检查 merge_target 是否在 remote
       ├── 网络 / 5xx → 重试 1 次 · 仍失败提示用户查网络
       └── 其他 → 输出 stderr 摘要 · ⏸️ 用户决策（重试 / URL 兜底 / 取消 Ship）
```

🔴 **PMO 失败诊断硬规则**：禁止静默降级到 URL 兜底。CLI 失败必须告知用户具体原因 + 给出可执行的环境配置指令 + 提供"URL 兜底"作为逃生舱。

##### 2.3.2 Tier 2：URL 兜底（CLI 不可用 / 失败 / 平台无 CLI）

按识别出的 host 使用对应模板：

| host | create MR URL 模板 |
|------|------------------|
| github | `https://github.com/{owner}/{repo}/compare/{merge_target}...{feature_branch}?expand=1` |
| gitlab / gitlab-self-hosted | `https://{host_domain}/{owner}/{repo}/-/merge_requests/new?merge_request[source_branch]={feature_branch}&merge_request[target_branch]={merge_target}` |
| gitee | `https://gitee.com/{owner}/{repo}/compare/{merge_target}...{feature_branch}` |
| bitbucket | `https://bitbucket.org/{owner}/{repo}/pull-requests/new?source={feature_branch}&t=1&dest={merge_target}` |
| unknown | 兜底：读 `.teamwork_localconfig.md.mr_url_template`；均无则输出 feature 分支 URL + ⚠️ "未识别平台，请手动在 remote 上创建 MR/PR" |

feature_branch 和 merge_target 在 URL 里需做 URL encoding（`/` → `%2F` 等）。

走兜底时 state.json 写：
- `mr_url`: null
- `mr_create_url`: {生成的 create URL}
- `mr_creation_method`: "url-fallback" / "unknown-platform"

🔴 **target_branch 必含硬规则（v7.3.10+P0-80 实战补强）**：生成 MR URL 后 PMO 必须 self-check URL 中**含目标分支标识**（避免平台默认走 `default branch` 而非 `merge_target`）：

| 平台 | 必含 target 标识（self-check 关键字） |
|------|-------------------------------------|
| github / gitee | URL 路径含 `compare/{merge_target}...{feature_branch}` 段（target 在前 · feature 在后 · 三个点分隔）|
| gitlab / gitlab-self-hosted | URL query 含 `merge_request[target_branch]=` 或 `merge_request%5Btarget_branch%5D=`（URL encoded）|
| bitbucket | URL query 含 `dest=` 参数 |

🔴 **PMO self-check 步骤**：生成 URL 后 grep 上述关键字确认存在；缺失 = 流程偏离 → 重生成 URL · 不输出残缺版给用户。

❌ **反例（v7.3.10+P0-70 实战 case）**：
```
https://git.example.com/owner/repo/-/merge_requests/new?merge_request%5Bsource_branch%5D=feature%2FF059-...
```
缺 `merge_request[target_branch]=` → 用户在平台合 MR 时默认走 default branch（可能合到错误目标 · merge_target 是 staging 而 default 是 main 时尤其危险）。

✅ **正确**：
```
https://git.example.com/owner/repo/-/merge_requests/new?merge_request%5Bsource_branch%5D=feature%2FF059-...&merge_request%5Btarget_branch%5D=staging
```

记入：
```json
{
  "mr_create_url": "https://github.com/owner/repo/compare/staging...feature%2FF042-email-login?expand=1",
  "git_host": "github",
  "feature_pushed_at": "2026-04-22T11:08:12Z",
  "feature_head_commit": "abc1234...",
  "phase": "pushed",
  "shipped": "pushed"
}
```

🔴 **v7.3.10+P0-29 关键步骤**：push 成功后 PMO 必须执行：
```bash
HEAD_COMMIT=$(git rev-parse "feature/{Feature 全名}")
```

📌 **state.py 调用**（落库 phase=pushed + 5 件套 evidence · 自动校验 git_host enum / mr_creation_method enum / cli-* 必带 mr_url / url-fallback 必带 mr_create_url）：

```bash
# CLI 创建路径
python3 {SKILL_ROOT}/tools/state.py ship-push --feature {artifact_root} \
  --feature-head-commit $HEAD_COMMIT --git-host {github|gitlab|...} \
  --mr-creation-method {cli-gh|cli-glab} --mr-url {真实 MR URL}

# URL 兜底路径
python3 {SKILL_ROOT}/tools/state.py ship-push --feature {artifact_root} \
  --feature-head-commit $HEAD_COMMIT --git-host {host} \
  --mr-creation-method {url-fallback|unknown-platform} --mr-create-url {兜底链接}
```

第二段 finalize 时脚本用此 hash 通过 `git branch -r --contains` 检测合并 → ship-confirm-merged。

### Step 3：第一段报告 + 等待合并暂停点

**第一段报告**（CLI 成功 / URL 兜底统一格式 · MR URL 必须独立行裸输出 · cite [../STATUS-LINE.md § 长 URL/长路径不进表格列硬规则](../STATUS-LINE.md)）

```
✅ Ship Phase 1 完成
- feature 分支: {worktree.branch} → {merge_target}
- 净化: residual {N} / 临时 {M} / 灰名单 {K}
- MR/PR {创建方式 cli-gh|cli-glab|url-fallback}:

{mr_url 或 mr_create_url · 独立行裸输出 · 终端可点击}

下一步: 平台合并 → 回 1 启动 Phase 2

请选择(回数字):
1. ✅ 已合并 · 启动收尾 💡
2. ⏳ 还在等待审核 / 合并(可退出 · 下次回此选项)
3. ❌ MR 被关闭未合并(进异常处理)
4. 其他指示
```

🔴 **渲染必含**（cite [../STATUS-LINE.md § 暂停点模板渲染契约](../STATUS-LINE.md) · 决策类暂停点）：
- 📚 决策参考 → ship-report.md / MR URL 独立行裸输出
- 末尾 3 行状态行 → 阶段 enum=`ship` · 「⏸️ MR 待合并」
- URL 兜底场景（mr_creation_method=url-fallback）→ 报告加一行「⚠️ 下次 Ship 装 gh/glab 让 PMO 直接创建 MR」

**用户选择处理**：
- **选 1**：进入第二段 finalize（Step 4-7）
- **选 2**：state.ship.phase 保持 `pushed`，PMO 输出"已记录待合并状态，下次进来回此选项即可继续"，可退出会话；下次进入时 PMO 在 triage 识别 phase=`pushed` → 直接展示 Step 3 暂停点而不重跑 Stage
- **选 3**：进入异常处理段（见下方「异常处理」）
- **选 4**：用户自由表达（PMO 按通用规则承接）

state.ship.phase 在 Step 3 暂停时设为 `pushed`，state.json 写入。worktree 不在第一段清理（v7.3.10+P0-29 改为第二段清理）。

worktree=off 时第一段没有 worktree，第二段 Step 6 跳过 worktree 清理。

---

### Step 4：fetch + 检测合并（第二段 - 用户选 1 后）

```bash
cd {主工作区}
git fetch origin {state.ship.merge_target}
```

执行合并检测：

```bash
if git branch -r --contains "{state.ship.feature_head_commit}" | \
   grep -q "origin/{state.ship.merge_target}"; then
    DETECTED="merged"
else
    DETECTED="not-detected"
fi
```

`branch-contains` 检测覆盖：
- ✅ Merge commit（feature 全部 commit 完整保留在 merge_target）
- ✅ Rebase merge（GitHub fast-forward 保留 hash）
- ❌ Squash merge（commits 被压缩为新 hash）
- ❌ GitLab rebase merge 默认重写（hash 变）

→ Squash / GitLab rebase 重写场景下走 Step 5 询问用户。

### Step 5：检测结果处理

#### 5.A：DETECTED == "merged"（高置信度）

确认合并通过，进入 Step 6。**不在本步写 state.json**（state.json 在 Step 7 统一写入 merge_target 工作区，避免双源）。

记录到内存变量供 Step 7 使用：

```
detected_merge_commit_hash = {feature_head_commit}
detected_method = "branch-contains"
detected_mr_merged_at = $(git log -1 --format=%cI {feature_head_commit})
```

#### 5.B：DETECTED == "not-detected"（询问用户）

```
⚠️ 自动检测未通过

git branch -r --contains {feature_head_commit} 未在 origin/{merge_target} 中找到此 commit。

可能原因：
1. MR 实际未合并（用户误选选项 1）
2. squash merge：commits 被压缩为新 hash，原 hash 不在 merge_target
3. GitLab rebase 重写：hash 被重写

请确认（回复数字）：
1. ✅ 已合并（请提供 merge commit hash）：__________
   → PMO 校验：git cat-file -e {hash} && git branch -r --contains {hash} | grep "origin/{merge_target}"
2. ❌ 实际未合并（回退到第一段暂停点等待）
3. ❌ MR 被关闭未合并（进入异常处理）
4. 其他指示
```

**用户回 1 提供 hash**：
- PMO 用 `git cat-file -e {hash}` 验证 hash 存在
- PMO 用 `git branch -r --contains {hash} | grep "origin/{merge_target}"` 验证 hash 在 merge_target
- 校验通过 → 记录 `detected_merge_commit_hash = {hash}`、`detected_method = "user-reported"`、`detected_mr_merged_at = $(git log -1 --format=%cI {hash})`，state.concerns 加 WARN "用户自报，未通过自动检测"
- 校验失败 → 暂停，让用户重新检查 hash

**用户回 2**：state.ship.phase 回退到 `pushed`，重新进入 Step 3 暂停点。

**用户回 3**：进入异常处理段。

### Step 6：切到 merge_target 主工作区（v7.3.10+P0-32 新增）

```bash
cd {主工作区}                                          # 离开 feature worktree
git checkout {state.ship.merge_target}                # 切到 merge_target 分支（如 staging）
git pull --ff-only origin {state.ship.merge_target}   # 拉合并后的最新 staging
```

🔴 **关键约束**：
- `git pull --ff-only`：仅 fast-forward 拉取，避免本地 staging 有未推 commit 时产生 merge commit
- 拉取后 staging 工作区含 `{Feature}/state.json`（合并时带过来的 phase=pushed 版本）
- 不在 worktree 内做最终态写入——避免 worktree 删除时丢失 state.json 改动

**worktree=off 模式**：跳过 `cd {主工作区}`（本来就在主工作区）；其他步骤照执行。

**git pull --ff-only 失败**（本地 staging 有未推 commit 与 origin 分歧）：
- 输出 WARN：`本地 {merge_target} 与 origin 分歧，无法 fast-forward。请处理后重跑 ship finalize`
- ⏸️ 暂停 + state.concerns 记录
- 不强制处理（避免 PMO 越权解决冲突）

### Step 7-8：写 state.json 最终态 + push merge_target（v7.3.10+P0-125 改 · 走 state.py）

📌 **state.py 调用**（语义化入参 · 自动校验 P0-124 治本三件套：merge_commit_hash + merge_detection_method + mr_merged_at 必齐）：

```bash
# 切到 merge_target 工作区（Step 6 已切）
# 把合并验证 + finalize push 状态一并落库（原子）
python3 {SKILL_ROOT}/tools/state.py ship-confirm-merged --feature {artifact_root} \
  --merge-commit-hash {detected_merge_commit_hash} \
  --merge-detection-method {branch-contains | user-reported} \
  --mr-merged-at {iso8601 · 缺省取 now}
```

push merge_target（红线 R1 例外 · 仅 state.json 一文件 / 仅状态字段）：

```bash
git add {artifact_root}/state.json
git commit -m "F{编号}: ship finalize - state.json → merged"
git push origin {state.ship.merge_target}
```

push 成功 → 立即调脚本记录 push 时刻：

```bash
python3 {SKILL_ROOT}/tools/state.py ship-confirm-merged --feature {artifact_root} \
  --merge-commit-hash {hash} --merge-detection-method {method} \
  --merge-target-pushed-at {iso8601 push 完成时刻}
```

> 上面两次调用形态一致 · phase 已是 merged 时第二次调用是幂等更新 finalize-push 字段。

#### push 失败降级处理

| 失败原因 | 检测方式 | 处理 |
|---------|---------|------|
| **冲突**（staging 被他人推了新 commit）| push 返回 non-fast-forward | `git pull --rebase origin {merge_target}` 重试 1 次 → 仍失败 → 走「降级到 feature 分支」 |
| **protect rule** | push 返回权限错误 | 直接走「降级到 feature 分支」 |
| **网络失败** | push 返回连接错误 | ⏸️ 询问用户：1. 重试 / 2. 降级到 feature 分支 / 3. 跳过 push（仅本地写 state.json）|
| **其他错误** | exit code != 0 | 走「降级到 feature 分支」 |

降级路径：

```bash
git checkout {state.worktree.branch}
git add {artifact_root}/state.json
git commit -m "F{编号}: ship finalize - state.json → merged (degraded: {reason})"
git push origin {state.worktree.branch}

# 调脚本记录失败状态 · 自动追加 concerns WARN
python3 {SKILL_ROOT}/tools/state.py ship-confirm-merged --feature {artifact_root} \
  --merge-commit-hash {hash} --merge-detection-method {method} \
  --merge-target-push-failed --failed-reason {conflict | protect-rule | network | other}
```

🔴 降级后**仍记 phase=merged / shipped=merged**（合并实际已完成）· 脚本自动追加 concerns："{时刻} WARN ship-finalize-push 失败（{reason}）→ 降级到 feature 分支 push · merge_target 上 state.json 仍为 phase=pushed · 用户可手动 cherry-pick 同步状态"。

🔴 **严格边界（红线 R1 例外条款 · v7.3.10+P0-32 / +P0-36）**：
- Feature 流程：仅修改 `{Feature}/state.json` 一个文件 · 仅状态字段（脚本物理拦截非状态字段写入）
- 简单 Bug 流程（P4 适配前临时仍用 Edit BUG-REPORT.md frontmatter · P4 后走 state.py bug-* 子命令）
- 禁止修改（共同）：业务代码 / 其他元数据文件 / 跨 Feature 改动

### Step 9：清理 worktree

🔴 **cleanup 入口硬门禁（v7.3.10+P0-124 · 实证 SVC-CORE-B005 · v7.3.10+P0-125 状态校验由脚本物化）**

📌 **state.py 调用**（脚本物理拦截 phase ≠ merged 的 cleanup · 不靠 PMO 自觉）：

```bash
python3 {SKILL_ROOT}/tools/state.py ship-cleanup --feature {artifact_root} \
  --status {cleaned | deferred | n_a}
```

- `--status cleaned` 在 phase ≠ merged 时脚本直接 exit 1 + 输出 `verdict: BLOCKED` · PMO 需返回 Step 4-5 重做
- `--status n_a`（worktree=off 路径）/ `--status deferred` 不触发 hard gate · 直接 PASS

destructive op 执行前 PMO 仍需即时校验（双层防御 · spec 层 + 脚本层）：

```bash
# 即时校验 · 不依赖 state.json
git branch -r --contains $(git rev-parse {feature_branch}) | grep "origin/{merge_target}"
```

🔴 通过条件（must ALL · 脚本已校验 [2] · spec 层强调 [1][3]）：
- ✅ [1] git branch -r --contains stdout 含 `origin/{merge_target}`（PMO 即时跑）
- ✅ [2] state.ship.shipped == "merged"（脚本拒绝 cleaned 时强校验）
- ✅ [3] Step 4-5 合并检测真实执行过（PMO 自查 · 凭印象推断 = 反模式）

🔴 不通过 → 脚本返回 BLOCKED · PMO 渲染 ⏸️ 暂停（cite [../STATUS-LINE.md § 暂停点模板渲染契约](../STATUS-LINE.md)）：

```
🔴 Cleanup BLOCKED · 合并检测未通过

当前状态：
- git branch -r --contains: {命中状态}
- state.ship.shipped: {值}（应为 "merged"）
- Step 4-5 执行状态: {evidence 存在状态}

可能原因：
- 用户尚未在平台合并 MR
- PMO 跳过 Step 3 ⏸️ 等合并暂停点
- finalize commit push feature branch 被误当作 Step 8 push merge_target

请选(回数字)：
1. 我已合并 · 再触发 Step 4-5 检测
2. MR 未合并 · 保留 worktree · 我去平台操作
3. 检查 git ls-remote 状态后决策
```

❌ **反模式黑名单**（命中 = 流程违规 · 必须重做）：
- 「Phase 1+2 完成」在 MR 未合并时输出
- 把 finalize commit push feature branch 当 Step 8 push merge_target
- 跳过 Step 3 ⏸️ 等合并暂停点直接 Step 4+
- `git branch -D` force-delete 在合并未验证时执行

✅ 检测通过后执行：

```bash
cd {主工作区}                                  # 确保不在 worktree 内
git worktree remove {state.worktree.path}
git branch -d {worktree.branch}                # 安全 delete（让 git 自校验 · 拒绝时见上方 BLOCKER）
```

🔴 禁止：`git push origin --delete {worktree.branch}`（remote feature 分支由平台 auto-delete-on-merge 或团队管理）

worktree=off 时跳过本步。

### Step 10：Feature 完成报告 + 关闭 Stage

📌 **state.py 调用**（三 gate satisfied + 转 completed）：

```bash
# Ship Stage 三 gate 满足（input/process/output 自动按 Step 1→2→9 推进 · 此处补 output）
python3 {SKILL_ROOT}/tools/state.py satisfy-gate --feature {artifact_root} --stage ship --gate output
python3 {SKILL_ROOT}/tools/state.py complete-stage --feature {artifact_root} --stage ship
python3 {SKILL_ROOT}/tools/state.py enter-stage --feature {artifact_root} --stage completed
```

📌 **post-feature 调用**（v7.3.10+P0-137 · scripts-policy R-SP-1/R-SP-2 · KNOWLEDGE check + ROADMAP 派生段渲染）：

```bash
python3 {SKILL_ROOT}/tools/post-feature.py \
  --project-dir {project_root} \
  --features-dir {features_dir_relative} \
  --feature-id {feature_id} \
  [--roadmap {roadmap_relative}] [--knowledge {knowledge_relative}]
```

- exit 0 = OK · ROADMAP AUTO-GENERATED 段已与 state.json 对齐 · KNOWLEDGE 已含 feature_id
- exit 1 = WARN · 非阻断（ROADMAP 无 marker / KNOWLEDGE 未含 feature_id）· stdout warnings 入 state.json · PMO 在完成报告里 cite
- exit 2 = FAIL · 阻断 · state.json 真值损坏 · 必须修复后重跑

🟢 **退役**：旧 `hooks/post-feature.sh` (bash) 在本 patch 删除 · 业务逻辑全迁 `tools/post-feature.py` · 跨宿主一致（CC/Codex/Gemini 同款 cite）· 详见 [../standards/scripts-policy.md](../standards/scripts-policy.md)。

输出 PMO 完成报告（见「Feature 完成报告模板」）· state.json 已通过脚本累计写入 · 本步只输出报告 + 调脚本收尾。

review-log.jsonl 追加一行 `stage: "ship-finalize"`，summary 含 merge_commit_hash + detection_method + push 状态（含降级标注） + post_feature_verdict（OK/WARN）。

---

### 异常处理段

#### 触发：Step 3 选项 3 / Step 5 选项 3（MR 被关闭未合并）

```
⏸️ MR 异常处理

state.ship.phase = "closed_unmerged"

请选择：
1. 🔄 重开 MR：feature 分支需要进一步修改 → 回到 Dev Stage 修复（state.current_stage = "dev"）
2. 📦 放弃 Feature：归档本 Feature → state.ship.shipped = "abandoned"，state.current_stage = "completed"（但标注未交付）
3. ⏳ 暂时等待：用户可能与团队讨论后决定 → state.ship.phase 保持 closed_unmerged，下次进来再决策
4. 其他指示
```

🔴 **渲染必含**（v7.3.10+P0-115 cite + v7.3.10+P0-118-A 骨架）：

📚 决策参考 → ship-report.md / REVIEW.md / 平台 MR 关闭原因（如可获取）

⬇️ 末尾骨架（阶段值 = `ship` enum「⏸️ MR 异常 待处理」）：

```
---
🔄 Teamwork 模式 | 流程：{Feature/敏捷/Bug} | 角色：PMO | {功能字段} | 阶段：⏸️ MR 异常 待处理 | 下一步：⏸️ 用户 4 选 1
📁 {worktree.path}/docs/features/{Feature}/
🌿 分支：{worktree.branch} → {merge_target} | worktree：{worktree.path}
```

📌 **state.py 调用**（按用户选项二选一）：

```bash
# 选 1 / 选 3 → 标记 closed_unmerged（不放弃）
python3 {SKILL_ROOT}/tools/state.py ship-closed --feature {artifact_root} \
  --reason "用户回报 MR 关闭未合并"

# 选 2 → 彻底放弃 Feature → shipped=abandoned + completed_at
python3 {SKILL_ROOT}/tools/state.py ship-closed --feature {artifact_root} --abandon \
  --reason "用户决定放弃 · 未交付"
```

**选 1 重开 MR**：先 `ship-closed`（无 --abandon）→ `enter-stage --stage dev --allow-skip` 回 Dev → 修复后重走 Review → Test → Ship；ship-push 允许 closed_unmerged → pushed 重 push。

**选 2 放弃 Feature**：`ship-closed --abandon` 一次性完成 phase=closed_unmerged + shipped=abandoned + completed_at；之后 `enter-stage --stage completed --allow-skip` 转 completed；输出 PMO 完成报告 + 显式标注「Feature 已放弃 · 未交付」+ worktree 清理（如有 · 走 ship-cleanup）。

**选 3 暂时等待**：`ship-closed`（无 --abandon · 也可不调脚本保持现状），可退出会话；下次 PMO 在 triage 识别 phase=closed_unmerged → 重新展示异常处理选项。

### 过程硬规则

- 🔴 **本 Stage PMO 自主执行，不启 Subagent**
- 🔴 **PMO 不动 merge_target**：禁止 checkout merge_target / merge / push merge_target。合并权 100% 属于用户和平台。
- 🔴 **不删 feature 分支**（本地 + remote 都不删）：feature 分支是 MR 的证据，平台合并后由 auto-delete-on-merge 或用户手动清理
- 🔴 **不新增业务 commit**：只允许 residual commit（净化产物）
- 🔴 **灰名单策略 A**：报告不动，禁止自动 commit 或删除
- 🔴 **push 失败不做智能重试**：push 被拒即 FAIL，让用户手工 resolve 后重跑 Ship Stage
- 🔴 **residual commit 必须在完成报告里高亮**：避免掩盖前序 Stage 的遗漏
- 🔴 **MR URL 必须写 state.json.ship.mr_create_url**：回溯依据
- 🔴 **MR URL 生成失败时必须显式报告**（unknown host 无模板时）：不得伪造 URL

---

## Output Contract

### 必须产出的文件/状态

| 产出 | 说明 | 必填字段 |
|------|------|---------|
| `{Feature}/state.json.ship` | JSON 子对象 | `shipped`, `sanitize_log`, `git_host`, `mr_create_url`, `feature_pushed_at`, `worktree_cleanup`, `started_at`, `completed_at` |
| `{Feature}/state.json.stage_contracts.ship` | 流转契约 | `input_satisfied`, `process_satisfied`, `output_satisfied` |
| `{Feature}/ship-report.md` | Markdown | 净化记录 + push 结果 + MR URL + worktree 处置 |
| `{Feature}/review-log.jsonl` 追加一行 | JSONL | `stage: "ship"`, `status: DONE/FAILED`, `artifact_path: "...mr_create_url..."` |

### 机器可校验条件

- [ ] `git ls-remote origin {feature_branch}` 返回非空（feature 分支已在 remote）
- [ ] `state.json.ship.mr_create_url` 非空且为有效 URL 格式（http/https 开头）或显式的 `null` + `concerns` 含"未识别平台"
- [ ] `state.json.ship.sanitize_log` 三个列表（residual_commits / cleaned_files / suspicious_files）均存在（空数组合法）
- [ ] `state.json.ship.git_host` 已填（github/gitlab/gitlab-self-hosted/gitee/bitbucket/unknown 之一）
- [ ] `review-log.jsonl` 新增 ship 行
- [ ] `state.json.current_stage == "completed"`（成功时）

### Done 判据

- Step 1-2 全部成功（净化完成 + feature push 成功 + MR URL 生成或显式兜底）
- Step 3 worktree 清理动作完成（清理 / 保留 / worktree=off 跳过）
- state.json / review-log 已同步
- 完成报告输出含 MR URL（可点击）

### 返回状态

| 状态 | 条件 | 后续 |
|------|------|------|
| ✅ DONE | 全流程成功 + MR URL 生成（已识别平台）| `current_stage = "completed"`, `shipped = true`, PMO 输出 Feature 完成报告 |
| ⚠️ DONE_WITH_CONCERNS | 成功但有 residual commit / 灰名单文件 / unknown host（URL 需用户手动创建）| 同上，但完成报告必须高亮 concerns |
| ❌ FAILED | push 被拒 / 网络失败 / detached HEAD 等 | ⏸️ 暂停，用户手工 resolve 后重跑 Ship Stage |

---

## 完成报告模板

Step 3 / Step 10 完成时输出（极简 · cite [../STATUS-LINE.md](../STATUS-LINE.md) 末尾 3 行状态行）：

```
✅ Ship Phase {N} 完成
- MR: {mr_url}
- feature 分支: {worktree.branch}（保留 · 由平台 auto-delete 或团队清理）
- 净化: residual {N} / 临时 {M} / 灰名单 {K}
- {phase=pushed → '下一步: 平台合并 → 回 1' | phase=merged → '已合并 · worktree 已清理'}
```

⏸️ worktree 清理暂停点（Step 9 完成后 · 非决策类）：
cite [../STATUS-LINE.md § 暂停点模板渲染契约](../STATUS-LINE.md) · 阶段 enum=`ship`「⏸️ worktree 清理待确认」· 3 选 1（清理 / 保留 / 其他）。

---


## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / FAILED}
├── 执行方式：PMO 主对话自主执行（v7.3.10+P0-15 MR 模式）
├── merge_target：{staging / main / ...}
├── git host：{github / gitlab / ...}
├── MR create URL：{url}
├── feature 分支 push：{成功 / 失败原因}
└── 耗时：{N} min

## 净化记录（Step 1）
├── residual commits：{N 个}
│   {如有 → 列出 commit message + 文件清单 + ⚠️ "前序 Stage 建议补充 commit 习惯"}
├── 清理临时文件：{M 个}
│   {列出清理的白名单文件}
└── 灰名单文件（未处理）：{K 个}
    {列出文件 + 建议动作：加 .gitignore / 手动 commit / 删除}

## MR 信息
├── 平台：{github / gitlab / gitee / bitbucket / unknown}
├── create URL：{mr_create_url}
└── 🔴 feature 分支保留（local + remote），由平台/团队清理

## Worktree 清理
├── 策略：{auto / manual / off}
├── 动作：{清理 / 保留 / n/a}
└── feature 分支：🔴 保留（不删）

## Output Contract 校验
├── feature 分支已在 remote：✅
├── MR/PR 状态：✅ CLI 已创建（{mr_url}）/ ✅ URL 兜底（{mr_create_url}）/ ⚠️ unknown host 需手动
├── mr_creation_method：{cli-gh / cli-glab / url-fallback / unknown-platform}
├── state.json.ship 完整：✅（mr_url 或 mr_create_url 至少一非空）
├── review-log.jsonl 新增 ship 行：✅
└── shipped 标志：✅ true

## Concerns（如有）
{residual commit / 灰名单 / unknown host / 仅本地 push 等}

---
🔄 Teamwork 模式 | 角色：PMO | 功能：F{编号} | 阶段：Ship 完成 | shipped={true/false} | MR：{url 短链}
```

---

## state.json.ship 字段结构

字段权威源：[templates/feature-state.json](../templates/feature-state.json) `ship` 子对象 + 顶部 `_instructions.ship_tracking_v7_3_10_P0_15`。本文件不复述 schema。

通过/失败状态记录在 `state.json.stage_contracts.ship.{input_satisfied, process_satisfied, output_satisfied}`；`shipped: true/false` 仅表达"feature 已推到 remote 且 MR URL 已生成"业务语义。

---

## 反模式（Anti-patterns）

| 反模式 | 正确做法 |
|--------|---------|
| PMO 发现 push 被拒就自动 rebase + 强推 | 🔴 禁止。push 被拒即 FAIL，让用户手工 resolve |
| PMO 本地 checkout merge_target 做 merge | 🔴 禁止。本 Stage 不动 merge_target |
| worktree 清理时顺便 `git branch -D` 删 feature 分支 | 🔴 禁止。feature 分支是 MR 证据，必须保留 |
| push 成功后 `git push origin --delete feature/xxx` | 🔴 禁止。remote feature 分支由平台/团队清 |
| unknown host 时拼凑一个疑似 URL 糊弄过去 | 🔴 必须显式标注 unknown host + 让用户手动创建 |
| CLI 失败静默降级到 URL 兜底（不告知用户）| 🔴 禁止（v7.3.10+P0-99）。CLI 失败必须诊断 + 告知用户具体原因 + 给出可执行的环境配置指令 + 提供"URL 兜底"作为逃生舱 |
| residual commit 产生后不在完成报告高亮 | 必须高亮，否则掩盖前序 Stage 的 commit 遗漏 |
| 清理灰名单文件（即便看起来是临时文件）| 🔴 灰名单策略 A：只报告不动，用户决定 |
| 把 MR 合并状态（merged / open）纳入 Teamwork 状态机 | Teamwork 到"feature 已 push + MR create URL 已生成"即 completed，后续合并状态由平台维护，不回写 state.json |
