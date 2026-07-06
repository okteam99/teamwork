# Changelog Archive

> 📦 **定期清空**:本文件只暂存从 [CHANGELOG.md](./CHANGELOG.md) keep-5 轮转出的条目 · 膨胀时整体清空 —— 完整历史 = **git 提交历史**(永不丢 · `git log` / `git show` 按需追溯)· 工作区不热存。
> 上次清空:**v8.193**(2026-07-06 · 清除 v8.128 → v8.187 共 60 版条目 · 约 1.0k 行)。

---
## v8.188 · 规划收尾:暂停问合入 merge_target → 建 MR → 提示用户合并 → 停(不自动起下一 feature)

> 实证 AON KA-PAGES:AI 规划完成后**自己** commit→push→建 draft MR,然后**立刻**跳进下一个 feature 的 prepare(还把新 feature 的 `merge_target` 设成**未合并的** `planning/ka-pages` 分支)—— 没有「是否合入 merge_target」确认暂停点,也没有「MR 建好 → 提示用户合并 → 停」。

### 改动(feature-planning Step 9 + planning-check)
- **规划收尾框成 3 步**(同 feature ship1):① R5 暂停问「**是否合入 `merge_target`**」② 确认后 worktree 内 commit+push planning 分支+开 MR(target=merge_target)③ 🔴 ⏸️ **提示用户合并 + 到此结束**。
- **🔴 不自动起下一 feature**:启动实施是**用户合并规划 MR 之后**的独立决策 · 🔴 **别叠 feature 在未合并 planning 分支**(feature `merge_target` = 集成分支 dev/staging · 非 planning 分支 · 否则实现 diff 混未合并规划、基线不稳)。
- `planning-check` `worktree_setup` + checklist item 6 同步(item 6 顺带修 v8.184 遗留的「主工作区直推」旧措辞)。

### 验证
- doc(feature-planning Step 9)+ code(`planning-check`)· `test_state` planning 4 passed · pytest 3 failed(baseline)/ 627 passed。
## v8.189 · 规划收尾 finalize:用户合并后切回主分支 + 清 worktree + 净化主分支(= ship2)

> 用户续 v8.188:规划 MR 建好提示用户后,用户说「已合并」→ 该进规划收尾流程:**切回主分支、清理 planning worktree、净化主分支**。补全 = 把规划收尾对齐 feature 的 **ship1→ship2** 两段。

### 改动(feature-planning Step 9 + planning-check)
- **收尾-2 finalize**(新 · = feature `ship-finalize`/ship2):用户说「已合并」→ 3 步镜像 ship-finalize:① `cd` 回主工作区 ② `git worktree remove` 清 planning worktree ③ `state.py main-sync --merge-target <mt>` 净化主分支(v8.145 起**不依赖 feature** · fetch + 按策略 pull 合并后规划产物 · 主工作区干净+最新)。
- **收尾-1** 的 MR 提示改成「合并完回来说『已合并』· 我进收尾」(引导第二段)。
- `planning-check` `worktree_setup` + checklist item 6 同步 finalize。

### 验证
- doc(feature-planning Step 9)+ code(`planning-check`)· `test_state` planning 4 passed · pytest 3 failed(baseline)/ 627 passed。
## v8.190 · main-sync 回收 teamwork auto-stash · 治 stash 累积无回收(harvest 跨两次最高频)

> 第二轮 harvest(163 条 · +74):「ship 收尾 / 主工作区 auto-stash 累积无回收」**26×**(上次 23×)· **跨两次 harvest 稳居第一**。main-sync `stash-pull` 每次备份 stash 但不 pop → 跨 feature/session 累积 **11+** · human 难判哪些可 drop。

### 改动
- **main-sync 回收 stash**(新 · 默认自动跑):`_reclaim_stashes` 只认 **teamwork 自建**的 main-sync stash(消息标识)· **drop 可证冗余的**(空 / 内容已在分支 · `git apply --reverse --check` 通过)· 剩含未合内容的 **surface**(feature 标签 + hint)· 🔴 **绝不碰用户自己的 stash**。
- **`--drop-stashes`**:用户确认不需要任何备份 → 全清 teamwork main-sync stash。
- ship-finalize / 规划 finalize / 独立 main-sync 都**自动回收**(emit `stash_reclaim`)· 不再累积。
- **测试** `test_stash_reclaim_v8190` +5(drop 冗余 / 留 live / 不碰用户 / drop-all / hint)。

### 验证
- code(`_v8_ship` `_reclaim_stashes` + main-sync emit + `--drop-stashes`)+ doc(ship-stage §6 · SKILL 命令行)· pytest 3 failed(baseline)/ 632 passed。
## v8.191 · external 机械成本三连修:preflight + 超时自动重试 + verify-fixes 增量重验

> 耗时归因(138 条 per-stage 数据)原因 2:external 的**机械 overhead**(非评审价值)—— 20× 实锤:「3 行改动跑 5 次 external(2 真轮+1 空跑+2 超时)review 墙钟 49m(80%)」「CLI 未登录到 review 才发现 → 降级折腾」「每采纳 finding 即全量重跑」。

### 改动(不动「评审必须真跑」原则 · 只砍机械成本)
- **`--preflight`**(①):review 干活前 which + **微 probe**(一次极小调用 · 秒级)验登录/网络/配额 E2E 通 · 失败此刻修环境 · 不烧完整评审墙钟才发现。
- **超时/空跑自动重试**(②):rc=124 / 空 stdout → **自动重试一次**(1.5x timeout · emit `attempts`/`timeout_sec_used`)· 省手动重跑轮;localconfig `external_review_timeout_sec` 调基础超时(长 review 项目)。
- **`--verify-fixes`**(③ · 仅 review):增量重验 —— base 锚**上一轮已评 commit**(结果文件 frontmatter `target_commit`)· prompt = 上轮 findings 全文 + 修复 diff · 任务 = 逐 finding 给 `fixed/not-fixed` verdict + 只查修复 diff 新问题 · **不全量重评**。结果落 `review-<model>-fixverify.md`(不 clobber 全量轮 · 供下轮再锚)· 锚点失效(rebase/同 commit)FAIL 提示退全量 · 与 `--prompt-doc` 互斥。
- review-stage.md 同步(external 步 + fix-retry 循环)。

### 验证
- code(`state.py` 4 helpers + cmd_external_review 三分支 + runners timeout/extra_prompt)+ doc · `test_external_mech_v8191` +12 · pytest 3 failed(baseline)/ 644 passed。
## v8.192 · pause-mark 计时排毒 · stage 内 R5 等待与工作分离(待优化 #5)

> 耗时归因:goal 均值 157m vs 中位 22m(max 128h)—— stage 内 R5 暂停(PRD 确认/预览确认/DB 确认)的**等用户墙钟全算成工作**(v8.172 只拆了 pm_acceptance)· 每次归因都要人肉排毒。

### 改动
- **`state.py pause-mark`**(新):emit R5 暂停点前打点(写 `open_pause`)· **下一个流程命令(start/complete/fix/retry)自动闭合**(`close_open_pause` 接进引擎 4 choke 点)· 等待累计进该 stage `await_minutes` —— resume 侧零纪律。
- **`_stage_durations`**:工作时长 = duration − await(breakdown 显示 `goal 20m(+等待30m)`)· 最耗时(工作)不再被等待污染。
- SKILL R5 协议加打点行。

### 验证
- code(engine helper+4 接线 · state.py 命令 · ship durations)· `test_pause_mark_v8192` +5 · v8.166 套件未破 · pytest 3 failed(baseline)/ 649 passed。
