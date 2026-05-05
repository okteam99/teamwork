# 评审 Scope 标准（v7.3.10+P0-85 单源）

> 🔴 **本文件是 Teamwork 框架内 review_scope 维度的唯一权威源**。各 role / stage / template 涉及 scope 一律 cite 本文件。
>
> 与 [review-verdict.md](./review-verdict.md) 协作：verdict 管"判得对不对"，scope 管"判什么 / 不判什么"。

---

## 一、Scope 三类

```
review_scope: prd | blueprint | code-review
```

| Scope | 评审对象 | 触发 stage | 评审者关注 |
|-------|---------|-----------|-----------|
| **prd** | PRD.md（产品视角文档）| Goal-Plan Stage 子步骤 3 | 业务可行性 / AC 可测性 / 用户故事完整性 / 业务方向 |
| **blueprint** | TECH.md / TC.md（技术方案 + 测试计划）| Blueprint Stage | 架构合理性 / 接口设计 / 测试规划 / 性能 / 安全 |
| **code-review** | 代码 + 单测 + 集成测试 | Review Stage | 实现正确性 / TDD 规范 / 模块设计 / 日志完整性 / 第三方依赖真实性 |

---

## 二、Scope 边界（哪些该审 / 哪些不该）

### 2.1 prd scope（Goal-Plan Stage）

```
✅ 该审：
├── 业务方向（PL 视角）
├── 用户故事完整性 / 验收标准 AC（PM 视角）
├── 技术可行性（PRD 是否能实现 · 不审具体实现 · RD 视角）
├── AC 可测试性（不审具体测试用例 · QA 视角）
└── UI/UX 完整性（不审视觉细节 · Designer 视角）

❌ 不该审（→ 移到 blueprint scope）：
├── 接口 schema 设计
├── 数据模型 / migration
├── 异常处理实现细节（重试 / 降级 / 兜底）
├── 性能实现方案
├── 复用既有库 / 模式
├── 具体测试用例
├── 集成测试规划 / 性能测试规划 / ROLLBACK 测试
├── 视觉风格约束 / token 设计 / 全景同步细节
└── ADR 触发判定（→ Blueprint Stage 架构师评审时判 · P0-78 三条门槛）
```

### 2.2 blueprint scope（Blueprint Stage）

```
✅ 该审：
├── 架构合理性 / 模块设计（Architect 视角 · 删除测试 + 两个 adapter 才抽象 P0-78）
├── 接口 schema / 数据模型（RD 视角）
├── 异常处理实现策略 / 性能方案 / 安全（RD + Architect 视角）
├── 测试用例完整性（QA 视角）
├── 集成测试 / 性能测试 / ROLLBACK 测试规划
├── ADR 触发判定（三条门槛 + 7 类合格列表 P0-78）
└── 第三方依赖真实性（external 视角）

❌ 不该审（→ 移到 code-review scope）：
├── 具体代码实现（变量命名 / 局部逻辑）
├── 测试代码细节（assert 写法）
├── TDD 红绿循环执行情况
└── 代码层 bug
```

### 2.3 code-review scope（Review Stage）

```
✅ 该审：
├── 实现正确性 / 业务逻辑 bug（QA + RD 视角）
├── 代码规范 / 可读性 / 复用（QA + Architect 视角）
├── TDD 规范执行（QA 视角 · cite standards/tdd.md）
├── 模块设计实现 / 架构一致性（Architect 视角）
├── 性能瓶颈 / 安全漏洞（Architect 视角）
├── 日志完整性（Architect 视角 · P0-69 三段式：INFO + ERROR + 脱敏）
├── 集成测试代码完整性（QA 视角）
├── ARCHITECTURE.md 同步（Architect 视角）
└── 第三方依赖真实性 / 并发安全（external 视角）

❌ 不该审（已在前置 stage 锁定）：
├── PRD 业务方向（Goal-Plan 已锁）
├── 技术方案大方向（Blueprint 已锁）
└── 测试用例规划（Blueprint TC 已锁）
```

---

## 三、Scope 越界拦截

🔴 **PMO 在评审 finding 整合时检查 scope 越界**：

| 越界类型 | PMO 动作 |
|---------|---------|
| reviewer 在 prd scope 提技术实现细节 finding（如接口 schema）| 标 finding 为 `out_of_scope: true` + 说明"该 finding 应在 Blueprint Stage 由 RD 评审 TECH.md 时提" + 不阻塞当前 verdict |
| reviewer 在 blueprint scope 提代码细节 finding | 同上 · 标延后到 Review Stage |
| reviewer 在 code-review scope 翻 PRD 业务方向 | 视为越界 · 不接受（PRD 已锁定 · 必须用户重启 Goal-Plan）|

---

## 四、Scope 与 Stage 的映射

```
Goal-Plan Stage  ── review_scope = "prd"        ── PRD.md
                                                    └─ PRD-REVIEW.md.reviews[].review_scope = "prd"

Blueprint Stage  ── review_scope = "blueprint"  ── TECH.md + TC.md
                                                    └─ TECH-REVIEW / TC-REVIEW（如有）.reviews[].review_scope = "blueprint"

Review Stage     ── review_scope = "code-review" ── 代码 + 单测 + 集成测试
                                                    └─ REVIEW.md.reviews[].review_scope = "code-review"
```

---

## 五、与其他规范的协作

| 规范 | 协作点 |
|------|-------|
| `standards/review-verdict.md` | scope 管"评什么" · verdict 管"评得对不对" · 两者正交 |
| `templates/prd.md` PRD-REVIEW schema | `reviews[].review_scope` enum 引用本文件三类 |
| `roles/*.md` | 各 role 评审职责段引用本文件 scope 边界（不重复定义）|
| `stages/{goal-plan,blueprint,review}-stage.md` | 各 stage 描述本 stage 对应 scope + cite 本文件 |

---

## 六、版本记录

- v7.3.10+P0-85（首次发布）：抽取 review_scope 三类 + 边界 + 越界拦截到单源
