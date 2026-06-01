# Lessons from PTR-F033 · v8.0+P0-1 ~ P0-5 治本汇总

> ⚠️ **归档文档(v8.0 重构期蓝图)**:本文件是 v7→v8 重构期的设计/规划文档 · 描述当时的**计划态**。v8 已稳定至 v8.45 · 现行权威以 [SKILL.md](../../SKILL.md) + tools/state.py 实际行为为准。文内可能引用已失效的 RULES.md/TRIAGE.md(并入 SKILL.md)/ 旧 stage 名 / 旧命令。PTR-F033 dogfood 复盘 · 引用的 RULES.md/TRIAGE.md 已并入 SKILL.md。不再维护。


> PTR-F033(Partner Credit Note Adjustment Feature)实战 case 暴露了 v8 多个设计缺口。
> 4 个 P0 patch + 1 个概念清理(P0-5)都源自此 case。
> 本文是反思 + 演进文档。

---

## Case 背景

PTR-F033 是 v8 第一个真实跑的 Feature。在 goal_plan 阶段:
1. AI 起草 PRD v0.1
2. AI 在主对话切角色 PL 评审 · 发现 3 个 issue + 5 个 Open Questions
3. AI 调 `AskUserQuestion` 问用户 5 个 Open Questions
4. 用户回 4 个决策
5. AI 修订 PRD → v0.2

**问题暴露**:
- AI 在 substep 2 后插了用户暂停点(违 R5 暂停点协议)
- AI 把 PRD 写在了主 tree 的 untracked(没建 worktree)
- AI 把 state.json 写在了主 tree(没 cd 进 worktree)
- v8 没在 stage 进入前给 worktree 物化指引

---

## 4 个 P0 + 1 概念清理(都源自此 case)

### v8.0+P0-1 · 暂停点纪律(L2 substep 链)

**根因**:`stage-start` emit brief 列了"6 个 substep + 末尾 Substep 6 ⏸️ 暂停点",但**没明文说"中间禁暂停"**。AI 把"至少 substep 6 暂停"理解成"至少这一次",而非"只有这一次"。

**修复**:
- `_v8_engine.py` 加 `_render_pause_discipline()` · execute_stage_start 自动 append 到 brief 末尾
- `StageSpec.authorized_pause_point` 字段 · 各 stage 显式声明唯一授权暂停
- `_v8_stage_specs.py` 加 `_evidence_review_after_primary()` + `_evidence_revision_history_present()` 间接 evidence(事后兜底:PRD-REVIEW mtime > PRD mtime + frontmatter.revision_history)

**详见**:[04-PAUSE-POINT-DISCIPLINE.md](./04-PAUSE-POINT-DISCIPLINE.md)

---

### v8.0+P0-2 · worktree 物理存在校验(stage-start 兜底)

**根因**:state.json 写了 `worktree.path / .branch / .strategy` 元数据,但**state.py 既没建也没校验**。PMO 漏 git worktree add → 主 tree 污染。

**修复**:
- `_v8_engine._worktree_physically_exists()` · stage-start 通用校验
- `worktree_mode != off` 且 worktree 物理不存在 → FAIL + hint
- bypass 协议:需 `--missing worktree_physical_exists --user-confirmed`

**注**:此 P0 的 init-feature 自动建 worktree 部分被 P0-5 删除(单一职责)· 仅保留 stage-start 校验。

---

### v8.0+P0-3 · cwd 物化校验(防 state.json 落主 tree)

**根因**:即使 worktree 建了 · 若 PMO 在主 tree cwd 跑 init-feature · state.json 仍落主 tree(因为 cwd 决定相对路径基点)。

**修复**:
- `state.py cmd_init_feature` 加 cwd 校验
- worktree_mode != off + cwd 不在 worktree → FAIL + hint
- feature_path 也必须在 worktree 内(防绝对路径反向)
- bypass:`TEAMWORK_BYPASS_CWD_WORKTREE=1`

---

### v8.0+P0-4 · brief 末尾必读路径速查

**根因**:brief 列了"必读:KNOWLEDGE.md / GLOSSARY.md / ..." 文件名 · 但**没给路径**。AI 拿到要自己 grep / find · 浪费 token + 找错风险。

**修复**:
- `_v8_engine._render_required_paths()` · 所有 stage brief 末尾自动 append
- 列出**实际存在**的 Feature artifact + stage spec + state.json 绝对路径
- "按需查询区"留给 AI 实地获取(KNOWLEDGE / GLOSSARY 等不在必读区)

---

### v8.0+P0-5 · 概念清理 + 入口规范(triage 不是 stage)

**根因**:v8 当前把 triage 当 "会话级 Stage" · 但实际 triage 是分诊入口 · 不在状态机内。混淆导致:
- triage 命令不写 state.json · 但叫"stage"
- worktree 决策应在 triage(入口)做 · 但 v8 让 init-feature 副作用建(P0-2)· state.json 落位错
- 用户暂停点应在 triage 出现 · 但 v8 没设计这个机制

