# 产品规划文档集成

> 当项目根目录存在 `product-overview/` 时，PMO/Product Lead 按以下规则按需加载上游产品文档。
> 🔴 不是每次交互都加载，只在特定场景触发。

## 冷启动:首次创建 product-overview(PL 引导模式)

> 🔴 项目**无** `product-overview/` 时(新项目冷启动)· session 启动 `bootstrap.py` emit
> `cold_start_product_planning_recommended` gate 引导**产品规划优先**(权威冷启动顺序的第一步)。
> 触发:项目缺 `product-overview/`(地图/规划解耦:地图根 `teamwork-space.md` 由 bootstrap 自动建 · 不是触发条件)· bare `/teamwork` 与 mode B execute 首条响应均 emit(详 [SKILL.md § bootstrap flow_gates 响应](SKILL.md))。

**权威冷启动顺序**(详 [SKILL.md § teamwork 业务流程架构](SKILL.md)):
`业务架构与产品规划.md`(愿景 + 执行线列表)→ ✅确认 → 派生 `teamwork-space.md` → **(涉 UI)UI 全景初步规划** → 起 WS 拆 feature → roadmap → Feature 状态机。

**PL 引导模式初创步骤**:
1. PMO 切 Product Lead 角色([roles/product-lead.md](roles/product-lead.md))
2. PL 与用户讨论 → 起草 `{项目名}_业务架构与产品规划.md`(产品定位 + 业务架构 + MVP + **执行线列表** · 按下方「建议章节 + 裁剪规则」按复杂度自适应裁剪)
3. 文档头部填「规划状态」表(初始 📝 草稿)· 末尾「规划议题追踪」表
4. 文档状态流转 📝→🔄→⏸️→✅(见下方「文档状态流转」)· 🔴 仅「✅ 已确认」内容才派生 `teamwork-space.md`
5. ✅确认后 → 派生 `teamwork-space.md`(工作区全景)→ **(涉 UI)UI 全景初步规划**(在 `{子项目}/docs/design/preview-project/` 出 design system + 关键页 + `sitemap.md` IA 地图 · 拆 WS 前先看清产品长啥样 · 详 [docs/feature-planning.md Step 5](docs/feature-planning.md))→ 起 WS(`workstream/WS-NN`)拆一组 feature → 写 roadmap

🔴 **用户拍板前不擅自建 `product-overview/`**(R5 暂停点)· 单 Feature 极简项目用户可拍板跳过、直接拆 ROADMAP。

---

## product-overview 文档规范

```
product-overview/
├── {项目名}_业务架构与产品规划.md   # 必须 · 愿景(产品定位 + 业务架构 + MVP)+ 执行线列表
├── workstream/                      # 规划单元目录(WS · 替代旧 changes/ + 执行手册的规划职责)
│   └── WS-NN-{名}.md                # 一个 Workstream · 详 templates/workstream.md
├── PENDING.md                       # 待规划需求池(跨 Feature/session 的"范围外但要做"项 · 从 teamwork-space 外置 · 详 templates/pending.md)
└── {项目名}_Product_Plan.md         # 可选 · 原始产品想法
```

**命名规则**：业务架构文档 `{项目名}_{文档类型}.md`（项目名英文，与目录名一致）；WS 文档 `WS-{三位数}-{短名}.md`。

> 🔴 `{项目名}_执行手册.md` **已废弃** —— 执行线移入 `业务架构与产品规划.md` 的「执行线列表」小节(taxonomy · 稳定);执行手册原承担的"拆一组 feature"职责由 **WS(workstream/)** 接管;非开发工作(运营/推广/BD)teamwork 不再结构化跟踪(执行线列表留个名即可)。旧 `执行手册.md` / `changes/` 老项目**向前兼容**(保留可读 · 不强迁)。

## product-overview 规划状态管理

> product-overview 有独立于 teamwork-space.md 的规划状态。
> 规划过程可能持续很长时间，涉及多个议题的多轮讨论，不确定性高。
> 只有规划状态变为「✅ 已确认」的内容才会影响 teamwork-space.md 和下游执行。

**每份 product-overview 文档头部必须包含规划状态表**：

```markdown
## 规划状态

| 字段 | 值 |
|------|---|
| 文档状态 | 📝 草稿 / 🔄 讨论中 / ⏸️ 待确认 / ✅ 已确认 |
| 最近更新 | YYYY-MM-DD |
| 待决议题 | N 项（见「规划议题追踪」） |
```

