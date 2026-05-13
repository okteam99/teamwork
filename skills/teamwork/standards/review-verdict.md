# 评审 Verdict 标准（v7.3.10+P0-85 单源）

> 🔴 **本文件是 Teamwork 框架内所有评审 verdict 的唯一权威源**。各 role / stage / template 中涉及 verdict 一律 cite 本文件，不在本文件以外另立等级或触发条件。
>
> 适用场景：Goal-Plan PRD 评审 / Blueprint TECH/TC 评审 / Review 代码评审 / PM 验收 / 任何 finding-driven 评审循环。

---

## 一、Verdict 三等级（统一定义）

```
✅ PASS                — 无任何 finding 或仅含 info severity
⚠️ PASS_WITH_CONCERNS  — 含 ≥1 个 SHOULD-fix concern · 不阻塞流转 · 但触发 PM 回应循环
🔁 NEEDS_REVISION      — 含 ≥1 个 MUST-fix finding · 阻塞流转 · 必须修订重审
```

### 等级 → 流转决策

| Verdict | 流转 | 后续动作 |
|---------|------|---------|
| PASS | 🚀 自动 | 进入下一 stage / 子步骤 |
| PASS_WITH_CONCERNS | 🚀 自动（v7.3.10+P0-51 扩展）| 触发 PM 回应循环（finding 必须 ADOPT/REJECT/DEFER + 对抗自查 P0-34-B）+ 不强制修订 PRD |
| NEEDS_REVISION | 🔁 回退 | PM/RD 修订 → 重审（最多 3 轮 · Review Stage 例外 5 轮 v7.3.10+P0-139 · 超限 ⏸️ 用户决策 P0-34）|

---

## 二、Finding Severity 三级（与 Verdict 联动）

```
🔴 MUST-fix      — 阻塞性 finding · 触发 NEEDS_REVISION
🟡 SHOULD-fix    — 建议性 finding · 触发 PASS_WITH_CONCERNS
🟢 NICE-to-have  — 优化性 finding · 不影响 verdict（但记录在案 · PM 可选 ADOPT）
```

### Severity 判定规则（reviewer 必遵守）

```
🔴 MUST-fix（任一命中即升级）：
├── 业务方向偏离用户已锁定意图
├── 技术方案不可实现 / 与既有架构冲突
├── AC 不可验证 / 验收标准模糊到无法转化为测试用例
├── 红线触发（15 条绝对红线 + 破坏性操作）
├── 代码层 bug（实现错误 / 安全漏洞 / 数据丢失风险）
├── 关键路径日志缺失（架构师 6.1 ERROR 日志 · 强制 BLOCKER）
└── 第三方依赖不真实（external 评审专属）

🟡 SHOULD-fix：
├── 边界场景描述不完整（用户感知层面）
├── AC 描述可改进但仍可测试
├── 模块设计可优化但不阻塞
├── 关键路径 INFO 日志缺失（架构师 6.2 · concern 兜底 P0-69）
├── 命名 / 注释 / 代码可读性问题
└── ADR 触发但未创建（依据三条门槛 P0-78）

🟢 NICE-to-have：
├── 命名优化建议
├── 性能微优化
├── 重构建议（非阻塞）
└── 文档补充建议（非必填）
```

---

## 三、整体 Verdict 收敛规则

**多 reviewer 时**（如 Goal-Plan 子步骤 3 的 QA + RD + Designer · Review Stage 的 architect + QA + external）：

```
overall_verdict 收敛规则（PMO 整合）：
├── 任一 reviewer = NEEDS_REVISION → overall = NEEDS_REVISION（最严胜出）
├── 无 NEEDS_REVISION 但有 ≥1 reviewer = PASS_WITH_CONCERNS → overall = PASS_WITH_CONCERNS
└── 全部 reviewer = PASS → overall = PASS
```

---

## 四、PM 回应规则（finding-driven 评审循环）

> 适用于触发 PM 回应循环的所有评审场景（Goal-Plan 子步骤 4 / Blueprint PM 评审段 / 用户 finding 等）。

### 4.1 三种回应（保留 P0-34）

