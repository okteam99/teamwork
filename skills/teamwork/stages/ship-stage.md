# Ship Stage

> **Phase 1**(§1-§4):在 **worktree 内**跑(sanitize/push 需 feature branch checkout · git push 必从 worktree)
> **Phase 2**(§5-§7):在 **主工作区**跑一条 `state.py ship-finalize`(自动编排 · 可重入)

---

## 怎么做

### 1. ship-start(在 worktree 内)
`state.py ship-start --feature X` · 校验前置(pm_acceptance.decision=approved_and_ship)

### 2. ship-phase sanitize(在 worktree 内)
`--action sanitize` · 净化 commit 记录(检查 residual / suspicious 文件)· 必带 `--distill`(§14)

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

用户确认已合并(§4 选项 1)后 · **cd 回主工作区** · 跑一条命令完成 Phase 2:

```bash
cd <main-tree>                                        # 🔴 必在主工作区(P0-156)
state.py ship-finalize --feature <main-tree>/<feature_dir>
```

ship-finalize 内部自动编排(**可重入** · 失败步骤修复后重跑即续):

| 步 | 动作 | 内容 |
|---|---|---|
| **0** | **state-sync** | 自动 `git fetch` + 安全 ff-pull merge_target(拉下 MR 合并后的 features dir)· 检测主工作区 state.json:不存在/缺 `ship.feature_head_commit` → 从 worktree 内 state.json 同步完整态(主工作区 pull 拉下的是合并前快照 · 完整态在 worktree 工作树) |
| 1 | verify-merge | `git fetch` + `merge-base --is-ancestor` 验证 feature_head 已进 merge_target |
| 2 | confirm-merged | `ship.phase` pushed → merged |
| 3 | cleanup | `ship.worktree_cleanup` = cleaned / n_a |
| 4 | ship-complete | `current_stage` → completed |
| 5 | **finalize-deliver** | 暂存收尾分支**前先停 `planning-backref` 暂停点**(AI 翻规划层 back-ref → `--planning-artifacts` 随同一收尾 MR · 或 `--no-planning-changes` · 详 §5.5)。state.py 暂存收尾 commit 到 `ship-finalize/<id>` 分支(`archive_on_ship` 默认 true:把过程层 feature 目录 zip 进 `features/_archive/<id>.zip` + INDEX.md + 从 merge_target **删原目录** · 详 §15)→ 交接 AI 用 gh/glab **创 MR + 自动合并** → 重跑检测已合 → 续。已交付判定 = zip 在 merge_target 存在。未合 → emit `PENDING`。**merge_target 全程只经 MR**(兼容保护分支 · 主工作区只 pull) |
| 6 | worktree-remove | 物理删 feature worktree + 本地 feature 分支(🔴 **收尾 MR 合并后**才删) |
| 7 | main-sync | 主工作区 `git fetch` + 安全 `git pull --ff-only`(让本地跟上 ship 结果)。归档已交付时:先把本地 feature 目录恢复 HEAD 干净态(内容已进 zip)→ ff-pull 干净删除该目录 |

**为什么必在主工作区**:step 6 worktree-remove 不能删自身所在 worktree · 且 Phase 2 状态同步语义属于 merge_target 主工作区(P0-156)。在 linked worktree 跑 → precheck FAIL · hint 给精确 cd 目标。

**AI 只在失败点干预**(其余全自动):
- **step 0 FAIL**(worktree 已被手工删 + 主工作区 state.json 不全):无路可走 · hint 排查 worktree path / --feature 路径 / 当前分支 · 或 bypass 后手工 finalize。
- **step 1 FAIL**(feature_head 不在 merge_target):两种可能 → ① MR 尚未合并 · 等用户;② squash / rebase 合并(见 §6)。按 R5 给用户 1/2 选项判断。
- **step 5 finalize-deliver PENDING**:收尾分支已暂存 · 待 AI 用 gh/glab 创 MR + 自动合。**降级**:gh/glab 不可用(未登录 / token 无 scope / 网络)→ 报明确原因给用户 · 解决后重跑;无法自动合 → 给 MR(create)链接让用户手动合 → 合后重跑。worktree **保留**(未交付不删)· 重跑可重入(语义检测已合 → 续删 worktree + pull)。
- **step 6 worktree-remove 失败**(worktree 占用等):降级 warning · state.json 已 finalize 不丢 · 按 hint 手动 `git worktree remove`。
- **step 7 pull 跳过**(主工作区不在 merge_target / 工作树有未提交改动 / 与 origin 分叉):降级 warning · 已 fetch · 按 hint 手动 `git pull --ff-only`。

### 5.5 规划层 back-reference 翻牌(随收尾 MR 一起合入 · 🔴 必做)

