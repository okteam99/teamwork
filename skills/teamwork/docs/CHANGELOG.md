# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.308 · 第二梯队:双写合并(-310 行)· 抓到一处「双副本已漂移」的现行犯

> 承 v8.307(第一梯队整段砍教学)。两批刻意分开:「删教学」与「改语义的合并」
> 混在一个 diff 里,review 时分不开哪些是删、哪些在改。
> 本批全是 ⑧重复 的收口,**判据:合并双写必须零语义丢失**(每段的实质条款逐条有测试锁)。

### 合并与压缩

| 位置 | 双写形态 | 处置 |
|---|---|---|
| `backend.md` §四 | **WARN 规则同文件写两遍**(非预期分支树里一遍 + 独立硬规则块一遍:触发/级别/字段/CR 门全同) | 合一段 · 触发面/字段清单/CR 门/两条 why 逐条保留(测试锁 15 个实质条款) |
| `backend.md` §五 | 「迁移与开发流程的衔接」流程图 = 状态机 stage 链复述;迁移基本卫生(up/down 可逆/已执行不可改)= 模型默认 | 图删(术语对照表留 —— 唯一映射信息);卫生删 · **项目守卫查询与跨子项目 Schema 链(真门)全留** |
| `templates/prd.md` | 通用 checklist 复述模板正文已有的段(Out of Scope 等);三文档分工讲到第三遍 | checkbox 仪式删 · **只留结构没问到的三件义务**(KNOWLEDGE/ADR 关联 · 跨子项目依赖 · 业务风险);第三遍复述删(第二处「PRD 不写什么」有裁决功能 · 留) |
| `feature-planning.md` §3 | 坑 1/3/5 = 正文 §1/Step 7/Step 9 的复述 | 删三留三(业务vs技术架构 · 三者分工 · planning-start BLOCKED)· 顺手修 Step 5 悬空的「坑 4」编号引用 |
| `ui-design-stage.md` | 全景模型节尾「🔴 硬规则」块与 ② 硬规则 1-2 几乎逐字双写 | 删块留 ②(单源)· 块里唯一非重复的向后兼容条款(缺 `panorama_medium` 视作 static-html)保留 |
| `common.md` §三 | 逐脚本职责树(7 个脚本 × 3-4 行叙述) | 压缩 · **名称清单 + 接口契约(退出码/幂等/无交互/JSON 尾行/--skip-if-running)一个不丢**(测试锁) |
| `prepare.md` §7.3 | git worktree add 排障三修法 | 模型自带知识 · 压成一行 |

### 🔴 现行犯:Designer 自查报告模板两份 · 已经漂了一维

`common.md` 四B 存的报告模板是 **5 维**,`templates/ui.md`(UI.md 章节的宣称单源)里那份是
**6 维**(多「框架基线唯一性」· PTR-F032 经四C 注册加的)—— **双副本必漂,这次抓的是漂移现场**。
顺藤摸出三个死锚点:四C 表指向 `designer.md § 6 维自查` 与 `ui-design-stage § 框架基线唯一性`
(两个节都不存在)、`pmo.md § 格式权威守门`(同)。

修:报告模板**只留 ui.md 一份**(common 四B 改指针 · verify-panorama 的 §四B 锚点保活)·
四B 维度数同步为 6 并**补第 6 维的清单定义**(此前它只在 ui.md 表里孤零一行)· 三个死锚点改指实处。

⚠️ **一并揭开的缺口(标注不修 · 留观测)**:`verify-panorama.py` 硬校验的只有维度 1-5 ——
第 6 维是模板承载、门禁未收。**不在本版收紧**:存量 in-flight Feature 的报告是 5 维格式,
硬拦会造出「注定失败的门」(v8.301 判据)。工具注释已写明缺口与收紧时机(看维度 6 缺失率)。

### 围栏门收紧

common.md 压缩后配平 → KNOWN_ODD 豁免名单从 6 缩到 3(bug-report / project / roadmap)。

## v8.307 · 指导类第二轮减法(-525 行)+ 三处断链修复

> 用户:先问「不考虑文档和审计,teamwork 相对默认工作流优势在哪」——
> 答案收敛为四个不衰减机制(零信任门禁 / 用户主权 / 独立采样 / 状态跨 context 存活);
> 随后:「指导类(怎么写测试 / 怎么规划)还有哪些需要砍的」→ 全库 65 个 md 逐个过一遍。

### 砍什么:v8.285 那轮漏网的同类

判据不变(**与模型默认行为的距离**),这轮的实锤是**三处「裁定只执行了一半」**:

