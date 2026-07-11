# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.218 · 四段结构试点:review + dev stage 重构(目标/硬规则白名单/建议手段菜单/契约)

> 用户方向(第一性重审):保留 stage 划分 · 每 stage 给**目标**(QA=保障质量)+ 保**必须规则**(如异常必有 log)· 评审方式拆细为**建议** · 降低强制比例给模型发挥空间 —— 更好也更快。现状:12 stage 1666 行 · 🔴×139(全是红线 = 没有红线)。

### 改动(试点 2/12)
- **review-stage 235→77 行**:①目标(拦质量盲区 · 独立采样 92/163)②硬规则 8 条白名单(独立性/定级实证/verdict 门槛/裁决举证对称/范围锁定/轮次预算/external 协议/汇总不替代 · **每条带 why**)③手段菜单 8 项(AC 对照/diff 走查/边界审查/对抗复现/简洁性 counter-lens/测试质量抽查/截图核对/KNOWLEDGE 对照 · 各标「何时值得」· AI 自选 + Execution Plan 留痕)④契约(findings schema/fix-retry 命令链)。
- **dev-stage 149→63 行**:①目标(设计→可验证实现)②硬规则 7 条(DEV-RULES/worktree 路径/测试证据硬门/设计↔实际核对/全景编译契约/Bug 不重写根因/完工自查打钩)③手段菜单 6 项(🔴 **TDD 红绿从强制降为强烈建议默认** —— 测试证据仍是硬门 · 手段自由)④dev-complete 契约。
- 「怎么做」步骤教程整段删(目标+菜单+契约足够 · 步骤模型自推)。
- 安全网:v8.217 分诊校准回路对冲(放权后质量掉 → 台账显形 → 判据回收)。

### 验证
- 370→140 行 · pytest 819 passed(stage 散文与机器层零耦合实证)· 余 10 stage 待数据后推开。

## v8.217 · 智能分诊 v2:台账「分诊校准(预测→实际)」列 + 降级触发(持续分诊)

> 承 v8.215/216(维度化+动态 roster):v2 落学习回路的数据侧 —— 分诊判定要能被事后打分,判据才能随数据校准而非拍脑袋。

### 改动
- **archive emit 加 `triage_calibration` 束**:预测侧 = clarity + roster 调整摘要(审计已留);实际侧 = diff 文件数(git 确定性)+ goal 修订轮数(PRD 被打回?)+ review 轮数。
- **PROCESS-LEDGER 末尾加「分诊校准(预测→实际)」列**(末尾加列纪律 · ledger-migrate 单源自模板**自动升级**——本版测试实证:旧表 10 列 → 新 canonical 自动 14 列)· 年检算**分诊准确率**(explicit 判定却 PRD 常打回/review 高轮次 → 判据收紧)。
- **降级触发**(持续分诊 · 补反向):blueprint brief 推「TECH 复杂度=简单且零架构决策而 roster 仍重 → 提议降级(R5 → change-review-roles)」—— 升级触发已有(§2.1)· 分诊不是一次性的。

### 验证
- `_triage_calibration` 测试 +2 · migrate 测试改不写死列数(canonical 单源验证)· pytest 819 passed(预期)。
