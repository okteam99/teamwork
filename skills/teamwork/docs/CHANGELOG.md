# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.184 · feature-planning 进流程建临时 worktree · 隔离规划产物(文档+全景代码)

> 用户:feature-planning 可能动文档和全景设计,进流程时应按 worktree 策略建临时 worktree。现状反例:feature-planning.md 明确「**不需要 worktree** · 在主工作区写文档」—— 但 planning 现在产出 WS/ROADMAP/product-overview 文档 **+ 全景 `preview-project` 代码**(v8.169 后是带 package.json 的真 code),落主工作区**污染主分支、撞并行 feature 基线**。

### 改动(反转「planning 不进 worktree」)
- **planning-check emit `worktree_setup`**(物化入口 · 同 feature 策略):进流程先 `git worktree add -b planning/<短名> .worktree/planning-<短名> origin/<merge-target>` + cd · 规划产物全写 worktree 内 · 完成 push + MR → 合并删 worktree。+ `key_constraints`/`next_hint` 同步。
- **feature-planning.md**:§1 反转「不需要 worktree」+ R6 nuance(不出 **feature 实现**代码 · 但全景 preview-project 是设计代码会改)· §2 加 **Step 0**(建 worktree 进流程第一步)· Step 9 改 worktree 内 commit + MR + 清理 worktree。
- **bootstrap 规划 forewarn** 加 worktree 提示。
- **定位**:worktree 只是**文件隔离** · planning 仍「PMO 主对话直接做」不进状态机 · 仅不走 ship 状态机(纯文档/全景 MR)· trivial 单文档微调用户可免。

### 验证
- code(`state.py` planning-check + `bootstrap` forewarn)+ doc(feature-planning.md §1/§2/§9)· `test_state` planning +worktree 断言 · pytest 3 failed(baseline)/ 620 passed。

## v8.183 · TECH 加错误日志(WARN/ERROR)+ SQL 查询性能(给理由)两必查项

> 用户:① 错误异常是否有 **WARN/ERROR 日志**作必查项 ② 涉 **SQL 查询**是否考虑性能优化也检查**并给理由**。

### 改动
- **§错误处理加「日志级别」列 + 不静默吞异常**:每条 catch / error 路径必有 **WARN**(可恢复/预期)或 **ERROR**(意外/需排查)日志 + 足够上下文(feature / 业务 id)· 静默 catch = 线上盲区、排查无据。
- **§查询性能**(新 · 涉 SQL 必填 · 🔴 给理由):list / 聚合 / JOIN / 高频查询分析性能特征(索引命中 / N+1 / 全表扫 / 分页)并 **justify 两个方向**(够快说为什么 · 要优化说优化了什么为什么)· 漏理由 = Tech Review 打回(同 §简洁性 / §FK 的 justify 模式)。
- **完工自查 +2 必查项**:错误/异常有 WARN/ERROR 日志(不静默吞)· 涉 SQL 查询性能已分析并给理由。
- **blueprint 规范同步**(§3 + §88 Output Contract)。

### 验证
- doc(`tech.md` 224→257 · `blueprint-stage.md` §3/§88)· 无 .py 改 · `test_v8_stage_specs` 90 passed · pytest 3 failed(baseline)/ 620 passed。

## v8.182 · TECH 加「完工自查」物化清单 · RD 实现完逐项打钩 · 对着设计防「设计了没实现」

> 用户:需要 RD 开发完在文档内逐项打钩的自查清单么?现状:dev-stage §4 **有**自查清单,但 ① 在 spec 里、**不在 per-feature 文档**(打钩只在 AI 脑子)② 通用门(规范/build/linter),**不覆盖 TECH 设计承诺**(新加的 §错误处理/§依赖与影响/§测试策略 + v8.176 parity + v8.178 基线)。

