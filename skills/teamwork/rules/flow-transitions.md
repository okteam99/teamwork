# 阶段状态转移表

> 🟢 **render-first 物化（v7.3.10+P0-143 · R-SP-6 第二阶段）**：阶段流转校验行（📋 行）由 [`tools/render-flow-transition.py`](../tools/render-flow-transition.py) 持单源 · 工具直接 read 本文件 · 编造 L行号 / 原文不可能。
> ```bash
> python3 {SKILL_ROOT}/tools/render-flow-transition.py --from "设计批 待确认" --to "Blueprint"
> # 输出含真实 L行号 + 原文 · 多匹配/未匹配自动 exit 2
> ```
> **❌ 禁止手敲 `📋 X → Y（📖 ...，来源：L...）`** · 必须调工具。
>
> 🔴 PMO 在阶段切换前，必须对照此表确认流转类型。不在表中的转移路径为非法。
> 每行的「流转」列标明：🚀自动 = 不暂停直接流转；⏸️暂停 = 等用户确认；🔀条件 = 按条件决定。
> 此文件为阶段转移的权威定义，校验行必须引用此表的行号+原文。

---

## 🔴 状态行触发规则（v7.3.10+P0-118-A 新增 · 阶段流转校验行 ≠ 状态行）

> **触发**：实战 case（PTR-F001-BUG-013 Bug Ship Phase 1）PMO 输出 📋 阶段流转校验行 + 自定义摘要「当前状态：xxx」 · 漏标准 3 行状态行 · 命中 STATUS-LINE.md 相似格式漂移黑名单。
>
> **根因**：「阶段流转校验行」和「末尾状态行」是**两类不同输出** · PMO 容易把前者当成「状态相关已输出」就跳过后者。

### 触发表

| 流转类型 | 输出 | 是否暂停 |
|---------|------|---------|
| 🚀 **自动流转** | 仅输出 📋 阶段流转校验行 · 继续 silent 执行下一步 · **不输出状态行** | 否（与 P0-105 silent execution 一致）|
| ⏸️ **暂停流转** | 输出 📋 阶段流转校验行 + 🔄 末尾标准 3 行状态行 + 📚 决策参考（决策类）· **缺一即流程偏离** | 是 |
| 🔀 **条件流转** | 按条件 resolve 后归入 🚀 或 ⏸️ 二选一 | 视条件 |

### 反模式（命中 = 流程偏离）

```
❌ ⏸️ 暂停点把 📋 阶段流转校验行当成"状态相关已输出"就跳过末尾 🔄 状态行
   实证：PTR-F001-BUG-013 case · v7.3.10+P0-118-A
❌ 用 `当前状态：xxx` / `📍 Teamwork：xxx` 摘要替代标准 3 行状态行
   cite STATUS-LINE.md 反模式黑名单
❌ 暂停点漏 📚 决策参考段（决策类暂停点必须含）
   cite STATUS-LINE.md § 决策点参考文档绝对路径硬规则
```

### 与 silent execution（P0-105）的边界

```
silent 限于：自动流转中间过程 / 框架仪式 / Step 头 / 思考链
silent 不豁免：暂停点终态产出（状态行 + 决策参考）
   原因：暂停点是用户决策入口 · 必须给齐渲染态
```

---

## ⚡ auto 模式豁免速查（v7.3.9+P0-11 新增 / v7.3.10+P0-76 引入 HITL/AFK mode 字段）

> `/teamwork auto [需求]` 开启 AUTO_MODE 后，本表所有 ⏸️暂停 行按 **mode 字段** 决定行为。
>
> 🔴 **mode 字段定义（v7.3.10+P0-76 新增 · 物理化原"强制保留 vs 豁免"二分）**：
> - **⏸️ HITL**（Human-In-The-Loop）= 当前的"强制保留" → auto 模式**不豁免** · 用户必须显式响应（涉及新业务判断 / 技术分歧 / 破坏性授权 / 红线 / 决策类暂停点）
> - **⏸️ AFK**（Away-From-Keyboard）= 当前的"豁免" → auto 模式**自动推进**按 💡 建议 + 输出 `⚡ auto skip` 日志（意图已被 auto 命令本身承载，「是否继续 / 恢复 / 启动」类）
> - 决策类暂停点（详见 [STATUS-LINE.md § 决策点参考文档绝对路径硬规则](../STATUS-LINE.md)的 10 类）⊆ HITL 集合（自动包含 📚 决策参考绝对路径）
>
> 🔴 **运行时**：未命中下方 HITL 清单 → AFK · 自动推进；命中 → HITL · 保留 + 输出"强制保留"提示

