# Review Stage：三路并行代码审查

> Dev Stage 通过后，PMO 启动本 Stage。内部并行执行架构师 Code Review + Codex Review + QA 代码审查，一次性返回全部审查结果。

---

## 一、设计意图

```
三个 review 并行执行，各自独立视角：

├── 架构师 Code Review：架构合理性、代码规范、ARCHITECTURE.md 同步
├── Codex Review：外部模型独立审查，发现同模型盲区（第三方依赖验证、安全漏洞）
└── QA 代码审查：TC 逐条验证覆盖、TDD 规范检查、测试质量

🎯 收益：
├── 三个 review 看同一份代码，发现可合并为 1 轮修复
├── 并行执行，总时间 = 最长的那个 review，而不是三者之和
└── 各 review 独立，互不锚定（🔴 Codex 不看架构师报告）
```

---

## 二、内部并行结构

```
┌─────────────────────────┬─────────────────────────┬─────────────────────────┐
│ 架构师 Code Review      │ Codex Review            │ QA 代码审查             │
│ 规范：agents/           │ 规范：Codex CLI /       │ 规范：agents/           │
│ arch-code-review.md     │ 降级 Sonnet             │ qa-code-review.md       │
│                         │                         │                         │
│ 审查维度：              │ 审查维度：              │ 审查维度：              │
│ ├── 架构合理性          │ ├── 逻辑正确性          │ ├── TC 逐条覆盖验证     │
│ ├── 代码规范            │ ├── 安全漏洞            │ ├── TDD 规范检查        │
│ ├── 性能/安全           │ ├── 第三方依赖真实性    │ ├── 集成测试覆盖检查    │
│ └── ARCHITECTURE.md     │ ├── 并发安全            │ ├── 用户行为边界        │
│     同步更新            │ └── 代码质量            │ └── 架构文档一致性      │
└────────────┬────────────┴────────────┬────────────┴────────────┬────────────┘
             ↓                         ↓                         ↓
                        PMO 汇合三份报告
```

---

## 三、输入文件

```
PMO 启动时注入（三个 review 共用）：
├── agents/README.md                                ← 通用规范
├── stages/review-stage.md                          ← 本文件
├── docs/features/F{编号}-{功能名}/PRD.md           ← 需求文档
├── docs/features/F{编号}-{功能名}/TC.md            ← 测试用例
├── docs/features/F{编号}-{功能名}/TECH.md          ← 技术方案
├── Dev Stage 执行报告（RD 自查报告）
├── 代码变更文件列表（git diff --name-only）
├── {SKILL_ROOT}/standards/common.md                ← 通用开发规范
│
各 review 专属输入：
├── 架构师 CR → 额外注入 ARCHITECTURE.md
├── Codex Review → 🔴 不注入架构师 CR 报告（保持独立性）
└── QA 代码审查 → 额外注入 TC 完整内容
```

---

## 四、执行流程

```
🔴 进度追踪：每个 Step 开始时报告进度（宿主支持 TodoWrite 时使用，否则输出 markdown 进度块），禁止黑盒执行。

Step 1: 读取本文件 + agents/README.md

Step 2: 并行启动三个 review
        ├── 架构师 Code Review（按 agents/arch-code-review.md）
        ├── Codex Review（Codex CLI 或降级 Sonnet，prompt 模板见原 review-stage.md §五）
        └── QA 代码审查（按 agents/qa-code-review.md）

Step 3: 汇合三份报告
        ├── 合并问题清单（去重：同一文件同一位置的问题只保留最严重的）
        ├── 按严重程度排序：🔴 阻塞 > 🟡 建议修复 > 🟢 建议优化
        └── 确定返回状态

Step 4: 输出 Review Stage 执行报告
```

---

## 五、返回状态

