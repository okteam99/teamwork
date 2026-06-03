# Ship Stage

> **Phase 1**(§1-§4):在 **worktree 内**跑(sanitize/push 需 feature branch checkout · git push 必从 worktree)
> **Phase 2**(§5-§7):在 **主工作区**跑一条 `state.py ship-finalize`(7 步自动编排 · 可重入)

---

## 怎么做

### 1. ship-start(在 worktree 内)
`state.py ship-start --feature X` · 校验前置(pm_acceptance.decision=approved_and_ship)

### 2. ship-phase sanitize(在 worktree 内)
`--action sanitize` · 净化 commit 记录(检查 residual / suspicious 文件)

### 3. ship-phase push(在 worktree 内)
`--action push --feature-head-commit ... --git-host gitlab --mr-creation-method cli-glab --mr-url ...` · push feature 分支 + CLI 创 MR

### 4. ⏸️ Phase 1 完成 · 等用户在平台合并(R5 标准暂停点)

🔴 **`auto_mode=true` 也必停此暂停点** —— 用户需在 git host 平台手动 merge MR · AI 无法代办(详 [SKILL.md § auto_mode=true 时各暂停点行为](../SKILL.md))。

🔴 **PMO 必输出 R5 标准 1/2/3 选项格式**(不要自由发挥"合并后回复『已合并』"):

```markdown
⏸️ Phase 1 完成 · MR #<num> 已创建 · 等用户在平台 review + 合并

请选择:

1. ✅ **已合并**(MR 已 merge) 💡 推荐(若你刚点 merge)
   理由:常规路径 · 进 Phase 2 同步 state.json finalize + 清理 worktree
   动作:回 `已合并` / `merged` / `1` → PMO cd 主工作区 · 跑 `ship-finalize`

2. ⏳ **暂未合并 / 还在 review**
   理由:平台审批中 / 等其他人合 / 暂存
   动作:无需操作 · 状态停 phase=pushed · 任意时刻回来回 `1` 继续

3. ❌ **撤回 / 关闭 MR**
   理由:发现问题需重做 / 不再需要
   动作:回 `撤回` → close-unmerged(`--abandon=true` 终态 / `--abandon=false` 留口子)

📚 决策参考:MR URL = <url> · 平台 review 状态 / 评论 / CI 结果
```

### 5. Phase 2:ship-finalize(一条命令 · 在主工作区跑)

用户确认已合并(§4 选项 1)后 · **cd 回主工作区** · 跑一条命令完成 Phase 2 全部 8 步:

```bash
cd <main-tree>                                        # 🔴 必在主工作区(P0-156)
state.py ship-finalize --feature <main-tree>/<feature_dir>
```

ship-finalize 内部自动编排(**可重入** · 失败步骤修复后重跑即续):

| 步 | 动作 | 内容 |
|---|---|---|
| **0** | **state-sync(v8.16)** | **自动 `git fetch` + 安全 ff-pull merge_target(拉下 MR 合并后的 features dir)· 检测主工作区 state.json:不存在/缺 `ship.feature_head_commit` → 从 worktree 内 state.json 同步完整态(主工作区拉下的是合并前快照 · 完整态在 worktree)。治本 SVC-CORE-B006 case(详 §12 实证)** |
| 1 | verify-merge | `git fetch` + `merge-base --is-ancestor` 验证 feature_head 已进 merge_target |
| 2 | confirm-merged | `ship.phase` pushed → merged |
| 3 | cleanup | `ship.worktree_cleanup` = cleaned / n_a |
| 4 | ship-complete | `current_stage` → completed |
| 5 | **finalize-deliver(v8.80 去直推 · v8.82 加归档 · v8.93 规划层 back-ref 同 MR)** | **v8.93**:暂存收尾分支**前先停 `planning-backref` 暂停点** —— AI 翻规划层 back-ref(ROADMAP/WS/teamwork-space.md/变更单)→ `--planning-artifacts <files>` 随同一收尾 MR 合入(或 `--no-planning-changes` 跳过)· 详 §5.5。**去直推**:state.py 暂存收尾 commit 到 `ship-finalize/<id>` 分支 → 交接 AI 用 gh/glab **创 MR + 自动合并** → 重跑检测已合 → 续。**v8.82(`archive_on_ship`·默认 true)**:收尾分支同步 state.json + 把交付的**过程层** feature 目录 zip 进 `features/_archive/<id>.zip`(+ INDEX.md)· 从 merge_target **删原目录**(详 §15)· 已交付判定 = zip 在 merge_target 存在。未合 → emit `PENDING`。merge_target **只经 MR**(兼容保护分支 · 主工作区只 pull) |
| 6 | worktree-remove | 物理删 feature worktree + 本地 feature 分支(🔴 **收尾 MR 合并后**才删) |
| 7 | main-sync | 主工作区 `git fetch` + 安全 `git pull --ff-only`(让本地跟上 ship 结果)。**v8.82 归档已交付**:先把本地 feature 目录恢复 HEAD 干净态(内容已进 zip)→ ff-pull 干净删除该目录 |

