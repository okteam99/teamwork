# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.209 · PROCESS-LEDGER + audit 记录 AI 宿主类型(codex / claude / gemini)

> 用户:台账要记 AI 宿主(codex 还是 claude)。宿主已在 `state.host`(claude-code/codex-cli/gemini-cli · audit 正文也有)· 本版落进台账列 + archive emit 采写数据 + audit frontmatter(供 harvest 按宿主分析)。

### 改动
- **ship1 archive emit `ledger_timing` 加 `host`**(= state.host)· 与时长/邮箱同束 · AI 照抄确定性。
- **audit frontmatter 加 `host:`**(与 v8.208 `user_email` 并列 · harvest 按宿主筛)。
- **PROCESS-LEDGER 模板加 `宿主` 列** + 口径说明(供年检**按宿主对比流程质量** —— external 采纳率 / 过场率 / AI 自主时长在 claude vs codex 的差异)。ship-stage §16 同步。

### 验证
- code(`_v8_ship` archive emit + audit frontmatter)+ 模板/§16 · `test_pause_mark_v8192` +1(host frontmatter)· pytest 818 passed。

## v8.208 · 流程价值台账时长三分(总/AI自主/等待用户)+ 各阶段细粒度 + 用户邮箱列

> 用户:台账时长要细化 —— 各阶段细粒度耗时 · 区分等待用户 · 排除等待=AI 自主运行耗时;加一列 git 用户邮箱。基础设施(v8.192 pause-mark `await_minutes` + `_AWAIT_USER_STAGES`)已有 · 本版把它落进台账/审计。

### 改动
- **`_timing_split(state)`**(新):`AI 自主 = Σ 工作 stage(duration − await)` · `等待用户 = Σ stage 内暂停 + Σ 纯等待 stage(pm_acceptance)墙钟` —— 分离墙钟里的人工等待。
- **`_git_user_email(cwd)`**(新):`git config user.email`。
- **ship1 archive emit 加 `ledger_timing`**(total_wall / ai_autonomous_min / await_user_min / per_stage / user_email)—— 台账在 archive 采写 · AI 照抄确定性数据不肉眼算 state。
- **audit 记录**:frontmatter `user_email` + 正文「AI 自主运行:Xm · 等待用户:Ym」+「用户邮箱」行(跨项目 harvest 按人分析)。
- **PROCESS-LEDGER 模板**:`时长` 拆为 `时长(总·AI自主·待用户)` + 新增 `各阶段耗时` + `用户邮箱` 列 + 三分口径说明。ship-stage §16 同步。

### 验证
- code(`_v8_ship` 2 helper + archive emit + audit)+ 模板/§16 · `test_pause_mark_v8192` +4 · pytest 817 passed。

## v8.207 · ship2 审计源材料预抽(治「先删 worktree 再要三段判断 → AI 被迫 unzip 反读」)

> 实证 case(用户看 Codex ship2):ship-finalize 删 worktree **后**要 AI 补 audit 三段判断,但源材料(REVIEW.md/TEST-REPORT.md)随 worktree 删除只剩归档 zip 内 → AI 被迫 `unzip -p` 反读。反直觉的人机工学 bug(交付安全无问题 · 主工作区干净)。

### 治本
- **`_capture_audit_sources(feature_dir)`**(新):ship-finalize 在 **worktree-remove 之前**(feature_dir 尚在)抓 `REVIEW*.md` + `TEST-REPORT.md` 压成紧凑摘录。
- **嵌进 audit 草稿 `## 源材料摘录` 段** —— AI 读草稿即可填三段(做的好的/发现的问题/待优化的)· 三段占位 + emit brief 改指「照实抄草稿内 §源材料摘录 + 实际数据 · 🔴 **无需 unzip 归档**」。
- 读失败静默降级(绝不阻塞 ship2)· 无源材料 → 不加空段(三段仍在)。

### 为什么不移到 ship1
实际数据全来自内存 `state`(worktree 删了也在)· 只有三段的**源文档**随 worktree 消失 —— 预抽摘录是最小修复,保持 v8.145「ship2 out-of-repo bookkeeping」不变(audit 落 `~/.teamwork/audit/` 非仓库)。

### 验证
- code(`_v8_ship`)+ ship-stage §16 doc · `test_audit_sources_v8207` +4 · pytest 813 passed。

## v8.206 · preview dev 工具面板改右下角悬浮(治顶栏 offset 布局 · 违 same-stack「零预览痕迹」)

> 实证 case(用户看预览页):dev 预览导航实际做成**右下角悬浮 Prototype Nav** · 比 spec 规定的**顶栏**合理。v8.187 理清了工具面板「放什么」(页面导航+状态注入 · 页内真实交互优先),但**位置写死「顶栏」**是错的。

### 治本
- **顶栏是 layout bar** —— 把真实页面内容**整体下推、offset 掉真实位置/尺寸**,恰恰违背 same-stack「**零预览痕迹 · 页面=真实代码**」核心目标(真实 app 没这条顶栏 → 加了预览就不像真实 app)。
- **右下角悬浮面板 = overlay** —— 不占布局流 · 不 shift 真实页面(页面在真实位置/尺寸渲染)· 右下角是 dev 工具通行惯例(devtools/toolbar 都在角落 · 一眼识别「工具非产品 chrome」)· 可折叠 · 半透明低层级。

### 改动(位置改 · 内容保 v8.187)
- ui-design-stage § 重命名 `preview dev 顶栏` → `preview dev 工具面板(右下角悬浮 · 非顶栏)` + 加位置治本段(顶栏反模式)· 页面区标注 `Prototype Nav`。
- 同步 same-stack 段 + `ui-rules.md` + `ui.md`(2 处)+ 新建的 `sitemap.md`:所有 dev shell 引用「顶栏」→「悬浮工具面板(右下角)」(RETRO 历史记录不动)。

### 验证
- doc-only · pytest 809 passed。

## v8.205 · 文档位置单源:SKILL 裸文件名误导修复 + sitemap 补模板(治 ROADMAP 落项目根)

> 实证 case(TermPro M5 规划):AI 把 `ROADMAP.md` 放**项目根**、来回挪。根因不是「没规范」而是**位置权威分裂** —— 模板阵营(templates/roadmap.md 头部「位置：docs/ROADMAP.md」)一致,但 SKILL.md 文档清单用**裸文件名**(`PROJECT.md`/`ROADMAP.md`/`sitemap.md` · 无路径)读起来像项目根,成了矛盾的第二源;sitemap 更糟 —— **连模板都没有**,全仓 3 个落点。

### 改动
- **SKILL.md 文档清单 + 路由速查**:三个裸名加 canonical 路径(`{子项目}/docs/PROJECT.md` · `docs/ROADMAP.md` · `{子项目}/docs/design/sitemap.md`)· 表头加 🔴「**位置权威 = 各 templates/*.md 头部「位置：」· 不在项目根裸放**」(单源指针 · 防再漂)。
- **新建 `templates/sitemap.md`**(补上唯一缺模板的产物 · 头部「位置：`{子项目}/docs/design/sitemap.md` 与全景同目录」+ IA 地图结构)· 全仓带路径引用本就一致指向 `panorama_path/sitemap.md`,conventions.md 是唯一异类 → 拉齐。
- **conventions.md** sitemap → `design/sitemap.md`(非 `docs/` 根)· **feature-planning Step 7** 写 ROADMAP 处加路径 + 指模板单源 · **templates/README** 登记 roadmap 位置 + sitemap 行。

### 验证
- doc-only(SKILL/conventions/feature-planning/templates)· pytest 809 passed。
