# 前端开发规范

> 前端 RD 必须遵守。通用规范见 📎 [common.md](./common.md) · TDD 流程唯一权威源 📎 [tdd.md](./tdd.md)。
> Subagent 加载指引：前端子项目加载本文件 + tdd.md + common.md，无需加载 backend.md。
> 📎 选型对比 / 配置样例 / 代码示例在 [frontend-guide.md](./frontend-guide.md)（**按需查阅 · 不默认加载**）· 各节「📎 示例」指向对应 §。

---

## 模块设计判定（借鉴 mattpocock/skills improve-codebase-architecture）

🔴 与 backend.md 同源：使用 [templates/knowledge.md § Glossary 通用架构词汇](../templates/knowledge.md) 8 词 + "删除测试" 启发式 + "两个 adapter 才抽象" 规则。前端场景下 Module = React Component / 模块 / Hook · Interface = Props / Context / Hook 签名 · Seam = 跨页面共享 Hook + UI 库的稳定边界。详见 [standards/backend.md § 模块设计判定](./backend.md)（同源 · 不重复）。

---

## 一、前端测试规范（测试先行，强制执行）

**覆盖率要求**: > 70%

### 测试分层

| 层级 | 覆盖目标 | 工具示例 | 要求 |
|------|----------|----------|------|
| **单元测试** | 工具函数、Hooks、纯逻辑（非 UI） | Jest, Vitest | 必须覆盖，覆盖率 > 70% |
| **E2E 测试** | 关键用户流程、页面交互 | Playwright, Cypress | P0 流程必须覆盖 |
| **组件测试** | UI 组件渲染、交互 | Testing Library | 可选，按需补充 |

### 必须测试的场景

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

### 可选测试（非强制）

```
⚪ 可选：
├── 纯展示组件（无逻辑，只接收 props 渲染）
├── 第三方组件简单封装
├── 样式/动画效果
└── 静态页面
```

### 前端 TDD 流程

🔴 **单源 = [standards/tdd.md](./tdd.md)**（Iron Law / RED-GREEN-REFACTOR 5 步 / 自检清单 / 反模式 / 例外）· 本文件不复制流程正文（防双源漂移 · 已注册 tdd.md §七 引用约定）。前端落地差异仅两点：测试命令 `vitest path/to/component.test.tsx`（tdd.md §二 Step 2 已列）· RED 阶段先写组件测试（组件还不存在 · 测试先行）。

### 前端测试命名规范

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

### E2E 测试要求

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

## 二、组件测试规范

- **交互测试优先 Testing Library**（@testing-library/react / vue）：测用户能看到什么、能操作什么 · **不测内部实现** · `userEvent` 优于 `fireEvent`。
- **快照测试仅限 UI 回归检测**：禁大型组件快照（易碎、难 review）· 小型纯展示组件可用 inline snapshot。
- **标准检验点 5 项**：渲染 / 交互 / 边界状态（空数据 · 加载中 · 错误 · 超长文本）/ Props 组合 / 可访问性（axe）。
- **Mock 策略**：API 用 MSW（拦截网络层而非代码层）· Context 不 mock 本身、只提供最小 Provider 测试数据 · Router 用 MemoryRouter · 时间用 fakeTimers · 🔴 **禁止 mock 被测组件自身的内部方法**。

📎 示例（Button 五检验点测试 / MSW 配置）→ [frontend-guide.md §二](./frontend-guide.md)

---

## 三、样式与 UI 规范

- 🔴 **项目内统一 CSS 方案 · 严格禁止混用**（CSS Modules / Tailwind / CSS-in-JS / Sass+BEM 选其一）。
- 🔴 **组件引用 design token 变量 · 禁止硬编码颜色值 / 魔法数字**；暗色模式通过 token 层切换（组件层不感知主题）；token 定期与设计稿对账。
- **响应式 mobile-first**：用预定义断点变量（参考 sm 640 / md 768 / lg 1024 / xl 1280 / 2xl 1536 · 可按项目调整）· 避免硬编码数值。
- **命名**：CSS Modules = camelCase · Tailwind = 官方类名（@apply 组合防类爆炸）· 原生 CSS = BEM。
- 🔴 **全局样式仅限 reset / base / typography** · 禁止在全局样式中定义业务组件样式。

📎 方案选型对比 / Design Tokens 配置 / BEM 示例 → [frontend-guide.md §三](./frontend-guide.md)

---

## 四、状态管理规范

- **状态分层**（作用域决策）：仅当前组件 → `useState` / `ref`；父子共享 ≤3 层 → props / Context（provide-inject）；跨页面共享才进全局库；**服务端数据归数据获取库**（TanStack Query / SWR）· 不存入 Zustand / Pinia（避免重复缓存）。
- **选型**：简单全局状态默认 Zustand（React）/ Pinia（Vue）· 复杂状态机 XState · Redux 仅存量项目维护（新项目不推荐）。
- 🔴 **反模式**：Context API 当全局状态库（性能问题）· 所有状态塞全局（过度全局化 = 隐式耦合）· 组件中直接 fetch / axios（必须封装为自定义 hook / 数据获取库）。

