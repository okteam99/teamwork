# 后端开发规范

> 后端 RD 必须遵守。通用规范见 📎 [common.md](./common.md)。
> Subagent 加载指引：后端子项目只需加载本文件 + common.md，无需加载 frontend.md。

---

## 一、后端测试规范（TDD 强制执行）

**覆盖率要求**: > 80%

### 开发流程（Red-Green-Refactor）

**Step 1: Red（写测试，必须失败）**
```
📋 Step 1: 编写测试 (Red)

根据 TC 用例编写单元测试：
- [ ] test_login_with_valid_credentials_should_succeed
- [ ] test_login_with_invalid_password_should_fail
- [ ] test_login_with_nonexistent_user_should_fail
- [ ] test_login_should_rate_limit_after_5_failures

运行测试: 4 个失败 ✅ (预期)
```

**Step 2: Green（写实现，让测试通过）**
```
📋 Step 2: 实现代码 (Green)

最小实现让测试通过：
- [ ] 实现 login 方法
- [ ] 实现密码验证
- [ ] 实现用户查询
- [ ] 实现限流逻辑

运行测试: 4 个通过 ✅
```

**Step 3: Refactor（重构，保持测试通过）**
```
📋 Step 3: 重构 (Refactor)

优化代码质量：
- [ ] 提取公共方法
- [ ] 优化命名
- [ ] 添加注释

运行测试: 4 个通过 ✅
```

### 测试命名规范

```
✅ 正确：
├── test_login_with_valid_credentials_should_return_token
├── test_login_with_wrong_password_should_return_401
└── test_create_user_with_duplicate_email_should_fail

❌ 错误：
├── test_login
├── test1
└── testLoginFunction
```

---

## 二、集成测试规范（后端 API）

### 触发条件

```
✅ 默认需要集成测试：
├── 所有后端 API 接口
├── 涉及数据库操作的功能
└── 涉及第三方服务调用的功能

⏸️ 可跳过（需用户确认）：
├── 无法 mock 或测试成本过高
├── 纯前端功能，无后端 API
└── 用户明确要求跳过
```

### 测试内容

#### 1. API 接口验证

```
📋 API 验证检查项：
├── 响应格式符合规范（code/msg/data/extra）
├── 状态码正确（成功/失败场景）
├── 必填字段完整
├── 数据类型正确
├── 边界条件处理（空值、超长、特殊字符）
└── 异常场景返回正确错误码
```

**验证示例**：
```python
# 正常场景
response = api.post("/api/v1/users", data={"name": "test", "email": "test@example.com"})
assert response.status_code == 200
assert response.json()["code"] == "SUCCESS"
assert "user_id" in response.json()["data"]

# 异常场景
response = api.post("/api/v1/users", data={"name": ""})
assert response.status_code == 400
assert response.json()["code"] == "INVALID_PARAM"
```

#### 2. 数据库验证

```
📋 数据库验证检查项：
├── 数据正确写入目标表
├── 字段值与请求参数一致
├── 关联数据正确创建/更新
├── 状态变更符合预期
├── 时间戳正确记录
└── 软删除/硬删除正确执行
```

**验证示例**：
```python
# 调用 API 创建用户
response = api.post("/api/v1/users", data={"name": "test", "email": "test@example.com"})
user_id = response.json()["data"]["user_id"]

# 查询数据库验证
db_user = db.query("SELECT * FROM users WHERE id = ?", user_id)
assert db_user["name"] == "test"
assert db_user["email"] == "test@example.com"
assert db_user["created_at"] is not None
```

#### 3. 测试数据管理

```
📋 测试数据规则：
├── 测试前：
│   ├── 检查 docs/TEST-DATA.md 中的测试数据
│   ├── 数据不存在 → 自动创建并记录
│   └── 数据存在 → 直接复用
├── 测试中：
│   ├── 使用独立的测试数据，避免污染
│   └── 记录新创建的数据 ID
└── 测试后：
    ├── 保留可复用的基础数据
    ├── 清理本次测试产生的临时数据
    └── 重置被修改的数据状态
```

