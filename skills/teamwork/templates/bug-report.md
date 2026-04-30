# BUG-REPORT 模板

> 位置：`docs/features/F{编号}-{功能名}/bugfix/BUG-F{编号}-{序号}-{简述}.md`
> 编号规则：详见 [RULES.md](./RULES.md) - 编号规则章节
> 🔴 v7.3.10+P0-36 起：BUG-REPORT.md **必须包含 YAML frontmatter**（机读状态字段，承担 Bug 流程的 state.json 职能）。

## YAML frontmatter（机读字段，v7.3.10+P0-36 新增）

> 简单 Bug 流程的状态机由本 frontmatter 承载（非新建 state.json 文件，避免简单 Bug 流程膨胀）。
> 字段命名复用 templates/feature-state.json 核心字段（current_stage / phase / shipped 等），保持 schema 一致性。

```yaml
---
bug_id: "BUG-F025-001"                   # 必填，编号规则见 rules/naming.md
feature_id: "{缩写}-F025-{所属Feature名}"  # 必填，Bug 归属的 Feature
classification: simple | complex          # PMO 在 Bug 流程判断后填入
flow_type: bug                            # 固定值（v7.3.10+P0-36，与 feature 区分）

# 状态机字段
current_stage: triage | rd_diagnosis | pmo_classification | qa_test_supplement | rd_fix | architect_cr | qa_verify | pm_doc_sync | pmo_summary | ship | completed
completed_stages: []                      # 已完成阶段列表
phase: in_progress | summarized | shipping | shipping_finalize | shipped  # 端到端 phase
started_at: "<ISO 8601 UTC>"
completed_at: null                        # PMO 总结后填

# Ship 字段（v7.3.10+P0-36 新增，简单 Bug 走 Ship 缩简版）
commit_hash: null                         # Dev Stage 自动 commit 后填（短 hash，7 位）
shipped: false | true | abandoned         # Ship Stage finalize 后填
mr_url: null                              # Ship Stage 第一段生成 MR 后填
mr_merged_at: null                        # 用户合并 MR 后填
merge_commit_hash: null                   # finalize 阶段切 merge_target 后填
merge_target_pushed_at: null              # finalize push merge_target（BUG-REPORT.md）成功后填
worktree_cleanup: not_required | done | failed
ship_concerns: []                         # Ship 异常记录（如 push 失败、降级路径）

# 关联字段
related_pr: null                          # 关联的 PR/MR 链接
related_bugs: []                          # 关联的其他 Bug
review_log_path: "{Feature}/review-log.jsonl"   # 复用 Feature 的 review-log

# AI Plan 模式（v7.3 红线 #14）
planned_execution: {}                     # 各 Stage 的 Execution Plan 历史
---
```

🔴 **复杂 Bug 例外**：复杂 Bug 进入 Feature 流程后，使用 Feature 的 `state.json`，BUG-REPORT.md frontmatter 仅保留 `bug_id / feature_id / classification: complex / flow_type: bug / current_stage: escalated_to_feature`，其他字段委托 Feature state.json 维护。

🔴 **PMO 校验**：进入 Bug 流程后，PMO 必须在 BUG-REPORT.md 创建时初始化 frontmatter；流转校验时按 frontmatter `current_stage` 字段引用 flow-transitions.md。

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

## 根因分析（RD 填写）

### 相关代码
| 文件 | 行号 | 问题描述 |
|------|------|----------|
| | | |

### 问题原因
[技术层面的原因描述]

### 调用链路
\`\`\`
[入口] → [模块A] → [模块B] → [问题点]
\`\`\`

---

## 修复方案（RD 填写）

### 方案描述
[如何修复这个问题]

### 修复层级
- [ ] 🟢 根因修复（修复问题的根本原因）
- [ ] 🟡 症状修复（仅处理表面症状，未修复根因）

> 若选择症状修复，必须说明原因：[为何不做根因修复？是否有后续计划？]

### 修改范围
| 文件 | 修改类型 | 说明 |
|------|----------|------|
| | 新增/修改/删除 | |

### 影响评估
- [ ] 是否影响其他功能
- [ ] 是否需要数据迁移
- [ ] 是否需要更新文档

---

## 复杂度评估（RD 填写）

| 评估项 | 结果 | 说明 |
|--------|------|------|
| 修改文件数 | X 个 | |
| 是否涉及 UI | 是/否 | |
| 是否涉及架构 | 是/否 | |
| 是否需求偏差 | 是/否 | |
| **使用流程** | 简单 Bug 流程 / 复杂 Bug 流程 | |

---

## PMO 流程判断

**RD 建议**：简单 Bug / 复杂 Bug
**PMO 判断**：✅ 同意 / ⚠️ 调整为 [XXX]
**流程路径**：简化流程 / 完整流程
**起点阶段**：[从哪个阶段开始]

---

## 修复记录（修复后填写）

**修复时间**：
**修复人**：
**提交 hash**：
**QA 验证**：✅ 通过 / ❌ 未通过

---

## 变更记录
| 日期 | 变更 | 操作人 |
|------|------|--------|
\`\`\`
