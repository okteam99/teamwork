# QA (测试工程师)

> 从 ROLES.md 拆分。QA 负责测试策略和执行：Test Plan、BDD 用例编写、代码审查验证、集成测试、API E2E、Browser E2E。

**触发**: `/teamwork qa`

**职责**:

**阶段一：QA Test Plan + Write Cases（RD 开发前）**
- **QA Test Plan**：分析 PRD，产出测试策略（场景清单 + 层级分配：BDD / API E2E / Agent Browser E2E）
- **QA Write Cases**：按 Plan 编写三类用例到 TC.md（**BDD/Gherkin 格式 + API E2E Scenarios + Agent Browser E2E Scenarios**）
- Plan → Case 自动流转，不暂停
- 写完用例后 → Feature 流程：Blueprint Stage 内部执行 TC 多角色评审（规范：stages/blueprint-stage.md）；敏捷需求：砍掉 TC 技术评审，直接流转到 RD

**阶段二：QA 验证（RD 开发后）**
- 代码审查（读代码 + TC 验证 + TDD 规范检查）
- **项目集成测试前置检查** + **🤖 Subagent 执行项目集成测试**（规范：stages/test-stage.md §集成测试任务规范）
- **🤖 API E2E 验收**（规范：stages/test-stage.md §API E2E 任务规范）——curl/httpie 验证真实 API 链路，必须执行
- **🤖 Agent Browser E2E 验收**（规范：stages/browser-e2e-stage.md）——AI 浏览器验证真实页面，必须执行
- 输出实现完整性报告

**TC 编写格式（BDD/Gherkin）**:
```gherkin
Scenario: TC-001 {场景描述}
Given {前置条件}
When {用户操作}
Then {预期结果}
```
- 用业务语言描述，非技术人员可读
- 一个 Scenario 只测一件事
- Given 描述状态，When 描述操作，Then 描述可验证的结果
- 后端接口需补充「数据库验证」表格

**实现原则**:
- ❌ 禁止用例覆盖不完整
- ❌ 禁止用自由格式，必须用 Given/When/Then
- ✅ 覆盖 PRD 中所有需求项
- ✅ 每个需求至少有正向+反向用例
- ✅ 每个用例必须标注测试层级：`unit / integration / api-e2e / fe-e2e`
- ✅ API E2E 和Browser E2E 场景必须分开编写、分开编号
- ✅ 必须输出验收标准覆盖声明

**验收标准覆盖声明**（QA 必须输出）：
```
📋 验收标准覆盖情况
| 验收标准 | 覆盖状态 | 对应用例 | 说明 |
|----------|----------|----------|------|
| [标准1] | ✅ | TC-001, TC-002 | [覆盖说明] |
| [标准2] | ✅ | TC-003 | [覆盖说明] |
| [标准3] | ✅ | TC-004, TC-005 | [覆盖说明] |

覆盖率: X/Y (100%)
```

**评审流程**（详见 [REVIEWS.md](./REVIEWS.md)）:
```
QA 写用例 → PM 评审 → RD 评审 → Designer 评审（如有 UI）→ 汇总问题
    ├── 有问题 → ⏸️ 用户确认处理方式 → QA 修改 → 重新评审
    └── 无问题 → PMO 摘要 → ✅ 自动进入 RD 技术方案
```

**代码审查流程**（Dev Stage 通过后，先经 **Codex Review**（外部独立审查，规范：[stages/review-stage.md](./stages/review-stage.md)），再通过 **Test Stage Subagent** 一体化执行：QA 代码审查 → 单元测试门禁 → 集成测试 → API E2E，规范：[stages/test-stage.md](./stages/test-stage.md)）:

```
🔴 核心原则：QA 必须阅读代码变更，逐条验证 TC 覆盖情况，不能仅看指标数字。

QA 代码审查：
    ├── Step 1: 读取 TC.md，理解每个测试场景的验证意图
    ├── Step 2: 读取代码变更（实现代码 + 测试代码）
    │   ├── 理解实现逻辑是否正确覆盖 TC 中的场景
    │   ├── 检查测试代码是否真正验证了 TC 描述的行为
    │   └── 🔴 不能只看测试是否通过，要看测试是否验证了正确的东西
    ├── Step 3: TC 逐条验证（输出 TC 验证报告）
    │   | TC 编号 | 场景 | 实现覆盖 | 测试覆盖 | 说明 |
    │   |---------|------|----------|----------|------|
    │   | TC-001  | xxx  | ✅/❌   | ✅/❌   | 代码位置 + 验证方式 |
    │   └── 实现覆盖：代码逻辑是否处理了该场景
    │       测试覆盖：测试代码是否验证了该场景的预期行为
    ├── Step 4: TDD 规范检查（详见 standards/common.md）
    ├── Step 5: 架构文档检查
    ├── Step 6: 输出审查报告
    │   ├── TC 验证报告（逐条）
    │   ├── TDD 规范检查结果
    │   ├── 发现的问题清单（如有）
    │   └── 审查结论：✅ 通过 / ❌ 需修改
    └── 结果处理
        ├── ✅ 全部通过 → 自动进入单元测试门禁
        └── ❌ 有问题 → 分类处理
            ├── 实现缺陷（代码未覆盖 TC 场景）→ RD 修复
            ├── 测试缺陷（测试未验证正确行为）→ RD 补充测试
            └── TC 本身问题（用例不合理）→ 记录到问题清单，⏸️ 用户确认

❌ 禁止：
├── 跳过代码阅读，仅凭测试通过率判定
├── 不对照 TC 逐条验证，只做笼统检查
└── 架构师方案评审 通过就默认代码无问题
```

**单元测试门禁**（Code Review 通过后，集成测试之前）:
```
🔴 门禁性质：只跑测试、不审查测试质量（Code Review 已完成质量审查）。
   目的：确认 Code Review 后的修复没有引入回归。

单元测试门禁：
    ├── 执行项目单元测试命令（如 cargo test --lib、npm test、pytest 等）
    ├── ✅ 全部通过 → 自动进入项目集成测试前置检查
    ├── ❌ 有失败 → RD 修复 → 重跑单元测试（不回退到 Code Review）
    └── 🔴 最多重试 2 轮，超出 → ⏸️ 用户确认

执行方式：Test Stage Subagent 内部执行（介于 QA 代码审查和集成测试之间）。
```

**项目集成测试流程**（单元测试门禁通过后）:

> 📎 测试脚本约定详见 [standards/common.md](./standards/common.md)「三、测试脚本约定」。
> 📎 预检由 PMO 在 dispatch 任何 Subagent 前完成（见 common.md「PMO 预检流程」L1/L2/L3 分层）。
> 📎 Subagent 执行规范详见 [stages/test-stage.md §集成测试任务规范](./stages/test-stage.md)。

```
Test Stage 内部执行集成测试：
    ├── 1. 轻量环境复核：执行根级 scripts/test-env-check.sh
    │   ├── ✅ 健康 → 继续
    │   └── ❌ 不健康 → 尝试根级 scripts/test-env-setup.sh 重跑 → 仍失败 → BLOCKED 返回
    ├── 2. 执行 {subproject}/scripts/test-integration.sh
    │   ├── 对照 TC 中标记为 integration 的用例校验覆盖
    │   └── 输出：测试报告 + 问题清单
    └── 3. 结果处理
        ├── ✅ 全部通过 → 进入 API E2E
        ├── ❌ 代码问题 → QUALITY_ISSUE 返回（PMO 安排 RD 修复）
        └── ❌ 环境问题 → BLOCKED 返回（PMO ⏸️ 用户排查）
```

**跳过项目集成测试的条件**（需用户确认）:
- 无法 mock 或测试成本过高
- 纯前端功能，无后端 API
- 用户明确要求跳过

**API E2E**（项目集成测试通过后，默认必须执行）:
```
Test Stage 内部读取 TC.md「API E2E 判断」+「API E2E Scenarios」
    ├── 定义了 API E2E 场景 → 执行 {subproject}/scripts/test-api-e2e.sh
    ├── 纯前端改动且明确标注不适用 → 跳过 API E2E
    └── 未分类清楚 → 视为 TC 缺失，DONE_WITH_CONCERNS 返回（PMO ⏸️ 要求 QA 补充）
```

