# Changelog Archive

> 📦 **定期清空**:本文件只暂存从 [CHANGELOG.md](./CHANGELOG.md) keep-5 轮转出的条目 · 膨胀时整体清空 —— 完整历史 = **git 提交历史**(永不丢 · `git log` / `git show` 按需追溯)· 工作区不热存。
> 上次清空:**v8.127**(2026-06-10 · 清除 v8.121 → v1 全部 293 条 · 约 13.9k 行)。

---

## v8.122 · MD review P1:frontend.md 瘦身 1684→166(guide 外迁)+ TDD 单源收敛 + 降级路径划清 + 数字宣称校验物化

> 用户:继续 P1(承 v8.121 全量 MD review 顺延项)。

### 诊断
- frontend.md 1684 行 · §二–§七 为教程式内容(选型对比/配置/示例)与 standards「must/must-not」定位不符 · subagent 默认加载即超载;且全文示例代码曾在一次历史格式清理中丢失全部**空括号 `()`**(`jest.fn()`→`jest.fn` · `() =>`→` =>`)· 文末悬空 ``` 破栅栏。
- §一「前端 TDD 流程」是 tdd.md(自称唯一权威源)的**未注册 fork**:4 步 vs 5 步(缺 VERIFY RED)· 示例腐坏 · tdd.md §七 引用约定表无 frontend.md 行。
- e1d12b2 清 v7 残留的同次事故还留 **7 处全角「Ｔ」脏标题**(tdd.md ×2 / adr.md ×3 / prd.md / common.md · v8.121 只修到 frontend/backend 标题 2 处)。
- review-stage「真超时重试失败 → 报因给用户」vs「异质不可用已重试失败 → 降级」边界未划清:持续限流超时归哪条两可 · AI 会在停报与降级间摇摆。
- v8.121 类数字宣称漂移(stage 数/版本徽章/gate 名)无物化校验 · 只靠人工 grep。

### 改动
- **frontend.md 瘦身 1684 → 166 行**:§二–§七 原文(决策树+示例)整体外迁新 `standards/frontend-guide.md`(按需查阅 · 不默认加载 · 头部声明历史损坏:箭头参数括号已批量修复 35 处 · 其余空调用括号待逐例修)· frontend.md 各节改硬规则 bullets +「📎 示例 → guide §N」指针 · 修文末破栅栏 · STANDARDS.md 注册 guide + 加载规则注明按需。
- **TDD 单源收敛**:删 frontend.md「前端 TDD 流程」fork(腐坏示例直接删 · 不外迁)· 改 1 段 cite tdd.md(§二 5 步 + §三 自检 · 前端差异仅 vitest 命令 + 组件测试先行)· tdd.md §七 引用约定表补 frontend.md 行。
- **脏字符清零(7 处)**:tdd.md「horizontal slicing（借鉴 mattpocock/skills tdd）」「NEVER refactor while RED（借鉴同上）」· adr.md 三条门槛 / 7 类列表 / 极简模板 · prd.md「Out of Scope（借鉴 …to-prd）」· common.md「调试日志规范（借鉴 …diagnose）」。
- **降级路径划清**:review-stage —— 串行重跑**仍**超时/空输出(环境性)→ 归入「异质客观不可用」走**显式降级**(合法继续 · 报因留痕);🔴 P0-154 禁的是「伪造/冒充/静默跳过」· 不是降级协议本身。客观不可用枚举两处同步补「持续超时·限流(串行重跑仍失败)」(review-stage + external-model-usage §11.5)。
- **数字宣称校验物化**:新 `tools/tests/test_spec_claims.py` 4 测 —— STAGES.md 索引 == STAGE_SPECS 全集 ·「N stage」宣称 == len(STAGE_SPECS) · README 徽章 major.minor == SKILL frontmatter(patch 不比 → auto-bump 免疫 · README 缺失〔安装副本〕skip)· 现行 md 的 cold_start_* gate 名必存在于 bootstrap/state 源码。负验证:regex 实测命中 5 处 stage 宣称 + 4 处徽章(非空匹配白过)。
- **bump 脚本(P1 项裁定不改)**:auto-bump 只动 patch 段 · 徽章语义 = major.minor → patch bump 不产生漂移;真实漂移向量 = **人工 minor bump 忘改 README** → 由上述 pytest 拦截(发版必跑)· 改 bump 脚本属误靶。

### 验证
- pytest **3 failed / 523 passed**(baseline 3 = scan-spec 既有 · +4 新校验全过 · 零回归)· 全仓现行 md/py「Ｔ」= 0 · frontend.md 1684 → 166 行 · guide 1554 行(§二–§七 原文零丢失 + 35 处箭头修复)。

### 顺延
- frontend-guide.md 示例**空调用括号**逐例修复(`jest.fn;` 类 · 已头部声明)· scan-spec-consumer 3 个 baseline failed 测试治理。

## v8.123 · 裁定删除 frontend-guide.md:通用教程不入库 · 知识归模型 · 规则已全在骨架

> 用户(承 v8.122):frontend-guide.md 是否有必要 · 或是否需要精简 → 委托裁定(「你觉得怎么处理合理」)。

### 裁定:删除(非精简 · 非保留)
- **消费者是 AI RD · 内容零增量**:1554 行中 90% 为代码栅栏(452 行通用决策树 + ~950 行示例)· 全是 Testing Library / MSW / Zustand / TanStack Query / WCAG / Vite / GH Actions 通用用法 = 模型训练数据常识;AI 需要示例时自生成的比腐坏样例(仍残 ~20 处空调用括号)质量高。
- **规范零丢失**:数值门禁 / 禁项 / 选型默认已 100% 在 frontend.md 骨架(v8.122 提炼)。
- **框架哲学对齐**:v8.114 三层律 teamwork 不 own 知识内容(防腐烂反向误导)· 通用教程无归属层 —— 项目特异归各项目 `DEV-RULES.md`(用户主权)· 通用知识归模型本身。精简成决策树版只把负资产变小 · 不解决归属。
- **可逆**:原文完整在 git 历史(v8.122 commit 8a76a43)。

### 改动
- 删 `standards/frontend-guide.md` · frontend.md 去 7 处 guide 指针 + 头部加「实施示例/选型教程不入库」哲学行(防未来被加回)· STANDARDS.md 去注册行 + 加载规则还原。
- 撤销 v8.122 顺延项「guide 示例空调用括号逐例修复」(随删除作废)。

### 验证
- grep 全仓 frontend-guide 引用 = 0(CHANGELOG 历史除外)· pytest 3 failed / 523 passed(baseline 3 · 含 4 项 spec 宣称校验 · 零回归)。
