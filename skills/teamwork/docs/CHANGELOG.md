# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.157 · PL 质疑加第六问「既有行为变更」:改既有默认行为必入待决策项 · 治 premise 焊死蒙混

> 用户(实证 TermPro 文件 locate-vs-open case · 排查 transcript):终端链接点击默认全走文件定位 · 查哪个需求引入 · 为什么没评估到位。

### 诊断:方向级默认行为变更被当既定事实 · 没进用户拍板点
- 根因不是实现 bug(代码 100% 忠实 PRD)· 是 PRD 把「文件点击 原打开 → 现只定位」这个**既有默认行为变更**登记成「既有行为取舍/有意改变」叙述段 · §待决策项 空 → **从没进 goal 确认暂停点让用户拍板**。8 轮 external 全打磨「怎么定位」却没人回炉「该不该只定位」前提(评审越细越巩固 locate-first 框)。
- 框架缺口:PL 质疑五问(价值前提/问题定义/范围最小化/上游对齐/复活检查)**没一问覆盖「既有默认行为变更 → 必须 ratify」**;§待决策项 也无「改既有行为必入此段」规则。

### 改动(doc-only · 治本)
- **PL 质疑五问 → 六问**:加 ⑥ **既有行为变更**(PRD 改了某既有用户可感知默认行为〔原 A → 现 B〕→ 🔴 必升级为显式 §待决策项让用户拍板 · 不可登记「取舍/有意改变」叙述蒙混)· goal-stage §3 + product-lead.md(附实证 case + 「评审越细越要防被越打磨越巩固的框带走」)。
- **PRD 模板 §待决策项 加硬规则**:改既有默认行为必入此段(列 原/新/为什么改/推荐)· 不可只在背景/取舍段当既定事实写掉。
- 全仓「五问」字面 → 六问(goal cite 表 / prd schema 注 · CHANGELOG/RETRO 历史不动)。

### 验证
- doc-only · pytest 3 failed / 534 passed(零回归)· 无测试 pin「五问」字面。

## v8.156 · 归档 INDEX 描述列业务-only:--archive-desc 只业务不过程 · 过程信息嗅探 WARN

> 用户(看 aifriend INDEX case API-F051/F053):feature 归档总结不应有过程信息 · 目标是总结需求是什么/做了什么/影响(业务信息)· 不是过程信息(评审轮次/bug 数/全绿)。

### 诊断
- `--archive-desc` 全链引导只写「≤200 字极简描述」· 从没说**业务非过程** —— AI 把刚跑完流程手头有的过程数据(「评审拦10真bug·external独家4」「cps11+集成11+回归520全绿」「11轮 external blueprint+3视角 code review」)灌进 INDEX 业务索引。过程数据本在 zip 内 state.json/REVIEW.md · 不该进业务索引。

### 改动(代码 + 文档 + 测试)
- **引导全面改「业务摘要 · 只业务不过程」**:archive planning gate emit / sanitize brief / ship-stage §3 命令 + §15 描述列 —— 明确「这需求是什么/做了什么/业务影响/对外契约」· 不写评审轮次/bug 数/测试数/全绿/external 独家/code review · §15 加 ✅业务 vs ❌过程 对照例(用截图 case)。
- **`_archive_desc_process_smell` 嗅探**(可枚举强信号进脚本):命中「评审/全绿/回归/external 独家/money bug/N 轮/N 视角/拦 N」→ archive emit **WARN**(不 BLOCK · 过程检测整体不可枚举 · 只逮无歧义强信号 · 防业务词误报)。
- 测试 +4(截图 bad case → WARN / 纯业务 good case → 不报 / N 轮计数 → WARN / 空 → 不报)。

### 验证
- pytest 3 failed / 534 passed(baseline 3 · 净 +4)· smell 对截图 API-F051 实例判别正确(bad→WARN · good→None)。

## v8.155 · goal 评审重构:草稿后并行派 3 个隔离 Agent 冷审 · 治锚定鼓掌 · PM 退整合者

> 用户(承数据分析线):goal 改成 PRD 草稿写完后 · 并行派 3 个 Agent 评审。

### 诊断闭环(多轮真实数据驱动)
- 读 aon/jdp/aifriend/TermPro 真实归档:in-context 的 arch/qa 在 goal 常产 **info-only 鼓掌**(SVC-F002:arch/qa 只 info 级背书解法)· 而隔离的 external/PL 抓到 high 契约 gap。根因 = **同一 AI 起草完审自己 = 带起草记忆脑补填缝 → 漏细微 gap**。框架早用 PL 的 subagent 隔离(v8.132)证明了机制,却把 arch/qa 留主对话靠「怀疑者视角防鼓掌」乐观假设(architect.md)—— 数据证伪。
- v8.149 拿掉 goal-external 的真实代价 = 丢「冷审安全网」;真修法不是加回 external · 是**把全部 reviewer 隔离冷审**。

