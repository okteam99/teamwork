# Changelog

> 📦 v8.108 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**保留最近 5 版**(每次发布:新增本版 → 若超过 5 版,把最旧的一版迁入归档)。

## v8.113 · 归档 INDEX.md 描述超 200 改「压缩重写」而非截断(FAIL 门禁 · 不丢尾)

> 用户:超则截 199 + 需要优化 —— 超过则压缩表达方式,压缩到 200 以内。

### 诊断:截断 = 机械丢尾 · 压缩是 AI 判断(不可枚举 → 留 AI)
- v8.112 的「超 200 截 199+`…`」机械丢尾失信息 · 用户要的是**压缩表达方式**(精简措辞 / 去枝节 / 保要点)塞进 200 —— 这是语言判断 · 纯函数做不了 · 归 AI(SKILL.md 哲学:不可枚举的判断留 AI)。

### 改法:门禁 FAIL 驱动 AI 压缩重跑(物化闸 · 不靠截断)
- **`_clean_archive_desc`(`_v8_ship.py`)**:删 `s[:199]+…` 截断 · 退化为**纯净化**(折叠空白 + 去 `|`/换行)· 任意长度照原样返。
- **`cmd_ship_finalize` 前置门禁**:`--archive-desc` 净化后 > 200 字 → **FAIL**(`failed_step=finalize-deliver` · 在任何归档暂存/推分支**之前**)· hint = 压缩表达方式重写到 ≤200 后重跑(ship-finalize 可重入 · 不丢尾)。
- **`ship-stage.md` §归档 + argparse help**:截断语义 → 压缩重跑语义。

### 验证
- `test_ship_archive_desc_v894.py`:`over_200_truncated`→`over_200_not_truncated_by_sanitizer`(净化不截)· 集成 `over_200_truncated_with_warning`→`over_200_blocks_with_compress_hint`(FAIL + 压缩 hint + **暂存前拦** · 收尾分支不推)+ 新 `compressed_under_200_passes`(≤200 完整写入 · 无 `…`)。
- pytest **3 failed / 511 passed**(baseline 3 = scan-spec 既有 · 零回归 · +1 净增)。

## v8.112 · 归档 INDEX.md feature 描述上限 50 → 200 字

> 用户:feature index.md feature 描述上限扩展到 200 字符以内。

### 改动
- **`_clean_archive_desc`(`_v8_ship.py`)**:`--archive-desc` 净化上限 **50 → 200 字**(超则截 199 + `…`)· 给更完整的 feature 描述空间。同步改 4 处文案:`_build_archive_index` 描述列说明 / finalize-deliver hint(`<≤200 字描述>`)/ 截断 warning(`超 200 字`)/ argparse help。
- **`stages/ship-stage.md`**:§归档 INDEX 描述列 + `--archive-desc` 说明 50 → 200。
- 历史 `CHANGELOG-ARCHIVE.md` v8.94 条目(记录当时「50 字上限」)= 历史真相 · **不改**。

### 验证
- `test_ship_archive_desc_v894.py`:`test_over_50_truncated`→`test_over_200_truncated`(199+`…`)· `test_exactly_50_kept`→`test_exactly_200_kept` · 新 `test_between_50_and_200_kept`(防回退:51–200 字不再截)· 集成 warning 测试改 `超 200 字`。
- pytest **3 failed / 510 passed**(baseline 3 = scan-spec 既有 · 零回归 · +1 新测试)。

## v8.111 · Bug 流程 2 摩擦点修复:reviewer 名精确匹配过严 + test brief 对 Bug 撒谎

> 用户:看下我们的 bug 流程是否有问题(附真实 Bug feature 跑流程 transcript:`external-claude` 被拒 + `verify-ac.py` 撞 PRD 不存在)。诊断后选 A+B 都修。

### 诊断:状态机骨架健全 · 坏的是 1 个全局过严匹配 + 1 段对 Bug 撒谎的 brief
- Bug 链 `diagnose→dev→review→test→pm_acceptance→ship` 全接对 · 门禁对 Bug 安全(`ac_test_binding` 已 skip Bug)· 暴露的 2 点都是文案/匹配层 friction。

### 改动
- **Fix A · reviewers roll-call 容许「角色-限定」写法**(`_v8_stage_specs.py:_evidence_reviewers_match`):原精确集合差 `required - reviewer_set` 使 `external-claude ≠ external` 被拒 —— 逼用户把更有信息量的「标明异质模型」写法降级成裸 `external`。改为 token 命中 `角色名本身` 或 `角色-<限定>` 前缀即算覆盖(`external-claude` 满足 `external` · `external-` 边界防 `externalize` 误匹配)。异质性不由此 roll-call 保证(由 `_evidence_external_review_artifact` 校验 cross-review 产物 `review_model`)· 放宽安全 · **全流程生效**(非仅 Bug)。
- **Fix B · `_test_brief` 按 flow_type 分支**(`_v8_stage_specs.py` + `stages/test-stage.md`):原 brief 写死 Feature 视角 · 完成判定列「`verify-ac.py` 通过 / AC 全覆盖」—— 但 **Bug 无 PRD/TC** · 实证有 agent 照着去跑 `verify-ac.py` 撞「PRD 不存在」困惑数轮(**门禁其实对 Bug 自动 skip · 是 brief 在撒谎**)。Bug brief 改为「回归测试转绿 + 既有套件保持绿 · verify-ac/AC 全覆盖 N/A · 别去跑 verify-ac.py」· test-stage.md 加「🐛 Bug 流程分支」callout + §1/§5 内联 Bug 提示。

