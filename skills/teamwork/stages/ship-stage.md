# Ship Stage

---

## 怎么做

### 1. ship-start
`state.py ship-start --feature X` · 校验前置(pm_acceptance.decision=approved_and_ship)

### 2. ship-phase sanitize
`--action sanitize` · 净化 commit 记录(检查 residual / suspicious 文件)

### 3. ship-phase push
`--action push --feature-head-commit ... --git-host gitlab --mr-creation-method cli-glab --mr-url ...` · push feature 分支 + CLI 创 MR

### 4. ⏸️ 等用户在平台合并
输出 MR URL 给用户 · Phase 1 结束

### 5. cd 回主工作区
`cd <main-tree>` · 治本 P0-156 · 后续命令必主 tree

### 6. git fetch + pull
git fetch origin <merge_target>; git pull --ff-only

### 7. ship-phase confirm-merged
`--action confirm-merged --merge-commit-hash ... --merge-detection-method branch-contains` · pushed → merged

### 8. 清理 worktree + branch
`git worktree remove <wt-path>; git branch -d <branch>`

### 9. ship-phase cleanup
`--action cleanup --status cleaned` · phase 必 merged(P0-124 hard gate)

### 10. ship-complete
`state.py ship-complete` · 自动转 completed

---


## 必读 cite 清单(P0-11)

本 stage 是 PMO 编排操作(不涉及内容创作角色)· **无 cite 要求**。

## 注意事项

### 坑 1 · confirm-merged / cleanup 在 worktree 跑
state.json 在 worktree 被 cleanup 时删除丢失(治本 ADMIN-F013)。
 **对策**:P0-156 物化拦截 · linked worktree FAIL · 必 cd 主工作区

### 坑 2 · cleanup --status cleaned 但 phase ≠ merged
destructive op 前合并未确认 · state 不一致。
 **对策**:P0-124 hard gate · phase 必 merged + merge_commit_hash 非空才能 cleaned

### 坑 3 · 用 git push hint URL 当 MR URL
git push 输出的 "remote: To create a merge request..." 是 trap · 不是首选。
 **对策**:P0-113 CLI-first · 必跑 gh/glab 拿真实 URL · 失败才 URL 兜底

### 坑 4 · close-unmerged 滥用
MR 暂时关闭就跑 close-unmerged · 后续重开困难。
 **对策**:close-unmerged 仅用于真正"放弃合入" · 暂时关用 --abandon=false 留口子

### 坑 5 · Ship 后想 reset-prev
状态不可逆 · 远程已动。
 **对策**:P0-6 reset-prev 物化拦截 · Ship 后 FAIL · 走 close-unmerged 或新 Feature 修复

---

## Output Contract(产物形态参考)

### `state.ship.phase`
null → pushed → merged 状态机 · 物化校验

### `state.ship.mr_url / mr_create_url`
CLI 创建的 URL(cli-*)或兜底 URL(url-fallback)

### `state.ship.merge_commit_hash`
confirm-merged 必传 · git 校验存在

### `state.ship.worktree_cleanup`
cleaned / deferred / n_a · cleaned 必 phase=merged

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `SHIP_SPEC`
- 入口规范:[../TRIAGE.md](../TRIAGE.md)
