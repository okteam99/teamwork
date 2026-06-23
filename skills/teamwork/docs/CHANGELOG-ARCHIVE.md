# Changelog Archive

> 📦 **定期清空**:本文件只暂存从 [CHANGELOG.md](./CHANGELOG.md) keep-5 轮转出的条目 · 膨胀时整体清空 —— 完整历史 = **git 提交历史**(永不丢 · `git log` / `git show` 按需追溯)· 工作区不热存。
> 上次清空:**v8.127**(2026-06-10 · 清除 v8.121 → v1 全部 293 条 · 约 13.9k 行)。

---

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
## v8.175 · ui_design「扩已有页」复现门:设计稿基于真实代码整页复现 · 禁概念页

> 实证 AON Offer-Analysis case:feature 给已有真实页 `/analytics/offers` 加 tab,ui_design 却产出孤立**概念页** —— 只画新 tab、没按真实代码复现整页(筛选区 / KPI·funnel·trend / Top card 位置),用户判「设计稿不完整、和实际不一致」打回重做。根因:规范的「在已有全景上增量补」**默认那张页早被规划期 seed 进 preview-project**;brownfield(扩已有页、规划期没 seed 这张)时「增量」无所补、「首次 seed」又没说「按真实代码复现整页」→ AI 画了概念页。

### 改动
- **§3 复现门**(ui-design-stage.md · 主修):扩已有真实页时设计稿单位 = **整张页** —— ① 读该页真实组件/路由源定当前形态(grounding 同 prepare/goal 核验真实文件)② preview-project 按真实形态复现整页(same-stack 直接复用真实共享组件 → 保真)再集成新部分 · 🔴 **禁「概念页」**(只画新控件不复现真实页结构 = 局部 = 评审/用户看不出落地效果)。
- **§1 判定**:加载上下文时先判「扩已有页 vs 全新页」· 扩已有页 → 必读真实代码当前形态作 grounding。
- **brief 同步推**(v8.170 铁律 · 治「模型不主动复现」):`_ui_design_brief` 加「扩已有页→复现整页·禁概念页」一行 —— spec 改了 brief 必跟,否则规则躺 doc 被跳过。
- **brief 断言测试** `test_ui_design_brief_v8175` +3:锁 brief 携带复现门 + 回归护栏(v8.170 的 UI-RULES/dev顶栏不许被挤掉)· 补上 v8.170 漏建的 brief-content 测试洞。

### 验证
- doc(ui-design-stage §1/§3)+ brief(`_v8_stage_specs`)+ test · pytest 3 failed(baseline)/ 576 passed。
## v8.174 · WS 进度可见:ws-progress 自 ROADMAP 派生 rollup + frontmatter 藏注释去 YAML 墙

> 用户(看 TermPro WS-01 文档):WS 有模板么 · 内容有点乱 · 没有进度标识。诊断:① frontmatter 被渲染器当正文显示成 YAML 墙 + 与 body 章节重复(乱)② `features[].status` 只是规划态、执行态从不上卷到 WS · 要翻 5 个子项目 ROADMAP 交叉比对才知进度(无进度)。

### 改动
- **ws-progress 命令**(`state.py` · 进度派生 · 不手抄):glob 全仓 `ROADMAP.md` · 按「关联 WS」列过滤 · 确定性汇总成「X/N 已完成」rollup + 总览表(BL/子项目/功能/状态/当前阶段/F)· `--write` 写回 WS 的 `<!-- WS-PROGRESS:START/END -->` 标记区。执行态**单一源仍在 ROADMAP**(职责单一)· WS 只读派生 —— 防 stale 双源。按列名定位解析、容列序差异、扫一文件多表、容裸数字 `--ws 1`。
- **frontmatter 藏进 TEAMWORK-MACHINE 注释**(同 PRD v8.165):workstream.md 机读/元数据契约外壳 `---` → `<!-- ... -->` · **字段全保留**(零悬空引用 · features[].current_state 等仍在)· 但 TermPro/Zed 不再当正文渲染成 YAML 墙(治「乱」主因)· body 章节成唯一可见权威。
- **三处消费点接好**(v8.151 消费时点主动推):feature-planning Step 7(写完 ROADMAP 首刷)+ ship `planning-backref`(翻 BL 牌后刷 · 顺序:WS 派生自 ROADMAP)+ 模板 §feature 总览(刷新命令 + 🔴 勿手改)。
- **WS 状态 ≠ feature 进度** 澄清:规划生命周期(📝→✅ 规划完成)与执行进度(建到哪了)是两维 · 模板状态生命周期 + 设计要点 #8/#9 写明。

### 验证
- code(`state.py` +ws-progress · `_v8_ship`/`feature-planning` 钩子)+ doc(workstream.md 重构)· `test_ws_progress_v8174` +12(解析/过滤/rollup/裸数字/写回幂等)· pytest 3 failed(baseline)/ 573 passed。
## v8.173 · 重点 review 指引改两层 + 选择题 + 说人话 · 治「读起来难」

> 实战(aon auth case · 用户):v8.168「冷审逐条全列」的导读**读起来难** —— 13 条 external ADOPT 和 4 条用户决策**平铺等权**(决策被淹)+ 代码 id(CR-1/PL-2/R-8/AC-12/Q3)当正文(逼用户回翻 PRD,而导读的意义就是不用回翻)。

### 改动(goal-stage §8 重点 review 指引模板)
- **第一节拆两层**:🟡 **你要拍板的**(REJECT/DEFER/升级 = AI 替你判断/升级 · 抽查 ROI 最高)+ ✅ **已处理**(ADOPT · 备查可跳)—— 决策不再被 ADOPT recap 淹。
- **决策写成选择题**:`<一句话背景> —— A)… / B)… · 我倾向 X(理由)` · 不再埋在 prose 末尾。
- **说人话**:CR/PL/AC/R/Q/v 等代码 id 挪进括号当 ref · 不当正文(导读要让没读过 PRD 的人也看懂)。
- **已处理压主题**:external N 轮压成「主题一句 + 共 M 条」· 不逐个 spell CR 码。🔴 **compact ≠ collapse**:压主题保留了「抓到什么」(substance)· 禁的仍是 v8.167 藏 substance 的「全部 ADOPT」。
- 反模式同步更新(平铺等权 / 代码当正文 / 没写选择题 / collapse 藏 substance)。

### 验证
- doc-only(goal-stage.md)· 无测试 pin 旧文案 · pytest 3 failed(baseline)/ 561 passed。
## v8.172 · harvest P0 四修:耗时区分等用户 + 补 add-concern + review-fix 推进 target + 截图兼容

> harvest docs/audit/(31 done 记录 · 3 项目)的高频框架反馈,四个干净 bug:

### ① v8.166 耗时统计把「等用户」当工作(5× · 我自己加的功能数据立刻打脸)
pm_acceptance 在多条记录占 84%/87%/73% —— 全是等用户拍板墙钟,非阶段内工作。`_stage_durations` 现**区分工作阶段 vs 用户决策等待**(`_AWAIT_USER_STAGES={pm_acceptance}`):最耗时只在工作阶段算,pm_acceptance 单列「用户决策等待(墙钟·不计入)」。治「误判验收环节慢」。

### ② `state.py add-concern` 命令重新实现(3× · doc/impl 漂移)
SKILL/goal-stage 多处引用 `add-concern --severity WARN --message`,但命令曾被误删 → AI 想记 incidental-scope concern 失败,只能塞 commit message。重加命令(append `state.concerns` · choices WARN/ERROR/INFO)+ 改 state.py 删除说明的 stale 注释。

### ③ review-fix 推进 review target 到 fix commit(3× · v8.161 姊妹 bug)
review-fix 写 `rounds[-1].fix_commit` 但不更新 `stage_contracts.<stage>.auto_commit` → 下轮 external-review 默认锚 pre-fix 树 · 报 stale finding 引旧行号(实证 ADMIN-Offer-Detail/ANDROID-F017/INFRA-F018 都要手动 `--commit HEAD`)。现 review-fix 同步推进 auto_commit。

### ⑥ playwright MCP 截图目录兼容(2× 连续)
MCP allowed-root 只能写 `<主仓根>/.playwright-mcp/`,写不了 §12.5 约定的 temp 目录 → 截图漏落主区。conventions §12.5 文档化:用 MCP 时 `.playwright-mcp/` 即可接受的自检截图目录(+ gitignore)· 别跟沙箱较劲。

### 验证
- 新增 test_add_concern_v8172 +4 · test_audit_timing 更新 + 等用户分离测试 · pytest 3 failed(baseline)/ 561 passed。
## v8.171 · 修 TEAMWORK-MACHINE marker 自闭合 · 机读块在预览又裸露了

> 实测(TermPro 编辑器 · 用户):PRD 机读块**仍裸露在预览**。根因 = v8.165 我自己埋的:marker 行写了「保持 `<!-- -->` 包裹」—— 那个**字面 `-->` 提前闭合了 HTML 注释**,浏览器在第一个 `-->`(描述文字里)就结束注释,后面 YAML 全可见。讽刺:v8.165 隐藏机读内容的目标被它自己 marker 的描述文字破坏了。

### 改动
- **模板 marker 行去掉字面 `<!-- -->`**(`保持 <!-- --> 包裹` → `勿删外层注释包裹`)· 注释现在是单个 well-formed HTML 注释 · 第一个 `-->` 即真正闭合 · YAML 全在注释内(预览隐藏)。
- parser **不受影响**(verify-ac/engine 用 `[^\n]*` 读 marker 行 · 只有渲染器在意 `-->`)· 实测仍抽到 AC + revision_history。
- 加防回归测试 `test_no_premature_comment_close`:模板 marker 到第一个 `-->` 之间必含完整 YAML(feature_id + revision_history)· 防再有人在 marker 写字面 `-->`。

### 边界 + 验证
- **存量 PRD**(已生成的 · 如 ADMIN-Offer-Analysis)copy 了破损 marker · 仍裸露 · 需各自把 PRD marker 行的 `<!-- -->` 删掉(一行)或重生成。
- doc+test · pytest 3 failed(baseline)/ 556 passed(+1)。
## v8.170 · ui_design brief 补 UI-RULES/rubric/dev顶栏 · 治 spec 改了 brief 没跟

> 用户 QA:UI-RULES 自动建么 · stage 和 brief 匹配么。查出真缺口:v8.167/169 只改了**被动躺的 spec**(ui-design-stage.md),`_ui_design_brief`(stage-start **主动推**的那段)完全没提 UI-RULES/rubric/dev顶栏 —— 违 v8.151「消费时点主动推 · 防 spec 只被动躺 doc」。

