# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.150 · review finding 处理对称化:先质疑→确认→采纳/驳 · 举证责任对称 · 治本盲采

> 用户:AI 对 review 结果的处理过程应该是先质疑、再确认、再采纳、给出采纳理由的思考过程 · 不能盲目认同。

### 诊断:举证责任不对称 → ADOPT 成无摩擦默认 = 盲采温床
- 框架有裁决三态(confirmed/rejected/deferred)+ adversarial_self_check + 12.2 点名「盲采是默认倾向」—— 但**防线不对称**:rejected「必记驳回依据」是硬的,ADOPT 的 rationale 只要填「改了什么」· adversarial_self_check 的示例/措辞全是 REJECT 方向(steelman finding 再驳)。结果:reject 有摩擦、adopt 无摩擦 → 盲采(reviewer 说啥改啥)恰是阻力最小路径,虽被点名却没设防。

### 改动(doc-only · 对称化既有机制 · 非加新仪式)
- **§12 头部加「固定思考顺序」**:① 质疑(先假设 finding 不成立:false positive/过度设计/错层/没看全)→ ② 确认(回读真实代码/AC/DEV-RULES)→ ③ 裁决+给理由。🔴 **举证责任对称**:confirmed 与 rejected 同责 —— 采纳也要给「为何确为真+为何这样改对」实证 ·「reviewer 说得对」不是理由。
- **§12.1 confirmed 判据**:加「先质疑」前置 + 处置加「记采纳依据(与 rejected 对称)」;§12.2 盲采标「最常踩」+「没经①②的 ADOPT = 盲采」。
- **pm_response.adversarial_self_check schema(prd.md)**:改方向对称 —— ADOPT 方向写「finding 不成立的最强反方→回读确认不成立→采纳」(给 ADOPT 示例);rationale 要求 ADOPT 含「质疑→确认链」三步,不接受无核实采纳。
- **review-stage.md / goal-stage.md substep 6 / roles/pm.md** 三处引用同步对称化(默认姿态=质疑)。

### 验证
- doc-only · pytest 3 failed / 527 passed(零回归)· 无测试 pin §12 措辞。

## v8.149 · goal 阶段去 external 评审:业务对齐阶段不做技术细节挑刺 · 细节/边界归 blueprint

> 用户:goal 阶段的外部评审去掉 —— 总会挑出细节和过度设计;这阶段目的是对齐业务目标(用户会看 PRD)· 细节和边界在技术方案阶段定就行。

### 判断:对的工具 · 错的阶段(非「external 没用」)
- external 整体 82% 采纳(实测数据)· 是框架 MVP —— 但**采纳率高 ≠ 每个阶段都该有**。goal 产物是业务对齐的 PRD、用户亲审;external 天然「找缺口 → 加校验」· 在「定要做什么」阶段把技术细节/边界审进来 = 噪音 + 过度设计提前涌入。external 留在 blueprint(技术方案)+ review(代码)· 那里技术挑刺正当其位。
- **框架早知道病只贴了创可贴**:goal-stage.md 原有「🔴 external finding 须对照简洁性取舍 · 每条单看合理 · 合起来把方案做臃肿」—— 承认了过度设计,却只让 AI 自己筛。v8.149 移除病因(不在此阶段做),而非继续筛。

### 改动(代码 1 处 + 文档)
- **`DEFAULT_REVIEW_ROLES[("Feature","goal")]`**:`[pm,qa,architect,pl,external]` → `[pm,qa,architect,pl]`(唯一硬接线处)。verdicts 门禁通用(谁在查谁 · 不硬要 external)· pl_challenge 独立 → 拆得干净。
- **能力保留**:`EXTERNAL_STAGE_TO_PROFILE` 仍含 goal · 确需对某 PRD 上 external → `change-review-roles --stage goal --roles '...,external'` 显式 opt-in(降默认不删能力)。
- **goal 过度设计防线 = Architect 简洁性 counter-lens(内审)**:external 走后这条内审 lens 成为 goal 唯一简洁性把关 · 文档强化。
- 文档对齐:goal-stage.md(默认 5→4 · 删 External Reviewer bullet · 新「goal 不做 external」段 · 重点 review 指引去 external)· prd.md 模板(reviewers/verdicts 示例)· prepare.md 角色表 · FLOW_STAGE_CHAIN hint。测试 1 处 pin 更新(simplicity-lens v8.76)。
- 🔴 敏捷需求 goal 本就无 external(不变)· Feature Planning goal/planning 的 external **未动**(不同 flow · 跨 feature 粒度 · 待用户单独定夺)。

### 验证
- pytest 3 failed / 527 passed(baseline 3 · 零回归)· build_default_stage_review_roles('Feature')['goal'] 验证去 external · blueprint external 保留。

## v8.148 · ship2 后流程质量审计落安装目录 docs/audit/ · 框架跨项目搜集(补全反馈环消费侧)

> 用户(承前三轮诊断):ship2 后加一段 AI 静默逻辑 · 总结当前项目执行数据(做的好的/发现的问题/待优化的 + 实际数据)· 写到 skill 安装目录 docs/audit/ · 方便框架层面搜集流程质量。

### 背景:补的是反馈环缺失的「rollup 回收层」
- 前三轮查实:① ship2→框架的反馈通道只有意图无机制(jdp 漏掉真判例);② 「年检」被引用 7 次作消费方 · 0 次定义 procedure(幽灵);③ 项目级→框架的总结流程根本不存在。三者同一病根 = 反馈环只建了「写」· 「读/rollup」整个没规范。本版补 rollup 回收层第一块。
- 三处落点分工成文:PROCESS-LEDGER(项目侧 per-feature)· **docs/audit/(安装目录回收侧 · 跨项目)** · RETRO-LEDGER(框架仓 per-version)。安装目录 = 本机所有 consuming 项目共享回收点 · consuming 项目不自改 spec · 只投递 · 框架来 harvest。

