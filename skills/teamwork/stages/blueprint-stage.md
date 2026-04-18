# Blueprint Stage：技术规格（QA 写 TC + TC 技术评审 + RD 写技术方案 + 架构师评审）

> 用户确认 PRD 后（Designer 完成后，如有 UI）进入本 Stage。产出"怎么测 + 怎么做"的完整蓝图，Dev Stage 按此执行。
> 🔴 契约优先：本文件规范 Input / Process / Output 三契约。执行方式由 AI 在 Plan 模式自主规划。

---

## 本 Stage 职责

产出经过多视角评审的 TC + TECH，为 Dev Stage 提供可直接实施的蓝图。TC 与 PRD AC 强绑定（test_refs 反查），TECH 与 ARCHITECTURE 对齐。

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

### 过程硬规则

- 🔴 **角色规范必读且 cite**：QA → 必读 `roles/qa.md` 并 cite 要点；RD → 必读 `roles/rd.md` 并 cite；架构师视角同上
- 🔴 **TC 必须 BDD/Gherkin 格式**：不接受自由格式
- 🔴 **AC↔test 强绑定**：TC.md 的 `tests[].covers_ac` 必须反查 PRD 所有 AC（每条 AC 至少 1 个测试）
- 🔴 **TC 技术评审不可跳过**
- 🔴 **架构师方案评审不可跳过**（无论方案多简单）
- 🔴 **TECH.md 必含实现计划**：文件清单 + 改动要点 + 测试策略
- 🔴 **内部评审修复循环**：每轮评审修复 ≤3 轮，超出则返回 DONE_WITH_CONCERNS

### 多视角独立性要求

- TC 技术评审：RD / Designer / PMO 分别输出评审意见（不互相引用）
- 架构师评审：独立于 RD 编写方案时的思路（评审者应以"第三方审视"姿态）

---

## Output Contract

### 必须产出的文件

| 文件路径 | 格式 | 必需字段 |
|---------|------|---------|
| `{Feature}/TEST-PLAN.md` | Markdown | 测试范围、风险点、测试数据策略 |
| `{Feature}/TC.md` | Markdown + YAML frontmatter | `feature_id`, `tests[]`（每条 id/file/function/covers_ac/level） |
| `{Feature}/TC-REVIEW.md` | Markdown | 3 视角评审意见（RD/Designer/PMO）+ 问题清单 + 修复记录 |
| `{Feature}/TECH.md` | Markdown | 文件清单、改动要点、数据模型、接口定义、测试策略 |
| `{Feature}/TECH-REVIEW.md`（或 TECH.md 尾部）| Markdown | 架构师评审维度（架构/扩展性/性能/安全/一致性）+ 修复记录 |

### 机器可校验条件

- [ ] TC.md frontmatter 可 YAML 解析（`yq '.tests[].id' TC.md` 成功）
- [ ] 每条 PRD AC 在 TC.md 中至少有 1 个 test 的 `covers_ac` 包含它（`scripts/verify-ac-coverage.sh` 通过）
- [ ] TC 用例数 ≥ PRD AC 数
- [ ] TECH.md 含"文件清单"章节且至少列出 1 个文件
- [ ] 无 TBD / TODO / 占位符

### Done 判据

- 所有产出文件存在且通过格式校验
- AC↔test 覆盖校验通过
- TC 技术评审 + 架构师评审均完成（且无 🔴 阻塞问题）
- `state.json.stage_contracts.blueprint.output_satisfied = true`

### 返回状态

| 状态 | 条件 | 后续 |
|------|------|------|
| ✅ DONE | 产出完整 + 评审通过 + 无阻塞 | PMO ⏸️ 用户确认技术方案 |
| ⚠️ DONE_WITH_CONCERNS | 有非阻塞建议或 PRD 疑问 | PMO ⏸️ 用户确认 |
| 💥 FAILED | 需求不清晰 / 架构冲突无法解决 | 返回错误 + 部分产出 |

---

## AI Plan 模式指引（非强制）

典型方案：

- **方案 A（推荐）**：主对话执行 4 步闭环
  - 适合：多数场景。4 步在主对话串行走完，多视角通过 prompt 切换
  - 节省 Subagent 冷启动
  - 用户可随时介入讨论

- **方案 B**：Subagent 一次性闭环
  - 适合：需求十分清晰、无需用户介入讨论、要求主对话 context 隔离
  - 按 [Dispatch 文件协议](../agents/README.md#四dispatch-文件协议) 生成 dispatch 文件
  - 4 步内部执行，最终返回全部产物

- **方案 C**：混合模式
  - TC 和 TECH 在主对话讨论起草，架构师评审用 Subagent 做独立审查

🔴 AI 开始本 Stage 前必须在主对话输出 Execution Plan 块，并声明"已加载 Loaded Role Specs & Standards"清单。

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
└── 架构师评审：{通过 / 有建议已纳入 / 修复 N 轮}

## 产出文件
├── 📁 TEST-PLAN.md
├── 📁 TC.md（frontmatter 可解析，tests[] 数量：{N}）
├── 📁 TC-REVIEW.md
├── 📁 TECH.md
└── 📁 TECH-REVIEW.md（或 TECH.md 尾部）

## Output Contract 校验
├── TC YAML：✅ 可解析
├── AC→test 覆盖：{PRD AC 数} → {覆盖数} ✅/❌
├── TC 用例数 ≥ AC 数：✅
├── TECH 含文件清单：✅
└── 无 TBD：✅

## Concerns（如有）
{非阻塞性问题清单}
```
