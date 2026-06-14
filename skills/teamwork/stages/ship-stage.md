# Ship Stage

> **v8.145 架构(用户拍板)**:**ship1 全交付 · ship2 零内容只清场**。
> **ship1**(§1-§5):全在 **worktree 内**跑 —— sanitize → **archive(归档+翻牌进 feature 分支)** → push + 创 MR · **终点 = MR 提交** · 提示用户合并后 feature 的 ship 即结束。
> **ship2**(§6):用户合并 MR 后 · 在**主工作区**跑一条 `state.py ship-finalize` —— 验已交付 → 删 worktree → 净化主工作区。**不修改任何内容**。
>
> 为什么这样分:内容性工作(归档/翻牌/台账)全部发生在**可控环境**(worktree · 自己的分支)· 随 feature MR **原子合入**;不可控环境(主工作区)只做清理。旧两-MR 链路(收尾分支 + 第二个 MR + 零 checkout plumbing)十二个版本(v8.16→v8.144)反复修补 · v8.145 整体删除。

---

## 怎么做

### 1. ship-start(在 worktree 内)
`state.py ship-start --feature X` · 校验前置(pm_acceptance.decision=approved_and_ship)

### 2. ship-phase sanitize(在 worktree 内)
`--action sanitize` · 净化 commit 记录(检查 residual / suspicious 文件)· 必带 `--distill`(§14)

### 3. ship-phase archive(在 worktree 内 · v8.145 ship1 终幕 · tool-executed)

```bash
state.py ship-phase --action archive --feature <path> \
  --planning-artifacts <逗号分隔 worktree 相对路径> \
  --archive-desc '<业务摘要 ≤200 字 · 只业务不过程>'
# 确无规划可翻(ad-hoc Bug/Micro · 无关联 BL)→ 用 --no-planning-changes 替代 --planning-artifacts
```

state.py 一口气做完(单 commit 进 feature 分支):
1. **规划翻牌 gate**:未传 `--planning-artifacts` 且未传 `--no-planning-changes` → emit `PENDING`(AI 先在 **worktree 内**翻规划层 back-ref · 详 §3.5)
2. **终态 state.json**:`current_stage=completed` + `ship.phase=archived`(终态进 zip = 墓碑 ·「completed 宣称」随 MR 合入与落地**原子可见**)
3. **zip + INDEX**:整个 feature 目录(工作树快照 · 含未 commit 的 review-log.jsonl)打成 `features/_archive/<id>.zip` · `_archive/INDEX.md` 追加一行(描述列 = `--archive-desc` · 超 200 字 FAIL · §15)
4. **`git rm --cached` 过程目录**(只删 index · **工作树保留** = ship2 接力卡)+ `git add` {zip + INDEX + 翻牌文件} + 单 commit

**MR diff 干净**:过程目录在分支历史里「加了又删」· 对 merge_target **净零** —— feature MR 的 diff 只剩 代码 + zip + INDEX 行 + 翻牌行。
🔴 archive 之后**勿在 worktree 跑 `git add -A`**(会把 untracked 接力卡目录加回分支)。
幂等:重跑检测「HEAD 含 zip + 不含目录」→ 同步后直接给 push 指引。

**冲突防线(v8.146 · 内置于 archive · 治本「共享追加文件进 feature 分支 → 并行 MR 大概率冲突」)**:
- ① **前置 sync**:archive 开头 fetch + behind 检测 → 落后自动 `merge origin/<mt>`(不 rebase 已推分支)· 干净则无感 · MR 开出来即可合;
- ② **追加型台账冲突机械自动解**(可枚举进脚本):INDEX.md(origin 为基 + 重放本 feature 行)+ PROCESS-LEDGER.md(v8.147 · 三方对比 **双方相对 base 纯增行**才 union:theirs 全文 + 本侧增量 · 任一侧有删改 → 拒动留 AI);
- ③ **代码/其余文件冲突留 AI**(不可枚举):emit `PENDING merge-conflict` + 文件清单 · AI 在 **worktree 内**评估处理 → `git add` → `git commit` → 重跑 archive;
- **MR 窗口期别人先合 → 平台报冲突**:回 worktree **重跑 archive**(= 冲突修复入口 · 自动 sync + 机械解)→ `git push` → MR 自动更新 → 用户再合。

