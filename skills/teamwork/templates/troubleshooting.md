# 项目排查工具集（TROUBLESHOOTING）

> 🟢 **本文是 teamwork prepare-stage 自动创建的空骨架**（v7.3.10+P0-118-B 起）· 类比 `teamwork_space.md` 模式。
> ⏳ **请按项目栈补充具体命令**（kubectl / psql / redis-cli / curl / 部署回滚链等）· 填完后 teamwork 排查时会自动 read 你的内容。
>
> teamwork PMO 在 mode A query / E · discuss 触及「排查 / 报错 / 查 log / 查环境」时按需 read。
> 与 [KNOWLEDGE.md](./knowledge.md) 互补：KNOWLEDGE = 踩坑注意点 · 本文 = 操作步骤。
>
> **路径硬规则**：项目根 `TROUBLESHOOTING.md`（teamwork 固定路径 · 不查 docs/）。
> **内容由项目维护**：teamwork 不规范具体命令（每个项目栈完全不同 · 用户按实际填）。
> **空骨架检测**：tools/init_triage.py 在 triage 入口跑 · grep 本段顶部标识符「本文是 teamwork prepare-stage 自动创建的空骨架」· 命中 = 未填 · advisory.severity=INFO topic=empty-skeleton。用户填完后建议删除本段顶部 🟢 提示行 · 否则脚本仍判定未填。

---

## 一、环境

| 环境 | 入口 / 域名 | 写操作授权 |
|------|----------|----------|
| local | ... | 任意 |
| staging | ... | 任意（只读副本优先）|
| production | ... | 🔴 必须用户暂停点授权（与 SKILL.md 红线 R8 协同）|

## 二、查 log

```bash
# 填项目实际命令（kubectl / docker logs / cloudwatch / 自建脚本 / ...）
# 区分 staging vs production
```

## 三、查数据 / 缓存（按需）

```bash
# 数据库连接：填命令（psql / mysql / mongo / dynamodb-cli / ...）
# 缓存 / 队列：填命令（redis-cli / RabbitMQ / SQS / ...）
# 🔴 production 写操作必须用户授权
```

## 四、常见报错（按项目实际填 3-5 条）

```
- 报错 X → 排查链：1. 看 X log → 2. 检查 Y → 3. 验证 Z
- ...
```

---

## 安全约束（必读）

🔴 PMO 排查时必守：

- staging 任意 / production 只读优先 / 写操作必须 ⏸️ 用户暂停点授权（红线 R8）
- 不写 secret / token / 密码到本文（用 `{VAR}` / `$ENV_VAR` 占位符）
- 不复述 secret 到主对话
- 不下载 dump / backup（合规风险）

## 维护

- 命令验证：每季度一次（运维变更可能让命令失效）
- 新增环境 / 工具时同步本文

末。
