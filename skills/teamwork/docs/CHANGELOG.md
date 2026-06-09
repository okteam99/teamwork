# Changelog

> 📦 v8.113 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**保留最近 5 版**(每次发布:新增本版 → 若超过 5 版,把最旧的一版迁入归档)。

## v8.118 · 修文档不准:归档路径 `docs/features/_archive` → `{子项目}/docs/features/_archive`(子项目根)

> 用户:`docs/features/_archive/` 描述不准确 · 应该是 子项目root/docs/features。

### 诊断:对(代码=真相)· v8.114–116 pointer 把归档写成顶层 · 实际在 per-subproject `docs_root` 下
- 真相 = `_v8_ship._archive_repo_paths`:`index_rel = {子项目 docs_root}/_archive/INDEX.md`(`features 根 git show-prefix`)· `test_ship_archive_v882` 实测断言 `svc/docs/features/_archive/INDEX.md`。`docs/features/_archive/` 只是 **N=1 单项目**(代码在 repo 根)的退化形 —— 多子项目(teamwork 主场)每子项目各有归档。

### 改动(doc 准确性 · **无行为变更**)
- 修 pointer text `docs/features/_archive/INDEX.md` → `{子项目}/docs/features/_archive/INDEX.md`(每子项目 docs_root):SKILL 路由表 2 行 · `teamwork-space.md` 知识入口 · guide §0.1 零死角律 · `architecture-workspace.md` 节点列 · bootstrap skeleton 知识入口行。
- `_v8_ship.py` 归档路径 docstring:澄清 prefix = 子项目 docs_root(如 `svc/docs/features`)· `docs/features/_archive/` 标「单项目=repo 根」。
- **不动**:checker `_find_archive_dirs` 本就 glob 两态(top-level + `*/docs/features/_archive`)· N=1 测试 fixture(单项目布局 · valid)。

### 验证
- pytest **3 failed / 519 passed**(baseline 3 = scan-spec 既有 · 零回归 · 纯文案)。

## v8.117 · teamwork-space.md 瘦身:架构全景 + 目录结构外迁 → `project-specs/ARCHITECTURE.md`

> 用户:teamwork-space.md 架构全景的内容是否有必要拆出 · 作为 project-specs/ 下一个约定文档 · 把 teamwork-space.md 做轻。

### 判断:该拆 —— 它是「参考详情」不是「导航索引」
- guide §0 自定「单元格 ≤ 1 行 · 详情外迁」· 而 架构全景(Mermaid 拓扑+依赖)+ 目录结构(tree)是文件里**唯二多行重内容**(偶尔读的参考 · 非每 session 读的导航)。且 v8.116 自动建骨架本就**没放**它们 → 拆出顺势让**模板与骨架对齐**。

### 改动(doc + bootstrap)
- **新 `templates/architecture-workspace.md`**(实例化 `project-specs/ARCHITECTURE.md`):**workspace 级** · 子项目拓扑 + 依赖 + 目录布局 · 🔴 区别 per-subproject `{子项目}/docs/architecture/`(**单子项目内部**技术架构)。
- **`templates/teamwork-space.md`**:删「项目架构全景 + 项目目录结构」两节 · 「知识入口」加「系统架构」1 行指针(零死角:进知识图谱节点 · v8.115 checker 校验)。
- **`bootstrap.py`**:`maintain_project_skeletons` 加 `ARCHITECTURE.md`(自动建空骨架)· `_kg_entry_rows` 探测 `project-specs/ARCHITECTURE.md` → 自动建的 teamwork-space.md 骨架含「系统架构」行。
- **去重**:ARCHITECTURE.md 目录布局**不**重复顶层知识节点(它们在知识入口)· 只展开子项目**内部**结构。
- **spec 同步**:guide §4(外迁说明+维护)+ §8(生命周期)· conventions §13(project-specs 加 ARCHITECTURE)· SKILL 路由表(workspace vs subproject 架构两行)· `templates/README`(注册新模板)。

