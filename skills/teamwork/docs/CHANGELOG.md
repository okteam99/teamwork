# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。

## v8.134 · 分层同构律:基建层共享包完全一致 · 页面层意图权威(四要素)· 共享基建改动须验全景编译

> 用户四轮推演(承 v8.133):镜像方式是否最合理 → mock 态全景提案 → 规划层不可纯文档(需最终视觉稿)→ 裁定分层同构 + 补「共享基建改动后 dev 结束须保证全景编译通过」。

### 推演与裁定(完整决策链留底)
- **v8.133 全量镜像律推到逻辑终点 = 双源死结**:一个「除数据层外处处必须相同」的镜像就是真实 app 本身 · 维护两份必须一样的代码正是框架反复消灭的反模式;且全貌要求意味着每次 ship 都要回灌镜像(spec 无此环节 · 权威必倒置)。
- **mock 态全景方案**(全景=真实 app mock 态 · 设计 worktree 内 mock-first)解了零翻译 · 但撞规划期约束(规划层需多方对齐的最终视觉稿 · 文字/草图不够 · 而规划期出真实 app 代码破 R6/worktree 纪律)+ 丢「多 future 合并浏览」能力 → 不采纳。
- **用户的第三条路**:同构承诺按「能否由结构保证」分层 —— 全镜像和废镜像都是错的。
- 顺带实锤:dev-stage §3 same-stack 还原段仍写「项目自身 /design/<page-id> 路由 diff」= 已废 in-app 旧模型残留。

### 改动(doc-only)
- **ui-design-stage 分层同构律**(替代数据层唯一差异律 · IA 镜像律保留):**Layer 1 基建层完全一致**(shell/架构/栈版本/组件库/主题 · ① 共享包优先〔monorepo workspace 包 · 两端依赖同一份代码 · 一致性由单源结构保证 · 零镜像维护〕② 不可抽包才版本锁定镜像+记豁免)· **Layer 2 业务页面层意图权威**(四要素:布局结构/交互流/状态/字段映射 = UI.md 既有段落 · 实现「重点参考」= 四要素必须对齐 · 像素/代码组织自由)· **权威时效**(设计权威至该页 ship 止 · 此后代码即真相 · 反模式:拿停更全景纠正已演化页面)。
- **下游编译契约(dev-stage 新 §3.5)**:共享基建两个消费者(真实 app + 全景)· feature diff 触及全景依赖的共享包 → dev-complete 前 worktree 内跑 preview-project build(exit 0)· 失败处置三分:机械适配顺手修(+UI.md 记录)/ 引发视觉变化走 --panorama-changed / 收回破坏性改动(改 API 者迁移所有消费者 · 同 Schema 影响分析责任模型)· 证据进 dev test evidence · ⏳ 物化 TODO(--panorama-build-exit-code 条件 evidence)· 自查清单 +1 项。
- **dev-stage §3 same-stack 还原重写**:废 in-app 路由 diff 残留 → 分层对照(L1 复用共享包不重写 · L2 四要素对齐非字节还原 · 设计变更不在 dev 顺手改)。
- **联动**:templates/ui.md(意图四要素 + 权威时效注)· designer(分层同构)· feature-planning Step 5(seed 基建层优先共享包)· 质量基线反模式更新(分层版)。

### 验证
- doc-only · pytest 3 failed / 532 passed(零回归)· 分层同构律/四要素/§3.5 五文件 grep 一致 · in-app 路由残留清零。

## v8.133 · same-stack 全景两律:IA 镜像(真实路由 + 首页设计稿)+ 数据层唯一差异 · 预览给页面直达 URL

> 用户(case:jdp console ingest-info-entry):same-stack 时预期设计稿与实现完全一致 · 区别只在数据层(mock);预览应给页面真实 path URL(如 :62706/xxxpath)· 不是把设计页顶在 / 上;/ 应是真实首页设计稿。相关 stage 描述是否有问题。

### 诊断:有问题 —— spec 亲手教 AI 给根 URL · 「全景」缺 IA 镜像这一半
- ui-design-stage § 预览写明「抓 PREVIEW_URL= 那行给用户 browse」(根 URL);preview.sh 模板注释同款;全文无「路由镜像 / 页面挂真实 path / `/` = 首页」任何要求 —— case 里 AI「未引入 react-router-dom(单页渲染不需要路由 · 有意省略)」是**照章办事** · 把设计页顶在 / 也合规。
- 「同技术栈」只字面要求栈名 · 未定义镜像范围:case 第一轮反馈(pnpm/antd 版本 / main.tsx 入口结构漂移)全靠用户人工抓 —— spec 缺「与真实实现差异只允许在数据层」的总律。
- sitemap.md 本就含路由(designer role:「IA 地图:层级/导航/路由」)—— IA 镜像意图在规划侧存在 · 但从未绑定到 preview-project。