```
| 状态 | 条件 | PMO 处理 |
|------|------|----------|
| ✅ DONE | 三个 review 均无阻塞问题 | 继续 → Test Stage |
| ⚠️ DONE_WITH_CONCERNS | 有 🟡 建议但无 🔴 阻塞 | PMO 评估，非阻塞则继续 |
| 🔁 NEEDS_FIX | 任一 review 发现 🔴 阻塞问题 | RD 修复 → PMO 判断重跑哪些 review |
| ❌ FAILED | Codex CLI 不可用 / 执行异常 | ⏸️ 用户选择：解决 / 降级 Sonnet / 跳过 Codex |
```

---

## 六、修复循环

```
Review Stage 返回 NEEDS_FIX 时：

Step 1: PMO 合并三份 review 的问题清单
        ├── 去重（同一问题被多个 review 发现 → 合并为一条）
        └── 输出给 RD 的修复清单

Step 2: RD 修复（PMO dispatch RD Fix）
        ├── 按修复清单逐项修复
        └── 跑单测确认无回归

Step 3: PMO 判断重跑范围
        ├── 修复范围 ≤2 文件且无逻辑变更 → 只重跑发现问题的 review
        ├── 修复涉及逻辑变更 → 全部三个 review 重跑
        └── 🔴 修复-重跑循环最多 3 轮，超出 → ⏸️ 用户

Codex Review 独立性保障：
├── 重跑时 Codex 仍不看架构师 CR 报告
├── Codex 的问题由 RD + 架构师评估后决定是否采纳
└── 第三方依赖验证除外——Codex 说"不存在"的包应严肃对待
```

---

## 七、输出与落盘

> 🔴 Review Stage 完成后必须将结论落盘到 `{功能目录}/REVIEW.md`，不能只返回给 PMO。

**落盘文件**：`docs/features/{功能目录}/REVIEW.md`

```markdown
# {功能名} - Code Review 汇总

## 状态
{DONE / DONE_WITH_CONCERNS / NEEDS_FIX}（{日期}）

## 审查概况
| 审查方 | 状态 | 问题数 |
|--------|------|--------|
| 架构师 CR | {PASS / NEEDS_FIX} | 🔴{x} 🟡{y} 🟢{z} |
| Codex Review | {PASS / NEEDS_FIX / FAILED / 跳过} | 🔴{x} 🟡{y} 🟢{z} |
| QA 代码审查 | {PASS / NEEDS_FIX} | 🔴{x} 🟡{y} 🟢{z} |

## 合并问题清单（去重后）
| # | 来源 | 严重程度 | 文件 | 位置 | 问题 | 建议 | 状态 |
|---|------|----------|------|------|------|------|------|
| 1 | 架构师 | 🔴 | src/... | L42 | ... | ... | 待修复/已修复/忽略 |

## 架构师 Code Review 详情
{按 agents/arch-code-review.md 输出格式}

## Codex Review 详情
{按 Codex prompt 模板输出格式}

## QA 代码审查详情
{按 agents/qa-code-review.md 输出格式}

## 修复记录（如有）
| 轮次 | 修复内容 | 重跑范围 | 结果 |
|------|----------|----------|------|

## ARCHITECTURE.md 更新
{已更新 / 无需更新}
```

**PMO 返回报告**（同时返回给 PMO 用于流转决策）：
```
📋 Review Stage 执行报告（F{编号}-{功能名}）
├── 最终状态：{DONE / DONE_WITH_CONCERNS / NEEDS_FIX / FAILED}
├── 合并问题数：🔴 {x} / 🟡 {y} / 🟢 {z}
├── 落盘文件：docs/features/{功能目录}/REVIEW.md
└── 详见 REVIEW.md
```

---

## 八、红线

```
🔴 进度可见：每个 Step 必须报告进度（TodoWrite 或 markdown 进度块），禁止黑盒执行
🔴 独立性：Codex 不看架构师 CR 报告，三个 review 互不锚定
🔴 完整性：每个 review 必须按各自规范完整执行，不能因为另一个 review 通过就简化
🔴 不修复：Review Stage 只审查不改代码，发现问题返回 PMO 安排 RD 修复
🔴 循环控制：修复-重跑最多 3 轮
```
