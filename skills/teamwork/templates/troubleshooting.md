# 项目排查工具集（TROUBLESHOOTING）

> 🟢 **本文是 teamwork bootstrap 自动创建的空骨架** · 类比 `teamwork-space.md` 模式。
> ⏳ **请按项目栈补充具体命令**（kubectl / psql / redis-cli / curl / 部署回滚链等）· 填完后 teamwork 排查时会自动 read 你的内容。
>
> teamwork PMO 在 mode A query / E · discuss 触及「排查 / 报错 / 查 log / 查环境」时按需 read。
> 与 [KNOWLEDGE.md](./knowledge.md) 互补：KNOWLEDGE = 踩坑注意点 · 本文 = 操作步骤。
>
> **路径硬规则**：`project-specs/TROUBLESHOOTING.md`（teamwork 固定路径 · 与 product-overview/ 同级 · 详 docs/conventions.md §13）。
> **内容由项目维护**：teamwork 不规范具体命令（每个项目栈完全不同 · 用户按实际填）。
> **空骨架提示**：未填时本段顶部保留 🟢 空骨架提示行 · 用户填完后建议删除该行（AI 读到提示行即知内容尚未按项目实际补充）。

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

## 五、本地敏感配置来源（`.teamwork-local-env/`）

🔐 本机敏感配置统一放 **`.teamwork-local-env/`**（项目根 · teamwork session 初始化自动创建 + 双重 gitignore · **绝不进仓库 / 不进 feature 产物 / 不进归档 zip**）：

- **键值型**（DB 密码 / API key / token）→ `.teamwork-local-env/config.properties`（`KEY=value`）
- **整文件型**（kubeconfig / 证书 / `service-account.json`）→ 直接作为文件放本目录

下面填**你项目实际的加载方式**（teamwork 不假设技术栈）：

```bash
# 键值型 secret（任选其一 · 看你的栈）
set -a; . ./.teamwork-local-env/config.properties; set +a   # shell source 进环境变量
# 整文件型，如 kubeconfig
export KUBECONFIG=.teamwork-local-env/kubeconfig
# 然后跑排查命令：kubectl get pods / PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST ... / ...
```

🔴 本文（TROUBLESHOOTING.md **会进仓库**）里**只写变量名 / 加载方式**，**真值只在 `.teamwork-local-env/`**。

---

## 安全约束（必读）

🔴 PMO 排查时必守：

- staging 任意 / production 只读优先 / 写操作必须 ⏸️ 用户暂停点授权（红线 R8）
- 不写 secret / token / 密码到本文（用 `{VAR}` / `$ENV_VAR` 占位符）· **真值放 `.teamwork-local-env/`（见 §五）**
- 不复述 secret 到主对话
- 不下载 dump / backup（合规风险）

## 维护

- 命令验证：每季度一次（运维变更可能让命令失效）
- 新增环境 / 工具时同步本文

末。
