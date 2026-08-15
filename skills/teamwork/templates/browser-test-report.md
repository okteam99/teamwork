---
feature_id: "{PREFIX}-{F|B|M}{NNN}-{kebab-name}"
author: QA + Designer
status: draft  # draft | confirmed
ui_ref: UI.md (vX.Y)
prd_ref: PRD.md (vX.Y)
test_run_at: "{ISO 8601 UTC}"
browser_automation: playwright  # 🔴 默认首选 playwright(用户拍板)· puppeteer | selenium 仅当项目已有该基建(复用 · 一致性优先)
replay_entry: "npx playwright test tests/e2e/browser/"  # 🔴 可重放入口(关键路径必填 · 一条可直接跑的命令);探索性/一次性验收填 n/a —— 空着 = 没想过要不要重放
viewport:
  width: 1440
  height: 900
url_base: "{http://localhost:3000 / https://staging.example.com}"
screenshots_count: 0
ac_coverage:
  total: 0
  with_screenshot: 0
revision_history:
  - version: v0.1
    date: "{YYYY-MM-DD}"
    author: QA
    summary: 首版起草
---

# {功能名} - Browser E2E Test Report

> 位置：`{Feature 目录}/BROWSER-TEST-REPORT.md`
> 🟢 **本文是 teamwork browser_e2e-stage 产物** · 起草模板 = `{SKILL_ROOT}/templates/browser-test-report.md`
> 🔴 **截图必含浏览器 chrome + URL bar** · 不裁剪(SOP 截图红线 · 见 [stages/browser-e2e-stage.md](../stages/browser-e2e-stage.md))

---

## §1 测试范围

| 项 | 内容 |
|---|---|
| 浏览器自动化 | {Playwright(默认首选)/ 复用既有 Puppeteer / Selenium 基建} |
| 浏览器版本 | {Chromium 120.x / WebKit 17.x} |
| viewport | 1440 × 900(桌面)/ 375 × 812(移动) |
| URL base | {http://localhost:3000} |
| 测试账号 | {test@example.com / pwd=...} |
| 浏览器前置状态 | {清空 cookie / 已登录} |

---

## §2 测试场景

> 🔴 每 AC 一组截图 · happy path + ≥1 边界 · 不漏关键状态。

### Scenario: FE-E2E-001 · {场景描述}

**对应 AC**:AC-1, AC-3
**优先级**:P0
**类型**:happy path

#### 执行步骤

```text
1. 打开 {url}
2. 输入 {字段} = {值}
3. 点击 {按钮}
4. 等待 {selector / 网络空闲}
5. 验证 {可观测结果}
```

#### 截图引用

| # | 步骤 | 文件 | 验证点 |
|---|---|---|---|
| 1 | 进入登录页 | `screenshots/fe-e2e-001-step1-login-page.png` | URL = /login · 表单可见 |
| 2 | 输入邮箱+密码 | `screenshots/fe-e2e-001-step2-filled.png` | 表单填充 · 按钮 enabled |
| 3 | 点击登录后跳转首页 | `screenshots/fe-e2e-001-step3-home.png` | URL = /home · welcome 文案 |

#### 异常发现

| ID | 现象 | 截图 | 严重度 | 决定 |
|---|---|---|---|---|
| - | (无) | - | - | - |

---

### Scenario: FE-E2E-002 · {边界场景描述}

**对应 AC**:AC-2(密码错误)
**优先级**:P0
**类型**:edge case

#### 执行步骤

```text
1. 打开 /login
2. 输入正确邮箱 + 错误密码
3. 点击登录
4. 验证错误提示
```

#### 截图引用

| # | 步骤 | 文件 | 验证点 |
|---|---|---|---|
| 1 | 错误密码提交 | `screenshots/fe-e2e-002-step1-wrong-pwd.png` | 错误提示「密码错误」可见 |
| 2 | 仍在登录页 | `screenshots/fe-e2e-002-step2-still-login.png` | URL = /login(未跳转) |

---

## §3 AC↔截图覆盖矩阵

| AC ID | 描述 | happy path 截图 | 边界截图 | 状态 |
|---|---|---|---|---|
| AC-1 | 邮箱登录 | fe-e2e-001 | - | ✅ |
| AC-2 | 密码错误提示 | - | fe-e2e-002 | ✅ |
| AC-3 | 登录后跳首页 | fe-e2e-001 | - | ✅ |

覆盖率:N / N(100%)

---

## §4 flaky / retry 处理

> 🔴 retry 必含 log + 失败截图 · 不静默成功(SOP)

| Scenario | 重试次数 | 失败截图 | 失败 log 摘录 | 最终结果 |
|---|---|---|---|---|
| FE-E2E-001 | 0 | - | - | ✅ pass |
| FE-E2E-002 | 1 | `screenshots/fe-e2e-002-retry1-fail.png` | `Timeout 5000ms exceeded` | ✅ pass(第 2 次) |

---

## §5 截图清单(全 inventory)

> screenshots/ 目录下所有文件 · 防漏

```text
screenshots/
├── fe-e2e-001-step1-login-page.png    (148 KB · 1440×900)
├── fe-e2e-001-step2-filled.png        (152 KB · 1440×900)
├── fe-e2e-001-step3-home.png          (203 KB · 1440×900)
├── fe-e2e-002-step1-wrong-pwd.png     (149 KB · 1440×900)
├── fe-e2e-002-step2-still-login.png   (149 KB · 1440×900)
└── fe-e2e-002-retry1-fail.png         (151 KB · 1440×900)

共 6 张 · 总 952 KB
```

---

## §6 已知异常 / 不阻塞项

| ID | 现象 | 截图 | 严重度 | 决定 | 跟踪 |
|---|---|---|---|---|---|
| - | (无) | - | - | - | - |

---

## §7 评审记录

| 日期 | 评审人 | 结论 | 备注 |
|---|---|---|---|
| {YYYY-MM-DD} | PM(看截图) | ✅ pass | - |

---

