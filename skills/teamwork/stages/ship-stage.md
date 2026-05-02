# Ship Stage：双段流程 - push feature → 等待合并 → finalize 收尾（v7.3.10+P0-29）

> PM 验收通过且用户选择「通过 + Ship」后进入本 Stage。
>
> 🟢 v7.3.10+P0-29 重构为**双段流程**：
> - **第一段（push）**：净化 → push feature → 生成 MR URL → ⏸️ 暂停等用户在平台合并
> - **第二段（finalize）**：用户回报合并完成后，PMO 用 `git branch -r --contains` 验证 → 清理 worktree → Feature 标记 completed
>
> 🔴 契约优先：PMO 不动 merge_target、不做本地 merge、不 push merge_target、不删 feature 分支。合并动作由用户在平台 UI 上完成。
>
> 🟢 v7.3.10+P0-15 版本变更：原 v7.3.9 的 6 步 direct-merge 流程（本地 merge + push merge_target + 冲突解决例外）全部取消，简化为 MR 单路径。
> 🟢 v7.3.10+P0-29 进一步：原"生成 MR URL 后即结束"模式留下"AI 看不到合并"的工程缺口；本次改为双段，第二段衔接合并后的 worktree 清理 + Feature completed。

---

## 本 Stage 职责

### 第一段（push）

把已通过 PM 验收的 Feature 分支推到 remote + 生成 MR/PR 创建链接：
- **净化**：处理前序 Stage 遗留的非预期 git 问题（uncommitted changes / 临时文件 / 灰名单）
- **push feature**：把 feature 分支同步到 remote，记录 `state.ship.feature_head_commit`
- **生成 MR URL**：识别 git host（GitHub/GitLab/Gitee/Bitbucket）→ 按平台模板生成 create MR/PR 链接
- **暂停等合并**：输出明确的"下一步该做什么"指引，让用户回平台创建 + 合并 MR；用户回数字触发第二段

第一段完成后 `state.ship.phase = "pushed"`，`state.current_stage` 仍为 `ship`（未到 completed）。

### 第二段（finalize）

用户在平台合并 MR 后回到会话，回选项 1 触发：
- **验证合并**：`git fetch origin {merge_target}` + `git branch -r --contains {feature_head_commit}` 检测合并
- **清理 worktree**：合并验证通过后清理（执行第一段延迟的 worktree 清理）
- **完成报告**：输出 Feature 全程耗时 / 交付物 / Stage 摘要，标记 `state.current_stage = completed`、`state.ship.shipped = "merged"`、`state.ship.phase = "merged"`

本 Stage **不产生 merge commit**（合并由平台处理），也**不删 feature 分支**（MR 合并后由平台/团队自主清理，平台通常支持 auto-delete-on-merge 选项）。

---

## 可配置点清单（v7.3.10+P0-55 新增）

| 可配置点 | 默认值 | 控制字段 | 决策时机 |
|---------|-------|---------|---------|
| `merge_target` | staging（localconfig 配置）| `state.environment_config.merge_target` | triage Step 7.5 探测决策 |
| `git_host` | 自动识别（GitHub / GitLab / Gitee / Bitbucket / 未知）| `state.ship.git_host` | 第一段 push 时识别 |
| `mr_create_url` | 自动按平台模板生成（未知 host 时为 null + concerns 标注）| `state.ship.mr_create_url` | 第一段 push 末段 |
| `worktree_cleanup` | cleaned / deferred / n_a（按 worktree mode 决策）| `state.ship.worktree_cleanup` | 第二段 finalize |
| Bug 简化分支（v7.3.10+P0-36）| 仅 Bug 流程触发 | spec 内嵌 | 流程类型判断 |
| `merge_target` push 边界 | 第二段 finalize 仅允许 state.json / BUG-REPORT.md 一文件（红线 #1 例外）| spec 内嵌硬规则 | 第二段 finalize |

🔴 不变内核：双段流程（第一段 push + 第二段 finalize）+ PMO 不做 merge / 不解决冲突 + push 失败降级（pull --rebase 重试 1 次）+ MR URL 生成。

