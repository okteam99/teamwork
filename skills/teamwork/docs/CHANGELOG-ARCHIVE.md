# Changelog Archive

> 📦 **定期清空**:本文件只暂存从 [CHANGELOG.md](./CHANGELOG.md) keep-5 轮转出的条目 · 膨胀时整体清空 —— 完整历史 = **git 提交历史**(永不丢 · `git log` / `git show` 按需追溯)· 工作区不热存。
> 上次清空:**v8.193**(2026-07-06 · 清除 v8.128 → v8.187 共 60 版条目 · 约 1.0k 行)。

---
## v8.188 · 规划收尾:暂停问合入 merge_target → 建 MR → 提示用户合并 → 停(不自动起下一 feature)

> 实证 AON KA-PAGES:AI 规划完成后**自己** commit→push→建 draft MR,然后**立刻**跳进下一个 feature 的 prepare(还把新 feature 的 `merge_target` 设成**未合并的** `planning/ka-pages` 分支)—— 没有「是否合入 merge_target」确认暂停点,也没有「MR 建好 → 提示用户合并 → 停」。

### 改动(feature-planning Step 9 + planning-check)
- **规划收尾框成 3 步**(同 feature ship1):① R5 暂停问「**是否合入 `merge_target`**」② 确认后 worktree 内 commit+push planning 分支+开 MR(target=merge_target)③ 🔴 ⏸️ **提示用户合并 + 到此结束**。
- **🔴 不自动起下一 feature**:启动实施是**用户合并规划 MR 之后**的独立决策 · 🔴 **别叠 feature 在未合并 planning 分支**(feature `merge_target` = 集成分支 dev/staging · 非 planning 分支 · 否则实现 diff 混未合并规划、基线不稳)。
- `planning-check` `worktree_setup` + checklist item 6 同步(item 6 顺带修 v8.184 遗留的「主工作区直推」旧措辞)。

### 验证
- doc(feature-planning Step 9)+ code(`planning-check`)· `test_state` planning 4 passed · pytest 3 failed(baseline)/ 627 passed。
## v8.189 · 规划收尾 finalize:用户合并后切回主分支 + 清 worktree + 净化主分支(= ship2)

> 用户续 v8.188:规划 MR 建好提示用户后,用户说「已合并」→ 该进规划收尾流程:**切回主分支、清理 planning worktree、净化主分支**。补全 = 把规划收尾对齐 feature 的 **ship1→ship2** 两段。

### 改动(feature-planning Step 9 + planning-check)
- **收尾-2 finalize**(新 · = feature `ship-finalize`/ship2):用户说「已合并」→ 3 步镜像 ship-finalize:① `cd` 回主工作区 ② `git worktree remove` 清 planning worktree ③ `state.py main-sync --merge-target <mt>` 净化主分支(v8.145 起**不依赖 feature** · fetch + 按策略 pull 合并后规划产物 · 主工作区干净+最新)。
- **收尾-1** 的 MR 提示改成「合并完回来说『已合并』· 我进收尾」(引导第二段)。
- `planning-check` `worktree_setup` + checklist item 6 同步 finalize。

### 验证
- doc(feature-planning Step 9)+ code(`planning-check`)· `test_state` planning 4 passed · pytest 3 failed(baseline)/ 627 passed。
## v8.190 · main-sync 回收 teamwork auto-stash · 治 stash 累积无回收(harvest 跨两次最高频)

> 第二轮 harvest(163 条 · +74):「ship 收尾 / 主工作区 auto-stash 累积无回收」**26×**(上次 23×)· **跨两次 harvest 稳居第一**。main-sync `stash-pull` 每次备份 stash 但不 pop → 跨 feature/session 累积 **11+** · human 难判哪些可 drop。

### 改动
- **main-sync 回收 stash**(新 · 默认自动跑):`_reclaim_stashes` 只认 **teamwork 自建**的 main-sync stash(消息标识)· **drop 可证冗余的**(空 / 内容已在分支 · `git apply --reverse --check` 通过)· 剩含未合内容的 **surface**(feature 标签 + hint)· 🔴 **绝不碰用户自己的 stash**。
- **`--drop-stashes`**:用户确认不需要任何备份 → 全清 teamwork main-sync stash。
- ship-finalize / 规划 finalize / 独立 main-sync 都**自动回收**(emit `stash_reclaim`)· 不再累积。
- **测试** `test_stash_reclaim_v8190` +5(drop 冗余 / 留 live / 不碰用户 / drop-all / hint)。

### 验证
- code(`_v8_ship` `_reclaim_stashes` + main-sync emit + `--drop-stashes`)+ doc(ship-stage §6 · SKILL 命令行)· pytest 3 failed(baseline)/ 632 passed。
## v8.191 · external 机械成本三连修:preflight + 超时自动重试 + verify-fixes 增量重验

> 耗时归因(138 条 per-stage 数据)原因 2:external 的**机械 overhead**(非评审价值)—— 20× 实锤:「3 行改动跑 5 次 external(2 真轮+1 空跑+2 超时)review 墙钟 49m(80%)」「CLI 未登录到 review 才发现 → 降级折腾」「每采纳 finding 即全量重跑」。

