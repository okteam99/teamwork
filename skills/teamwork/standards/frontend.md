# 前端开发规范

> 前端 RD 必须遵守。通用规范见 📎 [common.md](./common.md)。
> Subagent 加载指引：前端子项目只需加载本文件 + common.md，无需加载 backend.md。

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

## 二、组件测试规范（新增）

### 组件测试策略

```
组件测试分类：
├── 交互测试（Testing Library）：模拟用户行为，验证 DOM 状态变化
│   ├── 优先使用 @testing-library/react（React）/ @testing-library/vue（Vue）
│   ├── 测试用户能看到什么、能操作什么，不测内部实现
│   └── 用 userEvent 代替 fireEvent（更接近真实用户行为）
├── 快照测试：仅用于 UI 回归检测，不作为主要测试手段
│   ├── 避免大型组件快照（易碎、难以 review）
│   └── 建议对小型纯展示组件使用 inline snapshot
└── 视觉回归测试（可选）：Chromatic / Percy，用于设计系统级组件
```

### 组件测试模板

```
标准组件测试包含以下检验点：
├── 1️⃣ 渲染测试：组件能否正常渲染，关键内容是否可见
├── 2️⃣ 交互测试：用户操作后状态是否正确变化
├── 3️⃣ 边界状态测试：空数据、加载中、错误状态、超长文本
├── 4️⃣ Props 测试：不同 props 组合的渲染结果
└── 5️⃣ 可访问性测试：axe-core 自动检测
```

**示例：Button 组件测试**
```typescript
describe('Button', () => {
  // 1️⃣ 渲染测试
  it('should render button with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  // 2️⃣ 交互测试
  it('should call onClick handler when clicked', async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click me</Button>);
    await userEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledOnce();
  });

  // 3️⃣ 边界状态测试
  it('should be disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  // 4️⃣ Props 测试
  it('should render with different variants', () => {
    render(
      <>
        <Button variant="primary">Primary</Button>
        <Button variant="secondary">Secondary</Button>
      </>
    );
    expect(screen.getByRole('button', { name: /primary/i })).toHaveClass('primary');
    expect(screen.getByRole('button', { name: /secondary/i })).toHaveClass('secondary');
  });

  // 5️⃣ 可访问性测试
  it('should have no accessibility violations', async () => {
    const { container } = render(<Button>Click me</Button>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

### Mock 策略

```
根据不同场景选择合适的 Mock 方式：
├── API Mock：MSW（Mock Service Worker）优先，拦截网络层而非代码层
│   ├── 优势：测试真实网络行为，支持 REST、GraphQL、WebSocket
│   └── 使用：server.use(http.get('/api/users', resolver))
├── Context/Provider Mock：测试文件中提供最小化 Provider 包装
│   ├── 方式：render(<Component />, { wrapper: TestProvider })
│   └── 避免：不要 mock Context 本身，只提供测试数据
├── Router Mock：使用 MemoryRouter / createMemoryRouter
│   └── 示例：<MemoryRouter initialEntries={['/dashboard']}><Component /></MemoryRouter>
├── 时间 Mock：vi.useFakeTimers() / jest.useFakeTimers()
│   └── 用途：测试延迟逻辑、轮询、防抖等时间相关功能
└── 🔴 禁止事项：禁止 Mock 被测组件自身的内部方法
```

**MSW 配置示例**
```typescript
// mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/users', () => {
    return HttpResponse.json([
      { id: 1, name: 'Alice' },
      { id: 2, name: 'Bob' },
    ]);
  }),
  http.post('/api/users', async ({ request }) => {
    const data = await request.json();
    return HttpResponse.json({ id: 3, ...data }, { status: 201 });
  }),
];

// vitest.config.ts - 全局设置
import { setupServer } from 'msw/node';
const server = setupServer(...handlers);
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

---

## 三、样式与 UI 规范（新增）

### CSS 方案选择

```
不同项目规模的 CSS 方案对比：
├── CSS Modules
│   ├── 适用：中型项目，需要局部作用域
│   ├── 优势：天然作用域隔离，无需额外配置
│   └── 示例：import styles from './Button.module.css'; <div className={styles.root} />
├── Tailwind CSS
│   ├── 适用：快速开发，设计系统完善
│   ├── 优势：快速开发，配合 design tokens 使用
│   └── 注意：需要定制 tailwind.config.js，防止默认样式不符设计规范
├── CSS-in-JS（styled-components / emotion）
│   ├── 适用：需要动态样式、运行时样式计算
│   ├── 优势：支持 TypeScript、动态属性
│   └── 示例：const Button = styled.button\`background: ${props => props.color};\`;
└── 原生 CSS + 预处理器（Sass/Less）
    ├── 适用：传统项目，大型 CSS 库
    └── 结合 BEM 命名确保维护性
```

**重要规则**：项目内统一 CSS 方案，严格禁止混用（避免样式冲突和维护混乱）

### 响应式断点标准

```
推荐断点设置（可按项目调整）：
├── sm: 640px   → 手机横屏 / 小平板
├── md: 768px   → 平板竖屏
├── lg: 1024px  → 平板横屏 / 小笔记本
├── xl: 1280px  → 桌面显示器
└── 2xl: 1536px → 大屏显示器

媒体查询示例：
├── Mobile-first 方法（推荐）：从小屏开始，逐步添加 @media (min-width: ...)
├── 使用 CSS 变量 + Tailwind 配置统一管理
└── 避免硬编码数值，优先使用预定义断点变量
```

**响应式布局示例**
```css
/* Mobile-first: 默认为手机样式 */
.container {
  padding: 16px;
}

/* 平板设备 */
@media (min-width: 768px) {
  .container {
    padding: 24px;
  }
}

/* 桌面设备 */
@media (min-width: 1024px) {
  .container {
    padding: 32px;
  }
}
```

### 设计令牌（Design Tokens）

