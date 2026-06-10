# Changelog

> 📦 v8.114 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**保留最近 5 版**(每次发布:新增本版 → 若超过 5 版,把最旧的一版迁入归档)。

## v8.119 · backend.md migration 命名:优先 DEV-RULES · 否则秒级真实时间戳 · 不读邻居

> 用户(case:consuming 项目 AI 用 `20260609000000` 日级填充时间戳 · 撞项目 version-ceiling 守卫 CI 挂):后端开发有默认规范么。诊断:有但偏松 → 改为「优先 DEV-RULES · 否则秒级 · 不读邻居」。

### 诊断:有规范(`standards/backend.md §五`)· 但命名偏松 + 缺守卫意识
- §五 命名只写「YYYYMMDD 或 YYYYMMDDHHmmss(按项目框架约定)」· 允许日级 + 没说真实精度/守卫 → AI 用 `20260609000000`(日+`000000` 填充)蒙混 · 同日撞号风险 + 撞未声明的项目 version-ceiling 守卫。

### 改动(`standards/backend.md §五` · doc-only)
- **命名规范改优先级链**:① 优先按 `DEV-RULES.md`(项目/子项目级)migration 命名/守卫约定 → ② 未规定默认 `YYYYMMDDHHmmss` 秒级**真实时间戳**(不用 `000000` 填充 · 防同日撞号+乱序)· 🔴 **不靠读邻居 migration 推断**(用户决策:邻居可能不一致/有坏样板 · 要么 DEV-RULES 要么秒级默认)。
- **强制要求加守卫行**:加 migration 前查 DEV-RULES 的 migration 约定/守卫(version-ceiling / 高水位线 / sequence guard)· 同 PR 满足(如 bump ceiling)· 撞未声明守卫(CI 失败)→ 记进 DEV-RULES/KNOWLEDGE。
- **边界**:项目特异守卫机制本身归项目 `DEV-RULES`/`KNOWLEDGE`(用户主权)· 不进 teamwork 默认。

### 验证
- doc-only · 无其他 spec 含旧「YYYYMMDD 或」措辞(grep=0)· pytest **3 failed / 519 passed**(baseline 3 = scan-spec 既有 · 零回归)。

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