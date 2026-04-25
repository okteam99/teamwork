# 阶段状态转移表

> 🔴 PMO 在阶段切换前，必须对照此表确认流转类型。不在表中的转移路径为非法。
> 每行的「流转」列标明：🚀自动 = 不暂停直接流转；⏸️暂停 = 等用户确认；🔀条件 = 按条件决定。
> 此文件为阶段转移的权威定义，校验行必须引用此表的行号+原文。

---

## ⚡ auto 模式豁免速查（v7.3.9+P0-11 新增）

> `/teamwork auto [需求]` 开启 AUTO_MODE 后，本表所有 ⏸️暂停 行的默认行为按下列规则调整：
> - ✅ 未命中强制保留清单 → 按 💡 建议自动推进（输出 `⚡ auto skip` 日志）
> - 🔴 命中强制保留清单 → 仍 ⏸️，输出「强制保留」提示

### 🔴 元规则：意图承载豁免（P0-11-A 修订）

```
判定前先问：这个暂停点需要用户给出的决策内容，是不是已经被 auto 命令本身承载了？
├── 是（「是否继续/恢复/启动」类）→ ✅ 豁免
└── 否（需要新的业务判断 / 技术分歧 / 破坏性授权 / 红线处理）→ 🔴 保留

🔴 反模式：auto 命令明说"推进到 Blueprint 完成"，却被中间"外部依赖恢复确认"卡住 → 把用户的命令意图当空气
```

### 🔴 强制保留清单（即便 AUTO_MODE=true 也必须 ⏸️）

> 下表按"当前阶段 / 条件"定位，避免行号随文件增删漂移。

| 当前阶段 / 条件 | 保留理由 |
|----------------|---------|
| PM 验收 → Ship / 归档 / RD Fix（三选项）| 业务判断，用户决策 |
| worktree 清理待确认 | 用户偏好 |
| 🔗 Ship Stage (push FAILED) → ⏸️ 用户决策 | push feature 失败不可替决（v7.3.10+P0-15：不重试、不降级）|
| 🔗 Dev Stage → ⏸️ 用户决策（FAILED）| 环境/逻辑异常 |
| 🔗 Review Stage (FAILED) → ⏸️ 用户决策 | Codex 不可用 / 超 3 轮 |
| 🔗 Test Stage (BLOCKED) → ⏸️ 用户处理 | 环境问题 |
| 🔗 Plan Stage (分歧) → PRD 待确认 | PL-PM 分歧项 |
| 🔗 Blueprint Stage (concerns) → 方案待确认 | concerns 需人判断 |
| Micro 流程：PMO 执行改动 → 用户验收 | Micro 唯一把关点 |
| Micro 流程：PMO 判定升级 → ⏸️ 升级确认 | 规模升级（切 Plan 模式走敏捷或 Feature）|
| Test Stage 前置确认（立即 / 延后 / 跳过）| 跨 Feature 节奏决策 |

### ✅ 豁免示例（其余 ⏸️ 行默认豁免）

- PMO 初步分析 → Plan Stage 入口 preflight：按 💡 自动进入
- Plan Stage 入口 preflight → Plan Stage（4 硬门禁全 ✅）：自动进入
- 🔗 Plan Stage → PRD 待确认 → UI Design / Blueprint：按 💡 自动流转
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

📎 完整规则见 `roles/pmo.md`「⚡ auto 模式暂停点豁免规则」+「🟡 Browser E2E auto 默认跳过」章节。

---