```
Design Tokens 职责：统一管理设计元素
├── 包含内容
│   ├── 颜色（primary、secondary、error、success、warning）
│   ├── 字体（font-family、font-size、font-weight、line-height）
│   ├── 间距（spacing scale: 4px, 8px, 12px, 16px, 24px, 32px...)
│   ├── 圆角（border-radius 预设值）
│   ├── 阴影（shadows 层级）
│   ├── z-index（分层管理：modal > dropdown > tooltip > base）
│   └── 过渡动画（transition timing function）
├── 管理方式
│   ├── CSS 变量：:root { --color-primary: #007bff; }
│   ├── JavaScript 对象：export const colors = { primary: '#007bff' };
│   └── YAML / JSON 文件 + 工具（figma-tokens 等）
├── 组件使用规范
│   ├── 组件中引用 token 变量，禁止硬编码颜色值 / 魔法数字
│   └── 示例：background: var(--color-primary); padding: var(--spacing-4);
├── 暗色模式支持
│   ├── 通过 token 层切换（:root[data-theme='dark']）
│   ├── 组件层不感知主题，直接使用 token 变量
│   └── 示例：:root[data-theme='dark'] { --color-primary: #0056b3; }
└── 与设计规范同步
    └── 定期 review Figma / Sketch，确保 token 值与设计稿一致
```

**Design Tokens 配置示例**
```typescript
// src/design-tokens.ts
export const tokens = {
  colors: {
    primary: 'var(--color-primary)',
    secondary: 'var(--color-secondary)',
    error: 'var(--color-error)',
    success: 'var(--color-success)',
  },
  spacing: {
    xs: 'var(--spacing-xs)',   // 4px
    sm: 'var(--spacing-sm)',   // 8px
    md: 'var(--spacing-md)',   // 16px
    lg: 'var(--spacing-lg)',   // 24px
    xl: 'var(--spacing-xl)',   // 32px
  },
  typography: {
    heading1: 'var(--font-heading-1)',
    heading2: 'var(--font-heading-2)',
    body: 'var(--font-body)',
    caption: 'var(--font-caption)',
  },
  radius: {
    sm: 'var(--radius-sm)',    // 4px
    md: 'var(--radius-md)',    // 8px
    lg: 'var(--radius-lg)',    // 12px
    full: 'var(--radius-full)', // 9999px
  },
};

// src/styles/variables.css
:root {
  /* Light Mode */
  --color-primary: #007bff;
  --color-secondary: #6c757d;
  --color-error: #dc3545;
  --color-success: #28a745;

  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;

  /* Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;
}

/* Dark Mode */
:root[data-theme='dark'] {
  --color-primary: #0056b3;
  --color-secondary: #495057;
  --color-error: #bd2130;
  --color-success: #1e7e34;
}
```

### 样式命名约定

```
不同 CSS 方案的命名规范：
├── CSS Modules：camelCase
│   ├── 示例：styles.headerTitle、styles.buttonPrimary
│   └── 优势：模块化自动前缀，避免冲突
├── Tailwind CSS：遵循官方类名规范
│   ├── 示例：<div className="p-4 bg-blue-500 text-white rounded-lg" />
│   ├── 自定义类：@apply 指令组合
│   └── 防止类爆炸：使用 component layer 定义可复用类
├── BEM（如用原生 CSS）：block__element--modifier
│   ├── 示例：.button / .button__text / .button--primary
│   └── 适用：不用预处理器或 CSS-in-JS 的项目
└── 全局样式使用场景（有限制）：
    ├── CSS reset：normalize.css 或自定义 reset
    ├── Base 样式：html、body、输入框等通用样式
    ├── Typography：全局字体定义
    └── 🔴 禁止：不要在全局样式中定义业务组件样式
```

**BEM 实践示例**
```css
/* Block */
.card {
  border: 1px solid #ddd;
  border-radius: 8px;
}

/* Element */
.card__header {
  padding: 16px;
  border-bottom: 1px solid #ddd;
}

.card__body {
  padding: 16px;
}

.card__footer {
  padding: 16px;
  border-top: 1px solid #ddd;
}

/* Modifier */
.card--elevated {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card--compact {
  border-radius: 4px;
}
```

---

## 四、状态管理规范（新增）

### 本地 vs 全局状态判断

```
状态作用域决策树：
├── 仅当前组件使用
│   ├── 工具：useState / useReducer（React）、ref / reactive（Vue）
│   ├── 示例：输入框内容、弹窗打开/关闭状态、悬浮状态
│   └── 不需要向上提升
├── 父子组件共享（≤3 层）
│   ├── 方式 1：Props drilling（数据下行，事件上行）
│   ├── 方式 2：React Context / Vue provide-inject
│   ├── 示例：表单字段、模态框数据
│   └── 避免：层级过多时才考虑全局状态
├── 跨页面 / 多组件共享
│   ├── 工具：全局状态库（Zustand、Pinia 等）
│   ├── 示例：用户信息、主题、国际化语言
│   └── 需要持久化时使用 localStorage plugin
└── 服务端数据（API 响应数据）
    ├── 工具：数据获取库（TanStack Query、SWR）
    ├── 与状态库分离（避免重复缓存）
    └── 不应直接存入 Zustand / Pinia
```

**反面教案：过度全局化**
```typescript
// ❌ 不推荐：所有状态都塞进 global store
const useGlobalStore = create((set) => ({
  formInput: '',          // 应该是本地状态
  dropdownOpen: false,    // 应该是本地状态
  selectedTab: 'tab1',    // 应该是本地状态
  user: null,             // ✅ 合理的全局状态
  theme: 'light',         // ✅ 合理的全局状态
}));

// ✅ 推荐：状态分层
// 本地状态：组件内 useState
// 全局状态：Zustand store
const useUserStore = create((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  logout: () => set({ user: null }),
}));

const useThemeStore = create((set) => ({
  theme: 'light',
  toggleTheme: () => set((state) => ({ theme: state.theme === 'light' ? 'dark' : 'light' })),
}));
```

### 状态库选择指引

```
选择状态库的决策依据：
├── 简单全局状态（推荐优先级 1）
│   ├── Zustand（React）：最小化、无样板代码、TypeScript 友好
│   ├── Pinia（Vue）：官方推荐，开发体验良好
│   └── 使用场景：用户信息、主题、国际化、UI 全局设置
├── 复杂状态机（推荐优先级 2）
│   ├── XState：状态机设计，易于推理和测试
│   └── 使用场景：工作流、支付流程、复杂交互状态
├── Redux（不推荐用于新项目）
│   ├── 仅在已有项目中继续使用，维持向后兼容
│   ├── 新项目优先选择 Zustand（更轻量）
│   └── Redux Toolkit 可简化使用，但 Zustand 仍更简洁
└── 🔴 反模式：
    ├── 禁止使用 Context API 作为全局状态库替代品（性能问题）
    └── 禁止将所有状态都放入全局（过度全局化 = 隐式耦合）
```