### 🔴 元规则：意图承载豁免（P0-11-A 修订）

```
判定前先问：这个暂停点需要用户给出的决策内容，是不是已经被 auto 命令本身承载了？
├── 是（「是否继续/恢复/启动」类）→ ✅ 豁免
└── 否（需要新的业务判断 / 技术分歧 / 破坏性授权 / 红线处理）→ 🔴 保留

🔴 反模式：auto 命令明说"推进到 Blueprint 完成"，却被中间"外部依赖恢复确认"卡住 → 把用户的命令意图当空气
```

### 🔴 ⏸️ HITL 清单（强制保留 · 即便 AUTO_MODE=true 也必须 ⏸️）

> 下表按"当前阶段 / 条件"定位，避免行号随文件增删漂移。

| 当前阶段 / 条件 | 保留理由 |
|----------------|---------|
| PM 验收 → Ship / 归档 / RD Fix（三选项）| 业务判断，用户决策 |
| worktree 清理待确认 | 用户偏好 |
| 🔗 Ship Stage (push FAILED) → ⏸️ 用户决策 | push feature 失败不可替决（v7.3.10+P0-15：不重试、不降级）|
| 🔗 Ship Stage 等待合并暂停点（4 选 1）| v7.3.10+P0-29：用户必须明确告知 MR 是否合并；auto 模式不能替代用户确认合并完成 |
| 🔗 Ship Stage 第二段检测失败（询问 commit hash）| v7.3.10+P0-29：自动检测未通过，必须用户提供 hash 或确认未合并 |
| 🔗 Ship Stage 异常处理（4 选 1）| v7.3.10+P0-29：MR 关闭未合并，重开/放弃/等待属于业务决策不可替决 |
| 🔗 Ship Stage 第二段 Step 6 pull --ff-only 失败 | v7.3.10+P0-32：本地 merge_target 与 origin 分歧；不强制处理冲突 |
| 🔗 Ship Stage 第二段 Step 8 push merge_target 网络失败（3 选 1）| v7.3.10+P0-32：网络问题需用户决策；冲突自动 pull --rebase 重试 / protect rule 自动降级 |
| 🔗 变更归属检查阻塞（4 选 1：先完成 / 强制启动 / 改独立 / 其他）| v7.3.10+P0-33：变更状态 != locked 或 launch_order 依赖未完成时启动子 Feature 属于业务决策不可替决；强制启动绕过须用户明确选数字 |
| 🔗 变更状态 planning → locked 锁定确认（4 选 1）| v7.3.10+P0-33：变更锁定决策必须用户明确确认（业务/规划层面决策）|
| 🔗 Goal-Plan Stage 评审组合决策（5 选 1：采用推荐 / 全 Subagent / 全主对话 / 自定义 / 其他）| v7.3.10+P0-34：评审角色 + 执行方式由用户在 triage 决定；auto 模式按 PMO 推荐自动应用 + 显式宣告，不算"跳过"|
| 🔗 Goal-Plan Stage 评审循环超 3 轮（5 选 1）| v7.3.10+P0-34：3 轮仍未通过表明评审角色非技术分歧，必须用户介入（强制通过 / 继续 Round 4 / 修改 scope / abort）；auto 模式不豁免 |
| 🔗 Goal-Plan Stage 子步骤 5 用户最终确认 | v7.3.10+P0-34：永远必做（含 auto 模式），用户最终批准 PRD 才能进 Blueprint |
| 🔗 Dev Stage → ⏸️ 用户决策（FAILED）| 环境/逻辑异常 |
| 🔗 Review Stage (FAILED) → ⏸️ 用户决策 | Codex 不可用 / 超 3 轮 |
| 🔗 Test Stage (BLOCKED) → ⏸️ 用户处理 | 环境问题 |
| 🔗 Goal-Plan Stage (分歧) → PRD 待确认 | PL-PM 分歧项 |
| 🔗 Blueprint Stage (concerns) → 方案待确认 | concerns 需人判断 |
| Micro 流程：PMO 执行改动 → 用户验收 | Micro 唯一把关点 |
| Micro 流程：PMO 判定升级 → ⏸️ 升级确认 | 规模升级（切 Plan 模式走敏捷或 Feature）|
| Test Stage 前置确认（立即 / 延后 / 跳过）| 跨 Feature 节奏决策 |

