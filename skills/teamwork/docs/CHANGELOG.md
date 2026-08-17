# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.335 · teamwork-space 入口注入 CLAUDE.md / AGENTS.md(用户拍板)

> 用户:初始化时把 teamwork-space.md 引入到 AGENTS.md 和 CLAUDE.md —— 目标是**不用 teamwork agent 也能充分了解项目**。
> 与 v8.211「注入退役」的边界(不构成推翻):当年退役的是**流程指令注入**(共享仓库里非 teamwork 用户被迫吃 PMO/worktree 规则 · 实证 case);本块**受众相反**(正是为非 teamwork 用户服务)· **内容零流程指令**(只有知识地图指针)。

### 变更
- **`bootstrap.maintain_space_pointer`**(随 session bootstrap · space 骨架之后):把 managed 块注入 `CLAUDE.md` + `AGENTS.md` ——「📍 项目知识地图:先读 teamwork-space.md(知识入口单源 · 无论是否使用 teamwork 流程,了解本项目从它开始;代码是细节唯一真相)」。
- **行为**(幂等):`teamwork-space.md` 不存在 → skip;目标文件不存在 → 创建(仅块);存在无块 → **顶部插入**(发现性 · 块外一字不动);存在有块 → 原位重写块内(带版本 marker · 升版可换文案不重复)。marker(`TEAMWORK-SPACE-POINTER`)与 legacy 清理正则(`TEAMWORK_BEGIN:`)不同族 —— `maintain_host_injection` 清历史注入时不会误删新块。
- guide 文档(teamwork-space-guide)注明注入机制与 v8.211 边界。

### 测试
`test_space_pointer_v8335.py` 7 条:双文件创建 / 顶部插入保用户内容 / 幂等 + 旧版块原位升级不重复 / 无 space 跳过 / **块内零流程指令**(PMO/worktree/Subagent/state.py/R5 全禁)/ legacy 清理不误删 / bootstrap wiring。全库全绿。

## v8.334 · 起草前深入调研 + 评审深度判断卡(回显不阻塞)(用户拍板)

> case(supersdk Analytics-Dashboard):起草前调研 = KNOWLEDGE/GLOSSARY + **读 1 个文件 + 2 条命令** → 直接写 174 行 PRD;派冷审用默认双路、零判断输出。旧 spec「按需选查」下这**完全合规** —— 判据缺失,不是执行失误。
> 用户拍板:做深入的调研 → 给出 PRD 评审深度判断(是否需要额外评审 · 需要谁 · 判断理由)→ 回显给用户但不阻塞,自动进行评审调度。

### 变更
- **「起草前调研」升级为「起草前深入调研」**(goal-stage):四面**必过**(代码现状 **grep 实测**〔只读一个文件不算调研〕· 数据面〔涉数据/统计/报表必查 schema 与查询路径〕· 既有相似实现 · 上游与规范)—— 查过的面各给一句发现,确不相关写「不涉」,**不许静默跳**;🔴 深度判据可判定:**查到能回答装配四轴 + 能写出「这个 PRD 最可能错在哪」,答不出不许起草**。调研同时喂两张卡(3.7 装配证据 + 评审深度判断卡)。
- **评审深度判断卡**(3.7 第①拍修订「不问用户」→「不问用户、但必回显」):派冷审**前** emit —— 调研纪要(关键发现 · 影响面/数据面实测)· goal 冷审 roster 与模型错开 · **是否需要额外评审**(+qa/+dba/升异质/默认两路)· **逐项判断理由**(引四轴证据)· 下游装配预告一行;**回显后直接派发不停等**(想调回一句 · 与第②拍「默认执行」同律)。
- goal brief 动作点同步(8 步开头改为 深入调研 → emit 判断卡 → 起草)。不设机器门(卡是回显行为 · 载体倒逼:调研不深写不出卡)。
- **并行姿态(用户追拍)**:四面默认多 subagent 并行采集(验证档 · 每面一路 ·「查什么+返回结构化发现」)· **整合与判断留主对话**(深度档)——「调研采集」入验证类白名单(agents/README + SKILL 同步);**不新立调研档**:档位是任务性质三分类,采集/判断二分正好落既有档,第四档只会让错开/例外/申报全部多一维。

### 测试
`test_research_depth_card_v8334.py` 9 条:四面必过+显式不涉 / grep 非单文件 / 深度判据可判定 / 双卡喂料 / 卡在派发前 / 拍板三要素 / 回显不阻塞 / v8.329 两拍结构不受扰 / brief 载体。全库全绿。

## v8.333 · PRD 验收标准表:大白话固定第二列(用户拍板)

> 截图实证:消费项目 PRD 的 BDD 列巨长,💬 大白话被挤成右侧竖条(一行一字)—— 给用户终确认读的那列反而最不可读。用户:大白话放第二列,宽一点。

### 变更
- **templates/prd.md 列序**:`ID → 💬 大白话 → 描述(BDD) → 优先级 → 覆盖测试`(大白话紧跟 ID · 渲染时拿到可读列宽);示例行同步。
- **宽度指引入注释**:大白话写**一句完整的话**别写三五个字(markdown 列宽由内容驱动 —— 位置 + 内容长度是仅有的两个旋钮);机器校验按表头名定位 · **不吃列序**(存量新旧两种列序都过 · 零迁移)。

### 测试
`test_ac_plain_column_v8333.py` 6 条:模板列序 / 指引锚 / 示例行 / 机器门新旧列序皆过 / 新列序下空值仍拦。全库全绿。