### 刻意不动(考量 C · 站得住)
- Bug 的 `test` 仍要 `e2e/*`(≥1)+ 双 exit-code 全绿 · review 需 `external` 异质评审 —— 对小 bug 偏重但能防 fix 引回归 · 可 `change-review-roles` 调 · 不在本轮改。

### 验证
- 新增 `TestV8111BugFlowFixes` 6 例(role-qualified 满足 / 裸 external 兼容 / 缺 external 仍 BLOCK / `externalize` 不误匹配 / Bug brief 无 verify-ac 假信号 / Feature brief 不回归)。
- pytest **3 failed / 509 passed**(baseline 3 = scan-spec 既有 · 零回归 · 509 = 503 + 6 新)。

## v8.110 · cosmetic 清理:删 vestigial `review_start.log` 读代码 + config.md 旧降级语义/版本标

> 用户:ok(清理上一轮列的 3 项 cosmetic)。

### 改动
- **vestigial 代码(`state.py`)**:删 `cmd_external_review` 里读/清 `review_start.log` 的 liveness 块 + rc!=0 hint 的 liveness 分支 + 两处 `liveness_confirmed_at` emit —— v8.106 纯 `claude -p`(无工具)已不写该文件 · `liveness_at` 恒 None(死代码)。FAIL hint 简化 + 指向 §11.5 subagent 降级。
- **`config.md`**:`disable_heterogeneous_review` 注释「exec 自审 / v8.88 self-review-fallback 落 self-review · 不满足门禁」→ 改 v8.108 subagent 降级语义(satisfies gate · `degraded_mode`)· 删 4 个 section-header 版本标(v8.79/82/89/90)+ 1 处 v8.80。
- **`test_state.py`** 旧 section 注释去 doc 模式/liveness 措辞。

### 刻意跳过(re-estimate · 风险 > 价值)
- **章节重编号**:`external-model-usage.md` §一→§十二 跳号(缺 §二/§十)**无害**(全部引用可解析)· renumber 会牵动 **15+ `§11.x` 跨文档引用**(含 state.py hints + 刚接好的 §11.5/§11.2 cites)· 易引入新 broken-ref → 不做。
- **`ui.md` v8.17/v8.58 版本标**:是**现行模型**的 provenance(panorama 唯一权威 / same-stack)· 非 stale content · code-fence 多 → 保留(避免 mangle)。

### 验证
- pytest **3 failed / 503 passed**(baseline 3 · 零回归)· liveness 残留引用 = 0(仅剩 bootstrap `.gitignore` 防御项 · 无害)。

## v8.109 · 跨文档一致性 sweep(清理 + 4-agent 审计修 v8.100–108 遗留的 conflict/stale/broken-ref)

> 用户:清理(SKILL 命令计数 + reviewer.md liveness carve-out)· 并整体 review 各 md 文件看语义冲突 / 冗余 / 缺失。

### 清理(2 项)
- `SKILL.md` 命令清单:`10 stage × 2` → `11`(补 diagnose-start/complete 条目)。
- `claude-agents/reviewer.md`:删 v8.102 liveness carve-out(`review_start.log`)—— v8.106 已删 doc 模式 / Write 工具 · 该 carve-out 已 moot;READ-ONLY 改「不写任何文件 · 经 stdout 返回」· stdin→argv。

### 审计(4 并行 agent 扫 SKILL/planning · stages · standards/roles · templates)→ 修 conflict/stale/broken-ref
- **v8.107 diagnose 接线漏修**:`dev-stage.md`(§1 加 Bug 读 diagnose 的 BUG 报告为输入 · §5/Output 改「dev 追加 §回归测试/§修复记录 · 不重写根因/方案」)· `FLOWS.md` Bug 链补 diagnose · `bug-report.md` `current_stage` enum 换 v8 BUG_FLOW(删 defunct triage 枚举)+ body 段对齐(根因/方案=diagnose · §回归测试=dev · 删复杂度评估/PMO 流程判断)· `roles/rd.md` + `SKILL.md` 授权暂停点 Bug 行加 diagnose。
- **v8.106/108 external-review 接线漏修**:`external-model-usage.md §一`(claude 路径删 doc 模式/liveness/--allowedTools → 纯 claude -p)· §11.2 加 honest-degrade 黑名单例外 · §11.4 修 broken ref `7.x→11.x` + subagent 反模式区分伪装 vs §11.5 诚实降级 · §11.3 决策树降级优先 · `review-stage.md §4` 删 liveness bullet。
- **v8.100/101/104 planning 接线**:`prepare.md` 死术语 `panorama-design`→「UI 全景初步规划」(3 处)· `feature-planning.md`「只产 3 文档」→ WS+preview-project · `PRODUCT-OVERVIEW`/`roadmap.md` launch_order→execution_waves + WS/ROADMAP 波次权威关系。
- **broken-ref / stale**:`workstream.md`/`workstream-readme.md`「§ 进度统计」→「§ 规划状态」· `external-reviewer.md` `{review_id}.md`→`<stage>-<model>.md`(合 §11.2)+ host-aware 异质 · `templates/README.md` knowledge「3 类含 Conventions」→ 4 类(Conventions 已迁 DEV-RULES)+ 补 pending/dev-rules 行 · `agents/README.md §三` 加「权威已迁 §11」指针。
- **去版本标**(违 v8.98 spec 写作约定):清掉近期加到 SKILL/prepare/feature-planning/teamwork-space-guide 的 `(v8.10x)` inline 标。

### 验证
- 残留 grep(panorama-design / 旧 liveness / § 进度统计 section-ref)= 0 · doc-only · pytest **3 failed / 503 passed**(baseline 3 = scan-spec · 零回归)。
- 余(cosmetic · 不阻塞):external-model-usage §二/§十 编号跳号 · ui.md/config.md 旧版本标 · state.py vestigial `review_start.log` 读(无害)。