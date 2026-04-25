# ADR 模板（Architecture Decision Record）

> 位置：`{子项目路径}/docs/adr/NNNN-{slug}.md`（NNNN 四位数字，从 0001 起连续编号，永不复用）
>
> 受众：**未来的开发者（包括未来的 AI）** — 用决策者视角记录"为什么选 A 而不是 B"，让未来读者能复用/质疑/替换此决策。
>
> 用途：记录具有跨 Feature 影响 / 高反悔成本 / 非显然选择的架构决策。**不是每个 Feature 都产 ADR**——由 Blueprint Stage 架构师评审阶段的「3 问触发器」决定。
>
> 触发条件（三问全 yes 才产）：
> 1. 这个决策会影响 ≥ 1 个未来 Feature 吗？
> 2. 反悔成本很高吗（需要大规模改动）？
> 3. 存在多个合理方案，选哪个不是显然的吗？
>
> 🔴 **备选项至少 2 个，否则不是"决策"，不需要 ADR**。
>
> 更新时机：
> - Blueprint Stage 架构师识别 → 创建（status=proposed）
> - 架构师方案评审通过 / 用户确认 → status=accepted
> - 后续被新决策替代 → status=superseded-by-ADR-NNNN（原 ADR 保留不删）
> - 后续判定不再适用但无替代 → status=deprecated
>
> 体量约束：单个 ADR **50-150 行**，超出说明备选项没收敛好，返工。

```markdown
---
id: ADR-NNNN
title: {决策标题 - 祈使句，如 "采用 PostgreSQL 作为主库"}
status: proposed | accepted | deprecated | superseded-by-ADR-NNNN
date: YYYY-MM-DD
tags: [db, api, auth, frontend, ...]  # 至少 1 个主题 tag
triggered_by: {Feature 目录名，如 "2026-04-用户系统"}
supersedes: []  # 被本决策替代的旧 ADR 列表，如 [ADR-0003]
---

# ADR-NNNN: {决策标题}

## 背景 (Context)

> 2-4 句话。什么场景下需要这个决策？什么触发了它？有哪些相关前置事实？

...

## 决策驱动因素 (Decision Drivers)

> 至少 2 项。决策要同时满足哪些约束 / 非功能需求 / 团队前提。

- 约束 1：...
- 约束 2：...
- （非功能需求，例如性能、可维护性、团队熟悉度、许可证）

## 备选项 (Alternatives Considered)

> 至少 2 个备选项。单方案不是决策，不需要 ADR。

### 方案 A: {名称}
- **描述**: 一句话说清楚是什么
- **优点**:
  - ...
- **缺点**:
  - ...
- **成本估算**: 开发时间 / 迁移成本 / 长期维护开销

### 方案 B: {名称}
- **描述**: ...
- **优点**: ...
- **缺点**: ...
- **成本估算**: ...

### 方案 C: {名称，可选}
...

## 决策 (Decision)

**选中：方案 {X}**

**理由** (1-3 句话说清楚为什么 X 胜出)：

...

## 后果 (Consequences)

### ✅ 正面影响
- ...（本决策带来的好处，特别是跨 Feature 的复用机会）

### ⚠️ 负面影响 / 代价
- ...（本决策的直接代价 / 放弃的能力）

### 🔗 长期影响（未来 Feature 需要知道）
- ...（未来 Feature 会受本决策约束的方面——这是 ADR 对 AI 自引用最有价值的部分）

### ❓ 未解决问题 / 已知风险
- ...（决策后还留下的问题，或可能让我们反悔的风险信号）

## 相关

- **触发 Feature**: [{Feature 目录名}]({Feature 路径})
- **关联 ADR**: ADR-NNNN（依赖）/ ADR-NNNN（互斥）/ ADR-NNNN（类似主题）
- **参考资料**: 链接 / 论文 / 博客 / benchmark

## 修订历史

| 日期 | 状态 | 说明 |
|------|------|------|
| YYYY-MM-DD | proposed | 初始提案（Blueprint Stage 架构师） |
| YYYY-MM-DD | accepted | 架构师评审通过 + 用户确认 |
| YYYY-MM-DD | superseded-by-ADR-NNNN | 被 ADR-NNNN 替代（说明原因） |
```

## 格式硬规则（v7.3.10+P0-21）

- 🔴 文件名：`NNNN-{slug}.md`，NNNN 四位数字从 0001 起连续编号，**永不复用**（被 superseded 的 ADR 保留文件，ID 不回收）
- 🔴 frontmatter 五个字段全必填：`id / title / status / date / tags`
- 🔴 备选项 ≥ 2（单方案走 TECH.md，不走 ADR）
- 🔴 每次 ADR 新增 / 状态变更 → 同步更新 `INDEX.md`
- 🔴 `status=superseded-by-*` 时，新 ADR 的 `supersedes` 字段必须反向引用旧 ADR ID（双向关联）
- 🟢 体量 50-150 行，超标通常说明备选项未收敛