## Feature 流程

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| PMO 初步分析 | Plan Stage 入口 preflight | ⏸️暂停 | 用户确认流程类型+方案后启动；v7.3.9+P0 preflight 暂停点：PMO 执行 worktree+分支+base+工作区干净 共 4 项硬门禁（P0 从原 6 项收敛，详见 stages/plan-stage.md），通过后统一暂停给用户 1 次确认（📎 worktree=auto 时 worktree 也在 preflight 阶段创建，base 显式指向 origin/{merge_target}）|
| Plan Stage 入口 preflight | 🔗 Plan Stage | ⏸️暂停 | Preflight 通过且用户确认 → 进入 Plan Stage（4 项硬门禁全通过；无独立软提示项）|
| 🔗 Plan Stage | PRD 待确认 | ⏸️暂停 | Plan Stage 返回定稿 PRD，等用户确认 |
| 🔗 Plan Stage (分歧) | PRD 待确认 | ⏸️暂停 | 有 PL-PM 分歧项，用户逐项决策后确认 |
| PRD 待确认 | 🔗 UI Design Stage / 🔗 Blueprint Stage | ⏸️暂停 | 用户确认（有 UI → UI Design；无 UI → Blueprint） |
| 🔗 UI Design Stage | 设计批 待确认 | ⏸️暂停 | v7.3.4 合并：Feature UI + 全景增量同步一次性产出，一个暂停点 |
| 设计批 待确认 | 🔗 UI Design Stage (修订) / 🔗 Blueprint Stage | ⏸️暂停 | 有问题→重跑 UI（≤3 轮）；通过→Blueprint |
| 🔗 Blueprint Stage | 方案待确认 | ⏸️暂停 | Blueprint 返回 TC + TECH.md + 评审报告 |
| 🔗 Blueprint Stage (concerns) | 方案待确认 | ⏸️暂停 | 有 concerns，用户确认处理方式 |
| 方案待确认 | 🔗 Dev Stage | ⏸️暂停 | 用户确认技术方案（📎 worktree 已在 Plan Stage 入口创建；本处仅校验存在性，不存在则补建） |
| 🔗 Dev Stage | 🔗 Review Stage | 🚀自动 | DONE（单测全绿） |
| 🔗 Dev Stage | ⏸️ 用户决策 | ⏸️暂停 | FAILED（单测持续失败/环境异常） |
| 🔗 Review Stage | 🔗 Test Stage | 🚀自动 | DONE（三个 review 均通过） |
| 🔗 Review Stage (NEEDS_FIX) | RD Fix → PMO 判断重跑哪些 review | 🔁回退 | ≤3 轮修复循环 |
| 🔗 Review Stage (FAILED) | ⏸️ 用户决策 | ⏸️暂停 | Codex CLI 不可用（走 agents/README.md §三 AI 自主降级 / 跳过）/ 超 3 轮 |
| 🔗 Test Stage | 🔗 Browser E2E Stage / PM 验收 | 🚀自动 | DONE（有 Browser E2E → ⏸️用户确认；无→PM 验收） |
| 🔗 Test Stage (QUALITY_ISSUE) | RD Fix → 重跑 Test Stage | 🔁回退 | ≤3 轮 |
| 🔗 Test Stage (BLOCKED) | ⏸️ 用户处理 | ⏸️暂停 | 环境问题 |
| 🔗 Browser E2E Stage | PM 验收 | 🚀自动 | 通过 |
| 🔗 Browser E2E Stage | RD Fix → 重新 Browser E2E | 🔁回退 | 功能缺陷（≤3 轮） |
| PM 验收 | 🔗 Ship Stage / ✅ 已完成（shipped=false）/ RD Fix | ⏸️暂停 | v7.3.10+P0-15：PM 验收三选项。1=通过+Ship → Ship Stage；2=通过但暂不 Ship → PMO 把前序 Stage 遗留 auto-commit + push feature 分支 + 归档 shipped=false；3=不通过+建议 → 按问题类型派发 RD Fix |
| 🔗 Ship Stage | worktree 清理待确认 | 🚀自动 | v7.3.10+P0-15：PMO 自主执行 Step 1-2（净化 → push feature → 生成 MR create URL），输出 Ship 报告含 MR 链接 |
| worktree 清理待确认 | ✅ 已完成（shipped=true）| ⏸️暂停 | v7.3.10+P0-15：worktree=auto/manual 时询问清理/保留；worktree=off 跳过。之后 PMO 输出 Feature 完成报告（含 MR 链接提示用户去平台合入） |
| 🔗 Ship Stage (push FAILED) | ⏸️ 用户决策 | ⏸️暂停 | v7.3.10+P0-15：push feature 失败（远端拒绝 / 网络 / 权限）→ 用户 2 选 1：a 手工处理后复跑 Ship / b 取消 Ship（回到 PM 验收态）。PMO 不重试、不降级为本地操作 |

