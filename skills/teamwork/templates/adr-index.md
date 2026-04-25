# ADR 索引模板

> 位置：`{子项目路径}/docs/adr/INDEX.md`（每个子项目各一份，与 ADR 同目录）
>
> 受众：PMO preflight 阶段读取此索引，列出可能影响当前 Feature 的相关决策。
>
> 用途：ADR 目录的快速索引，按状态 + 主题双维度组织。
>
> 更新时机：
> - 新增 ADR → 插入「活跃决策」段
> - ADR 状态变更为 deprecated / superseded → 移到对应段
> - 🔴 每次 ADR 变更必须同步更新本索引（Blueprint Stage 架构师职责）

```markdown
# ADR 索引

> 本项目的架构决策记录索引。ADR 体系见 [templates/adr.md](../../teamwork/templates/adr.md)。

## 活跃决策 (Accepted)

| ID | 标题 | 主题 | 日期 | 触发 Feature |
|----|------|------|------|-------------|
| ADR-0001 | {标题} | db | YYYY-MM-DD | {Feature 目录名} |
| ADR-0002 | ... | ... | ... | ... |

## 提案中 (Proposed)

| ID | 标题 | 主题 | 日期 | 触发 Feature | 等待 |
|----|------|------|------|-------------|------|
| ADR-NNNN | ... | ... | ... | ... | 架构师评审 / 用户确认 |

## 已废弃 (Deprecated / Superseded)

| ID | 标题 | 主题 | 状态 | 废弃日期 | 被替代 / 原因 |
|----|------|------|------|---------|-------------|
| ADR-NNNN | ... | ... | superseded | YYYY-MM-DD | ADR-NNNN |
| ADR-NNNN | ... | ... | deprecated | YYYY-MM-DD | {原因} |

## 按主题索引

> 每个 tag 对应的 ADR 列表。PMO preflight 时按当前 Feature 的主题扫描相关 ADR。

- **db** (数据库选型/schema/迁移): ADR-0001, ADR-0005
- **api** (API 设计/契约/版本): ADR-0002
- **auth** (鉴权/授权/会话): ADR-0003
- **frontend** (UI 框架/状态管理/样式方案): ADR-0004
- **backend** (后端框架/运行时/进程模型): ...
- **deploy** (部署方式/环境/CI-CD): ...
- **observability** (日志/监控/告警): ...
- **security** (安全/加密/合规): ...
- **{其他主题}**: ...

## 维护约定

- 🔴 ID 连续编号（0001, 0002, ...），永不复用；superseded 的 ID 保留在「已废弃」段
- 🔴 每条新增 / 状态变更必须同步更新本索引
- 🔴 superseded 时双向链接：新 ADR 的 `supersedes` 字段 + 旧 ADR 的 `status=superseded-by-*`
- 📎 新增主题 tag 时在「按主题索引」段追加一行
- 📎 PMO preflight 读取此文件时只需读前 N 行即可（体量上限 200 行，超出说明需要分片）
```

## 使用约定（v7.3.10+P0-21）

- **PMO preflight**：读取本索引，按当前 Feature 的主题/涉及模块扫描「活跃决策」段，列出可能影响当前 Feature 的 ADR-ID 清单，注入 PMO 初步分析摘要
- **Blueprint Stage 架构师评审**：新增 / 变更 ADR 时同步更新此索引（不更新 = 流程偏离）
- **首次创建**：项目首次产出 ADR 时自动创建本索引文件（Blueprint Stage 架构师职责）
