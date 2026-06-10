# Changelog

> 📦 v8.116 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**保留最近 5 版**(每次发布:新增本版 → 若超过 5 版,把最旧的一版迁入归档)。

## v8.121 · 全量 MD review P0 修复:数字宣称对齐代码 + 断链/旧名/脏标题清理

> 用户:重新 review teamwork 的所有 md · 看下哪些不合理。6 路并行 review + 主对话逐条复核:实锤 16 条(高 7 / 中 5 / 低 4)· 排除误报 3 条。本版收 P0 批次(宣称/断链类 9 项)。

### 诊断:数字型宣称(版本/stage 数/段结构/gate 名/§ 编号)写死多处 · 无单源无校验 → 演进必漂
- 代码真相 **12 stage**(`STAGE_SPECS`)· 文档四种口径:README「10 stage 索引」· SKILL.md「11 stage × 2」+「10 stage 完整契约」(B 类清单漏 panorama_sync)· STAGES.md「11 stage 索引」且**漏 diagnose 行**(Bug 流首 stage 不在索引)。
- README 版本徽章 **v8.87**(落后 33 版 · bump 脚本只改 SKILL.md frontmatter)。
- v8.116 改名的 cold-start gate 在 PRODUCT-OVERVIEW-INTEGRATION.md 残留旧名 `cold_start_workspace_uninitialized` + 触发条件还写「无 teamwork-space.md」(地图根已自动建);prepare.md 必读指向不存在的「SKILL.md § P0-11」(实际 STAGES.md §2);FLOWS.md 引幽灵小节「§ 4.1」;state.py rule 串引幽灵「§3.4」。
- blueprint-stage 宣称 TECH.md「5 段:模块/数据/接口/依赖/风险」与 templates/tech.md 实际结构不符;goal-stage「必含 5 角色」与 `change-review-roles` 可调机制矛盾(调整后按新值校验);frontend/backend.md「模块设计判定」标题被 v7 清理(e1d12b2)误删成脏字符。

### 改动(doc-only + state.py 2 处显示字符串/注释)
- **stage 数对齐 12**:README/README-EN「12 stage 索引」· SKILL.md B 类「12 stage × 2 + 4 fix/retry + ship-phase/ship-finalize/main-sync」+ 补 `panorama_sync-start/complete` 行 · 路由表「12 stage 完整契约(stage 数单源 STAGE_SPECS)」· STAGES.md 索引标题挂单源 + 补 diagnose 行 · state.py 注释 11→12。
- **版本徽章**:README/README-EN v8.87 → v8.121 · 注明「版本单源 = SKILL.md frontmatter」(README 徽章为快照)。
- **断链/旧名**:POI gate 改 `cold_start_product_planning_recommended` + 触发改「缺 product-overview(v8.116 地图/规划解耦)」· prepare.md 必读改链 [STAGES.md §2](../STAGES.md) · FLOWS.md + feature-planning.md「§ 4.1」→「5 mode 分诊」· conventions.md「§ 4.2/4.3 worktree 决策」改指 prepare.md(R-T2:worktree 决策是 prepare 职责)· `templates/host-instruction-injection.md`(注入块单源)+ 根 CLAUDE.md 实例去坏链(根目录 `../SKILL.md` 指向仓库外)改纯文本 · state.py rule 串去「§3.4」。
- **口径对齐机制**:blueprint-stage TECH 结构改按 templates/tech.md 真实段(技术方案〔架构/数据结构/接口〕/实现思路/TDD 计划/待决策)· goal-stage 改「必含 `stage_review_roles[goal]` 全部角色(默认 5 · change-review-roles 调整后按新值)」。
- **标题修复**:frontend/backend.md「## 模块设计判定（借鉴 mattpocock/skills improve-codebase-architecture）」。

### 验证
- grep 全仓现行 md/py:旧 gate 名 / P0-11 误指 / § 4.1 / §3.4 / 10|11 stage / 「5 段:模块」零残留(CHANGELOG/归档除外)· pytest **3 failed / 519 passed**(baseline 3 = scan-spec 既有 · 零回归)。

### 顺延(P1 · 本版未收)
- frontend.md TDD fork 瘦身(tdd.md 单源)· external-review「超时重试失败 vs 降级」路径划清 · frontend.md 教程式内容外迁 · 数字宣称纳入 scan-spec 类校验 · bump 脚本顺带改 README 徽章。

## v8.120 · prepare 流程概览加「流程目标」首行:用户 review 第一校准点

> 用户(case:PTR Assets 上传 Feature 的 prepare 总览):流程概览时需要输出流程目标概述(如需求目标 / bug 解决目标)· 方便 review。

### 诊断:`# 流程概览` 只有 flow_type + stage 链 + 理由 —— 全是「怎么流转」· 没有「要达成什么」
- 「理由」解释的是流程类型判定依据 · 「上下文准备」是事实盘点 · 用户 review 暂停点时无处校准「AI 对任务目标的理解」—— 目标理解偏 → 后面 goal/blueprint 全偏 · review 成本最低的校准点反而缺位。

### 改动(`docs/prepare.md §4` · doc-only)
- emit 模板 `# 流程概览` 首行加 `📋 **流程目标**`:1-2 句概述本次流程要达成什么 · 从用户原文/BL 描述提炼 · 按 flow_type 措辞(Feature/敏捷需求=需求目标〔给谁 · 什么能力/价值〕· Bug=解决目标〔问题现象 → 期望修复后行为〕· Micro=改动目标)· 🔴 写「要什么」不写「怎么做」(防目标位被写成实现方案)。
- §4 5 段定义 + §4.1 emit 自检清单同步为「流程目标 + flow_type + stage 链 + 理由」· 自检项注明动机(目标 = 用户 review 第一校准点)。

### 验证
- doc-only · 「流程概览」结构仅 prepare.md 一处定义(grep 全仓 = prepare.md + 归档)· 工具层无渲染(`emit_template_markdown` 仍 ⏳ TODO · 物化时直接带上目标行)。

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
