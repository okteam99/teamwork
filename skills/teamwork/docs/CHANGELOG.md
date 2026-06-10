# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。

## v8.127 · 仓库减重 55%:删 docs/archive + CHANGELOG-ARCHIVE 清空立「定期清空」制(历史归 git)

> 用户(承 v8.126 体量分析):docs/archive 都删掉 · CHANGELOG-ARCHIVE 清空一版内容 · 定期清空 · 其他先不动。

### 裁定
- 冻结历史的「冷库」职责由 **git 提交历史**承担(永不丢 · git log/show 可溯)· 工作区不再热存 16.3k 行不被读的内容(占仓库 55% · 每次装机同步)。

### 改动
- 删 `docs/archive/`(v8-redesign 00-MANIFESTO / 01-COMMAND-SCHEMA / 04-PAUSE-POINT / 05-LESSONS + DESIGN + change-request · 2,396 行)。
- `CHANGELOG-ARCHIVE.md` 13,867 行(v8.121 → v1 全部 293 条)清空 → 政策 stub · CHANGELOG.md 头部立规:keep-5 轮转 → 归档暂存 → **定期清空**。
- 重指/清理悬空引用 **34 处**:README×2(顺带修 :332 残留「最近 1 版」→「最近 5 版」)· SKILL×4(含路由表归档行删除)· FLOWS / STANDARDS / prepare / goal-stage 各 1 · roles ×8「设计宪法」指针 · 工具 docstring/注释 ×11(state / engine / ship / stage_specs / update)。
- `_v8_engine._render_pause_discipline` 渲染串「📖 详细」改指 **SKILL.md § R5(b)**(现行权威 · 原 04-PAUSE-POINT-DISCIPLINE 已清理)· 同步 `test_pause_discipline_v871` 断言(04 文件名 → R5(b))。

### 验证
- grep 现行 md/py:docs/archive / 00-MANIFESTO / 01-COMMAND-SCHEMA / 04-PAUSE / 05-LESSONS 实体引用 = 0 · pytest 3 failed / 523 passed(零回归 · 含改断言后的 pause 测试)· 仓库 md 总量 29,821 → 13,552 行。

## v8.126 · 覆盖注册处收口单源:DEV-RULES 有则为准 · 没有按当前默认 · 去 KNOWLEDGE 兼容层

> 用户(承 v8.125):「KNOWLEDGE.md 声明为准」改为 DEV-RULES 口径 · 没有则按照当前规范。

### 裁定:覆盖声明唯一注册处 = DEV-RULES.md · 两级链(有声明为准 / 无声明按默认)
- v8.125 为平滑迁移留了「兼容既有 KNOWLEDGE.md 声明」层 · 用户裁定不要兼容层:单一注册处更干净 · KNOWLEDGE 回归纯「项目事实/踩坑」定位(dev-rules 模板边界表)。

### 改动(6 处去兼容)
- STANDARDS.md 全局优先级:兼容句 → 「覆盖声明唯一注册处 = DEV-RULES.md(未声明 → 按 standards 当前默认);KNOWLEDGE.md 不作为规范覆盖注册处 · 既有覆盖声明应迁入 DEV-RULES」。
- backend.md §四 日志 / §五 FK 覆盖条款 + ✅ 条件行 / §六 版本策略:去「兼容既有 KNOWLEDGE 声明」· 统一为「DEV-RULES 声明后以其为准;未声明按本节默认」。
- templates/tech.md FK 决策行示例:「KNOWLEDGE.md L{行号} 已覆盖默认」→「DEV-RULES.md L{行号}」。
- 不动(KNOWLEDGE 正确用途):common.md Gotcha 沉淀 / tdd.md「DEV-RULES(规矩)+ KNOWLEDGE(事实/坑)」分档 / backend §五 撞守卫后记 DEV-RULES/KNOWLEDGE(记坑)。

### 验证
- grep standards+templates+roles:「兼容…KNOWLEDGE」「或既有 KNOWLEDGE」「以 KNOWLEDGE.md 为准」= 0 · pytest 3 failed / 523 passed(零回归)。

## v8.125 · standards 优先级成文:DEV-RULES 为主 · teamwork 默认为缺省 · §三 API 规范挂优先级链

> 用户(承 v8.124):服务端 API 接口规范是否需要优先以 DEV-RULES.md 为主 · 没有再降级成现有规范。