| 决策 | 含义 | 必填字段 |
|------|------|---------|
| **ADOPT** | 接受 finding 建议 + 修订产物 | `rationale: "已修订：{改了什么 + 段落引用}"` + `adversarial_self_check`（P0-34-B）|
| **REJECT** | 拒绝 finding · 给反驳理由 | `rationale: "反方论据为何不成立 + 替代方案"` + `adversarial_self_check`（P0-34-B）|
| **DEFER** | 延后处理 | `category: business-decision`（P0-34-A 严格收紧 · 仅业务决策类允许）+ `rationale: "延后理由 + 追踪位置 + 上升给用户决策的具体问题"` |

### 4.2 对抗自查（P0-34-B 物理拦截）

🔴 **每条 ADOPT/REJECT 必含非空 `adversarial_self_check`**（≥2 句反方最强论据模拟）· 否则视为对抗强度不足 · PMO 打回。

```
adversarial_self_check 模板：
"站在 finding 提出方视角写最强反驳论据（≥2 句具体内容）。
 示例（finding 由 RD 提，PM 想 REJECT）：
 'RD 反方最强论据：当前 PRD 接口缺 token 刷新策略，会导致鉴权失败回退到登录页，
  用户体验断点；如果不加，跨租户场景会出现幽灵会话。
  我的 REJECT 理由必须证明这两点不成立或代价可接受。'"
```

### 4.3 DEFER 严格收紧（P0-34-A）

🔴 `pm_response.action == "DEFER"` 时**必须** `pm_response.category == "business-decision"`（业务决策需用户最终拍板的事）· 其他类别 DEFER = 流程偏离 · PMO 校验拦截 · 打回 PM 重做。

---

## 五、循环上限（P0-34 / v7.3.10+P0-139 加 Review 例外）

```
通用 PM 回应循环 ≤ 3 轮（Goal-Plan PRD 评审 / Blueprint TC+TECH 评审）：
├── Round 1：reviewer 给 finding · PM 回应
├── Round 2：reviewer 看修订后 PRD · 给新 finding（或 PASS）· PM 再回应
├── Round 3：reviewer 终轮 · PM 终回应
└── 仍 NEEDS_REVISION → ⏸️ 用户决策（5 选 1）：
    1. 强制通过（用户接受当前状态）
    2. 继续 Round 4（用户授权延长）
    3. 修改 scope（缩小本 Feature 范围）
    4. abort（取消 Feature）
    5. 其他指示
```

🟢 **Review Stage 例外（v7.3.10+P0-139）**：代码层修复循环 ≤ **5 轮**（而非 3）· 详 [stages/review-stage.md § 修复循环规则](../stages/review-stage.md)。
- 理由：代码层 finding 修复粒度比文档层更细（单元测试 / 边界 case / 第三方依赖真实性等多视角并发），3 轮经常不够 · 5 轮覆盖典型大改动
- 超限决策菜单同上（强制通过 / 继续 Round 6 / 缩小 scope / abort / 其他）

---

## 六、与其他规范的协作

| 规范 | 协作点 |
|------|-------|
| `templates/prd.md` PRD-REVIEW frontmatter schema | `reviews[].verdict` enum 引用本文件三等级 · `findings[].severity` enum 引用本文件三级 |
| `standards/review-scope.md` | review_scope（prd / blueprint / code-review）维度 + 各 scope 的 verdict 应用 |
| `roles/*.md` | 各 role 评审职责段 cite 本文件（不重复定义 verdict / severity）|
| `stages/{goal-plan,blueprint}-stage.md` | 评审循环段 cite 本文件第五节（≤3 轮 + 超限处理）|
| `stages/review-stage.md` | 代码层修复循环 cite 本文件第五节 Review 例外（≤**5 轮** · v7.3.10+P0-139）|
| `rules/flow-transitions.md` | 评审循环 transition 引用本文件流转决策表 |

---

## 七、版本记录

- v7.3.10+P0-85（首次发布）：抽取 verdict 三等级 + severity 三级 + PM 回应规则 + 循环上限到单源；各 role/stage/template cite
