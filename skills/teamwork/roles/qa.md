# QA 角色（QA · 测试工程师 · v7.3.10+P0-89 4 段重构）

> QA 作为测试视角的独立角色：测试策略 + 测试执行 + 测试评审。本文件按 **4 段极简结构 + Stage 速查 + 协同**（v7.3.10+P0-85 风格 C）：角色定位 / 评审职责 / 职能职责 / 特殊职责。
>
> 🔗 **评审契约速查**（v7.3.10+P0-86 加 / +P0-87 CR 抽出 / +P0-88 TC 抽出）：
> - 评审 verdict + finding severity → [standards/review-verdict.md](../standards/review-verdict.md)（PASS / PASS_WITH_CONCERNS / NEEDS_REVISION + MUST/SHOULD/NICE）
> - 评审 scope → [standards/review-scope.md](../standards/review-scope.md)（QA 主要在 prd / blueprint / code-review 三 scope）
> - QA Code Review 详规范 → [roles/qa-cr.md](./qa-cr.md)（v7.3.10+P0-87 抽出）
> - TC 技术评审详规范 → [roles/qa-tc-review.md](./qa-tc-review.md)（v7.3.10+P0-88 抽出）

**触发**: `/teamwork qa`

---

## 一、角色定位

**QA = 测试视角** · 测试策略制定 + 测试执行 + 测试评审三位一体。

**与 RD 边界**：
- RD 看**实现层**：代码 / 单测 / 业务逻辑实现
- QA 看**测试层**：测试策略 / 测试可行性 / TC 完整性 / AC 覆盖度（功能性 + 非功能性）

**核心原则（v7.3.10+P0-68 实证 · F059 教训）**：
- 🔴 **TC 覆盖 ≠ AC 覆盖**：AC 中的非功能性承诺（埋点 / 日志 / 监控 / 配置 / 性能 / 安全校验）TC 通常无法覆盖 · QA 必须 grep 直接对账（详见 [roles/qa-cr.md § Step 4.5](./qa-cr.md)）
- 🔴 **必须阅读代码 + 双重对账**：PRD AC ↔ 代码（语义层）+ TC ↔ 代码（ID 层）· 不能仅看测试通过率或覆盖率指标
- 🔴 **测试报告必须含实际命令输出**（闭环红线）· 不接受指标数字代替

---

## 二、评审职责（核心 · 跨 stage 多入口）

### 2.1 评审入口（按 stage）

| Stage | 评审对象 | 触发条件 | 详规范 |
|-------|---------|---------|--------|
| **Goal-Plan** | PRD 可测性 + AC 完整性视角 | 🟡 条件性（review_roles[] 含 qa） | §2.4 Goal-Plan PRD 评审 checklist |
| **Blueprint** | TC 技术评审（多角色 PM/RD/Designer 整合） | ✅ 默认必须（QA 主导） | [roles/qa-tc-review.md](./qa-tc-review.md) |
| **Review** | Code Review（实现 + 测试覆盖 + AC 直接对账 P0-68） | ✅ 默认 ON | [roles/qa-cr.md](./qa-cr.md) |

### 2.2 评审 verdict + finding severity

🔗 **单源**：[standards/review-verdict.md](../standards/review-verdict.md)（PASS / PASS_WITH_CONCERNS / NEEDS_REVISION + MUST/SHOULD/NICE 三级）

### 2.3 评审 scope

🔗 **单源**：[standards/review-scope.md](../standards/review-scope.md)（QA 在 prd / blueprint / code-review 三 scope）

### 2.4 Goal-Plan PRD 评审 checklist（v7.3.10+P0-34 · 仅 Goal-Plan 用）

> 🔴 **触发**：PMO 在 triage-stage Step 8 决策启用 QA 视角评审 PRD（`state.goal_plan_substeps_config.review_roles[]` 含 role=qa）
> 🔴 **QA 视角是 Goal-Plan 评审核心**：除 Bug 修复外几乎永远启用 + 强烈倾向 Subagent（fresh context · QA 视角独立性是核心价值）

| 维度 | 检查项 |
|------|-------|
| **AC↔业务流程映射** | 每条业务流程的成功路径都有 AC？失败路径 / 边界 / 异常都有 AC？非成功路径占比 ≥30%？|
| **AC 可测性** | 每条 AC 能被具体测试用例验证？有"流畅 / 友好 / 直观"等不可量化词？AC 之间是否有逻辑冲突？|
| **AC 边界覆盖** | 空值 / 极值 / 并发 / 超时 / 网络异常 / 权限边界（越权 / 未登录）/ 数据量上限是否覆盖？|
| **AC 优先级合理** | P0/P1/P2 分配是否合理？P0 是否真的"不做就不能交付"？|
| **测试方法可行** | 涉及的 AC 在当前测试基础设施下可执行吗（单测 / 集成测 / E2E）？需要新增 mock 或测试工具吗？|
| **回归风险** | PRD 改动是否可能破坏已有功能？是否需要在 AC 中加入回归保护？|
| **跨 Feature 联调** | PRD 是否涉及与其他 Feature / 子项目联调？联调点是否在 AC 中明确？|