### ✅ ⏸️ AFK 示例（auto 模式自动推进 · 其余 ⏸️ 行默认 AFK）

- triage-stage → Goal-Plan Stage（环境配置已在 triage 决定）：自动进入
- 🔗 Goal-Plan Stage → PRD 待确认 → UI Design / Blueprint：按 💡 自动流转
- 🔗 UI Design Stage → 设计批待确认 → 下一步：按 💡 自动流转
- 🔗 Blueprint Stage → 方案待确认 → Dev Stage：自动进入（无 concerns 时）
- 问题排查：问题排查梳理 → 排查待确认 → PMO / RD / 结束：按 💡 自动推进
- 敏捷需求：PMO 分析 → 精简 PRD → PRD 待确认 → BlueprintLite：按 💡 自动流转
- Micro 流程：PMO 分析 → PMO 执行改动（主对话直接改）：按 💡 自动进入（PMO 自行判断执行方式，无需暂停）
- **外部依赖已就绪 → 恢复流程**（P0-11-A 修订）：auto 命令已承载"恢复"意图 → 按 💡 自动恢复
- **PM Roadmap / Workspace 架构 / teamwork_space.md / Workspace Planning 收尾**：auto 命令已承载"推进 Planning"意图 → 按 💡 自动汇总确认
- **Test Stage → Browser E2E Stage**（P0-11-B 新增）：auto 模式下**默认跳过 Browser E2E**，直接进入 PM 验收；留痕到 `state.json.stage_contracts.browser_e2e` + `review-log.jsonl`；例外见下

### 🟡 P0-11-B：Browser E2E auto 默认跳过

```
AUTO_MODE=true + Test Stage 完成 + TC.md 含 Browser E2E AC
  → 默认跳过 Browser E2E Stage，直接进 PM 验收
  → 留痕：state.json.stage_contracts.browser_e2e = {status: "SKIPPED_BY_AUTO", skipped_at, skip_reason}
  → 追加 review-log.jsonl 一行 {event: "browser_e2e_skipped_by_auto", feature_id, timestamp}
  → PMO 输出 ⚡ auto skip 日志 + PM 验收/完成报告显式标注「⚠️ Browser E2E 已按 auto 模式跳过」
  → 用户逃逸：PM 验收时选"3 返修"或下轮带上「含 browser e2e」关键词

🔴 例外（不跳过）：
  - 命令含 "含 browser e2e" / "带 e2e" / "run e2e" 关键词
  - TC.md 显式 required_even_in_auto=true
  - 手动模式（AUTO_MODE=false）
```

📎 完整规则见 [roles/pmo-auto-mode.md](../roles/pmo-auto-mode.md)（v7.3.10+P0-94 抽出 · auto 模式 + Browser E2E 默认跳过 · 角色契约 [roles/pmo.md](../roles/pmo.md)）。

---

