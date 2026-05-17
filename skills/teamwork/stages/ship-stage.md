# Ship Stage

---

## 怎么做

### 1. ship-start
`state.py ship-start --feature X` · 校验前置(pm_acceptance.decision=approved_and_ship)

### 2. ship-phase sanitize
`--action sanitize` · 净化 commit 记录(检查 residual / suspicious 文件)

### 3. ship-phase push
`--action push --feature-head-commit ... --git-host gitlab --mr-creation-method cli-glab --mr-url ...` · push feature 分支 + CLI 创 MR

### 4. ⏸️ Phase 1 完成 · 等用户在平台合并(R5 标准暂停点)

🔴 **PMO 必输出 R5 标准 1/2/3 选项格式**(不要自由发挥"合并后回复『已合并』"):

```markdown
⏸️ Phase 1 完成 · MR #<num> 已创建 · 等用户在平台 review + 合并

请选择:

1. ✅ **已合并**(MR 已 merge) 💡 推荐(若你刚点 merge)
   理由:常规路径 · 进 Phase 2 同步 state.json finalize + 清理 worktree
   动作:回 `已合并` / `merged` / `1` → PMO 跑 confirm-merged

2. ⏳ **暂未合并 / 还在 review**
   理由:平台审批中 / 等其他人合 / 暂存
   动作:无需操作 · 状态停 phase=pushed · 任意时刻回来回 `1` 继续

3. ❌ **撤回 / 关闭 MR**
   理由:发现问题需重做 / 不再需要
   动作:回 `撤回` → close-unmerged(`--abandon=true` 终态 / `--abandon=false` 留口子)

📚 决策参考:MR URL = <url> · 平台 review 状态 / 评论 / CI 结果
```

### 5. cd 回主工作区
`cd <main-tree>` · 治本 P0-156 · 后续命令必主 tree

### 6. 切到 merge_target branch + fetch + pull
```bash
git fetch origin <merge_target>
git switch <merge_target>            # 🔴 必切 · MR merge 后 feature dir 已在该 branch
git pull --ff-only origin <merge_target>
```
此时主工作区 `{main-tree}/{feature_dir}` = MR 合入后的快照 · 含旧 `state.json`(phase=pushed)。
**为什么必切**:后续 §7 confirm-merged + §10 cleanup 都用主工作区 `{feature_dir}` · 不在 merge_target branch → feature_dir 不存在 / state.json not found。

### 7. ship-phase confirm-merged(`--feature` 指主工作区 feature dir)
```bash
state.py ship-phase --action confirm-merged \
  --feature {main-tree}/{feature_dir} \
  --merge-commit-hash ... \
  --merge-detection-method branch-contains
```
state.py 把主工作区 merge_target branch 上的 `state.json` 更新到 `phase=merged`。
🔴 **不要用 worktree 路径作 --feature**(用 worktree 路径会让 confirm-merged 写到 worktree · 后续要 cherry-pick 才能同步 · 平添复杂度)。

### 8. finalize 直推(§12 直推例外 · 在主工作区 merge_target branch)
```bash
git add -A {feature_dir}/                                # R-S7 范围规则
git commit -m "chore({Feature}): finalize state.json (ship phase=merged)"
git push origin {merge_target}
```
🔴 单文件 + 仅状态字段 + 零业务影响 → 直推不走 MR(详 §12 适用范围 + 禁止滥用)。

### 9. 清理 worktree + branch
```bash
git worktree remove {wt-path}
git branch -d {branch}
```

### 10. ship-phase cleanup(--feature 同 §7 · 仍主工作区 feature dir)
```bash
state.py ship-phase --action cleanup --status cleaned \
  --feature {main-tree}/{feature_dir}
```
P0-124 hard gate · phase 必 merged + merge_commit_hash 非空。

### 11. ship-complete
`state.py ship-complete --feature {main-tree}/{feature_dir}` · 自动转 completed。

### 异常 · close-unmerged
放弃合入 → `--action close-unmerged --abandon=true` · 暂时关闭(后续重开)→ `--abandon=false`(留口子 · 不进 closed 终态)。

---

## 必读 cite 清单(P0-11)

本 stage 是 PMO 编排操作(不涉及内容创作角色)· **无 cite 要求**。

