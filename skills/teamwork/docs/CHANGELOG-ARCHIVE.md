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