**为什么必在主工作区**:step 6 worktree-remove 不能删自身所在 worktree · 且 Phase 2 状态同步语义属于 merge_target 主工作区(P0-156)。在 linked worktree 跑 → precheck FAIL · hint 给精确 cd 目标。

**AI 只在失败点干预**(其余全自动):
- **step 0 FAIL**(worktree 已被手工删 + 主工作区 state.json 不全):无路可走 · hint 排查 worktree path / --feature 路径 / 当前分支 · 或 bypass 后手工 finalize。
- **step 1 FAIL**(feature_head 不在 merge_target):两种可能 → ① MR 尚未合并 · 等用户;② squash / rebase 合并(见 §6)。按 R5 给用户 1/2 选项判断。
- **step 5 finalize-deliver PENDING(v8.80)**:收尾分支已暂存 · 待 AI 用 gh/glab 创 MR + 自动合。**降级**:gh/glab 不可用(未登录 / token 无 scope / 网络)→ 报明确原因给用户 · 解决后重跑;无法自动合 → 给 MR(create)链接让用户手动合 → 合后重跑。worktree **保留**(未交付不删)· 重跑可重入(语义检测已合 → 续删 worktree + pull)。
- **step 6 worktree-remove 失败**(worktree 占用等):降级 warning · state.json 已 finalize 不丢 · 按 hint 手动 `git worktree remove`。
- **step 7 pull 跳过**(主工作区不在 merge_target / 工作树有未提交改动 / 与 origin 分叉):降级 warning · 已 fetch · 按 hint 手动 `git pull --ff-only`。

### 5.5 规划层 back-reference 翻牌(随收尾 MR 一起合入 · v8.93 · 🔴 必做)

🔴 ship-finalize 进 step 5 finalize-deliver 时 · **暂存收尾分支之前先停在 `planning-backref` 暂停点**(emit PENDING + brief):须把**规划层 back-reference** 翻牌 —— **这是 ship 的一部分 · 不是「后续 / 非本次范围 / 下次规划」**。