### 改动(doc + 模板注释)
- **ui-design-stage 立两律**(same-stack 模型区):🔴 **IA 镜像律** —— preview-project 路由结构 = 真实 app(与 sitemap 一致)· 本次设计页挂真实 `route_path` · `/` = 真实首页设计稿 · router 属栈镜像必含(「单页不需要路由」= 漂移反模式);🔴 **数据层唯一差异律** —— 框架/版本/包管理器/入口结构/路由/组件库全镜像 · 差异只允许 mock 数据层 · 其他漂移修复或 UI.md 记显式豁免。
- **预览地址约定**:PMO 给用户的 URL = `PREVIEW_URL` + `pages_changed[].route_path`(页面直达)· 注明 `/` = 首页 · 多页给直达清单 · 把设计页渲染在 `/` 顶掉首页 = 违规。§5 暂停点决策参考 / preview.sh 模板注释 ×2 同步。
- **frontmatter 加 `route_path`**(same-stack 必填 · ui-design-stage 示例 + templates/ui.md):`panorama_file` 降级 static-html 必 / same-stack 可选。
- **联动**:roles/designer.md 镜像两律 + 直达 URL · feature-planning Step 5(全景 seed 即按真实路由组织 · router 必含)· 质量基线加 IA 镜像反模式行。
- ⏳ 物化 TODO:same-stack 时 route_path 必填校验(parse_frontmatter 不支持嵌套 list-of-dict · 需 raw 扫描 · 渐进)。

### 验证
- doc-only(+模板注释)· pytest 3 failed / 532 passed(零回归)· IA 镜像律/数据层唯一差异律/route_path 五文件 grep 一致(ui-design-stage / ui.md / preview.sh / designer / feature-planning)。

## v8.132 · goal stage 质量改造:调研前置 + PL 对抗质疑 + 三闸早问门 + 全员通过物化(产高质量业务目标 PRD)

> 用户:review goal stage 逻辑是否合理(目的:产高质量业务目标 PRD)→ 追问早问门会否纵容上抛/有无调研前置 → 追问对抗性讨论(PL 质疑)→ 确认。

### 诊断(review 实锤)
- **结构 4 弱点**:业务目标事实输入薄 · 校准点全在最后(锚定:全员 APPROVE 包装后 step 7 才见用户 · v8.128 镜像);PL「审视」非「质疑」· 无人负责杀前提(同上下文切帽子 = 鼓掌效应);external@goal 无业务上下文(留台账裁决);AC 规模无反压。
- **漂移/死门禁 6 实锤**:goal-complete **不校验 verdicts**(全 NEEDS_REVISION 也能过 ·「全员通过」纸面纪律);authorized_pause_point「Substep 6」vs 文档 7 步(编号错位);`_check_prepare_completed` 死门禁(恒真 · hint 引用 P0-12 已删命令);PRD-REVIEW 模板内嵌旧 4 角色叙述段(RD/Designer/PMO)+ Round schema「删 pl/pmo · architect 不参与 prd」与现行 5 角色三方矛盾 · 顶层 reviewers/verdicts 字段缺失(machine schema 不满足代码门禁!)· PASS 系词表漂移;章节名两套(§需求背景/§用户场景/§边界 vs 模板 §背景/§用户故事/§Out of Scope);模板「PM 起草规范 checklist(单源化)」含起草前必读代码现状 · 但 cite 清单不路由 = writer-only。

### 改动
- **代码物化(+2 门禁 · −1 死门禁)**:`prd_verdicts_all_pass`(verdicts 全 APPROVE/SKIP · frontmatter 原文块级解析兼容行内{}与缩进 map · 旧 PASS 词表判 FAIL 强制 canon)· `pl_challenge_present`(角色含 pl 时 PRD-REVIEW 必含 PL-CHALLENGE · 敏捷需求无 pl 自动放行)· 删 prepare_completed 死门禁 · pause point 改「Substep 9 + 条件:Substep 4 早问门」· brief 同步 9 步。**+9 测试**(行内/缩进/SKIP/旧词表拒/缺失/无 pl 放行)。
- **goal-stage.md 重写为 9 步五层防线**:调研先行(事实层 · 四类:代码现状/KNOWLEDGE FA·Pref·OoS/GLOSSARY/上游规划 = 早问门入场券)→ 起草(模板单源 + AC>10 规模反压)→ **PL 对抗质疑**(前提层 · 质疑五问:价值前提/问题定义/范围最小化/上游对齐 cite/复活检查 · Q1 命中 subagent 隔离不喂起草心路 · PL-CHALLENGE-{n} 产物)→ **三闸早问门**(用户主权层 · 条件暂停:调研穷尽/主权判别〔上抛事实类=R5 违规〕/格式四件套+≤3+全带推荐 · auto 不停转 §待决策项+WARN)→ 多角色评审(完备性层)→ 用户确认(裁决层)。
- **模板对齐(464→388)**:删旧 4 角色叙述段 · role 枚举对齐现行 5 角色 · 顶层 reviewers+verdicts 补齐(满足代码门禁)· 词表统一 APPROVE|NEEDS_REVISION|SKIP · category +premise-challenge · 调研四类入 checklist ·「子步骤 3 RD 评审」×3 → substep 5 多角色。
- **联动**:roles/pm.md(调研/早问门/对抗自查)· roles/product-lead.md(质疑五问职责)· prepare Q1 命中后果 +「PL 质疑 subagent 隔离版」· 对抗有效性观测进 PROCESS-LEDGER(PL-CHALLENGE 采纳率 · 早问门 改:默)。

