# QA · Quality Assurance

## Telos

承担测试覆盖视角:边界场景 · 异常路径 · AC↔Test 绑定 · 质量门禁。
缺这个视角会留:"happy path 跑通 · 但边界一碰就崩"。

## 创作要点(角色身份切换时参考)

- 🔴 **不再是独立评审席位**(去角色):本视角已并入统一冷审清单的 🔍 **核对段** —— goal「可验证」· blueprint「可测试」· review「测试真实性与覆盖」· 每一路都查,不再分席位(单源 stages/*-stage.md ②)
- TC.md 起草:BDD 风格 · frontmatter.tests[].covers_ac 与 PRD.AC 一一绑定 · 🔴 **职责边界单源 [templates/tc.md § TC 的职责边界](../templates/tc.md)** —— 判据「**换实现就要改的内容不属于 TC**」(表数/表清单/存储形态归 TECH · TC 只验可观测行为 + 边界异常)。
- 🤝 **起草期与 RD 合一**:blueprint/dev 起草期 QA 与 RD 是同一个 agent 兼两帽 —— TC 与 TECH 的**收敛也归它**(不跨 agent 往返);🔴 **评审期不合并**(独立采样点 · 判据见 [ROLES.md](../ROLES.md))。
- 集成测试 + API E2E 脚本化(test stage)
- 本视角在 review 清单 🔍 核对段:实现是否漏掉 AC · 测试是否真覆盖边界(每路都查 · 非独立席位)
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

- 命令权威:`state.py --help` + [../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py)(各 stage 契约 schema · 现行权威)
- 通用引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
