# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.338 · 方向类停等第 2 项恒为「继续讨论」(用户拍板)

> 用户:PRD 和 Feature Planning 给出 1/2/3 选项时,第 2 项永远都是继续讨论 —— 目的是方便 AI 和用户讨论清楚目标和方向。

### 变更
- **SKILL R5(b) 新增恒定规则**(⏸️ 标记 · 红密度门撞线后按判例自降红):方向类停等(PRD 终确认 + Feature Planning 全部 R5)第 2 项恒为「继续讨论」—— 修订/落地是讨论收敛后的事,不逼用户在「确认」与「给修改点」之间二选一。
- **四处载体落位**:goal 终确认(2=按反馈修订重审 → 2=继续讨论〔目标与方向 · 想法/疑虑直接说〕)· planning 全景确认(2=要改全景 → 2=继续讨论,收敛后再改再确认)· planning 拆解讨论(措辞统一「继续讨论」+ 方向疑虑入口)· planning 收尾(2=继续讨论插位 · 原选项顺延 1/3/4/5/6 ·「一步到位」与自动合并硬门同步改号 1/3)。

### 测试
`test_option2_discuss_v8338.py` 5 条:R5(b) 恒定规则 / 四载体逐处(含收尾重排与硬门改号)。全库全绿。

## v8.337 · 链装配卡固定三槽:评审力度不许再丢(用户纠偏)

> case(supersdk 实证):PRD 终确认导读的「链装配」实际输出 =「进 UI 设计、也进浏览器验收 / 不改数据库 / 动到的面…」—— 只剩环节与影响面,**评审力度整维丢失**(是否需要评审、几路、谁审、为什么,一个字没有),流程阶段也没按链展示。用户预期:根据复杂度配置**流程阶段(有哪些)+ 评审力度(是否需要 · 需要几个评审)**。
> 根因 = v8.302 老病:导读要求是形容词式(「环节取舍 + 下游评审面」)—— 形容词糊得过,槽位糊不过。
> 用户同步锚定目的:**尽量降低流程税** —— 槽位不是加税:评审减没减、减到几路,必须让用户一眼可核(减税要减在明处);整卡 ≤6 行、每槽一行、理由一句,防槽位自己变新税。

### 变更
- **goal-stage 3.7 ② 固定三槽(缺槽即漏 · 整卡 ≤6 行)**:①**流程阶段** —— 完整链逐段展示、可选段标 进/跳 + 一句理由;②**评审力度** —— 逐评审 stage 一行「**是否需要 × 几路 × 谁 × 理由**」,**收到零也显式写 `0 路 + 理由`**;③**四轴证据**各半句。默认执行/不阻塞语义不变。
- PRD 终确认导读「🔗 链装配」项与 goal brief 同步指槽位。

### 测试
`test_assembly_card_slots_v8337.py` 8 条:全链形态 / 四问逐项 / 零路显式 / 证据槽 / 减税可见 + ≤6 行防新税 / 导读指槽 / brief 载体。全库全绿。

## v8.336 · panorama_sync stage 退役:全景变更判级并入 ui_design 出口(用户拍板)

> 用户:design 流程是基于现有项目全景改造么?如果是,应该去掉全景同步的流程,没有必要了。
> 前提验证成立且比预期更实:①ui_design 新模式 = 全景唯一权威 · Designer **直接改全景**(panorama-sync 自己承认「不重复同步」);②机器自相矛盾实锤 —— 附录维度 4 要求 ui_design 期改 sitemap,退役前的 mtime 门(> 本 stage started_at)逼人**二次 touch**;③同文件双载体互撞(旧规则 5「不直接改 sitemap 归 panorama_sync」vs 附录维度 4「modify-in-place」);④消费数据 11 次全是 L1 分钟级过场 · 零 L2 真协调。

### 变更
- **stage 退役**:`PANORAMA_SYNC_SPEC` / 转移分支 / `--panorama-changed` 参数与 evidence / stage 文件 / SKILL·FLOWS·STAGES 各表行全清;`ui_design → blueprint` 恒定转移。canonical 链 12 → **11 stage**(README 双语数字同步 —— spec_claims 数字门当场抓到三处,又一实证「数字宣称必漂」)。存量兼容:状态枚举保留 `panorama_sync`(历史 completed_stages 合法);in-flight 停在该 stage 的用 `jump-to-stage` 出(WARN 留痕)。
- **真价值并入 ui_design 出口(规则 8 重写)**:改动涉全景 → 判级 —— **L1**(节点内增量 · 三判据全过:无节点增删移/无 token 变更/受影响 Features 零命中)→ `add-concern WARN` 留痕直进;**L2**(任一不满足或拿不准)→ 判级结论 + 受影响 Features **并入既有的用户确认设计稿暂停点**(零新增停等 · 与 blueprint DB 变更 R5 同形态 · auto_mode 跳过 WARN 留痕);判级依据写 **UI.md §全景变更判级**(替代 panorama-change-summary.md 独立产物)。
- **双载体互撞消解**:规则 5 改为「sitemap / overview 随设计一并改」(与附录维度 4 同轴);dev-stage 两处改口(回 ui_design 走出口判级);verify-panorama 注释同步。

### 测试
`test_panorama_retire_v8336.py` 10 条:注册表/磁盘/转移/flag 持久化四路退役 · 存量枚举兼容 · L1 三判据 · L2 搭既有停等 · UI.md 节替代 · sitemap 互撞消解 · 活引用锁(符号/注册键/链边/表行 —— 迁移史标注合法)· 数字宣称清零;既有 4 个锁文件(state/engine_fixes/v8284/spec_claims 触发面)按新设计更新。全库全绿。

## v8.335 · teamwork-space 入口注入 CLAUDE.md / AGENTS.md(用户拍板)

> 用户:初始化时把 teamwork-space.md 引入到 AGENTS.md 和 CLAUDE.md —— 目标是**不用 teamwork agent 也能充分了解项目**。
> 与 v8.211「注入退役」的边界(不构成推翻):当年退役的是**流程指令注入**(共享仓库里非 teamwork 用户被迫吃 PMO/worktree 规则 · 实证 case);本块**受众相反**(正是为非 teamwork 用户服务)· **内容零流程指令**(只有知识地图指针)。

### 变更
- **`bootstrap.maintain_space_pointer`**(随 session bootstrap · space 骨架之后):把 managed 块注入 `CLAUDE.md` + `AGENTS.md` ——「📍 项目知识地图:先读 teamwork-space.md(知识入口 · 无论是否使用 teamwork 流程,了解本项目从它开始;代码是细节唯一真相)」。
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
