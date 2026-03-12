# Teamwork 开发规范

> 本文件定义所有开发相关的技术规范，RD 必须遵守。

---

## 一、测试规范

### 核心原则（前后端通用）

```
❌ 禁止：先写实现代码再补测试
❌ 禁止：跳过测试直接提交代码
✅ 必须：先写测试，再写实现（测试先行）
✅ 必须：测试失败后才写实现代码
✅ 必须：每个 TC 用例都有对应测试
```

---

### 后端测试规范（TDD 强制执行）

**覆盖率要求**: > 80%

#### 开发流程（Red-Green-Refactor）

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

#### 测试命名规范

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

### 前端测试规范（测试先行，强制执行）

**覆盖率要求**: > 70%

#### 测试分层

| 层级 | 覆盖目标 | 工具示例 | 要求 |
|------|----------|----------|------|
| **单元测试** | 工具函数、Hooks、纯逻辑（非 UI） | Jest, Vitest | 必须覆盖，覆盖率 > 70% |
| **E2E 测试** | 关键用户流程、页面交互 | Playwright, Cypress | P0 流程必须覆盖 |
| **组件测试** | UI 组件渲染、交互 | Testing Library | 可选，按需补充 |

#### 必须测试的场景

```
✅ 必须覆盖：
├── 表单验证逻辑（输入校验、错误提示）
├── 状态管理（store/context 的状态变更）
├── API 调用和错误处理（loading、error、success 状态）
├── 路由守卫/权限控制
├── 关键业务流程（登录、支付、提交订单等）
├── 条件渲染逻辑（显示/隐藏、启用/禁用）
└── 用户交互（点击、输入、拖拽等关键操作）
```

#### 可选测试（非强制）

```
⚪ 可选：
├── 纯展示组件（无逻辑，只接收 props 渲染）
├── 第三方组件简单封装
├── 样式/动画效果
└── 静态页面
```

#### 前端 TDD 流程

**Step 1: 根据 TC 写测试（必须先写）**
```typescript
// ❌ 组件还不存在，测试先行
describe('LoginForm', () => {
  it('should show error when email is empty', () => {
    render(<LoginForm />);
    fireEvent.click(screen.getByRole('button', { name: /登录/i }));
    expect(screen.getByText(/邮箱不能为空/i)).toBeInTheDocument();
  });

  it('should show error when password is less than 6 characters', () => {
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/密码/i), { target: { value: '123' } });
    fireEvent.click(screen.getByRole('button', { name: /登录/i }));
    expect(screen.getByText(/密码至少6位/i)).toBeInTheDocument();
  });

  it('should call onSubmit with form data when valid', () => {
    const onSubmit = jest.fn();
    render(<LoginForm onSubmit={onSubmit} />);
    fireEvent.change(screen.getByLabelText(/邮箱/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/密码/i), { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: /登录/i }));
    expect(onSubmit).toHaveBeenCalledWith({ email: 'test@example.com', password: '123456' });
  });
});
```

**Step 2: 运行测试，确认失败**
```bash
npm test -- LoginForm.test.tsx
# 3 个测试失败 ✅ (预期)
```

**Step 3: 实现组件，让测试通过**
```typescript
// 实现 LoginForm 组件...
```

**Step 4: 重构，保持测试通过**

#### 前端测试命名规范

```
✅ 正确：
├── describe('LoginForm', () => { ... })
├── it('should show error when email is empty', ...)
├── it('should disable submit button while loading', ...)
└── it('should redirect to home after successful login', ...)

❌ 错误：
├── test('test1', ...)
├── it('works', ...)
└── it('LoginForm', ...)
```

#### E2E 测试要求

```
P0 流程必须有 E2E 测试：
├── 用户注册流程
├── 用户登录流程
├── 核心业务流程（如下单、支付）
└── 权限相关流程（如管理员操作）

E2E 测试文件位置：
└── e2e/
    ├── login.spec.ts
    ├── register.spec.ts
    └── checkout.spec.ts
```

---

### TDD 检查清单（提交前必查）

```
📋 TDD 自检：
├── [ ] 测试代码先于实现代码编写
├── [ ] 每个 TC 用例都有对应测试
├── [ ] 覆盖率达标（后端 > 80%，前端 > 70%）
├── [ ] 测试可独立运行（无外部依赖）
├── [ ] 测试命名清晰
├── [ ] 包含边界条件测试
├── [ ] 包含异常场景测试
└── [ ] 所有测试通过
```

