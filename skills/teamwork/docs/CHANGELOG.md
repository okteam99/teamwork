# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.188 · 规划收尾:暂停问合入 merge_target → 建 MR → 提示用户合并 → 停(不自动起下一 feature)

> 实证 AON KA-PAGES:AI 规划完成后**自己** commit→push→建 draft MR,然后**立刻**跳进下一个 feature 的 prepare(还把新 feature 的 `merge_target` 设成**未合并的** `planning/ka-pages` 分支)—— 没有「是否合入 merge_target」确认暂停点,也没有「MR 建好 → 提示用户合并 → 停」。

### 改动(feature-planning Step 9 + planning-check)
- **规划收尾框成 3 步**(同 feature ship1):① R5 暂停问「**是否合入 `merge_target`**」② 确认后 worktree 内 commit+push planning 分支+开 MR(target=merge_target)③ 🔴 ⏸️ **提示用户合并 + 到此结束**。
- **🔴 不自动起下一 feature**:启动实施是**用户合并规划 MR 之后**的独立决策 · 🔴 **别叠 feature 在未合并 planning 分支**(feature `merge_target` = 集成分支 dev/staging · 非 planning 分支 · 否则实现 diff 混未合并规划、基线不稳)。
- `planning-check` `worktree_setup` + checklist item 6 同步(item 6 顺带修 v8.184 遗留的「主工作区直推」旧措辞)。

### 验证
- doc(feature-planning Step 9)+ code(`planning-check`)· `test_state` planning 4 passed · pytest 3 failed(baseline)/ 627 passed。

## v8.187 · preview 修订:真实交互页面内做 · dev 顶栏只放页面到不了的态(修 v8.169 过度)

> 用户(实战 AON admin 预览):全景设计尽量**页面内直接跳转**(点「新建模型」按钮直接开 Drawer)· 不要都依赖 dev 顶栏切换 · 顶栏只放**页面入口覆盖不到的**(错误/加载/难自然触发的态)。v8.169 当时矫枉过正 ——「页面切换 + 状态切换**都**走顶栏 · 页面禁内嵌**任何**预览控件」把真实可达的交互(按钮→Drawer)也赶到顶栏 · 反不如真实 app 保真。

### 改动(ui-design § preview dev 顶栏 + 分层同构 + brief)
- **区分「交互可达性」vs「状态注入」**:① 真实 app 点页面按钮能到的(新建/编辑 Drawer · Modal · 行→详情 · 页内导航/Tab)→ **页面内做成真实可点**(默认 · 交互保真 · 正是「设计=代码」要的)② dev 顶栏只放**真实交互无法自然触发的态**(`Loading/Error/Empty/边缘态` · 难自然触发的展示态 / preset 直开)。
- **「禁内嵌 switcher」澄清**:禁的是**预览专属控件**(真实 app 没有的 state-switcher 下拉/场景 toggle)· **不是禁真实交互按钮**。状态注入仍走顶栏(Storybook args)· 但**交互可达性走页面**。
- 页间跳转有**页内入口**则页内优先 · 顶栏兜底无页内入口的页。

### 验证
- doc(ui-design-stage § preview dev 顶栏 / 分层同构 line76)+ brief(`_ui_design_brief`)· `test_ui_design_brief` 断言措辞同步 · pytest 3 failed(baseline)/ 627 passed。

## v8.186 · ws-lint:WS 文档最新模板符合性校验 · 治 AI 抄项目旧 WS 无人检查

> 实证 AON WS-012:AI 做 feature-planning 写 WS 时**抄项目里旧/混合格式**(裸 `---` frontmatter · 无 `TEAMWORK-MACHINE` 块 · 无 `WS-PROGRESS`/`WS-DAG` 标记 · 缺 `ui_panorama_confirmed`)· **无符合性检查** · 只有用户主动问「按最新模板写的么」才发现。

