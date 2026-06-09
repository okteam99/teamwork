# Changelog

> 📦 v8.109 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**保留最近 5 版**(每次发布:新增本版 → 若超过 5 版,把最旧的一版迁入归档)。

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