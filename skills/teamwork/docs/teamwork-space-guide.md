# teamwork-space.md 维护规范(AI 读 · 非实例化内容)

> 本文件是 `teamwork-space.md` 的**维护行为规范** —— 规则 / 生命周期 / 字段语义 / 硬约束。
> 🔴 模板 [templates/teamwork-space.md](../templates/teamwork-space.md) 只放**实例化骨架**(项目里那份);本文件放"AI 怎么维护它"(不进用户项目)。
> 模板↔规则解耦:模板瘦身,规则外迁本文件,避免实例化的 teamwork-space.md 臃肿、违背它自己的"≤1 行一眼看懂"原则。

---

## 0. 核心定位 + 变更协议

- **定位**:`teamwork-space.md` 是本项目**知识地图根 / 索引之索引**(子项目结构 + 依赖 + **全部知识入口** + 跨项目追踪)· **不是**事件日志 / 进度看板 / 评审记录 · **不承担知识内容**(三层律:地图 / 领土=代码 / 冷库=归档 zip · 详 [SKILL.md § 项目级文档信息架构](../SKILL.md))。
- 🔴 **核心简化原则**:**任一表格的任一单元格 ≤ 1 行**;详情一律外迁(workstream/WS-NN.md / Feature state.json + PRD / PROJECT.md / ADR)· 永远保持"一眼看懂全景",避免演化到几百行难维护。
- 🔴 **变更协议**:任何变更(创建/修改/删除)**必须暂停等用户确认**(R5)· 本文件是 teamwork-space.md 的唯一格式权威源。
- **N≥1 统一模型**:任何 teamwork 项目都有 teamwork-space.md(知识地图根)· **单项目 = 1 个逻辑子项目**(N=1)· 子项目是**职责单元非物理仓** · 知识层与项目是否 monorepo **无直接耦合**。🟢 **已物化**:bootstrap **自动建** teamwork-space.md 骨架(`maintain_teamwork_space` · 知识入口自动探测 + 子项目清单空表)+ cold-start 解耦(gate fire 于无 `product-overview/` · 非无 teamwork-space.md)+ 结构 checker(见 §0.1)。**不再"单项目可无"**(子项目清单空表 → state.py 路由校验 SKIP · 回填后生效)。teamwork 面向复杂业务 · 地图根开销是预期。

## 0.1 § 知识入口(索引之索引 · 零死角律)

- **职责边界**:teamwork-space.md 承担**知识导航(地图)** · **不承担知识内容** —— 三层律「地图 / 领土=代码(细节唯一真相)/ 冷库=归档 zip(按需解压)」详 [SKILL.md § 项目级文档信息架构](../SKILL.md)。
- 🔴 **零死角律**:本项目**每个磁盘上存在的知识节点**必在「知识入口」表有一行指针 —— 子项目 `docs_root` / `product-overview/` / `project-specs/`(DEV-RULES·KNOWLEDGE·GLOSSARY·TROUBLESHOOTING·RESOURCES·ARCHITECTURE)/ `external/` / 归档 `{子项目}/docs/features/_archive/INDEX.md`(每子项目 docs_root 下)。漏一个 = 知识泄露死角。无对应目录的项目删该行(不留空指针)。
- **一行只写"去哪"**:指针 + 内含摘要 · **不写"是什么"**(文档*类型*语义 = 律法 · 在 SKILL.md · 不复制进项目文件 · 否则每项目背一份会腐烂的副本)。
- **末行永远是代码**:「细节 → grep+Read 源码 · 不信文档转述」· 地图不替代领土。
- 🟢 **物化校验已落**:`bootstrap.py check_knowledge_graph_integrity`(归档 `INDEX.md`↔`*.zip` 双向对账 + workspace 节点登记)· session 启动跑 · 命中 emit `checks.knowledge_graph` WARN + 截断鲁棒 digest 行。🔴 **只查可达性 · 不查内容新鲜度**(否则 checker 通过会被误读成「知识完整」· 自己成误导信号 · 违 §「信号≠判决」)。「零死角」从约定升为物化 WARN。

## 1. § 产品规划引用(有 product-overview/ 时)

- teamwork-space 的**上游输入** · 状态同步自 product-overview 文档头部规划状态表 · 🔴 仅「✅ 已确认」内容才驱动子项目规划。
- 规划状态含义:📝 初创未讨论 → 🔄 有活跃议题讨论中 → ✅ 用户确认可作执行依据。
- 🔴 执行手册已废弃(执行线移入业务架构「执行线列表」)· Workstream 落 `product-overview/workstream/WS-NN.md` · 老 `执行手册.md` 向前兼容 · 无 product-overview/ 可省本章。

