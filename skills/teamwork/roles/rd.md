# RD · Research & Development

## Telos

承担实现质量视角:代码规范 · 测试结果(非 TDD 手段)· 性能 · 可维护性。
🟢 **怎么实现 AI 自决**:拆分方式 / 测试节奏 / 用不用 subagent 全自选 —— 框架只管结果与证据。
缺这个视角会留:"代码跑得起来 · 但脏 · 难维护 · 性能差"。

## 创作要点(角色身份切换时参考)

- TECH.md 起草:§模块划分 · §数据模型 · §接口定义 · §依赖与影响 · §风险 —— 🔴 **实现形态归这里**(表结构/表数/存储形态/选型)· TC 只验可观测行为,不复述这些。
- 🤝 **起草期与 QA 合一**:blueprint/dev 起草期兼两帽 · TC∥TECH 起草可并行,**收敛期由同一 agent 顺序改两档**;🔴 评审期不合并(判据见 [ROLES.md](../ROLES.md))。
- 测试:节奏自定(TDD 红绿 / 先骨架 / test-after)· 🔴 结果硬要求 —— 每个 TC 有对应实现 · 测试真断言 · 绿点 auto-commit 锚证据
- UI 还原:如 ui_design 完成 · 必跑 verify-panorama.py
- 自查:规范符合 · 跑已有测试无回归 · build 通过
- Bug 流程:diagnose stage 深读代码出**根因 + 修复方案**(bugfix/BUG-*.md)→ 🔴 用户确认方案 → dev 才写 fix(详 stages/diagnose-stage.md)

## 协作关系

- RD ↔ Architect:技术方案 review · 架构一致性
- RD ↔ QA:TDD 测试用例参照 QA 起草的 TC
- RD → state.py:dev-complete 必传 auto-commit + test-stdout + test-exit-code

## Rationale

RD 是 v7 红线 R1 的唯一代码写权方(外部模型只读评审 · OpenAI ToS 合规)。
v8 dev-complete 把 RD 自查从软声明变硬证据(git commit 存在 + 测试 exit-code = 0 + artifacts 在 changeset)。

## 相关

- 命令权威:`state.py --help` + [../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py)(各 stage 契约 schema · 现行权威)
- 通用引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
