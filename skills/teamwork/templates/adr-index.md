# ADR 索引模板

> 位置：`{子项目路径}/docs/adr/INDEX.md`（每个子项目各一份，与 ADR 同目录）
>
> 受众：PMO 在 triage 阶段读取此索引，列出可能影响当前 Feature 的相关决策。详见 [SKILL.md § Triage 入口规范](../SKILL.md)。
>
> 用途：ADR 目录的快速索引，按状态 + 主题双维度组织。
>
> 更新时机：
> - 新增 ADR → 插入「活跃决策」段
> - ADR 状态变更为 deprecated / superseded → 移到对应段
> - 🔴 每次 ADR 变更必须同步更新本索引（Blueprint Stage 架构师职责）

```markdown
# ADR 索引

> 本项目的架构决策记录索引。ADR 体系与单条格式基准 = teamwork skill 的 `templates/adr.md`（随 skill 安装 · 不在本项目内 · 不放相对链接）。

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

> 每个 tag 对应的 ADR 列表。PMO triage 时按当前 Feature 的主题扫描相关 ADR。

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

> 🔴 编号规则 / 每次变更同步本索引 / superseded 双向链接 —— 基准同 `templates/adr.md`,此处不复述。
```

> 本文件原 66 行里,「PMO 读本索引」写了 4 遍、编号与同步规则与 `adr.md` 各写一份。
> 现在只留**索引骨架** —— 规则单源在 [adr.md](./adr.md)。
