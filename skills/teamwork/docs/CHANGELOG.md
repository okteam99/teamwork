# Changelog

> 📦 v8.81 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**只留最近 1 版**(每次发布把上一版迁入归档)。

## v8.82 · ship2 归档本体(archive · 过程层 feature 目录 zip+rm · 随收尾 MR · 代码是唯一真相 · dev-only)

> 用户:归档的主要目的是**防止 AI 检索到过时的 feature 信息**(过程稿交付即 drift)· 代码是唯一真相。做完(distill 把知识 graduate 到知识层后)直接归档 —— 过程层 `docs/features/{id}/` zip 进 `_archive/`,原目录删。承接 v8.81(distill 是归档的知识安全前置)。

### finalize-deliver 加归档本体(`archive_on_ship` · 默认 true)
- `ship-finalize` step 5 收尾分支不止同步 `state.json` · 而是把交付的**过程层** feature 目录整体 **zip 进 `features/_archive/<id>.zip`**(arcname=`<id>/...` 自描述 · 固定 mtime 可复现)· 追加 `_archive/INDEX.md` 一行索引 · 并在同一收尾 commit **删除 feature 目录的所有 tree 条目** → push `ship-finalize/<id>` → 交接 AI 创 MR + 自动合(同 v8.80 去直推 · merge_target 只经 MR)。
- **删而不是留**:过程稿(PRD/TECH/report)交付即开始与代码 drift · 留着会被 AI 当真相检索 → 归档为 zip 快照 · 知识层(§14 distill)才是「代码的文档」。
- **随收尾 MR 合**(MR 合入后目录才从 merge_target 消失 · 经 review)· distill(v8.81)是其知识安全前置。

### 已交付判定改为「zip 存在」+ 幂等 3rd-run
- 已交付 = `git cat-file -e origin/<merge_target>:features/_archive/<id>.zip`(抗 squash · 替代 v8.80 的 `state.json current_stage==completed` 语义判定)。
- step 7 main-sync:归档已交付 → 先把本地 feature 目录恢复 HEAD 干净态(内容已进 zip)→ `ff-pull` 干净删除该目录 + 落地 zip(防「would be overwritten by merge」)。
- **幂等 3rd-run**:目录已删 → state-sync 找不到 state.json · 但检测到 zip 已在 merge_target → emit 幂等 `PASS`(终态 · 无动作)· 不再误 BLOCK。
- **opt-out**:`archive_on_ship: false` → 退回 v8.80(收尾 MR 只同步 `state.json` 终态 · 不归档 · 目录留存)。

### 实现 + 验证
- `_v8_ship.py`:`ARCHIVE_DIR_NAME` + `_read_archive_on_ship` / `_archive_repo_paths` / `_remote_archive_delivered` / `_build_archive_zip` / `_build_archive_index` / `_stage_archive_commit`(git plumbing 零 checkout · `--force-remove` 删目录 tree 条目)/ `_purge_local_feature_dir_for_archive` / `_archive_idempotent_zip` · step 5 接线 + step 7 purge + 3rd-run 前置 + emit `archived`。
- templates/teamwork_localconfig.json + config.md:`archive_on_ship`(默认 true)。
- pytest:**67 failed / 460 passed**(baseline 67 · 新增 14 测试[config 默认/false/非法 · zip 打包/确定性 · 路径推导/目录已删 · 首跑暂存 zip+rm+INDEX · 终态进 zip · 全周期归档+清本地+幂等 · archive off 回退]· 零回归)。旧 v8.80 finalize 测试加 `archive_on_ship:false` 锚定非归档路径。
- ship-stage.md §15(归档本体)+ §12/step5/step7 接线;CHANGELOG 轮转(v8.81 → 归档)。

### 后续
- ROADMAP/WS forced-marker(规划层翻牌硬标记 · 当前 v8.77 `_planning_backref_reminder` 软提示已覆盖)留 v8.83。