#### 4. 环境依赖部署（通过测试脚本）

> 📎 测试脚本接口约定详见 [common.md](./common.md)「三、测试脚本约定」。
> RD 在开发阶段创建根级 `scripts/test-env-setup.sh`，封装全局环境准备逻辑（Docker/本地/远程均可）。

```
📋 RD 创建 test-env-setup.sh 时的实现指南（后端项目）：

典型实现（Docker 优先）：
├── 检测 Docker 环境
│   ├── ✅ 可用 → 使用 docker-compose
│   └── ❌ 不可用 → 检查 docs/RESOURCES.md 是否有远程环境
│       ├── 有 → 使用远程环境
│       └── 无 → 退出码非 0 + stderr 输出「需要 Docker 或远程环境配置」
├── 启动依赖服务（DB/Redis/MQ）
│   ├── docker-compose.test.yml（放在 docs/integration_test/ 下）
│   ├── 等待健康检查（最多 60 秒）
│   └── 加载前置数据（init.sql / seed.redis 等）
├── 验证连通性
│   ├── 数据库连接 ✅
│   ├── Redis 连接 ✅（如有）
│   └── API 服务可达 ✅
└── 成功时 stdout 最后一行输出环境信息 JSON：
    {"db_url": "...", "redis_url": "...", "api_base": "http://localhost:8080"}

🔴 脚本必须满足接口约定：退出码 0/非 0、幂等、无交互、JSON 输出。
   具体实现自由（Docker/K8s/本地进程/远程连接均可）。
```

### 集成测试报告

```
📋 集成测试报告（F001-用户登录）
=====================================

## 环境信息
- 环境: Docker Local / Dev Remote
- 部署方式: docker-compose.test.yml / 远程连接
- API Base: http://localhost:8080
- 数据库: localhost:3306/test_db (Docker) / dev_db@10.0.0.1 (Remote)
- 缓存: localhost:6379 (Docker) / N/A

## API 测试结果
| 接口 | 场景 | 预期 | 实际 | 结果 |
|------|------|------|------|------|
| POST /api/v1/login | 正常登录 | 200 + token | 200 + token | ✅ |
| POST /api/v1/login | 密码错误 | 401 | 401 | ✅ |
| POST /api/v1/login | 用户不存在 | 404 | 404 | ✅ |

## 数据库验证结果
| 操作 | 表 | 验证项 | 结果 |
|------|-----|--------|------|
| 登录成功 | user_sessions | session 创建 | ✅ |
| 登录成功 | users | last_login_at 更新 | ✅ |

## 测试数据使用
| 数据 | ID | 操作 |
|------|-----|------|
| 测试用户 | test_user_001 | 复用 |
| 登录会话 | session_xxx | 新建后清理 |

## 结论
✅ 全部通过 / ❌ 有失败项

## 失败项（如有）
| 接口 | 问题 | 建议 |
|------|------|------|
```

### 失败处理流程

```
集成测试失败（Test Stage 返回后由 PMO 处理）：
    ↓
判断失败类型（根据 Test Stage 报告）：
    ├── 代码 Bug (QUALITY_ISSUE) → PMO dispatch RD Fix → 重新 dispatch Test Stage
    ├── 环境问题 (BLOCKED) → ⏸️ 用户排查 → 修复后 PMO 重新预检 + dispatch
    ├── 需求理解偏差 → ⏸️ 用户确认 → 决定修复方案
    └── 测试用例问题 → ⏸️ 用户确认 → 调整用例或跳过

测试完成后清理（可选）：
    ├── 执行根级 scripts/test-env-teardown.sh（如存在）
    └── 默认保留环境供后续测试复用
```

---

## 三、服务端 API 接口规范

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

### 响应示例

**成功响应**：
```json
{
  "code": "SUCCESS",
  "msg": "获取用户信息成功",
  "data": {
    "user_id": "12345",
    "user_name": "张三",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "extra": {}
}
```

**失败响应**：
```json
{
  "code": "USER_NOT_FOUND",
  "msg": "用户不存在",
  "data": {},
  "extra": { "request_id": "req-abc123" }
}
```

