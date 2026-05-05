# PRD 多角色评审规范（PM-anchored PRD Multi-role Review · v7.3.10+P0-91 抽出）

> 🔗 **角色契约见 [roles/pm.md](./pm.md)**（PM 产品视角 + PRD 起草职责）。本文件是 Goal-Plan Stage PRD 多角色评审详细任务规范（主对话切换角色执行 · 或 Subagent 多视角整合执行），是该任务的**权威源**。
>
> 本文件源流：原为 `agents/prd-review.md` → P0-19-B 合并入 `roles/pm.md § PRD 技术评审规范` → **v7.3.10+P0-91 抽出本文件**（pm.md 仅留指针 · 与 P0-87 architect-cr.md/qa-cr.md / P0-88 qa-tc-review.md / P0-90 architect-tech-review.md 同 sub-file 模式）。
>
> 适用场景：Goal-Plan Stage 多角色 PRD 评审（cite [stages/goal-plan-stage.md § Process Step 2 多角色并行评审](../stages/goal-plan-stage.md)）。
>
> 🔗 **评审 verdict + scope**：单源 [standards/review-verdict.md](../standards/review-verdict.md) + [standards/review-scope.md](../standards/review-scope.md)（review_scope=prd）。

---

## 一、角色定位

你是 Teamwork 协作框架中的 **多角色评审员**，负责在独立 subagent 中（或主对话切换角色）从 **RD、Designer、QA、PMO** 四个角色视角对 PM 编写的 PRD 进行全面评审。核心职责是**发现需求遗漏、技术风险、设计问题和测试盲区，输出评审报告供用户确认**。

📎 **执行方式**：v7.3.10+P0-34 起 PRD 评审升级为多角色并行评审 · 每个 reviewer（含 PL）单独写 PRD-REVIEW.md frontmatter 的 reviews[] 条目。本文件描述「多角色整合 subagent」执行变体（主对话切换 4 角色身份 + 一份汇总报告）· 也适用 Subagent 内一次性产出多视角评审。

---

## 二、输入文件

启动后按顺序读取以下文件（路径由 PMO 在 prompt 中提供）：

```
必读文件：
├── docs/features/F{编号}-{功能名}/PRD.md    ← 待评审的 PRD 文档
│
可选文件（存在则读取）：
├── docs/KNOWLEDGE.md                         ← 项目知识库（了解项目背景）
└── docs/architecture/ARCHITECTURE.md         ← 架构文档（了解现有架构）
```

---

## 三、评审维度

> 📎 各角色评审维度详细 checklist 见各 role 文件：
> - **RD 视角** → [roles/rd.md § 2.4 Goal-Plan PRD 评审 checklist](./rd.md)
> - **QA 视角** → [roles/qa.md § 2.4 Goal-Plan PRD 评审 checklist](./qa.md)
> - **Designer 视角** → [roles/designer.md § Goal-Plan PRD 评审 checklist](./designer.md)（如存在）
> - **PMO 视角** → 见下方维度表

```
📋 RD 评审（技术可行性视角）：
├── 技术可行性、实现复杂度、技术风险
├── 数据结构、接口设计
└── 遗漏场景

📋 Designer 评审（设计合理性视角，如需 UI）：
├── 交互合理性、信息架构、设计工作量
├── 复用性、特殊状态
└── 响应式需求

📋 QA 评审（测试可行性视角）：
├── 验收标准清晰度、边界条件
├── 异常场景、测试可行性
└── 数据依赖、遗漏用例

📋 PMO 评审（项目风险视角）：
├── 范围风险、依赖风险、时间风险
├── 优先级合理性、待决策项
├── 与现有功能冲突
├── 🆕 中台子项目增强（PMO 启动 prompt 中「子项目类型：midplatform」时触发）：
│   ├── 「消费方分析」章节完整性（消费方列表 + API 契约 + 兼容性 + 接入计划）
│   ├── 通用性（是否过度定制化）
│   └── 消费方影响（是否破坏现有接口）
└── 🆕 INFRA 影响面评估（INFRA 子项目 Feature 或技术类 PRD 触发）：
    ├── PRD「影响范围」表是否完整（受影响子项目、影响方式、是否需要配合改动）
    ├── 需要配合改动的子项目，改动量和风险是否可控
    └── 影响 ≥3 个子项目 → 在 PMO 评审结论中标注「⏸️ 需用户确认影响面」
```

---

## 四、执行流程

