# Test Stage

> 🧭 **四段结构**(目标 / 硬规则 / 建议手段菜单 / Output Contract):目标 + 契约给足,**手段 AI 自选**。

---

## ① 目标(telos)

**把「实现说它好了」变成机器可验的通过证据**:跑出 integration(进程内跨模块契约)与 api-e2e(真跨进程 live)的**真实** exit-code,并留下 AC↔Test 全覆盖台账(Bug 流则是回归台账)。拦的风险:AI 自报「测试全跑了」而实际只跑子集、xfail/skip 凑绿的假通过、把进程内测试冒名成全链路、以及 brownfield 红 base 下每个 feature 人肉 stash 重算基线。

---

## ② 硬规则(白名单 · 每条一行 why)

1. **测试证据由工具自采**:主路径 `test-complete --run-tests`(工具 subprocess 跑 localconfig 配的 cmd · 真实 exit_code 直接写进 evidence)· AI 自报 exit-code/stdout 是 deprecated 通道,只在 debug / 工具不可用 / 差分口径下用(why:实证 case —— AI 自报「67 个 test 全跑了」实际只跑 3 个 framework test,或借「context 不够」不跑;自报通道可伪造、可跳测)。
1.7 🎛️ **主对话 = Orchestrator(默认姿态 · 全局单源 [SKILL § subagent/teammate](../SKILL.md) · 本条 stage 实例)**:**不建议在主对话(主循环)直接编写与执行测试** —— 测试执行本就是验证类白名单(一律降验证档 subagent · 主窗口跑 = 例外须 R5 用户授权);测试**编写**(TC 对应实现 / 集成用例)同白名单默认派。主对话优先做:环境预检调度 · 子代理派发 · **差分基线裁决** · 门禁命令(test-complete 证据)· 失败分诊与小型精准修复(why:同 dev 1.7 —— 主对话 context 留给编排;测试日志是最大的 context 污染源之一)。
2. **测试体系 4 层不冒名**(层名 = 证据语义):**unit** 单类/单函数 → dev stage 内 TDD 红绿循环(RD)· **integration** = **单进程内**跨模块/跨服务契约(如 axum router + `tower::ServiceExt` 打 router · 抹掉跨进程边界 · 适合契约/数据流校验)→ 本 stage(QA)· **api-e2e** = **真跨进程**(独立 gateway binary + 真 HTTP + 真 DB/Redis 等依赖 · 验全链路)→ 本 stage(QA)· **browser-e2e** UI 交互流 + 截图 → browser_e2e stage(QA + Designer)。🔴 进程内「模拟跨服务」= integration,**不是** api-e2e(why:冒名 = 声称验了全链路其实没验,TEST-REPORT 与后续 audit 全部失真)。
2.9 🔁 **CI 门禁对照(本地测试与 MR CI 同构性)**:test 收口前必须跑 `state.py ci-commands --root <worktree 根>`,把 CI 真正会跑的门禁命令逐条标注 **本地已跑 / 跑不了(为什么)/ 本次不适用**,写进 `TEST-REPORT.md §2.5`。
   - 🔴 **不要求本地跑全集** —— 有些 job 需要 infra 凭据或耗时过长,强行复现是纯税;要求的是**看过并给出处置**;
   - 🔴 **「跑不了」必须显式列出**:那是「已知会在 CI 才发现」的清单,写出来风险才可见(零也显式 · 静默省略与静默漏配在产物上无法区分);
   - 🔴 **别自己猜 CI 配置路径**(why:实证 case aon-main DEV-F260830125314 —— TEST-REPORT 只记 `cargo check`〔只验编译〕而 CI 跑 `cargo clippy -- -D warnings`,一条 lint 漏到 CI 才炸;**那个 AI 试过 grep**,猜的是 `.gitlab-ci.yml`,真配置在 include 进来的 `infra/ci/api-gateway.yml`,grep 空结果被当成「没有 CI」—— 不是偷懒,是不知道去哪找,所以该由机器端清单)。
   - 📎 与 MR 窗口期 CI 归因(ship-stage)的分工:**这一条是防**(进 CI 前先对照),那一条是**治**(真红了归因 + 自己引入的直接修)。

