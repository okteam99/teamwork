# Review Stage：三视角独立代码审查

> Dev Stage 通过后进入本 Stage。产出三份**独立视角**的代码审查报告（架构师 / QA / 外部），汇合到 REVIEW.md。
> 🔴 契约优先：独立性通过**产物结构**保证（而非强制执行方式）。AI 可按场景选择实现路径。
> 📎 **角色 CR 详细任务规范已迁出（v7.3.10+P0-87）**：架构师 → [roles/architect-cr.md](../roles/architect-cr.md)；QA → [roles/qa-cr.md](../roles/qa-cr.md)。本文件仅留 Stage 调度契约 + 短指针（§架构师 CR 任务规范 / §QA CR 任务规范）。外部模型视角单独走对应 CLI spawn（按 state.external_cross_review.model 选择 codex-agents/ 或 claude-agents/），prompt 模板见本文件 §外部模型代码 Review 任务规范。

---

## 本 Stage 职责

对 Dev Stage 产出的代码从三个独立视角审查：
- **架构师视角**：架构合理性、代码规范、ARCHITECTURE.md 同步
- **QA 视角**：TC 逐条验证覆盖、TDD 规范、测试质量
- **外部独立视角**（Codex 或等效外部模型）：发现同模型盲区、安全、第三方依赖

---

## 可配置点清单（v7.3.10+P0-55 新增）

| 可配置点 | 默认值 | 控制字段 | 决策时机 |
|---------|-------|---------|---------|
| `review_roles[]` | architect + qa + external（推荐默认含 external，代码层最后 gate）| `state.review_substeps_config.review_roles[]` | Stage 入口实例化 |
| 各角色 `execution` | architect / qa subagent（防鼓掌效应）+ external external-shell | `state.review_substeps_config.review_roles[].execution` | Stage 入口实例化 |
| `parallel_mode` | true（三视角并行）| `state.review_substeps_config.parallel_mode` | Stage 入口实例化 |
| `schema_change_triggered` | git diff 含 migration / DDL / schema 改动 | `state.schema_change_evidence.detected_at_review` | 架构师 CR 入口判断（v7.3.10+P0-119）|
| 修复循环 max | 3 轮 | spec 内嵌 | Stage 出口判断 |
| 模型偏好（v7.3.10+P0-40）| Opus（AI Plan 模式默认）| `state.planned_execution.review.model` | Stage 入口 |
| `hint_overrides` | null | `state.review_substeps_config.hint_overrides` | Stage 入口实例化偏离 hint 时 |

🔴 不变内核：三视角独立性产物结构（独立 generated_at + files_read + 互不引用）+ external 异质性硬约束 + 完整性硬规则（按各自规范完整执行）。

🔴 **schema 变更触发**（v7.3.10+P0-119 新增）：
- 入口实例化时 grep dev 产物：`git diff --name-only` 命中 `*.sql` migration / `src/**/migrations/*` / `src/**/schema.{rs,py}` / `src/**/models/*`
- 命中 → state.schema_change_evidence.detected_at_review 写入（与 P0-101 evidence-binding 协同 · 含 command + stdout + timestamp）
- 命中 → 架构师 CR 必启用「DB schema 变更 CR 专项」checklist（cite [roles/architect-cr.md § 2.1](../roles/architect-cr.md)）
- 命中 → 评审 verdict 不允许把「全局 schema 文档已更新」降级为 PASS_WITH_CONCERNS（实证 SVC-PLATFORM-F034 case）
- 命中 → CR 启动时执行全仓库 find 自检：`find {repo_root} -name "*database*schema*.md"` 比对 state.json.global_schema_docs[]（防 monorepo 嵌套漏检）

---

## Input Contract

### 共用必读文件

```
├── {SKILL_ROOT}/stages/review-stage.md（本文件，含三视角任务规范）
├── {Feature}/PRD.md
├── {Feature}/TC.md
├── {Feature}/TECH.md
├── Dev Stage 产出（代码 diff + 自查报告路径）
└── {SKILL_ROOT}/standards/common.md

Subagent 模式额外：
└── {SKILL_ROOT}/agents/README.md（Subagent 执行协议）
```

