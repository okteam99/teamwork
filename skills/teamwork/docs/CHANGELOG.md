# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。

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

## v8.129 · 流程价值反思:ship2 后输出台账行 + digest(给仪式攒「该不该活着」的数据)

> 用户(承「teamwork 是否该存在」复盘):我们是否需要增加一个流程价值反思流程 · 在 ship2 后输出 → ok。

### 诊断:框架只有负反馈回路(出事 → 判例 → 加规则)· 没有正/零反馈(这环节这次拦没拦住东西)
- 规则只增不减(v8.0 以来 120+ 版首次系统性减法发生在 v8.121-127)· 仪式价值靠信念:多角色评审 self-talk 嫌疑 / 暂停点 all-default 率 / external confirmed 率全部无数据 · 「该不该砍」永远是辩论不是查表。
- 风险:反思流程自己变成新仪式 → 设计三条反仪式约束。

### 改动(doc-only · v1)
- **ship-stage.md §16**:ship-finalize 完成后 PMO 输出两层 —— ① 台账行 append 到 workspace `project-specs/PROCESS-LEDGER.md`(机器字段为主:实走 stages/时长/rounds/external 总采驳/角色真 finding/暂停点 改:默/bypass · AI 判断仅 2 格 · 照实抄不美化)② digest ≤10 行固定 4 问(拦住真问题?/纯过场?/流程新判例?/成本异常?)。
- **三条反仪式约束**:🔴 零新增暂停点(纯情报 · auto/yolo 照常)· 机器字段为主防 self-talk · 消费方指名(流程审视场景 + 年检 kill criteria:无新判例→仪式砍半 · external confirmed≈0→异质降可选 · 角色长期零真 finding→评审矩阵收缩)。
- **与既有 retros 划界**:`docs/retros/` = 业务/工程复盘(子项目级 · 知识层);PROCESS-LEDGER = 流程仪式价值度量(workspace 级)· 🔴 别混写(spec/模板双侧声明)。
- **豁免**:Micro 只记台账行不出 digest(最轻通道不加仪式)。
- 新 `templates/process-ledger.md` · 注册三处:templates/README 表 · conventions §13 project-specs 清单 · SKILL 路由表。
- ⏳ 物化 TODO(v2):ship-finalize 自动抽机器字段 emit ledger_row(AI 只补判断格)。

### 验证
- doc-only · pytest 3 failed / 523 passed(零回归)· 注册三处 + spec/模板分工声明 grep 一致。

## v8.128 · 排查先行律:根因未定的现象类输入先问题排查再定流程(治「猜测进 prepare 总览」)

> 用户(case:consuming 项目「ci 编译失败」):应该先诊断再给流程。

### 诊断:关键词路由跟「用户措辞」不跟「事实已知度」· prepare 总览写进未验证猜测
- 现行表「报错/挂了/500」直接 → Bug;「排查/查 log」才 → 问题排查 —— 现象类输入(ci 编译失败)被直接定 Bug · emit prepare:「代码现状」填了未验证假设(i18next 类型推导)· diagnose 才查出真因(ff326a74 path 类型加宽 · 4 调用点漏改 2)—— **命名/前缀路由/worktree 全押在猜测上**(真因在别的子项目就全配错)· 用户 review 被误导(中途反问「你排查到原因了么」)。
- diagnose-stage 自述「triage/prepare 读码只够判流程类型」—— 现象类场景连流程类型都判不可靠。

### 改动
- **prepare.md §2 立排查先行律**:现象类输入(报错/挂了/CI 失败/慢 · 无修复指令)且根因·影响面·归属未定 → 不定 Bug · 不 emit prepare —— 先问题排查(主对话 · 不进状态机)→ 排查闭合走 SKILL「Mode A/E 升级触发」暂停点(已验证根因 + 影响面 + 建议流程:转 Bug / Micro / Feature / 不动 / revert)→ 用户拍板 → prepare(排查结论 = 「代码现状」· 命名/路由据真因所在子项目)。**Bug 直入边界**:缺陷已指认(明确要求修复 · 现象+期望+位置已知)。判别题 = 「定流程所需事实是否已知」· 非「用户用了哪个词」。
- **关键词表两处收窄**(prepare §2 + FLOWS 识别列表):问题排查行接收现象类输入 · Bug 行加「仅当缺陷已指认」。
- prepare §0.5 反模式 +#7(现象输入未排查直接定 Bug + 总览填猜测)· §1.5.3「代码现状」加硬规则:**只写已验证事实 · 假设不得写入**。
- FLOWS 问题排查:用户选项补「转 Micro / revert 肇事 commit」+ 排查先行律;diagnose-stage 加**双入口**(②问题排查转入 → cite 结论复核不重查 · 重点落 BUG 报告 + 方案 R5 确认)。

### 验证
- doc-only · 关键词表两处口径一致(grep 复核)· pytest 3 failed / 523 passed(零回归)。
