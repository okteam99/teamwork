# Feature Planning · 流程指南

> **Feature Planning 不进状态机** · 由 PMO 主对话直接执行(类似问题排查 mode A)。
> `state.py init-feature --flow-type "Feature Planning"` **会被 reject** ·
> 不创建 state.json · 不分 stage · 不走 stage 链。
>
> 🔴 **进入本流程前先跑** `state.py planning-check --project-root <abs>`(v8.46 物化入口)·
> emit 规划 checklist + 必读规范 + (若有 product-overview/)规划状态机。
> 治本「规划路径不进状态机 · 无 state.py 兜底 · 纯靠 AI 自觉读 spec」漏洞 —— planning-check
> 让 AI 跑命令就拿到规范要点,不依赖记得读本文件 / PRODUCT-OVERVIEW-INTEGRATION.md。

---

> 🔴 **冷启动顺序(v8.48 · 治本 gcpdev case)**:本流程(Feature Planning · 拆 ROADMAP)是**下游**。
> 新项目权威顺序 = `product-overview`(产品规划 · PL 引导模式 · 见 [PRODUCT-OVERVIEW-INTEGRATION.md](../PRODUCT-OVERVIEW-INTEGRATION.md))
> → ✅确认 → **派生** `teamwork-space.md`(工作区全景)→ **再**进本流程拆 ROADMAP。
>
> ⚠️ **`teamwork-space.md` 不是本流程产出的** —— 它由 product-overview「✅ 已确认」内容派生(genesis 在产品规划上游 ·
> PRODUCT-OVERVIEW-INTEGRATION.md:67)。本流程 §2 Step 5「工作区级」改 teamwork-space.md 指的是**已存在后的迭代**,
> 不是首次 genesis。冷启动若无 product-overview/teamwork-space → bootstrap emit `cold_start_workspace_uninitialized`
> gate 引导先走产品规划上游(治本:已做 Feature Planning 却跳过 product-overview + teamwork-space.md)。

---

## 0. 何时进入此流程(入口判据)

**关键词触发**:用户说"规划 / 拆 roadmap / 路线图 / 全景 / 商业模式调整 / 做电商 / 做 SaaS"等(详 [prepare.md §2 关键词表](./prepare.md))。

**复杂度触发**(关键词命中 Feature/敏捷需求/Micro 时 PMO 必再扫 · 详 [prepare.md §2.1](./prepare.md)):
- 跨仓库联动(≥2 个 · 如后端 + 前端 + 管理后台)
- 数据模型重构(删/改老字段 / 表结构变动)
- 老需求架构性废弃("X 不要了"/"统一为 Y"/"重构这套逻辑")
- 影响 ≥2 BL(一次需求拆成多 Feature 协同)
- 方向级业务变更(新增/删除业务能力)

🔴 **命中任一 = 强制升级**(不论关键词初判)· 否则会 PMO 主对话散述伪 PRD(违 R5 暂停点协议)。

---

## 1. 为什么不进状态机

Feature Planning 的产出是**规划文档**(不是单 Feature 的 artifact)· 核心是 **WS**:
- 🔴 **WS 是本流程的产物** —— "起一个 WS" = 进 feature-planning(PMO 切 Product Lead 引导/讨论)· **不在流程外 ad-hoc 创建 WS**
- **WS**(`product-overview/workstream/WS-NN.md`)= 一块规划 → 拆一组 feature(v8.49 · 详 [SKILL.md § teamwork 业务流程架构](../SKILL.md))
- feature 写入 **ROADMAP**(BL · 关联回 WS)· **完成标准 = feature 写进 roadmap**
- 0-1 冷启动时还含 `业务架构与产品规划.md`(愿景 + 执行线列表)/ `sitemap.md`(信息架构)

特点:
- 没有"Feature ID"(规划期分配 BL-NNN · WS 用 WS-NN · 见 [conventions.md § 4](./conventions.md))
- 没有 PRD / TC / TECH(那是 Feature 流程的事)
- 不出代码(R6 红线)
- 不需要 worktree(在主工作区写文档即可 · 用户决定是否 worktree)
- 不需要 ship 流程(项目级文档直接 commit + push 或开 MR)

强行套状态机会增加复杂度而无收益(stage 链只 1 步 · 校验都是文档存在性 · PMO 主对话能直接做)。

---

## 2. PMO 主对话执行流程

### Step 1 · 加载上下文 + 🔴 实际代码调研

