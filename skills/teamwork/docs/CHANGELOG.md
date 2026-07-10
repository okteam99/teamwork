# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.211 · 宿主指令文件注入退役(治共享仓库污染非 teamwork 用户)· 关键信息收进 SKILL.md

> 实证 case(commercial-data-warehouse):bootstrap 往 AGENTS.md/CLAUDE.md 注入 teamwork 段 · 共享仓库同事一 commit · **不用 teamwork 的用户也被迫吃到**。用户拍板:去注入 · 关键信息写进 SKILL.md(加载 skill 即生效 · 只影响用 teamwork 的 session —— 这才是正确的作用边界)。

### 改动
- **`maintain_host_injection` 反转为清理模式**:不再写入;发现历史 `<!-- TEAMWORK_BEGIN: -->` 块 → **移除**(marker 外用户内容一字不动 · 清后全空连文件删 · 幂等)· emit `cleanup_removed` + note。
- **SKILL.md 新增 § Subagent 默认授权**(载体自宿主注入块迁入 · v8.135 授权长期化的新家)+ 196 行引用改指本段;PMO 定位 / worktree 纪律 SKILL 本就有 · 不再依赖注入。
- **退役死资产**:`tools/sync-drift.py` + `templates/host-instruction-injection.md` + `test_sync_drift.py`;scripts-policy / templates/README / SKILL 工具清单 / README 中英措辞同步。
- 本仓根 `CLAUDE.md`(纯注入块)用新逻辑自清 → 已删。

### 验证
- 冒烟:移除保用户内容 ✓ 纯注入删文件 ✓ 干净不动 ✓ 幂等 ✓ 绝不创建 ✓ · 注入测试重写为清理语义(+4)· pytest 814 passed。

## v8.210 · PROCESS-LEDGER schema 演进纪律「只在末尾加列」+ 幂等 ledger-migrate(治旧项目台账不升级)

> 用户:模板升级了但旧项目台账没升级 · 要不要迁移逻辑。查实:台账**无按列位解析的代码**(冲突解是行级 union · 年检 AI 读)→ schema 漂移不 crash;但 v8.208/209 把新列**插在中间/前面** → 新行(13 列)追加到旧表头(10 列)**错位**、年检读错列。

### 治本:改 schema 纪律 = **只在末尾加列**
- **重排 v8.208/209 新列到表最右**(各阶段耗时/用户邮箱/宿主)→ 旧数据行天然是新 schema 的**有效前缀**(新列它们为空 = 该 feature 早于该指标 · 诚实)· 迁移退化为**仅换表头一行**。零成本(新 schema 刚上 dev · 无真实项目已落)。
- **`state.py ledger-migrate --feature <path>`**(新 · 幂等):旧 schema → 升级表头 + 分隔行(canonical 表头单源自 `templates/process-ledger.md`)· **旧数据行逐字不动** · 已最新 no-op · 无台账 SKIP。ship-stage §16 append 前必跑。

### 为什么不写重映射迁移器
「只在末尾加列」让旧行永远是有效前缀 → 永不需要 cell 级重映射 · 任何未来加列都只是表头一行替换。

### 验证
- code(`state.py` 2 helper + 命令)+ 模板重排 + §16 · `test_ledger_migrate_v8210` +4 · pytest 822 passed。

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