### 改动
- **`_ui_design_brief` 加两行主动推**:① 设计前读 UI-RULES(workspace + 子项目两层 · 缺则从 templates 建)+ 对照 § 交互&视觉 rubric(治降智)② same-stack 设计=代码:预览工具走 dev 顶栏 · 页面零预览痕迹(禁内嵌 switcher)。
- **子项目 UI-RULES 自动建说明**:workspace `project-specs/UI-RULES.md` 由 bootstrap 自动建;子项目 `{子项目}/docs/UI-RULES.md` **不自动建**(同子项目 KNOWLEDGE/DEV-RULES · bootstrap 时不知子项目清单)· 改由 brief 主动提示「缺则建」(首次 UI 工作时按需建)。

### 验证
- code(brief string)· brief 渲染含 UI-RULES/rubric/dev顶栏/零预览痕迹 · pytest 3 failed(baseline)/ 555 passed。
## v8.169 · UI 规范包:UI-RULES 两层 + 同构按介质拆 + preview dev 顶栏(设计=代码)

> 用户:① 子项目要有放 UI 设计规范的地方(全局 + 子项目两层 · 颜色主题/优先控件)② 设计稿要和实际代码完全一致 ③ 全景顶部全局导航条放每页测试入口。实证 AON Admin:Data/Loading/Empty/Error 切换器**内嵌在页面里** = 真实 app 没有它 = 设计 ≠ 代码。

### 改动(三件一版)
- **UI-RULES 两层**(人维护设计规范 · 同 DEV-RULES 模式):`project-specs/UI-RULES.md`(workspace 共享设计语言)+ `{子项目}/docs/UI-RULES.md`(子项目特有)· 装**策略/约定**(控件偏好/色板策略/交互约定/a11y/copy)· 🔴 **不装视觉值**(hex/px 在 preview-project tokens · markdown 复述必 drift)。`templates/ui-rules.md` + bootstrap 建空骨架 + conventions §13 登记 + ui_design substep1/rubric cite。
- **分层同构律按介质拆**(修订 v8.134):**same-stack → 完全一致**(页面内容从共享组件渲染 · 零预览痕迹 · 设计=代码是「构造保证」非人肉对齐 · 删「像素自由」口子)· **static-html → 仅参考**(介质差异不可像素仿)· 权威至 ship 止保留(time-authority · 不改永远同步 = 不重引双维护)。
- **preview dev 顶栏**(治「设计≠代码」根因):预览工具全外置到 **dev-only 全局顶栏**(页面区→route_path · 状态区→Data/Loading/Empty/Error 测试入口)· 页面内容**禁内嵌 switcher** · 状态由顶栏 mock-data provider 驱动 = Storybook 模型(顶栏选页×状态 · 画布渲染干净组件)· 不违 IA 镜像。Designer 自查加「状态走顶栏」。

### 验证
- code+doc(7 文件)· test_bootstrap 骨架清单 +UI-RULES(setUp + 3 断言)· pytest 3 failed(baseline)/ 555 passed。

## v8.168 · goal 重点 review 指引:冷审逐条(每条 NEEDS_REVISION 一句话+结论)· 禁 collapse

> 实战(ADMIN-Offer-Management):重点 review 指引第一节把 QA/PL 的 NEEDS_REVISION **collapse 成一句「全部 ADOPT」**,藏掉了 reviewer 实际发现了什么。用户:逐条列、每条一句话通俗总结 + 结论。

### 改动(goal-stage.md Substep 8 指引模板)
- **第一节「替你做的判断」(只 REJECT/DEFER · collapse)→「冷审逐条」**:每条 NEEDS_REVISION finding 一行 = `[角色] 一句话问题(通俗)→ ✅ADOPT 改了啥 / 🔴REJECT 理由 / 🟡DEFER 去哪`,**全列不 collapse**。
- **🔴REJECT/🟡DEFER 标「重点抽查」**(AI 判断替代了 reviewer 建议 · ROI 最高)—— 保留原「替你做的判断」抽查重心,但不再藏掉 ADOPT 的实际发现。
- 配套:intro「每节 ≤2 行」→「首节逐条 + 余 5 节 ≤2 行」· rationale 更新 · §质量基线加反模式「多条 finding collapse 成『全部 ADOPT』= 藏掉 reviewer 发现 · 必逐条列」。

### 验证
- doc-only(goal-stage.md)· 无测试 pin 旧文案 · pytest 3 failed(baseline)/ 555 passed。

## v8.167 · ui_design 加交互 & 视觉质量 rubric · 治「对交互没判断力」

> 实战反馈(Deli Yang · teamwork+Codex):涉交互改动效果「降智」· 模型对交互体验没判断力 · 要人逐条纠正。诊断坐实:designer 角色 ~90% 讲全景生产/预览机制 · ~0% 讲「什么是好交互」(§交互流 只是段落标题无 rubric)· 模型既无 taste 又无 rubric → 必然 generic。Qianliu 提「找设计 skill 吸收」—— 对,但吸收知识不吸收 skill(Codex 调不了 Claude/gstack skill)。

### 改动(吸收设计判断 · host-agnostic)
- **ui-design-stage.md 加 § 交互 & 视觉质量 rubric**(单源):**A 交互状态**(反馈 hover/active/focus-visible/loading 骨架/success · 完备态 normal/empty/error/disabled · 可恢复 · 边界退化 · 触控 ≥44px)+ **B 视觉地板**(排版/颜色 WCAG/间距 · **对照既有系统不自造**)+ **C 文案**(用户视角命名/active voice/全流程同名/error 当指引)。
- **蒸馏自 `design-review`(交互状态/排版/颜色/间距 80 项)+ `frontend-design`(copy)**· 🔴 **按「扩展既有 app」裁剪**:品牌独特性 ethos **只在全景首版/greenfield 用** · per-feature 要一致不要独特(不 cargo-cult)。
- rubric = **设计/dev 还原/评审同一基准**:Designer 起草逐条过 · §5 预览前自查 A 段 · reviewer 对着审(防凭空 generic)。designer.md §交互流 + cite 清单 cite 它。

### 边界 + 验证
- rubric 治「可枚举」那层(状态/反馈/边界/约定)· 真正的 taste/delight 仍归 §5 用户预览(框架给不了品味 · 但能让模型不交 generic 半成品)· Claude Code 额外可委托 design-review 跑 live QA(增强非依赖)。
- doc-only(ui-design-stage.md +25 / designer.md)· pytest 3 failed(baseline)/ 555 passed。

## v8.166 · audit 记录加各阶段耗时 + 耗时分析 + 主对话模型

> 用户(看 TermPro audit 截图):实际数据该加 ① 各阶段耗时 ② 耗时分析 ③ 主对话用的模型 —— 让 harvest 能按阶段/按模型分析流程质量,不只看总时长。

### 改动(audit 生成器 · _v8_ship.py)
- **各阶段耗时**(确定性抽):`_stage_durations` 从 `stage_contracts[*].duration_minutes` 渲染「goal 22m · blueprint 28m · dev 41m · …」(completed_stages 顺序)。
- **耗时分析**(确定性):阶段总和 + 最耗时阶段及占比(「阶段总和 160m · 最耗时 dev 41m(26%)」)· 与总时长差 = 阶段间等待。
- **主对话 host + 模型**:host 从 `state.host`(确定性)· 精确 model 由 PMO 在 `ship-finalize --main-model` 声明(它知道自身 model · state 不记)· 缺省只记 host。
- 配套:`--main-model` 加到 **ship-finalize** parser(非 ship-phase · 两个 subparser 别搞错)· ship-stage.md SOP + docs/audit/README 同步。

### 验证
- 新增 `test_audit_timing_v8166.py` +4(breakdown 顺序 / 最耗时% / 跳无 duration stage / 空兜底)· ship-finalize --help 实测含 --main-model · pytest 3 failed(baseline)/ 555 passed。

## v8.165 · PRD 机读契约搬进 `<!-- TEAMWORK-MACHINE -->` 注释块:所有渲染器都隐藏

> 用户实测(TermPro + Zed 双截图):YAML frontmatter 在 **Zed / GitHub 等主流渲染器不隐藏** · 机读 AC 裸露在 PRD 预览顶部 = 冗余。v8.158「机读内容预览隐藏」赌的是「frontmatter 被隐藏」· 但现实只有 frontmatter-aware 渲染器隐藏 → 目标对 frontmatter 没达成。「修 viewer」行不通(改不了 Zed)· 只能产物侧治。

### 改动(选 C·彻底隐藏·非半截瘦身)
- **机读契约从 YAML frontmatter 搬进 `<!-- TEAMWORK-MACHINE ... -->` HTML 注释块**(所有渲染器都隐藏 HTML 注释)· PRD 预览只剩人读正文 · 顶部零机读裸露。
- **两个解析器优先读注释块 · 兜底 `---` frontmatter**:`verify-ac.extract_frontmatter`(re · 行首锚定)+ 引擎 `parse_frontmatter`(str · 行首锚定)。`frontmatter_required` + `revision_history` 两个 goal-complete 门都走引擎 parse_frontmatter · 改一处全覆盖。
- **兜底不破**:in-flight PRD(TermPro/aifriend 现存 `---`)+ 其他产物(TC/PRD-REVIEW 仍 frontmatter)走兜底分支 · 零破坏 · 平滑迁移(新 PRD 用注释块 · 旧的继续跑)。
- 模板 AC 块顺手修成合法 2 空格 YAML(原 1 空格 illustrative-malformed)+ 补 revision_history 例 + 行首锚定防 prose 字面引用误命中。

### 验证
- 新增 `test_machine_block_v8165.py` +6(引擎读注释块/兜底/两者无→None/注释块优先 · verify-ac 抽注释块/兜底)· 模板块 PyYAML 合法 + grep_keyword `\|` 字节完好 · pytest 3 failed(baseline)/ 551 passed。

## v8.164 · PRD 模板三层 + 挑衅式开放区:必填核/按需/开放区显式 · 既有行为侦测提成主动挑衅

> 设计讨论结论(③④⑤+① 接力):模板该分「必填核(消费测试过)/ 按需 / 开放区」· 开放区给结构没问到的留逼判断的尖问题(非空白自由发挥)· 既有行为变更从待决策项里的被动 HTML 注释提成开放区的主动必答挑衅。

