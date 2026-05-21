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

## §3 决策选项(三选一 · 用户拍板)

> 🔴 三选项都是**用户**决策 · AI 自决 = 越权 R3(详 stage spec § 4)。

### 3.1 若 approved_and_ship(推荐 · AC 全过且可发布)

**理由(PM 写一句)**:{如:核心 AC 全过 · 截图与 PRD UI 一致 · 无阻塞问题 · 可进 ship}
**后续动作**:进 ship stage(push 分支 + 建 MR · Phase 1 仍有"等用户在平台合并"暂停点)

### 3.2 若 approved_no_ship(完成但暂不发)

**理由**:{如:等协同 Feature X 合并后再统一发版 / 等运营时机}
**后续动作**:Feature 直接 completed · 不 ship

### 3.3 若 rejected_with_feedback(发现需返工)

**finding 列表**(必填):

| ID | 描述 | 涉及 AC | 严重度 | 建议改 | 类型(代码/需求/UI) |
|---|---|---|---|---|---|
| F1 | {如:登录失败提示文案与 PRD AC-2 不符 · PRD 要"密码错误" · 实现是"凭证无效"} | AC-2 | high | 改 src/auth/login.ts:42 提示文案 | 代码 |
| F2 | {如:AC-4 漏了空态截图 · QA 没测} | AC-4 | medium | 补 fe-e2e-005 空态场景 | QA 补测 |

**后续动作**(由 finding 类型决定 · 详 stage spec § 回退选项):
- 代码 bug → `state.py reset-prev` → dev-fix → review → test → pm_acceptance 重走
- AC / 需求改 → `state.py jump-to-stage --to goal --reason "..."` → 改 PRD + 重 review
- UI 设计改 → `state.py jump-to-stage --to ui_design --reason "..."` → 改 UI
- 放弃 Feature → `state.py ship-phase --action close-unmerged --abandon=true`

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

## 起草要点(PM cite · 写时删)

📚 **必读 cite**(P0-11):
- `roles/pm.md § 验收规范` —— 对照 TEST-REPORT 实际数据 · 不口述 OK
- `stages/pm-acceptance-stage.md § 4 三选项暂停点` —— 三选项 R5 emit 模板 · 用户拍板

❌ **反模式**(SOP 红线):
- "看起来 OK" 口述 → 必逐条 AC 对照实测数据
- AI 自决 decision(含"保守"的 approved_no_ship)→ 越权 R3
- `approved_no_ship` 躲避决策 → 仅用于真"完成但等时机" · 不用作躲避
- rejected 不写 finding → state.py 强校验 `--note` · 必明确改什么
- finding 模糊「整体不太好」→ 必具体到 AC + 文件 + 建议
