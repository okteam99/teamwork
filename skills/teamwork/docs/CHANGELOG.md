# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