**文档状态流转**：
```
📝 草稿（Product Lead 引导模式初创 / 首次写入）
 ↓ 用户参与讨论
🔄 讨论中（有活跃的规划议题未决）
 ↓ 所有议题已决
⏸️ 待确认（Product Lead 请求用户最终确认）
 ↓ 用户确认
✅ 已确认（可作为下游执行的依据）
 ↓ 后续变更触发
🔄 讨论中（新议题打开，文档局部更新中）
```

**规划议题追踪表**（追加在每份 product-overview 文档末尾）：

```markdown
## 规划议题追踪

| 编号 | 议题 | 状态 | 结论 | 影响章节 | 日期 |
|------|------|------|------|----------|------|
| Q-001 | [议题描述] | 💬 讨论中 / ✅ 已决 / ❌ 搁置 | [结论摘要] | [章节名] | YYYY-MM-DD |
```

> 议题状态：💬 讨论中（未决）→ ✅ 已决（结论已写入文档）→ ❌ 搁置（暂不处理，记录原因）
> 当所有议题均为 ✅ 已决 或 ❌ 搁置 时，文档状态可从 🔄 讨论中 → ⏸️ 待确认

**规划状态与下游的关系**：
```
product-overview 规划状态 → 对 teamwork-space.md 的影响
────────────────────────────────────────────────────────────
📝 草稿 / 🔄 讨论中 → 不影响，teamwork-space.md 不更新
⏸️ 待确认 → 不影响，等用户最终确认
✅ 已确认 → 可以生成/更新 teamwork-space.md
✅ 已确认 → 🔄 讨论中（变更） → 已有的 teamwork-space.md 不变，
 新变更 = 新建一个 WS（workstream/）管理，
 WS 规划完成（feature 写入 roadmap）后才更新 teamwork-space.md
```

**🔴 状态管理约束**：
```
├── Product Lead 每次修改 product-overview 文档时必须同步更新规划状态表
├── 新增议题时文档状态自动回退到 🔄 讨论中
├── 只有 ✅ 已确认 状态的文档内容才能派生 teamwork-space / 起 WS
├── 处于 🔄 讨论中 的文档不阻塞已有 Feature 的开发（已确认部分仍有效）
├── 用户可以要求部分确认：某些章节已确认、某些仍在讨论
└── 部分确认时，Product Lead 在文档中标注各章节的确认状态
```

---

**业务架构与产品规划 · 建议章节**（PL 根据项目复杂度自适应裁剪）：
```
核心章节（所有项目）：
├── 规划状态（状态表，见上方）
├── 产品定位（一句话定义）
├── 业务架构（核心模块 + 角色关系 + 业务流程，建议 Mermaid 图）
├── 执行线列表（Line N：名称 + 一句话使命 · taxonomy · 稳定 · 新增执行线才更新 · 详下方）
├── MVP 范围定义
└── 待决策项（Open Questions）

扩展章节（中大型项目按需添加）：
├── 收入模型
├── 分阶段路线图（Phase 划分 + 各阶段目标）
└── 规划议题追踪（议题表，见上方）

裁剪规则：
├── 简单工具类项目 → 核心章节即可，产品定位和业务架构可合并为一段
├── 中等项目 → 核心 + 按需选择扩展章节
└── 复杂项目（多角色 / 多业务线）→ 全部章节 + PL 可追加项目特有章节
```

**执行线列表 · 写法**（在「业务架构与产品规划.md」内 · 替代旧「执行手册」）：
```markdown
## 执行线列表

| Line | 名称 | 使命（一句话） |
|------|------|---------------|
| Line 0 | 基建 | ... |
| Line 1 | 用户增长 | ... |
```
> 🔴 执行线 = 业务价值视角的「要做什么」· **不绑定子项目 / Feature 编号** · 每格 ≤1 行 · 稳定 taxonomy。
> 🔴 它**只是分类轴**：不跟踪进度、不进统计、不登记 WS。WS 在自己文档里 tag「承接 1+ 执行线」· 反查得「某执行线下有哪些 WS / feature」。
> 非开发工作（运营/推广/内容/生态）可在「使命」里点一句，但 teamwork **不结构化跟踪** —— 那是业务侧的事。
> 旧「执行手册」的"拆一组 feature"职责 → 由 **WS（`workstream/`）** 接管；里程碑/Phase → 进各 WS 或 ROADMAP Wave。

## 加载触发规则