### 改动(不动「评审必须真跑」原则 · 只砍机械成本)
- **`--preflight`**(①):review 干活前 which + **微 probe**(一次极小调用 · 秒级)验登录/网络/配额 E2E 通 · 失败此刻修环境 · 不烧完整评审墙钟才发现。
- **超时/空跑自动重试**(②):rc=124 / 空 stdout → **自动重试一次**(1.5x timeout · emit `attempts`/`timeout_sec_used`)· 省手动重跑轮;localconfig `external_review_timeout_sec` 调基础超时(长 review 项目)。
- **`--verify-fixes`**(③ · 仅 review):增量重验 —— base 锚**上一轮已评 commit**(结果文件 frontmatter `target_commit`)· prompt = 上轮 findings 全文 + 修复 diff · 任务 = 逐 finding 给 `fixed/not-fixed` verdict + 只查修复 diff 新问题 · **不全量重评**。结果落 `review-<model>-fixverify.md`(不 clobber 全量轮 · 供下轮再锚)· 锚点失效(rebase/同 commit)FAIL 提示退全量 · 与 `--prompt-doc` 互斥。
- review-stage.md 同步(external 步 + fix-retry 循环)。

### 验证
- code(`state.py` 4 helpers + cmd_external_review 三分支 + runners timeout/extra_prompt)+ doc · `test_external_mech_v8191` +12 · pytest 3 failed(baseline)/ 644 passed。
## v8.192 · pause-mark 计时排毒 · stage 内 R5 等待与工作分离(待优化 #5)

> 耗时归因:goal 均值 157m vs 中位 22m(max 128h)—— stage 内 R5 暂停(PRD 确认/预览确认/DB 确认)的**等用户墙钟全算成工作**(v8.172 只拆了 pm_acceptance)· 每次归因都要人肉排毒。

### 改动
- **`state.py pause-mark`**(新):emit R5 暂停点前打点(写 `open_pause`)· **下一个流程命令(start/complete/fix/retry)自动闭合**(`close_open_pause` 接进引擎 4 choke 点)· 等待累计进该 stage `await_minutes` —— resume 侧零纪律。
- **`_stage_durations`**:工作时长 = duration − await(breakdown 显示 `goal 20m(+等待30m)`)· 最耗时(工作)不再被等待污染。
- SKILL R5 协议加打点行。

### 验证
- code(engine helper+4 接线 · state.py 命令 · ship durations)· `test_pause_mark_v8192` +5 · v8.166 套件未破 · pytest 3 failed(baseline)/ 649 passed。
## v8.193 · skills 删减 batch:退役迁移器/收尾遗物/手写模板 + ARCHIVE 照章清空(−2.2k 行)

> 全量 review skills(29.6k 行):按自家律法(三层律 · 定期清空 · 工具自动落禁手写)删 🟢 批次。

### 改动
- **CHANGELOG-ARCHIVE 照章清空**(−1.0k):v8.128→187 共 60 版条目 · git 历史是冷库(章程自 v8.127 就这么写)。
- **删 `_v8_migrate.py` + migrate-v7-to-v8 命令**(−258):v7→v8 一次性迁移已过 190+ 版 · 无 v7 存量。
- **删 `post-feature.py` + 其测试**(−690):v7.3 时代收尾遗物 · v8.145 ship 重构漏删 · 仅自引用。
- **删 `templates/external-cross-review.md`**(−279):v8.20 起 external 产物**工具自动落**、手写是红线 —— 给禁止手写的文件留手写模板自相矛盾;engine scaffold 映射 3 处同步清。
- SKILL/TEMPLATES 引用同步清(migrate 3 处 + 1 处)。agents/README 瘦身(683→~150)留下批。

### 验证
- 净减 ~2.2k 行 · `test_v8_stage_specs` 90 passed · pytest 3 failed(baseline)/ 639 passed(删 post-feature 测试 −10)。
## v8.194 · agents/README 瘦身 683→64 行 · 删自标废止段 + v7.3 产物协议残留

> 承 v8.193 删减 batch 下批:agents/README(683 行 · 全仓仅 1 处历史引用)—— §三 Codex 调用规范**自标「历史记录 · 已被 §11 取代」仍躺 77 行**;§五主对话产物大半是 v7.3 产物命名(dev-report/acceptance.md 等 v8 已不产);§一模型偏好逐 stage 枚举(随模型代际漂移的拐杖);§四协议核心真实但三处重述 Progress Log、启动自问出现两遍。

### 改动
- 重写为 64 行紧凑协议:保留(dispatch 宿主速查 / 降级 WARN / 文件化 dispatch / Key Context 6 类 / Progress Log flush+轮询 / 状态分级 / 危险命令红线)· 删除(自标废止的 §三 · v7.3 产物命名表与 review-log schema · 模型逐 stage 枚举 · 重复段)· external 指针改指 standards §11。
- 净减 −619 行。零活引用(仅 external-model-usage 一处历史注)。

### 验证
- doc-only · pytest 3 failed(baseline)/ 640 passed。
## v8.195 · 🟡 待确认项裁决:删 diff-html-vs-panorama(static-html 退役工具)· 其余 3 件确认活消费保留

