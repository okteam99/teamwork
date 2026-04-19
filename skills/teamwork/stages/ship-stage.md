# Ship Stage：Feature 合并到 merge_target（v7.3.9 新增）

> PM 验收通过且用户选择「通过 + Ship」后进入本 Stage。PMO 全程操作：净化 → push feature → 暂停点（merge+push / 仅 merge）→ worktree 清理。
> 🔴 契约优先：本 Stage 由 PMO 自主执行（不启 Subagent），冲突由 PMO 在例外授权内解决，解不了则升级暂停。
> 🟢 v7.3.9 版本变更：原 v7.3.4 的 "PM 验收 + commit + push 合并暂停点" 拆为"PM 验收三选项"+"Ship Stage 独立阶段"两段。

---

## 本 Stage 职责

把已通过 PM 验收的 Feature 分支合入 merge_target（默认 staging）：
- 净化：处理前序 Stage 遗留的非预期 git 问题（uncommitted changes / 临时文件 / 灰名单）
- push feature：把 feature 分支同步到 remote
- 合并：`git merge --no-ff feature/* → merge_target`
- 可选 push merge_target（用户决定）
- worktree 清理

本 Stage **不新增业务 commit**。Ship Stage 产生的 commit 只有两类，都是合并机制产物：
1. residual commit（净化阶段遗留改动自动 commit，记 state.json 警告）
2. merge commit（`git merge --no-ff`）

---

## Input Contract

### 必读文件

```
├── {SKILL_ROOT}/stages/ship-stage.md（本文件）
├── {SKILL_ROOT}/roles/pmo.md（PMO Ship Stage 职责段）
├── {Feature}/state.json（读 worktree.path / worktree.branch / ship.merge_target）
├── 项目根 .teamwork_localconfig.md（读 merge_target / ship_rebase_before_push / worktree_cleanup）
└── 项目根 .gitignore（净化判断白名单/灰名单时参考）
```

### Key Context（PMO 在本 Stage 主对话自行判断，不需填契约字段）

- merge_target 来源层级：state.json.ship.merge_target > .teamwork_localconfig.md > 默认 `staging`
- ship_rebase_before_push 默认 `false`（v7.3.9：兼容多人协作）
- 多人协作场景 feature 分支可能已有他人 commit → 强推前必须 `--force-with-lease`
- worktree=off 时主工作区就是开发环境，切换分支要小心

### 前置依赖

- `state.json.current_stage == "pm_acceptance"`
- PM 验收已在主对话完成（PM 输出验收结论）
- 用户在 PM 验收暂停点选了「1. 通过 + Ship」
- `state.json.stage_contracts.pm_acceptance.output_satisfied == true`

---

## Process Contract

### 步骤概览

```
Step 1: 净化（git status 分析 + 分类处理）
    ↓
Step 2: push feature 分支
    ↓
Step 3 (可选): rebase 到 origin/{merge_target}（ship_rebase_before_push=true 时才做）
    ↓
Step 4: 切到 merge_target 并执行 git merge --no-ff feature/*（本地）
    ↓
Step 5: 输出 Merge 预览 + ⏸️ 暂停点（2 子选项）
    ├── 选 1：git push origin {merge_target}
    └── 选 2：仅本地 merge（不 push）
    ↓
Step 6: worktree 清理（PMO 询问：清理 / 保留）
    ↓
✅ state.json.current_stage = "completed"，shipped=true
```

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

🔴 **灰名单默认策略 = A（报告但不动，用户决定）**：PMO 不得自行 commit 或删除灰名单文件。在 Merge 预览报告里以 ⚠️ 列出，由用户后续决定处理。

### Step 2：push feature 分支

```bash
cd {worktree.path}
git push origin {worktree.branch}
```

失败处理：
- push 被拒（远端有新 commit）→ 判断：
  - `ship_rebase_before_push == true` → 直接跳到 Step 3 做 rebase
  - `ship_rebase_before_push == false` → 🔴 FAIL，提示用户"feature 分支远端有他人 commit，手动同步后重试 Ship Stage"
- 网络失败 → 重试 2 次，仍失败 → 🔴 FAIL

### Step 3：rebase（可选，仅 ship_rebase_before_push=true 时执行）

```bash
cd {worktree.path}
git fetch origin {merge_target}
git rebase origin/{merge_target}
```

