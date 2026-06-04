# Changelog

> 📦 v8.95 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**保留最近 5 版**(每次发布:新增本版 → 若超过 5 版,把最旧的一版迁入归档)。

## v8.100 · UI 可视全景前移到规划层(拆 WS 前先出全景初步规划 · feature 边界对齐 UI 结构)

> 用户:UI 可视全景能否更早出 —— 放到 feature 阶段就晚了。确认链路:feature-planning 讨论需求规划逻辑 → 产出 UI 全景初步规划 → 据全景拆成最终 WS(1 个或多个)。

### 设计(全景出生点前移:per-Feature ui_design → 规划层 feature-planning)
- **拆 WS 之前先出全景初步**:涉 UI 的轮次,feature-planning 在拆 WS 前于 `{子项目}/docs/design/preview-project/` 出 design system + 关键页(🔴 **初步**:系统 + 代表页 · **非每页** · 防瀑布 · 跑 `preview.sh` 看)+ 同步 `sitemap.md`(IA 地图 · 🔴 只写层级/导航不写视觉)· 完成产生 git diff = **拆 WS 的输入**。非 UI 轮跳过(WS 标 `N-A`)。
- **WS 据全景拆 · 1..N 个**:feature-planning 输入=全景 diff + 业务目标 → 拆 **1 或多个 WS**(feature 边界对齐 UI 结构)· 每 WS 记 `ui_panorama: ✅/N-A` + `ui_panorama_pages`(覆盖页清单 · 替代模糊的"基于哪轮全景")· 涉 UI 必 ✅ 才转「规划完成」。
- **ui_design 改增量扩**:全景规划期已出生 · ui_design 阶段在已有全景上**增量补**本 Feature 的页与细节(源即权威)· 非从零搭;老项目/跳过规划路径 → 此处首次 seed(回退)。
- **三者分工厘清**:`sitemap.md`=IA 地图(文字 · 不写视觉)· `preview-project/`=视觉权威(可跑)· 单 Feature `UI.md`=本 feature 涉及的页(不重复全局)。

### 接线(8 文档/工具 · 一个 release)
- `docs/feature-planning.md`:§2 重排 Step —— 新 Step 5「🎨 UI 全景初步规划(条件)」插在拆 WS 之前 · 新 Step 6 显式「拆 WS(1..N)」· §1/§4 产物加 preview-project · 坑 4 改三者分工。
- `templates/workstream.md`:frontmatter 加 `ui_panorama` + `ui_panorama_pages` · 状态生命周期加「全景初规子门禁」(涉 UI 必 ✅ 才转规划完成)· 设计要点 +1。
- `stages/ui-design-stage.md`:§3 加「全景在规划期已出生 · ui_design 增量扩」框定 + same-stack 措辞「扩/搭」。
- `PRODUCT-OVERVIEW-INTEGRATION.md`:权威冷启动顺序 ×2 插入「(涉 UI)UI 全景初步规划」。
- `docs/conventions.md §13`:`design/` 加「首次 seed 在规划层」注 · `sitemap.md` 标「只写地图不写视觉」。
- `tools/state.py cmd_planning_check`:checklist +「🎨 全景UI初步规划」项 + WS 项加全景状态/页清单 + `planning_order` 加全景环。
- `roles/designer.md` + `roles/product-lead.md`:规划层参与/主导全景初规。
- `SKILL.md § 业务流程架构`:纵向链路图加「(涉 UI)UI 全景初步规划」一环 + 2 bullet。

### 验证
- 新增 `test_v8100_planning_check_panorama_before_ws`(全景在 WS 之前 + checklist 项 + WS 状态/页清单文案)· `planning_checklist` 5→6。
- pytest **3 failed / 500 passed**(baseline 3 = scan-spec 既有 · 零回归 · +1 测试)。

## v8.99 · DEV-RULES 模板去示例(只留段骨架 + 填写引导)

> 用户:DEV-RULES 模板不用给示例。

- `templates/dev-rules.md` 内嵌骨架各段(架构/分层 · 命名 · 错误处理 · 测试策略 · 代码风格 · 其他约定)删掉 `示例:…` 条目 · 只留 `## 段标题` + 一行 `>` 填写引导。人维护时空段直接填,不被示例干扰 / 误当真规则。
- doc-only · 无 code/测试影响(bootstrap scaffold 用本模板 · 测试用 fake 模板不依赖其内容)。

## v8.98 · spec 全文档去噪(删版本标 / case-id / 演进叙事 · 只留 how/后果/反模式)+ 立写作规约

> 用户:review ship-stage.md 是否冗余 —— 目的是让 AI 遵守(说清**怎么做** / **不做的后果** / **反模式**)· 不要描述背景(哪个版本发生过什么)= 噪音。承 v8.97(ship-stage 试点),本轮全 skill 铺开 + 立长期规约防再长。