### 验证
- pytest 3 failed / 532 passed(baseline 3 · +9 新全过 · 零回归)· 模板旧口径 grep 清零(PASS 词表/旧角色段/删 pl 注释/子步骤旧编号)。

## v8.131 · 框架自省台账 RETRO-LEDGER:发版三件套 · 框架反思归框架仓(永久层)

> 用户:是否每次流程完善后写一段 teamwork 的问题/优化点/有用的地方/反思 · 记到 teamwork skill 子目录 —— 全项目总结汇一起 · 框架自身的东西不适合放项目目录。

### 诊断:框架自省无持久层 · 正反馈无归档处
- 框架反思散落 chat(session 结束即丢)与 CHANGELOG(keep-5 轮转 + 归档定期清空 · **故意易逝**);「有用的地方」(正反馈)更是哪都没记 → 年检只剩坏消息可查。PROCESS-LEDGER(v8.129)是项目侧的 · 框架侧缺对偶。

### 改动(doc-only)
- 新 `docs/RETRO-LEDGER.md`(框架自省台账):一行一版 · 6 列(版本/来源 case/问题/优化点/**有用的地方**/反思)· 单元格 ≤1 行 · 不复述 CHANGELOG · **永久**(超 ~500 行年检主题化压缩 · 原文 git 可溯)。
- **三层分工成文**:CHANGELOG = 单版细节(易逝)· PROCESS-LEDGER = 项目侧环节价值 · RETRO-LEDGER = 框架侧自省蒸馏(永久)。
- **发版三件套**(CHANGELOG 头部立约 · 同 commit):CHANGELOG entry + RETRO-LEDGER 1 行 + 版本 bump。
- **消费方指名**:年检/存在性审视直接读表;框架改进 session 动手前读最近 10 行(防重复踩坑)。
- **回填种子**:本 session v8.120→v8.130 共 11 行 + v8.131 自身 = 12 行。

### 验证
- doc-only · pytest 3 failed / 523 passed(零回归)。

## v8.130 · 台账采集时机修正:ship2 归档删目录后取数断粮 → 两段式(planning-backref 采写 · finalize 后 emit)

> 用户(承 v8.129):ship2 之后相关的产物都压缩了 · 你还能找到统计信息么。

### 诊断:对 —— v8.129 v1 设计两个缺陷被一问暴露
- **取数断粮**:§16 原定「finalize 完成后输出」· 但 §15 归档已把 state.json / REVIEW.md zip 进 `_archive/<id>.zip` 并删原目录 —— 数据没丢(zip 自描述 · `unzip -p` 可取)但取数高摩擦 · AI 大概率跳过或凭记忆填(违「照实抄」)。
- **写入无载体**:finalize 后 merge_target 全程只经 MR · 此时 append 台账行 = 脏文件无合入载体。

### 改动(doc-only)
- **§16 改两段式**:① 采集 + 写台账行 = ship2 step 5 `planning-backref` 暂停点(state.json/REVIEW.md 尚在磁盘 · 取数零成本)· 台账文件加进 `--planning-artifacts` 随**同一收尾 MR** 合入(`_resolve_planning_artifacts` 只校验「存在+仓内」· 已核代码)② digest = finalize 全部完成后 emit(从已写行渲染 · 时长口径 = init → ship2 暂存 · 表内统一)。
- **兜底成文**:漏写 → `unzip -p features/_archive/<id>.zip <id>/state.json` 不落盘取数 · 补行随下次任意 MR。
- v2 物化 TODO 同步:ship-finalize 在 planning-backref 暂停点 emit ledger_row 草稿(漏写不可能)。
- 同步措辞 4 处:templates/process-ledger.md 写入时机 · conventions §13 · SKILL 路由表 · templates/README。

### 验证
- doc-only · `--planning-artifacts` 路径校验已读码核实(存在+仓内即可)· pytest 3 failed / 523 passed(零回归)。
