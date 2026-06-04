# Changelog

> 📦 v8.93 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**保留最近 5 版**(每次发布:新增本版 → 若超过 5 版,把最旧的一版迁入归档)。

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

## v8.95 · 禁异质项目的 external 违规 FAIL 改给专属修复指引(去通用「调异质」误导 · hint-only)

> 用户:看 case(aon SVC-PLATFORM-B260603103943)—— 关掉异质后物化校验真的不认么?案例里 `disable_heterogeneous_review=true` 项目,AI **手写**同模型自审(没打降级标记)被 review-complete 异质门禁拦。

### 诊断:认 —— 只认 `state.py external-review` 跑出的降级文件,不认手写
- 门禁 `_evidence_external_review_artifact` 在 `disable_heterogeneous_review=true` 时**接受** `external-cross-review/*.md` frontmatter 带 `degraded:true`+`heterogeneous:false` 的降级自审(v8.90);而 `state.py external-review` 在该项目里**自动**打这俩标(state.py config-disabled 分支 L3201-3203)→ 两边严丝合缝,本就认。
- 案例 FAIL 因 AI **手写**自审、没打标(把 `heterogeneous_review: degraded` 写进 **REVIEW.md** · 而门禁查的是 external-cross-review **文件**的 `degraded`/`heterogeneous` 键)→ 判同源伪装拦(v8.67 反伪造 · 拦得对)。

### 改法:violation FAIL 文案分 het_disabled(hint-only · 不动门禁逻辑)
- `het_disabled=true` 的 violation → 给**专属**修复:跑 `state.py external-review`(config-disabled 自动产出被接受的降级自审 · **别手写**)· 或补 `degraded:true`+`heterogeneous:false`(写在 external-cross-review 文件 · 非 REVIEW.md)· 想恢复真异质 → 删 disable 开关。
- 默认(未禁)项目仍走原通用 hint(host 自动映射异质模型 / change-review-roles)。治本:旧文案在禁异质项目里仍喊「调异质模型」误导单模型用户(与 v8.90 opt-out 初衷相悖 · case 里 AI 就是被带去找 codex)。

### 验证
- `test_v8_stage_specs.py` 扩断言:het_disabled violation → 含 `disable_heterogeneous_review`/`别手写`/`state.py external-review` · **不含**「host 自动映射异质模型」;默认项目反之(锁两分支)。
- pytest **3 failed / 498 passed**(baseline 3 = scan-spec 既有 · 零回归)。

## v8.94 · feature 归档加极简描述(`--archive-desc` ≤50 字 → INDEX.md 描述列)

> 用户:feature archive 的时候给一段极简的 feature 描述(限 50 字以内),写到 INDEX.md。

### `--archive-desc`(ship-finalize · 写入 `_archive/INDEX.md` 描述列)
- **新参数**:`ship-finalize --archive-desc '<≤50 字>'` —— AI 在 planning-backref 暂停点连同 `--planning-artifacts` 一起给本 feature 一句极简描述(是判断活 · 故 AI 给 · 非脚本自动抽)。`_clean_archive_desc` 净化:折叠空白 + 去 `|`/换行(防破表格)+ **≤50 字**(超则截 49+`…`)+ 缺省 `—`;超长 emit warning。
- **INDEX.md 加列**:`| Feature | 描述 | 交付归档时间 | 归档物 |`(原 3 列)· 便于日后**不解压**就识别归档内容。
- **旧行自动迁移**:base 上旧 3 列 INDEX 行下次归档时补 `—` 迁为 4 列(`_build_archive_index`)· re-archive 同 feature 去重。
- **接线**:planning-backref gate brief + 命令示例 + argparse + ship-stage.md §5.5/§15。仅 archive 模式(`archive_on_ship` 默认 true)写 INDEX。

### 验证
- 新增 `test_ship_archive_desc_v894.py` **12 测试**:`_clean_archive_desc`(正常/超 50 截断/`|` 净化/换行折叠/空→`—`/恰好 50)· `_build_archive_index`(新列/缺省 `—`/旧 3 列迁移/re-archive dedup)· 集成(--archive-desc 入 INDEX / 超 50 截断 + warning)。
- pytest **3 failed / 498 passed**(baseline 3 = scan-spec 既有 · 零回归 · +12 测试)。