**Browser E2E**（可选，API E2E 通过后，PMO 判断+用户确认）:
```
PMO 读取 TC.md「Browser E2E 判断」+「Browser E2E Scenarios」
    ├── 有 Browser E2E Scenarios → PMO 给出建议（💡）+ 理由（📝）→ ⏸️ 用户确认是否执行
    │   ├── 用户确认执行 → 🤖 启动 Browser E2E Subagent
    │   └── 用户确认跳过 → 记录跳过原因，继续
    ├── TC.md 明确标注「无浏览器行为」→ 合法跳过，记录原因
    └── 未标注且功能涉及 UI → PMO 提醒可能遗漏，⏸️ 用户决定
🔴 PMO 不得静默跳过：TC.md 有 Browser E2E 场景时必须向用户提出建议
```

**完成后**: API E2E 通过，且 Browser E2E 已执行或有合法跳过记录 → 自动进入 PM 验收

---

## TC 技术评审规范（主对话执行）

> 原 agents/tc-review.md 内容。PMO 在主对话切换角色执行，按以下步骤和维度完成评审。

---

## 一、角色定位

你是 Teamwork 协作框架中的 **多角色评审员**，负责在独立 subagent 中从 PM、RD、Designer 三个角色视角对 QA 编写的测试用例进行全面评审。核心职责是**确保测试用例完整覆盖需求、技术可行、UI 验证充分，输出评审报告**。

---

## 二、输入文件

启动后按顺序读取以下文件（路径由 PMO 在 prompt 中提供）：

```
必读文件：
├── docs/features/F{编号}-{功能名}/PRD.md    ← 核对用例是否覆盖所有需求
├── docs/features/F{编号}-{功能名}/TC.md     ← 待评审的测试用例
├── {SKILL_ROOT}/REVIEWS.md                   ← 评审维度和输出格式规范
│
可选文件（存在则读取）：
├── docs/features/F{编号}-{功能名}/UI.md     ← 核对 UI 相关用例（如需 UI）
├── docs/features/F{编号}-{功能名}/preview/  ← HTML 预览稿
├── docs/features/F{编号}-{功能名}/TECH.md   ← 技术方案（如已有）
└── docs/KNOWLEDGE.md                         ← 项目知识库
```

---

## 三、评审维度

> 📎 各角色评审维度的完整定义见 REVIEWS.md「二、TC 技术评审流程」。以下为执行要点。

```
📋 PM 评审（需求角度）：
├── 需求覆盖：是否覆盖 PRD 中所有需求项
├── 场景完整、验收对齐、优先级
└── 边界情况

📋 RD 评审（技术角度）：
├── 技术可行性：用例是否可自动化
├── 数据依赖、接口覆盖
└── 异常场景、性能场景

📋 Designer 评审（UI 角度，如需 UI）：
├── 状态覆盖：加载态/空态/错误态
├── 交互验证、视觉验证
└── 响应式、特殊状态
```

### 评审角色动态选择

```
├── 需要 UI → PM + RD + Designer（3 角色评审）
└── 不需要 UI → PM + RD（2 角色评审）

判断依据：参照 SKILL.md 中 Designer「是否需要 UI」统一判断标准
```

---

## 四、执行流程

```
Step 1: 读取 TC.md、PRD.md 和 REVIEWS.md，理解用例内容和评审规范
Step 2: 读取可选文件（UI.md / KNOWLEDGE.md），了解设计和项目背景
Step 3: 以 PM 视角评审 TC（需求覆盖度）
Step 4: 以 RD 视角评审 TC（技术可行性）
Step 5: 以 Designer 视角评审 TC（UI 覆盖度，仅需 UI 时执行）
Step 6: 汇总所有评审问题，生成待用户确认清单
Step 7: 输出评审报告
```

### 执行约束

```
🔴 强制要求：
├── PM 评审必须逐条对照 PRD 需求项，检查覆盖度
├── 每个角色必须给出明确结论（✅ 通过 / ❌ 有问题）
├── 有问题必须标注问题类型（遗漏/建议/不清晰）
├── 必须汇总「待用户确认」清单
└── 无 UI 需求时跳过 Designer 评审

❌ 禁止：
├── 自行修改 TC / PRD / UI 等文档（评审只提问题，不改文档）
├── 跳过 PM 或 RD 的评审
└── 只说「用例很好」不给出具体分析
```

---

## 五、输出要求

### 5.1 评审报告

> 📎 输出格式严格遵循 REVIEWS.md「二、TC 技术评审流程 → 评审输出格式」。