### 3.5 规划层 back-reference 翻牌(随 feature MR 原子合入 · 🔴 必做)

- **为什么翻牌**:`feature = 某 BL 的落地`。落地完不翻「📋 → ✅ 已交付」→ 规划层与执行层永久脱节 · 进度统计失真。
- **v8.145 为什么更对**:翻牌在 worktree 内改 · 随 feature MR **原子生效** —— MR 不合 · ROADMAP 不显示已交付;MR 被 revert · 翻牌同退。不再有「merge 后另一个 MR 翻牌」的时间窗。
- **做什么**:① AI 判断哪些要翻(只改相关的 · AI 自决):ROADMAP 对应 BL(若是 WS 最后一个 BL → WS 标完成)· `product-overview/workstream/WS-NN.md` · `teamwork-space.md`(按需)· 项目变更单(按需);② **PROCESS-LEDGER 行**(§16 采写 · 数据源 state.json/REVIEW.md 此刻就在 worktree);③ 在 **worktree 内**改好(不 commit)→ 全部路径传 `--planning-artifacts` → archive 随归档 commit 带走。
- 找不到 BL 别急着跳:先读 `product-overview/workstream/` + `ROADMAP.md` 定位本 Feature 条目;确无 → `--no-planning-changes` 显式声明。
- **并行提示**:INDEX.md / PROCESS-LEDGER / ROADMAP 是共享文件 · 并行 feature 的 MR 合并窗口重叠时可能行冲突(append 类 · 解决简单)。

### 4. ship-phase push(在 worktree 内 · 声明式记录)
AI 自己执行:`git push origin <feature 分支>` → **CLI-first 创建 feature MR**(gh/glab · P0-113 · 拿真实 MR URL)→ 记录:

```bash
state.py ship-phase --action push --feature <path> \
  --feature-head-commit <push 后 HEAD> --git-host <host> \
  --mr-creation-method cli-<gh|glab> --mr-url <真实 URL>
```

门禁:`phase` 必须已是 `archived`(先 §3)· url-fallback 在 CLI 可用时 BLOCKED(P0-113 物化)。

### 5. ⏸️ ship1 终点 · 提示用户合并 MR(R5 标准暂停点)

🔴 **feature 的 ship 到此结束** —— 归档/翻牌/终态已全部在这个 MR 里。
🔴 **`auto_mode=true` 也必停此暂停点** —— 用户需在 git host 平台手动 merge · AI 无法代办(详 [SKILL.md § auto_mode=true 时各暂停点行为](../SKILL.md))。

```markdown
⏸️ ship1 完成 · feature MR 已创建(含代码 + 归档 + 规划翻牌)· 等用户在平台 review + 合并

请选择:

1. ✅ **已合并** 💡 推荐(若你刚点 merge)
   动作:回 `1` → PMO cd 主工作区 · 跑 `ship-finalize`(ship2 清场)
2. ⏳ **暂未合并 / 还在 review**
   动作:无需操作 · 任意时刻回来回 `1` 继续
3. ⚠️ **平台报冲突(别的 feature 先合了)**
   动作:回 `冲突` → PMO 回 worktree 重跑 `--action archive`(自动 sync · INDEX 机械解 ·
   代码冲突 AI 处理)→ `git push` → MR 更新 → 你再合并
4. ❌ **撤回 / 关闭 MR**
   动作:回 `撤回` → close-unmerged(`--abandon=true` 终态 / false 留口子)

📚 决策参考:MR URL = <url> · 平台 review 状态 / CI 结果
```

### 6. ship2:ship-finalize(一条命令 · 在主工作区跑 · 零内容修改)

```bash
cd <main-tree>                                        # 🔴 必在主工作区(P0-156)
state.py ship-finalize --feature <worktree 内 feature 目录路径> \
  --main-model "<你的模型 · 如 claude-opus-4-8 · 写入 audit 供按模型分析流程质量>"
```