## v8.332 · 主对话 = Orchestrator:dev/test 默认姿态(用户拍板)

> 用户:dev stage 和 test stage 加上不建议在主对话(主循环)进行开发和测试 —— 主对话优先用做 Orchestrator:任务拆解、阶段规划、子代理调度、集成接线、提交/推送、验证门禁、小型精准修改等。
> 设计要点:**位置(谁持有 context)与档位(用什么模型)正交** —— 验证档白名单早已把测试执行推出主对话,但档位表执行档行还写着「主对话继承会话模型即是」,等于默认背书主对话写码;本版把位置姿态独立立规。

### 变更
- **dev-stage 1.7(🎛️)**:不建议主对话直接成块开发 —— 拍板职责清单逐项入规(任务拆解 / 阶段规划 / 子代理调度 / 集成接线 / 提交推送 / 验证门禁 / **小型精准修改**);成块实现派 subagent(worktree 内路径 · **执行档继承会话模型不降档** · Meta 申报);出口显式:小 / 耦合 / 强串行 → 主对话直接做(派发协调开销反拖慢)。why:主对话 context 是最稀缺资源(跨 stage 编排状态 / 用户拍板记忆 / 集成全景全活在这里)· Orchestrator 姿态让并行成为默认而非事后补问。
- **test-stage 1.7**:不建议主对话直接编写与执行测试(执行本就是验证档白名单硬约束 · 编写同白名单默认派);主对话留 环境预检调度 / **差分基线裁决** / 门禁命令 / 失败分诊 —— 测试日志是最大的 context 污染源之一。
- **档位表执行档行调和**(agents/README):模型继承会话档不降 + **位置默认 subagent**(单源指 dev-stage 1.7)——「主对话继承会话模型即是」旧背书措辞退役。
- **brief 三处动作点同步**(dev · test Feature 流 · test Bug 流)。建议姿态 · 不设机器门。
- **全局化(用户追拍:其他阶段也需要)**:总纲上提 SKILL § subagent/teammate 条目(全 stage 默认姿态 · 单源 · 🔴 密度不变)—— 成块产出(实现/测试/调研 fan-out/冷审/设计稿)默认派;dev/test 1.7 降为 stage 实例并标单源关系。

### 测试
`test_orchestrator_posture_v8332.py` 10 条:拍板职责逐项 / 出口保留 / 位置×档位正交 / 白名单衔接 / 档位表旧措辞退役 / 三 brief / 无新门。全库全绿。

## v8.331 · standards 载体合并:tech-rules 三时点唯一必读(用户拍板)

> 拍板链:①整理为「技术架构及方案的 review 要点」一个文件 · 没必要拆太多文档(前后端约束已很少);②就叫 tech-rules.md,把 HARD-RULES 也整合进来 —— 方案起草、review、dev 开发三时点必读;③明确必须读项目 `project-specs/DEV-RULES.md`(标准路径)· **需同时满足项目规范和本规范 · 冲突部分以项目规范为准**。
> 讨论中确认的关键事实:backend.md 现存内容的主要动词已是「评审必查 / CR 阻塞」—— 重命名是纠名实;整合消灭「详见分册」二跳,**起草时读的就是 review 会查的**(门与预告同源)。

### 变更
- **新 `standards/tech-rules.md`(~160 行 · 五节)**:§一 逆模型默认(原 HARD-RULES)· §二 框架/项目约定(+权威源单源 / 架构文档落点 / Mermaid / TEST-DATA 登记四条薄段收编)· §三 方案与架构门(原 backend 评审门整体入驻:API 契约优先级链与缺省码表 · 日志 CR 门详版 · Schema 变更门与验证链 · FK 决策门〔唯一权威〕· API 版本)· §四 前端专项 · §五 收口自查表。头部即用户三句契约(标准路径 / 同时满足 / 冲突以项目为准 · DEV-RULES 缺失回退 + 提示固化)。
- **内容按消费时点归位(搬家不是删除)**:scratch 全文 + 迁移命名与起号纪律 → conventions §12.48/12.49(执行环境约定 · 与构建世界同族 · lazy-install 踩坑并入 §12.45);测试脚本两层契约 → scripts-policy §7(顺手删 §3 样板 + §4 已完结历史段);Designer 自查 6 维 → ui-design-stage 附录(verify-panorama 指路牌同步)。
- **三文件退役**:HARD-RULES.md · common.md · backend.md。standards/ 终态 3 文件 411 行(764→411)。
- **三时点接线**:blueprint 规则 1(起草重点 §三)· dev 读取契约 · review 手段菜单 tech-rules 对照行 + reviewer prompt 评审对照基线;**运行时 brief 三处全接**(dev 读取契约 · blueprint「起草对照 · 起草读的就是 review 会查的」· review「评审对照基线」—— stage 文档有 ≠ brief 有,动作点载体单独核);SKILL 目录表 · templates(tech/tc/prd/README/ui/dev-rules)· roles/architect · 工具注释全量改指;全库悬空引用清零(机器锁)。
- 压缩措辞按原文回补(降级前/后方案 · 限流/熔断/降级信号 · APM/sidecar · 先 ERROR 再 WARN · MTTR why)—— 合并零实质丢失(v8308 逐条款锁复核)。

### 测试
`test_tech_rules_merge_v8331.py` 15 条(三句契约逐句 / 五节 / 评审门吸收 / 退役 / **全库零悬空引用** / 归位三处 / 三时点接线 / brief / 零版本标);6 个历史锁文件(v8285/86/03/07/08/10)按新载体重锁,实质条款逐条复核。全库全绿。
