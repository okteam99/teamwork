# Dev Stage：代码实现 + 单元测试

> Blueprint 通过后进入本 Stage。按方案/需求/设计稿/参考用例实现代码，完成单测 + 集成测代码。
> 🔴 契约优先：**Dev Stage 默认主对话**（v7.3.9+P0-14），RD 在 AI Plan 阶段按规模自评，超阈值（TECH >10 文件 / 产出 >500 行 / 需独立聚焦）opt-in 为 Subagent。
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
└── {Feature}/UI.md + preview/*.html
    🔴 若 state.stage_contracts.ui_design.output_satisfied==true → **必读（视觉/交互权威）**
    🟡 若 UI Design Stage 未跑 → 跳过该项

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

### Stage 入口 Preflight：懒装依赖（P0 新增）

> 🟢 **P0 懒装依赖模型**：Feature worktree 创建时不装依赖（见 plan-stage.md）。进入 Dev Stage 第一件事是检测依赖并按需安装。

```
1. 检测依赖产物是否存在：
   ├── Node 项目    → 检查 node_modules/ 是否存在且与 package.json 一致
   ├── Python 项目  → 检查 .venv / site-packages 是否存在且与 requirements.txt / pyproject.toml 一致
   ├── Go 项目      → 检查 $GOPATH/pkg/mod（模块缓存通常共享，一般无需额外动作）
   └── 其他 → 参照项目 README / ARCHITECTURE.md

2. 不存在 / 不一致 → 尝试低代价路径：
   ├── 从父 worktree symlink（Linux/macOS）：ln -s ../主仓/node_modules ./node_modules
   │   └── 成功 → 跳过 install，节省 1-5 分钟
   └── symlink 不可用 / 失败 → 跑完整 install（npm install / pip install / uv sync / pnpm install）

3. install 失败 → BLOCKED（报告具体错误给 PMO 安排解决）

4. 成功后将依赖状态记录到 state.json.stage_contracts.dev.dependency_install：
   ├── method: "symlink" | "fresh-install" | "skipped"
   ├── duration_seconds: N
   └── installed_at: ISO 时间戳
```

🔴 **规则**：Dev Stage 开始"完整按方案实现"之前，依赖必须就绪（或显式 skip 的理由写入 state.json）。不允许在 TDD 循环中临时装依赖导致不稳定。

### 必做动作

1. **完整按方案实现**
   - 按 TECH.md 的文件清单和改动要点实现
   - 🔴 **UI 还原**：若 UI Design Stage 已完成（`state.stage_contracts.ui_design.output_satisfied==true`），**UI.md + preview/\*.html 为视觉/交互权威**，Dev 完成前必做 UI 还原自检（见 `agents/rd-develop.md § UI 还原权威层级 + UI 还原自检清单`）。preview 未覆盖的交互状态以 TECH.md 为准，TECH 也未覆盖 → concerns 升级给 PMO
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
- 🔴 **Stage 完成前 git 干净** → 统一遵循 [rules/gate-checks.md § Stage 完成前 git 干净](../rules/gate-checks.md#-stage-完成前-git-干净v739-硬规则p0-集中化)（本 Stage commit message：`F{编号}: Dev Stage - {简述}`；给 Review Stage 提供稳定 diff 锚点）

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

🔴 **v7.3.9+P0-14 默认主对话**：Dev Stage 默认 `main-conversation`；subagent 是 opt-in 路径（有明确理由才选）。RD 在 AI Plan 阶段按规模自评 + 声明 Rationale。

| 条件 | 推荐 mode | 说明 |
|------|---------|------|
| 默认（无特别信号） | `main-conversation` | 大多数 Feature（改动 ≤10 文件、产出 ≤500 行）主对话最优：省冷启动、用户可见 TDD 过程、便于多轮调试 |
| TECH.md 文件清单 >10 / 预期产出 >500 行 | `subagent` | 大改动独立聚焦，避免主对话被大量代码细节淹没 |
| 严格 TDD + 跨模型独立性需求（罕见） | `subagent` | 仅当明确需要 fresh context 保障独立性时 |
| 多轮调试 / 探索 / 环境问题 / 跨 Feature 对照 | `main-conversation`（强化默认）| 累积 context 有实质价值 |
| 灰色地带（临界规模） | `main-conversation`（向默认倾斜）| 存疑时选默认，错了下一个 Feature 再切换 |

🟢 **灰色地带判定示例**：
- 「10 文件 / 400 行 / 单模块」→ 主对话（边界内）
- 「12 文件 / 600 行 / 跨前后端」→ subagent（超边界）
- 「8 文件 / 300 行 / 但需 3 轮 TDD 迭代调试」→ 主对话（调试需要过程可见）

Plan 的 Rationale 必须说明"基于规模/复杂度的判断"。Plan 写入 `state.json.planned_execution.dev`（含 approach + rationale + estimated_minutes）。

**Expected duration baseline（v7.3.3 / v7.3.9+P0-14 微调）**：
- **主对话（默认）**：≤3 文件 15-25 min / 5-10 文件 30-60 min（大多数 Feature 落此档）
- **Subagent（opt-in）**：中大改动 30-90 min（>10 文件或 >500 行时选用，含冷启动 3-5 min 税）
- 大改动（>10 文件 / 多模块）全 subagent 60-120 min

AI 在 `Estimated` 字段按 TECH.md 的文件清单数和复杂度校准。

### Worktree 集成（PMO 执行，v7.3.8 改为校验存在；创建已前移到 Plan Stage 入口）

```
前提：worktree=auto 时 worktree 已在 Plan Stage 入口创建（见 stages/plan-stage.md §Worktree 集成）
Dev Stage 入口 PMO 只做校验 + 使用，不再负责创建。

worktree 校验流程：
├── 读 state.json.worktree.{strategy, path, branch}
├── strategy == "off" → 跳过，主分支执行
├── strategy == "auto" / "manual"：
│   ├── 路径存在 + 分支检出正确 → ✅ 沿用
│   ├── 路径缺失（被误删 / 机器迁移）→ 🔴 补建 worktree（auto 时自动，manual 时提醒用户）
│   │   并在 state.json.concerns 追加 "worktree 丢失已补建" WARN
│   └── 分支不匹配（被手动 checkout）→ 🔴 恢复分支并继续
└── cwd 切换到 worktree 路径（Subagent 执行时 dispatch 文件 cwd 字段同步写入）

Review / Test / Browser E2E Stage 复用同一 worktree（不再创建）。
PMO 在 Feature 完成（commit+push 之后）清理：
├── auto 模式 → 询问用户 "是否清理 worktree"（不自动删，保留检视机会）
└── manual 模式 → 提醒用户自行清理

为什么 Dev Stage 不再负责创建（v7.3.8 修订）：
├── 前移到 Plan Stage 后，PRD/UI/Blueprint 所有产物都在 feature 分支
├── Dev Stage 入口 worktree 必然已存在（正常流转顺序）
└── 补建逻辑作为异常分支保留（机器迁移 / 用户误删 / off→auto 中途切换）
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
