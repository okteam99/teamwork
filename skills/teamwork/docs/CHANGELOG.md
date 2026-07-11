# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.225 · 模型档位判断框架(任务性质→档)+ 并行姿态翻转(鼓励 subagent/teammate)

> 用户两提案合一:① skill 层加模型建议(规划/方案/关键评审用高档 · 代码用执行档 · 测试验证用轻档 · GPT 同理);② 鼓励多用 subagent/teammate 提并行度。形态守 v8.194/216 判例:**「任务性质 → 档位」判断框架 · 非「stage → 型号」映射**(型号随代际漂移 · 跨宿主不通 · 逐 stage 映射是规则不是判断)。

### 改动
- **agents/README §一 重写为档位表**:深度档(创造+深度判断:规划/TECH/架构 CR/PRD/诊断/关键裁决)· 执行档(实现 · 主对话继承即是)· 验证档(校验/枚举:TC 对照/测试执行/机械外化)—— 型号列仅当前映射示例(Claude: Fable/Opus↔会话↔Sonnet/Haiku · GPT 对应档)+ 每档标**典型并行形态**。
- **三条硬边界**:架构 CR 与关键裁决不降档;**评审独立性优先于档位**(两个轻模型冷审 > 一个强模型热审);主对话模型 = 用户主权(AI 只建议)。
- **并行姿态翻转**(SKILL subagent 条目):从「⚠️ 非默认 · 不过度使用」改为「**默认考虑:每 stage 开工先问哪些子任务可并行**」(冷审 N 路同发/多模块 teammate/调研 fan-out)· 护栏原样(边界清晰且够大/worktree 路径/**流转与整合永归主对话**)。
- **prepare §1.4**:关键 Feature 建议主对话深度档 + prepare 时标出可并行子任务。台账 host+model(v8.208/209)= 档位建议的年检校准数据源。

### 验证
- doc-only · pytest 826 passed。

## v8.224 · skill 全文件描述审计:A 类 7 项「变假话」清零 + FLOWS 重写薄壳(102→40)

> 用户:整体看 skill 各文件描述的冗余与不合理。盘点实锤:合并三连(v8.220-223)后 **7 项过时描述**在教旧规则 + 流程类型**三处平行描述**(FLOWS×SKILL×prepare)。另发现元教训:cite(v8.199)/顶栏(v8.206)/hooks(v8.213)各漏扫一个目录 —— 退役清扫必须覆盖全部内容目录。

### 改动
- **FLOWS.md 重写 102→40 行**:闭集表 = Feature(full/micro)/Bug/Planning/排查 · telos 一行化 · 判定权威显式指 prepare(结束三处平行:prepare=权威 · SKILL=视图 · FLOWS=薄壳)。
- **SKILL 类型段真重写**(吃掉 v8.220/223 两层过渡注记):新 5 行表 + 授权暂停点表(删敏捷需求行 · Micro→Feature·micro)+ DB 变更措辞。
- **STAGES.md** flow 列更新 + blueprint_lite 标 DEPRECATED;**roles/pmo.md** 六闭集行改;**conventions.md §1** ID 表(敏捷/M 行标 legacy · 存量 M-id 有效不迁)。
- **漏网残留清零**:cite 仪式 ×4(prepare + 三个 report 模板)· dev 顶栏 ×1(scripts-policy)· hooks ×1(prepare)。

### 验证
- pytest 826 passed。

## v8.223 · blueprint_lite 并入 blueprint + lite preset 退役(preset 收为 full/micro)

> 用户两连问推到底:① blueprint_lite 还需要吗 —— 它与 blueprint **目标相同**(dev 前方案收敛)· 差异全是重量(评审组合=roster 已管 · verify-ac 分档=一行判断 · 文档深度=四段/模板已管)= 「stage 版的敏捷需求」;② 并入后 lite 链 = Feature 链的 **needs-ui=false 剖面**(一条冗余链)→ lite preset 整体退役。micro 保留(跳 review/test 是真结构差)。

### 改动(新路收口 · 存量三保留)
- **`FEATURE_PRESETS = (full, micro)`** · `LEGACY_FLOW_ALIASES:敏捷需求 → Feature·full`(轻量由动态 roster + clarity 承担)· `--preset` choices 同步。
- **存量兼容三保留**(in-flight 不断链):AGILE_FLOW 图原样(`resolve_flow_graph` 对 state.preset=lite 仍解析)· `internal_flow_key/_flow_key` 的 lite→敏捷需求 映射保留 · `BLUEPRINT_LITE_SPEC` 保持注册(标 DEPRECATED · 存量走完后删)。
- blueprint-lite-stage.md 挂 deprecated 横幅;prepare 关键词行(加按钮类 → Feature · 轻量由 roster/clarity)+ SKILL/README 注记同步。

### 验证
- pytest 826 passed(存量 lite 兼容断言全绿)。

## v8.222 · 物化校验 flow 归一审计:10 处 legacy 比较死门复活(含 Micro initial=goal 真 bug)

> 用户点名:检查 python 脚本物化校验是否匹配 v8.220 合并。审计实锤 **10 处失配** —— state 只存 `Feature+preset` 后,所有 `flow_type == "敏捷需求"/"Micro"` 直接比较**静默失配**:最重的是 `DEFAULT_INITIAL_STAGE` 查表 → **preset=micro 错拿 initial=goal(应 dev)**,真 bug;其余 9 处是死门(needs-ui×lite 拦截失效 / goal 转移 lite 走错 blueprint / dev-next micro 不再跳 review / test-done micro 放行失效 / TC-PRD skip 失效 / agile 判定失效 / ship distill micro 键失效)。

### 修法(一处逻辑 · 十处生效)
- **`internal_flow_key(flow_type, preset)`**(state.py)+ **`_flow_key(state)`**(specs):public/legacy → 内部图表键(敏捷需求/Micro 键保留 · 存量 state 兼容)。
- init 的归一提前到 `initial_stage` 查表**之前**(原在其后 → UnboundLocal · 测试首轮 50 failed 抓出)· 查表改内部键。
- specs 8 位点比较统一走 `_flow_key` · ship distill micro 判定补 preset 分支。

### 验证
- `test_flow_merge_v8222` +7(键映射 / micro initial=dev / 5 个死门复活断言)· pytest **826 passed**。

## v8.221 · prepare 适配 v8.220:配置面板新词汇(flow=Feature·preset)+ 分支前缀统一 + 链预览归一

> 实证 case(用户看 INFRA CI 缓存 prepare):配置确认还在说旧语言 —— `flow=Micro` · `ID=INFRA-M…`(M 系)· `branch=micro/…`。v8.220 机器层合并后 prepare 面是适配缺口。

### 改动
- **prepare-check emit 加对外词汇**:`flow_type_public`(Feature/Bug)+ `preset`(full/lite/micro)+ `config_line_hint`(⚙️ 配置行照抄:`flow=Feature · preset=micro` · 非 full 才标)。
- **链预览归一**:legacy flow 名 → 内部链键映射(engine `FLOW_STAGE_CHAIN` 键保留 · `Feature:lite/micro` 归一)· micro 链照旧 `dev→pm_acceptance→ship`。
- **分支前缀统一**:`agile/`、`micro/` 退役 —— Feature 全 preset 一律 `feature/`(Bug=`fix/`)· prepare.md 分支表改。
- **关键词表改 preset 语言**:「换 logo/改文案…」→ Feature·preset=micro;「加按钮/加字段…」→ Feature·preset=lite。
- 冒烟:legacy `--flow-type Micro` → public=Feature · preset=micro · **ID=F 系** · 链正确。

### 验证
- pytest 819 passed。
