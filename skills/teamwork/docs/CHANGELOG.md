# Changelog

> 📦 v8.92 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**只留最近 1 版**(每次发布把上一版迁入归档)。

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
