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

## 🐛 Bug 流程分支(无 PRD/TC · Bug 流程先读这段)

> Bug 流程规格依据 = `bugfix/BUG-*.md`(**非** PRD/TC)· 下面「怎么做」的 Feature 步骤按此调整,**不要照搬 PRD/AC/verify-ac**:

- **§1 加载上下文** → 读 `BUG-*.md`(§现象 / §根因 / §修复方案 / §回归测试)+ 实际代码 + dev commit ·**无 PRD.AC / TC.md**
- **§5 跑 verify-ac.py** → **skip**:门禁 `ac_test_binding` 对 Bug 自动 N/A(机器判 `_flow_key(state) in (Bug, Micro)` 直接 return skip · Feature·preset=micro 亦归一为内部键 Micro)· **别去跑 `verify-ac.py`** —— 它要 PRD.md · 必报「PRD 不存在」· 那是**假信号不是错**
- **测试焦点 = 回归**:复现 bug 的用例修复后转绿(对齐 `BUG-*.md §回归测试`)+ 既有 integration/api-e2e 套件保持绿 · `e2e/*` 复跑**触发 bug 的关键路径**
- **§质量基线 / Output Contract 里的 verify-ac 物化校验**:对 Bug 同样 N/A · 但 `TEST-REPORT.md` 仍必产(§回归结果 + exit-code 摘录)

---

## 怎么做

### 1. 加载上下文
读 PRD.AC · TC.md · 实际代码 · dev 阶段 commit
(Bug 流程:读 `BUG-*.md` 替代 PRD/TC · 详上「🐛 Bug 流程分支」)

### 2. QA 起草 integration(进程内集成)
基于 TC.md 用例 · 跨模块 / 跨服务契约(**单进程内** · 不起 live 服务)

### 3. QA 起草 api-e2e(live 跨进程)
- **用 Python 写**(语言统一 · 减项目间割裂)
- 落 `{Feature}/e2e/*.py` 或 `services/<svc>/tests/e2e/<feature-id>/`(按子项目结构 · RD/QA 决定)
- 起 live 服务 + 真实 HTTP 调用 · 脚本退出码 = api-e2e 真实结果(exit-code=0 = 通过)
- 🔴 **跑通即可**:**不强求 CI 可复用** · **不统一 DB/seed/env SOP**(各项目环境差异大 · 由项目自维护起服务方式)
- pm_acceptance / ship 审计会按 state.json evidence 验证据真实性 · test stage 只管 exit-code

### 4. 跑测试
integration + api-e2e 双 exit-code=0

### 5. 跑 verify-ac.py
AC↔Test 全覆盖物化校验 · 漏覆盖 FAIL
🐛 **Bug 流程 skip 本步**:无 PRD/TC · 门禁自动 N/A · 别跑 verify-ac.py(详「🐛 Bug 流程分支」)

### 6. 起草 TEST-REPORT.md
§integration 结果 / §api-e2e 结果 / §AC 覆盖度 / §回归

### 7. complete

🟢 **主路径(推荐)· 工具自跑 · AI 不能伪造 stdout**:
```
state.py test-complete --feature <path> --run-tests
# 工具自 subprocess 跑 .teamwork_localconfig.json test_commands 配的 cmd
# 完整 log 落 <feature_dir>/test-stdout.log(不污染主 PMO context · 仅 emit tail 100 行)
# 自动设 evidence.integration_test_exit_code = subprocess 真实 exit_code
# 防 AI 自报 "67 test 全跑了" 但实际只跑 3 framework test · 借 "context 不够" 不做
```

`.teamwork_localconfig.json` 配 test cmd(一次配 · 全 Feature 用):
```json
{
  "test_commands": {
    "default": "cargo test --test '*'",
    "by_feature_id_pattern": {
      "SVC-CORE-F037-*": "cargo test --test f037_quality_gate_framework"
    }
  },
  "test_timeout_sec": 1800,
  "test_log_tail_lines": 100
}
```
📎 **构建/测试临时产物落 scratch 根**(v8.247 · 🔴 v8.249 纠正):`CARGO_TARGET_DIR` / 测试日志 → `${TMPDIR:-/tmp}/teamwork/<feature_id>/...`(🔴 完整 feature_id · 禁 `bl031` 类简称)。🔴 **build target 按 feature 共享 = `<feature_id>/target`**(串行 stage 复用增量编译 —— dev 编好 test 热增量不重编 · 别按 stage 切成 `/test-stage`〔冷编整棵 deps · test 阶段主浪费〕· 锁隔离只需到 feature 粒度)。测试日志等无缓存价值的可自由 `<用途>` 命名。回收 = ship2 tmp-cleanup + bootstrap TTL 7 天 —— 详 [standards/common.md §六](../standards/common.md)。

