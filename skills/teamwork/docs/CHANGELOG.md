# Changelog

> 📦 v8.79 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**只留最近 1 版**(每次发布把上一版迁入归档)。

## v8.80 · ship-finalize 去直推 → 收尾 MR(投递重构 · 兼容保护分支 · 主工作区只 pull · dev-only)

> 用户拍板:ship2(finalize)直推 merge_target 在保护分支下不兼容 · 且后续要给 finalize 加实质改动(归档/ROADMAP)· 直推「单文件零业务影响」的合法性不再成立。去直推 · 收尾改动也走一个 MR · gh/glab 自动合 · 合并后才回主工作区删 worktree + pull。

### 变更:step 5 finalize-push(直推)→ finalize-deliver(收尾 MR · AI 驱动)
- state.py 把收尾 commit(state.json + review-log)暂存到 `ship-finalize/<id>` 分支(git plumbing 零 checkout · 复用 v8.18 commit-building)· **不再直推 merge_target**。
- 交接 AI 用 **gh/glab 创 MR + 自动合并**(state.py 不代跑 CLI · 与 Phase 1 创 MR 同模型 · 架构一致)· emit `PENDING` + next_action + resume。
- **降级阶梯**:gh/glab 不可用(未登录 / token 无 scope / 网络)→ 报明确原因 · 用户解决后重跑;无法自动合 → 给 MR(create)链接让用户手动合 → 合后重跑。
- **可重入 · 语义检测**:重跑判「已交付」= origin/merge_target 上 state.json `current_stage == completed`(抗 squash 合并 + save_state 非确定性 · 不靠 commit ancestor / 字节 no-delta)。
- **reorder**:worktree-remove(step 6)+ main-sync(step 7)**移到收尾 MR 合并之后**(未合 PENDING 即 return · 不删 worktree · 投递没成 worktree 还在可重试)。

### 效果
- **merge_target 全程只经 MR** → 兼容保护分支(原直推撞 protect-rule 只能降级)。
- **主工作区只 pull · ship 不再制造脏 main**(收尾改动不在本地直接 commit)。
- **不持久化额外字段**:本地 state.json == 交付内容 → step 7 pull 不分叉冲突。

### 实现 + 验证
- `_v8_ship.py`:`_finalize_push_plumbing` 加 `push_ref/force`(推收尾分支)· 新 `_remote_finalize_delivered`(语义判定)· 新 `_ship_finalize_deliver_pending`(PENDING 交接)· 重写 step 5 + 删 step 6 旧「finalize 失败保留 worktree」死分支。
- pytest:**67 failed / 439 passed**(baseline 67 · 新增 2 deliver 测试[首跑暂存+PENDING / 全周期 暂存→合→交付→幂等]· 零回归)。
- ship-stage.md step 表 + §12 同步(直推例外标历史)。

### 后续
- v8.81:archive(zip+rm)+ distill(知识层 6 项 ship1 闸门)+ ROADMAP forced-marker —— 架在本投递重构之上(实质改动随收尾 MR 走)。

---

## 更早版本(v8.79 → v1)

完整历史已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)(v8.0 之前的 v7/v6/… 旧系统亦在此)。