### 验证
- 更新 3 测(skeletons created/existed 加 ARCHITECTURE · fixture 加 `architecture-workspace.md` 模板)+ auto-create 测加「系统架构」断言 · E2E 验证 ARCHITECTURE 自动建 + 骨架探测到。
- pytest **3 failed / 519 passed**(baseline 3 = scan-spec 既有 · 零回归)。

## v8.116 · N≥1 物化:bootstrap 自动建 teamwork-space.md + cold-start 解耦(地图 ≠ 规划)

> 用户:单项目自动建 teamwork-space.md 符合预期 · 没必要兼容(单项目可无)· teamwork 是为复杂业务准备的。承 v8.115 arc 余项。

### 改动(bootstrap-only · **无 state.py 改动**)
- **`maintain_teamwork_space`(`bootstrap.py`)**:teamwork-space.md 缺失 → 自动建**精简骨架** —— 知识入口表**自动探测**(仅磁盘存在的节点:product-overview / project-specs / external / 归档冷库)+ 子项目清单**空表待规划回填**。幂等(已存在不动)。N≥1:任何项目(含单项目=1 子项目)都有地图根 · **不再"单项目可无"**。
- **cold-start 解耦**:teamwork-space.md(地图)自动建后,原 `cold_start_workspace_uninitialized`(fire 于无 teamwork-space.md)若不改则**永不触发** → 产品规划 nudge 静默消失。改为 `cold_start_product_planning_recommended`(fire 于无 **product-overview**)· 保留规划引导(reframe:地图自动建 · 规划要人建)· 承 v8.48「产品规划优先」。
- **路由零改动**:骨架子项目清单**空表** → state.py `_parse_workspace_registry` 返回 `{}` → 路由校验 SKIP(line 661)· 回填子项目行后才生效 · 不误阻断。
- **spec 同步**:`SKILL.md` triage cold-start 段(gate 改名 + 地图/规划解耦 + N≥1)· `feature-planning.md`(teamwork-space.md 地图骨架自动建 · 子项目清单回填)· guide §0(去「过渡期单项目仍可无」→ 已物化)。

### 验证
- 重写 3 cold-start 测(gate 改名 + 新 condition:no-PO→gate / PO→planning_spec 接管)+ 新 `test_teamwork_space_auto_created`(知识入口探测 + 空表 + 幂等)· E2E 两场景(fresh→自动建+cold-start gate / 有 PO→无 cold-start)· 骨架空表→registry `{}`→SKIP 已验。
- pytest **3 failed / 519 passed**(baseline 3 = scan-spec 既有 · 零回归)。

### 知识图谱 arc 收官(v8.114–116)
- v8.114 契约(律法/地图分工 + 三层律 + N≥1 模型)· v8.115 结构 checker(零死角物化 WARN)· v8.116 N≥1 地图根自动建 + cold-start 解耦。**teamwork 知识导航责任全物化**:从 teamwork-space.md(自动建·必读)零死角(checker 保结构)抵达一切 · 代码唯一真相 · 归档冷库按需解压。

## v8.115 · 知识图谱结构 checker(零死角从约定升物化 WARN · bootstrap 接线)

> 用户(承 v8.114 讨论):继续 —— 上 v8.115 物化 arc。本版交付 arc 第一步:**结构 checker**(最自包含)· 余(bootstrap 自动建 + cold-start 解耦 + 路由 always)再后续。

