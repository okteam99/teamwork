# Teamwork 开发规范（索引）

> 开发规范已按技术栈拆分，请按需加载对应文件，减少上下文负担。

---

## 规范文件清单

| 文件 | 内容 | 适用角色 |
|------|------|----------|
| 📎 [common.md](./standards/common.md) | 测试核心原则、TDD 检查清单、代码架构规范、RD 自查规范、QA 代码审查检查项、文档流程图规范 | **所有 RD** |
| 📎 [backend.md](./standards/backend.md) | 后端 TDD（Red-Green-Refactor）、集成测试规范、API 接口规范、日志规范 | **后端 RD** |
| 📎 [frontend.md](./standards/frontend.md) | 前端测试分层、前端 TDD 流程、E2E 测试要求 | **前端 RD** |

---

## 加载规则

```
Subagent / RD 加载指引：
├── 后端子项目 → 加载 common.md + backend.md
├── 前端子项目 → 加载 common.md + frontend.md
└── 全栈项目   → 加载 common.md + backend.md + frontend.md
```

---

## 版本说明

- 拆分自原始单文件 STANDARDS.md
- 通用规范（架构、自查、QA 审查、Mermaid）提取到 common.md
- 后端专项（TDD、集成测试、API、日志）提取到 backend.md
- 前端专项（测试分层、TDD、E2E）提取到 frontend.md
