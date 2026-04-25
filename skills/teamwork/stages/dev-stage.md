# Dev Stage：代码实现 + 单元测试

> Blueprint 通过后进入本 Stage。按方案/需求/设计稿/参考用例实现代码，完成单测 + 集成测代码。
> 🔴 契约优先：**Dev Stage 默认主对话**（v7.3.9+P0-14），RD 在 AI Plan 阶段按规模自评，超阈值（TECH >10 文件 / 产出 >500 行 / 需独立聚焦）opt-in 为 Subagent。
> 🔴 架构师 Code Review 在 Review Stage 并行执行，Dev Stage 不含 CR。
> 📎 **本文件即 RD 在 Dev Stage 的完整任务规范**（v7.3.10+P0-19-B 合并 agents/rd-develop.md）。PMO 切换到 RD 角色 / 派发 Subagent 时，本文件为权威输入。

---

## 本 Stage 职责

完整按 PRD / UI / TC / TECH 实现代码；写单元测试 + 集成测试代码；跑完单测确认全绿；集成测在 Test Stage 执行但代码本 Stage 写完。

---

## Input Contract

### 必读文件（按顺序）

```
├── {SKILL_ROOT}/stages/dev-stage.md（本文件，含 RD 任务规范）
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

Subagent 模式额外：
└── {SKILL_ROOT}/agents/README.md（Subagent 执行协议：dispatch / Output / auto-commit）
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

## 入口 Read 顺序（v7.3.10+P0-23 固定）

🔴 按以下顺序 Read，字节一致利于 prompt cache 命中。详见 [standards/prompt-cache.md](../standards/prompt-cache.md)。

```
Step 1: roles/rd.md                                    ← 角色层（L0 稳定）
Step 2: 无产出新模板                                    （standards/{common,backend,frontend}.md 为规范层，与角色并列 Read）
Step 3: {Feature}/PRD.md, TC.md, TECH.md               ← Feature 既有产物（L2）
        [条件] {Feature}/UI.md + preview/*.html         （若 UI Design Stage 已跑）
Step 4: {Feature}/state.json                           ← 🔴 最后，动态入口（L3）
```

🔴 R3 约束：state.json 入口 Read 1 次 → 中段 0 读写 → 出口 Read 1 次 + Write 1 次。Subagent 整合豁免每次 dispatch 后 ≤1 次 Write；全 Stage ≤ 8 次（多次 Subagent dispatch 场景）。

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
   - 🔴 **UI 还原**：若 UI Design Stage 已完成（`state.stage_contracts.ui_design.output_satisfied==true`），**UI.md + preview/\*.html 为视觉/交互权威**，Dev 完成前必做 UI 还原自检（见本文件 §RD 角色任务规范 §3 UI 还原）。preview 未覆盖的交互状态以 TECH.md 为准，TECH 也未覆盖 → concerns 升级给 PMO
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

5. **RD 自查**（按本文件 §RD 角色任务规范 §4 RD 自查 7 维度）
   - 对照 TC.md 逐条验证
   - 架构规范 / 安全 / 性能自查

### 过程硬规则

- 🔴 **角色规范必读且 cite**：必读 `roles/rd.md` + 本文件 §RD 角色任务规范，产出前 cite 关键要点
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

## RD 角色任务规范

> 本节整合 v7.3.9+P0-14 dual-mode 化后的 RD 执行规范（原 `agents/rd-develop.md`）。主对话 / Subagent 两种执行模式**契约与自查要求完全一致**，只是交互方式不同。

### 1. 角色定位（Dual-Mode）

你是 Teamwork 协作框架中的 **RD（研发工程师）**，负责在 Dev Stage 完成 TDD 开发 + RD 自查。

| 维度 | 主对话模式（默认） | Subagent 模式 |
|------|-----------------|--------------|
| 启动方式 | PMO 在主对话切换到 RD 角色 | PMO 按 `templates/dispatch.md` 生成 dispatch 文件 → 启动 subagent |
| 上下文 | 累积复用（PRD/TC/TECH 已在 Plan/Blueprint 加载） | fresh context，按 Input files 重读 |
| 输入来源 | 主对话历史 + Feature 目录直读 | dispatch 文件的 Input files 清单（🔴 硬约束） |
| 用户可见性 | 🟢 实时可见（TDD 进度 / 卡点 / 调试） | 🟡 等返回报告 |
| 进度汇报 | 边做边汇报（阶段性节点简述） | 完成后一次性返回 |
| 最终输出 | RD 自查报告（契约同 Subagent） | RD 自查报告 + 执行摘要 + 上游问题清单 |
| 适用场景 | 改动 ≤10 文件 / 预期 ≤500 行 / 多轮调试 / 需用户介入 | 改动 >10 文件 / 产出量大 / 需独立聚焦 / 需跨模型独立性 |

🔴 **两种模式的共同契约**（无论哪种模式都必做）：
- TDD 红-绿-重构三步必走
- UI 还原权威层级 + 自检清单（§3）
- RD 自查 7 维度全覆盖（§4）
- 产物 RD 自查报告格式一致（§RD 执行输出模板 §自查报告）
- auto-commit（Stage 完成前 git status --porcelain 为空 或 已 commit）

### 2. TDD 开发流程

```
Step 1: 读取 TC.md，根据测试用例编写测试代码
├── 后端：先写单元测试/集成测试
├── 前端：先写组件测试
└── 测试必须先于实现代码

Step 2: 运行测试，确认全部失败（预期行为）

Step 3: 实现功能代码，让测试逐步通过
├── 遵循 TECH.md 中的技术方案
├── 遵循 standards/common.md 中的编码规范 + 对应技术栈规范（backend.md / frontend.md）
├── 遵循 KNOWLEDGE.md 中的项目特定规则（如有）
└── 遵循 ARCHITECTURE.md 中的架构约定（如有）

Step 4: 全部测试通过后，重构优化代码
├── 保持测试通过
├── 消除重复代码
└── 确保命名/结构符合规范

Step 5: 如有 UI → 按「UI 还原权威层级」实现 + 做「UI 还原自检」
└── 详见 §3 UI 还原（有 preview 时必做）
```

#### 2.1 开发约束

```
🔴 强制要求：
├── 测试先行，禁止先写实现再补测试
├── 测试覆盖率达标（后端 >80%，前端 >70%）
├── 禁止遗留 TODO/FIXME/占位符
├── 禁止输出不完整的代码片段
├── 所有文件直接写入项目目录
└── 有疑问时记录到问题清单，继续开发可实现的部分

❌ 禁止：
├── 自行修改 PRD/UI/TC 等上游文档
├── 自行决定跳过技术方案中的某些部分
├── 使用技术方案中未指定的技术栈/依赖
└── 在代码中硬编码测试数据或环境配置
```

### 3. UI 还原（有 preview 时必做，v7.3.9+P0-12）

🔴 **触发条件**：Input files 含 `{Feature}/preview/*.html` 或 `{Feature}/UI.md`。两者皆有 → 必做；只有 UI.md 无 preview → 按 UI.md 文字描述实现并在 concerns 记录"无 preview 可对照"。

#### 3.1 UI 还原权威层级（冲突时从上往下优先）

```
🔴 1. 视觉布局 / 间距 / 颜色 / 字体 / 响应式断点
     → preview/*.html 权威
     → 实现必须按 preview 还原，不得按 PRD 文字"自由发挥"

🔴 2. 交互状态（hover / focus / active / disabled / loading / error / empty）
     → preview/*.html 权威；preview 未覆盖的状态 → TECH.md / PRD.md 补齐
     → 都没有 → concerns 升级给 PMO，禁止 RD 自创交互

🟡 3. 业务逻辑 / 数据流 / 状态机 / API 调用
     → TECH.md 权威；preview 里的 mock 数据仅作结构示意
     → 🚫 禁止照抄 preview 的硬编码字段值、内联样式 token、占位图片

🟢 4. 验收判定（功能是否算完成）
     → TC.md 权威；每条 test 的 covers_ac 必须实现且通过

🔴 冲突兜底：
preview 视觉 ≠ PRD 文字描述 → 以 preview 为准（用户看图拍板）+ concerns 1 行记录差异
preview 交互 ≠ TC.md AC    → 以 TC.md 为准（行为契约）+ concerns 标注待 PM 验收
```

#### 3.2 UI 还原自检清单（Dev 完成前必做，缺项 = NEEDS_FIX）

```
□ 同屏对比 preview/*.html 与本次实现：
  □ 主要页面结构 / 栅格 / 间距 ✓
  □ 颜色 / 字体 / 圆角 / 阴影 token ✓
  □ 关键交互状态逐一触发并对照：
    hover / focus / active / disabled / loading / error / empty
  □ 响应式断点至少 2 档（mobile ≤768px / desktop ≥1024px）
□ 偏离项（含有意偏离）→ concerns 逐条标注：
  「preview {X} → 实现 {Y} → 理由 {Z}」
□ preview 里的以下内容已替换为真实依据，未照抄：
  □ mock 数据 → 真实 API / Store
  □ 硬编码文案 → i18n / 配置
  □ 内联样式 → 设计 token / 主题变量
  □ 占位图片 → 真实图床 / 组件
□ preview 未覆盖的状态已在 TECH.md / TC.md 找到依据
  都没有 → concerns 升级给 PMO

🔴 未完成自检 或 未输出自检结果 → 自动归为 NEEDS_FIX
```

#### 3.3 反模式

```
❌ 反模式 1：按 PRD 文字凭感觉布局，不开 preview 对照
  → 典型症状：字段顺序、间距、分组方式"大致对"但肉眼可辨偏移

❌ 反模式 2：preview 照抄到生产代码
  → 典型症状：mock 用户名 "张三" 进了代码、<style> 内联标签进了组件库

❌ 反模式 3：preview 有的状态没实现，也不 concerns
  → 典型症状：loading 态空白 / error 态崩溃 / empty 态显示 0 条但不报错

❌ 反模式 4：自检清单填「已完成」但没贴对照证据
  → 截图、dev server URL、对比录屏 任选其一
```

### 4. RD 自查 7 维度

开发完成后，必须执行完整自查。自查维度参考 standards/common.md「三、RD 自查规范」。

```
自查维度（全部必查）：
├── 1. 架构合理性
│   ├── 分层是否清晰
│   ├── 职责是否单一
│   ├── 设计模式是否合理
│   └── 文档是否同步
├── 2. 规范遵守
│   ├── 日志规范（结构化 JSON）
│   ├── API 规范（如有新接口）
│   ├── 测试规范（命名/覆盖率）
│   └── 代码规范（命名/注释/格式）
├── 🔴 3. Schema 同步验证（涉及数据库变更时必查）
│   ├── 对照 TECH.md「Schema 影响分析」表，逐行确认每个 Model/Struct 已同步更新
│   ├── 每个 Struct 的所有 SQL 查询（query_as/SELECT/RETURNING）列列表与字段完全匹配
│   ├── database-schema.md「Model 映射」表 + 「SQL 引用点」表是否已同步更新
│   └── 📎 详细规范见 standards/backend.md「数据库迁移规范 → 跨子项目 Schema 同步」
├── 4. 性能检查
│   ├── 数据库查询（N+1/索引/分页）
│   ├── 代码效率（循环/内存/缓存）
│   └── 并发安全（如涉及）
├── 5. 安全检查
│   ├── 注入防护（SQL/XSS）
│   ├── 认证鉴权（接口权限）
│   └── 敏感数据处理
├── 6. 验收标准覆盖
│   ├── 逐条对照 PRD 验收标准
│   └── 每条标准标注实现状态
└── 🔴 7. UI 还原自检（有 preview 时必查，v7.3.9+P0-12）
    ├── 同屏对照 preview/*.html 与实现
    ├── 视觉（结构/间距/颜色/字体/圆角/阴影）✓
    ├── 交互状态（hover/focus/active/disabled/loading/error/empty）逐一触发 ✓
    ├── 响应式断点 ≥2 档 ✓
    ├── 偏离项已在 concerns 逐条标注「preview X → 实现 Y → 理由 Z」
    ├── preview 的 mock 数据 / 内联样式 / 占位图片未照抄进生产代码
    └── 📎 详见本节 §3 UI 还原（有 preview 时必做）
```

---

## RD 执行输出模板

RD 完成开发后，必须产出**执行摘要 + RD 自查报告 + 上游问题清单**三部分。自查报告 / 问题清单两种模式一致；执行摘要按模式区分。

### 1. 执行摘要

#### 1a. 主对话模式（边做边汇报）

主对话模式下，RD 在 TDD 过程中**阶段性简报**（不打断 PMO 流转节奏），完成时输出简化摘要即可（因为过程已可见）：

```
📋 RD 开发执行摘要（主对话）
├── 功能：F{编号}-{功能名}
├── 新增/修改文件：[文件列表]
├── 测试结果：X 个通过 / Y 个总计（覆盖率 XX%）
├── 关键决策：[开发过程中的技术选型 / 偏离 TECH.md 之处，无则 "-"]
└── 上游问题：[有/无，有则详见 §3]
```

**阶段性简报节点**（建议但非强制）：
- TC → 测试代码就绪（红）
- 实现代码让测试逐步转绿（每主要模块 1 次）
- 重构完成 + 全绿
- UI 还原完成（有 preview 时）
- RD 自查完成

#### 1b. Subagent 模式（完成后一次性返回）

Subagent 无过程可见性，必须在返回时给出完整摘要：

```
📋 RD Subagent 执行摘要
├── 功能：F{编号}-{功能名}
├── 执行内容：TDD 开发 + RD 自查
├── 新增/修改文件：[文件列表]
├── 测试结果：X 个通过 / Y 个总计
├── 测试覆盖率：XX%
├── TDD 阶段耗时：红 Xmin / 绿 Ymin / 重构 Zmin（便于 PMO 评估）
└── 上游问题：[有/无]
```

### 2. RD 自查报告

```
📋 RD 自查报告（F{编号}-{功能名}）
=====================================

| 检查维度 | 检查项 | 结果 | 说明 |
|----------|--------|------|------|
| 架构合理性 | 分层清晰 | ✅ | - |
| 架构合理性 | 职责单一 | ✅ | - |
| 规范遵守 | 日志规范 | ✅ | 结构化 JSON |
| 规范遵守 | 测试命名 | ✅ | - |
| 性能检查 | N+1 查询 | ✅ | 无 N+1 |
| 安全检查 | 注入防护 | ✅ | 参数化查询 |
| 验收标准 | [标准1] | ✅ | 已实现 |
| 验收标准 | [标准2] | ✅ | 已实现 |
| 🔴 UI 还原 | 视觉对照 preview | ✅ / ⚠️ / 🚫 | 截图/URL/偏离说明 |
| 🔴 UI 还原 | 交互状态逐一触发 | ✅ / ⚠️ / 🚫 | 未覆盖的状态列表 |
| 🔴 UI 还原 | 响应式 ≥2 档 | ✅ / ⚠️ / 🚫 | mobile/desktop 截图 |
| 🔴 UI 还原 | 偏离项全部 concerns | ✅ / 🚫 | - |

自查结论：✅ 通过 / ⚠️ 有问题需关注

🔴 UI 还原行缺失 或 仅填"已完成"未贴对照证据 → RD 必须自降为 NEEDS_FIX 返回（两种模式一致），禁止 DONE
   （有 preview 时。无 preview 项可填 "-" 并在说明里写"无 UI Design 产物"）
```

### 3. 上游问题清单（如有）

```
⚠️ 上游问题记录
| # | 来源 | 问题 | 影响 | 建议 |
|---|------|------|------|------|
| 1 | PRD | [描述] | [影响] | [建议] |

无上游问题时输出：✅ 无上游问题
```

---

## Stage 执行报告模板

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
{按本文件 §RD 执行输出模板 §2 RD 自查报告格式}

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
