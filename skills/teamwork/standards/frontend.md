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
