# Test Stage

---

## 怎么做

### 1. 加载上下文
读 PRD.AC · TC.md · 实际代码 · dev 阶段 commit

### 2. QA 起草集成测试
基于 TC.md 测试用例 · 跨模块集成场景

### 3. QA 起草 API E2E
端到端 API 调用脚本 · 落 `{Feature}/e2e/*.py`(或语言对应)

### 4. 跑测试
集成测试 + API E2E 双 exit-code=0

### 5. 跑 verify-ac.py
AC↔Test 全覆盖物化校验 · 漏覆盖 FAIL

### 6. 起草 TEST-REPORT.md
§集成测试结果 / §API E2E 结果 / §AC 覆盖度 / §回归测试

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
| 2. QA 起草集成测试 | `roles/qa.md + standards/backend.md` | § 集成测试 | 跨模块场景 / 不是单测复刻 |
| 3. QA API E2E | `roles/qa.md + standards/frontend.md` | § E2E 测试 | 落 e2e/* · 语言无关 · 可重跑 |
| 4. 跑测试 | — | — | (无) |
| 5. 跑 verify-ac.py | — | — | (物化校验 · 无 spec cite) |
| 6. 起草 TEST-REPORT.md | — | — | (无) |
| 7. complete | — | — | (无) |


📎 **cite 纪律**(输出格式 / 强约束 / 为什么 cite)· 单源详 [../STAGES.md § 2 P0-11 cite 纪律](../STAGES.md)

## 质量基线

📎 **物化拦截**:`verify-ac.py`(每 AC ≥1 集成测试或 E2E · `TC.md frontmatter.tests[].covers_ac` 显式 cite)

**SOP**(违反 → 假通过 / 失去 audit):
- 测试失败必修 · skip 必含 reason + tracking issue · 不为 exit-code=0 标 xfail 走捷径
- E2E `e2e/*.py` 独立可执行 · 不依赖 dev 主对话上下文(CI 可复用)
- TEST-REPORT 含具体测试 stdout 摘录 + exit-code 数值 · 不口述"通过"
- 集成测试聚焦"模块间接口契约"(跨模块 / 跨服务)· 不是单元测试复刻

---

## Output Contract(产物形态参考)

### `TEST-REPORT.md`
§集成 / §E2E / §AC 覆盖 / §回归

### `e2e/*`
至少 1 文件 · 语言无关 · 可重跑

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `TEST_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
