# KNOWLEDGE 模板

> 位置:`project-specs/KNOWLEDGE.md`(workspace 级 · 与 product-overview/ 同级)+ `{子项目}/docs/KNOWLEDGE.md`(子项目级)· 详 [docs/conventions.md §13](../docs/conventions.md)
>
> 受众:**未来的开发者(包括未来的 AI)** — 让后续 Feature 启动时快速感知"本项目有哪些特殊事实/踩坑"。
>
> 🔴 **本文件 = AI 沉淀**(开发中被动发现的客观事实):**Gotchas(踩坑)/ Flagged Ambiguities(已澄清歧义)/ Preferences(用户偏好)/ Out-of-Scope(已否方向)**。teamwork triage 扫描 + bug/review/dev 流程中追加。
>
> 🔴 **边界声明**(别混):
>
> | 信息类型 | 去处 | 理由 |
> |---------|------|------|
> | **本项目强制开发规矩**(API 契约/错误处理/其他约定 · 团队约定)| 🔗 `DEV-RULES.md` | 人事前定的规矩 · 人维护;不是 AI 沉淀 |
> | 架构决策(为什么选 A 不选 B · 有备选 + 后果)| 🔗 [ADR](./adr.md) | 决策有备选 + 后果结构 |
> | 业务术语 / 实体关系 / 命名词典 | 🔗 `GLOSSARY.md` | 术语主权威 |
> | 通用代码规范 / 通用设计词汇 | 🔗 standards/ 或 rules/ | 跨项目通用 · 不属项目本地知识 |
> | 单个 Feature 复盘(时间线 + 指标)| `docs/retros/` | 复盘是时间线 · 不是事实索引 |
> | **项目特有的事实 / 踩坑 / 偏好** | **本文件** | 不是决策 · 是"发现"——没有备选项的客观事实 |
>
> 🔴 **体量上限 300 行**,超出:(a) Gotcha 升 ADR(若本质是决策)/ (b) 分拆到子项目级 KNOWLEDGE.md / (c) 过期归档(加 archived 标记 · 放末尾)。

```markdown
# 项目本地知识库

> 本文件记录开发中积累的**项目特有事实 / 踩坑 / 用户偏好**(AI 沉淀)。
> 不记录:开发规矩/约定(走 DEV-RULES.md)、决策(走 ADR)、通用规范(走 standards/rules)、术语(走 GLOSSARY.md)、复盘(走 retros/)。
> Teamwork 在 triage(用户输入承接阶段)会扫描本文件,注入「📚 相关项目事实」段。详见 [SKILL.md § Triage 入口规范](../SKILL.md)。

> 📌 **术语 → `GLOSSARY.md`**;**开发规矩/约定 → `DEV-RULES.md`**。本文件不再收录这两类。

## 🔀 Flagged Ambiguities(已澄清的歧义)

> 评审循环中暴露"用户用 X 词同时指 A 和 B"时,澄清完后**实时**记录到此(不批处理)。
> 防止下个 Feature 来同样的词又得 PMO 重新询问澄清一次。

| ID | 模糊词 | 澄清结论 | 触发 Feature | 时间 |
|----|--------|---------|-------------|------|
| FA-001 | "账号" | 三义:Customer(客户实体)/ User(操作主体)/ Tenant(多租户隔离单元);上下文未明确时一律走 PMO 澄清 | F035 评审 | 2026-04-12 |

## ⚠️ Gotchas(陷阱 / 约束 / 历史坑)

> 项目特有的陷阱、历史踩坑、外部系统的怪癖。**不是决策**——是被动发现的客观约束。
> 触发写入时机:Bug 修复完成 / Review Stage 发现陷阱 / Dev Stage 踩坑。

| ID | 主题 | 描述 | 规避方法 | 发现时间 | 触发 Feature |
|----|------|------|---------|---------|-------------|
| GO-001 | db | Postgres JSONB GIN 索引在高并发写入时会锁表 | 高频写字段避免 JSONB,拆到独立列 | 2026-01-15 | F023-xxx |
| GO-002 | api | 支付网关冷启动延迟 2s | 请求前必须先调 `/warmup` | 2026-02-03 | F031-支付重构 |

## 🎨 Preferences(用户偏好)

> 用户在产品层面强调的偏好——风格、交互、沟通方式。**不是规范**——是用户的口味。
> 触发写入时机:PM 验收时用户明确强调 / UI Design Stage 用户选 A 不选 B 时陈述的理由。

| ID | 类别 | 偏好 | 来源 | 记录时间 |
|----|------|------|------|---------|
| PR-001 | UI | 所有卡片圆角统一 8px | F015 验收时用户明确要求 | 2026-01-10 |
| PR-002 | 沟通 | PM 验收时用户偏好简洁汇报(3 行内),不要长篇分析 | 多个 Feature 累计反馈 | 2026-03-15 |

## ❌ Out of Scope(已拒绝过的方案/方向)

> 拒绝过的方案 / 方向——防止 AI 反复提同一个被否的方案。
> 触发写入时机:评审循环中明确 REJECT / PM 验收拒绝某方向 / Goal Stage 确认"这个方向不做"。
> PMO 在 Goal Stage 起草前必扫描本段,避免 PM 重新提已被否的方向。

| ID | 拒绝的方向 | 拒绝理由 | 拒绝时间 | 触发 Feature / 决策点 |
|----|-----------|---------|---------|----------------------|
| OS-001 | 接入 GraphQL 替代 REST API | 团队 REST 经验深 / 工具链成熟 / 当前瓶颈不在协议层 | 2026-02-10 | F029 评审 |

🔴 **PMO 起草 Goal / 评审循环时必须先扫 OS-NNN 列表**:发现 PRD 草案重新提了被否方向 → 直接打回让 PM 改写或显式说明"为什么本次重新审视"(必须有新触发原因,否则违规)。

## 按主题索引

> PMO preflight 时可按主题快速 grep。

- **db**: GO-001
- **api**: GO-002
- **UI**: PR-001
- **沟通**: PR-002
- **拒绝**: OS-001
- **歧义**: FA-001

## 归档(archived)

> 已不适用的 Gotcha / Preference,保留备查。Feature 新启动时 PMO preflight 可忽略本段。

| ID | 原内容 | 归档原因 | 归档时间 |
|----|--------|---------|---------|
| GO-000 | ~~示例:旧约束~~ | 升级后问题消失(ADR-0008)| 2026-04-01 |
```

