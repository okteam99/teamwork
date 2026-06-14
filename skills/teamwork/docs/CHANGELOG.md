# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.161 · review 外审评本 feature 增量 diff:进 dev 冻结 base 锚 · 治跨 feature 串味 + 超时

> harvest docs/audit/(aifriend 20 条)最高频框架信号:external review 评 `merge_target...HEAD` · 在长 WS / stacked 分支(yolo/ws02)随 deliverable 累积 → ① 跨 feature 串味(B014/B017 实测:一次涌 5 个跨子系统 finding · 本 bug 只占 1 · in/out scope 全靠 AI 自决无工具)② 600s 超时(B016/B017:base...head 全量随 deliverable 增长)。

### 改动(治本:diff base 从「不前进的 merge_target」改「本 feature 的 pre-dev 锚」)
- **进 dev 冻结 base 锚**:`maybe_freeze_review_base`(_v8_engine.py)· stage-complete 进 dev 那刻把 pre-dev HEAD(完成 stage=blueprint/diagnose/blueprint_lite 的 commit)冻进 `state.review_base_commit` · 它在 commit graph 上是 dev HEAD 祖先 → `base...HEAD` **天然排除 prior features**(拓扑无关)。仅首次进 dev 设 · review→dev 回退不覆盖。
- **review 外审默认用增量锚**(state.py)· `base = --base > review_base_commit(仅 review stage · 且校验是目标 commit 祖先)> merge_target(兜底)`。`_is_ancestor`(git merge-base --is-ancestor)失效→透明兜底既有行为 · **绝不因锚点失效而 BLOCK**。
- **审计可见**:emit 加 `base_source`(--base / review_base_commit / merge_target)· prompt 措辞兼容 commit 锚 · `--base` help + init schema 显式化。
- goal/blueprint 评文档不评 diff · 锚逻辑只在 review stage 生效。

### 验证
- 新增 `test_review_base_commit_v8161.py` +11(冻结 4 / 祖先校验 3 / dry-run 解析 4)· pytest 3 failed(baseline)/ 545 passed。

## v8.160 · 全模板瘦身:剥贴在活规则上的版本号 + 删「已移除字段/撤销旧决策/上线计划」考古

> 用户(承 v8.159):查看其他模板是否有 prd.md 同类问题(过时/历史背景)。

### 改动(10 模板 · 同 v8.159 律:剥死历史留 why)
- **剥版本号前缀**(贴在仍有效规则上 · 规则留、`vX.Y` 去):`bug-report`(v8.107×2 / v7.3)· `tc`(v7.3 契约化×2)· `external-cross-review`(v8.19/20/21)· `ui`(v8.17×4 / v8.58 option B×3 / v8.134)· `config`(v7.3.8)· `roadmap`(v8.49)· `必读 cite(P0-11)`×3(browser-test/pm-note/test-report)。
- **删决策/迁移考古块**:`config`「撤销 默认 off 决策」4 bullet(留「改 off 的合理理由」=何时选 off 的 why)+「已移除字段 ship_rebase/ship_policy」+ disable_external_review「改名自…旧名已废弃」(v8.154 已硬改名无兼容)· `external-cross-review`「字段重命名重构」note +「十、启用路线 Week 1-2」上线计划(早物化)· `ui`「旧模板…段已删除」改写为 live 规则。
- **保留 why / live 行为**(不误伤):ui「治本双副本不一致 / 介质 drift」· config archive_on_ship「残留被忽略+WARN」(代码仍读)· 老模式向前兼容 note。
- **假阳性不碰**:host-injection `teamwork-pointer v8.2`(sync-drift.py 解析的功能 marker)· ADR/e2e/workstream「废弃」状态枚举(live 数据模型)· tech 迁移策略段 · config P0-154(live 约束追溯)。

### 验证
- doc-only(模板)· 10 文件 −18 行 · pytest 3 failed(baseline)/ 534 passed(零回归)。

## v8.159 · PRD 模板瘦身:删迁移考古 + 版本演进注 + 「：」artifact · 留有用 why

> 用户(承 v8.158):看下 PRD 模板是否需要瘦身 · 过时内容/历史背景描述。

### 改动(模板 · 删死历史留有用 why)
- **删迁移考古**:「重构(PRD 模板合并 · 原两套)」「删除 prd_variant/business_direction_locked_at 字段」「历史 PRD-REVIEW.md 兼容性段」「方向 A grep + 方向 B brief 对比(P0-73)」—— 填 PRD 的人不需要知道历史上合并过/删过啥/有过哪些方案。
- **删版本演进注**:`v7.3 契约化更新`/`v8.132 删旧 4 视角`/`原 PASS_WITH_CONCERNS`/`+P0-51`/`schema 调整` —— 留规则本身、去「它曾经是什么」。
- **清「：」「／）」artifact**(历史 label 清理留下的悬空符 · ~7 处)· `触发实证` 长 para 压成一行 why。
- **留有用 why**(非可枚举判断的依据 · 不砍):frontmatter 防漂移 / PM 读代码省评审轮 / PRD 不写技术细节 / 三阶段职责正交。
- 384 → 367 行 · verify-ac.py 实测解析正常 · 段结构/schema/checklist 实质全留。

### 验证
- doc-only(模板)· pytest 3 failed / 534 passed(零回归)。

## v8.158 · PRD 模板优化:frontmatter AC 瘦身(去机读冗余 description)· 待决策项移到交付预期下

> 用户:① 机读内容能否用注释在 MD 预览隐藏 ② 把待裁决/已裁决项放交付预期下面方便快读。

### 改动(模板 · 优化人读体验)
- **请求①(机读隐藏)真解 = 去冗余非注释**:核查 `verify-ac.py` 只读 `acceptance_criteria[].id`(+test_refs)· **description 根本不被机读** —— 它在 frontmatter + body §验收标准 重复两份(9 条 AC 的完整 BDD 句子撑爆 GitHub 式预览的 frontmatter 表)。frontmatter 不能注释(parse_frontmatter 要解析)· 故 **frontmatter 只留机读字段**(id/category/priority/test_refs/grep)· **AC 描述/BDD 全文只留 body §验收标准表(人读单源)** —— frontmatter 从 27 行瘦到 17 行 · 消除重复 + 去「改 AC 同步两处」维护税。
- **填写指引转 HTML 注释**(`<!-- -->` 预览隐藏 · 源码可见):§验收标准 / §待决策项 的 schema/规则说明从 blockquote(预览渲染)改注释 —— 真 PRD 预览只见内容不见指引。
- **请求②**:§待决策项 移到 §交付预期**正下方**(原在文档底)· 收待裁决(决策列空)+ 已裁决(决策列填)· 用户读完「做完啥变化」紧接「还需我定啥」· 快读决策面。新顺序:背景 → 用户故事 → 交付预期 → **待决策项** → 验收标准 → …
- 一致性规则更新:frontmatter↔body **id 一致**即可(verify-ac.py 按 id↔TC.covers_ac 校验 · description 不再两处同步)。

### 验证
- doc-only(模板)· verify-ac.py 实测解析瘦身 frontmatter 正常 · pytest 3 failed / 534 passed(零回归)。

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

