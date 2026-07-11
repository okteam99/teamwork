# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.220 · flow_type 机器层收缩 6→3(用户拍板「直接到位」):Feature/Bug + preset 重量档

> 数据:170 audit 里敏捷+Micro 合计 11% —— 它们是「同一种工作的重量档」非独立工作形态 · 与维度化(clarity/roster)形成冗余平行系统。Bug(diagnose 先行 · 结构不同)与 Planning(不进状态机)保留;问题排查退到 triage mode A 深度版。

### 改动(机器层 · 存量零迁移)
- **`FLOW_BY_TYPE` 键收编**:`Feature`(=full)/ `Feature:lite`(原敏捷)/ `Feature:micro`(原 Micro)/ `Bug` · 三份转移图**原样保留**(行为等价)。
- **`resolve_flow_graph(flow_type, preset)` + `normalize_flow`**:legacy 名(敏捷需求/Micro)传入自动归一 → state 只存 `flow_type∈{Feature,Bug}` + `preset∈{full,lite,micro}`;存量 state.json 读到 legacy 值同样归一(零迁移)。
- **`init-feature --preset`** 新参;legacy choices 保留作别名(肌肉记忆/脚本兼容)。
- **角色矩阵 preset-aware**:`build_default_stage_review_roles(flow_type, preset)`(内部键映射旧名)。
- **ID 字母收敛 F/B**(Micro 的 M 退役 · 存量 M-id 不受影响);specs `allowed_flow_types` 收编(blueprint/blueprint_lite → Feature · 链图限定可达)。
- SKILL/README/prepare 加机器层收缩注记(6 类型表转为语言层预设视图 · 全表重写下版)。

### 验证
- pytest 819 passed(M→F 断言更新 ×3)· R2 闭集红线新形态 = 枚举 2 + preset 有界。

## v8.219 · goal-stage 四段结构(试点 3/12)+ 修 v8.216 roster 硬编码残留

> 用户问 goal 是否需调整 → 判定:比其余更迫切 —— 除四段欠账(🔴×24/153 行 · 密度第二)外还有 **v8.216 活冲突**:§3 写死「Feature 派 3 个/敏捷 2 个」固定组合 · 而 Output Contract 又说「按 stage_review_roles」—— 同 spec 两套口径 · brief 已 roster 驱动 · 旧文字每 feature 都在误导(照章办事风险)。

### 改动
- **goal-stage 153→85 行**:①目标(拦意图偏差)②硬规则 8 条白名单(PRD 三命门/冷审隔离**不喂心路**〔派谁派几个=按 roster〕/早问门三闸〔事实类上抛=R5 违规〕/物化门禁/既有行为变更必升级/AC>10 反压/收敛软上限/auto 留痕 · 每条 why)③手段菜单(调研四源按需/各角色 mandate 表**按 roster 派**〔质疑六问指 roles 单源〕/双向质疑/验证模式)④契约(PRD/PRD-REVIEW schema + 重点 review 指引压缩为契约段)。
- **roster 冲突修复**:删「3 个/2 个」硬编码与 external opt-in 特例段 —— 组合全部交给 prepare 的 role_value_criteria + change-review-roles 审计。

### 验证
- 试点累计:review 235→77 · dev 149→63 · goal 153→85(537→225 行)· pytest 819 passed。
