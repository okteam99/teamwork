# 后端开发规范

> 后端 RD 必须遵守。通用规范见 📎 [common.md](./common.md) · 🔴 必读白名单 📎 [HARD-RULES.md](./HARD-RULES.md)。
> Subagent 加载指引：后端子项目加载 HARD-RULES.md(必读)+ 本文件 + common.md(按需)，无需加载 frontend.md。
> 📎 **通用教程不入库**（同 frontend.md v8.123 裁定）：保留的 ✅/❌ 示例仅限**承载契约/门禁字段**的对照（如 §四 日志必须字段）· 通用技术用法由 AI 按需自生成 · 项目特异约定归各项目 `DEV-RULES.md`。

---

## 一、后端测试规范

> v8.287:TDD 手段规定已整体撤除(怎么测 AI 自觉)· 测试的三条**结果规则**见 [HARD-RULES.md](./HARD-RULES.md)。本框架的证据硬门在 stage 层(`dev-complete --test-exit-code 0` + 差分基线)。

## 二、集成测试规范（后端 API）

> 检查什么(响应格式/边界/落库真值)= 模型自带知识 · 不复述。本节只留项目约定:

- **触发**:后端 API / 数据库操作 / 三方调用 → 默认需要;可跳过(无法 mock / 成本过高 / 纯前端)**需用户确认**。
- **测试数据走 `docs/TEST-DATA.md`**:测试前先查它复用 · 新建的数据登记进去 · 测试后清临时数据、保基础数据(不登记 = 下个 Feature 重复造数据)。
- **环境依赖走根级 `scripts/test-env-setup.sh`**(RD 开发阶段创建维护 · 实现自由:Docker/本地/远程):接口契约(退出码 0/非0 · 幂等 · 无交互 · stdout JSON)**单源 [common.md §三](./common.md)**。
- **集成测试报告**(产物字段):环境信息(服务/DB/配置来源)· API 测试结果(端点 × 状态 × 断言)· 数据库验证结果(落库真值核对)· 测试数据使用(fixture / seed 来源)· 结论 · 失败项(现象 + 定位 + 处理)。**格式不规定**,字段齐即可。

## 三、服务端 API 接口规范

> 🔴 **优先级链**(同 §五 迁移命名 v8.119 模式 · 本节全部小节适用:响应结构 / JSON 命名 / 状态码 / 分页):
> ① 优先按项目/子项目 `DEV-RULES.md` 的 API 约定 —— 有则严格照办 · 本节默认不适用。
> ② DEV-RULES 未规定 · 但**存量服务已有明确一致的接口风格**(envelope / 命名 / 错误码)→ **沿用存量**(对外契约 · 同服务内一致性 = 正确性 · 新接口不得自创风格)· 🔴 并**提示用户**把该约定固化进 DEV-RULES.md(AI 不代写 · dev-rules 模板约定)。
> ③ 全新服务 / 无任何既有约定 → 用本节 teamwork 默认。
> 📎 与 §五 migration「不读邻居」的区别:迁移文件名是**内部惯例**(坏样板不该传染 · 要么 DEV-RULES 要么默认);API 响应结构是**对外契约**(消费方依赖 · 同服务不一致即破坏)→ 存量风格在 ② 合法沿用。

### 统一响应格式

