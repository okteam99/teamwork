# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.314 · 业务交付视角拆分:治「跨子项目 → 顺手拆多个 feature」

> 用户:跨多个子项目时容易拆多个 feature;应从业务交付视角拆,允许一个 feature 跨多个子项目。

### 判定:规则早已存在(用户拍板过 · 三处)· 这次查的是顶着规则的结构性推力

「主判据 = 交付内聚 · feature 可跨子项目 · 子项目边界不是拆分理由」自拍板起就在
feature-planning Step 5.7 / workstream target 注释 / PLANNING_CHECKLIST —— 又一例
**规则存在 ≠ 规则执行**。三个推力:

| # | 推力 | 形态 |
|---|---|---|
| ① | **prepare 路由单数假设** | 「据改动代码**所在的子项目目录**定前缀」对跨子项目零指引 —— 「一个 feature 没法有两个前缀」的别扭感隐性推向拆开 |
| ② | **判据到达质量差** | 判据埋在 PLANNING_CHECKLIST 一个 500 字巨条目中段 + `target` 字段注释里 —— 一条 item 装十件事 |
| ③ | **草案载体没逼出交付视角** | 讨论稿只要求「边界理由」—— 这个槽能用技术话术糊(「partner 侧改动独立」);没有槽逼 AI 写「单独上线后谁得到什么」,而**横切件恰恰写不出这个** |

### 修(全部是结构 · 不是措辞)

- **① prepare 路由补跨子项目走法**:monorepo 内改动跨多个子项目 = **照样一个 feature** ——
  前缀/docs_root 取**业务交付宿主**(交付物主要落地 / 用户感知所在的子项目)· 其余子项目改动在
  同一 worktree 同一 feature 里做;并点名「前缀选择的别扭不构成拆分压力」(推力不点名就还在暗处起作用)。
- **③ 拆解讨论稿加「业务交付物」必答槽**(载体的形状决定内容会不会出现):每条候选 BL 必答
  「**这条单独上线后,谁得到什么**」—— 写不出可感知交付 = 横切件并回宿主;
  明文排除技术伪交付(「后端接口就绪」「partner 侧改动」不是交付物)。WS 模板每-feature 节同步加交付物行(长期载体)。
- **② checklist 判据拆独立条目**(一条一事):`planning-check` emit 的 checklist 新增第 7 条
  「拆分视角 = 业务交付,不是子项目」· 170 字 · 测试锁上限防它长回巨条目。

不做的:ws-lint 机器识别「按子项目横切」—— 合法的跨子项目独立交付对与横切件在结构上同形
(分属两子项目 + 有依赖),启发式误报率高;「交付物写不出来」这个人读信号比结构启发式准。

## v8.313 · yolo 自动验收物化 + 外部世界动作边界

> 实证(SDK-F260809171303 · 公共 JSSDK 发布):yolo 跑到 pm_acceptance,AI 停下等 1/2/3,
> 说「发布决策是 Teamwork 强制用户确认点,YOLO 也不能跳过」。用户:**yolo 应该自动合入 yolo 分支。**

### 判定:AI 没编规则 —— 它忠实执行了到达动作点的 brief

`_pm_acceptance_brief` **无条件**写着「decision 是用户决策点 · emit 三选项然后停 · AI 不可自决」,
整个函数没有 yolo 分支;而 SKILL yolo 表明写「pm_acceptance = **自动 approved_and_ship** + WARN」。
SKILL 在几百个工具调用之前、brief 在动作点 —— **动作点的载体赢了**。
🔴 **fast_mode 同族第二例**:spec 承诺的模式行为从未物化,工具在动作点反向覆盖。

### 修 ①:yolo 自动验收物化(brief 按 `state.yolo` 分支)

- yolo → brief 直接给自动路径:**AC 对照照做不跳**(自动 ≠ 免验收)→ `add-concern WARN` 留痕 →
  `pm_acceptance-complete --decision approved_and_ship` → 自动进 ship 合入 merge_target(非主分支硬门);
  AC 真有问题走 `rejected_with_feedback` 回修(**不硬过** · yolo 自主解决);release-gated 待补证据照常随行。
- 非 yolo(含 auto_mode)照旧停 —— 产品决策权是用户专属。
- 三载体收同口径:SKILL 表(自动)· brief(自动 · 新物化)· pm-acceptance-stage.md(补「唯一例外 = yolo」)。

