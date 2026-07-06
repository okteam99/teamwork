# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.193 · skills 删减 batch:退役迁移器/收尾遗物/手写模板 + ARCHIVE 照章清空(−2.2k 行)

> 全量 review skills(29.6k 行):按自家律法(三层律 · 定期清空 · 工具自动落禁手写)删 🟢 批次。

### 改动
- **CHANGELOG-ARCHIVE 照章清空**(−1.0k):v8.128→187 共 60 版条目 · git 历史是冷库(章程自 v8.127 就这么写)。
- **删 `_v8_migrate.py` + migrate-v7-to-v8 命令**(−258):v7→v8 一次性迁移已过 190+ 版 · 无 v7 存量。
- **删 `post-feature.py` + 其测试**(−690):v7.3 时代收尾遗物 · v8.145 ship 重构漏删 · 仅自引用。
- **删 `templates/external-cross-review.md`**(−279):v8.20 起 external 产物**工具自动落**、手写是红线 —— 给禁止手写的文件留手写模板自相矛盾;engine scaffold 映射 3 处同步清。
- SKILL/TEMPLATES 引用同步清(migrate 3 处 + 1 处)。agents/README 瘦身(683→~150)留下批。

### 验证
- 净减 ~2.2k 行 · `test_v8_stage_specs` 90 passed · pytest 3 failed(baseline)/ 639 passed(删 post-feature 测试 −10)。

## v8.192 · pause-mark 计时排毒 · stage 内 R5 等待与工作分离(待优化 #5)

> 耗时归因:goal 均值 157m vs 中位 22m(max 128h)—— stage 内 R5 暂停(PRD 确认/预览确认/DB 确认)的**等用户墙钟全算成工作**(v8.172 只拆了 pm_acceptance)· 每次归因都要人肉排毒。

### 改动
- **`state.py pause-mark`**(新):emit R5 暂停点前打点(写 `open_pause`)· **下一个流程命令(start/complete/fix/retry)自动闭合**(`close_open_pause` 接进引擎 4 choke 点)· 等待累计进该 stage `await_minutes` —— resume 侧零纪律。
- **`_stage_durations`**:工作时长 = duration − await(breakdown 显示 `goal 20m(+等待30m)`)· 最耗时(工作)不再被等待污染。
- SKILL R5 协议加打点行。

### 验证
- code(engine helper+4 接线 · state.py 命令 · ship durations)· `test_pause_mark_v8192` +5 · v8.166 套件未破 · pytest 3 failed(baseline)/ 649 passed。

## v8.191 · external 机械成本三连修:preflight + 超时自动重试 + verify-fixes 增量重验

> 耗时归因(138 条 per-stage 数据)原因 2:external 的**机械 overhead**(非评审价值)—— 20× 实锤:「3 行改动跑 5 次 external(2 真轮+1 空跑+2 超时)review 墙钟 49m(80%)」「CLI 未登录到 review 才发现 → 降级折腾」「每采纳 finding 即全量重跑」。

### 改动(不动「评审必须真跑」原则 · 只砍机械成本)
- **`--preflight`**(①):review 干活前 which + **微 probe**(一次极小调用 · 秒级)验登录/网络/配额 E2E 通 · 失败此刻修环境 · 不烧完整评审墙钟才发现。
- **超时/空跑自动重试**(②):rc=124 / 空 stdout → **自动重试一次**(1.5x timeout · emit `attempts`/`timeout_sec_used`)· 省手动重跑轮;localconfig `external_review_timeout_sec` 调基础超时(长 review 项目)。
- **`--verify-fixes`**(③ · 仅 review):增量重验 —— base 锚**上一轮已评 commit**(结果文件 frontmatter `target_commit`)· prompt = 上轮 findings 全文 + 修复 diff · 任务 = 逐 finding 给 `fixed/not-fixed` verdict + 只查修复 diff 新问题 · **不全量重评**。结果落 `review-<model>-fixverify.md`(不 clobber 全量轮 · 供下轮再锚)· 锚点失效(rebase/同 commit)FAIL 提示退全量 · 与 `--prompt-doc` 互斥。
- review-stage.md 同步(external 步 + fix-retry 循环)。

### 验证
- code(`state.py` 4 helpers + cmd_external_review 三分支 + runners timeout/extra_prompt)+ doc · `test_external_mech_v8191` +12 · pytest 3 failed(baseline)/ 644 passed。

## v8.190 · main-sync 回收 teamwork auto-stash · 治 stash 累积无回收(harvest 跨两次最高频)

> 第二轮 harvest(163 条 · +74):「ship 收尾 / 主工作区 auto-stash 累积无回收」**26×**(上次 23×)· **跨两次 harvest 稳居第一**。main-sync `stash-pull` 每次备份 stash 但不 pop → 跨 feature/session 累积 **11+** · human 难判哪些可 drop。

### 改动
- **main-sync 回收 stash**(新 · 默认自动跑):`_reclaim_stashes` 只认 **teamwork 自建**的 main-sync stash(消息标识)· **drop 可证冗余的**(空 / 内容已在分支 · `git apply --reverse --check` 通过)· 剩含未合内容的 **surface**(feature 标签 + hint)· 🔴 **绝不碰用户自己的 stash**。
- **`--drop-stashes`**:用户确认不需要任何备份 → 全清 teamwork main-sync stash。
- ship-finalize / 规划 finalize / 独立 main-sync 都**自动回收**(emit `stash_reclaim`)· 不再累积。
- **测试** `test_stash_reclaim_v8190` +5(drop 冗余 / 留 live / 不碰用户 / drop-all / hint)。

### 验证
- code(`_v8_ship` `_reclaim_stashes` + main-sync emit + `--drop-stashes`)+ doc(ship-stage §6 · SKILL 命令行)· pytest 3 failed(baseline)/ 632 passed。

## v8.189 · 规划收尾 finalize:用户合并后切回主分支 + 清 worktree + 净化主分支(= ship2)

> 用户续 v8.188:规划 MR 建好提示用户后,用户说「已合并」→ 该进规划收尾流程:**切回主分支、清理 planning worktree、净化主分支**。补全 = 把规划收尾对齐 feature 的 **ship1→ship2** 两段。

### 改动(feature-planning Step 9 + planning-check)
- **收尾-2 finalize**(新 · = feature `ship-finalize`/ship2):用户说「已合并」→ 3 步镜像 ship-finalize:① `cd` 回主工作区 ② `git worktree remove` 清 planning worktree ③ `state.py main-sync --merge-target <mt>` 净化主分支(v8.145 起**不依赖 feature** · fetch + 按策略 pull 合并后规划产物 · 主工作区干净+最新)。
- **收尾-1** 的 MR 提示改成「合并完回来说『已合并』· 我进收尾」(引导第二段)。
- `planning-check` `worktree_setup` + checklist item 6 同步 finalize。

### 验证
- doc(feature-planning Step 9)+ code(`planning-check`)· `test_state` planning 4 passed · pytest 3 failed(baseline)/ 627 passed。