处理：
- 无冲突 → 继续
- 有冲突 → PMO 解（见"冲突解决权限"）
- 解完后 → `git push --force-with-lease origin {worktree.branch}`

默认 `false`（v7.3.9 决策）：多人协作场景下 rebase+强推会覆盖其他协作者的本地 feature 分支副本，保守起见默认不做。

### Step 4：切到 merge_target 并本地 merge

切换执行位置的决策：

| 场景 | 执行位置 | 命令 |
|------|---------|------|
| worktree=auto/manual（有独立 feature worktree） | 主工作区（通常在 `{项目根}`，通过 `git worktree list` 找主仓库路径） | `cd {主工作区}` |
| worktree=off | 当前目录（已经在主工作区） | - |

命令序列：

```bash
cd {主工作区路径}
git fetch origin {merge_target}
git checkout {merge_target}
git pull --ff-only origin {merge_target}
git merge --no-ff {worktree.branch} -m "Merge {worktree.branch} into {merge_target} (F{编号}-{功能名})"
```

冲突处理：
- 无冲突 → 继续到 Step 5
- 有冲突 → PMO 解（见"冲突解决权限"）

### Step 5：Merge 预览 + 暂停点（唯一）

PMO 输出 Merge 预览报告（见"Merge 预览模板"），然后暂停：

```
⏸️ 请选择（回复数字即可）

1. 📤 merge + push {merge_target}（执行 git push origin {merge_target}） ← 💡 推荐
2. 💤 仅 merge {merge_target}（本地已合并，push 由你决定）
3. 其他指示（自由输入）
```

**选 1 处理**：
```bash
git push origin {merge_target}
```
- push 成功 → Step 6
- push 失败（远端有新 commit）→ PMO 重试：
  - `git fetch origin {merge_target}`
  - `git pull --rebase origin {merge_target}`（仅 rebase merge commit，不改 feature 历史）
  - `git push origin {merge_target}`（最多重试 2 次）
  - 仍失败 → 🔴 FAIL 挂起，提示用户手动处理

**选 2 处理**：
- 不 push merge_target
- 在完成报告里标注"merge_target 本地已更新，push 由你决定"
- 直接进入 Step 6

### Step 6：worktree 清理（PMO 询问）

worktree=off 时跳过本步。worktree=auto/manual 时：

```
⏸️ worktree 清理（回复数字）

1. 🧹 清理 worktree + 删 feature 分支 ← 💡 推荐（shipped=true 时）
2. 💾 保留 worktree + feature 分支（备查）
3. 其他指示
```

选 1 执行：
```bash
cd {主工作区}
git worktree remove {worktree.path}
git branch -D {worktree.branch}  # 仅当 merge 已成功合入 merge_target 时
```

选 2 → 不动，state.json 记录 worktree_cleanup=deferred。

### 过程硬规则

- 🔴 **本 Stage PMO 自主执行，不启 Subagent**（和其他 Stage 不同）
- 🔴 **不新增业务 commit**：只允许 residual commit（净化产物）和 merge commit（合并产物）
- 🔴 **冲突解决权限边界**：
  - **可解**：git 冲突标记（`<<<<< ===== >>>>>`）的直接消除 / 格式冲突 / import 顺序冲突 / 注释冲突
  - **必须升级**：同一函数内多方修改 / 跨文件协同变更 / 解完需调整其他文件
  - **判定标准**：解完冲突后跑单测（`npm test` / `pytest` / `go test` 等），**全绿 = 可解**；失败或需要改其他文件 = 必须升级
- 🔴 **升级 FAIL 的暂停点**：暂停时给用户三个选项：
  - a. 用户手工介入（进 worktree 自己解）
  - b. 启 RD Subagent 处理（退回到 Subagent dispatch 路径）
  - c. 取消 Ship（Feature 回到 PM 验收态，state.json.ship.status="cancelled"）
- 🔴 **灰名单策略 A**：报告不动，禁止自动 commit 或删除
- 🔴 **PMO 不得强 push merge_target**：merge_target 是共享分支，禁用 `--force` / `--force-with-lease`
- 🔴 **residual commit 必须在完成报告里高亮**：避免掩盖前序 Stage 的遗漏
- 🔴 **暂停点前不得执行 `git push origin {merge_target}`**：push 必须由用户显式确认

---

