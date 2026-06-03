# Changelog

> 📦 v8.91 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**保留最近 5 版**(每次发布:新增本版 → 若超过 5 版,把最旧的一版迁入归档)。

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

## v8.93 · 规划层 back-ref 随收尾 MR 原子合入(planning-backref 暂停点 · 去 §5.5 直推)

> 用户:看 case(aon ADMIN-F260603063006)—— 规划层的改动是否需要在收尾 MR 之前、随收尾 MR 一起合入?案例里 feature MR(379)+ 收尾 MR(381)都走 glab MR,但 ROADMAP BL-020 / BG-022 翻牌是在 381 已合并 + worktree 已清**之后**才做、且按旧 §5.5 直推 staging。用户定:不需要 amend,AI 改完相关文档和 zip 收尾**一个 MR** 好了;改哪些由 AI 判断(主要 WS / ROADMAP / teamwork-space.md)。

### 诊断:旧 §5.5 post-step 直推与 v8.80「去直推」自相矛盾
- 收尾 MR(v8.80 去直推 · v8.82 加归档)全程走 MR(兼容保护分支);但 §5.5(v8.77)规划层 back-ref 却是 finalize **之后**的 post-step + **直推 merge_target**。
- 后果:① 保护分支(case 里 staging)**直推被拒**;② back-ref 触发时收尾 MR 早已合并关闭 → 规划层**物理塞不进** → 非原子(归档已交付但 ROADMAP 仍「规划中」的窗口)。

### 改法:planning-backref 暂停点 · 随同一收尾 MR(`_v8_ship.py` · 不 amend)
- **三态 finalize-deliver**:① 收尾分支已暂存 → reuse(🔴 **不 amend**);② 规划未决定且未暂存 → emit **`planning-backref`** 暂停点(gate · 让 AI 先翻牌);③ 规划已决定 → 暂存 {归档 zip + 删目录 + state.json + **规划文件**} 进**同一收尾分支** + 还原工作树 HEAD(防 step7 ff-pull 冲突)→ deliver-pending。
- **新参数**:`ship-finalize --planning-artifacts <逗号分隔相对路径>`(AI 判断 ROADMAP/WS/teamwork-space.md/变更单 哪些翻「已交付」· 改好后传)· `--no-planning-changes`(ad-hoc 无 BL 显式跳过)。文件不存在 / 仓外 → FAIL(不静默漏翻)。
- **staging 复用零 checkout plumbing**:`_stage_archive_commit` / `_finalize_push_plumbing` 加 `planning_files` —— hash 工作树内容 → update-index --add 进收尾 commit(规划文件在 force-remove 之后加 · 防误删)。
- **删 post-step**:移除 `_planning_backref_reminder` + PASS emit 的 `planning_backref_pending`;`_ship_finalize_brief` 改「规划层已随收尾 MR 合入(或 --no-planning-changes)」。
- **逃生口**:暂存后漏文件 → `git push origin --delete ship-finalize/<id>` 删分支重跑(不 amend)。
- 接线 spec:`stages/ship-stage.md` §5 步表 / §5.5 重写 / §12 增量 · `SKILL.md` 快速开始 L92。

### 验证
- 新增 `test_ship_planning_bundle_v893.py` **7 测试**:planning gate 首跑不暂存 / `--no-planning-changes` 归档-only / `--planning-artifacts` 翻牌入收尾分支 + 工作树还原 / 文件不存在·仓外 FAIL / 全周期原子合入(origin/main + 工作树含翻牌内容)/ 收尾分支 reuse 不 amend + warning。
- 旧 `test_ship_archive_v882.py` + `test_ship_finalize_state_sync.py` 的 `_finalize` 补 `--no-planning-changes`(跳 gate 直入暂存 · 语义不变)· 旧 post-step 测试类改写为 v8.93 行为。
- pytest **3 failed / 486 passed**(baseline 3 = scan-spec 既有 · 零回归 · 净 +6 测试)。

## v8.92 · review-stage §5 澄清「汇总层 ≠ 合并」(防三视角揉进一个 REVIEW.md · doc-only)

> 用户:看下面的 case,是否是 review 规范写的不清楚 —— 案例里 AI 跑完 arch/qa/external 三视角后只写了一份汇总 `REVIEW.md`(+ `reviewers:[…]` list),review-complete 因缺 per-role 文件 FAIL,补 `REVIEW-arch.md`/`REVIEW-qa.md` 后才过。

### 诊断:不是「漏写」· 是 §5 决策点的认知陷阱
- per-role 文件其实在 **8 处**写明(stage.md §2/§3/命令清单/质量基线/Output Contract + `_review_brief` 结果清单/完成命令 `--artifacts` + `REVIEW_SPEC.artifacts` 硬门禁)→ 信息完整,gate 弹回是**正确行为**(不动 gate)。
- 但 **§5「汇合 → REVIEW.md」** 落在「AI 决定产物形态」那一步,四个信号合力把人往「一个文件搞定」带:① "汇合" 字面像 merge into one;② `reviewers:[arch,qa,external]` 是 list-frontmatter 暗示"一个文件装所有视角";③ per-role 文件零内容校验显得像可选脚手架;④ gate 重点 `reviewers_match` 只查 REVIEW.md。多视角独立性 WHY(防鼓掌效应)又埋在质量基线、没出现在决策点。

### 改法(doc-only · 不动 gate 逻辑)
- **`stages/review-stage.md` §5**:标题改「🔴 汇总层 · 不是合并:arch/qa/external 三份产物都要独立留盘」+ 正文点明「REVIEW.md 是三份产物**之上**的汇总,**不替代**它们(P0 门禁硬要求 · 原因:多视角独立性 SOP 防鼓掌效应)」+ 显式警告「别揉进一个 REVIEW.md + reviewers list 就交差 → review-complete 会因缺 per-role 文件 FAIL」。
- **§cite 表第 5 行**:从「(整合 · 无 spec cite)」改为「(汇总层 · REVIEW-arch/qa 已各自落盘 · REVIEW.md 只汇总不替代)」。

### 验证
- doc-only · 无代码变更 · gate 与测试不受影响(per-role 硬门禁本就正确)。