### 各视角专属必读

```
架构师视角 额外读：
├── {SKILL_ROOT}/roles/architect.md（角色契约 · v7.3.10+P0-86 独立 role）
├── {SKILL_ROOT}/roles/architect-cr.md（CR 详细任务规范 · v7.3.10+P0-87 抽出）
└── docs/architecture/ARCHITECTURE.md

QA 视角 额外读：
├── {SKILL_ROOT}/roles/qa.md（角色契约）
├── {SKILL_ROOT}/roles/qa-cr.md（CR 详细任务规范 · v7.3.10+P0-87 抽出）
└── {Feature}/UI.md + preview/*.html（如有，用于设计-代码一致性）

外部视角（Codex / 其他模型） 额外读：
├── 🔴 严禁读：架构师 Review 报告（保持独立性）
└── 只基于代码 diff + PRD/TECH/TC + standards
```

### Key Context（逐项判断，无则 `-`）

- 本轮聚焦点（重跑时必填：上一轮问题清单）
- 已识别风险
- 降级授权（Codex CLI 不可用 → 🟢 AI 自主判断适合的降级模式，参考 agents/README.md §三「降级路径决策」）
- 优先级 / 容忍度

### 前置依赖

- `state.json.stage_contracts.dev.output_satisfied == true`
- Dev Stage 单测全绿
- state.json.current_stage == "review"

---

## 入口 Read 顺序（v7.3.10+P0-23 固定）

🔴 按以下顺序 Read，字节一致利于 prompt cache 命中。详见 [standards/prompt-cache.md](../standards/prompt-cache.md)。

```
Step 1: roles/rd.md（含架构师规范）, roles/qa.md        ← 角色层（L0 稳定）
Step 2: 无新模板                                        （checklist 在本 Stage spec 内）
Step 3: {Feature}/PRD.md, TC.md, TECH.md, REVIEW 基准 ← Feature 既有产物（L2）
        [条件] {Feature}/UI.md + preview/*.html         （若有 UI）
        docs/architecture/ARCHITECTURE.md（架构师视角）
Step 4: {Feature}/state.json                           ← 🔴 最后，动态入口（L3）
```

🔴 外部模型视角独立 dispatch 时，外部 session 内不经过 state.json 入口流，只读 diff + PRD/TECH/TC + standards（保持独立性）。
🔴 R3 约束：state.json 入口 Read 1 次 → 中段 0 读写 → 出口 Read 1 次 + Write 1 次。fix 修复循环豁免 ≤3 轮、每轮 ≤1 次 Write；全 Stage ≤ 8 次。

🌐 v7.3.10+P0-38：Stage 入口实例化时宣告 external 角色启用情况：
- `"external" in state.review_substeps_config.review_roles[].role`：`🌐 external 角色启用: model={state.external_cross_review.model}`
- 不在 review_roles[]：不输出此行（external 角色未启用）

---

## 🆕 Review Stage 入口实例化（v7.3.10+P0-48 引用统一规范）

> 🔴 **遵循 [standards/stage-instantiation.md](../standards/stage-instantiation.md) 通用流程**（4 步：read state hints → 决策 active_roles + execution + round_loop → 输出 5 行 Execution Plan → 默认通道 / 标准通道判定）。

**Review Stage 特定参数**：

- 候选 `active_roles`：Architect / QA / external（推荐：architect/qa 默认 active；external 视代码复杂度，推荐默认含 external——代码层最后 gate）
- `key_outputs`：CR finding / TC 验证结果 / external review report
- 子步骤：三视角并行审查（active_roles 互不依赖）
- `review_substeps_config` 特有字段：`parallel_mode: true`（三视角并行）
- 决策信号：Dev Stage 代码量 / 改动复杂度 / 跨模块影响

**特殊例外**：
- architect / qa 通常 execution=subagent（fresh context 防鼓掌效应）
- external 固定 execution=external-shell

---

### 主对话输出 Tier 应用（v7.3.10+P0-54 升级）

> 🔴 **遵循 [standards/output-tiers.md](../standards/output-tiers.md) 通用 Tier 1/2/3 规范 + 4 类反模式禁令**。

