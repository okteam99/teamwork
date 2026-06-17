# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

