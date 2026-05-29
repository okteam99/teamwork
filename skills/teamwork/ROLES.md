# ROLES · v8.0 索引

> 8 角色 · 每个 ~30 行(只留 telos + 创作要点 + 协作 + rationale)。
> 角色协作流程已物化到 `tools/state.py` 各 stage `brief_template_fn` · AI 不再读 spec 凭记忆调度。

---

## 8 角色

| 角色 | 文件 | 职责视角 |
|------|------|---------|
| **PMO** | [roles/pmo.md](./roles/pmo.md) | 编排器(实际是 state.py)· 主对话身份切换时参考 |
| **PM** | [roles/pm.md](./roles/pm.md) | 需求完整性 · PRD 起草 · 验收 |
| **QA** | [roles/qa.md](./roles/qa.md) | 测试覆盖 · TC 起草 · 边界场景 |
| **RD** | [roles/rd.md](./roles/rd.md) | 实现质量 · TDD · 唯一代码写权 |
| **Architect** | [roles/architect.md](./roles/architect.md) | 技术合理性 · Tech Review · Code Review |
| **Designer** | [roles/designer.md](./roles/designer.md) | UX 视角 · UI.md + HTML 预览 |
| **PL** | [roles/product-lead.md](./roles/product-lead.md) | 产品方向 · ROADMAP · 变更级联 |
| **External Reviewer** | [roles/external-reviewer.md](./roles/external-reviewer.md) | 异质模型 cross-review |

---

## 相关

- [SKILL.md](./SKILL.md) — 命令清单 + 5 mode
- [stages/*.md](./stages/) — 各 stage 的角色协作详情
- [tools/state.py](./tools/state.py) — 编排器(替代 PMO 大部分职责)