**分页响应**：
```json
{
  "code": "SUCCESS",
  "msg": "查询成功",
  "data": { "list": [] },
  "extra": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

### JSON 命名规范

```
✅ 正确（snake_case）：
├── user_id
├── user_name
├── created_at
├── order_status
└── page_size

❌ 错误：
├── userId（驼峰）
├── UserName（帕斯卡）
├── user-id（中划线）
└── USERNAME（全大写）
```

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

### 日志级别

| 级别 | 使用场景 | 示例 |
|------|----------|------|
| **DEBUG** | 开发调试信息，生产环境关闭 | 变量值、执行路径 |
| **INFO** | 正常业务流程的关键节点 | 请求开始/结束、状态变更 |
| **WARN** | 非预期但可处理的情况 | 参数为空用默认值、降级处理 |
| **ERROR** | 业务异常，需要关注 | 业务校验失败、外部服务调用失败 |
| **CRITICAL** | 严重错误，系统可能无法运行 | 数据库连接失败、配置缺失 |

### 结构化日志格式（服务端必须遵守）

> 默认推荐以下结构化日志格式（示例如下）。项目可在 `docs/KNOWLEDGE.md` 中声明自定义日志格式（如 ELK/Datadog/自建方案），声明后以 KNOWLEDGE.md 中的格式为准。

```json
{
  "severity": "ERROR",
  "message": "Failed to process payment",
  "time": "2024-01-15T10:30:00.000Z",
  "labels": {
    "service": "payment-service",
    "version": "1.0.0"
  },
  "trace": "trace-id-abc123",
  "context": {
    "userId": "user-123",
    "orderId": "order-456"
  },
  "error": {
    "message": "Connection timeout",
    "stack": "Error: Connection timeout\n    at ..."
  }
}
```

### 必填字段（无论使用哪种日志格式，以下字段必须包含）

```
├── severity     # 日志级别
├── message      # 人类可读的日志描述
├── time         # ISO 8601 格式时间戳
└── context      # 业务上下文
```

### 日志规范要求

```
❌ 禁止：
├── 日志信息不包含上下文（无法追溯问题）
├── 异常不打日志直接吞掉
├── 非预期分支逻辑不打日志
└── 日志格式不符合结构化日志规范

✅ 必须：
├── 使用结构化 JSON 格式输出
├── ERROR 级别必须包含 error.stack
├── 请求入口和出口都打 INFO 日志
├── 外部服务调用必须打日志（包含耗时）
├── 关联 trace ID 便于分布式追踪
└── 所有非预期的异常和分支逻辑必须打 WARN 或 ERROR 日志
```

### 非预期分支日志规则

```
⚠️ 必须打 WARN 日志（硬规则，无例外）：
├── 🔴 降级/兜底逻辑触发（任何 fallback 路径）
│   ├── 主服务失败降级到备用服务
│   ├── 新实现失败降级到旧实现
│   ├── 远程调用失败使用本地缓存/默认值
│   ├── Subagent/Agent dispatch 失败降级到主对话执行
│   ├── 首选配置不可用降级到次选配置
│   └── 任何「A 方案失败 → B 方案继续」的兜底路径
├── 进入 else/default 等兜底分支
├── 参数为空或无效，使用默认值
├── 重试逻辑触发
├── 缓存未命中走数据库
└── 任何「理论上不应该走到」的代码路径

❌ 必须打 ERROR 日志：
├── 捕获到异常（即使已处理）
├── 🔴 调用三方 / 外部服务返回异常（任何非预期响应，含 HTTP 非 2xx、业务错误码、超时、连接失败、协议错误、反序列化失败）
├── 数据校验失败
├── 业务规则冲突
└── 任何需要开发人员关注的异常情况
```

**🔴 三方 / 外部服务调用异常 ERROR 日志规则（硬规则）**

```
范围定义（"调用三方 / 其他服务"）：
├── 外部第三方 API（支付、短信、OAuth、地图、IM、推送等）
├── 公司内部其他服务（gRPC / HTTP / MQ / RPC 跨服务调用）
├── 云厂商 SDK 调用（OSS / S3 / Redis 云版 / 云数据库等托管服务）
├── 外部中间件调用（Kafka / RabbitMQ / Elasticsearch / 消息队列等）
└── 任何"跨进程边界"的网络调用（本进程内函数调用不在此范围）