## 使用约定

### 写入硬时机

🔴 以下时机 PMO 必须提示对应角色写入 KNOWLEDGE.md(不写 = 流程偏离):

- **Gotcha 写入时机**:
  - Bug 修复流程完成时 → PMO 在完成报告里提示 RD 补一条 Gotcha(除非确认一次性 bug 无复发风险)
  - Dev Stage 遇未知陷阱(调试 ≥30 分钟 / 改动方案多次返工)→ 修复后必写一条 Gotcha
  - Review Stage 架构师发现 RD 绕过陷阱写了特殊处理 → 必写一条 Gotcha(把"为什么这么写"显式化)
- **Preference 写入时机**:
  - PM 验收时用户明确表达偏好 → PM 必记 PR-NNN
  - UI Design Stage 用户在多方案中选 A 并陈述理由 → Designer 必记 PR-NNN
- 🔴 **开发规矩/约定 不写这里 → 见 `DEV-RULES.md`**(人维护):AI 在 review/dev 发现值得固化的新约定 → **提示用户**加进 DEV-RULES.md · **不代写**(那是人定的规矩)。

### PMO preflight 扫描

🔴 PMO 初步分析任何 Feature / Bug / Feature Planning 时,必须扫描 KNOWLEDGE.md:
- 读 `{目标子项目}/docs/KNOWLEDGE.md`(不存在 → 「本项目暂无 KNOWLEDGE 记录」)
- 按当前 Feature 主题 + 涉及模块扫描索引,列出可能相关的条目 ID
- 注入 PMO 初步分析输出的「📚 相关项目事实」行
- 只读 KNOWLEDGE.md 前 300 行(体量上限 = 扫描上限)

### 体量与归档

- 🔴 单个 KNOWLEDGE.md ≤ 300 行。超出时必选一种处理:
  - (a) 判定条目本质是决策 → 升格为 ADR,本文件删除
  - (b) 多子项目模式下条目只适用某子项目 → 迁到 `{子项目}/docs/KNOWLEDGE.md`
  - (c) 条目已过期 → 移到「归档」段加 archived 标记
- 🟢 每个条目 ≤ 2 行,超出说明不够"事实",可能是决策伪装

### ID 编号规则

- Gotcha:GO-NNN(三位数字,从 001 起)· Preference:PR-NNN · Out of Scope:OS-NNN · Flagged Ambiguities:FA-NNN
- 🔴 编号连续不复用,归档条目保留原 ID

## 与其他文档的协作

- 🔗 `DEV-RULES.md` — 本项目强制开发规矩(人维护 · blueprint/dev 必读);本文件只记"被动发现的事实/踩坑"
- 🔗 `GLOSSARY.md` — 业务术语 / 命名词典
- 🔗 [ADR 模板](./adr.md) — 决策归 ADR,本文件不重复
- 🔗 [standards/common.md](../standards/common.md) — 通用规范归 standards,本文件只记项目特有