```
PMO 判断场景 → 决定是否加载 product-overview：

📁 日常 Feature 开发（单 Feature · BL 已在 roadmap）
└── ❌ 不加载 · 正常走 Feature 流程

📋 起 WS / 规划（拆一组 feature）
├── ✅ 读「业务架构与产品规划.md」（愿景 + 执行线列表 · 确认 WS 承接哪条线）
├── ✅ 扫现有 workstream/（避免重复 · 找依赖）
└── 用途：WS 对齐执行线 → 拆 feature 写 roadmap

🔄 方向级变更（PMO 检测到需求可能影响产品方向时）→ 仍是「起一个 WS」，按级别决定要不要先动业务架构：
├── Level 1（功能级 · 在已有执行线范围）→ 直接起 WS / 加 BL · 不动业务架构
├── Level 2（业务模块级 · 影响执行线目标 / 跨线依赖）→ 切 Product Lead 评估 → 起 WS
└── Level 3（方向级 · 改产品定位 / 增删执行线 / 改核心业务流程）→ 切 Product Lead → **先更新业务架构（含执行线列表）→ ✅确认 → 再起 WS 落地**
```

## 与 teamwork 流程的映射

```
概念 → teamwork 对应机制
─────────────────────────────────────────────
执行线           → 分类轴(taxonomy) · WS 向上 tag · 不绑子项目/Feature 编号
WS(workstream/)  → 一组 feature 的规划单元(替代旧 CHG / 执行手册的拆分职责)
WS 规划完成       → feature 写入各子项目 ROADMAP(BL) · 转执行
里程碑 / Phase    → 进 WS 或 ROADMAP Wave
业务架构文档      → 规划上游愿景(WS / 执行线 对齐它)
Level 3 变更      → 先更新业务架构 → ✅确认 → 起 WS 落地
```

## 🔄 变更级联规则（方向变更 → Feature List）

> 产品方向变更后，必须逐层级联到子项目 Feature List，确保所有变更最终落地为可执行的任务。
> 🔴 级联过程中每一层都有确认暂停点，只有用户确认后才推进到下一层。

```
变更级联流程（Level 2 / Level 3）· 一个方向变更 = 一个 WS · 逐层推进 · 每层 ⏸️ 用户确认后才进下一层：

第一层 · 进 feature-planning(PMO 切 Product Lead)→ 产出 WS
├── 前提：(Level 3) 业务架构已更新 ✅确认 / (Level 2) 在已有执行线范围内
├── feature-planning 产出 workstream/WS-NN.md：背景 / 承接执行线 / 受影响子项目 / 拆哪些 feature / 跨子项目依赖 / 风险
└── ⏸️ 用户确认 WS 拆解 → WS 状态 📝 → 🔄

第二层 · 工作区架构更新（Level 3 · 增删子项目时；Level 2 跳过）
├── PM 更新 teamwork-space.md（子项目清单）+ `project-specs/ARCHITECTURE.md`（子项目拓扑/依赖 · 架构图已从 teamwork-space 外迁 · 详 [teamwork-space-guide.md §4](docs/teamwork-space-guide.md)）· 执行线列表已在业务架构 ✅确认时定
└── ⏸️ 用户确认

第三层 · feature 写入各子项目 ROADMAP（= WS 规划完成标准）
├── PM 把 WS 拆出的 feature 登记进各子项目 ROADMAP.md：🆕 新增 / ✏️ 修改 / 🗑️ 废弃 / ✅ 不受影响（明确标注）· BL 关联回 WS-NN
└── ⏸️ 每个子项目 ROADMAP 变更独立确认 → 全部写完 = WS ✅ 规划完成

第四层 · 收尾
├── WS-NN.md 记「变更日志」· teamwork-space 进度统计该 WS 转「规划完成」（从未完成 WS 计数移除）
└── ⏸️ 最终确认 → 逐个启动新增/修改的 Feature（按 WS 内 execution_waves 波次 / launch_order · prepare + init-feature）
```

**🔴 级联规则强制约束**：
```
├── 每一层完成后必须暂停等待用户确认，禁止跨层自动推进
├── 业务架构变更必须先于 teamwork-space.md 变更
├── teamwork-space.md 变更必须先于子项目 ROADMAP 变更
├── 废弃 Feature 只标记状态，不删除已有文档和代码
├── 新增 Feature 只写入 ROADMAP.md（一句话 + 验收标准 + 关联 WS），不写 PRD
└── 🔴 WS 未「规划完成」前禁止启动其子 Feature（=旧 BG locked 语义 · 防边规划边启动）
```

## 🔄 自下而上影响检测与升级（Bottom-Up Impact Escalation）

