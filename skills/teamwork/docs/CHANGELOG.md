# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.196 · 规划链路 #1+#2:F↔BL 机读绑定(init --bl)+ ws-progress 可启动集

> 规划链路整体审视的两刀:① **F↔BL 绑定是链路最脆一环** —— 只存在于 ROADMAP 手填「对应F编号」单元格 · ship 自刷 WS/翻牌全押它填对;② **「下一个做什么」没有工具答案** —— execution_waves 是静态快照 · 执行中要人肉对照 DAG。

### 改动
- **`init-feature --bl BL-NNN`**(可选):写入 `state.json.bl` = F↔BL 机读绑定;`_resolve_ws_from_feature` **优先**走 state.bl → WS 名册反查(ROADMAP「对应F编号」降为兜底)—— 翻牌漏填单元格不再断链。
- **`ws-progress` 输出 `ready_to_start`**:名册里**依赖全 ✅ 已完成、自身待开始**的 feature(短名+BL)· emit 字段 + 进度块尾行「▶ 可启动(依赖已齐)」—— 并行调度/yolo 直接喂启动决策。
- 测试 +2(state.bl 解析 · ready 推导)。

### 验证
- code(`state.py` 3 处)· pytest 3 failed(baseline)/ 632 passed。

## v8.195 · 🟡 待确认项裁决:删 diff-html-vs-panorama(static-html 退役工具)· 其余 3 件确认活消费保留

> 承 v8.193/194 删减:🟡 批次逐件消费点确认。**diff-html-vs-panorama.py**(340 行):仅 static-html 分支引用 · 163 条 audit 里 static-html 使用 = **1** · 前端栈已定项目强制 same-stack · verify-panorama 已 medium-aware 覆盖 → **删**(+测试 −10 · dev-stage/roles/ui.md 3 处引用改指 verify-panorama)。

### 确认保留(活消费实证)
- **e2e-registry.md**:ship §16 采写 `reg` 字段(REG-case)消费。
- **config.md**:conventions 3 处(缩写注册 + localconfig 模板)。
- **architecture.md**:含 database-schema 模板 = TECH §Schema 影响分析的上游。

### 验证
- 净减 ~700 行 · 引用清零 · pytest 3 failed(baseline)/ 630 passed。

## v8.194 · agents/README 瘦身 683→64 行 · 删自标废止段 + v7.3 产物协议残留

> 承 v8.193 删减 batch 下批:agents/README(683 行 · 全仓仅 1 处历史引用)—— §三 Codex 调用规范**自标「历史记录 · 已被 §11 取代」仍躺 77 行**;§五主对话产物大半是 v7.3 产物命名(dev-report/acceptance.md 等 v8 已不产);§一模型偏好逐 stage 枚举(随模型代际漂移的拐杖);§四协议核心真实但三处重述 Progress Log、启动自问出现两遍。

### 改动
- 重写为 64 行紧凑协议:保留(dispatch 宿主速查 / 降级 WARN / 文件化 dispatch / Key Context 6 类 / Progress Log flush+轮询 / 状态分级 / 危险命令红线)· 删除(自标废止的 §三 · v7.3 产物命名表与 review-log schema · 模型逐 stage 枚举 · 重复段)· external 指针改指 standards §11。
- 净减 −619 行。零活引用(仅 external-model-usage 一处历史注)。

### 验证
- doc-only · pytest 3 failed(baseline)/ 640 passed。

## v8.193 · skills 删减 batch:退役迁移器/收尾遗物/手写模板 + ARCHIVE 照章清空(−2.2k 行)

> 全量 review skills(29.6k 行):按自家律法(三层律 · 定期清空 · 工具自动落禁手写)删 🟢 批次。

### 改动
- **CHANGELOG-ARCHIVE 照章清空**(−1.0k):v8.128→187 共 60 版条目 · git 历史是冷库(章程自 v8.127 就这么写)。
- **删 `_v8_migrate.py` + migrate-v7-to-v8 命令**(−258):v7→v8 一次性迁移已过 190+ 版 · 无 v7 存量。
- **删 `post-feature.py` + 其测试**(−690):v7.3 时代收尾遗物 · v8.145 ship 重构漏删 · 仅自引用。
- **删 `templates/external-cross-review.md`**(−279):v8.20 起 external 产物**工具自动落**、手写是红线 —— 给禁止手写的文件留手写模板自相矛盾;engine scaffold 映射 3 处同步清。
- SKILL/TEMPLATES 引用同步清(migrate 3 处 + 1 处)。agents/README 瘦身(683→~150)留下批。

### 验证
- 净减 ~2.2k 行 · `test_v8_stage_specs` 90 passed · pytest 3 failed(baseline)/ 639 passed(删 post-feature 测试 −10)。

## v8.192 · pause-mark 计时排毒 · stage 内 R5 等待与工作分离(待优化 #5)

> 耗时归因:goal 均值 157m vs 中位 22m(max 128h)—— stage 内 R5 暂停(PRD 确认/预览确认/DB 确认)的**等用户墙钟全算成工作**(v8.172 只拆了 pm_acceptance)· 每次归因都要人肉排毒。

### 改动
- **`state.py pause-mark`**(新):emit R5 暂停点前打点(写 `open_pause`)· **下一个流程命令(start/complete/fix/retry)自动闭合**(`close_open_pause` 接进引擎 4 choke 点)· 等待累计进该 stage `await_minutes` —— resume 侧零纪律。
- **`_stage_durations`**:工作时长 = duration − await(breakdown 显示 `goal 20m(+等待30m)`)· 最耗时(工作)不再被等待污染。
- SKILL R5 协议加打点行。

### 验证
- code(engine helper+4 接线 · state.py 命令 · ship durations)· `test_pause_mark_v8192` +5 · v8.166 套件未破 · pytest 3 failed(baseline)/ 649 passed。
