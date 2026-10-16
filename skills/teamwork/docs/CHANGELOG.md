# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.362 · 归档后 MR 修复通道 + CI 归因修正(实证 GPT-F261014120919-Offer-Plugin)

> 起因:ship1 归档后 MR CI 红,修一行 tsconfig —— 被迫重走 dev→review→test→browser_e2e→pm_acceptance→ship,test / browser_e2e 各 bypass 一次;同时 await-merge 把本分支新增 `proxy.ts` 导致的 TS2307 连判 8 次「base 预存在」,监控不报警。

- **P0 · 归档后报告门不再逼 bypass**:`ship.phase ∈ {archived, pushed}` 时 TEST-REPORT / BROWSER-TEST-REPORT 跳过「在 commit 内」检查(需求目录已 `git rm --cached` 出分支 · 永远满足不了)· 文件存在照查 · concerns 记 INFO(设计内豁免)。实证:本单 bypass 2 次。
- **P0 · MR 修复轻量通道**:回炉目标 dev、相对上次 push 代码改动 ≤3 文件且 ≤30 行 → dev-complete 直达 ship 重录 push(验收早已发生);超出照走完整链 · 重录即关闭通道并回到 completed · dev brief 要求测试证据跑 CI 失败的那条命令。原「bypass_log 区分豁免/逃生」不再需要(这类 bypass 不再发生)。实证:一行修复走完 7 个 stage。
- **P0 · CI 归因**:GitLab `_mr_ci_status` 原来 `failing` 恒为空 → 归因无 job 名 → 每次落进「预存在」分支(与「未知按自己引入」的设计相反)。改为 API 取失败 job 名(取不到记 `pipeline`)· base 只看 merge_target **最新一条** pipeline · 失败 job 名命中本分支 `git diff origin/<base>...HEAD` 改动目录 → 直接判本 feature 引入 · 依据逐条打日志 · 两边都空时不判预存在。实证:`fe-ember-official-site-build` 连判 8 次。
- **P1 · ci-commands 跟 GitLab `include: local`**(递归 · 支持 glob)。实证:返回 0 条,CI 对照只能人工。
- **P1 · test-baseline 不越界写主工作区**:worktree 里没有 project-specs 时 `--add` 返回 PENDING,`--target worktree` 写副本 / `--target main --user-confirmed` 写主工作区 · 读取取各份并集。实证:写到了主工作区未跟踪文件。
- **P1 · 复发防御清单门禁**:project-specs 在主工作区未跟踪时给两个落点的绝对路径,主工作区那份有条目也算通过。实证:只能 `--no-defense-entry` 跳过。
- **P1 · 文档**:dev 中途追加范围 → `jump-to-stage --to blueprint`(reason 记停掉 / 待重派的 lane)· 未新增命令(已有能力);blueprint 确认卡对类型/枚举/provider 类字段问「取值集合固定还是会增长」(只问取值集合,不问「将来要不要做 X」)。实证:登录 provider 可扩展性在 dev 中途才追加。
- 验证:新增 `test_post_archive_mr_fix_v8362.py` 16 例(真实临时 Git 仓库跑「归档后修 1 行 → 不 bypass 重录 push」全流程)· 全量通过。

## v8.361 · 年检提效:砍掉价值不高的环节(用户拍板「都做」)

> 数据源:aon-core `PROCESS-LEDGER.md`(2026-08-16 后 128 个 Feature)+ 174 份流程复盘。AI 自主中位 115m、等用户中位 136m(等待占墙钟 ~70%)· **~30% 轮次是协调开销**(781/2564)· 暂停点 71% 按默认放行 · 台账 `rejected_with_feedback` 0 次。外审采纳率 goal 7/7、blueprint 24/24 —— **评审环节保留**,砍的是框架自己制造的开销与重复停等。