---

### 集成测试规范（后端 API）

#### 触发条件

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

#### 测试内容

##### 1. API 接口验证

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

##### 2. 数据库验证

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

##### 3. 测试数据管理

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

##### 4. 环境依赖部署（Docker 优先）

```
📋 集成测试环境准备（按优先级执行）：

Step 1: 检测 Docker 环境
├── 执行 `docker --version` 和 `docker compose version`
├── ✅ 已安装 → Step 2
└── ❌ 未安装 → ⏸️ 提示用户安装 Docker：
    ├── macOS: 「请安装 Docker Desktop: https://www.docker.com/products/docker-desktop」
    ├── Linux: 「请执行: curl -fsSL https://get.docker.com | sh」
    └── 用户确认安装完成后 → 重新检测 → Step 2

Step 2: 检查 docs/integration_test/ 目录
├── ✅ 已有 docker-compose.test.yml → 使用已有配置
│   └── `docker compose -f docs/integration_test/docker-compose.test.yml up -d`
└── ❌ 没有 → Step 3

Step 3: 根据 TECH.md 中的技术栈自动生成测试环境
├── 创建 docs/integration_test/ 目录结构
├── 分析依赖项（数据库类型、Redis、MQ 等）
├── 生成 docker-compose.test.yml，包含：
│   ├── 数据库服务（MySQL/PostgreSQL/MongoDB 等）
│   ├── 缓存服务（Redis 等，如需要）
│   ├── 消息队列（RabbitMQ/Kafka 等，如需要）
│   ├── 端口映射、健康检查
│   └── volumes 挂载前置数据目录（如 ./pg:/docker-entrypoint-initdb.d）
├── 生成前置数据文件（init.sql / seed.redis 等）
├── 写入 docs/integration_test/
└── `docker compose -f docs/integration_test/docker-compose.test.yml up -d`

Step 4: 等待服务就绪 + 加载前置数据
├── 健康检查（最多等待 60 秒）
├── ✅ 全部就绪：
│   ├── 数据库：init.sql 通过 volume 挂载自动执行（Docker 首次启动时）
│   ├── Redis：`redis-cli < docs/integration_test/redis/seed.redis`（如有）
│   ├── MongoDB：`mongosh < docs/integration_test/mongo/init.js`（如有）
│   ├── 将连接信息写入 docs/RESOURCES.md
│   └── → 进入测试
└── ❌ 启动失败 → 输出日志 → ⏸️ 用户确认处理方式

⚠️ Docker 不可用时的降级方案：
├── 检查 docs/RESOURCES.md 是否有远程环境配置
├── 有 → 使用远程环境
└── 无 → ⏸️ 暂停，请求用户提供：
    ├── 数据库连接信息（host/port/user/password）
    ├── 第三方服务配置（如需要）
    └── 测试账号（如无法自主注册）
    └── 用户提供后 → 写入 docs/RESOURCES.md → 后续自动复用
```

#### 集成测试报告

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

#### 失败处理流程

```
集成测试失败：
    ↓
判断失败类型：
    ├── 代码 Bug → RD 自动修复 → 重新测试
    ├── Docker 容器异常 → `docker compose logs` 排查 → 重启容器 → 重新测试
    ├── 环境问题 → 尝试自动恢复 → 重新测试
    ├── 需求理解偏差 → ⏸️ 用户确认 → 决定修复方案
    └── 测试用例问题 → ⏸️ 用户确认 → 调整用例或跳过

测试完成后清理（可选）：
    ├── `docker compose -f docker-compose.test.yml down` 停止并移除容器
    └── 保留容器供后续测试复用（默认保留）
```

---

## 二、代码架构规范

### 架构分层原则

```
✅ 必须遵守：
├── 严格遵循项目现有的分层架构（参考 ARCHITECTURE.md）
├── 每一层只做该层该做的事，不越界
├── 依赖方向：上层依赖下层，禁止反向依赖
└── 层与层之间通过接口/协议通信，不直接依赖实现

❌ 禁止：
├── 一个类/文件承担过多职责（God Class）
├── 业务逻辑写在 UI 层
├── 数据访问逻辑散落在各处
├── 工具方法和业务逻辑混在一起
└── 命名模糊不清（如 Helper、Manager、Utils 包含大量不相关方法）
```

### 类/模块职责原则

