# 阶段状态转移表

> 🔴 PMO/各角色在阶段切换前，必须对照此表确认流转类型。不在表中的转移路径为非法。
> 每行的「流转」列标明：🚀自动 = 不暂停直接流转；⏸️暂停 = 等用户确认；🔀条件 = 按条件决定。
> 此文件为阶段转移的权威定义，Pre-flight Check 必须查此表。

## Feature 流程

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| PMO 初步分析 | PM 编写 PRD | ⏸️暂停 | 用户确认流程类型+方案后切换 |
| PM 编写 PRD | PL-PM Teams 讨论 | 🚀自动 | PRD 初稿完成 |
| PL-PM Teams 讨论 | PRD 评审 | 🔀条件 | 共识 → 🚀自动；分歧 → ⏸️用户决策 |
| PRD 评审 | PRD 待确认 | ⏸️暂停 | 评审 Subagent 完成，等用户确认 |
| PRD 待确认 | Designer 设计 / QA Test Plan | ⏸️暂停 | 用户确认（有 UI → Designer；无 UI → QA） |
| Designer 设计 | UI 待确认 | ⏸️暂停 | 设计 Subagent 完成，等用户确认 |
| UI 待确认 | QA Test Plan | ⏸️暂停 | 用户确认 |
| QA Test Plan | QA Write Cases | 🚀自动 | Plan 完成 |
| QA Write Cases | TC 评审 | 🚀自动 | 三类 Case 完成（BDD + API E2E + Browser E2E） |
| TC 评审 | RD 技术方案 | 🔀条件 | 无阻塞项 → 🚀自动；有阻塞项 → ⏸️用户确认处理方式 |
| RD 技术方案 | 架构师 Review | 🚀自动 | 技术方案完成 |
| 架构师 Review | 技术方案待确认 | ⏸️暂停 | Review Subagent 完成，等用户确认 |
| 技术方案待确认 | RD 实现计划 | ⏸️暂停 | 用户确认 |
| RD 实现计划 | 🔗 Dev Chain | 🚀自动 | 实现计划完成 |
| 🔗 Dev Chain | UI 还原验收 / Codex Review | 🚀自动 | DONE（有 UI → UI 验收；无 UI → Codex Review） |
| 🔗 Dev Chain | ⏸️ 用户决策 | ⏸️暂停 | QUALITY_ISSUE / FAILED（内部≤3 轮修复未解决） |
| UI 还原验收 | Codex Review | ⏸️暂停 | 用户确认通过 |
| UI 还原验收 | 🔗 Dev Chain (RD Fix) | 🔁回退 | 有问题 → RD 修复 |
| Codex Review | 🔗 Verify Chain | 🚀自动 | DONE / DONE_WITH_CONCERNS |
| Codex Review | RD Fix → 重跑 Codex Review | 🔁回退 | NEEDS_FIX（三方修复流程，≤3 轮） |
| Codex Review | ⏸️ 用户决策 | ⏸️暂停 | FAILED（Codex CLI 不可用） / 超 3 轮未收敛 |
| 🔗 Verify Chain | QA Browser E2E / QA Lead 质量总结 | 🚀自动 | DONE（有 Browser E2E → ⏸️ 用户确认；无 → QA Lead） |
| 🔗 Verify Chain | RD Fix → 重新 Verify Chain | 🔁回退 | QUALITY_ISSUE → RD 修复后重跑（≤3 轮 Verify-Fix 循环） |
| 🔗 Verify Chain | ⏸️ 用户处理 | ⏸️暂停 | BLOCKED（环境问题） |
| QA Browser E2E | QA Lead 质量总结 | 🚀自动 | 通过 |
| QA Browser E2E | RD Fix → 重新 Browser E2E | 🔁回退 | 功能缺陷（≤3 轮） |
| QA Lead 质量总结 | PM 验收 | 🚀自动 | 通过（无阻塞项或仅有建议） |
| QA Lead 质量总结 | RD 开发+自查 | 🔁回退 | 有阻塞项 → RD 补充测试（≤2 轮） |
| PM 验收 | ✅ 已完成 | 🚀自动 | 验收通过 + PMO 完成报告 |

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

> 🔴 敏捷需求 = Feature 子集。除精简 PRD 外，所有阶段复用 Feature 定义。砍掉 7 个环节：PL-PM 讨论、PRD 评审、Designer、TC 评审、技术方案、架构师方案 Review、QA Lead。

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| PMO 分析 | 精简 PRD 编写 | ⏸️暂停 | 用户确认走敏捷需求流程 |
| 精简 PRD 编写 | QA Test Plan | 🚀自动 | PRD 完成 |
| QA Test Plan | QA Write Cases | 🚀自动 | Plan 完成 |
| QA Write Cases | RD 实现计划 | 🚀自动 | 三类 Case 完成（🔴 敏捷砍掉 TC 评审，直接流转 RD） |
| RD 实现计划 | 🔗 Dev Chain | 🚀自动 | 实现计划完成 |
| 🔗 Dev Chain | Codex Review | 🚀自动 | DONE |
| Codex Review | 🔗 Verify Chain | 🚀自动 | DONE（🔴 敏捷砍掉 QA Lead，其余与 Feature 一致） |
| _后续 QA → PM 验收阶段复用 Feature 流程转移表_ | | | |

## Micro 流程

> 🔴 Micro = 零逻辑变更专用通道。PMO 禁止自己改代码，必须启 RD Subagent。

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| PMO 分析 | Micro 变更说明 | ⏸️暂停 | 用户确认走 Micro 流程 |
| Micro 变更说明 | 🤖 RD Subagent | 🚀自动 | 变更说明完成 |
| 🤖 RD Subagent | 用户验收 | ⏸️暂停 | Subagent 返回 DONE（PMO 输出摘要后等用户验收） |
| 🤖 RD Subagent | ⏸️ 升级确认 | ⏸️暂停 | 发现需要逻辑变更 → 升级为敏捷或 Feature |
| 用户验收 | ✅ 已完成 | 🚀自动 | 用户确认通过 + PMO 完成报告 |

## 通用特殊状态（适用所有流程）

| 当前阶段 | 允许的下一阶段 | 流转 | 条件 |
|----------|---------------|------|------|
| 任意阶段 | ⏳ 等待外部依赖 | 🚀自动 | PMO 判断需等待外部依赖 |
| ⏳ 等待外部依赖 | 外部依赖已就绪 | 🚀自动 | 依赖到位 |
| 外部依赖已就绪 | （暂停前的阶段） | ⏸️暂停 | 用户确认恢复 |