- **门禁纯开销**:删 goal `prd_review_after_prd`(mtime 顺序门 · 每改 PRD 都得连带碰 PRD-REVIEW · 10 份复盘记过);`must_be_in_commit` 放宽为「本 stage 内已提交且与 auto-commit 一致」也算入账(TEST-REPORT 与代码分两次提交不再被逼重提 · 未提交改动 / 上一轮旧报告仍拦)。
- **测试证据指纹只算代码**:流程目录(feature 目录 / `docs/features` / `docs/retros` / `project-specs`)下的文档类文件不进指纹 → 提交 TEST-REPORT / 改 PRD 不再让证据作废重跑(76 份复盘提到重跑);feature 目录里的 `e2e/*.py` 照算。新增 `state.py tree-hash` 单源取指纹(配方不再手抄 python 片段);旧口径指纹兼容放行。
- **验收拍板并入 ship1**:AC 全过 → pm_acceptance 不停,验收结论进 ship1 MR 卡片「✅ 验收」段,**点合并 = 验收通过并发布**;要改回「要改 <问题>」(MR 窗口期放行口加 `goal` / `ui_design`)。AC 没过 / 有阻塞 / 有产品取舍 → 照旧停三选项。
- **流程复盘文档按需写**:仅协调开销 ≥30% / 有 bypass / review ≥3 轮 / MR 窗口期回炉 / 反思摘要是「判例:」时写;ship brief 直接告诉本单写不写 · 台账行照落。
- **medium 档不产 TC.md**:测试设计归 TECH §测试策略 · AC↔测试绑定走 `PRD.acceptance_criteria[].test_refs`(与 lite 同载体 · test 阶段校验);引擎 `StageArtifactSpec.skip_if`。
- 同期已推 dev 的小改(v8.360.5–.8):功能生效闸先问触发条件能否从源头消除 · PRD 终确认待决策项逐项讨论 · 守卫清单「只在绕过时变」必给触发路径证据。
- 验证:新增 `test_annual_cut_v8361.py` 20 例(真实临时 Git 仓库验指纹与入账判定);全量 **1840 passed, 2 subtests passed**。

## v8.360.4 · 修复评审证据归属、流程修订与合并后清场

- 修正规划收尾的选项编号与执行分支，选 2 仅继续讨论；统一独立冷审的执行规范。
- 外审结果按阶段筛选，新派发绑定请求 ID 与被审 commit；修复后必须有覆盖最后 fix commit 的实际结果，prompt 不再充当完成证据。
- `revise-plan` 同步执行位置、合法下一阶段与评审配置；自定义维度的阶段准入与文档要求按实际计划判定。
- `await-merge --feature` 检测合并后在主工作区实际调用 `ship-finalize`，保留失败、脏文件保护和待决策结果。
- 验证：新增 20 个回归用例；全量 **1812 passed, 2 subtests passed**；真实临时 Git 仓库验证 worktree 删除与主工作区同步。

## v8.360 · 防过度防护:先问冗余,再算 ROI(用户拍板)

> 起因 case(SVC-CORE payout 两态 · 财务账本):TECH 列了 7 项 DB 守卫。用户「有必要做这个 check 么,是不是代码保障就好了」→「**你看下还有哪些不必要的 check,减少过渡保护**」→ AI 第二轮自己分出三组,**第一组「纯冗余,建议全删」**:up 前置断言「无 `status='failed'` 行」(紧接着重建的列 CHECK 对存量行本来就会 23514)· 三条常驻 grep 门「零引用」(删掉的表和函数编译期就报错)——「它们只是把后面必然发生的失败提前说清楚,**删了行为不变**」。
> 🔴 **这些冗余是在冷审 26 条全部处置、Round 2 双路 APPROVE 之后,靠用户追问两次才挖出来的。** 框架明明有 ROI 规则(v8.266/v8.279)却没拦住。

### 三层原因
- ① 🔴 **分类漏网(决定性)**:ROI 算账的对象定义是「降级兜底/安全兜底(fallback / degradation / 重试熔断 / 防御层)」= **出错时怎么办**(fail-safe);而 DB CHECK / trigger / 前置断言是**不让错发生**(guard)。实证:那份 TECH 白纸黑字写着「🛡️ **兜底清单:无**」,同时挂着 7 项 DB 守卫 —— **逐项算账、填 ROI 表、随暂停点透出**这整条流程从未触发。用户看到的是「变更明细」,而那张表问的是「为何非更简方案不可」= 为什么要**改**它,不是为什么要**有**它。
- ② **ROI 对守卫天然算得过**:财务账本脏数据后果极高 → 概率×后果永远立得住。v8.279 自己就写了「安全加固/兜底降级**听着最负责任故最难驳**」。而 AI 第二轮用的判据不需要估概率:**「删了行为会变吗」**,当场可判。
- ③ **冷审拦不住**:冷审的 mandate 是找缺陷,而「多一道无害的断言」读起来是更严谨 —— **防护读起来永远像更负责任**(与 v8.354「限制读起来永远像最小范围」同族)。

