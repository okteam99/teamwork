# STANDARDS · v8.0 索引

> 技术规范(不含流程规范 · 流程规范全部物化到 state.py)。
> 按技术栈拆分,按需加载。

🔴 **全局优先级(用户主权)**:项目/子项目 `DEV-RULES.md`(强制开发规矩 · 人维护)**>** 本目录 standards 默认 —— standards 是「DEV-RULES 未规定时的缺省」· 不是凌驾项目既有约定的法律。存量项目的**对外契约**(如 API 响应结构)一致性优先:沿用存量风格 · 并**提示用户**把该约定固化进 DEV-RULES.md(AI 不代写 · [templates/dev-rules.md](./templates/dev-rules.md) 约定)。覆盖声明**唯一注册处 = DEV-RULES.md**(未声明 → 按 standards 当前默认);`KNOWLEDGE.md` 不作为规范覆盖注册处(只归项目事实/踩坑 · 既有覆盖声明应迁入 DEV-RULES)。

---

## 技术规范文件

| 文件 | 内容 | 适用角色 |
|------|------|---------|
| [tdd.md](./standards/tdd.md) | 🔴 TDD 唯一权威源:Iron Law + RED-GREEN-REFACTOR + 自检清单 + 反模式 | **所有 RD + QA Code Review** |
| [common.md](./standards/common.md) | 测试核心原则、代码架构规范、RD 自查、QA 检查项、Mermaid 规范 | **所有 RD** |
| [backend.md](./standards/backend.md) | 后端集成测试、API 接口、日志规范 | **后端 RD** |
| [frontend.md](./standards/frontend.md) | 前端规范骨架:测试分层 / 组件测试 / 样式 / 状态管理 / 性能 / 无障碍 / 构建 硬规则 | **前端 RD** |
| [external-model-usage.md](./standards/external-model-usage.md) | 外部模型 OpenAI ToS 合规(只读评审 · 不参与代码写权) | **PMO**(外部评审调度时)|
| [scripts-policy.md](./standards/scripts-policy.md) | 脚本设计原则(退出码 / 输出格式 / 模块化)| **state.py 等工具脚本作者** |

---

## 加载规则

```
RD 加载指引:
├── 后端子项目 → tdd.md + common.md + backend.md
├── 前端子项目 → tdd.md + common.md + frontend.md
└── 全栈项目 → tdd.md + common.md + backend.md + frontend.md
```

---

## 相关

- [SKILL.md](./SKILL.md) — 命令清单
- [SKILL.md § PMO 软约束](./SKILL.md) + [docs/archive/v8-redesign/00-MANIFESTO.md § 十一](./docs/archive/v8-redesign/00-MANIFESTO.md) — 9 红线 rationale
- [tools/state.py](./tools/state.py) — 流程规范物化层
