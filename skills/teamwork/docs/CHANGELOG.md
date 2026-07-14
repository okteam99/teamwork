# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.241 · 全库文档审计清扫:83 findings 修复 + 退役词表回归网 + 两处工具侧治本

> 用户令「整体 review 各文档找不合理/冲突/冗余」→ 5 路评审 subagent 按文档簇并行(SKILL/stages/docs/templates+roles/对外三件)+ 主对话词表扫描,共 **83 处经双边原文验证的 findings**。病灶高度聚簇:五次大改版(v8.204 外审默认反转 / v8.211 注入退役 / v8.219 四段化 / v8.220-223 流程收缩 / v8.233-234 ship 终点)各留扫尾债。机器契约层(FLOWS↔常量 · frontmatter↔物化校验 · 台账 schema)五路核验零冲突。

### 工具侧治本(2)
- **REVIEW-arch/REVIEW-qa roster 化**:静态必查与动态 roster(v8.216)互斥(角色可被合法移出 roster 而产物仍硬查)→ 新 `review_role_artifacts` evidence check 按 `stage_review_roles.review` 查(移出不查 · legacy 无 roster 全查不放松存量)。
- **close-unmerged 任意 stage 可走**:pm_acceptance rejected 的「放弃 Feature」选项此前是死路(emit 给的命令必被 `_require_ship_stage` 拒)→ 放宽该 action(幂等门仍由 phase 检查把守)。

### 文档修复(四大簇 + Tier1)
- **照抄即错**:规划层 auto 留痕 add-concern 不可执行(规划无状态机 · 全景确认与 v8.239 Step 5.7 同病)→ 改 WS frontmatter/背景节留痕;main-sync 示例与机器 hint 补 required `--strategy`;prepare §5 示例补 `--clarity/--preset/--bl` 落点;config_line_hint 机器残留 `lite` 清除;bug-report 模板补 `symptom/root_cause/fix_summary`(机器 gate 校验它们非空);config.md 外审开关说明与实例相反(「删此项恢复异质」在新语义下效果相反)重写。
- **v8.204 外审默认反转簇(7)**:blueprint §6 整段旧教义(无条件异质必跑)→ roster 三层条件式;blueprint Architect「主对话不走 subagent」→ 隔离冷审(对齐 goal 实证);roles/external-reviewer 补三层现实;standards/external-model-usage「默认 false + WARN 催恢复」重写;README-EN/ prepare/ ship 措辞。
- **v8.220-223 流程收缩簇(~20)**:SKILL §2.2 quick-ref 重写为 preset 词表 · 两处 F/B/M→F/B · micro「≤5 文件」两口径删阈值(FLOWS 同步);prepare §2.2 整节重写(敏捷需求准入档退役 · micro 白名单准入单源)· 编号断裂(1.4/1.5×2→1.6/1.7)· lite/M 字残留;conventions M 示例与 §8 补 legacy 标;roadmap 模板 v7 阶段名→v8 stage 名;README CN 6 行流程表→5 行闭集(与 EN 对齐)。
- **README 双语过时宣称(8)**:Ship 节还在描述 v8.145 已删的旧两-MR 链路 → 重写为 user_card+await-merge 两段现实;PENDING 外置 / TROUBLESHOOTING 收敛 project-specs / KNOWLEDGE 四类 / 执行手册废弃补 workstream/ / hooks 清理措辞 / EN sitemap→panorama 误译。
- **断链引用(~12)**:四段化后 ui-design→dev §3/§3.5、roles/pm→goal §4/§1;重编号后 conventions→ship-stage §坑1/§8、→feature-planning Step 5、feature-planning 自引 Step 5、checklist spec Step 8→9;三报告模板→roles 不存在小节;SKILL 自指不存在的 silent execution 节。
- **冗余与小项**:agents/README **保留**(§二/§三 dispatch 协议是 subagent 独立载体 · codex-agents toml 运行时指读)但 §一 姿态/声明制散文去重(指回 SKILL 单源 · 档位表+三硬边界仍单源本文件);SKILL 快速开始 ship 旧剧本→await-merge · auto 表删 browser_e2e 幽灵行 + 补 diagnose 行(skip+WARN)· 暂停点清单补 panorama_sync L2 · ≈40 命令→≈55 + B 类补 await-merge · 物化覆盖率两口径统一 · 状态行 2/3 行统一;pm-acceptance raw-write→jump-to-stage;tc.md TC-REVIEW 死段删;bug-report classification 零消费机制删;9 模板补「位置:」行;project-specs 清单三文档归一 conventions §13。

### 制度化(治「每次大改各留扫尾债」)
- **退役词表回归网**:新 `test_retired_vocab_sweep.py` —— 退役词(敏捷需求/Micro/blueprint_lite/teamwork_version/Goal-Plan)只许出现在带 legacy 标注的当句 · 裸残留 = pre-push 红。

### 验证
- 新测试 +7(roster 化 4 + close-unmerged 2 + 词表网 1)· pytest **846 passed**。

## v8.240 · 拆解边界判据:交付内聚>子项目边界 + 含金量对照 + id 不重排纪律

> 来源 case(JCB 卡片 WS · v8.239 门生效前的存量拆解):7 件逐 feature 代码审计发现 4 件薄(S2/S3/S6 薄配套 · S7 半运营 · 「其余四件加起来的代码量可能不如 S5 一件」),但 v8.239 粒度反压零触发(7<8 · 每件流程上都「站得住」);用户亲自解禁「feature 也可以跨子项目」才合成 5;且落盘后合并触发**第三次编号重排 = 整卷重写防漏引用**。三个判据缺口,不加新暂停点。

### 改动(Step 5.7 判据升级 + 模板 + checklist 同步)
- **边界判据**:主判据 = **交付内聚**,**feature 可跨子项目**(`target` 只是 ROADMAP 归属 · 「代码在不同子项目」不是拆分理由,评审 blast radius 才是);**薄承接件默认并入宿主件**(只承接另一件产物/同 surface 严格串行/协调点可内化为里程碑),保持独立须给硬理由之一:外部依赖 gate / 交付节奏不同 / blast radius / 管辖边界(四类全部萃取自该 case 的真实裁决:S1+S2 并 · S6 gate 独 · S7 节奏独 · S3 blast radius 独)。
- **含金量对照**:讨论稿每条 BL 标「真新增工程量 vs 薄配套(承接/枚举/配置级)」——**含金量悬殊 = 强合并信号**(反压 BL>8 抓不住 7 件 4 薄这类)。
- **id 纪律**:草案期编号随便改;**落盘后合并/砍件不重排幸存 id**——被并件留一行遗迹(`S2 → 已并入 S1`)· 缺号不补。
- 模板顺手修:`flow_type` 注释还是 v8.222 合并前旧词表(feature/agile/bug/micro)→ 现闭集(Feature/Bug · micro 是 preset)。

### 验证
- 文档+模板+checklist 消费点三处同步 · ws-lint 不消费 target/flow_type 注释(纯文案安全)· pytest 839 passed。