## 会话级 + 流程级 Stage（v7.3.10+P0-26 新增）

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| 会话启动 | 🔗 triage-stage | 🚀自动 | `/teamwork [子命令]` 触发；详见 stages/triage-stage.md（v7.3.10+P0-106 重写为 5 mode 分诊） |
| 🔗 triage-stage (mode A) | 终止 | 🚀自动 | 直接 grep / Read / 答 + 跟进引导 |
| 🔗 triage-stage (mode B) | 🔗 prepare-stage | 🚀自动 | 进 prepare-stage 做重型准备（v7.3.10+P0-106 新增） |
| 🔗 triage-stage (mode C) | 对应 current_stage | 🚀自动 | 找 state.json + jump-to-stage |
| 🔗 triage-stage (mode D) | 终止 | 🚀自动 | 加载看板 + 输出 |
| 🔗 triage-stage (mode E) | 升级 mode | ⏸️暂停 | 给观点 + 选项 + 推荐 + 询问 → 用户拍板后切 mode B/A/C/D |
| 🔗 prepare-stage | 用户确认流程暂停点 | ⏸️暂停 | CLAUDE.md 校验 + KNOWLEDGE/ADR + 流程类型识别 + 流程步骤描述输出 |
| 用户确认流程 | 对应业务 Stage 第一步 | ⏸️暂停 | 用户回数字确认流程类型 → 创建 Feature state.json（如适用）→ 转入对应流程入口 |

🟢 **会话级 / 流程级 Stage 状态归属**（v7.3.10+P0-106 重构）：triage-stage 幂等不持久化（仅分诊 · 不写 state.json）；prepare-stage 仅 mode B 触发（吸收原 init Step 1.2/2 + 原 triage Step 2-9）；Feature state.json 在用户确认流程类型后由 prepare-stage Step 14 创建（按流程类型懒加载 · Feature Planning 不创建）。原 init-stage 已 DEPRECATED · 见 stages/init-stage.md redirect。

---

## Feature 流程

> 🟢 **运行时权威源**（v7.3.10+P0-131）：Stage → Stage 转移图硬编码在 [tools/state.py](../tools/state.py) `FEATURE_FLOW` 字典 · `enter-stage` 物理校验 `legal_next_stages`。本表是**人读语义参考**：标注每个转移的 mode（自动 / 暂停 / 回退）+ 触发条件 · 不再列内部 step 细节（详 stages/{X}-stage.md）。

| 当前阶段 | 允许的下一阶段 | 流转 | 条件（语义） |
|----------|---------------|------|------|
| 🔗 triage-stage | 🔗 Goal-Plan Stage | 🚀自动 | 用户确认走 Feature · environment_config 已写入 |
| 🔗 Goal-Plan Stage | PRD 待确认（暂停点）| ⏸️暂停 | PRD 多轮评审收敛后 · 用户最终确认（详 [goal-plan-stage.md](../stages/goal-plan-stage.md) 内部子步骤）|
| PRD 待确认 | 🔗 UI Design / 🔗 Blueprint | ⏸️暂停 | 用户确认（有 UI → UI Design；无 UI → Blueprint） |
| 🔗 UI Design Stage | 设计批 待确认 | ⏸️暂停 | UI + 全景增量同步一次产出（v7.3.4 合并）|
| 设计批 待确认 | 🔗 UI Design (修订) / 🔗 Blueprint | ⏸️暂停 | 有问题 → 重跑（≤3 轮）；通过 → Blueprint |
| 🔗 Blueprint Stage | 方案待确认 | ⏸️暂停 | Blueprint 返回 TC + TECH + 评审报告 |
| 方案待确认 | 🔗 Dev Stage | ⏸️暂停 | 用户确认技术方案 |
| 🔗 Dev Stage | 🔗 Review Stage / ⏸️ 用户决策 | 🚀自动 / ⏸️ | DONE 自动；FAILED 暂停 |
| 🔗 Review Stage | 🔗 Test Stage / Fix 回退 / ⏸️ | 🚀自动 / 🔁回退 / ⏸️ | DONE 自动；NEEDS_FIX ≤3 轮回退；超 3 轮或 CLI 不可用 ⏸️ |
| 🔗 Test Stage | 🔗 Browser E2E / PM 验收 / Fix 回退 / ⏸️ | 🚀自动 / 🔁回退 / ⏸️ | DONE 走 E2E 或 PM 验收；QUALITY_ISSUE 回退；BLOCKED ⏸️ |
| 🔗 Browser E2E Stage | PM 验收 / Fix 回退 | 🚀自动 / 🔁回退 | 通过自动；功能缺陷 ≤3 轮回退 |
| PM 验收 | 🔗 Ship 第一段 / ✅ shipped=false / Fix 派发 | ⏸️暂停 | 三选项（详 [pmo-pm-acceptance-ship.md](../roles/pmo-pm-acceptance-ship.md)）|
| 🔗 Ship Stage 第一段 | 等待合并暂停点 | 🚀自动 | 净化 + push + CLI 创建 MR（详 [ship-stage.md](../stages/ship-stage.md) Step 1-3）|
| 等待合并暂停点 | 🔗 Ship 第二段 / 暂退 / 异常 | ⏸️暂停 | 4 选 1（详 ship-stage.md Step 3）|
| 🔗 Ship Stage 第二段 | ✅ shipped=merged | 🚀自动 | 合并验证 + finalize + 清理（详 ship-stage.md Step 4-9）· `ship-cleanup` 在 phase ≠ merged 时 BLOCKED（治本 P0-124）|
| Ship Stage 异常处理 | 🔗 Dev / shipped=abandoned / 暂等 | ⏸️暂停 | MR 关闭未合并 4 选 1（详 ship-stage.md 异常段）|
| 🔗 Ship Stage (push FAILED) | ⏸️ 用户决策 | ⏸️暂停 | push feature 失败 · 用户 2 选 1（手工 resolve / 取消 Ship） |