触发 ERROR 日志的"返回异常"定义（满足任一即触发）：
├── HTTP 状态码非 2xx（含 3xx 非预期跳转、4xx、5xx）
├── 业务响应码表示失败（如 code != 0 / success == false / 约定失败码）
├── 网络层异常（超时 / 连接拒绝 / DNS 失败 / TLS 错误）
├── 响应体反序列化失败（JSON 解析错误 / schema 不匹配）
├── 响应字段缺失或类型不符合约定
├── 限流 / 熔断 / 降级信号（即便下游返回 200 但业务语义是失败）
└── 任何"调用方认为不符合预期"的响应

日志级别：ERROR（不得降为 WARN/INFO，不得静默）

必须字段（缺一不可）：
├── 调用目标：服务名 / 接口名 / 方法（如 payment-service / POST /v1/pay）
├── 请求标识：traceId / spanId（分布式追踪必备）
├── 请求摘要：请求参数（敏感字段脱敏）
├── 响应摘要：HTTP 状态码 + 响应体（或错误对象的 message/code/stack）
├── 耗时：duration_ms
├── 重试信息（如有）：当前重试次数 / 最大次数
└── 业务上下文：user_id / order_id 等业务标识

评审门禁：
├── Code Review 时，所有跨进程调用点必须验证是否有 ERROR 日志
├── try/catch 包住外部调用但 catch 里没打 ERROR → 阻塞 CR
├── 仅依靠 APM / sidecar 自动上报 ≠ 免除打日志义务
│   （业务上下文无法被 APM 采集，必须在代码里显式写 ERROR 日志）
└── 外部调用被降级兜底时：
    ├── 先打 ERROR 日志（记录异常本身）
    └── 再打 WARN 日志（记录降级动作）—— 两条都必须，缺一不可

🎯 目的：跨服务边界是故障定位的关键切面。
       静默失败的外部调用 = 排查时毫无头绪 = MTTR 飙升。
       降级可以兜业务可用性，但不能兜可观测性。
```

**示例**：
```javascript
// ✅ 正确：外部调用异常 ERROR 日志（+ 降级时叠加 WARN）
const start = Date.now();
try {
    const resp = await paymentClient.pay({ orderId, amount });
    if (resp.code !== 0) {
        logger.error("Payment service returned business error", {
            target: "payment-service",
            endpoint: "POST /v1/pay",
            traceId: ctx.traceId,
            request: { orderId, amount },
            response: { code: resp.code, msg: resp.msg },
            durationMs: Date.now() - start,
            orderId,
            userId: ctx.userId,
        });
        throw new BusinessError(resp.code, resp.msg);
    }
    return resp.data;
} catch (e) {
    logger.error("Payment service call failed", {
        target: "payment-service",
        endpoint: "POST /v1/pay",
        traceId: ctx.traceId,
        request: { orderId, amount },
        error: { message: e.message, stack: e.stack },
        durationMs: Date.now() - start,
        orderId,
        userId: ctx.userId,
    });
    throw e;
}

// ❌ 错误：吞掉异常 / 只打 WARN / 无业务上下文
try {
    return await paymentClient.pay({ orderId, amount });
} catch (e) {
    logger.warn("payment failed");  // 级别错 + 无上下文 + 无 traceId + 无耗时
    return null;                     // 静默兜底，排查时毫无线索
}
```

**🔴 降级兜底逻辑 WARN 日志规则（硬规则）**

```
任何降级/兜底逻辑（fallback）必须打 WARN 日志，缺一不可：

