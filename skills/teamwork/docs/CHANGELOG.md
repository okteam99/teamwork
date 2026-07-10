# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.214 · 注入段/hooks 清理挪出 skip_maintain 版本门(每次 bootstrap 都清 · 治 merge 回流旧块)

> 用户问:升级后会清注入段么?答:**会**(升级 → 版本 marker 不匹配 → maintain 跑 → 清理触发 · E2E 实证)。但验证同时抓到真实边缘:清理挂在 `skip_maintain` 版本门内 —— **同版本内二跑不清**。实害:并行分支上旧版 bootstrap 注入过的 AGENTS.md 被 `git merge` 带回 · 同版本内永不清 · 要等下次升级。

### 改动
- **`maintain_host_injection` + `maintain_host_hooks` 挪出 skip_maintain**(每次 bootstrap 都跑 · 同 v8.91 localconfig backfill「无论 skip 与否」先例)—— 清理幂等且轻(字符串查找)· merge 回流的旧注入块/hook 当次 session 即被兜住。chmod/gitignore 仍在版本门内(真·一次性维护)。

### 验证
- 冒烟:同版本 skip 下 merge 回流块被清 ✓(CLAUDE.md 只剩用户内容 · hook 同清)· pytest 813 passed。

## v8.213 · Claude hooks 全退役(teamwork 不需要 hooks)· bootstrap 转清理 + codex toml 保留

> 用户拍板:去掉 Claude hooks 相关逻辑。Review 佐证:hooks 是「宿主独有事件的自动触发层」· 与跨宿主原则相悖(scripts-policy 本就限制它只当薄壳);post-compact 恢复已由 state.json 断点续跑覆盖;codex hooks.json 更是当年 codex 账号 "cyber abuse" 警告的诱因之一(external-model-usage §抽出来源)—— 且 spec §110 明令删它 · bootstrap 却还在拷(spec-代码矛盾)。

### 改动(退役三件套:停部署 + 清存量 + 功能找新家)
- **删 `hooks/`**(hooks.json + post-compact/post-stop/post-subagent/session-restore.sh · 5 件)。
- **`maintain_host_hooks` 反转清理模式**:绝不部署 hooks;清历史部署(`.claude/hooks/` 5 个列名文件 + `.codex/hooks.json` · 🔴 **签名守卫**:内容含 teamwork 生态标记〔eamwork/PMO/dispatch_log/STATUS.md〕才删 · 用户同名 hook 保留)· 空目录顺手删 · 幂等。
- **codex agent toml 部署保留**(`.codex/agents/*.toml` = subagent profile · 活功能 · 与 hooks 无关)。
- **git-hooks/pre-push 不动**(发版 auto-bump · git hook 非 Claude hook)。
- SKILL 导航删 hooks/ 行 · scripts-policy hooks 段改退役声明 · 本仓 `.claude/hooks/` 自清(5 件全删含 PMO 签名的 post-subagent)。

### 验证
- 冒烟:签名删 ✓ 外来保留 ✓ toml 照部署 ✓ hooks.json 绝不部署 ✓ 幂等 ✓ · hooks 测试重写为退役语义 · pytest 813 passed。

## v8.212 · SKILL 文档导航补全(注入退役后 SKILL = 唯一入口 · 导航必须无死角)

> 用户:skill 里有目录索引吗?答:有(两类三层:skill 自身 § 文档导航 + 二级索引 STAGES/ROLES/STANDARDS/TEMPLATES;用户项目侧 § 文档清单/路由速查/结构索引 + teamwork-space)。但核对发现 § 文档导航**缺口真实**:docs/ 只列 CHANGELOG —— prepare(mode B 必经)/ feature-planning / conventions / teamwork-space-guide 全不在;STAGES.md(编排单源!)/ agents/README(subagent 协议)/ PRODUCT-OVERVIEW-INTEGRATION / hooks/ / agents profile 目录也不在。v8.211 注入退役后 SKILL 是唯一载体 · 导航更须全。

### 改动
- **§ 文档导航 15 行 → 24 行**:补 STAGES.md · PRODUCT-OVERVIEW-INTEGRATION · agents/README · docs/{prepare,feature-planning,conventions,teamwork-space-guide} · hooks/ · codex-agents/+claude-agents(external profile · 核实为活资产非死目录)· RETRO-LEDGER;TEMPLATES 行指向 templates/README 全清单;_v8_ship 描述更新(+ship-finalize/await-merge)。

### 验证
- doc-only · 相关套件通过。

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
