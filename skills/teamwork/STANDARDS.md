# Teamwork 开发规范（索引）

> 开发规范已按技术栈拆分，请按需加载对应文件，减少上下文负担。

---

## 规范文件清单

| 文件 | 内容 | 适用角色 |
|------|------|----------|
| 📎 [tdd.md](./standards/tdd.md) | 🔴 **TDD 唯一权威源**（v7.3.10+P0-63）：Iron Law + RED-GREEN-REFACTOR 5 步 + 自检清单 + 反模式 + 例外 + ≥3 次失败升级 | **所有 RD + QA Code Review** |
| 📎 [common.md](./standards/common.md) | 测试核心原则、TDD 检查快查（详见 tdd.md）、代码架构规范、RD 自查规范、QA 代码审查检查项、文档流程图规范 | **所有 RD** |
| 📎 [backend.md](./standards/backend.md) | 后端集成测试规范、API 接口规范、日志规范（TDD 通用规范见 tdd.md） | **后端 RD** |
| 📎 [frontend.md](./standards/frontend.md) | 前端测试分层、E2E 测试要求（TDD 通用规范见 tdd.md） | **前端 RD** |
| 📎 [prompt-cache.md](./standards/prompt-cache.md) | teamwork 自身 prompt 组织规范（v7.3.10+P0-23）：动态内容后置 + 入口 Read 顺序固定化 + state.json 访问 ≤5 次/Stage | **PMO**（每 Stage 入口引用） |
| 📎 [external-model.md](./standards/external-model.md) | 外部模型交叉评审规范（v7.3.10+P0-24）：候选清单 + 同源约束 + PMO 运行时探测 + 调用规范 + 失败降级 | **PMO**（初步分析时调用 detect-external-model.py） |

---

## 加载规则

```
Subagent / RD 加载指引（v7.3.10+P0-63）：
├── 后端子项目 → 加载 tdd.md + common.md + backend.md
├── 前端子项目 → 加载 tdd.md + common.md + frontend.md
└── 全栈项目   → 加载 tdd.md + common.md + backend.md + frontend.md
```

---

## 版本说明

- 拆分自原始单文件 STANDARDS.md
- 通用规范（架构、自查、QA 审查、Mermaid）提取到 common.md
- 后端专项（TDD、集成测试、API、日志）提取到 backend.md
- 前端专项（测试分层、TDD、E2E）提取到 frontend.md
