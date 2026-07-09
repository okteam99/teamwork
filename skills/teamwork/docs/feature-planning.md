# Feature Planning · 流程指南

> **Feature Planning 不进状态机** · 由 PMO 主对话直接执行(类似问题排查 mode A)。
> `state.py init-feature --flow-type "Feature Planning"` **会被 reject** ·
> 不创建 state.json · 不分 stage · 不走 stage 链。
>
> 🔴 **进入本流程前先跑** `state.py planning-check --project-root <abs>`(物化入口)·
> emit 规划 checklist + 必读规范 + (若有 product-overview/)规划状态机。
> 治本「规划路径不进状态机 · 无 state.py 兜底 · 纯靠 AI 自觉读 spec」漏洞 —— planning-check
> 让 AI 跑命令就拿到规范要点,不依赖记得读本文件 / PRODUCT-OVERVIEW-INTEGRATION.md。

---

> 🔴 **冷启动顺序**:本流程(Feature Planning · 拆 ROADMAP)是**下游**。
> 新项目权威顺序 = `product-overview`(产品规划 · PL 引导模式 · 见 [PRODUCT-OVERVIEW-INTEGRATION.md](../PRODUCT-OVERVIEW-INTEGRATION.md))
> → ✅确认 → **派生** `teamwork-space.md`(工作区全景)→ **再**进本流程拆 ROADMAP。
>
> ⚠️ **`teamwork-space.md` 地图骨架由 bootstrap 自动建**,但**子项目清单**由 product-overview「✅ 已确认」+ 本流程**回填**
> (taxonomy genesis 在产品规划上游 · 详 [PRODUCT-OVERVIEW-INTEGRATION.md § product-overview 规划状态管理](../PRODUCT-OVERVIEW-INTEGRATION.md))。本流程 §2 Step 5「工作区级」改 teamwork-space.md
> 指的是**回填子项目清单 / 迭代**,不是建文件本身(那是 bootstrap)。冷启动若无 `product-overview/` → bootstrap emit
> `cold_start_product_planning_recommended` gate 引导先走产品规划上游(治本:已做 Feature Planning 却跳过 product-overview)。

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
- **WS**(`product-overview/workstream/WS-NN.md`)= 一块规划 → 拆一组 feature(详 [SKILL.md § teamwork 业务流程架构](../SKILL.md))
- feature 写入 **ROADMAP**(BL · 关联回 WS)· **完成标准 = feature 写进 roadmap**
- **涉 UI 时**:拆 WS 前先出 **UI 可视全景初步规划** → `{子项目}/docs/design/preview-project/`(视觉 · 系统+关键页)+ `sitemap.md`(IA 地图)
- 0-1 冷启动还含 `业务架构与产品规划.md`(愿景 + 执行线列表)

特点:
- 没有"Feature ID"(规划期分配 BL-NNN · WS 用 WS-NN · 见 [conventions.md § 4](./conventions.md))
- 没有 PRD / TC / TECH(那是 Feature 流程的事)
- 不出 **feature 实现代码**(R6 红线)· **但**产出含**全景 `preview-project`**(设计代码 · 会改文件)+ WS / ROADMAP / product-overview 文档
- 🔴 **进流程先建临时 worktree**(隔离规划产物 · 同 feature worktree 策略)—— 规划产出 committed 文档 + 全景代码,落主工作区会**污染主分支**、撞**并行 feature 基线**(主工作区是它们的 baseline)。详 §2 Step 0 + `state.py planning-check` 的 `worktree_setup`(trivial 单文档微调 · 用户可决定免 worktree)
- **不进状态机**(无 stage 链)· **但走 worktree + MR**(规划产物随 MR 原子合入 · 仅**不走 ship 状态机**)

强行套**执行层状态机**会增加复杂度而无收益(stage 链只 1 步 · 校验都是文档存在性 · PMO 主对话能直接做)· 但 worktree 隔离与状态机无关 —— 它只是文件隔离,planning 仍是「PMO 主对话直接做」,只是在 worktree 内做。

---

## 2. PMO 主对话执行流程

### Step 0 · 🔴 建临时 worktree(进流程第一步 · 隔离规划产物)

规划产出 committed 文档(WS / ROADMAP / product-overview)+ 全景 `preview-project` 代码 —— 落主工作区会污染主分支、撞并行 feature 基线。**进流程先建临时 worktree**(同 feature worktree 策略 · `state.py planning-check` 的 `worktree_setup` 给完整命令):

