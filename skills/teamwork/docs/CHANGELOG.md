# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.236 · dev brief 补并行提示(开工先问哪些模块可并行)+ 修 stale 措辞

> 用户问:dev brief 有提醒用 subagent/teammate/workflow 么?查实:**没有** —— 并行规则全在 SKILL 全局/agents/README(被动),而 dev 恰是并行红利最大的 stage(多端/多模块实现);顺带抓到 brief「详细步骤 6 步 + 注意事项 5 条」是 v8.218 四段重构前的 stale 旧话。

### 改动
- **dev brief +1 行**(stage 专属手段提示 · 指向全局不复制 · 不违 v8.230 单源判例):🧩 开工先问「哪些模块可并行」→ 多端/多模块各派 subagent/teammate(**ultracode → workflow 优先**)· 派发按 SKILL 🎚️ **声明 model + why** · 契约层/集成点留主对话 · 子 agent 只写 worktree 内路径。
- 必读行修正为四段结构措辞(6 步旧话清除)。

### 验证
- brief 冒烟 ✓ · pytest 834 passed。

## v8.235 · dispatch 声明制:派 subagent/teammate/workflow 必声明「model + 一句为什么」+ 并行鼓励强化

> 用户指令:使用 subagent/teammate/workflow 时需给出匹配的模型并**说明为什么**;鼓励多用以提升并行度和效率。承 v8.230(全局档位规则)/v8.231(unspecified 观测)—— 规则有了、观测有了 · 缺**声明动作**逼出有意识选择。

### 改动
- **SKILL 全局条目升级为声明制**:每次派发必声明「model + 一句为什么」(主对话派发语句 / dispatch 文件 Meta / workflow `agent()` 旁注释)· 例 `model: sonnet(TC 对照 = 校验型 · 验证档够用)` · **不声明 = 默认继承没思考**(台账 unspecified 就在数这个)。⚡ 鼓励并行再强化:**能并行的不串行** · 并行度是效率的第一杠杆(ultracode 时 workflow 优先)。
- **agents/README**:并行姿态段声明制同步;文件化 dispatch **Meta 字段加 `model + model_reason`**。

### 验证
- doc-only · pytest 834 passed。

## v8.234 · await-merge 全模式必跑:「停 ≠ 停监控」(治 auto 停在 pushed 无人收尾)

> 实证 case(KA-PAGES):auto_mode feature 停在 ship.pushed · 用户 5 分钟后合了 MR · **没人收尾**(worktree/过程目录残留)· 该 session 的 AI 还解释成「auto 不监控 MR · 只有 yolo 才会」。两层缺口:① await-merge 指令只活在 ship-stage 文档 · **push emit(AI 实际照做的那份)没提**;② SKILL「auto 也必停此暂停点」被读成「session 到此结束」。

### 改动
- **push emit 补必跑步**:贴完卡片+总结后**立即跑 `await-merge`** —— 🔴 **所有模式(普通/auto/yolo)都跑**:「停」= 不能替用户点合并 · **不是停止监控**;MERGED → 自动 ship-finalize;手动 ship-finalize 降为 await-merge 不可用时的兜底。
- **SKILL auto_mode 表 ship1 行**:`stop` → `stop + 监控`(语义澄清 + 实证注)。
- **ship-stage §5** auto 措辞同步。

### 验证
- emit 断言 +2(await-merge / 不是停止监控)· pytest 834 passed。

## v8.233 · ship1 输出格式修正:卡片 + 交付总结**两段定序都必含**(撤 v8.232「禁总结」过度限制)

> 用户修正 v8.232 的理解偏差:不是让工具替掉总结 —— **总结是要的**(case 里那段链路/决策/解锁的内容本身有价值),要规范的是**格式结构**:URL 不能埋在总结里 · 两者都必含 · 各归其位。

### 改动
- **ship-stage §5 输出规范改为两段定序**:① MR 卡片(URL 置顶独立行 · 可直接用 emit `user_card` · 分支/URL 不抄错)② **📦 交付总结(必含 · AI 照实写 · 三槽结构:链路一行 / 关键决策与遗留 / 合并后解锁)**。🔴 **次序不可倒**(总结在前 = URL 埋段落 · 实证 case)。
- push emit 指令同步(「禁自写总结段」→「先卡片后总结 · 三槽」)· 测试断言同步。

### 验证
- pytest 834 passed。

## v8.232 · ship1 终点输出物化为 user_card(URL 置顶 · 工具生成 · AI 原样贴)

> 实证 case(SVC-PLATFORM offer-goals):ship1 收尾 AI 自由发挥写「本轮总结」长段 · **MR URL 埋进段落** · 用户被迫问「你把 mr 地址发出来啊」。spec 旧模板也把 URL 放最底部「决策参考」行。暂停点内容要**易消费**:第一屏第一信息 = 用户要点的那个链接。

### 改动
- **push emit 加 `user_card`**(工具确定性生成 · 🔴 AI **原样贴给用户 · 禁自写总结段**):标题行 → **🔗 MR URL 独立行置顶** → 分支/包含/监控/异常口令各一行;交付摘要要加 → 卡片之后 ≤3 行。next_action_brief 首条指令 = 贴卡片。
- **ship-stage §5 模板重写**:旧「四选项 + URL 沉底」→ 卡片契约 + await-merge 语义收敛(用户无需回编号 —— **合并动作本身就是确认**;仅「冲突/撤回」两个异常口令需要回话)。
- 卡片构造容错(无 feature 路径/git 失败 → 占位符 · 不阻塞 push)。

### 验证
- `user_card` URL 置顶断言 +1 · pytest 834 passed。