**Zustand 最佳实践**
```typescript
// src/store/user.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  name: string;
  email: string;
}

interface UserStore {
  user: User | null;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useUserStore = create<UserStore>()(
  persist(
    (set) => ({
      user: null,
      setUser: (user) => set({ user }),
      logout: () => set({ user: null }),
    }),
    {
      name: 'user-store',        // localStorage key
      version: 1,                // 版本管理，用于迁移
    }
  )
);

// 在组件中使用
function Profile() {
  const { user, logout } = useUserStore();

  if (!user) return <div>未登录</div>;

  return (
    <div>
      <p>欢迎，{user.name}</p>
      <button onClick={logout}>登出</button>
    </div>
  );
}
```

**Pinia 最佳实践（Vue）**
```typescript
// src/stores/user.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null);

  const setUser = (newUser: User) => {
    user.value = newUser;
  };

  const logout = () => {
    user.value = null;
  };

  return { user, setUser, logout };
}, {
  persist: true,  // 启用持久化
});
```

### 数据获取规范

```
数据获取层最佳实践：
├── React：TanStack Query（React Query）优先
│   ├── 官方：@tanstack/react-query
│   ├── 功能：自动缓存、过期管理、乐观更新
│   └── 与状态库分离：Query 处理服务端数据，Zustand 处理 UI 状态
├── Vue：TanStack Query for Vue 或 useFetch composable
│   ├── 官方：@tanstack/vue-query（推荐）
│   └── 轻量方案：useFetch from @vueuse/core
├── SWR（轻量级方案）：如果项目足够简单可考虑
│   ├── npm: swr
│   └── 适用于：数据获取较简单的项目
└── GraphQL：Apollo Client / TanStack Query + graphql-request
```

**数据获取最佳实践**
```typescript
// ✅ 推荐：所有 API 请求封装为自定义 hook
// src/hooks/useUsers.ts
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/services/api';

export const useUsers = () => {
  return useQuery({
    queryKey: ['users'],
    queryFn: () => api.get('/users'),
    staleTime: 5 * 60 * 1000,      // 5 分钟数据新鲜
    gcTime: 10 * 60 * 1000,        // 10 分钟垃圾回收
  });
};

export const useCreateUser = () => {
  return useMutation({
    mutationFn: (user: CreateUserDTO) => api.post('/users', user),
    onSuccess: (data, variables, context) => {
      // ✅ 乐观更新：立即刷新用户列表
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
};

// src/components/UserList.tsx
function UserList() {
  const { data: users, isLoading, error } = useUsers();
  const createUserMutation = useCreateUser();

  if (isLoading) return <div>加载中...</div>;
  if (error) return <div>错误：{error.message}</div>;

  return (
    <div>
      {users?.map(user => <div key={user.id}>{user.name}</div>)}
      <button onClick={() => createUserMutation.mutate({ name: 'New User' })}>
        添加用户
      </button>
    </div>
  );
}

// ❌ 禁止：直接在组件中调用 fetch/axios
// function UserList() {
//   useEffect(() => {
//     fetch('/api/users')  // ❌ 不要这样做
//       .then(res => res.json())
//       .then(setUsers);
//   }, []);
// }
```

**乐观更新示例**
```typescript
const useUpdateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (user: User) => api.put(`/users/${user.id}`, user),
    // 乐观更新：更新前立即更新 UI
    onMutate: async (newUser) => {
      // 取消所有 pending 的 'users' 查询
      await queryClient.cancelQueries({ queryKey: ['users'] });

      // 获取旧数据
      const previousUsers = queryClient.getQueryData(['users']);

      // 乐观更新缓存
      queryClient.setQueryData(['users'], (old: User[]) =>
        old.map(u => u.id === newUser.id ? newUser : u)
      );

      return { previousUsers };
    },
    // 如果失败，回滚到旧数据
    onError: (err, newUser, context) => {
      queryClient.setQueryData(['users'], context?.previousUsers);
    },
  });
};
```

---

## 五、性能规范（新增）

### Core Web Vitals 性能预算

```
前端关键性能指标目标（Google 核心指标）：
├── LCP（Largest Contentful Paint）< 2.5s
│   ├── 含义：最大内容元素的绘制时间
│   ├── 优化方向：减少 JS 体积、优化图片加载、预加载关键资源
│   └── 测量：Chrome DevTools → Lighthouse
├── INP（Interaction to Next Paint）< 200ms
│   ├── 含义：用户交互到页面响应的时间
│   ├── 优化方向：减少长任务、优化事件处理器、使用 Web Worker
│   └── 已替代 FID（First Input Delay）
├── CLS（Cumulative Layout Shift）< 0.1
│   ├── 含义：页面布局移动的累积度量
│   ├── 优化方向：为图片设置尺寸、避免动态插入内容、使用 transform 替代 layout 变更
│   └── 常见问题：图片加载、字体加载 FOUT、广告加载
└── TTFB（Time to First Byte）< 800ms（额外参考）
    ├── 含义：从请求到收到第一个字节的时间
    └── 通常由服务端和网络延迟决定，前端优化空间有限
```

### 代码分割策略

```
按需加载关键决策：
├── 路由级 lazy load（推荐优先级 1）
│   ├── React：const Dashboard = lazy(() => import('./Dashboard'));
│   ├── Vue：const Dashboard = defineAsyncComponent(() => import('./Dashboard.vue'));
│   ├── 优势：有效减少初始 bundle 体积
│   └── 示例：每个路由作为一个分割点
├── 大型第三方库动态导入
│   ├── 示例：图表库（Chart.js、ECharts）、编辑器、PDF 查看器
│   ├── 方法：import('chart.js').then(Chart => { /* use Chart */ })
│   └── 工具库：@loadable/component（React）、dynamic import
├── 模态框 / 弹窗组件按需加载
│   ├── 示例：导入 modal 的内容只在打开时加载
│   └── 使用动态导入或 <dialog> 标签
├── 条件功能按需加载
│   ├── 示例：高级功能、实验性功能、地区限制功能
│   └── 基于用户权限或配置动态导入
└── 🔴 禁止事项：
    ├── 首屏关键路径禁止动态导入（导致白屏）
    ├── 关键数据依赖的组件不能 lazy load
    └── 过度分割导致请求数激增（balance is key）
```

