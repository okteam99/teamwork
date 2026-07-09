# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.204 · external 异质评审默认关(用户拍板 · 全局一刀切 · yolo 也跟随)· 省 CLI 冷启动

> 用户:`disable_external_review` 默认改 true(默认关异质评审 · 太耗时)· yolo 也跟随默认关。厘清:开关只降级**第三视角 reviewer**(异质外部 CLI → 同模型 subagent 隔离冷审)· **架构师+QA 多角色评审完全不受影响照跑** · 耗时大头 = external CLI 冷启动。

### 改动(默认翻转 · 三处)
- **`_read_disable_external_review` + `_localconfig_disable_external` + bootstrap CONFIG_DEFAULTS**:key 缺省 / 无 config / 读失败 → **true**(禁用);**显式 `false` = opt-in 跨模型异质**。template localconfig seed 同步 true。
- **告警软化**(现在是默认常态 · 不再红字每次响):bootstrap heterogeneous_review status→`cold-review (default)` + note(非 warning)· 删 digest 🔴 行 · yolo kickoff `🔴🔴 醒目告警`→一行 `ℹ️ INFO`。
- **物化门禁不变**:第三视角**仍必真跑**(默认校验 `review_via: subagent` 冷审 · opt-in 异质校验实跑日志)· 去掉整个第三视角仍 BLOCK · 「非异质」也不许「不冷审」。

### 文档 reframe(避免变假话)
- README(中英)支柱表 / flow 表 / yolo 段:「异质 cross-review」→「第三视角独立 Review(默认同模型隔离冷审 · 跨模型异质 opt-in 升级)」。SKILL yolo 红线同步(第三视角默认冷审 · 异质 opt-in)。

### 验证
- pytest 809 passed(21 处 external 测试 setUp 改为显式 opt-in `disable_external_review:false` + 默认断言翻转)· 两读取器冒烟一致。

## v8.203 · 规划收尾暂停点重构:头两项一步到位(自动合并 + 收尾 / 收尾+启动首个 BL)

> 实证 case(AON WS-14 MMP 规划):收尾是「终审 → 建 MR → 等你告知已合并 → 再收尾」的多段手动接力 · 用户被迫手动短路「你直接合并然后规划收尾」。收尾该把常用路径做成一等选项。

### 改动(feature-planning Step 9 + planning-check 双 emit 同步)
- **暂停点选项重构**:① **确认·合入 MR + 收尾**(commit+push+开 MR+**自动合并**+清 worktree+净化主分支 · 一步到位)💡 ② **确认·合入收尾 + 启动首个 BL**(同 ① · 收尾完直接 prepare 首波 ready BL〔execution_waves W1 / ws-progress ready_to_start〕)③ 建 MR 我自己平台合(await-merge 轮询 / 平台合)④ 先不提交 ⑤ 其他。
- 🔴 **自动合并硬门(选 1/2)**:仅 `merge_target` 非主分支(main/master)—— 集成分支纯文档/全景低风险 · 同 yolo 自动合入非主分支风险模型;平台拒(审批/CI/保护)→ **自动回退选项 3** · 绝不 force。
- 🔴 **启动首个 BL(选 2)守 v8.188 护栏**:必 finalize 完成后(集成分支已含规划产物)+ 用户显式选 + feature target=集成分支 —— 「别叠 feature 在未合并 planning 分支」仍成立(planning 分支已消亡)。

### 验证
- doc + planning-check 双 emit · 新选项出现在 emit ✓ · pytest 809 passed。

## v8.202 · 模板地址全 stage 到位:diagnose 补映射 + scaffold_hints 加「别抄旧」+ 4 brief 指针

> 用户:是否所有 start brief 都给模板地址?查实:`scaffold_hints`(v8.14)**早已**在 stage-start emit 绝对路径(10 stage 映射+validator)· 但 PRD 到达率 2/11 证明被忽略。真缺口三处。

### 改动
- **diagnose 补进 STAGE_TEMPLATES**(原漏:产 BUG-XXX.md 的 stage 反而 start 时不给 bug-report 模板)。
- **scaffold_hints 加 `usage` 警示**(单点 · 全 stage 生效):照绝对路径起草 · **别抄项目里同名旧产物**(旧文件 = 旧版模板快照 · 附到达率实测)。
- **4 个 brief 加统一指针**(blueprint_lite/test/browser_e2e/pm_acceptance):「📋 产物模板见 scaffold_hints.templates」—— 不在 brief 重复路径(防双源)· 只指向。

### 验证
- code(engine 映射+usage · specs 4 指针)· diagnose hints 冒烟 ✓ · pytest 809 passed。
