# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.231 · dispatch 模型分布观测(档位建议采纳率的数据闭环最后一块)

> 用户观察:很多时候还在用主模型跑 subagent。诊断三因:①到达率(v8.225-230 规则太新 · 副本未同步)②软约束惯性 ③**观测盲区 —— per-dispatch 的 model 无任何记录 · 「分档建议是否被采纳」无数据可验**。本版补 ③。

### 改动
- **`_dispatch_model_distribution(feature_dir)`**:从 `dispatch_log/*.md` 宽松解析每文件首个 `model:` 行 · 汇总分布;**未写 model 计 `unspecified(继承会话)`** —— 正是要观测的「没分档」信号;无 dispatch_log → {}(覆盖面 = 文件化 dispatch · 可审计路径)。
- **接进 `triage_calibration` 束**(archive emit)+ **audit 记录实际数据段** +1 行 + 台账「分诊校准」口径说明更新 —— 年检直接看 `unspecified` 占比 = 档位建议采纳率。

### 验证
- 冒烟(sonnet/opus/unspecified 分布 · INDEX 跳过 · 无目录空)· 测试 +2 · pytest 833 passed。

## v8.230 · dispatch 档位上移 SKILL 全局规则(撤 goal/review brief 散点 · 单源)

> 用户裁定:档位选择是**横切关注点**(任何 stage 任何 dispatch 适用)· 该放 SKILL.md 全局 · 不该散在 goal brief —— v8.229 的两处 brief 行是三处重复(agents/README 表 + 两 brief)· 必漂。

### 改动
- **SKILL subagent/teammate 条目追加「🎚️ dispatch 档位(全局规则)」**:不传 model = 继承会话模型(常费不自知)→ 派前按任务性质定档(校验/枚举型 → 验证档;判断/创造型 → 不降档)· 档位表与硬边界**单源 = agents/README §一**。
- **撤 v8.229 两处 brief 行**(goal/review)—— PMO 任何 dispatch 都在 SKILL 语境下 · 全局条目即消费点 · brief 保持极简。

### 验证
- brief 撤净冒烟 ✓ · pytest 831 passed。
