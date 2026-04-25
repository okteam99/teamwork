# Ship Stage：push feature 分支 + 生成 MR/PR 创建链接（v7.3.10+P0-15 MR 单路径）

> PM 验收通过且用户选择「通过 + Ship」后进入本 Stage。PMO 只做三件事：净化 → push feature → 生成 MR 创建链接并记录。合并动作由用户在平台 UI 上完成。
> 🔴 契约优先：本 Stage PMO 不动 merge_target，不做本地 merge，不 push merge_target。冲突解决权 100% 回归用户。
> 🟢 v7.3.10+P0-15 版本变更：原 v7.3.9 的 6 步 direct-merge 流程（本地 merge + push merge_target + 冲突解决例外）全部取消，简化为 3 步 MR 流程。

---

## 本 Stage 职责

把已通过 PM 验收的 Feature 分支推到 remote + 生成 MR/PR 创建链接：
- **净化**：处理前序 Stage 遗留的非预期 git 问题（uncommitted changes / 临时文件 / 灰名单）
- **push feature**：把 feature 分支同步到 remote
- **生成 MR URL**：识别 git host（GitHub/GitLab/Gitee/Bitbucket）→ 按平台模板生成 create MR/PR 链接
- **记录 + worktree 清理**：MR URL 写入 state.json（回溯用），worktree 由用户决定清理或保留

本 Stage **不产生 merge commit**（合并由平台处理），也**不删 feature 分支**（MR 合并后由平台/团队自主清理，平台通常支持 auto-delete-on-merge 选项）。

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

## Process Contract

### 步骤概览

```
Step 1: 净化（git status 分析 + 分类处理）
    ↓
Step 2: push feature 分支 + 识别 git host + 生成 MR create URL
    ↓
Step 3: 输出完成报告（含 MR URL）+ ⏸️ worktree 清理询问
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
  "feature_pushed_at": "2026-04-22T11:08:12Z"
}
```

### Step 3：完成报告 + worktree 清理暂停点

输出完成报告（见"完成报告模板"），然后暂停：

```
⏸️ worktree 清理（回复数字）

1. 🧹 清理 worktree（保留 feature 分支在 remote / 本地） ← 💡 推荐
2. 💾 保留 worktree + 本地 feature 分支（多轮改动 / 待 MR review 后再改）
3. 其他指示

📌 说明：
├── 🔴 无论选哪项，feature 分支在 remote 始终保留（等 MR 合并后平台自动清理）
└── 选 1 时：git worktree remove {worktree.path}（仅清本地 worktree，不删本地或 remote 分支）
```

**选 1 执行**：
```bash
cd {主工作区}
git worktree remove {worktree.path}
# 🔴 禁止：git branch -D {worktree.branch}
# 🔴 禁止：git push origin --delete {worktree.branch}
```

**选 2 执行**：不动，state.json 记录 worktree_cleanup=deferred。

worktree=off 时跳过本步（没有 worktree 可清）。

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