```
✅ 单一职责：
├── 每个类/模块只负责一件事
├── 类名/文件名能清晰表达其职责
├── 如果一个类做了多件事，必须拆分
├── 方法长度适中，单个方法不超过 50 行
└── 复杂逻辑必须拆分为多个小方法
```

### 代码组织要求

```
📁 文件组织：
├── 相关功能放在同一目录/包下
├── 文件数量适中，单个目录不超过 15 个文件
├── 文件过多时按子功能拆分子目录
└── 公共代码提取到 shared/common 目录

📄 单文件要求：
├── 单个文件不超过 300 行（超过必须拆分）
├── 文件开头有简要说明（这个文件是做什么的）
├── 公开方法/接口放在文件顶部
├── 私有方法放在文件底部
└── 相关方法放在一起，按逻辑分组

📝 命名规范：
├── 类名：名词，表达「是什么」（UserService, PaymentRepository）
├── 方法名：动词，表达「做什么」（createUser, validatePayment）
├── 变量名：有意义，避免 a, b, temp 等无意义命名
└── 常量名：全大写下划线分隔（MAX_RETRY_COUNT）
```

### Review 友好度检查

```
📋 提交代码前自检：
├── [ ] 每个新增的类/文件职责是否单一清晰？
├── [ ] 类名/方法名是否能让 reviewer 一眼理解其作用？
├── [ ] 是否有超过 300 行的文件需要拆分？
├── [ ] 是否有超过 50 行的方法需要拆分？
├── [ ] 复杂逻辑是否有注释说明「为什么这样做」？
├── [ ] 是否遵循了项目现有的分层架构？
└── [ ] 新增代码是否放在了正确的层/目录下？
```

### 架构文档维护规则

> **维护责任人**：资深架构师（在架构师 Code Review Subagent 中执行）
> **文档位置**：`docs/architecture/{项目}/ARCHITECTURE.md`

```
❌ 禁止：
├── 跳过架构师 Code Review 就进入 QA 代码审查
├── 新增模块不在架构文档中说明
├── 架构调整不记录设计决策
└── 删除模块不更新架构文档

✅ 必须（架构师 Code Review 时执行）：
├── 审查代码后检查是否需要更新架构文档
├── 新增模块 → 在「核心模块说明」中添加
├── 架构调整 → 更新架构图 + 记录设计决策
├── 目录结构变化 → 更新「目录结构」章节
└── 进入 QA 代码审查前，架构文档必须是最新的
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
  "data": { "list": [...] },
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
⚠️ 必须打 WARN 日志：
├── 进入 else/default 等兜底分支
├── 参数为空或无效，使用默认值
├── 重试逻辑触发
├── 降级处理触发
├── 缓存未命中走数据库
└── 任何「理论上不应该走到」的代码路径

❌ 必须打 ERROR 日志：
├── 捕获到异常（即使已处理）
├── 外部服务调用失败
├── 数据校验失败
├── 业务规则冲突
└── 任何需要开发人员关注的异常情况
```

**示例**：
```javascript
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

## 五、RD 自查规范

> RD 开发完成后、提交 QA 审查前，必须完成自查并输出自查报告。

### 自查触发时机

```
RD 开发完成（测试通过）
    ↓
执行自查清单
    ↓
输出自查报告
    ↓
自查通过 → 进入 QA 代码审查
```

### 自查清单详解

#### 1. 架构合理性检查

```
📋 架构检查项：
├── 分层正确性
│   ├── 是否符合现有分层架构（参考 ARCHITECTURE.md）
│   ├── 业务逻辑是否在正确的层（不在 UI 层/数据层）
│   └── 依赖方向是否正确（上层依赖下层，无反向依赖）
├── 职责清晰性
│   ├── 每个类/模块职责是否单一
│   ├── 是否有 God Class（承担过多职责的类）
│   └── 类名/方法名是否清晰表达其职责
├── 设计合理性
│   ├── 是否有过度设计（不需要的抽象）
│   ├── 是否有设计不足（该抽象没抽象）
│   └── 扩展点是否合理
└── 文档同步
    └── 新增/修改的模块是否已更新到 ARCHITECTURE.md
