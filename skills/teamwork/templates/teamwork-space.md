# teamwork-space.md 模板(实例化骨架)

> 位置:项目根 `teamwork-space.md`(**必读知识地图根 · 索引之索引** · 任何 teamwork 项目都有 · N≥1 子项目 · **单项目 = 1 个子项目**)。
> 🔴 **任何变更必须暂停等用户确认(R5)** · 任一单元格 ≤ 1 行 · 详情外迁(workstream/WS-NN.md / Feature state.json / PROJECT.md / ADR)。
> 🔴 **维护规则 / 字段语义 / 生命周期 / 硬约束 → [docs/teamwork-space-guide.md](../docs/teamwork-space-guide.md)**(AI 读 · 不复制进项目文件)。
> 🔴 **三层律**:本文件 = **地图**(导航指针)· **代码 = 领土**(细节唯一真相)· `_archive/*.zip` = **冷库**(按需解压)· 详 [SKILL.md § 项目级文档信息架构](../SKILL.md)。

```markdown
# Teamwork Space

> **本项目知识地图根 · 索引之索引** · 任何 session 先读本文件 → 它指向每个知识节点(子项目 / 规划 / 工程文档 / 三方 / 归档冷库)· 指向的领土(代码 / 大文档)按需读 · **代码是细节唯一真相**。任何变更需用户确认。

---

## 知识入口（索引之索引 · 零死角）

<!-- 🔴 本项目所有知识节点的一行指针 · AI 从这里能抵达一切 · 缺节点 = 知识泄露死角 · 一行只写"去哪"不写"是什么"(文档类型语义 = 律法 · 在 SKILL.md)· 详 guide §0.1 -->

| 知识域 | 入口 | 内含 |
|--------|------|------|
| 子项目代码 + 文档 | ↓ § 子项目清单(`docs_root`) | 每个子项目 `docs/`:PROJECT / architecture / ROADMAP / KNOWLEDGE / sitemap / features/ |
| 产品规划（有时） | [`product-overview/`](product-overview/) | 业务架构+执行线 · `workstream/` · `PENDING.md` |
| 工程规范（workspace） | [`project-specs/`](project-specs/) | DEV-RULES · KNOWLEDGE · GLOSSARY · TROUBLESHOOTING · RESOURCES |
| 三方 / 外部 | [`external/`](external/) | SDK · 协议 · 供应商文档 |
| 归档冷库 | [`docs/features/_archive/INDEX.md`](docs/features/_archive/) | 已交付 feature(id + 描述 + zip）· 先读描述 · 必要才解压 |
| 代码（唯一真相） | `grep` + `Read` 源码 | 🔴 细节一律现查代码 · 不信文档转述 |

> 🔴 每个磁盘上存在的知识节点必在本表有一行 —— 漏一个 = 知识泄露死角。无 product-overview/external 的项目删对应行。

---

## 产品规划引用（有 product-overview/ 时）

<!-- 上游输入 · 状态同步自 product-overview 文档头部 · 仅 ✅ 已确认 才驱动下游 · 详 guide §1 -->

| 文档 | 路径 | 规划状态 |
|------|------|----------|
| 业务架构与产品规划 | 📎 [`product-overview/{项目名}_业务架构与产品规划.md`](product-overview/)（愿景 + 执行线列表） | 📝 / 🔄 / ✅ |

> Workstream（规划单元）落 `product-overview/workstream/WS-NN.md` · 无 product-overview/ 可省本章。

---

## 规划状态

<!-- 项目现状统计 = 未完成 WS（规划态·本表）+ 各子项目完成度（执行态·子项目清单）· 详 guide §2 -->

| 字段 | 值 |
|------|---|
| 状态 | ✅ 正常 |
| 当前阶段 | 初始化 / 架构规划中 / 开发中 |
| 未完成 WS | N 个（如 WS-03 📝 / WS-05 🔄）· 规划态 |
| 最近规划 | - |
| 受影响子项目 | - |

---

## 执行线概览（可选派生视图）

<!-- 权威源 = 业务架构「执行线列表」· 本表可省 · WS 向上 tag 承接执行线 · 详 guide §3 -->

| 执行线 | 使命（一句话） |
|--------|---------------|
| Line 1 · XXX | [取自业务架构执行线列表] |

---

## 项目架构全景

<!-- PL 子项目拆分方案产出 · PMO 填入 · 结构变更时 PM 更新 · 详 guide §4 -->

（Mermaid 子项目拓扑 + 依赖关系图）

---

## 项目目录结构

<!-- PMO 子项目拆分确认后生成 · 子项目直接放根下 · 文档布局遵循 conventions.md §13 · 详 guide §4 -->

```
项目根/
├── teamwork-space.md          # 本文件 — 全景入口
├── product-overview/          # 产品规划（业务架构与产品规划 + workstream/）
├── project-specs/             # workspace 级工程文档（KNOWLEDGE/GLOSSARY/TROUBLESHOOTING/RESOURCES）
├── external/                  # 三方/外部资源文档
├── {子项目A}/                  # business — 负责:{职责}。不负责:{边界}
│   ├── docs/                  # PROJECT.md + ROADMAP.md + KNOWLEDGE.md + features/ + architecture/
│   └── src/
└── {子项目B}/
```

---

## 子项目清单

<!-- 🔴 docs_root 必填（路由权威·缺失则 triage 阻断）· 技术栈前端列非空→same-stack panorama · 完成度=已完成/总数 · 详 guide §5 -->

| 缩写 | 名称 | 类型 | 职责范围 | docs_root | 承接执行线 | 技术栈 | 需要 UI | 消费方 | 完成度 | 项目详情 |
|------|------|------|----------|-----------|-----------|--------|---------|--------|--------|----------|
| AUTH | 认证服务 | business | 负责:认证/权限/Token。不负责:业务权限校验 | auth/docs/features | Line 1 | | 否 | - | 0/0 | [链接] |
| WEB | 前端应用 | business | 负责:终端 UI/交互/路由。不负责:业务规则计算 | web/docs/features | Line 1, Line 2 | React (Vite) | 是 | - | 0/0 | [链接] |
| PAY | 支付中台 | midplatform | 负责:渠道/状态/对账。不负责:订单逻辑 | pay/docs/features | Line 1 | | 否 | AUTH, WEB | 0/0 | [链接] |

> 类型:`business`（默认·服务终端用户）/ `midplatform`（服务内部消费方）。

---

## 待规划需求池

<!-- 🔴 外置:append-heavy · 不占全景索引 · 只留 1 行指针 · 详 guide §6 -->

> 🔗 **已外置** → [`product-overview/PENDING.md`](product-overview/PENDING.md)(跨 Feature/session 的"范围外但要做"项 · 按需读 · 模板 templates/pending.md)。

---

## 跨项目变更与历史

<!-- 🟢 本文件不维护变更表格 · 规划/阻塞/历史单源 = product-overview/workstream/WS-NN.md · WS 未✅规划完成禁启动其子 Feature · 详 guide §7 -->

（无表格 · 见 workstream/）
```
