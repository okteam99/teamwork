# TC 模板

> 🔴 v7.3 契约化更新：TC 文件头必须包含 YAML frontmatter，将 `tests[]` 结构化为机器可读。
> 每条 test 通过 `covers_ac[]` 字段反查到 PRD 的 AC id。
> 机器校验脚本 `{SKILL_ROOT}/templates/verify-ac.py` 会校验 PRD 每条 AC 至少有一个 test 覆盖。直接调用：
> `python3 {SKILL_ROOT}/templates/verify-ac.py {Feature 目录}`

## TC.md（BDD/Gherkin 格式）

```markdown
---
feature_id: "{缩写}-F{编号}-{功能名}"
status: draft  # draft | pending_review | confirmed
tests:
  - id: T-001
    file: tests/unit/auth/login.test.ts
    function: test_AC1_email_login_happy_path
    covers_ac: ["AC-1"]
    level: unit  # unit | integration | api-e2e | fe-e2e
    priority: P0
  - id: T-002
    file: tests/unit/auth/login.test.ts
    function: test_AC2_password_wrong_shows_red
    covers_ac: ["AC-2"]
    level: unit
    priority: P0
  - id: T-003
    file: tests/integration/auth.test.ts
    function: test_AC1_integration
    covers_ac: ["AC-1"]
    level: integration
    priority: P0
---

# {功能名称} - 测试用例

## 状态
草稿 | 待评审 | 已确认

---

## Feature: {功能名称}

作为 {角色}
我希望 {功能}
以便 {价值}

---

## 需求覆盖矩阵

> 🔴 v7.3：本节是 frontmatter `tests[]` 的人读视图。
> 反查 PRD.md frontmatter 的 `acceptance_criteria[]`，确保每条 AC 都在"用例 ID"列有至少 1 个对应测试。
> 机器校验：`python3 {SKILL_ROOT}/templates/verify-ac.py {Feature}` 自动检查覆盖完整性。

| AC ID（PRD）| 需求描述 | 优先级 | 覆盖测试（对应 frontmatter `tests[].id`）| 状态 |
|-------------|---------|--------|------------------------------------------|------|
| AC-1 | 邮箱登录 | P0 | T-001, T-003 | ✅ |
| AC-2 | 密码错误提示 | P0 | T-002 | ✅ |

覆盖率: {覆盖 AC 数} / {PRD AC 总数} ({百分比})

---

## 测试场景

### Scenario: TC-001 {场景描述}
**优先级**: P0 | P1 | P2
**类型**: 功能 | 边界 | 异常
**测试层级**: unit | integration | api-e2e | fe-e2e

\`\`\`gherkin
Given {前置条件1}
  And {前置条件2，可选}
When {用户操作1}
  And {用户操作2，可选}
Then {预期结果1}
  And {预期结果2，可选}
\`\`\`

**数据库验证**（后端接口需填写）:
| 表名 | 验证项 | 预期值 |
|------|--------|--------|
| users | last_login_at | 更新为当前时间 |

---

### Scenario: TC-002 {场景描述}
**优先级**: P0
**类型**: 功能
**测试层级**: integration

\`\`\`gherkin
Given 用户 "test@example.com" 已注册且密码为 "123456"
  And 用户处于登录页面
When 用户输入邮箱 "test@example.com"
  And 用户输入密码 "123456"
  And 用户点击登录按钮
Then 用户应该跳转到首页
  And 用户应该看到欢迎信息 "你好，张三"
\`\`\`

**数据库验证**:
| 表名 | 验证项 | 预期值 |
|------|--------|--------|
| user_sessions | 新记录创建 | session_id 存在 |
| users | last_login_at | 更新 |

---

### Scenario: TC-003 {异常场景}
**优先级**: P0
**类型**: 异常
**测试层级**: api-e2e

\`\`\`gherkin
Given 用户 "test@example.com" 已注册
When 用户输入错误密码 "wrong_password"
  And 用户点击登录按钮
Then 用户应该看到错误提示 "密码错误"
  And 用户应该仍在登录页面
  And 登录失败次数应该增加 1
\`\`\`

**API 验证**:
| 接口 | 预期状态码 | 预期 code |
|------|-----------|-----------|
| POST /api/v1/login | 401 | AUTH_FAILED |

---

### Scenario Outline: TC-004 {参数化场景}
**优先级**: P1
**类型**: 边界

\`\`\`gherkin
Given 用户处于注册页面
When 用户输入密码 "<password>"
  And 用户点击注册按钮
Then 用户应该看到 "<result>"

Examples:
| password | result |
| 12345 | 密码至少6位 |
| 123456 | 注册成功 |
| 123456789012345678901 | 密码最多20位 |
\`\`\`

---

## UI 还原检查（如有 UI）

| 检查点 | 设计稿标准 | 状态 |
|--------|------------|------|
| 按钮颜色 | #1890ff | ⬜ |
| 字体大小 | 14px | ⬜ |
| 间距 | 16px | ⬜ |

---

## E2E 端到端验收（QA Write Cases 阶段必须填写此章节）

### API E2E 判断（QA 必填，默认必须执行）

| 项目 | 内容 |
|------|------|
| 是否需要 API E2E | ✅ 需要 / ⏭️ 不适用（原因：{如"纯前端改动，无 API 行为变化"}） |
| 原因 | {如：功能对外暴露 API，必须验证真实请求链路、响应、副作用和数据库状态} |

> 🔴 API E2E 是强制验收层。只要功能存在对外 API 或由 API 驱动的业务链路，默认必须执行。
> 只有纯前端、纯文案、纯样式且无 API 行为变化的需求，才能标注「不适用」，并写明原因。
> PMO 在项目集成测试通过后读取此章节，决定是否进入 API E2E 阶段。

### API E2E 前置条件（API E2E 需要时填写）

| 条件类型 | 具体内容 | 获取方式 |
|----------|----------|----------|
| 测试账号 | {如：需要一个已注册用户账号} | {如：用户提供 / 测试脚本自动创建} |
| Token/凭证 | {如：需要有效的 access_token} | {如：通过登录接口获取，占位符 \`${ACCESS_TOKEN}\`} |
| 测试数据 | {如：需要至少 3 条商品记录} | {如：seed 脚本 \`npm run seed:test\`} |
| 服务地址 | {如：API 需要在 localhost:3000 可访问} | {如：\`docker compose up\`} |
| 第三方依赖 | {如：需要支付 sandbox 环境} | {如：用户提供 sandbox API key} |

> 获取方式标注 \`用户提供\` 的项 → PMO 在 API E2E 前置检查阶段一次性向用户收集。
> 获取方式标注脚本/自动的项 → API E2E Subagent 自行执行。

### API E2E Scenarios

#### API-E2E-001: {完整 API 业务场景描述}
**执行方式**: api（curl/httpie）

\`\`\`gherkin
Given {真实环境前置状态}
When {API 调用序列}
Then {端到端预期结果}
\`\`\`

**验证点**:
| 验证类型 | 验证内容 | 预期值 |
|----------|----------|--------|
| 响应 | {如：响应 status=200，body.code=SUCCESS} | |
| 数据库 | {如：orders 表新增记录，status=paid} | |
| 副作用 | {如：邮件发送队列有新消息} | |

---

### Browser E2E 判断（有 UI 时填写）

| 项目 | 内容 |
|------|------|
| 是否需要Browser E2E | ✅ 需要 / ⏭️ 可跳过（原因：{如"本次仅接口层改动，无前端交互变化"}） |
| 用户是否可选择跳过 | 是（PMO 在执行前询问） |

> Browser E2E 指 AI 浏览器对真实页面做黑盒验证。
> Browser E2E 不是默认强制项，但涉及关键 UI 流程、核心转化链路或高风险交互时，QA 应明确建议执行。

### Browser E2E 前置条件（Browser E2E = 需要时填写）

| 条件类型 | 具体内容 | 获取方式 |
|----------|----------|----------|
| 页面地址 | {如：登录页 /orders/new} | {如：本地 dev server / 测试环境 URL} |
| 测试账号 | {如：运营账号 / 普通用户账号} | {如：用户提供 / seed 脚本自动创建} |
| 浏览器前置状态 | {如：需清空 cookie / 需已登录} | {如：脚本处理 / QA 手动步骤} |

### Browser E2E Scenarios

#### FE-E2E-001: {完整前端业务场景描述}
**执行方式**: browser（AI 浏览器操作）

\`\`\`gherkin
Given {真实页面前置状态}
When {用户完整操作序列}
Then {页面可观测结果}
\`\`\`

**验证点**:
| 验证类型 | 验证内容 | 预期值 |
|----------|----------|--------|
| 页面 | {如：出现成功提示、按钮状态变化、页面跳转} | |
| 数据回显 | {如：页面展示新建订单编号} | |
| 交互状态 | {如：loading 消失、按钮恢复可点击} | |

---

## 实现完整性报告（代码审查时填写）

| 需求项 | 状态 | 代码位置 | 测试位置 |
|--------|------|----------|----------|
| 正常登录 | ✅ | src/auth/login.ts | tests/auth/login.test.ts |
| 密码错误 | ✅ | src/auth/login.ts | tests/auth/login.test.ts |

完整性: X/Y (XX%)

---

## TDD 检查（代码审查时填写）

- [ ] 测试先于实现（检查 git 提交顺序）
- [ ] 后端覆盖率 > 80%
- [ ] 前端覆盖率 > 70%
- [ ] 测试可独立运行
- [ ] 测试命名符合 Scenario 描述
- [ ] 边界条件已覆盖
- [ ] 异常场景已覆盖

---

## 变更记录

| 日期 | 变更 |
|------|------|
```

