# 文档模板索引

本目录包含 Teamwork 所有文档模板。

## 模板清单

| 文件名 | 模板类型 | 用途 | 加载时机 |
|--------|---------|------|----------|
| prd.md | PRD + PRD (技术) | 产品需求文档（标准 + 技术类变体） | Feature Planning 后 PM 编写 |
| tc.md | TC + TC-REVIEW | 测试用例文档与评审记录 | 需求评审后 QA 编写 |
| tech.md | TECH | 技术方案设计 | PRD 确认后 RD 编写 |
| ui.md | UI | UI 设计文档 | 需求明确后 Designer 设计 |
| status.md | STATUS | Feature 阶段状态追踪 | Feature 创建时初始化 |
| roadmap.md | ROADMAP | 产品执行路线图 | Feature Planning 完成时 PM 编写 |
| project.md | PROJECT | 子项目业务总览 | 项目初始化时创建 |
| architecture.md | ARCHITECTURE + database-schema | 技术架构设计 | 项目初始化时创建 |
| knowledge.md | KNOWLEDGE | 项目本地知识库 | 项目初始化时创建 |
| teamwork-space.md | teamwork_space | 多子项目全景入口 | 多子项目项目初始化时创建 |
| bug-report.md | BUG-REPORT | Bug 排查与修复报告 | Bug 流程中创建 |
| config.md | RESOURCES + .teamwork_localconfig + external/README | 项目配置与资源管理 | 项目初始化时创建 |
| dependency.md | DEPENDENCY-REQUESTS | 跨子项目依赖请求追踪 | 需要依赖时创建 |
| e2e-registry.md | E2E REGISTRY + ENVIRONMENT + REG case | E2E 回归测试中心 | Feature 完成时创建 |
| pl-pm-feedback.md | PL-FEEDBACK + PM-RESPONSE | PL-PM 讨论反馈 | Feature 讨论阶段产出 |

## 按流程查看模板

### Feature 开发全流程

1. **PRD 阶段**
   - 📄 [prd.md](./prd.md) - PM 编写产品需求

2. **PL-PM 讨论阶段**
   - 📄 [pl-pm-feedback.md](./pl-pm-feedback.md) - PL 反馈、PM 回应

3. **评审阶段**
   - 📄 [prd.md](./prd.md) - PRD 评审（含评审记录）

4. **设计阶段（有 UI 时）**
   - 📄 [ui.md](./ui.md) - UI 设计文档

5. **测试用例阶段**
   - 📄 [tc.md](./tc.md) - 测试用例编写与评审

6. **技术方案阶段**
   - 📄 [tech.md](./tech.md) - 技术方案设计

7. **状态追踪**
   - 📄 [status.md](./status.md) - Feature 阶段状态（全流程）

8. **E2E 回归**
   - 📄 [e2e-registry.md](./e2e-registry.md) - E2E 测试用例与注册

### 项目级文档

- 📄 [project.md](./project.md) - 子项目业务总览
- 📄 [architecture.md](./architecture.md) - 技术架构（含 database-schema）
- 📄 [knowledge.md](./knowledge.md) - 项目知识库
- 📄 [roadmap.md](./roadmap.md) - 产品路线图
- 📄 [teamwork-space.md](./teamwork-space.md) - 多子项目全景
- 📄 [config.md](./config.md) - 配置与资源

### Bug 流程

- 📄 [bug-report.md](./bug-report.md) - Bug 排查报告

### 跨项目协作

- 📄 [dependency.md](./dependency.md) - 跨项目依赖请求