> 承 v8.193/194 删减:🟡 批次逐件消费点确认。**diff-html-vs-panorama.py**(340 行):仅 static-html 分支引用 · 163 条 audit 里 static-html 使用 = **1** · 前端栈已定项目强制 same-stack · verify-panorama 已 medium-aware 覆盖 → **删**(+测试 −10 · dev-stage/roles/ui.md 3 处引用改指 verify-panorama)。

### 确认保留(活消费实证)
- **e2e-registry.md**:ship §16 采写 `reg` 字段(REG-case)消费。
- **config.md**:conventions 3 处(缩写注册 + localconfig 模板)。
- **architecture.md**:含 database-schema 模板 = TECH §Schema 影响分析的上游。

### 验证
- 净减 ~700 行 · 引用清零 · pytest 3 failed(baseline)/ 630 passed。
## v8.196 · 规划链路 #1+#2:F↔BL 机读绑定(init --bl)+ ws-progress 可启动集

> 规划链路整体审视的两刀:① **F↔BL 绑定是链路最脆一环** —— 只存在于 ROADMAP 手填「对应F编号」单元格 · ship 自刷 WS/翻牌全押它填对;② **「下一个做什么」没有工具答案** —— execution_waves 是静态快照 · 执行中要人肉对照 DAG。

### 改动
- **`init-feature --bl BL-NNN`**(可选):写入 `state.json.bl` = F↔BL 机读绑定;`_resolve_ws_from_feature` **优先**走 state.bl → WS 名册反查(ROADMAP「对应F编号」降为兜底)—— 翻牌漏填单元格不再断链。
- **`ws-progress` 输出 `ready_to_start`**:名册里**依赖全 ✅ 已完成、自身待开始**的 feature(短名+BL)· emit 字段 + 进度块尾行「▶ 可启动(依赖已齐)」—— 并行调度/yolo 直接喂启动决策。
- 测试 +2(state.bl 解析 · ready 推导)。

### 验证
- code(`state.py` 3 处)· pytest 3 failed(baseline)/ 632 passed。
## v8.197 · 规划链路 #3+#4:执行线存在性 lint(幽灵 Line)+ 规划后变更成文路径

> 规划链路审视余下两刀:③ WS「承接执行线」写 Line 4 但业务架构里没有 → 无人查(愿景层→WS 的 taxonomy 是纯 doc 约定 · 断了不报);④ WS ✅ 规划完成后追加/砍 feature 无成文路径(实证 WS-03 追加 BL-006 · 合法性/是否重确认是灰区)。

### 改动
- **ws-lint 执行线存在性**(③):WS 承接的 `Line N` 必须在 `product-overview/*业务架构*.md` 的执行线列表存在 · 幽灵 Line → NONCONFORMANT(hint:新线先在业务架构登记)· 无业务架构文档 → skip 不误报。
- **feature-planning Step 10 规划后变更**(④):**追加 feature** = 轻量(R5 一句确认 → worktree 内改名册+ROADMAP+变更日志 → ws-lint/ws-progress → MR · 不重开全流程);**砍/改方向** = 回 feature-planning(WS 回 🔄 讨论中);🔴 已启动的 F 不在此列(执行层变更 · 别用规划变更掩盖执行返工)。
- 测试 +3(幽灵 Line / 存在 OK / 无架构 skip)。

### 验证
- code(`state.py` ws-lint)+ doc(feature-planning Step 10)· pytest 3 failed(baseline)/ 635 passed。
## v8.198 · loops 对照两修:await-merge 30s 轮询(合并自动下一步)+ yolo fix-retry 10 轮止损

> 对照 claude.com「Getting Started with Loops」:teamwork 是 Turn-based 最佳实践重度实现 · 缺口在 Time-based(结构性等待窗无人看:132h 等合并长尾 · CI 红无人接)+ Goal-based 的 max-attempts(yolo「持续自主解决」无轮次上限 · runaway 风险)。

### 改动
- **`state.py await-merge`**(新 · time-based loop):ship1 / 规划收尾 emit 等合并提示后**跑它** —— 30s 轮询 MR 状态(gh/glab · `--interval/--max-checks` 可调)· **MERGED → emit 下一步**(ship-finalize / 规划 finalize)· WAITING → 重跑续等(用户随时打断改人工)· CLOSED → surface · 连续 3 次查询失败 → FAIL(环境)。`--feature`(读 state.ship.mr_url)或 `--mr-url` 直传(规划场景)。
- **yolo fix-retry 止损**(goal-based max-attempts):同 stage fix-retry **≥10 轮**未收敛 → 硬停 surface(`yolo_rounds_exceeded` 接进 `execute_stage_fix` · 真·硬停的合法扩展:收敛失败 ≠ 继续死磕)· 非 yolo 不受影响(既有「3 次问用户」协议)。
- ship-stage §5 / feature-planning 收尾-1 / SKILL yolo 表同步。

### 验证
- code(`_v8_ship` await-merge · `_v8_engine` 止损)+ doc ×3 · `test_loops_v8198` +4 · pytest 806 passed(基线三失败已由并行修复清零)。
## v8.199 · 删 P0-11 cite 纪律(A 全删)+ brief 全面性核查

