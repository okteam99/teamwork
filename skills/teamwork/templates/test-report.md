---
feature_id: "{PREFIX}-{F|B|M}{NNN}-{kebab-name}"
author: QA
status: draft  # draft | confirmed
prd_ref: PRD.md (vX.Y)
tc_ref: TC.md (vX.Y)
test_run_at: "{ISO 8601 UTC}"
# 物化校验 evidence(state.py test-complete 必传)·
# 这里只是冗余记录便于人读 · 真权威在 state.json.stage_contracts.test
evidence:
  integration_test_exit_code: 0   # 0 = 通过 · 非 0 = 失败 → 走 fix-retry
  e2e_test_exit_code: 0           # 同上
  ac_coverage_verify: pass        # verify-ac.py 结果
revision_history:
  - version: v0.1
    date: "{YYYY-MM-DD}"
    author: QA
    summary: 首版起草
---

# {功能名} - Test Report

> 🟢 **本文是 teamwork test-stage 产物** · 起草模板 = `{SKILL_ROOT}/templates/test-report.md`
> 🔴 **必含 stdout 摘录 + exit-code 数值** · 不口述「测试通过」(SOP 红线 · 见 [stages/test-stage.md](../stages/test-stage.md))

---

## §1 测试范围

| 层 | 范围 | 文件 / 入口 | 责任人 |
|---|---|---|---|
| integration(进程内集成) | {模块 A ↔ 模块 B 契约} | `tests/integration/<feature>/*.test.ts` | QA |
| api-e2e(live 跨进程) | {真 binary + 真 HTTP + 真 DB} | `{Feature}/e2e/*.py` | QA |
| (可选)browser-e2e | {UI 交互流 + 截图} | 见 [BROWSER-TEST-REPORT.md](./BROWSER-TEST-REPORT.md) | QA + Designer |

🔴 概念边界(不混):integration = 单进程内 ServiceExt 打 router · api-e2e = 真跨进程(独立 binary + 真依赖)。
进程内"模拟跨服务"叫 integration · 不叫 api-e2e。

---

## §2 integration 结果

### 2.1 执行命令

```bash
{npm test -- tests/integration/<feature>/ | cargo test --test integration_<feature> | ...}
```

### 2.2 stdout 摘录(关键段 · 不全贴)

```text
{粘 ≥3 行 · 含通过/失败计数 · 含失败 stack 摘要(若有)}
PASS  tests/integration/<feature>/foo.test.ts
  ✓ AC-1: should ...
  ✓ AC-2: should ...

Tests:       N passed, N total
Time:        X.Y s
```

### 2.3 exit-code

`exit-code = 0`(通过)/ `exit-code = N`(失败 · 见 §6 fix-retry)

---

## §3 api-e2e 结果

### 3.1 前置环境

| 项 | 内容 | 获取方式 |
|---|---|---|
| 服务地址 | {http://localhost:3000} | {docker compose up / cargo run} |
| DB | {postgres@localhost:5432 · seed: npm run seed:test} | {项目脚本 / 用户提供} |
| 测试账号 | {test@example.com / pwd=...} | {seed 自动 / 用户提供} |

### 3.2 执行命令

```bash
cd {Feature}/e2e/
python3 test_<scenario>.py
# 或一次跑全部:python3 -m pytest .
```

### 3.3 stdout 摘录

```text
{粘真实 stdout · 含 HTTP 状态码 + DB 验证结果}
✓ API-E2E-001: POST /api/v1/<endpoint> → 200 · body.code=SUCCESS
✓ DB 验证: orders 表新增记录 · status=paid

Ran 3 tests in 4.2s
OK
```

### 3.4 exit-code

`exit-code = 0`(通过)

---

## §4 AC 覆盖度(verify-ac.py 结果)

```bash
python3 {SKILL_ROOT}/templates/verify-ac.py {Feature 目录}
```

### 4.1 verify-ac.py 输出

```text
{粘 verify-ac.py stdout · 含 PRD AC 数 / TC tests 数 / 漏覆盖 AC 列表}
AC 总数: N · TC 覆盖: N · 漏覆盖: 0
PASS
```

### 4.2 AC↔Test 矩阵

| AC ID | 描述 | 覆盖 TC | 层级 | 状态 |
|---|---|---|---|---|
| AC-1 | {描述} | T-001, T-003 | unit + integration | ✅ |
| AC-2 | {描述} | T-002 | api-e2e | ✅ |

覆盖率:N / N(100%)

---

## §5 回归测试

| 测试集 | 范围 | 结果 |
|---|---|---|
| 全量 unit | {模块} | ✅ N passed |
| 全量 integration | {模块} | ✅ N passed |
| critical-path 回归 | {核心流} | ✅ N passed |

---

## §6 fix-retry 历史(若 round > 1)

> 📋 stage_contracts.test.rounds[] 是机器权威 · 此节是人读视图。

| Round | test_commit | integration_exit | e2e_exit | fix_commit | addresses_findings | 备注 |
|---|---|---|---|---|---|---|
| 1 | c1a2b3c | 1 | 0 | c4d5e6f | F1 | {模块 A 边界条件漏处理} |
| 2 | c7g8h9i | 0 | 0 | - | - | 全绿 · 进 pm_acceptance |

---

## §7 已知问题(不阻塞 · audit 留痕)

| ID | 描述 | 严重度 | 决定 | 跟踪 |
|---|---|---|---|---|
| - | (无) | - | - | - |

---

## §8 评审记录

| 日期 | 评审人 | 结论 | 备注 |
|---|---|---|---|
| {YYYY-MM-DD} | PM | ✅ pass | - |

---

## 起草要点(QA cite · 写时删)

📚 **参考**(v8.199 cite 仪式已废 · 按需读):
- `roles/qa.md § 集成测试` —— integration = 进程内 · 跨模块/服务契约 · 不抹边界
- `roles/qa.md § E2E 测试` —— api-e2e = Python · live 跨进程 · 跑通即可
- `stages/test-stage.md § SOP` —— stdout 必摘录 · exit-code 必数值 · 不口述

❌ **反模式**(写 TEST-REPORT 时常见):
- "测试通过" 口述无证据 → 必贴 stdout 摘录 + exit-code 数值
- skip 不写 reason · 不挂 tracking issue → 必含原因(SOP)
- xfail 走 exit-code=0 捷径 → 测试失败必修 · 不掩盖(SOP)
- integration 冒名叫 e2e → 进程数判定(详 stage spec § 测试体系)
