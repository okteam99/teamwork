# Blueprint Stage：技术规格（QA 写 TC + TC 技术评审 + RD 写技术方案 + 架构师评审）

> 用户确认 PRD 后（Designer 完成后，如有 UI）进入本 Stage。产出"怎么测 + 怎么做"的完整蓝图，Dev Stage 按此执行。
> 🔴 契约优先：本文件规范 Input / Process / Output 三契约。执行方式由 AI 在 Plan 模式自主规划。

---

## 本 Stage 职责

产出经过多视角评审的 TC + TECH，为 Dev Stage 提供可直接实施的蓝图。TC 与 PRD AC 强绑定（test_refs 反查），TECH 与 ARCHITECTURE 对齐。4 步内部闭环（QA TC → TC 评审 → RD TECH → 架构师评审）为强制项；🟡 Codex 交叉评审（v7.3.9+P0-13 改为 opt-in，默认 OFF）仅当 `state.codex_cross_review.enabled==true` 时追加执行，用于捕捉同模型多角色评审的注意力盲点。

---

## Input Contract

### 必读文件（按顺序）

```
├── {SKILL_ROOT}/agents/README.md
├── {SKILL_ROOT}/stages/blueprint-stage.md（本文件）
├── {SKILL_ROOT}/roles/qa.md（含 TC 技术评审规范）
├── {SKILL_ROOT}/roles/rd.md（含架构师方案评审规范）
├── {SKILL_ROOT}/templates/tc.md
├── {SKILL_ROOT}/templates/tech.md（如有）
├── {SKILL_ROOT}/standards/common.md
├── {Feature}/PRD.md（已确认）
└── {Feature}/UI.md（如有）

可选：
├── docs/architecture/ARCHITECTURE.md
├── docs/architecture/database-schema.md
└── docs/KNOWLEDGE.md

条件必读（v7.3.9+P0-13 新增）：
└── {SKILL_ROOT}/templates/codex-cross-review.md
    🟡 仅当 state.codex_cross_review.enabled == true 时必读（Blueprint Stage Codex 开关）
    🟢 关闭时跳过 Step 5 + 相关校验，节省启动 token
```

### Key Context（逐项判断，无则 `-`）

- 历史决策锚点：技术栈选型、架构模式、既定约定
- 本轮聚焦点：重派或修订场景必填
- 跨 Feature 约束：与并行 Feature 的接口/数据模型兼容
- 已识别风险：KNOWLEDGE.md 中相关陷阱、历史 Bug
- 降级授权：例如 Codex 不可用时架构师评审继续
- 优先级 / 容忍度

### 前置依赖

- `{Feature}/PRD.md` 存在且 `state.json.stage_contracts.plan.output_satisfied == true`
- 若有 UI：`{Feature}/UI.md` + `preview/*.html` 已完成且用户确认
- state.json.current_stage == "blueprint"

---

## 入口 Read 顺序（v7.3.10+P0-23 固定）

🔴 按以下顺序 Read，字节一致利于 prompt cache 命中。详见 [standards/prompt-cache.md](../standards/prompt-cache.md)。

```
Step 1: roles/qa.md, roles/rd.md                       ← 角色层（L0 稳定）
Step 2: templates/tc.md, templates/tech.md              ← 模板层（L0 稳定）
        [条件] templates/codex-cross-review.md          （仅 codex_cross_review.enabled=true）
Step 3: {Feature}/PRD.md                               ← Feature 既有产物（L2）
        [条件] {Feature}/UI.md                          （若 UI Design Stage 已跑）
Step 4: {Feature}/state.json                           ← 🔴 最后，动态入口（L3）
```

🔴 R3 约束：state.json 入口 Read 1 次 → 中段 0 读写 → 出口 Read 1 次 + Write 1 次。TC/TECH 内部评审修复循环豁免每轮 ≤1 次 Write，总轮次 ≤3；全 Stage ≤ 8 次。

---

## Process Contract

### 必做动作