## Bug 处理流程（v7.3.10+P0-36 加 Ship Stage 缩简分支）

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| RD Bug 排查 | PMO Bug 判断 | 🚀自动 | 排查报告（BUG-REPORT.md）完成；BUG-REPORT.md frontmatter `current_stage: pmo_classification` |
| PMO Bug 判断 | QA 补充用例 | 🚀自动 | 判定为简单 Bug；frontmatter `classification: simple` |
| PMO Bug 判断 | PM 编写 PRD / Designer / RD 技术方案 / RD 开发+自查 | 🔀条件 | 判定为复杂 Bug → 按起点进入 Feature 流程；frontmatter `classification: complex` + `current_stage: escalated_to_feature`；状态机移交 Feature 的 state.json |
| QA 补充用例 | RD Bug 修复 | 🚀自动 | 用例补充完成；frontmatter `current_stage: rd_fix` |
| RD Bug 修复 | RD Bug 自查 | 🚀自动 | 修复完成 |
| RD Bug 自查 | 架构师 Bug Code Review | 🚀自动 | 自查通过；frontmatter `current_stage: architect_cr` |
| 架构师 Bug Code Review | QA Bug 验证 | 🚀自动 | Review 通过（🔴 必须，无论改动大小）；frontmatter `current_stage: qa_verify` |
| QA Bug 验证 | PM 文档同步 | 🚀自动 | 验证通过；frontmatter `current_stage: pm_doc_sync` |
| PM 文档同步 | PMO Bug 总结 | 🚀自动 | 文档检查完成；frontmatter `current_stage: pmo_summary` |
| PMO Bug 总结 | 🔗 Ship Stage（Bug 缩简分支）| 🚀自动 | v7.3.10+P0-36：PMO 输出 Bugfix 记录 + 自动 commit；frontmatter `phase: summarized`；进入 Ship Stage 缩简版（详见 stages/ship-stage.md「🆕 Bug 流程缩简分支」段）|
| 🔗 Ship Stage 第一段（push, Bug）| Ship 等待合并（Bug）| 🚀自动 | v7.3.10+P0-36 / +P0-113：净化 + push feature + **CLI 优先创建 MR/PR**（command -v glab/gh → 实创建拿 mr_url · 标题 `[Bug] {简述} (BUG-{编号})`；CLI 不可用才走 URL 兜底；🔴 git push 输出的 hint URL 是兜底备选 · 不是首选产物 · 详见 ship-stage.md §2.3 + R8(c)）；frontmatter `phase: shipping` |
| Ship 等待合并（Bug）| 🔗 Ship Stage 第二段（finalize, Bug）| ⏸️暂停 | v7.3.10+P0-36：用户在平台合并 MR 后回数字 1；frontmatter `mr_url` 已填 |
| 🔗 Ship Stage 第二段（finalize, Bug）| Bugfix 完成 ✅ | 🚀自动 | v7.3.10+P0-36：合并验证 → 切 merge_target → 写 BUG-REPORT.md frontmatter shipped/merge_commit_hash/completed_at → push merge_target（仅 BUG-REPORT.md 一文件，红线 R1 Ship Finalize 例外扩展）→ 清理 worktree；frontmatter `current_stage: completed` + `shipped: merged` + `phase: shipped` |
| Ship Stage 异常处理（Bug）| 🔗 RD Bug 修复 / ✅ 已完成（shipped=abandoned）/ 暂时等待 | ⏸️暂停 | v7.3.10+P0-36：MR 关闭未合并 → 用户 4 选 1：1=重开 MR（回 RD Bug 修复）/ 2=放弃 Bug / 3=暂时等待 / 4=其他 |
| 🔗 Ship Stage (Bug, push FAILED) | ⏸️ 用户决策 | ⏸️暂停 | v7.3.10+P0-36：push feature 失败（远端拒绝 / 网络 / 权限）→ 用户 2 选 1：a 手工处理后复跑 Ship / b 取消 Ship（回到 PMO Bug 总结态）。PMO 不重试、不降级为本地操作 |

