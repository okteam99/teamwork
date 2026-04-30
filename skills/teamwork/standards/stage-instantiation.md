# Stage 入口实例化通用规范（v7.3.10+P0-48 抽取）

> 🔴 **本文件是 Plan / Blueprint / Review 三 Stage 入口实例化的唯一权威源**。三 Stage spec 仅声明本 Stage 特有的角色清单 + 子步骤名称，通用流程引用本文件。

> 🟢 **抽取自**：原 goal-plan-stage.md L154-266 (113 行) + blueprint-stage.md L12-43 (30 行) + review-stage.md L89-125 (37 行)，三处合并去重 → 单一规范，杜绝漂移。

---

## 一、延迟绑定原则

triage 时上下文不足以决策评审组合（PRD/TECH/代码状态尚不充分），具体决策推迟到各 Stage 入口实例化。

- triage Step 8 给**骨架 + execution_hints（软建议）**
- Stage 入口 PMO 给**最终决策（硬规则）**：active_roles + execution + round_loop

---

## 二、Stage 入口实例化流程（4 步通用）

```
1. Read state.execution_plan_skeleton.stages[<stage>]
   ├── goal / key_outputs / pause_points  （必读）
   └── execution_hints                    （可选；存在时必读 + cite 原文）

2. PMO 基于已有信息决策（写入 state.<stage>_substeps_config）：
   ├── active_roles：实际启用的评审角色
   │   └── 默认采纳 execution_hints；调整时 cite hint + 写 hint_overrides
   │   └── active_roles ⊆ state.available_roles（triage Step 4 扫描结果）
   │
   ├── 每个角色 execution：subagent | main-conversation | external-shell
   │   └── external 角色固定 external-shell（角色契约硬约束）
   │   └── 内部角色按文件数 / 上下文累积价值决定
   │
   └── round_loop：max_rounds=3 + overflow_decision=null

3. 输出 Execution Plan（红线 #14 的 5 行核心）：
   - Approach: main-conversation 主导 + N 角色 subagent/external 并行
   - Rationale: 基于 execution_hints + Feature 复杂度信号（≥1 句具体）
   - Role specs loaded: roles/{active_roles}.md（必须真实 Read）
   - Steps remaining: <Stage 特定子步骤序列>
   - Estimated: ... min（基于 active_roles 数 / 评审循环预期）

4. PMO 自动判定通道（默认通道 / 标准通道，详见三）
```

---

## 三、默认通道 vs 标准通道（v7.3.10+P0-45 反转默认）

```
🟢 默认通道（无暂停点，PMO 直接进入子步骤 1）：
条件 ANY：
  ├── 实例化决策完全采纳 hint（无 hint_overrides）
  └── 仅轻微偏差：
      ├── 单个角色 execution 微调（main-conversation ↔ subagent，仅 1 个角色）
      ├── 角色启用条件细化（基于上游产物状态决定 Designer 是否启用）
      └── 评审循环参数细化（max_rounds 默认 3）

→ PMO cite hint 原文 + 写 hint_overrides=null（或文本说明轻微调整）
→ 阶段摘要 cite "推荐与 triage 骨架一致 / 仅微调"作为审计痕迹
→ 进入子步骤 1


🟡 标准通道（⏸️ 5 选 1 暂停点）：
触发条件 ANY（6 维度严重偏差）：
  ├── 角色组合变更：triage hint 含 X，PMO 决策跳过 X / 加未推荐的 Y
  ├── execution 方式整体反转：hybrid → 全 subagent / 全 main-conversation
  ├── 跳过整个 Stage：triage 骨架含此 Stage，PMO 决策跳过
  ├── external 角色启用反转：hint 推荐启用 / PMO 跳过（或反之）
  ├── triage 选项 2/3：用户在 triage 时已表达调整意图
  └── execution_hints == null：hint 缺失

→ 输出 5 选 1 决策（采用 / 全 Subagent / 全主对话 / 自定义 / 其他）
→ 用户回数字 → 写入 state.<stage>_substeps_config


🔴 用户主动打断（默认通道下仍可触发标准通道）：
用户输入"调整骨架" / "改 execution 方式" / "我要确认评审组合" 等
→ 立即回退到标准通道 5 选 1
```