---

## Input Contract

### 必读文件

```
├── {SKILL_ROOT}/stages/ship-stage.md（本文件）
├── {SKILL_ROOT}/roles/pmo.md（PMO Ship Stage 职责段）
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
Step 1: roles/pmo.md（Ship Stage 职责段）              ← 角色层（L0 稳定）
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
Step 8: commit + push 到 merge_target（v7.3.10+P0-32 红线 #1 例外，仅 state.json 一文件）
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
| Step 8 push 内容 | 仅 `{Feature}/state.json` 一文件 | 仅 `{Feature}/bugfix/BUG-{id}-*.md` 一文件（红线 #1 Ship Finalize 例外扩展，v7.3.10+P0-36） |
| Worktree 清理 | feature worktree | 同上（Bug 也用 worktree） |
| 完成报告 | Feature 完整 Stage 摘要 | Bug 修复摘要（QA 验证 / 文件 / commit / merge_commit）|

#### 各步骤的 Bug 分支差异说明

```
Step 1（净化）：与 Feature 一致，无差异。

Step 2（push feature）：
  - feature 分支由 RD Bug 修复阶段创建（命名 bugfix/BUG-{id}）
  - push 后记录到 BUG-REPORT.md frontmatter `feature_head_commit`（不是 state.json）

Step 3（第一段报告 + ⏸️）：
  - MR URL 标题用 `[Bug] {简述} (BUG-{编号})`
  - MR description 来源：BUG-REPORT.md 的"问题描述 + 根因 + 修复方案 + QA 验证"段
  - phase 字段：BUG-REPORT.md frontmatter `phase = "shipping"`（不是 state.ship.phase）

Step 4-5（合并检测）：与 Feature 一致，无差异。

Step 6（切 merge_target）：与 Feature 一致，无差异。

Step 7（写最终态）：
  - 写入对象：BUG-REPORT.md frontmatter（不是 state.json）
  - 字段：
    - current_stage = "completed"
    - phase = "shipped"
    - shipped = "merged"
    - merge_commit_hash / mr_merged_at / completed_at / worktree_cleanup

Step 8（push merge_target）：
  - 🔴 红线 #1 Ship Finalize 例外条款扩展（v7.3.10+P0-36）：
    Bug 流程允许 push merge_target，仅限 BUG-REPORT.md 一文件、仅元数据字段（frontmatter shipped / merge_commit_hash / completed_at 等）、零业务影响
  - 业务代码（src/ 等）已在 MR 合并时入 merge_target，不重复 push
  - push 失败降级：与 Feature 一致（pull --rebase 重试 1 次 → 退回 feature 分支 push + frontmatter ship_concerns WARN）

