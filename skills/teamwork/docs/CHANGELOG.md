# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.229 · 冷审 dispatch 档位推进 brief(治「goal 冷审全跑主对话模型」)

> 用户观察:goal 冷审实际都是主对话模型。根因 = v8.170 老病复发:档位框架(v8.225)躺 agents/README(被动)· goal/review brief 没推(主动)—— dispatch 不传 model 默认继承会话模型 · **常费而不自知**。

### 改动
- **goal brief +1 行**:dispatch 按角色性质分档 —— QA 冷审(可测性/边界 = 校验型)→ **验证档**(如 sonnet);**Architect / PL 不降档**(可行+简洁判断 · 价值前提对抗 = 深度判断)—— 三路冷审不该一刀切。
- **review brief +1 行**:QA code review 可派验证档;架构 CR 不降档(硬边界)。

### 验证
- brief 冒烟 ✓ · pytest 831 passed。

## v8.228 · 管辖判据 + 直答通道:管辖外输入(尤其现状问答)零仪式直答

> 用户指令:输入不属 teamwork 该管的(非 功能/缺陷/排查/规划)—— 尤其**问现状类** —— 直接回答,不走流程。现状病:5-mode 把一切输入往流程装,连「X 怎么实现的」都套 audit_line/mode 宣告/状态行(仪式噪音)。

### 改动
- **SKILL Triage 新增「🔴 管辖判据 · 直答通道」**(分诊之前先过):不属四类工作 → 直答 · **零 teamwork 输出协议**(无 audit_line/mode 宣告/状态行/recap/流程推销);现状/知识问答明确归此;答后追问升级成工作才进分诊 · **不主动推销流程**;拿不准按直答(误加仪式代价 > 误省)。
- **audit_line 作用域**:「首条响应必含」→「承接 teamwork 工作时必含 · 直答免」。
- **状态行作用域**:「有活动 feature/流程时」才输出 · 管辖外轮次免。
- roles/pmo.md 同步一行。

### 验证
- doc-only · pytest 831 passed。

## v8.227 · README-EN 类型体系补改(v8.224 只改了中文侧的残留)

> backlog #2:EN「6 Flow Types」表 + R2 红线行 + 快捷启动例仍是六类旧口径(变假话残留 · v8.224 描述审计只扫了中文面)。

### 改动
- EN 类型表重写(Feature·full / Feature·micro / Bug / Planning / Investigation + 机器层收缩说明)· R2 行改 `{Feature,Bug}+preset` · 启动示例注释改 preset 语言。

### 验证
- doc-only · 词汇残留复扫清零。