🔴 ship-finalize 进 step 5 finalize-deliver 时 · **暂存收尾分支之前先停在 `planning-backref` 暂停点**(emit PENDING + brief):须把**规划层 back-reference** 翻牌 —— **这是 ship 的一部分 · 不是「后续 / 非本次范围 / 下次规划」**。

- **为什么翻牌**:`feature = 某 BL 的落地`。规划期把 BL 写进 ROADMAP 是「📋 规划中」· 落地完不翻成「✅ 已交付」→ 规划层(ROADMAP/WS 进度)与执行层永久脱节 · 进度统计失真。
- **为什么随收尾 MR**:back-ref 翻牌与归档(都表示「本 feature 已交付」)是**同一件事** · 应**原子合入同一个收尾 MR**。🔴 **不要**事后单独直推 merge_target 翻牌 —— 保护分支会拒推 · 且收尾 MR 此刻已关闭、规划层塞不进 → 非原子 + 直推隐患。
- **做什么**:① AI 判断这几处哪些要翻「📋 规划中 → ✅ 已交付」(只改相关的 · AI 自决):ROADMAP 对应 BL(若是 WS 最后一个 BL → WS 标完成)· `product-overview/workstream/WS-NN.md`(WS 进度)· `teamwork-space.md`(工作区索引 · 按需)· 项目变更单(如 `BG-NNN.md` 阶段状态 · 按需);② 在**主工作区**改好这些文件(**不要 commit** · ship-finalize 会随收尾 MR 带走)。
- **然后**:`state.py ship-finalize --feature <path> --planning-artifacts <逗号分隔相对路径> --archive-desc '<≤200 字描述>'` → state.py 把这些文件随 {归档 zip + 删目录 + 终态 state.json} **同一收尾分支**暂存(并还原工作树 HEAD 防 step7 ff-pull 冲突)→ 你创建并合并**一个**收尾 MR(归档 + 规划翻牌原子)→ 重跑 ship-finalize 续清理 worktree + 主分支 pull。
  - **`--archive-desc`**:给本 feature 一句 **≤200 字**极简描述 · 写进归档 `_archive/INDEX.md` 的「描述」列(便于日后不解压识别)· 内容多则**压缩表达方式**(精简措辞 / 去枝节 / 保要点)塞进 200 字 · **超 200 → ship-finalize FAIL**(按 hint 压缩重写后重跑 · 不截断丢尾)· 缺省 `—`。
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
→ §12 状态档直推 → git worktree remove → ship-complete
```

两条路径状态机等价。手动路径要点:每条命令自己 cd 主工作区 · 不漏状态档同步 · 不漏 worktree 清理。

### 异常 · close-unmerged
放弃合入 → `--action close-unmerged --abandon=true` · 暂时关闭(后续重开)→ `--abandon=false`(留口子 · 不进 closed 终态)。

---

## 必读 cite 清单(P0-11)

本 stage 是 PMO 编排操作(不涉及内容创作角色)· **无 cite 要求**。

📎 **物化拦截清单**(已在工具层 BLOCKED + hint · spec 不重复展开):
- P0-6 ship 后 reset-prev FAIL
- P0-113 push 必 CLI-first 拿 MR URL · 不接受 git push hint URL
- P0-113 物化:`--mr-creation-method url-fallback` 时 · `git_host` 对应 CLI(github→gh / gitlab*→glab)若**已装 + 已认证** → **BLOCKED**(防 AI 退化用 git push hint URL)。逃生口:`--accept-cli-unavailable --reason '<具体原因>' --user-confirmed`(走 bypass log + concerns WARN 留痕)· 真不可用场景(网络隔离 / token scope 不够 / 强制内部流程)用此。
- P0-124 cleanup --status cleaned 必 phase=merged + merge_commit_hash 非空
- P0-156 ship-finalize / confirm-merged / cleanup 必在主工作区跑(linked worktree precheck FAIL)

---

## 12. state.json 直推例外(逃生口 · 仅状态档)

> 正常 finalize 全程经收尾 MR(§5)。本节是**逃生口**:当状态档(`state.json` / `review-log.jsonl`)漏进 MR、或手动路径(§7)收尾时,允许**仅对状态档**直推 merge_target —— 业务文件**永不**直推。

**合法直推范围**(不走 MR):

| 流程 | 允许直推的文件 | 允许的字段 |
|---|---|---|
| Feature | `state.json` + `review-log.jsonl` | 仅状态字段:`current_stage` / `completed_stages` / `ship.phase` / `ship.shipped` / `ship.merge_*` / `worktree_cleanup` / `completed_at` 等 |
| Bug | `BUG-REPORT.md`(单文件) | 仅 frontmatter 元数据:`current_stage` / `phase` / `shipped` / `merge_commit_hash` 等 |

**直推命令**(在主工作区 cwd):
```bash
# Step 0 · 二次验证合入(防 user-reported 误报 / confirm-merged 后状态变化)
git fetch origin <merge_target>
git branch -r --contains <merge_commit_hash> | grep origin/<merge_target>
# 命中 = 真合入 · 继续;空 = 未合入 → BLOCKED · 排查 MR 状态(可能被 revert / 误报)· 不要直推

