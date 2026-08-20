# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.342 · 四档流程回归:tiny 立档 · lite 由 full 装配出来(用户拍板)

> 拍板链:①「我们是否考虑加回多档流程」→ 加;②「tiny dev → review(单路 architect)→ pm_acceptance → ship / lite dev(TC 并行)→ 单路 architect → test → pm_acceptance → ship 这样合理么」;③「lite 是否也要有 PRD,不要 TC,要 verify-ac」;④「lite 是不是可以被 full 装配出来」→ **是**。
> 上一版把「直接做」形态拼成「micro + 手工附加轻门」——「附加」是形容词式承诺,没有载体就不会发生。本版给它正式档位。

### 变更
- **四档、三 preset**:`preset ∈ {full, tiny, micro}`。判据 = **preset 只给「不立就走不通链」的档**(micro 跳 review/test · tiny 无 goal/blueprint 入口);lite 与 full 只差「跳 blueprint」一条边 → FEATURE_FLOW 加 `goal→dev` / `ui_design→dev` 直边 + 装配旋钮,**不加图**。多一张转移图 = 多一处要同步的口径(legacy `lite`/`blueprint_lite` 正是这么烂掉的:三份 flow-key 实现对同一输入解析出两张不同的图)。
- **tiny(新 preset)**:`dev → review〔architect 单路〕 → pm_acceptance → ship` · 零文档(规格 = dev brief **理解卡**,brief 要求开工前回显一遍)· 无 test stage(判据 = 四轴的**验证成本**轴:diff 可验)。与 micro 的分界 = 有没有独立验收口(micro 在 MR diff 上验)。
- **lite(装配形态 · 零 re-init)**:`goal-complete --needs-blueprint false` → 跳 blueprint,不产 TC/TECH/TECH-REVIEW。**PRD 照要、终确认停等照停**(降的是文档与路数,不是拍板权)。dev 前置从「blueprint 完成」回落到「goal 完成」,不是无条件放行。
- **绑定载体换而不撤**:lite 无 TC → AC↔测试绑定改走 PRD 机读块 `acceptance_criteria[].test_refs`,`verify-ac.py --mode test-refs` 校验**非空 + 引用真实存在**(文件存在 · 带 `::用例名` 的名字要在文件里出现)。顺带堵住 TC 模式老坑:TC 点名的函数全仓不存在,覆盖率照样 21/21 全绿。
- **降档不降独立性**:tiny/lite 的单路 architect 仍须错开模型(单路不变式)—— 减的是路数,不是「换个人看」这件事本身。
- **装配环节第三旋钮**:装配卡流程阶段槽从「ui_design / browser_e2e」扩到三段可选,`blueprint 进/跳` 入槽;goal 3.7 减法侧分级表改四档(超低→micro · 低→tiny · 中低→lite · 中/高→full)。
- **prepare 接线**:§2.2 超 micro 白名单 → 推荐 tiny(选项 2 = 继续讨论,守 v8.338);`prepare-check --preset` 让链预览按档出 —— 原实现 `flow_type in FLOW_STAGE_CHAIN` 短路,preset 永远读不到,定了轻档也预览全链(用户看到的链才是他感知到的重量)。
- 顺手修:`build_stage_chain_preview` 用 raw flow_type 查 roster 矩阵恒 miss(键是内部名)· Micro 无 roster 条目才一直没暴露,Tiny 有条目会直接把 architect/pm 吃掉。

### 测试
`test_flow_tiers_v8342.py` 34 条:三 preset/四档不变式 · lite 不许有自己的图 · tiny 四道会死锁的门 · 三实现 flow-key 一致 · lite 旋钮只认显式 false · PRD/test 门不因降档松开 · test-refs 五种情形(含「点名不存在的用例」)· 门不休眠(lite 下换口径而非 skip)· prepare-check 按档预览 · spec 载体。既有锁按新载体重锁:v8329(三旋钮)· v8336(锁退役不锁出边条数)· v8341(四档 + 降档不降独立性)· engine_fixes(goal→dev 已合法 · 非法样本改用 test→dev)。全库 1504 绿。

## v8.341 · 评审力度减法侧分级 +「直接做」形态正名(用户拍板)

> case(jolichatbox 域名配置):v8.334-337 链条全部正常工作(深调研/判断卡/跳 ui·browser),但四轴全低的配置改动仍默认吃满六路评审 —— 用户当场问「这么简单的需求为什么还要那么多 review」,消费 AI 中途 re-init 切 micro 落地开 MR(自评:「按全链启动了 —— 这是错配」)。
> 用户拍板目标形态:**按理说直接开发,完成后架构师 review 一下,PM 验收盯 staging 部署就可以了。**

### 变更
- **3.7 装配判断表补减法侧(加减两侧都要判)**:**超低**(纯配置/删除/文案级 · 无契约面 · diff/断言可验)→ 建议改走 `preset=micro`(同 feature re-init 合法 · 消费实证)+ **micro 附加轻门**(execute 完成后单路 architect diff 冷审〔subagent 错开 · 只拦 BLOCKER〕· PM 验收 = MR diff + 合并后盯 staging〔await-merge 自动带 CI〕);**低**(行为性但小)→ goal `[fast]` 单路合并 · blueprint 0 路 · **review `[architect]` 单路(用户形态)**;中 = 缺省;高 = 加法触发。
- **一致性倒逼**:判断卡/装配卡评审力度行,路数与四轴对不上必须写「为什么不降」(写不出就降)。
- **prepare §2.2「坚持 micro」正名**:行为性小改动亦合法(留痕)+ 附轻门建议 —— 消费 AI 的逃生路径转正。goal brief 同步。