**路由级分割示例**
```typescript
// React Router v6
const routes = [
  { path: '/', element: <Home /> },
  { path: '/dashboard', element: <Suspense fallback={<Loading />}><lazy(() => import('./Dashboard')) /></Suspense> },
  { path: '/admin', element: <Suspense><lazy(() => import('./Admin')) /></Suspense> },
];

// Vue Router
const routes = [
  { path: '/', component: () => import('./views/Home.vue') },
  { path: '/dashboard', component: () => import('./views/Dashboard.vue') },
  { path: '/admin', component: () => import('./views/Admin.vue') },
];
```

**大型库动态导入示例**
```typescript
// ❌ 不推荐：初始加载所有依赖
import ECharts from 'echarts';

function ChartComponent() {
  // ECharts 被包含在首屏 bundle 中
}

// ✅ 推荐：按需加载
async function renderChart() {
  const ECharts = await import('echarts');
  const chart = ECharts.init(containerEl);
  chart.setOption(/* ... */);
}
```

### 图片优化

```
图片优化最佳实践：
├── 格式选择（优先级从高到低）
│   ├── WebP：现代浏览器首选，体积最小
│   ├── AVIF：更新的格式，压缩率更好（需要 fallback）
│   ├── PNG：需要透明度或高保真图像
│   ├── JPEG：照片类图片
│   └── 🔴 禁止 BMP、GIF、TIFF（除了动画 GIF）
├── 懒加载
│   ├── 原生：loading="lazy" 属性（支持度 95%+）
│   ├── 库方案：react-lazyload、v-lazy（Vue）
│   ├── 规则：非首屏图片全部懒加载
│   └── Intersection Observer 优于滚动事件
├── 尺寸约束
│   ├── 始终提供 width 和 height 属性（防止 CLS）
│   ├── 示例：<img src="photo.jpg" width="800" height="600" loading="lazy" />
│   └── CSS 亦然：img { width: 100%; height: auto; }
├── 响应式图片
│   ├── 方式 1：<img srcset="small.jpg 640w, large.jpg 1280w" sizes="..." />
│   ├── 方式 2：<picture><source srcset="image.webp" /><img src="image.jpg" /></picture>
│   └── 优势：根据设备宽度加载合适尺寸，减少流量
└── 图片 CDN
    ├── 使用 CDN 服务（Cloudflare、阿里云、七牛等）进行动态裁剪和格式转换
    ├── 示例：image.com/photo.jpg?w=800&format=webp
    └── 避免：不要自己做复杂的图片处理，交给 CDN
```

**现代图片加载示例**
```html
<!-- 优化前 -->
<img src="photo.jpg" />

<!-- 优化后 -->
<picture>
  <!-- WebP 格式，高分辨率屏幕 -->
  <source
    srcset="photo-large.webp 1280w, photo-small.webp 640w"
    sizes="(min-width: 1024px) 1280px, 640px"
    type="image/webp" />
  <!-- AVIF 格式（可选） -->
  <source
    srcset="photo-large.avif 1280w, photo-small.avif 640w"
    sizes="(min-width: 1024px) 1280px, 640px"
    type="image/avif" />
  <!-- Fallback JPG -->
  <img
    src="photo.jpg"
    srcset="photo-large.jpg 1280w, photo-small.jpg 640w"
    sizes="(min-width: 1024px) 1280px, 640px"
    alt="产品照片"
    width="800"
    height="600"
    loading="lazy"
    decoding="async" />
</picture>
```

### Bundle 分析与体积控制

```
Bundle 体积管理流程：
├── 定期分析
│   ├── 工具：webpack-bundle-analyzer、rollup-plugin-visualizer
│   ├── 命令：npm run build:analyze
│   └── 频率：每次主要依赖更新时运行
├── 增量体积检查
│   ├── 规则：单次 PR 增量 > 50KB 时，必须在 PR 描述中说明原因
│   ├── 例外情况：引入新功能、大型库更新（需合理说明）
│   └── 工具：bundlesize / size-limit 集成到 CI
├── 第三方库引入审核
│   ├── 检查网站：bundlephobia.com
│   ├── 评估：体积、依赖数、更新频率
│   ├── 决策：是否有更轻量的替代方案
│   └── 示例：避免同时使用 moment + dayjs（选一个）
├── Tree-shaking 优化
│   ├── 条件：库必须支持 ESM 格式
│   ├── 验证：npm view <package> module / exports
│   ├── 配置：webpack/Vite sideEffects 标记
│   └── 示例：import { debounce } from 'lodash-es';（不要 import * as _）
└── 依赖去重
    ├── 检查：npm ls 查看重复依赖
    ├── 管理：使用 npm workspaces、monorepo 统一版本
    └── 工具：npm audit、npkill
```

**Bundle 分析配置（Vite）**
```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    react(),
    visualizer({
      open: true,  // 构建后自动打开分析页面
      gzipSize: true,
      brotliSize: true,
    }),
  ],
});

// 运行：npm run build（vite 会生成 stats.html）
```

### 渲染优化