| 文件 | 砍掉 | 自相矛盾的证据 |
|---|---|---|
| `frontend.md` 90→18 | 组件测试写法 / 状态管理选型 / 性能手法 / WCAG 细则 / 构建实践 / 自我总结表 | 头部自 v8.123 就写着「**选型教程不入库**」,正文却全是选型教程;且 ui-design-stage v8.284 已按「模型内建常识」删过同类 —— **同一判例只执行了一个文件** |
| `backend.md` 563→329 | §四两大段 JS 教学示例(78 行)· §二检查项树与 Docker 实现指南 · §六 breaking 枚举与 deprecation 三步 | 示例只是「必须字段」清单的实例化;**规则本体一行未动**(外部调用必 ERROR / 降级必 WARN / 必须字段 / CR 门 —— 逆默认最高价值格,有测试锁) |
| `templates/tc.md` 266→210 | 填好值的 TC-002/003 场景 | 模型写 Gherkin 不需要两个填好的例子;**骨架与两张验证表(载体)保留**,并补了「断言到的状态码/code 必须写具体值」红线进骨架 |
| `PRODUCT-OVERVIEW-INTEGRATION.md` 305→206 | 自下而上的信号枚举树 / 升级流程树(94→15 行)· 章节裁剪教程 | 识别「范围溢出」= 模型自判;**用户主权协议 4 条全留**(只标记不改上游 / 每级必经确认 / 挂起待上游 / 不升级也留痕) |
| `scripts-policy.md` 276→212 | R-SP-8 的「渐进切换三阶段(第二/三阶段:待定)」与过期扫描快照 · R-SP-3 退役规则的 bash 教学示例 | 违反 conventions「spec = **现行真相手册**」—— 迁移计划与数据快照不是现行规则 |

### 断链修复(review 中撞见 · v8.293 类)

- 🔴 **backend/frontend「模块设计判定」整节退役**:它引用 `templates/knowledge.md` 的两个节作单源,
  而**那两节 v8.96 就删了** —— ~200 版无人发现 = 零消费者;抗过度设计的活规则本就在
  `HARD-RULES.md` 规则 5(「两个 adapter 才抽象」),退役副本不丢规则(测试锁三方状态)。
- 🔴 **scripts-policy 三处死引用**:`tools/post-feature.py` 不存在(连 R-SP-2 的示例命令本身都是它);
  §4 迁移表说 4 个 hook「保留」而同文件 R-SP-1 明写 hooks 已全退役、目录已删。
  修:示例换真实存在的 `verify-ac.py` + **立零信任门**(本文件 cite 的每个脚本路径必须真实存在)。
- 🔴 **v8.304 自己的悬账**:codex agent toml 已从「部署」改「回收」,但 `agents/README` 与
  `SKILL.md` 两处仍写「bootstrap 部署」—— 正是 v8.300 立过判例的「改规则只写新的、没撤旧的」,
  这次是自己上一版种的。
- **backend.md §二断栏修复**:v8.284 压缩时把说明插进旧示例围栏内、删了闭合线 → §三整段在渲染器里
  显示为代码块;fence 计数是偶数所以 v8.293 围栏门抓不到「配错对」。修后 backend/frontend
  **移出 KNOWN_ODD 豁免收紧门**。

### 明确不砍的(判断边界)

stages/ 十二件(四段结构后全是判据形态)· agents/README 档位与派发(逆默认+实证)·
日志 ERROR/WARN 规则与必须字段 · FK 策略(逆教科书默认标杆)· migration 起号纪律 ·
复发防御清单 / PRD 起草思考规范 · scratch 约定。

留给用户的裁定(未动):conventions「spec 不写版本标/case 叙事」与 R-SP-8「实证 case 是合法
消费者标注」互相冲突 —— 哪条为主需要拍板,本版不单方面扫。

## v8.306 · 测试证据的两个维度:谁跑的(申报)+ 对应哪份代码(零信任)

> 实证(aon-core):AI **在主窗口直接跑了测试**,用户问「为什么没切验证档」它才发现。
> 自陈:「沿用了『主编排收口测试』的做法,**漏掉了 v8.299 的硬规则**」——
> 🔴 **规则它读过**(自己引用了版本号),漏的是**时点**:提醒在 stage-start,动作在几十个工具调用之后。
> 与 v8.299 派发声明、v8.301 命令时点是**同一个失效机理**。

### 提案按「可验证性」分三级裁决,不整包收下

| 提案 | 裁决 | 理由 |
|---|---|---|
| **tree-hash 绑定** | 🟢 收 | complete 时**自己重算**,不读任何申报字段 = **零信任**;挡的是今天完全没挡的洞:**先绿、后改、仍拿旧日志过门** |
| **runner/tier/model 申报** | 🟡 收(标清边界) | AI 自己写 → **拦得住「忘了」,拦不住「故意」**;而这次恰恰是忘了,故有效 |
| **`agent_task_id` 作硬门** | 🔴 不做 | **跨宿主不可得**(Codex 与 Claude Code 的 subagent 标识不同)· 会变成某些宿主上**注定失败的门**(v8.301 判据) |

