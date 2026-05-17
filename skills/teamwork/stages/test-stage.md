# Test Stage

---

## teamwork 测试体系(4 层 · 概念统一)

| 层 | 范围 | 归 stage | 责任人 |
|---|---|---|---|
| **unit** 单元测试 | 单类 / 单函数 · 红绿循环 | dev stage 内(TDD) | RD |
| **integration** 进程内集成 | 跨模块 / 跨服务契约(**单进程内** · 如 axum router + `tower::ServiceExt`) | test stage | QA |
| **api-e2e** API live 跨进程 | 真 binary + 真路由 + 真依赖(起 live 服务) | test stage | QA |
| **browser-e2e** 浏览器 E2E | UI 交互流 + 截图 | browser_e2e stage(可选) | QA + Designer |

🔴 **概念边界(不可混)**:
- **integration vs api-e2e** = 进程数 / live 程度差异
  - integration:单进程内 ServiceExt 打 router · 抹掉跨进程边界 · 适合契约 / 数据流校验
  - api-e2e:**真跨进程**(独立 gateway binary + 真 HTTP + 真 DB/Redis 等依赖)· 验全链路
- 进程内"模拟跨服务" ≠ api-e2e(是 integration · 别叫错)

---

## 怎么做

### 1. 加载上下文
读 PRD.AC · TC.md · 实际代码 · dev 阶段 commit

### 2. QA 起草 integration(进程内集成)
基于 TC.md 用例 · 跨模块 / 跨服务契约(**单进程内** · 不起 live 服务)

### 3. QA 起草 api-e2e(live 跨进程)
- **用 Python 写**(语言统一 · 减项目间割裂)
- 落 `{Feature}/e2e/*.py` 或 `services/<svc>/tests/e2e/<feature-id>/`(按子项目结构 · RD/QA 决定)
- 起 live 服务 + 真实 HTTP 调用 · 脚本退出码 = api-e2e 真实结果(exit-code=0 = 通过)
- 🔴 **跑通即可**:**不强求 CI 可复用** · **不统一 DB/seed/env SOP**(各项目环境差异大 · 由项目自维护起服务方式)
- pm_acceptance / review 阶段会按 state.json evidence 验证据真实性 · test stage 只管 exit-code

### 4. 跑测试
integration + api-e2e 双 exit-code=0

### 5. 跑 verify-ac.py
AC↔Test 全覆盖物化校验 · 漏覆盖 FAIL

### 6. 起草 TEST-REPORT.md
§integration 结果 / §api-e2e 结果 / §AC 覆盖度 / §回归

### 7. complete
`state.py test-complete --integration-test-exit-code 0 --e2e-test-exit-code 0 ...`
- exit_code 都 0 → 自动转 pm_acceptance(或 browser_e2e · 看 needs_browser_e2e)
- 任一 exit_code 非 0 → 留 test-stage · 走 §fix-retry 循环

---

## fix-retry 循环(stage 内 · v8.10 · 同 review v8.9 模式)

test 失败时 stage 内 fix-retry · 不切 stage:

```
Round N: test-complete --integration-test-exit-code 1 (失败 · 写 rounds[-1])
  ↓ (current_stage 仍是 test · transitioned_to=None · emit fix_retry_hint)
RD 修代码 + commit
  ↓
test-fix --auto-commit <hash> [--addresses-findings F1,F2]
  ↓ (写 rounds[-1].fix_commit · 重置 contract gates + evidence.exit_code)
test-retry
  ↓ (rounds 加 round N+1 · 清 evidence.{integration,e2e}_test_exit_code)
重新跑 integration test + API E2E
  ↓
test-complete --integration-test-exit-code 0 --e2e-test-exit-code 0
  ↓ 都 0 → 自动转 pm_acceptance
```

**rounds[] 结构**:
```json
"stage_contracts.test.rounds": [
  {"round": 1, "test_commit": "C1",
   "integration_test_exit_code": 1, "e2e_test_exit_code": 0,
   "fix_commit": "C2", "fix_at": "...", "addresses_findings": ["F1"]},
  {"round": 2, "test_commit": "C3",
   "integration_test_exit_code": 0, "e2e_test_exit_code": 0,
   "completed_at": "..."}
]
```

**与 dev-stage 的关系**:
- test-stage 内 fix 是 RD 写代码(同 review)· 仍归 RD 角色 · R1 不违反
- 如果失败本质是 dev 设计错(不是 finding 级 fix 能解决)· 用 `state.py reset-prev` 退到 dev 重做

**与 review-stage fix-retry 的差异**:
- review:fix 解决 architect/qa finding
- test:fix 解决 test failure(integration / e2e exit_code 非 0)
- 共用 _v8_engine.execute_stage_fix / execute_stage_retry 通用函数(`_STAGE_FIX_RETRY_CONFIG`)

---

## 必读 cite 清单(P0-11 · 各 substep 动手前主对话输出)

| Substep | 必读 spec | 段 | cite 关键点 |
|---------|----------|----|------------|
| 1. 加载上下文 | — | — | (读 PRD.AC + TC.md + 代码) |
| 2. QA 起草 integration | `roles/qa.md` | § 集成测试 | 进程内 · 跨模块/服务契约 · 不抹边界叫 E2E |
| 3. QA 起草 api-e2e | `roles/qa.md` | § E2E 测试 | Python · live 跨进程 · 跑通即可 |
| 4. 跑测试 | — | — | (无) |
| 5. 跑 verify-ac.py | — | — | (物化校验 · 无 spec cite) |
| 6. 起草 TEST-REPORT.md | — | — | (无) |
| 7. complete | — | — | (无) |


📎 **cite 纪律**(输出格式 / 强约束 / 为什么 cite)· 单源详 [../STAGES.md § 2 P0-11 cite 纪律](../STAGES.md)

## 质量基线

📎 **物化拦截**:`verify-ac.py`(每 AC ≥1 integration 或 api-e2e · `TC.md frontmatter.tests[].covers_ac` 显式 cite)

**SOP**(违反 → 假通过 / 失去 audit):
- 测试失败必修 · skip 必含 reason + tracking issue · 不为 exit-code=0 标 xfail 走捷径
- TEST-REPORT 含具体测试 stdout 摘录 + exit-code 数值 · 不口述"通过"
- integration 不冒名 api-e2e:进程内 ServiceExt = integration · 真跨进程 binary = api-e2e(详 §测试体系)
- api-e2e 用 Python 写 · 跑通(exit-code=0)即可 · 环境编排由项目自维护(不统一 DB/seed/env SOP)

---

## Output Contract(产物形态参考)

### `TEST-REPORT.md`
§integration / §api-e2e / §AC 覆盖 / §回归

### `e2e/*.py`
至少 1 文件 · Python · 可重跑 · exit-code=0 = 通过

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `TEST_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
