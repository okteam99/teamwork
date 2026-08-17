# STAGES · 通用规范索引

> 各 stage spec 的**通用纪律单源**。各 `stages/*.md` 不再重复 · 1 行 cite 本文件即可。

---

## 1. Stage 索引(数量单源 `STAGE_SPECS` · 不写死数字 —— 与 [tools/_v8_stage_specs.py](./tools/_v8_stage_specs.py) 对齐)

| Stage | 文件 | 适用 flow_type |
|---|---|---|
| goal | [stages/goal-stage.md](./stages/goal-stage.md) | Feature |
| ui_design | [stages/ui-design-stage.md](./stages/ui-design-stage.md) | Feature(--needs-ui=true) |
| blueprint | [stages/blueprint-stage.md](./stages/blueprint-stage.md) | Feature |
| diagnose | [stages/diagnose-stage.md](./stages/diagnose-stage.md) | Bug(流首 stage · 根因细查+修复方案 · 用户确认后进 dev) |
| dev | [stages/dev-stage.md](./stages/dev-stage.md) | Feature(full)/ Bug |
| execute | [stages/execute-stage.md](./stages/execute-stage.md) | Feature(preset=micro · 零门禁自由执行 → ship) |
| review | [stages/review-stage.md](./stages/review-stage.md) | Feature / Bug |
| test | [stages/test-stage.md](./stages/test-stage.md) | Feature / Bug |
| browser_e2e | [stages/browser-e2e-stage.md](./stages/browser-e2e-stage.md) | Feature(execution_hints.browser_e2e_needed) |
| pm_acceptance | [stages/pm-acceptance-stage.md](./stages/pm-acceptance-stage.md) | Feature(full/micro)/ Bug |
| ship | [stages/ship-stage.md](./stages/ship-stage.md) | Feature(full/micro)/ Bug |

详细 stage 链 / 转移图见 [tools/state.py](./tools/state.py) `FLOW_BY_TYPE` · 评审角色矩阵见 [tools/_v8_engine.py](./tools/_v8_engine.py) `DEFAULT_REVIEW_ROLES`。

---

## 3. 各 stage spec 结构约定(🧭 四段结构 · 现行标准)

> 📌 **例外**:`ship-stage.md` 主体是**命令序列 + 物化门禁**(非「怎么思考」),保留 §1-§6 操作顺序叙事 —— 四段结构治的是 HOW-to 教程,不是必要的操作次序。

每个 `stages/*-stage.md` **必含**:

| 段 | 内容 | 备注 |
|---|---|---|
| `## ① 目标(telos)` | 这个 stage 要达成什么 + **拦的是什么风险** | 一段话 · 不写步骤 |
| `## ② 硬规则(白名单 · 每条一行 why)` | **只装违反了会出真实事故的**(见下判据)· 每条 ≤2 行 + why 指向**具体失效模式** | 🔴 白名单 = 不在此列的都不是硬规则 |
| `## ③ 建议手段菜单(AI 自选 · 不强制)` | 表格:手段 × **何时值得**(给判断准则 · 不给操作步骤) | 可省(HOW 空间小的 stage) |
| `## ④ Output Contract` | 产物字段形态 + complete 命令字面 | 机器语法只出现在这里 |
| `## 相关` | 引擎/spec/入口规范 + stage 专属链 | 3-5 行 |

🔴 **② 硬规则的保留判据**(原则):**治结构风险,不教干活**——
① **证据/验证**(机器可验的证据要求:test exit-code / artifact 在 commit / coverage 申报)· ② **独立采样**(冷审隔离 / 不喂起草心路 / 模型错开)· ③ **用户主权**(暂停点 / 必须用户拍板的决策)· ④ **纯机械操作**(worktree 路径 / 命令参数 / 文件约定)。
**不该进②的**:怎么调研 / 怎么拆任务 / 怎么写代码(→ ③菜单或交还模型)· 通用工程规范(→ `standards/` + 项目 `DEV-RULES.md`)· 教模型它本来就会的。

🔴 **不设「怎么做」步骤清单,也不设末尾「质量基线」复检段**(删):
- 「怎么做」= HOW-to 教程 —— **把强模型的地板变天花板**(原话)· 目标 + 契约给足,步骤模型自推;
- 「质量基线」= 把②的规则再复述一遍 —— 实测未迁移文件因此把同一条规则讲 2-3 遍(test/panorama_sync/pm_acceptance/diagnose 均命中)。**同一件事:叙事在②只写一次 · 机器语法在④只写一次 · 没有第三处**;
- 物化拦截清单归 ④ Output Contract(它本就是产物/门禁形态)。

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
