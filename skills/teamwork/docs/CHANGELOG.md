# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.226 · external-ingest:ultra review 摄入为第三视角(session 主路径)+ ultracode workflow 姿态

> 让渡战略第一刀(评审执行让给更强的原生能力):`/code-review ultra` = 产品化多智能体独立评审(用户触发/计费/out-of-session)—— 接入为 external 第三视角的 **opt-in 增强源**。🔴 用户修正关键时序:**评审时 MR 多未创建** → 主路径 = **session 摄入**(用户在本 session 跑 ultra · findings 已在对话 · AI 转录)· paste 兜底(标 manual 降级)· pr-comments 留作 MR 窗口期增强(拉取即机器证据)。

### 改动
- **`state.py external-ingest --from session|paste|pr-comments [--label ultra]`**:归一化落盘 `external-cross-review/review-<label>.md`(frontmatter `review_via: ultra-ingest` + origin + 时间)· 过短拒收 · 🔴 **分层**:命令只做转录归一(确定性)· **裁决永远归 PMO**(emit 明示走 质疑→确认→裁决 管线 · ultra 也会 false positive · 盲采仍是反模式)。
- **门禁两处**:yolo 冷视角判定认 `review_via ∈ {subagent, ultra-ingest}`;异质文件名白名单校验对 ultra-ingest **豁免**(它非单一模型产物 · 独立性来自 out-of-session pipeline)。
- **review 手段菜单 +1 行**(关键/高风险改动 · 用户在场愿投入时建议);**agents/README 并行姿态 +1 句**:ultracode 开启的 session 冷审/验证 fan-out 优先用 Workflow(schema 化 findings · 契约不变 · 裁决归主对话)。
- 战略注记:review_engine 适配层(原 v8.227)确认**不建**(2-3 路负载下负 ROI · ultracode 下 PMO 手写 workflow 即可);workflow 改投**年检工具化**(harvest/spec 审计 50-200 路 fan-out 才是甜区)。

### 验证
- `test_external_ingest_v8226` +5(session 归一/paste 降级标/过短拒/缺 URL 拒/门禁认)· pytest 831 passed。
