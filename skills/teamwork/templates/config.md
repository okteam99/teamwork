# CONFIG 模板

## RESOURCES.md（资源依赖配置）

> 位置：`project-specs/RESOURCES.md`（workspace 级，非功能级 —— 详 docs/conventions.md §13）

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

## .teamwork_localconfig.json（本地协作配置）

> 此文件存放在项目根目录，记录当前用户负责的子项目范围。
> 🔴 本地配置，不提交到 git（应加入 .gitignore）。每个开发者各自维护一份。

```markdown
# Teamwork 本地配置

## 负责人
- 名称：[用户名 / 昵称]

## Skill 版本标记（🔴 新增·PMO 自动维护，禁止手改）

<!-- teamwork_version: PMO 启动时写入的当前 skill 版本号，用作 CLAUDE.md / AGENTS.md 校验缓存。 -->
<!-- 机制： -->
<!-- - 启动 Step 1.2 读取此字段 → 与 SKILL.md frontmatter version 字段比对 -->
<!-- - 一致 → 跳过 CLAUDE.md / AGENTS.md 逐字符 diff（99%+ 场景，节省 ~65-75% 启动 token） -->
<!-- - 不一致 / 缺失 / localconfig 不存在 → 走全量校验 + 写回新版本号 -->
<!-- - 漂移自愈仍保留：skill 升级 → 版本不一致 → 触发一次全量 diff → 写回新版本号 → 下次跳过 -->
<!-- 逃生舱：`/teamwork force-init` 强制走全量校验（忽略版本缓存）。 -->
<!-- 🔴 禁止手改：此字段由 PMO 维护。手改后果 = 版本命中但 CLAUDE.md 未同步，红线 R7 风险。 -->
teamwork_version:

## 负责子项目
<!-- scope: all 表示负责所有子项目；否则列出具体子项目缩写 -->
scope: all

<!-- 如果只负责部分子项目，改为如下格式：
scope:
 - AUTH
 - WEB
-->

## Git Worktree 策略
<!-- worktree: off / auto / manual -->
<!-- auto = PMO 在 Goal-Plan Stage 入口自动创建 worktree（v7.3.8 前移），Feature 完成后询问用户清理【默认】 -->
<!-- manual = PMO 提醒用户自行管理 worktree，不自动创建/清理 -->
<!-- off = 不使用 worktree，所有 Feature 在主分支开发（适合单 Feature 串行 / megarepo / IDE 跨 worktree 跳转受限场景） -->
<!-- -->
<!-- 默认值变更（撤销 默认 off 决策）： -->
<!-- - 多 Feature 并行场景实际更常见，worktree 隔离避免主分支污染 -->
<!-- - Ship Stage 双段流程后 worktree 清理已闭环（合并验证后自动清理） -->
<!-- - worktree deps 处理已有完整指引（standards/common.md） -->
<!-- - 环境配置预检前置到 triage，worktree 创建已自动化无暂停点 -->
<!-- -->
<!-- 改 off 的合理理由（保留 off 为可选）： -->
<!-- - megarepo：每个 worktree 是全量 checkout，多 Feature 并行时磁盘/索引代价高 -->
<!-- - IDE 跨 worktree 跳转受限：worktree 在 sibling 目录下，IDEA/VS Code 跨 worktree 搜索/跳转不便 -->
<!-- - 工具链忽略复杂：每个工具需单独配排除（tsc/eslint/jest/docker...） -->
<!-- -->
<!-- 🔴 缺失硬默认（避免 AI 钻空子）： -->
<!-- - localconfig 文件中本字段缺失 / 注释掉 → PMO 必须按 auto 处理（不是 off） -->
<!-- - 禁止 AI 自降级到 off（如以"主工作区干净"等理由） -->
<!-- - 仅当用户在 triage 暂停点显式选 off 才允许 off -->
<!-- - 实战 case 反模式：localconfig 没配 worktree，AI 沿用主工作区写代码 = 流程违规 -->
worktree: auto

### Worktree 根目录

<!-- worktree_root_path: worktree 的根目录。每个 Feature 自动在此目录下创建子目录(子目录名 = Feature ID 全名)。 -->
<!-- 默认值: .worktree(项目根目录下) -->
<!-- 完整规范(模板示例 / monorepo 多模块策略 / .gitignore 约束 / 解析优先级)见 docs/conventions.md § 9-11。 -->
worktree_root_path: .worktree

## Ship 策略

<!-- 🟢 变更：Ship Stage 改为 MR 模式（PMO 只负责净化 + push feature + 生成 MR/PR create URL，不做本地 merge / push merge_target / 冲突解决）。 -->
<!-- 已移除字段：ship_rebase_before_push（不再做 rebase）、ship_policy（不再有 merge+push 暂停点）。 -->

### 合并目标分支
<!-- merge_target: Feature 的目标分支，用于 MR/PR 的 base 分支。默认 staging。 -->
<!-- 解析优先级：state.json.merge_target > 本文件 merge_target > 默认 staging -->
<!-- 常见值：staging / develop / main（单分支模型） -->
<!-- 作用：Ship Stage 生成 MR create URL 时作为 base 分支；worktree 创建时作为 base。 -->
merge_target: staging

### MR/PR 创建链接模板（可选）
<!-- mr_url_template: Ship Stage 生成 MR/PR create URL 的模板。 -->
<!-- 留空 = PMO 按 git remote 自动识别平台（github / gitlab / gitlab-self-hosted / gitee / bitbucket）生成。 -->
<!-- 识别失败（unknown 平台）时，mr_create_url=null 并在完成报告 concerns 标注，需用户手动创建 MR。 -->
<!-- 若使用自建 gitlab / 企业 git 需要自定义链接格式，可在此配置，支持以下占位符： -->
<!-- {remote_url} = git remote 原始 URL（含 .git 后缀已去除） -->
<!-- {remote_host} = git host 域名（如 git.internal.example.com） -->
<!-- {repo_path} = owner/repo 路径（如 team/service） -->
<!-- {feature_branch_enc} = URL-encoded feature 分支名（feature/F042-login → feature%2FF042-login） -->
<!-- {merge_target} = 目标分支名 -->
<!-- 示例（自建 GitLab）：{remote_url}/-/merge_requests/new?merge_request[source_branch]={feature_branch_enc}&merge_request[target_branch]={merge_target} -->
mr_url_template:

### Worktree 清理策略
<!-- worktree_cleanup: ask / keep / remove（默认 ask） -->
<!-- ask = Ship 完成后询问用户（推荐） -->
<!-- keep = 默认保留 worktree 便于复查 -->
<!-- remove = 默认清理 worktree（仅建议稳定流程用） -->
worktree_cleanup: ask

### Artifact ID 号段策略
<!-- id_strategy: utc-yymmddhhmmss（默认）/ sequential -->
<!-- utc-yymmddhhmmss = artifact ID 号段用 UTC0 秒级时间戳 YYMMDDHHMMSS（12 位）。跨机/多 agent 并行各自生成、免中心协调 → 根治分布式 max+1 撞号；字典序=时间序、肉眼可读创建时间。 -->
<!-- sequential = 旧 3 位顺序号 max+1（单 clone 项目可 opt-out · 保留好念短序号）。 -->
<!-- 改此项只影响新建 feature · 存量 ID 不重编号（新旧天然可区分：3-4 位 vs 12 位）。详 docs/conventions.md §1。 -->
id_strategy: utc-yymmddhhmmss

### ship2 归档策略
<!-- archive_on_ship: true（默认）/ false -->
<!-- true = 交付后过程层 feature 目录 zip 进 features/_archive/<id>.zip（+ INDEX.md）· 原目录从 merge_target 删 · 随收尾 MR 合（防 AI 检索过时 feature 信息 · 代码是唯一真相）。 -->
<!-- false = 收尾 MR 只同步终态 state.json · 不归档 · feature 目录留存。详 stages/ship-stage.md §14。 -->
archive_on_ship: true

### 本地敏感配置目录
<!-- local_env_auto_create: true（默认）/ false -->
<!-- true = bootstrap 在 .teamwork-local-env/ 缺失时自动创建（config.properties 模板 + 目录内 .gitignore），已存在不覆盖。 -->
<!-- 用途：kubeconfig / DB 密码 / 个人 API key 等本机敏感配置统一放此目录 · 双重 gitignore（根 .gitignore + 目录内 .gitignore）绝不进仓库。读取约定见 TROUBLESHOOTING.md。 -->
<!-- false = 不主动创建（opt-out · 仍保留 gitignore 预留规则）。 -->
local_env_auto_create: true

### 禁用异质模型审核（单模型用户）
<!-- disable_heterogeneous_review: false（默认）/ true -->
<!-- false = external 评审跑异质模型（claude↔codex 交叉 · 唯一跨模型安全网 · 推荐）。 -->
<!-- true = 只有一个模型时：external-review 自动 emit subagent 降级配方（PMO 起宿主自身模型 subagent 自审 · 不 exec · 落 external-cross-review/ 满足 P0-154 · frontmatter degraded_mode:config-disabled · 非异质 · 同盲点）· 每次 bootstrap 启动 WARN 提醒。详 standards/external-model-usage.md §11.5。 -->
<!-- 区分 --self-review-fallback（异质临时不可用的 per-run 降级 · 同走 subagent · degraded_mode:subagent-fallback）：本项是项目级长期策略（每次自动降级）。 -->
<!-- 装好第二个模型 CLI 后建议删此项 / 设 false 恢复异质，交叉 review 质量更高。 -->
disable_heterogeneous_review: false

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
├── README.md ← 本文件（三方资源总览索引）
├── {三方服务A}/ # 如：wechat-pay/
│ ├── 接入指南.md # 接入流程、前置条件、配置步骤
│ ├── API参考.md # 接口文档、请求/响应格式
│ └── ... # SDK 文档、示例代码等
├── {三方服务B}/
│ └── ...
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
4. **敏感信息**：API Key、Secret 等配置不放在此目录，统一在 \`project-specs/RESOURCES.md\` 中管理
5. **弃用三方**：状态改为「已弃用」，子目录保留（历史参考），在接入指南中注明替代方案
\`\`\`
