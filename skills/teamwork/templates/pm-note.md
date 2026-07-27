---
feature_id: "{PREFIX}-{F|B|M}{NNN}-{kebab-name}"
author: PM
status: draft  # draft | confirmed
decision: ""   # approved_and_ship | approved_no_ship | rejected_with_feedback
decided_at: "{ISO 8601 UTC}"
prd_ref: PRD.md (vX.Y)
test_report_ref: TEST-REPORT.md
browser_test_report_ref: BROWSER-TEST-REPORT.md  # 若有
ac_total: 0
ac_passed: 0
revision_history:
  - version: v0.1
    date: "{YYYY-MM-DD}"
    author: PM
    summary: 首版起草
---

# {功能名} - PM 验收说明(PM-NOTE)

> 位置：`{Feature 目录}/PM-NOTE.md`
> 🟢 **本文是 teamwork pm_acceptance-stage 可选产物** · 起草模板 = `{SKILL_ROOT}/templates/pm-note.md`
> 🔴 **状态字段权威在 state.json** · 本文是人读说明 / rejected 时的 finding 列表 / 决策理由留痕。
> 🔴 **rejected_with_feedback 时本文 finding 列表必填** · state.py 强校验 `--note`(详 [stages/pm-acceptance-stage.md](../stages/pm-acceptance-stage.md))。

---

## §1 验收概要

| 项 | 内容 |
|---|---|
| 决策 | {approved_and_ship · approved_no_ship · rejected_with_feedback} |
| AC 通过数 | {N / N} |
| 评审依据 | PRD.AC + TEST-REPORT + (可选)BROWSER-TEST-REPORT + 截图 |
| 决策时间 | {ISO 8601 UTC} |

---

## §2 AC 逐条对照(对照 TEST-REPORT 实际数据 · 不口述 OK)

> 🔴 SOP:逐条 AC 对照 TEST-REPORT.md 的实际 stdout / 截图 · 不靠"看起来 OK"。

| AC ID | 描述 | 实测数据出处 | PM 判断 | 备注 |
|---|---|---|---|---|
| AC-1 | {邮箱登录} | TEST-REPORT § integration · T-001 stdout | ✅ pass | - |
| AC-2 | {密码错误提示} | BROWSER-TEST-REPORT · FE-E2E-002 截图 | ✅ pass | - |
| AC-3 | {首页跳转} | TEST-REPORT § api-e2e · API-E2E-001 stdout | ✅ pass | - |

---

## §3 决策(用户已拍板 · 记录结果 · 不是选项脚本)

> 🔴 三个选项与各自的回退命令**单源在 [pm-acceptance-stage.md](../stages/pm-acceptance-stage.md)** ——
> 本文件是**决策之后的记录**,不复述暂停点脚本(v8.293:原三分支槽位 + 四条回退命令与 stage 逐字重复)。

**决策**:{approved_and_ship / approved_no_ship / rejected_with_feedback}
**理由**(一句):{如:核心 AC 全过 · 截图与 PRD UI 一致 · 无阻塞问题}

### rejected_with_feedback 时必填 finding 列表

| ID | 描述 | 涉及 AC | 严重度 | 建议改 | 类型(代码/需求/UI) |
|---|---|---|---|---|---|
| F1 | {如:登录失败提示文案与 PRD AC-2 不符 · PRD 要"密码错误" · 实现是"凭证无效"} | AC-2 | high | 改 src/auth/login.ts:42 提示文案 | 代码 |
| F2 | {如:AC-4 漏了空态截图 · QA 没测} | AC-4 | medium | 补 fe-e2e-005 空态场景 | QA 补测 |

---

## §4 主对话试用(可选)

| 路径 | PM 实测 | 截图 / log |
|---|---|---|
| {如:登录 → 首页} | ✅ 流畅 | (粘截图引用 / log) |

---

## §5 决策依据

| 来源 | 内容 |
|---|---|
| PRD.AC | acceptance_criteria[] N 条 |
| TEST-REPORT | integration N · api-e2e N · 全 exit-code=0 |
| BROWSER-TEST-REPORT(可选)| FE-E2E-NNN · N 截图 |
| 其他(如灰度数据 / 协同状态) | - |

---

