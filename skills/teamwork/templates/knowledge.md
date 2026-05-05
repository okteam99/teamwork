# KNOWLEDGE 模板（v7.3.10+P0-22 收敛版）

> 位置：`docs/KNOWLEDGE.md`（项目级）+ `{子项目}/docs/KNOWLEDGE.md`（子项目级，多子项目模式）
>
> 受众：**未来的开发者（包括未来的 AI）** — 让后续 Feature 启动时能快速感知"本项目有哪些特殊事实"。
>
> 🔴 **边界声明（v7.3.10+P0-22 关键收敛）**：
>
> | 信息类型 | 去处 | 理由 |
> |---------|------|------|
> | 架构决策（为什么选 A 不选 B，有备选项有后果）| 🔗 [ADR](./adr.md) | 决策有备选项 + 后果，KNOWLEDGE 没有此结构 |
> | 通用代码规范 | standards/ 或 rules/ | 跨项目通用的不属于项目本地知识 |
> | 单个 Feature 的复盘（时间线 + 指标）| `docs/retros/` + [retros-index.md](./retros-index.md) | 复盘是时间线回顾，不是事实索引 |
> | **项目特有的事实 / 约束 / 偏好** | **本文件** | 不是决策，是"发现"——没有备选项的客观事实 |
>
> 🔴 **本文件只收录 3 类内容**：Gotchas（陷阱）/ Conventions（约定）/ Preferences（偏好）。其他一律迁出。
>
> 🔴 **体量上限 300 行**，超出说明需要：(a) 把部分 Gotcha 升格为 ADR（如果本质是决策）/ (b) 分拆到子项目级 KNOWLEDGE.md / (c) 过期条目归档（加 archived 标记，放末尾）。