```bash
git fetch origin
git worktree add -b planning/<短名> <repo-root>/.worktree/planning-<短名> origin/<merge-target>
cd <worktree-path>   # 🔴 之后所有规划产物写 worktree 内路径(推荐绝对路径 · 同 worktree 纪律)
```

- `merge-target` 同 feature 默认(集成分支 · dev/staging · localconfig 默认或用户指定)· 分支用 `planning/<短名>`。
- **trivial 单文档微调**(改一行 WS / 修 typo)· 用户可决定免 worktree 直接主工作区改 —— 但涉全景 / 多文档 / 跨子项目 → 必 worktree。
- 与状态机无关:planning 仍「PMO 主对话直接做」· worktree 只是文件隔离。

### Step 1 · 加载上下文 + 🔴 实际代码调研

读 PROJECT.md(若存在 · 当前业务架构)+ ROADMAP.md(若存在 · 现有 Backlog)+ 用户需求。

🔴 **拆 BL/WS 前必须调研实际代码现状**:
- 每个候选 BL 核验「**已做什么 / 真缺口在哪**」· 拆解反映**真实完成度** —— 不把已完成的列为 todo,不把"已有脚手架"的当 greenfield;WS `features[].current_state` 记录复用点 vs 真缺口。
- 🔴 **decisive 前提必 Read 实际文件核验 · 不轻信 Explore/sub-agent 摘要** —— 摘要可能把"schema-only 空表"误报成"已有 seed 数据",让 WS 拆解基于错误前提(把已有骨架当 greenfield / 把真缺口漏掉)。"数据是否真入库 / 某能力是否真生效"这类命门事实,必看真实代码,不靠摘要。
- 🔴 **调研需 live 环境数据**(查 staging DB / log 真实状态)→ **先读 `project-specs/TROUBLESHOOTING.md` 拿连接 + 操作方式**(运维权威 · 用户主权)· 别凭 `.env` / 启动脚本瞎试。连法缺失 → 补进 TROUBLESHOOTING.md。

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

### Step 4 ·(条件)起草/更新 PROJECT.md 业务架构

仅 **Level 2/3 或新增子项目**时 · §业务架构 + §执行线对齐 + §关键决策 · PL(Product Lead)主导。Level 1 跳过。模板见 [templates/project.md](../templates/project.md)。

### Step 5 · 🎨 UI 全景初步规划(条件:本轮涉 UI · 否则跳过)

🔴 **在拆 WS 之前出** —— 先看清"产品长啥样",WS 才能把 feature 切对(边界跟 UI 结构对齐)。对**本轮 scope 做一次**(不是 per-WS 各画),在 `{子项目}/docs/design/preview-project/`:
- **出 design system + 本轮关键页**(🔴 **初步**:系统 + 代表页 · **不是每页** · 细节随各 feature 的 ui_design 增量补 · 防瀑布)· 🔴 seed 即按**真实路由结构**组织(router 必含 · `/` = 首页设计稿 · 各页挂真实 path · 与 sitemap 一致 · 详 ui-design-stage § IA 镜像律)· 基建层优先依赖真实 app 的**共享包**(packages/ui · theme · shell · 详 ui-design-stage § 分层同构律)· 跑 `preview.sh` 实时看(同 ui_design 同栈机制)。
- 同步 `sitemap.md`(IA 地图:本轮新增/调整的页节点 · 🔴 **只写层级/导航/路由,不写视觉** —— 视觉在 preview-project · 防双副本漂移)。
- 🔴 全景是**一份活物**:不存在 → 首次 seed;已存在 → 扩本轮的页(源即权威)。完成即产生 git diff(= 本轮全景产出 · 下一步拆 WS 的输入)。
- **非 UI 轮**(纯后端/基建)→ 跳过此步 · 下游 WS 标 `全景初规: N-A`。

🔴 **全景用户确认暂停点(涉 UI 必经 · R5 · 拆 WS 前)**:全景初步规划出完 → **给用户可访问的预览 URL** + 等用户确认,**不能 AI 自己说"全景 ok"就往下拆**:
- 后台跑 `bash {子项目}/docs/design/preview-project/preview.sh` → 抓早期 stdout 的 `PREVIEW_URL=` 行 → 把 **URL 给用户**(根 `/` = 首页设计稿 · 多页给关键页直达清单 · dev server 实时 · 动态端口 · 同 ui_design 机制)。
- emit R5 标准暂停点:
```
⏸️ UI 全景初步规划已出 · 预览:<PREVIEW_URL>(根 + 关键页直达 <route>)· 请确认是否符合预期:
1. 确认全景 · 据此拆 WS 💡 推荐 —— design system + 关键页符合预期
2. 要改全景 —— {改 design system / 页结构 / 关键页}后重出预览再确认
3. 其他指示
```
- 🔴 **用户确认后**才在下游 WS frontmatter 记 `ui_panorama_confirmed: <ISO 用户确认时间>` · **未确认不得拆 WS、更不得转 `✅ 规划完成`**(见 Step 9 + 完成标准)。
- 🔴 **`auto_mode=true` / yolo 跳过此暂停点**(用户已委托)· 但必 `state.py add-concern --severity WARN --message "auto skip: 全景确认 · preview <url>"` 留 audit + 仍记 `ui_panorama_confirmed`(标 auto)· 详 [SKILL.md § auto_mode 暂停点](../SKILL.md)。