> 📎 **复杂 Bug 进入 Feature 流程后**，后续转移遵循 Feature 流程表（含 Feature 的 Ship Stage 双段）；BUG-REPORT.md frontmatter 仅保留归属信息，状态机由 Feature 的 state.json 维护。
>
> 📎 **简单 Bug 状态承载**（v7.3.10+P0-36）：BUG-REPORT.md frontmatter 复用 feature-state.json 字段命名（current_stage / phase / shipped / commit_hash / mr_url / merge_commit_hash 等），承担 Bug 流程的 state.json 职能。详见 [templates/bug-report.md](../templates/bug-report.md)。

## 问题排查流程（v7.3.10+P0-30 简化）

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| 🔗 triage-stage（问题排查 + 信号置信度高）| 问题排查执行 | 🚀自动 | v7.3.10+P0-30：跳过 4 选 1 流程确认暂停点；PMO 主动声明 + 直接进入排查执行 |
| 🔗 triage-stage（问题排查 + 信号置信度中/低）| 问题排查执行 | ⏸️暂停 | 走标准 4 选 1 流程确认；用户回 1 → 进入排查执行 |
| 问题排查执行 | 排查待确认 | 🚀自动 | v7.3.10+P0-30：PMO 自主决定排查范围（默认只读，不启本地服务）+ 直接执行 + 输出排查报告（含未实测项标注）|
| 排查待确认 | triage-stage / ✅ 结束 | ⏸️暂停 | v7.3.10+P0-30：用户决策（不处理 / 修复时按规模选 Micro / 敏捷 / Feature / Bug，重走 triage 创建对应流程）|

## Feature Planning 流程（v7.3.10+P0-108 简化为纯执行流程）

> 🟡 **职责正交化**：讨论部分已迁到 E · discuss（mode 层）· 本流程仅承担"写多文档"执行动作。
> 详见 [FLOWS.md § Feature Planning](../FLOWS.md) + [standards/discussion-mode.md](../standards/discussion-mode.md)。

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| prepare-stage 流程类型识别 = Feature Planning | PMO 整理变更摘要 | 🚀自动 | 用户已在 E · discuss 拍板 · 流程类型识别后自动进入 |
| PMO 整理变更摘要 | 变更摘要待确认 | ⏸️暂停 | 摘要含：文件变更点 + Feature 编号分配 + 依赖关系 |
| 变更摘要待确认 | 落地写多文档（同一回合）| ⏸️暂停 | 用户回 ok / 提修改建议 |
| 落地写多文档 | ✅ Planning 完成 | 🚀自动 | sitemap / PROJECT / ROADMAP 全部写入完成 |

