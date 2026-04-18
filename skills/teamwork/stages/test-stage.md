# Test Stage：集成测试 + API E2E（并行执行，🟡 可选 Stage）

> Review Stage 通过后，PMO **先询问用户是否立即执行 Test Stage**，获得确认后再启动本 Stage。
> 并行执行集成测试和 API E2E，一次性返回全部测试结果。
> 🔴 单元测试已在 Dev Stage 完成，本 Stage 不重跑单测。
> 🔴 QA 代码审查已在 Review Stage 完成，本 Stage 只跑测试。
>
> 🟡 **可选 Stage 说明**：Test Stage 是可选阶段，PMO 在执行前必须询问用户。
> 典型场景：多个 Feature 并行开发，用户可能希望全部开发完成后统一测试，而不是每个 Feature 完成后立即测试。
> 📎 详细的前置确认流程见 [roles/pmo.md](../roles/pmo.md#test-stage-前置确认pmo-专属)。

---

## 一、设计意图

```
Test Stage = 纯测试执行（不审代码、不写代码）
├── 集成测试：验证跨模块/跨服务的交互
├── API E2E：验证完整 API 链路（TC.md 标注需要时执行）
└── 并行执行，总时间 = 最长的那个测试
```

---

## 二、输入文件

> 🔴 Test Stage 两路并行 = 两个独立 Subagent dispatch，PMO 必须按 [Dispatch 文件协议](../agents/README.md#dispatch-文件协议) **分别生成两个 dispatch 文件**：
> - `{Feature}/dispatch_log/{NNN}-integration-test.md`
> - `{Feature}/dispatch_log/{NNN+1}-api-e2e.md`（TC.md 标注不适用时可省略）
>
> 两个文件的「Meta > Batch」字段填同一批次 ID（如 `test-round-1`）。
> 未生成 dispatch 文件不得 dispatch。

```
两个 dispatch 文件共用的 Input files（各自写入自己的 dispatch 文件）：
├── agents/README.md                                ← 通用规范
├── stages/test-stage.md                            ← 本文件
├── docs/features/F{编号}-{功能名}/PRD.md           ← 需求文档
├── docs/features/F{编号}-{功能名}/TC.md            ← 测试用例
├── docs/features/F{编号}-{功能名}/TECH.md          ← 技术方案
├── Review Stage 执行报告（路径注入）
├── {SKILL_ROOT}/standards/common.md                ← 通用开发规范
│
各 dispatch 专属追加：
├── integration-test dispatch → agents/integration-test.md
└── api-e2e dispatch → agents/api-e2e.md
│
写入 Additional inline context（非文件路径）：
├── API base URL（API E2E 用）
├── TC.md 中 API E2E 判断结果（需要/不适用）
├── PMO 环境预检结果
├── 子项目路径
└── 子项目 scripts/ 目录下可用的测试脚本清单
```

---

## 三、内部并行结构

```
┌─────────────────────────┬─────────────────────────┐
│ 集成测试                │ API E2E（如需）         │
│ agents/integration-     │ agents/api-e2e.md       │
│ test.md                 │                         │
│                         │                         │
│ ├── 环境复核            │ ├── 逐场景验证 API 链路 │
│ ├── 执行 test-          │ └── 输出 API E2E 报告   │
│ │   integration.sh      │                         │
│ └── 输出集成测试报告    │ （TC.md 标注不适用 →   │
│                         │   跳过，不执行）         │
└────────────┬────────────┴────────────┬────────────┘
             ↓                         ↓
                    PMO 汇合报告
```

---

## 四、执行流程

```
🔴 进度追踪：每个 Step 开始时报告进度（宿主支持 TodoWrite 时使用，否则输出 markdown 进度块），禁止黑盒执行。

Step 1: 读取所有规范文件

Step 2: 环境复核
        ├── 执行根级 scripts/test-env-check.sh
        ├── ✅ 健康 → 继续
        └── ❌ 不健康 → 尝试 test-env-setup.sh → 仍失败 → BLOCKED 返回

Step 3: 并行执行测试
        ├── 集成测试（按 agents/integration-test.md）
        └── API E2E（按 agents/api-e2e.md，TC.md 标注需要时执行）

Step 4: 汇合报告
        ├── 整理所有测试结果
        ├── 确定返回状态
        └── 输出 Test Stage 执行报告
```

---

## 五、返回状态

```
| 状态 | 条件 | PMO 处理 |
|------|------|----------|
| ✅ DONE | 全部测试通过 | 继续 → Browser E2E 判断 / PM 验收 |
| 🔁 QUALITY_ISSUE | 代码问题导致测试失败 | RD 修复 → 重跑 Test Stage（≤3 轮） |
| ❌ BLOCKED | 环境问题 | ⏸️ 用户处理环境 |
| ⚠️ DONE_WITH_CONCERNS | TC 本身问题 | ⏸️ 用户确认 |
```

---

## 六、红线

```
🔴 进度可见：每个 Step 必须报告进度（TodoWrite 或 markdown 进度块），禁止黑盒执行
🔴 只测试不修复：发现问题 → 记录 + 返回，由 PMO 安排 RD 修复
🔴 阶段完整性：集成测试按 integration-test.md 完整执行，API E2E 按 api-e2e.md 完整执行
🔴 证据链完整：测试命令 + 实际输出必须包含在报告中，禁止空口"通过"
🔴 API E2E 脚本化交付（v7.2）：
  ├── Subagent 必须生成 `{子项目}/tests/e2e/F{编号}/api-e2e.py` 脚本
  ├── 脚本必须通过 py_compile 语法自检后才能执行
  ├── 脚本 + README.md 必须 git commit 作为 Feature 交付物
  └── P0/P1 级必须注册到 e2e-registry（REGISTRY.md + REG case 文件）
🔴 API E2E 必须包含完整 request/response（在脚本 evidence 字段 + 证据文件中体现）
```

### Expected deliverables（写入 dispatch 文件）

```
├── 📁 集成测试证据文件：docs/integration_test/evidence-F{编号}.md
├── 📁 API E2E 脚本：{子项目}/tests/e2e/F{编号}-{功能名}/api-e2e.py（+ README.md）
├── 📁 API E2E 执行输出：JSON 结构化结果（写入 dispatch Result 段）
├── 📝 e2e-registry 更新：REGISTRY.md 新增行 + 对应 REG-{N}-{名称}.md case 文件
└── 📋 Test Stage 执行报告（含上述产物指针）
```

---

## 七、输出格式

```
📋 Test Stage 执行报告（F{编号}-{功能名}）
============================================

## 执行概况
├── 最终状态：{DONE / QUALITY_ISSUE / BLOCKED / DONE_WITH_CONCERNS}
├── 集成测试：{通过/失败/未执行}
├── API E2E：{通过/失败/TC 标注不适用/未执行}
└── 中止点：{如有}

## 集成测试报告
{按 agents/integration-test.md 输出格式}

## API E2E 报告（如执行）
{按 agents/api-e2e.md 输出格式}

## 问题清单（如有）
| # | 发现阶段 | 问题类型 | 描述 | 建议处理 |
|---|----------|----------|------|----------|
```
