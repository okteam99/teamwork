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

---

## Goal-Plan Stage PRD 评审 checklist（v7.3.10+P0-34 新增）

> 🔗 **触发**：PMO 在 triage-stage Step 8 决策启用 Designer 视角评审 PRD（`state.goal_plan_substeps_config.review_roles[]` 含 role=designer）。
>
> **触发条件（双保险）**：
> - PRD frontmatter `requires_ui: true`
> - PMO 识别用户消息含 UI 关键词（"页面 / 按钮 / 弹窗 / 表单 / 交互 / UI / UX"等）
> - 任一命中即启用

### Designer 评审维度（PRD UI/UX 完整性视角）

| 维度 | 检查项 |
|------|-------|
| **UI 流程完整性** | PRD 涉及的所有用户操作都有对应的 UI 页面 / 状态？流程图是否覆盖完整？|
| **UI 状态全面性** | 是否考虑空状态 / 加载状态 / 错误状态 / 边界状态？AC 中是否有对应描述？|
| **响应式 / 多端** | PRD 是否涉及移动端 / 平板 / 桌面？AC 是否说明各端要求？|
| **可访问性（A11y）** | 表单 / 按钮 / 错误提示是否符合可访问性基本要求？AC 是否提到？|
| **与全景一致性** | PRD 涉及的页面在 design/sitemap.md 中位置 / 与既有页面的导航关系是否清晰？|
| **设计资源准备度** | PRD 是否需要新增设计稿 / 图标 / 配色？是否有依赖项需要先设计？|
| **埋点 / 数据可视化** | PRD 涉及的页面是否需要埋点（PV / 事件 / 业务漏斗）？AC 是否覆盖？|

### Designer 评审 verdict 标准

| Verdict | 含义 |
|---------|------|
| **PASS** | PRD 含完整 UI 流程描述，状态覆盖完整，与全景一致 |
| **PASS_WITH_CONCERNS** | PRD UI 主体清晰，有 1-2 条建议（如建议 UI Design Stage 补充某状态）|
| **NEEDS_REVISION** | PRD UI 流程不完整 / 关键状态缺失 / 与全景冲突，必须 PM 修订 |

### Subagent / 主对话模式

执行方式由 PMO 在 triage 阶段按信号决定。

- **Subagent**：含完整 UI 设计变更时（独立 UI 视角更可靠）
- **主对话**：仅小 UI 改动 / Designer 已有项目 UI 上下文累积时