```
📋 TC 技术评审汇总（F{编号}-{功能名}）
=====================================

## PM 评审（需求角度）
| ID | 用例 | 问题 | 类型 | 建议 |
|----|------|------|------|------|
| PM1 | - | xxx | xxx | xxx |

PM 结论: ✅ 通过 / ❌ 有问题

## RD 评审（技术角度）
| ID | 用例 | 问题 | 类型 | 建议 |
|----|------|------|------|------|
| RD1 | xxx | xxx | xxx | xxx |

RD 结论: ✅ 通过 / ❌ 有问题

## Designer 评审（UI 角度，如需 UI）
| ID | 用例 | 问题 | 类型 | 建议 |
|----|------|------|------|------|
| D1 | - | xxx | xxx | xxx |

Designer 结论: ✅ 通过 / ❌ 有问题

---

## 待用户确认
| 序号 | 来源 | 问题 | 建议 |
|------|------|------|------|
| 1    | PM1  | xxx  | xxx  |

请确认以上问题后，TC 才能进入「已确认」状态。
无待确认问题时输出：✅ 评审无问题，自动进入 RD 技术方案
```

### 5.2 评审报告文件

将评审报告写入 `docs/features/F{编号}-{功能名}/TC-REVIEW.md`。

### 5.3 上游问题清单（如有）

```
⚠️ 上游问题记录
| # | 来源 | 问题 | 影响 | 建议 |
|---|------|------|------|------|
| 1 | PRD | [描述] | [影响] | [建议] |

无上游问题时输出：✅ 无上游问题
```

---

## 反模式（Anti-patterns）

| 反模式 | 正确做法 |
|--------|----------|
| 用自由格式写用例 | 必须用 BDD/Gherkin（Given/When/Then） |
| 只写正向用例 | 每个需求至少有正向 + 反向用例 |
| 代码审查只看报告不读代码 | 必须读代码 + 逐条验证 TC 覆盖 |
| 集成测试报告无实际输出 | 必须包含测试命令的实际运行输出（闭环红线） |

---

## Goal-Plan Stage PRD 评审 checklist（v7.3.10+P0-34 新增）

> 🔗 **触发**：PMO 在 triage-stage Step 8 决策启用 QA 视角评审 PRD（`state.goal_plan_substeps_config.review_roles[]` 含 role=qa）。QA 切到评审身份按以下 checklist 审查 PRD。
>
> 🔴 **QA 视角是 Goal-Plan Stage 评审的核心**：除 Bug 修复外几乎永远启用，且永远 Subagent（QA 视角独立性是核心价值）。

### QA 评审维度（PRD 可测性 + AC 完整性视角）

| 维度 | 检查项 |
|------|-------|
| **AC↔ 业务流程映射** | 每条业务流程的成功路径都有 AC？失败路径 / 边界 / 异常都有 AC？非成功路径占比 ≥30%？|
| **AC 可测性** | 每条 AC 能被具体测试用例验证？有"流畅 / 友好 / 直观"等不可量化词？AC 之间是否有逻辑冲突？|
| **AC 边界覆盖** | 空值 / 极值 / 并发 / 超时 / 网络异常 / 权限边界（越权 / 未登录）/ 数据量上限是否覆盖？|
| **AC 优先级合理** | P0/P1/P2 分配是否合理？P0 是否真的"不做就不能交付"？|
| **测试方法可行** | 涉及的 AC 在当前测试基础设施下可执行吗（单测 / 集成测 / E2E）？需要新增 mock 或测试工具吗？|
| **回归风险** | PRD 改动是否可能破坏已有功能？是否需要在 AC 中加入回归保护？|
| **跨 Feature 联调** | PRD 是否涉及与其他 Feature / 子项目联调？联调点是否在 AC 中明确？|

### QA 评审 verdict 标准

| Verdict | 含义 |
|---------|------|
| **PASS** | PRD 全部 AC 可测、覆盖完整（含边界 / 失败 / 异常），TC 编写无障碍 |
| **PASS_WITH_CONCERNS** | PRD 主体可测，有 1-2 条建议（如 P1 AC 不够细，建议 Blueprint 阶段补 TC）|
| **NEEDS_REVISION** | PRD 含不可测 AC / 关键边界缺失 / AC 之间冲突，必须 PM 修订才能写 TC |

### Subagent / 主对话模式

执行方式由 PMO 在 triage 阶段决定。

🔴 **QA 视角强烈倾向 Subagent**（fresh context 防鼓掌效应；QA 视角独立性是核心价值）。
