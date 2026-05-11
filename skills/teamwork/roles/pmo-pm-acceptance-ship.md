# PMO PM 验收 + Ship Stage 详规范（PMO PM Acceptance + Ship Stage · v7.3.10+P0-93 抽出）

> 🔗 **角色契约见 [roles/pmo.md](./pmo.md)**（PMO 项目管理角色 + 调度协调）。本文件是 PMO 在 PM 验收暂停点 + Ship Stage 调度的详细任务规范 · 是该任务的**权威源**。
>
> 本文件源流：原寄生在 roles/pmo.md L1430-1665（v7.3.10+P0-15 引入 MR 模式后的 PM 验收 + Ship 完整规范）→ **v7.3.10+P0-93 抽出本文件**（pmo.md 1814 → ~1400 行向 ~500 cap 推进 · Wave 4 Phase 1）。
>
> 适用场景：
> - PM 验收暂停点（3 选 1：通过+Ship / 通过但暂不 Ship / 不通过）
> - Ship Stage 双段执行（push / finalize · v7.3.10+P0-29 双段 / +P0-32 finalize push merge_target）
>
> 🔗 Stage 调度契约：[stages/pm-acceptance-stage.md](../stages/pm-acceptance-stage.md) + [stages/ship-stage.md](../stages/ship-stage.md)

---

## 一、设计目标（v7.3.10+P0-15 MR 模式）

🟢 v7.3.10+P0-15 版本变更：Ship Stage 从「PMO 本地 merge + push merge_target」简化为「MR 模式」——PMO 只负责净化 + push feature + 生成 MR create URL · 合并权由平台和用户处理：

1. **PM 验收暂停点**（§ 二）——3 选 1：通过+Ship / 通过但暂不 Ship / 不通过
2. **Ship Stage**（独立 Stage · 规范见 [stages/ship-stage.md](../stages/ship-stage.md)）——PMO 自主执行净化 → push feature → 生成 MR/PR create 链接 → worktree 清理

🔴 各 Stage 完成前必须 git 干净（v7.3.9 硬规则）：PMO 在每个 Stage 的 `output_satisfied=true` 之前执行 `git status --porcelain` 校验 · 非空则 auto-commit 遗留改动 · commit message 按 `F{编号}: {Stage 名} Stage - {简述}` 模板生成。

🟢 Ship Stage 行为（v7.3.10+P0-15）：Ship Stage PMO **不做**本地 merge / push merge_target / 冲突解决；只负责净化 + push feature + 生成 MR 创建链接。合并权由平台和用户处理（红线 R1 不再有 Ship 例外条款）。

---

## 二、PM 验收暂停点

### 2.1 执行流程

```
PM 完成验收判断（在 PM 角色的主对话 session 中 · 参照 roles/pm.md「验收」）
    ↓
PMO 接管 · 输出 PM 验收摘要 + 3 选 1 暂停点（见下方模板）
    ↓
⏸️ 用户 3 选 1：
├── 1️⃣ ✅ 通过 + Ship → 进入 Ship Stage
│   ├── state.json.current_stage = "ship"
│   └── 按 stages/ship-stage.md 执行（PMO 自主 · 无需再启 Subagent）
│
├── 2️⃣ ✅ 通过 → 仅 commit + push feature 分支 · 暂不合入 merge_target
│   ├── PMO 执行：前序遗留 auto-commit（如有）+ git push origin {feature branch}
│   ├── state.json.ship = { shipped: false, status: "deferred" }
│   ├── state.json.current_stage = "completed"（但 shipped=false）
│   └── PMO 输出完成报告 + 标注「⚠️ 尚未合入 {merge_target} · 用户保留 Ship 决定」
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

### 2.2 PM 验收暂停点模板

```
📊 PM 验收完成 · 等待 Ship 决策
============================================

## 验收结果
├── ✅ PM 验收：通过
├── ✅ Feature 产物完整性校验：通过
└── 📦 Feature 分支：{worktree.branch} @ {HEAD short hash}