| 步 | 动作 | 内容 |
|---|---|---|
| 1 | **verify-delivered** | fetch 后验 **zip 在 `origin/<merge_target>`**(= feature MR 已合 · 抗 squash)。未合 → emit `PENDING` 等用户 · 🔴 **绝不在合并前删 worktree** |
| 2 | worktree-remove | 删 feature worktree + 本地 feature 分支(接力卡 state.json 随之消亡)+ `fetch --prune` |
| 3 | main-sync | 净化主工作区:**副产物(bootstrap 注入块 / harness 锁)自动 commit**(用户拍板)· 用户真改动 → 影响评估 + R5(b) 决策面板(commit-push / stash-pull / skip)· pull(`--rebase` 若有本地 commit)· push(被保护分支拒 → 提示走 MR) |

尾随:teamwork stash 盘点(v8.144 · 防自动 stash 堆积埋改动)+ digest 指引(§16)。

**幂等**:接力卡已消亡(worktree 已删)→ 在 `origin/<分支>` 全树搜 `_archive/<id>.zip` 判已交付 → `PASS` noop。
**接力卡**:`--feature` 指向的是 **worktree 内**路径 —— archive 留下的 untracked state.json 提供 ship2 全部元数据(merge_target / worktree path / branch)· 它随 worktree 删除自然消亡 · 主工作区**从未物化过过程目录**。
**AI 只在两处干预**:① PENDING(MR 未合 → 等用户);② main_sync_decision(用户改动 → 转 R5(b) 暂停点 · 用户选项后跑 `state.py main-sync --merge-target <mt> --strategy <选项>` —— v8.145 起不依赖 --feature)。

### 异常 · close-unmerged
放弃合入 → `--action close-unmerged --abandon=true` · 暂时关闭(后续重开)→ `--abandon=false`。重开走 §3 archive(幂等)→ §4 push 重 MR。

---

## 必读 cite 清单(P0-11)

本 stage 是 PMO 编排操作(不涉及内容创作角色)· **无 cite 要求**。

📎 **物化拦截清单**(已在工具层 BLOCKED + hint · spec 不重复展开):
- P0-6 ship 后 reset-prev FAIL
- P0-113 push 必 CLI-first 拿 MR URL · `url-fallback` 在 CLI 已装+已认证时 **BLOCKED**(逃生口:`--accept-cli-unavailable --reason '<原因>' --user-confirmed` · bypass log + concerns WARN 留痕)
- v8.145 push 必先 archive(`phase: archived → pushed` 物化)· archive 规划 gate(`--planning-artifacts` / `--no-planning-changes` 二选一)
- P0-156 ship-finalize 必在主工作区跑(linked worktree precheck FAIL)

---

## 13 · R-S7 · git add 范围规则(强红线)

**任何 commit Feature 产物**(各 stage-complete 后 · §3 archive **之前**):

```bash
# ✅ 必这样(范围明确 · 一并 add state.json + review-log.jsonl 等状态档)
git add -A <feature_dir>/

# ❌ 禁止(state.py 持续写的状态档不在 PMO 视野 · 列文件名 = 凭记忆 = 必漏)
git add <feature_dir>/dev/*.md <feature_dir>/PRD.md
```

**理由**:`state.json` + `review-log.jsonl` 由 state.py 持续写 · PMO 列文件易漏 → MR 不含状态档 → 下游评审看不到历史。`-A {feature_dir}/` 范围严格限定。
🔴 **v8.145 时序界**:§3 archive **之后**目录已转 untracked 接力卡 —— 此后**禁止**再 `git add -A <feature_dir>/`(会把已归档目录加回分支)。

---

## Output Contract(产物形态参考)

### `state.ship.phase`
null → **archived**(§3)→ **pushed**(§4)状态机 · 物化校验。`merged` 不再出现在 state(合并事实 = zip 在 origin · 物理判定)。

### `state.ship.mr_url / mr_create_url`
CLI 创建的 URL(cli-*)或兜底 URL(url-fallback)

### `features/_archive/<id>.zip` + `INDEX.md` 行
ship1 交付本体(随 feature MR)· zip 内 state.json = 终态墓碑(current_stage=completed)