```

#### 2. 规范遵守检查

```
📋 规范检查项：
├── 日志规范（参考「四、日志规范」）
│   ├── 请求入口/出口有 INFO 日志
│   ├── 异常场景有 ERROR 日志（含 stack）
│   ├── 非预期分支有 WARN 日志
│   ├── 外部服务调用有日志（含耗时）
│   └── 日志格式符合结构化日志规范
├── API 规范（参考「三、服务端 API 接口规范」）
│   ├── 响应格式正确（code/msg/data/extra）
│   ├── JSON key 使用 snake_case
│   └── 错误码定义合理
├── 测试规范（参考「一、测试规范」）
│   ├── 测试先于实现（检查 git 提交顺序）
│   ├── 覆盖率达标（后端 > 80%，前端 > 70%）
│   └── 测试命名符合 Scenario 描述
└── 代码规范（参考「二、代码架构规范」）
    ├── 单文件 < 300 行
    ├── 单方法 < 50 行
    ├── 命名清晰有意义
    └── 复杂逻辑有注释说明「为什么」
```

#### 3. 性能检查

```
📋 性能检查项：
├── 数据库性能
│   ├── 是否有 N+1 查询问题
│   ├── 查询是否使用了合适的索引
│   ├── 大数据量是否有分页/限制
│   └── 是否有不必要的全表扫描
├── 代码性能
│   ├── 是否有不必要的循环或重复计算
│   ├── 是否有可缓存的计算结果未缓存
│   ├── 热点路径是否有缓存考虑
│   └── 是否有潜在的内存泄漏风险
├── 并发性能
│   ├── 共享资源是否有竞争条件
│   ├── 锁的粒度是否合理
│   └── 是否有死锁风险
└── 网络性能
    ├── 是否有不必要的网络请求
    ├── 是否可以批量处理减少请求次数
    └── 超时时间是否合理设置
```

#### 4. 安全检查

```
📋 安全检查项：
├── 注入防护
│   ├── SQL 查询是否使用参数化（防 SQL 注入）
│   ├── 命令执行是否有输入校验（防命令注入）
│   └── 模板渲染是否转义（防 XSS）
├── 认证授权
│   ├── 接口是否有权限校验
│   ├── 权限校验是否完整（不能只在前端校验）
│   └── 敏感操作是否有二次确认
├── 数据安全
│   ├── 敏感数据是否脱敏/加密存储
│   ├── 日志中是否泄露敏感信息
│   ├── 错误信息是否暴露系统细节
│   └── 是否有硬编码的密钥/密码
└── 输入校验
    ├── 用户输入是否有长度/格式限制
    ├── 文件上传是否有类型/大小限制
    └── 是否有越权访问风险（如 ID 枚举）
```

### 自查报告模板

```markdown
## RD 自查报告（F{编号}-{功能名}）

### 检查结果汇总
| 维度 | 检查项 | 通过 | 问题 |
|------|--------|------|------|
| 架构合理性 | 4 | 4 | 0 |
| 规范遵守 | 8 | 7 | 1 |
| 性能检查 | 6 | 6 | 0 |
| 安全检查 | 6 | 6 | 0 |
| **合计** | **24** | **23** | **1** |

### 问题详情
| 维度 | 问题 | 严重程度 | 处理方式 |
|------|------|----------|----------|
| 规范遵守 | 用户查询接口缺少 INFO 日志 | 低 | 已修复 |

### 自查结论
✅ 自查通过，可进入 QA 代码审查
```

### 自查结果处理

```
自查结果：
├── 全部通过 → ✅ 进入 QA 代码审查
├── 有低风险问题
│   ├── 可快速修复 → 修复后重新自查
│   └── 有正当理由 → 记录到报告，继续
└── 有高风险问题
    └── 必须修复 → 修复后重新自查
```

---

## 六、QA 代码审查检查项

### TDD 规范检查

```
📋 TDD 规范检查：
├── 测试先于实现: ✅/❌ (检查 git 提交顺序)
├── 测试覆盖率: XX% (后端 > 80%，前端 > 70%)
├── 测试可独立运行: ✅/❌
├── 测试命名规范: ✅/❌
└── 边界条件覆盖: ✅/❌
```

### 架构文档检查

```
📋 架构文档检查：
├── 架构文档是否存在: ✅/❌
├── 架构文档是否最新: ✅/❌ (检查「最后更新」日期)
├── 新增模块是否已记录: ✅/❌
├── 目录结构是否准确: ✅/❌
└── 分层职责是否清晰: ✅/❌
```

### 实现完整性检查

```
📋 实现完整性：
| 需求项 | 状态 | 代码位置 |
|--------|------|----------|
| xxx    | ✅   | src/xxx  |

完整性: X/Y (XX%)
```