- **为什么翻牌**:`feature = 某 BL 的落地`。规划期把 BL 写进 ROADMAP 是「📋 规划中」· 落地完不翻成「✅ 已交付」→ 规划层(ROADMAP/WS 进度)与执行层永久脱节 · 进度统计失真。
- **为什么随收尾 MR**(v8.93 治本):back-ref 翻牌与归档(都表示「本 feature 已交付」)本是**同一件事** · 应**原子合入同一个收尾 MR**。旧 v8.77 把它当 finalize **之后**的 post-step + **直推 merge_target** —— 与 v8.80「去直推」自相矛盾(保护分支会拒推)· 且收尾 MR 此刻早已关闭 → 规划层物理塞不进 → 非原子 + 直推隐患(治本 case:aon ADMIN-F260603063006 · staging 受保护 · 第三笔直推被拒)。
- **做什么**:① AI 判断这几处哪些要翻「📋 规划中 → ✅ 已交付」(只改相关的 · 本质是 AI 自决):ROADMAP 对应 BL(若是 WS 最后一个 BL → WS 标完成)· `product-overview/workstream/WS-NN.md`(WS 进度)· `teamwork-space.md`(工作区索引 · 按需)· 项目变更单(如 `BG-NNN.md` 阶段状态 · 按需);② 在**主工作区**改好这些文件(**不要 commit** · ship-finalize 会随收尾 MR 带走)。
- **然后**:`state.py ship-finalize --feature <path> --planning-artifacts <逗号分隔相对路径>` → state.py 把这些文件随 {归档 zip + 删目录 + 终态 state.json} **同一收尾分支**暂存(并还原工作树 HEAD 防 step7 ff-pull 冲突)→ 你创建并合并**一个**收尾 MR(归档 + 规划翻牌原子)→ 重跑 ship-finalize 续清理 worktree + 主分支 pull。
- **确无可翻**(ad-hoc Bug/Micro · 无关联 BL)→ `state.py ship-finalize --feature <path> --no-planning-changes` 显式跳过(找不到 BL 别急着跳:先读 `product-overview/workstream/` + `ROADMAP.md` 定位本 Feature 条目)。
- 🔴 **不 amend**:收尾分支一次打包成型 · 不重建已暂存分支;若暂存后才发现漏文件 → `git push origin --delete ship-finalize/<id>` 删分支再重跑 `--planning-artifacts`。

### 6. squash / rebase 合并(branch-contains 检测不到)

平台用 **squash** 或 **rebase** 合并 → feature commit hash 变了 · `branch-contains` 自动检测不到 → step 1 FAIL。
用户确认已合并后 · 带上 merge_target 上的合并 commit 重跑:

```bash
state.py ship-finalize --feature <path> --merge-commit-hash <merge_target 上的合并 commit>
```

检测方式记为 `user-reported` · concerns 自动加 INFO 留痕。

### 7. 手动子动作(ship-finalize 的退路)

ship-finalize 是 Phase 2 **推荐路径**。极端情况(脚本环境受限 / 调试 / 单步排查)可用 `ship-phase` 手动子动作逐步走:

```
ship-phase --action confirm-merged → ship-phase --action cleanup --status cleaned
→ §12 finalize 直推 → git worktree remove → ship-complete
```

两条路径状态机等价。手动路径要点:每条命令自己 cd 主工作区 · 不漏 §12 finalize 直推 · 不漏 worktree 清理。

### 异常 · close-unmerged
放弃合入 → `--action close-unmerged --abandon=true` · 暂时关闭(后续重开)→ `--abandon=false`(留口子 · 不进 closed 终态)。

---

## 必读 cite 清单(P0-11)

本 stage 是 PMO 编排操作(不涉及内容创作角色)· **无 cite 要求**。

📎 **物化拦截清单**(已在工具层 BLOCKED + hint · spec 不重复展开):
- P0-6 ship 后 reset-prev FAIL
- P0-113 push 必 CLI-first 拿 MR URL · 不接受 git push hint URL
- **v8.37 P0-113 物化**:`--mr-creation-method url-fallback` 时 · `git_host` 对应 CLI(github→gh / gitlab*→glab)若**已装 + 已认证** → **BLOCKED**(治本 SVC-CORE-B007 case · AI 退化用 git push hint URL)。逃生口:`--accept-cli-unavailable --reason '<具体原因>' --user-confirmed`(走 bypass log + concerns WARN 留痕)· 真不可用场景(网络隔离 / token scope 不够 / 强制内部流程)用此。
- P0-124 cleanup --status cleaned 必 phase=merged + merge_commit_hash 非空
- P0-156 ship-finalize / confirm-merged / cleanup 必在主工作区跑(linked worktree precheck FAIL)

---

## 12. Phase 2 finalize · 收尾投递(v8.80 去直推 → 收尾 MR)

