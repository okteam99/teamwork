# Changelog

> 📦 v8.86 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**只留最近 1 版**(每次发布把上一版迁入归档)。

## v8.87 · 修 ship2 归档后主工作区残留 feature 目录(state.json/review-log.jsonl · dev-only)

> 用户实证(SVC-F001):ship2 归档后 `_archive/<id>.zip` 已生成,但原 `<feature_dir>/` 仍残留 `state.json` + `review-log.jsonl`。预期:worktree 内 ship2 后,主工作区不应多出任何文件。

### 根因
v8.82 的 step 7 清理依赖「`checkout HEAD` 恢复 feature 目录 → ff-pull 删掉」。但 ff-pull **被跳过/失败**时(主工作区与 origin 分叉 / 非 merge_target 分支 / 有其他 dirty),恢复出来的 `state.json` 留在原地;`lingering worktree` 还可能把 `state.json` resurrect 回来 + 触发 ship-complete 重写 `review-log.jsonl` → 主工作区残留过程层文件。

### 修复(双保险 · zip 是真相)
- **step 7 最终保证**:`archive_delivered` 且当前在 merge_target → 强制物理清除本地 feature 目录(`git rm -r -f --ignore-unmatch` + `rmtree` 残余 untracked)· **不再依赖 ff-pull 成功**。staged 删除下次 pull 自愈 · 并 emit warning 留痕。
- **幂等路径兜底**:3rd-run(state-sync not-found + zip 已交付)也 `rmtree` 任何残留 feature 目录(防 untracked `review-log.jsonl` 残留)。

### 验证
- 新增 `test_v887_purges_even_when_ff_pull_skipped`:复刻「归档已交付 + 本地 main 与 origin 分叉 → ff-pull 跳过」· 断言 feature 目录(含 state.json/review-log.jsonl)仍被强制清除。
- pytest **3 failed / 464 passed**(baseline 3 = scan-spec 既有 · 零回归 · +1 测试)· 既有 `test_full_cycle_archives_and_purges`(clean 路径)仍绿(net 为 no-op)。