> 精简讨论首刀(用户拍板 A):cite 纪律 = 每 substep 动手前引 spec 原文自证「真读」+ 切角色重 cite —— 每 feature 几十次仪式输出。163 条 audit **零实证**拦到任何东西 · `cited_specs` 字段**零消费**(写了没人收)· 它想治的病(AI 不读 spec)已被 v8.151 起「brief 消费时点主动推」+ gate 物化接管。**模型越聪明 · 过时仪式越忠实执行 = 越有害**。

### 改动
- **全删**:STAGES.md §2 定义(~25 行)· 11 个 stage 的「必读 cite 清单」表(~140 行)· 各处 📎 指针行 · `stage-complete --cite` 参数与 `cited_specs` 死字段。
- **brief 全面性核查**(cite 表删后 brief = 唯一消费时点推送):13 个 brief **全部**指回对应 stage 文件(导航不丢)· 关键 🔴 推送就位(dev 3 / diagnose 3 / goal 2 / ui_design 3…)· 补 1 处:`_blueprint_brief` 的 TECH 结果行从老五段更新为 v8.181-183 全结构(现状基线/错误处理/依赖影响/查询性能/完工自查)。
- 误删回滚:roles/ 3 行 v8.155 冷审规范(「cite」为普通引用义)· git checkout 恢复。

### 验证
- 净减 ~180 行 + 每 feature 几十次仪式输出归零 · pytest 806 passed。
## v8.200 · 全模板加「🧩 补充洞察」自由区 · 模板是地板不是天花板

> 用户:模板是否可能限制模型能力?是否加一个 AI 自由发挥的补充板块(限制少 · 可留空)。判断:槽位不限能力 · 但「填完表=完成」的心智会 —— 模板外的重要发现(非常规风险/更好方案线索/跨 feature 影响)没处落就不会写。PRD 已有先例(v8.164 扩展区)· 推广到其余产物模板。

### 改动
- **tc / tech / ui / bug-report 四模板**统一加末段 `## 🧩 补充洞察(AI 自由发挥 · 可留空)`:模板槽位之外重要但没处落的 · 🔴 **地板不是天花板 · 填完槽位 ≠ 想完了** · 没有写「无」或删本节 · **不为凑内容而写**(防它自己变成新仪式)。
- PRD 不动(v8.164 `## 开工前必须想清的` 已是同物)。

### 验证
- doc-only(4 模板各 +5 行)· `test_v8_stage_specs` 90 passed。
## v8.201 · PRD canonical 到达率:goal brief 约束模板 + goal-complete 三命门校验

> 实测(v8.200 扩展区验证):post-v8.164 的 10 份 live PRD **仅 1 份**用 canonical 模板,其余自由结构/抄项目旧 PRD(同 WS-012 病根)—— 机读块/扩展区等新机制**到达不了**,加什么槽位都白加。

### 改动
- **goal brief 约束**(消费时点推):🔴 照 `templates/prd.md` 起草 · **别抄项目里旧 PRD**(附实测数据)。
- **goal-complete 校验**(`prd_template_conformance` evidence):只查**三个机读命门段**(不管字数/风格)—— `TEAMWORK-MACHINE` 机读块(或 legacy frontmatter)· 验收标准/AC(verify-ac 依赖)· 『开工前必须想清的』扩展区(可写「无」但段要在)· 缺 → FAIL + hint 指 canonical 模板。
- 测试 +3(自由结构拦三段 / canonical 放行 / legacy 缺扩展区仍拦)。

### 验证
- code(`_v8_stage_specs` check+接线+brief)· pytest 809 passed。
## v8.202 · 模板地址全 stage 到位:diagnose 补映射 + scaffold_hints 加「别抄旧」+ 4 brief 指针

> 用户:是否所有 start brief 都给模板地址?查实:`scaffold_hints`(v8.14)**早已**在 stage-start emit 绝对路径(10 stage 映射+validator)· 但 PRD 到达率 2/11 证明被忽略。真缺口三处。

### 改动
- **diagnose 补进 STAGE_TEMPLATES**(原漏:产 BUG-XXX.md 的 stage 反而 start 时不给 bug-report 模板)。
- **scaffold_hints 加 `usage` 警示**(单点 · 全 stage 生效):照绝对路径起草 · **别抄项目里同名旧产物**(旧文件 = 旧版模板快照 · 附到达率实测)。
- **4 个 brief 加统一指针**(blueprint_lite/test/browser_e2e/pm_acceptance):「📋 产物模板见 scaffold_hints.templates」—— 不在 brief 重复路径(防双源)· 只指向。

### 验证
- code(engine 映射+usage · specs 4 指针)· diagnose hints 冒烟 ✓ · pytest 809 passed。
## v8.203 · 规划收尾暂停点重构:头两项一步到位(自动合并 + 收尾 / 收尾+启动首个 BL)

> 实证 case(AON WS-14 MMP 规划):收尾是「终审 → 建 MR → 等你告知已合并 → 再收尾」的多段手动接力 · 用户被迫手动短路「你直接合并然后规划收尾」。收尾该把常用路径做成一等选项。

