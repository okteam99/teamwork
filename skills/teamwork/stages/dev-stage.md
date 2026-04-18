# Dev Stage：代码实现 + 单元测试

> Blueprint 通过后进入本 Stage。按方案/需求/设计稿/参考用例实现代码，完成单测 + 集成测代码。
> 🔴 契约优先：**Dev Stage 由 AI 自主决定执行方式**（主对话 / Subagent / 混合，按规模判断）。
> 🔴 架构师 Code Review 在 Review Stage 并行执行，Dev Stage 不含 CR。

---

## 本 Stage 职责

完整按 PRD / UI / TC / TECH 实现代码；写单元测试 + 集成测试代码；跑完单测确认全绿；集成测在 Test Stage 执行但代码本 Stage 写完。

---

## Input Contract

### 必读文件（按顺序）

```
├── {SKILL_ROOT}/agents/README.md
├── {SKILL_ROOT}/stages/dev-stage.md（本文件）
├── {SKILL_ROOT}/agents/rd-develop.md（RD 开发规范）
├── {SKILL_ROOT}/roles/rd.md
├── {SKILL_ROOT}/standards/common.md                 ← 必读
├── {SKILL_ROOT}/standards/backend.md                ← 后端项目必读
├── {SKILL_ROOT}/standards/frontend.md               ← 前端项目必读
├── {Feature}/PRD.md                                 ← 需求（AC 结构化）
├── {Feature}/TC.md                                  ← 测试用例（tests[] 含 covers_ac）
├── {Feature}/TECH.md                                ← 技术方案
└── {Feature}/UI.md + preview/*.html（如有）

可选：
├── docs/KNOWLEDGE.md
└── docs/architecture/ARCHITECTURE.md
```

### Key Context（逐项判断，无则 `-`）

- 历史决策锚点：既定约定、技术栈限制、已有模式
- 本轮聚焦点：重派或修复场景必填
- 跨 Feature 约束：禁改文件列表（其他 Feature 正在修改的）
- 已识别风险：KNOWLEDGE.md 中的陷阱（N+1、缓存击穿、并发等）
- 降级授权：例如 worktree 失败授权主分支直接执行
- 优先级 / 容忍度

### 前置依赖

- `{Feature}/PRD.md` + `TC.md` + `TECH.md` 存在且 `state.json.stage_contracts.blueprint.output_satisfied == true`
- state.json.current_stage == "dev"
- Worktree 策略已处理（见下方"Worktree 集成"）

---

## Process Contract

### 必做动作