**关键变化（vs v7.3.10+P0-108 之前）**：
- ❌ 删除"PM 与用户讨论产品方向"暂停点（讨论已在 E · discuss）
- ❌ 删除"全景设计验收"独立暂停点（合并到变更摘要确认）
- ❌ 删除"PROJECT.md → ROADMAP.md"分多步暂停（合并到一回合写完）
- ✅ 仅 1 个 ⏸️ 确认点（变更摘要）+ 1 个 🚀 执行（写多文档）

## PL 模式

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| PL 引导模式 | PL 讨论模式 | ⏸️暂停 | 草案就绪，等用户审阅 |
| PL 讨论模式 | PL 结论待确认 | ⏸️暂停 | 讨论达成结论，等用户确认 |
| PL 结论待确认 | PL 执行模式 | ⏸️暂停 | 用户确认 |
| PL 执行模式 | CHG 待确认 | ⏸️暂停 | 变更评估完成，等用户确认 |
| CHG 待确认 | PM Roadmap 编写 / PMO 初步分析 | ⏸️暂停 | 用户确认 |

## 变更管理状态转移（v7.3.10+P0-33 新增）

| 当前状态 | 允许的下一状态 | 流转 | 条件 |
|---------|---------------|------|------|
| `discussion` | `planning` | ⏸️暂停 | PL 讨论方向锁定 + 创建 changes/{change_id}.md |
| `planning` | `locked` | ⏸️暂停 | 用户确认锁定（4 选 1：锁定 / 调整 / 拆分 / 其他）—— 所有子 Feature 完整规划完成 |
| `planning` | `discussion` | ⏸️暂停 | 用户选「拆分变更」→ 退回讨论阶段 |
| `locked` | `in-progress` | 🚀自动 | 第一个子 Feature 启动（按 launch_order） |
| `in-progress` | `completed` | 🚀自动 | 所有子 Feature status=completed |
| `discussion / planning / locked / in-progress` | `abandoned` | ⏸️暂停 | 用户决定放弃本变更 |
| `locked / in-progress`（已锁定状态）| 启动归属本变更的子 Feature | ⏸️暂停 | PMO 在 triage Step 6.5 校验 launch_order 拓扑位置（依赖未完成则硬阻塞）|

🔴 **硬阻塞条件**（v7.3.10+P0-33）：
- status != `locked`（即 discussion / planning / abandoned）时禁止启动任何归属本变更的子 Feature
- status == `locked / in-progress` 但当前 Feature 不在 launch_order 下一个可启动节点（依赖未完成）时禁止启动
- 用户可选「强制启动」逃生舱（须显式选数字，不接受 ok / 默认推进），state.concerns 加 WARN

## 敏捷需求流程

> 🔴 敏捷需求 = Feature 精简版。砍掉 PL-PM 讨论+技术评审、UI Design/Panorama、完整 Blueprint（含评审）。
> 用 BlueprintLite Stage（轻量蓝图：简化 TC + 实现计划，无评审）替代完整 Blueprint。
> Dev Stage 保持不变——始终按蓝图执行，不区分 Feature/敏捷模式。

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| PMO 分析 | 精简 PRD 编写 | ⏸️暂停 | 用户确认走敏捷需求流程（📎 worktree=auto 时 PMO 在此处创建 worktree，v7.3.8 前移）|
| 精简 PRD 编写 | PRD 待确认 | ⏸️暂停 | PRD 完成，等用户确认 |
| PRD 待确认 | 🔗 BlueprintLite Stage | ⏸️暂停 | 用户确认 PRD |
| 🔗 BlueprintLite Stage | 🔗 Dev Stage | 🚀自动 | DONE（简化 TC + 实现计划就绪） |
| 🔗 Dev Stage | 🔗 Review Stage | 🚀自动 | DONE（与 Feature 一致） |
| 🔗 Review Stage | 🔗 Test Stage | 🚀自动 | DONE（与 Feature 一致） |
| _后续 Test Stage → Browser E2E → PM 验收 → Ship Stage（v7.3.9）复用 Feature 流程转移表_ | | | |

## Micro 流程