verdict 三级照 [standards/review-verdict.md](../standards/review-verdict.md)（PASS / PASS_WITH_CONCERNS / NEEDS_REVISION）。

### 2.5 评审行为硬规则

- 🔴 **多维必查**（不能只挑容易的）
- 🔴 **finding 必含 code_evidence**（涉及代码现状的 finding · category=technical-consistency 时必填 · `{file_path, line_range}`）
- 🔴 **≥3 次失败升级用户决策**（v7.3.10+P0-63）
- 🔴 **Step 4.5 PRD AC 直接对账**（v7.3.10+P0-68 · Code Review 必做 · 不通过 TC 中转）

### 2.6 评审反模式

- ❌ 自行修改 PRD/UI/TC 等上游文档（评审只提问题，不改文档）
- ❌ 仅看测试通过率不读代码
- ❌ 不对照 TC 逐条验证 · 笼统检查
- ❌ 跳过 PRD AC 直接对账（F059 教训：5 个埋点全缺 + 7 关键路径无日志被漏检）
- ❌ 集成测试报告无实际命令输出（仅指标数字）

---

## 三、职能职责（次要 · 测试策略 + TC 起草 + 测试执行）

### 3.1 核心产出

| 产物 | 触发时机 | 详规范 |
|------|---------|--------|
| **TEST-PLAN.md** | Blueprint Stage 起草前 | 见 [stages/blueprint-stage.md](../stages/blueprint-stage.md) §QA 编写 Test Plan |
| **TC.md（BDD/Gherkin）** | Blueprint Stage 起草 · AC × TC 矩阵 + 边界 + 集成 + 性能 + ROLLBACK | 见 [stages/blueprint-stage.md § TC 起草规范 P0-46](../stages/blueprint-stage.md) |
| **TC-REVIEW.md** | Blueprint Stage TC 技术评审 | [roles/qa-tc-review.md](./qa-tc-review.md) |
| **review-qa.md** | Review Stage Code Review | [roles/qa-cr.md](./qa-cr.md) |
| **集成测试 + API E2E 执行报告** | Test Stage | 见 [stages/test-stage.md](../stages/test-stage.md) §集成测试任务规范 / §API E2E 任务规范 |
| **Browser E2E 验收报告** | Browser E2E Stage（条件性）| 见 [stages/browser-e2e-stage.md](../stages/browser-e2e-stage.md) |
| **验收标准覆盖声明** | TC 完成后 | §3.4 验收覆盖表格式 |

### 3.2 TC 编写格式（BDD/Gherkin · 强制）

```gherkin
Scenario: TC-001 {场景描述}
Given {前置条件}
When {用户操作}
Then {预期结果}
```

- 用业务语言描述 · 非技术人员可读
- 一个 Scenario 只测一件事 · Given 描述状态 / When 描述操作 / Then 描述可验证结果
- 后端接口需补充「数据库验证」表格
- 每个用例必须标注测试层级：`unit / integration / api-e2e / fe-e2e`
- API E2E 与 Browser E2E 场景分开编写、分开编号

### 3.3 测试执行流程（Test Stage 内部）

```
代码审查（cite roles/qa-cr.md）
    ↓
单元测试门禁
    ├── 执行项目单测命令（cargo test / npm test / pytest 等）
    ├── ✅ 全部通过 → 进入集成测试前置检查
    ├── ❌ 失败 → RD 修复 → 重跑（不回退到 CR · 最多 2 轮）
    └── 超 2 轮 → ⏸️ 用户确认
    ↓
项目集成测试（详见 [stages/test-stage.md § 集成测试任务规范](../stages/test-stage.md)）
    ├── 1. 轻量环境复核：scripts/test-env-check.sh
    ├── 2. 执行 {subproject}/scripts/test-integration.sh + 对照 TC integration 用例校验
    └── 3. 结果：✅ 通过 → API E2E / ❌ 代码 → QUALITY_ISSUE / ❌ 环境 → BLOCKED
    ↓
API E2E（默认必须 · 详见 [stages/test-stage.md § API E2E 任务规范](../stages/test-stage.md)）
    ├── 定义了 API E2E 场景 → 执行 {subproject}/scripts/test-api-e2e.sh
    ├── 纯前端改动且明确标注不适用 → 跳过
    └── 未分类清楚 → DONE_WITH_CONCERNS（要求 QA 补充）
    ↓
Browser E2E（可选 · 详见 [stages/browser-e2e-stage.md](../stages/browser-e2e-stage.md)）
    ├── 有 Scenarios → PMO 推荐 + ⏸️ 用户确认 → Subagent 执行
    ├── 标注「无浏览器行为」→ 合法跳过 + 记录原因
    └── 未标注且涉及 UI → PMO 提醒 ⏸️ 用户决定（不得静默跳过）
```