3. **api-e2e 用 Python 写**,落 `{Feature}/e2e/*.py` 或 `services/<svc>/tests/e2e/<feature-id>/`(按子项目结构 · RD/QA 决定)· 起 live 服务 + 真实 HTTP 调用 · **脚本退出码 = api-e2e 真实结果**(exit-code=0 = 通过)(why:语言统一减项目间割裂 · 退出码是唯一机器可验信号)。🔴 **跑通即可**:**不强求 CI 可复用** · **不统一 DB/seed/env SOP**(各项目环境差异大 · 起服务方式由项目自维护)—— test stage 只管 exit-code,证据真实性由 pm_acceptance / ship 按 `state.json` evidence 审计。
4. **不为凑 exit-code=0 走捷径**:测试失败必修 · skip 必含 reason + tracking issue · 不标 xfail 蒙混(why:假绿 = 门禁形同虚设,下游 pm_acceptance 拿到的是空证据)。
5. **TEST-REPORT 摘录具体测试 stdout + exit-code 数值**,不口述「通过」(why:口述不可 audit —— 复盘时无从判断当时到底跑没跑、跑了什么)。
6. 🔴 **base 即红 → 走差分基线,不人肉 stash**:brownfield 共享套件常有**预存在失败**(历史重构遗留 / 他人欠债)→ 登记进 `project-specs/test-baseline.md`(项目级单源 · 含原因 + 清账计划)· 跑**全量** integration(不许缩成 targeted 子集)拿当前失败 id 集,与基线差分:**0 新增**(当前 ⊆ 基线)= 红 base 非回归 · 照常转 pm_acceptance 不留 fix-retry;**有新增** = 回归(修)**或** 新出现的预存在(在 base 上核实即红 → 登记原因后重跑)。🔴 **本 feature 新引入的失败绝不登记进基线**(那是回归必修)· e2e 仍严格 0(feature-scoped · 不走差分)(why:实证 audit —— 同一批 5-6 个预存在失败被跨 3+ feature 反复「stash → 跑 base → diff → 写 REVIEW 论证非本 feature」,纯重复成本)。
7. **每条 AC 必有测试绑定**(`verify-ac.py` 物化拦截 · 漏覆盖 FAIL · 语法见 ④)(why:blueprint 已校验过一次,此处再校验一次防 dev 阶段改了实现却漏改 TC)。🐛 **Bug 流 carve-out**:无 PRD/TC → 门禁 `ac_test_binding` 对 Bug 自动 N/A(机器判 `_flow_key(state) in (Bug, Micro)` 直接 return skip · Feature·preset=micro 亦归一为内部键 Micro)· **别去跑 `verify-ac.py`** —— 它要 PRD.md,必报「PRD 不存在」,那是**假信号不是错**。
8. **Bug 流规格依据 = `bugfix/BUG-*.md`(非 PRD/TC)· 焦点 = 回归**:复现 bug 的用例修复后转绿(对齐 `BUG-*.md §回归测试`)+ 既有 integration/api-e2e 套件保持绿 + `e2e/*` 复跑**触发 bug 的关键路径**;AC 覆盖类校验 N/A,但 `TEST-REPORT.md` 仍必产(why:Bug 没有 AC 台账,唯一能证明「修对了且没修坏」的就是回归证据)。
9. **构建/测试临时产物落 scratch 根**:`CARGO_TARGET_DIR` / 测试日志 → worktree 模式 `<worktree>/.teamwork-scratch/...`(ignored · 随 worktree 消亡)· off 模式旧根 `${TMPDIR:-/tmp}/teamwork/<feature_id>/...`(🔴 完整 feature_id · 禁简称)· 🔴 **build target 按 feature 共享 = `.teamwork-scratch/target`**,不许按 stage 切(why:串行 stage 复用增量编译 —— dev 编好、test 热增量不重编;按 stage 切 = 冷编整棵 deps,是 test 阶段的主浪费。锁隔离只需到 feature 粒度)。回收 = ship1 push 即清 + worktree 生命周期 + TTL 兜底(详 [conventions.md §12.48](../docs/conventions.md))。

---

## ③ 建议手段菜单(AI 按本 feature 自选 · 不强制)

| 手段 | 何时值得 |
|---|---|
| **先跑一遍既有套件摸 base** | 项目还没有 `test-baseline.md`、或分不清红是不是自己造的 —— 先判「预存在 vs 本次引入」,再决定走全量 0 还是差分口径(硬规则 6)|
| **按 TC.md 用例逐条起 integration** | 有结构化 TC 的 Feature 默认首选(TC 已把用例拆好 · 直接映射 · 顺带满足 AC 绑定)|
| **api-e2e 只打关键路径** | 覆盖率靠 integration 拿 —— live 环境启停贵,e2e 是验「真的跨进程通了」,不是刷覆盖 |
| **subagent 并行写 integration / api-e2e** | 两边零文件重叠 + 可独立环境隔离(如各自 `TEST_PG_DB_NAME`)时;耦合或改动小 → 自己串行做(协调开销反拖慢)|
| **失败先分类再修** | 进 fix-retry 前先判清 回归 / 预存在 / 环境 —— 环境问题去改产品代码是白修 |

---

## ④ Output Contract(产物契约 · 机读)