1. **完整按方案实现**
   - 按 TECH.md 的文件清单和改动要点实现
   - 对照 UI.md / preview/*.html（如有）还原 UI
   - 对照 PRD AC 逐条检查功能覆盖
   - 对照 TC.md 确保每条 test 的实现存在

2. **TDD 开发**（推荐，弱约束）
   - 推荐"先写测试（红）→ 实现（绿）→ 重构"
   - 机器无法校验时序，但推荐在主对话日志记录"先写 test X 再实现 Y"
   - 弱约束不代表可跳过测试

3. **写完整测试代码**
   - 单元测试：每条 TC.md 中 level=unit 的 test 必须实现
   - 集成测试代码：level=integration 的 test 写代码（执行在 Test Stage）
   - API E2E case：level=e2e 的 test 预留结构（脚本化在 Test Stage 完成）

4. **跑单元测试**
   - 🔴 Dev Stage 返回前单测必须全绿
   - 实际测试命令 + 输出作为产物证据

5. **RD 自查**（按 `agents/rd-develop.md`）
   - 对照 TC.md 逐条验证
   - 架构规范 / 安全 / 性能自查

### 过程硬规则

- 🔴 **角色规范必读且 cite**：必读 `roles/rd.md` + `agents/rd-develop.md`，产出前 cite 关键要点
- 🔴 **Standards 强制加载**：`common.md` 必读；按项目类型加载 `backend.md` 或 `frontend.md`，Execution Plan 中声明已加载
- 🔴 **完整按方案**：禁止偏离 TECH.md（如需偏离，必须在产出报告中显式标注 + 理由）
- 🔴 **单测全绿**：Dev Stage 返回前单测必须通过，带着失败测试返回 = FAILED
- 🔴 **不做 Code Review**：架构师 CR / QA CR 在 Review Stage
- 🔴 **实际测试输出**：自查报告必须附测试命令 + 结果，禁止空口"通过"
- 🔴 **无 TODO/FIXME/占位符**：产出代码不能留 TODO（非本 Feature 范围的例外，显式标注）

---

## Output Contract

### 必须产出的文件

| 文件路径 | 格式 | 必需内容 |
|---------|------|---------|
| `{子项目}/src/**/*` | 代码 | 按 TECH.md 文件清单的新增/修改 |
| `{子项目}/tests/unit/**/*` | 代码 | 每条 TC.md level=unit 的 test 实现 |
| `{子项目}/tests/integration/**/*` | 代码 | 每条 TC.md level=integration 的 test 代码（未执行） |
| `{Feature}/dev-report.md`（或 dispatch Result 段） | Markdown | 代码变更清单 + 测试输出 + RD 自查报告 |

### 机器可校验条件（🔴 硬门禁）

- [ ] 单测：`npm test` / `pytest tests/unit` / `go test ./...` 等 exit 0
- [ ] Typecheck：`npm run typecheck` / `mypy` / `tsc --noEmit` exit 0（如项目有配置）
- [ ] Lint：`npm run lint` / `ruff check` / `golangci-lint run` exit 0（如项目有配置）
- [ ] 无 TODO/FIXME：`grep -rE "TODO|FIXME" {变更文件}` 为空（除非标注"out-of-scope"）
- [ ] 代码实际落盘（不是只在对话中展示）
- [ ] 测试文件与 TC.md `tests[]` 对应

### Done 判据

- 所有产出文件存在
- 上述所有机器校验 exit 0
- RD 自查通过（含验证证据）
- `state.json.stage_contracts.dev.output_satisfied = true`

### 返回状态

| 状态 | 条件 | 后续 |
|------|------|------|
| ✅ DONE | 单测全绿 + 自查通过 | 进入 Review Stage |
| ⚠️ DONE_WITH_CONCERNS | 单测通过但有非阻塞问题（上游文档疑似有误等）| PMO 判断是否暂停 |
| 💥 FAILED | 环境异常 / 无法编译 / 单测持续失败 | PMO 降级处理 |

---

## AI Plan 模式指引（本 Stage 特别重要）

📎 Execution Plan 3 行格式 → [SKILL.md](../SKILL.md#-ai-plan-模式规范v73-新增)。

本 Stage 默认 **AI 自主按规模/复杂度决定** approach（Dev Stage 是改造的核心自主决策点）：

| 条件 | 推荐 |
|------|------|
| 改动 ≤ 3 文件 + 逻辑简单（无多模块联动）| `main-conversation`（省冷启动）|
| 改动复杂 / 产出 >500 行 / 多模块联动 | `subagent`（隔离主对话）|
| 严格 TDD 红-绿循环 + 独立聚焦 | `subagent`（独立 context）|
| 多轮调试 / 探索 / 环境问题 | `main-conversation`（保留调试 context）|
| 跨 Feature / 需对照其他进行中 Feature | `main-conversation`（累积 context 有用）|

Plan 的 Rationale 必须说明"基于规模/复杂度的判断"。Plan 写入 `state.json.planned_execution.dev`。

### Worktree 集成（PMO 执行，不受 Subagent/主对话影响）

```
worktree 策略（从 .teamwork_localconfig.md 读取）：

├── off → 跳过
├── manual → PMO 提醒用户创建
└── auto → PMO 自动创建 + 记录到 state.json 的 worktree 字段

AI 选主对话方案时：cwd 切到 worktree 路径执行
AI 选 Subagent 方案时：dispatch 文件 cwd 字段写入 worktree 路径

Review / Test Stage 复用同一 worktree。
PMO 在 Feature 完成时清理（auto 模式）或提醒用户（manual 模式）。
```

---

## 执行报告模板

```
📋 Dev Stage 执行报告（F{编号}-{功能名}）
============================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / FAILED}
├── 执行方式：{主对话 / Subagent / 混合}（来自 Execution Plan）
├── 单元测试：{通过数/总数}
├── Typecheck：{pass / fail / 无配置}
├── Lint：{pass / fail / 无配置}
└── 实际测试输出：{测试命令 + 结果}

## RD 自查报告
{按 agents/rd-develop.md 输出格式}

## 代码变更清单
| 文件 | 操作 | 说明 | TECH.md 对应章节 |
|------|------|------|------------------|

## 测试覆盖
| TC ID | 测试文件 | 测试函数 | covers_ac | 通过 |
|-------|---------|---------|-----------|------|

## Output Contract 校验
├── 单测：✅ X/X 通过
├── Typecheck：✅ / ⏭️ 无配置
├── Lint：✅ / ⏭️ 无配置
├── 无 TODO：✅
└── TC↔test 对应：✅ 全覆盖

## Concerns（如有）
{非阻塞性问题}
```