### 改动(流程重构 · 代码 + 文档 + 测试)
- **goal §3+§5 合并为「并行冷审循环」**(9 步 → 8 步):草稿 v0.1 → **并行派 QA/Architect/PL 三个隔离 subagent 冷审**(只喂 PRD+cite+KB · 不喂起草心路)→ 早问门(**后移到冷审后** · 冷审视角更准识别用户决策)→ PM 整合修订 → **Round 2+ 验证模式**(喂上轮 finding+处置 · 核实 fix+找新)→ 全 APPROVE 收敛 · 3 轮不收敛升级用户。
- **PM 退出 reviewer**:`DEFAULT_REVIEW_ROLES[Feature,goal]` `[pm,qa,architect,pl]`→`[qa,architect,pl]`(敏捷 `[pm,qa,architect]`→`[qa,architect]`)· PM = 作者+整合者(审自己最锚定)· 不给 verdict · 门禁/模板 reviewers 同步去 pm。
- **architect.md 翻案**:goal 评审 `默认主对话`→`默认隔离 subagent`(评的是自己起草物 · 必隔离)· blueprint/review 评 RD 产物沿用主对话。qa.md 同加 goal 冷审默认。
- external opt-in 保留(契约型后端地基 feature 仍可加为第 4 冷审 · v8.149 安全阀 · 数据证明有用)。
- 测试:reviewers_match/pl_challenge 适配去 pm · simplicity-lens pin 更新(external opt-in)· 注释校正。

### 验证
- pytest 3 failed / 530 passed(baseline 3 · 零回归)· 8 步链 + cite 表 + brief + Output Contract 全对齐。

## v8.154 · disable_external_review 改 hard rename:撤 v8.153 旧名兼容(无项目使用 · 不留)

> 用户(承 v8.153):不用兼容。

### 改动(代码 + 模板 + 文档 + 测试)
- 撤掉 v8.153 加的旧名 OR 兼容:两 reader(state / _v8_stage_specs)+ bootstrap WARN reader **只读新名** `disable_external_review` · 旧名 `disable_heterogeneous_review` 废弃不再读取。
- 依据:核过无任何消费项目设旧名(只框架仓自己 · v8.153 已改新名)· 硬改无 silent break 风险 —— 同 v8.145「不留兼容期」路子。
- templates / standards 的「旧名仍兼容」注 → 改「v8.154 旧名已废弃」。
- 测试:v8.153 兼容测试反转为 hard-break 回归守护(单设旧名 true **不再生效** · 防有人误把 OR fallback 加回)。

### 验证
- pytest 3 failed / 530 passed(baseline 3 · 零回归)· 旧名非-docstring/非-守护引用清零。

## v8.153 · config 改名 disable_heterogeneous_review → disable_external_review(旧名 OR 兼容)

> 用户:`disable_heterogeneous_review` 这个配置名字改为 `disable_external_review`。

### 改动(代码 + 模板 + 文档 + 测试)
- **config key 全量改名** `disable_heterogeneous_review` → `disable_external_review`(更贴语义:禁的是 external 评审角色 · 不是「异质」jargon):两个 reader(`_read_disable_external_review` / `_localconfig_disable_external`)· bootstrap 默认 + 自愈 + 启动 WARN · templates(localconfig.json / config.md)· standards §11/§十二 · 内部 var `het_disabled → ext_disabled`。
- 🔴 **旧名 OR 兼容(不 silent break)**:reader 读「新名 is True **or** 旧名 is True」—— 防 bootstrap additive 自愈把新名补默认 false 顶翻已有旧 true(healer 只补不覆盖 · 老项目旧 key 仍生效)。
- 行为口径顺带校正:reader/template/doc 旧注释还写「exec 自审」· 实际 v8.108 起是 **subagent 降级配方**(emit SUBAGENT_FALLBACK · 非 exec)· 一并改正。
- `checks.heterogeneous_review`(bootstrap emit check 名)语义仍准(报异质评审健康度)· 留;warning 文案已用新 key。
- 测试:reader/默认/降级三处改新名 + 新增旧名兼容测试(旧 true+新 false → 仍禁用)。

### 验证
- pytest 3 failed / 530 passed(baseline 3 · 净 +1 兼容测试)· 残留扫描:非测试/非兼容引用清零。

