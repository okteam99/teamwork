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

## v7 → v8 角色变化

| 范式 | 文件数 | 总行数 | 内容 |
|------|--------|-------|------|
| v7 | 21 文件(7 主角色 + 14 sub-file)| 5252 行 | 详细 dispatch 流程 + 自查清单 + review verdict 标准 |
| v8 | 8 文件 | ~247 行 | 只留 telos + 创作要点 + 协作 + rationale |

删除的 sub-file:
- `pmo-auto-mode.md` / `pmo-cross-project.md` / `pmo-external-orchestration.md` / `pmo-pm-acceptance-ship.md` / `pmo-reporting.md` / `pmo-state-mgmt.md` / `pmo-user-input.md`(7 个 PMO sub)→ 编排逻辑进 state.py
- `architect-cr.md` / `architect-tech-review.md`(2 个)→ Code/Tech Review 流程进 state.py review-stage / blueprint-stage spec
- `qa-cr.md` / `qa-tc-review.md`(2 个)→ 同上
- `pm-prd-review.md`(1 个)→ PRD 评审 verdict 进 state.py goal_plan-complete artifact 校验
- `product-lead-change-mgmt.md`(1 个)→ 变更级联进 state.py(待 v8.x 物化)

---

## 相关

- [SKILL.md](./SKILL.md) — 命令清单 + 5 mode
- [stages/*.md](./stages/) — 各 stage 的角色协作详情
- [tools/state.py](./tools/state.py) — 编排器(替代 PMO 大部分职责)
