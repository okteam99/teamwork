# STAGES · 通用规范索引

> 各 stage spec 的**通用纪律单源**。各 `stages/*.md` 不再重复 · 1 行 cite 本文件即可。

---

## 1. 10 stage 索引

| Stage | 文件 | 适用 flow_type |
|---|---|---|
| goal | [stages/goal-stage.md](./stages/goal-stage.md) | Feature / 敏捷需求 |
| ui_design | [stages/ui-design-stage.md](./stages/ui-design-stage.md) | Feature(--needs-ui=true) |
| blueprint | [stages/blueprint-stage.md](./stages/blueprint-stage.md) | Feature |
| blueprint_lite | [stages/blueprint-lite-stage.md](./stages/blueprint-lite-stage.md) | 敏捷需求 |
| dev | [stages/dev-stage.md](./stages/dev-stage.md) | Feature / 敏捷需求 / Bug / Micro |
| review | [stages/review-stage.md](./stages/review-stage.md) | Feature / 敏捷需求 / Bug |
| test | [stages/test-stage.md](./stages/test-stage.md) | Feature / 敏捷需求 / Bug |
| browser_e2e | [stages/browser-e2e-stage.md](./stages/browser-e2e-stage.md) | Feature(execution_hints.browser_e2e_needed) |
| pm_acceptance | [stages/pm-acceptance-stage.md](./stages/pm-acceptance-stage.md) | Feature / 敏捷需求 / Bug / Micro |
| ship | [stages/ship-stage.md](./stages/ship-stage.md) | Feature / 敏捷需求 / Bug / Micro |

详细 stage 链 / 转移图见 [tools/state.py](./tools/state.py) `FLOW_BY_TYPE` · 评审角色矩阵见 [tools/_v8_engine.py](./tools/_v8_engine.py) `DEFAULT_REVIEW_ROLES`。

---

## 2. P0-11 cite 纪律(各 stage 通用 · 单源)

### 2.1 输出格式

每个 substep 动手前必在主对话输出:
```
📖 cite:
- <spec> § <段>:"<引该段 1 句关键原文 · 证明真读>"
```

### 2.2 强约束(R5 + P0-11 软约束 · 用户监督)

- 标 "—" 的 substep 无 cite 要求(状态机操作 / 用户暂停 / 已物化)
- 其余 substep **动手前必输出 cite 块** · 缺 cite 视为 process 违规(用户可叫停)
- cite 必含 § 段标题 + 至少 1 句原文(原文必真实存在于该 spec · 不可瞎编)
- AI 在 stage 内多次切角色 · 每次切换前重新 cite 该角色规范

### 2.3 为什么 cite

- brief 列路径(P0-4)只解决"AI 找不到路径"· 不保证 AI 真读
- complete 时校验太晚(AI 已做完)
- substep 动手前 cite = 事前提醒 · 强制 AI 翻一眼 spec
- 物化死角(state.py 看不到 markdown Read 动作)· 软约束 + 用户监督兜底

---

## 3. 各 stage spec 结构约定

每个 `stages/*-stage.md` **必含**:

| 段 | 内容 | 备注 |
|---|---|---|
| `## 怎么做` | substep 序列 + 关键命令 | stage 专属 |
| `## 必读 cite 清单` | 表头 4 列(Substep / 必读 spec / 段 / cite 关键点) | 表内容 stage 专属 · 表后的"输出格式 / 强约束 / 为什么"段 cite STAGES.md §2 即可 |
| `## 质量基线` | 物化拦截清单 + 短句 SOP | stage 专属 |
| `## Output Contract` | 产物字段形态 | stage 专属 |
| `## 相关` | 引擎/spec/入口规范 + stage 专属链(如 dev → tdd/common/verify-panorama) | 3-5 行 · 无需抽公共 |

---

## 4. 执行方式 · 主对话身份切换 vs subagent

- **默认**:主对话身份切换 —— PMO 切到 RD / QA / Architect 等角色(切角色 = 切 checklist + 强制重读 · 保留累积上下文)。
- **可选**:PMO 自行判断 · 可把 stage 内的**任务**(如 dev 的代码实现、test 的测试编写)dispatch 给 subagent 执行 —— 用于上下文隔离。

**边界**:
- stage 编排(`xx-start` / `xx-complete` / state.py 命令 / 暂停点)始终归 PMO 主对话 · subagent 只接「任务执行」· 不碰状态机。
- subagent 产物仍走 `state.py xx-complete` 校验 · `state.json` 单源不变 · R1 / R7 不豁免。
- 用不用 subagent 是 PMO 判断(不可枚举 · 留 AI 自决)· 不强制 · 无 dispatch 预检协议。
- architect review 默认主对话(保留架构演进的累积上下文 · 详 [roles/architect.md](./roles/architect.md))。

---

## 5. worktree 写文件纪律

🔴 worktree 模式下 · 本 Feature 所有文件读写一律在 worktree 内 · 不碰主工作区(详 [SKILL.md § worktree 纪律](./SKILL.md))。

---

## 6. 相关

- 引擎:[tools/_v8_engine.py](./tools/_v8_engine.py) `execute_stage_start` / `execute_stage_complete`
- spec 契约:[tools/_v8_stage_specs.py](./tools/_v8_stage_specs.py)
- 入口规范:[SKILL.md § Triage 入口规范](./SKILL.md) + [docs/prepare.md](./docs/prepare.md)
- 暂停点协议:[SKILL.md § PMO 软约束 + R5(b)](./SKILL.md)