> 项目演进有两种驱动模式：
> - **自上而下（规划驱动）**：Product Lead 更新产品方向 → 级联到 Feature List（上方已定义）
> - **自下而上（迭代驱动）**：Feature 开发中发现需求超出当前层级范围 → 逐级向上反馈 → 用户确认后升级处理
>
> 🔴 自下而上的每一次升级都必须暂停等用户确认，禁止自动向上传播。· 下游：自动传播 → 用户事后发现"Feature 影响 PROJECT.md / Roadmap"· R5(a) 暂停红线违规 · 必须 rollback 重做

```
项目文档层级（从上到下）：

 product-overview/业务架构与产品规划.md ← 最上层：产品定位、业务流程、收入模型、执行线列表
 ↕
 product-overview/workstream/WS-NN.md ← 规划单元：一组 feature 的拆解(承接执行线)
 ↕
 teamwork-space.md ← 子项目架构
 ↕
 各子项目 ROADMAP.md ← Feature(BL) 清单、优先级(关联 WS)
 ↕
 各 Feature PRD/TECH/TC ← 最下层：具体功能设计与实现
```

**自下而上影响检测触发点**：

```
PM/RD 在 Feature 流程中工作时，检测到以下信号 → 标记「上游影响」：

信号 1：Feature 范围溢出
├── PRD 编写时发现需求边界不清，涉及其他子项目
├── 技术方案发现需要修改共享模块或跨子项目接口
└── → 可能影响层级：ROADMAP（同子项目其他 Feature）/ teamwork-space（跨子项目依赖）

信号 2：假设冲突
├── Feature 实现中发现与业务架构文档描述的流程不一致
├── 发现业务架构执行线列表中某执行线的目标/范围已过时
└── → 可能影响层级：业务架构（执行线）

信号 3：方向质疑
├── 用户在 Feature 讨论中提出了超出当前功能范围的新想法
├── 开发过程中发现原定方案不可行，需要产品方向调整
└── → 可能影响层级：业务架构 / 产品定位
```

**自下而上升级流程**：

```
PM/RD 检测到上游影响信号
 ↓
在当前阶段输出中标记「⚠️ 上游影响」：
├── 影响信号：[信号类型]
├── 影响描述：[具体发现]
├── 可能影响层级：[ROADMAP / teamwork-space / 业务架构(执行线)]
├── 建议：[继续当前 Feature / 暂停等待上游决策]
 ↓
⏸️ PMO 承接，暂停当前 Feature 流程
 ↓
PMO 评估影响级别：
├── 仅影响 ROADMAP（同子项目内）
│ └── → 暂停当前 Feature → ⏸️ 用户确认
│ 用户选择：调整当前 Feature 范围 / 进 feature-planning 起一个 WS 拆后续
│
├── 影响 teamwork-space（跨子项目）→ Level 2
│ └── → 暂停当前 Feature → ⏸️ 用户确认
│ 用户选择：仅调整依赖关系 / 进 feature-planning(切 Product Lead)起一个新 WS 协调跨子项目
│
└── 影响业务架构 / 执行线 / 产品定位 → Level 3
 └── → 暂停当前 Feature → ⏸️ 用户确认
 用户确认升级 → 切换 Product Lead（讨论模式）
 更新业务架构（含执行线列表）→ ✅确认 → 进 feature-planning 起 WS 落地
```

**升级后的原 Feature 处理**：
```
当 Feature 触发了上游升级后，原 Feature 的状态：
├── ⏸️ 挂起（等待上游决策）
├── PMO 记录挂起原因和关联的 WS 编号
├── 上游级联完成后，PMO 检查：
│ ├── 原 Feature 仍然有效 → 恢复流程（可能需要更新 PRD）
│ ├── 原 Feature 被修改 → 重新走 PM PRD 流程
│ ├── 原 Feature 被废弃 → PMO 输出关闭报告
│ └── ⏸️ 由用户决定
└── 🔴 禁止在上游决策完成前恢复被挂起的 Feature
```

**🔴 自下而上升级强制约束**：
```
├── 每一级升级都必须暂停等用户确认，禁止自动向上传播
├── PM/RD 只能标记「上游影响」，不能自行修改上游文档
├── PMO 只做影响级别评估，不做产品方向决策
├── 升级到 Product Lead 后，**进 feature-planning 流程**（讨论模式 · 不跳过确认）→ 产出 WS（workstream/ · 不在流程外 ad-hoc 手搓）
├── 被挂起的 Feature 必须等上游级联完成后再决定去留
├── 用户可以选择「不升级」→ 调整当前 Feature 范围在现有框架内完成
└── 「不升级」的决策也应记录在 Feature 的 PRD 中（记录为设计决策/妥协）
```