```json
{
 "code": "SUCCESS",
 "msg": "操作成功",
 "data": {},
 "extra": {}
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `code` | string | ✅ | 业务状态码，成功为 `"SUCCESS"`，失败为具体错误码 |
| `msg` | string | ✅ | 人类可读的提示信息 |
| `data` | object | ✅ | 业务数据，无数据时为空对象 `{}` |
| `extra` | object | ❌ | 扩展字段，用于分页信息、调试信息等 |

### JSON 命名规范

**默认 snake_case**(`user_id` / `created_at`)—— 禁驼峰/帕斯卡/中划线/全大写混入(同服务不一致即破坏 · 存量风格按本节头部优先级链 ② 沿用)。

### 常用业务状态码

| 状态码 | 说明 | HTTP Status |
|--------|------|-------------|
| `SUCCESS` | 操作成功 | 200 |
| `INVALID_PARAM` | 参数校验失败 | 400 |
| `UNAUTHORIZED` | 未登录/认证失败 | 401 |
| `FORBIDDEN` | 无权限 | 403 |
| `NOT_FOUND` | 资源不存在 | 404 |
| `CONFLICT` | 资源冲突 | 409 |
| `RATE_LIMITED` | 请求频率超限 | 429 |
| `INTERNAL_ERROR` | 服务器内部错误 | 500 |

**自定义状态码格式**：`{模块}_{错误类型}`
- `USER_NOT_FOUND`
- `ORDER_ALREADY_PAID`
- `PAYMENT_INSUFFICIENT_BALANCE`
- `AUTH_TOKEN_EXPIRED`

---

## 四、日志规范

### 日志级别与格式(v8.285 压缩 · 级别语义与 JSON 示例已删 —— 模型默认就会)

- 级别按标准语义(DEBUG 开发 / INFO 关键节点 / WARN 非预期可处理 / ERROR 业务异常 / CRITICAL 系统级)。
- **结构化日志必填字段**(项目约定 · 不是通用常识):`timestamp` · `level` · `service` · `trace_id`(链路追踪)· `message` · 业务上下文键(如 `feature_id` / 关键业务 id)· 异常时附 `stack`。格式 JSON,字段名以此为准。

### 非预期分支日志规则(两条逆默认硬规则 · 原双段合并 · 各带 CR 门)

**🔴 降级/兜底必打 WARN(不得降为 INFO/DEBUG · 不得静默)**

- **触发**:任何「A 失败 → B 兜底继续」的分支 —— 含 else/default 兜底、参数无效用默认值、重试触发、缓存未命中走库、以及一切「理论上不应该走到」的路径(Subagent dispatch 失败降级主对话同规 · 见 [agents/README](../agents/README.md) 降级必 WARN)。
- **必须字段**:降级原因(原始异常/不可用信号)· 降级前方案 · 降级后方案 · 业务上下文(trace_id / 业务 id)。
- why:降级是「正确但不正常」的路径,必须可观测、可告警、可追溯 —— **静默降级 = 掩盖问题** = 生产事故来源;兜得住业务可用性,不能兜可观测性。

**🔴 三方/外部服务调用异常必打 ERROR(不得降为 WARN/INFO · 不得静默)**

- **范围**:任何跨进程边界的网络调用(三方 API / 内部服务 RPC·MQ / 云 SDK / 中间件)。
- **触发**:HTTP 非 2xx · 业务码失败 · 网络层异常 · 反序列化失败 / 字段不符约定 —— 🔴 含**限流/熔断/降级信号**(下游返回 200 但业务语义是失败也算)。捕获到的异常(即使已处理)、数据校验失败、业务规则冲突同级 ERROR。
- **必须字段(缺一不可)**:调用目标(服务/接口)· 请求标识:traceId / spanId · 请求摘要(敏感脱敏)· 响应摘要(状态码 + body 或 error)· 耗时:duration_ms · 重试信息(如有)· 业务上下文(user_id / order_id)。
- 🔴 **APM / sidecar 自动上报 ≠ 免除打日志义务**(业务上下文 APM 采不到);外部调用被降级兜底时**先 ERROR(异常本身)再 WARN(降级动作)· 两条缺一不可**。
- why:跨服务边界是故障定位的关键切面 —— 静默失败的外部调用 = 排查毫无头绪 = MTTR 飙升。

**评审门禁**:CR 时所有跨进程调用点必须验证有 ERROR(try/catch 包住外部调用但 catch 里没打 → 阻塞 CR);所有 fallback/catch-and-continue 路径必须验证有 WARN,缺失即阻塞。

---

## 五、数据库迁移规范

> Schema 的当前设计（ER 图、表结构）记录在 ARCHITECTURE.md 的 📎 database-schema.md 中。
> 本章定义的是 **变更 schema 的操作规范**。

### 迁移文件规则

```
📁 迁移文件位置：
└── {项目路径}/migrations/ （或项目约定的迁移目录）

