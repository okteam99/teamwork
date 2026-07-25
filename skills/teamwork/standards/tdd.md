# 测试规范(手段自定 · 只管结果 · v8.286)

> 🔴 **v8.286 变更**:本文件不再规定 **TDD 方法论**(Iron Law / RED-GREEN-REFACTOR 五步 / 自检清单 / 反模式 / 「跳过 TDD」需用户同意的例外机制 —— 原 93 行已删)。
> **怎么测由 AI 自觉**:先写测试(TDD 红绿)· 先打通骨架再补边界 · test-after —— 按本 feature 自选。框架不规定节奏、不规定粒度、不需要申请跳过许可。
> **理由**:TDD 是**手段**,模型早已内建;框架该管的是**结果**(测试存在、真验行为、真跑绿),而结果有机器门与评审兜着(见下表)。文件名保留是为了不打断既有引用。

---

## 只有三条(结果规则 · 无例外)

1. 🔴 **每个 TC 用例必须有对应实现**。
   AC↔TC 的绑定由 `verify-ac.py` 机器校验;**TC↔实现**这一跳靠本条 —— TC 写了却没实现 = 需求链在最后一米断掉,而「测试全绿」会把它盖住。

2. 🔴 **测试必须真断言**(防假绿)· **禁止 mock 被测组件自身的内部方法**。
   *模型默认倾向:为了让测试过,把正要验的那段 mock 掉。* 恒绿的空壳测试比没有测试更危险 —— 它让门禁、评审、验收同时失效。抽查归 review 的「测试真实性与覆盖」覆盖方向 + 变异红测。

3. 🔴 **同一处失败修复 ≥3 次仍不过 → 停下升级**(不是 TDD 规则 · 是排障纪律)。
   不再试错性改实现:重读 TECH 检查方案设计 → 必要时升级 architect / external review(dev 输出 BLOCKED · PMO 调度)。
   *模型默认倾向:一直试下去。第 4/5/6 次「无意识重试」是症状性修复反模式。*

---

## 结果由谁保证(机器门 · 不靠自觉)

| 结果 | 保证方式 |
|---|---|
| AC 有测试覆盖 | `verify-ac.py`(每 AC ↔ TC `tests[].covers_ac` · blueprint-complete 自动跑 · 漏覆盖 FAIL) |
| 测试真跑过、真绿 | `dev-complete --test-exit-code 0` + `--test-stdout` 非空;brownfield 红 base 走 `test-baseline` 差分「0 新增」 |
| 测试没作弊 | test-stage ②「不为凑 exit-code=0 走捷径」(skip 必含 reason + tracking · 不标 xfail 蒙混)+ review 外审必覆盖「测试真实性与覆盖」 |
| 集成/契约测试没被单测糊弄 | TECH §测试策略(哪里必须真实 DB/BFF · 不靠两边 mock) |

---

## 相关

- 必读白名单:[HARD-RULES.md](./HARD-RULES.md) · 分层与阈值:[backend.md](./backend.md) / [frontend.md](./frontend.md)
- 测试体系 4 层与证据语义:[../stages/test-stage.md](../stages/test-stage.md) ②硬规则