# Step 1 · finalize 直推
git pull --ff-only origin <merge_target>
git cherry-pick <state.json finalize commit>      # 或 git checkout/cp 同效
git push origin <merge_target>
```

**为什么是合法例外**:单文件 + 仅状态字段 = 零业务影响 · 不需要 review;走 MR 浪费多角色 round-trip。

**push 失败降级**:
- `git push` exit≠0 → 把 finalize 留在 feature 分支 + state.concerns 加 WARN · 不阻塞 ship-cleanup / ship-complete
- 用 `state.py ship-phase --action confirm-merged --merge-target-push-failed --failed-reason {conflict|protect-rule|network|other}` 记录

**🔴 禁止滥用**:
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

**违规后修复**:已 push → 在 feature 分支 `git add -A {feature_dir}/ && commit && push`(fast-forward · 不破 review)· 已 merge → §12 状态档直推例外补 push 到 merge_target。

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

## 14. ship1 知识沉淀闸门(distill)

> 🔴 **过程 / 知识两层**:`docs/features/{id}/`(PRD/TC/TECH/report/state)= **过程层**(交付即历史快照 · 会 drift)· 而 `KNOWLEDGE.md`/`ADR`/`REG`/`retro`/`ARCHITECTURE.md`/`database-schema.md` = **知识层**(持久 · 须保鲜)。「描述代码」的文档随代码进 MR —— ship 前(Phase 1)把该 graduate 的知识提到知识层,**随本次 feature MR 一起被 review + 合**(这也是过程层归档 §15 的前置:先把真相提到知识层,过程稿才能安心归档)。

**硬闸门**:`ship-phase --action sanitize` **必带 `--distill`**(JSON · 知识层 6 项决策)· 缺 / 非法 / 缺项 → BLOCK。

```
--distill '{
  "knowledge":     "promoted <gotcha/事实> / none",     # KNOWLEDGE.md(AI 沉淀 · 约定/规范→DEV-RULES.md 人维护 · AI 只提示用户加 · 不代写)
  "adr":           "ADR-NNNN <决策> / none",            # docs/adr/(决策有备选+后果)
  "reg":           "REG-<case> / none",                 # e2e-registry(可复用测试场景)
  "retro":         "done / n/a",                        # docs/retros/(复盘)
  "architecture":  "updated <模块/接口> / no-change",   # docs/architecture/ARCHITECTURE.md
  "db_schema":     "updated <表> / no-change / data-only migration"  # docs/architecture/database-schema.md
}'
```

- **R0**:强制 AI **逐项走一遍**(每项记 `updated/promoted <what>` 或显式 `none`/`n/a` · 证明已判断)· **质量留 AI · 「走没走」进脚本**。distill **只校验+留痕 · 不代写文件**:知识层文件由 AI 手写 + 在 worktree commit(随 feature MR 合)· `ship["distill"]` 记录决策。
- 🔴 **迁移↔schema 机械校验**:feature diff 含 `migration` 文件 **且** `db_schema` 声明无变更 **且** `database-schema.md` 未更 → **BLOCK**(防 schema 文档 drift)。纯数据迁移 → `db_schema` 写 `data-only migration`。
- 🔴 建了 ADR → `ARCHITECTURE.md`「技术设计决策」表应有对应行。

---

## 15. ship2 归档本体(archive)

> 🔴 **过程层归档**:distill(§14)已把「描述代码」的知识 graduate 到知识层(随 feature MR 合)· 过程层 `docs/features/{id}/` 的使命已尽。**ship2 收尾 MR** 把它 zip 进 `features/_archive/<id>.zip` · 并从 merge_target **删原目录**。
>
> **为什么删而不是留**:防止 AI 检索到过时的 feature 信息(PRD/TECH 等过程稿交付即开始 drift · 与实际代码不匹配)。**代码是唯一真相** · 知识层是代码的文档 · 过程稿只留可追溯的 zip 快照。

**何时**:`ship-finalize` step 5 finalize-deliver(`archive_on_ship` 默认 true)· **随收尾 MR 一起合**(MR 合入后目录才从 merge_target 消失 · 经 review)。

**机制**(state.py 全自动 · AI 只在 PENDING 处创/合 MR):
1. step 1-4 把终态写进本地 feature 目录(含 `state.json current_stage=completed`)。
2. step 5 把整个 feature 目录打成 `features/_archive/<id>.zip`(arcname=`<id>/...` · 自描述)· 追加 `_archive/INDEX.md` 一行 · 并在收尾 commit 里 **删除 feature 目录的所有 tree 条目** · push 到 `ship-finalize/<id>` 分支 → emit `PENDING`(交接 AI 创 MR + 自动合)。
   - **INDEX 描述列**:`INDEX.md` 表为 `| Feature | 描述 | 交付归档时间 | 归档物 |`。「描述」= AI 经 `--archive-desc '<≤200 字>'` 给的极简 feature 描述(超 200 字 → ship-finalize FAIL · 要求压缩表达方式重写到 ≤200 重跑 · 不截断 · `|`/换行净化 · 缺省 `—`)· 便于日后不解压就识别归档内容。旧 3 列 INDEX 行下次归档时自动迁移补 `—`。
3. 收尾 MR 合并后重跑:**已交付判定 = zip 在 `origin/merge_target` 存在**(抗 squash)· 续 step 6/7。
4. step 7 主工作区:先把本地 feature 目录恢复 HEAD 干净态(内容已进 zip)→ `ff-pull` 干净删除该目录 + 落地 zip。
5. **幂等 3rd-run**:目录已被删 → state-sync 找不到 state.json · 但检测到 zip 已在 merge_target → emit 幂等 `PASS`(已交付终态 · 无动作)。

**opt-out**:`archive_on_ship: false` → 收尾 MR 只同步终态 `state.json` · 不 zip · 目录留存。详 templates/config.md。

**取历史**:`unzip features/_archive/<id>.zip` · 或读 `_archive/INDEX.md` 索引。

---

## 16. 流程价值反思(ship2 后输出 · 零暂停)

> 🔴 **telos**:给流程仪式攒「该不该活着」的数据 —— 框架此前只有负反馈(出事 → 判例 → 加规则)· 没有正/零反馈(这环节这次拦没拦住东西)→ 规则只增不减 · 仪式价值靠信念。本节把它变成台账。
> 🔴 **与 `docs/retros/`(§14 distill.retro)的分工**:retros = **业务/工程复盘**(这个 feature 本身做得如何 · 子项目级 · 知识层);本节 = **流程仪式价值度量**(teamwork 流程哪个环节值不值 · workspace 级)。**别混写**。

**触发**:`ship-finalize` 全部完成(归档 PASS / 幂等终态)后 · PMO 输出。🔴 **零新增暂停点**(纯情报 · 不等用户确认 · auto/yolo 模式照常输出)。

**两层输出**:

1. **台账行**(持久 · 累积):append 到 workspace `project-specs/PROCESS-LEDGER.md`(无则按 [templates/process-ledger.md](../templates/process-ledger.md) 创建)· 一行一 feature。🔴 字段以**机器可抽**为主(state.json:实走 stages / stage 时间戳 / rounds / bypass / concerns;REVIEW.md:verdicts / external 逐条裁决)· AI 判断仅「过场候选 / 反思摘要」两格 · **照实抄不美化**。
2. **digest**(emit ≤10 行 · 固定 4 问 · 不落 feature 目录):

```
📊 流程价值反思(<ID> · <flow> · 总时长 <X>)
- 拦住真问题:<external confirmed N 条(列举) / test 抓回归 / diagnose 改变修复方向 | 无>
- 纯过场候选:<零 finding + 零修订 + 全默认的环节 | 无>
- 流程新判例:<违规/摩擦 → 建议反馈 teamwork(consuming 项目不自改 spec) | 无>
- 成本异常:<rounds 过多 / bypass(理由) / 重试 | 无>
→ 台账 +1 行 · 建议:<保持 | 此类 feature 建议 X(仅建议 · 用户拍板)>
```

**豁免**:Micro 流程只记台账行 · 不出 digest(最轻通道不再加仪式)。

**消费方**(🔴 指名 · 写而不读 = 白写):
- **流程审视场景**(用户问「流程价值 / 哪些环节该砍」)→ PMO 读台账算:external confirmed 率 · 各角色真 finding 率 · 暂停点 all-default 率;
- **年检 kill criteria 数据源**:连续数月无新判例 → 流程仪式砍半;external confirmed ≈ 0 → 异质强制(P0-154)降可选;某角色长期零真 finding → 评审矩阵收缩。

⏳ **物化 TODO(v2)**:`ship-finalize` 自动抽机器字段 emit `ledger_row`(AI 只补 2 个判断格)· 同 prepare §0.5 渐进物化模式。

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `SHIP_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