---

## 14. ship1 知识沉淀闸门(distill)

> 🔴 **过程 / 知识两层**:`docs/features/{id}/`(PRD/TC/TECH/report/state)= **过程层**(交付即历史快照 · 会 drift)· 而 `KNOWLEDGE.md`/`ADR`/`REG`/`retro`/`ARCHITECTURE.md`/`database-schema.md` = **知识层**(持久 · 须保鲜)。ship1 把该 graduate 的知识提到知识层 · **随本次 feature MR 一起被 review + 合**(这是 §3 归档的前置:先把真相提到知识层 · 过程稿才能安心归档)。

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

- **R0**:强制 AI **逐项走一遍**(每项记 `updated/promoted <what>` 或显式 `none`/`n/a`)· **质量留 AI ·「走没走」进脚本**。distill **只校验+留痕 · 不代写文件**:知识层文件由 AI 手写 + 在 worktree commit(随 feature MR 合)。
- 🔴 **迁移↔schema 机械校验**:feature diff 含 `migration` 文件 **且** `db_schema` 声明无变更 **且** `database-schema.md` 未更 → **BLOCK**。纯数据迁移 → `db_schema` 写 `data-only migration`。
- 🔴 建了 ADR → `ARCHITECTURE.md`「技术设计决策」表应有对应行。

---

## 15. 过程层归档(v8.145 起属 ship1 · §3 archive 执行)

> 🔴 distill(§14)已把「描述代码」的知识 graduate 到知识层 · 过程层 `docs/features/{id}/` 的使命已尽。§3 archive 把它 zip 进 `features/_archive/<id>.zip` · 并从 **feature 分支**删原目录 —— 随 feature MR 合入后 · merge_target 上**从未出现过**过程目录(主工作区也从未物化)。
>
> **为什么删而不是留**:防 AI 检索过时 feature 信息(过程稿交付即 drift)。**代码是唯一真相** · 知识层是代码的文档 · 过程稿只留可追溯的 zip 快照。

- **INDEX 描述列 = 业务索引**:`| Feature | 描述 | 交付归档时间 | 归档物 |`。「描述」= `--archive-desc`(≤200 字 · 超 200 → FAIL · `|`/换行净化 · 缺省 `—`)· 🔴 **只写业务**(这需求是什么 · 做了什么 · 业务影响/对外契约)· **不写过程信息**(评审轮次/bug 数/测试数/「全绿」/external 独家/code review —— 那些在 zip 内 state.json/REVIEW.md · 不进业务索引 · 命中明显过程信号 archive emit WARN)。
  - ✅ 业务:「CPS 安装归因计佣后端地基:cps 4 表 + 安装归因绑定/dl 校验/点击端点 + 计佣 post-commit(GalaxyEdge+IAP 双路·幂等)+ 退款冲销。对外暴露 promoter/install/click/refund 契约」
  - ❌ 过程:「…评审拦 10 真 bug(external 独家 4·含 2 money bug)。cps11+集成11+回归520全绿」(评审/测试数据属过程 · 不进业务索引)
- **已交付判定**(ship2 安全闸)= zip 在 `origin/<merge_target>`(抗 squash · 物理真相)。
- ~~`archive_on_ship: false` opt-out~~ **v8.145 废弃**(归档是新架构根基)· 残留配置被忽略 + WARN。
- **取历史**:`unzip features/_archive/<id>.zip` · 或读 `_archive/INDEX.md` 索引。

---

## 16. 流程价值反思(ship2 后输出 · 零暂停)

> 🔴 **telos**:给流程仪式攒「该不该活着」的数据 —— 框架此前只有负反馈(出事 → 判例 → 加规则)· 没有正/零反馈 → 规则只增不减。本节把它变成台账 + 跨项目回收。
> 🔴 **与 `docs/retros/`(§14 distill.retro)的分工**:retros = 业务/工程复盘(子项目级 · 知识层);本节 = 流程仪式价值度量(workspace 级)。**别混写**。

