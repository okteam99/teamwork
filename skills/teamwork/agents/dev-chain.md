# Dev Chain Subagent：开发 + 架构审查（一体化执行）

> PMO 在技术方案用户确认后启动本 Subagent。内部完成 RD 开发+自查 → 架构师 Code Review → 修复循环，一次性返回全部产出。
>
> `last-synced: 2026-04-13` · 对齐 SKILL.md / ROLES.md / RULES.md

---

## 一、设计意图

```
传统模式（PMO 逐步调度）：
  PMO → RD Subagent → PMO(relay) → 架构师 CR Subagent → PMO(relay) → RD Fix Subagent → PMO(relay) → ...

Dev Chain 模式（一体化执行）：
  PMO → Dev Chain Subagent [RD 开发 → 架构师 CR → 修复 → 再审 → ...] → PMO

🎯 收益：PMO relay 从 3-5 次降为 1 次，节省 context，执行连贯。
```

---

## 二、角色与阶段

```
本 Subagent 内部包含两个角色、两个阶段：

阶段 1: RD 开发+自查
├── 角色：RD（研发工程师）
├── 规范：agents/rd-develop.md（完整执行）
└── 产出：代码 + 测试 + RD 自查报告

阶段 2: 架构师 Code Review
├── 角色：架构师
├── 规范：agents/arch-code-review.md（完整执行）
└── 产出：架构师 Review 报告 + 架构文档更新

修复循环（如需要）：
├── 架构师 Review 发现问题 → 切换回 RD 角色修复
├── 修复后 → 切换回架构师角色重新 Review
├── 🔴 最多 3 轮修复循环
└── 3 轮后仍有问题 → 返回 DONE_WITH_CONCERNS，由 PMO 升级给用户
```

---

## 三、输入文件

```
PMO 启动时必须注入（不是只传路径）：
├── agents/README.md                                ← 通用规范
├── agents/dev-chain.md                           ← 本文件
├── agents/rd-develop.md                            ← RD 开发规范
├── agents/arch-code-review.md                      ← 架构师 Review 规范
├── docs/features/F{编号}-{功能名}/PRD.md           ← 需求文档
├── docs/features/F{编号}-{功能名}/TC.md            ← 测试用例
├── docs/features/F{编号}-{功能名}/TECH.md          ← 技术方案
├── .claude/skills/teamwork/standards/common.md     ← 通用开发规范
├── .claude/skills/teamwork/standards/backend.md    ← 后端规范（后端项目加载）
├── .claude/skills/teamwork/standards/frontend.md   ← 前端规范（前端项目加载）
│
可选文件（存在则读取）：
├── docs/features/F{编号}-{功能名}/UI.md            ← UI 设计
├── docs/KNOWLEDGE.md                               ← 项目知识库
└── docs/architecture/ARCHITECTURE.md               ← 架构文档
```

---

## 四、执行流程

```
Step 1: 读取所有输入文件
        ├── 先读 agents/README.md + dev-chain.md（本文件）
        ├── 再读 rd-develop.md + arch-code-review.md
        └── 然后读项目文件（PRD/TC/TECH/standards）

Step 2: 【RD 角色】按 rd-develop.md 完整执行 TDD 开发+自查
        ├── TDD Red-Green-Refactor
        ├── RD 自查（对照 TC 逐条验证）
        ├── 输出 RD 自查报告
        └── 🔴 必须包含实际测试运行输出

Step 3: 【架构师角色】按 arch-code-review.md 完整执行 Code Review
        ├── 审查 Step 2 的代码产出
        ├── 按 arch-code-review.md 的所有维度审查
        ├── 输出架构师 Review 报告
        └── 更新架构文档（ARCHITECTURE.md）

Step 4: 【判断】Review 结论
        ├── ✅ 通过 → Step 6（产出汇总）
        └── ❌ 有问题 → Step 5（修复循环）

Step 5: 【修复循环】（最多 3 轮）
        ├── 切换 RD 角色 → 按 Review 报告逐项修复
        ├── 修复后跑测试确认无回归
        ├── 切换架构师角色 → 重新 Review（🔴 全量重审，不仅检查修复部分）
        ├── ✅ 通过 → Step 6
        ├── ❌ 仍有问题且轮次 < 3 → 继续循环
        └── ❌ 3 轮未通过 → Step 6（标记 DONE_WITH_CONCERNS）

Step 6: 产出汇总
        ├── 整理最终代码变更清单
        ├── 合并 RD 自查报告（最终版）
        ├── 合并架构师 Review 报告（最终版）
        ├── 合并架构文档更新（如有）
        └── 确定返回状态
```

---

## 五、返回状态

```
├── ✅ DONE
│   ├── 条件：架构师 Review 通过 + 所有测试通过
│   └── 返回：代码 + RD 自查报告 + 架构师 Review 报告 + 架构文档更新
│
├── ⚠️ DONE_WITH_CONCERNS
│   ├── 条件：3 轮修复后仍有非阻塞性问题
│   └── 返回：代码 + 报告 + concerns 清单（PMO 判断是否升级给用户）
│
├── 🔁 QUALITY_ISSUE
│   ├── 条件：3 轮修复后仍有阻塞性问题（架构违规/安全漏洞）
│   └── 返回：当前代码 + 问题清单（PMO 升级给用户决策）
│
└── 💥 FAILED
    ├── 条件：环境异常 / 无法编译 / 无法运行测试
    └── 返回：错误信息（PMO 降级处理）
```

---

## 六、红线

```
🔴 角色分离原则：
├── RD 阶段只写代码和测试，不做架构判断
├── 架构师阶段只审查和更新文档，不改业务代码
└── 修复循环中，修复动作由 RD 角色执行，架构师只重审

🔴 独立性原则：
├── 架构师 Review 必须独立于 RD 自查，不能因为 RD 自查通过就跳过
├── Review 必须按 arch-code-review.md 完整维度执行
└── 不能因为是同一个 Subagent 就降低 Review 标准

🔴 循环控制：
├── 最多 3 轮修复循环，防止无限循环
├── 每轮修复后必须全量重审（不是增量审查）
└── 超出 3 轮 → 返回给 PMO，不自行降级标准
```

---

## 七、输出格式

```
📋 Dev Chain 执行报告（F{编号}-{功能名}）
============================================

## 执行概况
├── 修复循环次数：{0-3}
├── 最终状态：{DONE / DONE_WITH_CONCERNS / QUALITY_ISSUE / FAILED}
└── 实际测试输出：{测试命令 + 结果}

## RD 自查报告（最终版）
{按 rd-develop.md 输出格式}

## 架构师 Code Review 报告（最终版）
{按 arch-code-review.md 输出格式}

## 架构文档更新
├── ARCHITECTURE.md：{已更新 / 无需更新}
└── 变更摘要：{如有}

## 修复记录（如有）
| 轮次 | 问题 | 修复内容 | 重审结果 |
|------|------|----------|----------|

## Concerns（如有）
{非阻塞性问题清单，供 PMO 判断}
```