### 测试
`test_review_intensity_tiers_v8341.py` 9 条:超低档 = 用户拍板句 / 低档逐 stage 缺省 / 判据机械 / 一致性倒逼 / 单路仍错开 / prepare 正名 / brief。全库全绿。

## v8.340 · ship1 后 CI pipeline 自动检查(用户拍板)

> 用户:另外 ship1 之后需要自动检查 CI 的 pipeline。
> 呼应点:await-merge 的 docstring 里写着原始痛点「CI 红无人接」(实证 132h 长尾)—— 但它只轮询合并态,CI 一直没人看。本版给这句话配上机器动作,并与 v8.339 的 MR 窗口期修复口闭环。

### 变更
- **push 记录成功即自动查一次 CI**(工具内建 · `_mr_ci_status` best-effort):emit `ci_status`(passing / failing / pending / none / unknown)—— 刚 push 常为 pending = 确认 pipeline 已起;failing → emit 直接带 `ci_fix_hint`(jump 回 dev 修复口);unknown(gh/glab 缺失或未登录)不拦流程。
- **await-merge 每轮轮询带 CI**:MR 未合并且 CI 红 → **不再傻等合并**,立即以 `CI_FAILING` 退出 + 修复口指引(红灯检查置于 MERGED 判定之前 · 测试锁顺序);MERGED / WAITING emit 均回显最后一次 `ci_status`。修复循环:jump 回 dev → push 重跑 → await-merge 续走(同一 MR)。
- 解析层纯函数化:GitHub `gh pr checks`(退出码 0/8/其他 × 行状态 · `_parse_gh_checks` 单测锁五态);GitLab `glab mr view -F json` 读 pipeline 字段。ship-stage 新节「MR 窗口期 CI 自动检查」。

### 测试
`test_ci_watch_v8340.py` 9 条:解析五态 / push emit 字段 / await-merge 轮询接线 + 红灯先于 MERGED / 修复口闭环 v8.339 / spec 节。v8339 spec 锚随新节重定位。全库全绿。

## v8.339 · MR 窗口期修复:同 feature 回 dev · 不开 Bug 流(用户拍板)

> case(supersdk SCLI):ship1 已 push,PR 上 3 个已知代码 blocker —— 消费 AI 按「Ship 后不可回」判成「必须开 Bug 流再合回」。用户纠偏:直接在当前 feature 回 dev 修,不要新开 bug。
> 判断:MR 反馈循环是交付的一部分 —— 逼开 Bug 流 = 把「改 PR」变成新立项(新 worktree / 新链 / 新文档全套税)。

### 变更
- **jump-to-stage 在 pushed 态开唯一放行口**:`--to dev` + `--reason`(必填)→ 放行,`ship.reopened_fixes[]` + concerns WARN(`mr-window-reopen`)双留痕 · **ship.phase 保持 pushed**(MR 还开着 · 事实不变)· completed_stages 不动;`--to` 其他 stage 照旧拒(hint 三分:未合并修代码 → 本口;已合并 → Bug 流;放弃 → close-unmerged)。reset-prev 的 pushed hint 同步指向本口。
- **ship-stage 新节「MR 窗口期修复」**:五步(jump 回 dev → dev 证据门照跑 · review/test 按修复规模与装配 → `push` 重跑 rerecord 更新同一 MR → zip 不重开〔初版墓碑 · 修复轮文档随接力卡〕→ 边界:平台已合并才走 Bug 流);SKILL Feature 停等链 ⑥ 带指针。
- push 重跑(rerecord + WARN)与 archive 幂等重入为既有机制 —— 本版零新命令,只开一个受控口。

### 测试
`test_mr_window_reopen_v8339.py` 6 条:放行 + 双留痕 + phase/历史不变 / 其他 stage 照拒 / reset-prev hint / 非 pushed 态不记 reopened / ship-stage 五要素 / SKILL 指针。全库全绿。

## v8.338 · 方向类停等第 2 项恒为「继续讨论」(用户拍板)

> 用户:PRD 和 Feature Planning 给出 1/2/3 选项时,第 2 项永远都是继续讨论 —— 目的是方便 AI 和用户讨论清楚目标和方向。

### 变更
- **SKILL R5(b) 新增恒定规则**(⏸️ 标记 · 红密度门撞线后按判例自降红):方向类停等(PRD 终确认 + Feature Planning 全部 R5)第 2 项恒为「继续讨论」—— 修订/落地是讨论收敛后的事,不逼用户在「确认」与「给修改点」之间二选一。
- **四处载体落位**:goal 终确认(2=按反馈修订重审 → 2=继续讨论〔目标与方向 · 想法/疑虑直接说〕)· planning 全景确认(2=要改全景 → 2=继续讨论,收敛后再改再确认)· planning 拆解讨论(措辞统一「继续讨论」+ 方向疑虑入口)· planning 收尾(2=继续讨论插位 · 原选项顺延 1/3/4/5/6 ·「一步到位」与自动合并硬门同步改号 1/3)。

### 测试
`test_option2_discuss_v8338.py` 5 条:R5(b) 恒定规则 / 四载体逐处(含收尾重排与硬门改号)。全库全绿。