> 🔴 **v8.80 变更**:step 5 已从「state.json 直推 merge_target」改为 **finalize-deliver**(收尾改动暂存到 `ship-finalize/<id>` 分支 → AI 用 gh/glab 创 MR + 自动合并 → 重跑语义检测已合)。**merge_target 全程只经 MR**(兼容保护分支)· 主工作区**只 pull · 不再制造脏 main** · worktree 删除/主分支 pull **在收尾 MR 合并之后**。降级:gh/glab 不可用 → 报因 + 用户解决重跑 / 给 MR 链接手合。详 CHANGELOG v8.80。
> 🔴 **v8.82 增量**:收尾 MR 不止同步 state.json · 默认(`archive_on_ship`)还把交付的过程层 feature 目录 **zip 进 `features/_archive/<id>.zip` + 删原目录**(防 AI 检索过时信息 · 代码是唯一真相)· 已交付判定改为「zip 在 merge_target 存在」。详 **§15**。
> 🔴 **v8.93 增量**:收尾 MR 再加上**规划层 back-ref 翻牌**(ROADMAP BL / WS / teamwork-space.md / 变更单 → 已交付)· 经 `--planning-artifacts` 随**同一收尾 MR** 原子合入(治本旧 v8.77 post-step 直推 merge_target 与「去直推」矛盾的隐患)· 详 **§5.5**。
> ⚠️ 下方「直推例外」段为 **≤v8.79 历史原理**(state-sync 实证仍有效 · 直推机制已被收尾 MR 取代)。

🟢 **实证 case · SVC-CORE-B006(2026-05-21)· step 0 state-sync 治本根因**:
Phase 1 `ship-phase sanitize / push` 写 state.json 后**不自动 commit**(by design · 防 MR 被 chore commit 弄脏)· 所以 push 到 feature 分支的 commit 不含完整 state.json(缺 `ship.phase=pushed` / `feature_head_commit` 等)。用户 merge MR 后 · 主工作区 `git pull` 拉下的 state.json 是合并前快照(不全)· Phase 2 step 1 verify-merge 读不到 `feature_head_commit` → FAIL。**完整态 state.json 永远在 worktree 内工作树**(sanitize/push 写入但未 commit)· v8.16 step 0 state-sync 自动把 worktree 内完整态拷到主工作区 · step 5 finalize-push 把完整态直推到 merge_target · 闭环。

confirm-merged 后,状态:
- worktree 内 state.json 已更新到 phase=merged(本地)
- merge_target 远程上的 state.json **还是 Phase 1 时的 phase=pushed**(因为 MR 已合并 · 但 state.json 是合并前的快照)

**合法直推**(不走 MR)· 适用范围:

| 流程 | 允许直推的文件 | 允许的字段 |
|---|---|---|
| Feature | `state.json` + `review-log.jsonl`(v8.18 multi-file) | 仅状态字段:`current_stage` / `completed_stages` / `ship.phase` / `ship.shipped` / `ship.merge_*` / `worktree_cleanup` / `completed_at` 等 |
| Bug | `BUG-REPORT.md`(单文件) | 仅 frontmatter 元数据:`current_stage` / `phase` / `shipped` / `merge_commit_hash` 等 |

🟢 **v8.18 治本 SVC-CORE-F028 case · 0 delta**:
- `merge_target_pushed_at` / `merge_target_push_failed=false` **预设在 plumbing 推之前**(写进同一 commit)· 推完 worktree state.json 与 commit 一致 · 无 delta
- 去掉 `merge_target_finalize_commit` **自引用字段**(commit X 自己的 hash 不可能装进 X)· audit 从 git log 反查 / ship-finalize emit JSON 顶层 `finalize_commit` 字段查
- `review-log.jsonl` ship stage_completed 行一并 plumbing 推(extra_files)· 不再 worktree 留 delta
- 旧实现每 Feature 留 ~12 行 delta + 主工作区与 origin 落后 → v8.18 成功路径 **0 delta** · step 7 main-sync ff-pull 直接走

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

## 14. ship1 知识沉淀闸门(distill · v8.81)

> 🔴 **过程 / 知识两层**:`docs/features/{id}/`(PRD/TC/TECH/report/state)= **过程层**(交付即历史快照 · 会 drift)· 而 `KNOWLEDGE.md`/`ADR`/`REG`/`retro`/`ARCHITECTURE.md`/`database-schema.md` = **知识层**(持久 · 须保鲜)。**「描述代码」的文档随代码进 MR** —— ship 前(Phase 1)把该 graduate 的知识提到知识层,**随本次 feature MR 一起被 review + 合**。