**Review Stage 特定 Tier 应用**：

- **Tier 1（永远输出）**：5 行 Execution Plan / 三视角 verdict（PASS / NEEDS_FIX）/ 🔴 阻塞 finding 摘要 / ⏸️ 用户处理 QUALITY_ISSUE 暂停点
- **Tier 2（命中折叠）**：🟡 建议 / 🟢 优化 finding 摘要（仅 round 2+ 有累积时）/ external review ADOPT/REJECT 摘要 / 修复循环重启时的 round 标记
- **Tier 3（不输出，走 state.json）**：review_substeps_config 详细字段 / 各角色 execution / files_read[] / generated_at / 三视角独立性校验细节

---

## Process Contract

### 必做动作

1. **三视角独立审查**（顺序无关，可并行可串行）
   - 每个视角独立读取自己的输入文件，产出独立报告
   - 每个视角不得引用其他视角的报告
   - 每个视角必须记录自己读过的文件清单（审计）

2. **架构师 Code Review**
   - 按 [roles/architect-cr.md](../roles/architect-cr.md)（v7.3.10+P0-87 抽出 · 角色契约见 [roles/architect.md](../roles/architect.md)）
   - 产出 `review-arch.md`
   - 维度：架构合理性 / 代码规范 / 性能 / 安全 / ARCHITECTURE.md 同步 / 日志完整性 P0-69 / 防御性路径 / Schema 同步

3. **QA 代码审查**
   - 按 [roles/qa-cr.md](../roles/qa-cr.md)（v7.3.10+P0-87 抽出 · 角色契约见 [roles/qa.md](../roles/qa.md)）
   - 产出 `review-qa.md`
   - 维度：TC 逐条覆盖 / TDD 规范 / Step 4.5 PRD AC 直接对账 P0-68 / 集成测试代码完整性 / 设计-代码一致性

4. **外部模型独立审查**（🟡 v7.3.10+P0-38 重构：external 升格为评审角色，受 review_substeps_config.review_roles[] 控制）
   - 🟡 **本 Stage external 评审现受 review_roles[] 控制**（v7.3.10+P0-38 改造）：`"external" in state.review_substeps_config.review_roles[].role` 时执行（推荐默认含 external——代码层最后 gate），不在 review_roles[] 时跳过本步（PMO 在 Stage 入口实例化时基于代码复杂度信号决定）。
   - 🔴 **默认推荐含 external**：与 v7.3.10+P0-27/P0-28 行为兼容；PMO 在 Review Stage 入口默认推荐 review_roles[] 含 external。仅当代码极简或用户主动调整时不含。
   - 🔴 **外部模型选择**（v7.3.10+P0-72 PMO 直接判定）：
     - PMO 在 Stage 入口实例化时**自报当前宿主**（基于自身运行环境，不读 state 旧值 / 不读项目目录标记），按当前宿主应用 E1 同源约束算 external 候选（详见 [standards/external-model.md § E2 PMO 直接判定](../standards/external-model.md)）
     - PMO 自报与 state 旧 host_main_model 不一致 → 按当前自报值更新 state + state.concerns 记录漂移 + 主对话显式声明切换
     ```
     ├── Claude Code 主对话 + Codex 可用 → 通过 Task/MCP 调 codex 子进程（codex-agents/reviewer.toml，fresh session）
     ├── Codex CLI 主对话 + Claude 可用 → shell 调 claude --print 子进程（claude-agents/invoke.md 范本，fresh session）
     │   └── 🔴 禁止："外部视角 = 主对话同模型自审"——必须是异质模型独立 spawn，不能在当前 session 内叙述
     ├── 两种宿主的独立性保证一致：fresh context + 独立 dispatch 文件 + 独立 generated_at
     └── 无可用外部模型（探测时所有候选不可用 / 调用失败）→ 进入降级分支（state.concerns 加 WARN + 跳过本步，依赖架构师 + QA 审查作为代码层 gate）
     ```
   - 按本文件 §外部模型代码 Review 任务规范
   - 产出 `review-external.md`（frontmatter：`perspective: external-{model}`（external-codex / external-claude），`executor: {对应调用机制描述}`）
   - 维度：逻辑正确性 / 安全漏洞 / 第三方依赖真实性 / 并发安全 / 代码质量

