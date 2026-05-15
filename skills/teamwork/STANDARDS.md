# STANDARDS · v8.0 索引

> 技术规范(不含流程规范 · 流程规范全部物化到 state.py)。
> 按技术栈拆分,按需加载。

---

## 技术规范文件

| 文件 | 内容 | 适用角色 |
|------|------|---------|
| [tdd.md](./standards/tdd.md) | 🔴 TDD 唯一权威源:Iron Law + RED-GREEN-REFACTOR + 自检清单 + 反模式 | **所有 RD + QA Code Review** |
| [common.md](./standards/common.md) | 测试核心原则、代码架构规范、RD 自查、QA 检查项、Mermaid 规范 | **所有 RD** |
| [backend.md](./standards/backend.md) | 后端集成测试、API 接口、日志规范 | **后端 RD** |
| [frontend.md](./standards/frontend.md) | 前端测试分层、E2E 测试要求 | **前端 RD** |
| [external-model-usage.md](./standards/external-model-usage.md) | 外部模型 OpenAI ToS 合规(只读评审 · 不参与代码写权) | **PMO**(外部评审调度时)|
| [scripts-policy.md](./standards/scripts-policy.md) | 脚本设计原则(退出码 / 输出格式 / 模块化)| **state.py 等工具脚本作者** |

---

## v7 → v8 standards 变化

| 范式 | 文件数 | 主要内容 |
|------|--------|---------|
| v7 | 14 文件 | 技术规范 + 流程规范(evidence-binding / output-tiers / review-verdict / review-scope / prompt-cache / stage-instantiation / discussion-mode / external-model)|
| v8 | 6 文件 | 仅技术规范(流程规范全部进 state.py) |

**已删除的流程规范文件**(已迁移到 state.py 代码层):
- `evidence-binding.md` → `_v8_engine.py` execute_stage_complete + `_v8_ship.py` 物化拦截
- `output-tiers.md` → state.py emit 时自动适配 Tier 1/2/3
- `review-verdict.md` → state.py `review-complete --verdict` enum + artifact 校验
- `review-scope.md` → state.py `_v8_stage_specs.py` 各 review 角色 spec
- `prompt-cache.md` → state.py 内部 Read 顺序固定 + state.json 访问次数控制
- `stage-instantiation.md` → state.py 各 stage `prerequisites` + `brief_template_fn`
- `discussion-mode.md` → TRIAGE.md § 2 mode E 内置(PMO 主对话行为 · 无 state.py 命令)
- `external-model.md` → state.py `_v8_init.py` detect_host + `_v8_engine.py` external review evidence

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
- [SKILL.md § PMO 软约束](./SKILL.md) + [docs/v8-redesign/00-MANIFESTO.md § 十一](./docs/v8-redesign/00-MANIFESTO.md) — 9 红线 rationale
- [tools/state.py](./tools/state.py) — 流程规范物化层
