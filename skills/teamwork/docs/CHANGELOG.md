# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.332 · 主对话 = Orchestrator:dev/test 默认姿态(用户拍板)

> 用户:dev stage 和 test stage 加上不建议在主对话(主循环)进行开发和测试 —— 主对话优先用做 Orchestrator:任务拆解、阶段规划、子代理调度、集成接线、提交/推送、验证门禁、小型精准修改等。
> 设计要点:**位置(谁持有 context)与档位(用什么模型)正交** —— 验证档白名单早已把测试执行推出主对话,但档位表执行档行还写着「主对话继承会话模型即是」,等于默认背书主对话写码;本版把位置姿态独立立规。

### 变更
- **dev-stage 1.7(🎛️)**:不建议主对话直接成块开发 —— 拍板职责清单逐项入规(任务拆解 / 阶段规划 / 子代理调度 / 集成接线 / 提交推送 / 验证门禁 / **小型精准修改**);成块实现派 subagent(worktree 内路径 · **执行档继承会话模型不降档** · Meta 申报);出口显式:小 / 耦合 / 强串行 → 主对话直接做(派发协调开销反拖慢)。why:主对话 context 是最稀缺资源(跨 stage 编排状态 / 用户拍板记忆 / 集成全景全活在这里)· Orchestrator 姿态让并行成为默认而非事后补问。
- **test-stage 1.7**:不建议主对话直接编写与执行测试(执行本就是验证档白名单硬约束 · 编写同白名单默认派);主对话留 环境预检调度 / **差分基线裁决** / 门禁命令 / 失败分诊 —— 测试日志是最大的 context 污染源之一。
- **档位表执行档行调和**(agents/README):模型继承会话档不降 + **位置默认 subagent**(单源指 dev-stage 1.7)——「主对话继承会话模型即是」旧背书措辞退役。
- **brief 三处动作点同步**(dev · test Feature 流 · test Bug 流)。建议姿态 · 不设机器门。

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

## v8.330 · 开发规范收形:方法论不设限 · 兜底白名单 + 收口自查表(用户拍板)

> 用户:进一步降低对模型的限制 —— 告诉他需要开发,不需要强制 TDD 等;有一个兜底的规范和自查项列表即可(例:异常分支必须打 log、DB 字段改动需充分论证);需要读各项目自己的开发和架构规范 + teamwork 兜底规范。
> 盘点结论:TDD 强制早已撤除(「怎么测由 AI 自觉」)、HARD-RULES 已是唯一必读兜底白名单(收录判据 = 与模型默认的距离)、分册按需查、项目规范优先已立 —— 缺的只有三块,本版补齐。

### 变更
- **HARD-RULES §三 收口自查表**(新增 · 槽位式 checkbox · 判断题不设机器门):异常/降级分支都有日志 · **DB 字段/表结构改动已充分论证**(TECH 论证 + blueprint R5 + ship 迁移门)· 测试真断言/输入真实链路/TC 有实现 · 生命周期定层 · scratch 与调试日志 · 交付卫生(build + 无 TODO/占位符)· 契约面改动核消费方。表头即声明:这是兜底不是方法论 —— 怎么开发全由 AI 自定。
- **dev-stage 规则 1 读取契约升级**:项目侧必读 `DEV-RULES.md` + **`ARCHITECTURE.md`(架构规范 · 升必读)** + `KNOWLEDGE §复发防御`(涉 UI 加 UI-RULES);teamwork 兜底 = HARD-RULES;并集 · 冲突以项目为准。
- **dev-stage 规则 1.5「方法论不设限」总纲**:框架只收三样 —— 读取契约 + 兜底白名单与收口自查表 + 结果证据门;其余(TDD/test-after/骨架先行/重构节奏/拆分方式)全由 AI 自定(手段规定是对强模型的注意力税)。
- **完工自查双源**:TECH §完工自查(设计对照)+ HARD-RULES §收口自查表(兜底)—— 防「设计了没实现」与「实现了但兜底裸奔」;dev brief 动作点同步总纲与双源。
- v8286 行数锁 70→85(自查表 = 用户拍板的短清单载体 · 与「防膨胀」初衷同向)。

### 测试
`test_dev_baseline_charter_v8330.py` 11 条:自查表槽位 ≥6 项 / 用户点名两例在表 / 不设机器门 / 白名单本体未动 / ARCHITECTURE 必读 / 总纲三样点名 / 双源 / brief 载体 / 无新 evidence 门。全库全绿。

## v8.329 · 装配后移:prepare 只对齐意图 · 链装配在 goal 调研后按实测复杂度定