> 🟢 Micro = 省 Plan/Blueprint/UI/Review/Test Stage 的最短 RD 闭环（v7.3 引入 / v7.3.10+P0-20 统一）：代码写权仍归 RD，允许主对话内 PMO→RD 身份切换由 RD 改动（无需 Subagent / Execution Plan / dispatch），或 🔀 判定超出 Micro 白名单时升级到 Plan 模式走敏捷或 Feature。Micro 不是红线 R1 的例外，是独立流程。
> 🔴 **身份切换必读不豁免（P0-16 补丁 / P0-20 保留）**：PMO→RD 身份切换改之前必须真实 Read `roles/rd.md`（职责 + 自查段）+ `standards/common.md`（必读）+ `standards/frontend.md` / `standards/backend.md`（按改动类型加读），并在主对话阶段摘要 cite 1-2 句规范要点。改动后按 `roles/rd.md` 自查段执行。
> 🔴 **反漂移双补丁（P0-20-B）**：
> - **第一人称锚点**：身份切换后阶段摘要首句必须以「作为 RD，……」开头，作为身份锚点
> - **追加改动回退**：RD 身份执行过程中若用户追加新改动请求，必须先跳回 PMO 身份重新做 Micro 准入（通过 → 切回 RD；超出白名单 → 升级）。禁止在 RD 身份下直接接收新需求

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| PMO 分析 | PMO→RD 身份切换、加载 RD 规范 | ⏸️暂停 | 用户确认走 Micro 流程（📎 worktree=auto 时 PMO 在此处创建 worktree，分支名用 `chore/*`；单文件零逻辑变更可允许用户选择 off 跳过）|
| PMO→RD 身份切换、加载 RD 规范 | RD 执行改动 | 🚀自动 | 🔴 Read roles/rd.md + standards/common.md（+ frontend/backend 按需）+ 摘要 cite 规范要点 完成 |
| RD 执行改动 | RD 自查 | 🚀自动 | RD 按变更清单主对话直改完成 |
| RD 自查 | 用户验收 | 🚀自动 | 按 roles/rd.md 自查段执行（规范符合 + 已有测试无回归）|
| RD 执行改动 / RD 自查 | ⏸️ 升级确认 | ⏸️暂停 | 执行前/中/自查中发现超出 Micro 白名单或隐含逻辑变更 → PMO 输出升级原因 → 用户确认走敏捷或 Feature |
| 用户验收 | Ship Stage 第一段 | 🚀自动 | 用户手测/目视确认通过 → 进 Ship Stage（v7.3.10+P0-74：Micro 走完整 Ship · 详见 stages/ship-stage.md § Micro 流程缩简分支）|
| Ship Stage 第一段 | ⏸️ 等用户合 MR | ⏸️暂停 | v7.3.10+P0-113：PMO auto-commit + push feature + **CLI 优先创建 MR/PR**（command -v glab/gh → 实创建拿 mr_url · 标题 `micro: {简述}`；CLI 不可用才走 URL 兜底 · 🔴 git push hint URL 不是产物 · 详见 R8(c)）→ 输出 MR URL · 等用户在平台合 MR |
| ⏸️ 等用户合 MR | Ship Stage 第二段（合入验证） | 🚀自动 | 用户告知 "已合 MR" → PMO 执行 git fetch + git merge-base --is-ancestor 检查合入 |
| Ship Stage 第二段（合入验证） | ✅ 已完成 | 🚀自动 | git merge-base --is-ancestor 通过 → PMO 完成报告（含事后审计 + 自查摘要 + commit hash + merge_commit_hash + 已合入 origin/{merge_target} 证据）|
| Ship Stage 第二段（合入验证） | ⏸️ 合入失败 | ⏸️暂停 | git merge-base --is-ancestor exit 1 → MR 关闭 / pending / 平台异常 → PMO concerns + 告知用户 + 不进 ✅ 完成 |

## 通用特殊状态（适用所有流程）

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| 任意阶段 | ⏳ 等待外部依赖 | 🚀自动 | PMO 判断需等待外部依赖 |
| ⏳ 等待外部依赖 | 外部依赖已就绪 | 🚀自动 | 依赖到位 |
| 外部依赖已就绪 | （暂停前的阶段） | ⏸️暂停 | 用户确认恢复 |
