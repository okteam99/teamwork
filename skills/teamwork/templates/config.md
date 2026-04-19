# CONFIG 模板

## RESOURCES.md（资源依赖配置）

> 位置：`docs/RESOURCES.md`（项目级，非功能级）

```markdown
# 资源依赖配置

> 本文件记录项目开发和测试所需的外部资源配置，首次配置后后续自动复用。

## 数据库配置

### Dev 环境
| 配置项 | 值 |
|--------|-----|
| Host | |
| Port | |
| Database | |
| Username | |
| Password | ⚠️ 敏感信息，建议使用环境变量 |
| 连接字符串 | |

### Test 环境
| 配置项 | 值 |
|--------|-----|
| Host | |
| Port | |
| Database | |

## 第三方服务配置

### {服务名，如 Redis/MQ/OSS}
| 配置项 | 值 |
|--------|-----|
| Endpoint | |
| AccessKey | ⚠️ |
| SecretKey | ⚠️ |

## 测试账号

| 用途 | 账号 | 密码 | 获取方式 | 备注 |
|------|------|------|----------|------|
| 普通用户 | | | 自主注册 | |
| 管理员 | | | 用户提供 | |
| VIP用户 | | | 用户提供 | |

## API 配置

| 环境 | Base URL | 备注 |
|------|----------|------|
| Dev | | |
| Test | | |
| Prod | | 仅查看，禁止测试 |

## 配置使用说明

\`\`\`bash
# 环境变量方式（推荐）
export DB_HOST=xxx
export DB_PASSWORD=xxx

# 或使用 .env 文件（已加入 .gitignore）
cp .env.example .env
# 编辑 .env 填入实际值
\`\`\`

## 变更记录
| 日期 | 变更 | 操作人 |
|------|------|--------|
\`\`\`

---

## .teamwork_localconfig.md（本地协作配置）

> 此文件存放在项目根目录，记录当前用户负责的子项目范围。
> 🔴 本地配置，不提交到 git（应加入 .gitignore）。每个开发者各自维护一份。

```markdown
# Teamwork 本地配置

## 负责人
- 名称：[用户名 / 昵称]

## 负责子项目
<!-- scope: all 表示负责所有子项目；否则列出具体子项目缩写 -->
scope: all

<!-- 如果只负责部分子项目，改为如下格式：
scope:
  - AUTH
  - WEB
-->

## Git Worktree 策略
<!-- worktree: off / auto / manual（默认 off） -->
<!-- off = 不使用 worktree，所有 Feature 在主分支开发【默认·保守】 -->
<!-- auto = PMO 在 Plan Stage 入口自动创建 worktree（v7.3.8 前移），Feature 完成后询问用户清理 -->
<!-- manual = PMO 提醒用户自行管理 worktree，不自动创建/清理 -->
<!-- -->
<!-- 保留 off 为默认的原因（v7.3.9+P0-9 决策）： -->
<!--   - megarepo：每个 worktree 是全量 checkout，多 Feature 并行时磁盘/索引代价高 -->
<!--   - IDE review：worktree 在 sibling 目录下，IDEA/VS Code 跨 worktree 搜索/跳转不便 -->
<!--   - 工具链忽略：.worktree/ 内嵌方案需每个工具单独配排除（tsc/eslint/jest/docker...） -->
<!--   - 选 auto/manual 前建议先用 P0-10 的 worktree_base + IDE workspace 自动配置（待实施） -->
worktree: off

## Ship 策略（v7.3.9 新增）

### 合并目标分支
<!-- merge_target: Feature 完成后合并的目标分支。默认 staging。 -->
<!-- 解析优先级：state.json.merge_target > 本文件 merge_target > 默认 staging -->
<!-- 常见值：staging / develop / main（单分支模型） -->
merge_target: staging

### Rebase 策略
<!-- ship_rebase_before_push: Ship Stage push feature 分支前是否 rebase onto 目标分支。 -->
<!-- false（默认，多人场景推荐）= 保留原 feature 分支历史，通过 merge --no-ff 合并 -->
<!-- true（单人场景可选）= push 前 rebase 最新 target，线性历史更干净但可能覆盖他人改动 -->
ship_rebase_before_push: false

### Ship 策略
<!-- ship_policy: auto / confirm（默认 confirm） -->
<!-- confirm = Ship Stage 每个关键操作（rebase/merge/push）前都需要用户确认 -->
<!-- auto = 信任 PMO 自主执行，仅在冲突/异常时暂停 -->
ship_policy: confirm

### Worktree 清理策略
<!-- worktree_cleanup: ask / keep / remove（默认 ask） -->
<!-- ask = Ship 完成后询问用户（推荐） -->
<!-- keep = 默认保留 worktree 便于复查 -->
<!-- remove = 默认清理 worktree（仅建议稳定流程用） -->
worktree_cleanup: ask

## 备注
<!-- 可选：记录当前阶段重点、临时分工调整等 -->
\`\`\`

---

## external/README.md（三方资源目录说明）

> 位置：项目根 `external/README.md`
> 🔴 PMO 初始化项目时自动创建 `external/` 目录和此 README。

```markdown
# 三方 / 外部资源文档

> 本目录集中存放项目依赖的所有三方服务、SDK、外部 API 的接入文档和参考资料。
> 按三方服务名称分子目录，方便一眼识别整个项目用了哪些外部依赖。

## 目录结构

\`\`\`
external/
├── README.md              ← 本文件（三方资源总览索引）
├── {三方服务A}/            # 如：wechat-pay/
│   ├── 接入指南.md         # 接入流程、前置条件、配置步骤
│   ├── API参考.md          # 接口文档、请求/响应格式
│   └── ...                # SDK 文档、示例代码等
├── {三方服务B}/
│   └── ...
└── ...
\`\`\`

## 三方资源索引

| 三方服务 | 子目录 | 使用方子项目 | 用途 | 状态 |
|----------|--------|-------------|------|------|
| | | | | 接入中 / 已接入 / 已弃用 |

> **使用方子项目**：填写依赖该三方资源的子项目缩写（如 PAY, WEB），便于评估三方变更的影响面。
> **状态**：\`接入中\` = 正在对接；\`已接入\` = 生产可用；\`已弃用\` = 已迁移到替代方案，保留文档供参考。

## 使用规范

1. **新增三方依赖**：创建子目录，至少包含一份接入指南，并在上方索引表中登记
2. **子目录命名**：统一使用 kebab-case（如 \`wechat-pay/\`、\`alipay-sdk/\`、\`google-maps/\`）
3. **三方 SDK/包**：存放官方文档副本或链接，不存放 SDK 二进制文件（二进制通过包管理器安装）
4. **敏感信息**：API Key、Secret 等配置不放在此目录，统一在 \`docs/RESOURCES.md\` 中管理
5. **弃用三方**：状态改为「已弃用」，子目录保留（历史参考），在接入指南中注明替代方案
\`\`\`