### Gherkin 语法速查

```
关键字说明：
├── Feature     - 功能描述（一个 TC 文件一个 Feature）
├── Scenario    - 具体测试场景
├── Given       - 前置条件（系统初始状态）
├── When        - 用户操作（触发行为）
├── Then        - 预期结果（断言）
├── And         - 连接多个 Given/When/Then
├── But         - 否定条件
└── Scenario Outline + Examples - 参数化测试

书写原则：
├── 用业务语言，不写技术实现
├── 一个 Scenario 只测一件事
├── Given 描述「是什么状态」，不是「怎么到达」
├── When 描述「做什么」，不是「怎么做」
├── Then 描述「应该怎样」，可观测可验证
└── 避免 UI 细节（如「点击第3个按钮」）
```

---

## TC-REVIEW.md

```markdown
# {功能名称} - 测试用例评审记录

## 当前状态
🔄 第 X 轮评审中 | ✅ 已通过

## PM 评审（需求角度）
| ID | 用例 | 问题 | 类型 | 用户确认 | 状态 |
|----|------|------|------|----------|------|
|    |      |      | 遗漏/不清晰/错误 | 修改/忽略 | 待处理/已修改 |

PM 结论: ✅ 通过 / ❌ 有问题

## RD 评审（技术角度）
| ID | 用例 | 问题 | 类型 | 用户确认 | 状态 |
|----|------|------|------|----------|------|
|    |      |      | 不可行/遗漏/建议 | 修改/忽略 | 待处理/已修改 |

RD 结论: ✅ 通过 / ❌ 有问题

## Designer 评审（UI 角度，如需 UI）
| ID | 用例 | 问题 | 类型 | 用户确认 | 状态 |
|----|------|------|------|----------|------|
|    |      |      | 状态遗漏/交互缺失/视觉验证 | 修改/忽略 | 待处理/已修改 |

Designer 评审维度：
├── 状态覆盖：加载态/空态/错误态是否有用例？
├── 交互验证：关键交互流程是否有用例？
├── 视觉验证：UI 还原检查点是否完整？
└── 特殊状态：设计稿中的特殊状态是否覆盖？

Designer 结论: ✅ 通过 / ❌ 有问题 / ➖ 不需要（非 UI 功能）

## 待用户确认
以上问题需要您确认：
- 回复「修改」+ 问题 ID → QA 将修改用例
- 回复「忽略」+ 问题 ID → 标记为已忽略
- 回复「全部修改」→ 修改所有问题
- 回复「讨论」+ 问题 ID → 记录到决策文档

## 评审历史

### 第 1 轮 - [日期]
- PM 问题: X 个
- RD 问题: X 个
- Designer 问题: X 个（如需 UI）
- 用户确认: 修改 X / 忽略 X
- 结论: 继续修改
```