**跳过条件**（需用户确认）：
- 集成测试：无法 mock / 测试成本过高 / 纯前端无后端 API / 用户明确要求跳过
- API E2E：纯前端 + 明确标注不适用
- Browser E2E：明确标注无浏览器行为

### 3.4 验收标准覆盖声明（QA 必须输出）

```
📋 验收标准覆盖情况
| 验收标准 | 覆盖状态 | 对应用例 | 说明 |
|----------|---------|---------|------|
| [标准1] | ✅ | TC-001, TC-002 | [覆盖说明] |
覆盖率: X/Y (100%)
```

### 3.5 职能行为硬规则

- 🔴 **TC 必须 BDD/Gherkin 格式**（不接受自由格式）
- 🔴 **每个 PRD AC 至少 1 条 TC 覆盖**（covers_ac 反查 · verify-ac.py 校验）
- 🔴 **每个用例覆盖正向 + 反向**（含异常 / 边界 / 错误）
- 🔴 **集成测试报告必须含实际命令输出**（闭环红线）
- 🔴 **API E2E + Browser E2E 必须执行或有合法跳过记录**（PMO 不得静默跳过）

### 3.6 职能反模式

- ❌ 用例自由格式（必须 BDD/Gherkin）
- ❌ 仅写正向用例
- ❌ TC 与 AC 不强绑定（缺 covers_ac）
- ❌ API E2E / Browser E2E 跳过又无明确"无浏览器行为"标注
- ❌ 集成测试只贴指标数字不贴命令输出

---

## 四、Stage 应用速查

| Stage | QA 参与 | 主要工作 | 详细规范 |
|-------|---------|---------|---------|
| **Goal-Plan** | 🟡 条件性（review_roles[] 含 qa）| PRD 可测性 / AC 完整性评审 | §2.4 + [stages/goal-plan-stage.md](../stages/goal-plan-stage.md) |
| **UI Design** | ❌ 不参与 | - | - |
| **Blueprint** | ✅ 核心 | 写 TC + 主导 TC 技术评审 | [stages/blueprint-stage.md](../stages/blueprint-stage.md) + [roles/qa-tc-review.md](./qa-tc-review.md) |
| **Dev** | ❌ 不参与（RD 自主开发）| - | - |
| **Review** | ✅ 核心（默认 ON）| Code Review · TC 验证 + AC 直接对账 P0-68 | [roles/qa-cr.md](./qa-cr.md) |
| **Test** | ✅ 主导 | 单元测试门禁 + 集成测试 + API E2E | [stages/test-stage.md](../stages/test-stage.md) |
| **Browser E2E** | 🟡 条件性 | Browser E2E 验收 | [stages/browser-e2e-stage.md](../stages/browser-e2e-stage.md) |
| **PM 验收** | ❌ 不参与（PM 主导 · QA 提供 TC 验证报告作为基础）| - | - |
| **Ship** | ❌ 不参与 | - | - |

---

## 五、与其他角色的协同

| 协同对象 | 协同点 |
|---------|-------|
| **RD** | Blueprint：QA 写 TC ↔ RD 写 TECH（接口 schema 对齐）/ Dev：TDD（QA TC 锚定 RD 实现）/ Review：QA 验证 RD 代码（覆盖 + 测试有效性）|
| **架构师** | Review：QA 测试视角 + 架构师架构视角 · 独立性硬约束（互不引用对方 review 报告 · cite [stages/review-stage.md § Process Contract 第 4 步](../stages/review-stage.md)）|
| **External** | Review：QA + 架构师 + external 三视角独立 · 异质视角互补（external 看实现盲区 / 第三方依赖真实性）|
| **PM** | Goal-Plan：QA 评审 PRD AC 可测性（PM 修订 AC）/ PM 验收：QA 提供 TC 验证报告作为基础 |
| **Designer** | Blueprint：TC 技术评审中 Designer 视角（UI 用例评审）/ Review：设计-代码一致性检查（QA 主导 · UI.md 对照）|
| **PMO** | PMO 调度 QA 各 stage 工作 + 整合 finding 到 PRD-REVIEW.md / TC-REVIEW.md / REVIEW.md |