1. **QA 编写 Test Plan + TC**（4 步闭环 1/4）
   - 按 PRD AC 逐条写 BDD/Gherkin 用例
   - TC.md frontmatter 填 `tests[]`，每条 test 的 `covers_ac[]` 反查 PRD AC id
   - 产出：TEST-PLAN.md + TC.md

2. **TC 技术评审**（4 步闭环 2/4）
   - 视角：RD + Designer（如有 UI）+ PMO
   - 按 `roles/qa.md`「TC 技术评审规范」
   - 有问题 → QA 修订 → 重新评审（≤2 轮）
   - 产出：TC-REVIEW.md

3. **RD 编写技术方案**（4 步闭环 3/4）
   - 按 `roles/rd.md` + `templates/tech.md`
   - 必须覆盖：文件清单、改动要点、数据模型、接口定义、测试策略
   - 产出：TECH.md

4. **架构师方案评审**（4 步闭环 4/4）
   - 按 `roles/rd.md`「架构师方案评审规范」
   - 有严重问题 → RD 修改 → 重新评审（≤3 轮）
   - 产出：TECH-REVIEW.md 或评审结果写入 TECH.md 尾部
   - **4.1 ADR 抽取判断**（v7.3.10+P0-21 新增）：评审通过后，架构师对本 Feature 产生的每个技术决策应用「3 问触发器」：
     1. 这个决策会影响 ≥ 1 个未来 Feature 吗？
     2. 反悔成本很高吗（需要大规模改动）？
     3. 存在多个合理方案，选哪个不是显然的吗？
     - **三问全 yes** → 抽取为独立 ADR（流程见下方「ADR 抽取流程」）
     - **任一 no** → 决策留在 TECH.md 即可，不产 ADR
     - 🔴 判断本身必须在 TECH-REVIEW.md 留痕（即使 no ADR，也要写明"ADR 判断：否（理由）"），不判断 = 流程偏离
     - 📎 典型 ADR 触发场景：选型决策（DB / 框架 / 消息队列）、通用模式（鉴权方案 / 缓存策略）、跨模块契约（API 版本规则 / 错误码体系）；典型 no-ADR 场景：单 Feature 内部实现细节、显然的 best practice、已有 ADR 覆盖的复用

5. 🟡 **Codex 交叉评审**（外部视角，v7.3.9+P0-13 改为 opt-in，默认 OFF）
   - **执行条件**：`state.codex_cross_review.enabled == true`
     - **开启时**必做；**关闭时**整个 Step 5 跳过（不产出 blueprint-codex-review.md，TC-REVIEW/TECH-REVIEW 尾部不写「Codex 交叉评审整合」section，或显式声明"Codex 已关闭"）
   - **前置（开启时适用）**：Step 1-4 全部 DONE（TC / TC-REVIEW / TECH / TECH-REVIEW 均已 output_satisfied）
   - 按 `templates/codex-cross-review.md` 调用 `codex-agents/blueprint-reviewer.toml`（TC+TECH 变体，C1-C6 checklist）
   - dispatch prompt 不得暗示结论；sandbox_mode = read-only
   - 产出：`{Feature}/blueprint-codex-review.md`（YAML frontmatter：perspective=external-codex、target=blueprint、files_read、findings[]）
   - **整合**：PMO 对每条 finding 分类 `ADOPT / REJECT / DEFER` 写入 TC-REVIEW.md（TC 相关）或 TECH-REVIEW.md（TECH 相关）尾部的「Codex 交叉评审整合」section
   - 🔴 严禁"全盘接受"或"全盘忽略"——逐条推理
   - ADOPT 项若涉及 TC 或 TECH 实质改动 → 触发相应文件小幅修订（不重走 4 步闭环，仅补丁式更新 + 记录 diff）
   - 默认关闭理由：Blueprint 产物为技术设计文档，4 步内部闭环已覆盖质量下限；Codex 主要价值在 Review Stage 的代码审查。用户可在 PMO 初步分析时按风险/规模手工开启。