### 改动(feature-planning Step 9 + planning-check 双 emit 同步)
- **暂停点选项重构**:① **确认·合入 MR + 收尾**(commit+push+开 MR+**自动合并**+清 worktree+净化主分支 · 一步到位)💡 ② **确认·合入收尾 + 启动首个 BL**(同 ① · 收尾完直接 prepare 首波 ready BL〔execution_waves W1 / ws-progress ready_to_start〕)③ 建 MR 我自己平台合(await-merge 轮询 / 平台合)④ 先不提交 ⑤ 其他。
- 🔴 **自动合并硬门(选 1/2)**:仅 `merge_target` 非主分支(main/master)—— 集成分支纯文档/全景低风险 · 同 yolo 自动合入非主分支风险模型;平台拒(审批/CI/保护)→ **自动回退选项 3** · 绝不 force。
- 🔴 **启动首个 BL(选 2)守 v8.188 护栏**:必 finalize 完成后(集成分支已含规划产物)+ 用户显式选 + feature target=集成分支 —— 「别叠 feature 在未合并 planning 分支」仍成立(planning 分支已消亡)。

### 验证
- doc + planning-check 双 emit · 新选项出现在 emit ✓ · pytest 809 passed。
## v8.204 · external 异质评审默认关(用户拍板 · 全局一刀切 · yolo 也跟随)· 省 CLI 冷启动

> 用户:`disable_external_review` 默认改 true(默认关异质评审 · 太耗时)· yolo 也跟随默认关。厘清:开关只降级**第三视角 reviewer**(异质外部 CLI → 同模型 subagent 隔离冷审)· **架构师+QA 多角色评审完全不受影响照跑** · 耗时大头 = external CLI 冷启动。

### 改动(默认翻转 · 三处)
- **`_read_disable_external_review` + `_localconfig_disable_external` + bootstrap CONFIG_DEFAULTS**:key 缺省 / 无 config / 读失败 → **true**(禁用);**显式 `false` = opt-in 跨模型异质**。template localconfig seed 同步 true。
- **告警软化**(现在是默认常态 · 不再红字每次响):bootstrap heterogeneous_review status→`cold-review (default)` + note(非 warning)· 删 digest 🔴 行 · yolo kickoff `🔴🔴 醒目告警`→一行 `ℹ️ INFO`。
- **物化门禁不变**:第三视角**仍必真跑**(默认校验 `review_via: subagent` 冷审 · opt-in 异质校验实跑日志)· 去掉整个第三视角仍 BLOCK · 「非异质」也不许「不冷审」。

### 文档 reframe(避免变假话)
- README(中英)支柱表 / flow 表 / yolo 段:「异质 cross-review」→「第三视角独立 Review(默认同模型隔离冷审 · 跨模型异质 opt-in 升级)」。SKILL yolo 红线同步(第三视角默认冷审 · 异质 opt-in)。

### 验证
- pytest 809 passed(21 处 external 测试 setUp 改为显式 opt-in `disable_external_review:false` + 默认断言翻转)· 两读取器冒烟一致。
## v8.205 · 文档位置单源:SKILL 裸文件名误导修复 + sitemap 补模板(治 ROADMAP 落项目根)

> 实证 case(TermPro M5 规划):AI 把 `ROADMAP.md` 放**项目根**、来回挪。根因不是「没规范」而是**位置权威分裂** —— 模板阵营(templates/roadmap.md 头部「位置：docs/ROADMAP.md」)一致,但 SKILL.md 文档清单用**裸文件名**(`PROJECT.md`/`ROADMAP.md`/`sitemap.md` · 无路径)读起来像项目根,成了矛盾的第二源;sitemap 更糟 —— **连模板都没有**,全仓 3 个落点。

