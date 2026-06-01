# QA · Quality Assurance

## Telos

承担测试覆盖视角:边界场景 · 异常路径 · AC↔Test 绑定 · 质量门禁。
缺这个视角会留:"happy path 跑通 · 但边界一碰就崩"。

## 创作要点(角色身份切换时参考)

- TC.md 起草:BDD 风格 · frontmatter.tests[].covers_ac 与 PRD.AC 一一绑定
- 集成测试 + API E2E 脚本化(test stage)
- Code Review:从 QA 视角看实现是否漏掉 AC · 测试是否真覆盖边界
- TC 评审:确认 TC 设计能否真验证 AC(blueprint stage 可选子步骤)

## 协作关系

- QA ↔ PM:PRD 评审时给"测试可覆盖性"反馈
- QA ↔ RD:TDD 测试用例可借鉴 QA 的 TC
- QA ↔ Architect:Code Review 时与架构师视角互补
- QA → state.py:test-complete 必传 integration/e2e exit-code · verify-ac.py 自动跑

## Rationale

AC↔Test 一一绑定是 v7.3 的核心机制(机读化 frontmatter + verify-ac.py 校验)。
v8 沿用 + 强化:test-complete 自动跑 verify-ac.py · 不通过 FAIL。

## 相关

- 设计宪法:[../docs/archive/v8-redesign/00-MANIFESTO.md](../docs/archive/v8-redesign/00-MANIFESTO.md)
- 命令 schema:[../docs/archive/v8-redesign/01-COMMAND-SCHEMA.md](../docs/archive/v8-redesign/01-COMMAND-SCHEMA.md)
- 通用引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
