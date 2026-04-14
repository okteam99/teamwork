# Verify Chain Subagent：QA 代码审查 + 单元测试 + 集成测试 + API E2E（一体化执行）

> PMO 在 Dev Chain 通过后（或 UI 还原验收通过后）启动本 Subagent。内部完成 QA 代码审查 → 单元测试门禁 → 集成测试 → API E2E，一次性返回全部验证结果。
>
> `last-synced: 2026-04-13` · 对齐 SKILL.md / ROLES.md / RULES.md

---

## 一、设计意图

```
传统模式（PMO 逐步调度）：
  PMO → QA 代码审查 Subagent → PMO(relay) → 集成测试 Subagent → PMO(relay) → API E2E Subagent → PMO(relay)

Verify Chain 模式（一体化执行）：
  PMO → Verify Chain Subagent [QA 审查 → 单元测试 → 集成测试 → API E2E] → PMO

🎯 收益：PMO relay 从 3-4 次降为 1 次，验证流程连贯，context 节省显著。
🔴 关键约束：Verify Chain 只做验证，发现代码问题 → 返回 PMO → PMO dispatch RD 修复。
```

---

## 二、内部阶段

```
阶段 1: QA 代码审查
├── 规范：agents/qa-code-review.md（完整执行）
├── 产出：TC 验证报告 + 审查结论
├── ✅ 通过 → 进入阶段 2
└── ❌ 有问题 → 整体返回 QUALITY_ISSUE（PMO 安排 RD 修复后重新 dispatch）

阶段 2: 单元测试门禁
├── 执行项目单元测试命令
├── ✅ 全部通过 → 进入阶段 3
└── ❌ 有失败 → 整体返回 QUALITY_ISSUE

阶段 3: 项目集成测试
├── 轻量环境复核：执行根级 scripts/test-env-check.sh（PMO 已预检，此处仅复核连通性）
│   └── ❌ 不健康 → 尝试根级 scripts/test-env-setup.sh → 仍失败 → BLOCKED 返回
├── 执行 {subproject}/scripts/test-integration.sh
├── 规范：agents/integration-test.md（完整执行验证逻辑）
├── 产出：集成测试报告
├── ✅ 通过 → 进入阶段 4（如需 API E2E）
├── ✅ 通过 + 无 API E2E → 整体返回 DONE
└── ❌ 有问题 → 分类处理（见异常处理）

阶段 4: API E2E（TC.md 标注需要时执行）
├── 执行 {subproject}/scripts/test-api-e2e.sh
├── 规范：agents/api-e2e.md（完整执行验证逻辑）
├── 产出：API E2E 验收报告
├── ✅ 通过 → 整体返回 DONE
└── ❌ 有问题 → 分类处理（见异常处理）
```

---

## 三、输入文件

```
PMO 启动时必须注入（不是只传路径）：
├── agents/README.md                                ← 通用规范
├── agents/verify-chain.md                          ← 本文件
├── agents/qa-code-review.md                        ← QA 代码审查规范
├── agents/integration-test.md                      ← 集成测试规范
├── agents/api-e2e.md                               ← API E2E 规范
├── docs/features/F{编号}-{功能名}/PRD.md           ← 需求文档
├── docs/features/F{编号}-{功能名}/TC.md            ← 测试用例
├── docs/features/F{编号}-{功能名}/TECH.md          ← 技术方案
├── Dev Chain 执行报告                             ← RD 自查报告 + 架构师 Review 报告
├── .claude/skills/teamwork/standards/common.md     ← 通用开发规范
├── .claude/skills/teamwork/standards/backend.md    ← 后端规范（后端项目加载）
├── .claude/skills/teamwork/standards/frontend.md   ← 前端规范（前端项目加载）
│
可选文件（存在则读取）：
├── docs/architecture/ARCHITECTURE.md               ← 架构文档
└── docs/KNOWLEDGE.md                               ← 项目知识库

PMO 还需注入：
├── API base URL（API E2E 用）
├── TC.md 中 API E2E 判断结果（需要/不适用）
├── PMO 环境预检结果（根级 scripts/test-env-setup.sh 输出的环境信息 JSON）
├── 子项目路径（如 packages/api）
└── 子项目 scripts/ 目录下可用的测试脚本清单
```

---

## 四、执行流程