```
组件渲染优化策略：
├── React.memo
│   ├── 用途：避免父组件重渲染时子组件不必要的渲染
│   ├── 条件：props 通常稳定，父组件频繁渲染
│   ├── 示例：export const UserCard = memo(({ user }) => <div>{user.name}</div>);
│   └── 🔴 禁止：对所有组件无脑添加 memo（增加复杂度且可能无收益）
├── useMemo / useCallback
│   ├── useMemo：计算开销大或作为子组件 props 时使用
│   ├── useCallback：传给子组件的回调函数，或依赖于 effect 的函数
│   ├── 示例：const memoValue = useMemo(() => expensiveCalculation(a, b), [a, b]);
│   └── 🔴 禁止：过度使用导致代码复杂度上升，没有实际收益
├── 虚拟列表（大列表优化）
│   ├── 何时使用：列表项数 > 100 条
│   ├── React：react-virtuoso（推荐）、react-window
│   ├── Vue：vue-virtual-scroller
│   └── 原理：只渲染可见区域的元素，滚动时动态更新
├── 避免在 render 中创建新对象/函数
│   ├── 错误：render 中定义 handleClick={() => {}}
│   ├── 正确：提到 component 外层或用 useCallback
│   └── 原因：每次 render 都创建新引用，破坏 memo 和依赖项比较
└── 分离快变和慢变数据
    ├── 场景：某个字段频繁变化，其他字段很少变化
    ├── 方案：使用多个状态管理器，避免整体重渲染
    └── 示例：useUserStore（用户信息）和 useScrollStore（滚动位置）分开
```

**虚拟列表示例**
```typescript
// React - react-virtuoso
import { VirtuosoGrid } from 'react-virtuoso';

function UserGrid({ users }: { users: User[] }) {
  return (
    <VirtuosoGrid
      style={{ height: '600px' }}
      data={users}
      itemContent={(index, user) => (
        <div key={user.id}>{user.name}</div>
      )}
      colCount={3}
    />
  );
}

// Vue - vue-virtual-scroller
<template>
  <RecycleScroller
    v-slot="{ item }"
    :items="users"
    :item-size="50"
    class="scroller"
  >
    <div>{{ item.name }}</div>
  </RecycleScroller>
</template>
```

---

## 六、无障碍访问规范（新增）

### 基本要求（WCAG 2.1 AA）

```
无障碍开发核心四大支柱：
├── 1. 可感知（Perceivable）
│   ├── 提供文本替代品（alt 文本、标题、标签）
│   ├── 颜色对比度：正文 ≥ 4.5:1，大文本 ≥ 3:1
│   └── 不仅靠颜色传达信息（例：错误应同时显示图标 + 文字）
├── 2. 可操作（Operable）
│   ├── 键盘可访问：所有功能可通过键盘操作
│   ├── 足够的时间：不要让内容消失得太快
│   ├── 避免导致癫痫的闪烁：闪烁频率 < 3Hz
│   └── 导航机制：清晰的页面结构、面包屑、跳链
├── 3. 可理解（Understandable）
│   ├── 语言明确：清晰的文案、避免行业术语
│   ├── 可预测的行为：不要在用户不知情的情况下改变页面
│   └── 输入协助：提供错误提示和修正建议
└── 4. 鲁棒性（Robust）
    ├── 有效的 HTML：使用验证工具检查
    ├── 支持辅助技术：屏幕阅读器、放大镜等
    └── API 兼容性：遵循标准 API
```

### 语义化 HTML

```
优先使用原生语义元素：
├── 导航元素
│   ├── <nav> 代替 <div class="navbar">
│   ├── <header> / <footer> 标识页面头尾
│   └── <main> 标识主要内容（每页只能一个）
├── 内容结构
│   ├── <article> 独立内容（博客、新闻）
│   ├── <section> 逻辑分组
│   ├── <aside> 侧边栏、补充信息
│   └── 正确的标题层级：<h1> → <h2> → <h3>（跳层会被认为是错误）
├── 表单元素
│   ├── <label htmlFor="inputId" /> 关联表单控件
│   ├── <fieldset> / <legend> 组织相关表单字段
│   ├── <input type="email" /> 使用语义类型
│   └── 禁止用 <div onClick /> 模拟表单元素
├── 按钮与链接
│   ├── <button> 执行操作
│   ├── <a href> 导航
│   ├── 🔴 禁止：<div role="button"> 代替真实按钮
│   └── 原因：缺少键盘支持、屏幕阅读器支持、原生样式
└── 列表
    ├── <ul> / <li> 无序列表
    ├── <ol> / <li> 有序列表
    └── 避免：用 <div> 模拟列表结构
```

**语义化示例**
```html
<!-- ❌ 不好：非语义化 -->
<div class="header">
  <div class="nav">
    <div class="nav-item"><a href="/home">Home</a></div>
    <div class="nav-item"><a href="/about">About</a></div>
  </div>
</div>
<div class="main">
  <div class="article">
    <div class="title">Article Title</div>
    <div class="content">...</div>
  </div>
</div>

<!-- ✅ 好：语义化 -->
<header>
  <nav aria-label="主导航">
    <ul>
      <li><a href="/home">Home</a></li>
      <li><a href="/about">About</a></li>
    </ul>
  </nav>
</header>
<main>
  <article>
    <h1>Article Title</h1>
    <p>...</p>
  </article>
</main>
```

### ARIA 标签

```
ARIA（Accessible Rich Internet Applications）使用规范：
├── 基础属性
│   ├── role：定义元素角色（button、dialog、alert 等）
│   ├── aria-label：为无文字的元素提供标签
│   ├── aria-labelledby：引用其他元素的 ID 作为标签
│   └── aria-describedby：提供额外描述
├── 动态内容通知
│   ├── aria-live="polite"：有礼貌地通知屏幕阅读器（等待说话完成）
│   ├── aria-live="assertive"：立即打断通知（如错误提示）
│   └── aria-atomic="true"：通知整个区域变化，不只是增量
├── 表单相关
│   ├── aria-required="true"：标记必填字段
│   ├── aria-invalid="true"：标记验证失败的字段
│   ├── aria-errormessage：关联错误提示信息
│   └── <label htmlFor> 或 aria-label 必须关联输入框
├── 状态和属性
│   ├── aria-expanded="true/false"：可展开元素的状态
│   ├── aria-pressed="true/false"：按钮的切换状态
│   ├── aria-selected="true/false"：列表项的选中状态
│   ├── aria-disabled="true"：禁用状态
│   └── aria-hidden="true"：隐藏装饰元素（不通知屏幕阅读器）
└── 🔴 禁止事项：
    ├── role="button" 代替真实 <button>（除非有特殊理由）
    ├── 过度使用 aria-label（优先使用语义化 HTML）
    └── aria-hidden="true" 隐藏可聚焦元素（会造成键盘陷阱）
```

