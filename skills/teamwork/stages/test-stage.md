# Test Stage：集成测试 + API E2E（🟡 可选 Stage）

> Review Stage 通过后进入本 Stage。PMO 在启动前必须询问用户（可能需要延后到多 Feature 合并测试）。
> 🔴 单元测试已在 Dev Stage 完成；QA 代码审查已在 Review Stage 完成。本 Stage 只跑测试。
> 🔴 契约优先：环境准备 / 集成测试 / API E2E 的执行方式由 AI 自主规划。

---

## 本 Stage 职责

验证代码在真实环境下的行为：
- 集成测试：跨模块/跨服务交互
- API E2E：完整 API 链路（按 TC.md「API E2E 判断」决定是否执行）

📎 可选 Stage 说明见 [roles/pmo.md#test-stage-前置确认](../roles/pmo.md)。

---

## Input Contract

### 必读文件（按顺序）

```
├── {SKILL_ROOT}/agents/README.md
├── {SKILL_ROOT}/stages/test-stage.md（本文件）
├── {SKILL_ROOT}/agents/integration-test.md       ← 集成测试规范
├── {SKILL_ROOT}/agents/api-e2e.md                ← API E2E 规范（脚本化）
├── {SKILL_ROOT}/roles/qa.md                      ← QA 角色规范
├── {SKILL_ROOT}/standards/common.md
├── {Feature}/PRD.md
├── {Feature}/TC.md（含 API E2E 判断结果）
├── {Feature}/TECH.md
├── {Feature}/REVIEW.md                           ← Review Stage 产出
└── 项目 scripts/（test-env-check.sh / test-env-setup.sh 等）
```

### Additional Context

- API base URL（API E2E 用）
- TC.md 中「API E2E 判断」结果（需要 / 不适用）
- 子项目路径
- 子项目 scripts/ 目录下可用的测试脚本清单

### Key Context

- 历史决策锚点（如既定测试环境、共享数据库）
- 跨 Feature 约束（并行 Feature 不要污染共享数据）
- 已识别风险（KNOWLEDGE 中相关陷阱）
- 降级授权
- 优先级 / 容忍度

### 前置依赖

- `state.json.stage_contracts.review.output_satisfied == true`
- 用户已确认启动 Test Stage（非延后/跳过）
- state.json.current_stage == "test"

---

## Process Contract

### 必做动作

1. **环境准备**（🔴 独立步骤，含 P0 懒装依赖兜底）
   - 🟢 **P0 懒装依赖兜底**：如 Dev Stage 未安装依赖（例如跳过 Dev 直接进 Test 的复测场景），Test Stage 入口先执行 dev-stage.md 的依赖检测流程补装，之后再进入环境健康检查
   - 执行 `scripts/test-env-check.sh` 确认环境健康
   - 不健康 → 尝试 `test-env-setup.sh`
   - 仍失败 → BLOCKED 返回
   - 环境信息（端口 / DSN / 测试账号）结构化落盘到 `{Feature}/test-env.json`

2. **集成测试**
   - 按 `agents/integration-test.md`
   - 跑已有集成测试命令（不生成新脚本）
   - 产出证据文件：`docs/integration_test/evidence-F{编号}.md`

3. **API E2E**（TC.md 标注需要时）
   - 按 `agents/api-e2e.md` 的脚本化方式
   - 生成 Python 脚本：`{子项目}/tests/e2e/F{编号}-{功能名}/api-e2e.py`
   - 脚本 py_compile 自检 → 执行 → 解读 JSON 输出
   - 产出报告 + 更新 e2e-registry

### 过程硬规则

- 🔴 **角色规范必读且 cite**：必读 `roles/qa.md` + `agents/integration-test.md` + `agents/api-e2e.md`
- 🔴 **只测试不修复**：发现问题 → 记录 + 返回，由 PMO 安排 RD 修复
- 🔴 **阶段完整性**：集成测试按 `integration-test.md` 完整执行；API E2E 按 `api-e2e.md` 完整执行
- 🔴 **证据链完整**：测试命令 + 实际输出必须在报告中，禁止空口"通过"
- 🔴 **API E2E 脚本化交付**（v7.2）：
  - 必须生成 `tests/e2e/F{编号}/api-e2e.py` 脚本
  - 脚本必须通过 py_compile 语法自检
  - 脚本 + README.md 必须 git commit
  - P0/P1 级必须注册到 e2e-registry（REGISTRY.md + REG case）
- 🔴 **API E2E 断言**：每场景至少覆盖 4 类断言（status / body / DB / 副作用）中的 2 类；所有环境值走 env var；DB 校验走只读 DSN
- 🔴 **Stage 完成前 git 干净** → 统一遵循 [rules/gate-checks.md § Stage 完成前 git 干净](../rules/gate-checks.md#-stage-完成前-git-干净v739-硬规则p0-集中化)（本 Stage commit message：`F{编号}: Test Stage - {简述}`；auto_commit 为**数组**字段，多轮 QUALITY_ISSUE 修复 append）

---

## Output Contract

### 必须产出的文件

| 文件路径 | 格式 | 必需内容 |
|---------|------|---------|
| `{Feature}/test-env.json` | JSON | `started_at`, `health_check: pass`, `base_url`, `db_dsn`（脱敏）, `test_accounts[]` |
| `docs/integration_test/evidence-F{编号}.md` | Markdown | 执行命令 + 完整输出 + 通过率 |
| `{子项目}/tests/e2e/F{编号}-{功能名}/api-e2e.py` | Python 脚本 | 4 类断言覆盖、env var 输入、JSON 结构化 evidence |
| `{子项目}/tests/e2e/F{编号}-{功能名}/README.md` | Markdown | 脚本执行指南 + env 要求 |
| `{子项目}/docs/e2e/REGISTRY.md`（更新） | Markdown 表 | 新增 REG-{N} 行（脚本路径、最后跑通） |
| `{子项目}/docs/e2e/cases/REG-{N}-{名称}.md` | Markdown | 自包含 case 文件 |
| `{Feature}/test-report.md`（或 dispatch Result 段）| Markdown | 汇总执行结果 |

### 机器可校验条件

- [ ] `{Feature}/test-env.json` 存在且 JSON 可解析
- [ ] 集成测试实际执行：`grep "PASSED" docs/integration_test/evidence-F{编号}.md` 命中
- [ ] API E2E 脚本存在且 `python -m py_compile` 通过
- [ ] API E2E 执行：JSON evidence 字段含 request + response
- [ ] 所有涉及的测试命令 exit 0
- [ ] e2e-registry 已更新（如适用）

### Done 判据

- 环境准备成功
- 集成测试全部通过
- API E2E（如需）脚本化交付 + 全部通过
- `state.json.stage_contracts.test.output_satisfied = true`

### 返回状态

| 状态 | 条件 | 后续 |
|------|------|------|
| ✅ DONE | 全部测试通过 | → Browser E2E 判断 / PM 验收 |
| 🔁 QUALITY_ISSUE | 代码问题导致测试失败 | RD 修复 → 重跑 Test Stage（≤3 轮）|
| ❌ BLOCKED | 环境问题 | PMO ⏸️ 用户处理 |
| ⚠️ DONE_WITH_CONCERNS | TC 本身问题 | PMO ⏸️ 用户确认 |

---

## AI Plan 模式指引

📎 Execution Plan 格式 → [SKILL.md](../SKILL.md#-ai-plan-模式规范v73-新增)。

🔴 **本 Stage 三轴全部由 AI 自主决策**（v7.3.9 明确化）：

```
├── 是否输出完整 Execution Plan：AI 按本 Feature 测试规模 + 复杂度自主判断
│   ├── 简单场景（单模块、测试命令 <3 条、无 API E2E）→ 可省略 Plan，直接执行并在报告中追述
│   └── 复杂场景（多模块、含 API E2E、环境需调试）→ 建议输出 Plan，便于用户把关
│
├── approach（main-conversation / subagent / hybrid）：AI 自主选择
│   ├── 参考依据：Feature 规模、测试命令耗时、是否 API E2E、主对话 context 压力
│   ├── 典型选择（非强制）：
│   │   ├── 小 Feature / 测试命令快 → main-conversation
│   │   ├── CI 环境稳定 / 无人值守 → 全 subagent
│   │   └── 环境需调试 + 脚本化 API E2E 混合 → hybrid
│   └── 🔴 禁止强制绑定某种 approach，AI 自己判断成本收益
│
└── 模型选择：AI 按任务复杂度自主决定
    ├── 参考维度：场景数量、事务复杂度、断言层级、历史失败率
    ├── 典型选择（非强制，仅供 AI 参考）：
    │   ├── 校验型脚本化任务（翻译 TC → 脚本 → 解读 JSON）→ Sonnet 通常性价比最优
    │   ├── 多步事务逻辑 / 场景 ≥10 / 历史 Sonnet 失败且归因能力 → 可升 Opus
    │   └── 极简场景（<3 scenarios，单纯 status+body）→ 可降 Haiku
    ├── Claude 环境通过 Task 工具 `model` 字段指定；Codex 通过 agent toml `model` 字段
    └── 🔴 禁止规范预设硬默认，AI 在 Plan / 执行报告中说明模型选择理由即可
```

**Expected duration baseline（v7.3.3）**：环境准备 2-5 min；集成测试 5-15 min；API E2E 脚本化 10-25 min（脚本生成 + 执行）。Hybrid 总计 15-30 min；环境异常 BLOCKED 时另计。AI 按实际 approach 在 Plan 中给出本次 Expected。

### 环境信息交接（任何 approach 都适用）

`{Feature}/test-env.json` 必须落盘。集成测试 / API E2E 走 Subagent 时，dispatch 文件的 Input files 必须含此 JSON 路径。Subagent 启动第一步应 ping health endpoint 确认环境活着。

---

## 执行报告模板

```
📋 Test Stage 执行报告（F{编号}-{功能名}）
============================================

## 执行概况
├── 最终状态：{DONE / QUALITY_ISSUE / BLOCKED / DONE_WITH_CONCERNS}
├── 执行方式：环境{主对话/Subagent} + 集成{主对话/Subagent} + API E2E {主对话/Subagent}
├── 环境：{健康 / 失败 / 降级}
├── 集成测试：{通过/失败/未执行}
├── API E2E：{通过/失败/TC 标注不适用/未执行}
└── 中止点：{如有}

## 集成测试报告
{按 agents/integration-test.md 输出格式}

## API E2E 报告（如执行）
{按 agents/api-e2e.md 输出格式}

## Output Contract 校验
├── test-env.json：✅ 可解析
├── 集成测试证据：✅ 含实际输出
├── API E2E 脚本 py_compile：✅
├── e2e-registry 更新：✅ / ⏭️ 无需
└── 所有测试 exit 0：✅

## 问题清单（如有）
| # | 发现阶段 | 问题类型 | 描述 | 建议处理 |
|---|----------|----------|------|----------|
```