### 改动
- **`state.py ws-lint`**(新):对照 `templates/workstream.md` 硬性形态校验 WS —— `TEAMWORK-MACHINE` 注释块(非裸 `---`)+ 必备 frontmatter(ws_id / status / ui_panorama / ui_panorama_confirmed / 承接执行线 / affected_subprojects / features)+ `WS-PROGRESS`/`WS-DAG` 标记区。`NONCONFORMANT` 列缺项 + hint「**别抄旧 WS** · 照模板补」。`--ws` / `--feature`。
- **feature-planning Step 6 + planning-check**:🔴 照 `templates/workstream.md` 起草 **别抄项目旧 WS** · 写完跑 `ws-lint` 校验 → 再 `ws-progress --write`。
- **测试** `test_ws_lint_v8186` +7(含 WS-012 复刻)。

### 验证
- code(`state.py` ws-lint)+ doc(feature-planning §2 + planning-check checklist)· pytest 3 failed(baseline)/ 627 passed。

## v8.185 · feature-planning 涉 UI 加全景用户确认暂停点(预览 URL)· 未确认不算规划完成

> 用户:feature-planning 涉 UI 要有**全景确认暂停点** + 给**可访问预览 URL** · 用户未确认过全景**不能算规划完成** · WS 加「全景设计已确认」标识。现状缺口:Step 5 出全景但**无用户确认暂停点**;WS `ui_panorama:✅` 只表「页在 preview-project」(AI 可自标)≠ 用户确认;规划完成门只卡 ✅ → WS 能在**用户没看过全景**时转规划完成。

### 改动
- **Step 5 加全景确认暂停点**(R5 · 拆 WS 前):全景出完 → 跑 `preview.sh` 抓 `PREVIEW_URL` → **给用户可访问预览 URL**(根 + 关键页直达)+ emit R5 等用户确认 · `auto_mode`/yolo 自动确认 + `add-concern` WARN 留痕。
- **WS 加 `ui_panorama_confirmed` 字段**(用户确认全景的 ISO · 非 UI `N-A`):区别于 `ui_panorama:✅`(页在全景 · AI 自标)—— 这是**用户拍板**标识。
- **规划完成硬门**:涉 UI WS 必 `ui_panorama:✅` **且** `ui_panorama_confirmed` 已填才能转 `✅ 规划完成` —— **用户没确认过全景 = 不算规划完成**。完成标准 / lifecycle / 子门禁 / Step 7 + planning-check checklist + SKILL §58 全同步。

### 验证
- code(`state.py` PLANNING_CHECKLIST)+ doc(feature-planning §5/6/7 · workstream.md · SKILL §58)· `test_state` planning 4 passed · pytest 3 failed(baseline)/ 620 passed。

## v8.184 · feature-planning 进流程建临时 worktree · 隔离规划产物(文档+全景代码)

> 用户:feature-planning 可能动文档和全景设计,进流程时应按 worktree 策略建临时 worktree。现状反例:feature-planning.md 明确「**不需要 worktree** · 在主工作区写文档」—— 但 planning 现在产出 WS/ROADMAP/product-overview 文档 **+ 全景 `preview-project` 代码**(v8.169 后是带 package.json 的真 code),落主工作区**污染主分支、撞并行 feature 基线**。

### 改动(反转「planning 不进 worktree」)
- **planning-check emit `worktree_setup`**(物化入口 · 同 feature 策略):进流程先 `git worktree add -b planning/<短名> .worktree/planning-<短名> origin/<merge-target>` + cd · 规划产物全写 worktree 内 · 完成 push + MR → 合并删 worktree。+ `key_constraints`/`next_hint` 同步。
- **feature-planning.md**:§1 反转「不需要 worktree」+ R6 nuance(不出 **feature 实现**代码 · 但全景 preview-project 是设计代码会改)· §2 加 **Step 0**(建 worktree 进流程第一步)· Step 9 改 worktree 内 commit + MR + 清理 worktree。
- **bootstrap 规划 forewarn** 加 worktree 提示。
- **定位**:worktree 只是**文件隔离** · planning 仍「PMO 主对话直接做」不进状态机 · 仅不走 ship 状态机(纯文档/全景 MR)· trivial 单文档微调用户可免。

### 验证
- code(`state.py` planning-check + `bootstrap` forewarn)+ doc(feature-planning.md §1/§2/§9)· `test_state` planning +worktree 断言 · pytest 3 failed(baseline)/ 620 passed。