```markdown
# 项目本地知识库

> 本文件记录项目开发过程中积累的**特有事实**、**团队约定**和**用户偏好**。
> 不记录决策（走 ADR）、不记录通用规范（走 standards/rules）、不记录复盘（走 retros/）。
> Teamwork 在 triage-stage（用户输入承接阶段）会扫描本文件，注入「📚 相关项目事实」段。详见 [stages/triage-stage.md](../stages/triage-stage.md) Step 2。

## 📚 Glossary（术语词典 · v7.3.10+P0-78 借鉴 mattpocock/skills grill-with-docs）

> **Be Opinionated**：多个词指同一概念时，**挑一个最好的**，其他列为 Avoid 别名。
> **Keep tight**：一句话定义"是什么"（不写"做什么"）。
> **Project-specific only**：通用编程概念（timeout / error type）不放——只放本项目业务术语 + 通用架构 8 词。
> **触发写入时机**：Goal-Plan / Blueprint Stage 评审中发现术语漂移 → 实时（inline · 不批处理）写入。

### 业务术语（项目专属）

| Term | 定义（一句话） | Avoid 别名 |
|------|---------------|-----------|
| **Order** | 用户提交的购买请求，含 ≥1 个商品 | Purchase, Transaction |
| **Invoice** | 订单交付后向客户发出的付款请求 | Bill, PaymentRequest |
| **Customer** | 下单的个人或组织 | Client, Buyer, Account |

### 通用架构词汇（v7.3.10+P0-78 借鉴 mattpocock/skills improve-codebase-architecture · 8 词）

| Term | 定义 | 用法 |
|------|------|------|
| **Module** | 一组高内聚的代码单元（文件 / 包 / namespace）| 不混用"组件 / 服务 / 层" |
| **Interface** | Module 对外暴露的契约（API / 函数签名 / Protocol）| 不混用"接口 / API"（Interface 是抽象 · API 是其外网络化具象）|
| **Depth** | Interface 的深度 = 信息隐藏程度（少 API + 多 internal 实现 = 深模块）| 设计目标：deep modules |
| **Seam** | 两个 Module 之间的真实分界（多调用方共享的 Interface）| 一个 adapter ≠ Seam · 两个 adapter 才是 |
| **Adapter** | 适配两个不兼容 Interface 的中间层 | 一次性 adapter 不抽象 · 重复 ≥ 2 次才抽象成 Seam |
| **Leverage** | 一处改动能影响多处的能力 | 高 leverage = 好设计；过度 leverage = 隐性耦合 |
| **Locality** | 相关代码的物理邻近性 | 高 locality = 好维护性 · 跨 Module 跳读 = 差 locality |
| **Boundary** | Context / 限界上下文之间的归属边界 | "Customer 数据归 Customer Context · 其他 Context 引用 ID" |

### Relationships（实体关系 · 业务术语之间）

- 一个 **Order** 产出 ≥1 个 **Invoice**
- 一个 **Invoice** 归属唯一一个 **Customer**
- 一个 **Customer** 可有 N 个 **Order**

### "删除测试"启发式（v7.3.10+P0-78 借鉴 improve-codebase-architecture）

🔴 **判断模块是否"shallow"（浅层 · 该删）**：删掉它 → 复杂度消失？还是分散到 N 个调用点？
- 复杂度消失 → 模块设计好（深模块 · 高 leverage）
- 复杂度分散到 N 个调用点 → shallow module · 应删除并 inline 到调用方

🔴 **"两个 adapter 才抽象"**：第一次出现适配需求 = 写 inline 一次性代码；第二次重复 = 抽象成 Seam（独立 Interface · 加到本词典）。**禁止 1 次就抽象**（过度设计警报）。

## 🔀 Flagged Ambiguities（已澄清的歧义 · v7.3.10+P0-78 借鉴 grill-with-docs）

> 评审循环中暴露"用户用 X 词同时指 A 和 B"时，澄清完后**实时**记录到此（不批处理）。
> 防止下个 Feature 来同样的词又得 PMO 重新询问澄清一次。

| ID | 模糊词 | 澄清结论 | 触发 Feature | 时间 |
|----|--------|---------|-------------|------|
| FA-001 | "账号" | 三义：Customer（客户实体）/ User（操作主体）/ Tenant（多租户隔离单元）；上下文未明确时一律走 PMO 澄清 | F035 评审 | 2026-04-12 |
| FA-002 | "推送" | 二义：Push Notification（系统级推送）/ Message Push（业务消息推送）；按上下文区分 | F048 评审 | 2026-04-22 |

## ⚠️ Gotchas（陷阱 / 约束 / 历史坑）

> 项目特有的陷阱、历史踩坑、外部系统的怪癖。**不是决策**——是被动发现的客观约束。
> 触发写入时机：Bug 修复完成 / Review Stage 发现陷阱 / Dev Stage 踩坑。

| ID | 主题 | 描述 | 规避方法 | 发现时间 | 触发 Feature |
|----|------|------|---------|---------|-------------|
| GO-001 | db | Postgres JSONB GIN 索引在高并发写入时会锁表 | 高频写字段避免 JSONB，拆到独立列 | 2026-01-15 | F023-xxx |
| GO-002 | api | 支付网关冷启动延迟 2s | 请求前必须先调 `/warmup` | 2026-02-03 | F031-支付重构 |
| GO-003 | env | CI 机器 Python 3.10 缺 `libffi-dev` | Dockerfile 里显式 `apt install libffi-dev` | 2026-03-10 | F042-CI 修复 |

## 📋 Conventions（团队约定）

> 团队内部约定但不够格成为全局代码规范的项目级约定。**不是红线，不是 standards**——是项目内部共识。
> 触发写入时机：Review Stage 架构师发现 RD 已默认遵守的约定 / PM 验收时用户强调的格式要求。

| ID | 主题 | 约定 | 理由 | 约定时间 |
|----|------|------|------|---------|
| CV-001 | api | 所有 API error 返回 `{code, message, details}` 结构 | 前端统一错误处理 | 2026-01-20 |
| CV-002 | frontend | 表单字段命名一律 camelCase（不跟后端 snake_case）| 前端工具链默认 | 2026-02-15 |
| CV-003 | naming | 数据库表前缀 `app_`，禁用 `tbl_` | 历史遗留迁移 | 2026-03-01 |

## 🎨 Preferences（用户偏好）

> 用户在产品层面强调的偏好——风格、交互、沟通方式。**不是规范**——是用户的口味。
> 触发写入时机：PM 验收时用户明确强调 / UI Design Stage 用户选 A 不选 B 时陈述的理由。

| ID | 类别 | 偏好 | 来源 | 记录时间 |
|----|------|------|------|---------|
| PR-001 | UI | 所有卡片圆角统一 8px | F015 验收时用户明确要求 | 2026-01-10 |
| PR-002 | 交互 | 提示消息统一在顶部居中，3s 自动消失 | F022 UI 评审时用户选项 | 2026-02-12 |
| PR-003 | 沟通 | PM 验收时用户偏好简洁汇报（3 行内），不要长篇分析 | 多个 Feature 累计反馈 | 2026-03-15 |

## 按主题索引

> PMO preflight 时可按主题快速 grep。

- **db**: GO-001
- **api**: GO-002, CV-001
- **env**: GO-003
- **frontend**: CV-002
- **naming**: CV-003
- **UI**: PR-001, PR-002
- **交互**: PR-002
- **沟通**: PR-003
- **拒绝**: OS-001, OS-002
- **术语**: Order, Invoice, Customer, Module, Interface, Seam（按主题速查 · v7.3.10+P0-78）
- **歧义**: FA-001, FA-002（v7.3.10+P0-78）

## ❌ Out of Scope（已拒绝过的方案/方向 · v7.3.10+P0-77 借鉴 mattpocock/skills triage）

> 拒绝过的方案 / 方向 / Feature 候选——防止 AI 反复提同一个被否的方案。
> 触发写入时机：评审循环中明确 REJECT / PM 验收时拒绝某方向 / Goal-Plan Stage 讨论中确认"这个方向不做"。
> PMO 在 Goal-Plan Stage 起草前必扫描本段，避免 PM 重新提已被否的方向。

| ID | 拒绝的方向 | 拒绝理由 | 拒绝时间 | 触发 Feature / 决策点 |
|----|-----------|---------|---------|----------------------|
| OS-001 | 接入 GraphQL 替代 REST API | 团队 REST 经验积累深 / 工具链成熟 / 当前性能瓶颈不在协议层 | 2026-02-10 | F029 评审 |
| OS-002 | 用户头像存 base64 进 DB | 体积大 / 缓存友好度差 / 应该走 CDN | 2026-03-05 | F034 评审 |

🔴 **PMO 起草 Goal-Plan / 评审循环时必须先扫 OS-NNN 列表**：发现 PRD 草案重新提了被否方向 → 直接打回让 PM 改写或显式说明"为什么本次重新审视这个方向"（必须有新的触发原因，否则违规）。

## 归档（archived）

> 已不适用的 Gotcha / Convention / Preference，保留备查。Feature 新启动时 PMO preflight 可忽略本段。

| ID | 原内容 | 归档原因 | 归档时间 |
|----|--------|---------|---------|
| GO-001 | ~~Postgres JSONB GIN 索引锁表~~ | 升级到 PG 15 后问题消失（ADR-0008）| 2026-04-01 |
```

