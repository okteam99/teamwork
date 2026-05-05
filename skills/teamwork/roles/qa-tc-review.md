# TC 技术评审规范（QA TC Technical Review · v7.3.10+P0-88 抽出）

> 🔗 **角色契约见 [roles/qa.md](./qa.md)**（QA 测试策略 + 验证职责）。本文件是 Blueprint Stage TC 技术评审详细任务规范（主对话执行 · 多角色视角整合），是该任务的**权威源**。
>
> 本文件源流：原为 `agents/tc-review.md` → P0-19-B 合并入 `roles/qa.md` § TC 技术评审规范 → **v7.3.10+P0-88 抽出本文件**（qa.md 仅留指针 · qa.md 从 359 → ~209 行回到 ≤300 cap · 与 P0-87 qa-cr.md / architect-cr.md 同 sub-file 模式）。
>
> 适用场景：Blueprint Stage TC 技术评审（cite [stages/blueprint-stage.md § Process Step 2 TC 技术评审](../stages/blueprint-stage.md)）。
>
> 🔗 **评审 verdict + scope**：单源 [standards/review-verdict.md](../standards/review-verdict.md) + [standards/review-scope.md](../standards/review-scope.md)（review_scope=blueprint）。

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
│
可选文件（存在则读取）：
├── docs/features/F{编号}-{功能名}/UI.md     ← 核对 UI 相关用例（如需 UI）
├── docs/features/F{编号}-{功能名}/preview/  ← HTML 预览稿
├── docs/features/F{编号}-{功能名}/TECH.md   ← 技术方案（如已有）
└── docs/KNOWLEDGE.md                         ← 项目知识库
```

> 📎 评审 verdict / severity / scope 通用规则见 [standards/review-verdict.md](../standards/review-verdict.md) + [standards/review-scope.md](../standards/review-scope.md)。

---

## 三、评审维度

> 📎 各角色评审维度的执行要点如下。完整评审 verdict 三级（PASS / PASS_WITH_CONCERNS / NEEDS_REVISION）+ severity 三级（MUST / SHOULD / NICE）见 [standards/review-verdict.md](../standards/review-verdict.md)。

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
Step 1: 读取 TC.md、PRD.md，理解用例内容和评审规范
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

> 📎 verdict 三级（PASS / PASS_WITH_CONCERNS / NEEDS_REVISION）+ severity 三级（MUST / SHOULD / NICE）严格遵循 [standards/review-verdict.md](../standards/review-verdict.md)。

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

## 六、反模式（Anti-patterns）

| 反模式 | 正确做法 |
|--------|----------|
| 用自由格式写用例 | 必须用 BDD/Gherkin（Given/When/Then） |
| 只写正向用例 | 每个需求至少有正向 + 反向用例 |
| 评审只看 TC 不看 PRD | 必须对照 PRD 逐条检查 AC↔TC 映射 |
| 单角色视角评审 | 必须 PM/RD（+Designer）多视角 · 任一缺失即重审 |
| 评审报告无问题清单 | 必须输出"待用户确认清单" + 标注 finding severity |