├── 触发条件：代码进入「A 失败 → 走 B 兜底」的任何分支
├── 日志级别：WARN（不得降为 INFO/DEBUG，不得静默）
├── 必须字段：
│   ├── 降级原因（为什么触发降级：原始异常/不可用信号）
│   ├── 降级前方案（原本期望走的路径）
│   ├── 降级后方案（实际执行的兜底路径）
│   └── 业务上下文（trace_id / 用户 ID / 业务标识）
└── 评审门禁：Code Review 时，所有 fallback/catch-and-continue
    代码路径必须验证是否有 WARN 日志，缺失即阻塞

🎯 目的：降级是「正确但不正常」的路径，必须可观测、可告警、可追溯。
       静默降级 = 掩盖问题 = 生产事故来源。
```

**示例**：
```javascript
// ✅ 正确：降级逻辑 + WARN 日志
try {
    result = await primaryService.call(req);
} catch (e) {
    logger.warn("Primary service failed, falling back to secondary", {
        reason: e.message,
        from: "primary-service",
        to: "secondary-service",
        traceId: ctx.traceId,
        userId: ctx.userId,
    });
    result = await secondaryService.call(req);
}

// ❌ 错误：静默降级
try {
    result = await primaryService.call(req);
} catch (e) {
    result = await secondaryService.call(req);  // 无日志，问题无法追溯
}

// WARN - 非预期但可处理
if (user == null) {
    logger.warn("User not found, using default", { userId, default: "guest" });
    user = defaultUser;
}

// ERROR - 异常情况
try {
    await paymentService.charge(amount);
} catch (e) {
    logger.error("Payment failed", { error: e, userId, amount });
    throw e;
}
```

---

## 五、数据库迁移规范

> Schema 的当前设计（ER 图、表结构）记录在 ARCHITECTURE.md 的 📎 database-schema.md 中。
> 本章定义的是 **变更 schema 的操作规范**。

### 迁移文件规则

```
📁 迁移文件位置：
└── {项目路径}/migrations/   （或项目约定的迁移目录）

📄 命名规范：
└── {时间戳}_{操作描述}.{扩展名}
    ├── 示例：20260312_add_user_email_index.sql
    ├── 示例：20260312_create_orders_table.sql
    └── 时间戳格式：YYYYMMDD 或 YYYYMMDDHHmmss（按项目框架约定）
```

### 强制要求

```
🔴 必须遵守：
├── 每次 schema 变更必须有迁移文件，禁止手动改库
├── 迁移必须可逆：提供 up（执行）和 down（回滚）
├── 迁移文件提交前必须在本地/Docker 环境验证通过
├── TECH.md 中必须声明是否涉及 schema 变更
│   └── 涉及 → 列出变更内容（新增表/字段/索引/约束）
├── 迁移完成后同步更新 ARCHITECTURE.md → database-schema.md
├── 破坏性变更（删列/改类型/删表）必须在 TECH.md 中标注风险
└── 🔴 跨子项目 Schema 同步（新增/修改/删除列时必查）：
    ├── TECH.md 必须包含「数据库变更 → Schema 影响分析」章节（模板见 templates/tech.md）
    ├── 影响分析来源：database-schema.md「Model/Struct 映射」表 + grep 全项目代码
    ├── 核对 Struct 字段列表与数据库列完全一致（字段名 + 类型 + 可空性）
    ├── 核对所有引用该 Struct 的 SQL 查询列列表与字段匹配（缺列 → ORM 报错 → 500）
    ├── 架构师技术 Review 独立验证影响分析完整性（不依赖 RD 自查）
    ├── 架构师 Code Review 对照影响分析表逐项验证代码变更
    └── 变更完成后同步更新 database-schema.md（Model 映射表 + SQL 引用点 + 变更记录）