## 2. § 规划状态

- 状态值:✅ 正常 / 📝 规划中 / ⏸️ 架构待确认 / 🔄 子项目 Planning 中 / ✅ 已完成。
- 当前阶段:初始化(仅引用 product-overview)→ 架构规划中(定义子项目)→ 开发中(正常运转)。
- 🔴 **项目现状统计 = 「未完成 WS」(规划态 · 本表)+ 各子项目「完成度」(执行态 BL · 子项目清单)**。WS 转 `✅ 规划完成` 即从「未完成 WS」移除(feature 转 ROADMAP 跟踪 · 不双计)。
- 🔴 **硬规则**:每槽位 ≤ 1 行。"最近规划"只写「日期 + 一句话事件 + 链 WS-NN / Feature 路径」· 多事件只保留最近一次,旧的移到 `workstream/WS-NN.md`「变更日志」段。

## 3. § 执行线概览(可选派生视图)

- 🔴 执行线**权威源 = `业务架构与产品规划.md` 的「执行线列表」(taxonomy)** · 本表是可选派生视图(嫌重复可省,直接看业务架构)。
- 执行线不反向绑定子项目 / Feature 编号 —— **WS 在自己文档 tag「承接 1+ 执行线」**,反查得映射。
- 🔴 **硬规则**:每格 ≤ 1 行,原文取自业务架构(不复述背景 / 不出现子项目缩写或 Feature 编号)。

## 4. § Workspace 架构(🔵 已外迁 → `project-specs/ARCHITECTURE.md`)