### 去噪(15 文档 · code-heavy 的 frontend/backend/tdd/common/scripts 零改)
- **删**:版本标 `(v8.xx)` / `[v8.xx]` / `v8.xx 变更·已物化`(~110 处)· case-id 叙事 `治本 SVC-CORE-Bxxx case` / `实证 PTR-Fxxx` / `旧实现…改成…`(~45 处)· 长 case 复盘段(SKILL F001 GCP gateway · prepare F-Bv2-8 等)。
- **留**:怎么做(步骤/命令/决策树)· 不做的后果(驱动遵守)· 反模式(防具体失败)· 设计 rationale(去版本/case)。
- 覆盖:`SKILL.md` · `conventions/prepare/feature-planning` · goal/blueprint/review/test/ui-design/panorama/pm-acceptance stage · `external-model-usage` · roles/designer·product-lead · `PRODUCT-OVERVIEW-INTEGRATION`。
- 残留版本标 / case-id **0**(CHANGELOG 与 SKILL 版本号除外)· 无 mangle · 保护 `v8.0` 范式标记。

### 立规约(治本 · 防再长)
- `docs/conventions.md` 新增「# spec 文档写作约定」:**spec = 现行真相**,不写版本标 / case-id / 演进叙事,**当它一直如此**地写;历史只进 CHANGELOG;发版加新规则别在 spec 写 `(v8.xx 新增)`。

### 验证
- pytest **3 failed / 499 passed**(baseline 3 = scan-spec 既有 · 零回归 · doc-only)。
- 护栏:code-heavy 文档 git diff 零改 · 残留 `v8.[1-9]` grep = 0 · 新增行无 mangle(空括号/悬挂分隔)。

## v8.97 · ship-stage.md 去噪(删版本标 / case-id / 演进叙事 · 只留 how/后果/反模式 · doc-only)

> 用户:review ship-stage.md 是否冗余 —— spec 目的是让 AI 知道**怎么做 / 不做的后果 / 反模式**,不需要「哪个版本发生过什么」这类背景噪音(那是 CHANGELOG 的活)。

### 去噪(doc-only · 不改任何行为/命令/门禁)
- 删全部版本标 `(v8.xx)`(21 行)+ case-id(SVC-CORE-B006/B007/F028 · PTR-A018 · aon ADMIN-…)+ 演进叙事(「旧…改成…增量」)。
- **合并废弃 §12**:原「Phase 2 收尾投递」演进 deep-dive(含已被收尾 MR 取代的**直推机制**历史)收敛为「state.json 直推例外(逃生口 · 仅状态档)」—— 只留仍有效的规则 + 命令 + 🔴 禁止滥用(业务文件必走 MR)。
- 保留全部可执行信息:step 表 / 决策树 / 命令 / 后果(「不翻牌 → 规划层永久脱节」)/ 反模式(❌ 列表)/ 逃生口。§5.5/§12/§13/§14/§15 锚点不变。
- **275 → 248 行**;版本标 **21→0** · case/历史 **12→0**。

### 验证
- doc-only · pytest **3 failed / 499 passed**(baseline 3 = scan-spec 既有 · 零回归)。
- 试点:效果好则同手法全 skill 铺开 + 把「spec 无版本标/无 case-id · 历史只进 CHANGELOG」定为长期规约(待用户拍板)。

## v8.96 · 项目开发规范从 KNOWLEDGE 拆出 → `project-specs/DEV-RULES.md`(人维护 · blueprint/dev 必读)

> 用户:项目开发规范是**人维护的团队约定**,KNOWLEDGE.md 是 **AI 沉淀的经验**——维护者不同应拆开;且 KNOWLEDGE 有点重,顺带精简。doc 名定 `DEV-RULES.md`;bootstrap 无则从模板建、有则不动。

### 拆分(按维护者轴:人定规矩 vs AI 沉淀)
- **新 `project-specs/DEV-RULES.md`(人维护)**:本项目强制开发规范(分层 / 命名 / 错误处理 / 依赖方向 / 测试策略 / 风格)· 模板 `templates/dev-rules.md` · bootstrap `maintain_project_skeletons` absent→从模板建 / present→**绝不改**(人维护)。
- **blueprint + dev 必读**:两 stage §1 + P0-11 cite 表 → `DEV-RULES.md`「存在则必读 · 须遵守」(不存在 skip · 不硬 FAIL · 用户主权 doc)。
- **KNOWLEDGE.md 瘦身**:抽走 Conventions(→ DEV-RULES);删通用架构词汇(8 词)+「删除测试」启发式(通用 · 违反它自己「通用走 standards」边界);Glossary 段去重为指向 GLOSSARY.md。KNOWLEDGE 回归本质「Gotchas / 已澄清歧义 / Preferences / 已否方向」(AI 沉淀)。
- **distill 不代写**:ship1 distill 的 `knowledge` 只 promote gotcha/事实 → KNOWLEDGE;约定/规范 → DEV-RULES.md 人维护,AI 只提示用户加。
- 接线:SKILL.md doc-index + 关键词路由、docs/conventions.md §13 布局 + 两层表、ship-stage.md distill 注释。
- 🔴 **存量项目不自动迁移**:已有 KNOWLEDGE.md 的项目,bootstrap 只补建空 DEV-RULES.md(不动 KNOWLEDGE);旧 Conventions 留在 KNOWLEDGE,用户按需手动搬。

### 验证
- `test_bootstrap.py`:fresh 建 4 骨架(含 DEV-RULES.md)+ 新增「DEV-RULES.md 已存在则 existed · 内容不改」测试 + E2E existed 列表更新。
- pytest **3 failed / 499 passed**(baseline 3 = scan-spec 既有 · 零回归 · +1 测试)。
