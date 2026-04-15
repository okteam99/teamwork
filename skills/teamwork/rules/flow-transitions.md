# 阶段状态转移表

> 🔴 PMO 在阶段切换前，必须对照此表确认流转类型。不在表中的转移路径为非法。
> 每行的「流转」列标明：🚀自动 = 不暂停直接流转；⏸️暂停 = 等用户确认；🔀条件 = 按条件决定。
> 此文件为阶段转移的权威定义，校验行必须引用此表的行号+原文。

## Feature 流程

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| PMO 初步分析 | 🔗 Plan Stage | ⏸️暂停 | 用户确认流程类型+方案后启动 |
| 🔗 Plan Stage | PRD 待确认 | ⏸️暂停 | Plan Stage 返回定稿 PRD，等用户确认 |
| 🔗 Plan Stage (分歧) | PRD 待确认 | ⏸️暂停 | 有 PL-PM 分歧项，用户逐项决策后确认 |
| PRD 待确认 | 🔗 UI Design Stage / 🔗 Blueprint Stage | ⏸️暂停 | 用户确认（有 UI → UI Design；无 UI → Blueprint） |
| 🔗 UI Design Stage | UI 待确认 | ⏸️暂停 | 设计完成，等用户确认 |
| UI 待确认 | 🔗 UI Design Stage (修订) / 🔗 Panorama Design Stage / 🔗 Blueprint Stage | ⏸️暂停 | 有问题→重跑 Design（≤3轮）；通过+涉及全景→Panorama；通过+不涉及→Blueprint |
| 🔗 Panorama Design Stage | 全景待确认 | ⏸️暂停 | 全景更新完成，等用户确认 |
| 全景待确认 | 🔗 Blueprint Stage | ⏸️暂停 | 用户确认全景 |
| 🔗 Blueprint Stage | 方案待确认 | ⏸️暂停 | Blueprint 返回 TC + TECH.md + 评审报告 |
| 🔗 Blueprint Stage (concerns) | 方案待确认 | ⏸️暂停 | 有 concerns，用户确认处理方式 |
| 方案待确认 | 🔗 Dev Stage | ⏸️暂停 | 用户确认技术方案（📎 worktree=auto 时 PMO 在此处创建 worktree） |
| 🔗 Dev Stage | 🔗 Review Stage | 🚀自动 | DONE（单测全绿） |
| 🔗 Dev Stage | ⏸️ 用户决策 | ⏸️暂停 | FAILED（单测持续失败/环境异常） |
| 🔗 Review Stage | 🔗 Test Stage | 🚀自动 | DONE（三个 review 均通过） |
| 🔗 Review Stage (NEEDS_FIX) | RD Fix → PMO 判断重跑哪些 review | 🔁回退 | ≤3 轮修复循环 |
| 🔗 Review Stage (FAILED) | ⏸️ 用户决策 | ⏸️暂停 | Codex CLI 不可用 / 超 3 轮 |
| 🔗 Test Stage | 🔗 Browser E2E Stage / PM 验收 | 🚀自动 | DONE（有 Browser E2E → ⏸️用户确认；无→PM 验收） |
| 🔗 Test Stage (QUALITY_ISSUE) | RD Fix → 重跑 Test Stage | 🔁回退 | ≤3 轮 |
| 🔗 Test Stage (BLOCKED) | ⏸️ 用户处理 | ⏸️暂停 | 环境问题 |
| 🔗 Browser E2E Stage | PM 验收 | 🚀自动 | 通过 |
| 🔗 Browser E2E Stage | RD Fix → 重新 Browser E2E | 🔁回退 | 功能缺陷（≤3 轮） |
| PM 验收 | ✅ 已完成 | 🚀自动 | 验收通过 + PMO 完成报告（📎 worktree=auto 时 PMO 在此处清理 worktree） |

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
| PMO 分析 | 精简 PRD 编写 | ⏸️暂停 | 用户确认走敏捷需求流程 |
| 精简 PRD 编写 | PRD 待确认 | ⏸️暂停 | PRD 完成，等用户确认 |
| PRD 待确认 | 🔗 BlueprintLite Stage | ⏸️暂停 | 用户确认 PRD |
| 🔗 BlueprintLite Stage | 🔗 Dev Stage | 🚀自动 | DONE（简化 TC + 实现计划就绪） |
| 🔗 Dev Stage | 🔗 Review Stage | 🚀自动 | DONE（与 Feature 一致） |
| 🔗 Review Stage | 🔗 Test Stage | 🚀自动 | DONE（与 Feature 一致） |
| _后续 Test Stage → Browser E2E → PM 验收复用 Feature 流程转移表_ | | | |

## Micro 流程

> 🔴 Micro = 零逻辑变更专用通道。PMO 禁止自己改代码，必须启 RD Subagent。

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| PMO 分析 | Micro 变更说明 | ⏸️暂停 | 用户确认走 Micro 流程 |
| Micro 变更说明 | 🤖 RD Subagent | 🚀自动 | 变更说明完成 |
| 🤖 RD Subagent | 用户验收 | ⏸️暂停 | Subagent 返回 DONE |
| 🤖 RD Subagent | ⏸️ 升级确认 | ⏸️暂停 | 发现需要逻辑变更 → 升级为敏捷或 Feature |
| 用户验收 | ✅ 已完成 | 🚀自动 | 用户确认通过 + PMO 完成报告 |

## 通用特殊状态（适用所有流程）

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| 任意阶段 | ⏳ 等待外部依赖 | 🚀自动 | PMO 判断需等待外部依赖 |
| ⏳ 等待外部依赖 | 外部依赖已就绪 | 🚀自动 | 依赖到位 |
| 外部依赖已就绪 | （暂停前的阶段） | ⏸️暂停 | 用户确认恢复 |