## Output Contract

### 必须产出的文件/状态

| 产出 | 说明 | 必填字段 |
|------|------|---------|
| `{Feature}/state.json.ship` | JSON 子对象 | `merge_target`, `status`, `shipped`, `sanitize_log`, `rebase_conflicts`, `merge_commit`, `pushed` |
| `{Feature}/ship-report.md` | Markdown | Merge 预览 + 净化记录 + 冲突记录（如有） |
| `{Feature}/review-log.jsonl` 追加一行 | JSONL | `stage: "ship"`, `status: DONE/FAILED`, `commit: {merge_commit_sha}`, `pushed: true/false` |

### 机器可校验条件

- [ ] `git log --oneline origin/{merge_target}` 中包含新的 merge commit
- [ ] `state.json.ship.merge_commit` 非空且为有效 sha
- [ ] `state.json.ship.sanitize_log` 三个列表（residual_commits / cleaned_files / suspicious_files）均存在（空数组合法）
- [ ] `review-log.jsonl` 新增 ship 行
- [ ] `state.json.current_stage == "completed"`（成功时）

### Done 判据

- Step 1-5 全部成功，用户在 Step 5 暂停点做出选择
- 若选 1：`git push origin {merge_target}` exit 0
- 若选 2：本地 merge commit 存在
- Step 6 worktree 清理动作完成（清理或保留）
- state.json / review-log 已同步

### 返回状态

| 状态 | 条件 | 后续 |
|------|------|------|
| ✅ DONE | 全流程成功（含 push / 仅 merge 两种）| `current_stage = "completed"`, `shipped = true`, PMO 输出 Feature 完成报告 |
| ⚠️ DONE_WITH_CONCERNS | 成功但有 residual commit / 灰名单文件 / 冲突解决记录 | 同上，但完成报告必须高亮 concerns |
| 🔁 NEEDS_FIX | Step 3/4 冲突 PMO 可解并已解完 | 继续流转（本质仍是 DONE）|
| ❌ FAILED | 冲突升级 / push 拒绝 / detached HEAD 等 | ⏸️ 暂停，用户选 a/b/c（见硬规则）|

---

## Merge 预览模板（Step 5 暂停点前输出）

```
📊 Ship Stage Merge 预览（F{编号}-{功能名}）
============================================

## 合并信息
├── feature 分支：{worktree.branch}
├── 目标分支：{merge_target}
├── merge commit：{sha, 7位}
├── 合并策略：no-ff
└── rebase 预处理：{否 / 是（无冲突）/ 是（冲突 N 条已解）}

## 净化记录（Step 1 产物）
├── residual commit：{N 个} {如有 → ⚠️ 提示"前序 Stage 可能漏 commit"}
├── 清理临时文件：{M 个}（白名单）
└── 灰名单文件（⚠️ 未处理，由你决定）：
    - {file1}（{理由：未知扩展名 / build 产物 / ...}）
    - {file2}

## 变更概览
├── 变更文件数：{N}
├── diff stats：+{A} / -{B}
└── commits 列表（feature 分支 → merge_target）：
    - {hash} {msg}
    - {hash} {msg}

## 冲突解决（如有）
├── rebase 冲突：{N 条，PMO 已解，单测绿}
└── merge 冲突：{N 条，PMO 已解，单测绿}

## 下一步
远端 origin/{merge_target} 尚未更新。push 后整个团队都会看到本次变更。

⏸️ 请选择（回复数字即可）

1. 📤 merge + push {merge_target}（执行 git push origin {merge_target}） ← 💡 推荐
2. 💤 仅 merge {merge_target}（本地已合并，push 由你决定）
3. 其他指示（自由输入）

📌 选项说明：
├── 2 适合：push 前还想自己 review merge 结果 / 统一多 Feature 批量 push
└── 💡 推荐 1：所有质量门禁均通过，远端同步降低丢失风险
```

---

## 执行报告模板（Ship Stage 完成后）

