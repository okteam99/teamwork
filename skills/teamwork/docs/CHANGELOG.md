# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.216 · 评审配置动态化:拆掉 clarity 硬编码 · AI 按「角色价值判据」逐角色配 roster

> 用户裁决(对 v8.215 的修正):`--clarity` 固定消费(跳 PL+跳 external)还是太规则化 —— 该**动态决策**,不一定去 PL,也可能去 QA / ARCH。机制其实早已存在:`stage_review_roles`(所有 gate 本就按它放行)+ `change-review-roles`(审计留痕)· v8.215 错在绕过它另立硬规则。

### 改动
- **删两处硬编码 clarity gate**(PL challenge / blueprint external)—— gate 回归纯 roster 路由:角色不在 `stage_review_roles[stage]` → 自动放行(既有逻辑)。
- **prepare-check emit 加 `role_value_criteria`**(给 AI 的判断框架 · 非规则):逐角色问「这个视角对本 feature 能拦住什么」—— pl=价值前提可质疑?qa=边界/可测性风险?architect=架构决策/跨模块?external=多触发点/同模型盲区?**每角色一行理由(有值留 · 无值去)**· review stage 从严(建议 ≥2 视角 · <2 需强理由)。
- **`triage_evidence.consumption` 改**:凭证据逐 stage 逐角色配 roster(`change-review-roles --reason` · 审计)· `--clarity` **仅记录**进 state(台账/年检校准 · 不触发硬编码行为)。
- goal / blueprint brief 推送同步(冷审派谁 = 按 roster · 非按 clarity 一刀切)。

### 验证
- 测试重写:clarity 单独**不再**跳过任何 gate ✓ · roster 去角色 → gate 放行 ✓(×4)· pytest 817 passed。

## v8.215 · 智能分诊 v1:clarity 维度(明确度)→ 评审强度比例化 + 分诊证据先行

> 实证 case(admin i18n):「**大而明确**」的需求走全重流程 —— 车道把「大」和「不确定」绑死(477 key/7 页 → Feature → goal 3 冷审 + PL 质疑 + blueprint external 全上 · 但需求零歧义)。智能分诊方向(用户确认):输出从「车道标签」走向「维度向量」· 证据先行 · 本版落 v1。

### 改动
- **prepare-check emit 加 `triage_evidence` 证据槽**(estimated_files/cross_repo/new_deps/has_ui/mechanical/clarity)——🔴「看过再判」:30 秒侦察后填 · **空着不给判**;prepare.md §1.5 判定标准(explicit=明确方案或机械映射类;ambiguous=方向词;normal=默认)。
- **`init-feature --clarity`**(explicit/normal/ambiguous · 默认 normal)→ `state.clarity`。
- **explicit 消费两处**(gate 自动放行 · 留痕):① goal **PL 对抗质疑跳过**(无产品歧义可质疑)+ brief 推「冷审 3→1(QA 边界)」;② **blueprint external 跳过**(架构师单审)。🔴 **review 三视角不动**(明确 ≠ 不会写错 · 拦真主力 92/163)。
- 解耦原则:改动面大 → Feature **骨架**照走;不确定性低 → **评审轻档**。预期 explicit 类膜时间 −30~40%。

### 验证
- `test_clarity_v8215` +4(PL 跳/PL 照拦/blueprint 跳/review 不受影响)· pytest 817 passed。

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
