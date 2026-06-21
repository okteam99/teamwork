# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.180 · ship 确定性自刷 WS 进度块 · 治 yolo 下 WS 文档 stale(软指令没人接住)

> 用户看 yolo ship2:感觉没更新 WS 文档。诊断:① WS 更新本在 **ship1 §3.5 翻牌**(不在 ship2 · ship2 零内容清场)② §3.5 spec 只说「改 WS-NN.md」**没说跑 ws-progress**(v8.174 只接了 emit 没同步 spec)③ planning-backref 门**软**(只看传没传 `--planning-artifacts` · 不校验 WS 刷没刷)→ yolo 自主无人接住 · WS 进度块 routinely stale。

### 改动
- **`ws-progress --feature`**(新):自 feature 的 F-id 在各 ROADMAP「对应F编号」匹配 → 解析**所属 WS**(关联WS · 带 BL→名册反查退路)· 不必报 WS 编号。解析不到 → WARN 跳过(best-effort)。
- **ship archive 确定性自刷**(主修):翻牌后 ship **自动** invoke `ws-progress --feature --write` 刷新 WS 进度块 / 依赖 DAG + 把 WS 文档纳进归档 commit(emit `ws_progress_refreshed`)· **不靠 AI 纪律 · yolo 也一定刷**。
- **§3.5 spec 同步**:翻牌填「对应F编号 = 本 feature F-id」(archive 靠它解析 WS)· WS 进度块**不用手动刷**(archive 自刷)· planning-backref emit 对齐。
- **测试** `test_ws_resolve_v8180` +6(解析 / 名册退路 / 归一化 / CLI)。

### 验证
- code(`state.py` --feature 解析 + `_v8_ship` archive 自刷)+ spec · pytest 3 failed(baseline)/ 620 passed。

## v8.179 · yolo 策略调整:预研门(物化硬门)+ 非异质降级 subagent 冷审 + localconfig 单源

> 用户调整 yolo 策略 3 点:① 异质 review 受 localconfig 控制(确认)② yolo 启动非异质 → 醒目提示 + 确保 subagent 冷审 ③ yolo 正式跑前深入调研 + 核心重要问题提前和用户确认。

### 改动
- **yolo 预研门**(③ · 物化硬门):`init-feature --yolo` **前**必产 `YOLO-PREFLIGHT.md`(深入调研真实代码 + 核心重要决策**逐条用户确认**)· 工具校验存在 + 已填(哨兵删)否则 FAIL。**理由**:yolo 零暂停点 → 意图保真膜必 **front-load**(意图/关键取舍错了没机会中途纠)。模板 `templates/yolo-preflight.md`。
- **非异质降级 subagent 冷审**(② · 修真 bug):旧 1644 yolo 实跑日志闸**无 ext_disabled 豁免** → 误 BLOCK 单模型 yolo(异质日志永远拿不到)。修:yolo + `disable_external_review` 改认 **subagent 冷审**证据(校验 `review_via: subagent` · 非主对话热审 / 手写)· 「非异质」也不许「不冷审」。+ `init-feature --yolo` 检测 `disable_external_review` → kickoff **醒目警告**(`yolo_external_warning`)。
- **localconfig 单源**(① · 确认):异质 external 受 `.teamwork_localconfig.json` `disable_external_review` **单一开关**控制 · SKILL § yolo 写明。
- **测试** `test_yolo_strategy_v8179` +8 + `test_state` CLI +2(preflight 缺失 / 哨兵 BLOCK)· 现有 5 个 yolo init 测试补 seed preflight。

### 验证
- code(`state.py` init 预研门 + 警告 · `_v8_stage_specs` 1644 闸)+ template + SKILL doctrine + test · pytest 3 failed(baseline)/ 614 passed。

## v8.178 · 测试基线失败集差分 gate · 治 brownfield 反复 stash-baseline（欠最久 harvest 项）

> harvest 89 条审计:「基线失败集 / stale 测试无门禁」**跨 3 次 harvest 复现**(8× · 欠最久)。brownfield 共享套件常 base 即红(历史重构遗留 / 他人欠债),没登记机制时每个 feature 都重复「stash → 跑 base → diff → REVIEW 论证非本 feature」甄别(实证跨 3+ feature 反复确认同一批 5-6 个失败)。