**三处落点(各管一段链路 · 别混)**:
| 落点 | 粒度 | 写时机 | 消费方 |
|---|---|---|---|
| `project-specs/PROCESS-LEDGER.md`(项目侧) | 一行一 feature · 机器字段 | §3 archive 规划 gate(worktree 内) | 项目自己流程审视 |
| **`<skill 安装目录>/docs/audit/<id>.md`(框架回收侧 · v8.148)** | 一份一 feature · 机器数据 + 三段判断 | **ship2 PASS 后工具落草稿 → AI 静默补判断** | **框架跨项目 harvest 流程质量** |
| `docs/RETRO-LEDGER.md`(框架仓) | 一行一版 · 永久 | 框架改进发版时 | 年检 / 存在性审视 |

**时机(v8.145/148 两段式)**:
- **采集 + 写台账行 = §3 archive 的规划 gate 时**(worktree 内 · `state.json`/`REVIEW.md`/`external-cross-review/` 全在工作树 · 取数零成本):PMO 在 worktree append `project-specs/PROCESS-LEDGER.md` 行(无则按 [templates/process-ledger.md](../templates/process-ledger.md) 创建)· 路径加进 `--planning-artifacts`(随 feature MR 原子合入)。
- **审计回收 + digest = ship2(ship-finalize)PASS 后**:
  - 🔴 **工具自动落** `<安装目录>/docs/audit/<id>.md` 草稿(机器数据段确定性抽自 state.json · 喂 kill-criteria 不可幻觉)· emit `audit_record` 路径;
  - 🔴 **AI 静默补完三段判断**(做的好的 / 发现的问题 / 待优化的 · 照实抄 REVIEW.md·state · 空写「无」· 改 frontmatter `audit_status: done`)—— **零新增暂停点 · 不等确认 · 写完即结束**(auto/yolo 照常)。「发现的问题」段 = 框架级 bug / 工具判例的**持久回收口**(取代旧易逝 digest 的「建议反馈 teamwork」行 · 详 [docs/audit/README.md](../docs/audit/README.md));
  - digest 仍可 emit(≤10 行 · 纯情报)。时长口径 = init → archive(不含 MR 等待)。
- **兜底**(漏写时):`unzip -p features/_archive/<id>.zip <id>/state.json` 取数 · 补行随下次任意 MR。

**两层输出**:

1. **台账行**(持久 · 累积):一行一 feature。🔴 字段以**机器可抽**为主(state.json:实走 stages / stage 时间戳 / rounds / bypass / concerns;REVIEW.md:verdicts / external 逐条裁决)· AI 判断仅「过场候选 / 反思摘要」两格 · **照实抄不美化**。
2. **digest**(emit ≤10 行 · 固定 4 问 · 不落 feature 目录):

```
📊 流程价值反思(<ID> · <flow> · 总时长 <X>)
- 拦住真问题:<external confirmed N 条(列举) / test 抓回归 / diagnose 改变修复方向 | 无>
- 纯过场候选:<零 finding + 零修订 + 全默认的环节 | 无>
- 流程新判例:<违规/摩擦 → 建议反馈 teamwork(consuming 项目不自改 spec) | 无>
- 成本异常:<rounds 过多 / bypass(理由) / 重试 | 无>
→ 台账 +1 行 · 建议:<保持 | 此类 feature 建议 X(仅建议 · 用户拍板)>
```

**豁免**:Micro 流程只记台账行 · 不出 digest。

**消费方**(🔴 指名 · 写而不读 = 白写):
- **流程审视场景**(用户问「流程价值 / 哪些环节该砍」)→ PMO 读台账算:external confirmed 率 · 各角色真 finding 率 · 暂停点 all-default 率;
- **年检 kill criteria 数据源**:连续数月无新判例 → 流程仪式砍半;external confirmed ≈ 0 → 异质强制(P0-154)降可选;某角色长期零真 finding → 评审矩阵收缩。

⏳ **物化 TODO(v2)**:archive 在规划 gate 自动抽机器字段 emit `ledger_row` 草稿(AI 只补 2 个判断格)。

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- ship 实现:[../tools/_v8_ship.py](../tools/_v8_ship.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `SHIP_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
