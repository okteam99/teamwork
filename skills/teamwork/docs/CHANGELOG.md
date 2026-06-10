# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。

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

## v8.127 · 仓库减重 55%:删 docs/archive + CHANGELOG-ARCHIVE 清空立「定期清空」制(历史归 git)

> 用户(承 v8.126 体量分析):docs/archive 都删掉 · CHANGELOG-ARCHIVE 清空一版内容 · 定期清空 · 其他先不动。

### 裁定
- 冻结历史的「冷库」职责由 **git 提交历史**承担(永不丢 · git log/show 可溯)· 工作区不再热存 16.3k 行不被读的内容(占仓库 55% · 每次装机同步)。

### 改动
- 删 `docs/archive/`(v8-redesign 00-MANIFESTO / 01-COMMAND-SCHEMA / 04-PAUSE-POINT / 05-LESSONS + DESIGN + change-request · 2,396 行)。
- `CHANGELOG-ARCHIVE.md` 13,867 行(v8.121 → v1 全部 293 条)清空 → 政策 stub · CHANGELOG.md 头部立规:keep-5 轮转 → 归档暂存 → **定期清空**。
- 重指/清理悬空引用 **34 处**:README×2(顺带修 :332 残留「最近 1 版」→「最近 5 版」)· SKILL×4(含路由表归档行删除)· FLOWS / STANDARDS / prepare / goal-stage 各 1 · roles ×8「设计宪法」指针 · 工具 docstring/注释 ×11(state / engine / ship / stage_specs / update)。
- `_v8_engine._render_pause_discipline` 渲染串「📖 详细」改指 **SKILL.md § R5(b)**(现行权威 · 原 04-PAUSE-POINT-DISCIPLINE 已清理)· 同步 `test_pause_discipline_v871` 断言(04 文件名 → R5(b))。

### 验证
- grep 现行 md/py:docs/archive / 00-MANIFESTO / 01-COMMAND-SCHEMA / 04-PAUSE / 05-LESSONS 实体引用 = 0 · pytest 3 failed / 523 passed(零回归 · 含改断言后的 pause 测试)· 仓库 md 总量 29,821 → 13,552 行。

## v8.126 · 覆盖注册处收口单源:DEV-RULES 有则为准 · 没有按当前默认 · 去 KNOWLEDGE 兼容层

> 用户(承 v8.125):「KNOWLEDGE.md 声明为准」改为 DEV-RULES 口径 · 没有则按照当前规范。

### 裁定:覆盖声明唯一注册处 = DEV-RULES.md · 两级链(有声明为准 / 无声明按默认)
- v8.125 为平滑迁移留了「兼容既有 KNOWLEDGE.md 声明」层 · 用户裁定不要兼容层:单一注册处更干净 · KNOWLEDGE 回归纯「项目事实/踩坑」定位(dev-rules 模板边界表)。

### 改动(6 处去兼容)
- STANDARDS.md 全局优先级:兼容句 → 「覆盖声明唯一注册处 = DEV-RULES.md(未声明 → 按 standards 当前默认);KNOWLEDGE.md 不作为规范覆盖注册处 · 既有覆盖声明应迁入 DEV-RULES」。
- backend.md §四 日志 / §五 FK 覆盖条款 + ✅ 条件行 / §六 版本策略:去「兼容既有 KNOWLEDGE 声明」· 统一为「DEV-RULES 声明后以其为准;未声明按本节默认」。
- templates/tech.md FK 决策行示例:「KNOWLEDGE.md L{行号} 已覆盖默认」→「DEV-RULES.md L{行号}」。
- 不动(KNOWLEDGE 正确用途):common.md Gotcha 沉淀 / tdd.md「DEV-RULES(规矩)+ KNOWLEDGE(事实/坑)」分档 / backend §五 撞守卫后记 DEV-RULES/KNOWLEDGE(记坑)。

### 验证
- grep standards+templates+roles:「兼容…KNOWLEDGE」「或既有 KNOWLEDGE」「以 KNOWLEDGE.md 为准」= 0 · pytest 3 failed / 523 passed(零回归)。