### 改动
- **`bootstrap.py` 加 `check_knowledge_graph_integrity`**(+ `_find_archive_dirs` / `_parse_archive_index_ids`)· session 启动跑 · 查:① 归档 `INDEX.md`↔`*.zip` **双向对账**(孤儿 zip〔已交付翻不到〕/ 悬空行〔断指针〕)② workspace 节点登记(`product-overview`/`project-specs`/`external` 存在于磁盘 → 必在 teamwork-space.md 提及)。**有界查找**(子项目直接放根下 · `*/docs/features/_archive` · 不深递归 node_modules)。
- **接线**:`result.checks.knowledge_graph` + 命中 leaks 加**截断鲁棒** `pmo_must_read` digest 行 · **不进 flow_gates/priority**(不劫持「升级>规划>任务」序)· teamwork-space.md 缺则 skip(cold-start gate 另管)。
- 🔴 **只查结构可达性 · 不查内容新鲜度**:leaks 必带 `scope_note`「不代表内容最新(内容=代码唯一真相)」—— 防 checker 通过被误读成「知识完整」· 自己成误导信号(承 v8.105「信号≠判决」)。
- **spec 同步**:`SKILL.md`「bootstrap 做什么」加 KG 校验行 · guide §0/§0.1 物化校验「→ v8.115」改「已落」。

### 验证
- 新增 `TestKnowledgeGraphIntegrity` 8 例(无 space→skip / clean / 孤儿 zip / 悬空行 / 匹配不报 / 节点未登记 / 节点已登记 / scope_note 必带)· E2E 确认 leak 经 digest 行 survive 截断。
- pytest **3 failed / 519 passed**(baseline 3 = scan-spec 既有 · 零回归 · +8 新)。

### 顺延(arc 余项)
- bootstrap 自动建 teamwork-space.md(N≥1 落地)+ cold-start 解耦(地图 vs 规划层)+ state.py 路由校验 always。

## v8.114 · teamwork 知识图谱契约:律法/地图分工 + 三层律 + N≥1 统一模型 + teamwork-space.md 必读地图根

> 用户:teamwork 是否该承担项目知识图谱责任 —— 从 teamwork-space.md 零死角抵达项目架构/文档/「去查什么」· 细查时代码仍是唯一真相 · 归档 zip 必要时解压。多轮讨论收敛后「按建议落实」。

### 定位:teamwork owns 知识导航(地图)· 不 owns 知识内容(防腐烂反向误导)
- 现状已有 ~80%(SKILL § 项目级文档信息架构路由表 + teamwork-space.md)· 本版**把契约说死 + 闭合死角**(doc 基座)· 物化 checker 顺延 v8.115。

### 改动(doc 基座 · 律法 SKILL / 地图 template+guide 解耦)
- **`SKILL.md` § 项目级文档信息架构**:加 ① **知识三层律**(地图=teamwork-space/docs · 领土=代码〔细节唯一真相〕· 冷库=归档 zip〔按需解压〕)② **律法/地图分工**(SKILL=generic 律法·不复制进项目;teamwork-space.md=实例地图)③ **N≥1 统一模型**(任何项目=teamwork-space.md + N≥1 逻辑子项目 · 单=N=1 · 知识层与 monorepo 无关)。路由表**闭合死角**:加 `external/` + 归档 `_archive/INDEX.md` 两行(文档清单 + 场景路由)· teamwork-space.md 标「🔴 必读地图根」· 代码行标「唯一真相·不信转述」。
- **`templates/teamwork-space.md`**:头部重定位「必读知识地图根 · N≥1 · 单=1」+ 三层律 · 新增 **「知识入口」节** —— 本项目每个知识节点一行指针(子项目 docs_root / product-overview / project-specs / external / 归档冷库 / 代码)· 这是「从 teamwork-space.md 零死角抵达一切」的**实例载体**。
- **`docs/teamwork-space-guide.md` §0**:定位改「知识地图根 · 不承担内容」+ N≥1 模型(替原「单项目可无」)· 新增 **§0.1 知识入口零死角律**(每磁盘节点必有指针 · 一行只写去哪不写是什么 · 末行永远代码 · 物化校验→v8.115)。

### 验证
- doc-only · pytest **3 failed / 511 passed**(baseline 3 = scan-spec 既有 · 零回归)。

### 顺延 v8.115(物化 arc · 把「零死角」从约定升门禁)
- bootstrap 自动建 teamwork-space.md(N≥1 落地)+ cold-start 解耦(地图 vs 规划层)+ state.py 路由校验 always + **结构 checker**(入口指向存在 / 归档 INDEX↔zip 对账 / 孤儿检测 → WARN)。