📎 **设计意图（P0-45 反转默认）**：实战 case（INFRA-F019）暴露 Stage 入口暂停点信息量低 —— triage 骨架已是用户拍板的，execution_hints 已说明启用角色，PMO 实例化决策大多数情况轻微偏差或完全采纳。**仅严重偏差时打扰用户**，PMO 自我评估偏差严重度。

---

## 四、入口实例化硬约束

🔴 **必守规则**：
- `execution_hints` 存在 → 必读 + cite 原文 + 决策时参考；否决时必须在 `<stage>_substeps_config.hint_overrides` 写文本说明（cite hint 原文 + override 原因）
- `active_roles ⊆ state.available_roles`（triage Step 4 扫描结果）
- `external` 角色（如启用）必须满足**异质性**（`state.external_cross_review.host_main_model ≠ external 角色调用的 model`，详见 roles/external-reviewer.md）
- 实例化决策必须 cite 决策信号（不允许 PMO "凭感觉"决策）

🔴 **默认通道硬约束**：
- 必须 cite hint 原文 + 在 5 行 Execution Plan 的 Rationale 行声明"推荐与 triage 骨架一致 / 仅微调"
- 写 state.json 时 `<stage>_substeps_config.hint_overrides = null` 或文本说明轻微调整原因

---

## 五、跳过实例化 = 流程违规（v7.3.10+P0-38-B 硬规则）

进入 Plan / Blueprint / Review Stage 必须先做实例化，禁止以下反模式：

```
❌ 直接跳到 Stage 内子步骤（如直接写 PRD / 直接 dispatch QA TC）
   绕过：读 execution_hints / cite hint / 写 <stage>_substeps_config / 输出 5 行 Plan

❌ Steps remaining 仅 2-3 步（缺实例化的多角色并行评审 / PM 回应循环 / 用户最终确认）

❌ 5 行 Execution Plan 中 Role specs loaded 仅含 roles/pm.md（缺评审角色规范）
```

🔴 **PMO 校验门禁**：进入 Stage 必须先输出 5 行 Execution Plan + 写入 `<stage>_substeps_config`（含 hint_overrides）+ 默认通道无暂停 / 标准通道 ⏸️ 5 选 1；任一缺失视为流程违规，不得进入 Stage 子步骤。

📎 与红线 #14（AI Plan 模式）的关系：本"入口实例化段"产出的就是红线 #14 要求的 5 行 Execution Plan + state.<stage>_substeps_config 写入，二者合一。

---

## 六、Stage 特定子步骤参考

各 Stage 的 `Steps remaining` 内容由各 Stage spec 定义，本文件仅给通用框架：

- **Goal-Plan Stage**：见 `stages/goal-plan-stage.md` § 5 子步骤序列（PRD 起草 → PL-PM 讨论 → 联合评审 → PM 回应 → 用户最终确认）
- **Blueprint Stage**：见 `stages/blueprint-stage.md` § 4 步内部闭环（QA TC → TC 评审 → RD TECH → 架构师评审）
- **Review Stage**：见 `stages/review-stage.md` § 三视角独立审查（CR / TC 验证 / external）

---

## 七、引用约定

各 Stage spec 在入口实例化段写：

```markdown
## <Stage 名> 入口实例化

> 🔴 **遵循 [standards/stage-instantiation.md](../standards/stage-instantiation.md) 通用流程**。

本 Stage 特定参数：
- 候选 active_roles：<本 Stage 角色清单>
- key_outputs：<本 Stage 关键产出>
- 子步骤序列：<见本文件 § X 子步骤详述>

特殊例外（如有）：<例如 Review Stage 的 external 角色推荐默认启用>
```

末。