### 改动
- **注册表**(新 `project-specs/test-baseline.md` · 项目级单源):登记 base 即红的预存在失败(id + 套件 + 原因/清账计划)· `templates/test-baseline.md` · `--add` 懒创建(不污染干净项目)。
- **`state.py test-baseline`**(新命令):`--add`(登记)/ `--list` / `--diff --current "ids"`(当前失败对照基线算 new / excluded / stale)。
- **差分 gate**(dev + test):`--current-failures` 传当前失败 id · 工具对照注册表算新增 —— **0 新增**(当前 ⊆ 基线)→ dev gate 放行 / test `_test_transition` 照常转 pm_acceptance;**有新增** = 回归(修)或新预存在(`--add` 登记)。e2e 仍严格 0(feature-scoped)· fix-retry `is_failed_round` 同步认 diff-clean。
- **brief 同步推**(v8.170 铁律):`_dev_brief` / `_test_brief` + test-stage.md §base 即红差分 —— 别人肉 stash-baseline。
- **测试** `test_test_baseline_v8178` +17(注册表 / 差分 / dev gate / test transition / CLI)。

### 验证
- code(`state.py` 命令 + `_v8_stage_specs` 3 gate + `_v8_engine` arg/evidence 白名单/fix-retry)+ template + spec/brief + test · pytest 3 failed(baseline)/ 604 passed。

## v8.177 · ws-progress 名册驱动 + 依赖 DAG · 跨子项目/legacy feature 不漏 + 派生依赖图

> 实证 supersimples WS-03:① 跨子项目前置 K0=SDK-F040 登记在 SDK ROADMAP 的 **legacy 表**(无「关联 WS」列)→ v8.174 ws-progress 只扫「关联 WS」漏掉它 · 总览只 6 个不是 7 个(用户被迫手写 📌 补注)② 无 feature 执行依赖关系图。根因:工具从不读 WS 自己的名册,而「WS 拥有哪些 feature」只在 WS frontmatter `features[]` 里声明。

### 改动
- **名册驱动**(`state.py` · 主修):ws-progress 读 WS frontmatter `features[]` 当**权威名册** —— 声明的 feature **全列出**(含跨子项目/前置)· 状态自各 ROADMAP 按 BL 匹配 · 匹配不到标「未匹配」不漏报。解析器放宽:① 表头门槛降到 BL+状态(吃无「关联 WS」列的 **legacy 表**)② 行 id 放行名册声明的非 BL id(SDK-Fxxx)。无名册 → 回退 v8.174 纯「关联 WS」扫(向后兼容)。
- **依赖 DAG**(新):自 `features[].dependencies` 派生 Mermaid flowchart,写回 WS 的 `WS-DAG` 标记区(节点=feature 短名 · 边=依赖→被依赖)。
- **模板**:加 `## feature 依赖关系图` + `WS-DAG` 标记区 · 总览注释 / 设计要点 #8 改名册驱动。
- **测试** +8(`test_ws_roster_dag_v8177`:名册解析 / legacy 表 / DAG / K0 现身)· v8.174 套件适配新签名。

### 验证
- code(`state.py` ws-progress 重写)+ template + test · pytest 3 failed(baseline)/ 587 passed。

## v8.176 · 设计=代码闭环:扩已有页导入真实源(构造)+ dev 设计↔实际一致性核对(验证)

> 用户:**最大限度保障设计稿和实际效果一致**。v8.175 复现门只解设计时一半,且「复用真实共享组件」是偏好不是硬约束;更关键:「和实际效果一致」只有真实 feature 建好后才能验,而那道闸(dev §3「并排对照」)是 optional + 含糊。本版把同构从「口号」收成「**强制构造 + 落地验证**」闭环两端。

### 改动
- **构造侧**(ui-design §3):扩已有页「**复现 ≠ 重写**」· 优先级同 Layer 1 —— ㉑ **导入真实页/组件源**(同 monorepo 包 → 与真实 app 同一份代码 · 改真实页 preview 自动跟)→ ㉒ 暂不可导入则 **1:1 镜像** + UI.md 记豁免 + 抽包回收 → 🔴 **绝不凭印象重画**(= 概念页变体 · drift 源头)。
- **验证侧**(dev §3 · 主修):「并排对照 · 可选」→ **设计↔实际一致性核对(必做)**:起全景 dev server + 真实路由两边并排 browse 截图 · **逐要素给「一致/背离」结论**(布局 / 交互流 / 状态 / 字段映射)· 像素自由非字节还原 · 背离不许静默放过(修实现 or 回 ui_design)· = 「设计稿=实际效果」的落地闸。
- **brief 同步推**(v8.170 铁律):`_dev_brief` 加「UI feature → dev 后设计↔实际核对必做」· 治模型 dev 时不主动核对。
- **反模式 +2**:扩已有页凭印象重画 / dev 跳过一致性核对。
- **测试** `test_dev_brief_parity_v8176` +3:锁 dev brief 携带落地闸。

### 验证
- doc(ui-design §3/反模式 · dev §3)+ brief(`_dev_brief`)+ test · pytest 3 failed(baseline)/ 579 passed。