🔴 提案原文称「这一个门禁就能直接防住我刚才的错误」—— **过誉**。
不标清「自我申报」这条边界,读者会高估这道门、进而放松其他把关。条文里已写明。

### 三处改动

- **`test_evidence_fresh`**(dev complete 硬门):指纹 = `HEAD tree` + **未提交 diff** 的 sha256。
  只绑 HEAD 不够 —— 「改了但没提交」同样让旧日志失效。
  三种降级放行:非 git / 算不出指纹 / 未传参数(存量 in-flight 兼容)——
  🔴 **绝不因环境问题 BLOCK**(注定失败的门比没有门更糟)。
- **`test_runner_declared`**(dev complete 硬门):`subagent | main-window | ci`,**不传 = BLOCK**。
  `main-window` 是**允许的值**,但走 v8.299 例外协议:需 `--user-confirmed`,否则 BLOCK ——
  **失误变得可见,而不是被静默吞掉**;拿到授权也留 WARN(年检要数得出这类例外的频次)。
- **`verification_recipe`**(dev/test 的 stage-start emit):派发声明 + **采指纹的可跑命令** + complete 三参数,
  一次给全。规则读过仍然漏 → 配方必须在**动作点之前**就是完整的,不能让 AI 现拼。

### 九种情形实测

指纹一致 pass · 测完改代码 BLOCK · 未传兼容 pass · 非 git 降级 pass ·
subagent(带/不带 model)pass · main-window 无授权 BLOCK / 有授权 pass+WARN · 未申报 BLOCK。

## v8.305 · 🐞 fast_mode 的 blueprint 被门禁强制跑 external(四个面的同一族 bug)

> 用户:**看下 fast 模式是否有 bug。**
> 实证(aon-core · `fast_mode=true`):`blueprint-complete` FAIL 要 external,
> 而**同一 stage 的 brief 明写「blueprint 评审跳过」** —— brief 与门禁直接对立。

### 后果:AI 做对了每一步,却仍然白付一轮

AI 没有篡改 state、没有 bypass(**两个判断都对**),先试 `change-review-roles` 想显式清空 ——
**被拒**;于是它按配方**真跑了一轮隔离冷审**。
🔴 **fast_mode 承诺的「blueprint 评审跳过」被静默取消,用户白付一轮。**
框架没给它任何一条正确的出路。

### 四个面

| # | 面 | 事实 |
|---|---|---|
| ① | **两个 evidence check 语义相反** | `external_review_artifact` 的 `if stage_roles and "external" not in stage_roles` 把「**有意配空**」当「**未配置 → 按默认要 external**」;而同文件 `reviewers_match` 对同一状态判 `if not required: return True`(skip) |
| ② | **靠键缺失表达意图** | v8.261 的 fast 只写 `{"goal":[…], "review":[…]}` —— blueprint **键缺失**。而缺失读不出「有意」还是「忘了」 |
| ③ | **用户无法自救** | `change-review-roles` 要求 stage **已在** dict 里,而 fast 恰恰把它去掉了 → 想显式设空都被拒 |
| ④ | **框架自产自拒** | `fast` 是 fast_mode 自己写进 roster 的**伪角色**,却**不在 `REVIEW_ROLE_ENUM`** → fast 模式下连把当前值传回去都判非法角色 = **该模式下这条命令整个不可用** |

### 修

- ① 守卫对齐「**空 roster = 本 stage 不要求评审**」(两处:external artifact + 验证轮日志);
- ② fast_mode **显式写 `blueprint: []`** —— 意图物化,不靠缺失暗示;
- ③ `change-review-roles` 改为只校验「stage 有无评审语义」(单源 `STAGES_WITH_REVIEW_ROLES_HINT`),
  **允许对未配置的 stage 设置**,且**允许显式清空**(`--roles ''`)——
  🔴 清空一个本就不存在的键**算 OK 不算 NOOP**(要把意图写进 state 与 audit);
- ④ `fast` 收进 `REVIEW_ROLE_ENUM`。

### 🔴 修 ① 时首版过宽,被既有测试当场抓出

首版把「roster **整个**缺失」也判 skip —— 那会让 **legacy state 静默跳过外审**。
两种「缺失」含义相反,必须分开:
**非空 roster 缺本 stage = 有意去掉(skip)· roster 整个空 = 未初始化(仍按默认要求)。**

