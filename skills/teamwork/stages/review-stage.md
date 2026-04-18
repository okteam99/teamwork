# Review Stage：三视角独立代码审查

> Dev Stage 通过后进入本 Stage。产出三份**独立视角**的代码审查报告（架构师 / QA / 外部），汇合到 REVIEW.md。
> 🔴 契约优先：独立性通过**产物结构**保证（而非强制执行方式）。AI 可按场景选择实现路径。

---

## 本 Stage 职责

对 Dev Stage 产出的代码从三个独立视角审查：
- **架构师视角**：架构合理性、代码规范、ARCHITECTURE.md 同步
- **QA 视角**：TC 逐条验证覆盖、TDD 规范、测试质量
- **外部独立视角**（Codex 或等效外部模型）：发现同模型盲区、安全、第三方依赖

---

## Input Contract

### 共用必读文件

```
├── {SKILL_ROOT}/agents/README.md
├── {SKILL_ROOT}/stages/review-stage.md（本文件）
├── {Feature}/PRD.md
├── {Feature}/TC.md
├── {Feature}/TECH.md
├── Dev Stage 产出（代码 diff + 自查报告路径）
└── {SKILL_ROOT}/standards/common.md
```

### 各视角专属必读

```
架构师视角 额外读：
├── {SKILL_ROOT}/roles/rd.md（含架构师规范）
├── {SKILL_ROOT}/agents/arch-code-review.md
└── docs/architecture/ARCHITECTURE.md

QA 视角 额外读：
├── {SKILL_ROOT}/roles/qa.md
├── {SKILL_ROOT}/agents/qa-code-review.md
└── {Feature}/UI.md + preview/*.html（如有，用于设计-代码一致性）

外部视角（Codex / 其他模型） 额外读：
├── 🔴 严禁读：架构师 Review 报告（保持独立性）
└── 只基于代码 diff + PRD/TECH/TC + standards
```

### Key Context（逐项判断，无则 `-`）

- 本轮聚焦点（重跑时必填：上一轮问题清单）
- 已识别风险
- 降级授权（Codex CLI 不可用 → 降级 Sonnet）
- 优先级 / 容忍度

### 前置依赖

- `state.json.stage_contracts.dev.output_satisfied == true`
- Dev Stage 单测全绿
- state.json.current_stage == "review"

---

## Process Contract

### 必做动作

1. **三视角独立审查**（顺序无关，可并行可串行）
   - 每个视角独立读取自己的输入文件，产出独立报告
   - 每个视角不得引用其他视角的报告
   - 每个视角必须记录自己读过的文件清单（审计）

2. **架构师 Code Review**
   - 按 `agents/arch-code-review.md`
   - 产出 `review-arch.md`
   - 维度：架构合理性 / 代码规范 / 性能 / 安全 / ARCHITECTURE.md 同步

3. **QA 代码审查**
   - 按 `agents/qa-code-review.md`
   - 产出 `review-qa.md`
   - 维度：TC 逐条覆盖 / TDD 规范 / 集成测试代码完整性 / 设计-代码一致性

4. **外部独立审查**（Codex 或等效）
   - 按 `agents/codex-review.md`（如无则按 `review-stage.md` 中的 prompt 模板）
   - 产出 `review-codex.md`
   - 维度：逻辑正确性 / 安全漏洞 / 第三方依赖真实性 / 并发安全 / 代码质量

5. **汇合到 REVIEW.md**（PMO 职责）
   - 合并去重（同一文件同一位置问题合并）
   - 按严重程度排序（🔴 阻塞 > 🟡 建议修复 > 🟢 优化）

### 过程硬规则

- 🔴 **角色规范必读且 cite**：每视角开始前必读对应 `agents/*-review.md` 或 `roles/*.md`，产出前 cite 要点
- 🔴 **三视角独立性（结构约束）**：
  - 每份报告必须有独立 `generated_at` 时间戳
  - 每份报告必须列出"本视角读过的文件"清单
  - 三份报告互不引用（`grep -r "review-arch" review-codex.md` 应为空，反之亦然）
