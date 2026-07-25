# 前端开发规范

> 前端 RD 必须遵守。通用规范见 📎 [common.md](./common.md) · TDD 流程唯一权威源 📎 [tdd.md](./tdd.md)。
> Subagent 加载指引：前端子项目加载本文件 + tdd.md + common.md，无需加载 backend.md。
> 📎 **实施示例 / 选型教程不入库**（v8.123 裁定）：通用技术用法是模型自带知识 · AI 按需自生成（防教程腐烂反向误导 · 承 v8.114 三层律「不 own 知识内容」）· 项目特异约定归各项目 `DEV-RULES.md`（用户主权）。本文件只保留 must/must-not 硬规则。

---

## 模块设计判定（借鉴 mattpocock/skills improve-codebase-architecture）

🔴 与 backend.md 同源：使用 [templates/knowledge.md § Glossary 通用架构词汇](../templates/knowledge.md) 8 词 + "删除测试" 启发式 + "两个 adapter 才抽象" 规则。前端场景下 Module = React Component / 模块 / Hook · Interface = Props / Context / Hook 签名 · Seam = 跨页面共享 Hook + UI 库的稳定边界。详见 [standards/backend.md § 模块设计判定](./backend.md)（同源 · 不重复）。

---

## 一、前端测试规范

> TDD 手艺单源 [tdd.md](./tdd.md)(v8.285:本节流程教程与示例已删)。本节只留**项目约定的阈值与清单**:

- **覆盖率**:> 70%
- **测试分层**:单元(纯函数/hook)· 组件(渲染 + 交互 + 状态)· 集成(跨组件/路由/数据流)· e2e(真实浏览器 · 归 browser_e2e stage)
- **必须测试的场景**:交互回调真被调用 · 条件渲染各分支 · 异步态(loading/success/error)· 边界输入(空/超长/特殊字符)· 错误边界不白屏

## 二、组件测试规范

- **交互测试优先 Testing Library**（@testing-library/react / vue）：测用户能看到什么、能操作什么 · **不测内部实现** · `userEvent` 优于 `fireEvent`。
- **快照测试仅限 UI 回归检测**：禁大型组件快照（易碎、难 review）· 小型纯展示组件可用 inline snapshot。
- **标准检验点 5 项**：渲染 / 交互 / 边界状态（空数据 · 加载中 · 错误 · 超长文本）/ Props 组合 / 可访问性（axe）。
- **Mock 策略**：API 用 MSW（拦截网络层而非代码层）· Context 不 mock 本身、只提供最小 Provider 测试数据 · Router 用 MemoryRouter · 时间用 fakeTimers · 🔴 **禁止 mock 被测组件自身的内部方法**。

---

## 三、样式与 UI 规范

- 🔴 **项目内统一 CSS 方案 · 严格禁止混用**（CSS Modules / Tailwind / CSS-in-JS / Sass+BEM 选其一）。
- 🔴 **组件引用 design token 变量 · 禁止硬编码颜色值 / 魔法数字**；暗色模式通过 token 层切换（组件层不感知主题）；token 定期与设计稿对账。
- **响应式 mobile-first**：用预定义断点变量（参考 sm 640 / md 768 / lg 1024 / xl 1280 / 2xl 1536 · 可按项目调整）· 避免硬编码数值。
- **命名**：CSS Modules = camelCase · Tailwind = 官方类名（@apply 组合防类爆炸）· 原生 CSS = BEM。
- 🔴 **全局样式仅限 reset / base / typography** · 禁止在全局样式中定义业务组件样式。

---

## 四、状态管理规范

- **状态分层**（作用域决策）：仅当前组件 → `useState` / `ref`；父子共享 ≤3 层 → props / Context（provide-inject）；跨页面共享才进全局库；**服务端数据归数据获取库**（TanStack Query / SWR）· 不存入 Zustand / Pinia（避免重复缓存）。
- **选型**：简单全局状态默认 Zustand（React）/ Pinia（Vue）· 复杂状态机 XState · Redux 仅存量项目维护（新项目不推荐）。
- 🔴 **反模式**：Context API 当全局状态库（性能问题）· 所有状态塞全局（过度全局化 = 隐式耦合）· 组件中直接 fetch / axios（必须封装为自定义 hook / 数据获取库）。

---

## 五、性能规范

- **性能预算（Core Web Vitals）**：LCP < 2.5s · INP < 200ms · CLS < 0.1（TTFB < 800ms 参考）。
- **代码分割**：路由级 lazy 优先 · 大型三方库 / 弹窗内容动态导入 · 🔴 首屏关键路径禁动态导入（白屏）· 防过度分割（请求数激增）。
- **图片**：WebP 优先（AVIF 进阶需 fallback）· 非首屏全部 `loading="lazy"` · 必须给 width/height 防 CLS · 响应式 srcset · 裁剪/转格式交给图片 CDN。
- **Bundle**：单 PR 增量 > 50KB 必须说明原因 · 引库前查 bundlephobia · ESM + tree-shaking（如 `import { debounce } from 'lodash-es'`）· size-limit / bundlesize 进 CI。
- **渲染**：memo / useMemo / useCallback 按需用（🔴 禁无脑全加）· 列表 > 100 条用虚拟列表 · 不在 render 中创建新对象/函数 · 快变慢变数据分 store。

---

## 六、无障碍访问规范（WCAG 2.1 AA）

- **四支柱**：可感知 / 可操作 / 可理解 / 鲁棒。
- **优先语义化 HTML**（nav / main / article / label / button）· 🔴 禁 `<div onClick>` / `role="button"` 模拟按钮和表单元素 · 标题层级不跳层。
- **ARIA**：无文字元素必须 aria-label(ledby) · 动态内容 aria-live · 表单错误 aria-invalid + aria-errormessage · 🔴 禁 `aria-hidden="true"` 隐藏可聚焦元素（键盘陷阱）。
- **键盘**：所有交互元素 Tab 可达 · 避免 tabindex > 0 · ESC 关闭弹层 · 模态框焦点陷阱 + 关闭归还焦点 · 不隐藏 outline 聚焦态。
- **对比度**：正文 ≥ 4.5:1 · 大文本/图形 UI ≥ 3:1 · 🔴 禁仅靠颜色传达状态（文字 + 图标 + 颜色并用）。
- **自动化**：jest-axe / @axe-core 进组件测试 · Lighthouse a11y ≥ 90 · 关键页面手动键盘 + 屏幕阅读器抽测。

---

## 七、构建与部署规范

- **环境变量分层**：`.env`（默认）/ `.env.development` / `.env.production` / `.env.test` 提交 git · `*.local` gitignore；🔴 密钥仅入 `.env.local` / CI secrets · 禁硬编码 API 端点和密钥 · 客户端可见变量按框架前缀（VITE_ / NEXT_PUBLIC_ / REACT_APP_）。
- **缓存**：构建产物 content hash 命名 · 静态资源 `max-age=31536000` · HTML 入口 no-cache（保证总能拿到新版本）。
- **Source Map**：生产用 hidden-source-map 并上传错误监控（Sentry 等）· 🔴 严禁生产 inline-source-map / source-map（泄源码）· `.map` 文件不进生产 public。
- **CI 检查顺序**：类型检查 → lint / format → 测试（覆盖率 70% 门禁）→ build → bundle 体积（可选）→ a11y（可选）→ Lighthouse（可选 · 性能 ≥ 80 / a11y ≥ 90）。

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
