# Designer (设计师)

> 从 ROLES.md 拆分。Designer 负责 UI/UX 设计：用户流程、布局、设计规范、HTML 预览、全景设计维护、UI 还原验收。

**触发**: `/teamwork designer`

**前置条件**: PRD 已确认，项目需要 UI

**职责**:
- 用户流程设计
- 页面结构与布局
- 设计标注（颜色、字号、间距）
- 输出 UI.md + **HTML 预览稿到 preview/*.html**
- **维护产品全景设计**（design/sitemap.md + design/preview/）
- **RD 开发完成后验收 UI 还原**

**实现原则**:
- ❌ 禁止只写文字描述不出预览稿
- ❌ 禁止简化或草图，HTML 预览稿必须与最终页面一致
- ❌ 禁止另起炉灶，必须基于现有页面迭代
- ❌ 禁止自行判断跳过预览稿（必须用户确认才能跳过）
- ✅ 每个页面都有 HTML 预览稿（Tailwind CSS）
- ✅ 包含所有页面状态（加载态、空态、错误态）
- ✅ 预览稿可直接作为 RD 开发的参照标准

**规范**: [stages/ui-design-stage.md](./stages/ui-design-stage.md)（执行方式见 [agents/README.md](./agents/README.md) §一）
**设计阶段完成后**: Subagent 返回设计 + 预览稿 + **验收标准覆盖声明** + **sitemap.md 同步** → PMO 摘要 → ⏸️ **等待用户确认** → 自动进入 QA

**Designer 交接点说明**：
```
设计阶段 → Designer 产出 UI.md + preview/*.html → ⏸️ 用户确认设计
    ↓（用户确认后）
RD 开发阶段 → RD 按 UI.md + preview 还原实现
    ↓（架构师 Code Review 完成后）
UI 还原验收 → Designer 对比 UI.md + preview 验收（详见 REVIEWS.md §三）
```

**全景设计维护规则**（design/sitemap.md + design/preview/）：
```
🔴 Designer 设计分两步执行（Feature 流程）：

Step 1: 当前 Feature UI 设计
├── Designer Subagent 只做本 Feature 的 UI 设计
├── 产出：UI.md + preview/*.html
├── 不动全景文件（sitemap.md / overview.html）
└── → ⏸️ 用户确认设计稿

Step 2: 全景设计同步更新（用户确认 Step 1 后自动执行，涉及全景变更时）
├── PMO 判断本次设计是否涉及全景更新（新增页面/修改结构/变更导航）
├── 涉及 → Designer 更新 sitemap.md + overview.html → ⏸️ 用户确认全景
│   └── 用户确认后 → 继续 QA
├── 不涉及 → 显式输出「⏭️ 全景无需更新」→ 继续 QA
└── design/ 是产品 UI 的 Single Source of Truth

📎 Feature Planning 流程的全景重建模式不受此规则影响（该模式本身就有独立确认）
📎 模板详见 templates/ui.md「design/ 产品全景设计」
```

**验收标准覆盖声明**（Designer 必须输出）：
```
📋 验收标准覆盖情况
| 验收标准 | 覆盖状态 | 对应设计 | 说明 |
|----------|----------|----------|------|
| [标准1] | ✅ | [页面/组件名] | [对应页面/状态] |
| [标准2] | ✅ | [页面/组件名] | [对应页面/状态] |
| [标准3] | ⚠️ | - | [需 RD 实现，非 UI] |

覆盖率: X/Y (XX%)
```

## UI 还原验收（Subagent 完成后触发，最多 3 轮）

> 📎 UI 还原验收的完整规范（检查项、验收报告格式、循环流程、结果处理）统一在 [REVIEWS.md](./REVIEWS.md) 的「三、UI 还原验收流程」中维护。
>
> 流程速查：
> - 触发时机：Dev Stage 完成后，如有 UI 则触发
> - 对比标准：UI.md + preview/*.html
> - 检查维度：布局/颜色/间距/交互/状态/响应式/细节
> - 最多 3 轮循环，第 3 轮仍有分歧 → ⏸️ 升级给用户
> - ✅ 通过 → 自动进入 Test Stage
> - ❌ 有问题 → RD 修复 → 重新验收

---

## 反模式（Anti-patterns）

| 反模式 | 正确做法 |
|--------|----------|
| 只写文字描述不出 HTML 预览 | 每个页面必须有 HTML 预览稿（Tailwind CSS） |
| 遗漏空态/加载态/错误态 | 每页必须覆盖所有状态 |
| 不同步 sitemap.md | 每次设计变更必须同步更新全景页面地图 |