```
Step 1: 读取所有规范文件
        ├── agents/README.md + verify-chain.md（本文件）
        ├── qa-code-review.md + integration-test.md + api-e2e.md
        └── 项目文件（PRD/TC/TECH/standards + Dev Chain 报告）

Step 2: 【QA 代码审查】按 qa-code-review.md 完整执行
        ├── 读取代码变更 + TC.md
        ├── TC 逐条验证（实现覆盖 + 测试覆盖）
        ├── TDD 规范检查
        ├── 集成测试覆盖检查
        ├── 用户行为边界检查（有 UI 时）
        ├── 架构文档一致性检查
        └── 输出 QA 代码审查报告
        🔴 发现问题 → 跳到 Step 7（返回 QUALITY_ISSUE）

Step 3: 【单元测试门禁】执行 {subproject}/scripts/test-unit.sh
        ├── 记录完整输出
        └── ✅ 全部通过 → 继续
        🔴 有失败 → 跳到 Step 7（返回 QUALITY_ISSUE）

Step 4: 【环境复核】执行根级 scripts/test-env-check.sh
        ├── 验证 PMO 预检的全局环境仍然可用（DB/Redis/各服务连通性）
        ├── ✅ 健康 → 继续
        └── ❌ 不健康 → 执行根级 scripts/test-env-setup.sh 重试一次
            ├── ✅ 恢复 → 继续
            └── ❌ 仍失败 → 跳到 Step 7（返回 BLOCKED，附诊断输出）

Step 5: 【集成测试】执行 {subproject}/scripts/test-integration.sh + 按 integration-test.md 验证
        ├── 对照 TC 中标记为 integration 的用例校验
        ├── 测试数据清理
        └── 输出集成测试报告
        🔴 有代码问题 → 跳到 Step 7（返回 QUALITY_ISSUE）
        🔴 有环境问题 → 跳到 Step 7（返回 BLOCKED）

Step 6: 【API E2E】执行 {subproject}/scripts/test-api-e2e.sh + 按 api-e2e.md 验证
        （TC.md 标注需要时执行，否则跳过）
        ├── 逐场景验证 API 链路
        └── 输出 API E2E 验收报告
        🔴 有功能缺陷 → 跳到 Step 7（返回 QUALITY_ISSUE）

Step 7: 产出汇总
        ├── 整理所有已执行阶段的报告
        ├── 确定返回状态
        └── 输出 Verify Chain 执行报告
```

---

## 五、异常处理

```
🔴 Verify Chain 不修复代码，只验证和报告。

问题分类与返回策略：

| 发现阶段 | 问题类型 | 返回状态 | PMO 处理 |
|----------|----------|----------|----------|
| QA 代码审查 | 实现缺陷/测试缺陷 | QUALITY_ISSUE | dispatch RD Fix → 重新 dispatch Verify Chain |
| QA 代码审查 | TC 本身问题 | DONE_WITH_CONCERNS | PMO ⏸️ 用户确认 |
| 单元测试 | 测试失败 | QUALITY_ISSUE | dispatch RD Fix → 重新 dispatch Verify Chain |
| 集成测试 | 代码问题 | QUALITY_ISSUE | dispatch RD Fix → 重新 dispatch Verify Chain |
| 集成测试 | 环境问题 | BLOCKED | PMO ⏸️ 用户处理环境 |
| API E2E | 功能缺陷 | QUALITY_ISSUE | dispatch RD Fix → 重新 dispatch Verify Chain |
| API E2E | 环境/配置问题 | BLOCKED | PMO ⏸️ 用户处理 |

🔴 QUALITY_ISSUE 返回时必须包含：
├── 哪个阶段发现的问题
├── 具体问题清单（RD 可直接修复的粒度）
├── 已完成阶段的报告（不丢弃已有成果）
└── 建议：修复后 Verify Chain 是否需要全量重跑还是从断点继续

🔴 PMO 重新 dispatch Verify Chain 时的优化：
├── 如果只是 QA 审查问题 → RD 修复后重新 dispatch 完整 Verify Chain
├── 如果集成测试/API E2E 问题（QA 审查已通过）→ PMO 可选择：
│   ├── 保守：完整 Verify Chain 重跑（推荐，修复可能引入新问题）
│   └── 激进：从失败阶段开始重跑（仅当修复范围极小时）
└── PMO 在 dispatch 时通过 prompt 注明从哪个阶段开始
```

---

## 六、红线

```
🔴 只验证不修复：
├── Verify Chain 内部禁止修改任何业务代码
├── 发现问题 → 记录 + 返回，由 PMO 安排 RD 修复
└── 例外：集成测试的前置数据/环境配置可以调整

🔴 阶段完整性：
├── 每个阶段必须按对应规范完整执行，不能因为前一阶段通过就简化后续
├── QA 代码审查必须按 qa-code-review.md 全部 Step 执行
├── 集成测试必须按 integration-test.md 全部 Step 执行
└── API E2E 必须按 api-e2e.md 全部 Step 执行

🔴 Early Exit 原则：
├── 发现阻塞性问题时立即中止后续阶段，不继续浪费执行
├── 但已完成阶段的报告必须保留并返回
└── 中止点记录在报告中，方便后续断点续跑

🔴 证据链完整性：
├── 每个阶段的实际执行输出（测试命令+结果）必须包含在报告中
├── 不能用"测试通过"替代实际输出（闭环红线）
└── API E2E 必须包含完整 request/response
```

---

## 七、输出格式

```
📋 Verify Chain 执行报告（F{编号}-{功能名}）
============================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / QUALITY_ISSUE / BLOCKED / FAILED}
├── 执行阶段：{已完成的阶段列表}
├── 中止点：{如有，在哪个阶段中止}
└── API E2E：{已执行 / TC 标注不适用 / 未到达}

## 1. QA 代码审查报告
{按 qa-code-review.md 输出格式}

## 2. 单元测试门禁
├── 测试命令：{实际命令}
├── 测试结果：{通过数/失败数/跳过数}
└── 实际输出：
    ```
    {完整测试输出}
    ```

## 3. 集成测试报告
{按 integration-test.md 输出格式}

## 4. API E2E 验收报告（如执行）
{按 api-e2e.md 输出格式}

## 问题清单（如有）
| # | 发现阶段 | 问题类型 | 描述 | 建议处理 |
|---|----------|----------|------|----------|

## 断点续跑建议（QUALITY_ISSUE 时）
├── 修复范围评估：{大/小}
├── 建议策略：{全量重跑 / 从阶段 X 开始}
└── 理由：{...}
```
