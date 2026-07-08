# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.198 · loops 对照两修:await-merge 30s 轮询(合并自动下一步)+ yolo fix-retry 10 轮止损

> 对照 claude.com「Getting Started with Loops」:teamwork 是 Turn-based 最佳实践重度实现 · 缺口在 Time-based(结构性等待窗无人看:132h 等合并长尾 · CI 红无人接)+ Goal-based 的 max-attempts(yolo「持续自主解决」无轮次上限 · runaway 风险)。

### 改动
- **`state.py await-merge`**(新 · time-based loop):ship1 / 规划收尾 emit 等合并提示后**跑它** —— 30s 轮询 MR 状态(gh/glab · `--interval/--max-checks` 可调)· **MERGED → emit 下一步**(ship-finalize / 规划 finalize)· WAITING → 重跑续等(用户随时打断改人工)· CLOSED → surface · 连续 3 次查询失败 → FAIL(环境)。`--feature`(读 state.ship.mr_url)或 `--mr-url` 直传(规划场景)。
- **yolo fix-retry 止损**(goal-based max-attempts):同 stage fix-retry **≥10 轮**未收敛 → 硬停 surface(`yolo_rounds_exceeded` 接进 `execute_stage_fix` · 真·硬停的合法扩展:收敛失败 ≠ 继续死磕)· 非 yolo 不受影响(既有「3 次问用户」协议)。
- ship-stage §5 / feature-planning 收尾-1 / SKILL yolo 表同步。

### 验证
- code(`_v8_ship` await-merge · `_v8_engine` 止损)+ doc ×3 · `test_loops_v8198` +4 · pytest 806 passed(基线三失败已由并行修复清零)。

## v8.197 · 规划链路 #3+#4:执行线存在性 lint(幽灵 Line)+ 规划后变更成文路径

> 规划链路审视余下两刀:③ WS「承接执行线」写 Line 4 但业务架构里没有 → 无人查(愿景层→WS 的 taxonomy 是纯 doc 约定 · 断了不报);④ WS ✅ 规划完成后追加/砍 feature 无成文路径(实证 WS-03 追加 BL-006 · 合法性/是否重确认是灰区)。

### 改动
- **ws-lint 执行线存在性**(③):WS 承接的 `Line N` 必须在 `product-overview/*业务架构*.md` 的执行线列表存在 · 幽灵 Line → NONCONFORMANT(hint:新线先在业务架构登记)· 无业务架构文档 → skip 不误报。
- **feature-planning Step 10 规划后变更**(④):**追加 feature** = 轻量(R5 一句确认 → worktree 内改名册+ROADMAP+变更日志 → ws-lint/ws-progress → MR · 不重开全流程);**砍/改方向** = 回 feature-planning(WS 回 🔄 讨论中);🔴 已启动的 F 不在此列(执行层变更 · 别用规划变更掩盖执行返工)。
- 测试 +3(幽灵 Line / 存在 OK / 无架构 skip)。

### 验证
- code(`state.py` ws-lint)+ doc(feature-planning Step 10)· pytest 3 failed(baseline)/ 635 passed。

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