### Step 6 · 拆 WS(🔴 核心产出 · `workstream/WS-NN.md` · 1 或多个)

**输入 = 本轮全景产出(Step 5 的 diff)+ 业务目标 + 承接执行线** · 把 scope 切成 **1..N 个 WS**:
- 每个 WS:背景 / 承接 1+ 执行线 / 拆哪些 feature(`features[].current_state` 记复用点 vs 真缺口)/ 跨子项目依赖 / 风险。
- 🔴 每个 WS 记 **全景初规状态**(`✅` 本 WS 的页已在全景 / `N-A` 非 UI)+ **覆盖的全景页清单**(本 WS owns 哪几页 · 替代模糊的"哪一轮")+ 🔴 **`ui_panorama_confirmed`**(Step 5 用户确认全景后填 ISO 时间 · 涉 UI 必有才能规划完成 · 非 UI 留 `N-A`)。
- **WS 是原子单位**:scope 大(如冷启动 MVP)就按执行线/能力拆**多个** WS(各自独立状态/启动)· 别塞巨型 WS;稳态一个方向变更 = 一个 WS。
- 🔴 **给执行顺序与并行建议**:拆完按 `features[].dependencies` 算**波次**(同波互不依赖 → 可并行 · 各自 worktree;跨波串行)写进 WS §执行顺序与并行建议 + frontmatter `execution_waves` · 并标 **同改面 / 跨子项目方向 / 带宽** 的额外串行约束 —— 让用户拿到 WS 就知道先起哪几个、能同时开几个。
- 🔴 **照 [templates/workstream.md](../templates/workstream.md) 起草 · 别抄项目里现有 WS**(易抄到旧/混合格式):最新形态 = `<!-- TEAMWORK-MACHINE -->` 注释块(非裸 `---`)+ `WS-PROGRESS`/`WS-DAG` 标记区 + frontmatter 含 `ui_panorama_confirmed`。
- 🔴 **写完每个 WS 跑 `state.py ws-lint --ws WS-NN` 校验符合最新模板**(NONCONFORMANT → 按缺项补)· 再跑 `ws-progress --ws WS-NN --write` 填进度/DAG。不跑校验 → 抄旧格式无人检查 · 只有用户问才发现。

### Step 7 · 写 ROADMAP.md(BL-NNN 分配)

🔴 **位置 = `docs/ROADMAP.md`(单项目根 · 即 repo 根的 `docs/` 下)/ `{子项目}/docs/ROADMAP.md`(多项目)** —— **不在项目根裸放**(照 [templates/roadmap.md](../templates/roadmap.md) 头部「位置：」· 单源)。

Feature 列表 + 优先级 + 排期(当前/下一/储备)。
- **每个 Backlog 分配 BL-NNN**(三位数字 · 各项目独立递增)· 详见 [conventions.md § 4](./conventions.md)
- **不分配 F-NNN**(F-NNN 在 Feature 流程启动时由 PMO 在 init-feature 时分配)
- 不细化到 task 级 · 一 Feature 一行(标题 + 优先级 + 状态 + 核心 AC ①②③)
- **BL 关联回 WS-NN**(ROADMAP 加「关联 WS」列)· 这一组 feature 全写进 ROADMAP = 对应 WS「规划完成」
- 🔴 **涉 UI 的 WS 转「✅ 规划完成」硬前提**:`ui_panorama: ✅` **且** `ui_panorama_confirmed` 已填(Step 5 用户确认过全景)—— **用户没确认过全景 = 不算规划完成**(光「页在 preview-project」不够,得用户看过预览 URL 拍板)。非 UI WS(`N-A`)直接放行。
- 🔴 **首刷 WS 进度块**:写完 ROADMAP(含「关联 WS」列)后跑 `state.py ws-progress --ws WS-NN --write` —— WS 的 §feature 总览即按 ROADMAP「状态」列**派生**出进度(规划完成时全「待开始」)· 之后 ship 翻 BL 牌时自动再刷(职责单一:WS 不手抄执行态)。