### 改动(prd.md 产物层 · 零代码)
- **③ 三层显式**:intro 改成「必填核(背景/用户故事/交付预期/待决策项/验收标准/Out of Scope)· 按需(流程图/埋点/消费方分析)· 开放区」· 消费测试定档(工具或下游真读 → 必填核)。
- **④ 挑衅式开放区**(`## 开工前必须想清的`):**可见**挑衅 4 问(🔁既有行为 / 🧱隐藏前提 / 🌊跨子系统涟漪 / ❓最不确定)· 「至少 1 实质 or 显式『无+理由』」· **人读 · 机器禁入**(无机读字段/不被 grep)· 冷审查是否过场。
- **⑤ 既有行为:被动注释 → 主动挑衅**:侦测(改了既有默认行为吗)提成开放区必答 🔁 · 后果(命中 → 必入待决策项让用户拍板)留刚性核(待决策项注释剥成「刚性后果」)。治 TermPro「8 轮打磨错前提」的结构成因。
- **① 残留接力**:必填核标「PRD 的脊 = prepare 已确认的意图(🎯/📦/🔁)· 起草不得偏离 · 冷审据此核对」· 防 goal 起草 re-drift(① 主体已被 v8.162/163 prepare 意图门吸收 · 不另建门)。
- goal-stage.md step 2 结构列表同步加 §开工前 + 修正段序对齐模板。

### 验证
- doc-only(模板)· prd.md 367→381(+开放区)· verify-ac 实测解析正常(开放区不碰机读)· pytest 3 failed(baseline)/ 545 passed。

## v8.163 · prepare 意图门 🧩 假设加硬约束:只列意图解读 · 禁抛未验证代码猜测