### 诊断:对 —— §三 无优先级链 · 且覆盖注册处两套口径(错档)
- §三 API 规范写成绝对条款(「统一响应格式」「必须遵守」)· 既有项目自有 envelope / camelCase 时直接冲突(违用户主权);v8.119 已为 §五 迁移命名定过「① DEV-RULES → ② 默认」模式 · §三 没挂。
- backend.md 注册处不一致:§四 日志 / §五 FK(×2)/ §六 版本策略的覆盖条款写「以 KNOWLEDGE.md 为准」(4 处)· 而 dev-rules.md 模板边界表明文「强制开发规矩 → DEV-RULES.md;踩坑/客观约束(AI 沉淀)→ KNOWLEDGE.md」—— 格式/策略类覆盖被错档进 KNOWLEDGE。
- STANDARDS.md 无全局优先级声明 · tdd.md §二 Step 3 也只提 KNOWLEDGE。

### 改动
- **STANDARDS.md 加全局优先级**(根治):项目/子项目 DEV-RULES.md(用户主权 · 人维护)> standards 默认 —— standards 是「未规定时的缺省」不是法律;存量对外契约一致性优先 · 沿用时**提示用户**固化进 DEV-RULES(AI 不代写 · 模板红线);兼容既有 KNOWLEDGE 声明 · 新增覆盖一律 DEV-RULES。
- **backend.md §三 挂优先级链**:① DEV-RULES API 约定 → ② 存量服务已有一致接口风格 → 沿用(对外契约 · 同服务一致性 = 正确性 · 新接口不得自创风格)+ 提示用户固化 → ③ 全新/无约定 → teamwork 默认。📎 注明与 §五 migration「不读邻居」的区别:迁移文件名 = 内部惯例(坏样板不传染);API 响应结构 = 对外契约(消费方依赖)→ 存量在 ② 合法沿用。
- **覆盖注册处统一 DEV-RULES**(4 处 · 全部兼容既有 KNOWLEDGE 声明):§四 日志格式 / §五 FK 覆盖条款 + ✅ 条件行 / §六 版本策略。
- tdd.md §二 Step 3:「遵循 KNOWLEDGE.md 项目特定规则」→「遵循 DEV-RULES.md(强制规矩)+ KNOWLEDGE.md(项目事实/坑)」。

### 验证
- pytest 3 failed / 523 passed(baseline 3 · 零回归)· grep:standards 内「以 KNOWLEDGE.md 为准」独立口径 = 0(全部改为 DEV-RULES 主 + KNOWLEDGE 兼容)。

## v8.124 · backend.md 同款体检:TDD fork 收敛 + 通用示例删除 + Date.now 腐坏修复(规范主体保留)

> 用户(承 v8.123):后端规范也看下。

### 体检结论:与 frontend 病情不同 · 主体是真规范 · 不大砍
- 781 行中 §三 响应契约 / §四 日志门禁(承载契约字段的 ✅/❌ 对照示例)/ §五 迁移+FK 策略(单源)/ §六 版本管理 / §二 集成测试报告模板+失败处理 都挂着 teamwork stage/角色语义 → 保留。
- 病灶三处:§一「开发流程(Red-Green-Refactor)」是 tdd.md 的**未注册 3 步 fork**(缺 VERIFY RED/GREEN · 与 frontend 同款漂移);§二 两段通用 python 验证示例(检查项树已承载规则 · 示例还带 `.json[` 腐坏);§四 示例 **`Date.now` ×3 丢空括号**(同 e1d12b2 事故 · 此前扫描正则未覆盖 `now`)。

### 改动
- §一 fork → 1 段 cite tdd.md(后端差异仅 pytest / npm test / go test 命令)· tdd.md §七 引用约定表补 backend.md 行 · 保留覆盖率 >80% + 测试命名规范。
- §二 删两段通用 python 示例(检查项树保留)。
- §四 修 `Date.now()` ×3。
- 头部加载指引补 tdd.md + 「通用教程不入库」哲学行(注明边界:保留的 ✅/❌ 示例仅限**承载契约/门禁字段**的对照 · 区别 frontend 教程类全删)。
- 全仓腐坏复扫(`Date.now`/`.json[`/`jest.fn`/`Math.random` 缺括号):仅 backend.md 7 处 · 本版全清。

### 验证
- pytest 3 failed / 523 passed(baseline 3 · 零回归)· backend.md 781 → 719 行 · 全仓空括号腐坏 grep = 0。

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
