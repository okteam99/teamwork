# Changelog

> 📦 v8.88 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**保留最近 5 版**(每次发布:新增本版 → 若超过 5 版,把最旧的一版迁入归档)。

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

## v8.91 · bootstrap 启动自愈 localconfig schema(缺字段补默认值 · dev-only)

> 用户:bootstrap.py 启动时检查 `.teamwork_localconfig.json`,`_bootstrap` 段字段不足的要补上默认值。

### `ensure_localconfig_complete`(bootstrap.py · 每次启动跑)
- **治本**:localconfig 由老版 bootstrap / 手建 / 部分写入时,`_bootstrap` 子键(`skill_version`/`host`/`last_maintain_at`/`last_maintain_results`)或**新增 feature 开关**(`archive_on_ship`/`local_env_auto_create`/`disable_heterogeneous_review`/`id_strategy`)缺失;且**版本命中 `skip_maintain` 时这些缺口永不补**(`write_bootstrap_marker` 只在 maintain 跑时重写 `_bootstrap`,且从不补新 config 键)→ 用户也看不到新选项。
- **行为**:补全 `_bootstrap` 4 子键 + 所有已知顶层 config 键的默认值。🔴 **additive only · 绝不覆盖**用户已有值(含显式 false/null);只在**已存在**的 localconfig 上跑(不存在 = 冷启动,由 prepare/maintain 创建,不在此凭空造);**无变化不写盘**(防 churn);skill 仓自身 skip。
- **接线**:跑在 maintain 之后(无论 skip 与否),覆盖 `skip_maintain` 缺口;结果落 `result.localconfig_backfill`(audit)。
- **默认源**:`LOCALCONFIG_CONFIG_DEFAULTS` + `LOCALCONFIG_BOOTSTRAP_DEFAULTS`(🔴 与 `templates/teamwork_localconfig.json` 保持同步,新增字段两处都加)。

### 验证
- live:incomplete(缺 `_bootstrap` + 新开关)→ backfilled 且用户值(merge_target=dev/worktree=off)保留;complete → `status:complete` 不写盘;absent → skip 不创建;部分 `_bootstrap` 子键 → 只补缺的。
- pytest **3 failed / 480 passed**(baseline 3 = scan-spec 既有 · 零回归 · +5 测试:补全保留用户值 / 部分 `_bootstrap` 补缺 / complete 不写 / absent 不建 / skill_root skip)。

## v8.90 · 单模型用户可禁异质评审(`disable_heterogeneous_review` · 默认开异质 · dev-only)

> 用户:只有一个模型(如 codex 环境下 claude 不可用/未登录/配额满)时,允许降级到当前模型 exec 自审;可在 `.teamwork_localconfig.json` 配置是否禁用异质,**默认关**(异质开);禁用时默认用 exec;每次 teamwork 启动 WARN 提醒交叉 review 质量下降、建议恢复异质。

### localconfig `disable_heterogeneous_review`(默认 false = 异质开)
- `true` → `external-review` **自动**用宿主自身模型 fresh exec 自审(无需 `--self-review-fallback`),落 `external-cross-review/<stage>-<model>.md`(**满足 P0-154**)· frontmatter 标 `heterogeneous:false degraded:true degraded_mode:config-disabled` + banner + `concern WARN`。
- 🔴 **review-complete 门禁配套**:`_evidence_external_review_artifact` 在 disable 时**接受**标 `degraded:true heterogeneous:false` 的降级自审 · 仍 BLOCK 未标记的同模型文件(防伪装)· 异质项目(默认)不受影响。
- 🔴 **每次启动 WARN**:bootstrap `checks.heterogeneous_review.status=disabled` + `pmo_must_read` 顶部 forewarn。
- 与 v8.88 `--self-review-fallback` 区分:后者临时 stopgap(self-review/·不满足门禁)· 本项目级长期策略(external-cross-review/·满足门禁但 startup WARN 持续提醒)。
- pytest 3 failed / 475 passed(baseline 3 · 零回归 · +5 测试)。spec:standards §11 + localconfig 模板/config.md。

## v8.89 · 本地敏感配置统一目录 `.teamwork-local-env/`(kubeconfig/密码/API key · dev-only)

> 用户:本地敏感配置(kubeconfig / DB 密码 / 个人 API key)散落 · 规范一个统一目录、默认 gitignore、TROUBLESHOOTING 配合读、session 初始化自动创建。决策 **A**(默认自动建)。目录名 v8.89 patch 内由下划线改连字符 `.teamwork-local-env/`(对齐连字符命名)。

### bootstrap 自动维护 `.teamwork-local-env/`(项目根 · `maintain_local_env`)
- **缺失 → 自动建**:目录 + `config.properties` 模板(注释示例 · **无真密钥**)+ 目录内 `.gitignore`(`*`)。
- **已存在 → skip**:绝不覆盖用户真 secret(仅补缺失的目录内 .gitignore)。skill 仓自身 skip。
- **opt-out**:`.teamwork_localconfig.json` 的 `local_env_auto_create: false`(默认 true)。
- 用途:键值型(DB 密码 / API key / token)→ `config.properties`(`KEY=value`);整文件型(kubeconfig / 证书)→ 直接放本目录。

### 🔐 双重 gitignore(防御纵深 · secret 绝不进仓库)
- 项目根 `.gitignore` 加 `.teamwork-local-env/`(`maintain_gitignore_worktree`)· **且**目录内自带 `.gitignore`(`*`)—— 即便根 .gitignore 漏/子 repo/手删,目录仍自我忽略全部内容。
- 与 `.teamwork_localconfig.json` 严格区分:前者 = **你的** secret(gitignored)· 后者 = **teamwork 自己**的配置(可提交)。

### 配套 + 验证
- template `local-env-config.properties` + TROUBLESHOOTING.md §五(从 `.teamwork-local-env/` 加载命令示例 · 真值只在此目录)+ conventions.md §13 + localconfig/config.md 文档化 `local_env_auto_create`。
- pytest **3 failed / 470 passed**(baseline 3 · 零回归 · +3 测试)。
