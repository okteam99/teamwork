# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

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

## v8.225 · 模型档位判断框架(任务性质→档)+ 并行姿态翻转(鼓励 subagent/teammate)

> 用户两提案合一:① skill 层加模型建议(规划/方案/关键评审用高档 · 代码用执行档 · 测试验证用轻档 · GPT 同理);② 鼓励多用 subagent/teammate 提并行度。形态守 v8.194/216 判例:**「任务性质 → 档位」判断框架 · 非「stage → 型号」映射**(型号随代际漂移 · 跨宿主不通 · 逐 stage 映射是规则不是判断)。

### 改动
- **agents/README §一 重写为档位表**:深度档(创造+深度判断:规划/TECH/架构 CR/PRD/诊断/关键裁决)· 执行档(实现 · 主对话继承即是)· 验证档(校验/枚举:TC 对照/测试执行/机械外化)—— 型号列仅当前映射示例(Claude: Fable/Opus↔会话↔Sonnet/Haiku · GPT 对应档)+ 每档标**典型并行形态**。
- **三条硬边界**:架构 CR 与关键裁决不降档;**评审独立性优先于档位**(两个轻模型冷审 > 一个强模型热审);主对话模型 = 用户主权(AI 只建议)。
- **并行姿态翻转**(SKILL subagent 条目):从「⚠️ 非默认 · 不过度使用」改为「**默认考虑:每 stage 开工先问哪些子任务可并行**」(冷审 N 路同发/多模块 teammate/调研 fan-out)· 护栏原样(边界清晰且够大/worktree 路径/**流转与整合永归主对话**)。
- **prepare §1.4**:关键 Feature 建议主对话深度档 + prepare 时标出可并行子任务。台账 host+model(v8.208/209)= 档位建议的年检校准数据源。

### 验证
- doc-only · pytest 826 passed。

## v8.224 · skill 全文件描述审计:A 类 7 项「变假话」清零 + FLOWS 重写薄壳(102→40)

> 用户:整体看 skill 各文件描述的冗余与不合理。盘点实锤:合并三连(v8.220-223)后 **7 项过时描述**在教旧规则 + 流程类型**三处平行描述**(FLOWS×SKILL×prepare)。另发现元教训:cite(v8.199)/顶栏(v8.206)/hooks(v8.213)各漏扫一个目录 —— 退役清扫必须覆盖全部内容目录。

### 改动
- **FLOWS.md 重写 102→40 行**:闭集表 = Feature(full/micro)/Bug/Planning/排查 · telos 一行化 · 判定权威显式指 prepare(结束三处平行:prepare=权威 · SKILL=视图 · FLOWS=薄壳)。
- **SKILL 类型段真重写**(吃掉 v8.220/223 两层过渡注记):新 5 行表 + 授权暂停点表(删敏捷需求行 · Micro→Feature·micro)+ DB 变更措辞。
- **STAGES.md** flow 列更新 + blueprint_lite 标 DEPRECATED;**roles/pmo.md** 六闭集行改;**conventions.md §1** ID 表(敏捷/M 行标 legacy · 存量 M-id 有效不迁)。
- **漏网残留清零**:cite 仪式 ×4(prepare + 三个 report 模板)· dev 顶栏 ×1(scripts-policy)· hooks ×1(prepare)。

### 验证
- pytest 826 passed。

## v8.223 · blueprint_lite 并入 blueprint + lite preset 退役(preset 收为 full/micro)

> 用户两连问推到底:① blueprint_lite 还需要吗 —— 它与 blueprint **目标相同**(dev 前方案收敛)· 差异全是重量(评审组合=roster 已管 · verify-ac 分档=一行判断 · 文档深度=四段/模板已管)= 「stage 版的敏捷需求」;② 并入后 lite 链 = Feature 链的 **needs-ui=false 剖面**(一条冗余链)→ lite preset 整体退役。micro 保留(跳 review/test 是真结构差)。

### 改动(新路收口 · 存量三保留)
- **`FEATURE_PRESETS = (full, micro)`** · `LEGACY_FLOW_ALIASES:敏捷需求 → Feature·full`(轻量由动态 roster + clarity 承担)· `--preset` choices 同步。
- **存量兼容三保留**(in-flight 不断链):AGILE_FLOW 图原样(`resolve_flow_graph` 对 state.preset=lite 仍解析)· `internal_flow_key/_flow_key` 的 lite→敏捷需求 映射保留 · `BLUEPRINT_LITE_SPEC` 保持注册(标 DEPRECATED · 存量走完后删)。
- blueprint-lite-stage.md 挂 deprecated 横幅;prepare 关键词行(加按钮类 → Feature · 轻量由 roster/clarity)+ SKILL/README 注记同步。

### 验证
- pytest 826 passed(存量 lite 兼容断言全绿)。