### 改动(代码 + 测试 + 文档)
- **`_write_audit_record`(ship-finalize PASS 后调)**:落 `<安装目录>/docs/audit/<id>.md` —— **机器数据段工具确定性抽**(来源项目/flow/实走 stages/总时长〔stage_contracts 时间戳算〕/concerns/bypass · 喂 kill-criteria 不可幻觉)+ **三段判断占位**(做的好的/发现的问题/待优化的)由 **AI 静默补**(零暂停 · 改 audit_status: done)。`TEAMWORK_AUDIT_DIR` env 可 override(测试)· 写失败静默降级不阻塞 ship2 · 已填不覆盖(幂等)。
- 「发现的问题」段 = 框架级 bug/工具判例的**持久回收口**(取代 §16 旧易逝 digest 的「建议反馈 teamwork」行)。
- docs/audit/README.md(回收/harvest 说明)· .gitignore 只入库 README(运行时 <id>.md 是 transient 本机回收料 · 抗 update.py 覆盖:_overwrite_skill_files 不删 target 多余文件)。
- §16 三处落点表 + 时机成文;emit 增 audit_record + brief 静默补完指示。
- 测试 +2(审计草稿落 TEAMWORK_AUDIT_DIR 含机器数据+占位 / 已填不被重跑覆盖)。

### 验证
- pytest 3 failed / 527 passed(baseline 3 · 净 +2)· 真实产物 eyeball(时长/stages/concerns 确定性正确)。

## v8.147 · LEDGER 冲突升级机械自动解:三方对比纯增行判定 · union 进脚本(实战 case 驱动)

> 用户(截图 case:SVC-CORE-B260612051432 · aon 实战):v8.146 防线首战 —— PROCESS-LEDGER 三行追加冲突按 ③ 留给 AI · AI 的处置 = 删标记保双方行 · **零判断纯机械**。判定:该进脚本(v8.146 保守只解 INDEX · 实战证明 LEDGER 同样可枚举)。

### 设计:安全前提物化
- `_try_append_union_resolve`:三方对比 base(:1:)/ours(:2:)/theirs(:3:)· **双方相对 base 都是纯增行**(base 行序列为两侧保序子序列)才自动 union(theirs 全文为基 + 本侧增量去重后置)· 任一侧有删/改 → 拒动留 AI(PENDING 提示改为「台账类但非纯增行 · 人工合」)。
- 适用名单制(`PROCESS-LEDGER.md`)· 不做通用文件 union(代码文件双方尾部追加 union 可能语义错误)。
- sync 返回升级:status 统一 `auto_resolved` + `auto_resolved_files` 清单 · archive emit 的 `sync` 注明解了哪些文件(透明可审计)。

### 实战判读(截图 case · 防线首战全对)
- 重跑 archive = 冲突修复入口 ✓ · INDEX 静默处理 ✓ · LEDGER union 保双方行 ✓ · 只 add 冲突文件不碰 untracked 接力卡 ✓ —— AI 处置零瑕疵 · 但这步本可不存在 · 故升级。

### 验证
- 测试 +2(纯增行自动 union 双方行都在 / 非纯增行〔同行双改〕拒动 PENDING 留 AI)· pytest 3 failed / 525 passed(baseline 3 · 净 +2)。

## v8.146 · ship1 冲突防线:archive 前置 sync 自动合 · INDEX 冲突机械自动解 · 代码冲突留 AI

> 用户(承 v8.145):ship1 在 MR 创建后大概率会冲突 · 是否有必要增加检测冲突环节 · 自动评估处理。判定:有必要 —— v8.145 设计时把该 trade-off 低估为「可能」· 实为「并行 ship 窗口重叠时必然」(INDEX/LEDGER 是 every-feature 同位追加)。

### 设计(按框架哲学拆:可枚举进脚本 · 不可枚举留 AI)
- 解决场所 = worktree(到 ship2 前一直活着 · 正是 v8.145「内容性工作在可控环境」的合法位置)。
- 同步用 **merge 不 rebase**(分支已推 · MR 已开 · 不破 review 历史)。

### 改动(代码 + 测试 + 文档)
- **`_sync_feature_branch`(内置于 archive · 首跑+幂等重跑共用)**:fetch + behind 检测 → 落后自动 `merge origin/<mt>` —— ① 干净则无感(MR 开出来即可合 · INDEX 基于合并后状态生成);② **INDEX.md 冲突机械自动解**(确定性再生成:origin 侧为基 + 重放本 feature 行 · 追加表语义明确);③ 其余冲突(代码/规划文件)→ emit `PENDING merge-conflict` + 文件清单(LEDGER 类提示 union)· AI 在 worktree 评估处理 → `git add`/`git commit` → 重跑 archive。
- **重跑 archive = MR 窗口期冲突修复入口**:平台报冲突 → 回 worktree 重跑(自动 sync + 机械解)→ `git push` → MR 自动更新;⏸️ ship1 暂停点加「平台报冲突」选项;emit 增 `sync` 字段(同步动作透明)。
- fetch 失败降级(冲突防线降级不阻塞归档 · WARN);未完成 merge 检测(MERGE_HEAD)→ 先收尾再重跑。
- 测试 +3(前置 sync 无感合 / INDEX 冲突自动解双方行都在 / 代码冲突 PENDING→解→重跑通过)· ship-stage.md §3 冲突防线成文。

### 验证
- pytest 3 failed / 523 passed(baseline 3 · 净 +3)。