读 PROJECT.md(若存在 · 当前业务架构)+ ROADMAP.md(若存在 · 现有 Backlog)+ 用户需求。

🔴 **拆 BL/WS 前必须调研实际代码现状**(治本 · AON category case 2026-05-29):
- 每个候选 BL 核验「**已做什么 / 真缺口在哪**」· 拆解反映**真实完成度** —— 不把已完成的列为 todo,不把"已有脚手架"的当 greenfield;WS `features[].current_state` 记录复用点 vs 真缺口。
- 🔴 **decisive 前提必 Read 实际文件核验 · 不轻信 Explore/sub-agent 摘要**。实证:Explore 误报"migration 含 11 条 seed INSERT" · 实际 schema-only(表为空)· 差点让 WS 拆解基于错前提("建接口" → 实际接口骨架已有、真缺口是 seed 数据 + DB 校验)。"数据是否真入库 / 某能力是否真生效"这类命门事实,必看真实代码,不靠摘要。
- 🔴 **调研需 live 环境数据**(查 staging DB / log 真实状态)→ **先读 `project-specs/TROUBLESHOOTING.md` 拿连接 + 操作方式**(运维权威 · 用户主权)· 别凭 `.env` / 启动脚本瞎试(实证 AON:连法 TROUBLESHOOTING.md 早有定义,AI 却 grep `.env`/`dev_start.sh` 试错 + psql 报错)。连法缺失 → 补进 TROUBLESHOOTING.md。

### Step 2 · 范围判定

| 触发 | 范围 |
|---|---|
| 涉及新增/删除/合并子项目 / 多项目职责调整 / 整体架构迁移 | **工作区级** · 改 teamwork-space.md + 多个 PROJECT.md |
| 单子项目内 Feature 拆分 / 单 PROJECT.md 内迭代 | **子项目级** · 改 PROJECT.md + ROADMAP.md + sitemap.md |

### Step 3 · Level 判定(配合 product-overview/ · 可选)

若项目根有 `product-overview/` 目录:

| Level | 触发 | 处理 |
|---|---|---|
| 1 | 功能级 · 不改方向 / 不动业务架构 | 直接进 Step 4 起草 |
| 2 | 业务模块级 · 影响执行线目标 / 跨线依赖 | 先 PL 评估 product-overview 影响 → 再起草 |
| 3 | 方向级 · 产品定位 / 核心业务流程变更 | PL 主导重构 product-overview → 再起草 |

无 product-overview/ → 跳过 Level 判定 · 直接进 Step 4。

### Step 4 · 起草 PROJECT.md

§业务架构 + §执行线列表 + §关键决策 · PL(Product Lead)主导。

模板见 [templates/project.md](../templates/project.md)。

### Step 5 · 起草 ROADMAP.md(BL-NNN 分配)

Feature 列表 + 优先级 + 排期(当前/下一/储备)。
- **每个 Backlog 分配 BL-NNN**(三位数字 · 各项目独立递增)· 详见 [conventions.md § 4](./conventions.md)
- **不分配 F-NNN**(F-NNN 在 Feature 流程启动时由 PMO 在 init-feature 时分配)
- 不细化到 task 级 · 一 Feature 一行(标题 + 优先级 + 状态 + 核心 AC ①②③)
- **BL 关联回 WS-NN**(ROADMAP 加「关联 WS」列)· 这一组 feature 全写进 ROADMAP = 对应 WS「规划完成」(v8.49)

模板见 [templates/roadmap.md](../templates/roadmap.md)。

### Step 6 · 起草 sitemap.md

信息架构 · 页面层级 · 模块边界(整体页面架构 · 不重复单 Feature UI.md)。

### Step 7 · PL-PM 讨论 + 多角色 review

PL 把方向 · PM 把可执行性 · Architect 把技术可行。
PMO 主对话切换角色 · 讨论收敛 · 不需要单独 review artifact。

### Step 8 · 提交(🔴 R5 暂停点 · 必问)

规划产出(WS + 各 ROADMAP 登记 + 业务架构 if 改)是**未提交的工作树改动**。规划完成时**必 emit R5 暂停点问用户是否提交 push** —— 不擅自 commit,也不放任改动悬着不提:

```
⏸️ 规划完成 · 产出 <WS-NN + N 个 ROADMAP 登记 + …> · 请选择:
1. 提交并 push(commit + 直推 / 开 MR)💡 推荐 —— 规划文档落库,后续启动 Feature 有据
2. 先不提交(继续调整 / 你稍后自己提)
3. 其他指示
```

