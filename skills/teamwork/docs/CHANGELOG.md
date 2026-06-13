# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