### 产物
- **`TEST-REPORT.md`** —— §integration 结果 / §api-e2e 结果 / §AC 覆盖度 / §回归(🐛 Bug 流:§回归结果 + exit-code 摘录)· 📋 起草模板 [templates/test-report.md](../templates/test-report.md)(含 stdout 摘录 + exit-code + AC 覆盖矩阵 · 别抄历史 Feature)。
- **`e2e/*.py`** —— 至少 1 文件 · Python · 可重跑 · exit-code=0 = 通过 · 无统一模板(按项目环境写)。

### 物化拦截(test-complete 校验)
| 门 | 判据 |
|---|---|
| `integration_test_present` / `e2e_test_present` | exit-code 已传(值可非 0 —— 失败留 test stage 走 fix-retry)|
| `ac_test_binding` | `python3 {SKILL_ROOT}/templates/verify-ac.py {Feature}`(test-complete 自动跑)· 每 AC ≥1 integration 或 api-e2e · `TC.md frontmatter.tests[].covers_ac` 显式 cite · 🐛 Bug 流 / preset=micro 自动 skip(硬规则 7)|
| artifacts | `TEST-REPORT.md` + `e2e/*` 至少 1 文件 |

### test-complete
🟢 **主路径(推荐 · 工具自跑 · AI 不能伪造 stdout)**:
```
state.py test-complete --feature <path> --run-tests
# 工具自 subprocess 跑 .teamwork_localconfig.json test_commands 配的 cmd
# 完整 log 落 <feature_dir>/test-stdout.log(不污染主 PMO context · 仅 emit tail 100 行)
# 自动设 evidence.integration_test_exit_code = subprocess 真实 exit_code
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
🟡 **deprecated 自报通道**(仅 debug / 工具不可用时 · 及红 base 差分场景〔`--run-tests` 尚不支持差分口径〕· AI 自报 = 可伪造/可跳测):
```
state.py test-complete --feature <path> --auto-commit <hash> \
  --artifacts TEST-REPORT.md,e2e/ \
  --integration-test-exit-code 0 --e2e-test-exit-code 0
```

### 差分基线(硬规则 6 的机器语法)
```
state.py test-baseline --diff --current "id1,id2"     # 对照 project-specs/test-baseline.md
# new=[] → test-complete --integration-test-exit-code <真实非0> --current-failures "id1,id2"
state.py test-baseline --add --test-id <id> --reason "<为何红 · 谁的债 · 何时清>"   # 新出现的预存在:核实即红后登记
```
基线文件模板 [templates/test-baseline.md](../templates/test-baseline.md) · `--current-failures` 与登记 id 同格式。

### 转移
- integration + e2e exit_code 都 0(或 integration 差分 0 新增)→ 自动转 `pm_acceptance`(或 `browser_e2e` · 看 `needs_browser_e2e`)。
- 任一非 0 → 留 test stage,走 fix-retry(`transitioned_to=None` · emit `fix_retry_hint`)。

### fix-retry 循环(stage 内 · 命令契约 · 同 review 模式)
```
test-complete --integration-test-exit-code 1        (失败 · 写 rounds[-1] · current_stage 仍是 test)
→ RD 修代码 + commit → test-fix --auto-commit <hash> [--addresses-findings F1,F2]
                                                    (写 rounds[-1].fix_commit · 重置 contract gates + evidence.exit_code)
→ test-retry                                        (rounds 加 round N+1 · 清 evidence.{integration,e2e}_test_exit_code)
→ 重跑 integration + API E2E
→ test-complete --integration-test-exit-code 0 --e2e-test-exit-code 0  → 都 0 自动转 pm_acceptance
```
`rounds[]` 结构由 state.py 维护(`round` / `test_commit` / `integration_test_exit_code` / `e2e_test_exit_code` / `fix_commit` / `fix_at` / `addresses_findings` / `completed_at` · audit 单源)。stage 内 fix 是 RD 写代码(同 review)· **R1 不违反**;失败本质是 dev 设计错(非 fix 级能解决)→ `state.py reset-prev` 退 dev 重做。

### 上下文入口(读什么)
PRD(AC)· TC.md(用例)· 实际代码 · dev 阶段 commit。🐛 **Bug 流**:`bugfix/BUG-*.md`(§现象/§根因/§修复方案/§回归测试)+ 实际代码 + dev commit 为权威输入 —— **无 PRD.AC / TC.md**。

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)(fix/retry 通用函数 `execute_stage_fix` / `execute_stage_retry` · `_STAGE_FIX_RETRY_CONFIG`)· spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `TEST_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md) · 通用纪律:[../STAGES.md](../STAGES.md)
- 模板:[../templates/test-report.md](../templates/test-report.md) / [../templates/test-baseline.md](../templates/test-baseline.md) · scratch 根:[../docs/conventions.md §12.48](../docs/conventions.md)
