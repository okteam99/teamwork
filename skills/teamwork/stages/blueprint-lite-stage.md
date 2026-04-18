# BlueprintLite Stage：轻量蓝图（敏捷需求专用）

> 敏捷需求流程中，用户确认精简 PRD 后启动本 Stage。
> 产出简化版 TC + 实现计划，为 Dev Stage 提供蓝图。
> 🔴 不做 TC 技术评审、不做架构师评审（敏捷砍掉的环节）。

---

## 一、设计意图

```
BlueprintLite = 敏捷需求的轻量蓝图
├── 保持"先规划后编码"的原则（Dev Stage 不该边想边写）
├── 但砍掉 Feature 流程中的重量级评审环节
├── QA 视角写简化 TC + RD 视角写实现计划（保持专业方向一致性）
├── 主对话快速执行（无需 Subagent，预期 3-5 分钟）
└── Dev Stage 保持不变——不管 Feature 还是敏捷，它收到的都是"已有蓝图"
```

---

## 二、输入文件

> ℹ️ 本 Stage 由 PMO 在主对话直接执行，不 dispatch Subagent，因此**不生成 dispatch 文件**。
> 但 PMO 需按清单顺序加载下方文件（缺失则报错或降级）。
> 若未来改为 Subagent 执行，再按 [Dispatch 文件协议](../agents/README.md#dispatch-文件协议) 生成 `{Feature}/dispatch_log/{NNN}-blueprint-lite.md`。

```
PMO 执行时加载：
├── stages/blueprint-lite-stage.md（本文件）
├── roles/qa.md（TC 编写规范部分）
├── roles/rd.md（实现计划规范部分）
├── templates/tc.md（TC 模板，用精简版）
├── docs/features/{功能目录}/PRD.md（已确认的精简 PRD）
│
可选文件（存在则读取）：
├── docs/architecture/ARCHITECTURE.md
└── docs/KNOWLEDGE.md
```

---

## 三、执行流程

```
📌 BlueprintLite 1/2: QA 编写简化版 TC
├── 按 PRD 验收标准逐条写 BDD 用例
├── 只覆盖核心场景（正常流程 + 主要异常）
├── 不要求完整的边界/并发/性能场景（Feature 流程才需要）
├── 产出：TC.md（精简版，标注「敏捷-精简」）

📌 BlueprintLite 2/2: RD 编写实现计划
├── 文件清单（新增/修改文件列表）
├── 改动要点（每个文件的核心变更说明）
├── 测试策略（单测 + 集成测试覆盖点）
├── 产出：嵌入 BlueprintLite 执行报告（不独立 TECH.md 文件）
```

---

## 四、返回状态

```
├── ✅ DONE → TC.md + 实现计划就绪，进入 Dev Stage
├── ⚠️ DONE_WITH_CONCERNS → PRD 有歧义但可继续（记录 concerns）
└── 💥 FAILED → PRD 不够清晰无法产出蓝图 → PMO ⏸️ 用户补充
```

---

## 五、红线

```
🔴 不做评审：BlueprintLite 不含 TC 技术评审和架构师评审（这是敏捷的核心精简点）
🔴 不替代 Blueprint：Feature 流程仍走完整 Blueprint Stage（含评审）
🔴 TC 质量底线：即使精简，每条 PRD 验收标准至少对应 1 条 BDD 用例
🔴 Dev Stage 不变：BlueprintLite 产出后，Dev Stage 按标准流程执行（TDD+单测）
```

---

## 六、输出格式

```
📋 BlueprintLite 执行报告（{功能编号}-{功能名}）
================================================

## TC 概况
├── 用例数：{N} 条 BDD
├── 覆盖 AC：{M}/{总 AC}
└── 标注：敏捷-精简（不含边界/并发/性能场景）

## 实现计划
| 文件 | 操作 | 改动要点 |
|------|------|----------|

## 测试策略
├── 单测：{覆盖点}
└── 集成测试：{覆盖点}

## Concerns（如有）
```