6. **ADR 抽取流程**（v7.3.10+P0-21 新增；仅当 Step 4.1 判断为"产 ADR"时执行）
   - **前置**：TECH-REVIEW.md 已记录"ADR 判断：是"+ 决策清单（每条决策一个后续 ADR）
   - **架构师职责**：
     1. 为每条决策分配 ADR-ID（查 `{子项目}/docs/adr/INDEX.md` 现有编号，取下一个）
     2. 按 `templates/adr.md` 格式在 `{子项目}/docs/adr/NNNN-{slug}.md` 创建 ADR 文件
     3. 填充 frontmatter（id/title/status=proposed/date/tags/triggered_by=本 Feature 目录名）+ 全部正文段（背景 / 驱动因素 / 备选项 ≥ 2 / 决策 / 后果 / 相关 / 修订历史）
     4. 更新 `docs/adr/INDEX.md`：在「提案中」段追加本条目（首次创建 ADR 时，如 INDEX.md 不存在 → 按 `templates/adr-index.md` 创建）
   - **PMO 流程整合**：
     1. 将新 ADR 列入阶段摘要的产出清单
     2. ⏸️ 等用户在 Blueprint Stage 完成确认时一并确认 ADR（用户同意 → 架构师将 status 从 proposed 改为 accepted + 同步 INDEX.md 移到「活跃决策」段）
     3. 若用户对 ADR 有异议 → 架构师修订 → 重新确认（不走 ≤3 轮修复限制，ADR 可以多轮讨论）
   - **产出**：
     - 新 / 修订的 ADR 文件（1 个或多个）
     - 更新的 INDEX.md
   - **体量控制**：单个 ADR 50-150 行；若超出说明备选项未收敛，架构师应重新精简而不是放任膨胀
   - **🔴 与 TECH.md 的去重**：决策的"理由 / 备选项 / 后果"迁移到 ADR 后，TECH.md 中只需引用 ADR-ID（一句话+链接），不再复述

### 过程硬规则

