# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.246 · 自动流转防歇脚:complete emit 机械附带「非暂停点 · 立即继续」提醒

> 来源 case:test→browser_e2e **自动流转**后 · AI 汇报完状态即结束回合(把回合边界当暂停点)· 用户被迫问「为什么暂停了」· AI 自己复盘用词与 SKILL R4 原文一致(「回合边界不构成暂停理由」)—— 规则早在 · 流转时刻无提醒 = 读过 ≠ 在场(与 v8.238 档位提醒同构的消费时点问题)。

### 改动
- **engine `AUTO_TRANSITION_CONTINUE_REMINDER`**:每次 auto-transition 的 stage-complete emit 附 `continue_reminder` 字段——「自动流转 · 非暂停点:本回合**立即继续执行 <next> stage**(汇报/总结完不停 · 回合边界/容量预算/让用户看进度都不是暂停理由 · R4)· 合法停点仅授权暂停点清单 · auto/yolo 同理」;fix-retry 未流转(transitioned_to=None)不附。
- SKILL R4「不膨胀」条款补实证与机器提醒说明。

### 验证
- 测试 +1(流转 emit 含 continue_reminder · 含下一 stage 名/非暂停点/回合边界关键词)· pytest **861 passed**。

## v8.245 · 排查升级暂停点:多候选逐一编号 + 斜杠并列即自由文本(治 ok 无从解析)

> 来源 case(问题排查 · codex 宿主):排查报告漂亮,收尾却 emit `⏸️ 请确认后续动作:Bugfix 流程 / 不处理代码(先修正 staging 配置)/ Feature 流程` —— 斜杠并列自由文本 · 无编号无 💡 推荐 → 用户回 `ok`(快捷词协议 = 选推荐项)无从解析 → AI 再问一轮 · 白耗两个来回。**模板其实早就存在**(SKILL Mode A/E 升级触发节 v8 早期就有 R5 格式),病根有二:①模板只有「进 X / 暂不升级」单流程形态 · case 是三候选动作 · 塞不进就退化成斜杠清单;②问题排查不进状态机 · 无机器 emit 可挂消费时刻提醒 · 长会话后凭记忆 emit 格式丢失。

### 改动(文本载体钉死 · 三处)
- **SKILL § Mode A/E 升级触发模板升级为多候选形态**:选项 1/2 = <按结论最可能的动作 · 具体化>💡 / <候选动作 B · 具体化>(不再绑死「进 X / 暂不升级」)· 新增三条规则:🔴 多候选动作**逐一编号**(斜杠并列 = 自由文本 · ok 无从解析 → 白问一轮)· 选项**具体化自排查结论**(「先修正 staging 配置(不改代码)」而非抽象流程名)· **💡 推荐必给**(排查者最有信息量 · 不给推荐 = 判断甩回用户 + ok 快捷词失灵)。
- **R5(b) 判定红线(全局)**:补「斜杠并列候选清单『A / B / C』同属自由文本」—— 不止排查 · 任何暂停点适用。
- **prepare.md 排查先行律**:升级暂停点行改为「候选动作逐一编号(R5 1/2/3 + 💡 推荐)」并显式点名反例(候选斜杠并列写进一行 = 自由文本)。

### 验证
- pytest 860 passed(纯文档 · 无行为变更)。

## v8.244 · blueprint/review 冷审 3→2 路并行:Architect 主审 + 覆盖方向制外审(review 从严清单)

> 用户拍板:tech review 与代码 review 同 goal(v8.243)改两路并行 · 审核内容不变提效率。沿用 v8.243 分界线:**判断型视角保持独立角色 · 枚举型视角方向化并入外审** —— blueprint/review 的判断型主线是 Architect(简洁性 counter-lens / 实现↔设计一致性),QA 视角(可测试 / 测试真实性)方向化。三点增强(评审时建议 · 用户 ok):①review 从严体现在必覆盖清单比 blueprint 重一档 ②AI 自主方向给 stage 特定候选菜单 ③coverage 物化门延伸成三 stage 统一闭环。

### 改动
- **默认 roster**:`blueprint/review(Feature)+ review(Bug)` 均 → `["architect", "external"]`(legacy 敏捷行不动);Architect 主审产物契约不变(TECH-REVIEW / REVIEW-arch)· REVIEW-qa 为 roster 加回项(v8.241 roster-aware 校验已铺路 · 机器零新改)。
- **外审内容契约(分 stage 从严)**:blueprint 必覆盖 **可测试**(TC 质量/测试策略 · AC↔TC 机械绑定归 verify-ac)· **方案盲区**(依赖/影响面/迁移风险)+ AI 自主方向 ≥1(候选:数据一致性/迁移风险/性能/安全边界);review 必覆盖 **测试真实性与覆盖**(测试真跑/覆盖真行为/边界回归)· **代码质量盲区**(错误处理/日志/并发)+ AI 自主方向 ≥1(候选:并发/资源泄漏/脱敏/兼容)。每方向 finding 或「查过无发现」。
- **物化门 `cross_review_coverage`**(blueprint-complete + review-complete):roster 含 external 时 `external-cross-review/*.md` 必含 `coverage: [...]` 申报 —— 与 goal 的 `external_coverage_present` 构成三 stage 统一「申报-物化-台账观测」闭环 · hint 按 stage 给对应从严清单。
- **消费点同步**:两 brief(specs)· blueprint-stage §5(QA 独立 TC Review 改 roster 加回项)/§6(外审契约)· review-stage 硬规则 7 + Output Contract 示例 · prepare Q3(external 已默认在 → 判据改升异质/加回 qa)· role_value_criteria(qa 三 stage 并入 · architect 注明 blueprint/review 主审席位保留)· roles/qa.md(三席位 generalize + TC 起草不受 roster 影响)· SKILL yolo 段(「三视角一个不少」→「roster 内全真跑一个不少」· 防削弱语义不变)。