> 承 v8.162 · 用户追问「prepare 前会读代码查事实么」暴露的洞:prepare 在强制读代码**之前**(§1.5.3 代码现状可选 · 强制深调研在 goal step-1)· 故 🧩 暴露的假设只能基于用户的话 · 若 AI 在此抛**猜的代码事实**(「我假设后端有 X 列」)= 让用户确认 AI 本该去查的事(正是 §1.5.3「代码现状只写已验证事实」+ 反模式 #7 已防的洞 · v8.162 的 🧩 措辞没把这纪律带进去)。

### 改动(prepare.md §4 · 一句硬约束)
- **🧩 只列「我假设你想要 X」类意图解读假设**(用户域 · 用户能直接拍)· **禁抛未验证代码/可行性猜测**(留给 goal 调研后的深门 · 或先验证再写)。
- 把浅/深意图门分工说干净:prepare 🧩 = 「我假设你**想要**什么」(意图 · 读代码前 · 用户拍)· goal 深门 = 「我读代码**发现**了什么、它怎么重塑意图」(现实 · 调研后 · 如 CPS-F003 后端 GAP)。

### 验证
- doc-only(prepare.md · 模板 🧩 行 + footnote 各一句)· pytest 3 failed(baseline)/ 545 passed(零碰)。

## v8.162 · prepare 暂停点信噪比反转:意图确认提到最前(暴露补的假设)· 执行 setup 塌一行

> 设计讨论结论:意图 fidelity(我们有没有理解对你要什么)只能由用户校验(用户是自己意图的唯一 oracle)· 而 prepare/triage 是规划→执行的那层膜 —— 这个唯一不可转移的校验该锁在前门。旧 prepare 暂停点领头是执行 setup(被 `ok` 盖章)· 把意图埋成一行 restatement → 误读搭便车溜过(实证 TermPro 前提盲:8 轮打磨错前提)。

### 改动(prepare.md 暂停点重排 · 同一处编辑解两个诉求)
- **意图确认提到最前**(`# 🎯 我的理解`):🗣️ 用户原话 + 🎯 理解 + **🧩 我补的假设**(摊开「你没说、我替你补的」= 抓误读核心零件 · 干净 restatement 会把假设藏起)+ 📦 范围 + 🔁 既有行为。**数据全是 prepare-check 已采的**(`--user-intent` + `--admission-judgment.ai_rationale`)· 只是从「目标概述」reframe 成「暴露假设的确认」。
- **执行 setup 塌一行**:旧 5 段(流程概览/评审角色表/上下文/Worktree/4 项配置)· 派生值多、用户盖章 → 配置一段 + 评审一行(各 stage-start 会再 emit · prepare 重列 = 噪音)+ 上下文**仅异常出**(上游未就绪/撞号/Planning 未 ship · 全绿不显)。
- **风险分级**:请求一清二楚 → 🧩 写「无补」秒过;含糊/大范围/改既有行为 → 摊假设让用户校(短指令恰是误读高发区)。
- 配套改自身护栏:§0.5 反模式 #6 / 自检 #5 / §4.1 自检 / §1.5 喂数据引用 / state.py `reviewer_thinking_hint`(评审思考结果进默认 · 不铺表)· prepare.md 459→417。

### 边界 + 验证
- 这是**浅意图门**(prepare · 调研前 · 拦粗误读)· **深意图**(goal 调研后才浮出的形状)是 goal 侧后续。
- doc + 1 hint 字符串(测试断言的 pl 默认保留/不要直接抄/F-Bv2-8 全保留)· pytest 3 failed(baseline)/ 545 passed。

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

## v8.152 · posture hint 两个方向都摆明实证:REJECT 也点名给理由(修 v8.151 自身不对称)

> 用户:REJECT 也要给理由。

### 诊断:v8.151 hint 矫枉过正 · 又写歪了对称
- v8.150 治的是「ADOPT 欠防」· v8.151 把姿态推进 brief 时**只把「ADOPT 也要给实证」摆明**· REJECT 的举证只剩抽象一句「举证责任对称」—— 讽刺地犯了 v8.150 要治的同款不对称(具体摆明的只有一侧)。doc 侧(§12.1 表 / pm_response schema)本就两侧都全 · 是 brief 字面歪了。

### 改动(代码 + 测试)
- **`_FINDING_POSTURE_HINT` + `_review_brief` 姿态行**:从「ADOPT 也要给实证」改为「**两个方向都必给实证**」并各自点名 —— ADOPT 给「为何确为真+为何这样改对」· REJECT 给「为何不是问题(指真实代码/规约/目标)」·「reviewer 说得对」与「我觉得没事」都不是理由。
- 测试断言更新(校验两侧都摆明 · 非只抽象「对称」)。

### 验证
- pytest 3 failed / 529 passed(baseline 3 · 零回归)。

## v8.151 · finding 质疑姿态进 brief:消费时点主动推 · 防 v8.150 spec 只被动躺 doc

> 用户(承 v8.150):相关的 brief 是否要有对应的提示。

### 诊断:spec 被动 · brief 主动 —— 防线得在决策那一刻到场
- v8.150 把「先质疑→确认→采纳 · 举证对称」写进了 §12 / schema / stage doc · 但这些是**被动 spec**(AI 要主动去读才生效)。而 findings 刚产出、即将被消费的那一刻,state.py 主动推的是 `next_action_brief` —— 它当时只说「整合 finding 到 REVIEW.md → complete」· 零质疑姿态。光改 doc 不改 brief = 防线在文档里、决策在别处(框架「可枚举/主动告知」哲学的要害)。

### 改动(代码 + 测试)
- **`_FINDING_POSTURE_HINT` 常量**:① 先质疑(过度设计/错层/false positive/没看全)→ ② 回读真实代码/AC/DEV-RULES 确认 → ③ 才 ADOPT/REJECT · **ADOPT 也要给实证** ·「reviewer 说得对」不是采纳理由 · 举证责任对称。
- **接进 external-review 成功 emit 的 next_hint**(default + degraded 两分支)—— 每个 stage(goal/blueprint/review)external finding 消费的必经处 · 一处覆盖三阶段。
- **`_review_brief` 加姿态行**(review stage start 即带)。
- 测试 +2(posture hint 关键 token / review brief 含姿态)。

### 验证
- pytest 3 failed / 529 passed(baseline 3 · 净 +2)。

## v8.150 · review finding 处理对称化:先质疑→确认→采纳/驳 · 举证责任对称 · 治本盲采

> 用户:AI 对 review 结果的处理过程应该是先质疑、再确认、再采纳、给出采纳理由的思考过程 · 不能盲目认同。

### 诊断:举证责任不对称 → ADOPT 成无摩擦默认 = 盲采温床
- 框架有裁决三态(confirmed/rejected/deferred)+ adversarial_self_check + 12.2 点名「盲采是默认倾向」—— 但**防线不对称**:rejected「必记驳回依据」是硬的,ADOPT 的 rationale 只要填「改了什么」· adversarial_self_check 的示例/措辞全是 REJECT 方向(steelman finding 再驳)。结果:reject 有摩擦、adopt 无摩擦 → 盲采(reviewer 说啥改啥)恰是阻力最小路径,虽被点名却没设防。

### 改动(doc-only · 对称化既有机制 · 非加新仪式)
- **§12 头部加「固定思考顺序」**:① 质疑(先假设 finding 不成立:false positive/过度设计/错层/没看全)→ ② 确认(回读真实代码/AC/DEV-RULES)→ ③ 裁决+给理由。🔴 **举证责任对称**:confirmed 与 rejected 同责 —— 采纳也要给「为何确为真+为何这样改对」实证 ·「reviewer 说得对」不是理由。
- **§12.1 confirmed 判据**:加「先质疑」前置 + 处置加「记采纳依据(与 rejected 对称)」;§12.2 盲采标「最常踩」+「没经①②的 ADOPT = 盲采」。
- **pm_response.adversarial_self_check schema(prd.md)**:改方向对称 —— ADOPT 方向写「finding 不成立的最强反方→回读确认不成立→采纳」(给 ADOPT 示例);rationale 要求 ADOPT 含「质疑→确认链」三步,不接受无核实采纳。
- **review-stage.md / goal-stage.md substep 6 / roles/pm.md** 三处引用同步对称化(默认姿态=质疑)。

### 验证
- doc-only · pytest 3 failed / 527 passed(零回归)· 无测试 pin §12 措辞。

## v8.149 · goal 阶段去 external 评审:业务对齐阶段不做技术细节挑刺 · 细节/边界归 blueprint

> 用户:goal 阶段的外部评审去掉 —— 总会挑出细节和过度设计;这阶段目的是对齐业务目标(用户会看 PRD)· 细节和边界在技术方案阶段定就行。

### 判断:对的工具 · 错的阶段(非「external 没用」)
- external 整体 82% 采纳(实测数据)· 是框架 MVP —— 但**采纳率高 ≠ 每个阶段都该有**。goal 产物是业务对齐的 PRD、用户亲审;external 天然「找缺口 → 加校验」· 在「定要做什么」阶段把技术细节/边界审进来 = 噪音 + 过度设计提前涌入。external 留在 blueprint(技术方案)+ review(代码)· 那里技术挑刺正当其位。
- **框架早知道病只贴了创可贴**:goal-stage.md 原有「🔴 external finding 须对照简洁性取舍 · 每条单看合理 · 合起来把方案做臃肿」—— 承认了过度设计,却只让 AI 自己筛。v8.149 移除病因(不在此阶段做),而非继续筛。

### 改动(代码 1 处 + 文档)
- **`DEFAULT_REVIEW_ROLES[("Feature","goal")]`**:`[pm,qa,architect,pl,external]` → `[pm,qa,architect,pl]`(唯一硬接线处)。verdicts 门禁通用(谁在查谁 · 不硬要 external)· pl_challenge 独立 → 拆得干净。
- **能力保留**:`EXTERNAL_STAGE_TO_PROFILE` 仍含 goal · 确需对某 PRD 上 external → `change-review-roles --stage goal --roles '...,external'` 显式 opt-in(降默认不删能力)。
- **goal 过度设计防线 = Architect 简洁性 counter-lens(内审)**:external 走后这条内审 lens 成为 goal 唯一简洁性把关 · 文档强化。
- 文档对齐:goal-stage.md(默认 5→4 · 删 External Reviewer bullet · 新「goal 不做 external」段 · 重点 review 指引去 external)· prd.md 模板(reviewers/verdicts 示例)· prepare.md 角色表 · FLOW_STAGE_CHAIN hint。测试 1 处 pin 更新(simplicity-lens v8.76)。
- 🔴 敏捷需求 goal 本就无 external(不变)· Feature Planning goal/planning 的 external **未动**(不同 flow · 跨 feature 粒度 · 待用户单独定夺)。

### 验证
- pytest 3 failed / 527 passed(baseline 3 · 零回归)· build_default_stage_review_roles('Feature')['goal'] 验证去 external · blueprint external 保留。

## v8.148 · ship2 后流程质量审计落安装目录 docs/audit/ · 框架跨项目搜集(补全反馈环消费侧)

> 用户(承前三轮诊断):ship2 后加一段 AI 静默逻辑 · 总结当前项目执行数据(做的好的/发现的问题/待优化的 + 实际数据)· 写到 skill 安装目录 docs/audit/ · 方便框架层面搜集流程质量。

### 背景:补的是反馈环缺失的「rollup 回收层」
- 前三轮查实:① ship2→框架的反馈通道只有意图无机制(jdp 漏掉真判例);② 「年检」被引用 7 次作消费方 · 0 次定义 procedure(幽灵);③ 项目级→框架的总结流程根本不存在。三者同一病根 = 反馈环只建了「写」· 「读/rollup」整个没规范。本版补 rollup 回收层第一块。
- 三处落点分工成文:PROCESS-LEDGER(项目侧 per-feature)· **docs/audit/(安装目录回收侧 · 跨项目)** · RETRO-LEDGER(框架仓 per-version)。安装目录 = 本机所有 consuming 项目共享回收点 · consuming 项目不自改 spec · 只投递 · 框架来 harvest。

### 改动(代码 + 测试 + 文档)
- **`_write_audit_record`(ship-finalize PASS 后调)**:落 `<安装目录>/docs/audit/<id>.md` —— **机器数据段工具确定性抽**(来源项目/flow/实走 stages/总时长〔stage_contracts 时间戳算〕/concerns/bypass · 喂 kill-criteria 不可幻觉)+ **三段判断占位**(做的好的/发现的问题/待优化的)由 **AI 静默补**(零暂停 · 改 audit_status: done)。`TEAMWORK_AUDIT_DIR` env 可 override(测试)· 写失败静默降级不阻塞 ship2 · 已填不覆盖(幂等)。
- 「发现的问题」段 = 框架级 bug/工具判例的**持久回收口**(取代 §16 旧易逝 digest 的「建议反馈 teamwork」行)。
- docs/audit/README.md(回收/harvest 说明)· .gitignore 只入库 README(运行时 <id>.md 是 transient 本机回收料 · 抗 update.py 覆盖:_overwrite_skill_files 不删 target 多余文件)。
- §16 三处落点表 + 时机成文;emit 增 audit_record + brief 静默补完指示。
- 测试 +2(审计草稿落 TEAMWORK_AUDIT_DIR 含机器数据+占位 / 已填不被重跑覆盖)。

### 验证
- pytest 3 failed / 527 passed(baseline 3 · 净 +2)· 真实产物 eyeball(时长/stages/concerns 确定性正确)。

## v8.147 · LEDGER 冲突升级机械自动解:三方对比纯增行判定 · union 进脚本(实战 case 驱动)

> 用户(截图 case:SVC-CORE-B260612051432 · aon 实战):v8.146 防线首战 —— PROCESS-LEDGER 三行追加冲突按 ③ 留给 AI · AI 的处置 = 删标记保双方行 · **零判断纯机械**。判定:该进脚本(v8.146 保守只解 INDEX · 实战证明 LEDGER 同样可枚举)。

### 设计:安全前提物化
- `_try_append_union_resolve`:三方对比 base(:1:)/ours(:2:)/theirs(:3:)· **双方相对 base 都是纯增行**(base 行序列为两侧保序子序列)才自动 union(theirs 全文为基 + 本侧增量去重后置)· 任一侧有删/改 → 拒动留 AI(PENDING 提示改为「台账类但非纯增行 · 人工合」)。
- 适用名单制(`PROCESS-LEDGER.md`)· 不做通用文件 union(代码文件双方尾部追加 union 可能语义错误)。
- sync 返回升级:status 统一 `auto_resolved` + `auto_resolved_files` 清单 · archive emit 的 `sync` 注明解了哪些文件(透明可审计)。

### 实战判读(截图 case · 防线首战全对)
- 重跑 archive = 冲突修复入口 ✓ · INDEX 静默处理 ✓ · LEDGER union 保双方行 ✓ · 只 add 冲突文件不碰 untracked 接力卡 ✓ —— AI 处置零瑕疵 · 但这步本可不存在 · 故升级。

### 验证
- 测试 +2(纯增行自动 union 双方行都在 / 非纯增行〔同行双改〕拒动 PENDING 留 AI)· pytest 3 failed / 525 passed(baseline 3 · 净 +2)。

## v8.146 · ship1 冲突防线:archive 前置 sync 自动合 · INDEX 冲突机械自动解 · 代码冲突留 AI

> 用户(承 v8.145):ship1 在 MR 创建后大概率会冲突 · 是否有必要增加检测冲突环节 · 自动评估处理。判定:有必要 —— v8.145 设计时把该 trade-off 低估为「可能」· 实为「并行 ship 窗口重叠时必然」(INDEX/LEDGER 是 every-feature 同位追加)。

### 设计(按框架哲学拆:可枚举进脚本 · 不可枚举留 AI)
- 解决场所 = worktree(到 ship2 前一直活着 · 正是 v8.145「内容性工作在可控环境」的合法位置)。
- 同步用 **merge 不 rebase**(分支已推 · MR 已开 · 不破 review 历史)。

### 改动(代码 + 测试 + 文档)
- **`_sync_feature_branch`(内置于 archive · 首跑+幂等重跑共用)**:fetch + behind 检测 → 落后自动 `merge origin/<mt>` —— ① 干净则无感(MR 开出来即可合 · INDEX 基于合并后状态生成);② **INDEX.md 冲突机械自动解**(确定性再生成:origin 侧为基 + 重放本 feature 行 · 追加表语义明确);③ 其余冲突(代码/规划文件)→ emit `PENDING merge-conflict` + 文件清单(LEDGER 类提示 union)· AI 在 worktree 评估处理 → `git add`/`git commit` → 重跑 archive。
- **重跑 archive = MR 窗口期冲突修复入口**:平台报冲突 → 回 worktree 重跑(自动 sync + 机械解)→ `git push` → MR 自动更新;⏸️ ship1 暂停点加「平台报冲突」选项;emit 增 `sync` 字段(同步动作透明)。
- fetch 失败降级(冲突防线降级不阻塞归档 · WARN);未完成 merge 检测(MERGE_HEAD)→ 先收尾再重跑。
- 测试 +3(前置 sync 无感合 / INDEX 冲突自动解双方行都在 / 代码冲突 PENDING→解→重跑通过)· ship-stage.md §3 冲突防线成文。

### 验证
- pytest 3 failed / 523 passed(baseline 3 · 净 +3)。

## v8.145 · ship 架构重构:ship1 全交付(worktree 内 · 终点 = MR 提交)· ship2 零内容清场 · 砍双 MR 链路

> 用户拍板:单个 ship 的终点就是提 MR · 收尾更新状态不属于本次 ship。ship1 全交付 feature 内容(文档总结/压缩 zip 全在 worktree 内)· 完成后提示用户合并 MR 即结束;ship2 回主工作区删 worktree · 净化(脏内容提交 · 影响大给方案由用户决策)· pull · push。**ship2 不修改任何内容**。三项确认:INDEX.md 保留 / 副产物自动 commit / 不留兼容期。

### 架构裁定(为什么对)
- 旧链路十二个版本(v8.16/31/32/33/70/80/82/87/93/113/130/144)反复修同一条尾巴 —— 根因 = 在**不可控的主工作区**(脏树/分叉/并行 feature/保护分支)做**内容性工作**(归档/翻牌/状态)。新原则:内容全部发生在可控环境(worktree · 自己的分支)随 feature MR **原子合入**;主工作区只清理。
- **单 MR**:归档 zip + 规划翻牌 + 终态 state.json 全进 feature MR · 不再有 ship-finalize/<id> 第二分支 + 第二个 MR。**MR diff 反而更干净**:过程目录在分支历史「加了又删」对 merge_target 净零 · diff 只剩代码 + zip + INDEX 行 + 翻牌行。
- **翻牌语义更对**:随 MR 原子生效 —— MR 不合 ROADMAP 不显示已交付 · revert 同退(旧模型有 merge 后时间窗)。
- **主工作区从未物化过程目录**:v8.82 purge / v8.87 残留清除 / v8.144 staged-D 终态 那批债结构性消失。

### 改动(代码 −979 行 · 测试 · 文档)
- **ship-phase 新 action `archive`**(ship1 终幕 · tool-executed):规划翻牌 gate(--planning-artifacts/--no-planning-changes · v8.93 前移)→ 终态 state.json(current_stage=completed · 墓碑进 zip · 宣称与落地随 MR 原子可见)→ zip + INDEX(--archive-desc ≤200 门禁保留)→ `git rm --cached` 过程目录(**工作树保留 = ship2 接力卡**)→ 单 commit。幂等;push 门禁改 archived → pushed。
- **ship-finalize 重定义为 ship2**(零内容):verify-delivered(zip 在 origin · 抗 squash · 未合 PENDING 绝不删 worktree)→ worktree-remove(+fetch --prune)→ main-sync(**副产物注入块/锁自动 commit** · 用户真改动决策面板 · pull --rebase/--ff-only 对症 · push 被拒提示)→ stash 盘点 + digest 指引。幂等:接力卡消亡 → origin 全树搜 zip → noop。
- **删除(不留兼容期)**:confirm-merged/cleanup 子动作 · state-sync · finalize-deliver 双 MR 链路 · 零 checkout plumbing(_stage_archive_commit/_finalize_push_plumbing)· v8.82 purge · v8.87 强清 · §12 state.json 直推例外 · archive_on_ship 配置(残留忽略 + WARN)。
- **main-sync 去 feature 依赖**(接力卡可已消亡):--feature 可选 · --merge-target 三级推导;决策面板命令串同步。
- 测试:新 test_ship_v8145_flow.py(13 测:archive gate/归档形态/翻牌原子/幂等/ship2 全周期/副产物自动 commit/决策面板/featureless main-sync)· 删旧链路 ~37 测 · ship 存量套件适配;SHIP_SPEC/SKILL/ship-stage.md/模板 全面改写。
- PROCESS-LEDGER 采写时机:planning-backref(主工作区)→ **archive 规划 gate(worktree 内)** · 数据源就在工作树。

### 验证
- pytest 3 failed / 520 passed(baseline 3 · 旧链路测试删除后净 −29 · 新流程 13 测全绿)。

## v8.144 · ship-finalize 收尾终态治理:pop 结果必查 · pull 失败对症判别 · 残留清除即补 pull · stash 盘点

> 用户(case:SVC-PLATFORM-B260611083636 收尾 transcript):看下收尾动作是否有问题 · 是否需要优化。终态正确(双 MR merged · 归档落位)· 但尾段甩给 AI ~20 条 git 手术 · 其中两处是框架自造的债。

### 诊断(代码对照 + git 沙箱实测)
- **pop 结果被无视**:step 7 stash→pull→pop 链 · pull 失败分支不查 pop.returncode · 宣称「stash 已 pop」—— 实证里 pop 没成 · bootstrap 注入块改动埋在 auto-stash · AI 误以为丢失**手工重写** = 与 stash 双份地雷。
- **「分叉 · 需手动 rebase」一刀切误导**:任何 pull 失败都喊分叉。沙箱实测(E2):staged 删除(本地删 vs origin 同删)+ 无关 M 文件**不阻塞** ff-pull —— 实际仅落后 · 一条 `git pull --ff-only` 即愈 · AI 却被引上 reset/stash/pull 手术路径。
- **v8.87「下次 pull 自愈」只对一半**:残留清除用 git rm 留 staged 删除等下次 pull —— 前提成立(实测)但「下次」不该留给人:PASS 终态停在 behind + staged D。
- **teamwork 自动 stash 跨 feature 堆积**(实证 3 个跨 2 feature)无人盘点;收尾分支零 checkout 仅存远端 · emit 不说 · AI 烧 4 条命令重发现;remote-tracking 残影要手动 prune。

### 改动(代码 + 测试)
- **`_behind_ahead` + `_pull_failure_remedy`**:rev-list --left-right 判别「仅落后(给 pull · 不喊 rebase)」vs「真分叉(才给 rebase)」· clean 路径 / v8.32 stash 路径 / v8.87 补 pull 三处接入。
- **pop 必查**:pull 失败分支区分 pop 成败 —— 失败 → `pull_failed_stash_stuck` + 「改动埋在 stash『名』· 先 pop 勿手工重写」;两处 pop 失败文案都带 stash 名。
- **v8.87 残留清除后立即补 ff-pull**(E1/E2 背书)→ 成功即 `purged_pulled` 干净+最新 · PASS 不再留 behind+staged D 终态。
- **stash 盘点**:emit `teamwork_stashes` + 处置指引(show -p 核对 → pop/drop · 勿堆积);deliver_pending 注明「分支仅存远端 · 本地查不到属正常」;delivered 清理后自动 `fetch --prune`。
- 测试:新 test_ship_main_sync_v8144.py(8 测 · 含 staged-D ff-pull 地面真相固化 · 防 git 行为回退静默失真)· ship 既有 55 测零回归。

### 验证
- pytest 3 failed / 557 passed(baseline 3 · 净 +8)。

## v8.143 · 发版交付边界:止于 push dev · 砍本机 rsync · 消费项目统一走 update.py(channel=dev)

> 用户:rsync 去掉 · 本地其他项目走 dev 版本升级 · 你只负责将修改提交到 dev。

### 诊断
- 发版例程里的 `rsync → ~/.agents/skills/teamwork` 是 session 习惯(仓内零成文)· 效果 = 本机消费项目被静默推到未过 main 发布门的版本:无升级提示(本地恒新于线上)· 无确认 · 无 update.py 的 backup · 回滚要手动。用户在 codex session 撞见「静默最新」后拍板砍掉。

### 改动(doc-only)
- **CHANGELOG 头部加「交付止于 push dev」规则**(发版 session 必读处 · 防未来 session 凭惯性恢复 rsync):发版不碰本机安装副本 · 框架仓工作区 ≠ 交付渠道。
- **本机消费项目与其他机器同路**:bootstrap 升级提示(v8.142 起带变更描述)→ 用户确认 → `update.py` tarball 覆盖(自带 backup)。本机项目在各自 `.teamwork_localconfig.json` 配 `"update_channel": "dev"`(项目侧动作 · 不在本仓)。
- 链路已验通:update.py 自 v8.41 去 git 化(tarball 下载覆盖)· 对非 git 安装副本可用;当前安装副本 v8.142.1 == dev tip · 下一版起提示自然出现。

### 验证
- doc-only · pytest 3 failed / 549 passed(零回归)。

## v8.142 · 升级提示带变更描述:线上 CHANGELOG 标题行进暂停点 · keep-5 断档加 git 历史注

> 用户:更新提示出现时 · 需要带一下更新描述。

### 诊断
- 升级暂停点只报版本号 + 「去 GitHub 看 CHANGELOG」指针 —— 用户在暂停点上无法判断「这次升级对我有什么」· 决策要出门。发版纪律里每版标题行本就是一行蒸馏摘要 · 现成可用。

### 改动
- **`_fetch_changelog_titles`**(bootstrap.py):outdated 时拉线上 `docs/CHANGELOG.md`(channel 同 SKILL.md · env `TEAMWORK_SKILL_CHANGELOG_URL` 测试覆盖)· 抽「本地版本之后」各版 `## vX.Y · 标题` 行(新→旧 · 扫到 ≤ 本地即停)· prompt 加「本次升级包含」清单(cap 8 · 超出加共 N 版注)。
- **keep-5 断档识别**:扫完未遇到 ≤ 本地的条目 = 落后超出线上留存范围 → 加「(线上 CHANGELOG 仅存最近 5 版 · 更早变更见 git 历史)」注。
- **best-effort**:拉取/解析失败返 None · prompt 降级回原指针 · 绝不阻塞 bootstrap;up_to_date 路径零额外网络(只在 outdated 才拉)。emit 增机器可读 `changelog_titles`。
- 测试 +4(标题进 prompt 且 ≤ 本地不列 / 拉取失败降级 / keep-5 断档注 / up_to_date 不拉)· setUp 把 changelog env 指向受控 file://(防既有测试外呼真 GitHub)。

### 验证
- pytest 3 failed / 549 passed(baseline 3 · 净 +4)。

## v8.141 · claude -p MCP 隔离:--strict-mcp-config 零 spawn · v8.106 归因翻案(裸跑也拉项目 MCP)

> 用户:claude -p 是否支持 --allowedTools · 重点解决 MCP 卡死。答:支持(CLI 2.1.173 实测)· 卡死真因不是 --allowedTools。

### 实测(本地四组对照 · marker 文件法 · 毒 MCP 项目)
| 案 | flags | 项目 MCP 真 spawn | 结果 |
|---|---|---|---|
| C1 | 裸 `claude -p` | **True** | 5.4s OK |
| C2 | `--allowedTools Read` | **True** | 4.2s OK |
| C3 | `--strict-mcp-config` | **False** | 4.8s OK |
| C4 | strict + `--allowedTools Read` | **False** | 7.4s OK |

### 诊断:v8.106 归因翻案
- **裸 `claude -p` 也每轮 spawn 消费项目 .mcp.json 全部 server**(C1)—— 现行外部评审一直在拉火药库 · 只是 CLI 2.1.173 连接不阻塞所以侥幸不卡;卡死与 `--allowedTools` 无关(C2 同 spawn)· 真正变量 = 项目 MCP 被 spawn + CLI 版本连接行为(2.1.15x 阻塞 → 当年卡死)。
- 评审 prompt 自包含零工具 · 本就不该碰项目 MCP —— 修法是**隔离整类**而不是赌 CLI 版本。

### 改动(代码 + 测试 + 文档)
- **`_build_claude_review_cmd` 固定加 `--strict-mcp-config`**(不传 --mcp-config = 零 MCP spawn · 不碰登录上下文 · 无 --bare 认证回归)· 生产 argv 形态在毒项目实测 3.9s rc=0 零 spawn。
- 测试:2 处 cmd pin 更新 + 新 1(strict 必在 + --mcp-config 必不在 · 缺一不可)。
- standards 新 §11.7(对照表 + 翻案记录)· §一 claude 路径行 + state.py 两处 docstring 同步修正因果。
- **解锁备忘**:strict 隔离下 `--allowedTools Read` 实测安全(C4)· 未来 ARG_MAX 卡长 prompt 可走「短 prompt + reviewer 自己 Read + strict」· 当前保持零工具 inline。

### 验证
- pytest 3 failed / 545 passed(baseline 3 · 净 +1)。

## v8.140 · 评审「开始声明」可行化:RUNNING 心跳(harness)+ 首行 REVIEW-ACK 自证(模型)

> 用户(承 v8.139):能否在 prompt 注入 · 让评审模型开始运行时在同名 .log 声明开始 + 时间戳。

### 裁定:直写 .log 不可行 · 拆成两个可行层
- **模型写不了文件**:claude -p 零工具(v8.106 故意拔 —— --allowedTools 激活 agentic 栈 → 拉消费项目 MCP → 卡死 · 恢复工具 = 复活该 bug 类);codex 沙箱不保证可写。且「开始时」恰是模型还没起来的窗口(认证/排队/网络)· 谁都报不了。
- 诉求拆解:① 运行中活性(还活着么)→ **harness 心跳**;② 模型亲口确认「处理的是本轮」→ **输出首行回显**(prompt 注入 · 可行)。

### 改动(代码 + 测试 + 文档)
- **RUNNING 心跳行**(`_run_streamed_to_log` 增 heartbeat 线程 · 默认 60s · 0 关):报已等待秒数 + 已收字节 —— claude -p 完成前 stdout 0 chars 属正常 · pid 行到 END 行之间原本仍是盲窗 · 心跳让 tail -f 分清「生成中」vs「卡死」。
- **首行 ACK 自证**(`_ack_block` 注入 + `_review_ack_status` 验证):generated 路径 prompt 尾注入输出契约「第一行必须 `REVIEW-ACK <prompt-doc stem>`」(stem 自带 stage/model/UTC ts)· 头 200 字符回显即 verified(emit `review_ack`)· 缺失 → `ack_missing` **WARN 不 BLOCK**(遵从概率性 · 不可枚举);两引擎先拼后落 doc(审计=输入不分叉)· `--prompt-doc` override 原样执行不注入不验。无 liveness 作用(print 模式整体到达)· 价值 = 输出 ↔ 本轮 prompt **对应性绑定**(v8.136 防 stale 从输入侧门禁补到输出侧自证 · 回显进结果文件与 .log 留档)。
- 测试 +4(心跳盲窗 0 字节/0 关/ACK 块契约/验证三态 + codex 测试加 ACK 断言)· standards §11.6 补两层。

### 验证
- pytest 3 failed / 544 passed(baseline 3 · 净 +4)。

## v8.139 · 外部评审过程实时落盘:prompt-doc 同名 .log · START 行 harness 写 · 黑盒窗口可观测

> 用户:触发外部评审后完全黑盒 · 提议过程输出写同名 log · 第一行由评审模型自报已开始 + 时间戳。裁定:同名配对 ✅ · 首行改 **harness 写**(模型自报不可行也不可靠)。

### 诊断:v8.55 日志三缺陷 = 黑盒根源
- **跑完才写**:`_log_external_run` 在 subprocess.run 返回(或超时)后落盘 —— 运行中窗口(最长整个 timeout)磁盘零痕迹 · 黑盒恰是这段。
- **藏 ~/.teamwork + 独立时间戳命名**:与 feature 内 prompt-doc 不同目录不同名 · 无法配对 · 用户不知其存在。
- **stderr 死因等验尸**:鉴权失败/codex 升级提示/限流都在 stderr 早期出现 · 却要等超时后才可见;超时还返空 stdout(丢已收部分)。
- **首行模型自报不可行**:`claude -p` print 模式输出整体到达 · 模型「已开始」行不可能先到;挂死/认证失败时恰恰零输出;且把流程关切注入评审 prompt(遵从概率性)。时间戳可枚举 → 归脚本(框架哲学)。

### 改动(代码 + 测试 + 文档)
- **`_run_streamed_to_log` 取代 `_log_external_run`**:Popen + 双 reader 线程实时落盘 —— 发起即写 `[UTC] START` 行(harness 时间戳)→ `pid=` 行 → stdout 原样 + stderr 逐行 `[stderr] ` 前缀(死因秒级可见 · mtime=心跳)→ `END · rc · 耗时 · 字节`;超时写 `TIMEOUT` 行 + **保留已收部分输出**(rc=124);重跑 append 叠加不覆盖;日志 OSError 静默降级绝不阻塞评审。
- **同名配对律**:log = prompt-doc `.with_suffix(".log")` · 审计三件套同目录成组(输入 .md / 过程 .log / 结果 external-cross-review/)。**codex 路径补齐审计=输入**(prompt 落唯一命名 doc · 执行仍 argv inline · 对齐 v8.136 claude 路径)。
- **透出**:发起时 stderr 打印 log 路径(tail -f 可观察 · 不污染 stdout JSON)· emit 增 `process_log`(成功/失败都有 · 失败 hint 第一条改「查过程日志」)· prompt_doc 字段放开到两引擎。
- 测试:改 2(mock 执行器)删 2(v8.55 旧日志)新 6(首行 START 序/超时保留部分输出/append 叠加/无 log 照跑/两引擎配对)· standards/external-model-usage.md 新 §11.6。

### 验证
- pytest 3 failed / 540 passed(baseline 3 · 净 +4)。

## v8.138 · panorama_sync 变更判级:L1 节点内增量不暂停(WARN 留痕)· L2 结构变更才停

> 用户(case:PTR-F260611065743 panorama_sync):全景修改的暂停点是否有必要 —— sitemap 仅描述行更新 · AI 推荐理由自证「IA 不变 · 未发现跨 Feature 冲突」· 用户按 1 纯放行。

### 诊断:暂停粒度与触发粒度错配 · 「纯过场」活标本
- 暂停保护两件事:IA 权威变更需多方评审 · 跨 Feature 影响需 owner 协调。case 两条件均不成立且 stage 内已查明(冲突扫描零命中 + 无节点增删)—— 事实已知还停 = 上抛已知事实(v8.128/v8.132 同款判别:停不停看事实已知度)· 收获只有默认放行。PROCESS-LEDGER「暂停点 改:默」kill criteria 的第一个判例(改:默 = 0:1)。
- 根因:`--panorama-changed=true` 判据是「panorama 文件动没动」(文件级 · sitemap 描述列更新也必走本 stage —— ui_design 不许直改 sitemap);暂停语义是「结构变更/跨 Feature 冲突」(语义级)。**stage 该进 · 暂停不该一律停**。

### 改动
- **变更判级**(substep 3 · 受影响 Features 扫描后判 · 依据逐条写进 §协调结论):**L1 节点内增量** = 三判据全满足(① 无节点增删移/路由变化 ② 无设计 token/共享视觉基线变更 ③ 受影响 Features 零命中);**L2 结构变更** = 任一不满足 · 拿不准按 L2。
- **L1 不暂停(任何模式)**:add-concern WARN 留痕(复用 auto-skip 语式)+ 零暂停 digest(≤3 行:变更/判据/产物指针)+ 直接 complete;**L2 必停**照旧(auto_mode 跳过规则不变)。
- **物化**:summary frontmatter 必含 `change_level: L1|L2`(缺即 FAIL —— 判级决定停不停 · 级别必须留痕);`authorized_pause_point` 改条件式。深校验(L1 时 sitemap diff 真无节点增删)不可枚举(sitemap 格式各项目异)→ AI 判 + 声明审计 + LEDGER L1/L2 比例兜底。
- **判级反模式成文**:结构变更标 L1 逃暂停 = R5 违规同级;ui-design-stage 触发处加期望管理(`true` ≠ 必暂停 · 不必预判影响大小)。

### 验证
- pytest 3 failed / 536 passed(baseline 3 · 净 +2:change_level 物化 pin + 条件暂停 pin)。

## v8.137 · goal 确认前置「重点 review 指引」:六节照实抄导读 · 替你做的判断放第一节

> 用户:PRD 在 AI 评审后直接交用户确认 · 希望请求确认前最后输出值得关注和了解的点 · 方便重点 review。

### 诊断:出口缺导读(v8.120 流程目标的对偶)
- 入口已有「流程目标」校准「要做什么」;出口(substep 9)用户面对的是全员 APPROVE 的成品 PRD · 没有导读告诉他**哪里值得抽查** —— 尤其 AI 在评审循环里替用户做过的判断(REJECT/DEFER 的 finding)完全不可见。

### 改动(doc-only)
- **goal-stage substep 9 加「重点 review 指引」**(请求确认前 emit · 固定 6 节 · 每节 ≤2 行):① **替你做的判断**(REJECT/DEFER 的 finding · AI 判断替代用户判断之处 · 抽查性价比最高 · 放第一节)② 核心取舍(争议已裁决 · cite id)③ 范围收窄(Out of Scope 中用户可能预期在内的)④ 影响面 ⑤ 修订轨迹(哪轮评审驱动)⑥ 残留风险/假设。
- **反即兴约束**:六节全部照实抄自已落盘结构化产物(pm_response / PL-CHALLENGE / revision_history / Out of Scope / PM 自查 / §待决策项)· 空节显式写「无」不可省 · 反模式成文(复述全文 / 营销式总结 /「经多轮评审已完善」/ 无产物出处)。

### 验证
- doc-only · pytest 3 failed / 534 passed(零回归)。

## v8.136 · claude -p 链路三修:prompt-doc 每轮唯一命名(审计=输入)· 模板提取治双嵌 PRD · 显式 doc staleness 门禁

> 用户(case:PTR-F260611065743 三轮 external review):claude -p 总是出现各种问题 · 整体 review → 裁定保留 doc 优先 · 每轮 doc 名唯一 · 传入 doc 路径。

### 诊断:结构性事故链(手工修复不可能根治)
- **固定名缓存中毒**:round 1 走 inline fallback 后把 prompt 写进固定名 `goal-claude.md` 作「审计副本」(v8.106 保留);round 2 的 `if prompt_doc.exists(): 优先读` 把它当 v8.44 人工 doc 消费 → 评审 stale PRD v0.1;AI 手工删 doc → round 3 又写回 → round 4 必复发。审计产物成了无失效机制的缓存。
- **模板整文件替换双嵌 PRD**:fallback 拿 claude-agents/reviewer.md **整文件**(文档+模板混合体)做全局 replace —— 尾部「占位符说明」表里的 `{file_list}` 示例格也被灌入完整 PRD → prompt 含模板元说明 + codex 对照表 + **双份 PRD**(~400 行垃圾 · 加重长 prompt 卡)。
- v8.44「scaffold + 人工填 summary」推荐路径零使用记录 · 每轮都 fallback + WARN · 形同虚设。

### 改动(代码 + 测试)
- **每轮唯一 prompt-doc(用户方案 · 优于直接废 doc)**:`_new_prompt_doc_path` = `<stage>-<model>-<UTC时间戳>.md` —— 默认路径每轮**现生成**(模板 Prompt 主体提取 + inline 当前文件 → 写新 doc → 用它执行)· **审计 = 输入零分叉** · 旧轮留档不复用 · 随 feature 归档。
- **显式 `--prompt-doc` 保留优先** + **staleness 门禁**(`_prompt_doc_stale_reason`:doc mtime 必须新于全部待评审文件 · stale → FAIL with hint)。
- **模板提取**(`_extract_prompt_body`):只取「## Prompt 主体」fenced block 内文本做替换(占位符表/对照表永不进 prompt · `{file_list}` 替换点唯一)· claude 路径 + subagent 降级路径同享。
- scaffold-review-prompt 改唯一命名(覆盖冲突消失 · `--force` 降 no-op 兼容)· subagent 降级 doc 同步时间戳命名。
- 测试:改 3(路径唯一性 / scaffold 两轮两 doc 且首份不被动)+ 新 3(提取排除模板文档+替换点唯一 / 无标记回退兼容 / staleness 门禁三态)· test_state 196 全过。

### 验证
- pytest 3 failed / 534 passed(baseline 3 · 净 +2 · 零回归)· grep `_default_prompt_doc_path` 残留 = 0。

## v8.135 · 注入块加「Subagent 默认授权」:满足宿主工具契约的长期授权 · 授权管能不能 · R4 判据管该不该

> 用户(case:codex-cli 跑 teamwork goal external review):注入逻辑增加 subagent 使用声明 —— 用户明确授权在 Teamwork 流程中默认使用 subagent(PRD/Blueprint/Review cross-review · 并行探索 · 互不重叠实现子任务)· 无需每次另行确认。

### 诊断:宿主工具契约与 teamwork 流程的缝隙
- Codex 的 spawn_agent 契约要求 "user explicitly asks";teamwork 流程(external review / 多角色评审 / PL 隔离质疑 / 并行实现)预设用 subagent —— 每次等口头授权会卡住流程(尤其无人值守 auto/yolo)。授权的合法落点 = 宿主指令文件(工具契约读取处)= 注入块。
- 两个措辞修正:注入块三宿主共用(不能写死「Codex」→ 通用宿主表述);约束不复述 SKILL 已有纪律(防双源 · 只给指针)。

### 改动(doc-only)
- **host-instruction-injection.md 注入块新增「Subagent 默认授权(Teamwork 流程)」段**:用户明确授权(三宿主通用)在 Teamwork 流程中默认使用 subagent · 无需每次另行确认;适用枚举(各阶段 cross-review/多角色评审 · PL 对抗质疑隔离执行 · 并行探索 · 互不重叠 write scope 实现子任务 · 验证/测试 sidecar);约束仅指针(R4 判据 · worktree 内写路径 · 流转不外包 · 主对话整合)。
- 本仓 CLAUDE.md 实例同步(gitignored · 下次 bootstrap sync-drift 也会按模板刷新);consuming 项目在各自下次 bootstrap 自动获得。
- **SKILL.md R4 subagent 条款加授权指针**:授权已长期化 —— 解决「能不能用」;R4 判据(独立且够大)仍管「该不该用」· 防授权被读成「滥用许可」。

### 验证
- doc-only · pytest 3 failed / 532 passed(零回归)· 注入模板/CLAUDE 实例/SKILL R4 三处口径一致。

## v8.134 · 分层同构律:基建层共享包完全一致 · 页面层意图权威(四要素)· 共享基建改动须验全景编译

> 用户四轮推演(承 v8.133):镜像方式是否最合理 → mock 态全景提案 → 规划层不可纯文档(需最终视觉稿)→ 裁定分层同构 + 补「共享基建改动后 dev 结束须保证全景编译通过」。

### 推演与裁定(完整决策链留底)
- **v8.133 全量镜像律推到逻辑终点 = 双源死结**:一个「除数据层外处处必须相同」的镜像就是真实 app 本身 · 维护两份必须一样的代码正是框架反复消灭的反模式;且全貌要求意味着每次 ship 都要回灌镜像(spec 无此环节 · 权威必倒置)。
- **mock 态全景方案**(全景=真实 app mock 态 · 设计 worktree 内 mock-first)解了零翻译 · 但撞规划期约束(规划层需多方对齐的最终视觉稿 · 文字/草图不够 · 而规划期出真实 app 代码破 R6/worktree 纪律)+ 丢「多 future 合并浏览」能力 → 不采纳。
- **用户的第三条路**:同构承诺按「能否由结构保证」分层 —— 全镜像和废镜像都是错的。
- 顺带实锤:dev-stage §3 same-stack 还原段仍写「项目自身 /design/<page-id> 路由 diff」= 已废 in-app 旧模型残留。

### 改动(doc-only)
- **ui-design-stage 分层同构律**(替代数据层唯一差异律 · IA 镜像律保留):**Layer 1 基建层完全一致**(shell/架构/栈版本/组件库/主题 · ① 共享包优先〔monorepo workspace 包 · 两端依赖同一份代码 · 一致性由单源结构保证 · 零镜像维护〕② 不可抽包才版本锁定镜像+记豁免)· **Layer 2 业务页面层意图权威**(四要素:布局结构/交互流/状态/字段映射 = UI.md 既有段落 · 实现「重点参考」= 四要素必须对齐 · 像素/代码组织自由)· **权威时效**(设计权威至该页 ship 止 · 此后代码即真相 · 反模式:拿停更全景纠正已演化页面)。
- **下游编译契约(dev-stage 新 §3.5)**:共享基建两个消费者(真实 app + 全景)· feature diff 触及全景依赖的共享包 → dev-complete 前 worktree 内跑 preview-project build(exit 0)· 失败处置三分:机械适配顺手修(+UI.md 记录)/ 引发视觉变化走 --panorama-changed / 收回破坏性改动(改 API 者迁移所有消费者 · 同 Schema 影响分析责任模型)· 证据进 dev test evidence · ⏳ 物化 TODO(--panorama-build-exit-code 条件 evidence)· 自查清单 +1 项。
- **dev-stage §3 same-stack 还原重写**:废 in-app 路由 diff 残留 → 分层对照(L1 复用共享包不重写 · L2 四要素对齐非字节还原 · 设计变更不在 dev 顺手改)。
- **联动**:templates/ui.md(意图四要素 + 权威时效注)· designer(分层同构)· feature-planning Step 5(seed 基建层优先共享包)· 质量基线反模式更新(分层版)。

### 验证
- doc-only · pytest 3 failed / 532 passed(零回归)· 分层同构律/四要素/§3.5 五文件 grep 一致 · in-app 路由残留清零。

## v8.133 · same-stack 全景两律:IA 镜像(真实路由 + 首页设计稿)+ 数据层唯一差异 · 预览给页面直达 URL

> 用户(case:jdp console ingest-info-entry):same-stack 时预期设计稿与实现完全一致 · 区别只在数据层(mock);预览应给页面真实 path URL(如 :62706/xxxpath)· 不是把设计页顶在 / 上;/ 应是真实首页设计稿。相关 stage 描述是否有问题。

### 诊断:有问题 —— spec 亲手教 AI 给根 URL · 「全景」缺 IA 镜像这一半
- ui-design-stage § 预览写明「抓 PREVIEW_URL= 那行给用户 browse」(根 URL);preview.sh 模板注释同款;全文无「路由镜像 / 页面挂真实 path / `/` = 首页」任何要求 —— case 里 AI「未引入 react-router-dom(单页渲染不需要路由 · 有意省略)」是**照章办事** · 把设计页顶在 / 也合规。
- 「同技术栈」只字面要求栈名 · 未定义镜像范围:case 第一轮反馈(pnpm/antd 版本 / main.tsx 入口结构漂移)全靠用户人工抓 —— spec 缺「与真实实现差异只允许在数据层」的总律。
- sitemap.md 本就含路由(designer role:「IA 地图:层级/导航/路由」)—— IA 镜像意图在规划侧存在 · 但从未绑定到 preview-project。

### 改动(doc + 模板注释)
- **ui-design-stage 立两律**(same-stack 模型区):🔴 **IA 镜像律** —— preview-project 路由结构 = 真实 app(与 sitemap 一致)· 本次设计页挂真实 `route_path` · `/` = 真实首页设计稿 · router 属栈镜像必含(「单页不需要路由」= 漂移反模式);🔴 **数据层唯一差异律** —— 框架/版本/包管理器/入口结构/路由/组件库全镜像 · 差异只允许 mock 数据层 · 其他漂移修复或 UI.md 记显式豁免。
- **预览地址约定**:PMO 给用户的 URL = `PREVIEW_URL` + `pages_changed[].route_path`(页面直达)· 注明 `/` = 首页 · 多页给直达清单 · 把设计页渲染在 `/` 顶掉首页 = 违规。§5 暂停点决策参考 / preview.sh 模板注释 ×2 同步。
- **frontmatter 加 `route_path`**(same-stack 必填 · ui-design-stage 示例 + templates/ui.md):`panorama_file` 降级 static-html 必 / same-stack 可选。
- **联动**:roles/designer.md 镜像两律 + 直达 URL · feature-planning Step 5(全景 seed 即按真实路由组织 · router 必含)· 质量基线加 IA 镜像反模式行。
- ⏳ 物化 TODO:same-stack 时 route_path 必填校验(parse_frontmatter 不支持嵌套 list-of-dict · 需 raw 扫描 · 渐进)。

### 验证
- doc-only(+模板注释)· pytest 3 failed / 532 passed(零回归)· IA 镜像律/数据层唯一差异律/route_path 五文件 grep 一致(ui-design-stage / ui.md / preview.sh / designer / feature-planning)。

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

## v8.128 · 排查先行律:根因未定的现象类输入先问题排查再定流程(治「猜测进 prepare 总览」)

> 用户(case:consuming 项目「ci 编译失败」):应该先诊断再给流程。

### 诊断:关键词路由跟「用户措辞」不跟「事实已知度」· prepare 总览写进未验证猜测
- 现行表「报错/挂了/500」直接 → Bug;「排查/查 log」才 → 问题排查 —— 现象类输入(ci 编译失败)被直接定 Bug · emit prepare:「代码现状」填了未验证假设(i18next 类型推导)· diagnose 才查出真因(ff326a74 path 类型加宽 · 4 调用点漏改 2)—— **命名/前缀路由/worktree 全押在猜测上**(真因在别的子项目就全配错)· 用户 review 被误导(中途反问「你排查到原因了么」)。
- diagnose-stage 自述「triage/prepare 读码只够判流程类型」—— 现象类场景连流程类型都判不可靠。

### 改动
- **prepare.md §2 立排查先行律**:现象类输入(报错/挂了/CI 失败/慢 · 无修复指令)且根因·影响面·归属未定 → 不定 Bug · 不 emit prepare —— 先问题排查(主对话 · 不进状态机)→ 排查闭合走 SKILL「Mode A/E 升级触发」暂停点(已验证根因 + 影响面 + 建议流程:转 Bug / Micro / Feature / 不动 / revert)→ 用户拍板 → prepare(排查结论 = 「代码现状」· 命名/路由据真因所在子项目)。**Bug 直入边界**:缺陷已指认(明确要求修复 · 现象+期望+位置已知)。判别题 = 「定流程所需事实是否已知」· 非「用户用了哪个词」。
- **关键词表两处收窄**(prepare §2 + FLOWS 识别列表):问题排查行接收现象类输入 · Bug 行加「仅当缺陷已指认」。
- prepare §0.5 反模式 +#7(现象输入未排查直接定 Bug + 总览填猜测)· §1.5.3「代码现状」加硬规则:**只写已验证事实 · 假设不得写入**。
- FLOWS 问题排查:用户选项补「转 Micro / revert 肇事 commit」+ 排查先行律;diagnose-stage 加**双入口**(②问题排查转入 → cite 结论复核不重查 · 重点落 BUG 报告 + 方案 R5 确认)。

### 验证
- doc-only · 关键词表两处口径一致(grep 复核)· pytest 3 failed / 523 passed(零回归)。

## v8.129 · 流程价值反思:ship2 后输出台账行 + digest(给仪式攒「该不该活着」的数据)

> 用户(承「teamwork 是否该存在」复盘):我们是否需要增加一个流程价值反思流程 · 在 ship2 后输出 → ok。

### 诊断:框架只有负反馈回路(出事 → 判例 → 加规则)· 没有正/零反馈(这环节这次拦没拦住东西)
- 规则只增不减(v8.0 以来 120+ 版首次系统性减法发生在 v8.121-127)· 仪式价值靠信念:多角色评审 self-talk 嫌疑 / 暂停点 all-default 率 / external confirmed 率全部无数据 · 「该不该砍」永远是辩论不是查表。
- 风险:反思流程自己变成新仪式 → 设计三条反仪式约束。

### 改动(doc-only · v1)
- **ship-stage.md §16**:ship-finalize 完成后 PMO 输出两层 —— ① 台账行 append 到 workspace `project-specs/PROCESS-LEDGER.md`(机器字段为主:实走 stages/时长/rounds/external 总采驳/角色真 finding/暂停点 改:默/bypass · AI 判断仅 2 格 · 照实抄不美化)② digest ≤10 行固定 4 问(拦住真问题?/纯过场?/流程新判例?/成本异常?)。
- **三条反仪式约束**:🔴 零新增暂停点(纯情报 · auto/yolo 照常)· 机器字段为主防 self-talk · 消费方指名(流程审视场景 + 年检 kill criteria:无新判例→仪式砍半 · external confirmed≈0→异质降可选 · 角色长期零真 finding→评审矩阵收缩)。
- **与既有 retros 划界**:`docs/retros/` = 业务/工程复盘(子项目级 · 知识层);PROCESS-LEDGER = 流程仪式价值度量(workspace 级)· 🔴 别混写(spec/模板双侧声明)。
- **豁免**:Micro 只记台账行不出 digest(最轻通道不加仪式)。
- 新 `templates/process-ledger.md` · 注册三处:templates/README 表 · conventions §13 project-specs 清单 · SKILL 路由表。
- ⏳ 物化 TODO(v2):ship-finalize 自动抽机器字段 emit ledger_row(AI 只补判断格)。

### 验证
- doc-only · pytest 3 failed / 523 passed(零回归)· 注册三处 + spec/模板分工声明 grep 一致。

## v8.130 · 台账采集时机修正:ship2 归档删目录后取数断粮 → 两段式(planning-backref 采写 · finalize 后 emit)

> 用户(承 v8.129):ship2 之后相关的产物都压缩了 · 你还能找到统计信息么。

### 诊断:对 —— v8.129 v1 设计两个缺陷被一问暴露
- **取数断粮**:§16 原定「finalize 完成后输出」· 但 §15 归档已把 state.json / REVIEW.md zip 进 `_archive/<id>.zip` 并删原目录 —— 数据没丢(zip 自描述 · `unzip -p` 可取)但取数高摩擦 · AI 大概率跳过或凭记忆填(违「照实抄」)。
- **写入无载体**:finalize 后 merge_target 全程只经 MR · 此时 append 台账行 = 脏文件无合入载体。

### 改动(doc-only)
- **§16 改两段式**:① 采集 + 写台账行 = ship2 step 5 `planning-backref` 暂停点(state.json/REVIEW.md 尚在磁盘 · 取数零成本)· 台账文件加进 `--planning-artifacts` 随**同一收尾 MR** 合入(`_resolve_planning_artifacts` 只校验「存在+仓内」· 已核代码)② digest = finalize 全部完成后 emit(从已写行渲染 · 时长口径 = init → ship2 暂存 · 表内统一)。
- **兜底成文**:漏写 → `unzip -p features/_archive/<id>.zip <id>/state.json` 不落盘取数 · 补行随下次任意 MR。
- v2 物化 TODO 同步:ship-finalize 在 planning-backref 暂停点 emit ledger_row 草稿(漏写不可能)。
- 同步措辞 4 处:templates/process-ledger.md 写入时机 · conventions §13 · SKILL 路由表 · templates/README。

### 验证
- doc-only · `--planning-artifacts` 路径校验已读码核实(存在+仓内即可)· pytest 3 failed / 523 passed(零回归)。

## v8.131 · 框架自省台账 RETRO-LEDGER:发版三件套 · 框架反思归框架仓(永久层)

> 用户:是否每次流程完善后写一段 teamwork 的问题/优化点/有用的地方/反思 · 记到 teamwork skill 子目录 —— 全项目总结汇一起 · 框架自身的东西不适合放项目目录。

### 诊断:框架自省无持久层 · 正反馈无归档处
- 框架反思散落 chat(session 结束即丢)与 CHANGELOG(keep-5 轮转 + 归档定期清空 · **故意易逝**);「有用的地方」(正反馈)更是哪都没记 → 年检只剩坏消息可查。PROCESS-LEDGER(v8.129)是项目侧的 · 框架侧缺对偶。

### 改动(doc-only)
- 新 `docs/RETRO-LEDGER.md`(框架自省台账):一行一版 · 6 列(版本/来源 case/问题/优化点/**有用的地方**/反思)· 单元格 ≤1 行 · 不复述 CHANGELOG · **永久**(超 ~500 行年检主题化压缩 · 原文 git 可溯)。
- **三层分工成文**:CHANGELOG = 单版细节(易逝)· PROCESS-LEDGER = 项目侧环节价值 · RETRO-LEDGER = 框架侧自省蒸馏(永久)。
- **发版三件套**(CHANGELOG 头部立约 · 同 commit):CHANGELOG entry + RETRO-LEDGER 1 行 + 版本 bump。
- **消费方指名**:年检/存在性审视直接读表;框架改进 session 动手前读最近 10 行(防重复踩坑)。
- **回填种子**:本 session v8.120→v8.130 共 11 行 + v8.131 自身 = 12 行。

### 验证
- doc-only · pytest 3 failed / 523 passed(零回归)。

## v8.132 · goal stage 质量改造:调研前置 + PL 对抗质疑 + 三闸早问门 + 全员通过物化(产高质量业务目标 PRD)

> 用户:review goal stage 逻辑是否合理(目的:产高质量业务目标 PRD)→ 追问早问门会否纵容上抛/有无调研前置 → 追问对抗性讨论(PL 质疑)→ 确认。

### 诊断(review 实锤)
- **结构 4 弱点**:业务目标事实输入薄 · 校准点全在最后(锚定:全员 APPROVE 包装后 step 7 才见用户 · v8.128 镜像);PL「审视」非「质疑」· 无人负责杀前提(同上下文切帽子 = 鼓掌效应);external@goal 无业务上下文(留台账裁决);AC 规模无反压。
- **漂移/死门禁 6 实锤**:goal-complete **不校验 verdicts**(全 NEEDS_REVISION 也能过 ·「全员通过」纸面纪律);authorized_pause_point「Substep 6」vs 文档 7 步(编号错位);`_check_prepare_completed` 死门禁(恒真 · hint 引用 P0-12 已删命令);PRD-REVIEW 模板内嵌旧 4 角色叙述段(RD/Designer/PMO)+ Round schema「删 pl/pmo · architect 不参与 prd」与现行 5 角色三方矛盾 · 顶层 reviewers/verdicts 字段缺失(machine schema 不满足代码门禁!)· PASS 系词表漂移;章节名两套(§需求背景/§用户场景/§边界 vs 模板 §背景/§用户故事/§Out of Scope);模板「PM 起草规范 checklist(单源化)」含起草前必读代码现状 · 但 cite 清单不路由 = writer-only。

### 改动
- **代码物化(+2 门禁 · −1 死门禁)**:`prd_verdicts_all_pass`(verdicts 全 APPROVE/SKIP · frontmatter 原文块级解析兼容行内{}与缩进 map · 旧 PASS 词表判 FAIL 强制 canon)· `pl_challenge_present`(角色含 pl 时 PRD-REVIEW 必含 PL-CHALLENGE · 敏捷需求无 pl 自动放行)· 删 prepare_completed 死门禁 · pause point 改「Substep 9 + 条件:Substep 4 早问门」· brief 同步 9 步。**+9 测试**(行内/缩进/SKIP/旧词表拒/缺失/无 pl 放行)。
- **goal-stage.md 重写为 9 步五层防线**:调研先行(事实层 · 四类:代码现状/KNOWLEDGE FA·Pref·OoS/GLOSSARY/上游规划 = 早问门入场券)→ 起草(模板单源 + AC>10 规模反压)→ **PL 对抗质疑**(前提层 · 质疑五问:价值前提/问题定义/范围最小化/上游对齐 cite/复活检查 · Q1 命中 subagent 隔离不喂起草心路 · PL-CHALLENGE-{n} 产物)→ **三闸早问门**(用户主权层 · 条件暂停:调研穷尽/主权判别〔上抛事实类=R5 违规〕/格式四件套+≤3+全带推荐 · auto 不停转 §待决策项+WARN)→ 多角色评审(完备性层)→ 用户确认(裁决层)。
- **模板对齐(464→388)**:删旧 4 角色叙述段 · role 枚举对齐现行 5 角色 · 顶层 reviewers+verdicts 补齐(满足代码门禁)· 词表统一 APPROVE|NEEDS_REVISION|SKIP · category +premise-challenge · 调研四类入 checklist ·「子步骤 3 RD 评审」×3 → substep 5 多角色。
- **联动**:roles/pm.md(调研/早问门/对抗自查)· roles/product-lead.md(质疑五问职责)· prepare Q1 命中后果 +「PL 质疑 subagent 隔离版」· 对抗有效性观测进 PROCESS-LEDGER(PL-CHALLENGE 采纳率 · 早问门 改:默)。

### 验证
- pytest 3 failed / 532 passed(baseline 3 · +9 新全过 · 零回归)· 模板旧口径 grep 清零(PASS 词表/旧角色段/删 pl 注释/子步骤旧编号)。
