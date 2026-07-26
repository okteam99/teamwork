# ROLES · v8.0 索引

> 8 角色 · 每个 ~30 行(只留 telos + 创作要点 + 协作 + rationale)。
> 角色协作流程已物化到 `tools/state.py` 各 stage `brief_template_fn` · AI 不再读 spec 凭记忆调度。

## 🔴 角色的两种用法(v8.294 · 判据)

**同一个词在起草期和评审期不是一回事** —— 用错会白付协调成本,或白丢独立性:

| | 起草期 | 评审期 |
|---|---|---|
| 角色是什么 | **分工标签**(同一个 AI 切帽子) | **独立采样点**(不同上下文 / 不同模型) |
| 能不能合并 | 🟢 **能** —— 合并省掉跨 agent 冷启动往返;拆开只在「两件事真能并行且互不依赖」时才划算 | 🔴 **不能** —— 合并 = 多视角退化成「一个视角 × N 份」 |
| 依据 | 起草的产物有机器门兜底(`verify-ac.py` / build / 测试硬门) | v8.155 实证:in-context 的 architect 在 goal 只产鼓掌 · 漏细微契约 gap · 被冷审的 external/PL 反超 |

**落地**:blueprint / dev 的 **RD 与 QA 起草期合一**(一个 agent 兼两帽 · TC 与 TECH 的收敛也归它);
评审席位照 `state.stage_review_roles` 隔离冷审,**不受此合并影响**。

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