- 🔴 **Codex 独立性硬约束**：外部视角严禁读架构师 / QA 的 review 报告
- 🔴 **完整性**：每个视角按各自规范完整执行，不能因为另一个视角已通过就简化
- 🔴 **不修复**：Review 只审不改，发现问题返回 PMO 安排 RD 修复
- 🔴 **循环控制**：修复-重跑循环 ≤3 轮

### 多视角独立性（产物结构保证）

这是本 Stage 契约的核心。Output Contract 要求三份独立报告 + 不互相引用 + 时间戳独立——AI 为满足这些产物条件，**结构上**必然做三次独立审查。

---

## Output Contract

### 必须产出的文件

| 文件路径 | 格式 | 必需字段 |
|---------|------|---------|
| `{Feature}/review-arch.md` | Markdown + YAML frontmatter | `perspective: architect`, `generated_at`, `files_read[]`, `findings[]`（含 severity/file/line/message/suggestion） |
| `{Feature}/review-qa.md` | Markdown + YAML frontmatter | `perspective: qa`, `generated_at`, `files_read[]`, `tc_coverage_report`, `findings[]` |
| `{Feature}/review-codex.md` | Markdown + YAML frontmatter | `perspective: external`, `generated_at`, `files_read[]`, `findings[]` |
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
5. 🔴 最多 3 轮，超出 → ⏸️ 用户决策

Codex 独立性保障：
├── 重跑时 Codex 仍不看架构师 / QA 报告
├── Codex 的问题由 RD + 架构师评估后决定是否采纳
└── 第三方依赖真实性问题严肃对待（Codex 说包不存在 → 必须核实）
```

---

## AI Plan 模式指引

📎 Execution Plan 3 行格式 → [SKILL.md](../SKILL.md#-ai-plan-模式规范v73-新增)。

本 Stage 默认 `hybrid`（架构师主对话 + QA/Codex 并行 Subagent）。

三路分工理由：
- 架构师视角需项目全局上下文（ARCHITECTURE 演化、历史决策），主对话保留累积
- QA / Codex 视角需独立性，Subagent 天然 fresh context
- 架构师主对话时加「怀疑者视角」prompt 防鼓掌（见下方）

典型偏离：
- 小改动 / 主对话 context 足够 → 三视角全 `main-conversation`（需清洗 context 防创建者偏见）
- 大改动 / 要求最强独立性 → 三视角全 `subagent`（Dispatch 文件 Batch 字段同批次）

🔴 不论哪种 approach，Output Contract 的独立性校验（三份产物独立 generated_at / files_read / 不互相引用）都必须满足。

### 架构师主对话 Review 防鼓掌机制（approach 含 main-conversation 时必做）

- 开始前显式声明"进入架构师审查模式，采用怀疑者视角"
- 不读 RD 自查报告（只看代码 diff + TECH.md + ARCHITECTURE.md）
- 强制产出 ≥3 条批评；若确实无，显式说明"代码高质量，未发现"+ 审查过的维度清单

---

## 执行报告模板

```
📋 Review Stage 执行报告（F{编号}-{功能名}）
============================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / NEEDS_FIX / FAILED}
├── 执行方式：架构师{主对话/Subagent} + QA {主对话/Subagent} + Codex {主对话/Subagent}
├── 合并问题数：🔴 {x} / 🟡 {y} / 🟢 {z}
└── 落盘：{Feature}/REVIEW.md

## 三视角产出
| 视角 | 文件 | generated_at | files_read | findings |
|------|------|-------------|------------|----------|
| 架构师 | review-arch.md | ... | 5 | 🔴0 🟡2 🟢1 |
| QA | review-qa.md | ... | 4 | 🔴0 🟡1 🟢0 |
| 外部（Codex）| review-codex.md | ... | 3 | 🔴0 🟡0 🟢2 |

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