> 起因 case(supersdk):删 3 个按钮被定价成九段全链,用户问「这个小需求为什么还走 feature」→ 诊断:复杂度判断不准确 —— prepare 手里只有需求文本没有代码现状,在**信息最少的时刻做信息最密的决策**是结构性错判。
> 用户拍板四连:①prepare 只对齐意图不做装配,装配移到 goal 深入调研后按实际复杂度给出;②feature 执行流程不变,装配 = 环节 + 评审面两维度;③写 PRD 时提示装配链,默认执行不阻塞,提示可调;④goal 自身评审面调研后 AI 自定,其余随 PRD 确认提示、不要求改就默认。

### 变更(决策时点搬迁 · 机器层零新参数)
- **prepare 收缩为四件**:意图对齐(理解卡)· flow 大类(Feature/Bug)· preset=micro 白名单速通(类型判断非装配 · 保留最快车道)· clarity + 4 项机械配置。Q1-Q4 装配思考整体迁出;暂停点「⚙️ 配置」从「评审:已据 Q1-Q4 设」改为「装配:goal 调研后定 · PRD 确认时展示(默认执行 · 可调)」。
- **goal-stage 规则 3.7「🔗 链装配」(单源)**:调研后按四轴实测定价 —— 改动方向(加/改/删)× 契约面 × 影响面(grep 实测)× 验证成本,**装配证据必填**(与 Bug 排查先行同律)。**两拍生效**:goal 自身评审面 AI 自定(change-review-roles 留痕不问用户);下游装配(环节双旋钮 --needs-ui/--needs-browser-e2e + 各 stage 评审面)写进 PRD 终确认导读「🔗 链装配」节 —— 默认按此执行 · 不单独停等。Q1-Q4 判断表迁入并升级为证据版。
- **机器层对齐而非改造**:needs-ui / needs-browser-e2e 本就是 goal-complete 参数、roster 本就随时可调 —— 机器作者的形状一直是「装配点在 goal 出口」,是 prepare spec 在提前抢答;本版让 spec 对齐机器。prepare-check emit 的 4 问 hint 改为后移指针;goal brief 带装配提醒(动作点载体)。
- 诚实边界(已向用户交代):环节可装配面 = ui_design/browser_e2e 两旋钮,文档重量(PRD 20 行门 / TC 结构 / TECH)不随装配塌缩(用户拍板不做第三维)—— 删按钮类从九段降到约六段、评审面可收零。

### 测试
`test_assembly_at_goal_v8329.py` 15 条(prepare 四件与 Q1-Q4 清除 / goal 四轴+两拍+判断表迁入 / 导读装配节 / brief·emit·FLOWS 载体 / 机器不变式);test_state v8.27 旧锁按新不变式更新(「不抄默认」义务随装配迁 goal)。全库全绿。

## v8.328 · finding 准入:功能优先 · 复杂度守恒(用户拍板)

> 用户:review 的时候注意,优先功能实现,不要做过多的兜底、测试门之类的;不要为了不重要的 bug 增加整体复杂度;真功能缺陷要报;PRD 和 TECH review 等都需要考虑。

### 变更(四载体 · 单源 + 指针 + prompt 自含)
- **review-stage 规则 2.5(单源全文)**:①真功能缺陷必报零门槛(行为错/AC 不满足/契约破坏/数据损坏/安全);②兜底/防御/加固类建议高门槛 —— 必须给**真实触发路径 + 后果等级**,给不出不成 finding(至多 NIT);③**修复代价 > 缺陷危害 → REJECT 是合法且推荐裁决**(rejected 实证写「危害不及修复复杂度」即成立);④不借 review 加流程/测试门(测试门归生命周期 `ci_reason` · 流程门归用户拍板;confirmed bug 回归锁不在此列);⑤**简化方向不设门槛**(高门槛只拦「往上加」)。why:评审的静默失败模式不是漏报,是低价值加固吃掉轮次预算、把简单实现推肥(实证 26-28% 协调开销 · 钟摆判例)。
- **goal-stage 6.5 / blueprint-stage 9.5**:冷审各一行指针(PRD 评「要做的东西对不对」/ TECH 不推防御式设计与预防性抽象)· 真缺陷必报语义随行。
- **claude-agents/reviewer.md prompt 主体**:自含压缩版(subagent 只读 prompt —— 动作点载体);显式声明 Checklist 的错误处理/边界方向按准入过滤,「理论上可能」不是触发路径。

### 测试
`test_review_functionality_first_v8328.py` 13 条:单源五要素 / REJECT 合法性 / ci_reason 指向 / 回归锁例外 / 简化方向豁免 / 既有 severity·钟摆纪律不动 / 两指针 / prompt 段位置在正文内 + 过滤声明。全库全绿。