📄 命名规范（🔴 优先级链）：
└── {时间戳}_{操作描述}.{扩展名} · 例 20260312143022_add_user_email_index.sql
 ├── ① 优先按 DEV-RULES.md（项目/子项目级）的 migration 命名 / 守卫约定 —— 有则严格照办
 ├── ② DEV-RULES 未规定 → 默认 YYYYMMDDHHmmss **秒级真实时间戳**（🔴 不用 000000 填充 · 防同日撞号 + 乱序）
 └── 🔴 **不靠读邻居 migration 推断**格式（邻居可能不一致 / 有坏样板）· 要么 DEV-RULES 要么秒级默认
```

### 起号纪律(🔴 多 Feature 并行撞号 · v8.293 从 templates/architecture.md 上提到此权威处)

teamwork 常态是**多 Feature 并行、各自 worktree 起 migration** —— 撞 timestamp 是反复出现的高频问题,
而模型默认只会「照当前时间起个号」,不会想到去看别人已经合进去的号。故这条是**信息不是教程**:

- 起号前先 `git fetch` merge_target,**取 merge_target tip 上的最大 timestamp**,新号必须**大于**它
  (只看本地 = 落后就撞已合并的号)。
- 用**真实当前时间精确到秒**;同秒手工 +1。🔴 **不要批量生成**(一次循环产多个 migration 同 timestamp = 自撞)。
- **撞号后用 `git mv` 改名 + amend**(同步改文件内 `schema_migrations` version 引用),
  🔴 **不要 revert + 新加** —— 会留两次 schema 变更历史、污染审计。
- 物化校验(取前 14 位 `sort | uniq -d` 非空即撞号)由**项目自行实施** —— 各 ORM / migration 路径差异大,框架不强制。

### 强制要求

> 迁移基本卫生(可逆 up/down / 提交前本地验证 / 已执行不可改 / 禁手动改库 / DML-DDL 分离)= 模型自带知识 · 不复述。本节只留项目约定与门:

- 🔴 **加 migration 前先查 DEV-RULES 的 migration 约定 / 守卫**(version-ceiling / 高水位线 / sequence guard 等)· 同 PR 满足守卫要求(如 bump ceiling)· 撞到未声明的项目守卫(CI 失败)→ 修复后记进 DEV-RULES/KNOWLEDGE(下次不再撞)。
- **TECH.md 必声明是否涉 schema 变更**(涉及 → 列变更内容;破坏性变更〔删列/改类型/删表〕必标风险)· 迁移完成后同步 ARCHITECTURE.md → database-schema.md。
- 🔴 **跨子项目 Schema 同步(增/改/删列时必查 · 缺列 → ORM 反序列化报错 → 500)**:
  - TECH.md 必含「数据库变更 → Schema 影响分析」章节(模板 templates/tech.md)· 来源 = database-schema.md「Model/Struct 映射」表 + grep 全项目代码;
  - 核对 Struct 字段与数据库列完全一致(字段名/类型/可空性)+ 所有引用该 Struct 的 SQL 查询列列表匹配;
  - 架构师 Tech Review **独立验证**影响分析完整性(不依赖 RD 自查)· Code Review 对照影响分析表逐项验证;
  - 变更完成后同步 database-schema.md(Model 映射表 + SQL 引用点 + 变更记录)。

### FK（外键）策略

> 🔴 **默认避免** DB-level `FOREIGN KEY` 约束（含 `ON DELETE CASCADE` / `ON UPDATE CASCADE`）。引用完整性由应用层 / ORM hook / 服务边界保证。
>
> 项目可在 `DEV-RULES.md` 声明覆盖此默认（如"本项目默认启用 FK"），声明后以其为准 + TECH.md 引用 DEV-RULES 行号；未声明则按本节默认（避免 FK）。

#### 默认避免的理由(逆教科书默认 · 故必须给 why)

分库分表后 FK 失效(规则终须落应用层 · 双层维护反而不一致)· 大批量写入/迁移/灰度回放时 FK check 成本不可控(锁/校验/死锁)· 跨服务边界的引用关系不该由 DB 隐式承载 · 级联删除生产事故回滚成本极高(一行 delete 删全库)· ORM 通常已能维护引用语义。

#### 引入 FK / CASCADE 的硬要求

🔴 若 TECH.md 仍要引入 `FOREIGN KEY` 或 `ON DELETE/UPDATE CASCADE`，**必须**在「Schema 影响分析」表中加一行 **「FK 决策 + 理由」**，理由须满足以下任一条件：

```
✅ 强一致小规模 OLTP（单库 · 不会分片 · 行数预估 <10M · 写入 QPS 低）
✅ 法务 / 合规 / 财务类强约束（应用层不可信 · DB 是最后真值防线）
✅ 内部管理后台 / 配置表（写入极低频 · 一致性 > 性能）
✅ DEV-RULES.md 已明文记录"本项目默认启用 FK"约定（cite 行号）
```

❌ **反模式黑名单**（命中即架构师 Tech Review BLOCKER · 不可降级为非阻塞 concern）：

```
❌ "ORM 自动生成的 FK 我没动" → 必须在 migration 显式 DROP CONSTRAINT 或在 TECH 给理由
❌ "为了开发期数据完整性方便" → 开发期 ≠ 生产期 · 单测覆盖才是真防线
❌ "防止脏数据" → 应用层 transaction + 单测才是真防线 · DB 兜底是误解
❌ "通用最佳实践" / "教科书推荐" / "DBA 默认建议" → 无项目语境的理由 = 没给理由
❌ 没在 TECH 写 FK 决策行 → 视为引入未声明 · BLOCKER
```

#### 出口校验（架构师 Tech Review · 命中触发关键词必查）

```
触发：TECH.md / migration / database-schema.md 含 FOREIGN KEY / REFERENCES / FK / CASCADE
校验：
 1. TECH.md「Schema 影响分析」表存在「FK 决策 + 理由」行
 2. 理由满足上述 ✅ 任一条件
 3. 反模式黑名单未命中
 4. 若启用 CASCADE → 额外列出"删除主行将连带删除哪些子行"清单 + Code Review 必查
