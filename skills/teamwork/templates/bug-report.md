# BUG-REPORT 模板

> 位置：`{artifact 目录}/bugfix/BUG-{缩写}-{F|B}{NNN}-{序号}.md`（artifact = Feature 目录 或标准 Bug 流程目录）
> 编号规则：详见 [docs/conventions.md § 1-2](../docs/conventions.md)（§1 顶层 artifact ID `{PREFIX}-{F|B|M}{NNN}` · §2 本 bug 报告文件 ID）
> 🔴 BUG-REPORT.md **必须包含 YAML frontmatter**（机读状态字段，承担 Bug 流程的 state.json 职能）。
> 🔴 **diagnose/dev 分工**：§现象 + §根因 + §修复方案 在 **diagnose** 阶段产出并**经用户确认**（深读代码挖真因 · frontmatter `root_cause`/`fix_summary` 非空）；实际 fix 代码 + §回归测试在 **dev** 阶段（按已确认的方案写 · 不在 diagnose 写 fix）。详 [stages/diagnose-stage.md](../stages/diagnose-stage.md)。

## YAML frontmatter（机读字段）

> 简单 Bug 流程的状态机由本 frontmatter 承载（非新建 state.json 文件，避免简单 Bug 流程膨胀）。
> 字段命名复用 Feature state.json 核心字段（current_stage / phase / shipped 等），保持 schema 一致性。

```yaml
---
bug_id: "BUG-PTR-F025-001" # 必填，编号规则见 docs/conventions.md § 2
feature_id: "{缩写}-F025-{所属Feature名}" # 必填，Bug 归属的 Feature
classification: simple | complex # PMO 在 Bug 流程判断后填入
flow_type: bug # 固定值（与 feature 区分）

# 状态机字段
current_stage: diagnose | dev | review | test | pm_acceptance | ship | completed   # = state.py BUG_FLOW(首 stage diagnose · 根因细查+修复方案确认)
completed_stages: [] # 已完成阶段列表
phase: in_progress | summarized | shipping | shipping_finalize | shipped # 端到端 phase
started_at: "<ISO 8601 UTC>"
completed_at: null # PMO 总结后填

# Ship 字段
commit_hash: null # Dev Stage 自动 commit 后填（短 hash，7 位）
shipped: false | true | abandoned # Ship Stage finalize 后填
mr_url: null # Ship Stage 第一段生成 MR 后填
mr_merged_at: null # 用户合并 MR 后填
merge_commit_hash: null # finalize 阶段切 merge_target 后填
merge_target_pushed_at: null # finalize push merge_target（BUG-REPORT.md）成功后填
worktree_cleanup: not_required | done | failed
ship_concerns: [] # Ship 异常记录（如 push 失败、降级路径）

# 关联字段
related_pr: null # 关联的 PR/MR 链接
related_bugs: [] # 关联的其他 Bug
review_log_path: "{Feature}/review-log.jsonl" # 复用 Feature 的 review-log

# AI Plan 模式（红线 R7）
planned_execution: {} # 各 Stage 的 Execution Plan 历史
---
```

🔴 **复杂 Bug 例外**：复杂 Bug 进入 Feature 流程后，使用 Feature 的 `state.json`，BUG-REPORT.md frontmatter 仅保留 `bug_id / feature_id / classification: complex / flow_type: bug / current_stage: escalated_to_feature`，其他字段委托 Feature state.json 维护。

🔴 **PMO 校验**：进入 Bug 流程后，PMO 必须在 BUG-REPORT.md 创建时初始化 frontmatter；stage 流转由 state.py 状态机物化校验（`FLOW_BY_TYPE`），BUG-REPORT.md frontmatter `current_stage` 仅作标识，权威状态在 `state.json`。

---

## Markdown 模板正文

```markdown
# Bug 排查报告：{Bug 简述}

## 状态
🔍 排查中 | 📋 已分析 | 🔧 修复中 | ✅ 已修复

> 🔴 本"状态"段是人读视图；frontmatter `current_stage / phase / shipped` 是机读源头，二者必须一致（修改时同步两处）。

---

## 问题描述
**报告人**：[用户]
**报告时间**：[时间]
**问题描述**：
[用户报告的问题]

**期望行为**：
[应该是什么样的]

**实际行为**：
[实际发生了什么]

---

## 复现步骤
1. [步骤1]
2. [步骤2]
3. ...

**复现环境**：
- 浏览器/设备：
- 账号类型：
- 其他条件：

---

> 🔴 §问题描述 + §复现步骤 = 现象(diagnose 阶段锁定 · 可复现)。

---

## 根因分析（diagnose 阶段产出 · 🔴 深读代码挖真因 · 非表面猜测）

### 相关代码
| 文件 | 行号 | 问题描述 |
|------|------|----------|
| | | |

### 根因（真因 · 非症状）
[技术层面的真因:哪行 / 哪个调用 / 哪个字段 / 为什么 · 🔴 区分症状 vs 根因(改症状会复发)]

### 调用链路
\`\`\`
[入口] → [模块A] → [模块B] → [真因点]
\`\`\`

---

## 修复方案（diagnose 阶段产出 · 🔴 用户确认后才进 dev · 本阶段不写 fix 码）

### 方案描述
[改哪 / 怎么改 / 取舍 / 影响面;多候选方案列出 + 推荐]

### 修复层级
- [ ] 🟢 根因修复（修复根本原因）
- [ ] 🟡 症状修复（仅表面 · 必说明原因 + 后续计划）

### 修改范围
| 文件 | 修改类型 | 说明 |
|------|----------|------|
| | 新增/修改/删除 | |

### 影响评估
- [ ] 是否影响其他功能 · [ ] 是否需数据迁移 · [ ] 是否需更新文档

> 📋 复杂度 = frontmatter `classification`(simple / complex)· 进入流程时定。入口**恒为 diagnose**(无需"起点阶段"判断)· complex Bug 升 Feature 流程见上方「复杂 Bug 例外」。

---

## 回归测试（dev 阶段产出）

[原 bug 不复发的测试 + 周边无新错 · 对应 §修复方案 · dev 按已确认方案写 fix 时一并补]

---

## 修复记录（dev 阶段 · fix 落地后填）

**修复时间**： · **提交 hash**： · **QA 验证**：✅ 通过 / ❌ 未通过

---

## 变更记录
| 日期 | 变更 | 操作人 |
|------|------|--------|

## 🧩 补充洞察（AI 自由发挥 · 可留空）

> 模板槽位之外你认为**重要但没处落**的：非常规风险 / 更好方案的线索 / 跨 feature 影响 / 用户没问但该想清的。
> 🔴 模板是**地板不是天花板** —— 填完槽位 ≠ 想完了。没有就写「无」或删本节 · **不为凑内容而写**（硬凑 = 新仪式）。

\`\`\`