## 使用约定（v7.3.10+P0-22）

### 写入硬时机

🔴 以下时机 PMO 必须提示对应角色写入 KNOWLEDGE.md（不写 = 流程偏离）：

- **Gotcha 写入时机**：
  - Bug 修复流程完成时 → PMO 在完成报告里提示 RD 补一条 Gotcha（除非确认是一次性 bug 无复发风险）
  - Dev Stage 遇到未知陷阱（调试 ≥30 分钟 / 改动方案多次返工）→ 修复后必写一条 Gotcha
  - Review Stage 架构师发现 RD 绕过陷阱写了特殊处理 → 必写一条 Gotcha（把"为什么这么写"显式化）

- **Convention 写入时机**：
  - Review Stage 架构师评审发现 RD 自发遵守某项约定 → 提示写入 CV-NNN（让后续 Feature 延续一致）
  - Goal-Plan Stage 用户强调格式要求 + 本要求跨 Feature 适用 → PM 记录 CV-NNN

- **Preference 写入时机**：
  - PM 验收时用户明确表达偏好 → PM 必记 PR-NNN
  - UI Design Stage 用户在多方案中选 A 并陈述理由 → Designer 必记 PR-NNN

### PMO preflight 扫描

🔴 PMO 初步分析任何 Feature / 敏捷需求 / Feature Planning 时，必须扫描 KNOWLEDGE.md：
- 读 `{目标子项目}/docs/KNOWLEDGE.md`（不存在 → 「本项目暂无 KNOWLEDGE 记录」）
- 按当前 Feature 主题 + 涉及模块扫描 3 类索引，列出可能相关的条目 ID
- 注入 PMO 初步分析输出的「📚 相关项目事实」行
- 只读 KNOWLEDGE.md 前 300 行（体量上限 = 扫描上限）

### 体量与归档

- 🔴 单个 KNOWLEDGE.md ≤ 300 行。超出时必选一种处理：
  - (a) 判定条目本质是决策 → 升格为 ADR，本文件删除
  - (b) 多子项目模式下条目只适用某子项目 → 迁到 `{子项目}/docs/KNOWLEDGE.md`
  - (c) 条目已过期 → 移到「归档」段加 archived 标记
- 🟢 每个条目 ≤ 2 行，超出说明不够"事实"，可能是决策伪装

### ID 编号规则

- Gotcha：GO-NNN（三位数字，从 001 起）
- Convention：CV-NNN
- Preference：PR-NNN
- Out of Scope：OS-NNN（v7.3.10+P0-77）
- Glossary：术语**直接用术语本身作为锚点**（Term 段加粗 · 不编号 · v7.3.10+P0-78）
- Flagged Ambiguities：FA-NNN（v7.3.10+P0-78）
- 🔴 编号连续不复用，归档条目保留原 ID

## 与其他文档的协作

- 🔗 [ADR 模板](./adr.md) — 决策归 ADR，本文件不重复
- 🔗 [retros-index.md](./retros-index.md) — 复盘时间线归独立索引
- 🔗 [standards/common.md](../standards/common.md) — 通用规范归 standards，本文件只记项目特有