```
📋 Ship Stage 执行报告（F{编号}-{功能名}）
============================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / FAILED}
├── 执行方式：PMO 主对话自主执行（v7.3.9）
├── merge_target：{staging / main / ...}
├── merge commit：{sha}
├── 本次 push：{已 push / 仅本地}
└── 耗时：{N} min

## 净化记录（Step 1）
├── residual commits：{N 个}
│   {如有 → 列出 commit message + 文件清单 + ⚠️ "前序 Stage 建议补充 commit 习惯"}
├── 清理临时文件：{M 个}
│   {列出清理的白名单文件}
└── 灰名单文件（未处理）：{K 个}
    {列出文件 + 建议动作：加 .gitignore / 手动 commit / 删除}

## 冲突解决（如有）
| 阶段 | 文件 | 冲突类型 | PMO 动作 | 单测结果 |
|------|------|----------|---------|---------|
| rebase | {path} | git 标记 | 采纳 feature 侧 | ✅ 绿 |

## Merge 信息
├── 合并前 feature HEAD：{sha}
├── 合并前 {merge_target} HEAD：{sha}
├── 合并后 {merge_target} HEAD：{sha, merge commit}
└── 合并方式：no-ff

## Worktree 清理
├── 策略：{auto / manual / off}
├── 动作：{清理 / 保留}
└── feature 分支：{已删 / 保留}

## Output Contract 校验
├── merge commit 存在：✅
├── state.json.ship 完整：✅
├── review-log.jsonl 新增 ship 行：✅
└── shipped 标志：✅ true

## Concerns（如有）
{residual commit / 灰名单 / 冲突记录 / 仅本地未 push 等}

---
🔄 Teamwork 模式 | 角色：PMO | 功能：F{编号} | 阶段：Ship 完成 | shipped={true/false}
```

---

## state.json.ship 字段结构

```jsonc
"ship": {
  "merge_target": "staging",              // 实际使用的 merge_target
  "status": "DONE",                       // DONE / DONE_WITH_CONCERNS / FAILED / CANCELLED
  "shipped": true,                        // 是否已合入 merge_target
  "pushed": true,                         // 是否已 push merge_target 到 remote
  "merge_commit": "abc1234...",           // merge commit 的完整 sha
  "merge_target_head_before": "def5678",  // merge 前的 merge_target HEAD
  "feature_head_before": "ghi9012",       // merge 前的 feature HEAD
  "sanitize_log": {
    "residual_commits": [                 // 净化阶段自动 commit 的 residual
      { "commit": "abc1...", "files": ["src/x.py"], "reason": "Dev Stage 漏 commit" }
    ],
    "cleaned_files": [".DS_Store", "__pycache__/mod.pyc"],
    "suspicious_files": [
      { "path": "build/output.txt", "reason": "未知扩展名，疑似 build 产物" }
    ]
  },
  "rebase_conflicts": [                   // ship_rebase_before_push=true 时可能有
    { "file": "src/y.py", "type": "git-marker", "resolved_by": "pmo", "unit_test_green": true }
  ],
  "merge_conflicts": [                    // Step 4 merge 时可能有
    { "file": "src/z.py", "type": "git-marker", "resolved_by": "pmo", "unit_test_green": true }
  ],
  "worktree_cleanup": "cleaned",          // cleaned / deferred / n/a
  "started_at": "2026-04-19T10:00:00Z",
  "completed_at": "2026-04-19T10:08:00Z",
  "duration_minutes": 8
}
```

---

## 反模式（Anti-patterns）

| 反模式 | 正确做法 |
|--------|---------|
| Ship Stage 入口发现 uncommitted changes 就直接 abort | 按分类净化：业务改动 auto commit、临时白名单清理、灰名单报告 |
| PMO 启 Subagent 解 merge 冲突 | Ship Stage PMO 直接解（红线 #1 例外）；解不了就升级 FAIL 让用户选 |
| 合入 merge_target 时用 `git merge` 不加 `--no-ff` | 必须 `--no-ff`（保留 feature 分支拓扑，可整块 revert） |
| push merge_target 失败后用 `--force` | 严禁强推共享分支。失败应 `pull --rebase` 再 push，或报告给用户 |
| 暂停点之前 PMO 悄悄 push merge_target | push 必须用户显式确认（暂停点选 1） |
| residual commit 产生后不在完成报告高亮 | 必须高亮，否则掩盖前序 Stage 的 commit 遗漏 |
| 清理灰名单文件（即便看起来是临时文件）| 🔴 灰名单策略 A：只报告不动，用户决定 |
| worktree=auto 默认自动清理 worktree 不询问 | 必须询问（worktree_cleanup: ask 是默认），用户要看机会 |