## Merge 目标（v7.3.10+P0-15 MR 模式）
├── merge_target: {staging / main / ...}（来源：{state.json / .teamwork_localconfig.md / 默认}）
└── 合入方式：生成 MR/PR create 链接 · 由平台 + 用户完成合入（PMO 不做本地 merge / push merge_target）

💡 建议：1（所有质量门禁通过 · 推荐生成 MR 链接）
📝 理由：
├── 所有 AC 覆盖 ✅ + 所有测试通过 ✅
└── 架构师 CR + QA 审查 + Codex Review 三路均 PASS

⏸️ 请选择（回复数字即可）

1. ✅ 通过 + Ship → 进入 Ship Stage（PMO 执行净化 + push feature + 生成 MR/PR create 链接） ← 💡 推荐
2. ✅ 通过但暂不 Ship → 仅 push feature 分支归档 · 不生成 MR 链接
3. ❌ 不通过（有建议）→ 说明哪个 AC / 哪个文件 / 什么错误 · PMO 派发修复
4. 其他指示（自由输入）

📌 选项说明：
├── 1：所有质量门禁通过且希望生成合入链接 → 推荐
├── 2：想等别的 Feature 一起 Ship / 产品侧要求分批 / 先让别人 review feature 分支
└── 3：用户在浏览器或实操后发现问题（回退循环 ≤3 轮）
```

🔴 **渲染必含**（v7.3.10+P0-115 cite + v7.3.10+P0-118-A 骨架强制）：

📚 决策参考段（cite [STATUS-LINE.md § 决策点参考文档绝对路径硬规则](../STATUS-LINE.md) #6 PM 验收三选项 · 列 PRD/TC/REVIEW/test-report/Browser E2E 截图绝对路径）

⬇️ 末尾照下面骨架填字段（不可省略 · 不可用摘要替代）：

```
---
🔄 Teamwork 模式 | 流程：{Feature/敏捷需求} | 角色：PMO | 功能：{缩写}-F{编号}-{功能名} | 阶段：⏸️ PM 验收（3 选 1） | 下一步：⏸️ 等待用户 3 选 1
📁 {worktree.path}/docs/features/{Feature}/
🌿 分支：{worktree.branch} → {merge_target} | worktree：{worktree.path}
```

详细格式 / emoji 间隔 / 路径边界规则 → cite [STATUS-LINE.md § 状态行格式定义](../STATUS-LINE.md)

### 2.3 选 1（通过 + Ship）后的处理

```
1. state.json.current_stage = "ship"
2. state.json.stage_contracts.pm_acceptance.output_satisfied = true
3. state.json.stage_contracts.pm_acceptance.decision = "approved_and_ship"
4. review-log.jsonl append: { stage: "pm_acceptance", status: "DONE", decision: "approved_and_ship" }
5. 按 stages/ship-stage.md 执行 3 步流（净化 → push feature + 生成 MR create URL → worktree 清理）
   └── Ship Stage 完成后 PMO 输出 Feature 完成报告（含 shipped=true · mr_create_url · worktree_cleanup 字段 · 提示用户到平台合入）
```

### 2.4 选 2（通过但暂不 Ship）后的处理

```
1. 前序遗留 auto-commit（如有）：
   ├── cd {worktree.path}（或主工作区）
   ├── git status --porcelain → 有业务改动 → git add + commit "F{编号}: Ship deferred - residual"
   └── 白名单临时文件清理（同 ship-stage.md Step 1 规则）
2. git push origin {worktree.branch}
   └── push 失败 → ⏸️ 报告错误 · 让用户手动处理
3. state.json.stage_contracts.pm_acceptance.decision = "approved_no_ship"
4. state.json.ship = {
     "shipped": false,
     "feature_pushed_at": "{时间戳}",
     "sanitize_log": {...},
     "mr_create_url": null,
     "worktree_cleanup": null
   }
