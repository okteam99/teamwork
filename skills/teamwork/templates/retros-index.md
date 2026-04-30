# 复盘索引模板（v7.3.10+P0-22 新增）

> 位置：`{子项目路径}/docs/retros/INDEX.md`（每个子项目各一份，与单条复盘同目录）
>
> 受众：PMO 在 Feature 启动前需要快速检索历史复盘（"类似 Feature 上次有哪些教训"）时读取。
>
> 用途：复盘文件（`{缩写}-F{编号}-{功能名}.md`，见 [retro.md 模板](./retro.md)）的时间线索引。
>
> 更新时机：
> - 每次 PMO 完成报告 8️⃣-A 阶段创建新复盘 → 同步追加一行到本索引
> - 🔴 每次复盘变更必须同步更新本索引（PMO 职责）

```markdown
# 复盘索引

> 本项目的 Feature 复盘索引。完整复盘数据见 `{文件名}.md`。

## 时间线（最近在前）

| 日期 | Feature | 流程类型 | 一句话摘要 | 复盘文件 |
|------|---------|---------|-----------|---------|
| YYYY-MM-DD | F0NN-xxx | Feature / Bug / 敏捷 | {一句话总结：打回几轮、关键教训} | [查看](./F0NN-xxx.md) |
| YYYY-MM-DD | F0MM-yyy | Feature | 首次通过，无打回 | [查看](./F0MM-yyy.md) |
| YYYY-MM-DD | F0KK-zzz | Bug | Root cause 在 CV-002 命名约定遗漏 | [查看](./F0KK-zzz.md) |

## 按流程类型索引

- **Feature**: F0NN, F0MM, ...
- **Bug 修复**: F0KK, ...
- **敏捷需求**: ...

## 偏差警报（retrospective pattern）

> Stage 连续偏差 ≥ 3 次 或 同类问题反复出现 → PMO 应该触发流程优化 proposal。

| 模式 | 出现次数 | 关联 Feature | 建议处理 |
|------|---------|-------------|---------|
| Goal-Plan Stage 超时 > +30% | 3 | F0NN, F0MM, F0LL | 评估 PRD 讨论模板是否要拆步 |
| Review Stage retry ≥ 2 | 2 | F0KK, F0JJ | 评估 RD 自测强度 |

## 维护约定

- 🔴 每个复盘产出必须同步 INDEX 一行
- 🔴 一句话摘要要说清"本次的痛点"（用户强调过的问题 / 打回原因 / 关键教训），不要流水账
- 🔴 体量上限 200 行；超出说明复盘条目过多需要定期 archive（半年以上复盘可移到 `archive/` 子目录）
- 📎 模式表（偏差警报）不是必填，PMO 发现连续偏差时主动添加
```

## 使用约定（v7.3.10+P0-22）

- **PMO 完成报告 8️⃣-A 阶段**：创建单条复盘文件时同步追加一行到 INDEX.md
- **Feature 启动前 PMO preflight**：若当前 Feature 与历史 Feature 主题相近，可扫描 INDEX.md 时间线段，读相关复盘的关键教训（不强制，是软加分项）
- **流程优化 proposal 触发**：PMO 发现「偏差警报」模式累计 ≥ 3 次 → 主动输出一轮流程改进建议（可能产 ADR 或 KNOWLEDGE Convention）
- **与 KNOWLEDGE.md 的区别**：复盘 = 时间线（每 Feature 一条）；KNOWLEDGE = 主题事实（跨 Feature 复用）
- **体量上限**：INDEX.md ≤ 200 行（超出按 archive/ 分片）；单条复盘无体量上限（详见 retro.md 模板）
