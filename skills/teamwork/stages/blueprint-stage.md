# Blueprint Stage：技术规格（QA 写 TC + TC 技术评审 + RD 写技术方案 + 架构师评审）

> PMO 在用户确认 PRD 后（Designer 完成后，如有 UI）启动本 Stage。
> 内部完成 QA 测试规格 + RD 技术方案 + 多角色评审，一次性返回全部规格文档。
> 🔴 目标：产出"怎么测 + 怎么做"的完整蓝图，Dev Stage 按此执行。

---

## 一、设计意图

```
Blueprint Stage = 开发前的完整技术规格
├── QA 视角：怎么测（TC）
├── RD 视角：怎么做（TECH.md）
├── 架构师视角：方案是否合理
└── 产出后交给用户确认，确认后 Dev Stage 按蓝图执行

PMO relay 从 4 次（QA→评审→RD→架构师）降为 1 次。
```

---

## 二、内部阶段

```
阶段 1: QA Test Plan + Write Cases
├── 角色：QA
├── 规范：roles/qa.md
├── 产出：TEST-PLAN.md + TC.md（BDD/Gherkin 格式）

阶段 2: TC 技术评审
├── 角色：RD + Designer（如有 UI）+ PMO
├── 规范：roles/qa.md「TC 技术评审规范」
├── 产出：TC-REVIEW.md
├── 有问题 → QA 内部修订 TC → 重新评审（≤2 轮）
└── 通过 → 进入阶段 3

阶段 3: RD 技术方案
├── 角色：RD
├── 规范：roles/rd.md
├── 产出：TECH.md（含实现计划、文件清单、改动要点）

阶段 4: 架构师方案评审
├── 角色：架构师
├── 规范：roles/rd.md「架构师方案评审规范」
├── 产出：评审报告
├── 有严重问题 → RD 修改方案 → 重新评审（≤3 轮）
└── 通过 → 定稿
```

---

## 三、输入文件

```
PMO 启动时必须注入：
├── agents/README.md
├── stages/blueprint-stage.md（本文件）
├── roles/qa.md（含 TC 技术评审规范）
├── roles/rd.md（含架构师方案评审规范）
├── templates/tc.md
├── docs/features/F{编号}-{功能名}/PRD.md（已确认）
├── docs/features/F{编号}-{功能名}/UI.md（如有）
├── .claude/skills/teamwork/standards/common.md
│
可选文件：
├── docs/architecture/ARCHITECTURE.md
├── docs/KNOWLEDGE.md
└── docs/architecture/database-schema.md
```

---

## 四、返回状态

```
├── ✅ DONE
│   ├── 条件：TC + TECH.md 定稿 + 评审通过
│   └── 返回：TC.md + TEST-PLAN.md + TECH.md + 评审报告
│
├── ⚠️ DONE_WITH_CONCERNS
│   ├── 条件：定稿但有非阻塞性问题（QA 有疑问 / 架构师有建议）
│   └── 返回：全部文档 + concerns 清单（PMO ⏸️ 用户确认）
│
└── 💥 FAILED
    ├── 条件：无法完成（需求不清晰 / 架构冲突无法解决）
    └── 返回：错误信息 + 已完成的部分
```

---

## 五、红线

```
🔴 TC 必须用 BDD/Gherkin 格式
🔴 TC 技术评审不可跳过
🔴 架构师方案评审不可跳过（无论方案多简单）
🔴 TECH.md 必须包含实现计划（文件清单 + 改动要点）
🔴 内部评审修复循环最多 3 轮，超出则返回 DONE_WITH_CONCERNS
```

---

## 六、输出格式

```
📋 Blueprint Stage 执行报告（F{编号}-{功能名}）
================================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / FAILED}
├── TC：{N} 条 BDD 用例，覆盖率 {M}/{总 AC}
├── TC 技术评审：{通过 / 有建议已纳入}
├── TECH.md：{完成 / 有 concerns}
└── 架构师评审：{通过 / 有建议已纳入}

## 产出文件
├── 📁 TEST-PLAN.md
├── 📁 TC.md
├── 📁 TC-REVIEW.md
├── 📁 TECH.md
└── 📁 架构师评审报告

## Concerns（如有）
{非阻塞性问题清单}
```