📎 决策树 / Zustand · Pinia · TanStack Query · 乐观更新示例 → [frontend-guide.md §四](./frontend-guide.md)

---

## 五、性能规范

- **性能预算（Core Web Vitals）**：LCP < 2.5s · INP < 200ms · CLS < 0.1（TTFB < 800ms 参考）。
- **代码分割**：路由级 lazy 优先 · 大型三方库 / 弹窗内容动态导入 · 🔴 首屏关键路径禁动态导入（白屏）· 防过度分割（请求数激增）。
- **图片**：WebP 优先（AVIF 进阶需 fallback）· 非首屏全部 `loading="lazy"` · 必须给 width/height 防 CLS · 响应式 srcset · 裁剪/转格式交给图片 CDN。
- **Bundle**：单 PR 增量 > 50KB 必须说明原因 · 引库前查 bundlephobia · ESM + tree-shaking（如 `import { debounce } from 'lodash-es'`）· size-limit / bundlesize 进 CI。
- **渲染**：memo / useMemo / useCallback 按需用（🔴 禁无脑全加）· 列表 > 100 条用虚拟列表 · 不在 render 中创建新对象/函数 · 快变慢变数据分 store。

📎 各项实施与配置示例 → [frontend-guide.md §五](./frontend-guide.md)

---

## 六、无障碍访问规范（WCAG 2.1 AA）

- **四支柱**：可感知 / 可操作 / 可理解 / 鲁棒。
- **优先语义化 HTML**（nav / main / article / label / button）· 🔴 禁 `<div onClick>` / `role="button"` 模拟按钮和表单元素 · 标题层级不跳层。
- **ARIA**：无文字元素必须 aria-label(ledby) · 动态内容 aria-live · 表单错误 aria-invalid + aria-errormessage · 🔴 禁 `aria-hidden="true"` 隐藏可聚焦元素（键盘陷阱）。
- **键盘**：所有交互元素 Tab 可达 · 避免 tabindex > 0 · ESC 关闭弹层 · 模态框焦点陷阱 + 关闭归还焦点 · 不隐藏 outline 聚焦态。
- **对比度**：正文 ≥ 4.5:1 · 大文本/图形 UI ≥ 3:1 · 🔴 禁仅靠颜色传达状态（文字 + 图标 + 颜色并用）。
- **自动化**：jest-axe / @axe-core 进组件测试 · Lighthouse a11y ≥ 90 · 关键页面手动键盘 + 屏幕阅读器抽测。

📎 语义化 / ARIA / 焦点陷阱实现示例 → [frontend-guide.md §六](./frontend-guide.md)

---

## 七、构建与部署规范

- **环境变量分层**：`.env`（默认）/ `.env.development` / `.env.production` / `.env.test` 提交 git · `*.local` gitignore；🔴 密钥仅入 `.env.local` / CI secrets · 禁硬编码 API 端点和密钥 · 客户端可见变量按框架前缀（VITE_ / NEXT_PUBLIC_ / REACT_APP_）。
- **缓存**：构建产物 content hash 命名 · 静态资源 `max-age=31536000` · HTML 入口 no-cache（保证总能拿到新版本）。
- **Source Map**：生产用 hidden-source-map 并上传错误监控（Sentry 等）· 🔴 严禁生产 inline-source-map / source-map（泄源码）· `.map` 文件不进生产 public。
- **CI 检查顺序**：类型检查 → lint / format → 测试（覆盖率 70% 门禁）→ build → bundle 体积（可选）→ a11y（可选）→ Lighthouse（可选 · 性能 ≥ 80 / a11y ≥ 90）。

📎 .env / Vite / Nginx 缓存 / Sentry / GitHub Actions 配置示例 → [frontend-guide.md §七](./frontend-guide.md)

---

## 总结与关键点

| 类别 | 关键规范 |
|------|----------|
| **测试** | TDD 先行（单源 tdd.md），覆盖率 > 70%，必须覆盖 P0 流程 |
| **组件测试** | Testing Library + MSW Mock，避免快照测试 |
| **样式** | 统一 CSS 方案，使用 design tokens，响应式 mobile-first |
| **状态管理** | 分层管理，仅当必要才全局化，数据获取用专门库 |
| **性能** | LCP < 2.5s，CLS < 0.1，路由级分割，图片 WebP 懒加载 |
| **无障碍** | 语义化 HTML，ARIA 标签，键盘导航，对比度检查 |
| **构建与部署** | 环境变量分层，content hash 缓存，CI 自动化检查 |