5. **汇合到 REVIEW.md**（PMO 职责）
   - 合并去重（同一文件同一位置问题合并）
   - 按严重程度排序（🔴 阻塞 > 🟡 建议修复 > 🟢 优化）

### 过程硬规则

- 🔴 **角色规范必读且 cite**：每视角开始前必读对应 §任务规范 + `roles/*.md`，产出前 cite 要点
- 🔴 **三视角独立性（结构约束）**：
  - 每份报告必须有独立 `generated_at` 时间戳
  - 每份报告必须列出"本视角读过的文件"清单
  - 三份报告互不引用（`grep -r "review-arch" review-external.md` 应为空，反之亦然）
- 🔴 **外部模型独立性硬约束**：外部视角严禁读架构师 / QA 的 review 报告
- 🔴 **完整性**：每个视角按各自规范完整执行，不能因为另一个视角已通过就简化
- 🔴 **不修复**：Review 只审不改，发现问题返回 PMO 安排 RD 修复
- 🔴 **循环控制**：修复-重跑循环 ≤3 轮
- 🔴 **Stage 完成前 git 干净** → 统一遵循 [rules/gate-checks.md § Stage 完成前 git 干净](../rules/gate-checks.md#-stage-完成前-git-干净v739-硬规则p0-集中化)（本 Stage commit message：`F{编号}: Review Stage - fix {简述}`；每轮修复独立 commit；auto_commit 为**数组**字段，多轮 QUALITY_ISSUE 修复 append）

### 多视角独立性（产物结构保证）

这是本 Stage 契约的核心。Output Contract 要求三份独立报告 + 不互相引用 + 时间戳独立——AI 为满足这些产物条件，**结构上**必然做三次独立审查。

---

## Output Contract

### 必须产出的文件

| 文件路径 | 格式 | 必需字段 |
|---------|------|---------|
| `{Feature}/review-arch.md` | Markdown + YAML frontmatter | `perspective: architect`, `generated_at`, `files_read[]`, `findings[]`（含 severity/file/line/message/suggestion） |
| `{Feature}/review-qa.md` | Markdown + YAML frontmatter | `perspective: qa`, `generated_at`, `files_read[]`, `tc_coverage_report`, `findings[]` |
| `{Feature}/review-external.md` | Markdown + YAML frontmatter | `perspective: external-{model}`（external-codex / external-claude）, `generated_at`, `files_read[]`, `findings[]` |
| `{Feature}/REVIEW.md` | Markdown | 汇总三份 + 合并去重问题清单 + 修复记录 |

### 机器可校验条件

- [ ] 三份 review 文件都存在
- [ ] 每份 frontmatter 可 YAML 解析且 `perspective` 字段唯一
- [ ] 三份 `generated_at` 时间戳互不相同
- [ ] 三份互不引用（`grep -l "review-{other}"` 互查为空）
- [ ] 每份都有 `findings[]`（空列表合法，但需显式 `findings: []`）
- [ ] 架构师视角必须有 ≥3 条 findings，若确实无则显式说明（例：`{severity: info, message: "整体高质量，未发现问题"}`）

### Done 判据

- 三份报告存在且通过结构/独立性校验
- 合并后无 🔴 阻塞问题（或有但已修复）
- REVIEW.md 落盘汇总
- `state.json.stage_contracts.review.output_satisfied = true`

### 返回状态

| 状态 | 条件 | 后续 |
|------|------|------|
| ✅ DONE | 三视角均无阻塞 | 进入 Test Stage |
| ⚠️ DONE_WITH_CONCERNS | 有 🟡 建议但无 🔴 阻塞 | PMO 评估，非阻塞则继续 |
| 🔁 NEEDS_FIX | 任一视角有 🔴 阻塞 | RD 修复 → 重跑相关视角（≤3 轮） |
| ❌ FAILED | Codex 不可用且降级失败 | PMO ⏸️ 用户选择 |

### 修复循环规则

```
Review Stage NEEDS_FIX 时：

1. PMO 合并三份 review 的问题清单（去重）
2. 派发 RD 修复（PMO dispatch 或主对话）
3. 修复范围 ≤2 文件且无逻辑变更 → 只重跑发现问题的视角
4. 修复涉及逻辑变更 → 全部三个视角重跑
5. 🔴 最多 3 轮，超出 → ⏸️ 用户决策（v7.3.10+P0-75 必含「📚 决策参考」绝对路径段，详见 STATUS-LINE.md § 决策点参考文档绝对路径硬规则）
   📚 必列：REVIEW.md / external-cross-review/review-external-{model}.md（如启用） / 涉及代码文件 / 涉及测试文件 全部绝对路径

Codex 独立性保障：
├── 重跑时 Codex 仍不看架构师 / QA 报告
├── Codex 的问题由 RD + 架构师评估后决定是否采纳
└── 第三方依赖真实性问题严肃对待（Codex 说包不存在 → 必须核实）
```

---

## AI Plan 模式指引

📎 Execution Plan 3 行格式 → [SKILL.md](../SKILL.md#-ai-plan-模式规范v73-新增)。

本 Stage 默认 `hybrid`（架构师主对话 + QA / 外部模型并行 Subagent）。

三路分工理由：
- 架构师视角需项目全局上下文（ARCHITECTURE 演化、历史决策），主对话保留累积
- QA / 外部模型视角需独立性，Subagent / 异质 CLI 天然 fresh context
- 架构师主对话时加「怀疑者视角」prompt 防鼓掌（见下方）

🔴 **v7.3.10+P0-40 模型默认值**：
- **架构师 Code Review**：默认 `opus`（深度架构判断不可降级；含 Review Stage + Bug 流程必经）
  - 主对话模式：继承用户会话模型（如非 Opus，建议关键 Feature 切换；架构 review 是质量最后 gate）
  - Subagent 模式：dispatch 时显式 `model: opus`
- **QA Code Review**：默认 `sonnet`（执行型校验，TC 逐条覆盖判断 Sonnet 够用）
  - Subagent 模式：dispatch 时显式 `model: sonnet`
- **external Code Review**：异质模型（codex / claude-cli），与 Claude 模型选择正交

典型偏离：
- 小改动 / 主对话 context 足够 → 三视角全 `main-conversation`（需清洗 context 防创建者偏见）
- 大改动 / 要求最强独立性 → 三视角全 `subagent`（Dispatch 文件 Batch 字段同批次）

🔴 不论哪种 approach，Output Contract 的独立性校验（三份产物独立 generated_at / files_read / 不互相引用）都必须满足。

**Expected duration baseline（v7.3.3）**：hybrid（默认）10-20 min（三路并行，墙钟 = max(架构师, QA, Codex)）；全 subagent 约 15-25 min（冷启动税）；全主对话 8-15 min（小改动）。如发生 NEEDS_FIX 重跑，每轮 +5-10 min。

### 架构师主对话 Review 防鼓掌机制（approach 含 main-conversation 时必做）

- 开始前显式声明"进入架构师审查模式，采用怀疑者视角"
- 不读 RD 自查报告（只看代码 diff + TECH.md + ARCHITECTURE.md）
- 强制产出 ≥3 条批评；若确实无，显式说明"代码高质量，未发现"+ 审查过的维度清单

---

## 架构师 CR 任务规范

> 🔴 **本节于 v7.3.10+P0-87 抽出**到 [roles/architect-cr.md](../roles/architect-cr.md)（~261 行 · 6 段：角色定位 / Review 维度（含日志完整性 P0-69 + 防御性路径 + Schema 同步）/ 执行流程 + 约束 / 架构文档更新规则 / 输出模板 / 上游问题清单）。Review Stage 架构师 Code Review 任务请直接读该文件。
>
> 🔗 **角色契约**：[roles/architect.md](../roles/architect.md)（4 段最小骨架 · 跨 stage 通用）。
>
> 历史源流：v7.3.10+P0-19-B 前为 `agents/arch-code-review.md` → P0-19-B 合并入本文件 → v7.3.10+P0-87 抽出到 `roles/architect-cr.md` 子文件（落"role 管角色契约 + 评审视角"风格 C 设计）。

---

## QA CR 任务规范

> 🔴 **本节于 v7.3.10+P0-87 抽出**到 [roles/qa-cr.md](../roles/qa-cr.md)（~204 行 · 5 段：角色定位 / 执行流程（含 TDD 检查 + Step 4.5 PRD AC 直接对账 P0-68 + 用户行为边界 + 设计-代码一致性）/ 执行约束 / QA Review 输出模板 / 结果处理）。Review Stage QA Code Review 任务请直接读该文件。
>
> 🔗 **角色契约**：[roles/qa.md](../roles/qa.md)（QA 测试策略 + 验证职责）。
>
> 历史源流：v7.3.10+P0-19-B 前为 `agents/qa-code-review.md` → P0-19-B 合并入本文件 → v7.3.10+P0-87 抽出到 `roles/qa-cr.md` 子文件（与架构师 CR 任务规范同步迁出 · 落"role 管角色契约 + 评审视角"风格 C 设计）。

---

## 外部模型代码 Review 任务规范

> 外部视角通过对应外部模型 CLI 独立 spawn fresh session 执行（按 state.external_cross_review.model 选择 codex CLI 或 claude CLI；详见 §Process Contract §4 外部模型独立审查）。本节为外部视角的 prompt 模板（适用于所有外部模型实例）。

### 输入（PMO 在 dispatch 中提供）

```
├── {Feature}/PRD.md
├── {Feature}/TECH.md
├── {Feature}/TC.md
├── Dev Stage 代码 diff
├── {SKILL_ROOT}/standards/common.md + backend.md/frontend.md
└── 🔴 严禁读：review-arch.md / review-qa.md（独立性硬约束）
```

### 审查维度

```
├── 逻辑正确性（边界 / 异常路径 / 错误处理）
├── 安全漏洞（注入 / XSS / 越权 / 敏感数据）
├── 第三方依赖真实性（🔴 异质外部模型跨模型优势点）
│   └── 包名是否真实存在、版本是否有已知 CVE
├── 并发安全（TOCTOU / 死锁 / 幂等性）
└── 代码质量（可读性 / 可维护性 / 冗余）
```

### 输出

```
review-external.md，frontmatter：
---
perspective: external-{model}        # external-codex | external-claude
executor: codex-cli-subprocess | codex-cli-subagent | claude-cli-subprocess
generated_at: ISO8601
model: codex-{version} | claude-sonnet-{version}    # 实际使用的外部模型版本
files_read:
  - ...
findings:
  - severity: high|medium|low|info
    file: ...
    line: ...
    message: ...
    suggestion: ...
---
```

---

## 执行报告模板

```
📋 Review Stage 执行报告（F{编号}-{功能名}）
============================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / NEEDS_FIX / FAILED}
├── 执行方式：架构师{主对话/Subagent} + QA {主对话/Subagent} + 外部模型{model}（{对应 CLI spawn 方式}）
├── 合并问题数：🔴 {x} / 🟡 {y} / 🟢 {z}
└── 落盘：{Feature}/REVIEW.md

## 三视角产出
| 视角 | 文件 | generated_at | files_read | findings |
|------|------|-------------|------------|----------|
| 架构师 | review-arch.md | ... | 5 | 🔴0 🟡2 🟢1 |
| QA | review-qa.md | ... | 4 | 🔴0 🟡1 🟢0 |
| 外部（{model}）| review-external.md | ... | 3 | 🔴0 🟡0 🟢2 |

## Output Contract 校验
├── 三份报告存在：✅
├── frontmatter 可解析：✅
├── generated_at 互不相同：✅
├── 报告互不引用：✅（grep 校验）
└── 架构师批评 ≥3 条：✅（或显式说明）

## 修复记录（如有）
| 轮次 | 修复内容 | 重跑范围 | 结果 |
|------|----------|----------|------|

## ARCHITECTURE.md 更新
{已更新 / 无需更新 / 待更新}
```
