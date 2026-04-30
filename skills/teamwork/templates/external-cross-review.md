# 外部模型交叉评审 (External Model Cross-Review) 模板

> 🟢 v7.3.10+P0-24：本模板原名 `codex-cross-review.md`，重命名为 `external-cross-review.md`。
> "外部模型"概念 + 候选清单 + 同源约束 + 调用规范 + PMO 运行时探测的权威规范见 [standards/external-model.md](../standards/external-model.md)。
> 本模板专注：checklist、Output schema、PMO 整合流程、成本治理（与外部模型实例无关）。

> 🔴 适用：Goal-Plan Stage（PRD）/ Blueprint Stage（TC + TECH）的前置阶段交叉审查。
> 🔴 不适用：Review Stage（代码审查）已有外部模型视角，规范见 [stages/review-stage.md](../stages/review-stage.md) §Process Contract 第 4 步。
> 🔴 不适用：Test Stage / Browser E2E Stage——测试是客观可复现产出，不需要独立视角补盲区。

本模板规范 PMO 如何在"需求与方案阶段"引入**外部模型**作为第 5 视角。

外部模型选择：
- 由 PMO 在初步分析阶段调用 `templates/detect-external-model.py` 探测可用候选，按用户选择决定
- Claude Code 主对话宿主下默认 = Codex（codex-agents/*.toml）
- Codex CLI 主对话宿主下默认 = Claude（claude-agents/）

---

## 一、为什么做这件事

同模型多角色切换（PM/PL/RD/Designer/QA/PMO）之间存在**注意力相关性**——同一个模型对同一段文本的盲区，换 checklist 也未必能看见。**异质外部模型**的训练语料与推理倾向与主对话统计独立，它的盲区与主对话模型的盲区独立分布。

定位：
- ✅ 盲区独立采样 | ✅ 早期高杠杆修错（PRD/TC/TECH 阶段修错比 Dev/Test 便宜 10-100 倍）
- ❌ 不是权威判决（advisory，PMO 必须分类 ADOPT/REJECT/DEFER）
- ❌ 不是防 AI 偷懒的工具（偷懒由 hook / 契约校验兜底）

---

## 二、适用场景

| 流程 | Goal-Plan Stage（PRD）| Blueprint Stage（TC+TECH）|
|------|-----------------|--------------------------|
| Feature | 🟡 opt-in（默认 OFF） | 🟡 opt-in（默认 OFF） |
| Feature Planning | 🟡 opt-in（默认 OFF） | N/A |
| 敏捷需求 | 🟡 opt-in（默认 OFF） | 🟡 opt-in（默认 OFF） |
| Bug / 问题排查 / Micro | 跳过 | 跳过 |

🟡 opt-in = PMO 在**初步分析**阶段询问用户后启用；决策写入 `state.external_cross_review.{enabled, model, decided_at, decided_by, note}`。

> **v7.3.9+P0-13 修订（保留）**：Feature / Feature Planning 的 Plan + Blueprint 阶段由原"🔴 强制"下调为"🟡 opt-in 默认 OFF"。
> **v7.3.10+P0-24 重构**：从 `codex_cross_review` 字段名重命名为 `external_cross_review`；外部模型实例由 PMO 运行时探测决定。
>
> 修订原因：
> - Plan/Blueprint 产物为文档（PRD / TC / TECH），内部多视角（RD/Designer/QA/PMO + 架构师）评审已覆盖质量下限
> - 外部模型的最大价值在 **Review Stage 的代码审查**（盲区独立采样 + 静态分析），此场景保持🔴强制，不受本开关影响
> - 默认 OFF 可节省 Feature 冷启 10-20 min + ~10K token；用户可按风险/规模在 PMO 初步分析时手工开启
>
> **Review Stage 外部模型代码审查不受本开关影响**（保持🔴强制，规范见 [stages/review-stage.md](../stages/review-stage.md) §Process Contract 第 4 步）。

### 2.1 PMO 初步分析决策（v7.3.10+P0-24 重构自 P0-13）

PMO 完整决策流见 [roles/pmo.md](../roles/pmo.md) §🌐 外部模型交叉评审开关决策（运行时探测 + 渲染 + 选项 6 步）。简版：

```
🌐 外部模型交叉评审决策（仅影响 Plan / Blueprint Stage；Review Stage 代码审查独立强制）
├── PMO 探测（detect-external-model.py）→ 可用候选 = [{recommendation}]
├── 默认值（v7.3.10+P0-28 三处独立）：plan_enabled=false / blueprint_enabled=false / review_enabled=true
├── 建议：{开 / 不开}
├── 理由：{例：大改动 + 跨子项目 → 建议开；小 bug 修复 + 单文件 → 建议不开}
└── 选项：
    1. 启用外部模型交叉评审（使用 {recommendation}）{💡 if 推荐开启}
    2. 关闭外部模型交叉评审 {💡 if 推荐关闭}
    3. 其他指示
```

无可用候选时直接说明跳过，不出选项。

用户选择后 PMO 写入 state.json（完整 schema 见 [standards/external-model.md](../standards/external-model.md) §五）：
```json
"external_cross_review": {
  "enabled": true | false,
  "model": "codex" | "claude" | null,
  "host_main_model": "{探测结果}",
  "host_detection_at": "{ISO 8601 UTC}",
  "available_external_clis": ["..."],
  "decided_at": "{ISO 8601 UTC}",
  "decided_by": "user",
  "note": "{用户理由 / PMO 推荐理由}",
  "reviewer_dispatches": []
}
```

---

## 三、Checklist

### 3.1 PRD 变体（用于 prd-reviewer.toml）

| ID | 维度 | 关键追问 |
|----|------|----------|
| C1 | 需求完整性 | 业务流程的未覆盖分支？用户故事里未定义的角色/状态？"待决策项"里该当下决策的事项？ |
| C2 | 验收标准可测性 | 每条 AC 能被具体测试验证吗？"流畅/友好/直观"这类不可量化词有没有？AC 之间逻辑冲突？ |
| C3 | 边界场景覆盖 | 空值/极值/并发/超时/网络异常覆盖了吗？权限边界（越权、未登录）明确吗？数据量上限定义了吗？ |
| C4 | 业务流程自洽 | 流程图每条分支都有终止？状态流转每个状态可达可退出？与既有产品功能冲突/重复？ |
| C5 | 需求-实现合理性 | 有隐含了过度复杂实现的描述吗？有无更简方案达成相同价值？埋点覆盖关键漏斗？ |
| C6 | 未明示假设 | PRD 隐含的"默认这样就行"假设有哪些？这些假设在其他项目中是否曾被证伪？ |

### 3.2 TC + TECH 变体（用于 blueprint-reviewer.toml）

| ID | 维度 | 关键追问 |
|----|------|----------|
| C1 | TC↔AC 映射完整性 | PRD 每条 AC 在 TC.md `tests[].covers_ac` 都被引用？有 AC 只 1 条测试吗？有 `covers_ac` 引用不存在的 AC 吗？ |
| C2 | TC 可执行性 | 每条 TC 前置条件明确？"做什么→期望什么"具体？需人类判断的 TC 标注了手工测试吗？ |
| C3 | 边界与失败用例 | 成功/失败/边界路径比例合理（非成功 ≥30%）？并发/超时/异常/降级场景有对应 TC？ |
| C4 | TECH 架构一致性 | TECH 是否与 ARCHITECTURE.md 既有模式一致？引入了未记录的新依赖/模式？有无隐含循环依赖？ |
| C5 | TECH 可行性与风险 | 关键技术选型有替代方案对比吗？有"看似简单但实际复杂"的工作量吗？性能/安全/可观测性显式考虑？ |
| C6 | TC↔TECH 对齐 | TECH 关键接口都有对应测试？TECH 的异常处理有对应失败路径 TC？ |

---

## 四、Output Schema（两变体共享）

输出文件名（v7.3.10+P0-24 字段化）：
- PRD 变体 → `{Feature}/external-cross-review/prd-{model}.md`
- TC+TECH 变体 → `{Feature}/external-cross-review/blueprint-{model}.md`

`{model}` 取自 `state.external_cross_review.model`（codex / claude）。

```yaml
---
perspective: external-{model}    # external-codex / external-claude
target: prd | blueprint
generated_at: "{ISO 8601 UTC，晚于被审查对象 mtime}"
files_read:
  - PRD.md           # 仅列实际读过的
  - docs/PROJECT.md
model: "codex-{version} | claude-sonnet-{version}"   # 实际使用的外部模型版本
findings:
  - id: CR-1
    checklist: C1           # 来自哪条 checklist
    severity: blocker | high | low | info
    location: "AC-3 / 第二段 / 业务流程图节点 B"
    issue: "具体问题描述（1-2 句）"
    rationale: "为什么是问题（1-2 句证据）"
    suggestion: "建议怎么改（可执行的具体方向）"
findings_summary:
  blocker: 0
  high: 0
  low: 0
  info: 0
  total: 0
---

# Body（可选，人读详情）
```

### 机器可校验条件

- `yq '.perspective' <file>` = `external-{model}` 之一（`external-codex` / `external-claude`）
- `yq '.target' <file>` 与阶段匹配
- `generated_at` 晚于被审查文件 mtime
- `files_read` 不含：`PRD-REVIEW.md` / `TC-REVIEW.md` / `TECH-REVIEW.md` / `discuss/*` / `review-arch.md` / `review-qa.md` / `pmo-internal-review.md`
- 每条 finding 七字段齐备
- `findings_summary` 计数与 `findings[]` 实际分布一致
- `model` 字段实际使用的外部模型版本，与 `state.external_cross_review.model` 一致

---

## 五、PMO 整合流程（强制顺序）

```
Step 1 - PMO 内部 review（🔴 防外包，强制前置）
    PMO 按同 checklist 自查，输出 ≥3 条 findings，暂存 pmo-internal-review.md。
    不做这一步直接 dispatch = 把思考外包 = 违反红线 R1。

Step 2 - Dispatch 外部模型（🔴 宿主无关，按 state.external_cross_review.model 执行）
    Claude Code 主对话 + model=codex: shell 启 codex CLI 子进程（fresh session，调用 codex-agents/*.toml）。
    Codex CLI 主对话 + model=claude: shell 启 claude CLI 子进程（fresh context，按 claude-agents/invoke.md 范本）。
    🔴 禁止："外部视角 = 主对话同模型自审"——必须 shell 调用异质 CLI。
    可用性检测: PMO 在初步分析时已通过 detect-external-model.py 探测过；本步直接读 state.external_cross_review.{enabled, model}。
    调用失败（exit code != 0） → 走 §六 降级（state.concerns 加 WARN + 降级单视角 review）。
    Dispatch 文件规范: 沿用现有协议，文件名 dispatch_log/{NNN}-external-{model}-review.md。

Step 3 - 独立性校验（机器检查）
    yq 校验 perspective/target；grep 校验 files_read 禁读清单；
    时间戳校验 generated_at > 被审查文件 mtime。
    任一失败 → 重跑（≤2 次）；两次失败 → 触发 §六 降级。

Step 4 - PMO 内部 review vs 外部模型 findings 对比
    PMO 在合入前必须输出对比表：
    ├── 共识（双方都提到）→ 优先处理
    ├── PMO 独有 → 保留
    ├── 外部模型独有 → 盲区信号，重点审视
    └── 都漏的（事后暴露）→ 不在本 step，仅记录到 retro

Step 5 - 分类每条外部模型 finding（🔴 不允许静默忽略）
    逐条三选一 + 写理由：
    ├── ADOPT  → 纳入 PRD-REVIEW.md / BLUEPRINT-REVIEW.md 交 PM/QA/RD 修改
    ├── REJECT → 必须写 rationale（如"与 KNOWLEDGE.md L42 约束冲突"）
    └── DEFER  → 必须写延后追踪位置（如"ROADMAP.md 技术债条目"）

Step 6 - 合入多视角评审文件
    Goal-Plan Stage: PRD-REVIEW.md 新增"外部模型评审 ({model}, 外部视角)"章节
    Blueprint Stage: TC-REVIEW.md + TECH-REVIEW.md 各新增"外部模型评审"章节

Step 7 - 更新 review-log.jsonl（一行）
    stage: "plan-external-review" | "blueprint-external-review"
    status: DONE | DONE_WITH_CONCERNS | SKIPPED | FAILED
    summary: "{model} 提 N 条，采纳 M / 拒绝 K / 延后 L"
    artifact_path: "{Feature}/external-cross-review/prd-{model}.md" 或对应 blueprint 文件
```

---

## 六、降级与异常

**降级路径**（与 standards/external-model.md §六 E3 规则一致）：

- 选定外部模型的 CLI 调用失败（exit code != 0 / 超时 / 输出为空 / 格式违规）→ state.concerns 加 WARN（含 stderr 摘要） + reviewer_dispatches[].status="failed" + 降级单视角 review，不阻塞流程
- 探测时发现无可用候选（PMO 初步分析阶段）→ 直接说明跳过外部模型评审，不出选项
- 降级执行时：在 review-log concerns 中写明降级决策理由，review-log status 标 `DONE_WITH_CONCERNS`

🔴 静默降级（不写 state.concerns）违反 RULES.md 闭环验证红线。

**两种可疑信号的特殊处理（本模板专有）**：

- **findings 全为 info 且总数 ≤1** → 二次挑战：用反事实角度重新 dispatch（"如果新人接手 PRD 最可能误解哪里"）。再次为空 → `DONE_WITH_CONCERNS` 标"疑似低召回"
- **blocker ≥5** → 不机械转给 PM 全改，⏸️ 用户决策。常见原因：外部模型误解项目约定 / PRD 系统性问题 / prompt 角度偏差

---

## 七、成本治理

| 指标 | 上限 | 超限处理 |
|------|------|---------|
| 单阶段外部模型 dispatch 次数（含重跑） | 2 | 第 3 次 ⏸️ 用户确认 |
| 单 Feature 跨阶段累计 dispatch | 5 | 超过触发 ROI 评估 |
| 单次 prompt + 输入 token | ≤15K | 超过需拆分或摘要 |
| 单次外部模型响应 token | ≤8K | 要求外部模型精简 |

### ROI 评估（每 5 个 Feature 一次）

PMO 写入 `docs/retros/external-cross-review-{YYYY-WW}.md`，核心指标：
- 本周期 dispatch 次数 / 累计耗时 / 累计 token 成本
- **采纳率**（ADOPT / 总 findings）、**拒绝后打脸率**（REJECT 但事后 bug-report 关联）
- **盲区捕获率**（外部模型独有 findings / 总 findings，越高越说明价值独特）

连续 2 周期 采纳率 <20% 或 盲区捕获率 <10% → 评估 checklist 修剪 / 降级到 opt-in / 继续保留（需写理由）。

---

## 八、红线

| # | 规则 |
|---|------|
| R1 | PMO 未输出 ≥3 条内部 review 之前，禁止 dispatch 外部模型 |
| R2 | 外部模型禁读其他视角评审草稿（files_read 机器校验） |
| R3 | 每条外部模型 finding 必须分类 ADOPT/REJECT/DEFER + 理由，禁止静默忽略 |
| R4 | 禁止无条件全盘采纳外部模型意见（= 反向外包） |
| R5 | findings 全空不视为"通过"，触发 §六 二次挑战 |
| R6 | 调用失败降级执行时必须在 review-log 标 DONE_WITH_CONCERNS + state.concerns 写 WARN |
| R7 | 🟡 v7.3.10+P0-24 重构（保留 P0-13 决策）：Feature / Feature Planning 的 Plan+Blueprint 为 opt-in 默认 OFF；用户决策写入 state.external_cross_review。Review Stage 代码审查仍🔴强制（如有可用候选），不受本开关影响 |
| R8 | Output schema 机器校验失败必须重跑，不得降级接受 |
| R9 | 🔴 v7.3.10+P0-24：选定的外部模型必须与主对话宿主**不同源**（standards/external-model.md §三 E1 约束） |

---

## 九、关联文件

| 文件 | 关联 |
|------|------|
| [standards/external-model.md](../standards/external-model.md) | 🔴 外部模型概念 + 候选清单 + 同源约束 + PMO 探测 + 调用规范的权威规范 |
| [templates/detect-external-model.py](./detect-external-model.py) | PMO 在初步分析时调用的探测脚本 |
| [stages/goal-plan-stage.md](../stages/goal-plan-stage.md) | Process Contract 已扩展为 5 视角（含外部模型） |
| [stages/blueprint-stage.md](../stages/blueprint-stage.md) | Process Contract 已新增 Step 5（外部模型交叉评审） |
| [stages/review-stage.md](../stages/review-stage.md) | 代码外部模型审查在此，不走本模板 |
| [codex-agents/prd-reviewer.toml](../codex-agents/prd-reviewer.toml) | PRD 变体 Codex CLI agent（model=codex 时使用） |
| [codex-agents/blueprint-reviewer.toml](../codex-agents/blueprint-reviewer.toml) | TC+TECH 变体 Codex CLI agent（model=codex 时使用） |
| [claude-agents/](../claude-agents/) | Claude CLI 调用规范（model=claude 时使用，v7.3.10+P0-24 新建） |
| [templates/review-log.jsonl](./review-log.jsonl) | stage 枚举已新增 plan-external-review / blueprint-external-review |

---

## 十、启用路线

```
Week 1-2: Feature 流程 / Goal-Plan Stage 启用 PRD 变体（仅一个插入点，观察 ROI）
Week 3-4: 扩展到 Blueprint Stage（TC+TECH 变体）
Week 5+:  依前 4 周数据调整 checklist / 启用矩阵 / 降级策略
         每次规则变动更新"变更记录"
```

---

## 变更记录

| 日期 | 版本 | 变更 | 作者 |
|------|------|------|------|
| {YYYY-MM-DD} | v0.1 | 首版，支持 Plan / Blueprint 两 stage 变体 | PMO |