**ARIA 应用示例**
```html
<!-- 自定义下拉菜单 -->
<div class="dropdown">
  <button
    aria-expanded="false"
    aria-haspopup="listbox"
    aria-controls="menu-list"
  >
    选项
  </button>
  <ul id="menu-list" role="listbox">
    <li role="option" aria-selected="false">选项 1</li>
    <li role="option" aria-selected="true">选项 2</li>
  </ul>
</div>

<!-- 动态通知区域 -->
<div aria-live="polite" aria-atomic="true" id="notification">
  <!-- 动态更新的内容会自动通知屏幕阅读器 -->
</div>

<!-- 带标签的搜索框 -->
<label htmlFor="search-input">搜索用户</label>
<input
  id="search-input"
  type="search"
  aria-describedby="search-help"
  placeholder="输入用户名或邮箱"
/>
<p id="search-help">支持按用户名、邮箱搜索</p>

<!-- 表单验证错误提示 -->
<input
  id="email"
  type="email"
  aria-invalid="true"
  aria-errormessage="email-error"
/>
<span id="email-error" role="alert">邮箱格式错误</span>
```

### 键盘导航

```
键盘导航实现要点：
├── Tab 键导航
│   ├── 所有交互元素必须可通过 Tab 聚焦
│   ├── tabindex 属性：-1（移除聚焦），0（正常顺序），1+（自定义顺序）
│   ├── 避免 tabindex > 0（会破坏导航顺序）
│   └── 使用 outline 展示聚焦状态（不要隐藏）
├── 回车键和空格键
│   ├── <button> 和 <a> 原生支持，无需额外处理
│   ├── 自定义组件需要手动实现
│   └── 示例：onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleClick(); }}
├── ESC 键
│   ├── 关闭模态框 / 弹窗 / 下拉菜单
│   ├── 示例：onKeyDown={(e) => { if (e.key === 'Escape') closeModal(); }}
│   └── 提高用户体验
├── 焦点管理
│   ├── 模态框打开时：将焦点移到模态框内容
│   ├── 模态框关闭时：焦点恢复到打开按钮
│   ├── 使用 focus() 或 ref.current.focus()
│   └── 工具：react-focus-lock（React）、@headlessui（UI 库）
├── 焦点陷阱（Focus Trap）
│   ├── 用途：在模态框中循环 Tab 键，不能跳出
│   ├── 实现：监听 Tab 键，循环焦点到第一个/最后一个元素
│   └── 库：focus-trap（原生）、react-focus-lock（React）
└── 避免键盘陷阱
    ├── 🔴 禁止：用 aria-hidden="true" 隐藏可聚焦元素
    ├── 后果：用户按 Tab 后无法恢复，失去操作能力
    └── 正确方法：用 display: none 或 visibility: hidden
```

**键盘导航示例**
```typescript
// React 焦点陷阱实现
import { useEffect, useRef } from 'react';

function Modal({ isOpen, onClose }) {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    // ESC 关闭模态框
    document.addEventListener('keydown', handleKeyDown);

    // 焦点陷阱：循环 Tab 导航
    const modal = modalRef.current;
    const focusableElements = modal?.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements?.[0] as HTMLElement;
    const lastElement = focusableElements?.[focusableElements.length - 1] as HTMLElement;

    // 打开时聚焦第一个元素
    firstElement?.focus();

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        // Shift + Tab：向上导航
        if (document.activeElement === firstElement) {
          lastElement?.focus();
          e.preventDefault();
        }
      } else {
        // Tab：向下导航
        if (document.activeElement === lastElement) {
          firstElement?.focus();
          e.preventDefault();
        }
      }
    };

    modal?.addEventListener('keydown', handleTabKey);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      modal?.removeEventListener('keydown', handleTabKey);
    };
  }, [isOpen, onClose]);

  return (
    <div ref={modalRef} role="dialog" aria-modal="true">
      {/* 模态框内容 */}
    </div>
  );
}
```

### 颜色对比度与视觉设计

```
颜色对比度检查标准（WCAG 2.1）：
├── 正文文本：对比度 ≥ 4.5:1（AA 级别）
│   ├── 正常尺寸字体（< 18px 或 < 14px 粗体）
│   └── 例：#000 on #fff = 21:1（✅ 充足）
├── 大文本：对比度 ≥ 3:1（AA 级别）
│   ├── 18px+ 或 14px+ 粗体字体
│   └── 例：#666 on #fff = 7:1（✅ 充足）
├── 图形和 UI 组件：对比度 ≥ 3:1
│   ├── 图表线条、图标、边框、焦点指示器
│   └── 例：蓝色按钮边框 on 白色背景
├── 检查工具
│   ├── Contrast Ratio（contrast-ratio.com）
│   ├── Chrome DevTools → Lighthouse
│   ├── WebAIM Color Contrast Checker
│   └── 自动化：@axe-core/react、jest-axe
└── 设计指导
    ├── 🔴 禁止：仅靠颜色区分状态（如错误 = 红色）
    ├── 应该：同时使用文字、图标、颜色（多种视觉提示）
    └── 示例：错误输入框 = 红色边框 + ❌ 图标 + 错误文本
```

**颜色对比度示例**
```html
<!-- ❌ 不好：灰色文本在白色背景上，对比度不足 -->
<p style="color: #999; background: white;">这是灰色文本</p>

<!-- ✅ 好：黑色文本在白色背景上，对比度充足 -->
<p style="color: #000; background: white;">这是黑色文本</p>

<!-- ❌ 不好：仅靠颜色表示错误 -->
<div style="border: 2px solid red;">邮箱不能为空</div>

<!-- ✅ 好：颜色 + 图标 + 文本 -->
<div style="border: 2px solid red; color: red;">
  ❌ 邮箱不能为空
</div>
```

### 可访问性自动化测试