**硬闸门**:`ship-phase --action sanitize` **必带 `--distill`**(JSON · 知识层 6 项决策)· 缺 / 非法 / 缺项 → BLOCK。

```
--distill '{
  "knowledge":     "promoted <gotcha/约定> / none",     # KNOWLEDGE.md(project-specs)
  "adr":           "ADR-NNNN <决策> / none",            # docs/adr/(决策有备选+后果)
  "reg":           "REG-<case> / none",                 # e2e-registry(可复用测试场景)
  "retro":         "done / n/a",                        # docs/retros/(复盘)
  "architecture":  "updated <模块/接口> / no-change",   # docs/architecture/ARCHITECTURE.md
  "db_schema":     "updated <表> / no-change / data-only migration"  # docs/architecture/database-schema.md
}'
```

- **R0**:强制 AI **逐项走一遍**(每项记 `updated/promoted <what>` 或显式 `none`/`n/a` · 证明已判断)· **质量留 AI · 「走没走」进脚本**。
- 🔴 **迁移↔schema 机械校验**:feature diff 含 `migration` 文件 **且** `db_schema` 声明无变更 **且** `database-schema.md` 未更 → **BLOCK**(治本 schema 文档 drift)。纯数据迁移 → `db_schema` 写 `data-only migration`。
- 🔴 建了 ADR → `ARCHITECTURE.md`「技术设计决策」表应有对应行(architecture.md §)。
- **落点**:6 项写的知识层文件须在 worktree **commit**(随 feature MR 合)· 不是直接改主工作区。`ship["distill"]` 记录决策留痕。
- **为什么在 ship1(合入前)**:知识层是「代码的文档」→ 随代码同 MR 被确认;且它是 feature 目录归档(过程层 · §15)的**前置** —— 先把真相提到知识层,过程稿才能安心归档。

---

## 15. ship2 归档本体(archive · v8.82)

> 🔴 **过程层归档**:distill(§14)已把「描述代码」的知识 graduate 到知识层(随 feature MR 合)· 过程层 `docs/features/{id}/` 的使命已尽。**ship2 收尾 MR** 把它 zip 进 `features/_archive/<id>.zip` · 并从 merge_target **删原目录**。
>
> **为什么删而不是留**:归档的主要目的是**防止 AI 检索到过时的 feature 信息**(PRD/TECH 等过程稿交付即开始 drift · 与实际代码不匹配)。**代码是唯一真相** · 知识层是代码的文档 · 过程稿只留可追溯的 zip 快照。

**何时**:`ship-finalize` step 5 finalize-deliver(`archive_on_ship`·默认 true)· **随收尾 MR 一起合**(MR 合入后目录才从 merge_target 消失 · 经 review)。

**机制**(state.py 全自动 · AI 只在 PENDING 处创/合 MR):
1. step 1-4 把终态写进本地 feature 目录(含 `state.json current_stage=completed`)。
2. step 5 把整个 feature 目录打成 `features/_archive/<id>.zip`(arcname=`<id>/...` · 自描述)· 追加 `_archive/INDEX.md` 一行 · 并在收尾 commit 里 **删除 feature 目录的所有 tree 条目** · push 到 `ship-finalize/<id>` 分支 → emit `PENDING`(交接 AI 创 MR + 自动合 · 同 §12)。
3. 收尾 MR 合并后重跑:**已交付判定 = zip 在 `origin/merge_target` 存在**(抗 squash)· 续 step 6/7。
4. step 7 主工作区:先把本地 feature 目录恢复 HEAD 干净态(内容已进 zip)→ `ff-pull` 干净删除该目录 + 落地 zip。
5. **幂等 3rd-run**:目录已被删 → state-sync 找不到 state.json · 但检测到 zip 已在 merge_target → emit 幂等 `PASS`(已交付终态 · 无动作)。

**opt-out**:`archive_on_ship: false` → 退回 v8.80(收尾 MR 只同步终态 `state.json` · 不 zip · 目录留存)。详 templates/config.md。

**取历史**:`unzip features/_archive/<id>.zip` · 或读 `_archive/INDEX.md` 索引。

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `SHIP_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