> 这次是**测试拦住了我**,不是我自己想到的。它也印证了 v8.303 那条:
> 我据「fast_mode 场景」推出了守卫该怎么改,**但没验证「roster 整个缺失」这个我没亲眼看过的分支**。

### 顺带:放宽守卫要跟着改下游

放开「stage 必须已存在」后,`before = review_roles[args.stage][:]` 立刻 KeyError ——
**放宽一处约束时,依赖该约束的下游全部要复核**。

### 测试

1092 → **1104**。

---

## v8.304 · 回收零工具 reviewer profile + 区分「执行失败」与「评审失败」

> 用户提案:隔离 Reviewer 无文件读取能力 · 冷审返 `files_read: []` + `no authorized read-only file access`,
> goal 流程被阻断。**宿主 = codex。**

### 根因链(逐环读文件核实)

| 环 | 事实 |
|---|---|
| ① | 被删的 `codex-agents/prd-reviewer.toml` **故意零工具** ——「READ-ONLY · Cannot write files via shell · Cannot execute commands」。因为**旧架构把待评审文件 inline 进 prompt**,reviewer 不需要自己读。**零工具是设计,不是缺陷。** |
| ② | 现配方**只 inline 一部分**:`goal→[PRD]` · `blueprint→[TC,TECH]` · **`review→[]`**;**上游 WS 与真实代码从不 inline**。v8.291 改 subagent 冷审 + v8.303 立「读真实代码」硬要求 → 零工具 profile **架构性不兼容**,不是配置没调好。 |
| ③ 🔴 | **v8.293 删了 skill 侧的源,却没写回收逻辑** —— bootstrap 只有 hook 的清理,没有 `.codex/agents/*.toml` 的。已部署副本留在用户项目里继续被宿主选中。 |

③ 是本 session 反复抓的形态(**退役了源,没清理已部署的副本**)的又一例 ——
但这次的后果比前几例重:**它在用户项目里活着并阻塞真实流程**。

### 修两侧

**bootstrap:由「部署」改为「回收」**(签名守卫同 hook —— 仅列名文件 + 内容含 teamwork 签名才删,
**用户自建的同名 profile 不碰**)。原部署分支在 v8.293 后已是死代码(`is_dir()` 守卫下静默 no-op),
连同那句「codex-cli 仍部署 …(**活功能**)」的错注释一并更正。

**门禁:区分 CAPABILITY_BLOCKED(执行失败)与 NEEDS_REVISION(评审失败)** —— 三类信号任一命中:
① `files_read` 显式为空 · ② `status: FAILED|CAPABILITY_BLOCKED` · ③ 正文出现「no authorized…」类回执。
报错直接说清 **「这不是 NEEDS_REVISION,是 reviewer 没有文件读取能力,产出的 finding 不可信」**
+ 三条处置 + **「预算没被消耗」**。旧门禁只报「产物不合规」,**把能力缺失说成评审问题**,用户被迫自排一轮。

🔴 `files_read` **缺失不算**(存量产物没这个字段)—— 只在**显式为空**时判定。宁可漏判,不可误判。

**配方 + 模板**:`external-review` 配方明确要求起的 subagent **必须有文件读取能力**,产物记 `files_read`;
`claude-agents/reviewer.md` 头部那段过时描述(还在写 `claude -p` 与 `_run_claude_review` ——
前者 v8.291 退役、后者 v8.293 删除)一并更正。

### 提案里我没照做的三条,以及为什么

- **建议 1/2/5(给专用 Reviewer 配最小只读工具集 / 修 teamwork 的 Reviewer 源模板并重新 bootstrap)**:
  teamwork **不 ship 任何 agent 定义**(`claude-agents/reviewer.md` 是 **prompt 模板**,无工具授权字段)——
  **建议 5 已无处可修**;agent 能力属**宿主侧配置**,框架不该也不能替用户配。
- **建议 3(派发前能力检查)** → 换成**产物侧要证据**:preflight 过了不代表正式跑时能读,
  而 `files_read` 是**已发生的事实**,还省一轮往返。
- **建议 4(CAPABILITY_BLOCKED 不占评审预算)** → **已天然成立** ——
  evidence check 在 `rounds.append` **之前**(`_v8_engine.py` 1720 vs 1791),
  失败根本走不到计数。本版只是把这个事实**写进报错**,让用户不必猜。

### 一处自伤(判定首版静默漏判)

`parse_frontmatter` 是**行式解析不是真 YAML** —— `files_read: []` 会解析成**字符串** `'[]'`。
首版按 list 判空,实测**该红的绿了**。已改为两种形态都判,并加门锁住解析器行为
(解析器一变,判定逻辑必须跟着复核)。

### 测试

1079 → **1092**。

---