```
在 CI/CD 流程中集成无障碍检查：
├── axe-core（推荐）
│   ├── 官方：npm install --save-dev @axe-core/react axe-jest-matchers
│   ├── 集成到测试文件：
│   │   import { axe, toHaveNoViolations } from 'jest-axe';
│   │   expect.extend(toHaveNoViolations);
│   └── 用法：const results = await axe(container); expect(results).toHaveNoViolations();
├── jest-axe（React Testing Library）
│   ├── 方便集成到现有测试流程
│   └── 自动扫描渲染的组件
├── vue-axe（Vue）
│   ├── 开发环境插件，实时反馈无障碍问题
│   └── 安装：npm install --save-dev vue-axe
├── Lighthouse CI
│   ├── 自动化 Lighthouse 审计（包括无障碍评分）
│   ├── 设置门禁：无障碍分数 ≥ 90
│   └── 集成：lighthouse-ci
└── 手动测试（关键）
    ├── 键盘导航：使用 Tab、Shift+Tab、ESC 导航整个页面
    ├── 屏幕阅读器：用 NVDA（Windows）或 VoiceOver（Mac）测试
    └── 放大与缩放：150% 缩放下是否仍可使用
```

**jest-axe 测试示例**
```typescript
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

describe('LoginForm Accessibility', () => {
  it('should have no accessibility violations', async () => {
    const { container } = render(<LoginForm />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have proper label association', () => {
    render(<LoginForm />);
    const emailInput = screen.getByLabelText(/邮箱/i);
    expect(emailInput).toHaveAttribute('type', 'email');
  });

  it('should show error messages with role="alert"', () => {
    render(<LoginForm onSubmit={() => {}} />);
    screen.getByRole('button').click();
    expect(screen.getByRole('alert')).toHaveTextContent(/邮箱不能为空/i);
  });
});
```

---

## 七、构建与部署规范（新增）

### 环境变量管理

```
环境变量分层策略：
├── 文件优先级（覆盖顺序从低到高）
│   ├── .env                  ：默认值，必须提交到 git
│   ├── .env.development      ：开发环境特定值，提交到 git
│   ├── .env.production       ：生产环境特定值，提交到 git
│   ├── .env.test             ：测试环境特定值，提交到 git
│   ├── .env.local            ：本地覆盖（gitignore），不提交
│   ├── .env.[mode].local     ：特定模式的本地覆盖，不提交
│   └── 系统环境变量           ：最高优先级
├── 敏感变量管理
│   ├── API Key、密钥、数据库密码：仅放 .env.local 或 CI 环境变量
│   ├── 禁止提交到 git，使用 .gitignore：*.local
│   └── CI/CD 中：使用 GitHub Secrets / GitLab Variables
├── 前缀规范（框架要求）
│   ├── Vite / Vue：VITE_ 前缀（客户端可访问）
│   ├── Next.js：NEXT_PUBLIC_ 前缀（客户端可访问）
│   ├── Create React App：REACT_APP_ 前缀（客户端可访问）
│   └── 其他环境变量（服务器端）：无特殊前缀
└── 🔴 禁止事项：
    ├── 硬编码 API 端点、密钥到源代码
    ├── 在 npm scripts 中暴露敏感变量
    └── 提交包含敏感数据的 .env 文件到 git
```

**.env 文件示例**
```bash
# .env（默认值，提交到 git）
VITE_API_URL=http://localhost:3000
VITE_LOG_LEVEL=debug

# .env.development（开发环境，提交到 git）
VITE_API_URL=http://localhost:3000
VITE_LOG_LEVEL=debug

# .env.production（生产环境，提交到 git）
VITE_API_URL=https://api.example.com
VITE_LOG_LEVEL=error

# .env.local（本地覆盖，gitignore）
VITE_API_KEY=sk-xxxxxxxxxxxx
VITE_DEBUG_MODE=true

# vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // 自动加载 .env 文件
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
  },
});

// src/api.ts
const apiUrl = import.meta.env.VITE_API_URL;
const apiKey = import.meta.env.VITE_API_KEY;  // 客户端无法访问（无 VITE_ 前缀）
```

### 静态资源版本策略

```
缓存策略与资源版本控制：
├── 构建产物命名
│   ├── Content Hash：基于文件内容生成哈希值
│   ├── 示例：main.a1b2c3d4.js（内容变化哈希值才变化）
│   ├── 配置：output.filename = '[name].[contenthash:8].js'
│   └── 好处：变更才更新，减少客户端缓存失效
├── 缓存策略分层
│   ├── 静态资源：Cache-Control: max-age=31536000（1 年）
│   │   ├── JS、CSS、字体、图片（含 hash 的）
│   │   └── 用户刷新或强制刷新才重新获取
│   ├── HTML 入口：Cache-Control: no-cache 或 max-age=300（5 分钟）
│   │   ├── 每次都检查是否有新版本
│   │   └── 保证用户总能获取最新 HTML
│   └── API 响应：根据业务需求（通常不缓存或短期缓存）
├── Service Worker / CDN 缓存
│   ├── 使用 Workbox 生成 Service Worker（自动管理缓存）
│   ├── CDN 配置缓存规则
│   └── 清除旧版本资源
└── 版本检测
    ├── 监听 HTML 版本变化，prompt 用户刷新
    ├── 或使用 Service Worker 自动更新
    └── 工具：npm-check-updates、depcheck
```

**Vite 构建配置**
```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        entryFileNames: '[name].[hash:8].js',
        chunkFileNames: '[name].[hash:8].js',
        assetFileNames: '[name].[hash:8].[ext]',
      },
    },
    // 代码分割
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom'],
          'vendor-ui': ['@mui/material'],  // 将第三方库分割
        },
      },
    },
  },
});

// 服务器配置（Nginx 示例）
server {
  listen 80;
  server_name example.com;

  root /var/www/html;

  # HTML 入口：不缓存
  location = /index.html {
    add_header Cache-Control 'no-cache';
  }

  # 静态资源（含 hash）：长期缓存
  location ~* \.([0-9a-f]{8})\. {
    add_header Cache-Control 'max-age=31536000';
  }

  # 其他资源：短期缓存
  location ~ ^/assets/ {
    add_header Cache-Control 'max-age=3600';
  }
}
```

### Source Map 策略