### 变更
- **清单正名 + 扩容**:§兜底清单 → **§兜底与守卫清单**,显式纳入 **DB CHECK / 约束 / trigger / 前置断言 / 运行时校验 / 常驻门禁(grep 门、lint 门)**。暂停点触发条件、blueprint 透出段、goal/blueprint brief、external 协议**六处消费方一并更新**(先 grep 出全部消费方再改 —— v8.356 的教训)。
- **前置判据(可判问句 · ❗ 顺序不可换)**:**这道防护删掉之后,行为会变吗?**
  - **不变**(后面必然有另一道拦住同一件事)→ **纯冗余,直接删** · **不进清单、不用算 ROI**;
  - **只在绕过正常路径时变**(运维直写 / 迁移脚本 / 将来绕过 service 的函数)→ 有取舍 → 进清单算 ROI,**随暂停点给用户拍板**;
  - **正常路径就变** → 那不是防护,是**功能**,归各自章节。
  🔴 **为什么顺序不能换**:ROI 对纯冗余也会算出「保留」—— 成本才十几行、后果却极高,于是永远立得住。三分法正是那个 AI 第二轮自己得出的,**框架里没有这个分法**,所以它第一轮没做。
- **清单表加「🔴 删了行为会变吗」列**,并写明「答『不变』的**不该出现在本表**」。
- **blueprint ⚔️ 对抗段补守卫版判据**(复用 v8.354「限制必要性」的形状):**这道守卫是需求要求的,还是我加的?**「我加的」→ 要么说出「不加会出什么事」**且那件事不会被别的机制拦住**,要么删。
- **external 协议同步**:external 天然偏加防御层 → 其 finding 裁决也是**先问冗余再算 ROI**,答「不变」直接 REJECT。
- 📎 撞 v8.283 价值门(🔴 规则 39 条 vs 3 处 why = 13.0 > 12)→ **服从门裁**:把新增规则的实证理由显式标成 `why:`(而不是削 🔴),比值回到 7.8。

- test_guard_redundancy_v8360(16 · 含「新判据不吃掉既有 ROI/透出」的回归锁)· 全量 **1792 passed**

## v8.359 · WS 拆解明细:去「人维护」+ 用户决策事实入槽(用户拍板)

> 用户(WS-48 财务链路截图):「这个**人维护**去掉,ws 这里 feature 补充一点可以详细一些,**不能丢用户决策的事实**」。

### 两个问题都真
- ① §拆出的 feature 标着「规划态 · **人维护**」,但这节恰恰是 **feature-planning 流程产出的** —— 标注会让 AI 以为不归它写,于是写薄或不写。
- ② 槽位只有 范围 / 依赖 / **高层 AC**,**规划期用户拍的板没有落点**:选了哪个方案(税务方案 A 不是 B)、打款 failed 分几态、定了什么口径 —— 全留在规划当时的对话里。

> 🔴 **这是 v8.353「已确认意图入 PRD」的上游断点**:v8.353 把 prepare 确认的意图搬进了 PRD,但更早一层(WS 规划期的决策)仍然只活在对话里。换 session / 派 subagent 就没了,下游 PM 只能凭「范围」一句去猜用户当初要什么 —— 而**意图错了是唯一一类下游全部质量门都拦不住的错**。

### 变更
- **去掉「人维护」标注**;`ws-lint` 新增一条:存量 WS 仍写该标注 → 报出(否则它会一直被抄下去)。
- **新增 `features[].user_decisions`(机读)+ 正文 🔒「用户已拍板的」段**:选了什么 / 排除了什么(并标「做不到」还是「我们选的边界」)/ 定了什么口径 · 🔴 **原样搬不润色**(润色 = 二次解释,偏差正是这么进来的)。
- **`ws-lint` 查槽位存在**(逐件点名缺的那些)· 🔴 **不查非空** —— `[]` 是合法值(该件未经用户单独拍板);强制非空会**逼出编造的「决策」**(与 v8.358 同一判断:必填 + 无出口 = 幻觉配方)。
- **链条写明**:这些事实是起 feature 时 `init-feature --user-intent` 的**输入**,再落进 PRD §已确认意图 —— 载体到位还不够,不说清往哪传,填了也没人用。
- **拆解明细改为「宁详勿略」**:原措辞「核心 AC(**高层** · 详细 AC 在 Feature PRD)」会诱导写薄,而这节是下游**唯一**能拿到规划期上下文的地方;AC 可写到具体字段 / 路由 / 状态值。
- 📎 ws-lint 拿到的是**文本**而既有 `_parse_ws_features` 收 `Path` → 拆出 `_parse_ws_features_text` 两边共用,**没写第二份扫描器**(双实现必漂 · v8.352 `_flow_key` 漏 floor 即实证)。

- test_ws_user_decisions_v8359(13)· 全量 **1776 passed**