📎 **物化拦截清单**(已在工具层 BLOCKED + hint · spec 不重复展开):
- P0-6 ship 后 reset-prev FAIL
- P0-113 push 必 CLI-first 拿 MR URL · 不接受 git push hint URL
- P0-124 cleanup --status cleaned 必 phase=merged + merge_commit_hash 非空
- P0-156 confirm-merged / cleanup 必 cd 主工作区(linked worktree FAIL)

---

## 12. Phase 2 finalize · state.json 直推例外

confirm-merged 后,状态:
- worktree 内 state.json 已更新到 phase=merged(本地)
- merge_target 远程上的 state.json **还是 Phase 1 时的 phase=pushed**(因为 MR 已合并 · 但 state.json 是合并前的快照)

**合法直推**(不走 MR)· 适用范围:

| 流程 | 允许直推的文件 | 允许的字段 |
|---|---|---|
| Feature | `state.json`(单文件) | 仅状态字段:`current_stage` / `completed_stages` / `ship.phase` / `ship.shipped` / `ship.merge_*` / `worktree_cleanup` / `completed_at` 等 |
| Bug | `BUG-REPORT.md`(单文件) | 仅 frontmatter 元数据:`current_stage` / `phase` / `shipped` / `merge_commit_hash` 等 |

**直推命令**(在主工作区 cwd):
```bash
# Step 0 · 二次验证合入(防 user-reported 误报 / confirm-merged 后状态变化)
git fetch origin <merge_target>
git branch -r --contains <merge_commit_hash> | grep origin/<merge_target>
# 命中 = 真合入 · 继续
# 空 = 未合入 → BLOCKED · 排查 MR 状态(可能被 revert / 误报)· 不要直推

# Step 1 · finalize 直推
git pull --ff-only origin <merge_target>
git cherry-pick <state.json finalize commit>      # 或 git checkout/cp 同效
git push origin <merge_target>
```

**为什么是合法例外**:
- 单文件 + 仅状态字段 = 零业务影响 · 不需要 review
- finalize 是流程闭环的元数据同步 · 不是新功能/修复 · review 视角无 finding 可贡献
- 走 MR 浪费多角色 review round-trip · 显式低 ROI

**push 失败降级**:
- `git push` exit≠0 → 把 finalize 留在 feature 分支 + state.concerns 加 WARN
- 不阻塞 ship-cleanup / ship-complete
- 用 `state.py ship-phase --action confirm-merged --merge-target-push-failed --failed-reason {conflict|protect-rule|network|other}` 记录

**禁止滥用**:
- ❌ 业务文件直推(代码 / PRD / TC / TECH 等)→ 必走 MR
- ❌ state.json 中非状态字段(blocking / planned_execution 等业务字段)→ 必走 MR
- ❌ Bug 流程 BUG-REPORT.md 正文修改 → 必走 MR(只允许 frontmatter)

---

## 13 · R-S7 · git add 范围规则(强红线)

**任何 commit Feature 产物**(各 stage-complete 后 + ship-phase push 前):

```bash
# ✅ 必这样(范围明确 · 一并 add state.json + review-log.jsonl 等状态档)
git add -A <feature_dir>/

# ❌ 禁止(state.py 持续写的状态档不在 PMO 视野 · 列文件名 = 凭记忆 = 必漏)
git add <feature_dir>/dev/*.md <feature_dir>/PRD.md
```

**理由**:`state.json` + `review-log.jsonl` 由 state.py 在 stage-complete 持续写 · PMO 列文件易漏 → MR 不含状态档 → 下游评审看不到 stage/review 历史。`-A {feature_dir}/` 范围严格限定 · 不会污染其它路径(.env/credentials 等)。**无例外**(单文件改也用 -A · 防误漏)。

**实证**:PTR-A018(aon-core) MR !190 push 后核实漏 state.json + review-log.jsonl · 补 push c00109ce..09c41c6a。

**违规后修复**:已 push → 在 feature 分支 `git add -A {feature_dir}/ && commit && push`(fast-forward · 不破 review)· 已 merge → §12 直推例外补 push 到 merge_target。

**治本路径(后续 P0 候选)**:`tools/_v8_ship.py:_handle_ship_sanitize` 加 `git ls-files {feature_dir}/state.json` + `review-log.jsonl`(rounds>0 时)校验 · 缺失 → BLOCKED with hint(可枚举进脚本 · R0 哲学)。

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
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