5. state.json.current_stage = "completed"（即便 shipped=false · Feature 流程主干完成）
6. review-log.jsonl append: { stage: "pm_acceptance", status: "DONE", decision: "approved_no_ship" }
7. PMO 输出 Feature 完成报告（⚠️ 醒目标注 shipped=false + 后续操作提示）
8. /teamwork 看板上该 Feature 标注「⏳ 待 Ship」（可通过 `/teamwork ship F{编号}` 触发后续 Ship Stage）
```

### 2.5 选 3（不通过）修复派发规则

```
PMO 基于用户补充信息判断类型 · 派发到对应阶段：

| 问题类型 | 派发阶段 | 状态变更 |
|---------|---------|---------|
| 功能缺陷（实现错误）| Review Stage（重新 Review + RD 修复）| state.json 回退到 dev 完成后 |
| 测试覆盖遗漏 | Test Stage（补测试）| state.json 回退到 review 完成后 |
| 需求理解偏差 | Goal-Plan Stage（PRD 修订）| state.json 回退到 plan（重走后续全流程）|
| UI/设计不符 | UI Design Stage（设计修改）| state.json 回退到 ui_design |
| 文档缺漏 | 对应角色补文档（不回退 Stage）| 原地修复 |

🔴 规则：
├── 前序 commit 保留（不 revert）—— 记录用户首次验收的真实状态
├── 修复后的代码作为新 commit append · 不篡改历史
├── 修复完成后再次进入「PM 验收暂停点」（允许多轮）
├── 每轮修复 PMO 必须在 review-log.jsonl 追加一条 retry 记录
└── 循环 ≤3 轮 · 超 3 轮 → ⏸️ 用户决策
```

---

## 三、commit 产物清单（各 Stage auto-commit + Ship Stage 净化共用）

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
├── PMO 默认不清理不 commit · 只在 Merge 预览报告里 ⚠️ 列出
└── 用户决定：加 .gitignore / 手动 commit / 删除
```

---

## 四、commit message 模板

**各 Stage auto-commit**（v7.3.9 硬规则产物）：

```
F{编号}: {Stage 名} Stage - {简述}

{body：改动概要}

关联：
- Feature: {缩写}-F{编号}-{功能名}
- Stage: {stage 名}
```

> 📎 v7.3.10+P0-15 说明：Ship Stage 不再产出 `git merge --no-ff` 的 merge commit（PMO 不做本地 merge）。合并 commit 由平台（GitHub/GitLab/Gitee/Bitbucket）在 MR/PR 合入时自动生成 · PMO 不参与。

- type 取值：`feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `perf`
- scope 取值：子项目缩写（如 `AUTH` / `WEB` / `INFRA`）

---

## 五、Ship Stage PMO 职责速查（v7.3.10+P0-29 双段 / +P0-32 finalize push merge_target）

> 📎 完整规范见 [stages/ship-stage.md](../stages/ship-stage.md)。

```
─── 第一段（push） ───
Step 1: 净化（分类处理 uncommitted / 白名单临时 / 灰名单 / 分支异常）
Step 2: git push origin {feature branch}
        + 记录 feature_head_commit = git rev-parse feature/{Feature 全名}
        + git host 识别（github / gitlab / gitlab-self-hosted / gitee / bitbucket / unknown）
        + 🆕 v7.3.10+P0-99 MR/PR 创建（CLI 优先 + URL 兜底）：
          ├── Tier 1：CLI 优先（gh pr create for github · glab mr create for gitlab）
          │   ├── command -v {cli} → 不存在 → 跳 Tier 2 + INFO concern「{cli} 未安装」
          │   ├── {cli} auth status → 未登录 → ⏸️ 提示用户 login + 重试 / URL 兜底
          │   └── 执行成功 → 解析 stdout 真实 MR URL → state.ship.mr_url + mr_creation_method=cli-{gh|glab}
          ├── Tier 2：URL 兜底（CLI 不可用 / 失败 / gitee / bitbucket / unknown）
          │   └── 按平台模板生成 mr_create_url + mr_creation_method=url-fallback
          └── 🔴 失败诊断硬规则：禁止静默降级 · 失败必告知用户具体原因 + 给出 login/install 指令 + 提供 URL 兜底逃生舱