### 验证
- 新测试 +8(三默认 roster + legacy 不动 + coverage 门四态含 stage 特定 hint)· 旧断言 1 处更新 · pytest **860 passed**。

## v8.243 · goal 冷审 3→2 路并行:PL 对抗质疑 + 覆盖方向制外审(QA/ARCH 视角并入 + AI 自主方向)

> 用户拍板:PRD 评审从 3 个(QA/Architect/PL)改为**两路并行**——保留 PL + 外审;外审至少覆盖**可实现、可验证**等,把 QA 和架构师考虑的点并进去,同时要有 **AI 自己的评审角度**。此前「角色→覆盖方向 coverage 化」讨论在 goal 的落刀:少一路冷审的编排/整合开销 · 覆盖不减(方向制)+ 增(AI 自主方向是三角色制没有的)。动态 roster 机制不动 —— 改的是默认值 + 外审内容契约,复杂 feature 仍可 `change-review-roles` 加回独立 qa/architect。

### 改动
- **默认 roster**:`("Feature","goal") = ["pl", "external"]`(engine · 史注保留 v8.155 三角色防鼓掌与 v8.149 去 external 脉络)。
- **外审内容契约(覆盖方向制)**:🔴 必覆盖 **可实现**(技术可行 / 架构影响 / **简洁性 counter-lens**——唯一防过度设计 lens 随方向保留)· **可验证**(AC 可测试性 / 边界场景 / 空值异常分支)+ 🔴 **AI 自主方向 ≥1**(按 feature 特性自选:安全/性能/数据一致性/兼容/运维…);每方向给 finding 或「查过无发现」;external 段记 `coverage: [...]`。默认同模型 subagent 冷审 · 异质 opt-in 不变(localconfig false 时改跑 external-review 落 external-cross-review/)。
- **物化门 `external_coverage_present`**(goal-complete):roster 含 external 时 PRD-REVIEW 必含 coverage 申报(对称 pl_challenge_present · 防外审退化成一段泛谈);roster 无 external 自动放行。
- **两路并行**:⚡ 同发两个隔离 subagent · 互不喂对方产出(brief/stage 文档明示)。
- 消费点同步:goal brief(specs)· goal-stage ③ mandate 表(qa/architect 行改「默认并入外审覆盖方向 · roster 加回时独立跑」)· templates/prd.md PRD-REVIEW schema(reviewers/verdicts 示例 + coverage 字段)· roles/qa+architect 席位行 · role_value_criteria(qa/arch 判强才加回 · external goal 默认在)。
- 顺带修:roles/architect.md 还宣称「blueprint/review 评审默认主对话」——与 v8.241 blueprint 隔离冷审矛盾(审计漏网)· 统一为隔离冷审。

### 验证
- 新测试 +6(默认 roster 两条 + coverage 门四态)· 旧断言 2 处按新默认更新 · pytest **852 passed**。

## v8.242 · 变更确认类暂停点必自带变更点明细(对象|变更|用途 · 治「概括 + 指针」逼用户追问)

> 来源 case:blueprint DB schema 确认点只 emit 四条分类概括(「增加诊断投影与快照序号」「增加日志序列、过期 tombstone、mutation 幂等、Tester durable queue 辅助表」)+ TECH.md 指针 → 用户被迫追问「DB 变更方案是什么」· 追问后 AI 才给出该有的 对象|变更|用途 明细表 + 迁移策略。**病根在 §7.5 模板本身没有变更点槽位**(从「请确认」直跳选项 · 决策参考=文件指针)—— case 里 AI 忠实执行模板仍失败 · 是模板的 bug。与 v8.232 ship1 同类:暂停点内容不可消费。

### 改动(消费点三件套)
- **blueprint-stage.md §7.5 模板重写**:选项之前必给 ①**变更点明细**(🔴 对象级每条一行:对象|变更|用途 —— 表/字段/索引/约束/新表核心列;分类概括 / 文件指针**不算**变更点)② **关键迁移策略**(≤6 行:有损与否 / 唯一约束前历史冲突预检 / 历史回填口径 / down migration / 清理周期);📚 指针降为深读补充 · 不替代明细。范式即 case 追问后的第二回。
- **SKILL R5(b) 新红线(全局)**:**方案/变更确认类暂停点必自带变更点清单** —— 情境一句 + 概括 + 指针不算 · 用户被迫追问「方案是什么」= 暂停点白跑一轮 · 决策材料在暂停点内自含。
- **机器消费点**:blueprint stage-start brief 的 §7.5 行机械附带「必自带变更点明细表」提醒(v8.238 消费时刻原则)。

### 验证
- pytest 846 passed(doc + brief 文案 · 无行为变更)。
