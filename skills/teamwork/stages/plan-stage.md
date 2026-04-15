# Plan Stage：需求定义（PM 写 PRD + PL-PM 讨论 + 多角色技术评审）

> PMO 在用户确认流程类型后启动本 Stage。内部完成 PM 写 PRD 初稿 → PL-PM 讨论收敛 → 多角色技术评审 → 产出定稿 PRD，一次性返回。
> 🔴 目标：产出一份经过产品对齐 + 技术评审的合格 PRD。

---

## 一、设计意图

```
传统模式（PMO 逐步调度）：
  PMO → PM 写 PRD → PMO(relay) → PL-PM 讨论 → PMO(relay) → 技术评审 → PMO(relay)

Plan Stage 模式（一体化执行）：
  PMO → Plan Stage [PM 写初稿 → PL-PM 讨论 → 技术评审 → 定稿] → PMO

🎯 收益：PMO relay 从 3 次降为 1 次，需求定义连贯，context 节省显著。
```

---

## 二、内部阶段

```
阶段 1: PM 编写 PRD 初稿
├── 角色：PM
├── 规范：roles/pm.md + templates/prd.md
├── 产出：PRD.md 初稿（含交付预期、验收标准、待决策项）
└── 🔴 必须包含「交付预期」section（用户视角的变化 + 验证方式）

阶段 2: PL-PM 讨论（产品方向对齐）
├── 角色：PL + PM 交替对话
├── 规范：原 pl-pm-discuss-stage.md 的讨论逻辑
├── 最多 3 轮讨论
├── ✅ 达成共识 → PM 按共识更新 PRD → 进入阶段 3
└── ⚠️ 有分歧 → 记录分歧项，标记为待用户决策 → 进入阶段 3

阶段 3: 多角色技术评审
├── 角色：RD（技术）+ Designer（设计，如有 UI）+ QA（测试）+ PMO（项目）
├── 规范：roles/pm.md「PRD 技术评审规范」
├── 产出：PRD-REVIEW.md
└── 汇总问题 + 建议

阶段 4: 定稿
├── PM 按评审结论更新 PRD
├── 标记 PRD 状态为「待用户确认」
└── 整理输出报告
```

---

## 三、输入文件

```
PMO 启动时必须注入：
├── agents/README.md                                ← 通用规范
├── stages/prd-stage.md                             ← 本文件
├── roles/pm.md                                     ← PM 角色 + PRD 技术评审规范
├── roles/product-lead.md                           ← PL 角色（讨论用）
├── templates/prd.md                                ← PRD 模板
├── .claude/skills/teamwork/standards/common.md     ← 通用开发规范
│
可选文件（存在则读取）：
├── docs/PROJECT.md                                 ← 产品总览
├── docs/KNOWLEDGE.md                               ← 项目知识库
├── docs/architecture/ARCHITECTURE.md               ← 架构文档（技术评审参考）
└── design/sitemap.md                               ← 全景设计（有 UI 时参考）
```

---

## 四、返回状态

```
├── ✅ DONE
│   ├── 条件：PRD 定稿 + 技术评审通过 + 无分歧
│   └── 返回：PRD.md + PRD-REVIEW.md + PL-PM 讨论纪要
│
├── ⚠️ DONE_WITH_CONCERNS
│   ├── 条件：PRD 定稿但有 PL-PM 分歧项待用户决策
│   └── 返回：PRD.md + 分歧项清单（PMO ⏸️ 用户逐项决策）
│
└── 💥 FAILED
    ├── 条件：无法完成 PRD（需求不清晰等）
    └── 返回：错误信息 + 已完成的部分产出
```

---

## 五、红线

```
🔴 PL-PM 讨论独立性：PL 和 PM 各自表达观点，不能一方主导
🔴 技术评审完整性：必须按 roles/pm.md 的评审维度（RD/Designer/QA/PMO）完整执行
🔴 PRD 质量：不能留 TBD / 待补充，验收标准必须量化可验证
🔴 讨论轮次控制：PL-PM 最多 3 轮，超出则记录分歧返回
```

---

## 六、输出格式

```
📋 Plan Stage 执行报告（F{编号}-{功能名}）
================================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / FAILED}
├── PL-PM 讨论：{R1 收敛 / R2 收敛 / 有分歧}
├── 技术评审：{通过 / 有建议已纳入 / 有问题}
└── PRD 验收标准数：{N} 条

## PL-PM 讨论纪要
├── 讨论轮次：{1-3}
├── 共识项：{N} 条
├── 分歧项：{M} 条（待用户决策）
└── PRD 修改：{已纳入的修改摘要}

## 技术评审报告
{按 PRD-REVIEW.md 格式}

## 产出文件
├── 📁 PRD.md（定稿）
├── 📁 PRD-REVIEW.md（评审记录）
└── 📁 discuss/PL-FEEDBACK-R{N}.md + PM-RESPONSE-R{N}.md
```