```

📎 单源约束：本段是 FK 策略的唯一权威 · `roles/architect.md` / `templates/tech.md` 仅 cite 不复述。

### Schema 变更链条术语对照

| 阶段 | 规范位置 | 使用术语 | 验证重点 | database-schema.md 操作 |
|------|----------|---------|---------|------------------------|
| TECH.md 编写 | — | Schema 影响分析 | 列出所有受影响 Model/Struct 和 SQL | — |
| Blueprint Stage 架构师方案评审 | roles/architect.md + stages/blueprint-stage.md | Schema 影响分析完整性 | 验证分析是否遗漏（独立 grep 对照） | 🔴 更新设计层（表结构、ER 图、设计原则） |
| RD 开发 | stages/dev-stage.md | Schema 同步验证 | 代码是否已按影响分析表同步 | — |
| 架构师 Code Review | roles/architect.md + stages/review-stage.md | Schema 同步验证 | 代码变更是否与影响分析表一致 | 🔴 补充实现层（Model 映射、SQL 引用点） |
| 集成测试 | stages/test-stage.md §集成测试任务规范 | 迁移 + ORM 映射验证 | 运行时验证迁移可执行 + ORM/SQL 映射正确性 | — |

> 📎 各阶段术语不同是因为验证角度不同，但校验基准统一为 TECH.md「Schema 影响分析」表。
> 📎 database-schema.md 两阶段更新：设计层（Tech Review 后写入）→ 实现层（Code Review 后补充）。
> 📎 衔接顺序即状态机 stage 链本身(TECH 声明 → 架构师评审 → RD 实现 → CR → 集成测试)· 各阶段动作与两阶段更新时点以上表为准 · 不再另画流程图。

---

## 六、API 版本管理规范

> API 的当前接口清单记录在 ARCHITECTURE.md 的 📎 api-design.md 中。
> 什么算 Breaking Change、deprecation 怎么走 = 模型自带知识 · 不复述。本章只留项目约定:

- **版本策略默认 URL Path**(`/api/v{N}/...`)· 项目可在 DEV-RULES.md 声明其他策略(如 Header 版本 · 声明后以其为准)。
- **Breaking Change 必升版本号**;版本状态(⚠️ 废弃中 / ❌ 已下线)与**废弃截止日期登记在 api-design.md 版本清单**(下线判定依据 —— 不登记 = 没人知道何时能下线)。
- **涉 API 变更的 TECH.md 必声明**:是否 Breaking → 新版本号 · 影响接口清单 · 旧版本迁移方案(如有调用方)· 完成后同步 api-design.md。