## Bug 处理流程

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| RD Bug 排查 | PMO Bug 判断 | 🚀自动 | 排查报告（BUG-REPORT.md）完成 |
| PMO Bug 判断 | QA 补充用例 | 🚀自动 | 判定为简单 Bug |
| PMO Bug 判断 | PM 编写 PRD / Designer / RD 技术方案 / RD 开发+自查 | 🔀条件 | 判定为复杂 Bug → 按起点进入 Feature 流程 |
| QA 补充用例 | RD Bug 修复 | 🚀自动 | 用例补充完成 |
| RD Bug 修复 | RD Bug 自查 | 🚀自动 | 修复完成 |
| RD Bug 自查 | 架构师 Bug Code Review | 🚀自动 | 自查通过 |
| 架构师 Bug Code Review | QA Bug 验证 | 🚀自动 | Review 通过（🔴 必须，无论改动大小） |
| QA Bug 验证 | PM 文档同步 | 🚀自动 | 验证通过 |
| PM 文档同步 | PMO Bug 总结 | 🚀自动 | 文档检查完成 |
| PMO Bug 总结 | Bugfix 完成 ✅ | 🚀自动 | PMO 输出 Bugfix 记录 |

> 📎 复杂 Bug 进入 Feature 流程后，后续转移遵循 Feature 流程表。

## 问题排查流程

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| 问题排查梳理 | 排查待确认 | ⏸️暂停 | 排查结论输出，等用户确认 |
| 排查待确认 | PMO 初步分析 / RD Bug 排查 / ✅ 结束 | ⏸️暂停 | 用户确认（Feature → PMO；Bug → RD；不处理 → 结束） |

## Feature Planning 流程

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| PM Roadmap 编写 | Roadmap 待确认 | ⏸️暂停 | Roadmap 初稿完成，等用户确认 |
| Roadmap 待确认 | PMO 初步分析 | ⏸️暂停 | 用户确认，逐个启动 Feature |
| 🌐 Workspace 架构讨论 | 🌐 teamwork_space.md 待确认 | ⏸️暂停 | 架构讨论完成，等用户确认 |
| 🌐 teamwork_space.md 待确认 | 🌐 子项目 Planning 中 | ⏸️暂停 | 用户确认 |
| 🌐 子项目 Planning 中 | 🌐 Workspace Planning 收尾 / 🌐 子项目 Planning 中 | 🚀自动 | 当前子项目完成（还有 → 继续；全部 → 收尾） |
| 🌐 Workspace Planning 收尾 | ✅ 完成 | ⏸️暂停 | 用户最终确认 |

## PL 模式

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| PL 引导模式 | PL 讨论模式 | ⏸️暂停 | 草案就绪，等用户审阅 |
| PL 讨论模式 | PL 结论待确认 | ⏸️暂停 | 讨论达成结论，等用户确认 |
| PL 结论待确认 | PL 执行模式 | ⏸️暂停 | 用户确认 |
| PL 执行模式 | CHG 待确认 | ⏸️暂停 | 变更评估完成，等用户确认 |
| CHG 待确认 | PM Roadmap 编写 / PMO 初步分析 | ⏸️暂停 | 用户确认 |

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

> 🟢 Micro = 省 Plan/Blueprint/UI/Review/Test Stage 的最短 RD 闭环（v7.3 引入 / v7.3.10+P0-20 统一）：代码写权仍归 RD，允许主对话内 PMO→RD 身份切换由 RD 改动（无需 Subagent / Execution Plan / dispatch），或 🔀 判定超出 Micro 白名单时升级到 Plan 模式走敏捷或 Feature。Micro 不是红线 #1 的例外，是独立流程。
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
| 用户验收 | ✅ 已完成 | ⏸️暂停 | 用户手测/目视确认通过 → PMO 完成报告（含事后审计 + 自查摘要）|

## 通用特殊状态（适用所有流程）

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| 任意阶段 | ⏳ 等待外部依赖 | 🚀自动 | PMO 判断需等待外部依赖 |
| ⏳ 等待外部依赖 | 外部依赖已就绪 | 🚀自动 | 依赖到位 |
| 外部依赖已就绪 | （暂停前的阶段） | ⏸️暂停 | 用户确认恢复 |