模板见 [templates/roadmap.md](../templates/roadmap.md)。

### Step 8 · PL-PM 讨论 + 多角色 review

PL 把方向 · PM 把可执行性 · Architect 把技术可行。
PMO 主对话切换角色 · 讨论收敛 · 不需要单独 review artifact。

### Step 9 · 提交 + 收尾(规划收尾 · 🔴 R5 暂停点 · 必问)

规划产出(WS + 各 ROADMAP 登记 + preview-project/sitemap if 涉 UI + 业务架构 if 改)是 **Step 0 worktree 内未提交的改动**。规划完成 → **必 emit R5 暂停点问用户如何收尾** —— 不擅自 commit / 合并,也不放任改动悬着。🔴 **头两项 = 一步到位**(治本 case:用户被迫手动「你直接合并然后规划收尾」· 收尾不该是「建 MR → 等你告知已合并 → 再收尾」的多段接力):

```
⏸️ 规划完成 · 产出 <WS-NN + N 个 ROADMAP 登记 + 全景 if UI> · 合入 <merge_target> 收尾?
1. 确认 · 合入 MR + 收尾规划 💡 推荐 —— 我 commit + push + 开 MR + **自动合并** + 清 worktree + 净化主分支(一步到位)
2. 确认 · 合入收尾 + 启动首个 BL <BL-xxx> —— 同 1 · 收尾完直接 prepare 首波 ready BL(execution_waves W1)进 Feature 流
3. 建 MR · 我自己平台 review 再合 —— commit + push + 开 MR → 你平台合(或我 `await-merge` 30s 轮询)→ 合后收尾
4. 先不提交(继续调整 / 你稍后自己提)
5. 其他指示
```

🔴 **自动合并硬门(选 1 / 2)**:仅当 `merge_target` **非主分支**(main / master)—— 规划 MR 走**集成分支**(dev/staging)· 纯文档/全景 · 低风险 · 同 yolo「自动合入只进非主分支」风险模型。主分支 / 平台要求审批或 CI 门 / 合并命令被拒 → **自动回退选项 3**(surface + 转人工合)· 绝不 force。

**【收尾执行 · commit → 开 MR →(选 1/2)自动合 /(选 3)等合 → finalize】**(= feature ship1+ship2 合流):

1. **建 MR**(= ship1):**Step 0 worktree 内** `git add` 规划产物 + commit + push planning 分支 + 开 MR(`gh`/`glab` CLI-first · 🔴 **target = `merge_target`**〔集成分支〕· 不走 ship 状态机 · 纯文档/全景 MR)。
2. **合并**:
   - **选 1/2** → `gh pr merge` / `glab mr merge`(🔴 非主分支硬门)· 成功即进 finalize;被平台拒(审批/CI/保护)→ 回退选项 3 并 surface 原因。
   - **选 3** → ⏸️ 给 `<MR URL>` · 用户平台合(或 `state.py await-merge --mr-url <URL>` 30s 轮询 · 合并自动续)→ 合后进 finalize。
3. **finalize**(= ship2 / ship-finalize · 3 步镜像):① `cd <主工作区路径>`(非 planning worktree)② `git worktree remove <planning-worktree-path>`(删不掉 `--force` 兜底)③ `python3 {SKILL_ROOT}/tools/state.py main-sync --merge-target <merge_target>`(不依赖 feature · fetch + 按策略 pull · 主工作区有用户改动会 surface 净化决策)。
4. **选 2 追加 · 启动首个 BL**:finalize 完 → 首波 ready BL(`<BL-xxx>` · 取 WS `execution_waves` W1 / `ws-progress` 的 `ready_to_start`)→ prepare → init-feature 进 Feature 状态机。

🔴 **启动首个 BL 的前提(选 2 · 守 v8.188 护栏)**:必须 **finalize 完成后**(集成分支基线**已含规划产物**)· 且是**用户显式选择**(非自动起)· 该 feature 的 `merge_target` = **集成分支**(dev/staging · **不是 planning 分支**)—— 「别叠 feature 在未合并 planning 分支」仍成立(规划已合入 · planning 分支已消亡)。选 1/3 收尾后拆出的 BL 同样由用户后续拍板再 prepare。

---

### Step 10 · 规划后变更(WS ✅ 规划完成之后)

规划完成 ≠ 冻结,但也不是随便改 —— 按变更性质分两路:

- **追加 feature(轻量 · 不重开全流程)**:R5 一句确认 → 在 Step 0 同款临时 worktree 内:WS 名册 `features[]` 加条目 + §拆出的 feature 补节 + §变更日志 +1 行 + ROADMAP 登记 BL(关联 WS)→ `ws-lint` + `ws-progress --write` 刷新 → commit + MR(同 Step 9 收尾)。
- **砍 feature / 改方向 / 动拆解边界**:影响拆解结构 → **回 feature-planning**(Step 1 调研起 · WS 状态回 `🔄 讨论中` · 重走确认)。
- 🔴 **已启动(F 已 init)的 feature 不在此列** —— 那是执行层变更(jump-to-stage / close-unmerged / 新 Bug 流),别用规划变更掩盖执行返工。

## 3. 注意事项

### 坑 1 · R6 红线 · Planning 出代码

Planning 流程中起草 PRD / 写代码 = 违 R6。

**对策**:Planning 产规划文档(WS-NN + ROADMAP + 涉 UI 时 preview-project/sitemap + 业务架构 if 改)· 🔴 不出代码(R6)· 想做某个 Feature → 走 Feature 流程(`init-feature --flow-type Feature` 启动新 session)。

### 坑 2 · PROJECT.md 业务架构 vs 技术架构混淆

把"用什么数据库"写进业务架构 · 应在 ARCHITECTURE.md。

**对策**:业务架构 = 业务能力 / 服务边界 · 技术架构 = 系统设计 · 各归各处。

### 坑 3 · ROADMAP 细化到 task 级

task 是 Feature 内 PRD 的事 · ROADMAP 只到 Feature 名 + 简述。

**对策**:ROADMAP 一 Feature 一行 · 标题 + 优先级 + 状态。

### 坑 4 · sitemap / 可视全景 / 单 Feature UI.md 三者分工

**对策**:三者各司其职 · 不重叠:
- `sitemap.md` = **IA 地图**(页面层级 / 导航 / 路由 · 文字 · 🔴 不写视觉 —— 防与全景漂移)
- `preview-project/` = **视觉权威**(design system + 页面 · 可跑)
- 单 Feature `UI.md` = 本 Feature 涉及的页(不重复全局)

### 坑 5 · Planning 完成自动启 Feature

PL 在 ROADMAP 拆完后顺手起 Feature flow · 越权(用户没拍板)。

**对策**:Planning 完成 = git push 项目级文档 · Feature 启动需用户主动跑 `/teamwork <feature>` 新 session。

### 坑 6 · 想跑 state.py planning-start

会 BLOCKED · `planning` stage 已删除(规划层不进状态机)。
若用户/AI 不知道还跑 `init-feature --flow-type "Feature Planning"`,会被 state.py reject + emit hint 指向本文件。

---

## 4. 产出形态参考

### `product-overview/workstream/WS-NN-XXX.md`(核心产出 · 1 或多个)
背景 + 怎么落 + 拆哪些 feature + 跨哪些子项目 + 承接 1+ 执行线 + **全景初规状态(✅/N-A)+ 覆盖的全景页清单** · 完成 = feature 写入 roadmap · 详 [templates/workstream.md](../templates/workstream.md)

### `{子项目}/docs/design/preview-project/`(涉 UI 时 · UI 可视全景初步规划)
design system + 本轮关键页(初步 · 系统+代表页 · 同栈可跑 · 源即视觉权威)· ui_design 后续增量扩

### `sitemap.md`(涉 UI 时 · IA 地图)
页面层级 / 导航 / 路由(文字 · 🔴 不写视觉 · 视觉在 preview-project)

### `ROADMAP.md`(各子项目)
Feature(BL)列表 + 优先级 + 「关联 WS」列 · 一 Feature 一行

### `业务架构与产品规划.md` / `PROJECT.md`(0-1 / 方向级变更时)
产品定位 + 业务架构 + 执行线列表(taxonomy)+ 关键决策

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

- [SKILL.md § Triage 入口规范 · 5 mode 分诊](../SKILL.md) — 流程类型识别(Feature Planning 关键词命中)
- [docs/prepare.md](./prepare.md) — 进状态机前的准备子流程(启 Feature 时走)
- [FLOWS.md § Feature Planning](../FLOWS.md) — telos
- [conventions.md § 4](./conventions.md) — BL ↔ F 编号
- [roles/product-lead.md](../roles/product-lead.md) — PL 角色规范
- [templates/project.md](../templates/project.md) / [templates/roadmap.md](../templates/roadmap.md) — 文档模板
