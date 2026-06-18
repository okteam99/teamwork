# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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