Step 3: 输出第一段报告 + ⏸️ 4 选 1（已合并 / 等待中 / 关闭未合并 / 其他）
        报告变体：A. CLI 成功（显示「✅ MR/PR 已创建」+ mr_url）/ B. URL 兜底（显示「🔗 MR/PR 创建链接」+ mr_create_url + 环境配置建议）
        state.ship.phase = "pushed" · state.ship.shipped = "pushed"
        worktree 不在第一段清理（延迟到第二段）

─── 第二段（finalize · 用户回选项 1 触发 · v7.3.10+P0-32 含 push merge_target 收尾）───
Step 4: git fetch origin {merge_target}
        + git branch -r --contains {feature_head_commit} | grep "origin/{merge_target}"
Step 5: 检测通过 → 记录 detected_merge_commit_hash + detected_method = branch-contains
        检测失败 → ⏸️ 询问用户 4 选 1（提供 hash / 实际未合并 / 关闭 / 其他）
                  用户提供 hash → git cat-file 校验 + branch -r --contains 校验 · method=user-reported + concerns
Step 6: cd {主工作区} + git checkout {merge_target} + git pull --ff-only origin {merge_target}
        worktree=off：跳过 cd（本来就在主工作区）
        pull 失败 → ⏸️ 暂停 + state.concerns（不强制处理冲突）
Step 7: 写 state.json 最终态（在 merge_target 工作区内的 feature 目录）
        🔴 严格边界（红线 R1 例外）：仅 {Feature}/state.json 一文件 · 仅状态字段 · 零业务影响
Step 8: git add {Feature}/state.json + git commit + git push origin {merge_target}
        commit message: "F{编号}: ship finalize - state.json → merged"
        push 失败降级：
          冲突 → pull --rebase 重试 1 次 → 仍失败 → 降级到 feature 分支 push
          protect rule → 直接降级到 feature 分支 push + concerns 提示用户人工合并
          网络失败 → ⏸️ 用户 3 选 1（重试 / 降级 / 仅本地）
        降级仍记 phase=merged / shipped=merged（合并已完成 · 仅 push staging 失败）
Step 9: cd {主工作区} + git worktree remove {worktree.path}（worktree=off 跳过）
Step 10: 输出 Feature 完成报告（state.json 已在 Step 7 + Step 8 完整写入 · 本步只输出报告）

─── 异常分支（用户回 Step 3 选项 3 / Step 5 选项 3） ───
state.ship.phase = "closed_unmerged"
⏸️ 4 选 1：1.重开 MR（回 Dev Stage）/ 2.放弃 Feature（shipped=abandoned）/ 3.暂时等待 / 4.其他

🔴 红线 R1 边界（v7.3.10+P0-32 修订）：
├── ✅ 允许：Step 8 push merge_target 仅 state.json 一文件 · 仅状态字段 · 零业务影响
├── 🔴 禁止：本地 git merge / git rebase / git cherry-pick 到 merge_target
├── 🔴 禁止：动业务代码 / 其他元数据文件（PRD/TC/TECH/UI 等）
├── 🔴 禁止：跨 Feature 改动 push merge_target
├── 🔴 禁止：第一段 push origin {merge_target}（仅第二段 Step 8 是允许的元数据 push）
├── 🔴 禁止：冲突解决（push feature 失败 → ⏸️ 用户决策 · 不重试 · 不降级）
├── 🔴 禁止：伪造 / 猜测 MR URL（git_host=unknown 时 mr_create_url=null + concerns 标注）
└── 🔴 禁止：第一段未完成 / 第二段未验证合并就跳过 worktree 清理或标记 completed

push FAILED 处理（第一段 push feature）：
└── ⏸️ 用户 2 选 1：a 手工处理后复跑 Ship / b 取消 Ship（回到 PM 验收态）

push FAILED 处理（第二段 Step 8 push merge_target）：
└── 自动降级到 feature 分支 push + state.concerns WARN（不阻塞流程）

第一段已完成 · 用户选了等待暂时退出（Step 3 选项 2）：
└── 下次进入会话 · PMO 在 triage 识别 state.ship.phase == "pushed" → 不重跑第一段 · 直接展示 Step 3 暂停点
```
