# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