```
Source Map 管理与错误监控：
├── 开发环境
│   ├── 推荐：cheap-module-source-map（快速重建）
│   ├── 特点：映射到编译前的源代码，不含列号
│   └── 配置：devtool: 'cheap-module-source-map'
├── 生产环境
│   ├── 推荐：hidden-source-map（完整映射，不公开）
│   ├── 特点：生成 .map 文件，但不在生产 JS 中引用
│   ├── 上传到错误监控服务（Sentry、Datadog）
│   └── 配置：devtool: 'hidden-source-map'
├── 🔴 严禁：inline-source-map / source-map（生产环境）
│   ├── 原因：将源码内联在生产 JS 中，泄露源代码
│   ├── 后果：竞争对手和恶意用户可直接看到源码
│   └── 检查：确保 .map 文件不在生产环境 public 目录
├── 错误监控集成
│   ├── Sentry：自动捕获错误并映射源代码
│   │   └── npm install @sentry/react @sentry/tracing
│   ├── Datadog：上传 source map 后才能看到源代码错误堆栈
│   ├── 上传流程：CI 中构建后上传 .map 文件到监控服务
│   └── 清理：定期删除过期的 source map（通常保留 30 天）
└── 本地调试
    ├── 开发模式全量 source map
    ├── 可以在浏览器 DevTools 看到原始 TypeScript 代码
    └── 生产调试：下载对应版本的 .map 文件到本地，加载到 DevTools
```

**Sentry 集成示例**
```typescript
// src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import * as Sentry from '@sentry/react';
import { BrowserTracing } from '@sentry/tracing';
import App from './App';

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.MODE,
  integrations: [
    new BrowserTracing(),
    new Sentry.Replay({ maskAllText: false, blockAllMedia: false }),
  ],
  // 性能监控采样率
  tracesSampleRate: import.meta.env.MODE === 'production' ? 0.1 : 1.0,
  // 错误采样率
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});

const SentryApp = Sentry.withProfiler(App);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <SentryApp />
  </React.StrictMode>,
);

// vite.config.ts
import { sentryVitePlugin } from '@sentry/vite-plugin';

export default defineConfig({
  plugins: [
    react(),
    sentryVitePlugin({
      org: 'your-org',
      project: 'your-project',
      authToken: process.env.SENTRY_AUTH_TOKEN,
    }),
  ],
  build: {
    sourcemap: true,  // 生成 source map
    rollupOptions: {
      output: {
        entryFileNames: '[name].[hash:8].js',
        chunkFileNames: '[name].[hash:8].js',
        assetFileNames: '[name].[hash:8].[ext]',
      },
    },
  },
});

// CI 上传 source map（GitHub Actions 示例）
- name: Upload source maps to Sentry
  run: |
    npm install -g @sentry/cli
    sentry-cli releases files upload-sourcemaps ./dist \
      --org your-org \
      --project your-project \
      --release ${{ github.sha }}
```

### CI 集成检查清单

```
前端项目 CI 流程（GitHub Actions / GitLab CI 示例）：
├── 依赖安装与缓存
│   ├── npm ci（使用 package-lock.json，避免版本不确定）
│   └── 缓存 node_modules（加速构建）
├── 1️⃣ 类型检查（TypeScript 项目）
│   ├── 命令：tsc --noEmit
│   ├── 检查：变量类型、函数签名、接口兼容性
│   └── 可选：eslint --max-warnings 0（严格 lint）
├── 2️⃣ 代码检查与格式化
│   ├── ESLint：npm run lint（检查代码质量）
│   ├── Prettier：npm run format:check（检查代码格式）
│   └── 可选：Stylelint（样式检查）
├── 3️⃣ 单元测试与组件测试
│   ├── 运行：npm run test:ci
│   ├── 覆盖率：覆盖率 > 70%，失败则 CI 失败
│   └── 报告：生成 coverage 报告上传到 Codecov / Coveralls
├── 4️⃣ 构建
│   ├── npm run build（使用生产配置）
│   ├── 检查输出文件（dist/）
│   └── 失败则 CI 失败
├── 5️⃣ Bundle 体积检查（可选但推荐）
│   ├── 工具：size-limit、bundlesize
│   ├── 规则：新增代码 > 50KB 则警告 / 失败
│   ├── 命令：npm run bundle:analyze
│   └── 输出：bundle 体积对比（vs. main 分支）
├── 6️⃣ 可访问性检查（可选）
│   ├── @axe-core/react 或 jest-axe
│   ├── 自动扫描渲染的组件
│   └── 某些违规可接受（如 icon-button）
└── 7️⃣ Lighthouse CI（可选）
    ├── 命令：npm run lighthouse:ci
    ├── 门禁：性能 ≥ 80、可访问性 ≥ 90、最佳实践 ≥ 85
    └── 失败则 CI 失败
```

**GitHub Actions 示例**
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-and-build:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        node-version: [18.x, 20.x]

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      # 1️⃣ 类型检查
      - name: Type check
        run: npm run type-check

      # 2️⃣ Lint 和格式检查
      - name: Lint
        run: npm run lint

      - name: Format check
        run: npm run format:check

      # 3️⃣ 测试
      - name: Run tests
        run: npm run test:ci

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json

      # 4️⃣ 构建
      - name: Build
        run: npm run build

      # 5️⃣ Bundle 分析
      - name: Analyze bundle
        run: npm run bundle:analyze

      # 6️⃣ 可访问性检查
      - name: A11y check
        run: npm run test:a11y

      # 7️⃣ Lighthouse CI
      - name: Run Lighthouse CI
        uses: treosh/lighthouse-ci-action@v9
        with:
          configPath: './lighthouserc.json'

  # 单独的部署 job
  deploy:
    needs: test-and-build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 20.x
          cache: 'npm'

      - name: Install and build
        run: |
          npm ci
          npm run build

      - name: Deploy to production
        run: |
          # 部署脚本（如 rsync、docker push 等）
          npm run deploy
```

---

## 总结与关键点

| 类别 | 关键规范 |
|------|----------|
| **测试** | TDD 先行，覆盖率 > 70%，必须覆盖 P0 流程 |
| **组件测试** | Testing Library + MSW Mock，避免快照测试 |
| **样式** | 统一 CSS 方案，使用 design tokens，响应式 mobile-first |
| **状态管理** | 分层管理，仅当必要才全局化，数据获取用专门库 |
| **性能** | LCP < 2.5s，CLS < 0.1，路由级分割，图片 WebP 懒加载 |
| **无障碍** | 语义化 HTML，ARIA 标签，键盘导航，对比度检查 |
| **构建与部署** | 环境变量分层，content hash 缓存，CI 自动化检查 |
```