### 改动
- **SKILL.md 文档清单 + 路由速查**:三个裸名加 canonical 路径(`{子项目}/docs/PROJECT.md` · `docs/ROADMAP.md` · `{子项目}/docs/design/sitemap.md`)· 表头加 🔴「**位置权威 = 各 templates/*.md 头部「位置：」· 不在项目根裸放**」(单源指针 · 防再漂)。
- **新建 `templates/sitemap.md`**(补上唯一缺模板的产物 · 头部「位置：`{子项目}/docs/design/sitemap.md` 与全景同目录」+ IA 地图结构)· 全仓带路径引用本就一致指向 `panorama_path/sitemap.md`,conventions.md 是唯一异类 → 拉齐。
- **conventions.md** sitemap → `design/sitemap.md`(非 `docs/` 根)· **feature-planning Step 7** 写 ROADMAP 处加路径 + 指模板单源 · **templates/README** 登记 roadmap 位置 + sitemap 行。

### 验证
- doc-only(SKILL/conventions/feature-planning/templates)· pytest 809 passed。
## v8.206 · preview dev 工具面板改右下角悬浮(治顶栏 offset 布局 · 违 same-stack「零预览痕迹」)

> 实证 case(用户看预览页):dev 预览导航实际做成**右下角悬浮 Prototype Nav** · 比 spec 规定的**顶栏**合理。v8.187 理清了工具面板「放什么」(页面导航+状态注入 · 页内真实交互优先),但**位置写死「顶栏」**是错的。

### 治本
- **顶栏是 layout bar** —— 把真实页面内容**整体下推、offset 掉真实位置/尺寸**,恰恰违背 same-stack「**零预览痕迹 · 页面=真实代码**」核心目标(真实 app 没这条顶栏 → 加了预览就不像真实 app)。
- **右下角悬浮面板 = overlay** —— 不占布局流 · 不 shift 真实页面(页面在真实位置/尺寸渲染)· 右下角是 dev 工具通行惯例(devtools/toolbar 都在角落 · 一眼识别「工具非产品 chrome」)· 可折叠 · 半透明低层级。

### 改动(位置改 · 内容保 v8.187)
- ui-design-stage § 重命名 `preview dev 顶栏` → `preview dev 工具面板(右下角悬浮 · 非顶栏)` + 加位置治本段(顶栏反模式)· 页面区标注 `Prototype Nav`。
- 同步 same-stack 段 + `ui-rules.md` + `ui.md`(2 处)+ 新建的 `sitemap.md`:所有 dev shell 引用「顶栏」→「悬浮工具面板(右下角)」(RETRO 历史记录不动)。

### 验证
- doc-only · pytest 809 passed。
## v8.207 · ship2 审计源材料预抽(治「先删 worktree 再要三段判断 → AI 被迫 unzip 反读」)

> 实证 case(用户看 Codex ship2):ship-finalize 删 worktree **后**要 AI 补 audit 三段判断,但源材料(REVIEW.md/TEST-REPORT.md)随 worktree 删除只剩归档 zip 内 → AI 被迫 `unzip -p` 反读。反直觉的人机工学 bug(交付安全无问题 · 主工作区干净)。

### 治本
- **`_capture_audit_sources(feature_dir)`**(新):ship-finalize 在 **worktree-remove 之前**(feature_dir 尚在)抓 `REVIEW*.md` + `TEST-REPORT.md` 压成紧凑摘录。
- **嵌进 audit 草稿 `## 源材料摘录` 段** —— AI 读草稿即可填三段(做的好的/发现的问题/待优化的)· 三段占位 + emit brief 改指「照实抄草稿内 §源材料摘录 + 实际数据 · 🔴 **无需 unzip 归档**」。
- 读失败静默降级(绝不阻塞 ship2)· 无源材料 → 不加空段(三段仍在)。

### 为什么不移到 ship1
实际数据全来自内存 `state`(worktree 删了也在)· 只有三段的**源文档**随 worktree 消失 —— 预抽摘录是最小修复,保持 v8.145「ship2 out-of-repo bookkeeping」不变(audit 落 `~/.teamwork/audit/` 非仓库)。

### 验证
- code(`_v8_ship`)+ ship-stage §16 doc · `test_audit_sources_v8207` +4 · pytest 813 passed。
## v8.208 · 流程价值台账时长三分(总/AI自主/等待用户)+ 各阶段细粒度 + 用户邮箱列

> 用户:台账时长要细化 —— 各阶段细粒度耗时 · 区分等待用户 · 排除等待=AI 自主运行耗时;加一列 git 用户邮箱。基础设施(v8.192 pause-mark `await_minutes` + `_AWAIT_USER_STAGES`)已有 · 本版把它落进台账/审计。

### 改动
- **`_timing_split(state)`**(新):`AI 自主 = Σ 工作 stage(duration − await)` · `等待用户 = Σ stage 内暂停 + Σ 纯等待 stage(pm_acceptance)墙钟` —— 分离墙钟里的人工等待。
- **`_git_user_email(cwd)`**(新):`git config user.email`。
- **ship1 archive emit 加 `ledger_timing`**(total_wall / ai_autonomous_min / await_user_min / per_stage / user_email)—— 台账在 archive 采写 · AI 照抄确定性数据不肉眼算 state。
- **audit 记录**:frontmatter `user_email` + 正文「AI 自主运行:Xm · 等待用户:Ym」+「用户邮箱」行(跨项目 harvest 按人分析)。
- **PROCESS-LEDGER 模板**:`时长` 拆为 `时长(总·AI自主·待用户)` + 新增 `各阶段耗时` + `用户邮箱` 列 + 三分口径说明。ship-stage §16 同步。

### 验证
- code(`_v8_ship` 2 helper + archive emit + audit)+ 模板/§16 · `test_pause_mark_v8192` +4 · pytest 817 passed。
## v8.209 · PROCESS-LEDGER + audit 记录 AI 宿主类型(codex / claude / gemini)

> 用户:台账要记 AI 宿主(codex 还是 claude)。宿主已在 `state.host`(claude-code/codex-cli/gemini-cli · audit 正文也有)· 本版落进台账列 + archive emit 采写数据 + audit frontmatter(供 harvest 按宿主分析)。

### 改动
- **ship1 archive emit `ledger_timing` 加 `host`**(= state.host)· 与时长/邮箱同束 · AI 照抄确定性。
- **audit frontmatter 加 `host:`**(与 v8.208 `user_email` 并列 · harvest 按宿主筛)。
- **PROCESS-LEDGER 模板加 `宿主` 列** + 口径说明(供年检**按宿主对比流程质量** —— external 采纳率 / 过场率 / AI 自主时长在 claude vs codex 的差异)。ship-stage §16 同步。

### 验证
- code(`_v8_ship` archive emit + audit frontmatter)+ 模板/§16 · `test_pause_mark_v8192` +1(host frontmatter)· pytest 818 passed。
## v8.210 · PROCESS-LEDGER schema 演进纪律「只在末尾加列」+ 幂等 ledger-migrate(治旧项目台账不升级)

> 用户:模板升级了但旧项目台账没升级 · 要不要迁移逻辑。查实:台账**无按列位解析的代码**(冲突解是行级 union · 年检 AI 读)→ schema 漂移不 crash;但 v8.208/209 把新列**插在中间/前面** → 新行(13 列)追加到旧表头(10 列)**错位**、年检读错列。

### 治本:改 schema 纪律 = **只在末尾加列**
- **重排 v8.208/209 新列到表最右**(各阶段耗时/用户邮箱/宿主)→ 旧数据行天然是新 schema 的**有效前缀**(新列它们为空 = 该 feature 早于该指标 · 诚实)· 迁移退化为**仅换表头一行**。零成本(新 schema 刚上 dev · 无真实项目已落)。
- **`state.py ledger-migrate --feature <path>`**(新 · 幂等):旧 schema → 升级表头 + 分隔行(canonical 表头单源自 `templates/process-ledger.md`)· **旧数据行逐字不动** · 已最新 no-op · 无台账 SKIP。ship-stage §16 append 前必跑。

### 为什么不写重映射迁移器
「只在末尾加列」让旧行永远是有效前缀 → 永不需要 cell 级重映射 · 任何未来加列都只是表头一行替换。

### 验证
- code(`state.py` 2 helper + 命令)+ 模板重排 + §16 · `test_ledger_migrate_v8210` +4 · pytest 822 passed。
## v8.211 · 宿主指令文件注入退役(治共享仓库污染非 teamwork 用户)· 关键信息收进 SKILL.md

> 实证 case(commercial-data-warehouse):bootstrap 往 AGENTS.md/CLAUDE.md 注入 teamwork 段 · 共享仓库同事一 commit · **不用 teamwork 的用户也被迫吃到**。用户拍板:去注入 · 关键信息写进 SKILL.md(加载 skill 即生效 · 只影响用 teamwork 的 session —— 这才是正确的作用边界)。

### 改动
- **`maintain_host_injection` 反转为清理模式**:不再写入;发现历史 `<!-- TEAMWORK_BEGIN: -->` 块 → **移除**(marker 外用户内容一字不动 · 清后全空连文件删 · 幂等)· emit `cleanup_removed` + note。
- **SKILL.md 新增 § Subagent 默认授权**(载体自宿主注入块迁入 · v8.135 授权长期化的新家)+ 196 行引用改指本段;PMO 定位 / worktree 纪律 SKILL 本就有 · 不再依赖注入。
- **退役死资产**:`tools/sync-drift.py` + `templates/host-instruction-injection.md` + `test_sync_drift.py`;scripts-policy / templates/README / SKILL 工具清单 / README 中英措辞同步。
- 本仓根 `CLAUDE.md`(纯注入块)用新逻辑自清 → 已删。

### 验证
- 冒烟:移除保用户内容 ✓ 纯注入删文件 ✓ 干净不动 ✓ 幂等 ✓ 绝不创建 ✓ · 注入测试重写为清理语义(+4)· pytest 814 passed。
## v8.212 · SKILL 文档导航补全(注入退役后 SKILL = 唯一入口 · 导航必须无死角)

> 用户:skill 里有目录索引吗?答:有(两类三层:skill 自身 § 文档导航 + 二级索引 STAGES/ROLES/STANDARDS/TEMPLATES;用户项目侧 § 文档清单/路由速查/结构索引 + teamwork-space)。但核对发现 § 文档导航**缺口真实**:docs/ 只列 CHANGELOG —— prepare(mode B 必经)/ feature-planning / conventions / teamwork-space-guide 全不在;STAGES.md(编排单源!)/ agents/README(subagent 协议)/ PRODUCT-OVERVIEW-INTEGRATION / hooks/ / agents profile 目录也不在。v8.211 注入退役后 SKILL 是唯一载体 · 导航更须全。

### 改动
- **§ 文档导航 15 行 → 24 行**:补 STAGES.md · PRODUCT-OVERVIEW-INTEGRATION · agents/README · docs/{prepare,feature-planning,conventions,teamwork-space-guide} · hooks/ · codex-agents/+claude-agents(external profile · 核实为活资产非死目录)· RETRO-LEDGER;TEMPLATES 行指向 templates/README 全清单;_v8_ship 描述更新(+ship-finalize/await-merge)。

### 验证
- doc-only · 相关套件通过。
## v8.213 · Claude hooks 全退役(teamwork 不需要 hooks)· bootstrap 转清理 + codex toml 保留

> 用户拍板:去掉 Claude hooks 相关逻辑。Review 佐证:hooks 是「宿主独有事件的自动触发层」· 与跨宿主原则相悖(scripts-policy 本就限制它只当薄壳);post-compact 恢复已由 state.json 断点续跑覆盖;codex hooks.json 更是当年 codex 账号 "cyber abuse" 警告的诱因之一(external-model-usage §抽出来源)—— 且 spec §110 明令删它 · bootstrap 却还在拷(spec-代码矛盾)。

### 改动(退役三件套:停部署 + 清存量 + 功能找新家)
- **删 `hooks/`**(hooks.json + post-compact/post-stop/post-subagent/session-restore.sh · 5 件)。
- **`maintain_host_hooks` 反转清理模式**:绝不部署 hooks;清历史部署(`.claude/hooks/` 5 个列名文件 + `.codex/hooks.json` · 🔴 **签名守卫**:内容含 teamwork 生态标记〔eamwork/PMO/dispatch_log/STATUS.md〕才删 · 用户同名 hook 保留)· 空目录顺手删 · 幂等。
- **codex agent toml 部署保留**(`.codex/agents/*.toml` = subagent profile · 活功能 · 与 hooks 无关)。
- **git-hooks/pre-push 不动**(发版 auto-bump · git hook 非 Claude hook)。
- SKILL 导航删 hooks/ 行 · scripts-policy hooks 段改退役声明 · 本仓 `.claude/hooks/` 自清(5 件全删含 PMO 签名的 post-subagent)。

### 验证
- 冒烟:签名删 ✓ 外来保留 ✓ toml 照部署 ✓ hooks.json 绝不部署 ✓ 幂等 ✓ · hooks 测试重写为退役语义 · pytest 813 passed。
## v8.214 · 注入段/hooks 清理挪出 skip_maintain 版本门(每次 bootstrap 都清 · 治 merge 回流旧块)

> 用户问:升级后会清注入段么?答:**会**(升级 → 版本 marker 不匹配 → maintain 跑 → 清理触发 · E2E 实证)。但验证同时抓到真实边缘:清理挂在 `skip_maintain` 版本门内 —— **同版本内二跑不清**。实害:并行分支上旧版 bootstrap 注入过的 AGENTS.md 被 `git merge` 带回 · 同版本内永不清 · 要等下次升级。

### 改动
- **`maintain_host_injection` + `maintain_host_hooks` 挪出 skip_maintain**(每次 bootstrap 都跑 · 同 v8.91 localconfig backfill「无论 skip 与否」先例)—— 清理幂等且轻(字符串查找)· merge 回流的旧注入块/hook 当次 session 即被兜住。chmod/gitignore 仍在版本门内(真·一次性维护)。

### 验证
- 冒烟:同版本 skip 下 merge 回流块被清 ✓(CLAUDE.md 只剩用户内容 · hook 同清)· pytest 813 passed。
## v8.215 · 智能分诊 v1:clarity 维度(明确度)→ 评审强度比例化 + 分诊证据先行

> 实证 case(admin i18n):「**大而明确**」的需求走全重流程 —— 车道把「大」和「不确定」绑死(477 key/7 页 → Feature → goal 3 冷审 + PL 质疑 + blueprint external 全上 · 但需求零歧义)。智能分诊方向(用户确认):输出从「车道标签」走向「维度向量」· 证据先行 · 本版落 v1。

### 改动
- **prepare-check emit 加 `triage_evidence` 证据槽**(estimated_files/cross_repo/new_deps/has_ui/mechanical/clarity)——🔴「看过再判」:30 秒侦察后填 · **空着不给判**;prepare.md §1.5 判定标准(explicit=明确方案或机械映射类;ambiguous=方向词;normal=默认)。
- **`init-feature --clarity`**(explicit/normal/ambiguous · 默认 normal)→ `state.clarity`。
- **explicit 消费两处**(gate 自动放行 · 留痕):① goal **PL 对抗质疑跳过**(无产品歧义可质疑)+ brief 推「冷审 3→1(QA 边界)」;② **blueprint external 跳过**(架构师单审)。🔴 **review 三视角不动**(明确 ≠ 不会写错 · 拦真主力 92/163)。
- 解耦原则:改动面大 → Feature **骨架**照走;不确定性低 → **评审轻档**。预期 explicit 类膜时间 −30~40%。

### 验证
- `test_clarity_v8215` +4(PL 跳/PL 照拦/blueprint 跳/review 不受影响)· pytest 817 passed。
## v8.216 · 评审配置动态化:拆掉 clarity 硬编码 · AI 按「角色价值判据」逐角色配 roster

> 用户裁决(对 v8.215 的修正):`--clarity` 固定消费(跳 PL+跳 external)还是太规则化 —— 该**动态决策**,不一定去 PL,也可能去 QA / ARCH。机制其实早已存在:`stage_review_roles`(所有 gate 本就按它放行)+ `change-review-roles`(审计留痕)· v8.215 错在绕过它另立硬规则。

### 改动
- **删两处硬编码 clarity gate**(PL challenge / blueprint external)—— gate 回归纯 roster 路由:角色不在 `stage_review_roles[stage]` → 自动放行(既有逻辑)。
- **prepare-check emit 加 `role_value_criteria`**(给 AI 的判断框架 · 非规则):逐角色问「这个视角对本 feature 能拦住什么」—— pl=价值前提可质疑?qa=边界/可测性风险?architect=架构决策/跨模块?external=多触发点/同模型盲区?**每角色一行理由(有值留 · 无值去)**· review stage 从严(建议 ≥2 视角 · <2 需强理由)。
- **`triage_evidence.consumption` 改**:凭证据逐 stage 逐角色配 roster(`change-review-roles --reason` · 审计)· `--clarity` **仅记录**进 state(台账/年检校准 · 不触发硬编码行为)。
- goal / blueprint brief 推送同步(冷审派谁 = 按 roster · 非按 clarity 一刀切)。

### 验证
- 测试重写:clarity 单独**不再**跳过任何 gate ✓ · roster 去角色 → gate 放行 ✓(×4)· pytest 817 passed。
