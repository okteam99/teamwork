# Teamwork 角色定义

> 各角色的完整定义（职责、输出格式、工作规范）拆分到 roles/ 目录，按需加载。
> PMO dispatch 角色时只需读取对应文件，不用加载全部角色定义。

## 角色索引

| 角色 | 文件 | 职责概要 |
|------|------|----------|
| PMO | [roles/pmo.md](./roles/pmo.md) | 项目管理：承接需求、判断流程、调度角色、流转校验、输出摘要和完成报告 |
| Product Lead | [roles/product-lead.md](./roles/product-lead.md) | 产品方向：业务架构、执行规划、变更影响评估（引导/讨论/执行 3 种模式 · 4 段重构 v7.3.10+P0-92 · 变更管理详规范 → [roles/product-lead-change-mgmt.md](./roles/product-lead-change-mgmt.md)）|
| PM | [roles/pm.md](./roles/pm.md) | 产品管理：需求澄清、PRD 编写、Feature Planning、Roadmap、PM 验收（4 段重构 v7.3.10+P0-91 · PRD 多角色评审详规范 → [roles/pm-prd-review.md](./roles/pm-prd-review.md)）|
| Designer | [roles/designer.md](./roles/designer.md) | UI/UX 设计：用户流程、布局、HTML 预览、全景设计维护、UI 还原验收（4 段重构 v7.3.10+P0-92）|
| QA | [roles/qa.md](./roles/qa.md) | 测试：Test Plan、BDD 用例、单元/集成测试、API E2E、Browser E2E（CR 详规范 → [roles/qa-cr.md](./roles/qa-cr.md) · TC 技术评审 → [roles/qa-tc-review.md](./roles/qa-tc-review.md)，v7.3.10+P0-87/P0-88 抽出）|
| 架构师 | [roles/architect.md](./roles/architect.md) | 架构层评审：架构合理性、模块设计、ADR 决策、ARCHITECTURE.md 维护（CR 详规范 → [roles/architect-cr.md](./roles/architect-cr.md) · Tech Review 详规范 → [roles/architect-tech-review.md](./roles/architect-tech-review.md)，v7.3.10+P0-86/P0-87/P0-90 独立 + 抽出）|
| RD | [roles/rd.md](./roles/rd.md) | 实现层开发：技术方案、TDD 开发、自查、Bug 排查（4 段重构 v7.3.10+P0-90 · 架构师方案评审段已迁出到 architect-tech-review.md）|

## 状态行格式

> 📎 状态行格式定义已迁移到 [STATUS-LINE.md](./STATUS-LINE.md)。