🟡 **deprecated 旧路径(仅 debug / 工具不可用时 · 及红 base 差分场景〔§ base 即红 → 差分基线〕—— `--run-tests` 尚不支持差分口径时走本通道)**:
```
state.py test-complete --integration-test-exit-code 0 --e2e-test-exit-code 0 ...
# AI 自报 stdout / exit_code · 漏洞:可伪造 / 可跳测试
```

- exit_code 都 0 → 自动转 pm_acceptance(或 browser_e2e · 看 needs_browser_e2e)
- 任一 exit_code 非 0 → 留 test-stage · 走 §fix-retry 循环

### 🔴 base 即红 → 差分基线(治反复 stash-baseline · v8.178)
brownfield 共享套件常**预存在失败**(base 即红 · 历史重构遗留 / 他人欠债)· 全量跑 integration 永远非 0 → 老做法 targeted 子集 + 每个 feature 人肉 `stash → 跑 base → diff → REVIEW 论证非本 feature`(实证 audit:跨 3+ feature 反复确认同一批 5-6 个失败 · 高频重复成本)。改**差分基线**:
- 预存在失败登记进 `project-specs/test-baseline.md`(项目级单源 · 含原因/清账计划 · 详 [templates/test-baseline.md](../templates/test-baseline.md))。
- 跑**全量** integration → 得当前失败 id 集 → `state.py test-baseline --diff --current "id1,id2"` 对照基线:
  - **0 新增**(当前 ⊆ 基线)→ `test-complete --integration-test-exit-code <真实非0> --current-failures "id1,id2"` · 工具算差分干净 → **照常转 pm_acceptance**(不留 fix-retry · 红 base 非回归)。
  - **有新增**(当前 − 基线 ≠ ∅)→ = **回归**(修)**或** 新出现的预存在(在 base 上核实即红 → `test-baseline --add` 登记原因后重跑)。
- 🔴 纪律:**本 feature 新引入的失败绝不登记**(那是回归必修)· id 与 `--current-failures` 同格式 · e2e 仍严格 0(feature-scoped · 不走差分)。

---

## fix-retry 循环(stage 内 · 同 review 模式)

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

## 质量基线

📎 **物化拦截**:`verify-ac.py`(每 AC ≥1 integration 或 api-e2e · `TC.md frontmatter.tests[].covers_ac` 显式 cite)

**SOP**(违反 → 假通过 / 失去 audit):
- 测试失败必修 · skip 必含 reason + tracking issue · 不为 exit-code=0 标 xfail 走捷径
- TEST-REPORT 含具体测试 stdout 摘录 + exit-code 数值 · 不口述"通过"
- integration 不冒名 api-e2e:进程内 ServiceExt = integration · 真跨进程 binary = api-e2e(详 §测试体系)
- api-e2e 用 Python 写 · 跑通(exit-code=0)即可 · 环境编排由项目自维护(不统一 DB/seed/env SOP)

---

## Output Contract(产物形态参考)

> 📋 **起草模板**(避免找历史 Feature 抄):
> - TEST-REPORT.md → `{SKILL_ROOT}/templates/test-report.md`(含 stdout 摘录 + exit-code + AC 覆盖矩阵)
> - e2e/*.py → 无统一模板 · 按项目环境写 Python 脚本(exit-code=0 = 通过)
>
> 🤖 **校验脚本**:`python3 {SKILL_ROOT}/templates/verify-ac.py {Feature}` · test-complete 自动跑 ·
> 校验 AC↔Test 覆盖完整性(同 blueprint stage · 此处再跑一次防 dev 阶段 TC 漏改)

### `TEST-REPORT.md`
§integration / §api-e2e / §AC 覆盖 / §回归

### `e2e/*.py`
至少 1 文件 · Python · 可重跑 · exit-code=0 = 通过

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `TEST_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