🔴 在**主工作区**提交(Feature Planning 不进 worktree)· 推到当前分支(直推或开 MR · 用户决定)· 不走 ship 流程。
完成 · 不需要 state.json / state.py 命令。

---

## 3. 注意事项

### 坑 1 · R6 红线 · Planning 出代码

Planning 流程中起草 PRD / 写代码 = 违 R6。

**对策**:Planning 只产 3 个文档(PROJECT/ROADMAP/sitemap)· 想做某个 Feature → 走 Feature 流程(`init-feature --flow-type Feature` 启动新 session)。

### 坑 2 · PROJECT.md 业务架构 vs 技术架构混淆

把"用什么数据库"写进业务架构 · 应在 ARCHITECTURE.md。

**对策**:业务架构 = 业务能力 / 服务边界 · 技术架构 = 系统设计 · 各归各处。

### 坑 3 · ROADMAP 细化到 task 级

task 是 Feature 内 PRD 的事 · ROADMAP 只到 Feature 名 + 简述。

**对策**:ROADMAP 一 Feature 一行 · 标题 + 优先级 + 状态。

### 坑 4 · sitemap 与单 Feature UI.md 重复

两处同步成本高。

**对策**:sitemap = 整体页面架构 · 单 Feature UI.md = 本 Feature 涉及的页面 · 后者不重复全局。

### 坑 5 · Planning 完成自动启 Feature

PL 在 ROADMAP 拆完后顺手起 Feature flow · 越权(用户没拍板)。

**对策**:Planning 完成 = git push 项目级文档 · Feature 启动需用户主动跑 `/teamwork <feature>` 新 session。

### 坑 6 · 想跑 state.py planning-start

会 BLOCKED · `planning` stage 已删(v8.x)。
若用户/AI 不知道还跑 `init-feature --flow-type "Feature Planning"`,会被 state.py reject + emit hint 指向本文件。

---

## 4. 产出形态参考

### `product-overview/workstream/WS-NN-XXX.md`(核心产出 · v8.49)
背景 + 怎么落 + 拆哪些 feature + 跨哪些子项目 + 承接 1+ 执行线 · 完成 = feature 写入 roadmap · 详 [templates/workstream.md](../templates/workstream.md)

### `ROADMAP.md`(各子项目)
Feature(BL)列表 + 优先级 + 「关联 WS」列 · 一 Feature 一行

### `业务架构与产品规划.md` / `PROJECT.md`(0-1 / 方向级变更时)
产品定位 + 业务架构 + 执行线列表(taxonomy)+ 关键决策

### `sitemap.md`(含 UI 时)
信息架构 · 页面层级

---

## 5. 与 Feature 流程的接口

Planning 完成后,某个 BL-NNN 启动开发(同 session · 不需要重新 triage):

```
PMO(主对话):
  → 用户拍板 "启动 BL-007"
  → PMO 走 prepare 子流程([docs/prepare.md](./prepare.md))
    · flow_type = Feature(默认 · BL 已经决定"做什么")
    · 收集 Feature ID(从 BL 推 · 如 BL-007 → PTR-F042-<name>)
    · 收集 worktree path / branch / merge_target(暂停点)
    · 用户确认 → PMO 跑 git worktree add + cd
  → state.py init-feature --flow-type Feature --feature-id <PROJ>-F<NNN>-<name> ...
  → ROADMAP 同步「对应 F编号」列(由 PMO 在 Feature 启动时回填 · 详 conventions.md § 4)
  → 进 goal stage 起 PRD ...
```

prepare 是可重入子流程 · 同 session 中 PMO 走过 triage(mode E discuss),启动 Feature 时不再 triage,直接进 prepare。

BL ↔ F 编号映射规则见 [conventions.md § 4](./conventions.md)。

---

## 6. 相关

- [SKILL.md § Triage 入口规范 § 4.1](../SKILL.md) — 流程类型识别(Feature Planning 关键词命中)
- [docs/prepare.md](./prepare.md) — 进状态机前的准备子流程(启 Feature 时走)
- [FLOWS.md § Feature Planning](../FLOWS.md) — telos
- [conventions.md § 4](./conventions.md) — BL ↔ F 编号
- [roles/product-lead.md](../roles/product-lead.md) — PL 角色规范
- [templates/project.md](../templates/project.md) / [templates/roadmap.md](../templates/roadmap.md) — 文档模板
