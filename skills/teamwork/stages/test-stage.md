# Test Stage：集成测试 + API E2E（🟡 可选 Stage）

> Review Stage 通过后进入本 Stage。PMO 在启动前必须询问用户（可能需要延后到多 Feature 合并测试）。
> 🔴 单元测试已在 Dev Stage 完成；QA 代码审查已在 Review Stage 完成。本 Stage 只跑测试。
> 🔴 契约优先：环境准备 / 集成测试 / API E2E 的执行方式由 AI 自主规划。
> 📎 **本文件即 QA 在 Test Stage 的完整任务规范**（v7.3.10+P0-19-B 合并 agents/integration-test.md + agents/api-e2e.md）。

---

## 本 Stage 职责

验证代码在真实环境下的行为：
- 集成测试：跨模块/跨服务交互
- API E2E：完整 API 链路（按 TC.md「API E2E 判断」决定是否执行）

📎 可选 Stage 说明见 [roles/pmo.md#test-stage-前置确认](../roles/pmo.md)。

---

## 可配置点清单（v7.3.10+P0-55 新增）

| 可配置点 | 默认值 | 控制字段 | 决策时机 |
|---------|-------|---------|---------|
| 测试范围 | 集成测试 + API E2E（按 TC.md 判断） | TC.md `test_scope[]` | Blueprint Stage 起草 TC 时决策 |
| Browser E2E 启用 | TC.md 含 Browser E2E AC 时启用（auto 模式默认跳过，P0-11-B）| `state.stage_contracts.browser_e2e.status` | Test Stage 入口 / auto 模式 |
| staging 实测 | 跨子项目 Feature / 数据流验证需求时启用 | execution_hints | Stage 入口决策 |
| 失败重跑循环 | 仅 fix 后重跑相关测试 | spec 内嵌 | Test 内运行时 |
| 跳过 Test Stage | Browser E2E auto 跳过（P0-11-B）| `state.stage_contracts.browser_e2e = SKIPPED_BY_AUTO` | auto 模式 |

🔴 不变内核：测试全绿才能进 PM 验收 + 失败 case 必须修 + 测试报告独立产物（test-report.md）。

---

## Input Contract

### 必读文件（按顺序）

```
├── {SKILL_ROOT}/stages/test-stage.md（本文件，含集成测试 / API E2E 任务规范）
├── {SKILL_ROOT}/roles/qa.md                      ← QA 角色规范
├── {SKILL_ROOT}/standards/common.md
├── {Feature}/PRD.md
├── {Feature}/TC.md（含 API E2E 判断结果）
├── {Feature}/TECH.md
├── {Feature}/REVIEW.md                           ← Review Stage 产出
└── 项目 scripts/（test-env-check.sh / test-env-setup.sh 等）

Subagent 模式额外：
└── {SKILL_ROOT}/agents/README.md（Subagent 执行协议）
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

## 入口 Read 顺序（v7.3.10+P0-23 固定）

🔴 按以下顺序 Read，字节一致利于 prompt cache 命中。详见 [standards/prompt-cache.md](../standards/prompt-cache.md)。

```
Step 1: roles/qa.md                                    ← 角色层（L0 稳定）
Step 2: 无产出新模板                                    （集成测 / API E2E 脚本在项目 scripts/ 下）
Step 3: {Feature}/PRD.md, TC.md, TECH.md, REVIEW.md   ← Feature 既有产物（L2）
Step 4: {Feature}/state.json                           ← 🔴 最后，动态入口（L3）
```

🔴 R3 约束：state.json 入口 Read 1 次 → 中段 0 读写 → 出口 Read 1 次 + Write 1 次。Subagent 整合豁免每次 dispatch 后 ≤1 次 Write；全 Stage ≤ 8 次。

---

## Process Contract

### 主对话输出 Tier 应用（v7.3.10+P0-54 新增）

> 🔴 **遵循 [standards/output-tiers.md](../standards/output-tiers.md) 通用 Tier 1/2/3 规范 + 4 类反模式禁令**。

**Test Stage 特定 Tier 应用**：

- **Tier 1（永远输出）**：5 行 Execution Plan / 集成测试 / API E2E 关键 verdict（PASS / FAILED）/ Browser E2E（如启用）verdict / 失败 case 摘要
- **Tier 2（命中折叠）**：每套测试的 case 数 + 通过率（一行摘要）/ 失败 case fix 重跑标记 / staging 实测启用时的环境差异说明
- **Tier 3（不输出，走 state.json）**：每个 case 详细输出 / test-report.md 段位完成度 / 测试套件耗时数据

---

### 必做动作

1. **环境准备**（🔴 独立步骤，含 P0 懒装依赖兜底）
   - 🟢 **P0 懒装依赖兜底**：如 Dev Stage 未安装依赖（例如跳过 Dev 直接进 Test 的复测场景），Test Stage 入口先执行 dev-stage.md 的依赖检测流程补装，之后再进入环境健康检查
   - 执行 `scripts/test-env-check.sh` 确认环境健康
   - 不健康 → 尝试 `test-env-setup.sh`
   - 仍失败 → BLOCKED 返回
   - 环境信息（端口 / DSN / 测试账号）结构化落盘到 `{Feature}/test-env.json`

2. **集成测试**
   - 按本文件 §集成测试任务规范
   - 跑已有集成测试命令（不生成新脚本）
   - 产出证据文件：`docs/integration_test/evidence-F{编号}.md`

3. **API E2E**（TC.md 标注需要时）
   - 按本文件 §API E2E 任务规范 的脚本化方式
   - 生成 Python 脚本：`{子项目}/tests/e2e/F{编号}-{功能名}/api-e2e.py`
   - 脚本 py_compile 自检 → 执行 → 解读 JSON 输出
   - 产出报告 + 更新 e2e-registry

### 过程硬规则

- 🔴 **角色规范必读且 cite**：必读 `roles/qa.md` + 本文件 §集成测试任务规范 + §API E2E 任务规范
- 🔴 **只测试不修复**：发现问题 → 记录 + 返回，由 PMO 安排 RD 修复
- 🔴 **阶段完整性**：集成测试按本文件 §集成测试任务规范 完整执行；API E2E 按本文件 §API E2E 任务规范 完整执行
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

## 集成测试任务规范

> 本节整合 v7.3.10+P0-19-B 前的 `agents/integration-test.md` 完整规范。主对话 / Subagent 模式均适用。

### 1. 角色定位

你是 QA 集成测试执行者。你的核心职责是**调用仓库既有的测试命令**（`cargo test --test xxx` / `pytest tests/integration/` / `npm run test:integration` 等），执行并捕获结构化输出，生成测试报告。

🔴 **执行原则**：集成测试本质上已经是脚本驱动（测试命令就是脚本）。你**不生成新脚本**，只负责：
1. 读取 TECH.md / package.json / Cargo.toml 找到项目既有的 integration test 命令
2. 执行命令 + 捕获输出到证据文件
3. 校验 TC.md 中标记为 integration 的用例是否被覆盖
4. 生成报告

🔴 **与 API E2E 的区别**：
- 集成测试 = 项目内部测试命令（开发视角，测试代码在项目仓库内）
- API E2E = 独立脚本 `tests/e2e/F{编号}/api-e2e.py`（外部调用方视角，专为本 Feature 生成，规范见本文件 §API E2E 任务规范）
- 🚫 不要在集成测试里做 curl 级黑盒验证，那是 API E2E 的职责

**⚠️ Subagent 模式下不能与用户交互。** 遇到任何问题（环境异常、测试失败、数据问题）只记录不中断，最终统一输出。主对话模式下可适度卡点询问 PMO。

### 2. 执行流程

#### Step 1: 读取规范和项目文件

```
按顺序读取：
├── 1. 本文件 §集成测试任务规范 / §API E2E 任务规范
├── 2. TECH.md → 获取项目集成测试命令、依赖说明、数据库要求
├── 3. TC.md → 获取测试用例（标记为 integration 的部分）
├── 4. PRD.md → 获取验收标准
└── 5. docs/RESOURCES.md → 获取环境连接信息

Subagent 模式额外：先读 agents/README.md（Subagent 执行协议）
```

#### Step 2: 验证环境连通性

```
快速验证（不做修复，只记录）：
├── 数据库连接是否正常
├── Redis 连接是否正常（如有）
├── API 服务是否可达
└── 异常 → 记录到问题清单，继续可执行的测试
```

#### Step 2.5: 迁移验证（涉及 schema 变更时执行）

```
前置判断：检查 TECH.md 是否包含「数据库变更」章节 → 无此章节则跳过 Step 2.5
有此章节时执行：
├── 验证迁移文件可执行：运行 migration up，确认无报错
├── 验证 ORM 映射正确：对 TECH.md「Schema 影响分析」表中的每个 Model/Struct：
│   ├── 执行一条简单 SELECT 查询（如 SELECT * FROM {表} LIMIT 1）
│   └── 确认 ORM 反序列化无报错（字段匹配 → 成功 / 缺列 → 报错 → ❌）
├── 验证迁移可回滚（如环境允许）：运行 migration down，确认无报错
│   └── 回滚后重新 up，确认可重新执行
├── 跨子项目影响验证：
│   └── 对影响分析表中「其他子项目」的 Model，同样执行 SELECT 验证 ORM 映射
└── 每项记录：验证项 | 目标表 | 受影响 Model | 结果（✅/❌）
```

#### Step 3: 执行项目集成测试命令

```
按项目实际技术栈执行 integration tests：
├── Rust 项目 → 优先运行 `cargo test --test ...` 或项目约定的 integration test 命令
├── 其他项目 → 运行仓库内约定的 integration test 命令
├── 记录命令、通过/失败、关键输出
└── 🔴 不在这里做 curl 级 API 黑盒验证；那属于 API E2E 阶段
```

#### Step 4: 验证 integration 用例覆盖情况

```
遍历 TC.md 中标记为 integration 的用例：
├── 核对每个用例是否有对应测试入口
├── 必要时按用例筛选测试命令或测试名
└── 记录：用例ID | 测试入口 | 实际结果 | 结果（✅/❌/⏭️）
```

#### Step 5: 测试数据清理

```
├── 清理本次测试产生的临时数据
├── 保留基础测试数据供后续复用
├── 记录数据变更到 docs/TEST-DATA.md（如有新增）
└── 异常 → 记录，不中断
```

#### Step 6: 输出测试报告

### 3. 执行约束

```
├── 🔴 Subagent 模式不能与用户交互，所有问题记录到报告中
├── 🔴 不能修改业务代码（只做测试，不做修复）
├── 🔴 不能跳过失败的测试（全部执行，统一报告）
├── 🔴 禁止凭推断或假设填写测试结果 → 没有实际执行证据的用例必须标记为 ⏭️ 未执行，不能标 ✅ 或 ❌
├── 🔴 集成测试必须基于仓库实际测试命令执行，禁止凭代码推断结果
├── ✅ 可以创建/修改测试脚本
├── ✅ 可以更新 docs/TEST-DATA.md
├── ✅ 环境连接失败时 → 记录问题，继续执行不依赖该环境的测试
└── ✅ 单个测试超时 → 标记为 ⏱️ 超时，继续下一个
```

### 4. 执行证据要求

**每一条测试结果必须有真实执行证据，无证据的结果无效。**

#### 4.1 证据文件

所有执行证据统一写入文件，不在对话窗口中展示原始输出：

```
docs/integration_test/
└── evidence-F{编号}.md    ← 本次集成测试的完整执行证据
```

测试报告中的汇总表只引用证据文件，例如：

```markdown
> 完整执行证据见 [docs/integration_test/evidence-F{编号}.md](docs/integration_test/evidence-F{编号}.md)
```

#### 4.2 证据文件格式

```markdown
# 集成测试执行证据（F{编号}-{功能名}）

执行时间: YYYY-MM-DD HH:MM
环境: {API Base / DB 连接信息}

---

## 集成测试命令证据

### 1. 运行 integration test

**执行命令：**
\```bash
cargo test --test order_flow -- --nocapture
\```

**关键输出：**
\```
running 3 tests
test create_order_success ... ok
test create_order_invalid_coupon ... ok
\```

**结果：** ✅ 命令执行成功，用例通过

---

## integration 用例映射证据

### 1. 验证: TC-INT-001 对应测试入口

**执行 SQL：**
\```sql
tests/order_flow.rs::create_order_success
\```

**结果：** ✅ 已由 integration test 命令覆盖

### 2. 验证: ...
...（每条验证一个小节）
```

#### 4.3 无法执行时的处理

```
如果因环境问题无法执行某项测试：
├── 结果标记为 ⏭️ 未执行（绝不能标 ✅）
├── 在证据文件中记录无法执行的原因（如：连接超时、服务未启动）
└── 归入问题清单的「环境问题」分类
```

### 5. 集成测试报告模板

```markdown
📋 集成测试报告（F{编号}-{功能名}）
=====================================

## 环境信息
- 环境: Docker Local / Dev Remote
- 部署方式: docker-compose.test.yml / 远程连接
- API Base: {实际地址}
- 数据库: {实际连接}
- 缓存: {实际连接 / N/A}

## 测试概览
- 总用例数: X
- 通过: Y ✅
- 失败: Z ❌
- 跳过: W ⏭️（环境不可用等原因）
- 超时: V ⏱️
- 通过率: YY%

## 集成测试命令结果
| 命令 | 覆盖范围 | 结果 | 说明 |
|------|----------|------|------|
| cargo test --test order_flow -- --nocapture | 下单主链路 | ✅ | 通过 |

> 完整执行证据见 [docs/integration_test/evidence-F{编号}.md] — 证据文件中无对应记录的行视为 ⏭️ 未执行。

## integration 用例映射结果
| 用例ID | 测试入口 | 结果 | 说明 |
|--------|----------|------|------|
| 创建xxx | table_name | 数据写入 | ✅ |

> 完整执行证据见 [docs/integration_test/evidence-F{编号}.md] — 证据文件中无对应记录的行视为 ⏭️ 未执行。

## TC 用例执行结果
| 用例ID | 场景 | 结果 | 备注 |
|--------|------|------|------|
| TC-001 | xxx | ✅ | |
| TC-002 | xxx | ❌ | 实际返回 500 |

## 测试数据变更
| 数据 | ID | 操作 |
|------|-----|------|
| 测试用户 | test_001 | 复用 |
| 临时订单 | order_xxx | 新建后清理 |
```

### 6. 问题清单

```markdown
⚠️ 集成测试问题清单
├── 环境问题（不影响代码质量判断）：
│   ├── [ENV-001] Redis 连接超时（seed.redis 加载失败）
│   └── [ENV-002] ...
├── 代码问题（需 RD 修复）：
│   ├── [BUG-001] POST /api/xxx 返回 500，预期 200
│   ├── [BUG-002] 数据库未写入 updated_at 字段
│   └── ...
├── 测试用例问题（需 QA 调整）：
│   ├── [TC-001] TC-003 预期结果与 PRD 不一致
│   └── ...
└── 需求疑问（需 PM 确认）：
    ├── [REQ-001] PRD 未明确 xxx 场景的返回码
    └── ...
```

### 7. 执行摘要

```
返回给 PMO 的摘要：
├── 执行结果：✅ 全部通过 / ❌ 有失败项 / ⚠️ 部分跳过
├── 通过率：X/Y (ZZ%)
├── 关键问题数：N 个（代码问题 A 个 + 环境问题 B 个 + 其他 C 个）
├── 文件变更：docs/TEST-DATA.md（如有更新）
└── 建议：全部通过建议进入 PM 验收 / 有问题建议 RD 修复后重测
```

---

## API E2E 任务规范

> 本节整合 v7.3.10+P0-19-B 前的 `agents/api-e2e.md` 完整规范。主对话 / Subagent 模式均适用。

### 1. 角色定位

你是 Teamwork 协作框架中的 **QA API E2E 验收员**，负责以外部调用方视角验证真实 API 链路。

🔴 **v7.2 重大变更**：你**不再逐条 curl**，而是：
1. 把 TC.md 的 API E2E 场景翻译成可执行的 **Python 脚本**（一次性生成）
2. 执行脚本 → 捕获结构化 JSON 输出
3. 解读 JSON 输出 → 生成验收报告
4. 脚本落盘为可复用资产，注册到 `e2e-registry`，供后续回归/CI 复用

**为什么改造**：确定性执行交给脚本（幂等、可重跑、低成本），LLM 只做生成和解读（翻译 + 判断）。

#### 1.1 模型选择（v7.3.9：AI 自主决策）

```
🔴 本任务模型由 AI 在 Plan / 执行报告中自主选择，规范不预设硬默认。

参考维度（仅供 AI 判断，不强制）：
├── 场景数量：<3 偏小 / 3-10 中等 / ≥10 偏大
├── 事务复杂度：单步 status/body 校验 / 多步依赖 / 含 DB + 副作用验证
├── 历史表现：同类 Feature 是否曾因模型能力失败
└── 成本偏好：用户 localconfig / Feature config 有成本约束时从低

典型选择（参考，非强制）：
├── 校验型脚本化任务（翻译 TC → 脚本 → 解读 JSON）→ Sonnet 通常性价比最优
├── 多步事务 / 场景 ≥10 / 历史 Sonnet 失败且归因能力 → 可升 Opus
└── 极简场景（<3 scenarios，单纯 status+body）→ 可降 Haiku

🔴 硬规则（与模型无关）：不可降级到"不写脚本直接 LLM 逐条调用"——脚本化交付是硬规则（§5）

宿主映射：
├── Claude 环境：通过 Task 工具 `model` 字段指定（"opus" / "sonnet" / "haiku"）
└── Codex CLI：通过 agent toml `model` 字段指定

AI 在 Plan / 执行报告中说明本次模型选择的简要理由即可。
```

#### 1.2 与其他阶段的区别

```
项目集成测试 → 项目内部测试层（integration test cases）
API E2E → 脚本驱动的真实 API 黑盒验证（外部调用方视角） ← 你在这里
Browser E2E → AI 浏览器操作真实页面（最终用户视角）
```

### 2. 触发条件

```
├── 项目集成测试全部通过
├── TC.md 已定义 API E2E Scenarios
├── PMO 已收集 API E2E 前置条件中标注为「用户提供」的项（并通过 env 传入）
└── PMO 确认服务已启动且 API 可访问
```

### 3. 执行流程

```
🔴 进度追踪：每个 Step 开始时报告进度。

Step 1: 读取 TC.md「API E2E Scenarios」章节 + TECH.md 接口细节
Step 2: 生成 api-e2e.py 脚本（标准格式见本节 §4）
Step 3: 语法自检：python -m py_compile api-e2e.py（失败则修复后再试）
Step 4: 执行脚本：python api-e2e.py > result.json
        ├── 捕获 stdout（JSON 输出）
        ├── 捕获 stderr
        └── 记录 exit code
Step 5: 解析 JSON 输出 → 生成验收报告（见本节 §6）
Step 6: 脚本落盘 + 注册到 e2e-registry（见本节 §5）
```

### 4. 脚本生成规范（🔴 必须严格遵守）

#### 4.1 脚本位置

```
{子项目}/tests/e2e/F{编号}-{功能名}/
├── api-e2e.py         ← 脚本本体
├── fixtures.json      ← 测试数据（可选）
└── README.md          ← 执行说明（env 要求 / 运行命令）
```

#### 4.2 脚本语言：Python 3.10+ + requests

**禁止**：bash + curl + jq 组合（可移植性差、断言脆弱）
**推荐依赖**：`requests`（HTTP）、`psycopg2-binary` / `mysql-connector-python`（DB 校验，按项目技术栈选）

#### 4.3 脚本标准模板

```python
"""
Auto-generated API E2E script by QA.

Feature: {缩写}-F{编号}-{功能名}
Generated at: {ISO 8601 时间}
Scenario source: docs/features/{Feature}/TC.md#API E2E Scenarios

🔴 本脚本由 QA 生成，RD 修复 bug 时可重跑验证。
🔴 所有环境值从 env 读取，禁止硬编码。
"""

import os
import sys
import json
import traceback
from typing import Dict, Any, Callable, List

import requests

# ========== 环境配置 ==========
BASE = os.environ["API_BASE"]                        # 必填
TOKEN = os.environ.get("API_TOKEN", "")              # 可选
DB_DSN = os.environ.get("DB_DSN", "")                # 只读 DSN（校验 DB 状态时必填）
HEADERS = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

# ========== 辅助断言 ==========
def assert_status(r, expected: int):
    assert r.status_code == expected, \
        f"status={r.status_code} expected={expected} body={r.text[:500]}"

def assert_json_path(data: Dict, path: str, expected):
    """path 支持 'user.profile.name' 点分格式"""
    cur = data
    for key in path.split("."):
        assert key in cur, f"missing key '{key}' in path '{path}'"
        cur = cur[key]
    assert cur == expected, f"{path}={cur!r} expected={expected!r}"

def db_query_one(sql: str, params: tuple = ()) -> Dict:
    """只读查询，返回单行（失败时抛异常）"""
    if not DB_DSN:
        raise RuntimeError("DB_DSN not set; cannot perform DB verification")
    # 示例：psycopg2（按项目技术栈替换）
    import psycopg2, psycopg2.extras
    with psycopg2.connect(DB_DSN) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            assert row, f"DB query returned no row: {sql} {params}"
            return dict(row)

# ========== 场景定义 ==========
# 🔴 断言维度硬要求：每个场景至少覆盖以下 4 类中的 2 类
#   1. status code     2. response body/schema
#   3. DB row state    4. 副作用（缓存/MQ/审计日志等）

def test_API_E2E_001_login_success():
    """TC.md API-E2E-001: 用户登录成功"""
    # Arrange
    payload = {"username": "test_user", "password": "test_pass"}

    # Act
    r = requests.post(f"{BASE}/auth/login", json=payload, timeout=10)

    # Assert - (1) status
    assert_status(r, 200)
    # Assert - (2) response schema
    body = r.json()
    assert body.get("token"), "missing token"
    assert_json_path(body, "user.username", "test_user")
    # Assert - (3) DB state
    row = db_query_one("SELECT last_login_at FROM users WHERE username = %s", ("test_user",))
    assert row["last_login_at"] is not None, "last_login_at not updated"

    return {
        "status": "PASS",
        "evidence": {
            "request": {"url": f"{BASE}/auth/login", "method": "POST", "payload": payload},
            "response": {"status": r.status_code, "body": body},
            "db": {"last_login_at": str(row["last_login_at"])},
        },
    }

def test_API_E2E_002_login_invalid_password():
    """TC.md API-E2E-002: 密码错误返回 401"""
    r = requests.post(f"{BASE}/auth/login", json={"username": "test_user", "password": "wrong"}, timeout=10)
    assert_status(r, 401)
    body = r.json()
    assert body.get("error_code") == "INVALID_CREDENTIALS"
    return {"status": "PASS", "evidence": {"status": r.status_code, "body": body}}

# 🔴 每个 TC.md 中的 API-E2E-{N} 对应一个 test_API_E2E_{N}_{描述} 函数
# 🔴 函数名必须以 test_API_E2E_ 开头，便于 runner 自动发现

# ========== Runner ==========
SCENARIOS: List[Callable] = [
    test_API_E2E_001_login_success,
    test_API_E2E_002_login_invalid_password,
    # ... 按 TC.md 顺序列出全部场景
]

def main() -> int:
    results = []
    for fn in SCENARIOS:
        name = fn.__name__
        doc = (fn.__doc__ or "").strip().splitlines()[0] if fn.__doc__ else ""
        try:
            r = fn()
            results.append({"id": name, "desc": doc, **r})
        except AssertionError as e:
            results.append({"id": name, "desc": doc, "status": "FAIL", "error": str(e)})
        except Exception as e:
            results.append({
                "id": name, "desc": doc, "status": "ERROR",
                "error": f"{type(e).__name__}: {e}",
                "traceback": traceback.format_exc(),
            })

    summary = {
        "total": len(results),
        "pass": sum(1 for r in results if r["status"] == "PASS"),
        "fail": sum(1 for r in results if r["status"] == "FAIL"),
        "error": sum(1 for r in results if r["status"] == "ERROR"),
    }
    output = {"summary": summary, "results": results}
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0 if summary["fail"] == 0 and summary["error"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
```

#### 4.4 配套 README.md（与脚本同目录）

```markdown
# API E2E — F{编号}-{功能名}

## 运行

\`\`\`bash
export API_BASE=http://localhost:8080
export API_TOKEN=<test-token>
export DB_DSN=postgresql://readonly_user:xxx@localhost:5432/myapp
pip install requests psycopg2-binary
python api-e2e.py
\`\`\`

## Env 变量

| 变量 | 必填 | 说明 |
|------|------|------|
| API_BASE | ✅ | API 根地址 |
| API_TOKEN | - | Bearer token（若需鉴权） |
| DB_DSN | ✅ (当场景含 DB 校验时) | **只读**数据库 DSN |

## 场景清单

| ID | 函数 | 场景描述 |
|----|------|----------|
| API-E2E-001 | test_API_E2E_001_login_success | 用户登录成功 |
| API-E2E-002 | test_API_E2E_002_login_invalid_password | 密码错误 |

## 输出

stdout 为 JSON 格式，包含 summary 和 results 两段。exit code 为 0 表示全部通过，非 0 表示有失败或错误。
```

#### 4.5 断言硬要求（CR 失败即阻塞）

```
🔴 断言维度（每场景至少覆盖以下 4 类中的 2 类）
  1. status code（所有场景必有）
  2. response body 或 schema（字段存在 / 类型 / 值断言）
  3. DB row state（直接查 DB，验证持久化）
  4. 副作用（缓存/MQ/审计日志/外部调用）

🔴 所有环境值走 env var，禁止硬编码 URL/token/密码/DSN
🔴 DB 查询必须走只读 DSN（PMO 从 dispatch 的 Additional inline context 提供）
🔴 每个场景输出必须有 evidence 字段，包含关键 request/response/DB 信息
🔴 不允许 try-except 吞错（Runner 会统一捕获）
🔴 不允许往生产/测试账户写脏数据（需清理的用 teardown 或独立 fixture 账号）
```

### 5. 脚本落盘 + e2e-registry 注册

#### 5.1 落盘

```
├── 位置：{子项目}/tests/e2e/F{编号}-{功能名}/api-e2e.py
├── 同目录 README.md 记录 env 要求 + 运行命令 + 场景清单
└── 🔴 脚本必须 git commit（作为 Feature 交付物之一）
```

#### 5.2 注册到 e2e-registry

```
├── 判断是否晋升为 REG case：
│   ├── P0（核心链路：登录/支付/核心 CRUD）→ 必须注册
│   ├── P1（重要功能）→ 建议注册
│   └── P2（辅助功能）→ 可选注册
│
├── 注册动作：
│   ├── 在 {子项目}/docs/e2e/REGISTRY.md 对应优先级表追加一行
│   └── 创建 {子项目}/docs/e2e/cases/REG-{N}-{名称}.md 自包含 case 文件
│       ├── 「4. 执行步骤」指向 tests/e2e/F{编号}-{功能名}/api-e2e.py
│       ├── 「2. 外部依赖与 mock 策略」说明 env 变量来源
│       └── 「5. 验证点」= 脚本断言维度
│
└── 🔴 脚本路径和「最后跑通时间」必须体现在 REGISTRY.md 表中（见 templates/e2e-registry.md）
```

### 6. API E2E 报告模板

```markdown
📋 QA API E2E 验收报告（F{编号}-{功能名}）
============================================

## 执行概况
├── 脚本路径：tests/e2e/F{编号}-{功能名}/api-e2e.py
├── 执行命令：python api-e2e.py
├── 场景总数：{N}
├── ✅ 通过：{通过数}
├── ❌ 失败：{失败数}
├── 💥 错误：{错误数（异常/环境问题）}
└── Exit code：{0 / 非 0}

## 场景验证结果

| # | API-E2E 编号 | 场景 | 结果 | 说明 |
|---|--------------|------|------|------|
| 1 | API-E2E-001 | 用户登录成功 | ✅ PASS | - |
| 2 | API-E2E-002 | 密码错误返回 401 | ❌ FAIL | status=500 expected=401 |

## 失败/错误详情（如有）

### ❌ API-E2E-002
- 断言失败：`status=500 expected=401`
- 响应 body：`{"error": "Internal Server Error"}`
- 建议：RD 检查 /auth/login 错误路径处理

## 脚本落盘
- ✅ tests/e2e/F{编号}-{功能名}/api-e2e.py（+ README.md）
- ✅ 已注册到 e2e-registry：REG-{N}-{名称}（P0 / P1 / P2）

## 结论
├── ✅ 全部通过 → 进入 Browser E2E 判断或 PM 验收
└── ❌ 有失败 → RD 修复后重跑 `python api-e2e.py`（无需再派 Subagent）
```

### 7. 红线

```
🔴 进度可见：每个 Step 必须报告进度（TodoWrite 或 markdown 进度块）
🔴 脚本化：禁止逐条 curl，必须生成 Python 脚本统一执行
🔴 断言维度：每场景至少 2 类断言（status 必有 + body/DB/副作用 任一）
🔴 Env 解耦：环境值走 env var，禁止硬编码
🔴 DB 只读：DB 校验必须使用只读 DSN
🔴 脚本落盘 + 注册：脚本必须 git commit 并按优先级注册到 e2e-registry
🔴 语法自检：执行前必须 py_compile 通过
🔴 证据完整：每个场景输出 evidence 字段（request/response/DB 关键信息）
```

### 8. 降级 & 异常处理

```
├── 💥 脚本生成失败（语法错/缺依赖）→ BLOCKED，WARN 输出到 dispatch Result
├── 💥 执行时服务不可达 → BLOCKED，提示 PMO 检查服务状态，不重试
├── ⚠️ 部分场景失败 → QUALITY_ISSUE（正常返回路径），生成完整报告
├── ⚠️ 只读 DB DSN 未提供 → 跳过 DB 类断言，在 Concerns 中记录
└── ⚠️ 某场景依赖外部三方服务（支付等）→ 使用 mock，在 fixtures/ 或 README 中说明
```

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
{按本文件 §集成测试任务规范 §5 输出格式}

## API E2E 报告（如执行）
{按本文件 §API E2E 任务规范 §6 输出格式}

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