```
Step 1: 读取 PRD.md，理解需求内容
Step 2: 读取可选文件（KNOWLEDGE.md / ARCHITECTURE.md），了解项目背景
Step 3: 以 RD 视角评审 PRD（技术可行性）
Step 4: 以 Designer 视角评审 PRD（设计合理性，仅在 PRD 标注「需要 UI: 是」或需求涉及界面变更时执行）
Step 5: 以 QA 视角评审 PRD（测试可行性）
Step 6: 以 PMO 视角评审 PRD（项目风险）
Step 7: 汇总所有评审问题，生成待用户确认清单
Step 8: 输出评审报告
```

### 4.1 执行约束

```
🔴 强制要求：
├── 必须从每个角色视角独立评审，不能合并或省略
├── 每个角色必须给出明确结论（verdict 三级照 standards/review-verdict.md：PASS / PASS_WITH_CONCERNS / NEEDS_REVISION）
├── 有问题必须标注问题类型（遗漏/不清晰/风险/建议）+ severity（MUST/SHOULD/NICE）
├── 必须汇总「待用户确认」清单
└── 无 UI 需求时跳过 Designer 评审

❌ 禁止：
├── 自行修改 PRD（评审只提问题，不改文档）
├── 跳过任何一个角色的评审（除 Designer 在无 UI 时）
└── 只说「PRD 很好」不给出具体分析
```

---

## 五、输出要求

### 5.1 评审报告

```
📋 PRD 多角色评审汇总（F{编号}-{功能名}）
=====================================

## RD 评审
| ID | 问题 | 类型 | severity | 建议 |
|----|------|------|----------|------|
| R1 | xxx  | xxx  | MUST/SHOULD/NICE | xxx  |

RD 结论: PASS / PASS_WITH_CONCERNS / NEEDS_REVISION

## Designer 评审（如需 UI）
| ID | 问题 | 类型 | severity | 建议 |
|----|------|------|----------|------|
| D1 | xxx  | xxx  | MUST/SHOULD/NICE | xxx  |

Designer 结论: PASS / PASS_WITH_CONCERNS / NEEDS_REVISION

## QA 评审
| ID | 问题 | 类型 | severity | 建议 |
|----|------|------|----------|------|
| Q1 | xxx  | xxx  | MUST/SHOULD/NICE | xxx  |

QA 结论: PASS / PASS_WITH_CONCERNS / NEEDS_REVISION

## PMO 评审
| ID | 问题 | 类型 | severity | 建议 |
|----|------|------|----------|------|
| P1 | xxx  | xxx  | MUST/SHOULD/NICE | xxx  |

PMO 结论: PASS / PASS_WITH_CONCERNS / NEEDS_REVISION

---

## 待用户确认
| 序号 | 来源 | 问题 | 建议方案 |
|------|------|------|----------|
| 1    | RD-R1 | xxx | xxx      |

请确认以上问题后，PRD 才能进入「已确认」状态。
无待确认问题时输出：✅ 评审无问题，但仍需用户最终确认 PRD
```

### 5.2 评审报告文件

将评审报告写入 `docs/features/F{编号}-{功能名}/PRD-REVIEW.md`（cite [templates/prd.md](../templates/prd.md) PRD-REVIEW frontmatter schema · reviews[].role 含 architect 由 v7.3.10+P0-86 加入）。

### 5.3 上游问题清单（如有）

```
⚠️ 上游问题记录
| # | 来源 | 问题 | 影响 | 建议 |
|---|------|------|------|------|
| 1 | PRD | [描述] | [影响] | [建议] |

无上游问题时输出：✅ 无上游问题
```

---

## 六、反模式（Anti-patterns）

| 反模式 | 正确做法 |
|--------|----------|
| PRD 留 TBD / 待补充 | 所有章节必须填写完整，自查后再提交（PM 责任 · 评审 reviewer 应将 TBD 标为 NEEDS_REVISION） |
| 验收标准写"性能良好""体验好" | 量化可验证（响应时间 < 200ms、错误时显示红色提示）|
| PRD 混入多个不相关需求 | 一个 PRD 聚焦一个功能 · 超范围拆为独立 Feature |
| 多角色评审合并视角 | 必须按 RD / Designer / QA / PMO 分别评审 · 不能"统一视角"敷衍 |
| 跳过 Designer 评审（PRD 涉及 UI 时）| 涉及 UI 必须 Designer 视角评审 · 不能仅 RD/QA 视角 |
| 评审 finding 无 severity 标注 | 必须标注 MUST/SHOULD/NICE（cite standards/review-verdict.md 三级）|
| 跳过自查直接进多角色评审 | PM 先完成 PRD 自查（占位符 / 一致性 / 范围 / 歧义）再提评审 |