- 🔴 **角色规范必读且 cite**：QA → 必读 `roles/qa.md` 并 cite 要点；RD → 必读 `roles/rd.md` 并 cite；架构师视角同上
- 🔴 **TC 必须 BDD/Gherkin 格式**：不接受自由格式
- 🔴 **AC↔test 强绑定**：TC.md 的 `tests[].covers_ac` 必须反查 PRD 所有 AC（每条 AC 至少 1 个测试）
- 🔴 **TC 技术评审不可跳过**
- 🔴 **架构师方案评审不可跳过**（无论方案多简单）
- 🔴 **ADR 抽取判断不可跳过**（v7.3.10+P0-21）：架构师必须对本 Feature 技术决策应用 3 问触发器，判断结论（产 / 不产 ADR + 理由）必须写入 TECH-REVIEW.md。跳过判断 = 流程偏离
- 🔴 **ADR 格式合规**（触发抽取时）：严格按 `templates/adr.md` 格式；备选项 ≥ 2；每次新增 / 状态变更必须同步更新 `docs/adr/INDEX.md`（同样按 `templates/adr-index.md` 格式）
- 🟡 **Codex 交叉评审（v7.3.9+P0-13 改为 opt-in）**：`state.codex_cross_review.enabled==true` 时必做（除 Codex CLI 不可用触发降级），且必须在 4 步内部闭环 DONE 后执行；==false 时整个 Step 5 跳过（默认行为）
- 🟡 **Codex 独立性（开启时适用）**：blueprint-reviewer dispatch prompt 不得暗示结论；产出 `files_read` 不得包含 TC-REVIEW.md / TECH-REVIEW.md / pmo-internal-review.md（违反 = 重 dispatch）
- 🟡 **Codex 降级处理（开启时适用）**：按 `agents/README.md §三` 三选一（修复 / 🟢 AI 自主规划等效独立审查 / skip+记入 concerns）
- 🟡 **防外包思考（Codex 开启时适用）**：PMO 收到 Codex 产出后逐条分类（ADOPT/REJECT/DEFER）；全盘同意或全盘否定视为可疑信号（按 codex-cross-review.md §六处理）
- 🔴 **TECH.md 必含实现计划**：文件清单 + 改动要点 + 测试策略
- 🔴 **内部评审修复循环**：每轮评审修复 ≤3 轮，超出则返回 DONE_WITH_CONCERNS
- 🔴 **Stage 完成前 git 干净** → 统一遵循 [rules/gate-checks.md § Stage 完成前 git 干净](../rules/gate-checks.md#-stage-完成前-git-干净v739-硬规则p0-集中化)（本 Stage commit message：`F{编号}: Blueprint Stage - {简述}`；TC + TECH 是后续 Dev Stage 的执行蓝图，必须 commit 以锚定）

### 多视角独立性要求

- TC 技术评审：RD / Designer / PMO 分别输出评审意见（不互相引用）
- 架构师评审：独立于 RD 编写方案时的思路（评审者应以"第三方审视"姿态）
- 🟡 Codex 交叉评审独立性（开启时适用）：通过产物结构强制独立——blueprint-codex-review.md frontmatter 声明 `perspective: external-codex` + `files_read`，且 `grep -E "TC-REVIEW\|TECH-REVIEW\|pmo-internal" blueprint-codex-review.md` 应为空

---

## Output Contract

### 必须产出的文件

| 文件路径 | 条件 | 格式 | 必需字段 |
|---------|------|------|---------|
| `{Feature}/TEST-PLAN.md` | 🔴 必需 | Markdown | 测试范围、风险点、测试数据策略 |
| `{Feature}/TC.md` | 🔴 必需 | Markdown + YAML frontmatter | `feature_id`, `tests[]`（每条 id/file/function/covers_ac/level） |
| `{Feature}/TC-REVIEW.md` | 🔴 必需 | Markdown | 3 视角评审意见（RD/Designer/PMO）+ 问题清单 + 修复记录；Codex 开启时追加尾部「Codex 交叉评审整合（TC 部分）」section，关闭时写"Codex 已关闭" |
| `{Feature}/TECH.md` | 🔴 必需 | Markdown | 文件清单、改动要点、数据模型、接口定义、测试策略 |
| `{Feature}/TECH-REVIEW.md`（或 TECH.md 尾部）| 🔴 必需 | Markdown | 架构师评审维度（架构/扩展性/性能/安全/一致性）+ 修复记录；Codex 开启时追加尾部「Codex 交叉评审整合（TECH 部分）」section |
| `{Feature}/blueprint-codex-review.md` | 🟡 仅 Codex 开启时必需 | Markdown + YAML frontmatter | `perspective: external-codex`, `target: blueprint`, `generated_at`, `files_read[]`, `findings[]`（C1-C6 checklist 分类）, `findings_summary` |
| `{子项目}/docs/adr/NNNN-{slug}.md` | 🟡 仅 Step 4.1「3 问触发器」全 yes 时必需 | Markdown + YAML frontmatter | `id`, `title`, `status`(proposed→accepted), `date`, `tags[]`, `triggered_by`, 备选项 ≥ 2，完整 Consequences 段（4 子段），体量 50-150 行 |
| `{子项目}/docs/adr/INDEX.md` | 🟡 首次产 ADR 时创建 / 每次 ADR 变更时更新 | Markdown | 活跃决策 / 提案中 / 已废弃三段 + 按主题索引 + 维护约定；严格按 `templates/adr-index.md` 格式 |

> 🟡 Codex 条件说明（v7.3.9+P0-13）：`state.codex_cross_review.enabled == true` 时 blueprint-codex-review.md 为必需产物；== false 时不产出，TC-REVIEW / TECH-REVIEW 尾部声明"Codex 已关闭（state.codex_cross_review.enabled=false）"即可。

> 🟡 ADR 条件说明（v7.3.10+P0-21）：ADR 为 opt-in 产物，由架构师 Step 4.1 的「3 问触发器」决定是否产出。不触发时 ADR 文件不产，TECH-REVIEW.md 内记录"ADR 判断：否 + 理由"即可；触发时每条决策一个 ADR，且 INDEX.md 必同步。

### 机器可校验条件

- [ ] TC.md frontmatter 可 YAML 解析（`yq '.tests[].id' TC.md` 成功）
- [ ] 每条 PRD AC 在 TC.md 中至少有 1 个 test 的 `covers_ac` 包含它（`python3 {SKILL_ROOT}/templates/verify-ac.py {Feature}` exit 0）
- [ ] TC 用例数 ≥ PRD AC 数
- [ ] TECH.md 含"文件清单"章节且至少列出 1 个文件
- [ ] 无 TBD / TODO / 占位符
- 🟡 以下校验仅当 `state.codex_cross_review.enabled == true` 时生效：
  - [ ] blueprint-codex-review.md frontmatter 可解析且 `perspective == "external-codex"` + `target == "blueprint"`
  - [ ] blueprint-codex-review.md 的 `files_read` 不包含 TC-REVIEW / TECH-REVIEW / pmo-internal-review（`grep -E "TC-REVIEW\|TECH-REVIEW\|pmo-internal" blueprint-codex-review.md` 为空）
  - [ ] TC-REVIEW.md + TECH-REVIEW.md 尾部「Codex 交叉评审整合」section 对每条 finding 均有 ADOPT/REJECT/DEFER 标记 + 理由
  - [ ] Codex 降级场景：若 Codex 未执行，state.json.concerns 或 TECH-REVIEW.md 需显式记录 skip_reason
- 🟢 若 `state.codex_cross_review.enabled == false`：
  - [ ] TC-REVIEW.md / TECH-REVIEW.md 任一尾部显式声明"Codex 已关闭（state.codex_cross_review.enabled=false，decided_at={ts}）"，不产出 blueprint-codex-review.md
- 🟡 以下校验仅当 Step 4.1「3 问触发器」产出 ADR 时生效（v7.3.10+P0-21）：
  - [ ] 每个新 ADR 文件 frontmatter 可解析且 `id` / `title` / `status` / `date` / `tags` 全非空；`status ∈ {proposed, accepted}`
  - [ ] ADR 正文含「备选项」段且备选项 ≥ 2（单方案走 TECH.md，不应走 ADR）
  - [ ] ADR 体量 ≥ 50 行 且 ≤ 150 行（超出/不足 = 备选项未收敛或过度膨胀）
  - [ ] `docs/adr/INDEX.md` 存在且本次新增 ADR 已列入相应段（proposed/accepted）
  - [ ] ADR 文件名格式 `NNNN-{slug}.md`（NNNN 四位数字连续编号，与 INDEX.md 现有 ID 不冲突不复用）
- 🟢 若未触发 ADR 抽取：TECH-REVIEW.md 须显式记录"ADR 判断：否 + 理由（3 问中哪条为 no）"

### Done 判据

- 所有产出文件存在且通过格式校验
- AC↔test 覆盖校验通过
- TC 技术评审 + 架构师评审完成（无 🔴 阻塞问题）
- 🟡 Codex 开启时额外判据：Codex 交叉评审完成（skip 需显式 concerns）+ findings 全部分类完毕（ADOPT/REJECT/DEFER）+ ADOPT 项已并入 TC / TECH；关闭时跳过本判据
- 🟡 ADR 触发时额外判据（v7.3.10+P0-21）：所有新 ADR 用户确认通过（status=accepted）+ INDEX.md 同步 + TECH.md 去重（决策理由迁出，仅留 ADR-ID 引用）
- `state.json.stage_contracts.blueprint.output_satisfied = true`

### 返回状态

| 状态 | 条件 | 后续 |
|------|------|------|
| ✅ DONE | 产出完整 + 评审通过 + 无阻塞 | PMO ⏸️ 用户确认技术方案 |
| ⚠️ DONE_WITH_CONCERNS | 有非阻塞建议或 PRD 疑问 | PMO ⏸️ 用户确认 |
| 💥 FAILED | 需求不清晰 / 架构冲突无法解决 | 返回错误 + 部分产出 |

---

## AI Plan 模式指引

📎 Execution Plan 4 行格式（含 Estimated）→ [SKILL.md「AI Plan 模式规范」](../SKILL.md#-ai-plan-模式规范v73-新增)。默认 approach → [agents/README.md §一 执行方式与模型](../agents/README.md)。

本 Stage 默认 `main-conversation`（4 步内部闭环：QA TC → TC 评审 → RD TECH → 架构师评审，全程多视角 prompt 切换）；🟡 Codex 交叉评审（开启时）走 subagent-codex 外部视角，默认 OFF（v7.3.9+P0-13）。典型偏离：需求极清晰 → `subagent` 一次闭环；或 `hybrid`（TC/TECH 主对话起草 + 架构师评审 Subagent 独立审）。Codex Step 5 固定 subagent-codex，不受闭环 approach 选择影响。

**Expected duration baseline（v7.3.3 / P0-13 修订）**：25-45 min（主对话 4 步闭环）；🟡 Codex 开启时额外 +5-10 min（交叉评审 + 整合），关闭时 0 额外开销。Subagent 一次闭环 30-60 min（冷启动）+ 可选 5-10 min Codex。AI 在 Execution Plan 的 `Estimated` 字段按本 Feature 规模（AC 数、TECH 预期文件数）+ Codex 开关状态校准。

---

## 执行报告模板

```
📋 Blueprint Stage 执行报告（F{编号}-{功能名}）
================================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / FAILED}
├── 执行方式：{主对话 / Subagent / 混合}
├── TC：{N} 条 BDD 用例，覆盖 AC {M}/{总 AC}
├── TC 技术评审：{通过 / 有建议已纳入 / 修复 N 轮}
├── TECH.md：{完成 / 有 concerns}
├── 架构师评审：{通过 / 有建议已纳入 / 修复 N 轮}
└── Codex 交叉评审：{ENABLED → DONE / DONE_WITH_CONCERNS / SKIPPED / FAILED | DISABLED（state.codex_cross_review.enabled=false）}（ADOPT: N / REJECT: M / DEFER: K）

## Codex 交叉评审摘要（🟡 仅当 state.codex_cross_review.enabled=true 时输出本节）
├── Codex 状态：{DONE / SKIPPED + 原因 / DISABLED}
├── Findings 总数：{N}（C1:{?} C2:{?} C3:{?} C4:{?} C5:{?} C6:{?}）
├── ADOPT: {a} 条（TC 补丁: {?}，TECH 补丁: {?}）
├── REJECT: {b} 条（理由见 TC-REVIEW.md / TECH-REVIEW.md 尾部）
└── DEFER: {c} 条（写入 state.json.concerns 或下一 Stage Key Context）

## 产出文件
├── 📁 TEST-PLAN.md
├── 📁 TC.md（frontmatter 可解析，tests[] 数量：{N}）
├── 📁 TC-REVIEW.md（Codex 开启时含整合章 TC 部分）
├── 📁 TECH.md
├── 📁 TECH-REVIEW.md（或 TECH.md 尾部；Codex 开启时含整合章 TECH 部分）
└── 🟡 blueprint-codex-review.md（外部视角，仅 Codex 开启时产出）

## Output Contract 校验
├── TC YAML：✅ 可解析
├── AC→test 覆盖：{PRD AC 数} → {覆盖数} ✅/❌
├── TC 用例数 ≥ AC 数：✅
├── TECH 含文件清单：✅
├── Codex 校验：{ENABLED → 独立性 grep ✅ + findings 分类 ✅ | DISABLED → TC/TECH-REVIEW 尾部声明已关闭 ✅}
└── 无 TBD：✅

## Concerns（如有）
{非阻塞性问题清单}
```
