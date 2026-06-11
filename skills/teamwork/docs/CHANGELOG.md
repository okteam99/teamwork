# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。

## v8.136 · claude -p 链路三修:prompt-doc 每轮唯一命名(审计=输入)· 模板提取治双嵌 PRD · 显式 doc staleness 门禁

> 用户(case:PTR-F260611065743 三轮 external review):claude -p 总是出现各种问题 · 整体 review → 裁定保留 doc 优先 · 每轮 doc 名唯一 · 传入 doc 路径。

### 诊断:结构性事故链(手工修复不可能根治)
- **固定名缓存中毒**:round 1 走 inline fallback 后把 prompt 写进固定名 `goal-claude.md` 作「审计副本」(v8.106 保留);round 2 的 `if prompt_doc.exists(): 优先读` 把它当 v8.44 人工 doc 消费 → 评审 stale PRD v0.1;AI 手工删 doc → round 3 又写回 → round 4 必复发。审计产物成了无失效机制的缓存。
- **模板整文件替换双嵌 PRD**:fallback 拿 claude-agents/reviewer.md **整文件**(文档+模板混合体)做全局 replace —— 尾部「占位符说明」表里的 `{file_list}` 示例格也被灌入完整 PRD → prompt 含模板元说明 + codex 对照表 + **双份 PRD**(~400 行垃圾 · 加重长 prompt 卡)。
- v8.44「scaffold + 人工填 summary」推荐路径零使用记录 · 每轮都 fallback + WARN · 形同虚设。

### 改动(代码 + 测试)
- **每轮唯一 prompt-doc(用户方案 · 优于直接废 doc)**:`_new_prompt_doc_path` = `<stage>-<model>-<UTC时间戳>.md` —— 默认路径每轮**现生成**(模板 Prompt 主体提取 + inline 当前文件 → 写新 doc → 用它执行)· **审计 = 输入零分叉** · 旧轮留档不复用 · 随 feature 归档。
- **显式 `--prompt-doc` 保留优先** + **staleness 门禁**(`_prompt_doc_stale_reason`:doc mtime 必须新于全部待评审文件 · stale → FAIL with hint)。
- **模板提取**(`_extract_prompt_body`):只取「## Prompt 主体」fenced block 内文本做替换(占位符表/对照表永不进 prompt · `{file_list}` 替换点唯一)· claude 路径 + subagent 降级路径同享。
- scaffold-review-prompt 改唯一命名(覆盖冲突消失 · `--force` 降 no-op 兼容)· subagent 降级 doc 同步时间戳命名。
- 测试:改 3(路径唯一性 / scaffold 两轮两 doc 且首份不被动)+ 新 3(提取排除模板文档+替换点唯一 / 无标记回退兼容 / staleness 门禁三态)· test_state 196 全过。

### 验证
- pytest 3 failed / 534 passed(baseline 3 · 净 +2 · 零回归)· grep `_default_prompt_doc_path` 残留 = 0。

## v8.135 · 注入块加「Subagent 默认授权」:满足宿主工具契约的长期授权 · 授权管能不能 · R4 判据管该不该

> 用户(case:codex-cli 跑 teamwork goal external review):注入逻辑增加 subagent 使用声明 —— 用户明确授权在 Teamwork 流程中默认使用 subagent(PRD/Blueprint/Review cross-review · 并行探索 · 互不重叠实现子任务)· 无需每次另行确认。

### 诊断:宿主工具契约与 teamwork 流程的缝隙
- Codex 的 spawn_agent 契约要求 "user explicitly asks";teamwork 流程(external review / 多角色评审 / PL 隔离质疑 / 并行实现)预设用 subagent —— 每次等口头授权会卡住流程(尤其无人值守 auto/yolo)。授权的合法落点 = 宿主指令文件(工具契约读取处)= 注入块。
- 两个措辞修正:注入块三宿主共用(不能写死「Codex」→ 通用宿主表述);约束不复述 SKILL 已有纪律(防双源 · 只给指针)。

### 改动(doc-only)
- **host-instruction-injection.md 注入块新增「Subagent 默认授权(Teamwork 流程)」段**:用户明确授权(三宿主通用)在 Teamwork 流程中默认使用 subagent · 无需每次另行确认;适用枚举(各阶段 cross-review/多角色评审 · PL 对抗质疑隔离执行 · 并行探索 · 互不重叠 write scope 实现子任务 · 验证/测试 sidecar);约束仅指针(R4 判据 · worktree 内写路径 · 流转不外包 · 主对话整合)。
- 本仓 CLAUDE.md 实例同步(gitignored · 下次 bootstrap sync-drift 也会按模板刷新);consuming 项目在各自下次 bootstrap 自动获得。
- **SKILL.md R4 subagent 条款加授权指针**:授权已长期化 —— 解决「能不能用」;R4 判据(独立且够大)仍管「该不该用」· 防授权被读成「滥用许可」。

### 验证
- doc-only · pytest 3 failed / 532 passed(零回归)· 注入模板/CLAUDE 实例/SKILL R4 三处口径一致。

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