**修复**:
- **概念**:triage = 入口规范 · 不是 stage · 不进 LEGAL_STAGES
- **新顶级文档**:[TRIAGE.md](../../TRIAGE.md)(与 SKILL.md / RULES.md / FLOWS.md 平级)
- **triage 实现**:mode B emit 加 `worktree_decision` + `pause_for_user.markdown` · 等用户确认 Feature ID / merge_target / worktree path / branch
- **init-feature 简化**:删 P0-2 自动建 worktree(单一职责)· 保留 P0-3 cwd 校验 + 加 worktree 物理存在硬校验
- **正路径**:triage → 用户确认 → PMO 显式 git worktree add → cd → init-feature(状态机)

**详见**:[../../TRIAGE.md](../../TRIAGE.md)

---

## 设计原则升级(总结)

### 元规则 1 · state.json 字段必须有 action + verifier

```
元数据字段 → 物理操作 → 物理校验
worktree.path → triage 建议 + PMO 显式 add → stage-start 物理存在校验
auto_commit → xx-complete 必传 → git cat-file -e + changeset 校验
mr_url → ship-phase --action push → URL 二选一 enum 校验
```

未来加任何 state.json 字段 · 必须同时定义 action(谁创建)+ verifier(谁校验)。

### 元规则 2 · 状态机的入口和出口物化拦截

```
入口物化:cwd 校验 + 前置存在性
出口物化:产物校验 + evidence 校验 + 间接 evidence(mtime / frontmatter)
```

### 元规则 3 · brief 长度上限 + 自动外置

```
MAX_BRIEF_LINES = 100
超出 → 自动写到 _brief_full_<stage>.md + brief 留摘要
防 Layer A(预防式 brief 内联)累积膨胀(v7 RULES.md 1883 行教训)
```

### 元规则 4 · 入口规范层 vs 状态机层

```
入口规范(TRIAGE)· stateless · 不写 state.json · 不进 LEGAL_STAGES
                ↓ 用户确认 worktree
状态机层(state.py)· stateful · stage 链 · 物化拦截
```

triage 不是 stage · 是入口分诊。新 AI 经常错误把 triage 当 stage(因为之前文档叫"会话级 Stage")· P0-5 概念清理后此误解消除。

---

## v8 文档体系最终结构(P0-5 后)

```
顶级(与 SKILL.md 平级):
├── SKILL.md          v8 命令清单 + 设计哲学
├── TRIAGE.md         入口规范(本 P0-5 新增)
├── RULES.md          9 红线 rationale
├── FLOWS.md          6 流程 telos
├── ROLES.md          8 角色索引
├── STANDARDS.md      技术规范索引
└── TEMPLATES.md      模板索引

stages/ · 各 stage 内容创作规范(待 P0-6 重写为"内容创作规范"格式)

docs/archive/v8-redesign/ · 设计文档 + 治本反思
├── 00-MANIFESTO.md          设计宪法
├── 01-COMMAND-SCHEMA.md     30 命令 schema
├── 02-CLEANUP.md            v7→v8 清理清单
├── 03-MIGRATION.md          迁移路线
├── 04-PAUSE-POINT-DISCIPLINE.md  P0-1 治本
└── 05-LESSONS-FROM-PTR-F033.md   本文档(P0-1~P0-5 汇总)
```

---

## 一个真实 case 的 ROI

PTR-F033 一个 case · 触发 4 个 P0 patch + 1 个概念清理 + 大量元规则升级。

这印证 v8 设计哲学:
- **dogfood 实战压测 > 闭门设计**
- **物化拦截 > AI 自觉**
- **暴露缺口 → 修复 → 写治本文档(给未来 AI 看 hint 时引用)**

后续真实 Feature 跑过来时 · 这 5 个治本应该让同型缺口不再发生:
- 暂停点违规 → P0-1 brief 自动 append discipline
- worktree 漏建 → P0-2 stage-start 物理校验
- state.json 落主 tree → P0-3 cwd 校验
- AI 漏看必读路径 → P0-4 brief 末尾路径速查
- triage / stage 概念混淆 → P0-5 TRIAGE.md 顶级文档

如果还有新 case 暴露新缺口 · 那就是 P0-6 的素材。

---

## 相关

- [00-MANIFESTO.md](./00-MANIFESTO.md) — v8 设计宪法
- [04-PAUSE-POINT-DISCIPLINE.md](./04-PAUSE-POINT-DISCIPLINE.md) — P0-1 暂停点纪律
- [../../TRIAGE.md](../../TRIAGE.md) — P0-5 入口规范
- [../../SKILL.md](../../SKILL.md) — v8 顶层叙事