Step 9（清理 worktree）：与 Feature 一致，无差异。

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
| Step 8 push 内容 | state.json 一文件 | BUG-REPORT.md 一文件 | **跳过**（无元数据可 push · 红线 #1 不需扩展） |
| Worktree 清理 | feature worktree | bugfix worktree | **通常无 worktree**（Micro 默认 worktree=off / 用 chore/* 分支直接在主仓） |
| 完成报告 | Feature 完整 Stage 摘要 | Bug 修复摘要 | Micro 改动摘要 + commit hash + 已合入 origin/{merge_target} 证据 |

#### 各步骤的 Micro 分支差异说明

```
Step 1（净化）：与 Feature 一致，无差异。
  - Micro 通常单文件，git status 范围极小，净化几乎不会触发任何动作。

Step 2（push feature）：
  - feature 分支在 Micro 准入时由 PMO 创建（命名 chore/{micro_id}-{简述}），或直接在当前分支
  - push 后记录到主对话内（不写 state.json）：commit_hash / pushed_at（仅口头）

Step 3（第一段报告 + ⏸️）：
  - MR URL 标题用 `micro: {简述}`
  - MR description 来源（来自主对话）：
    - 变更清单（PMO 初步分析时已列）
    - RD 自查摘要（规范符合 + 回归通过）
    - 验证结果（build / 单测 / 目视确认）
  - phase 字段：主对话内表述 "shipping"（不写盘）

Step 4-5（合并检测）：与 Feature 一致，无差异。
  - PMO 在用户告知 "已合 MR" 后执行 `git fetch origin {merge_target}`
  - `git merge-base --is-ancestor {commit_hash} origin/{merge_target}` 检查
    ├── exit 0 → 已合入 ✅ → 进 Step 6 完成报告
    └── exit 1 → 未合入（MR 关闭 / pending / 平台异常）→ 主对话 concerns + 告知用户 + 不进 ✅ 完成

Step 6（切 merge_target）：与 Feature 一致，无差异（仅用于查询 merge_commit_hash）。

Step 7（写最终态）：
  - 🔴 **跳过**：Micro 无 state.json / 无 BUG-REPORT.md，无元数据载体
  - phase 状态在主对话完成报告内表述（"shipped" / "merged"）

Step 8（push merge_target）：
  - 🔴 **跳过**：无元数据文件可 push，红线 #1 Ship Finalize 例外不需要扩展第三类
  - 业务代码（Micro 的单文件改动）已在 MR 合并时入 merge_target

Step 9（清理 worktree）：
  - Micro 默认 worktree=off → 跳过本步骤
  - 若 Micro 用了 chore worktree（极少见 · 用户主动开启）→ 与 Feature 一致清理

Step 10（完成报告）：
  - 报告对象：Micro 改动
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

### Step 2：push feature 分支 + 生成 MR create URL

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

#### 2.3 生成 MR create URL

按识别出的 host 使用对应模板：

| host | create MR URL 模板 |
|------|------------------|
| github | `https://github.com/{owner}/{repo}/compare/{merge_target}...{feature_branch}?expand=1` |
| gitlab / gitlab-self-hosted | `https://{host_domain}/{owner}/{repo}/-/merge_requests/new?merge_request[source_branch]={feature_branch}&merge_request[target_branch]={merge_target}` |
| gitee | `https://gitee.com/{owner}/{repo}/compare/{merge_target}...{feature_branch}` |
| bitbucket | `https://bitbucket.org/{owner}/{repo}/pull-requests/new?source={feature_branch}&t=1&dest={merge_target}` |
| unknown | 兜底：读 `.teamwork_localconfig.md.mr_url_template`；均无则输出 feature 分支 URL + ⚠️ "未识别平台，请手动在 remote 上创建 MR/PR" |

feature_branch 和 merge_target 在 URL 里需做 URL encoding（`/` → `%2F` 等）。

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
git rev-parse "feature/{Feature 全名}"
```
取得 feature 分支当前 HEAD 的 commit hash，写入 `state.ship.feature_head_commit`。第二段 finalize 时用此 hash 通过 `git branch -r --contains` 检测合并。

### Step 3：第一段报告 + 等待合并暂停点（v7.3.10+P0-29 重构）

输出第一段报告（见「第一段报告模板」），然后暂停：

🔴 **MR URL 渲染硬规则（v7.3.10+P0-70）**：
- MR/PR 创建链接**必须独立成行**输出（裸 URL · 行首行尾 whitespace 边界 · 终端识别为可点击 hyperlink）
- **禁止挤入 markdown 表格列** — 长 URL 进表格会被列宽切碎多行 / 全角竖线干扰识别 → 用户无法点击
- 禁止用全角括号或中文标点紧贴 URL（违反 P0-67 路径边界规则）
- 禁止把 URL 嵌入 markdown 链接语法 `[文字](URL)` 当报告主呈现（链接文本可附加，但 URL 本体仍要独立一行）

```
✅ Ship Stage 第一段完成 - 等待用户在平台合并

📦 当前状态：
- feature 分支已 push: feature/{Feature 全名}
- feature_head_commit: {abc1234}
- 净化检查: ✅ 无遗留 commits / 可疑文件
- worktree: {worktree.path}（暂保留，待第二段验证合并后清理）

🔗 MR/PR 创建链接：

{mr_create_url}

📋 后续步骤（你需要做的）：
1. 点击上方 MR/PR 创建链接
2. 在平台完成 MR 描述、走 CR / CI、与 reviewer 讨论
3. 在平台合并 MR/PR
4. ⬇️ 合并完成后回到这里回复数字，PMO 启动第二段收尾流程 ⬇️

请选择：
1. ✅ 已在平台合并 MR/PR，启动收尾（PMO 验证合并 + 清理 worktree + Feature 标记 completed） 💡
2. ⏳ 还在等待审核 / 合并（你可以暂时退出会话，下次回来再回此选项）
3. ❌ MR 被关闭未合并（进入异常处理）
4. 其他指示
```

❌ **错误示例**（实证 2026-04-30 截图）：

```
| 项 | 状态 |
|----|------|
| feature/F059-... push | ✅ origin (commits ...) |
| MR 创建链接 | https://git.okok.ai/matrix/vlite/-/merge_requests/new?merge_request%5Bsource_branch%5D=feature%2FF059-relax-package-check |
| MR 合并状态 | 未合并 |
```
→ URL 被表格列宽切成多行 / 全角竖线干扰 / 用户无法直接点击

✅ **正确示例**（spec 默认）：

```
📦 当前状态：
- feature 分支已 push: feature/F059-relax-package-check (commits 8c35b83 + 7f03d62)
- 净化检查: ✅ 无遗留 commits / 可疑文件

🔗 MR/PR 创建链接：

https://git.okok.ai/matrix/vlite/-/merge_requests/new?merge_request%5Bsource_branch%5D=feature%2FF059-relax-package-check

⏳ MR 合并状态: 未合并（git fetch + git log main 仍是 b7763d5）
```
→ URL 独立行 · 前后 whitespace 边界 · 终端可点击

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

### Step 7：写 state.json 最终态（v7.3.10+P0-32 新增）

在 merge_target 工作区内的 feature 目录写 state.json 最终态：

```json
{
  "current_stage": "completed",
  "ship": {
    "phase": "merged",
    "shipped": "merged",
    "merge_commit_hash": "<detected_merge_commit_hash>",
    "merge_detection_method": "branch-contains | user-reported",
    "mr_merged_at": "<detected_mr_merged_at>",
    "completed_at": "<ISO 8601 UTC>",
    "worktree_cleanup": "cleaned"
  }
}
```

🔴 **严格边界（v7.3.10+P0-32 / +P0-36 红线 #1 例外条款）**：
- **Feature 流程**：仅修改 `{Feature}/state.json` 一个文件，仅修改状态字段（current_stage / ship.phase / ship.shipped / ship.merge_commit_hash / ship.mr_merged_at / ship.merge_detection_method / ship.completed_at / ship.worktree_cleanup）
- **简单 Bug 流程**（v7.3.10+P0-36 扩展）：仅修改 `{Feature}/bugfix/BUG-{id}-*.md` 一个文件，仅修改 frontmatter 元数据字段（current_stage / phase / shipped / merge_commit_hash / mr_merged_at / completed_at / worktree_cleanup / merge_target_pushed_at）
- 禁止修改（共同）：业务代码 / 其他元数据文件（PRD/TC/TECH/UI 等）/ 跨 Feature 改动

### Step 8：commit + push 到 merge_target（v7.3.10+P0-32 新增红线 #1 例外）

```bash
git add docs/features/{Feature}/state.json
git commit -m "F{编号}: ship finalize - state.json → merged"
git push origin {state.ship.merge_target}
```

记录 `state.ship.merge_target_pushed_at = "<ISO 8601 UTC>"`。

#### push 失败降级处理

| 失败原因 | 检测方式 | 处理 |
|---------|---------|------|
| **冲突**（staging 被他人推了新 commit）| push 返回 non-fast-forward | `git pull --rebase origin {merge_target}` 重试 1 次 → 仍失败 → 走「降级到 feature 分支」 |
| **protect rule**（review approved required）| push 返回权限错误 | 直接走「降级到 feature 分支」 + state.concerns 加 "merge_target 受保护，请人工合并 state.json 更新" |
| **网络失败** | push 返回连接错误 | ⏸️ 询问用户：1. 重试 / 2. 降级到 feature 分支 / 3. 跳过 push（仅本地写 state.json） |
| **其他错误** | exit code != 0 | 走「降级到 feature 分支」 + state.concerns 含 stderr 摘要 |

#### 降级到 feature 分支

```bash
git checkout {state.worktree.branch}                    # 切回 feature 分支
git add docs/features/{Feature}/state.json              # state.json 应是 Step 7 写入的最终态
git commit -m "F{编号}: ship finalize - state.json → merged (degraded: merge_target push failed)"
git push origin {state.worktree.branch}                 # push 到 feature 分支
```

state.json 写入：

```json
{
  "ship": {
    "merge_target_pushed_at": null,
    "merge_target_push_failed": true,
    "merge_target_push_failed_reason": "<reason>"
  },
  "concerns": [
    "merge_target push 失败（{reason}）→ 降级到 feature 分支 push；staging 上 state.json 仍为 phase=pushed；用户可手动 cherry-pick {feature 分支 commit hash} 到 staging 同步状态"
  ]
}
```

🔴 降级后**仍记 phase=merged / shipped=merged**（合并实际已完成，只是 push merge_target 没成功），不影响 PMO 后续 triage 的 git 推断（git branch -r --contains 仍能识别已合并）。

### Step 9：清理 worktree

```bash
cd {主工作区}                                  # 确保不在 worktree 内
git worktree remove {state.worktree.path}
```

🔴 禁止：`git branch -D {worktree.branch}`（feature 分支在 remote 已合并，本地保留作历史）
🔴 禁止：`git push origin --delete {worktree.branch}`（remote feature 分支由平台 auto-delete-on-merge 或团队管理）

worktree=off 时跳过本步。

### Step 10：Feature 完成报告

输出 PMO 完成报告（见「Feature 完成报告模板」）。state.json 已在 Step 7 + Step 8（含降级路径）完整写入，本步只输出报告，不再写 state.json。

review-log.jsonl 追加一行 `stage: "ship-finalize"`，summary 含 merge_commit_hash + detection_method + push 状态（含降级标注）。

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

**选 1 重开 MR**：state.current_stage = `dev`，回到 Dev Stage；feature 分支保留，用户在 worktree 内修改 → 重新走 Review → Test → Ship 流程（重新进入 Ship Stage 第一段）。

**选 2 放弃 Feature**：
- state.ship.shipped = `abandoned`
- state.current_stage = `completed`（流程已结束，但 Feature 未交付）
- 输出 PMO 完成报告 + 显式标注"Feature 已放弃，未交付"
- worktree 清理（如有）

**选 3 暂时等待**：state.ship.phase 保持 `closed_unmerged`，可退出会话；下次进入 PMO 在 triage 识别该状态 → 重新展示异常处理选项。

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

## 完成报告模板（Step 3 输出）

```
📤 Ship Stage 完成报告（F{编号}-{功能名}）
============================================

## 合并准备就绪
╔══════════════════════════════════════════════════╗
║  🔗 创建 MR / PR:                               ║
║  {mr_create_url}                                 ║
║                                                  ║
║  （点击链接打开平台 UI 创建 Merge Request）     ║
╚══════════════════════════════════════════════════╝

## 分支信息
├── feature 分支（已 push）：{worktree.branch}
├── 目标分支：{merge_target}
├── git host：{github / gitlab / ...}
└── push 时间：{ISO 时间戳}

## 净化记录（Step 1 产物）
├── residual commit：{N 个} {如有 → ⚠️ 提示"前序 Stage 可能漏 commit"}
├── 清理临时文件：{M 个}（白名单）
└── 灰名单文件（⚠️ 未处理，由你决定）：
    - {file1}（{理由：未知扩展名 / build 产物 / ...}）
    - {file2}

## 变更概览
├── 变更文件数：{N}
├── diff stats：+{A} / -{B}
└── commits 列表（feature 分支）：
    - {hash} {msg}
    - {hash} {msg}

## 下一步（交给用户和平台）
├── 1️⃣ 点上方链接创建 MR/PR，填描述
├── 2️⃣ 等 CI + Code Review（平台工作，Teamwork 不介入）
├── 3️⃣ 平台合并（squash / rebase / merge commit 按团队规则）
└── 4️⃣ 合并后 feature 分支由平台 auto-delete 或团队手动清理（Teamwork 不删）

## Worktree 处置
├── 策略：{auto / manual / off}
├── 动作：{清理 / 保留 / n/a（off 时）}
└── 🔴 feature 分支（本地 + remote）：保留（由平台/用户清理）

⏸️ worktree 清理（回复数字）
1. 🧹 清理 worktree ← 💡 推荐
2. 💾 保留 worktree
3. 其他指示
```

---

## 执行报告模板（Ship Stage DONE 后写入）

```
📋 Ship Stage 执行报告（F{编号}-{功能名}）
============================================

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
├── mr_create_url 有效：✅ / ⚠️ unknown host 需手动
├── state.json.ship 完整：✅
├── review-log.jsonl 新增 ship 行：✅
└── shipped 标志：✅ true

## Concerns（如有）
{residual commit / 灰名单 / unknown host / 仅本地 push 等}

---
🔄 Teamwork 模式 | 角色：PMO | 功能：F{编号} | 阶段：Ship 完成 | shipped={true/false} | MR：{url 短链}
```

---

## state.json.ship 字段结构

> 字段权威：详见 `templates/feature-state.json` 的 `ship` 字段 + 顶部 `_instructions.ship_tracking_v7_3_10_P0_15`。以下为示例数据（merge_target 从顶层 `state.json.merge_target` 读取，不在 ship 子对象中重复）。

```jsonc
"ship": {
  "shipped": true,                        // 是否已推到 remote + 生成 MR URL
  "git_host": "github",                   // github / gitlab / gitlab-self-hosted / gitee / bitbucket / unknown
  "mr_create_url": "https://github.com/owner/repo/compare/staging...feature%2FF042?expand=1",
  "feature_pushed_at": "2026-04-22T11:08:12Z",
  "sanitize_log": {
    "residual_commits": [                 // 净化阶段自动 commit 的 residual
      { "commit": "abc1...", "files": ["src/x.py"], "reason": "Dev Stage 漏 commit" }
    ],
    "cleaned_files": [".DS_Store", "__pycache__/mod.pyc"],
    "suspicious_files": [
      { "path": "build/output.txt", "reason": "未知扩展名，疑似 build 产物" }
    ]
  },
  "worktree_cleanup": "cleaned",          // cleaned / deferred / n_a (worktree=off)
  "started_at": "2026-04-22T11:00:00Z",
  "completed_at": "2026-04-22T11:08:12Z"
}
```

> 通过/失败状态记录在 `state.json.stage_contracts.ship.{input_satisfied, process_satisfied, output_satisfied}`；`shipped: true/false` 仅表达"feature 是否已推到 remote 且 MR URL 已生成"的业务语义。

---

## 反模式（Anti-patterns）

| 反模式 | 正确做法 |
|--------|---------|
| PMO 发现 push 被拒就自动 rebase + 强推 | 🔴 禁止。push 被拒即 FAIL，让用户手工 resolve |
| PMO 本地 checkout merge_target 做 merge | 🔴 禁止。本 Stage 不动 merge_target |
| worktree 清理时顺便 `git branch -D` 删 feature 分支 | 🔴 禁止。feature 分支是 MR 证据，必须保留 |
| push 成功后 `git push origin --delete feature/xxx` | 🔴 禁止。remote feature 分支由平台/团队清 |
| unknown host 时拼凑一个疑似 URL 糊弄过去 | 🔴 必须显式标注 unknown host + 让用户手动创建 |
| residual commit 产生后不在完成报告高亮 | 必须高亮，否则掩盖前序 Stage 的 commit 遗漏 |
| 清理灰名单文件（即便看起来是临时文件）| 🔴 灰名单策略 A：只报告不动，用户决定 |
| 把 MR 合并状态（merged / open）纳入 Teamwork 状态机 | Teamwork 到"feature 已 push + MR create URL 已生成"即 completed，后续合并状态由平台维护，不回写 state.json |