- 🔵 **外迁**:原 teamwork-space.md「项目架构全景(Mermaid 拓扑+依赖)+ 项目目录结构(tree)」两节 → `project-specs/ARCHITECTURE.md`(workspace 级)· teamwork-space.md 只在「知识入口」留 1 行指针(轻量化 · 它是偶尔读的参考详情 · 非每 session 读的导航索引)。bootstrap `maintain_project_skeletons` 自动建空骨架(模板 `templates/architecture-workspace.md`)。
- **维护**(同迁移前 · 改在 ARCHITECTURE.md):PL 子项目拆分方案产出 → PMO 填入(子项目拓扑 + 依赖)· 后续结构变更时 PM 更新。
- 🔴 **区别 per-subproject**:`project-specs/ARCHITECTURE.md` = **跨子项目**拓扑(workspace);`{子项目}/docs/architecture/` = **单子项目内部**技术架构(技术栈/分层/模块)—— 别混。
- 🔴 子项目目录直接放项目根下,不嵌套 `packages/` 等中间层。
- 🔴 **目录布局去重**:顶层知识节点(product-overview/project-specs/external/归档)**不**在 ARCHITECTURE.md 目录布局重复 —— 它们在 teamwork-space.md「知识入口」· ARCHITECTURE.md 目录只展开子项目**内部**结构。
- 🔴 文档布局遵循 [conventions.md §13](./conventions.md):workspace 级工程文档(DEV-RULES/KNOWLEDGE/GLOSSARY/TROUBLESHOOTING/RESOURCES/**ARCHITECTURE**)进 `project-specs/`(与 `product-overview/` 同级)· 顶级仓库不设 teamwork `docs/` · ROADMAP.md + 子项目 KNOWLEDGE.md 落 `{子项目}/docs/`。
- ⚠️ 决策走 ADR(`{子项目}/docs/adr/` · conventions.md §3)· 不单设 workspace 级 `decisions/`(OQ · 暂不体现)。

## 5. § 子项目清单(路由权威)

- 初始化时 PMO 从 PL 子项目拆分方案填入 · 「承接执行线」列维护子项目↔执行线映射(多值 · 执行线侧不反向记录)。
- **职责范围**:「负责:XX。不负责:YY」格式 · PMO 路由依据 · 交叉时标「与 XX 共同负责 YY」。
- 🔴 **docs_root(必填 · 路由权威)**:子项目 Feature 文档根(相对项目根)· 标准 `{子项目}/docs/features` · PMO triage 时算 `state.artifact_root = {docs_root}/{Feature 全名}` · 不允许"沿用历史根"偏离 · 缺失 → triage 阻断(用户先补)。
- 🔴 **技术栈(前端栈 = panorama 介质权威信号)**:列内前端部分(`React (Vite)`/`Vue`/`Next`)非空 → ui_design 必走 `same-stack` panorama(详 stages/ui-design-stage.md)· 仅后端/留空 → 允许 `static-html` 兜底 · 详细前端栈声明落子项目 `PROJECT.md § 技术栈·前端`(缺声明会导致介质判定死循环)。
- **消费方**:仅 midplatform 填(依赖本子项目的其他子项目缩写)· business 填 `-`。
- **完成度**:`已完成数/总数` · 基于子项目 ROADMAP feature 统计 · PMO 每 Feature 完成时同步 · 无 ROADMAP 填 `0/0`。
- 🔴 **硬规则**:任一单元格 ≤ 1 行 · 可选列只写「最近状态结论 + 链 PROJECT.md/ROADMAP.md」· 不复述 Feature 进度详情。

## 6. § 待规划需求池(🔴 已外置 → `product-overview/PENDING.md`)

- 🟢 **不再放 teamwork-space.md**:此池 append-heavy(每次跨 Feature 发现追加一行)· 违背全景索引"≤1 行 / 一眼看懂"原则 · 外置到 `product-overview/PENDING.md`(规划层 inbox)· teamwork-space 只留 1 行指针。
- 🟢 **context 收益**:不再随 session 入口 silent-read 进 PMO 上下文 · 改为 mode A query 命中 backlog 关键词时**按需读**。
- 维护规则(ID `PENDING-NNN` / 只留 active 📝🔄 / 追加触发 / 转化即删 / 每格 ≤1 行)→ 见 [templates/pending.md](../templates/pending.md) 头部(自描述)。
- mode A query 命中"待做 / 待规划 / pending / backlog / 还要做什么" → PMO 读 `product-overview/PENDING.md` 给用户(详 SKILL.md § Triage §2.1)。

## 7. § 跨项目变更与历史

- 🟢 本文件**不维护变更类表格**(结构静态描述 · 非事件日志/看板)。
- **规划/阻塞/历史单源(WS)**:
  - 🔴 活跃规划(WS · 状态/拆解/承接执行线/影响子项目/拆出 feature/launch_order/风险)→ `product-overview/workstream/WS-NN.md` frontmatter + 「变更日志」(schema 见 [templates/workstream.md](../templates/workstream.md))。
  - 🔴 当前阻塞 → 对应 `workstream/WS-NN.md`「风险与缓解」段 / 单 Feature `state.concerns`。
  - 🔴 Feature 级事件(Stage/Ship/评审)→ Feature `state.json` + `review-log.jsonl` + git log。
  - 🔴 跨 WS 回溯:`ls product-overview/workstream/*.md` / `grep -l "✅ 规划完成" product-overview/workstream/*.md`。
- **Feature → WS 反查**:ROADMAP「关联 WS」列 + Feature `state.json`。
- 🔴 **核心硬约束**:WS != `✅ 规划完成` 时禁止启动归属本 WS 的子 Feature · PMO triage 硬阻塞(留"用户明确强制启动"逃生舱)· 校验直接读 `workstream/WS-NN.md` frontmatter。老 `changes/*.md`(CHG/BG)向前兼容。

## 8. 生命周期

```
阶段 1 · 初始化(首次启动 · bootstrap 自动建 teamwork-space.md 骨架 + project-specs/ARCHITECTURE.md 空骨架)
  → 骨架知识入口自动探测 · 子项目清单/架构待规划回填 → 阶段 2
阶段 2 · 架构规划(逐个子项目 Planning 或首个 WS 落地)
  → PM 回填 teamwork-space.md 子项目清单 + project-specs/ARCHITECTURE.md(系统架构)+ 各子项目 ROADMAP → ⏸️ 用户确认 → 阶段 3
阶段 3 · 开发期(正常运转)
  → 子项目清单(teamwork-space.md)+ 系统架构(project-specs/ARCHITECTURE.md)按结构变更同步 · 变更/阻塞/事件落 workstream/WS-NN.md 或 Feature state.json · 自上而下 / 自下而上双向更新
```

---

## 相关

- 模板(实例化骨架):[templates/teamwork-space.md](../templates/teamwork-space.md)
- 规划层链路:[SKILL.md § teamwork 业务流程架构](../SKILL.md)
- WS:[templates/workstream.md](../templates/workstream.md) · [PRODUCT-OVERVIEW-INTEGRATION.md](../PRODUCT-OVERVIEW-INTEGRATION.md)
- ID / 路径:[conventions.md](./conventions.md)
