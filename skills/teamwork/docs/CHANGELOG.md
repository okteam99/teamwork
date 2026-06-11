# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。

## v8.138 · panorama_sync 变更判级:L1 节点内增量不暂停(WARN 留痕)· L2 结构变更才停

> 用户(case:PTR-F260611065743 panorama_sync):全景修改的暂停点是否有必要 —— sitemap 仅描述行更新 · AI 推荐理由自证「IA 不变 · 未发现跨 Feature 冲突」· 用户按 1 纯放行。

### 诊断:暂停粒度与触发粒度错配 · 「纯过场」活标本
- 暂停保护两件事:IA 权威变更需多方评审 · 跨 Feature 影响需 owner 协调。case 两条件均不成立且 stage 内已查明(冲突扫描零命中 + 无节点增删)—— 事实已知还停 = 上抛已知事实(v8.128/v8.132 同款判别:停不停看事实已知度)· 收获只有默认放行。PROCESS-LEDGER「暂停点 改:默」kill criteria 的第一个判例(改:默 = 0:1)。
- 根因:`--panorama-changed=true` 判据是「panorama 文件动没动」(文件级 · sitemap 描述列更新也必走本 stage —— ui_design 不许直改 sitemap);暂停语义是「结构变更/跨 Feature 冲突」(语义级)。**stage 该进 · 暂停不该一律停**。

### 改动
- **变更判级**(substep 3 · 受影响 Features 扫描后判 · 依据逐条写进 §协调结论):**L1 节点内增量** = 三判据全满足(① 无节点增删移/路由变化 ② 无设计 token/共享视觉基线变更 ③ 受影响 Features 零命中);**L2 结构变更** = 任一不满足 · 拿不准按 L2。
- **L1 不暂停(任何模式)**:add-concern WARN 留痕(复用 auto-skip 语式)+ 零暂停 digest(≤3 行:变更/判据/产物指针)+ 直接 complete;**L2 必停**照旧(auto_mode 跳过规则不变)。
- **物化**:summary frontmatter 必含 `change_level: L1|L2`(缺即 FAIL —— 判级决定停不停 · 级别必须留痕);`authorized_pause_point` 改条件式。深校验(L1 时 sitemap diff 真无节点增删)不可枚举(sitemap 格式各项目异)→ AI 判 + 声明审计 + LEDGER L1/L2 比例兜底。
- **判级反模式成文**:结构变更标 L1 逃暂停 = R5 违规同级;ui-design-stage 触发处加期望管理(`true` ≠ 必暂停 · 不必预判影响大小)。

### 验证
- pytest 3 failed / 536 passed(baseline 3 · 净 +2:change_level 物化 pin + 条件暂停 pin)。

## v8.137 · goal 确认前置「重点 review 指引」:六节照实抄导读 · 替你做的判断放第一节

> 用户:PRD 在 AI 评审后直接交用户确认 · 希望请求确认前最后输出值得关注和了解的点 · 方便重点 review。

### 诊断:出口缺导读(v8.120 流程目标的对偶)
- 入口已有「流程目标」校准「要做什么」;出口(substep 9)用户面对的是全员 APPROVE 的成品 PRD · 没有导读告诉他**哪里值得抽查** —— 尤其 AI 在评审循环里替用户做过的判断(REJECT/DEFER 的 finding)完全不可见。

### 改动(doc-only)
- **goal-stage substep 9 加「重点 review 指引」**(请求确认前 emit · 固定 6 节 · 每节 ≤2 行):① **替你做的判断**(REJECT/DEFER 的 finding · AI 判断替代用户判断之处 · 抽查性价比最高 · 放第一节)② 核心取舍(争议已裁决 · cite id)③ 范围收窄(Out of Scope 中用户可能预期在内的)④ 影响面 ⑤ 修订轨迹(哪轮评审驱动)⑥ 残留风险/假设。
- **反即兴约束**:六节全部照实抄自已落盘结构化产物(pm_response / PL-CHALLENGE / revision_history / Out of Scope / PM 自查 / §待决策项)· 空节显式写「无」不可省 · 反模式成文(复述全文 / 营销式总结 /「经多轮评审已完善」/ 无产物出处)。

### 验证
- doc-only · pytest 3 failed / 534 passed(零回归)。

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