### 修 ②:外部世界动作边界(用户拍板:合入后单独停给用户)

case 里的「发布」= **npm 公网发包 + 建公开仓**。yolo 的安全模型是**分支门**(merge_target 非 main ·
主分支人工提升),但外部动作**不经过分支** —— 「零 stop」字面执行会让幻觉级错误(泄密/白名单漏洞)
直接入公网且不可撤。**AI 停下的直觉方向对、挂点错**:该挡的是外部发布,不是验收与合入。

新边界(SKILL yolo 节 + brief + stage doc 三处同口径):公网 registry 发布 / 创建公开仓 / 生产部署等
**不经过分支门且不可逆**的动作不在「零 stop」范围 = release 域(RELEASE-GUIDE · 发布归用户)——
**先自动验收 + 合入 + 清场(不阻断),外部发布单独停给用户**;❌ 不得以「有外部发布」为由把验收/合入也停下。

### 🔴 密度门当场管了一次注意力经济

新边界初版带 2 个 🔴 → SKILL 总数 56 超 55 门 —— 按既有判例**服从门、裁自己的红**
(动作点载体 brief 里的 🔴 才是到达关键 · SKILL 处降级为 ⛔ 靠语境)。

## v8.312 · 测试生命周期三层:临时的从不入库 · 进 CI 是例外要理由

> 用户:测试写太多、有用没用都写、卡 CI · AI 处理 case 消耗太大 —— 是否按生命周期分层?
> 两次拍板:①**只写规范不配门** + L3 落 scratch ②**进 L1 一定要有充足理由**。

### 与 R-SP-1b 不是翻案,是补另一半

那轮实测证明**执行**成本在进程派生不在数量(61% 用例 <5ms);但**维护**成本按语料线性
—— AI 每次重构要同步全部测试、CI 墙钟逐 feature 累加。**执行便宜 ≠ 维护便宜。**
R-SP-1b 管「不合并断言」(失败定位是最贵的信息),本版管「留不留 / 在哪跑」,两条正交并立。

### 三层(判据按「失败信号的消费者」,不按阶段名)

**一句话判据:交付后还有谁需要它失败的信号?**

| 层 | 准入 | 归宿 | 谁跑 |
|---|---|---|---|
| **L1 CI 契约层** | 🔴 **默认不进 · 进必带 `ci_reason`**(拦住什么级别的事故;「顺手写的/覆盖率好看」不算)| TC 注册 `ci: true` | CI 每次 |
| **L2 回归层** | TC 其余(AC 绑定 / bug 回归 · 缺省层)| TC 注册 | test stage 全量 + 发版前 |
| **L3 脚手架** | TDD 中间步 / 探索 probe / 一次性验证 | 🔴 **scratch `scaffold-tests/` · 不入仓库不进 TC** | 仅本 feature dev 循环 |

- **L1 例外化与 WS 拆分同构**(默认合并 · 拆分是例外):理由由**模板字段承载**(`ci_reason` 空着即可见)
  —— 符合「不配门」裁定,靠结构不靠扫描。
- **L3 复用 scratch 机制**:与「看一眼截图不落 worktree」是同一条规则的同构应用 ——
  临时 case 不是「写了再清」,是**写的时候就不进仓库**,清退成本归零、随 ship2 回收。
- **CI 对接归项目主权**:项目 CI 按 `tests[].ci` 挑子集,框架只给注册与判据。

### 落点

tc.md 新增 § 生命周期三层(单源 · 含第二条 TC 边界「**交付后不需要再跑的,不属于 TC**」)·
HARD-RULES 规则 17(必读到达)· dev-stage ②规则 8(写测试的动作点 · 规则必须到场)·
common §六 scratch 用途补 `scaffold-tests/`。守卫测试反向锁「没有人顺手造门」。

### 顺手清一类数字宣称

「~50 行白名单」写死三处、实际已 60 行 —— 数字宣称必漂,三处全部去数(HARD-RULES 头部改为
「行数不写死」+ blueprint/dev 引用同步)。

## v8.311 · TROUBLESHOOTING 收归用户主权(AI 只读 + 提示 · 不代写)

> 用户裁定:**TROUBLESHOOTING 是用户主权文件,AI 不要在流程中修改它;AI 可以自动改 KNOWLEDGE。**

### 实况:确实存在 AI 写入路径,且归类本身就是漏的