❌ 禁止：
├── 手动连线上数据库执行 DDL
├── 在迁移文件中包含业务数据操作（DML 和 DDL 分离）
├── 迁移文件提交后再修改（已执行的迁移不可变）
└── 不写 down 回滚脚本
```

### Schema 变更链条术语对照

| 阶段 | Agent 文件 | 使用术语 | 验证重点 | database-schema.md 操作 |
|------|-----------|---------|---------|------------------------|
| TECH.md 编写 | — | Schema 影响分析 | 列出所有受影响 Model/Struct 和 SQL | — |
| Blueprint Stage 架构师方案评审 | roles/rd.md | Schema 影响分析完整性 | 验证分析是否遗漏（独立 grep 对照） | 🔴 更新设计层（表结构、ER 图、设计原则） |
| RD 开发 | rd-develop.md | Schema 同步验证 | 代码是否已按影响分析表同步 | — |
| 架构师 Code Review | arch-code-review.md | Schema 同步验证 | 代码变更是否与影响分析表一致 | 🔴 补充实现层（Model 映射、SQL 引用点） |
| 集成测试 | integration-test.md | 迁移 + ORM 映射验证 | 运行时验证迁移可执行 + ORM/SQL 映射正确性 | — |

> 📎 各阶段术语不同是因为验证角度不同，但校验基准统一为 TECH.md「Schema 影响分析」表。
> 📎 database-schema.md 两阶段更新：设计层（Tech Review 后写入）→ 实现层（Code Review 后补充）。

### 迁移与开发流程的衔接

```
TECH.md 声明 schema 变更 + 填写「Schema 影响分析」表
    ↓
架构师技术评审 → 检查迁移方案合理性 + 🔴 独立验证影响分析完整性
    ↓
🔴 架构师更新 database-schema.md 设计层（表结构 + ER 图 + 设计原则）
    ↓
RD 编写迁移文件 + 同步所有受影响 Model/Struct/SQL + 单元测试
    ↓
RD 自查 → 对照影响分析表逐项确认 + 验证 up/down 可执行
    ↓
Code Review → 🔴 对照影响分析表逐项验证代码变更 + 确认迁移文件
    ↓
🔴 架构师补充 database-schema.md 实现层（Model 映射表 + SQL 引用点）
    ↓
集成测试 → 🔴 迁移验证（ORM 映射正确性 + 跨子项目 Model 可查询）
    ↓
PMO 完成报告 → 确认 database-schema.md 已完整同步（设计层 + 实现层）
```

---

## 六、API 版本管理规范

> API 的当前接口清单记录在 ARCHITECTURE.md 的 📎 api-design.md 中。
> 本章定义的是 **API 版本变更的操作规范**。

### 版本策略

```
📌 URL Path 版本（默认策略）：
└── /api/v{N}/...
    ├── v1: /api/v1/users
    ├── v2: /api/v2/users
    └── 项目可在 KNOWLEDGE.md 中声明使用其他策略（如 Header 版本），声明后以 KNOWLEDGE.md 为准
```

### 何时需要升版本

```
🔴 必须升版本号（Breaking Change）：
├── 删除已有字段或接口
├── 修改字段类型或含义
├── 修改响应结构
├── 修改认证/鉴权方式
└── 变更业务语义（同一接口返回不同含义的数据）

✅ 不需要升版本（Non-Breaking Change）：
├── 新增可选字段
├── 新增接口
├── 修复 Bug（不改变接口契约）
└── 性能优化（不改变接口行为）
```

### 旧版本废弃流程

```
Step 1: 标记 Deprecated
├── 在旧版本接口响应 Header 中添加 Deprecation 标记
├── 在 api-design.md 中标注版本状态为「⚠️ 废弃中」
└── TECH.md 中说明废弃原因和新版本迁移指引

Step 2: 通知期
├── 保持旧版本可用，设定废弃截止日期
└── 截止日期记录在 api-design.md 版本清单中

Step 3: 下线
├── 确认无调用方使用旧版本
├── 在 api-design.md 中标注版本状态为「❌ 已下线」
└── 移除旧版本代码（可选，保留也可）
```

### TECH.md 声明要求

```
📋 涉及 API 变更的 TECH.md 必须包含：
├── 是否为 Breaking Change → 是/否
├── Breaking Change → 新版本号是什么（如 v1 → v2）
├── 影响的接口清单
├── 旧版本迁移方案（如有调用方）
└── 完成后同步更新 api-design.md
```