### 改动
- **TECH.md §完工自查**(新 · RD 实现完逐项打 ✅):**对着本 TECH 设计逐条**(现状基线前提 / §错误处理 / §依赖与影响消费方 / §数据结构跨层 / §数据库变更 / §测试策略集成契约)+ 通用门(规范/无回归/build/linter/commit)+ (UI)设计↔实际核对。每项指向证据(测试/文件/编译)· 不适用 `N-A` · **专防「设计了没实现」**。
- **dev-stage §4 改物化**:「读清单」→「在 `TECH.md §完工自查` **文档内逐项打钩** · review 据此核」· cite 清单 + `_dev_brief` 同步推(消费点)。
- **定位**:soft **完整性**自证 —— 强门禁(test exit-code / verify-ac / external-review)仍是硬墙;本清单补「设计↔实现」完整性 · review 验 · 非橡皮图章。

### 验证
- doc(`tech.md` +完工自查 · `dev-stage.md` §4/cite)+ brief(`_dev_brief`)· `test_v8_stage_specs` 90 passed · pytest 3 failed(baseline)/ 620 passed。

## v8.181 · TECH 模板补 6 缺口 · 进 dev 前最后 spec 完整化

> 用户 review TECH 模板(进 dev 前最后 spec)找遗漏。交叉比对:blueprint 规范 §3 要求 TECH 含「§模块 · §数据 · §接口 · §依赖与影响 · §风险」5 段,**模板只有前 3 段** —— §依赖与影响、§风险 规范要求但模板**没槽位**(AI 必漏)。另有 4 处真盲区。

### 改动(模板 + 规范对齐)
- **Tier 1**(规范要求、模板缺):**§依赖与影响面**(改契约必列消费方 · grep 不凭记忆 · 治 harvest 实锤「跨子项目改动撞 fixture red 无 CI 拦」「迁移 import 名单 MR 窗口被并行扩」)+ **§风险与缓解**(≠ 待决策)。
- **Tier 2**(真盲区):**§现状基线**(grounded 真实代码 · 同 prepare/goal decisive 前提核验)· **§错误处理 / 异常路径**(失败语义 · dev 不必现编)· **§简洁性自查**(RD 主动自证防过度设计 · 物化 Architect counter-lens 到起草侧)· **§测试策略层次**(单元/集成/契约 · 哪里要真实 DB/BFF · 治「跨层 mock 盲区」+ 接 v8.178 基线失败集)。
- **blueprint 规范同步**(§3 段名 + §88 Output Contract 结构描述)· 防 spec/模板再漂(v8.170 教训)。

### 验证
- doc(`templates/tech.md` 170→224 · `blueprint-stage.md` §3/§88)· 无 .py 改 · `test_v8_stage_specs` 90 passed · pytest 3 failed(baseline)/ 620 passed。

## v8.180 · ship 确定性自刷 WS 进度块 · 治 yolo 下 WS 文档 stale(软指令没人接住)

> 用户看 yolo ship2:感觉没更新 WS 文档。诊断:① WS 更新本在 **ship1 §3.5 翻牌**(不在 ship2 · ship2 零内容清场)② §3.5 spec 只说「改 WS-NN.md」**没说跑 ws-progress**(v8.174 只接了 emit 没同步 spec)③ planning-backref 门**软**(只看传没传 `--planning-artifacts` · 不校验 WS 刷没刷)→ yolo 自主无人接住 · WS 进度块 routinely stale。

### 改动
- **`ws-progress --feature`**(新):自 feature 的 F-id 在各 ROADMAP「对应F编号」匹配 → 解析**所属 WS**(关联WS · 带 BL→名册反查退路)· 不必报 WS 编号。解析不到 → WARN 跳过(best-effort)。
- **ship archive 确定性自刷**(主修):翻牌后 ship **自动** invoke `ws-progress --feature --write` 刷新 WS 进度块 / 依赖 DAG + 把 WS 文档纳进归档 commit(emit `ws_progress_refreshed`)· **不靠 AI 纪律 · yolo 也一定刷**。
- **§3.5 spec 同步**:翻牌填「对应F编号 = 本 feature F-id」(archive 靠它解析 WS)· WS 进度块**不用手动刷**(archive 自刷)· planning-backref emit 对齐。
- **测试** `test_ws_resolve_v8180` +6(解析 / 名册退路 / 归一化 / CLI)。

### 验证
- code(`state.py` --feature 解析 + `_v8_ship` archive 自刷)+ spec · pytest 3 failed(baseline)/ 620 passed。