- 两处条文明确指示 AI 写它:SKILL「连法缺失 → **补进它**(知识沉淀)」· feature-planning Step 1 同款;
- conventions §13 清单里它**没标维护方** —— 旁边 DEV-RULES/UI-RULES 都标着「人维护」,
  它和 GLOSSARY 裸着。**没归类的文件,写入权会默认漂向 AI**;
- 工具层干净:state.py / engine 只**读**它拿连法;bootstrap 只建空骨架(DEV-RULES 同款 · 骨架≠内容 · 保留)。

### 修(镜像 DEV-RULES 模式 · 五处)

- **转记流**(SKILL + feature-planning 两处原违例):连法缺失/AI 摸索出来的 →
  记 `KNOWLEDGE.md`(AI 沉淀 · 用户明确保留 AI 写权)+ **提示用户**固化进 TROUBLESHOOTING · 不代写;
- **归类补标**:conventions §13 + SKILL 文档清单行 + 模板头部 → 「人维护 · AI 不代写」;
- **KNOWLEDGE 边界表补行**:「运维操作步骤 / 环境连接方式 → TROUBLESHOOTING(人维护)」——
  这张表是「什么写哪」的单源,此前缺这行。

### 机器门

任何 spec 行「TROUBLESHOOTING + 写动词(补进/写入/追加…)」而无「提示用户/不代写」豁免 → 红。
另:新增条文撞上 SKILL 🔴 密度门(55 = 上限)—— 按既有判例**服从门、裁自己的红点**(主权语义靠加粗承载)。

## v8.310 · 文档合并(-3 文件)+ 考古注释清零 + 机器门

> 用户:看下各 md 是否需要合并 · 去掉没必要的注释。
> 合并判据:**要么减少重复,要么减少读取量 —— 两者都不减的不合**(文件数不是成本,读取行数才是)。

### 合并三件(65 → 62 个 md)

| 退役 | 为什么 | 独有内容去哪 |
|---|---|---|
| `STANDARDS.md` | 独有内容仅一句;其余是**已经漂移的分册简介**(还在描述 v8.307 已删的「组件测试/状态管理/无障碍」)+ 与各分册头部重复的加载指引 —— **索引描述是内容的副本,索引也会漂** | 「覆盖声明唯一注册处 = DEV-RULES · KNOWLEDGE 不作注册处 · 存量对外契约沿用」→ HARD-RULES.md 头部(必读文件) |
| `TEMPLATES.md` | 格式权威红线与 templates/README 头部 + common §四C **三重复写**;页脚声称 roles/{pmo,pm,rd} 有「格式权威」条目 —— **三个文件都没有**(幽灵引用) | 红线要点并入 templates/README 头部 · meta 规则 cite §四C 单源 |
| `standards/frontend.md` | v8.307 砍完教学后仅 13 行正文,**头部比正文长** —— 不值一个独立加载单元 | 整体并入 common.md **§七 前端专项**(阈值与禁令 · 标明仅前端子项目适用) |

### 评估后不合的(记录判断 · 防下轮重新讨论)

- **roles/ 9→1**:引用横跨 15 个 md · stage spec 逐点 cite 具体角色文件的具体节;合并不减重复也不减读取量,只减文件数。不合。
- **PRODUCT-OVERVIEW-INTEGRATION → feature-planning**:tools 层 3 处真实咬死路径(bootstrap flow_gates + state.py planning-check 的 must_read emit);两文件分工清楚(文档体系与状态管理 vs 流程步骤),合成 450 行巨文件反而变差。不合。
- **teamwork-space 模板 ↔ guide**:bootstrap 拷模板做项目骨架,guide 的规则内容不能进模板(会被拷进用户项目)。不合。

### 考古注释清零 + 机器门

按 v8.309 判据(「删掉这句,现行规则的说服力掉不掉?」)清掉一类**删除记账**:
「原 N 行已删 / 压缩原 X / 借鉴 mattpocock/skills」共 14 处(SKILL 命令节 · STAGES 试点转正叙事 ·
common 三处节名后缀 · ui-design 三处 · ui/config/prd/adr-index/external-model-usage 各一)——
**why 原则保留**(「模型内建常识不入库」支撑现行形状 · 防回潮),删的只是记账与署名。
新门:`原 N 行` / `压缩原` / `借鉴 mattpocock` 出现在 spec 即红 —— 门首跑就抓到人工扫描漏掉的 2 处。
